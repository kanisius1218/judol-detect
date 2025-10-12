"""
Structured logging configuration with JSON output, rotation, and monitoring integration.
Implements correlation IDs, performance tracking, and sensitive data masking.
"""
import logging
import sys
import json
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
import traceback
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from contextvars import ContextVar
import uuid
from pythonjsonlogger import jsonlogger
from .config import settings
from .security import SecurityUtils


# Context variable for request correlation
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class SecurityFilter(logging.Filter):
    """Filter to mask sensitive data in logs."""
    
    SENSITIVE_FIELDS = [
        'password', 'token', 'api_key', 'secret', 'authorization',
        'credit_card', 'ssn', 'email', 'phone', 'ip_address'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Mask sensitive data in log records."""
        # Check message
        if hasattr(record, 'msg'):
            record.msg = self._mask_sensitive(str(record.msg))
        
        # Check extra fields
        for field in self.SENSITIVE_FIELDS:
            if hasattr(record, field):
                value = getattr(record, field)
                if value:
                    setattr(record, field, SecurityUtils.mask_sensitive_data(str(value)))
        
        return True
    
    def _mask_sensitive(self, text: str) -> str:
        """Mask sensitive patterns in text."""
        import re
        
        # Mask email addresses
        text = re.sub(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            lambda m: SecurityUtils.mask_sensitive_data(m.group()),
            text
        )
        
        # Mask JWT tokens
        text = re.sub(
            r'Bearer\s+[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
            'Bearer [MASKED]',
            text
        )
        
        # Mask API keys (common patterns)
        text = re.sub(
            r'([Aa]pi[_-]?[Kk]ey|[Aa]uth|[Tt]oken)["\']?\s*[:=]\s*["\']?([A-Za-z0-9-_]{20,})["\']?',
            r'\1: [MASKED]',
            text
        )
        
        return text


class ContextFilter(logging.Filter):
    """Add context information to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID and other context to records."""
        # Add correlation ID
        record.correlation_id = correlation_id_var.get() or "system"
        
        # Add timestamp in ISO format
        record.timestamp = datetime.utcnow().isoformat()
        
        # Add environment
        record.environment = settings.ENVIRONMENT
        
        # Add app info
        record.app_name = settings.APP_NAME
        record.app_version = settings.APP_VERSION
        
        # Add hostname (useful for distributed systems)
        import socket
        record.hostname = socket.gethostname()
        
        return True


class PerformanceFilter(logging.Filter):
    """Add performance metrics to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add memory and timing information."""
        import psutil
        import os
        
        # Memory usage
        process = psutil.Process(os.getpid())
        record.memory_mb = process.memory_info().rss / 1024 / 1024
        record.cpu_percent = process.cpu_percent()
        
        return True


class ErrorLogger:
    """Enhanced error logging with stack traces and context."""
    
    @staticmethod
    def log_exception(
        logger: logging.Logger,
        exc: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """Log an exception with full context."""
        error_id = str(uuid.uuid4())
        
        error_data = {
            "error_id": error_id,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "stack_trace": traceback.format_exc(),
            "context": context or {},
            "user_id": user_id
        }
        
        # Log to file
        logger.error(
            f"Exception occurred: {error_id}",
            extra=error_data,
            exc_info=True
        )
        
        # Send to monitoring service (e.g., Sentry) if configured
        if settings.SENTRY_DSN:
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(exc, extra=error_data)
            except ImportError:
                pass
        
        return error_id


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Ensure consistent field names
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add thread information for debugging
        log_record['thread'] = record.thread
        log_record['thread_name'] = record.threadName
        
        # Add process information
        log_record['process'] = record.process
        log_record['process_name'] = record.processName
        
        # Remove redundant fields
        for field in ['levelname', 'funcName', 'lineno', 'module', 'name']:
            log_record.pop(field, None)


def setup_logging() -> logging.Logger:
    """
    Set up structured logging with proper handlers and formatters.
    Returns the root logger.
    """
    # Create logs directory if it doesn't exist
    if settings.LOG_FILE_PATH:
        log_dir = settings.LOG_FILE_PATH.parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            timestamp=True
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SecurityFilter())
    console_handler.addFilter(ContextFilter())
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if settings.LOG_FILE_PATH:
        file_handler = RotatingFileHandler(
            settings.LOG_FILE_PATH,
            maxBytes=100 * 1024 * 1024,  # 100 MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SecurityFilter())
        file_handler.addFilter(ContextFilter())
        file_handler.addFilter(PerformanceFilter())
        root_logger.addHandler(file_handler)
    
    # Add Sentry handler if configured
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration
            
            sentry_logging = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
            
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[sentry_logging],
                traces_sample_rate=0.1,
                environment=settings.ENVIRONMENT
            )
        except ImportError:
            root_logger.warning("Sentry SDK not installed, skipping Sentry integration")
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return root_logger


class LoggerFactory:
    """Factory for creating named loggers with consistent configuration."""
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger with the given name."""
        logger = logging.getLogger(name)
        
        # Ensure filters are applied
        for handler in logger.handlers:
            if not any(isinstance(f, SecurityFilter) for f in handler.filters):
                handler.addFilter(SecurityFilter())
            if not any(isinstance(f, ContextFilter) for f in handler.filters):
                handler.addFilter(ContextFilter())
        
        return logger


class AuditLogger:
    """Special logger for audit trail."""
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("audit")
        
        # Add special handler for audit logs (separate file)
        audit_file = Path("logs/audit.log")
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        audit_handler = RotatingFileHandler(
            audit_file,
            maxBytes=50 * 1024 * 1024,  # 50 MB
            backupCount=20  # Keep more audit logs
        )
        
        audit_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(message)s',
            timestamp=True
        )
        audit_handler.setFormatter(audit_formatter)
        
        self.logger.addHandler(audit_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_action(
        self,
        action: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ):
        """Log an auditable action."""
        audit_entry = {
            "action": action,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(
            f"AUDIT: {action} on {resource_type}/{resource_id}",
            extra=audit_entry
        )
    
    def log_deletion(
        self,
        platform: str,
        content_id: str,
        user_id: str,
        reason: str,
        confidence_score: float,
        rollback_token: str
    ):
        """Log a deletion action with rollback information."""
        self.log_action(
            action="DELETE_SPAM",
            user_id=user_id,
            resource_type=f"{platform}_comment",
            resource_id=content_id,
            details={
                "reason": reason,
                "confidence_score": confidence_score,
                "rollback_token": rollback_token,
                "platform": platform
            }
        )
    
    def log_rollback(
        self,
        platform: str,
        content_id: str,
        user_id: str,
        rollback_token: str
    ):
        """Log a rollback action."""
        self.log_action(
            action="ROLLBACK_DELETION",
            user_id=user_id,
            resource_type=f"{platform}_comment",
            resource_id=content_id,
            details={
                "rollback_token": rollback_token,
                "platform": platform
            }
        )


# Initialize loggers
logger = setup_logging()
audit_logger = AuditLogger()


# Utility functions
def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for the current context."""
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()
