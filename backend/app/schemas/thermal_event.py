import math
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from app.schemas.facility import IndustrialFacilityResponse
from app.schemas.ai_classification import AIClassificationResponse
from app.schemas.risk_assessment import RiskAssessmentResponse


class ThermalEventBase(BaseModel):
    event_id: Optional[str] = Field(None, description="Unique event identifier (e.g. EVT-2026-001)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate between -90.0 and +90.0")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate between -180.0 and +180.0")
    detected_at: Optional[datetime] = Field(None, description="Detection timestamp (defaults to current time)")
    event_type: str = Field(..., min_length=1, max_length=100, description="Type of thermal event")
    thermal_intensity: Optional[str] = Field(None, description="Thermal intensity or Radiative Power (MW)")
    persistence: Optional[str] = Field(None, description="Temporal persistence (e.g. Continuous, Transient)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Calculated composite risk score (0 to 100)")
    risk_priority: Optional[str] = Field(None, description="Risk priority category: CRITICAL, HIGH, MEDIUM, LOW")
    facility_id: Optional[int] = Field(None, description="Associated industrial facility ID")
    land_cover: Optional[str] = Field(None, description="Underlying land cover description")
    data_source: str = Field("NASA FIRMS", description="Originating telemetry / satellite source")
    status: str = Field("active", description="Operational status: active, contained, monitoring, resolved")
    is_demo: bool = Field(False, description="Flag indicating whether record is demonstration/simulated data")

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> Optional[float]:
        if v is not None:
            try:
                val = float(v)
                if val > 1.0:
                    val = val / 100.0
                return min(1.0, max(0.0, val))
            except (ValueError, TypeError):
                pass
        return v


class ThermalEventCreate(ThermalEventBase):
    pass


class ThermalEventUpdate(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude between -90.0 and +90.0")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude between -180.0 and +180.0")
    event_type: Optional[str] = Field(None, min_length=1, max_length=100)
    thermal_intensity: Optional[str] = None
    persistence: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    risk_priority: Optional[str] = None
    facility_id: Optional[int] = None
    land_cover: Optional[str] = None
    data_source: Optional[str] = None
    status: Optional[str] = None
    is_demo: Optional[bool] = None

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> Optional[float]:
        if v is not None:
            try:
                val = float(v)
                if val > 1.0:
                    val = val / 100.0
                return min(1.0, max(0.0, val))
            except (ValueError, TypeError):
                pass
        return v


