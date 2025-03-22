import os
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.api.endpoints import  legal
from app.core.config import Settings, get_settings
from app.core.security import get_api_key

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Lexicon Legal Entity Recognition API",
    description="API for Indonesian Legal Entity Recognition using ChatGPT API.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(legal.router, prefix="/api", tags=["legal"])

# Health check endpoint
@app.get("/api/health", tags=["health"])
async def health_check(
    api_key: str = Depends(get_api_key)
):
    """
    Check if the service is healthy and model is loaded.

    Requires API key authentication via the X-API-Key header when API key security is enabled.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "version": "1.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Preload the model on startup for faster inference."""
    logger.info("Starting up the Legal Entity Recognition service")
    try:
        # Check OpenAI configuration
        settings = get_settings()
        if settings.OPENAI_API_KEY:
            logger.info(f"OpenAI API key configured. Using model: {settings.OPENAI_MODEL}")
        else:
            logger.warning("OpenAI API key not configured. Legal entity analysis will not be available.")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # We'll continue and try to load the model on the first request

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    logger.info("Shutting down the NER service")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)