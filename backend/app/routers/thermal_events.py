import re
import math
import uuid
from datetime import datetime, date, time, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc, asc

from app.core.database import get_db
from app.models.thermal_event import ThermalEvent
from app.models.facility import IndustrialFacility
from app.schemas.thermal_event import (
    
    ThermalEventCreate,
    ThermalEventUpdate,
    ThermalEventResponse,
    ThermalEventPaginatedResponse,
)
from app.core.seed import seed_demo_thermal_events
from app.core.spatial import (
    is_inside_india,
    INDIA_LAT_MIN,
    INDIA_LAT_MAX,
    INDIA_LON_MIN,
    INDIA_LON_MAX,
)

router = APIRouter(prefix="/thermal-events", tags=["Thermal Events"])


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def parse_intensity_mw(intensity_str: Optional[str]) -> float:
    """Extracts numeric MW from thermal intensity string for accurate sorting."""
    if not intensity_str:
        return 0.0
    match = re.search(r"(\d+(\.\d+)?)", intensity_str)
    if match:
        return float(match.group(1))
    lower = intensity_str.lower()
    if "critical" in lower:
        return 1000.0
    elif "high" in lower:
        return 600.0
    elif "moderate" in lower or "medium" in lower:
        return 300.0
    elif "low" in lower:
        return 50.0
    return 0.0


def determine_risk_priority(score: float) -> str:
    """Infers categorical risk priority from a numeric score (0 to 100)."""
    if score >= 85.0:
        return "CRITICAL"
    elif score >= 65.0:
        return "HIGH"
    elif score >= 40.0:
        return "MEDIUM"
    return "LOW"


