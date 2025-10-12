"""
Rate limiting middleware to prevent API abuse.
Implements token bucket algorithm with Redis backend.
"""
from typing import Optional, Callable
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
import redis.asyncio as aioredis
import hashlib
import json
from ....core import settings, logger, RateLimitExceededError


class RateLimiter:
    """Rate limiter using Redis for distributed rate limiting."""
    
    def __init__(
        self,
        redis_client: Optional[aioredis.Redis] = None,
        requests_per_minute: int = None,
        requests_per_hour: int = None,
        burst_size: int = None
    ):
        self.redis = redis_client
        self.rpm = requests_per_minute or settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.rph = requests_per_hour or settings.RATE_LIMIT_REQUESTS_PER_HOUR
        self.burst = burst_size or settings.RATE_LIMIT_BURST_SIZE
        
    async def connect(self):
        """Connect to Redis if not already connected."""
        if not self.redis:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD.get_secret_value() if settings.REDIS_PASSWORD else None,
                decode_responses=True
            )
    
    async def check_rate_limit(
        self,
        identifier: str,
        cost: int = 1
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: Unique identifier (user_id, IP, API key)
            cost: Cost of this request (default 1)
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True, None
        
        await self.connect()
        
        now = datetime.utcnow()
        
        # Check minute limit
        minute_key = f"rate_limit:minute:{identifier}:{now.minute}"
        minute_count = await self.redis.get(minute_key) or 0
        minute_count = int(minute_count)
        
        if minute_count + cost > self.rpm:
            retry_after = 60 - now.second
            return False, retry_after
        
        # Check hour limit
        hour_key = f"rate_limit:hour:{identifier}:{now.hour}"
        hour_count = await self.redis.get(hour_key) or 0
        hour_count = int(hour_count)
        
        if hour_count + cost > self.rph:
            retry_after = 3600 - (now.minute * 60 + now.second)
            return False, retry_after
        
        # Check burst limit (sliding window)
        burst_key = f"rate_limit:burst:{identifier}"
        burst_count = await self.redis.get(burst_key) or 0
        burst_count = int(burst_count)
        
        if burst_count >= self.burst:
            return False, 1
        
        # Update counters
        pipe = self.redis.pipeline()
        
        # Increment minute counter
        pipe.incr(minute_key, cost)
        pipe.expire(minute_key, 60)
        
        # Increment hour counter
        pipe.incr(hour_key, cost)
        pipe.expire(hour_key, 3600)
        
        # Increment burst counter
        pipe.incr(burst_key, 1)
        pipe.expire(burst_key, 1)
        
        await pipe.execute()
        
        return True, None
    
    async def get_limits_for(self, identifier: str) -> dict:
        """Get current rate limit status for identifier."""
        await self.connect()
        
        now = datetime.utcnow()
        
        minute_key = f"rate_limit:minute:{identifier}:{now.minute}"
        hour_key = f"rate_limit:hour:{identifier}:{now.hour}"
        burst_key = f"rate_limit:burst:{identifier}"
        
        minute_count = await self.redis.get(minute_key) or 0
        hour_count = await self.redis.get(hour_key) or 0
        burst_count = await self.redis.get(burst_key) or 0
        
        return {
            "minute": {
                "used": int(minute_count),
                "limit": self.rpm,
                "remaining": max(0, self.rpm - int(minute_count))
            },
            "hour": {
                "used": int(hour_count),
                "limit": self.rph,
                "remaining": max(0, self.rph - int(hour_count))
            },
            "burst": {
                "used": int(burst_count),
                "limit": self.burst,
                "remaining": max(0, self.burst - int(burst_count))
            }
        }
    
    async def reset_limits_for(self, identifier: str):
        """Reset rate limits for identifier (admin only)."""
        await self.connect()
        
        now = datetime.utcnow()
        
        keys = [
            f"rate_limit:minute:{identifier}:{now.minute}",
            f"rate_limit:hour:{identifier}:{now.hour}",
            f"rate_limit:burst:{identifier}"
        ]
        
        for key in keys:
            await self.redis.delete(key)


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to incoming requests."""
        
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get identifier (prefer authenticated user, fallback to IP)
        identifier = self._get_identifier(request)
        
        # Get request cost (some endpoints might cost more)
        cost = self._get_request_cost(request)
        
        # Check rate limit
        allowed, retry_after = await self.limiter.check_rate_limit(identifier, cost)
        
        if not allowed:
            # Get current limits for response
            limits = await self.limiter.get_limits_for(identifier)
            
            response = Response(
                content=json.dumps({
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                        "limits": limits,
                        "retry_after_seconds": retry_after
                    }
                }),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.limiter.rpm)
            response.headers["X-RateLimit-Remaining"] = str(limits["minute"]["remaining"])
            response.headers["X-RateLimit-Reset"] = str(int(datetime.utcnow().timestamp()) + retry_after)
            response.headers["Retry-After"] = str(retry_after)
            
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        limits = await self.limiter.get_limits_for(identifier)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.rpm)
        response.headers["X-RateLimit-Remaining"] = str(limits["minute"]["remaining"])
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting."""
        # Check for authenticated user
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Check for API key
        api_key = request.headers.get(settings.API_KEY_HEADER)
        if api_key:
            # Hash API key for privacy
            return f"api_key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for proxy headers
        if "X-Forwarded-For" in request.headers:
            client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in request.headers:
            client_ip = request.headers["X-Real-IP"]
        
        return f"ip:{client_ip}"
    
    def _get_request_cost(self, request: Request) -> int:
        """
        Calculate request cost based on endpoint.
        Some endpoints might consume more rate limit quota.
        """
        path = request.url.path
        method = request.method
        
        # Batch operations cost more
        if "batch" in path:
            return 10
        
        # Detection endpoints
        if "detect" in path:
            return 3
        
        # Analytics endpoints
        if "analytics" in path or "report" in path:
            return 5
        
        # Write operations
        if method in ["POST", "PUT", "DELETE"]:
            return 2
        
        # Default cost
        return 1


# Custom rate limit decorator for specific endpoints
def rate_limit(
    requests_per_minute: Optional[int] = None,
    requests_per_hour: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for custom rate limiting on specific endpoints.
    
    Usage:
        @router.get("/expensive-operation")
        @rate_limit(requests_per_minute=10)
        async def expensive_operation():
            ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Create custom limiter for this endpoint
            limiter = RateLimiter(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour
            )
            
            # Get identifier
            if key_func:
                identifier = key_func(request)
            else:
                # Default to IP-based limiting
                identifier = request.client.host if request.client else "unknown"
            
            # Check rate limit
            allowed, retry_after = await limiter.check_rate_limit(identifier)
            
            if not allowed:
                raise RateLimitExceededError(
                    message="Endpoint rate limit exceeded",
                    retry_after=retry_after
                )
            
            # Execute function
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# Global rate limiter instance
rate_limiter = RateLimiter()


# IP-based rate limiter for anonymous users
class IPRateLimiter:
    """Simple IP-based rate limiter for public endpoints."""
    
    def __init__(self):
        self.limiter = RateLimiter(
            requests_per_minute=30,  # Stricter for anonymous users
            requests_per_hour=500
        )
    
    async def check(self, request: Request):
        """Check rate limit for IP."""
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for proxy headers
        if "X-Forwarded-For" in request.headers:
            client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in request.headers:
            client_ip = request.headers["X-Real-IP"]
        
        allowed, retry_after = await self.limiter.check_rate_limit(f"ip:{client_ip}")
        
        if not allowed:
            raise RateLimitExceededError(retry_after=retry_after)


ip_limiter = IPRateLimiter()
