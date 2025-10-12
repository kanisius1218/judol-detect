"""Health check endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from ..schemas import response as response_schema

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=response_schema.HealthStatus)
async def liveness() -> response_schema.HealthStatus:
    return response_schema.HealthStatus(status="ok", timestamp=datetime.utcnow(), details={})


@router.get("/ready", response_model=response_schema.HealthStatus)
async def readiness() -> response_schema.HealthStatus:
    return response_schema.HealthStatus(status="ok", timestamp=datetime.utcnow(), details={"db": "ok"})
