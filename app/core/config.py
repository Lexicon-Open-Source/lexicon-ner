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
    API_KEY: str = os.getenv("API_KEY", "lexicon-ner-default-key")
    REQUIRE_API_KEY: bool = os.getenv("REQUIRE_API_KEY", "1") == "1"

    # Flair settings
    USE_CUDA: bool = os.getenv("USE_CUDA", "0") == "1"
    MIN_TEXT_LENGTH: int = 3

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))

    class Config:
        case_sensitive = True


# Get global settings
def get_settings() -> Settings:
    """Return the settings instance."""
    return Settings()