from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, computed_field


class IndustrialFacilityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Facility official designation")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude between -90.0 and +90.0 degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude between -180.0 and +180.0 degrees")
    industry_type: str = Field(..., min_length=1, max_length=100, description="Primary industry sector or operation")
    operator: Optional[str] = Field(None, max_length=255, description="Operating entity or parent corporation")
    risk_level: Optional[str] = Field(None, max_length=50, description="Baseline risk category: High, Medium, Low")
    address: Optional[str] = Field(None, description="Physical geographic address or regional sector")
    is_demo: bool = Field(False, description="Whether this is a simulated demo facility")


class IndustrialFacilityCreate(IndustrialFacilityBase):
    pass


class IndustrialFacilityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude between -90.0 and +90.0 degrees")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude between -180.0 and +180.0 degrees")
    industry_type: Optional[str] = Field(None, min_length=1, max_length=100)
    operator: Optional[str] = None
    risk_level: Optional[str] = None
    address: Optional[str] = None
    is_demo: Optional[bool] = None


class IndustrialFacilityResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    industry_type: str
    operator: Optional[str] = None
    risk_level: Optional[str] = None
    address: Optional[str] = None
    is_demo: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def geojson(self) -> Dict[str, Any]:
        """Map-compatible GeoJSON Feature representation."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "id": self.id,
                "name": self.name,
                "industry_type": self.industry_type,
                "operator": self.operator,
                "risk_level": self.risk_level,
                "is_demo": self.is_demo
            }
        }


class IndustrialFacilityPaginatedResponse(BaseModel):
    total: int = Field(..., description="Total count of matching facilities")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total available pages")
    has_next: bool = Field(..., description="Whether a subsequent page exists")
    has_prev: bool = Field(..., description="Whether a preceding page exists")
    items: List[IndustrialFacilityResponse] = Field(..., description="List of industrial facilities")
