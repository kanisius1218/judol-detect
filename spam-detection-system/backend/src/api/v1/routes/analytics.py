"""Analytics endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from ....services.analytics_service import AnalyticsService
from ...deps import get_analytics_service
from ..middleware.auth import enforce_api_key
from ..schemas import response as response_schema

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(enforce_api_key)])


@router.get("/summary", response_model=response_schema.AnalyticsSummary)
async def analytics_summary(service: AnalyticsService = Depends(get_analytics_service)) -> response_schema.AnalyticsSummary:
    summary = service.summary()
    return response_schema.AnalyticsSummary(
        totals=dict(summary["totals"]),
        false_positive_rate=summary["false_positive_rate"],
        accuracy=summary["accuracy"],
        window_start=None,
        window_end=None,
    )
