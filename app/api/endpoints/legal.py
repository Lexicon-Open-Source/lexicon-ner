import logging
import traceback
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.legal_entity_analyzer import LegalEntityAnalyzer, get_legal_entity_analyzer
from app.core.security import get_api_key

logger = logging.getLogger(__name__)

# Router for legal entity endpoints
router = APIRouter()

# Model for legal entity request
class LegalEntityRequest(BaseModel):
    text: str = Field(...,
                      description="The legal text to analyze for entities",
                      min_length=1,
                      example="In the case of Smith v. Jones, the plaintiff John Smith filed a lawsuit against the defendant Sarah Jones. Attorney Michael Johnson represents the plaintiff.")

# Model for batch legal entity request
class BatchLegalEntityRequest(BaseModel):
    texts: List[str] = Field(...,
                            description="List of legal texts to analyze for entities",
                            min_items=1,
                            max_items=10)

# Model for legal entity response
class LegalEntity(BaseModel):
    name: str = Field(..., description="The name of the person")
    role: str = Field(..., description="The role in the legal context (defendant, plaintiff, representative, unknown)")
    confidence: float = Field(..., description="Confidence score between 0 and 1")

class LegalEntityResponse(BaseModel):
    entities: List[LegalEntity] = Field(default_factory=list, description="List of legal entities found")
    text: str = Field(..., description="Original text")

class BatchLegalEntityResponse(BaseModel):
    results: List[LegalEntityResponse] = Field(default_factory=list, description="List of legal entity results")

# Legal entity recognition for a single text
@router.post("/legal-entities", response_model=LegalEntityResponse, summary="Extract legal entities from text")
async def extract_legal_entities(
    request: LegalEntityRequest,
    analyzer: LegalEntityAnalyzer = Depends(get_legal_entity_analyzer),
    settings: Settings = Depends(get_settings),
    api_key: str = Depends(get_api_key)
):
    """
    Extract legal entities from the given text.

    The API analyzes the input text and identifies legal roles such as:
    - Defendant
    - Plaintiff
    - Representative (lawyer, judge, etc.)

    Returns a list of entities with their names, roles, and confidence scores.

    Requires API key authentication via the X-API-Key header.
    Requires OpenAI API key configuration.
    """
    try:
        # Check if OpenAI API key is configured
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key not configured")
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in the environment variables."
            )

        # Check if model exists and is available in OpenAI's API
        model = settings.OPENAI_MODEL
        if not model:
            logger.error("OpenAI model name not configured")
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI model name not configured. Please set OPENAI_MODEL in the environment variables."
            )

        # Process the request
        logger.info(f"Processing legal entity request with text length: {len(request.text)}")
        entities = analyzer.analyze_legal_entities(request.text)

        if not entities and request.text and len(request.text) > settings.MIN_TEXT_LENGTH:
            logger.warning(f"No entities found in text with length {len(request.text)}")
            # This might indicate an error in processing
            # Check if OpenAI client is initialized properly
            if not analyzer.client:
                logger.error("OpenAI client not initialized correctly")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="OpenAI client not initialized correctly. Please check your API key and model settings."
                )
            else:
                logger.info("OpenAI client is initialized, but no entities were found.")

        # Convert to LegalEntity objects
        entity_objects = []
        for entity in entities:
            try:
                entity_objects.append(LegalEntity(
                    name=entity['name'],
                    role=entity['role'],
                    confidence=entity['confidence']
                ))
            except KeyError as e:
                logger.error(f"Missing field in entity: {e}")
                logger.error(f"Entity data: {entity}")
                # Continue with next entity instead of failing completely
                continue

        return LegalEntityResponse(
            entities=entity_objects,
            text=request.text
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log detailed error and provide generic message to client
        logger.error(f"Error processing text: {type(e).__name__} - {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text: {str(e)}"
        )

# Batch legal entity recognition for multiple texts
@router.post("/legal-entities/batch", response_model=BatchLegalEntityResponse, summary="Extract legal entities from multiple texts")
async def extract_legal_entities_batch(
    request: BatchLegalEntityRequest,
    analyzer: LegalEntityAnalyzer = Depends(get_legal_entity_analyzer),
    settings: Settings = Depends(get_settings),
    api_key: str = Depends(get_api_key)
):
    """
    Extract legal entities from multiple texts in a single request.

    This endpoint is optimized for processing multiple texts at once.

    Each text is analyzed to identify legal roles such as:
    - Defendant
    - Plaintiff
    - Representative (lawyer, judge, etc.)

    Returns a list of results, one for each input text.

    Requires API key authentication via the X-API-Key header.
    Requires OpenAI API key configuration.
    """
    try:
        # Check if OpenAI API key is configured
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key not configured")
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in the environment variables."
            )

        # Check if model exists and is available in OpenAI's API
        model = settings.OPENAI_MODEL
        if not model:
            logger.error("OpenAI model name not configured")
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI model name not configured. Please set OPENAI_MODEL in the environment variables."
            )

        # Process the request
        logger.info(f"Processing batch legal entity request with {len(request.texts)} texts")
        batch_results = analyzer.analyze_legal_entities_batch(request.texts)

        # Convert to response objects
        responses = []
        for i, entities in enumerate(batch_results):
            entity_objects = []
            for entity in entities:
                try:
                    entity_objects.append(LegalEntity(
                        name=entity['name'],
                        role=entity['role'],
                        confidence=entity['confidence']
                    ))
                except KeyError as e:
                    logger.error(f"Missing field in entity: {e}")
                    logger.error(f"Entity data: {entity}")
                    # Continue with next entity instead of failing completely
                    continue

            responses.append(LegalEntityResponse(
                entities=entity_objects,
                text=request.texts[i]
            ))

        return BatchLegalEntityResponse(
            results=responses
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log detailed error and provide generic message to client
        logger.error(f"Error processing batch: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch: {str(e)}"
        )