@router.get(
    "",
    response_model=ThermalEventPaginatedResponse,
    summary="Query and filter thermal events with spatial & attribute filters",
    description="""
    Retrieves a paginated list of thermal anomalies with comprehensive filtering:
    - **Event Attributes**: event type, status, data source, demo records flag.
    - **Risk**: risk priority (CRITICAL/HIGH/MEDIUM/LOW), exact or range risk score.
    - **Time**: specific calendar date or datetime range.
    - **Facility**: facility name or ID.
    - **Spatial Proximity**: center latitude/longitude with search radius in km.
    - **Bounding Box**: min/max coordinates or standard bbox string (min_lon,min_lat,max_lon,max_lat).
    - **Sorting**: newest, risk score, or thermal intensity.
    Returns map-compatible GeoJSON objects inside each event response.
    """,
)
def get_thermal_events(
    event_type: Optional[str] = Query(None, description="Filter by event type (e.g. 'Industrial Fire', 'Gas Flare')"),
    risk_priority: Optional[str] = Query(None, description="Filter by risk priority (CRITICAL, HIGH, MEDIUM, LOW)"),
    risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Filter for events matching or exceeding this risk score"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum risk score threshold"),
    max_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Maximum risk score threshold"),
    date_filter: Optional[date] = Query(None, alias="date", description="Filter events detected on specific calendar date (YYYY-MM-DD)"),
    start_date: Optional[datetime] = Query(None, description="Start date/time threshold (ISO-8601)"),
    end_date: Optional[datetime] = Query(None, description="End date/time threshold (ISO-8601)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by operational status: active, contained, monitoring, resolved"),
    data_source: Optional[str] = Query(None, description="Filter by data source (e.g. 'NASA FIRMS', 'DEMO')"),
    facility: Optional[str] = Query(None, description="Filter by associated industrial facility name or operator"),
    facility_id: Optional[int] = Query(None, description="Filter by exact industrial facility ID"),
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Center latitude for proximity radius query (-90.0 to +90.0)"),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Center longitude for proximity radius query (-180.0 to +180.0)"),
    radius_km: Optional[float] = Query(25.0, gt=0, description="Search radius in kilometers around center latitude/longitude"),
    min_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Bounding box minimum latitude"),
    max_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Bounding box maximum latitude"),
    min_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Bounding box minimum longitude"),
    max_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Bounding box maximum longitude"),
    bbox: Optional[str] = Query(None, description="Bounding box string in standard format: min_lon,min_lat,max_lon,max_lat"),
    is_demo: Optional[bool] = Query(None, description="Filter by demo/simulated records flag"),
    sort_by: str = Query("newest", description="Sort criteria: newest, risk_score, thermal_intensity"),
    sort_order: str = Query("desc", description="Sort order direction: desc or asc"),
    page: int = Query(1, ge=1, description="Pagination page index (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    query = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.facility),
        joinedload(ThermalEvent.classifications),
        joinedload(ThermalEvent.risk_assessments),
    )

    # 1. Event Type Filter
    if event_type:
        query = query.filter(ThermalEvent.event_type.ilike(f"%{event_type.strip()}%"))

    # 2. Risk Priority Filter
    if risk_priority:
        query = query.filter(ThermalEvent.risk_priority.ilike(risk_priority.strip()))

    # 3. Risk Score Filters
    if min_risk_score is not None:
        query = query.filter(ThermalEvent.risk_score >= min_risk_score)
    if max_risk_score is not None:
        query = query.filter(ThermalEvent.risk_score <= max_risk_score)
    if risk_score is not None and min_risk_score is None:
        query = query.filter(ThermalEvent.risk_score >= risk_score)

    # 4. Date and DateTime Filters
    if date_filter:
        day_start = datetime.combine(date_filter, time.min)
        day_end = datetime.combine(date_filter, time.max)
        query = query.filter(ThermalEvent.detected_at >= day_start, ThermalEvent.detected_at <= day_end)
    if start_date:
        query = query.filter(ThermalEvent.detected_at >= start_date)
    if end_date:
        query = query.filter(ThermalEvent.detected_at <= end_date)

    # 5. Status & Data Source Filters
    if status_filter:
        query = query.filter(ThermalEvent.status.ilike(status_filter.strip()))
    if data_source:
        query = query.filter(ThermalEvent.data_source.ilike(f"%{data_source.strip()}%"))
    if is_demo is not None:
        query = query.filter(ThermalEvent.is_demo == is_demo)

    # 6. Facility Filters
    if facility_id is not None:
        query = query.filter(ThermalEvent.facility_id == facility_id)
    elif facility:
        query = query.join(ThermalEvent.facility).filter(
            or_(
                IndustrialFacility.name.ilike(f"%{facility.strip()}%"),
                IndustrialFacility.operator.ilike(f"%{facility.strip()}%"),
                IndustrialFacility.industry_type.ilike(f"%{facility.strip()}%"),
            )
        )

    # 7. Bounding Box Filter
    bbox_min_lat, bbox_max_lat = min_lat, max_lat
    bbox_min_lon, bbox_max_lon = min_lon, max_lon

    if bbox:
        try:
            parts = [float(p.strip()) for p in bbox.split(",")]
            if len(parts) == 4:
                # Expected format: min_lon, min_lat, max_lon, max_lat
                b_min_lon, b_min_lat, b_max_lon, b_max_lat = parts
                bbox_min_lat = b_min_lat
                bbox_max_lat = b_max_lat
                bbox_min_lon = b_min_lon
                bbox_max_lon = b_max_lon
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bbox format. Expected 'min_lon,min_lat,max_lon,max_lat' with numerical values."
            )

    # Strict India Territorial Clamping (Guarantees dataset cannot escape India)
    effective_min_lat = INDIA_LAT_MIN if bbox_min_lat is None else max(INDIA_LAT_MIN, bbox_min_lat)
    effective_max_lat = INDIA_LAT_MAX if bbox_max_lat is None else min(INDIA_LAT_MAX, bbox_max_lat)
    effective_min_lon = INDIA_LON_MIN if bbox_min_lon is None else max(INDIA_LON_MIN, bbox_min_lon)
    effective_max_lon = INDIA_LON_MAX if bbox_max_lon is None else min(INDIA_LON_MAX, bbox_max_lon)

    query = query.filter(
        ThermalEvent.latitude >= effective_min_lat,
        ThermalEvent.latitude <= effective_max_lat,
        ThermalEvent.longitude >= effective_min_lon,
        ThermalEvent.longitude <= effective_max_lon,
    )

    # 8. Spatial Proximity Filter (Haversine distance)
    has_proximity = latitude is not None or longitude is not None
    if has_proximity:
        if latitude is None or longitude is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both 'latitude' and 'longitude' must be provided together for proximity search."
            )
        
        # Pre-filter with rough bounding box for database performance
        deg_lat = (radius_km or 25.0) / 111.0
        deg_lon = (radius_km or 25.0) / (111.0 * max(0.01, math.cos(math.radians(latitude))))
        query = query.filter(
            ThermalEvent.latitude >= latitude - deg_lat,
            ThermalEvent.latitude <= latitude + deg_lat,
            ThermalEvent.longitude >= longitude - deg_lon,
            ThermalEvent.longitude <= longitude + deg_lon,
        )

    # 9. Sorting
    is_desc = sort_order.lower() == "desc"
    sort_criterion = sort_by.lower()

    if sort_criterion in ["newest", "detected_at", "date"]:
        query = query.order_by(desc(ThermalEvent.detected_at) if is_desc else asc(ThermalEvent.detected_at))
    elif sort_criterion in ["risk_score", "risk"]:
        query = query.order_by(desc(ThermalEvent.risk_score) if is_desc else asc(ThermalEvent.risk_score))
    elif sort_criterion in ["thermal_intensity", "intensity"]:
        query = query.order_by(desc(ThermalEvent.thermal_intensity) if is_desc else asc(ThermalEvent.thermal_intensity))
    else:
        query = query.order_by(desc(ThermalEvent.detected_at))

    all_matching = query.all()

    # Apply precise Haversine distance if proximity requested
    if has_proximity:
        all_matching = [
            evt for evt in all_matching
            if haversine_distance_km(latitude, longitude, evt.latitude, evt.longitude) <= radius_km
        ]

    # Post-sort for thermal intensity numeric value if requested
    if sort_criterion in ["thermal_intensity", "intensity"]:
        all_matching.sort(
            key=lambda evt: parse_intensity_mw(evt.thermal_intensity),
            reverse=is_desc
        )

    total = len(all_matching)
    total_pages = math.ceil(total / page_size) if page_size > 0 else 1

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = all_matching[start_idx:end_idx]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "items": paged_items,
    }


