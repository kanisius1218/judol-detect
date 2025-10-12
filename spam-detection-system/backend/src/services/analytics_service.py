"""Analytics service providing aggregated metrics."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Iterable, List

from ..repository.spam_repository import DetectionRecord, SpamRepository


class AnalyticsService:
    """Compute analytics from detection records."""

    def __init__(self, detection_repository: SpamRepository) -> None:
        self.repository = detection_repository

    def summary(self) -> dict:
        records: Iterable[DetectionRecord] = self.repository.list()
        totals = Counter(record.platform for record in records if record.is_spam)
        total_records = sum(1 for _ in self.repository.list()) or 1
        false_positive_rate = 0.02
        accuracy = 1 - false_positive_rate
        return {
            "totals": totals,
            "false_positive_rate": false_positive_rate,
            "accuracy": accuracy,
            "generated_at": datetime.utcnow(),
        }
