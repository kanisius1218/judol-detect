"""Simple in-memory rate limiter middleware for demonstration."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import Request, Response

RateLimitKey = Tuple[str, str]


class RateLimiter:
    """Naive sliding window rate limiter suitable for small deployments."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[RateLimitKey, Deque[float]] = defaultdict(deque)

    def is_allowed(self, identifier: RateLimitKey) -> bool:
        now = time.time()
        queue = self._hits[identifier]
        while queue and now - queue[0] > self.window_seconds:
            queue.popleft()
        if len(queue) >= self.max_requests:
            return False
        queue.append(now)
        return True


def rate_limiter_factory(max_requests: int, window_seconds: int):
    limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)

    async def middleware(request: Request, call_next):  # type: ignore[override]
        identifier = (request.client.host if request.client else "anon", request.url.path)
        if not limiter.is_allowed(identifier):
            return Response(status_code=429, content="Too Many Requests")
        return await call_next(request)

    return middleware
