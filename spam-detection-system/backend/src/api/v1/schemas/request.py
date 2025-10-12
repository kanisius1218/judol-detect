"""Request models for API v1."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, conlist


class CommentPayload(BaseModel):
    """Payload describing a comment that should be analysed."""

    id: str = Field(..., description="Platform specific identifier")
    author_id: Optional[str] = Field(None, description="Author identifier")
    text: str = Field(..., min_length=1, description="Comment text")
    platform: str = Field(..., description="Source platform (youtube, instagram, tiktok)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class DetectionRequest(BaseModel):
    """Request to detect spam for a batch of comments."""

    comments: conlist(CommentPayload, min_items=1, max_items=100)
    aggressive: bool = Field(False, description="Enable a more aggressive threshold")


class DeletionRequest(BaseModel):
    """Request to schedule automatic deletion for provided comments."""

    comment_ids: conlist(str, min_items=1)
    platform: str = Field(..., description="Target platform for deletion")
    reviewer_id: Optional[str] = Field(None, description="Optional reviewer to notify")
    dry_run: bool = Field(False, description="If true, the deletion is only simulated")


class ManualReviewRequest(BaseModel):
    """Request to mark a comment for manual review."""

    comment_id: str
    platform: str
    notes: Optional[str] = None


class RollbackRequest(BaseModel):
    """Request to rollback a deletion."""

    deletion_id: str
    reason: Optional[str] = Field(None, description="Reason for the rollback")
    notify: bool = Field(True, description="Whether to notify reviewers about the rollback")


class AnalyticsWindow(BaseModel):
    """Parameters to fetch aggregated analytics."""

    start: Optional[str] = Field(None, description="ISO start datetime")
    end: Optional[str] = Field(None, description="ISO end datetime")
    platforms: Optional[List[str]] = Field(None, description="Subset of platforms")


class ApiKeyCreateRequest(BaseModel):
    """Request to provision a new API key for an integration."""

    name: str = Field(..., description="Friendly name for the integration")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook callback for notifications")
    scopes: conlist(str, min_items=1) = Field(..., description="Granted scopes")
