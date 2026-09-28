import math
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.operator_team import EmergencyResponseTeam, EmergencyDispatchLog
from app.models.thermal_event import ThermalEvent
from app.models.user import User
from app.models.facility import IndustrialFacility
from app.schemas.operator_team import (
    OperatorTeamCreate,
    OperatorTeamUpdate,
    OperatorTeamResponse,
    OperatorTeamNearbyResponse,
    OperatorTeamNearbyItem,
    EmergencyDispatchLogResponse,
)
from app.services.operator_notification_service import OperatorNotificationService, get_operator_service

router = APIRouter(
    prefix="/operator-teams",
    tags=["Operator Teams & Emergency Notifications"]
)


def _format_team_response(team: EmergencyResponseTeam) -> OperatorTeamResponse:
    assigned = []
    member_names = []
    if team.members:
        for u in team.members:
            role_val = u.role.value if hasattr(u.role, "value") else str(u.role)
            assigned.append({
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": role_val,
            })
            member_names.append(u.full_name or u.email)
    fac_name = team.facility.name if team.facility else None
    fac_type = team.facility.industry_type if team.facility else (team.industry_type or team.team_type)
    resp = OperatorTeamResponse.model_validate(team)
    resp.facility_name = fac_name
    resp.facility_type = fac_type
    resp.assigned_users = assigned
    if not member_names and team.contact_person:
        member_names = [team.contact_person]
    resp.team_members = member_names
    resp.team_email = team.effective_email
    resp.team_phone = team.effective_phone
    resp.specialization = team.team_type
    return resp


