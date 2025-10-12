"""Application configuration management."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    environment: str = Field("development", env="ENVIRONMENT")
    api_debug: bool = Field(False, env="API_DEBUG")
    api_allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    database_url: str = Field("sqlite:///./spam.db", env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    model_storage_path: Path = Field(Path("./ml_models"), env="MODEL_STORAGE_PATH")
    model_default_version: str = Field("v1", env="MODEL_DEFAULT_VERSION")

    celery_broker_url: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_backend_url: str = Field("redis://localhost:6379/1", env="CELERY_BACKEND_URL")

    secret_key: str = Field("insecure", env="SECRET_KEY")
    api_key_salt: str = Field("salt", env="API_KEY_SALT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
