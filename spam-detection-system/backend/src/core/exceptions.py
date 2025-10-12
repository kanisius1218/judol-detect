"""
Custom exceptions for the spam detection system.
Provides detailed error information and proper HTTP status codes.
"""
from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""
    
    # Authentication & Authorization
    AUTHENTICATION_FAILED = "AUTH_001"
    INVALID_TOKEN = "AUTH_002"
    TOKEN_EXPIRED = "AUTH_003"
    INSUFFICIENT_PERMISSIONS = "AUTH_004"
    API_KEY_INVALID = "AUTH_005"
    
    # Validation
    VALIDATION_ERROR = "VAL_001"
    INVALID_INPUT = "VAL_002"
    MISSING_REQUIRED_FIELD = "VAL_003"
    INVALID_FORMAT = "VAL_004"
    VALUE_OUT_OF_RANGE = "VAL_005"
    
    # Business Logic
    SPAM_DETECTION_FAILED = "BIZ_001"
    MODEL_NOT_AVAILABLE = "BIZ_002"
    PLATFORM_NOT_SUPPORTED = "BIZ_003"
    DELETION_NOT_ALLOWED = "BIZ_004"
    ROLLBACK_WINDOW_EXPIRED = "BIZ_005"
    DUPLICATE_ENTRY = "BIZ_006"
    RESOURCE_NOT_FOUND = "BIZ_007"
    QUOTA_EXCEEDED = "BIZ_008"
    
    # External Services
    PLATFORM_API_ERROR = "EXT_001"
    DATABASE_ERROR = "EXT_002"
    CACHE_ERROR = "EXT_003"
    MESSAGE_QUEUE_ERROR = "EXT_004"
    EMAIL_SERVICE_ERROR = "EXT_005"
    
    # System
    INTERNAL_ERROR = "SYS_001"
    SERVICE_UNAVAILABLE = "SYS_002"
    RATE_LIMIT_EXCEEDED = "SYS_003"
    TIMEOUT_ERROR = "SYS_004"
    CONFIGURATION_ERROR = "SYS_005"


class BaseAPIException(Exception):
    """Base exception class for API errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.headers = headers
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": self.details
            }
        }


# Authentication & Authorization Exceptions
class AuthenticationError(BaseAPIException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            status_code=401,
            details=details,
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidTokenError(BaseAPIException):
    """Raised when token is invalid."""
    
    def __init__(self, message: str = "Invalid token", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_TOKEN,
            status_code=401,
            details=details
        )


class TokenExpiredError(BaseAPIException):
    """Raised when token has expired."""
    
    def __init__(self, message: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.TOKEN_EXPIRED,
            status_code=401,
            details=details
        )


class InsufficientPermissionsError(BaseAPIException):
    """Raised when user lacks required permissions."""
    
    def __init__(
        self,
        required_permission: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not message:
            message = f"Insufficient permissions. Required: {required_permission}"
        
        if not details:
            details = {}
        details["required_permission"] = required_permission
        
        super().__init__(
            message=message,
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            status_code=403,
            details=details
        )


class APIKeyInvalidError(BaseAPIException):
    """Raised when API key is invalid."""
    
    def __init__(self, message: str = "Invalid API key", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.API_KEY_INVALID,
            status_code=401,
            details=details
        )


# Validation Exceptions
class ValidationError(BaseAPIException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Validation error",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=details
        )


class InvalidInputError(BaseAPIException):
    """Raised when input is invalid."""
    
    def __init__(
        self,
        message: str = "Invalid input",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            details=details
        )


# Business Logic Exceptions
class SpamDetectionError(BaseAPIException):
    """Raised when spam detection fails."""
    
    def __init__(
        self,
        message: str = "Spam detection failed",
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if reason:
            details["reason"] = reason
        
        super().__init__(
            message=message,
            error_code=ErrorCode.SPAM_DETECTION_FAILED,
            status_code=500,
            details=details
        )


class ModelNotAvailableError(BaseAPIException):
    """Raised when ML model is not available."""
    
    def __init__(
        self,
        message: str = "ML model is not available",
        model_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if model_name:
            details["model_name"] = model_name
        
        super().__init__(
            message=message,
            error_code=ErrorCode.MODEL_NOT_AVAILABLE,
            status_code=503,
            details=details
        )


class PlatformNotSupportedError(BaseAPIException):
    """Raised when platform is not supported."""
    
    def __init__(
        self,
        platform: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not message:
            message = f"Platform '{platform}' is not supported"
        
        if not details:
            details = {}
        details["platform"] = platform
        details["supported_platforms"] = ["youtube", "instagram", "tiktok"]
        
        super().__init__(
            message=message,
            error_code=ErrorCode.PLATFORM_NOT_SUPPORTED,
            status_code=400,
            details=details
        )


class DeletionNotAllowedError(BaseAPIException):
    """Raised when deletion is not allowed."""
    
    def __init__(
        self,
        message: str = "Deletion not allowed",
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if reason:
            details["reason"] = reason
        
        super().__init__(
            message=message,
            error_code=ErrorCode.DELETION_NOT_ALLOWED,
            status_code=403,
            details=details
        )


class RollbackWindowExpiredError(BaseAPIException):
    """Raised when rollback window has expired."""
    
    def __init__(
        self,
        message: str = "Rollback window has expired",
        expired_hours: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if expired_hours:
            details["window_hours"] = expired_hours
        
        super().__init__(
            message=message,
            error_code=ErrorCode.ROLLBACK_WINDOW_EXPIRED,
            status_code=400,
            details=details
        )


class ResourceNotFoundError(BaseAPIException):
    """Raised when resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not message:
            message = f"{resource_type} with ID '{resource_id}' not found"
        
        if not details:
            details = {}
        details["resource_type"] = resource_type
        details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details=details
        )


class QuotaExceededError(BaseAPIException):
    """Raised when quota is exceeded."""
    
    def __init__(
        self,
        message: str = "Quota exceeded",
        quota_type: Optional[str] = None,
        limit: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if quota_type:
            details["quota_type"] = quota_type
        if limit:
            details["limit"] = limit
        
        super().__init__(
            message=message,
            error_code=ErrorCode.QUOTA_EXCEEDED,
            status_code=429,
            details=details
        )


# External Service Exceptions
class PlatformAPIError(BaseAPIException):
    """Raised when platform API call fails."""
    
    def __init__(
        self,
        platform: str,
        message: str = "Platform API error",
        api_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        details["platform"] = platform
        if api_error:
            details["api_error"] = api_error
        
        super().__init__(
            message=message,
            error_code=ErrorCode.PLATFORM_API_ERROR,
            status_code=502,
            details=details
        )


class DatabaseError(BaseAPIException):
    """Raised when database operation fails."""
    
    def __init__(
        self,
        message: str = "Database error",
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details=details
        )


# System Exceptions
class RateLimitExceededError(BaseAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        if not details:
            details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details,
            headers=headers
        )


class ServiceUnavailableError(BaseAPIException):
    """Raised when service is unavailable."""
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if service_name:
            details["service"] = service_name
        
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
            details=details
        )


class TimeoutError(BaseAPIException):
    """Raised when operation times out."""
    
    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not details:
            details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        
        super().__init__(
            message=message,
            error_code=ErrorCode.TIMEOUT_ERROR,
            status_code=504,
            details=details
        )
