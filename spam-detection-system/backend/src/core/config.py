"""
Core configuration management using Pydantic Settings.
Production-ready with environment variable validation.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator, SecretStr
from functools import lru_cache
import secrets
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with validation and type checking."""
    
    # Application
    APP_NAME: str = "Spam Detection System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="production", regex="^(development|staging|production)$")
    
    # API
    API_V1_STR: str = "/api/v1"
    API_KEY_HEADER: str = "X-API-Key"
    
    # Security
    SECRET_KEY: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))
    JWT_SECRET_KEY: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12
    BCRYPT_ROUNDS: int = 12
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(default_factory=list)
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and v:
            return [i.strip() for i in v.split(",")]
        return v
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/spam_detection"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False
    
    # Redis Cache
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[SecretStr] = None
    REDIS_POOL_MIN_SIZE: int = 10
    REDIS_POOL_MAX_SIZE: int = 20
    CACHE_TTL_SECONDS: int = 3600
    
    # RabbitMQ / Celery
    CELERY_BROKER_URL: str = Field(default="amqp://guest:guest@localhost:5672//")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1")
    CELERY_TASK_ALWAYS_EAGER: bool = False
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 1000
    RATE_LIMIT_BURST_SIZE: int = 10
    
    # ML Model
    MODEL_PATH: Path = Field(default=Path("models/spam_detector.pkl"))
    MODEL_VERSION: str = "1.0.0"
    MODEL_CONFIDENCE_THRESHOLD: float = 0.85
    MODEL_MAX_INPUT_LENGTH: int = 10000
    FEATURE_EXTRACTION_TIMEOUT: int = 5
    
    # Auto-Deletion Settings
    AUTO_DELETE_ENABLED: bool = True
    AUTO_DELETE_CONFIDENCE_THRESHOLD: float = 0.95
    AUTO_DELETE_BATCH_SIZE: int = 100
    AUTO_DELETE_DELAY_SECONDS: int = 30  # Grace period before deletion
    AUTO_DELETE_MAX_RETRIES: int = 3
    ROLLBACK_WINDOW_HOURS: int = 24
    
    # Platform API Keys (Encrypted in production)
    YOUTUBE_API_KEY: Optional[SecretStr] = None
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[SecretStr] = None
    
    INSTAGRAM_CLIENT_ID: Optional[str] = None
    INSTAGRAM_CLIENT_SECRET: Optional[SecretStr] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[SecretStr] = None
    
    TIKTOK_CLIENT_ID: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[SecretStr] = None
    
    # Monitoring & Logging
    LOG_LEVEL: str = Field(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: Optional[Path] = Field(default=Path("logs/app.log"))
    LOG_ROTATION: str = "100 MB"
    LOG_RETENTION: str = "30 days"
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    
    # Email Notifications
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[SecretStr] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "noreply@spamdetection.com"
    EMAIL_ADMIN: List[str] = Field(default_factory=list)
    
    # Webhook Settings
    WEBHOOK_ENABLED: bool = True
    WEBHOOK_RETRY_COUNT: int = 3
    WEBHOOK_TIMEOUT_SECONDS: int = 10
    
    # Feature Flags
    FEATURE_FLAGS: Dict[str, bool] = Field(default_factory=lambda: {
        "batch_processing": True,
        "real_time_analytics": True,
        "auto_training": False,
        "advanced_filters": True,
        "export_reports": True,
    })
    
    # Testing
    TESTING: bool = False
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
    @validator("LOG_FILE_PATH", pre=True)
    def create_log_directory(cls, v: Optional[Path]) -> Optional[Path]:
        if v:
            v = Path(v)
            v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("MODEL_PATH", pre=True)
    def validate_model_path(cls, v: Path) -> Path:
        v = Path(v)
        if not v.parent.exists():
            v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get configuration for specific platform."""
        platform = platform.lower()
        if platform == "youtube":
            return {
                "api_key": self.YOUTUBE_API_KEY,
                "client_id": self.YOUTUBE_CLIENT_ID,
                "client_secret": self.YOUTUBE_CLIENT_SECRET,
            }
        elif platform == "instagram":
            return {
                "client_id": self.INSTAGRAM_CLIENT_ID,
                "client_secret": self.INSTAGRAM_CLIENT_SECRET,
                "access_token": self.INSTAGRAM_ACCESS_TOKEN,
            }
        elif platform == "tiktok":
            return {
                "client_id": self.TIKTOK_CLIENT_ID,
                "client_secret": self.TIKTOK_CLIENT_SECRET,
            }
        return {}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export singleton
settings = get_settings()
