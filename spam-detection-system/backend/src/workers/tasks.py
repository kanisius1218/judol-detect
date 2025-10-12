"""Celery task definitions."""
from __future__ import annotations

from ..api.deps import get_detection_service
from ..core.logging import get_logger
from .celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="deletion.execute")
def execute_deletion(job_id: str) -> None:
    service = get_detection_service()
    job = service.repository.get_deletion_job(job_id)
    if not job:
        logger.warning("deletion.missing", extra={"job_id": job_id})
        return
    service.repository.update_job_status(job_id, "completed")
    logger.info("deletion.executed", extra={"job_id": job_id})
