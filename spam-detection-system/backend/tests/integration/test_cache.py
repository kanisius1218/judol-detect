"""Tests for cache service integration."""
from __future__ import annotations

import time

from backend.src.services.cache_service import CacheService


def test_cache_expiry():
    cache = CacheService()
    cache.set("key", "value", ttl=1)
    assert cache.get("key") == "value"
    time.sleep(1.1)
    assert cache.get("key") is None
