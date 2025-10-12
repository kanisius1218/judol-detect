"""Adapter for TikTok API interactions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TikTokComment:
    id: str
    text: str


class TikTokAdapter:
    """Placeholder adapter for TikTok."""

    def fetch_comments(self, video_id: str) -> List[TikTokComment]:
        logger.info("adapter.fetch", extra={"platform": "tiktok", "video_id": video_id})
        return []

    def delete_comment(self, comment_id: str) -> None:
        logger.info("adapter.delete", extra={"platform": "tiktok", "comment_id": comment_id})
