"""Rate limiting module."""

from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

from ..logging_config import get_logger

logger = get_logger(__name__)


def get_identifier():
    """Get identifier untuk rate limiting (API key atau IP)."""
    # Prioritas: API key > User ID > IP address
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return f"key:{api_key[:16]}"
    
    user_id = getattr(request, 'user_id', None)
    if user_id:
        return f"user:{user_id}"
    
    # Fallback ke IP address
    return get_remote_address()


def setup_rate_limiting(app: Flask, redis_url: str = None) -> Limiter:
    """
    Setup rate limiting untuk Flask app.
    
    Args:
        app: Flask application
        redis_url: Redis URL untuk storage
        
    Returns:
        Limiter instance
    """
    # Determine storage backend
    if redis_url:
        storage_uri = redis_url
    else:
        storage_uri = "memory://"
        logger.warning("Using in-memory rate limiting (not recommended for production)")
    
    # Create limiter
    limiter = Limiter(
        app=app,
        key_func=get_identifier,
        storage_uri=storage_uri,
        default_limits=["1000 per day", "100 per hour"],
        headers_enabled=True,
        swallow_errors=True,  # Don't crash if Redis is down
        strategy="fixed-window-elastic-expiry"
    )
    
    # Custom error handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        logger.warning("Rate limit exceeded",
                      extra={'identifier': get_identifier(),
                            'endpoint': request.endpoint})
        return {
            'error': 'rate_limit_exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': e.description
        }, 429
    
    logger.info("Rate limiting configured", 
               extra={'storage': 'redis' if redis_url else 'memory'})
    
    return limiter
