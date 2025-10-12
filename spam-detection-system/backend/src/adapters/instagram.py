"""Adapter for Instagram API interactions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class InstagramComment:
    id: str
    text: str


class InstagramAdapter:
    """Placeholder adapter for Instagram."""

    def fetch_comments(self, media_id: str) -> List[InstagramComment]:
        logger.info("adapter.fetch", extra={"platform": "instagram", "media_id": media_id})
        return []

    def delete_comment(self, comment_id: str) -> None:
        logger.info("adapter.delete", extra={"platform": "instagram", "comment_id": comment_id})
