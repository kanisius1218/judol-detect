"""Generic helper utilities."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable


def generate_audit_id(prefix: str) -> str:
    return f"{prefix}-{datetime.utcnow().isoformat()}"


def chunked(iterable: Iterable, size: int):
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
