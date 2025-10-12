"""Core module for configuration, security, logging, and exceptions."""

from .config import settings, get_settings
from .security import (
    SecurityUtils,
    RateLimiter,
    Permission,
    Role,
    check_permission,
    TokenData
)
from .logging import (
    logger,
    audit_logger,
    LoggerFactory,
    ErrorLogger,
    set_correlation_id,
    get_correlation_id
)
from .exceptions import (
    BaseAPIException,
    AuthenticationError,
    ValidationError,
    SpamDetectionError,
    ResourceNotFoundError,
    RateLimitExceededError,
    ErrorCode
)

__all__ = [
    # Config
    "settings",
    "get_settings",
    # Security
    "SecurityUtils",
    "RateLimiter",
    "Permission",
    "Role",
    "check_permission",
    "TokenData",
    # Logging
    "logger",
    "audit_logger",
    "LoggerFactory",
    "ErrorLogger",
    "set_correlation_id",
    "get_correlation_id",
    # Exceptions
    "BaseAPIException",
    "AuthenticationError",
    "ValidationError",
    "SpamDetectionError",
    "ResourceNotFoundError",
    "RateLimitExceededError",
    "ErrorCode"
]
