import os
import logging
import re
from functools import lru_cache
from typing import Dict, List, Optional, Any

import flair
import torch
from flair.data import Sentence
from flair.models import SequenceTagger
from flair.nn import Classifier
from cachetools import LRUCache

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Override Flair/PyTorch's model loading to address PyTorch 2.6 compatibility
# This patch ensures models load correctly with the new PyTorch 2.6 default behavior
original_torch_load = torch.load

def patched_torch_load(*args, **kwargs):
    # Only modify if weights_only is not explicitly specified
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return original_torch_load(*args, **kwargs)

# Apply the patch
torch.load = patched_torch_load

# Define non-academic titles to be removed from person entities
NON_ACADEMIC_TITLES = [
    # Government/political titles
    'Presiden', 'Wakil Presiden', 'Menteri', 'Gubernur', 'Wakil Gubernur',
    'Bupati', 'Wakil Bupati', 'Walikota', 'Wakil Walikota', 'Sekretaris',
    'Ketua', 'Wakil Ketua', 'Direktur', 'Jenderal', 'Jendral', 'Panglima',

    # Religious titles
    'Ustaz', 'Ustadz', 'Kyai', 'Kiai',

    # Military/police ranks
    'Letnan', 'Kapten', 'Mayor', 'Kolonel', 'Laksamana', 'Komisaris',
    'Inspektur', 'Brigadir',

    # Business titles
    'CEO', 'CFO', 'COO', 'CTO', 'Manajer', 'Manager', 'Direktur'
]

# Compile a regex pattern for efficient matching
# This pattern now handles titles that may be followed by geographic identifiers
# It matches: 1. Title at start, 2. Optional geographic/org identifier, 3. Actual name
TITLE_PATTERN = re.compile(
    r'^(' + '|'.join(NON_ACADEMIC_TITLES) + r')\s+' +  # The title
    r'(?:(?:[A-Z][a-z]*\s*)+\s+)?' +  # Optional geographic/org identifier (e.g., "Jawa Barat")
    r'([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*)'  # The actual person name (e.g., "Ridwan Kamil")
    , re.UNICODE)

# Academic titles that should be preserved
ACADEMIC_TITLES = [
    'Dr', 'Prof', 'Ir', 'Drs', 'Drg', 'M.Sc', 'M.Si', 'M.A', 'M.M', 'M.Kom', 'Ph.D',
    'S.T', 'S.Kom', 'S.E', 'S.Sos', 'S.H', 'S.Pd', 'S.I.P', 'S.Ag', 'S.IP'
]

