"""Repository handling spam detection logs and deletion jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .base import InMemoryRepository


@dataclass
class DetectionRecord:
    comment_id: str
    platform: str
    is_spam: bool
    confidence: float
    reasons: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeletionJobRecord:
    job_id: str
    platform: str
    comment_ids: List[str]
    status: str
    scheduled_for: datetime
    dry_run: bool = False


class SpamRepository(InMemoryRepository[DetectionRecord]):
    """Repository storing detection results and deletion jobs in memory."""

    def __init__(self) -> None:
        super().__init__()
        self._deletion_jobs: List[DeletionJobRecord] = []

    def add_deletion_job(self, job: DeletionJobRecord) -> None:
        self._deletion_jobs.append(job)

    def list_deletion_jobs(self) -> List[DeletionJobRecord]:
        return list(self._deletion_jobs)

    def get_deletion_job(self, job_id: str) -> Optional[DeletionJobRecord]:
        return next((job for job in self._deletion_jobs if job.job_id == job_id), None)

    def update_job_status(self, job_id: str, status: str) -> Optional[DeletionJobRecord]:
        job = self.get_deletion_job(job_id)
        if job:
            job.status = status
        return job
