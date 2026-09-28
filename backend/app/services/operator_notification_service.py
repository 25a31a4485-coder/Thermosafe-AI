import math
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.operator_team import EmergencyResponseTeam, EmergencyDispatchLog
from app.models.thermal_event import ThermalEvent
from app.models.alert import Alert

logger = logging.getLogger("operator_notification_service")


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two coordinates in kilometers using Haversine formula."""
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


class OperatorNotificationService:
    """
    AI-Powered Geospatial Emergency Response & Operator Team Notification Service.
    Identifies the optimal nearby emergency response unit based on spatial proximity,
    specialization, and operational status, and manages emergency dispatch tasking.
    """

    @staticmethod
    def find_nearest_teams(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 60.0,
        max_results: int = 5,
        required_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Finds and ranks all emergency response teams ordered by proximity to the coordinates.
        """
        query = db.query(EmergencyResponseTeam)
        if required_status:
            query = query.filter(EmergencyResponseTeam.status == required_status)
        else:
            # By default include available, on_call, and even dispatched teams
            query = query.filter(EmergencyResponseTeam.status != "off_duty")

        teams = query.all()
        ranked = []
        for t in teams:
            dist = haversine_distance_km(latitude, longitude, t.latitude, t.longitude)
            is_within_coverage = dist <= max(radius_km, t.coverage_radius_km)
            ranked.append({
                "team": t,
                "distance_km": round(dist, 2),
                "is_within_coverage": is_within_coverage
            })

        # Sort by distance ascending
        ranked.sort(key=lambda x: x["distance_km"])

        # Filter strictly within coverage unless empty, then take nearest overall
        filtered = [item for item in ranked if item["is_within_coverage"]]
        if not filtered and ranked:
            filtered = ranked[:1]  # Fallback to absolute nearest

        return filtered[:max_results]

    @staticmethod
    def dispatch_emergency_team(
        db: Session,
        thermal_event: ThermalEvent,
        alert: Optional[Alert] = None,
        preferred_team_id: Optional[int] = None,
        dispatch_channel: str = "AUTOMATED_SMS",
        force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates thermal event priority and automatically tasks the nearest
        appropriate operator team when risk is HIGH or CRITICAL.
        """
        priority_norm = (thermal_event.risk_priority or "LOW").strip().upper()
        is_emergency = priority_norm in ["HIGH", "CRITICAL"] or (thermal_event.risk_score or 0) >= 50.0

        if not is_emergency and not force:
            logger.info(
                f"Thermal event {thermal_event.event_id} with priority '{priority_norm}' "
                f"does not meet operator emergency notification threshold (HIGH/CRITICAL). Skipped."
            )
            return None

        # Determine target team
        target_team = None
        target_dist = 0.0

        if preferred_team_id:
            target_team = db.query(EmergencyResponseTeam).filter(EmergencyResponseTeam.id == preferred_team_id).first()
            if target_team:
                target_dist = haversine_distance_km(
                    thermal_event.latitude, thermal_event.longitude,
                    target_team.latitude, target_team.longitude
                )

        if not target_team:
            nearby = OperatorNotificationService.find_nearest_teams(
                db=db,
                latitude=thermal_event.latitude,
                longitude=thermal_event.longitude,
                radius_km=100.0,
                max_results=1
            )
            if nearby:
                target_team = nearby[0]["team"]
                target_dist = nearby[0]["distance_km"]

        if not target_team:
            logger.warning(f"No operator/emergency response team found in database for event {thermal_event.event_id}.")
            return None

        # Build emergency dispatch message
        facility_str = f" at {thermal_event.facility.name}" if thermal_event.facility else ""
        msg = (
            f"URGENT DISPATCH [{priority_norm} RISK]: {thermal_event.event_type}{facility_str}. "
            f"Coordinates: {thermal_event.latitude:.4f}° N, {thermal_event.longitude:.4f}° E "
            f"({target_dist:.1f} km from your station). Risk Score: {thermal_event.risk_score:.1f}/100. "
            f"Intensity: {thermal_event.thermal_intensity or 'HIGH'}. Tactical team mobilized."
        )

        dispatch_log = EmergencyDispatchLog(
            team_id=target_team.id,
            thermal_event_id=thermal_event.id,
            alert_id=alert.id if alert else None,
            event_id=thermal_event.event_id,
            distance_km=round(target_dist, 2),
            risk_priority=priority_norm,
            risk_score=thermal_event.risk_score,
            dispatch_channel=dispatch_channel,
            status="DISPATCHED",
            message=msg,
        )

        # Update team operational status to dispatched
        target_team.status = "dispatched"

        db.add(dispatch_log)
        db.commit()
        db.refresh(dispatch_log)
        db.refresh(target_team)

        logger.info(
            f"Successfully dispatched emergency team '{target_team.name}' (ID:{target_team.id}) "
            f"to incident {thermal_event.event_id} ({target_dist:.1f} km away)."
        )

        return {
            "dispatched": True,
            "team_id": target_team.id,
            "team_name": target_team.name,
            "team_type": target_team.team_type,
            "contact_phone": target_team.contact_phone,
            "radio_frequency": target_team.radio_frequency,
            "distance_km": round(target_dist, 2),
            "status": "DISPATCHED",
            "dispatch_id": dispatch_log.id,
            "message": msg,
            "dispatch_log": dispatch_log,
        }


def get_operator_service() -> OperatorNotificationService:
    """Dependency provider for OperatorNotificationService."""
    return OperatorNotificationService()
