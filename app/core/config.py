import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # Model settings
    MODEL_PATH: str = os.getenv("MODEL_PATH", "/app/models/indonesian-ner-model")
    TOKENIZER_PATH: str = os.getenv("TOKENIZER_PATH", "/app/models/tokenizer")

    # Performance settings
    CACHE_SIZE: int = int(os.getenv("CACHE_SIZE", "1000"))
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "32"))

    # Server settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Flair settings
    USE_CUDA: bool = os.getenv("USE_CUDA", "0") == "1"
    MIN_TEXT_LENGTH: int = 3

    class Config:
        case_sensitive = True


# Get global settings
def get_settings() -> Settings:
    """Return the settings instance."""
    return Settings()