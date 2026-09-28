"""
Router for Analytics and Executive KPI endpoints.
Calculates dynamic aggregations across thermal anomalies, alerts, and facilities
with date filtering support.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    RiskDistributionResponse,
    EventTypeDistributionResponse,
    TimeSeriesResponse,
)
from app.services.analytics_service import AnalyticsService, get_analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics & Intelligence KPIs"]
)


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve executive KPI summary and counts",
    description=(
        "Returns dynamically aggregated platform KPIs including total events, "
        "counts across all risk priorities (Critical, High, Moderate, Low), "
        "active unread alerts, registered industrial facilities, and events detected "
        "today and during the past 7 days. Supports optional temporal window filtering."
    )
)
def get_analytics_summary(
    start_date: Optional[datetime] = Query(None, description="Filter events on or after this ISO datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter events on or before this ISO datetime"),
    is_demo: Optional[bool] = Query(None, description="Filter by demo/simulated records flag"),
    db: Session = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummaryResponse:
    """
    Get aggregated summary KPIs.
    """
    return analytics_service.get_summary(db=db, start_date=start_date, end_date=end_date, is_demo=is_demo)


@router.get(
    "/risk-distribution",
    response_model=RiskDistributionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve risk priority category distribution",
    description=(
        "Calculates the count, percentage share, and average risk score for each "
        "risk bracket (Critical, High, Moderate, Low) from live thermal observations."
    )
)
def get_risk_distribution(
    start_date: Optional[datetime] = Query(None, description="Filter events on or after this ISO datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter events on or before this ISO datetime"),
    is_demo: Optional[bool] = Query(None, description="Filter by demo/simulated records flag"),
    db: Session = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> RiskDistributionResponse:
    """
    Get risk priority bracket distribution.
    """
    return analytics_service.get_risk_distribution(db=db, start_date=start_date, end_date=end_date, is_demo=is_demo)


@router.get(
    "/event-types",
    response_model=EventTypeDistributionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve breakdown by thermal hazard designation",
    description=(
        "Aggregates thermal events grouped by classification designation "
        "(e.g. Critical Industrial Fire, Gas Flare, High-Risk Thermal Event), "
        "computing total counts, percentage distributions, and average risk severity."
    )
)
def get_event_types(
    start_date: Optional[datetime] = Query(None, description="Filter events on or after this ISO datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter events on or before this ISO datetime"),
    is_demo: Optional[bool] = Query(None, description="Filter by demo/simulated records flag"),
    db: Session = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> EventTypeDistributionResponse:
    """
    Get breakdown by hazard type.
    """
    return analytics_service.get_event_types(db=db, start_date=start_date, end_date=end_date, is_demo=is_demo)


@router.get(
    "/time-series",
    response_model=TimeSeriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve chronological time-series trend data",
    description=(
        "Aggregates thermal anomaly occurrences into daily bins with severity breakdowns "
        "and average risk scores for timeline graphing and historical trend analysis."
    )
)
def get_time_series(
    start_date: Optional[datetime] = Query(None, description="Filter events on or after this ISO datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter events on or before this ISO datetime"),
    interval: str = Query("daily", description="Time bin aggregation interval (default: daily)"),
    is_demo: Optional[bool] = Query(None, description="Filter by demo/simulated records flag"),
    db: Session = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> TimeSeriesResponse:
    """
    Get chronological time-series aggregations.
    """
    return analytics_service.get_time_series(
        db=db,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        is_demo=is_demo,
    )
