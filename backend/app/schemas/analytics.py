from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyticsSummaryResponse(BaseModel):
    """
    High-level operational metrics and KPIs dynamically aggregated from database records.
    """
    total_thermal_events: int = Field(..., ge=0, description="Total thermal anomalies recorded")
    critical_events: int = Field(..., ge=0, description="Count of critical priority events")
    high_risk_events: int = Field(..., ge=0, description="Count of high-risk priority events")
    moderate_events: int = Field(..., ge=0, description="Count of moderate priority events")
    low_risk_events: int = Field(..., ge=0, description="Count of low-risk priority events")
    active_alerts: int = Field(..., ge=0, description="Total active unread alerts")
    industrial_facilities: int = Field(..., ge=0, description="Total registered industrial facilities")
    events_detected_today: int = Field(..., ge=0, description="Events detected during today UTC")
    events_detected_this_week: int = Field(..., ge=0, description="Events detected within the past 7 days")
    start_date: Optional[datetime] = Field(None, description="Start date filter applied if any")
    end_date: Optional[datetime] = Field(None, description="End date filter applied if any")


class RiskDistributionItem(BaseModel):
    category: str = Field(..., description="Risk category: Critical, High, Moderate, Low")
    count: int = Field(..., ge=0, description="Number of events in this bracket")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of total events")
    avg_risk_score: float = Field(..., ge=0.0, le=100.0, description="Average calculated risk score")


class RiskDistributionResponse(BaseModel):
    """
    Distribution of thermal anomalies categorized by risk priority bracket.
    """
    total_events: int = Field(..., ge=0, description="Total events analyzed")
    distribution: List[RiskDistributionItem] = Field(..., description="Breakdown by risk category")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class EventTypeDistributionItem(BaseModel):
    event_type: str = Field(..., description="Event classification (e.g. Critical Industrial Fire, Gas Flare)")
    count: int = Field(..., ge=0, description="Number of events with this designation")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of total events")
    avg_risk_score: float = Field(..., ge=0.0, le=100.0, description="Average risk score for this type")


class EventTypeDistributionResponse(BaseModel):
    """
    Breakdown of events grouped by hazard and operational event type.
    """
    total_events: int = Field(..., ge=0)
    distribution: List[EventTypeDistributionItem] = Field(...)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TimeSeriesDataPoint(BaseModel):
    date: str = Field(..., description="Date period in YYYY-MM-DD format")
    total_events: int = Field(..., ge=0, description="Total events detected on this date")
    critical_events: int = Field(0, ge=0)
    high_events: int = Field(0, ge=0)
    moderate_events: int = Field(0, ge=0)
    low_events: int = Field(0, ge=0)
    avg_risk_score: float = Field(..., ge=0.0, le=100.0)


class TimeSeriesResponse(BaseModel):
    """
    Temporal aggregation of thermal events for time-series trend charting.
    """
    interval: str = Field("daily", description="Time grouping interval (e.g. daily)")
    total_periods: int = Field(..., ge=0, description="Number of aggregated temporal bins")
    total_events: int = Field(..., ge=0, description="Total events across all bins")
    series: List[TimeSeriesDataPoint] = Field(..., description="Chronological trend series")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
