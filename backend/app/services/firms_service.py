"""
NASA FIRMS Satellite Thermal Telemetry Service.
Provides robust, resilient integration with NASA FIRMS (Fire Information for Resource Management System)
for near real-time (NRT) thermal hotspot detection via VIIRS (NOAA-21 / NOAA-20 / SNPP) and MODIS sensors.

Architectural Guarantees:
1. Periodic background fetch from NASA FIRMS with configurable refresh interval (default: 15 min).
2. Canonical SQLite/Postgres database live event cache with idempotent upsert.
3. Persistent "last known good" live dataset: temporary NASA outages never wipe or clear events.
4. Truthful operational status codes: LIVE_CURRENT, LIVE_STALE, LIVE_OK_ZERO_EVENTS, CONFIGURATION_REQUIRED.
5. Exponential retry/backoff and lightweight circuit breaker to prevent hammering NASA.
6. Zero API key leaks in logs, error strings, or client responses.
"""

import csv
import io
import logging
import math
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.spatial import (
    is_inside_india,
    INDIA_LAT_MIN,
    INDIA_LAT_MAX,
    INDIA_LON_MIN,
    INDIA_LON_MAX,
    INDIA_BBOX_CSV,
    INDIA_COUNTRY_CODE,
)
from app.models.thermal_event import ThermalEvent
from app.models.ai_classification import AIClassification
from app.models.risk_assessment import RiskAssessment
from app.models.facility import IndustrialFacility
from app.schemas.ai_classification import AIClassificationResponse, AIClassifyRequest
from app.schemas.risk_assessment import RiskAnalysisRequest, RiskAssessmentResponse
from app.schemas.satellite import SatelliteThermalEventsResponse, FIRMSHealthResponse
from app.schemas.thermal_event import ThermalEventResponse
from app.services.ai_service import get_classifier
from app.services.risk_service import get_risk_engine

logger = logging.getLogger("firms_service")


def mask_secret(text: str, secret: Optional[str]) -> str:
    """Safely mask any secret API key occurrences from log strings or URLs."""
    if not secret or len(secret) < 4:
        return text
    return text.replace(secret, f"{secret[:2]}...[REDACTED]...{secret[-2:]}")


# ThermoSafe AI operates in permanent INDIA-ONLY mode.
# All geographic queries map strictly to India's territorial coordinates.
COUNTRY_BOUNDING_BOXES: Dict[str, str] = {
    "IND": INDIA_BBOX_CSV,
    "INDIA": INDIA_BBOX_CSV,
    "WORLD": INDIA_BBOX_CSV,
}


