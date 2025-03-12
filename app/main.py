import os
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import ner
from app.core.config import Settings
from app.core.model_loader import ModelLoader, get_model_loader

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Lexicon Named Entity Recognition API",
    description="API for Indonesian Named Entity Recognition using Flair NLP",
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
app.include_router(ner.router, prefix="/api", tags=["ner"])

# Health check endpoint
@app.get("/api/health", tags=["health"])
async def health_check(model_loader: ModelLoader = Depends(get_model_loader)):
    """Check if the service is healthy and model is loaded."""
    return {
        "status": "ok",
        "model_loaded": model_loader.is_model_loaded(),
        "version": "1.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Preload the model on startup for faster inference."""
    logger.info("Starting up the NER service")
    try:
        # Preload model for faster inference
        model_loader = get_model_loader()
        model_loader.load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        # We'll continue and try to load the model on the first request

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    logger.info("Shutting down the NER service")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)