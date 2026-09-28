import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.core.database import get_db
from app.models.facility import IndustrialFacility
from app.schemas.facility import (
    IndustrialFacilityCreate,
    IndustrialFacilityUpdate,
    IndustrialFacilityResponse,
    IndustrialFacilityPaginatedResponse,
)
from app.core.seed import seed_demo_facilities

router = APIRouter(prefix="/facilities", tags=["Industrial Facilities"])


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


@router.get(
    "",
    response_model=IndustrialFacilityPaginatedResponse,
    summary="Query and filter monitored industrial facilities",
    description="""
    Retrieves a paginated list of industrial facilities with multi-criteria filtering:
    - **Industry Sector**: filter by industry_type (e.g. Refinery, Steel, Power, Chemical, Port).
    - **Risk Category**: filter by risk_level (High, Medium, Low).
    - **Geographic Area**:
      - Region/State/City address text search (e.g. 'Gujarat', 'Surat', 'Mumbai', 'Andhra Pradesh').
      - Spatial proximity via center coordinates (`latitude`, `longitude`, `radius_km`).
      - Bounding box coordinates (`min_lat`, `max_lat`, `min_lon`, `max_lon` or `bbox`).
    - **Demo Marker**: filter simulated vs production facilities (`is_demo`).
    - **Sorting**: sort by name, risk_level, or creation date.
    """,
)
def get_facilities(
    industry_type: Optional[str] = Query(None, description="Filter by industry type (e.g. 'Refinery', 'Steel', 'Power')"),
    risk_level: Optional[str] = Query(None, description="Filter by facility risk level (e.g. 'High', 'Medium', 'Low')"),
    area: Optional[str] = Query(None, description="Filter by geographic area or region within address (e.g. 'Gujarat', 'Mumbai')"),
    is_demo: Optional[bool] = Query(None, description="Filter by demonstration/simulated facility status"),
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Center latitude for proximity radius query (-90.0 to +90.0)"),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Center longitude for proximity radius query (-180.0 to +180.0)"),
    radius_km: Optional[float] = Query(50.0, gt=0, description="Search radius in kilometers around center latitude/longitude"),
    min_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Bounding box minimum latitude"),
    max_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Bounding box maximum latitude"),
    min_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Bounding box minimum longitude"),
    max_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Bounding box maximum longitude"),
    bbox: Optional[str] = Query(None, description="Bounding box string in format: min_lon,min_lat,max_lon,max_lat"),
    sort_by: str = Query("name", description="Sort criteria: name, risk_level, created_at"),
    sort_order: str = Query("asc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    query = db.query(IndustrialFacility)

    # 1. Industry Type Filter
    if industry_type:
        query = query.filter(IndustrialFacility.industry_type.ilike(f"%{industry_type.strip()}%"))

    # 2. Risk Level Filter
    if risk_level:
        query = query.filter(IndustrialFacility.risk_level.ilike(risk_level.strip()))

    # 3. Geographic Area Filter (Address / Region text match)
    if area:
        query = query.filter(
            or_(
                IndustrialFacility.address.ilike(f"%{area.strip()}%"),
                IndustrialFacility.name.ilike(f"%{area.strip()}%"),
                IndustrialFacility.operator.ilike(f"%{area.strip()}%"),
            )
        )

    # 4. Demo Filter
    if is_demo is not None:
        query = query.filter(IndustrialFacility.is_demo == is_demo)

    # 5. Bounding Box Filter
    bbox_min_lat, bbox_max_lat = min_lat, max_lat
    bbox_min_lon, bbox_max_lon = min_lon, max_lon

    if bbox:
        try:
            parts = [float(p.strip()) for p in bbox.split(",")]
            if len(parts) == 4:
                bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat = parts
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bbox format. Expected 'min_lon,min_lat,max_lon,max_lat' with numerical values."
            )

    if bbox_min_lat is not None and bbox_max_lat is not None:
        if bbox_min_lat > bbox_max_lat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"min_lat ({bbox_min_lat}) cannot be greater than max_lat ({bbox_max_lat})."
            )
        query = query.filter(IndustrialFacility.latitude >= bbox_min_lat, IndustrialFacility.latitude <= bbox_max_lat)

    if bbox_min_lon is not None and bbox_max_lon is not None:
        if bbox_min_lon > bbox_max_lon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"min_lon ({bbox_min_lon}) cannot be greater than max_lon ({bbox_max_lon})."
            )
        query = query.filter(IndustrialFacility.longitude >= bbox_min_lon, IndustrialFacility.longitude <= bbox_max_lon)

    # 6. Spatial Proximity Filter (Haversine distance)
    has_proximity = latitude is not None or longitude is not None
    if has_proximity:
        if latitude is None or longitude is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both 'latitude' and 'longitude' must be provided together for proximity search."
            )
        deg_lat = (radius_km or 50.0) / 111.0
        deg_lon = (radius_km or 50.0) / (111.0 * max(0.01, math.cos(math.radians(latitude))))
        query = query.filter(
            IndustrialFacility.latitude >= latitude - deg_lat,
            IndustrialFacility.latitude <= latitude + deg_lat,
            IndustrialFacility.longitude >= longitude - deg_lon,
            IndustrialFacility.longitude <= longitude + deg_lon,
        )

    # 7. Sorting
    is_desc = sort_order.lower() == "desc"
    sort_criterion = sort_by.lower()

    if sort_criterion == "name":
        query = query.order_by(desc(IndustrialFacility.name) if is_desc else asc(IndustrialFacility.name))
    elif sort_criterion in ["risk_level", "risk"]:
        query = query.order_by(desc(IndustrialFacility.risk_level) if is_desc else asc(IndustrialFacility.risk_level))
    elif sort_criterion in ["created_at", "date"]:
        query = query.order_by(desc(IndustrialFacility.created_at) if is_desc else asc(IndustrialFacility.created_at))
    else:
        query = query.order_by(asc(IndustrialFacility.name))

    all_matching = query.all()

    # Exact Haversine radial distance filter
    if has_proximity:
        all_matching = [
            fac for fac in all_matching
            if haversine_distance_km(latitude, longitude, fac.latitude, fac.longitude) <= radius_km
        ]

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
    "/{id}",
    response_model=IndustrialFacilityResponse,
    summary="Get single industrial facility details by ID",
    description="Retrieves a single facility record with full attributes and map geometry.",
)
def get_facility_by_id(
    id: int,
    db: Session = Depends(get_db),
):
    facility = db.query(IndustrialFacility).filter(IndustrialFacility.id == id).first()
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Industrial facility with ID {id} not found.",
        )
    return facility


