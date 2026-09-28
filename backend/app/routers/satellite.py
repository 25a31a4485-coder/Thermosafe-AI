"""
Router for Satellite Thermal Telemetry endpoints (NASA FIRMS / Demonstration Feed).
Provides backend-mediated access to satellite thermal observations.
Never exposes API keys or credentials to the client.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.satellite import SatelliteThermalEventsResponse
from app.services.firms_service import FIRMSService, get_firms_service

router = APIRouter(
    prefix="/satellite",
    tags=["Satellite Telemetry (NASA FIRMS)"]
)


@router.get(
    "/thermal-events",
    response_model=SatelliteThermalEventsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve satellite thermal events from NASA FIRMS or local demonstration feed",
    description=(
        "Fetches near real-time satellite thermal detections (VIIRS / MODIS) via NASA FIRMS "
        "when configured in live mode with a valid NASA_FIRMS_API_KEY, or serves local demonstration "
        "satellite passes in demo mode. All records are normalized into the internal ThermalEvent format "
        "complete with map-compatible GeoJSON Point features."
    )
)
def get_satellite_thermal_events(
    mode: Optional[str] = Query(
        None,
        description="Override data mode: 'demo' or 'live'. Defaults to server SATELLITE_DATA_MODE setting."
    ),
    country: str = Query(
        "IND",
        min_length=3,
        max_length=50,
        description="ISO 3-letter country code or bbox (default: IND for India)."
    ),
    days: int = Query(
        1,
        ge=1,
        le=5,
        description="Number of past days to query from satellite pass (1 to 5 days)."
    ),
    source: str = Query(
        "VIIRS_NOAA21_NRT",
        description="Sensor source: 'VIIRS_NOAA21_NRT', 'VIIRS_NOAA20_NRT', 'VIIRS_SNPP_NRT', 'MODIS_NRT'."
    ),
    min_confidence: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Filter events by minimum confidence score (0.0 to 1.0)."
    ),
    db: Session = Depends(get_db),
    firms_service: FIRMSService = Depends(get_firms_service),
) -> SatelliteThermalEventsResponse:
    """
    Retrieve normalized satellite thermal telemetry.
    """
    return firms_service.get_satellite_events(
        mode=mode,
        country=country,
        days=days,
        source=source,
        min_confidence=min_confidence,
        db=db,
    )


@router.get(
    "/health",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Retrieve NASA FIRMS Telemetry Worker Health Status",
)
def get_firms_health(
    firms_service: FIRMSService = Depends(get_firms_service),
) -> dict:
    """
    Returns sanitized telemetry health status:
    firms_configured, firms_worker_running, last_successful_fetch,
    last_attempt, last_error, cached_event_count, stale_age_seconds, next_scheduled_fetch.
    """
    return firms_service.get_health_status()


@router.post(
    "/refresh",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Trigger immediate background or synchronous FIRMS live refresh",
)
def trigger_firms_refresh(
    db: Session = Depends(get_db),
    firms_service: FIRMSService = Depends(get_firms_service),
) -> dict:
    """
    Triggers an immediate live ingestion attempt and returns the ingestion result.
    """
    return firms_service.ingest_live_telemetry(db=db)
