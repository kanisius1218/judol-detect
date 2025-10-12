"""Detection endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, status

from ....services.detection_service import DetectionService
from ...deps import get_detection_service
from ..middleware.auth import enforce_api_key
from ..schemas import request as request_schema
from ..schemas import response as response_schema

router = APIRouter(prefix="/detection", tags=["detection"], dependencies=[Depends(enforce_api_key)])


@router.post("/predict", response_model=response_schema.DetectionResponse, status_code=status.HTTP_200_OK)
async def predict_spam(
    payload: request_schema.DetectionRequest,
    service: DetectionService = Depends(get_detection_service),
) -> response_schema.DetectionResponse:
    results, version = service.detect(
        [comment.dict() for comment in payload.comments], aggressive=payload.aggressive
    )
    detection_results = [
        response_schema.DetectionResult(
            comment_id=result.comment_id,
            platform=result.platform,
            is_spam=result.is_spam,
            confidence=result.confidence,
            reasons=result.reasons,
        )
        for result in results
    ]
    return response_schema.DetectionResponse(
        results=detection_results,
        model_version=version,
        processed_at=datetime.utcnow(),
    )


@router.post("/auto-delete", response_model=response_schema.DeletionResponse)
async def auto_delete(
    payload: request_schema.DeletionRequest,
    service: DetectionService = Depends(get_detection_service),
) -> response_schema.DeletionResponse:
    jobs = service.queue_deletion(
        comment_ids=list(payload.comment_ids),
        platform=payload.platform,
        dry_run=payload.dry_run,
    )
    response_jobs = [
        response_schema.DeletionJob(
            job_id=job.job_id,
            platform=job.platform,
            status=job.status,
            scheduled_for=job.scheduled_for,
            dry_run=job.dry_run,
        )
        for job in jobs
    ]
    return response_schema.DeletionResponse(jobs=response_jobs, queued_at=datetime.utcnow())


@router.post("/manual-review", status_code=status.HTTP_202_ACCEPTED)
async def manual_review(
    payload: request_schema.ManualReviewRequest,
    service: DetectionService = Depends(get_detection_service),
) -> None:
    service.mark_for_manual_review(
        comment_id=payload.comment_id,
        platform=payload.platform,
        notes=payload.notes,
    )


@router.post("/rollback", response_model=response_schema.RollbackResponse)
async def rollback_deletion(
    payload: request_schema.RollbackRequest,
    service: DetectionService = Depends(get_detection_service),
) -> response_schema.RollbackResponse:
    job = service.rollback_deletion(job_id=payload.deletion_id, reason=payload.reason)
    return response_schema.RollbackResponse(
        rollback_id=job.job_id,
        status=job.status,
        completed_at=datetime.utcnow(),
    )
