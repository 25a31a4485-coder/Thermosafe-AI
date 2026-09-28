"""
Router for Alerts and Emergency Notification endpoints.
Provides threshold-triggered alert generation, listing, unread filtering,
and read-status updating.
"""

import os
from typing import Optional, Union, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.alert import Alert, NotificationDeliveryLog
from app.schemas.alert import (
    AlertCreate,
    AlertResponse,
    AlertUnreadResponse,
    AlertPaginatedResponse,
    AlertEvaluationRequest,
    AlertAcknowledgeRequest,
    NotificationDeliveryLogResponse,
)
from app.services.notification_service import NotificationDispatcher, get_notification_service

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts & Emergency Notifications"]
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create or evaluate an emergency alert",
    description=(
        "Creates an emergency alert in the database and dispatches notifications. "
        "If evaluated from a thermal event, alerts are triggered when risk_priority is "
        "'High' or 'Critical'. Low and Moderate priority events do not breach the emergency "
        "threshold and return a 200 response with status 'threshold_not_met'."
    )
)
def create_or_evaluate_alert(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_service),
):
    """
    Handle alert creation or threshold evaluation.
    """
    risk_priority = payload.get("risk_priority") or payload.get("severity")
    if risk_priority:
        priority_norm = str(risk_priority).strip().capitalize()
        # Threshold Check: ONLY High or Critical events trigger alerts
        if priority_norm not in ["High", "Critical"]:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "alert_created": False,
                    "status": "threshold_not_met",
                    "message": (
                        f"Thermal event risk priority '{risk_priority}' does not breach alert threshold. "
                        "Emergency alerts are only generated for 'High' or 'Critical' risks."
                    ),
                    "alert": None
                }
            )

    # If it has required fields for evaluation, run through dispatcher
    if "risk_score" in payload and "latitude" in payload and "longitude" in payload:
        eval_req = AlertEvaluationRequest(
            event_id=payload.get("event_id"),
            thermal_event_id=payload.get("thermal_event_id"),
            risk_priority=priority_norm if "priority_norm" in locals() else "High",
            risk_score=float(payload["risk_score"]),
            event_type=payload.get("event_type", "Thermal Anomaly"),
            latitude=float(payload["latitude"]),
            longitude=float(payload["longitude"]),
            thermal_intensity=payload.get("thermal_intensity"),
            facility_name=payload.get("facility_name"),
            custom_message=payload.get("message"),
        )
        alert = dispatcher.evaluate_and_create_alert(eval_req, db)
        if alert:
            return AlertResponse.model_validate(alert)

    # Standard direct alert creation
    title = payload.get("title") or f"EMERGENCY: {payload.get('severity', 'High').upper()} Priority Thermal Hazard"
    message = payload.get("message") or "Emergency thermal incident detected requiring immediate response."
    severity = (payload.get("severity") or payload.get("risk_priority") or "High").capitalize()

    alert_create = AlertCreate(
        user_id=payload.get("user_id"),
        thermal_event_id=payload.get("thermal_event_id"),
        event_id=payload.get("event_id"),
        title=title,
        message=message,
        severity=severity,
        risk_score=payload.get("risk_score"),
        risk_priority=payload.get("risk_priority") or severity,
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        event_type=payload.get("event_type"),
        is_read=payload.get("is_read", False),
    )
    alert = dispatcher.create_alert(alert_create, db)
    return AlertResponse.model_validate(alert)


@router.post(
    "/evaluate",
    summary="Evaluate thermal event for threshold-triggered alert generation",
    description="Specifically evaluates whether a thermal event triggers an alert (risk_priority = High or Critical)."
)
def evaluate_thermal_event_alert(
    request: AlertEvaluationRequest,
    db: Session = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_service),
):
    """
    Evaluates thermal event risk priority against alert thresholds.
    """
    alert = dispatcher.evaluate_and_create_alert(request, db)
    if alert:
        return {
            "alert_created": True,
            "status": "alert_dispatched",
            "message": f"Alert successfully created and dispatched for {alert.severity} event {alert.event_id}.",
            "alert": AlertResponse.model_validate(alert)
        }
    return {
        "alert_created": False,
        "status": "threshold_not_met",
        "message": f"Event priority '{request.risk_priority}' does not meet alert threshold (High/Critical).",
        "alert": None
    }


