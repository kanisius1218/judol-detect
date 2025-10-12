"""Response models for API v1."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    """Result of a spam detection inference."""

    comment_id: str
    platform: str
    is_spam: bool
    confidence: float = Field(..., ge=0, le=1)
    reasons: List[str] = Field(default_factory=list)


class DetectionResponse(BaseModel):
    """Response payload for bulk detection requests."""

    results: List[DetectionResult]
    model_version: str
    processed_at: datetime


class DeletionJob(BaseModel):
    """Metadata for a deletion job queued for execution."""

    job_id: str
    platform: str
    status: str
    scheduled_for: datetime
    dry_run: bool = False


class DeletionResponse(BaseModel):
    """Response after queueing deletion jobs."""

    jobs: List[DeletionJob]
    queued_at: datetime


class RollbackResponse(BaseModel):
    """Response emitted after a rollback request."""

    rollback_id: str
    status: str
    completed_at: datetime


class AnalyticsSummary(BaseModel):
    """Aggregated analytics for detections and deletions."""

    totals: Dict[str, int]
    false_positive_rate: float = Field(..., ge=0, le=1)
    accuracy: float = Field(..., ge=0, le=1)
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None


class HealthStatus(BaseModel):
    """Service health indicator."""

    status: str
    timestamp: datetime
    details: Dict[str, str] = Field(default_factory=dict)


class AdminActionResponse(BaseModel):
    """Response emitted for administrative actions."""

    action: str
    status: str
    executed_at: datetime
