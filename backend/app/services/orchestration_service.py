"""
Central Event & Emergency Notification Orchestration Service for SIH26162.
Phases 38, 39, and 40:
- Automatic Risk -> Alert Pipeline
- Smart Notification Content (Dynamic Incident URLs & Formats)
- Central Notification Orchestration (Deduplication, Cooldown, Delivery Tracking)
"""

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.thermal_event import ThermalEvent
from app.models.facility import IndustrialFacility
from app.models.alert import Alert, NotificationDeliveryLog
from app.models.ai_classification import AIClassification
from app.models.risk_assessment import RiskAssessment
from app.models.operator_team import EmergencyDispatchLog
from app.schemas.ai_classification import AIClassifyRequest
from app.schemas.risk_assessment import RiskAnalysisRequest
from app.services.ai_service import get_classifier
from app.services.risk_service import get_risk_engine
from app.services.operator_routing_service import find_nearest_responsible_team
from app.services.notification_service import get_notification_service

logger = logging.getLogger("orchestration_service")

# Cooldown window to prevent spamming notifications for identical events/teams
NOTIFICATION_COOLDOWN_MINUTES = 15


def _extract(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to extract attributes across ORM models, Pydantic schemas, and dicts."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, key):
        val = getattr(obj, key)
        return val if val is not None else default
    return default


def build_smart_notification_content(
    classification: str,
    risk_priority: str,
    risk_score: float,
    event_type: str,
    confidence: float,
    location_str: str,
    event_id: str,
    latitude: float,
    longitude: float
) -> Dict[str, Any]:
    """
    Builds professional smart notification titles and bodies according to Phase 39 specification.
    Includes standardized 10-field payload with dynamic incident URL.
    """
    classif_lower = (classification or "").lower()
    priority_upper = (risk_priority or "LOW").upper()

    # Dynamic Incident URL linking directly to Live Map centered on the exact marker
    incident_url = f"/?event={event_id}&view=map"

    # Phase 39 Content Templates
    if priority_upper == "CRITICAL" or "critical" in classif_lower:
        title = "CRITICAL INDUSTRIAL FIRE DETECTED"
        body = (
            f"Risk Score: {risk_score:.0f}/100. Location: {location_str}. "
            f"Event Type: {event_type}. AI Confidence: {confidence:.0f}%. "
            f"Immediate Response Required."
        )
    elif "gas flare" in classif_lower:
        title = "GAS FLARE DETECTED"
        body = (
            f"Operational gas flare thermal signature identified. Monitored industrial stack. "
            f"Risk Score: {risk_score:.0f}/100. Location: {location_str}."
        )
    elif "persistent" in classif_lower:
        title = "PERSISTENT THERMAL SOURCE"
        body = (
            f"Persistent thermal source detected. Continuous operational heat emissions. "
            f"Risk Score: {risk_score:.0f}/100. Location: {location_str}."
        )
    elif priority_upper == "HIGH":
        title = "HIGH-RISK THERMAL EVENT"
        body = (
            f"High-risk thermal activity detected near an industrial facility. "
            f"Risk Score: {risk_score:.0f}/100. Location: {location_str}."
        )
    elif priority_upper == "MODERATE" or priority_upper == "MEDIUM":
        title = "MODERATE THERMAL ANOMALY"
        body = (
            f"Moderate heat signature detected near industrial sector. "
            f"Risk Score: {risk_score:.0f}/100. Location: {location_str}."
        )
    else:
        title = "THERMAL MONITORING EVENT"
        body = f"Thermal observation logged. Risk Score: {risk_score:.0f}/100. Location: {location_str}."

    payload = {
        "event_id": str(event_id),
        "event_type": str(event_type),
        "risk_priority": str(priority_upper),
        "risk_score": f"{risk_score:.1f}",
        "latitude": f"{latitude:.4f}",
        "longitude": f"{longitude:.4f}",
        "incident_url": incident_url,
        "classification": str(classification),
        "confidence": f"{confidence:.1f}",
        "title": title,
        "body": body,
    }

    return {
        "title": title,
        "body": body,
        "payload": payload,
        "incident_url": incident_url
    }


def is_duplicate_notification(
    db: Session,
    dedup_key: str,
    cooldown_minutes: int = NOTIFICATION_COOLDOWN_MINUTES
) -> bool:
    """
    Checks if a notification with this deterministic key was dispatched within the cooldown window.
    Deterministic Key: event_id + operator_team_id + risk_priority + notification_type
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
    recent = (
        db.query(NotificationDeliveryLog)
        .filter(
            NotificationDeliveryLog.dedup_key == dedup_key,
            NotificationDeliveryLog.created_at >= cutoff,
            NotificationDeliveryLog.status.in_(["SENT", "DELIVERED", "CONFIGURATION_REQUIRED"])
        )
        .first()
    )
    return recent is not None


def process_thermal_event(
    event: Union[ThermalEvent, Dict[str, Any]],
    db: Session,
    force_alert: bool = False,
    client_notif_preference: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Central orchestration function for the complete end-to-end event processing lifecycle:
    1. Thermal Event Normalization / Lookup
    2. AI Classification
    3. Multi-Factor Risk Assessment
    4. Nearest Operator Team Routing (Phase 37)
    5. Smart Alert Creation (Phase 38)
    6. Smart Notification Content Generation (Phase 39)
    7. Deduplication & Cooldown Protection (Phase 40)
    8. Push Notification Dispatch & Delivery Logging (Phase 40)

    Guarantees non-blocking execution: missing Firebase credentials or network failures
    safely log CONFIGURATION_REQUIRED or FAILED without interrupting the event lifecycle.
    """
    logger.info("process_thermal_event: Commencing automated thermal intelligence pipeline.")

    # -------------------------------------------------------------------------
    # 1. Thermal Event Normalization & Persistence
    # -------------------------------------------------------------------------
    thermal_event = None
    if isinstance(event, ThermalEvent):
        thermal_event = event
    elif isinstance(event, dict) and event.get("id"):
        thermal_event = db.query(ThermalEvent).filter(ThermalEvent.id == event["id"]).first()

    event_id = _extract(event, "event_id")
    if not event_id:
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        event_id = f"EVT-{today_str}-{uuid.uuid4().hex[:6].upper()}"

    lat = float(_extract(event, "latitude", 22.3039))
    lon = float(_extract(event, "longitude", 70.8022))
    raw_intensity = str(_extract(event, "thermal_intensity", "High (850 MW)"))
    raw_persistence = str(_extract(event, "persistence", "Continuous (24+ hours)"))
    facility_id = _extract(event, "facility_id")

    # Resolve facility context
    facility = None
    if facility_id:
        facility = db.query(IndustrialFacility).filter(IndustrialFacility.id == facility_id).first()

    facility_name = facility.name if facility else _extract(event, "facility_name")
    location_str = (facility.address or facility.name) if facility else f"{lat:.2f}° N, {lon:.2f}° E"

    # If thermal_event doesn't exist in DB, create it
    if not thermal_event:
        existing_evt = db.query(ThermalEvent).filter(ThermalEvent.event_id == event_id).first()
        if existing_evt:
            thermal_event = existing_evt
        else:
            thermal_event = ThermalEvent(
                event_id=event_id,
                latitude=lat,
                longitude=lon,
                detected_at=_extract(event, "detected_at", datetime.now(timezone.utc)),
                event_type=_extract(event, "event_type", "Industrial Fire"),
                thermal_intensity=raw_intensity,
                persistence=raw_persistence,
                facility_id=facility_id,
                land_cover=_extract(event, "land_cover", "Industrial"),
                data_source=_extract(event, "data_source", "NASA FIRMS Telemetry"),
                status=_extract(event, "status", "active"),
                is_demo=_extract(event, "is_demo", False),
            )
            db.add(thermal_event)
            db.commit()
            db.refresh(thermal_event)

    # -------------------------------------------------------------------------
    # 2. AI Classification
    # -------------------------------------------------------------------------
    ai_classifier = get_classifier()
    ai_req = AIClassifyRequest(
        latitude=lat,
        longitude=lon,
        thermal_intensity=thermal_event.thermal_intensity or raw_intensity,
        persistence=thermal_event.persistence or raw_persistence,
        nearby_industrial_facility=facility_name,
        land_cover=thermal_event.land_cover or "Industrial",
        historical_occurrences=3
    )
    ai_res = ai_classifier.classify(ai_req)
    classification = ai_res.classification
    confidence = ai_res.confidence * 100.0 if ai_res.confidence <= 1.0 else ai_res.confidence
    ai_explanation = ai_res.explanation

    # Persist or update AI classification record
    existing_classif = db.query(AIClassification).filter(AIClassification.thermal_event_id == thermal_event.id).first()
    if not existing_classif:
        ai_record = AIClassification(
            thermal_event_id=thermal_event.id,
            classification=classification,
            confidence=confidence,
            explanation=ai_explanation,
            model_name=getattr(ai_classifier, "MODEL_NAME", "ThermalSafe-RuleEngine-Prototype-v1")
        )
        db.add(ai_record)
        db.commit()

    # -------------------------------------------------------------------------
    # 3. Multi-Factor Risk Assessment
    # -------------------------------------------------------------------------
    risk_engine = get_risk_engine()
    risk_req = RiskAnalysisRequest(
        event_id=thermal_event.event_id,
        thermal_intensity=thermal_event.thermal_intensity or raw_intensity,
        persistence=thermal_event.persistence or raw_persistence,
        industrial_facility_proximity_km=0.1 if facility else 2.5,
        nearby_industrial_facility=facility_name,
        population_proximity_km=3.0,
        historical_recurrence=3,
        ai_classification=classification,
        event_type=thermal_event.event_type or "Industrial Fire",
        latitude=lat,
        longitude=lon
    )
    if thermal_event.risk_score is not None and thermal_event.risk_score > 0 and thermal_event.risk_priority:
        risk_score = thermal_event.risk_score
        risk_priority = str(thermal_event.risk_priority).upper()
        risk_explanation = f"Retained designated risk assessment: {risk_score:.1f} ({risk_priority})"
        risk_res = risk_engine.evaluate_risk(risk_req)
    else:
        risk_res = risk_engine.evaluate_risk(risk_req)
        risk_score = risk_res.risk_score
        risk_priority = risk_res.risk_priority.upper()
        risk_explanation = risk_res.explanation
        thermal_event.risk_score = risk_score
        thermal_event.risk_priority = risk_priority

    thermal_event.confidence = confidence
    if not thermal_event.event_type:
        thermal_event.event_type = classification
    db.commit()
    db.refresh(thermal_event)

    # Persist RiskAssessment record
    existing_risk = db.query(RiskAssessment).filter(RiskAssessment.thermal_event_id == thermal_event.id).first()
    if not existing_risk:
        risk_record = RiskAssessment(
            thermal_event_id=thermal_event.id,
            risk_score=risk_score,
            risk_priority=risk_priority,
            thermal_factor=risk_res.thermal_factor,
            persistence_factor=risk_res.persistence_factor,
            industrial_proximity_factor=risk_res.industrial_proximity_factor,
            population_proximity_factor=risk_res.population_proximity_factor,
            historical_factor=risk_res.historical_factor,
            explanation=risk_explanation,
            methodology=getattr(risk_engine, "METHODOLOGY_TAG", "ThermalSafe Prototype Risk Index v1.0")
        )
        db.add(risk_record)
        db.commit()

    # -------------------------------------------------------------------------
    # 4. Nearest Responsible Operator Team Routing (Phase 37)
    # -------------------------------------------------------------------------
    team_routing = find_nearest_responsible_team(thermal_event, db=db)
    assigned_team_id = team_routing.get("team_id")
    assigned_team_name = team_routing.get("team_name", "No Nearby Response Team")
    team_distance_km = team_routing.get("distance_km")
    team_notification_enabled = team_routing.get("notification_enabled", False)

    # -------------------------------------------------------------------------
    # 5. Smart Alert Creation Decision (Phase 38 Policy)
    # -------------------------------------------------------------------------
    # Policy:
    # CRITICAL -> Immediate Alert + Immediate Notification
    # HIGH     -> Immediate Alert + Immediate Notification
    # MODERATE -> Dashboard Alert created; Push dispatched if client/team allows
    # LOW      -> Dashboard/Database record only
    should_create_alert = force_alert or risk_priority in ["CRITICAL", "HIGH", "MODERATE", "MEDIUM"]
    should_dispatch_push = force_alert or risk_priority in ["CRITICAL", "HIGH"]
    if risk_priority in ["MODERATE", "MEDIUM"] and (client_notif_preference or team_notification_enabled):
        should_dispatch_push = True

    alert = None
    smart_content = build_smart_notification_content(
        classification=classification,
        risk_priority=risk_priority,
        risk_score=risk_score,
        event_type=thermal_event.event_type or classification,
        confidence=confidence,
        location_str=location_str,
        event_id=thermal_event.event_id,
        latitude=lat,
        longitude=lon
    )

    if should_create_alert:
        # Check for existing alert for this thermal event
        existing_alert = db.query(Alert).filter(Alert.thermal_event_id == thermal_event.id).first()
        if existing_alert:
            alert = existing_alert
            alert.assigned_team_id = assigned_team_id
            alert.risk_score = risk_score
            alert.risk_priority = risk_priority
            alert.severity = risk_priority.capitalize()
            db.commit()
            db.refresh(alert)
        else:
            alert = Alert(
                thermal_event_id=thermal_event.id,
                event_id=thermal_event.event_id,
                assigned_team_id=assigned_team_id,
                title=smart_content["title"],
                message=smart_content["body"],
                severity=risk_priority.capitalize(),
                risk_score=risk_score,
                risk_priority=risk_priority,
                latitude=lat,
                longitude=lon,
                event_type=classification,
                status="ACTIVE",
                delivery_status="PENDING",
                is_read=False,
                is_acknowledged=False,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)

    # -------------------------------------------------------------------------
    # 6. Duplicate Protection & Notification Dispatch (Phases 39 & 40)
    # -------------------------------------------------------------------------
    delivery_status = "SKIPPED_POLICY"
    failure_reason = None
    fcm_response = None

    if alert and should_dispatch_push:
        dedup_team = str(assigned_team_id or "NOTEAM")
        dedup_key = f"{thermal_event.event_id}:{dedup_team}:{risk_priority}:THERMAL_ALERT"

        if is_duplicate_notification(db, dedup_key):
            logger.info(f"Duplicate notification prevented for key '{dedup_key}' within cooldown window.")
            delivery_status = "SUPPRESSED_DUPLICATE"
        else:
            notif_service = get_notification_service()
            extra_data = smart_content["payload"]

            if not assigned_team_id:
                delivery_status = "NO_NEARBY_TEAM"
                logger.info(f"Alert ID {alert.id} generated with NO_NEARBY_TEAM.")
            else:
                try:
                    # Attempt dispatch to assigned team
                    fcm_res = notif_service.send_to_team(
                        team_id=assigned_team_id,
                        title=smart_content["title"],
                        body=smart_content["body"],
                        db=db,
                        alert=alert,
                        data=extra_data
                    )
                    fcm_response = json.dumps(fcm_res)
                    status_raw = fcm_res.get("status", "")
                    if status_raw == "success":
                        delivery_status = "DELIVERED" if fcm_res.get("dispatched_count", 0) > 0 else "SENT"
                    elif status_raw == "CONFIGURATION_REQUIRED":
                        delivery_status = "CONFIGURATION_REQUIRED"
                    elif status_raw in ["no_recipients", "simulated"]:
                        delivery_status = "CONFIGURATION_REQUIRED" if not notif_service.is_active else "SENT"
                    else:
                        delivery_status = "FAILED"
                        failure_reason = fcm_res.get("error") or fcm_res.get("message")
                except Exception as dispatch_err:
                    logger.error(f"Push dispatch error for alert {alert.id}: {dispatch_err}")
                    delivery_status = "FAILED"
                    failure_reason = str(dispatch_err)

            # Record in notification_delivery_logs
            delivery_log = NotificationDeliveryLog(
                alert_id=alert.id,
                event_id=thermal_event.event_id,
                team_id=assigned_team_id,
                notification_type="THERMAL_ALERT",
                risk_priority=risk_priority,
                dedup_key=dedup_key,
                channel="fcm_push",
                status=delivery_status,
                title=smart_content["title"],
                body=smart_content["body"],
                payload_json=json.dumps(extra_data),
                provider_response=fcm_response,
                failure_reason=failure_reason,
                sent_at=datetime.now(timezone.utc) if delivery_status in ["SENT", "DELIVERED", "CONFIGURATION_REQUIRED"] else None
            )
            db.add(delivery_log)

            # Update alert delivery status
            alert.delivery_status = delivery_status
            db.commit()
            db.refresh(alert)

            # Also create EmergencyDispatchLog if team was assigned
            if assigned_team_id:
                try:
                    disp_log = EmergencyDispatchLog(
                        team_id=assigned_team_id,
                        thermal_event_id=thermal_event.id,
                        alert_id=alert.id,
                        event_id=thermal_event.event_id,
                        distance_km=team_distance_km or 0.0,
                        risk_priority=risk_priority,
                        risk_score=risk_score,
                        dispatch_channel="FCM_EMERGENCY_PUSH",
                        status="DISPATCHED",
                        message=smart_content["body"]
                    )
                    db.add(disp_log)
                    db.commit()
                except Exception as d_err:
                    logger.warning(f"Could not write EmergencyDispatchLog: {d_err}")

    logger.info(
        f"process_thermal_event: Completed for {thermal_event.event_id}. "
        f"Classification='{classification}', Risk={risk_score:.0f} ({risk_priority}), "
        f"Team='{assigned_team_name}', Alert={alert.id if alert else None}, Delivery={delivery_status}."
    )

    return {
        "status": "success",
        "event_id": thermal_event.event_id,
        "thermal_event_id": thermal_event.id,
        "classification": classification,
        "confidence": confidence,
        "risk_score": risk_score,
        "risk_priority": risk_priority,
        "factors": {
            "thermal": risk_res.thermal_factor,
            "persistence": risk_res.persistence_factor,
            "industrial_proximity": risk_res.industrial_proximity_factor,
            "population_proximity": risk_res.population_proximity_factor,
            "historical": risk_res.historical_factor
        },
        "assigned_team": {
            "team_id": assigned_team_id,
            "team_name": assigned_team_name,
            "distance_km": team_distance_km,
            "notification_enabled": team_notification_enabled
        },
        "alert": {
            "id": alert.id,
            "title": alert.title,
            "severity": alert.severity,
            "status": alert.status,
            "delivery_status": alert.delivery_status,
            "incident_url": smart_content["incident_url"]
        } if alert else None,
        "delivery_status": delivery_status
    }
