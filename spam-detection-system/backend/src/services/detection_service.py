"""Business logic for spam detection and automated deletion."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Tuple
from uuid import uuid4

from ..core.config import Settings
from ..core.exceptions import SpamDetectionError
from ..core.logging import get_logger
from ..models.ml.model_manager import ModelManager
from ..repository.spam_repository import DeletionJobRecord, DetectionRecord, SpamRepository
from ..services.cache_service import CacheService

logger = get_logger(__name__)


@dataclass
class DetectionOutput:
    comment_id: str
    platform: str
    is_spam: bool
    confidence: float
    reasons: List[str]


class DetectionService:
    """Coordinate spam detection, deletion workflow and audit logging."""

    def __init__(
        self,
        repository: SpamRepository,
        model_manager: ModelManager,
        cache: CacheService,
    ) -> None:
        self.repository = repository
        self.model_manager = model_manager
        self.cache = cache
        self.detector, self.model_info = self.model_manager.load()

    @classmethod
    def from_settings(cls, settings: Settings) -> "DetectionService":
        repository = SpamRepository()
        model_manager = ModelManager(
            storage_path=settings.model_storage_path,
            default_version=settings.model_default_version,
        )
        cache = CacheService()
        return cls(repository=repository, model_manager=model_manager, cache=cache)

    def detect(self, comments: Iterable[dict], aggressive: bool = False) -> Tuple[List[DetectionOutput], str]:
        comment_texts = [comment["text"] for comment in comments]
        results = self.detector.classify(comment_texts, aggressive=aggressive)
        outputs: List[DetectionOutput] = []
        for comment, (is_spam, probability, reasons) in zip(comments, results):
            output = DetectionOutput(
                comment_id=comment["id"],
                platform=comment["platform"],
                is_spam=is_spam,
                confidence=probability,
                reasons=reasons,
            )
            outputs.append(output)
            record = DetectionRecord(
                comment_id=output.comment_id,
                platform=output.platform,
                is_spam=output.is_spam,
                confidence=output.confidence,
                reasons=output.reasons,
            )
            self.repository.add(record)
            logger.info(
                "detection.processed",
                extra={
                    "comment_id": output.comment_id,
                    "platform": output.platform,
                    "is_spam": output.is_spam,
                    "confidence": output.confidence,
                },
            )
        return outputs, self.model_info.version

    def queue_deletion(self, comment_ids: List[str], platform: str, dry_run: bool = False) -> List[DeletionJobRecord]:
        if not comment_ids:
            raise SpamDetectionError(message="No comment ids provided")
        jobs: List[DeletionJobRecord] = []
        for comment_id in comment_ids:
            job = DeletionJobRecord(
                job_id=str(uuid4()),
                platform=platform,
                comment_ids=[comment_id],
                status="queued",
                scheduled_for=datetime.utcnow() + timedelta(minutes=5),
                dry_run=dry_run,
            )
            self.repository.add_deletion_job(job)
            jobs.append(job)
            logger.info("deletion.queued", extra={"job_id": job.job_id, "comment_id": comment_id})
        return jobs

    def mark_for_manual_review(self, comment_id: str, platform: str, notes: str | None = None) -> None:
        cache_key = f"manual_review:{platform}:{comment_id}"
        self.cache.set(cache_key, {"notes": notes}, ttl=3600)
        logger.info("review.marked", extra={"comment_id": comment_id, "platform": platform})

    def rollback_deletion(self, job_id: str, reason: str | None = None) -> DeletionJobRecord:
        job = self.repository.update_job_status(job_id, status="rollback_requested")
        if not job:
            raise SpamDetectionError(message="Deletion job not found")
        cache_key = f"rollback:{job_id}"
        self.cache.set(cache_key, {"reason": reason}, ttl=3600)
        logger.info("deletion.rollback", extra={"job_id": job_id, "reason": reason})
        return job
