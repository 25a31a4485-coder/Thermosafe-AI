"""
Router for Reports and Compliance Intelligence Endpoints.
Supports generating structured JSON incident and audit reports,
multi-dimensional filtering (date range, region, risk priority, event type, facility),
database persistence, and CSV export.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.report import Report
from app.schemas.report import (
    ReportCreateRequest,
    ReportDetailResponse,
    ReportPaginatedResponse,
)
from app.services.report_service import ReportService, get_report_service

router = APIRouter(
    prefix="/reports",
    tags=["Reports & Compliance Intelligence"]
)


@router.post(
    "",
    response_model=ReportDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new structured intelligence report",
    description=(
        "Queries thermal incidents matching specified multi-dimensional filter criteria "
        "(date range, geographic region, risk priority, event hazard type, industrial facility), "
        "computes executive summary KPIs, stores report metadata in the database, and returns "
        "a structured JSON report payload."
    )
)
def create_report(
    payload: ReportCreateRequest,
    db: Session = Depends(get_db),
    report_service: ReportService = Depends(get_report_service),
) -> ReportDetailResponse:
    """
    Generate and persist a new thermal intelligence report.
    """
    return report_service.generate_report(db=db, req=payload)


@router.get(
    "",
    response_model=ReportPaginatedResponse,
    status_code=status.HTTP_200_OK,
    summary="List generated reports with pagination",
    description=(
        "Returns a paginated list of previously generated reports with metadata, "
        "applied filter parameters, executive summary KPIs, and generation timestamps."
    )
)
def list_reports(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    report_type: Optional[str] = Query(None, description="Filter by report category (e.g. incident_report)"),
    db: Session = Depends(get_db),
    report_service: ReportService = Depends(get_report_service),
) -> ReportPaginatedResponse:
    """
    List reports with pagination.
    """
    skip = (page - 1) * page_size
    return report_service.list_reports(db=db, skip=skip, limit=page_size, report_type=report_type)


@router.get(
    "/{report_id}",
    response_model=ReportDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve detailed structured report by ID",
    description=(
        "Retrieves a specific report by its primary key, returning the executive summary KPIs, "
        "applied filter parameters, all included incident records, and format export links."
    )
)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    report_service: ReportService = Depends(get_report_service),
) -> ReportDetailResponse:
    """
    Get detailed report by ID.
    """
    report = report_service.get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} was not found."
        )
    return report


@router.get(
    "/{report_id}/export",
    summary="Export report in specified format (CSV, PDF)",
    description=(
        "Streams the report content in a downloadable format. Currently supports CSV export. "
        "PDF export architecture is prepared for headless rendering integration."
    )
)
def export_report(
    report_id: int,
    format: str = Query("csv", description="Target export format: csv (supported) or pdf (planned)"),
    db: Session = Depends(get_db),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Export report to CSV or PDF download.
    """
    report_model = db.query(Report).filter(Report.id == report_id).first()
    if not report_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} was not found."
        )

    fmt_lower = format.strip().lower()
    if fmt_lower == "csv":
        csv_content = report_service.export_report_csv(report_model)
        filename = f"thermo_report_{report_id}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif fmt_lower == "pdf":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF export is architecturally planned for integration with a headless PDF rendering engine. Please use CSV export."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{format}'. Supported formats: csv."
        )
