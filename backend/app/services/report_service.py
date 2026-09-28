"""
Reporting and Compliance Intelligence Service for SIH26162.
Provides multi-dimensional querying, executive KPI aggregation,
database-backed persistence, and extensible export capabilities (CSV, JSON, and future PDF).
"""

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import or_, and_, desc
from sqlalchemy.orm import Session, joinedload

from app.core.spatial import INDIA_LAT_MIN, INDIA_LAT_MAX, INDIA_LON_MIN, INDIA_LON_MAX
from app.models.report import Report
from app.models.thermal_event import ThermalEvent
from app.models.facility import IndustrialFacility
from app.schemas.report import (
    ReportFilterParameters,
    ReportCreateRequest,
    ReportSummaryKPIs,
    ReportResponse,
    ReportDetailResponse,
    ReportPaginatedResponse,
)

logger = logging.getLogger("report_service")


class ReportService:
    """
    Service responsible for querying thermal incidents across multiple dimensions,
    generating executive summaries, persisting report metadata, and exporting reports.
    """

    def generate_report(
        self,
        db: Session,
        req: ReportCreateRequest,
        user_id: Optional[int] = None,
    ) -> ReportDetailResponse:
        """
        Query incidents matching filter criteria, compute summary statistics,
        persist the generated report record in the database, and return detailed results.
        """
        filters = req.filters or ReportFilterParameters()

        # Build base query joining facility for deep inspection, restricted to India
        query = db.query(ThermalEvent).options(joinedload(ThermalEvent.facility)).filter(
            ThermalEvent.latitude >= INDIA_LAT_MIN,
            ThermalEvent.latitude <= INDIA_LAT_MAX,
            ThermalEvent.longitude >= INDIA_LON_MIN,
            ThermalEvent.longitude <= INDIA_LON_MAX,
        )

        # Temporal slicing
        if filters.start_date:
            query = query.filter(ThermalEvent.detected_at >= filters.start_date)
        if filters.end_date:
            query = query.filter(ThermalEvent.detected_at <= filters.end_date)

        # Risk priority filtering
        if filters.risk_priority:
            p_clean = filters.risk_priority.strip().lower()
            query = query.filter(ThermalEvent.risk_priority.ilike(f"%{p_clean}%"))

        # Event hazard type filtering
        if filters.event_type:
            t_clean = filters.event_type.strip().lower()
            query = query.filter(ThermalEvent.event_type.ilike(f"%{t_clean}%"))

        # Facility ID filtering
        if filters.facility_id is not None:
            query = query.filter(ThermalEvent.facility_id == filters.facility_id)

        # Facility Name or Region filtering requires joining IndustrialFacility
        needs_facility_join = bool(filters.facility_name or filters.region)
        if needs_facility_join:
            query = query.outerjoin(IndustrialFacility, ThermalEvent.facility_id == IndustrialFacility.id)

        if filters.facility_name:
            fn_clean = filters.facility_name.strip()
            query = query.filter(
                or_(
                    IndustrialFacility.name.ilike(f"%{fn_clean}%"),
                    IndustrialFacility.operator.ilike(f"%{fn_clean}%"),
                )
            )

        if filters.region:
            reg_clean = filters.region.strip()
            query = query.filter(
                or_(
                    IndustrialFacility.address.ilike(f"%{reg_clean}%"),
                    ThermalEvent.land_cover.ilike(f"%{reg_clean}%"),
                )
            )

        # Order by newest detections first
        events: List[ThermalEvent] = query.order_by(desc(ThermalEvent.detected_at)).all()

        # Calculate Executive Summary KPIs
        total_incidents = len(events)
        critical_count = 0
        high_count = 0
        moderate_count = 0
        low_count = 0
        risk_scores: List[float] = []
        distinct_facilities = set()

        incidents_data: List[Dict[str, Any]] = []

        for e in events:
            score = float(e.risk_score or 0.0)
            risk_scores.append(score)
            p_str = (e.risk_priority or "").lower()

            # Categorize based on priority label and score
            if "crit" in p_str or score >= 75.0:
                critical_count += 1
            elif "high" in p_str or score >= 50.0:
                high_count += 1
            elif "mod" in p_str or score >= 25.0:
                moderate_count += 1
            else:
                low_count += 1

            if e.facility_id is not None:
                distinct_facilities.add(e.facility_id)

            incidents_data.append({
                "id": e.id,
                "event_id": e.event_id,
                "detected_at": e.detected_at.isoformat() if e.detected_at else None,
                "event_type": e.event_type,
                "thermal_intensity": e.thermal_intensity,
                "persistence": e.persistence,
                "confidence": e.confidence,
                "risk_score": e.risk_score,
                "risk_priority": e.risk_priority,
                "facility_id": e.facility_id,
                "facility_name": e.facility.name if e.facility else None,
                "facility_operator": e.facility.operator if e.facility else None,
                "facility_type": e.facility.industry_type if e.facility else None,
                "facility_address": e.facility.address if e.facility else None,
                "land_cover": e.land_cover,
                "latitude": e.latitude,
                "longitude": e.longitude,
                "data_source": e.data_source,
                "status": e.status,
            })

        avg_risk_score = round(sum(risk_scores) / total_incidents, 1) if total_incidents > 0 else 0.0
        highest_risk_score = round(max(risk_scores), 1) if risk_scores else 0.0

        summary_kpis = ReportSummaryKPIs(
            total_incidents=total_incidents,
            critical_count=critical_count,
            high_count=high_count,
            moderate_count=moderate_count,
            low_count=low_count,
            avg_risk_score=avg_risk_score,
            highest_risk_score=highest_risk_score,
            facilities_involved=len(distinct_facilities),
        )

        # Generate report title if not provided
        now_utc = datetime.now(timezone.utc)
        if req.title and req.title.strip():
            title = req.title.strip()
        else:
            time_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
            filter_tags = []
            if filters.risk_priority:
                filter_tags.append(filters.risk_priority)
            if filters.region:
                filter_tags.append(filters.region)
            if filters.facility_name:
                filter_tags.append(filters.facility_name)
            tag_str = f" ({', '.join(filter_tags)})" if filter_tags else ""
            title = f"Thermal Incident Intelligence Report{tag_str} - {time_str}"

        # Serialize applied filter parameters
        params_dict = {
            k: (v.isoformat() if isinstance(v, datetime) else v)
            for k, v in filters.model_dump().items()
            if v is not None
        }

        # Persist report in database
        report = Report(
            user_id=user_id,
            report_type=req.report_type or "incident_report",
            title=title,
            parameters=params_dict,
            summary=summary_kpis.model_dump(),
            content=incidents_data,
            status="completed",
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        logger.info(
            f"Generated Report id={report.id} title='{report.title}' with {total_incidents} incidents"
        )

        return self._format_detail_response(report)

    def get_report_by_id(self, db: Session, report_id: int) -> Optional[ReportDetailResponse]:
        """
        Retrieve a single report by primary key.
        """
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return None
        return self._format_detail_response(report)

    def list_reports(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        report_type: Optional[str] = None,
    ) -> ReportPaginatedResponse:
        """
        List generated reports with pagination and optional type filter.
        """
        query = db.query(Report)
        if report_type:
            query = query.filter(Report.report_type == report_type)

        total = query.count()
        reports = query.order_by(desc(Report.generated_at)).offset(skip).limit(limit).all()

        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        items = [ReportResponse.model_validate(r) for r in reports]

        return ReportPaginatedResponse(
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
            items=items,
        )

    def export_report_csv(self, report_model: Report) -> str:
        """
        Generate a standardized CSV representation of incidents in a report.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header row
        headers = [
            "Incident ID",
            "Event Reference",
            "Detected At",
            "Event Type",
            "Risk Priority",
            "Risk Score",
            "Thermal Intensity",
            "Persistence",
            "Confidence",
            "Facility Name",
            "Facility Operator",
            "Facility Type",
            "Facility Address",
            "Land Cover",
            "Latitude",
            "Longitude",
            "Data Source",
            "Status",
        ]
        writer.writerow(headers)

        incidents: List[Dict[str, Any]] = report_model.content or []
        for inc in incidents:
            writer.writerow([
                inc.get("id", ""),
                inc.get("event_id", ""),
                inc.get("detected_at", ""),
                inc.get("event_type", ""),
                inc.get("risk_priority", ""),
                inc.get("risk_score", ""),
                inc.get("thermal_intensity", ""),
                inc.get("persistence", ""),
                inc.get("confidence", ""),
                inc.get("facility_name", "") or "",
                inc.get("facility_operator", "") or "",
                inc.get("facility_type", "") or "",
                inc.get("facility_address", "") or "",
                inc.get("land_cover", "") or "",
                inc.get("latitude", ""),
                inc.get("longitude", ""),
                inc.get("data_source", ""),
                inc.get("status", ""),
            ])

        return output.getvalue()

    def _format_detail_response(self, report: Report) -> ReportDetailResponse:
        """
        Helper to construct a comprehensive ReportDetailResponse.
        """
        return ReportDetailResponse(
            id=report.id,
            user_id=report.user_id,
            report_type=report.report_type,
            title=report.title,
            status=report.status,
            parameters=report.parameters,
            summary=report.summary,
            generated_at=report.generated_at,
            incidents=report.content or [],
            available_exports={
                "csv": f"/api/reports/{report.id}/export?format=csv",
                "pdf": f"/api/reports/{report.id}/export?format=pdf (Planned)",
                "json": f"/api/reports/{report.id}",
            },
        )


_report_service_instance = ReportService()


def get_report_service() -> ReportService:
    """Dependency injection provider for ReportService."""
    return _report_service_instance