@router.get(
    "/{event_id}",
    response_model=ThermalEventResponse,
    summary="Get single thermal event details by event_id or numeric ID",
    description="Retrieves comprehensive thermal event data including facility relations, AI classifications, and map geometry.",
)
def get_thermal_event_by_id(
    event_id: str,
    db: Session = Depends(get_db),
):
    query = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.facility),
        joinedload(ThermalEvent.classifications),
        joinedload(ThermalEvent.risk_assessments),
    )

    # Support lookup by string event_id (e.g. DEMO-EVT-001) or primary key int
    if event_id.isdigit():
        event = query.filter(or_(ThermalEvent.id == int(event_id), ThermalEvent.event_id == event_id)).first()
    else:
        event = query.filter(ThermalEvent.event_id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event with identifier '{event_id}' not found.",
        )
    return event


@router.post(
    "",
    response_model=ThermalEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new thermal event",
    description="Creates a new thermal anomaly event. Validates coordinates (-90 to +90 lat, -180 to +180 lon) and auto-generates ID and risk priority if omitted.",
)
def create_thermal_event(
    event_in: ThermalEventCreate,
    db: Session = Depends(get_db),
):
    # Auto-generate event_id if omitted
    event_id = event_in.event_id
    if not event_id:
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        event_id = f"EVT-{today_str}-{uuid.uuid4().hex[:6].upper()}"

    # Check for uniqueness
    existing = db.query(ThermalEvent).filter(ThermalEvent.event_id == event_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Thermal event with event_id '{event_id}' already exists.",
        )

    # Validate or associate facility
    if event_in.facility_id is not None:
        fac = db.query(IndustrialFacility).filter(IndustrialFacility.id == event_in.facility_id).first()
        if not fac:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facility with ID {event_in.facility_id} does not exist.",
            )

    # Enforce strict India territorial scope
    if not is_inside_india(event_in.latitude, event_in.longitude):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coordinates ({event_in.latitude}, {event_in.longitude}) are outside India territorial scope (Lat: 6.0-37.5, Lon: 68.0-97.5)."
        )

    # Infer risk priority if omitted
    priority = event_in.risk_priority or determine_risk_priority(event_in.risk_score)
    detected_at = event_in.detected_at or datetime.now(timezone.utc)

    thermal_event = ThermalEvent(
        event_id=event_id,
        latitude=event_in.latitude,
        longitude=event_in.longitude,
        detected_at=detected_at,
        event_type=event_in.event_type,
        thermal_intensity=event_in.thermal_intensity,
        persistence=event_in.persistence,
        confidence=event_in.confidence,
        risk_score=event_in.risk_score,
        risk_priority=priority,
        facility_id=event_in.facility_id,
        land_cover=event_in.land_cover,
        data_source=event_in.data_source,
        status=event_in.status,
        is_demo=event_in.is_demo,
    )

    db.add(thermal_event)
    db.commit()
    db.refresh(thermal_event)

    # Automatically trigger Central Orchestration Pipeline (Phases 38-40)
    try:
        from app.services.orchestration_service import process_thermal_event
        process_thermal_event(thermal_event, db=db)
    except Exception as proc_err:
        import logging
        logging.getLogger("thermal_events").warning(
            f"Automated pipeline note for event {thermal_event.event_id}: {proc_err}"
        )

    db.refresh(thermal_event)
    return thermal_event


