"""Pytest fixtures."""
from __future__ import annotations

import pytest

from backend.src.core.config import Settings
from backend.src.services.detection_service import DetectionService


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def detection_service(settings: Settings) -> DetectionService:
    return DetectionService.from_settings(settings)
