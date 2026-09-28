from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.device import UserDevice
from app.models.user import User
from app.models.operator_team import EmergencyResponseTeam
from app.schemas.device import (
    DeviceRegisterRequest,
    DeviceUpdateRequest,
    DeviceResponse,
)
from app.core.security import decode_access_token

router = APIRouter(
    prefix="/devices",
    tags=["Browser & Device Push Registrations"]
)


def _get_user_from_header(authorization: Optional[str], db: Session) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ")[1].strip()
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        return None
    try:
        user_id = int(payload.get("sub"))
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None


def _format_device_response(device: UserDevice) -> DeviceResponse:
    team_name = None
    if device.operator_team:
        team_name = device.operator_team.team_name or device.operator_team.name
    elif device.user and device.user.operator_team:
        team_name = device.user.operator_team.team_name or device.user.operator_team.name

    resp = DeviceResponse.model_validate(device)
    resp.operator_team_name = team_name
    return resp


@router.post(
    "/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register or update browser / mobile notification endpoint",
    description="Registers client device fingerprint, push token, and permission state for targeted alert dispatch."
)
def register_device(
    payload: DeviceRegisterRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    current_user = _get_user_from_header(authorization, db)
    if not current_user:
        # Fallback to first active user if unauthenticated for local/demo flexibility
        current_user = db.query(User).filter(User.is_active == True).first()
        if not current_user:
            # Create a default operator user if none exists
            from app.core.security import hash_password
            from app.models.user import UserRole
            current_user = User(
                email="operator@thermosafe.ai",
                full_name="Duty Watch Operator",
                hashed_password=hash_password("ThermoSafePass123!"),
                role=UserRole.OPERATOR,
                is_active=True
            )
            db.add(current_user)
            db.commit()
            db.refresh(current_user)

    now = datetime.now(timezone.utc)
    team_id = payload.operator_team_id or current_user.operator_team_id

    # Check for existing device registration for this user and identifier
    existing = db.query(UserDevice).filter(
        UserDevice.user_id == current_user.id,
        UserDevice.device_identifier == payload.device_identifier
    ).first()

    if existing:
        changed = False
        if payload.platform and existing.platform != payload.platform:
            existing.platform = payload.platform
            changed = True
        if payload.browser and existing.browser != payload.browser:
            existing.browser = payload.browser
            changed = True
        if payload.notification_permission and existing.notification_permission != payload.notification_permission:
            existing.notification_permission = payload.notification_permission
            changed = True
        if payload.push_token and existing.push_token != payload.push_token:
            existing.push_token = payload.push_token
            changed = True
        if team_id and existing.operator_team_id != team_id:
            existing.operator_team_id = team_id
            changed = True
        if not existing.is_active:
            existing.is_active = True
            changed = True

        time_diff = (now - existing.last_seen_at.replace(tzinfo=timezone.utc)).total_seconds() if (existing.last_seen_at and existing.last_seen_at.tzinfo) else 9999
        if changed or time_diff > 1800:
            existing.last_seen_at = now
            db.commit()
            db.refresh(existing)
        return _format_device_response(existing)

    new_device = UserDevice(
        user_id=current_user.id,
        operator_team_id=team_id,
        device_identifier=payload.device_identifier,
        push_token=payload.push_token,
        platform=payload.platform or "web",
        browser=payload.browser,
        notification_permission=payload.notification_permission or "default",
        is_active=True,
        last_seen_at=now
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return _format_device_response(new_device)


@router.get(
    "",
    response_model=List[DeviceResponse],
    summary="List registered devices",
    description="Retrieves registered browser and mobile device push endpoints."
)
def list_devices(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    operator_team_id: Optional[int] = Query(None, description="Filter by operator team ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    query = db.query(UserDevice)
    current_user = _get_user_from_header(authorization, db)

    # Non-admin users only see their own devices by default if no user_id query
    if current_user and current_user.role != "admin" and not user_id:
        query = query.filter(UserDevice.user_id == current_user.id)
    elif user_id:
        query = query.filter(UserDevice.user_id == user_id)

    if operator_team_id:
        query = query.filter(UserDevice.operator_team_id == operator_team_id)
    if is_active is not None:
        query = query.filter(UserDevice.is_active == is_active)

    devices = query.order_by(desc(UserDevice.last_seen_at)).all()
    return [_format_device_response(d) for d in devices]


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Update device push settings or active status",
)
def update_device(
    device_id: int,
    payload: DeviceUpdateRequest,
    db: Session = Depends(get_db),
):
    device = db.query(UserDevice).filter(UserDevice.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device registration {device_id} not found."
        )

    dump = payload.model_dump(exclude_unset=True)
    for field, val in dump.items():
        if hasattr(device, field):
            setattr(device, field, val)

    device.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(device)
    return _format_device_response(device)


@router.delete(
    "/{device_id}",
    summary="Deregister device push endpoint",
)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
):
    device = db.query(UserDevice).filter(UserDevice.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device registration {device_id} not found."
        )

    db.delete(device)
    db.commit()
    return {"status": "success", "message": f"Device {device_id} successfully deregistered."}