@router.put(
    "/{event_id}",
    response_model=ThermalEventResponse,
    summary="Update an existing thermal event",
    description="Updates attributes of an existing thermal anomaly record. Re-validates coordinates and re-computes risk priority when risk score is modified.",
)
def update_thermal_event(
    event_id: str,
    event_update: ThermalEventUpdate,
    db: Session = Depends(get_db),
):
    query = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.facility),
        joinedload(ThermalEvent.classifications),
    )

    if event_id.isdigit():
        event = query.filter(or_(ThermalEvent.id == int(event_id), ThermalEvent.event_id == event_id)).first()
    else:
        event = query.filter(ThermalEvent.event_id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event with identifier '{event_id}' not found.",
        )

    update_data = event_update.model_dump(exclude_unset=True)

    # Validate facility if being changed
    if "facility_id" in update_data and update_data["facility_id"] is not None:
        fac = db.query(IndustrialFacility).filter(IndustrialFacility.id == update_data["facility_id"]).first()
        if not fac:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facility with ID {update_data['facility_id']} does not exist.",
            )

    # Validate coordinates if being updated
    if "latitude" in update_data or "longitude" in update_data:
        new_lat = update_data.get("latitude", event.latitude)
        new_lon = update_data.get("longitude", event.longitude)
        if not is_inside_india(new_lat, new_lon):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Updated coordinates ({new_lat}, {new_lon}) are outside India territorial scope.",
            )

    # If risk_score is updated without explicit risk_priority, auto-derive it
    if "risk_score" in update_data and "risk_priority" not in update_data:
        update_data["risk_priority"] = determine_risk_priority(update_data["risk_score"])

    for field, value in update_data.items():
        setattr(event, field, value)

    event.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)
    return event


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a thermal event",
    description="Deletes a thermal anomaly record and all related AI classifications or alerts.",
)
def delete_thermal_event(
    event_id: str,
    db: Session = Depends(get_db),
):
    query = db.query(ThermalEvent)
    if event_id.isdigit():
        event = query.filter(or_(ThermalEvent.id == int(event_id), ThermalEvent.event_id == event_id)).first()
    else:
        event = query.filter(ThermalEvent.event_id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event with identifier '{event_id}' not found.",
        )

    deleted_id = event.event_id
    db.delete(event)
    db.commit()
    return {
        "status": "success",
        "message": f"Thermal event '{deleted_id}' deleted successfully.",
        "event_id": deleted_id,
    }


@router.post(
    "/seed",
    summary="Seed realistic industrial demo thermal events",
    description="Populates the database with 5 realistic industrial thermal anomalies with geographical coordinates, associated facilities, and AI classifications.",
)
def trigger_seed_demo_events(
    force: bool = Query(False, description="Whether to overwrite/re-seed existing demo records"),
    db: Session = Depends(get_db),
):
    result = seed_demo_thermal_events(db=db, force=force)
    return result


