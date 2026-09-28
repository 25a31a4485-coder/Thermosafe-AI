from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, computed_field


class AlertBase(BaseModel):
    user_id: Optional[int] = Field(None, description="Optional target user ID")
    thermal_event_id: Optional[int] = Field(None, description="Associated thermal event integer DB ID")
    assigned_team_id: Optional[int] = Field(None, description="Assigned operator response team ID")
    event_id: Optional[str] = Field(None, description="Alphanumeric Event identifier (e.g. DEMO-EVT-001)")
    title: str = Field(..., min_length=1, max_length=255, description="Alert title/header")
    message: str = Field(..., min_length=1, description="Detailed incident message and context")
    severity: str = Field(..., description="Alert severity: Critical, High, Moderate, Low")
    risk_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Composite risk score (0 to 100)")
    risk_priority: Optional[str] = Field(None, description="Risk priority category: Critical, High, Moderate, Low")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude coordinate between -90 and +90")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude coordinate between -180 and +180")
    event_type: Optional[str] = Field(None, max_length=100, description="Type of detected thermal hazard")
    status: str = Field("ACTIVE", description="Alert status: ACTIVE, ACKNOWLEDGED, RESOLVED")
    delivery_status: str = Field("SENT", description="Notification delivery status: PENDING, SENT, DELIVERED, FAILED, NO_NEARBY_TEAM, CONFIGURATION_REQUIRED")
    is_read: bool = Field(False, description="Read/acknowledged status")
    is_acknowledged: bool = Field(False, description="Explicit operator acknowledgement status")
    acknowledged_at: Optional[datetime] = Field(None, description="Timestamp when operator acknowledged alert")
    acknowledged_by: Optional[str] = Field(None, description="Name of operator who acknowledged alert")
    acknowledged_by_user_id: Optional[int] = Field(None, description="User ID of acknowledging operator")


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    is_read: Optional[bool] = Field(None, description="Mark alert as read or unread")
    is_acknowledged: Optional[bool] = Field(None, description="Mark alert as acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Acknowledging operator name")


class AlertAcknowledgeRequest(BaseModel):
    operator_name: Optional[str] = Field(None, description="Optional override name for operator")
    notes: Optional[str] = Field(None, description="Optional acknowledgement notes")


class AlertResponse(AlertBase):
    id: int = Field(..., description="Unique alert identifier")
    created_at: datetime = Field(..., description="Timestamp when alert was generated")

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def geojson(self) -> Optional[Dict[str, Any]]:
        """Map-compatible GeoJSON Point representation if coordinates exist."""
        if self.latitude is not None and self.longitude is not None:
            return {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [self.longitude, self.latitude]
                },
                "properties": {
                    "alert_id": self.id,
                    "event_id": self.event_id,
                    "title": self.title,
                    "severity": self.severity,
                    "risk_priority": self.risk_priority,
                    "is_read": self.is_read
                }
            }
        return None


class AlertUnreadResponse(BaseModel):
    unread_count: int = Field(..., ge=0, description="Total number of active unread alerts")
    items: List[AlertResponse] = Field(..., description="List of unread alerts")


class AlertPaginatedResponse(BaseModel):
    total: int = Field(..., ge=0, description="Total alerts count matching query")
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(20, ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total available pages")
    items: List[AlertResponse] = Field(..., description="List of alert items")


class NotificationDeliveryLogResponse(BaseModel):
    id: int
    alert_id: Optional[int] = None
    event_id: Optional[str] = None
    team_id: Optional[int] = None
    user_id: Optional[int] = None
    notification_type: str
    risk_priority: Optional[str] = None
    dedup_key: Optional[str] = None
    channel: str
    status: str
    title: Optional[str] = None
    body: Optional[str] = None
    payload_json: Optional[str] = None
    provider_response: Optional[str] = None
    failure_reason: Optional[str] = None
    retry_count: int = 0
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertEvaluationRequest(BaseModel):
    """
    Payload for evaluating whether a thermal event should trigger an alert.
    Triggers when risk_priority is 'High' or 'Critical'.
    """
    event_id: Optional[str] = Field(None, description="Event identifier")
    thermal_event_id: Optional[int] = Field(None, description="Database integer ID of thermal event")
    risk_priority: str = Field(..., description="Risk category: Critical, High, Moderate, Low")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Risk score (0-100)")
    event_type: str = Field(..., description="Classification designation")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    thermal_intensity: Optional[str] = Field(None, description="Thermal radiative power or intensity")
    facility_name: Optional[str] = Field(None, description="Name of nearby facility if known")
    custom_message: Optional[str] = Field(None, description="Optional custom alert message override")