class ThermalEventResponse(BaseModel):
    id: int
    event_id: str
    latitude: float
    longitude: float
    detected_at: datetime
    event_type: str
    thermal_intensity: Optional[str] = None
    persistence: Optional[str] = None
    confidence: Optional[float] = None
    risk_score: float
    risk_priority: str
    facility_id: Optional[int] = None
    land_cover: Optional[str] = None
    data_source: str
    status: str
    is_demo: bool = False
    created_at: datetime
    updated_at: datetime

    facility: Optional[IndustrialFacilityResponse] = None
    classifications: List[AIClassificationResponse] = []
    risk_assessments: List[RiskAssessmentResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> Optional[float]:
        if v is not None:
            try:
                val = float(v)
                if val > 1.0:
                    val = val / 100.0
                return min(1.0, max(0.0, val))
            except (ValueError, TypeError):
                pass
        return v

    @computed_field
    @property
    def ai_classification(self) -> Optional[AIClassificationResponse]:
        """Returns the primary or most recent AI classification."""
        if self.classifications and len(self.classifications) > 0:
            return self.classifications[-1]
        return None

    @computed_field
    @property
    def brightness(self) -> Optional[str]:
        """Brightness / Radiative Power (MW)."""
        return self.thermal_intensity or "N/A"

    @computed_field
    @property
    def acquisitionDate(self) -> Optional[str]:
        """Acquisition date (YYYY-MM-DD)."""
        if self.detected_at:
            return self.detected_at.strftime("%Y-%m-%d")
        return None

    @computed_field
    @property
    def acquisitionTime(self) -> Optional[str]:
        """Acquisition time (HH:MM UTC)."""
        if self.detected_at:
            return self.detected_at.strftime("%H:%M UTC")
        return None

    @computed_field
    @property
    def satellite(self) -> str:
        """Satellite sensor platform."""
        ds = (self.data_source or "").lower()
        if "noaa21" in ds:
            return "NOAA-21 (JPSS-2)"
        elif "noaa20" in ds:
            return "NOAA-20 (JPSS-1)"
        elif "snpp" in ds:
            return "Suomi-NPP"
        elif "modis" in ds:
            return "Terra/Aqua (MODIS)"
        return "VIIRS NOAA-21"

    @computed_field
    @property
    def instrument(self) -> str:
        """Sensor instrument."""
        if "modis" in (self.data_source or "").lower():
            return "MODIS"
        return "VIIRS"

    @computed_field
    @property
    def source(self) -> str:
        """Originating telemetry source."""
        return self.data_source or "NASA FIRMS"

    @computed_field
    @property
    def location(self) -> str:
        """Normalized geographical location description."""
        if self.facility and self.facility.name:
            return self.facility.name
        return f"India ({self.latitude:.3f}°N, {self.longitude:.3f}°E)"


    @computed_field
    @property
    def industrial_natural_group(self) -> str:
        """Segregation group: INDUSTRIAL, NATURAL/FOREST, OTHER, UNKNOWN."""
        if self.classifications and len(self.classifications) > 0:
            c = (self.classifications[-1].classification or "").lower()
            if "forest" in c or "wildfire" in c or "agricultural" in c:
                return "NATURAL/FOREST"
            elif "industrial" in c or "flare" in c or "mining" in c or "refinery" in c or "power" in c:
                return "INDUSTRIAL"
            elif "low-risk" in c or "other" in c:
                return "OTHER"
            elif "unknown" in c:
                return "UNKNOWN"
        etype = (self.event_type or "").lower()
        if "forest" in etype or "wildfire" in etype or "agricultural" in etype:
            return "NATURAL/FOREST"
        if "industrial" in etype or "flare" in etype or "mining" in etype or self.facility_id:
            return "INDUSTRIAL"
        return "UNKNOWN"

    @computed_field
    @property
    def persistence_status(self) -> str:
        """Persistence category: ONE_TIME_EVENT, REPEATED_ACTIVITY, PERSISTENT_SOURCE."""
        p = (self.persistence or "").lower()
        if "continuous" in p or "persistent" in p or "36+" in p or "90+" in p:
            return "PERSISTENT_SOURCE"
        elif "recurrent" in p or "semi-continuous" in p or "8 hour" in p or "repeated" in p:
            return "REPEATED_ACTIVITY"
        return "ONE_TIME_EVENT"

    @computed_field
    @property
    def distance_km(self) -> Optional[float]:
        """Calculates distance to associated facility in km if facility exists."""
        if self.facility and self.facility.latitude and self.facility.longitude:
            R = 6371.0
            dlat = math.radians(self.facility.latitude - self.latitude)
            dlon = math.radians(self.facility.longitude - self.longitude)
            a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(self.latitude)) * math.cos(math.radians(self.facility.latitude)) * math.sin(dlon / 2.0) ** 2
            c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
            return round(R * c, 2)
        return None

    @computed_field
    @property
    def nearest_facility(self) -> Optional[Dict[str, Any]]:
        """Associated facility summary if available."""
        if self.facility:
            return {
                "id": self.facility.id,
                "name": self.facility.name,
                "facility_type": self.facility.industry_type,
                "operator": self.facility.operator,
                "distance_km": self.distance_km,
                "association_reason": f"Proximity within {self.distance_km or 0.0} km of active facility infrastructure (contextual association, not confirmed causation).",
                "association_confidence": max(0.1, min(0.95, 1.0 - ((self.distance_km or 0.0) / 10.0))) if self.distance_km is not None else 0.5
            }
        return None

    @computed_field
    @property
    def evidence(self) -> Dict[str, Any]:
        """Structured evidence summary for analysis view."""
        return {
            "thermal_intensity": self.thermal_intensity,
            "persistence": self.persistence,
            "land_cover": self.land_cover,
            "confidence": self.confidence,
            "data_source": self.data_source,
            "classification": self.event_type,
            "industrial_natural_group": self.industrial_natural_group,
            "persistence_status": self.persistence_status,
            "nearest_facility": self.facility.name if self.facility else None,
            "distance_km": self.distance_km
        }

    @computed_field
    @property
    def classification_timestamp(self) -> datetime:
        """Timestamp of classification."""
        if self.classifications and len(self.classifications) > 0:
            return self.classifications[-1].created_at
        return self.created_at

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
                "event_id": self.event_id,
                "event_type": self.event_type,
                "thermal_intensity": self.thermal_intensity,
                "risk_score": self.risk_score,
                "risk_priority": self.risk_priority,
                "status": self.status,
                "is_demo": self.is_demo,
                "industrial_natural_group": self.industrial_natural_group,
                "persistence_status": self.persistence_status,
                "facility_name": self.facility.name if self.facility else None,
                "distance_km": self.distance_km
            }
        }



class ThermalEventPaginatedResponse(BaseModel):
    total: int = Field(..., description="Total count of matching events")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total available pages")
    has_next: bool = Field(..., description="Whether a subsequent page exists")
    has_prev: bool = Field(..., description="Whether a preceding page exists")
    items: List[ThermalEventResponse] = Field(..., description="List of thermal events")
