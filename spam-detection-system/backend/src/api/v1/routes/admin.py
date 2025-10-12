"""Administrative endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from ....core.security import SecurityService
from ...deps import get_notification_service
from ..middleware.auth import enforce_api_key, enforce_internal_header, get_security_service
from ..schemas import request as request_schema
from ..schemas import response as response_schema

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(enforce_api_key)])


@router.post("/api-keys", response_model=response_schema.AdminActionResponse, dependencies=[Depends(enforce_internal_header)])
async def create_api_key(
    payload: request_schema.ApiKeyCreateRequest,
    security: SecurityService = Depends(get_security_service),
) -> response_schema.AdminActionResponse:
    raw_key, _ = security.generate_api_key(payload.name, payload.scopes)
    return response_schema.AdminActionResponse(
        action="create_api_key",
        status=f"issued:{raw_key}",
        executed_at=datetime.utcnow(),
    )


@router.post("/alerts", response_model=response_schema.AdminActionResponse)
async def trigger_alert(
    subject: str,
    notification_service=Depends(get_notification_service),
) -> response_schema.AdminActionResponse:
    notification_service.notify_admin(subject=subject, body="Admin triggered alert")
    return response_schema.AdminActionResponse(
        action="trigger_alert",
        status="sent",
        executed_at=datetime.utcnow(),
    )