from pydantic import BaseModel as _PydanticBase


class ThermalSimulationRequest(_PydanticBase):
    template: str = "Industrial Fire"
    facility_name: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@router.post(
    "/simulate",
    summary="Simulate a thermal anomaly through the real automated pipeline",
    description="Creates a simulated thermal event and triggers the entire AI classification, risk analysis, operator routing, alert generation, and notification delivery pipeline."
)
def simulate_thermal_event_endpoint(
    req: Optional[ThermalSimulationRequest] = None,
    db: Session = Depends(get_db),
):
    from app.services.orchestration_service import process_thermal_event
    import random

    template_name = req.template if req else "Industrial Fire"

    TEMPLATES = {
        "Industrial Fire": {
            "intensity": "Critical (1250 MW)",
            "persistence": "Continuous (36+ hours active)",
            "facility_name": "Jamnagar Petrochemical Complex",
            "city": "Jamnagar",
            "state": "Gujarat",
            "lat": 22.3039,
            "lng": 70.8022,
            "event_type": "Industrial Fire"
        },
        "High-Risk Thermal": {
            "intensity": "High (650 MW)",
            "persistence": "Sustained (8 hours active)",
            "facility_name": "Hazira Steel & Heavy Manufacturing Works",
            "city": "Hazira",
            "state": "Gujarat",
            "lat": 21.1167,
            "lng": 72.6500,
            "event_type": "High-Risk Thermal Event"
        },
        "Gas Flare": {
            "intensity": "Moderate (380 MW)",
            "persistence": "Intermittent Flaring Cycle (< 4 hours)",
            "facility_name": "Mumbai High Offshore Processing Platform",
            "city": "Mumbai Offshore",
            "state": "Maharashtra",
            "lat": 19.0760,
            "lng": 72.8777,
            "event_type": "Gas Flare"
        },
        "Persistent Thermal Source": {
            "intensity": "High (520 MW)",
            "persistence": "Continuous Baseline Thermal Source (90+ days)",
            "facility_name": "NTPC Simhadri Super Thermal Power Station",
            "city": "Visakhapatnam",
            "state": "Andhra Pradesh",
            "lat": 17.6868,
            "lng": 83.2185,
            "event_type": "Persistent Thermal Source"
        }
    }

    t = TEMPLATES.get(template_name, TEMPLATES["Industrial Fire"])

    jitter_lat = (random.random() - 0.5) * 0.05
    jitter_lng = (random.random() - 0.5) * 0.05

    lat = (req.latitude if req and req.latitude is not None else t["lat"]) + jitter_lat
    lon = (req.longitude if req and req.longitude is not None else t["lng"]) + jitter_lng
    fac_name = (req.facility_name if req and req.facility_name else t["facility_name"])

    fac = db.query(IndustrialFacility).filter(IndustrialFacility.name.ilike(f"%{fac_name[:12]}%")).first()

    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_event_id = f"SIM-{today_str}-{uuid.uuid4().hex[:6].upper()}"

    thermal_event = ThermalEvent(
        event_id=unique_event_id,
        latitude=lat,
        longitude=lon,
        detected_at=datetime.now(timezone.utc),
        event_type=t["event_type"],
        thermal_intensity=t["intensity"],
        persistence=t["persistence"],
        confidence=95.0,
        risk_score=85.0,
        risk_priority="CRITICAL" if "Fire" in template_name else "HIGH",
        facility_id=fac.id if fac else None,
        land_cover="Industrial Perimeter",
        data_source="NASA FIRMS (Automated Simulation)",
        status="active",
        is_demo=True,
    )
    db.add(thermal_event)
    db.commit()
    db.refresh(thermal_event)

    # Run complete orchestration pipeline
    pipeline_res = process_thermal_event(thermal_event, db=db, force_alert=True)
    db.refresh(thermal_event)

    return {
        "status": "success",
        "message": f"Simulated thermal event '{thermal_event.event_id}' processed through real pipeline.",
        "event": ThermalEventResponse.model_validate(thermal_event),
        "pipeline": pipeline_res
    }