class ModelLoader:
    """Responsible for loading and managing the model."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = None
        self.cache = LRUCache(maxsize=settings.CACHE_SIZE)

        # Configure flair to use GPU if available and requested
        if settings.USE_CUDA and flair.device.type != 'cuda':
            flair.device = 'cuda'
            logger.info("Using GPU for inference")
        else:
            flair.device = 'cpu'
            logger.info("Using CPU for inference")

    def load_model(self) -> None:
        """Load the NER model."""
        if self.model is not None:
            logger.info("Model already loaded")
            return

        try:
            # Try to load a pre-trained Indonesian NER model directly using SequenceTagger
            logger.info("Loading Indonesian NER model...")

            # Try to load a standard Flair NER model first (most compatible)
            try:
                logger.info("Attempting to load Flair's multilingual NER model...")
                self.model = SequenceTagger.load('ner-multi')
                logger.info("Successfully loaded Flair's multilingual NER model")
            except Exception as e:
                logger.warning(f"Failed to load Flair's multilingual NER model: {e}")

                # Then try the specific Indonesian models
                try:
                    model_name = "cahya/bert-base-indonesian-NER"
                    logger.info(f"Attempting to load {model_name}...")
                    self.model = SequenceTagger.load(model_name)
                    logger.info(f"Successfully loaded {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")

                    # If that fails, try another Indonesian model
                    try:
                        model_name = "cahya/xlm-roberta-base-indonesian-NER"
                        logger.info(f"Attempting to load {model_name}...")
                        self.model = SequenceTagger.load(model_name)
                        logger.info(f"Successfully loaded {model_name}")
                    except Exception as e:
                        logger.error(f"Failed to load any NER models: {e}")
                        raise ValueError("Could not load any NER model. Please check PyTorch and Flair compatibility.")

            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def is_model_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.model is not None

    def _process_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an entity to remove non-academic titles from person names.

        Args:
            entity: The entity dictionary from the model

        Returns:
            Processed entity dictionary
        """
        # Only process person entities
        if entity['type'] == 'PER':
            text = entity['text']

            # Try to identify and remove titles
            for title in NON_ACADEMIC_TITLES:
                # Check if text starts with this title
                pattern = f"^{title}\\s+"
                if re.match(pattern, text, re.IGNORECASE):
                    # Text starts with this title

                    # Check for academic title (to preserve it)
                    if not any(academic_title in title for academic_title in ACADEMIC_TITLES):
                        # Find the title length including the following space
                        title_length = len(title) + 1

                        # Check for geographic identifiers
                        rest_of_text = text[title_length:].strip()
                        words = rest_of_text.split()

                        # If there are at least 3 words, the first might be a geographic identifier
                        # (e.g., "Jawa" in "Gubernur Jawa Barat Ridwan Kamil")
                        if len(words) >= 3 and words[0][0].isupper() and words[1][0].isupper():
                            # Check if second word also starts with uppercase (likely part of geo identifier)
                            # "Jawa Barat" in "Gubernur Jawa Barat Ridwan Kamil"
                            name_start = title_length + len(words[0]) + 1 + len(words[1]) + 1
                            person_name = text[name_start:].strip()
                        else:
                            # No geographic identifier, just remove the title
                            person_name = rest_of_text

                        # Update the entity
                        entity['text'] = person_name
                        entity['start_pos'] = entity['start_pos'] + (text.find(person_name))

                        logger.debug(f"Removed title: '{title}' from person entity, new value: '{person_name}'")

                        # We found and processed a title, exit the loop
                        break

        return entity

    def predict(self, text: str) -> List[Dict[str, Any]]:
        """
        Predict named entities in the given text.

        Args:
            text: The text to analyze

        Returns:
            List of recognized entities with type, text, and position
        """
        if len(text) < self.settings.MIN_TEXT_LENGTH:
            return []

        # Check if result is cached
        cache_key = text.strip()
        if cache_key in self.cache:
            logger.debug("Cache hit")
            return self.cache[cache_key]

        # Make sure model is loaded
        if not self.is_model_loaded():
            self.load_model()

        # Create a Flair sentence
        sentence = Sentence(text)

        # Predict NER tags
        self.model.predict(sentence)

        # Extract entities
        entities = []
        for entity in sentence.get_spans('ner'):
            # Extract entity data
            entity_dict = {
                'text': entity.text,
                'type': entity.tag,
                'start_pos': entity.start_position,
                'end_pos': entity.end_position,
                'confidence': entity.score
            }

            # Process the entity to remove titles if needed
            entity_dict = self._process_entity(entity_dict)

            entities.append(entity_dict)

        # Cache the result
        self.cache[cache_key] = entities

        return entities

    def predict_batch(self, texts: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Predict named entities for multiple texts at once.

        Args:
            texts: List of texts to analyze

        Returns:
            List of lists of recognized entities
        """
        if not texts:
            return []

        # Filter out very short texts
        valid_texts = [text for text in texts if len(text) >= self.settings.MIN_TEXT_LENGTH]
        if not valid_texts:
            return [[] for _ in texts]

        # Make sure model is loaded
        if not self.is_model_loaded():
            self.load_model()

        # Check which texts are cached
        results = []
        sentences = []
        text_to_idx = {}

        for i, text in enumerate(texts):
            cache_key = text.strip()
            if cache_key in self.cache:
                # Use cached result
                results.append(self.cache[cache_key])
            else:
                # Create a sentence for prediction
                sentence = Sentence(text)
                sentences.append(sentence)
                text_to_idx[id(sentence)] = i
                # Add a placeholder for this result
                results.append(None)

        # If there are uncached sentences, predict them
        if sentences:
            # Predict NER tags
            self.model.predict(sentences, mini_batch_size=self.settings.MAX_BATCH_SIZE)

            # Extract entities
            for sentence in sentences:
                i = text_to_idx[id(sentence)]
                entities = []
                for entity in sentence.get_spans('ner'):
                    # Extract entity data
                    entity_dict = {
                        'text': entity.text,
                        'type': entity.tag,
                        'start_pos': entity.start_position,
                        'end_pos': entity.end_position,
                        'confidence': entity.score
                    }

                    # Process the entity to remove titles if needed
                    entity_dict = self._process_entity(entity_dict)

                    entities.append(entity_dict)

                # Cache the result
                cache_key = texts[i].strip()
                self.cache[cache_key] = entities

                # Update the result
                results[i] = entities

        # Make sure all results are filled
        for i, result in enumerate(results):
            if result is None:
                results[i] = []

        return results


# Create a singleton instance of ModelLoader
@lru_cache()
def get_model_loader() -> ModelLoader:
    """Return the singleton ModelLoader instance."""
    settings = get_settings()
    return ModelLoader(settings)