@router.get(
    "",
    response_model=AlertPaginatedResponse,
    status_code=status.HTTP_200_OK,
    summary="List all alerts with pagination and filters",
    description="Returns all stored alerts sorted from newest to oldest, with optional severity and read-status filtering."
)
def get_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    severity: Optional[str] = Query(None, description="Filter by severity: Critical, High, Moderate, Low"),
    is_read: Optional[bool] = Query(None, description="Filter by read status (true/false)"),
    db: Session = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_service),
) -> AlertPaginatedResponse:
    """
    List alerts with pagination and sorting.
    """
    items, total = dispatcher.get_alerts(
        db=db,
        page=page,
        page_size=page_size,
        severity=severity,
        is_read=is_read,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return AlertPaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[AlertResponse.model_validate(a) for a in items]
    )


@router.get(
    "/unread",
    response_model=AlertUnreadResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all unread emergency alerts",
    description="Returns list of currently unread alerts along with total unread count."
)
def get_unread_alerts(
    limit: int = Query(50, ge=1, le=200, description="Maximum unread alerts to fetch"),
    db: Session = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_service),
) -> AlertUnreadResponse:
    """
    Retrieve unread alerts for dashboard notification feeds.
    """
    items, unread_count = dispatcher.get_unread_alerts(db=db, limit=limit)
    return AlertUnreadResponse(
        unread_count=unread_count,
        items=[AlertResponse.model_validate(a) for a in items]
    )


@router.put(
    "/{alert_id}/read",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark an alert as read",
    description="Updates the alert's is_read property to true."
)
def mark_alert_as_read(
    alert_id: int,
    db: Session = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_service),
) -> AlertResponse:
    """
    Acknowledge/mark an emergency alert as read.
    """
    alert = dispatcher.mark_as_read(db=db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found."
        )
    return AlertResponse.model_validate(alert)


@router.put(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Acknowledge an emergency alert with operator attribution",
    description=(
        "Updates the alert with explicit operator acknowledgement timestamp, "
        "identifies the authenticated operator (or uses provided operator name), "
        "and sets both is_acknowledged and is_read to true."
    )
)
def acknowledge_alert_endpoint(
    alert_id: int,
    payload: Optional[AlertAcknowledgeRequest] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_service),
) -> AlertResponse:
    # 1. Verify alert exists in database
    existing_alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not existing_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found."
        )

    # 2. Prevent duplicate acknowledgement (Phase 36 Requirement)
    if existing_alert.is_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alert with id {alert_id} has already been acknowledged."
        )

    # 3. Extract operator identity from JWT Bearer token if present, or from payload
    operator_name = payload.operator_name if payload else None
    user_id = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        token_data = decode_access_token(token)
        if token_data and token_data.get("sub"):
            try:
                user_id = int(token_data["sub"])
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.full_name:
                    operator_name = user.full_name
            except Exception:
                pass

    if not operator_name:
        operator_name = "Command Center Operator"

    alert = dispatcher.acknowledge_alert(
        db=db,
        alert_id=alert_id,
        acknowledged_by=operator_name,
        acknowledged_by_user_id=user_id,
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found."
        )
    return AlertResponse.model_validate(alert)


@router.get(
    "/{alert_id}/delivery-status",
    response_model=list[NotificationDeliveryLogResponse],
    summary="Get notification delivery logs for an alert",
    description="Returns all audit delivery logs recorded for this emergency alert."
)
def get_alert_delivery_status(
    alert_id: int,
    db: Session = Depends(get_db),
) -> list[NotificationDeliveryLogResponse]:
    logs = (
        db.query(NotificationDeliveryLog)
        .filter(NotificationDeliveryLog.alert_id == alert_id)
        .order_by(NotificationDeliveryLog.created_at.desc())
        .all()
    )
    return [NotificationDeliveryLogResponse.model_validate(log) for log in logs]


@router.get(
    "/fcm/status",
    summary="Get Firebase Cloud Messaging push integration status",
    description="Returns current operational status (PASS or CONFIGURATION_REQUIRED) and active mode of FCM integration."
)
def get_fcm_status(
    dispatcher: NotificationDispatcher = Depends(get_notification_service),
) -> dict:
    return dispatcher.get_firebase_status()


