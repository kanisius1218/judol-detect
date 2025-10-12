"""
Spam detection API endpoints.
Handles single and batch detection, auto-deletion management.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from ....api.deps import get_db
from ....api.v1.schemas.request import (
    DetectionRequest,
    BatchDetectionRequest,
    DeletionRequest,
    RollbackRequest
)
from ....api.v1.schemas.response import (
    DetectionResponse,
    BatchDetectionResponse,
    DeletionResponse,
    RollbackResponse,
    DetectionHistoryResponse
)
from ....api.v1.middleware.auth import get_current_user, get_optional_user, require_permission
from ....api.v1.middleware.rate_limit import ip_limiter
from ....models.database.user import User
from ....models.ml.spam_detector import SpamDetector
from ....workers.tasks import detect_spam, auto_delete_spam, rollback_deletion, batch_detect_spam
from ....services.detection_service import DetectionService
from ....core import logger, audit_logger, Permission, settings
from celery.result import AsyncResult


router = APIRouter(prefix="/detection", tags=["detection"])

# Initialize services
spam_detector = SpamDetector()
detection_service = DetectionService()


@router.post("/detect", response_model=DetectionResponse)
async def detect_single(
    request: DetectionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Detect spam in a single message.
    
    - **text**: The message text to analyze
    - **platform**: Optional platform context (youtube, instagram, tiktok)
    - **metadata**: Optional metadata for context
    
    Returns spam detection result with confidence score.
    """
    # Apply stricter rate limiting for anonymous users
    if not current_user:
        await ip_limiter.check(request)
    
    try:
        # Run detection
        result = await spam_detector.predict(request.text)
        
        # Store detection in background
        if current_user:
            background_tasks.add_task(
                detection_service.store_detection,
                db=db,
                user_id=current_user.id,
                text=request.text,
                platform=request.platform,
                result=result,
                metadata=request.metadata
            )
        
        # Schedule auto-deletion if enabled and confidence is high
        if (result.is_spam and 
            result.confidence >= settings.AUTO_DELETE_CONFIDENCE_THRESHOLD and
            settings.AUTO_DELETE_ENABLED and
            request.platform and
            request.content_id):
            
            # Queue deletion task
            task = detect_spam.apply_async(
                args=[request.text, request.platform, request.content_id, request.metadata],
                queue='high_priority'
            )
            
            logger.info(f"Queued auto-deletion task {task.id} for {request.platform}:{request.content_id}")
        
        return DetectionResponse(
            is_spam=result.is_spam,
            confidence=result.confidence,
            spam_score=result.spam_score,
            risk_level=result.risk_level,
            explanation=result.explanation,
            features=result.features,
            model_version=result.model_version,
            processing_time_ms=result.processing_time_ms,
            auto_delete_scheduled=(
                result.is_spam and 
                result.confidence >= settings.AUTO_DELETE_CONFIDENCE_THRESHOLD and
                settings.AUTO_DELETE_ENABLED
            )
        )
        
    except Exception as e:
        logger.error(f"Detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Detection service error")


