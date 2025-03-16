import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.model_loader import ModelLoader, get_model_loader
from app.core.security import get_api_key

logger = logging.getLogger(__name__)

# Router for NER endpoints
router = APIRouter()

# Model for single text NER request
class NERRequest(BaseModel):
    text: str = Field(...,
                      description="The text to analyze for named entities",
                      min_length=1,
                      example="Presiden Joko Widodo mengunjungi Jakarta untuk bertemu dengan Menteri Anies Baswedan.")

# Model for batch NER request
class BatchNERRequest(BaseModel):
    texts: List[str] = Field(...,
                            description="List of texts to analyze for named entities",
                            min_items=1,
                            max_items=100)

# Model for NER response
class Entity(BaseModel):
    text: str = Field(..., description="The entity text")
    type: str = Field(..., description="The entity type (e.g., PER, LOC, ORG)")
    start_pos: int = Field(..., description="Start position in the text")
    end_pos: int = Field(..., description="End position in the text")
    confidence: float = Field(..., description="Confidence score between 0 and 1")

class NERResponse(BaseModel):
    entities: List[Entity] = Field(default_factory=list, description="List of named entities found")
    text: str = Field(..., description="Original text")

class BatchNERResponse(BaseModel):
    results: List[NERResponse] = Field(default_factory=list, description="List of NER results")

# NER for a single text
@router.post("/ner", response_model=NERResponse, summary="Extract named entities from text")
async def extract_entities(
    request: NERRequest,
    model_loader: ModelLoader = Depends(get_model_loader),
    settings: Settings = Depends(get_settings),
    api_key: str = Depends(get_api_key)
):
    """
    Extract named entities from the given text.

    The API analyzes the input text and identifies named entities such as:
    - PER (Person)
    - LOC (Location)
    - ORG (Organization)

    Returns a list of entities with their types, positions, and confidence scores.

    Requires API key authentication via the X-API-Key header.
    """
    try:
        # Process the request
        entities = model_loader.predict(request.text)

        # Convert to Entity objects
        entity_objects = []
        for entity in entities:
            entity_objects.append(Entity(
                text=entity['text'],
                type=entity['type'],
                start_pos=entity['start_pos'],
                end_pos=entity['end_pos'],
                confidence=entity['confidence']
            ))

        return NERResponse(
            entities=entity_objects,
            text=request.text
        )
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

# Batch NER for multiple texts
@router.post("/ner/batch", response_model=BatchNERResponse, summary="Extract named entities from multiple texts")
async def extract_entities_batch(
    request: BatchNERRequest,
    model_loader: ModelLoader = Depends(get_model_loader),
    settings: Settings = Depends(get_settings),
    api_key: str = Depends(get_api_key)
):
    """
    Extract named entities from multiple texts in a single request.

    This endpoint is optimized for processing multiple texts at once, which can
    be significantly faster than making multiple individual requests.

    Returns a list of NER results, one for each input text.

    Requires API key authentication via the X-API-Key header.
    """
    try:
        # Process the request
        batch_results = model_loader.predict_batch(request.texts)

        # Convert to response objects
        responses = []
        for i, entities in enumerate(batch_results):
            entity_objects = []
            for entity in entities:
                entity_objects.append(Entity(
                    text=entity['text'],
                    type=entity['type'],
                    start_pos=entity['start_pos'],
                    end_pos=entity['end_pos'],
                    confidence=entity['confidence']
                ))

            responses.append(NERResponse(
                entities=entity_objects,
                text=request.texts[i]
            ))

        return BatchNERResponse(
            results=responses
        )
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")