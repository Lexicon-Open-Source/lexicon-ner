import logging
from fastapi import Security, HTTPException, Depends, status
from fastapi.security.api_key import APIKeyHeader

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

# API Key header definition
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key_header: str = Security(api_key_header),
    settings: Settings = Depends(get_settings)
) -> str:
    """
    Validate the API key.

    This function is used as a dependency in FastAPI endpoints to secure
    them with API key authentication.
    """
    # If API key is not required, skip validation
    if not settings.REQUIRE_API_KEY:
        return None

    # If API key is required but not provided
    if api_key_header is None:
        logger.warning("API key missing in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing. Please provide a valid API key using the X-API-Key header."
        )

    # Validate API key
    if api_key_header != settings.API_KEY:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key. Please provide a valid API key."
        )

    return api_key_header