import json
import logging
from typing import Dict, List, Optional, Any
from functools import lru_cache

import openai
from cachetools import LRUCache

from app.core.config import Settings, get_settings
from app.core.model_loader import ModelLoader, get_model_loader

logger = logging.getLogger(__name__)

class LegalEntityAnalyzer:
    """
    Class for analyzing legal entities in texts using OpenAI's GPT model.
    Identifies entities as defendants, plaintiffs, or representatives.
    """

    def __init__(self, settings: Settings, model_loader: ModelLoader):
        self.settings = settings
        self.model_loader = model_loader
        self.cache = LRUCache(maxsize=settings.CACHE_SIZE)

        # Initialize OpenAI client
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not set. Legal entity analysis will not work.")
        else:
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(f"OpenAI client initialized with model: {settings.OPENAI_MODEL}")

    def analyze_legal_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Analyze text to identify legal entities (defendants, plaintiffs, representatives).

        Args:
            text: The text to analyze

        Returns:
            List of identified legal entities with their roles
        """
        if len(text) < self.settings.MIN_TEXT_LENGTH:
            return []

        # Check cache first
        cache_key = text.strip()
        if cache_key in self.cache:
            logger.debug("Cache hit for legal entity analysis")
            return self.cache[cache_key]

        # If OpenAI API key is not set, return empty result
        if not self.settings.OPENAI_API_KEY:
            logger.error("OpenAI API key not set. Cannot perform legal entity analysis.")
            return []

        try:
            # First get standard NER results to identify people
            ner_results = self.model_loader.predict(text)

            # Filter to only keep person entities
            person_entities = [entity for entity in ner_results if entity['type'] == 'PER']

            if not person_entities:
                logger.debug("No person entities found in text")
                return []

            # Extract person names
            person_names = [entity['text'] for entity in person_entities]

            # Call OpenAI to classify these people
            result = self._classify_legal_entities(text, person_names)

            # Cache the result
            self.cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in legal entity analysis: {e}")
            return []

    def _classify_legal_entities(self, text: str, person_names: List[str]) -> List[Dict[str, Any]]:
        """
        Use OpenAI to classify people in the text as defendants, plaintiffs, or representatives.

        Args:
            text: The full text to analyze
            person_names: List of person names to classify

        Returns:
            List of classified legal entities
        """
        try:
            # Format the prompt for OpenAI
            prompt = self._create_prompt(text, person_names)

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                temperature=self.settings.OPENAI_TEMPERATURE,
                max_tokens=self.settings.OPENAI_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": "You are a legal document analyzer that identifies the roles of people mentioned in legal texts."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)

            # Extract the entities from the result
            if 'entities' in result:
                return result['entities']
            else:
                logger.warning("OpenAI response did not contain expected 'entities' field")
                return []

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return []

    def _create_prompt(self, text: str, person_names: List[str]) -> str:
        """
        Create the prompt for the OpenAI API.

        Args:
            text: The text to analyze
            person_names: List of person names to classify

        Returns:
            Formatted prompt
        """
        names_list = ", ".join([f'"{name}"' for name in person_names])

        prompt = f"""Analyze the following text and identify the roles of these people: {names_list}.

For each person, determine if they are a defendant, plaintiff, or representative (like a lawyer, judge, etc.).
If their role cannot be determined, classify them as "unknown".

Text:
```
{text}
```

Return the results in JSON format with the following structure:
{{
  "entities": [
    {{
      "name": "<person name>",
      "role": "<defendant|plaintiff|representative|unknown>",
      "confidence": <float between 0 and 1>
    }},
    ...
  ]
}}
"""
        return prompt

    def analyze_legal_entities_batch(self, texts: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Analyze multiple texts to identify legal entities.

        Args:
            texts: List of texts to analyze

        Returns:
            List of lists of identified legal entities with their roles
        """
        if not texts:
            return []

        # Filter out very short texts
        valid_texts = [text for text in texts if len(text) >= self.settings.MIN_TEXT_LENGTH]
        if not valid_texts:
            return [[] for _ in texts]

        # Process each text individually and return results
        results = []
        for i, text in enumerate(texts):
            if i >= len(valid_texts):
                results.append([])
            else:
                results.append(self.analyze_legal_entities(text))

        return results


@lru_cache
def get_legal_entity_analyzer() -> LegalEntityAnalyzer:
    """
    Factory function to create and cache a LegalEntityAnalyzer instance.

    Returns:
        Cached LegalEntityAnalyzer instance
    """
    settings = get_settings()
    model_loader = get_model_loader()
    return LegalEntityAnalyzer(settings, model_loader)