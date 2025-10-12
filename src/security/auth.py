"""Authentication dan authorization module."""

import secrets
import hashlib
import hmac
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Callable
import redis
from datetime import datetime, timedelta

from ..exceptions import AuthenticationError, AuthorizationError
from ..logging_config import get_logger

logger = get_logger(__name__)


class APIKeyManager:
    """Manager untuk API key authentication."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.key_prefix = "apikey:"
        
    def create_api_key(self, user_id: str, name: str = "", 
                       rate_limit: int = 1000) -> str:
        """
        Generate API key baru.
        
        Args:
            user_id: User ID
            name: Nama deskriptif untuk key
            rate_limit: Request limit per hour
            
        Returns:
            API key string
        """
        # Generate secure random key
        api_key = f"sk_{secrets.token_urlsafe(32)}"
        
        # Hash key untuk storage
        key_hash = self._hash_key(api_key)
        
        # Store metadata di Redis
        metadata = {
            'user_id': user_id,
            'name': name,
            'rate_limit': rate_limit,
            'created_at': datetime.utcnow().isoformat(),
            'last_used': '',
            'total_requests': 0
        }
        
        self.redis.hmset(f"{self.key_prefix}{key_hash}", metadata)
        
        logger.info(f"API key created for user {user_id}", 
                   extra={'user_id': user_id, 'key_name': name})
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[dict]:
        """
        Verify API key dan return metadata.
        
        Args:
            api_key: API key string
            
        Returns:
            Metadata dict jika valid, None jika invalid
        """
        if not api_key or not api_key.startswith('sk_'):
            return None
        
        key_hash = self._hash_key(api_key)
        key_data = self.redis.hgetall(f"{self.key_prefix}{key_hash}")
        
        if not key_data:
            return None
        
        # Decode bytes to string
        metadata = {k.decode(): v.decode() for k, v in key_data.items()}
        
        # Update last used timestamp
        self.redis.hset(f"{self.key_prefix}{key_hash}", 
                       'last_used', 
                       datetime.utcnow().isoformat())
        
        # Increment request count
        self.redis.hincrby(f"{self.key_prefix}{key_hash}", 
                          'total_requests', 
                          1)
        
        return metadata
    
    def check_rate_limit(self, api_key: str) -> bool:
        """
        Check apakah request masih dalam rate limit.
        
        Args:
            api_key: API key string
            
        Returns:
            True jika masih dalam limit, False jika exceeded
        """
        key_hash = self._hash_key(api_key)
        rate_key = f"rate:{key_hash}"
        
        # Get current count
        current = self.redis.get(rate_key)
        
        if current is None:
            # First request in this window
            self.redis.setex(rate_key, 3600, 1)  # 1 hour window
            return True
        
        # Get rate limit for this key
        metadata = self.redis.hget(f"{self.key_prefix}{key_hash}", 
                                   'rate_limit')
        rate_limit = int(metadata.decode()) if metadata else 1000
        
        if int(current) >= rate_limit:
            return False
        
        self.redis.incr(rate_key)
        return True
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key."""
        key_hash = self._hash_key(api_key)
        deleted = self.redis.delete(f"{self.key_prefix}{key_hash}")
        
        if deleted:
            logger.info(f"API key revoked", extra={'key_hash': key_hash[:8]})
        
        return bool(deleted)
    
    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash API key menggunakan SHA256."""
        return hashlib.sha256(api_key.encode()).hexdigest()


def require_api_key(f: Callable) -> Callable:
    """
    Decorator untuk require API key authentication.
    
    Usage:
        @app.route('/api/protected')
        @require_api_key
        def protected_endpoint():
            return {'message': 'Access granted'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("Missing API key in request",
                         extra={'ip': request.remote_addr,
                               'endpoint': request.endpoint})
            raise AuthenticationError("API key required")
        
        # Get API key manager
        redis_client = current_app.extensions.get('redis')
        if not redis_client:
            logger.error("Redis client not available")
            raise AuthenticationError("Authentication service unavailable")
        
        key_manager = APIKeyManager(redis_client)
        
        # Verify key
        metadata = key_manager.verify_api_key(api_key)
        if not metadata:
            logger.warning("Invalid API key used",
                         extra={'ip': request.remote_addr,
                               'key_prefix': api_key[:10]})
            raise AuthenticationError("Invalid API key")
        
        # Check rate limit
        if not key_manager.check_rate_limit(api_key):
            logger.warning("Rate limit exceeded",
                         extra={'user_id': metadata['user_id'],
                               'ip': request.remote_addr})
            raise AuthorizationError("Rate limit exceeded")
        
        # Add user info to request context
        request.user_id = metadata['user_id']
        request.api_key_metadata = metadata
        
        logger.info("API request authenticated",
                   extra={'user_id': metadata['user_id'],
                         'endpoint': request.endpoint})
        
        return f(*args, **kwargs)
    
    return decorated_function


def create_api_key(user_id: str, name: str = "", 
                  rate_limit: int = 1000) -> str:
    """
    Helper function untuk create API key.
    
    Args:
        user_id: User ID
        name: Key name
        rate_limit: Requests per hour
        
    Returns:
        New API key
    """
    from flask import current_app
    
    redis_client = current_app.extensions.get('redis')
    if not redis_client:
        raise RuntimeError("Redis client not available")
    
    key_manager = APIKeyManager(redis_client)
    return key_manager.create_api_key(user_id, name, rate_limit)


def verify_api_key(api_key: str) -> Optional[dict]:
    """
    Helper function untuk verify API key.
    
    Args:
        api_key: API key to verify
        
    Returns:
        Metadata if valid, None otherwise
    """
    from flask import current_app
    
    redis_client = current_app.extensions.get('redis')
    if not redis_client:
        return None
    
    key_manager = APIKeyManager(redis_client)
    return key_manager.verify_api_key(api_key)