@router.post(
    "/fcm/test",
    summary="Send test push notification via FCM / Web Push",
    description="Dispatches a test emergency push notification to verify push delivery pipeline."
)
def send_fcm_test(
    payload: Optional[Dict[str, Any]] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_service),
) -> dict:
    title = (payload.get("title") if payload else None) or "TEST EMERGENCY ALERT: Thermal Anomaly"
    body = (payload.get("body") if payload else None) or "Test push dispatch from SIH26162 ThermoSafe AI Emergency System."
    team_id = payload.get("team_id") if payload else None

    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        token_data = decode_access_token(token)
        if token_data and token_data.get("sub"):
            try:
                user_id = int(token_data["sub"])
            except Exception:
                pass

    return dispatcher.send_test_notification(
        title=title,
        body=body,
        db=db,
        user_id=user_id,
        team_id=team_id
    )


@router.post(
    "/{alert_id}/escalate",
    summary="Trigger phone escalation for unacknowledged high/critical alert",
    description="Implements acknowledgement-based escalation: stops if acknowledged; calls configured Operator Team via mock telephony if unacknowledged."
)
def escalate_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
) -> dict:
    from app.services.operator_routing_service import OperatorRoutingService
    from app.models.operator_team import EmergencyResponseTeam

    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found."
        )

    # 1. If alert is already acknowledged, stop escalation immediately
    if alert.is_acknowledged:
        return {
            "alert_id": alert.id,
            "status": "STOPPED",
            "escalation_stopped": True,
            "reason": "Alert was already acknowledged by operator. Phone escalation stopped.",
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        }

    # 2. Check risk priority
    sev = (alert.severity or alert.risk_priority or "LOW").strip().upper()
    if sev not in ["HIGH", "CRITICAL"]:
        return {
            "alert_id": alert.id,
            "status": "NOT_REQUIRED",
            "escalation_stopped": True,
            "reason": f"Alert severity '{sev}' does not meet High/Critical threshold for phone escalation.",
        }

    # 3. Locate responsible operator team
    team = None
    if alert.assigned_team_id:
        team = db.query(EmergencyResponseTeam).filter(EmergencyResponseTeam.id == alert.assigned_team_id).first()

    if not team and alert.latitude and alert.longitude:
        routing = OperatorRoutingService.find_nearest_responsible_team(alert, db)
        team = routing.get("team")
        if team and not alert.assigned_team_id:
            alert.assigned_team_id = team.id
            db.commit()

    if not team:
        # Fallback to any active operator team
        team = db.query(EmergencyResponseTeam).filter(EmergencyResponseTeam.is_active == True).first()

    if not team:
        return {
            "alert_id": alert.id,
            "status": "NO_TEAM_CONFIGURED",
            "reason": "No active Operator Team configured in the system.",
        }

    # 4. Check if team has call escalation enabled
    if not getattr(team, "call_escalation_enabled", True):
        return {
            "alert_id": alert.id,
            "status": "ESCALATION_DISABLED_FOR_TEAM",
            "team_id": team.id,
            "team_name": team.effective_team_name,
            "reason": f"Call escalation is disabled for team '{team.effective_team_name}'.",
        }

    # 5. Execute telephony dispatch (Safe DEMO/MOCK telephony when real provider not configured)
    official_phone = team.effective_phone or "+91-288-2234-911"
    telephony_provider = os.environ.get("TELEPHONY_PROVIDER", "mock").lower()

    simulated_message = (
        f"[SIMULATED VOICE CALL - NOT A REAL CALL] Emergency escalation for Alert #{alert.id} "
        f"({alert.title}). Dialing configured Operator Team '{team.effective_team_name}' at {official_phone}."
    )

    # Log to notification delivery audit trail
    log = NotificationDeliveryLog(
        alert_id=alert.id,
        event_id=alert.event_id,
        team_id=team.id,
        channel="phone_escalation",
        status="SIMULATED_VOICE_CALL" if telephony_provider == "mock" else "SENT",
        title=f"Phone Call Escalation: {alert.title}",
        body=simulated_message,
        provider_response="Simulated telephony engine (No actual telecom charges or real calls triggered).",
    )
    db.add(log)
    db.commit()

    return {
        "alert_id": alert.id,
        "status": "ESCALATED",
        "escalation_level": "LEVEL_1_OPERATOR_CALL",
        "team_id": team.id,
        "team_name": team.effective_team_name,
        "facility_id": team.facility_id,
        "target_phone": official_phone,
        "telephony_mode": "SIMULATED_MOCK_TELEPHONY",
        "message": simulated_message,
        "audit_log_id": log.id,
    }