@router.get(
    "",
    response_model=List[OperatorTeamResponse],
    summary="List all industrial emergency response teams",
    description="Retrieves registered emergency operator teams with optional filtering by operational status, team type, or facility."
)
def list_operator_teams(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: available, dispatched, on_call, off_duty"),
    team_type: Optional[str] = Query(None, description="Filter by team type keyword"),
    facility_id: Optional[int] = Query(None, description="Filter by industrial facility ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(EmergencyResponseTeam)
    if status_filter:
        query = query.filter(EmergencyResponseTeam.status == status_filter.strip().lower())
    if team_type:
        query = query.filter(
            (EmergencyResponseTeam.team_type.ilike(f"%{team_type.strip()}%")) |
            (EmergencyResponseTeam.industry_type.ilike(f"%{team_type.strip()}%"))
        )
    if facility_id:
        query = query.filter(EmergencyResponseTeam.facility_id == facility_id)
    if is_active is not None:
        query = query.filter(EmergencyResponseTeam.is_active == is_active)

    offset = (page - 1) * page_size
    teams = query.order_by(EmergencyResponseTeam.id.asc()).offset(offset).limit(page_size).all()
    return [_format_team_response(t) for t in teams]


@router.get(
    "/nearby",
    response_model=OperatorTeamNearbyResponse,
    summary="Find nearest emergency response teams by coordinates",
    description="Geospatial proximity query calculating distance from given latitude/longitude to all available operator teams."
)
def get_nearby_teams(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Target event latitude"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Target event longitude"),
    radius_km: float = Query(60.0, gt=0, le=500.0, description="Search radius in kilometers"),
    max_results: int = Query(5, ge=1, le=20, description="Maximum teams to return"),
    status_filter: Optional[str] = Query(None, alias="status", description="Required status filter"),
    db: Session = Depends(get_db),
    operator_service: OperatorNotificationService = Depends(get_operator_service),
):
    nearby_items = operator_service.find_nearest_teams(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        max_results=max_results,
        required_status=status_filter,
    )

    formatted_items = []
    for item in nearby_items:
        formatted_items.append(
            OperatorTeamNearbyItem(
                team=_format_team_response(item["team"]),
                distance_km=item["distance_km"],
                is_within_coverage=item["is_within_coverage"]
            )
        )

    return OperatorTeamNearbyResponse(
        total=len(formatted_items),
        query_latitude=latitude,
        query_longitude=longitude,
        radius_km=radius_km,
        items=formatted_items
    )


@router.get(
    "/dispatches/logs",
    response_model=List[EmergencyDispatchLogResponse],
    summary="List emergency dispatch notification audit trail",
    description="Returns chronological audit logs of emergency notifications dispatched to operator teams."
)
def list_dispatch_logs(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return db.query(EmergencyDispatchLog).order_by(desc(EmergencyDispatchLog.dispatched_at)).limit(limit).all()


@router.get(
    "/{team_id}",
    response_model=OperatorTeamResponse,
    summary="Get operator team details by ID",
)
def get_operator_team(
    team_id: int,
    db: Session = Depends(get_db),
):
    team = db.query(EmergencyResponseTeam).filter(EmergencyResponseTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator team with ID {team_id} not found."
        )
    return _format_team_response(team)


@router.post(
    "",
    response_model=OperatorTeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new emergency response team",
)
def create_operator_team(
    team_in: OperatorTeamCreate,
    db: Session = Depends(get_db),
):
    import re
    # Validation
    email_val = (team_in.team_email or team_in.email or team_in.contact_email or "").strip()
    if email_val and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_val):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid team email format: {email_val}")

    phone_val = (team_in.team_phone or team_in.phone or team_in.contact_phone or "").strip()
    if phone_val and len(re.sub(r"\D", "", phone_val)) < 7:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid team phone number: {phone_val}")

    team_name_val = (team_in.team_name or team_in.name or "").strip()
    if not team_name_val:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team name is required.")

    # Facility association
    facility_id = team_in.facility_id
    if not facility_id and team_in.facility_name:
        fac = db.query(IndustrialFacility).filter(
            IndustrialFacility.name.ilike(f"%{team_in.facility_name.strip()}%")
        ).first()
        if fac:
            facility_id = fac.id

    if facility_id:
        facility = db.query(IndustrialFacility).filter(IndustrialFacility.id == facility_id).first()
        if not facility:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Associated facility ID {facility_id} does not exist.")

    # Filter data to model columns only
    valid_cols = set(EmergencyResponseTeam.__table__.columns.keys())
    raw_dict = team_in.model_dump()
    data = {k: v for k, v in raw_dict.items() if k in valid_cols and v is not None}

    data["name"] = team_name_val
    data["team_name"] = team_name_val
    data["contact_phone"] = phone_val or "+91-288-2234-911"
    data["phone"] = data["contact_phone"]
    data["contact_email"] = email_val or None
    data["email"] = data["contact_email"]
    data["team_type"] = team_in.specialization or team_in.team_type or "Industrial Fire Brigade"
    data["industry_type"] = team_in.facility_type or team_in.industry_type or data["team_type"]
    data["coverage_radius_km"] = team_in.response_radius_km or team_in.coverage_radius_km or 50.0
    data["response_radius_km"] = data["coverage_radius_km"]
    data["facility_id"] = facility_id
    data["notification_enabled"] = team_in.notification_enabled
    data["call_escalation_enabled"] = team_in.call_escalation_enabled
    data["is_active"] = team_in.is_active

    team = EmergencyResponseTeam(**data)
    db.add(team)
    db.commit()
    db.refresh(team)

    # Assign users if requested
    if team_in.assigned_user_ids:
        users = db.query(User).filter(User.id.in_(team_in.assigned_user_ids)).all()
        for u in users:
            u.operator_team_id = team.id
        db.commit()
        db.refresh(team)

    return _format_team_response(team)


@router.put(
    "/{team_id}",
    response_model=OperatorTeamResponse,
    summary="Update operator team status, configuration, or assigned personnel",
)
def update_operator_team(
    team_id: int,
    team_in: OperatorTeamUpdate,
    db: Session = Depends(get_db),
):
    import re
    team = db.query(EmergencyResponseTeam).filter(EmergencyResponseTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator team with ID {team_id} not found."
        )

    dump = team_in.model_dump(exclude_unset=True)
    assigned_user_ids = dump.pop("assigned_user_ids", None)
    dump.pop("team_members", None)
    fac_name = dump.pop("facility_name", None)
    spec = dump.pop("specialization", None)
    fac_type = dump.pop("facility_type", None)

    # Email and phone validation
    if "email" in dump or "contact_email" in dump or "team_email" in dump:
        email_val = (dump.get("team_email") or dump.get("email") or dump.get("contact_email") or "").strip()
        if email_val and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_val):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid team email format: {email_val}")
        dump["email"] = email_val
        dump["contact_email"] = email_val

    if "phone" in dump or "contact_phone" in dump or "team_phone" in dump:
        phone_val = (dump.get("team_phone") or dump.get("phone") or dump.get("contact_phone") or "").strip()
        if phone_val and len(re.sub(r"\D", "", phone_val)) < 7:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid team phone number: {phone_val}")
        dump["phone"] = phone_val
        dump["contact_phone"] = phone_val

    if spec:
        dump["team_type"] = spec
    if fac_type:
        dump["industry_type"] = fac_type

    if fac_name and "facility_id" not in dump:
        fac = db.query(IndustrialFacility).filter(
            IndustrialFacility.name.ilike(f"%{fac_name.strip()}%")
        ).first()
        if fac:
            dump["facility_id"] = fac.id

    if "facility_id" in dump and dump["facility_id"] is not None:
        facility = db.query(IndustrialFacility).filter(IndustrialFacility.id == dump["facility_id"]).first()
        if not facility:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Associated facility ID {dump['facility_id']} does not exist.")

    # Sync aliases
    if "team_name" in dump:
        dump["name"] = dump["team_name"]
    elif "name" in dump:
        dump["team_name"] = dump["name"]

    valid_cols = set(EmergencyResponseTeam.__table__.columns.keys())
    for field, val in dump.items():
        if field in valid_cols:
            setattr(team, field, val)

    # Re-assign users if specified
    if assigned_user_ids is not None:
        current_members = db.query(User).filter(User.operator_team_id == team.id).all()
        for cm in current_members:
            cm.operator_team_id = None

        if assigned_user_ids:
            new_members = db.query(User).filter(User.id.in_(assigned_user_ids)).all()
            for nm in new_members:
                nm.operator_team_id = team.id

    db.commit()
    db.refresh(team)
    return _format_team_response(team)