@router.post(
    "",
    response_model=IndustrialFacilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new industrial facility",
    description="Creates a new monitored industrial facility. Validates coordinates (-90 to +90 lat, -180 to +180 lon).",
)
def create_facility(
    facility_in: IndustrialFacilityCreate,
    db: Session = Depends(get_db),
):
    facility = IndustrialFacility(
        name=facility_in.name,
        latitude=facility_in.latitude,
        longitude=facility_in.longitude,
        industry_type=facility_in.industry_type,
        operator=facility_in.operator,
        risk_level=facility_in.risk_level or "Medium",
        address=facility_in.address,
        is_demo=facility_in.is_demo,
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility


@router.put(
    "/{id}",
    response_model=IndustrialFacilityResponse,
    summary="Update an existing industrial facility",
    description="Updates attributes of an industrial facility. Re-validates coordinates if modified.",
)
def update_facility(
    id: int,
    facility_update: IndustrialFacilityUpdate,
    db: Session = Depends(get_db),
):
    facility = db.query(IndustrialFacility).filter(IndustrialFacility.id == id).first()
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Industrial facility with ID {id} not found.",
        )

    update_data = facility_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(facility, field, value)

    db.commit()
    db.refresh(facility)
    return facility


@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an industrial facility",
    description="Deletes an industrial facility record from the database.",
)
def delete_facility(
    id: int,
    db: Session = Depends(get_db),
):
    facility = db.query(IndustrialFacility).filter(IndustrialFacility.id == id).first()
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Industrial facility with ID {id} not found.",
        )

    facility_name = facility.name
    db.delete(facility)
    db.commit()
    return {
        "status": "success",
        "message": f"Industrial facility '{facility_name}' (ID: {id}) deleted successfully.",
        "id": id,
    }


@router.post(
    "/seed",
    summary="Seed demo industrial facilities",
    description="Populates the database with realistic demo industrial facilities across key industrial corridors in India.",
)
def trigger_seed_demo_facilities(
    force: bool = Query(False, description="Whether to overwrite existing demo facilities"),
    db: Session = Depends(get_db),
):
    result = seed_demo_facilities(db=db, force=force)
    return result
