"""Custom exception hierarchy untuk aplikasi."""

from typing import Optional, Dict, Any


class SpamDetectorError(Exception):
    """Base exception untuk semua custom errors."""
    
    error_code: str = "UNKNOWN_ERROR"
    status_code: int = 500
    message: str = "An unexpected error occurred"
    
    def __init__(self, message: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to JSON-serializable dict."""
        result = {
            'error': self.error_code,
            'message': self.message,
            'status_code': self.status_code
        }
        if self.details:
            result['details'] = self.details
        return result


# ============================================================================
# AUTHENTICATION & AUTHORIZATION ERRORS
# ============================================================================

class AuthenticationError(SpamDetectorError):
    """Authentication failed."""
    error_code = "AUTH_001"
    status_code = 401
    message = "Authentication failed"


class AuthorizationError(SpamDetectorError):
    """Authorization failed."""
    error_code = "AUTH_002"
    status_code = 403
    message = "Access denied"


class InvalidAPIKeyError(AuthenticationError):
    """Invalid API key provided."""
    error_code = "AUTH_003"
    message = "Invalid API key"


class APIKeyExpiredError(AuthenticationError):
    """API key has expired."""
    error_code = "AUTH_004"
    message = "API key has expired"


class RateLimitExceededError(AuthorizationError):
    """Rate limit exceeded."""
    error_code = "AUTH_005"
    status_code = 429
    message = "Rate limit exceeded"


# ============================================================================
# VALIDATION ERRORS
# ============================================================================

class ValidationError(SpamDetectorError):
    """Input validation failed."""
    error_code = "VAL_001"
    status_code = 400
    message = "Validation failed"


class InvalidInputError(ValidationError):
    """Invalid input format."""
    error_code = "VAL_002"
    message = "Invalid input format"


class MissingFieldError(ValidationError):
    """Required field missing."""
    error_code = "VAL_003"
    message = "Required field missing"


class InvalidFieldValueError(ValidationError):
    """Invalid field value."""
    error_code = "VAL_004"
    message = "Invalid field value"


# ============================================================================
# MODEL ERRORS
# ============================================================================

class ModelError(SpamDetectorError):
    """Model-related errors."""
    error_code = "MODEL_001"
    status_code = 500
    message = "Model error occurred"


class ModelNotLoadedError(ModelError):
    """Model not loaded."""
    error_code = "MODEL_002"
    status_code = 503
    message = "Model not loaded"


class ModelPredictionError(ModelError):
    """Model prediction failed."""
    error_code = "MODEL_003"
    message = "Model prediction failed"


class ModelVersionError(ModelError):
    """Invalid model version."""
    error_code = "MODEL_004"
    message = "Invalid model version"


# ============================================================================
# DATABASE ERRORS
# ============================================================================

class DatabaseError(SpamDetectorError):
    """Database operation failed."""
    error_code = "DB_001"
    status_code = 500
    message = "Database error occurred"


class DatabaseConnectionError(DatabaseError):
    """Database connection failed."""
    error_code = "DB_002"
    message = "Database connection failed"


class DatabaseQueryError(DatabaseError):
    """Database query failed."""
    error_code = "DB_003"
    message = "Database query failed"


class RecordNotFoundError(DatabaseError):
    """Database record not found."""
    error_code = "DB_004"
    status_code = 404
    message = "Record not found"


# ============================================================================
# EXTERNAL API ERRORS
# ============================================================================

class ExternalAPIError(SpamDetectorError):
    """External API call failed."""
    error_code = "EXT_001"
    status_code = 502
    message = "External API error"


class YouTubeAPIError(ExternalAPIError):
    """YouTube API error."""
    error_code = "EXT_002"
    message = "YouTube API error"


class InstagramAPIError(ExternalAPIError):
    """Instagram API error."""
    error_code = "EXT_003"
    message = "Instagram API error"


# ============================================================================
# CACHE ERRORS
# ============================================================================

class CacheError(SpamDetectorError):
    """Cache operation failed."""
    error_code = "CACHE_001"
    status_code = 500
    message = "Cache error occurred"


class CacheConnectionError(CacheError):
    """Cache connection failed."""
    error_code = "CACHE_002"
    message = "Cache connection failed"


# ============================================================================
# CONFIGURATION ERRORS
# ============================================================================

class ConfigurationError(SpamDetectorError):
    """Configuration error."""
    error_code = "CONFIG_001"
    status_code = 500
    message = "Configuration error"


class MissingConfigError(ConfigurationError):
    """Missing required configuration."""
    error_code = "CONFIG_002"
    message = "Missing required configuration"


class InvalidConfigError(ConfigurationError):
    """Invalid configuration value."""
    error_code = "CONFIG_003"
    message = "Invalid configuration value"


# ============================================================================
# RESOURCE ERRORS
# ============================================================================

class ResourceNotFoundError(SpamDetectorError):
    """Resource not found."""
    error_code = "RES_001"
    status_code = 404
    message = "Resource not found"


class ResourceUnavailableError(SpamDetectorError):
    """Resource unavailable."""
    error_code = "RES_002"
    status_code = 503
    message = "Resource temporarily unavailable"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_exception_class(error_code: str) -> Optional[type]:
    """Get exception class by error code."""
    for cls in SpamDetectorError.__subclasses__():
        if hasattr(cls, 'error_code') and cls.error_code == error_code:
            return cls
        # Check nested subclasses
        for subcls in cls.__subclasses__():
            if hasattr(subcls, 'error_code') and subcls.error_code == error_code:
                return subcls
    return None
