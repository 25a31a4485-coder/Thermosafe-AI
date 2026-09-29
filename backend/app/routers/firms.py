"""
Router for NASA FIRMS Satellite Thermal Telemetry endpoints.
Provides backend-mediated access to live NASA FIRMS thermal observations for India.
Never exposes API keys or credentials to the client.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.firms_service import FIRMSService, get_firms_service

router = APIRouter(
    prefix="/firms",
    tags=["NASA FIRMS Live Telemetry"]
)


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Retrieve live NASA FIRMS thermal hotspots for India",
    description="Fetches or queries real near-real-time NASA FIRMS thermal detections strictly within India.",
)
def get_firms_live(
    days: int = Query(1, ge=1, le=5, description="Number of past days (1 to 5)."),
    source: str = Query("VIIRS_NOAA21_NRT", description="Sensor source: VIIRS_NOAA21_NRT, VIIRS_NOAA20_NRT."),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score (0.0 to 1.0)."),
    db: Session = Depends(get_db),
    firms_service: FIRMSService = Depends(get_firms_service),
) -> Dict[str, Any]:
    """
    Returns standardized NASA FIRMS live response:
    {
      "success": true,
      "source": "NASA FIRMS",
      "live": true,
      "count": <count>,
      "data": [...]
    }
    """
    return firms_service.get_firms_live_payload(
        days=days,
        source=source,
        min_confidence=min_confidence,
        db=db,
    )


@router.get(
    "/thermal-events",
    status_code=status.HTTP_200_OK,
    summary="Alias for live NASA FIRMS thermal hotspots",
)
def get_firms_thermal_events(
    days: int = Query(1, ge=1, le=5),
    source: str = Query("VIIRS_NOAA21_NRT"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    firms_service: FIRMSService = Depends(get_firms_service),
) -> Dict[str, Any]:
    return get_firms_live(
        days=days,
        source=source,
        min_confidence=min_confidence,
        db=db,
        firms_service=firms_service,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Root NASA FIRMS live endpoint",
)
def get_firms_root(
    days: int = Query(1, ge=1, le=5),
    source: str = Query("VIIRS_NOAA21_NRT"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    firms_service: FIRMSService = Depends(get_firms_service),
) -> Dict[str, Any]:
    return get_firms_live(
        days=days,
        source=source,
        min_confidence=min_confidence,
        db=db,
        firms_service=firms_service,
    )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Retrieve NASA FIRMS health and availability status",
    description="Returns public health status without exposing any secrets or API keys."
)
def get_firms_health(
    firms_service: FIRMSService = Depends(get_firms_service),
) -> Dict[str, Any]:
    """
    Returns:
    {
      "service": "NASA FIRMS",
      "configured": true,
      "reachable": true,
      "live": true
    }
    """
    return firms_service.get_firms_health_summary()


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Trigger immediate live ingestion from NASA FIRMS",
)
def trigger_firms_refresh(
    db: Session = Depends(get_db),
    firms_service: FIRMSService = Depends(get_firms_service),
) -> Dict[str, Any]:
    return firms_service.ingest_live_telemetry(db=db)
