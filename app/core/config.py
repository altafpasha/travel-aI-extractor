from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application Settings managed via environment variables and .env file."""
    
    PROJECT_NAME: str = "Travel AI Extractor"
    API_V1_STR: str = ""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API Security Key
    API_KEY: str = "travel_sec_key_892374918237"

    # API Keys
    GEMINI_API_KEY: str = ""
    GOOGLE_PLACES_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Database & Redis
    DATABASE_URL: str = "sqlite+aiosqlite:///./travel_extractor.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "travel_ai_extractor"

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    @property
    def async_database_url(self) -> str:
        """Returns configured async database URL, defaulting to DATABASE_URL if explicitly specified."""
        if self.DATABASE_URL and not self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
