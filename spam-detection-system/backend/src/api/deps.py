"""Common dependency injection helpers."""
from __future__ import annotations

from functools import lru_cache

from ..core.config import Settings, get_settings
from ..services.analytics_service import AnalyticsService
from ..services.detection_service import DetectionService
from ..services.notification_service import NotificationService


@lru_cache(maxsize=1)
def get_detection_service() -> DetectionService:
    settings = get_settings()
    return DetectionService.from_settings(settings)


@lru_cache(maxsize=1)
def get_analytics_service() -> AnalyticsService:
    detection = get_detection_service()
    return AnalyticsService(detection_repository=detection.repository)


@lru_cache(maxsize=1)
def get_notification_service() -> NotificationService:
    settings = get_settings()
    return NotificationService(settings=settings)


def get_runtime_settings() -> Settings:
    return get_settings()
