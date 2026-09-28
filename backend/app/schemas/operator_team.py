from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class OperatorTeamBase(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Team official designation")
    team_name: Optional[str] = Field(None, max_length=255, description="Team official designation")
    organization_name: Optional[str] = Field("Industrial Emergency Command", max_length=255, description="Parent organization or operator")
    team_type: str = Field("Industrial Fire Brigade", max_length=100, description="Specialty: Industrial Fire Brigade, Hazmat Response, Medical, Disaster Unit")
    industry_type: Optional[str] = Field(None, max_length=100, description="Industrial sector classification")
    facility_id: Optional[int] = Field(None, description="Primary industrial facility association ID")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Station/Base latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Station/Base longitude")
    contact_person: Optional[str] = Field(None, max_length=255, description="Team leader or duty officer name")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Emergency dispatch telephone or hot-line")
    phone: Optional[str] = Field(None, max_length=50, description="Emergency dispatch telephone or hot-line")
    contact_email: Optional[str] = Field(None, max_length=255, description="Emergency notification email")
    email: Optional[str] = Field(None, max_length=255, description="Emergency notification email")
    radio_frequency: Optional[str] = Field("VHF 156.800 MHz (Ch 16)", max_length=50, description="Operational tactical radio frequency")
    coverage_radius_km: float = Field(50.0, gt=0, le=500.0, description="Operational emergency response radius in km")
    response_radius_km: Optional[float] = Field(None, gt=0, le=500.0, description="Response radius in km")
    notification_enabled: bool = Field(True, description="Whether automated emergency alerts are dispatched to this team")
    call_escalation_enabled: bool = Field(True, description="Whether phone call escalation is enabled for high/critical alerts")
    is_active: bool = Field(True, description="Whether team is active")
    status: str = Field("available", max_length=50, description="Operational status: available, dispatched, on_call, off_duty")
    is_demo: bool = Field(False, description="Whether record is demo data")
    specialization: Optional[str] = Field(None, max_length=100, description="Team specialization e.g. Industrial Fire, Hazmat")
    team_email: Optional[str] = None
    team_phone: Optional[str] = None
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None
    team_members: Optional[List[str]] = None

    @model_validator(mode="after")
    def sync_aliases(self):
        # Sync name & team_name
        if not self.name and self.team_name:
            self.name = self.team_name
        elif not self.team_name and self.name:
            self.team_name = self.name
        elif not self.name and not self.team_name:
            self.name = "Industrial Emergency Unit"
            self.team_name = "Industrial Emergency Unit"

        # Sync phone & contact_phone & team_phone
        chosen_phone = self.team_phone or self.phone or self.contact_phone or "+91-288-2234-911"
        self.phone = chosen_phone
        self.contact_phone = chosen_phone
        self.team_phone = chosen_phone

        # Sync email & contact_email & team_email
        chosen_email = self.team_email or self.email or self.contact_email
        self.email = chosen_email
        self.contact_email = chosen_email
        self.team_email = chosen_email

        # Sync specialization & team_type
        if self.specialization and not self.team_type:
            self.team_type = self.specialization
        elif self.team_type and not self.specialization:
            self.specialization = self.team_type

        # Sync facility_type & industry_type
        if self.facility_type and not self.industry_type:
            self.industry_type = self.facility_type
        elif self.industry_type and not self.facility_type:
            self.facility_type = self.industry_type

        # Sync response_radius_km & coverage_radius_km
        if self.response_radius_km is not None and self.coverage_radius_km == 50.0:
            self.coverage_radius_km = self.response_radius_km
        elif self.response_radius_km is None:
            self.response_radius_km = self.coverage_radius_km

        # Sync industry_type & team_type
        if not self.industry_type and self.team_type:
            self.industry_type = self.team_type
        elif not self.team_type and self.industry_type:
            self.team_type = self.industry_type

        return self


class OperatorTeamCreate(OperatorTeamBase):
    assigned_user_ids: Optional[List[int]] = None


class OperatorTeamUpdate(BaseModel):
    name: Optional[str] = None
    team_name: Optional[str] = None
    organization_name: Optional[str] = None
    team_type: Optional[str] = None
    specialization: Optional[str] = None
    industry_type: Optional[str] = None
    facility_type: Optional[str] = None
    facility_id: Optional[int] = None
    facility_name: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    phone: Optional[str] = None
    team_phone: Optional[str] = None
    contact_email: Optional[str] = None
    email: Optional[str] = None
    team_email: Optional[str] = None
    radio_frequency: Optional[str] = None
    coverage_radius_km: Optional[float] = Field(None, gt=0, le=500.0)
    response_radius_km: Optional[float] = Field(None, gt=0, le=500.0)
    notification_enabled: Optional[bool] = None
    call_escalation_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None
    is_demo: Optional[bool] = None
    team_members: Optional[List[str]] = None
    assigned_user_ids: Optional[List[int]] = None


class OperatorTeamResponse(OperatorTeamBase):
    id: int
    facility_name: Optional[str] = None
    assigned_users: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def geojson(self) -> Dict[str, Any]:
        """Map-compatible GeoJSON Feature object representation."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "id": self.id,
                "name": self.team_name or self.name,
                "team_name": self.team_name or self.name,
                "organization_name": self.organization_name,
                "team_type": self.team_type,
                "industry_type": self.industry_type,
                "facility_id": self.facility_id,
                "facility_name": self.facility_name,
                "status": self.status,
                "is_active": self.is_active,
                "notification_enabled": self.notification_enabled,
                "contact_phone": self.phone or self.contact_phone,
                "phone": self.phone or self.contact_phone,
                "email": self.email or self.contact_email,
                "radio_frequency": self.radio_frequency,
                "coverage_radius_km": self.response_radius_km or self.coverage_radius_km,
                "response_radius_km": self.response_radius_km or self.coverage_radius_km,
            }
        }


class OperatorTeamNearbyItem(BaseModel):
    team: OperatorTeamResponse
    distance_km: float
    is_within_coverage: bool

    model_config = ConfigDict(from_attributes=True)


class OperatorTeamNearbyResponse(BaseModel):
    total: int
    query_latitude: float
    query_longitude: float
    radius_km: float
    items: List[OperatorTeamNearbyItem]


class EmergencyDispatchLogCreate(BaseModel):
    team_id: int
    thermal_event_id: Optional[int] = None
    alert_id: Optional[int] = None
    event_id: Optional[str] = None
    distance_km: float
    risk_priority: str
    risk_score: Optional[float] = None
    dispatch_channel: str = "AUTOMATED_SMS"
    status: str = "DISPATCHED"
    message: str


class EmergencyDispatchLogResponse(BaseModel):
    id: int
    team_id: int
    thermal_event_id: Optional[int] = None
    alert_id: Optional[int] = None
    event_id: Optional[str] = None
    distance_km: float
    risk_priority: str
    risk_score: Optional[float] = None
    dispatch_channel: str
    status: str
    message: str
    dispatched_at: datetime
    team: Optional[OperatorTeamResponse] = None

    model_config = ConfigDict(from_attributes=True)
