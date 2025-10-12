"""Load test placeholder."""
from __future__ import annotations

from time import perf_counter

from backend.src.core.config import Settings
from backend.src.services.detection_service import DetectionService


def test_detection_performance_baseline():
    service = DetectionService.from_settings(Settings())
    comments = [
        {"id": str(i), "text": "Click now for free stuff", "platform": "youtube"}
        for i in range(10)
    ]
    start = perf_counter()
    outputs, _ = service.detect(comments)
    elapsed = perf_counter() - start
    assert len(outputs) == 10
    assert elapsed < 1.0
