import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
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
            raise HTTPException(
                status_code=501,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in the environment variables."
            )

        # Process the request
        entities = analyzer.analyze_legal_entities(request.text)

        # Convert to LegalEntity objects
        entity_objects = []
        for entity in entities:
            entity_objects.append(LegalEntity(
                name=entity['name'],
                role=entity['role'],
                confidence=entity['confidence']
            ))

        return LegalEntityResponse(
            entities=entity_objects,
            text=request.text
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

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
            raise HTTPException(
                status_code=501,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in the environment variables."
            )

        # Process the request
        batch_results = analyzer.analyze_legal_entities_batch(request.texts)

        # Convert to response objects
        responses = []
        for i, entities in enumerate(batch_results):
            entity_objects = []
            for entity in entities:
                entity_objects.append(LegalEntity(
                    name=entity['name'],
                    role=entity['role'],
                    confidence=entity['confidence']
                ))

            responses.append(LegalEntityResponse(
                entities=entity_objects,
                text=request.texts[i]
            ))

        return BatchLegalEntityResponse(
            results=responses
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")