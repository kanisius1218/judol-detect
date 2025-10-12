"""Notification service for alerting reviewers and system owners."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..core.config import Settings
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Notification:
    recipient: str
    subject: str
    body: str


class NotificationService:
    """Service responsible for dispatching notifications."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def notify_reviewers(self, reviewers: Iterable[str], subject: str, body: str) -> None:
        for reviewer in reviewers:
            logger.info("notification.sent", extra={"reviewer": reviewer, "subject": subject})

    def notify_admin(self, subject: str, body: str) -> None:
        logger.info("notification.admin", extra={"subject": subject})
