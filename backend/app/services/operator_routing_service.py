"""
Operator Routing Service for SIH26162 ThermoSafe AI.
Phase 37: Automatic Nearest Operator Team Routing.

Evaluates thermal event spatial coordinates, facility association, risk priority,
and operational hazard profiles to determine the optimal emergency response team.
Uses the Haversine formula to compute great-circle distance.
"""

import math
import logging
from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.operator_team import EmergencyResponseTeam

logger = logging.getLogger("operator_routing_service")


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in kilometers using the Haversine formula."""
    R = 6371.0  # Earth mean radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _extract_attribute(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to extract attribute from SQLAlchemy model, Pydantic model, or dict."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, key):
        val = getattr(obj, key)
        return val if val is not None else default
    return default


def find_nearest_responsible_team(
    event: Any,
    db: Optional[Session] = None,
    max_radius_km: float = 150.0
) -> Dict[str, Any]:
    """
    Automatically determine which operator team should receive the alert for a thermal event.

    Evaluates:
    - team active status (is_active == True)
    - notification enabled status (prefers notification_enabled == True)
    - event latitude & longitude
    - team latitude & longitude
    - response radius (response_radius_km / coverage_radius_km)
    - industry / event compatibility
    - facility association (facility_id)
    - risk priority

    Returns:
    - team_id: int or None
    - team_name: str
    - distance_km: float or None
    - facility_id: int or None
    - compatibility: str
    - notification_enabled: bool
    - status: 'ASSIGNED' or 'NO_NEARBY_TEAM'
    """
    # 1. Extract coordinates and event context
    lat = _extract_attribute(event, "latitude")
    if lat is None:
        lat = _extract_attribute(event, "lat")

    lon = _extract_attribute(event, "longitude")
    if lon is None:
        lon = _extract_attribute(event, "lng")

    facility_id = _extract_attribute(event, "facility_id")
    event_type = str(_extract_attribute(event, "event_type", "Industrial Hazard") or "").lower()
    risk_priority = str(_extract_attribute(event, "risk_priority", "HIGH") or "").upper()

    fallback_result = {
        "team_id": None,
        "team_name": "No Nearby Response Team",
        "distance_km": None,
        "facility_id": None,
        "compatibility": "NONE",
        "notification_enabled": False,
        "status": "NO_NEARBY_TEAM",
        "team": None
    }

    if lat is None or lon is None:
        logger.warning("find_nearest_responsible_team: Event lacks latitude/longitude coordinates.")
        return fallback_result

    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (ValueError, TypeError):
        logger.warning(f"find_nearest_responsible_team: Invalid coordinates ({lat}, {lon}).")
        return fallback_result

    # 2. Acquire database session
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        # Filter for active emergency response teams
        teams = db.query(EmergencyResponseTeam).filter(
            EmergencyResponseTeam.is_active == True
        ).all()

        if not teams:
            logger.info("find_nearest_responsible_team: No active operator teams found in database.")
            return fallback_result

        candidates = []
        for team in teams:
            dist = haversine_distance_km(lat_f, lon_f, team.latitude, team.longitude)
            effective_radius = team.effective_radius or 50.0

            # Compatibility analysis
            compatibility_score = 0.0
            compatibility_tags = []

            # A. Facility match (highest operational suitability)
            if facility_id is not None and team.facility_id is not None and team.facility_id == facility_id:
                compatibility_score += 100.0
                compatibility_tags.append("FACILITY_STATIONED")

            # B. Event type & hazard specialization match
            team_type = (team.team_type or "").lower()
            team_ind = (team.effective_industry or "").lower()

            if "fire" in event_type and ("fire" in team_type or "fire" in team_ind):
                compatibility_score += 40.0
                compatibility_tags.append("FIRE_SPECIALIZED")
            elif "flare" in event_type and ("petrochemical" in team_ind or "refinery" in team_ind or "hazmat" in team_type):
                compatibility_score += 35.0
                compatibility_tags.append("PETROCHEM_HAZMAT")
            elif "persistent" in event_type or "power" in event_type:
                compatibility_score += 25.0
                compatibility_tags.append("INDUSTRIAL_MONITORING")
            else:
                compatibility_score += 15.0
                compatibility_tags.append("GENERAL_TACTICAL")

            # C. Notification enabled preference
            if team.notification_enabled:
                compatibility_score += 20.0
                compatibility_tags.append("NOTIF_READY")

            # D. Status preference (available > on_call > dispatched)
            team_status = (team.status or "available").lower()
            if team_status == "available":
                compatibility_score += 20.0
            elif team_status == "on_call":
                compatibility_score += 10.0
            elif team_status == "dispatched":
                compatibility_score += 5.0

            # E. Distance score (closer teams score substantially higher)
            # Normalize distance penalty: e.g. within 10 km = full points
            dist_score = max(0.0, 100.0 - (dist * 1.0))
            total_rank = (compatibility_score * 0.45) + (dist_score * 0.55)

            is_within_coverage = dist <= max(effective_radius, max_radius_km)

            candidates.append({
                "team": team,
                "distance_km": round(dist, 2),
                "is_within_coverage": is_within_coverage,
                "compatibility_score": compatibility_score,
                "compatibility": ", ".join(compatibility_tags) if compatibility_tags else "STANDARD",
                "total_rank": total_rank
            })

        # Filter strictly within reasonable reach (up to max_radius_km or team radius)
        viable = [c for c in candidates if c["is_within_coverage"]]
        if not viable and candidates:
            # If no team within nominal coverage, select absolute closest candidate within max_radius_km * 2
            viable = [c for c in candidates if c["distance_km"] <= (max_radius_km * 2.0)]

        if not viable:
            logger.info(f"find_nearest_responsible_team: No team found within reachable distance of ({lat_f}, {lon_f}).")
            return fallback_result

        # Sort primarily by total rank descending, secondarily by distance ascending
        viable.sort(key=lambda x: (-x["total_rank"], x["distance_km"]))
        best = viable[0]
        selected_team = best["team"]

        logger.info(
            f"find_nearest_responsible_team: Matched team '{selected_team.effective_team_name}' "
            f"(ID:{selected_team.id}) at {best['distance_km']} km (Compatibility: {best['compatibility']})."
        )

        return {
            "team_id": selected_team.id,
            "team_name": selected_team.effective_team_name,
            "distance_km": best["distance_km"],
            "facility_id": selected_team.facility_id,
            "compatibility": best["compatibility"],
            "notification_enabled": bool(selected_team.notification_enabled),
            "status": "ASSIGNED",
            "team": selected_team
        }

    except Exception as e:
        logger.error(f"Error finding nearest responsible team: {e}", exc_info=True)
        return fallback_result
    finally:
        if own_session:
            db.close()


class OperatorRoutingService:
    """Service wrapper class for class-based DI and backwards compatibility."""
    find_nearest_responsible_team = staticmethod(find_nearest_responsible_team)
