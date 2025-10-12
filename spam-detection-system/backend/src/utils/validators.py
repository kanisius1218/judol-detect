"""Validation utilities."""
from __future__ import annotations

from typing import Iterable


ALLOWED_PLATFORMS = {"youtube", "instagram", "tiktok"}


def validate_platform(platform: str) -> None:
    if platform not in ALLOWED_PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")


def ensure_unique(values: Iterable[str]) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise ValueError(f"Duplicate value detected: {value}")
        seen.add(value)