@router.post("/batch", response_model=BatchDetectionResponse)
async def detect_batch(
    request: BatchDetectionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detect spam in multiple messages.
    Requires authentication.
    
    - **texts**: List of messages to analyze (max 100)
    - **platform**: Platform context
    - **metadata**: Optional metadata for each text
    
    Returns batch detection results.
    """
    if len(request.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per batch")
    
    try:
        # Queue batch detection task
        task = batch_detect_spam.apply_async(
            args=[request.texts, request.platform, request.metadata],
            queue='high_priority'
        )
        
        # Wait for results (with timeout)
        results = task.get(timeout=30)
        
        # Store results in background
        background_tasks.add_task(
            detection_service.store_batch_detection,
            db=db,
            user_id=current_user.id,
            results=results,
            platform=request.platform
        )
        
        return BatchDetectionResponse(**results)
        
    except Exception as e:
        logger.error(f"Batch detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch detection service error")


@router.post("/delete", response_model=DeletionResponse, dependencies=[Depends(require_permission(Permission.MANUAL_DELETE))])
async def delete_spam(
    request: DeletionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually delete detected spam.
    Requires MANUAL_DELETE permission.
    
    - **platform**: Platform name
    - **content_id**: Content identifier
    - **detection_id**: Detection record ID
    - **reason**: Reason for deletion
    
    Returns deletion result with rollback token.
    """
    try:
        # Verify detection exists and belongs to user
        detection = await detection_service.get_detection(db, request.detection_id)
        
        if not detection:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        # Queue deletion task
        task = auto_delete_spam.apply_async(
            args=[
                request.platform,
                request.content_id,
                request.detection_id,
                detection.spam_score,
                True  # Force deletion
            ],
            queue='auto_deletion'
        )
        
        # Wait for result
        result = task.get(timeout=10)
        
        # Log action
        audit_logger.log_action(
            action="MANUAL_DELETE",
            user_id=str(current_user.id),
            resource_type="spam_content",
            resource_id=request.content_id,
            details={
                "platform": request.platform,
                "reason": request.reason,
                "detection_id": request.detection_id
            }
        )
        
        return DeletionResponse(**result)
        
    except Exception as e:
        logger.error(f"Manual deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Deletion service error")


@router.post("/rollback", response_model=RollbackResponse, dependencies=[Depends(require_permission(Permission.ROLLBACK))])
async def rollback_spam_deletion(
    request: RollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rollback a spam deletion.
    Requires ROLLBACK permission.
    
    - **rollback_token**: Unique rollback token from deletion
    - **reason**: Reason for rollback
    
    Returns rollback result.
    """
    try:
        # Queue rollback task
        task = rollback_deletion.apply_async(
            args=[request.rollback_token, request.reason],
            queue='rollback'
        )
        
        # Wait for result
        result = task.get(timeout=10)
        
        # Log action
        audit_logger.log_action(
            action="ROLLBACK_DELETE",
            user_id=str(current_user.id),
            resource_type="rollback",
            resource_id=request.rollback_token,
            details={
                "reason": request.reason
            }
        )
        
        return RollbackResponse(**result)
        
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Rollback service error")


@router.get("/history", response_model=DetectionHistoryResponse)
async def get_detection_history(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    is_spam: Optional[bool] = Query(None, description="Filter by spam status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(50, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detection history for the current user.
    
    Query parameters:
    - **platform**: Filter by platform
    - **is_spam**: Filter by spam status
    - **start_date**: Start date for filtering
    - **end_date**: End date for filtering
    - **limit**: Maximum number of results
    - **offset**: Offset for pagination
    
    Returns paginated detection history.
    """
    try:
        # Get history from service
        history = await detection_service.get_user_history(
            db=db,
            user_id=current_user.id,
            platform=platform,
            is_spam=is_spam,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        # Get total count
        total = await detection_service.count_user_detections(
            db=db,
            user_id=current_user.id,
            platform=platform,
            is_spam=is_spam,
            start_date=start_date,
            end_date=end_date
        )
        
        return DetectionHistoryResponse(
            items=history,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to get history: {str(e)}")
        raise HTTPException(status_code=500, detail="History service error")


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of an async detection task.
    
    - **task_id**: Celery task ID
    
    Returns task status and result if available.
    """
    try:
        result = AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "result": result.result if result.successful() else None,
            "error": str(result.info) if result.failed() else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail="Task status error")


@router.post("/override/{detection_id}")
async def override_detection(
    detection_id: str,
    override_status: str = Body(..., regex="^(spam|not_spam|keep)$"),
    reason: str = Body(..., min_length=1, max_length=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Override a detection result for training feedback.
    
    - **detection_id**: Detection record ID
    - **override_status**: New status (spam, not_spam, keep)
    - **reason**: Reason for override
    
    Returns updated detection.
    """
    try:
        # Update detection with override
        updated = await detection_service.override_detection(
            db=db,
            detection_id=detection_id,
            user_id=current_user.id,
            override_status=override_status,
            reason=reason
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        # Log override for model training
        audit_logger.log_action(
            action="DETECTION_OVERRIDE",
            user_id=str(current_user.id),
            resource_type="detection",
            resource_id=detection_id,
            details={
                "override_status": override_status,
                "reason": reason
            }
        )
        
        return {
            "detection_id": detection_id,
            "override_status": override_status,
            "reason": reason,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to override detection: {str(e)}")
        raise HTTPException(status_code=500, detail="Override service error")
