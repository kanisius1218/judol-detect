"""Tests for the detection service."""
from __future__ import annotations

from datetime import datetime


def test_detection_outputs(detection_service):
    comments = [
        {"id": "1", "text": "Subscribe for free bitcoin", "platform": "youtube"},
        {"id": "2", "text": "Nice video!", "platform": "youtube"},
    ]
    outputs, version = detection_service.detect(comments)
    assert version == detection_service.model_info.version
    assert len(outputs) == 2
    assert outputs[0].is_spam is True
    assert outputs[1].is_spam is False


def test_queue_deletion(detection_service):
    jobs = detection_service.queue_deletion(["1"], platform="youtube", dry_run=True)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.dry_run is True
    assert job.status == "queued"
    assert isinstance(job.scheduled_for, datetime)
