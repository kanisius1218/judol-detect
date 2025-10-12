"""Integration test placeholders for database interactions."""
from __future__ import annotations

from backend.src.repository.spam_repository import DetectionRecord, SpamRepository


def test_repository_persists_records():
    repo = SpamRepository()
    record = DetectionRecord(
        comment_id="1",
        platform="youtube",
        is_spam=True,
        confidence=0.9,
        reasons=["keyword_match"],
    )
    repo.add(record)
    stored = list(repo.list())
    assert stored[0].comment_id == "1"
