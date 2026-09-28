from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskAssessmentBase(BaseModel):
    thermal_event_id: int
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_priority: str
    thermal_factor: Optional[float] = None
    persistence_factor: Optional[float] = None
    industrial_proximity_factor: Optional[float] = None
    population_proximity_factor: Optional[float] = None
    historical_factor: Optional[float] = None
    explanation: Optional[str] = None
    methodology: Optional[str] = None


class RiskAssessmentCreate(RiskAssessmentBase):
    pass


class RiskAssessmentResponse(RiskAssessmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskAnalysisRequest(BaseModel):
    thermal_intensity: str = Field(..., min_length=1, description="Thermal intensity string or MW value (e.g. '1250 MW', 'Critical', '45 MW')")
    persistence: str = Field(..., min_length=1, description="Duration or recurrence pattern (e.g. 'Continuous (36h)', 'Transient', 'Recurrent')")
    industrial_facility_proximity_km: Optional[float] = Field(None, ge=0.0, description="Distance to nearest industrial facility in km")
    nearby_industrial_facility: Optional[str] = Field(None, description="Designation of nearby industrial facility if known")
    population_proximity_km: Optional[float] = Field(None, ge=0.0, description="Distance to nearest populated settlement or residential zone in km")
    historical_recurrence: Optional[int] = Field(0, ge=0, description="Number of historical thermal anomalies in the cluster radius")
    ai_classification: Optional[str] = Field(None, description="Classification from AI engine (e.g. 'Critical Industrial Fire', 'Gas Flare')")
    event_type: Optional[str] = Field(None, description="Reported event type designation")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude coordinate between -90.0 and +90.0")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude coordinate between -180.0 and +180.0")


class RiskAnalysisResponse(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Calculated composite risk score on a 0 to 100 scale")
    risk_priority: str = Field(..., description="Risk category: Low (0–24), Moderate (25–49), High (50–74), Critical (75–100)")
    thermal_factor: float = Field(..., ge=0.0, le=100.0, description="Thermal intensity sub-score factor (0 to 100)")
    persistence_factor: float = Field(..., ge=0.0, le=100.0, description="Temporal persistence sub-score factor (0 to 100)")
    industrial_proximity_factor: float = Field(..., ge=0.0, le=100.0, description="Industrial facility proximity factor (0 to 100)")
    population_proximity_factor: float = Field(..., ge=0.0, le=100.0, description="Population proximity exposure factor (0 to 100)")
    historical_factor: float = Field(..., ge=0.0, le=100.0, description="Historical recurrence factor (0 to 100)")
    explanation: str = Field(..., description="Detailed breakdown of scoring rationale and heuristic sub-scores")
    methodology: str = Field(
        "ThermalSafe Prototype Risk Index v1.0 (Experimental Heuristic Model - Not Officially Validated)",
        description="Disclaimer and version of the prototype risk methodology"
    )
