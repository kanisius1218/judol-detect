"""Adapter for YouTube API interactions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class YouTubeComment:
    id: str
    text: str


class YouTubeAdapter:
    """Placeholder adapter for YouTube."""

    def fetch_comments(self, video_id: str) -> List[YouTubeComment]:
        logger.info("adapter.fetch", extra={"platform": "youtube", "video_id": video_id})
        return []

    def delete_comment(self, comment_id: str) -> None:
        logger.info("adapter.delete", extra={"platform": "youtube", "comment_id": comment_id})