@router.patch(
    "/{team_id}/toggle-active",
    response_model=OperatorTeamResponse,
    summary="Activate or deactivate an operator team",
)
def toggle_operator_team_active(
    team_id: int,
    db: Session = Depends(get_db),
):
    team = db.query(EmergencyResponseTeam).filter(EmergencyResponseTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator team with ID {team_id} not found."
        )
    team.is_active = not team.is_active
    db.commit()
    db.refresh(team)
    return _format_team_response(team)


@router.delete(
    "/{team_id}",
    summary="Delete or deactivate an emergency response team",
)
def delete_operator_team(
    team_id: int,
    db: Session = Depends(get_db),
):
    team = db.query(EmergencyResponseTeam).filter(EmergencyResponseTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator team with ID {team_id} not found."
        )

    # Unlink assigned users
    for u in team.members:
        u.operator_team_id = None

    db.delete(team)
    db.commit()
    return {"status": "success", "message": f"Operator team {team_id} successfully deleted."}


@router.post(
    "/dispatch",
    summary="Trigger emergency notification dispatch to nearby operator team",
    description="Mobilizes and tasks an operator team for a detected thermal incident."
)
def trigger_dispatch(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    operator_service: OperatorNotificationService = Depends(get_operator_service),
):
    event_id = payload.get("event_id")
    if not event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'event_id' is required to dispatch an emergency response team."
        )

    # Lookup thermal event
    thermal_event = db.query(ThermalEvent).filter(
        (ThermalEvent.event_id == str(event_id)) | (ThermalEvent.id == int(event_id) if str(event_id).isdigit() else False)
    ).first()

    if not thermal_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    preferred_team_id = payload.get("team_id")
    dispatch_channel = payload.get("dispatch_channel", "AUTOMATED_DISPATCH_CONSOLE")

    dispatch_result = operator_service.dispatch_emergency_team(
        db=db,
        thermal_event=thermal_event,
        preferred_team_id=preferred_team_id,
        dispatch_channel=dispatch_channel,
        force=True
    )

    if not dispatch_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to dispatch emergency response team. No active response unit found."
        )

    return {
        "status": "success",
        "message": f"Emergency response team '{dispatch_result['team_name']}' successfully mobilized.",
        "dispatch_id": dispatch_result["dispatch_id"],
        "team_name": dispatch_result["team_name"],
        "team_phone": dispatch_result["contact_phone"],
        "distance_km": dispatch_result["distance_km"],
        "operational_status": dispatch_result["status"],
    }
