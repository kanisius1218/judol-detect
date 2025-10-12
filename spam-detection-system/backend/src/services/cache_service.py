"""Cache service backed by an in-memory dictionary."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class CacheService:
    """Naive TTL cache for storing temporary state such as review decisions."""

    def __init__(self) -> None:
        self._cache: Dict[str, CacheEntry] = {}

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        self._cache[key] = CacheEntry(value=value, expires_at=time.time() + ttl)

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if not entry:
            return None
        if entry.expires_at < time.time():
            self._cache.pop(key, None)
            return None
        return entry.value

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)
