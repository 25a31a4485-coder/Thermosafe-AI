from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.thermal_event import ThermalEventResponse


class SatelliteThermalEventsResponse(BaseModel):
    """
    Schema for satellite thermal telemetry response, converting external
    or demo satellite records into the internal ThermalEvent structure.
    Standardized contract for NASA FIRMS live proxy.
    """
    mode: str = Field(..., description="Telemetry operating mode: 'demo' or 'live'")
    source: str = Field(..., description="Satellite sensor feed or data origin")
    connected: bool = Field(default=False, description="Canonical boolean whether live FIRMS feed succeeded")
    live_connected: bool = Field(default=False, description="True if successfully connected to live NASA FIRMS API")
    last_updated: Optional[str] = Field(None, description="ISO timestamp of telemetry acquisition")
    event_count: int = Field(default=0, ge=0, description="Total count of satellite thermal events returned")
    total: int = Field(default=0, ge=0, description="Total count of satellite thermal events returned")
    message: Optional[str] = Field(None, description="Operational status message, warning, or fallback diagnosis")
    error: Optional[str] = Field(None, description="Safe error diagnosis if connection failed (no secrets)")
    reason: Optional[str] = Field(None, description="Diagnostic error category (e.g. upstream_timeout, invalid_api_key, network_failure)")
    status_code: Optional[str] = Field(None, description="Diagnostic pipeline status code: LIVE_OK_EVENTS, LIVE_OK_ZERO_EVENTS, LIVE_CONNECTION_FAILED, LIVE_INGESTION_FAILED, CONFIGURATION_REQUIRED")
    status: Optional[str] = Field(None, description="Canonical status: LIVE_CURRENT, LIVE_STALE, LIVE_OK_ZERO_EVENTS, CONFIGURATION_REQUIRED")
    last_successful_fetch: Optional[str] = Field(None, description="ISO timestamp of last successful NASA FIRMS fetch")
    next_refresh: Optional[str] = Field(None, description="ISO timestamp of next scheduled NASA FIRMS refresh")
    stale_age_seconds: Optional[int] = Field(None, description="Seconds elapsed since last successful NASA fetch")
    items: List[ThermalEventResponse] = Field(default_factory=list, description="Normalized thermal events with map-compatible GeoJSON")
    events: List[ThermalEventResponse] = Field(default_factory=list, description="Alias for items list")


class FIRMSHealthResponse(BaseModel):
    """Health and diagnostics status for NASA FIRMS background worker and cache."""
    firms_configured: bool = Field(..., description="Whether a valid FIRMS MAP_KEY is configured")
    firms_worker_running: bool = Field(..., description="Whether the background ingestion loop is active")
    last_successful_fetch: Optional[str] = Field(None, description="ISO timestamp of last successful NASA fetch")
    last_attempt: Optional[str] = Field(None, description="ISO timestamp of last NASA fetch attempt")
    last_error: Optional[str] = Field(None, description="Sanitized description of the last error encountered")
    reason: Optional[str] = Field(None, description="Diagnostic error category")
    cached_event_count: int = Field(default=0, ge=0, description="Total active live events in database cache")
    stale_age_seconds: Optional[int] = Field(None, description="Seconds since last successful fetch")
    next_scheduled_fetch: Optional[str] = Field(None, description="ISO timestamp of next scheduled NASA fetch")
    circuit_breaker_open: bool = Field(default=False, description="Whether circuit breaker has tripped")
