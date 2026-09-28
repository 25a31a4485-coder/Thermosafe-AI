from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field


class ReportFilterParameters(BaseModel):
    """
    Multi-dimensional filter criteria for generating incident and compliance reports.
    """
    start_date: Optional[datetime] = Field(None, description="Start date filter (ISO format)")
    end_date: Optional[datetime] = Field(None, description="End date filter (ISO format)")
    region: Optional[str] = Field(None, description="Geographic region, corridor, or state (e.g. Gujarat, Maharashtra)")
    risk_priority: Optional[str] = Field(None, description="Risk priority filter: Critical, High, Moderate, Low")
    event_type: Optional[str] = Field(None, description="Hazard type (e.g. Critical Industrial Fire, Gas Flare)")
    facility_id: Optional[int] = Field(None, description="Filter incidents associated with a specific facility ID")
    facility_name: Optional[str] = Field(None, description="Filter incidents matching a facility name keyword")


class ReportCreateRequest(BaseModel):
    """
    Request payload to generate a new structured intelligence report.
    """
    title: Optional[str] = Field(None, description="Custom report title (auto-generated if omitted)")
    report_type: str = Field("incident_report", description="Report category: incident_report, facility_audit, regional_summary")
    filters: Optional[ReportFilterParameters] = Field(default_factory=ReportFilterParameters, description="Filter criteria")
    format: str = Field("json", description="Target output format: json (default), csv, pdf")


class ReportSummaryKPIs(BaseModel):
    """
    Executive statistics computed for the generated report.
    """
    total_incidents: int = Field(0, description="Total matching thermal anomalies")
    critical_count: int = Field(0, description="Count of critical hazard incidents")
    high_count: int = Field(0, description="Count of high risk incidents")
    moderate_count: int = Field(0, description="Count of moderate risk incidents")
    low_count: int = Field(0, description="Count of low risk incidents")
    avg_risk_score: float = Field(0.0, description="Average risk score across matching incidents")
    highest_risk_score: float = Field(0.0, description="Peak risk score recorded in the sample")
    facilities_involved: int = Field(0, description="Count of distinct facilities impacted")


class ReportBase(BaseModel):
    user_id: Optional[int] = None
    report_type: str = "incident_report"
    title: str
    status: str = "completed"
    parameters: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None


class ReportCreate(ReportBase):
    content: Optional[List[Dict[str, Any]]] = None


class ReportResponse(ReportBase):
    id: int
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportDetailResponse(ReportResponse):
    """
    Full structured report response including incident records and export capabilities.
    """
    incidents: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed incident records")
    available_exports: Dict[str, str] = Field(default_factory=dict, description="Links to export in various formats")


class ReportPaginatedResponse(BaseModel):
    total: int = Field(..., ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1)
    total_pages: int = Field(..., ge=0)
    items: List[ReportResponse]
