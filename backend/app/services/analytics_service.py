"""
Analytics Service for SIH26162.
Performs real dynamic database aggregations across thermal events, alerts,
and industrial facilities without hardcoding.
Supports temporal date slicing, risk distributions, event hazard breakdowns,
and time-series charting feeds.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import func, or_, and_, case, desc, asc
from sqlalchemy.orm import Session

from app.models.thermal_event import ThermalEvent
from app.models.alert import Alert
from app.models.facility import IndustrialFacility
from app.core.spatial import INDIA_LAT_MIN, INDIA_LAT_MAX, INDIA_LON_MIN, INDIA_LON_MAX
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    RiskDistributionItem,
    RiskDistributionResponse,
    EventTypeDistributionItem,
    EventTypeDistributionResponse,
    TimeSeriesDataPoint,
    TimeSeriesResponse,
)


class AnalyticsService:
    """
    Analytics engine performing dynamic SQL aggregations.
    """

    def get_summary(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_demo: Optional[bool] = None,
    ) -> AnalyticsSummaryResponse:
        """
        Aggregate high-level KPIs across the database.
        """
        # Base query for thermal events with strict India-Only territorial filter
        q = db.query(ThermalEvent).filter(
            ThermalEvent.latitude >= INDIA_LAT_MIN,
            ThermalEvent.latitude <= INDIA_LAT_MAX,
            ThermalEvent.longitude >= INDIA_LON_MIN,
            ThermalEvent.longitude <= INDIA_LON_MAX,
        )
        if is_demo is not None:
            q = q.filter(ThermalEvent.is_demo == is_demo)
        if start_date:
            q = q.filter(ThermalEvent.detected_at >= start_date)
        if end_date:
            q = q.filter(ThermalEvent.detected_at <= end_date)

        total_thermal_events = q.count()

        # Mutually exclusive risk category conditions
        cond_critical = or_(
            ThermalEvent.risk_priority.ilike("%crit%"),
            and_(ThermalEvent.risk_priority.is_(None), ThermalEvent.risk_score >= 75.0),
        )
        cond_high = and_(
            ~cond_critical,
            or_(
                ThermalEvent.risk_priority.ilike("%high%"),
                and_(ThermalEvent.risk_priority.is_(None), ThermalEvent.risk_score >= 50.0, ThermalEvent.risk_score < 75.0),
            ),
        )
        cond_moderate = and_(
            ~cond_critical,
            ~cond_high,
            or_(
                ThermalEvent.risk_priority.ilike("%mod%"),
                ThermalEvent.risk_priority.ilike("%med%"),
                and_(ThermalEvent.risk_priority.is_(None), ThermalEvent.risk_score >= 25.0, ThermalEvent.risk_score < 50.0),
            ),
        )
        cond_low = and_(
            ~cond_critical,
            ~cond_high,
            ~cond_moderate,
        )

        critical_count = q.filter(cond_critical).count()
        high_risk_count = q.filter(cond_high).count()
        moderate_count = q.filter(cond_moderate).count()
        low_risk_count = q.filter(cond_low).count()

        # Active (unread) alerts count
        active_alerts = db.query(Alert).filter(Alert.is_read == False).count()

        # Total industrial facilities
        total_facilities = db.query(IndustrialFacility).count()

        # Events detected today and this week (strictly India-only)
        now = datetime.now(timezone.utc)
        start_of_today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        one_week_ago = now - timedelta(days=7)

        today_q = db.query(ThermalEvent).filter(
            ThermalEvent.detected_at >= start_of_today,
            ThermalEvent.latitude >= INDIA_LAT_MIN,
            ThermalEvent.latitude <= INDIA_LAT_MAX,
            ThermalEvent.longitude >= INDIA_LON_MIN,
            ThermalEvent.longitude <= INDIA_LON_MAX,
        )
        week_q = db.query(ThermalEvent).filter(
            ThermalEvent.detected_at >= one_week_ago,
            ThermalEvent.latitude >= INDIA_LAT_MIN,
            ThermalEvent.latitude <= INDIA_LAT_MAX,
            ThermalEvent.longitude >= INDIA_LON_MIN,
            ThermalEvent.longitude <= INDIA_LON_MAX,
        )
        if is_demo is not None:
            today_q = today_q.filter(ThermalEvent.is_demo == is_demo)
            week_q = week_q.filter(ThermalEvent.is_demo == is_demo)

        events_today = today_q.count()
        events_this_week = week_q.count()

        return AnalyticsSummaryResponse(
            total_thermal_events=total_thermal_events,
            critical_events=critical_count,
            high_risk_events=high_risk_count,
            moderate_events=moderate_count,
            low_risk_events=low_risk_count,
            active_alerts=active_alerts,
            industrial_facilities=total_facilities,
            events_detected_today=events_today,
            events_detected_this_week=events_this_week,
            start_date=start_date,
            end_date=end_date,
        )

    def get_risk_distribution(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_demo: Optional[bool] = None,
    ) -> RiskDistributionResponse:
        """
        Group events by standardized risk priority bracket.
        """
        q = db.query(ThermalEvent).filter(
            ThermalEvent.latitude >= INDIA_LAT_MIN,
            ThermalEvent.latitude <= INDIA_LAT_MAX,
            ThermalEvent.longitude >= INDIA_LON_MIN,
            ThermalEvent.longitude <= INDIA_LON_MAX,
        )
        if is_demo is not None:
            q = q.filter(ThermalEvent.is_demo == is_demo)
        if start_date:
            q = q.filter(ThermalEvent.detected_at >= start_date)
        if end_date:
            q = q.filter(ThermalEvent.detected_at <= end_date)

        total_events = q.count()
        if total_events == 0:
            return RiskDistributionResponse(
                total_events=0,
                distribution=[
                    RiskDistributionItem(category="Critical", count=0, percentage=0.0, avg_risk_score=0.0),
                    RiskDistributionItem(category="High", count=0, percentage=0.0, avg_risk_score=0.0),
                    RiskDistributionItem(category="Moderate", count=0, percentage=0.0, avg_risk_score=0.0),
                    RiskDistributionItem(category="Low", count=0, percentage=0.0, avg_risk_score=0.0),
                ],
                start_date=start_date,
                end_date=end_date,
            )

        cond_critical = or_(
            ThermalEvent.risk_priority.ilike("%crit%"),
            and_(ThermalEvent.risk_priority.is_(None), ThermalEvent.risk_score >= 75.0),
        )
        cond_high = and_(
            ~cond_critical,
            or_(
                ThermalEvent.risk_priority.ilike("%high%"),
                and_(ThermalEvent.risk_score >= 50.0, ThermalEvent.risk_score < 75.0),
            ),
        )
        cond_moderate = and_(
            ~cond_critical,
            ~cond_high,
            or_(
                ThermalEvent.risk_priority.ilike("%mod%"),
                ThermalEvent.risk_priority.ilike("%med%"),
                and_(ThermalEvent.risk_score >= 25.0, ThermalEvent.risk_score < 50.0),
            ),
        )
        cond_low = and_(
            ~cond_critical,
            ~cond_high,
            ~cond_moderate,
        )

        brackets = [
            ("Critical", cond_critical),
            ("High", cond_high),
            ("Moderate", cond_moderate),
            ("Low", cond_low),
        ]

        items: List[RiskDistributionItem] = []
        for cat_name, cond in brackets:
            cat_q = q.filter(cond)
            count = cat_q.count()
            avg_q = db.query(func.avg(ThermalEvent.risk_score)).filter(cond)
            if is_demo is not None:
                avg_q = avg_q.filter(ThermalEvent.is_demo == is_demo)
            avg_score = avg_q.scalar() or 0.0
            pct = round((count / total_events) * 100.0, 1) if total_events > 0 else 0.0
            items.append(
                RiskDistributionItem(
                    category=cat_name,
                    count=count,
                    percentage=pct,
                    avg_risk_score=round(float(avg_score), 1),
                )
            )

        return RiskDistributionResponse(
            total_events=total_events,
            distribution=items,
            start_date=start_date,
            end_date=end_date,
        )

    def get_event_types(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_demo: Optional[bool] = None,
    ) -> EventTypeDistributionResponse:
        """
        Group events by hazard classification designation.
        """
        q = db.query(
            ThermalEvent.event_type,
            func.count(ThermalEvent.id).label("count"),
            func.avg(ThermalEvent.risk_score).label("avg_risk"),
        ).filter(
            ThermalEvent.latitude >= INDIA_LAT_MIN,
            ThermalEvent.latitude <= INDIA_LAT_MAX,
            ThermalEvent.longitude >= INDIA_LON_MIN,
            ThermalEvent.longitude <= INDIA_LON_MAX,
        )
        if is_demo is not None:
            q = q.filter(ThermalEvent.is_demo == is_demo)
        if start_date:
            q = q.filter(ThermalEvent.detected_at >= start_date)
        if end_date:
            q = q.filter(ThermalEvent.detected_at <= end_date)

        results = q.group_by(ThermalEvent.event_type).order_by(desc("count")).all()
        total_events = sum(r[1] for r in results) if results else 0

        items: List[EventTypeDistributionItem] = []
        for event_type, count, avg_risk in results:
            pct = round((count / total_events) * 100.0, 1) if total_events > 0 else 0.0
            items.append(
                EventTypeDistributionItem(
                    event_type=event_type or "Unknown Hazard",
                    count=count,
                    percentage=pct,
                    avg_risk_score=round(float(avg_risk or 0.0), 1),
                )
            )

        return EventTypeDistributionResponse(
            total_events=total_events,
            distribution=items,
            start_date=start_date,
            end_date=end_date,
        )

    def get_time_series(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "daily",
        is_demo: Optional[bool] = None,
    ) -> TimeSeriesResponse:
        """
        Aggregate chronological counts and average risk scores grouped by date.
        """
        cond_critical = or_(
            ThermalEvent.risk_priority.ilike("%crit%"),
            and_(ThermalEvent.risk_priority.is_(None), ThermalEvent.risk_score >= 75.0),
        )
        cond_high = and_(
            ~cond_critical,
            or_(
                ThermalEvent.risk_priority.ilike("%high%"),
                and_(ThermalEvent.risk_score >= 50.0, ThermalEvent.risk_score < 75.0),
            ),
        )
        cond_moderate = and_(
            ~cond_critical,
            ~cond_high,
            or_(
                ThermalEvent.risk_priority.ilike("%mod%"),
                ThermalEvent.risk_priority.ilike("%med%"),
                and_(ThermalEvent.risk_score >= 25.0, ThermalEvent.risk_score < 50.0),
            ),
        )
        cond_low = and_(
            ~cond_critical,
            ~cond_high,
            ~cond_moderate,
        )

        date_expr = func.date(ThermalEvent.detected_at)
        q = db.query(
            date_expr.label("event_date"),
            func.count(ThermalEvent.id).label("total"),
            func.sum(case((cond_critical, 1), else_=0)).label("critical"),
            func.sum(case((cond_high, 1), else_=0)).label("high"),
            func.sum(case((cond_moderate, 1), else_=0)).label("moderate"),
            func.sum(case((cond_low, 1), else_=0)).label("low"),
            func.avg(ThermalEvent.risk_score).label("avg_risk"),
        ).filter(
            ThermalEvent.latitude >= INDIA_LAT_MIN,
            ThermalEvent.latitude <= INDIA_LAT_MAX,
            ThermalEvent.longitude >= INDIA_LON_MIN,
            ThermalEvent.longitude <= INDIA_LON_MAX,
        )

        if is_demo is not None:
            q = q.filter(ThermalEvent.is_demo == is_demo)
        if start_date:
            q = q.filter(ThermalEvent.detected_at >= start_date)
        if end_date:
            q = q.filter(ThermalEvent.detected_at <= end_date)

        rows = q.group_by(date_expr).order_by(asc("event_date")).all()

        series: List[TimeSeriesDataPoint] = []
        total_events = 0

        for r in rows:
            date_str = str(r[0])
            t = int(r[1])
            total_events += t
            series.append(
                TimeSeriesDataPoint(
                    date=date_str,
                    total_events=t,
                    critical_events=int(r[2] or 0),
                    high_events=int(r[3] or 0),
                    moderate_events=int(r[4] or 0),
                    low_events=int(r[5] or 0),
                    avg_risk_score=round(float(r[6] or 0.0), 1),
                )
            )

        return TimeSeriesResponse(
            interval=interval,
            total_periods=len(series),
            total_events=total_events,
            series=series,
            start_date=start_date,
            end_date=end_date,
        )


_analytics_service_instance: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Dependency provider for AnalyticsService singleton."""
    global _analytics_service_instance
    if _analytics_service_instance is None:
        _analytics_service_instance = AnalyticsService()
    return _analytics_service_instance
