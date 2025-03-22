import json
import logging
import traceback
import os
from typing import Dict, List, Optional, Any
from functools import lru_cache

import litellm
from cachetools import LRUCache

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

class LegalEntityAnalyzer:
    """
    Class for analyzing legal entities in texts using LLM models via LiteLLM.
    Identifies entities as defendants, plaintiffs, or representatives.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.cache = LRUCache(maxsize=settings.CACHE_SIZE)

        # Initialize LiteLLM
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not set. Legal entity analysis will not work.")
            return

        try:
            # Configure LiteLLM with the API key
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

            # LiteLLM will use the environment variable
            logger.info("Using LiteLLM for model calls")
            logger.info(f"LiteLLM configured with model: {settings.OPENAI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize LiteLLM: {e}")
            logger.error(traceback.format_exc())

    def analyze_legal_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Analyze text to identify legal entities (defendants, plaintiffs, representatives).

        Args:
            text: The text to analyze

        Returns:
            List of identified legal entities with their roles
        """
        if len(text) < self.settings.MIN_TEXT_LENGTH:
            logger.debug("Text too short for analysis")
            return []

        # Check cache first
        cache_key = text.strip()
        if cache_key in self.cache:
            logger.debug("Cache hit for legal entity analysis")
            return self.cache[cache_key]

        # If OpenAI API key is not set, return empty result
        if not self.settings.OPENAI_API_KEY:
            logger.error("API key not set. Cannot perform legal entity analysis.")
            return []

        try:
            # Get entity classification via LiteLLM
            result = self._identify_and_classify_legal_entities(text)
            logger.info(f"Classification result: {result}")

            # Cache the result
            self.cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in legal entity analysis: {e}")
            logger.error(traceback.format_exc())
            return []

    def _identify_and_classify_legal_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Use LiteLLM to identify people in the text and classify them as defendants, plaintiffs, or representatives.

        Args:
            text: The full text to analyze

        Returns:
            List of classified legal entities
        """
        try:
            # Format the prompt for the LLM
            prompt = self._create_prompt(text)
            logger.info(f"Created prompt for LLM classification. Text length: {len(text)}")
            logger.debug(f"Prompt: {prompt}")

            content = ""
            try:
                # Log API key (masked)
                api_key = self.settings.OPENAI_API_KEY
                masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key and len(api_key) > 8 else "None"
                logger.info(f"Using API Key: {masked_key}")
                logger.info(f"Using Model: {self.settings.OPENAI_MODEL}")

                # Use LiteLLM to call the API
                logger.info("Calling LLM via LiteLLM")
                messages = [
                    {"role": "system", "content": "You are a legal document analyzer that identifies people mentioned in legal texts and determines their roles."},
                    {"role": "user", "content": prompt}
                ]

                # Call the API using LiteLLM
                response = litellm.completion(
                    model=self.settings.OPENAI_MODEL,
                    messages=messages,
                    temperature=self.settings.OPENAI_TEMPERATURE,
                    max_tokens=self.settings.OPENAI_MAX_TOKENS
                )

                # Extract response content
                content = response.choices[0].message.content
                logger.info(f"Received LLM response of length: {len(content)}")
                logger.debug(f"Response content: {content}")

            except Exception as e:
                logger.error(f"Error calling LLM API via LiteLLM: {e}")
                logger.error(traceback.format_exc())

                # Fallback to manual extraction
                logger.info("API call failed, falling back to manual extraction")
                return self._fallback_entity_extraction(text)

            # Try to extract entities from the response
            entities = []

            try:
                # Try to parse as JSON first
                result = json.loads(content)
                logger.info(f"Parsed JSON result: {result}")

                # Extract the entities from the result
                if 'entities' in result:
                    logger.info(f"Extracted entities from JSON: {result['entities']}")
                    entities = result['entities']
                elif isinstance(result, list):
                    # Sometimes LLM might return a list directly
                    logger.info("Result is a list, using as entities")
                    entities = result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response content: {content}")

                # Fall back to manual extraction
                return self._fallback_entity_extraction(text)

            # Validate entity format
            validated_entities = self._validate_entities(entities)
            logger.info(f"Final validated entities: {validated_entities}")
            return validated_entities

        except Exception as e:
            logger.error(f"Error in entity classification: {e}")
            logger.error(traceback.format_exc())
            return []


    def _validate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and normalize entity format

        Args:
            entities: List of extracted entities

        Returns:
            List of validated entities
        """
        validated_entities = []
        for entity in entities:
            try:
                # Ensure all required fields are present
                name = entity.get('name', '')
                role = entity.get('role', 'unknown')
                confidence = entity.get('confidence', 0.7)

                # Validate role
                if role not in ['defendant', 'plaintiff', 'representative', 'unknown']:
                    role = 'unknown'

                # Validate confidence
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                    confidence = 0.7

                validated_entities.append({
                    'name': name,
                    'role': role,
                    'confidence': confidence
                })
            except Exception as e:
                logger.error(f"Error validating entity: {e}")

        # Special case: if there's only one entity, it should be classified as a defendant
        if len(validated_entities) == 1:
            logger.info("Only one entity found, classifying as defendant")
            validated_entities[0]['role'] = 'defendant'
            # Keep the original confidence if it was high, otherwise boost it
            if validated_entities[0]['confidence'] < 0.8:
                validated_entities[0]['confidence'] = 0.8


        return validated_entities

    def _create_prompt(self, text: str) -> str:
        """
        Create the prompt for the LLM.

        Args:
            text: The text to analyze

        Returns:
            Formatted prompt
        """
        prompt = f"""Analyze the following legal text and identify all people mentioned. Look for names of individuals.

For each person found, determine if they are a defendant, plaintiff, or representative (like a lawyer, judge, etc.).
If their role cannot be determined, classify them as "unknown".

Follow these rules carefully:
1. In Indonesian legal documents, individual names that appear without explicit roles should generally be classified as defendants, especially if they have lineage (Bin/Binti) or titles.
2. If there's no clear plaintiff mentioned, prioritize classifying individuals as defendants.

Indonesian terminology:
- "Penggugat" means plaintiff
- "Terdakwa" means defendant
- "Kuasa Hukum", "Pengacara", or "Advokat" means legal representative/lawyer
- "Hakim" means judge (a type of representative)
- "Jaksa/Penuntut Umum" means prosecutor (a type of representative)

Text:
```
{text}
```

IMPORTANT: Return ONLY raw JSON with no markdown formatting, code blocks, or explanations.
Do NOT begin your response with ```json or any other markers.
Do NOT end your response with ```.
Simply return a clean, valid JSON object with the following structure:

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

The response must be valid JSON that can be directly parsed using json.loads().
"""
        return prompt

    def _create_batch_prompt(self, texts: List[str]) -> str:
        """
        Create a prompt for batch processing multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            Formatted prompt for batch processing
        """
        # Create the base prompt with instructions
        prompt = """Analyze each of the following legal texts and identify all people mentioned in each text. Look for names of individuals.

For each person found in each text, determine if they are a defendant, plaintiff, or representative (like a lawyer, judge, etc.).
If their role cannot be determined, classify them as "unknown".

Follow these rules carefully:
1. In Indonesian legal documents, individual names that appear without explicit roles should generally be classified as defendants, especially if they have lineage (Bin/Binti) or titles.
2. If there's no clear plaintiff mentioned, prioritize classifying individuals as defendants.

Indonesian terminology:
- "Penggugat" means plaintiff
- "Terdakwa" means defendant
- "Kuasa Hukum", "Pengacara", or "Advokat" means legal representative/lawyer
- "Hakim" means judge (a type of representative)
- "Jaksa/Penuntut Umum" means prosecutor (a type of representative)

Texts to analyze:
"""
        # Add each text with an index
        for i, text in enumerate(texts, 1):
            prompt += f"\nText {i}:\n```\n{text}\n```\n"

        prompt += """
IMPORTANT: Return ONLY raw JSON with no markdown formatting, code blocks, or explanations.
Do NOT begin your response with ```json or any other markers.
Do NOT end your response with ```.
Simply return a clean, valid JSON object with the following structure:

{
  "results": [
    {
      "text_index": 1,
      "entities": [
        {
          "name": "<person name>",
          "role": "<defendant|plaintiff|representative|unknown>",
          "confidence": <float between 0 and 1>
        },
        ...
      ]
    },
    {
      "text_index": 2,
      "entities": [
        ...
      ]
    },
    ...
  ]
}

The response must be valid JSON that can be directly parsed using json.loads().
"""
        return prompt

    def analyze_legal_entities_batch(self, texts: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Analyze multiple texts to identify legal entities in a single batch.

        Args:
            texts: List of texts to analyze

        Returns:
            List of lists of identified legal entities with their roles
        """
        if not texts:
            return []

        # Filter out very short texts and get their indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if len(text) >= self.settings.MIN_TEXT_LENGTH:
                valid_texts.append(text)
                valid_indices.append(i)

        if not valid_texts:
            return [[] for _ in texts]

        try:
            # Create batch prompt
            prompt = self._create_batch_prompt(valid_texts)
            logger.info(f"Created batch prompt for {len(valid_texts)} texts")

            # Call LLM API
            try:
                logger.info("Calling LLM via LiteLLM for batch processing")
                messages = [
                    {"role": "system", "content": "You are a legal document analyzer that identifies people mentioned in legal texts and determines their roles."},
                    {"role": "user", "content": prompt}
                ]

                response = litellm.completion(
                    model=self.settings.OPENAI_MODEL,
                    messages=messages,
                    temperature=self.settings.OPENAI_TEMPERATURE,
                    max_tokens=self.settings.OPENAI_MAX_TOKENS
                )

                content = response.choices[0].message.content
                logger.info(f"Received batch LLM response of length: {len(content)}")

            except Exception as e:
                logger.error(f"Error in batch LLM API call: {e}")
                # Fallback to individual processing
                return [self.analyze_legal_entities(text) for text in texts]

            try:
                # Parse the response
                result = json.loads(content)
                logger.info("Successfully parsed batch response JSON")

                # Initialize results list with empty lists
                final_results = [[] for _ in texts]

                # Process each text's results
                if 'results' in result:
                    for text_result in result['results']:
                        text_index = text_result.get('text_index', 0) - 1  # Convert to 0-based index
                        if 0 <= text_index < len(valid_indices):
                            original_index = valid_indices[text_index]
                            entities = text_result.get('entities', [])
                            validated_entities = self._validate_entities(entities)
                            final_results[original_index] = validated_entities

                return final_results

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse batch response JSON: {e}")
                # Fallback to individual processing
                return [self.analyze_legal_entities(text) for text in texts]

        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            logger.error(traceback.format_exc())
            # Fallback to individual processing
            return [self.analyze_legal_entities(text) for text in texts]


@lru_cache
def get_legal_entity_analyzer() -> LegalEntityAnalyzer:
    """
    Factory function to create and cache a LegalEntityAnalyzer instance.

    Returns:
        Cached LegalEntityAnalyzer instance
    """
    settings = get_settings()
    return LegalEntityAnalyzer(settings)