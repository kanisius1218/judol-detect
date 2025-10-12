"""Centralized logging configuration dengan structured logging."""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path
import traceback


class StructuredFormatter(logging.Formatter):
    """Custom formatter untuk structured logging (JSON format)."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add request context if available
        try:
            from flask import has_request_context, request
            if has_request_context():
                log_data['request'] = {
                    'method': request.method,
                    'path': request.path,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                }
                if hasattr(request, 'user_id'):
                    log_data['user_id'] = request.user_id
        except:
            pass
        
        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter untuk development."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record dengan colors."""
        # Get color for level
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build message
        parts = [
            f"{color}{record.levelname:8s}{reset}",
            f"{timestamp}",
            f"{record.name}:{record.lineno}",
            f"- {record.getMessage()}"
        ]
        
        message = " | ".join(parts)
        
        # Add exception if present
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        
        return message


class ContextFilter(logging.Filter):
    """Filter untuk add context information to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to record."""
        # Add hostname
        import socket
        record.hostname = socket.gethostname()
        
        # Add process info
        import os
        record.pid = os.getpid()
        
        return True


def setup_logging(app_name: str = 'spam-detector',
                 log_level: str = 'INFO',
                 log_file: str = None,
                 json_format: bool = False) -> logging.Logger:
    """
    Setup centralized logging configuration.
    
    Args:
        app_name: Application name
        log_level: Logging level
        log_file: Log file path (optional)
        json_format: Use JSON format (for production)
        
    Returns:
        Configured root logger
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Choose formatter
    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = HumanReadableFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ContextFilter())
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(StructuredFormatter())  # Always JSON for file
        file_handler.addFilter(ContextFilter())
        root_logger.addHandler(file_handler)
    
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    root_logger.info(f"Logging configured for {app_name}",
                    extra={'app_name': app_name, 'log_level': log_level})
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Adapter untuk add default context to all log messages."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log message."""
        # Get extra dict
        extra = kwargs.get('extra', {})
        
        # Merge with adapter's extra
        extra.update(self.extra)
        
        kwargs['extra'] = extra
        return msg, kwargs


# ============================================================================
# SENTRY INTEGRATION (Optional)
# ============================================================================

def setup_sentry(dsn: str, environment: str = 'production',
                release: str = None, traces_sample_rate: float = 0.1):
    """
    Setup Sentry error tracking.
    
    Args:
        dsn: Sentry DSN
        environment: Environment name
        release: Release version
        traces_sample_rate: APM sampling rate
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate,
            integrations=[
                FlaskIntegration(),
                RedisIntegration(),
                SqlalchemyIntegration()
            ],
            # Filter sensitive data
            before_send=filter_sensitive_data,
            # Performance monitoring
            profiles_sample_rate=0.1,
        )
        
        logging.info("Sentry initialized", 
                    extra={'environment': environment, 
                          'release': release})
    
    except ImportError:
        logging.warning("Sentry SDK not installed. Error tracking disabled.")
    except Exception as e:
        logging.error(f"Failed to initialize Sentry: {e}")


def filter_sensitive_data(event: Dict, hint: Dict) -> Dict:
    """Filter sensitive data from Sentry events."""
    # Remove API keys from headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        for key in ['X-API-Key', 'Authorization', 'Cookie']:
            if key in headers:
                headers[key] = '[FILTERED]'
    
    # Remove sensitive query params
    if 'request' in event and 'query_string' in event['request']:
        # Filter query string if needed
        pass
    
    return event


# ============================================================================
# PERFORMANCE LOGGING
# ============================================================================

import time
from functools import wraps


def log_performance(threshold_ms: float = 1000):
    """
    Decorator untuk log slow operations.
    
    Args:
        threshold_ms: Log if operation takes longer than this (milliseconds)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"Slow operation: {func.__name__}",
                        extra={
                            'function': func.__name__,
                            'duration_ms': round(duration_ms, 2),
                            'threshold_ms': threshold_ms
                        }
                    )
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'duration_ms': round(duration_ms, 2),
                        'error': str(e)
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    
    return decorator
