from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AIClassificationBase(BaseModel):
    thermal_event_id: int
    classification: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: Optional[str] = None
    model_name: str = "ThermalWatch-AI-v1"

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> float:
        if v is not None:
            try:
                val = float(v)
                if val > 1.0:
                    val = val / 100.0
                return min(1.0, max(0.0, val))
            except (ValueError, TypeError):
                pass
        return 0.5


class AIClassificationCreate(AIClassificationBase):
    pass


class AIClassificationResponse(AIClassificationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIClassifyRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate between -90.0 and +90.0")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate between -180.0 and +180.0")
    thermal_intensity: str = Field(..., min_length=1, description="Thermal intensity string or numeric (e.g. '1250 MW', 'Critical', '45 MW')")
    persistence: str = Field(..., min_length=1, description="Persistence temporal description (e.g. 'Continuous', 'Transient', 'Recurrent')")
    nearby_industrial_facility: Optional[str] = Field(None, description="Designation of nearby industrial facility if identified")
    facility_id: Optional[int] = Field(None, description="Optional associated facility ID")
    facility_type: Optional[str] = Field(None, description="Optional facility category/type")
    facility_distance_km: Optional[float] = Field(None, description="Distance to facility in km if pre-calculated")
    land_cover: Optional[str] = Field(None, description="Underlying land cover (e.g. 'Heavy Industrial Zone', 'Forest', 'Agricultural')")
    historical_occurrences: Optional[int] = Field(0, ge=0, description="Count of historical thermal detections in the local vicinity")
    data_source: Optional[str] = Field("NASA FIRMS", description="Originating satellite sensor or telemetry feed")
    firms_confidence: Optional[float] = Field(None, ge=0.0, le=100.0, description="FIRMS raw confidence")
    brightness_temperature_k: Optional[float] = Field(None, description="Brightness temperature in Kelvin")


class AIClassifyResponse(BaseModel):
    classification: str = Field(..., description="Classification category (e.g. 'Critical Industrial Fire', 'Gas Flare', 'Low-Risk Thermal Activity')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score strictly between 0.0 and 1.0")
    explanation: str = Field(..., description="Transparent deterministic explanation of rule execution and telemetry analysis")
    model_name: str = Field(..., description="Model identifier explicitly denoting rule-based prototype engine")

    # SIH26162 Taxonomy & Segregation Requirements
    taxonomy_code: str = Field("INDUSTRIAL_FIRE", description="Canonical taxonomy code: INDUSTRIAL_FIRE, FOREST_OR_WILDFIRE, AGRICULTURAL_BURNING, GAS_FLARE, MINING_THERMAL_ACTIVITY, PERSISTENT_INDUSTRIAL_THERMAL_SOURCE, OTHER_THERMAL_EVENT, UNKNOWN")
    taxonomy_label: str = Field("Industrial Fire", description="Human-readable taxonomy label")
    industrial_natural_group: str = Field("INDUSTRIAL", description="Segregation group: INDUSTRIAL, NATURAL/FOREST, OTHER, UNKNOWN")
    reason: Optional[str] = Field(None, description="Evidence-based classification rationale")
    supporting_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Structured supporting evidence factors")
    facility_association: Optional[Dict[str, Any]] = Field(None, description="Facility proximity and association evidence")
    persistence_status: str = Field("ONE_TIME_EVENT", description="Persistence classification: ONE_TIME_EVENT, REPEATED_ACTIVITY, PERSISTENT_SOURCE")
    classification_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of classification")

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> float:
        if v is not None:
            try:
                val = float(v)
                if val > 1.0:
                    val = val / 100.0
                return min(1.0, max(0.0, val))
            except (ValueError, TypeError):
                pass
        return 0.5