class FIRMSService:
    """
    Robust Satellite Thermal Telemetry Service interfacing with NASA FIRMS.
    Maintains a persistent database cache of live thermal hotspots.
    Guarantees continuous application availability regardless of external NASA API status.
    """

    def __init__(
        self,
        base_url: str = settings.NASA_FIRMS_BASE_URL,
        api_key: Optional[str] = None,
        default_mode: str = settings.SATELLITE_DATA_MODE,
        timeout_seconds: int = settings.NASA_FIRMS_TIMEOUT_SECONDS,
        refresh_interval_seconds: int = settings.FIRMS_REFRESH_INTERVAL_SECONDS,
        retention_days: int = settings.FIRMS_RETENTION_DAYS,
    ):
        self.base_url = base_url.rstrip("/")
        raw_key = api_key if api_key is not None else settings.effective_firms_map_key
        self.api_key = raw_key.strip() if raw_key else None
        self.default_mode = default_mode.lower().strip()
        self.timeout_seconds = timeout_seconds
        self.refresh_interval_seconds = refresh_interval_seconds
        self.retention_days = retention_days

        self.preferred_sensor = getattr(settings, "FIRMS_PREFERRED_SENSOR", "VIIRS_NOAA21_NRT")
        self.fallback_sensor = getattr(settings, "FIRMS_FALLBACK_SENSOR", "VIIRS_NOAA20_NRT")
        self.default_area = getattr(settings, "FIRMS_DEFAULT_AREA", "IND")

        self.ai_classifier = get_classifier()
        self.risk_engine = get_risk_engine()

        # Telemetry State & Ingestion Tracking
        self.last_successful_fetch: Optional[datetime] = None
        self.last_attempt: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.last_diagnostic_reason: Optional[str] = None
        self.last_status: str = "INITIALIZING"
        self.consecutive_failures: int = 0
        self.circuit_breaker_open: bool = False
        self.circuit_breaker_until: Optional[float] = None
        self.next_scheduled_fetch: Optional[datetime] = None

        self._last_ingestion_result: Dict[str, Any] = {
            "success": False,
            "source": self.preferred_sensor,
            "event_count": 0,
            "new_events": 0,
            "updated_events": 0,
            "error": None,
        }

        # Background Worker State
        self._worker_running: bool = False
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Check existing database state on initialization
        self._initialize_from_database()

    def _initialize_from_database(self) -> None:
        """Inspect database for existing live records on initialization, strictly enforcing India scope."""
        try:
            with SessionLocal() as db:
                # Cleanup any legacy non-India records on startup to guarantee India-only dataset
                try:
                    purged = (
                        db.query(ThermalEvent)
                        .filter(
                            or_(
                                ThermalEvent.latitude < INDIA_LAT_MIN,
                                ThermalEvent.latitude > INDIA_LAT_MAX,
                                ThermalEvent.longitude < INDIA_LON_MIN,
                                ThermalEvent.longitude > INDIA_LON_MAX,
                            )
                        )
                        .delete(synchronize_session=False)
                    )
                    if purged > 0:
                        db.commit()
                        logger.info("Purged %d non-India legacy events from database on startup", purged)
                except Exception as purge_err:
                    db.rollback()
                    logger.warning("Could not purge non-India records on startup: %s", purge_err)

                count = (
                    db.query(ThermalEvent)
                    .filter(
                        ThermalEvent.is_demo == False,
                        ThermalEvent.latitude >= INDIA_LAT_MIN,
                        ThermalEvent.latitude <= INDIA_LAT_MAX,
                        ThermalEvent.longitude >= INDIA_LON_MIN,
                        ThermalEvent.longitude <= INDIA_LON_MAX,
                    )
                    .count()
                )
                if count > 0:
                    latest: Optional[ThermalEvent] = (
                        db.query(ThermalEvent)
                        .filter(
                            ThermalEvent.is_demo == False,
                            ThermalEvent.latitude >= INDIA_LAT_MIN,
                            ThermalEvent.latitude <= INDIA_LAT_MAX,
                            ThermalEvent.longitude >= INDIA_LON_MIN,
                            ThermalEvent.longitude <= INDIA_LON_MAX,
                        )
                        .order_by(ThermalEvent.detected_at.desc())
                        .first()
                    )
                    if latest is not None:
                        fetch_time = latest.updated_at or latest.created_at or latest.detected_at
                        if fetch_time is not None:
                            if fetch_time.tzinfo is None:
                                fetch_time = fetch_time.replace(tzinfo=timezone.utc)
                            self.last_successful_fetch = fetch_time
                            age = (datetime.now(timezone.utc) - fetch_time).total_seconds()
                            self.last_status = "LIVE_CURRENT" if age < self.refresh_interval_seconds * 2 else "LIVE_STALE"
                        else:
                            self.last_status = "LIVE_STALE"
                    else:
                        self.last_status = "LIVE_STALE"
                    logger.info("FIRMS Service initialized from DB cache: %d live India events found (status=%s)", count, self.last_status)
                else:
                    self.last_status = "CONFIGURATION_REQUIRED" if not self.is_configured else "LIVE_STALE"
                    logger.info("FIRMS Service initialized: 0 live India events currently in DB")
        except Exception as e:
            logger.warning("Could not check initial DB cache for FIRMS: %s", e)

    @property
    def is_configured(self) -> bool:
        """Check whether a non-placeholder MAP_KEY is present."""
        raw_key = settings.effective_firms_map_key
        return bool(raw_key and raw_key not in ["", "your-nasa-firms-map-key"])

    # =========================================================================
    # STEP 1: FETCH FIRMS DATA
    # =========================================================================
    def fetch_firms_data(
        self,
        source: Optional[str] = None,
        area: Optional[str] = None,
        days: int = 1,
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[int], Optional[str]]:
        """
        Execute request to official NASA FIRMS Area API.
        Returns: (success: bool, csv_text: Optional[str], error_message: Optional[str], http_status: Optional[int], diagnostic_reason: Optional[str])
        Never leaks MAP_KEY in logs, exceptions, or error messages.
        """
        # 1. Verify Configuration
        current_key = settings.effective_firms_map_key
        if not current_key:
            self.last_diagnostic_reason = "missing_api_key"
            return (False, None, "NASA FIRMS API key is not configured in backend/.env", None, "missing_api_key")

        self.api_key = current_key

        # 2. Check Circuit Breaker
        now_ts = time.time()
        if self.circuit_breaker_open:
            if self.circuit_breaker_until and now_ts < self.circuit_breaker_until:
                wait_sec = int(self.circuit_breaker_until - now_ts)
                self.last_diagnostic_reason = "temporary_service_failure"
                return (False, None, f"Circuit breaker active: cooling down for {wait_sec}s", None, "temporary_service_failure")
            else:
                logger.info("FIRMS circuit breaker cooldown expired, resuming connection attempts")
                self.circuit_breaker_open = False
                self.circuit_breaker_until = None

        # 3. Determine Sensor Candidate List (with automatic fallback)
        primary_source = source or self.preferred_sensor
        candidates = [primary_source]
        if primary_source == "VIIRS_NOAA21_NRT" and self.fallback_sensor not in candidates:
            candidates.append(self.fallback_sensor)

        # ThermoSafe AI strictly enforces India geographic boundaries
        target_area = (area or self.default_area or "IND").strip()
        if target_area.upper() in COUNTRY_BOUNDING_BOXES:
            area_param = COUNTRY_BOUNDING_BOXES[target_area.upper()]
        else:
            area_param = INDIA_BBOX_CSV

        days_param = max(1, min(days, 5))
        last_error = None
        last_status = None
        last_reason = None

        for sensor in candidates:
            url = f"{self.base_url}/api/area/csv/{self.api_key}/{sensor}/{area_param}/{days_param}"
            safe_url = mask_secret(url, self.api_key)

            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "ThermoSafe-AI/1.0 (Industrial Thermal Intelligence Backend)",
                    "Accept": "text/csv, application/json",
                },
            )

            try:
                logger.info("Calling NASA FIRMS Area API: sensor=%s area=%s days=%d", sensor, area_param, days_param)
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    status_code = response.status
                    last_status = status_code
                    raw_bytes = response.read()
                    csv_text = raw_bytes.decode("utf-8", errors="replace")

                if status_code == 200:
                    first_line = csv_text.strip().split("\n")[0] if csv_text else ""
                    if "Invalid MAP_KEY" in first_line:
                        last_reason = "invalid_api_key"
                        last_error = "NASA FIRMS API rejected key: Invalid MAP_KEY"
                        self.last_diagnostic_reason = last_reason
                        return (False, None, last_error, 200, last_reason)
                    elif "Transaction limit" in first_line:
                        last_reason = "temporary_service_failure"
                        last_error = "NASA FIRMS transaction limit exceeded"
                        self.last_diagnostic_reason = last_reason
                        return (False, None, last_error, 200, last_reason)
                    elif "Invalid API call" in first_line:
                        last_reason = "http_error"
                        last_error = f"NASA FIRMS API rejected: {first_line.strip()}"
                        self.last_diagnostic_reason = last_reason
                        return (False, None, last_error, 200, last_reason)

                    # Successfully received valid response body from NASA
                    self.last_diagnostic_reason = None
                    return (True, csv_text, None, 200, None)
                else:
                    last_error = f"FIRMS HTTP {status_code}"
                    last_reason = "http_error"

            except urllib.error.HTTPError as he:
                last_status = he.code
                last_reason = "invalid_api_key" if he.code in (401, 403) else ("temporary_service_failure" if he.code in (429, 502, 503, 504) else "http_error")
                err_body = ""
                try:
                    err_body = he.read().decode("utf-8", errors="replace").strip().split("\n")[0]
                except Exception:
                    pass
                detail = f" - {err_body}" if err_body else ""
                sanitized_err = mask_secret(f"FIRMS HTTP {he.code}{detail}", self.api_key)
                logger.warning("NASA FIRMS HTTP Error: %s (sensor=%s)", sanitized_err, sensor)
                last_error = sanitized_err

                # If primary sensor 404, try next candidate
                if he.code == 404 and sensor != candidates[-1]:
                    logger.info("Sensor %s returned 404, attempting fallback sensor %s", sensor, candidates[-1])
                    continue
                break

            except (socket.timeout, TimeoutError) as te:
                sanitized_err = mask_secret(f"Remote NASA server timeout ({te})", self.api_key)
                logger.warning("NASA FIRMS timeout: %s", sanitized_err)
                last_error = "Remote NASA server connection timeout"
                last_reason = "upstream_timeout"
                break

            except urllib.error.URLError as ue:
                if isinstance(ue.reason, (socket.timeout, TimeoutError)):
                    last_error = "Remote NASA server connection timeout"
                    last_reason = "upstream_timeout"
                else:
                    sanitized_err = mask_secret(f"URLError: {ue.reason}", self.api_key)
                    logger.warning("NASA FIRMS network failure: %s", sanitized_err)
                    last_error = "Remote NASA server unreachable"
                    last_reason = "network_failure"
                break

            except Exception as ex:
                sanitized_err = mask_secret(f"{type(ex).__name__}: {ex}", self.api_key)
                logger.error("Unexpected error contacting NASA FIRMS: %s", sanitized_err)
                last_error = "Unexpected NASA FIRMS connection failure"
                last_reason = "network_failure"
                break

        self.last_diagnostic_reason = last_reason or "http_error"
        return (False, None, last_error or "NASA FIRMS request failed", last_status, self.last_diagnostic_reason)

    # =========================================================================
    # STEP 2: VALIDATE FIRMS RESPONSE
    # =========================================================================
    def validate_firms_response(self, csv_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate whether raw response text represents a legitimate FIRMS CSV payload.
        Detects inline NASA error messages such as 'Invalid MAP_KEY' or 'Transaction limit'.
        Returns: (is_valid: bool, error_message: Optional[str], diagnostic_reason: Optional[str])
        """
        if not csv_text or not csv_text.strip():
            return (False, "Empty response from NASA FIRMS", "invalid_response")

        first_line = csv_text.strip().split("\n")[0]
        # Detect textual rejections from NASA API
        if "Invalid MAP_KEY" in first_line:
            return (False, "NASA FIRMS API rejected: Invalid MAP_KEY", "invalid_api_key")
        if "Transaction limit" in first_line:
            return (False, "NASA FIRMS transaction limit exceeded", "temporary_service_failure")
        for reject_phrase in ["Invalid API call", "Not Found"]:
            if reject_phrase in first_line:
                return (False, f"NASA FIRMS API rejected: {first_line.strip()}", "http_error")

        # Ensure header contains expected columns
        header_lower = first_line.lower()
        if "latitude" not in header_lower or "longitude" not in header_lower:
            return (False, f"Malformed NASA CSV headers: {first_line[:80]}", "invalid_response")

        return (True, None, None)

    # =========================================================================
    # STEP 3: NORMALIZE FIRMS EVENTS
    # =========================================================================
    def normalize_firms_events(
        self,
        csv_text: str,
        source_name: str,
        min_confidence: Optional[float] = None,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        Parse valid NASA FIRMS CSV rows, validate coordinates, normalize telemetry values,
        execute AI classification & risk calculations, and generate deterministic stable IDs.
        """
        csv_file = io.StringIO(csv_text.strip())
        reader = csv.DictReader(csv_file)
        normalized_records: List[Dict[str, Any]] = []

        now = datetime.now(timezone.utc)
        close_db = False
        active_db = db
        if active_db is None:
            active_db = SessionLocal()
            close_db = True

        try:
            for row in reader:
                try:
                    # 1. Coordinate Validation & Strict India-Only Enforcement
                    lat_raw = row.get("latitude")
                    lon_raw = row.get("longitude")
                    if lat_raw is None or lon_raw is None:
                        continue

                    lat = float(lat_raw)
                    lon = float(lon_raw)

                    # Strict boundary checks: ONLY INDIA
                    if not is_inside_india(lat, lon):
                        continue

                    # 2. FRP and Thermal Intensity Normalization
                    frp_raw = row.get("frp")
                    try:
                        frp_val = float(frp_raw) if frp_raw else 25.0
                    except (ValueError, TypeError):
                        frp_val = 25.0
                    thermal_intensity = f"{frp_val:.1f} MW"

                    # 3. Confidence Normalization
                    conf_raw = str(row.get("confidence", "nominal")).strip().lower()
                    if conf_raw in ["h", "high"]:
                        confidence = 0.95
                    elif conf_raw in ["n", "nominal"]:
                        confidence = 0.65
                    elif conf_raw in ["l", "low"]:
                        confidence = 0.30
                    else:
                        try:
                            c_float = float(conf_raw)
                            confidence = c_float / 100.0 if c_float > 1.0 else c_float
                        except ValueError:
                            confidence = 0.50

                    if min_confidence is not None and confidence < min_confidence:
                        continue

                    # 4. Acquisition Datetime Normalization
                    acq_date = row.get("acq_date")
                    acq_time = row.get("acq_time")
                    detected_at = now
                    time_clean = "0000"
                    if acq_date and acq_time:
                        try:
                            time_clean = str(acq_time).strip().zfill(4)
                            detected_at = datetime.strptime(
                                f"{acq_date.strip()} {time_clean}", "%Y-%m-%d %H%M"
                            ).replace(tzinfo=timezone.utc)
                        except Exception:
                            detected_at = now

                    # 5. Day / Night & Persistence
                    daynight = str(row.get("daynight", "D")).strip().upper()
                    persistence = "Nighttime Hotspot" if daynight == "N" else "Daytime Hotspot"

                    # 6. Industrial Facility Proximity Correlation
                    facility_obj = None
                    facility_id = None
                    facility_name = None
                    proximity_km = 999.0

                    if active_db:
                        facility_obj, proximity_km = self._find_nearest_facility(lat, lon, active_db)
                        if facility_obj and proximity_km <= 15.0:
                            facility_id = facility_obj.id
                            facility_name = facility_obj.name

                    # 7. AI Classification Integration
                    ai_req = AIClassifyRequest(
                        latitude=lat,
                        longitude=lon,
                        thermal_intensity=thermal_intensity,
                        persistence=persistence,
                        nearby_industrial_facility=facility_name,
                        facility_id=facility_id,
                        facility_distance_km=round(proximity_km, 2) if facility_name else None,
                        land_cover="Industrial Perimeter" if (facility_name and proximity_km <= 5.0) else "Open Land",
                        historical_occurrences=1 if frp_val > 50 else 0,
                        data_source=source_name,
                    )
                    ai_res = self.ai_classifier.classify(ai_req)
                    event_type = ai_res.classification

                    # 8. Risk Assessment Engine Integration
                    risk_req = RiskAnalysisRequest(
                        thermal_intensity=thermal_intensity,
                        persistence=persistence,
                        industrial_facility_proximity_km=proximity_km if facility_name else None,
                        nearby_industrial_facility=facility_name,
                        population_proximity_km=5.0 if facility_name else None,
                        historical_recurrence=1 if frp_val > 50 else 0,
                        ai_classification=ai_res.classification,
                        event_type=event_type,
                        latitude=lat,
                        longitude=lon,
                    )
                    risk_res = self.risk_engine.evaluate_risk(risk_req)

                    # 9. Deterministic Stable Event Identifier for Idempotent UPSERT
                    # Format: FIRMS-<SENSOR>-<YYYYMMDD>-<HHMM>-<LAT>_<LON>
                    sensor_tag = "NOAA21" if "21" in source_name else ("NOAA20" if "20" in source_name else ("SNPP" if "SNPP" in source_name else "VIIRS"))
                    acq_date_clean = acq_date.replace("-", "") if acq_date else detected_at.strftime("%Y%m%d")
                    stable_event_id = f"FIRMS-{sensor_tag}-{acq_date_clean}-{time_clean}-{round(lat, 3):+.3f}_{round(lon, 3):+.3f}"

                    normalized_records.append({
                        "event_id": stable_event_id,
                        "latitude": round(lat, 4),
                        "longitude": round(lon, 4),
                        "detected_at": detected_at,
                        "event_type": event_type,
                        "thermal_intensity": thermal_intensity,
                        "persistence": persistence,
                        "confidence": confidence,
                        "risk_score": risk_res.risk_score,
                        "risk_priority": risk_res.risk_priority,
                        "facility_id": facility_id,
                        "facility_name": facility_name,
                        "facility_obj": facility_obj,
                        "land_cover": "Industrial Zone" if facility_name else "Rural Terrain",
                        "data_source": source_name,
                        "ai_res": ai_res,
                        "risk_res": risk_res,
                        "raw_row": row,
                    })

                except Exception as row_err:
                    logger.debug("Skipping unparseable FIRMS CSV row: %s", row_err)
                    continue

        finally:
            if close_db and active_db is not None:
                active_db.close()

        return normalized_records

    # =========================================================================
    # STEP 4: UPSERT FIRMS EVENTS (IDEMPOTENT DATABASE PERSISTENCE)
    # =========================================================================
    def upsert_firms_events(
        self,
        normalized_records: List[Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> Dict[str, int]:
        """
        Idempotently insert or update normalized FIRMS events in the database.
        Never duplicates events across polling cycles.
        """
        if not normalized_records:
            return {"new_events": 0, "updated_events": 0}

        close_db = False
        active_db = db
        if active_db is None:
            active_db = SessionLocal()
            close_db = True

        new_count = 0
        updated_count = 0
        now = datetime.now(timezone.utc)

        try:
            for rec in normalized_records:
                lat = float(rec["latitude"])
                lon = float(rec["longitude"])
                # Strict boundary check: reject any event outside India
                if not is_inside_india(lat, lon):
                    continue

                stable_id = rec["event_id"]
                existing: Optional[ThermalEvent] = active_db.query(ThermalEvent).filter(ThermalEvent.event_id == stable_id).first()

                if existing is not None:
                    # Update existing record
                    existing.status = "active"
                    existing.updated_at = now
                    existing.confidence = rec["confidence"]
                    existing.risk_score = rec["risk_score"]
                    existing.risk_priority = rec["risk_priority"]
                    existing.thermal_intensity = rec["thermal_intensity"]
                    existing.persistence = rec["persistence"]
                    existing.is_demo = False
                    updated_count += 1
                else:
                    # Create new ThermalEvent record
                    new_event = ThermalEvent(
                        event_id=stable_id,
                        latitude=rec["latitude"],
                        longitude=rec["longitude"],
                        detected_at=rec["detected_at"],
                        event_type=rec["event_type"],
                        thermal_intensity=rec["thermal_intensity"],
                        persistence=rec["persistence"],
                        confidence=rec["confidence"],
                        risk_score=rec["risk_score"],
                        risk_priority=rec["risk_priority"],
                        facility_id=rec["facility_id"],
                        land_cover=rec["land_cover"],
                        data_source=rec["data_source"],
                        status="active",
                        is_demo=False,
                        created_at=now,
                        updated_at=now,
                    )
                    active_db.add(new_event)
                    active_db.flush()

                    # Persist related AIClassification
                    ai_res = rec["ai_res"]
                    ai_rec = AIClassification(
                        thermal_event_id=new_event.id,
                        classification=ai_res.classification,
                        confidence=ai_res.confidence,
                        explanation=ai_res.explanation,
                        model_name=getattr(ai_res, "model_name", "ThermoSafe-AI-v1"),
                        created_at=now,
                    )
                    active_db.add(ai_rec)

                    # Persist related RiskAssessment
                    risk_res = rec["risk_res"]
                    risk_rec = RiskAssessment(
                        thermal_event_id=new_event.id,
                        risk_score=risk_res.risk_score,
                        risk_priority=risk_res.risk_priority,
                        thermal_factor=risk_res.thermal_factor,
                        persistence_factor=risk_res.persistence_factor,
                        industrial_proximity_factor=risk_res.industrial_proximity_factor,
                        population_proximity_factor=risk_res.population_proximity_factor,
                        historical_factor=risk_res.historical_factor,
                        explanation=risk_res.explanation,
                        methodology="ThermalSafe Dynamic Risk Model v1.0",
                        created_at=now,
                    )
                    active_db.add(risk_rec)
                    new_count += 1

            active_db.commit()
            logger.info("UPSERT complete: %d new events inserted, %d existing events refreshed", new_count, updated_count)

        except Exception as e:
            active_db.rollback()
            logger.exception("Database UPSERT failed: %s", e)
            raise e
        finally:
            if close_db and active_db is not None:
                active_db.close()

        return {"new_events": new_count, "updated_events": updated_count}

    # =========================================================================
    # STEP 5: ORCHESTRATE LIVE INGESTION LIFECYCLE
    # =========================================================================
    def ingest_live_telemetry(
        self,
        source: Optional[str] = None,
        area: Optional[str] = None,
        days: int = 1,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Execute full lifecycle:
        fetch_firms_data() -> validate_firms_response() -> normalize_firms_events() -> upsert_firms_events()
        Thread-safe and never destroys last known good database data on error.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            self.last_attempt = now
            source_tag = source or self.preferred_sensor

            # 1. Fetch raw data
            fetch_res = self.fetch_firms_data(
                source=source_tag,
                area=area,
                days=days,
            )
            success = fetch_res[0]
            raw_csv = fetch_res[1]
            err_msg = fetch_res[2]
            http_code = fetch_res[3]
            diag_reason = fetch_res[4] if len(fetch_res) > 4 else self.last_diagnostic_reason

            if not success or not raw_csv:
                self.consecutive_failures += 1
                self.last_error = err_msg or "Failed to retrieve NASA FIRMS data"
                self.last_diagnostic_reason = diag_reason or "network_failure"

                if not self.is_configured:
                    self.last_status = "CONFIGURATION_REQUIRED"
                else:
                    self.last_status = "LIVE_STALE"

                # Check Circuit Breaker trigger
                if self.consecutive_failures >= settings.FIRMS_CIRCUIT_BREAKER_FAILURES:
                    self.circuit_breaker_open = True
                    self.circuit_breaker_until = time.time() + settings.FIRMS_CIRCUIT_BREAKER_COOLDOWN_SECONDS
                    logger.warning(
                        "FIRMS Circuit Breaker TRIPPED after %d consecutive failures. Cooling down for %ds.",
                        self.consecutive_failures,
                        settings.FIRMS_CIRCUIT_BREAKER_COOLDOWN_SECONDS,
                    )

                self._last_ingestion_result = {
                    "success": False,
                    "source": f"NASA FIRMS ({source_tag})",
                    "fetched_at": now.isoformat(),
                    "event_count": 0,
                    "new_events": 0,
                    "updated_events": 0,
                    "error": self.last_error,
                    "reason": self.last_diagnostic_reason,
                    "last_successful_fetch": self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
                    "stale_age_seconds": self._calculate_stale_age(),
                }
                return self.return_ingestion_result()

            # 2. Validate payload
            is_valid, validation_err, val_reason = self.validate_firms_response(raw_csv)
            if not is_valid:
                self.consecutive_failures += 1
                self.last_error = validation_err
                self.last_diagnostic_reason = val_reason or "invalid_response"
                self.last_status = "LIVE_STALE"
                self._last_ingestion_result = {
                    "success": False,
                    "source": f"NASA FIRMS ({source_tag})",
                    "fetched_at": now.isoformat(),
                    "event_count": 0,
                    "new_events": 0,
                    "updated_events": 0,
                    "error": self.last_error,
                    "reason": self.last_diagnostic_reason,
                    "last_successful_fetch": self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
                    "stale_age_seconds": self._calculate_stale_age(),
                }
                return self.return_ingestion_result()

            # 3. Check for legitimate 0-events response
            csv_lines = [l for l in raw_csv.strip().split("\n") if l.strip()]
            if len(csv_lines) <= 1:
                # NASA returned 0 data rows (header only)
                self.consecutive_failures = 0
                self.last_successful_fetch = now
                self.last_error = None
                self.last_diagnostic_reason = None
                self.last_status = "LIVE_OK_ZERO_EVENTS"
                self.circuit_breaker_open = False
                logger.info("NASA FIRMS returned 0 active thermal hotspots for area=%s", area or self.default_area)
                self._last_ingestion_result = {
                    "success": True,
                    "source": f"NASA FIRMS ({source_tag})",
                    "fetched_at": now.isoformat(),
                    "event_count": 0,
                    "new_events": 0,
                    "updated_events": 0,
                    "error": None,
                    "reason": None,
                    "last_successful_fetch": now.isoformat(),
                    "stale_age_seconds": 0,
                }
                return self.return_ingestion_result()

            # 4. Normalize rows
            try:
                normalized = self.normalize_firms_events(
                    csv_text=raw_csv,
                    source_name=f"NASA FIRMS ({source_tag})",
                    db=db,
                )
            except Exception as norm_err:
                self.consecutive_failures += 1
                self.last_error = f"Normalization failure: {norm_err}"
                self.last_status = "LIVE_STALE"
                logger.exception("Failed to normalize FIRMS CSV: %s", norm_err)
                return self.return_ingestion_result()

            # 5. UPSERT to canonical database cache
            try:
                counts = self.upsert_firms_events(normalized, db=db)
                self.consecutive_failures = 0
                self.last_successful_fetch = now
                self.last_error = None
                self.last_status = "LIVE_CURRENT"
                self.circuit_breaker_open = False
                self._last_ingestion_result = {
                    "success": True,
                    "source": f"NASA FIRMS ({source_tag})",
                    "fetched_at": now.isoformat(),
                    "event_count": len(normalized),
                    "new_events": counts["new_events"],
                    "updated_events": counts["updated_events"],
                    "error": None,
                    "last_successful_fetch": now.isoformat(),
                    "stale_age_seconds": 0,
                }
                logger.info("Live FIRMS ingestion success: %d events active in database", len(normalized))
            except Exception as upsert_err:
                self.consecutive_failures += 1
                self.last_error = f"Database ingestion failure: {upsert_err}"
                self.last_status = "LIVE_STALE"
                logger.exception("Failed to upsert FIRMS events: %s", upsert_err)

            return self.return_ingestion_result()

    def return_ingestion_result(self) -> Dict[str, Any]:
        """Return the internal structured summary of the last ingestion execution."""
        return {
            "success": self._last_ingestion_result.get("success", False),
            "source": self._last_ingestion_result.get("source", f"NASA FIRMS ({self.preferred_sensor})"),
            "fetched_at": self._last_ingestion_result.get("fetched_at"),
            "event_count": self._last_ingestion_result.get("event_count", 0),
            "new_events": self._last_ingestion_result.get("new_events", 0),
            "updated_events": self._last_ingestion_result.get("updated_events", 0),
            "error": self.last_error,
            "last_successful_fetch": self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
            "stale_age_seconds": self._calculate_stale_age(),
            "status": self.last_status,
        }

    def _calculate_stale_age(self) -> Optional[int]:
        """Calculate seconds elapsed since the last verified successful NASA fetch."""
        if not self.last_successful_fetch:
            return None
        now = datetime.now(timezone.utc)
        ts = self.last_successful_fetch if self.last_successful_fetch.tzinfo else self.last_successful_fetch.replace(tzinfo=timezone.utc)
        return max(0, int((now - ts).total_seconds()))

    # =========================================================================
    # STEP 6: READ FROM CANONICAL DATABASE CACHE
    # =========================================================================
    def get_cached_live_events(
        self,
        db: Optional[Session] = None,
        limit: int = 100,
    ) -> List[ThermalEventResponse]:
        """
        Query the canonical live dataset from database cache (is_demo == False).
        Always returns real, persisted observations even when NASA API is temporarily offline.
        """
        close_db = False
        active_db = db
        if active_db is None:
            active_db = SessionLocal()
            close_db = True

        try:
            query = (
                active_db.query(ThermalEvent)
                .filter(
                    ThermalEvent.is_demo == False,
                    ThermalEvent.status == "active",
                    ThermalEvent.latitude >= INDIA_LAT_MIN,
                    ThermalEvent.latitude <= INDIA_LAT_MAX,
                    ThermalEvent.longitude >= INDIA_LON_MIN,
                    ThermalEvent.longitude <= INDIA_LON_MAX,
                )
                .order_by(ThermalEvent.detected_at.desc())
                .limit(limit)
            )
            records = query.all()
            return [ThermalEventResponse.model_validate(r) for r in records]
        except Exception as e:
            logger.exception("Error querying live database cache: %s", e)
            return []
        finally:
            if close_db and active_db is not None:
                active_db.close()

    # =========================================================================
    # STEP 7: SATELLITE API CONTROLLER INTERFACE
    # =========================================================================
    def get_satellite_events(
        self,
        mode: Optional[str] = None,
        country: str = "IND",
        days: int = 1,
        source: str = "VIIRS_NOAA21_NRT",
        min_confidence: Optional[float] = None,
        db: Optional[Session] = None,
    ) -> SatelliteThermalEventsResponse:
        """
        Retrieve satellite thermal events for API consumer / UI.
        In LIVE mode:
        1. Reads directly from canonical database cache (instant response, no blocking).
        2. Returns last known good observations if NASA is temporarily unreachable.
        3. Never wipes UI or clears database on remote error.
        4. Provides truthful status: LIVE_CURRENT, LIVE_STALE, LIVE_OK_ZERO_EVENTS, CONFIGURATION_REQUIRED.
        """
        target_mode = (mode or self.default_mode).lower().strip()
        if target_mode not in ["demo", "live"]:
            target_mode = "live"

        if target_mode == "demo":
            return self._generate_demo_events(
                country=country,
                source=source,
                min_confidence=min_confidence,
                db=db,
            )

        # LIVE MODE: Serve from canonical database cache
        cached_events = self.get_cached_live_events(db=db, limit=100)
        stale_age = self._calculate_stale_age()
        now_iso = datetime.now(timezone.utc).isoformat()
        last_success_iso = self.last_successful_fetch.isoformat() if self.last_successful_fetch else None
        next_refresh_iso = self.next_scheduled_fetch.isoformat() if self.next_scheduled_fetch else None

        # Determine truthful canonical status with strict India-Only scope
        if self.last_status == "LIVE_OK_ZERO_EVENTS" and len(cached_events) == 0:
            status_val = "LIVE_CURRENT"
            status_code = "LIVE_OK_ZERO_EVENTS"
            connected = True
            live_connected = True
            msg = "DATA SOURCE: NASA FIRMS LIVE (0 active thermal hotspots returned for India)"
        elif self.last_status == "LIVE_CURRENT" or (self.last_successful_fetch and stale_age and stale_age < self.refresh_interval_seconds * 2):
            status_val = "LIVE_CURRENT"
            status_code = "LIVE_OK_EVENTS"
            connected = True
            live_connected = True
            msg = f"DATA SOURCE: NASA FIRMS LIVE ({len(cached_events)} active detections synchronized - India Only)"
        elif len(cached_events) > 0:
            # Serving last known good live database records
            status_val = "LIVE_STALE"
            status_code = "LIVE_STALE"
            connected = True
            live_connected = True
            msg = f"LIVE DATA (Showing {len(cached_events)} synchronized India events; NASA refresh: active cache)"
        elif not self.is_configured:
            status_val = "CONFIGURATION_REQUIRED"
            status_code = "CONFIGURATION_REQUIRED"
            connected = False
            live_connected = False
            msg = "NASA FIRMS API key is not configured in backend/.env."
        else:
            status_val = "LIVE_UNAVAILABLE"
            status_code = "LIVE_UNAVAILABLE"
            connected = False
            live_connected = False
            msg = "DATA SOURCE: NASA FIRMS UNAVAILABLE (India Scope Active)"

        return SatelliteThermalEventsResponse(
            mode="live",
            source=f"NASA FIRMS ({source})",
            connected=connected,
            live_connected=live_connected,
            status=status_val,
            status_code=status_code,
            last_updated=last_success_iso or now_iso,
            last_successful_fetch=last_success_iso,
            next_refresh=next_refresh_iso,
            stale_age_seconds=stale_age,
            event_count=len(cached_events),
            total=len(cached_events),
            message=msg,
            error=self.last_error,
            reason=self.last_diagnostic_reason,
            items=cached_events,
            events=cached_events,
        )

    # =========================================================================
    # STEP 8: DEMO DATA GENERATION (ISOLATED TO DEMO MODE)
    # =========================================================================
    def _generate_demo_events(
        self,
        country: str,
        source: str,
        min_confidence: Optional[float],
        db: Optional[Session],
    ) -> SatelliteThermalEventsResponse:
        """
        Generate realistic demonstration satellite thermal telemetry.
        Isolated to explicit demo mode; never leaks into LIVE mode.
        """
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")

        csv_lines = [
            "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight",
            f"22.3039,70.8022,367.4,0.4,0.4,{today_str},0215,N,VIIRS,h,2.0NRT,298.5,1250.0,N",
            f"21.1124,72.6582,345.8,0.5,0.4,{today_str},0945,1,VIIRS,h,2.0NRT,301.2,680.0,D",
            f"19.4167,71.3333,328.6,0.6,0.5,{today_str},0320,N,VIIRS,n,2.0NRT,295.1,320.0,N",
            f"22.3595,82.6801,318.2,0.4,0.4,{today_str},1105,1,VIIRS,n,2.0NRT,299.0,140.0,D",
            f"21.7100,72.5800,308.5,0.5,0.4,{today_str},0150,N,VIIRS,l,2.0NRT,294.0,45.0,N",
            f"17.6258,83.1812,334.1,0.4,0.4,{today_str},0240,N,VIIRS,h,2.0NRT,297.8,410.0,N",
            f"20.2644,86.6715,340.5,0.5,0.4,{today_str},1015,1,VIIRS,h,2.0NRT,300.4,520.0,D",
        ]
        demo_csv = "\n".join(csv_lines)

        normalized = self.normalize_firms_events(
            csv_text=demo_csv,
            source_name="Local Demonstration Satellite Feed (VIIRS Model)",
            min_confidence=min_confidence,
            db=db,
        )

        # Convert to response objects without database persistence
        items: List[ThermalEventResponse] = []
        for idx, rec in enumerate(normalized, start=20001):
            ai_res = rec["ai_res"]
            ai_class_resp = AIClassificationResponse(
                id=idx,
                thermal_event_id=idx,
                classification=ai_res.classification,
                confidence=ai_res.confidence,
                explanation=ai_res.explanation,
                model_name=ai_res.model_name,
                created_at=now,
            )
            evt = ThermalEventResponse(
                id=idx,
                event_id=f"DEMO-VIIRS-{rec['detected_at'].strftime('%Y%m%d')}-{idx:04d}",
                latitude=rec["latitude"],
                longitude=rec["longitude"],
                detected_at=rec["detected_at"],
                event_type=rec["event_type"],
                thermal_intensity=rec["thermal_intensity"],
                persistence=rec["persistence"],
                confidence=rec["confidence"],
                risk_score=rec["risk_score"],
                risk_priority=rec["risk_priority"],
                facility_id=rec["facility_id"],
                land_cover=rec["land_cover"],
                data_source="Local Demonstration Satellite Feed (VIIRS Model)",
                status="active",
                is_demo=True,
                created_at=now,
                updated_at=now,
                facility=rec["facility_obj"],
                classifications=[ai_class_resp],
                risk_assessments=[],
            )
            items.append(evt)

        return SatelliteThermalEventsResponse(
            mode="demo",
            source="Local Demonstration Satellite Feed (VIIRS Model)",
            connected=False,
            live_connected=False,
            status="DEMO_MODE",
            status_code="DEMO_MODE",
            last_updated=now.isoformat(),
            last_successful_fetch=None,
            next_refresh=None,
            stale_age_seconds=None,
            event_count=len(items),
            total=len(items),
            message="Demonstration satellite telemetry active (Simulating VIIRS passes over major industrial hubs)",
            error=None,
            items=items,
            events=items,
        )

    # =========================================================================
    # STEP 9: DATA RETENTION CLEANUP
    # =========================================================================
    def run_retention_cleanup(
        self,
        retention_days: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> int:
        """
        Delete expired live records older than retention threshold.
        Only executed during scheduled background maintenance.
        NEVER triggered by a failed NASA refresh.
        """
        days = retention_days or self.retention_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        close_db = False
        active_db = db
        if active_db is None:
            active_db = SessionLocal()
            close_db = True

        deleted_count = 0
        try:
            # Purge expired live events
            deleted_count = (
                active_db.query(ThermalEvent)
                .filter(ThermalEvent.is_demo == False, ThermalEvent.detected_at < cutoff)
                .delete(synchronize_session=False)
            )
            # Guarantee non-India events are also purged
            non_india_deleted = (
                active_db.query(ThermalEvent)
                .filter(
                    or_(
                        ThermalEvent.latitude < INDIA_LAT_MIN,
                        ThermalEvent.latitude > INDIA_LAT_MAX,
                        ThermalEvent.longitude < INDIA_LON_MIN,
                        ThermalEvent.longitude > INDIA_LON_MAX,
                    )
                )
                .delete(synchronize_session=False)
            )
            active_db.commit()
            if deleted_count > 0:
                logger.info("FIRMS retention cleanup: purged %d expired live events older than %d days", deleted_count, days)
            if non_india_deleted > 0:
                logger.info("FIRMS retention cleanup: purged %d non-India events", non_india_deleted)
        except Exception as e:
            active_db.rollback()
            logger.warning("FIRMS retention cleanup failed: %s", e)
        finally:
            if close_db and active_db is not None:
                active_db.close()

        return deleted_count

    # =========================================================================
    # STEP 10: SINGLE BACKGROUND INGESTION WORKER
    # =========================================================================
    def start_background_worker(self) -> None:
        """
        Start exactly ONE background worker thread per process.
        Safe against duplicate registration.
        """
        with self._lock:
            if self._worker_running:
                logger.info("FIRMS background worker already running (singleton verified)")
                return

            self._stop_event.clear()
            self._worker_running = True
            self._worker_thread = threading.Thread(
                target=self._background_worker_loop,
                name="FIRMS-Live-Ingestion-Worker",
                daemon=True,
            )
            self._worker_thread.start()
            logger.info("FIRMS background ingestion worker started successfully")

    def stop_background_worker(self) -> None:
        """Gracefully stop the background worker thread."""
        with self._lock:
            if not self._worker_running:
                return
            self._stop_event.set()
            self._worker_running = False
            logger.info("FIRMS background ingestion worker signaled to stop")

    def _background_worker_loop(self) -> None:
        """
        Continuous background worker loop:
        1. Executes initial fetch on startup.
        2. Sleeps for configured interval (or backoff on failure).
        3. Re-ingests fresh telemetry.
        4. Periodically executes retention cleanup.
        Protected by top-level try/except: never terminates or crashes FastAPI.
        """
        logger.info("FIRMS worker loop entered. Initial attempt starting...")
        
        # Initial startup fetch attempt
        try:
            if self.is_configured:
                self.ingest_live_telemetry()
            else:
                logger.info("FIRMS MAP_KEY unconfigured on startup; waiting for configuration before polling NASA")
        except Exception as init_err:
            logger.warning("Initial FIRMS ingestion attempt caught exception: %s", init_err)

        cleanup_counter = 0

        while not self._stop_event.is_set():
            try:
                # Determine sleep duration
                if self.circuit_breaker_open:
                    sleep_sec = settings.FIRMS_CIRCUIT_BREAKER_COOLDOWN_SECONDS
                elif self.consecutive_failures > 0:
                    # Exponential backoff: 30s, 60s, 120s, max 300s
                    backoff = min(300, 30 * (2 ** min(self.consecutive_failures - 1, 3)))
                    sleep_sec = backoff
                else:
                    sleep_sec = self.refresh_interval_seconds

                self.next_scheduled_fetch = datetime.now(timezone.utc) + timedelta(seconds=sleep_sec)
                logger.debug("FIRMS worker sleeping for %ds (next fetch at %s)", sleep_sec, self.next_scheduled_fetch.isoformat())

                # Responsive sleep: wake up quickly if stop requested
                for _ in range(sleep_sec):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)

                if self._stop_event.is_set():
                    break

                # Execute Scheduled Ingestion
                if self.is_configured:
                    self.ingest_live_telemetry()
                else:
                    logger.debug("FIRMS MAP_KEY still unconfigured, skipping NASA poll")

                # Periodic retention cleanup (every ~2 hours)
                cleanup_counter += 1
                if cleanup_counter >= 8:
                    cleanup_counter = 0
                    self.run_retention_cleanup()

            except Exception as loop_err:
                logger.exception("Unexpected error inside FIRMS background worker loop: %s", loop_err)
                time.sleep(10)

        logger.info("FIRMS background worker loop exited gracefully")

    # =========================================================================
    # STEP 11: HEALTH & DIAGNOSTICS REPORT
    # =========================================================================
    def get_health_status(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic health status for NASA FIRMS telemetry."""
        cached_count = 0
        try:
            with SessionLocal() as db:
                cached_count = (
                    db.query(ThermalEvent)
                    .filter(
                        ThermalEvent.is_demo == False,
                        ThermalEvent.latitude >= INDIA_LAT_MIN,
                        ThermalEvent.latitude <= INDIA_LAT_MAX,
                        ThermalEvent.longitude >= INDIA_LON_MIN,
                        ThermalEvent.longitude <= INDIA_LON_MAX,
                    )
                    .count()
                )
        except Exception:
            pass

        return {
            "firms_configured": self.is_configured,
            "firms_worker_running": self._worker_running,
            "last_successful_fetch": self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
            "last_attempt": self.last_attempt.isoformat() if self.last_attempt else None,
            "last_error": self.last_error,
            "reason": self.last_diagnostic_reason,
            "cached_event_count": cached_count,
            "stale_age_seconds": self._calculate_stale_age(),
            "next_scheduled_fetch": self.next_scheduled_fetch.isoformat() if self.next_scheduled_fetch else None,
            "circuit_breaker_open": self.circuit_breaker_open,
            "status": self.last_status,
        }

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _find_nearest_facility(
        self, lat: float, lon: float, db: Session
    ) -> Tuple[Optional[Any], float]:
        """Find closest facility and calculate approximate distance in km."""
        facilities = db.query(IndustrialFacility).all()
        if not facilities:
            return None, 999.0

        min_dist = 999.0
        closest = None

        for fac in facilities:
            dlat = math.radians(fac.latitude - lat)
            dlon = math.radians(fac.longitude - lon)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat))
                * math.cos(math.radians(fac.latitude))
                * math.sin(dlon / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist = 6371.0 * c  # Earth radius km
            if dist < min_dist:
                min_dist = dist
                closest = fac

        return closest, min_dist


_firms_service_instance: Optional[FIRMSService] = None
_firms_lock = threading.Lock()


def get_firms_service() -> FIRMSService:
    """Dependency provider for FIRMSService singleton."""
    global _firms_service_instance
    if _firms_service_instance is None:
        with _firms_lock:
            if _firms_service_instance is None:
                _firms_service_instance = FIRMSService()
    return _firms_service_instance
