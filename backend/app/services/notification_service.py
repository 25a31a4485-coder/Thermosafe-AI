"""
Notification and Emergency Alert Service for SIH26162.
Provides threshold-triggered alert generation for High and Critical thermal risks,
database-backed persistence, and an extensible architecture designed for future
multi-channel notification integrations (Firebase Cloud Messaging, Web Push, Email, SMS).
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.thermal_event import ThermalEvent
from app.schemas.alert import AlertCreate, AlertEvaluationRequest

logger = logging.getLogger("notification_service")


class BaseNotificationChannel(ABC):
    """
    Abstract interface for notification dispatch channels.
    Allows plug-and-play extensions for FCM, Web Push, Email, and SMS.
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Identifier name of the notification channel."""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """True if channel is fully configured with production credentials."""
        pass

    @abstractmethod
    def dispatch(self, alert: Alert) -> bool:
        """Dispatch the alert over this communication channel."""
        pass


class DatabaseNotificationChannel(BaseNotificationChannel):
    """
    Active primary notification channel.
    Stores and indexes alerts directly in the database for dashboard and API consumption.
    """

    @property
    def channel_name(self) -> str:
        return "database"

    @property
    def is_active(self) -> bool:
        return True

    def dispatch(self, alert: Alert) -> bool:
        logger.info(
            f"Alert [ID:{alert.id}] Severity={alert.severity} dispatched to Database Channel for Event={alert.event_id}"
        )
        return True


class FCMNotificationChannel(BaseNotificationChannel):
    """
    Firebase Cloud Messaging (FCM) integration for push notifications to browsers and mobile devices.
    If production Firebase credentials are provided, dispatches via Firebase Admin SDK.
    If credentials are not yet configured, safely reports CONFIGURATION_REQUIRED and runs in
    transparent simulated fallback mode without crashing or blocking the application.
    """

    def __init__(self):
        self._firebase_app = None
        self._is_initialized = False
        self._init_firebase()

    def _init_firebase(self) -> None:
        # 1. Check for raw Service Account JSON in environment
        raw_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if raw_json:
            try:
                import firebase_admin
                from firebase_admin import credentials

                cert_dict = json.loads(raw_json)
                cred = credentials.Certificate(cert_dict)
                if not firebase_admin._apps:
                    self._firebase_app = firebase_admin.initialize_app(cred)
                else:
                    self._firebase_app = firebase_admin.get_app()
                self._is_initialized = True
                logger.info("Firebase Admin SDK successfully initialized via FIREBASE_SERVICE_ACCOUNT_JSON.")
                return
            except (ImportError, Exception) as e:
                logger.warning(f"Could not initialize Firebase via FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
                self._is_initialized = False

        # 2. Check for credentials file path
        try:
            from app.core.config import settings

            cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None) or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        except Exception:
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if cred_path and os.path.exists(cred_path):
            try:
                import firebase_admin
                from firebase_admin import credentials

                if not firebase_admin._apps:
                    cred = credentials.Certificate(cred_path)
                    self._firebase_app = firebase_admin.initialize_app(cred)
                else:
                    self._firebase_app = firebase_admin.get_app()
                self._is_initialized = True
                logger.info("Firebase Admin SDK successfully initialized with provided service credentials.")
                return
            except (ImportError, Exception) as e:
                logger.warning(f"Firebase Admin SDK initialization warning: {e}. Running in simulated fallback mode.")
                self._is_initialized = False
        else:
            logger.info("Firebase credentials not configured. Notification engine status: CONFIGURATION_REQUIRED.")
            self._is_initialized = False

    @property
    def channel_name(self) -> str:
        return "fcm_mobile_push"

    @property
    def is_active(self) -> bool:
        return self._is_initialized

    @property
    def status_label(self) -> str:
        return "PASS" if self._is_initialized else "CONFIGURATION_REQUIRED"

    def format_payload(
        self,
        title: str,
        body: str,
        alert: Optional[Alert] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        Builds standardized notification payload compliant with Phase 32 requirements:
        title, body, severity, event_id, event_type, risk_priority, risk_score, latitude, longitude, incident_url.
        All payload values are stringified to satisfy Firebase FCM data message requirements.
        """
        extra = extra_data or {}
        event_id = str(alert.event_id if alert and alert.event_id else extra.get("event_id", "DEMO-EVT-001"))
        alert_id = str(alert.id if alert and alert.id else "")
        url_target = f"/?event={event_id}" if event_id else (f"/?alert={alert_id}" if alert_id else "/")

        payload: Dict[str, str] = {
            "title": str(title or "Emergency Thermal Alert"),
            "body": str(body or "High thermal signature detected."),
            "severity": str(alert.severity if alert and alert.severity else extra.get("severity", "High")),
            "event_id": event_id,
            "event_type": str(alert.event_type if alert and alert.event_type else extra.get("event_type", "Industrial Hazard")),
            "risk_priority": str(alert.risk_priority if alert and alert.risk_priority else extra.get("risk_priority", "High")),
            "risk_score": str(alert.risk_score if (alert and alert.risk_score is not None) else extra.get("risk_score", "78.5")),
            "latitude": str(alert.latitude if (alert and alert.latitude is not None) else extra.get("latitude", "22.3039")),
            "longitude": str(alert.longitude if (alert and alert.longitude is not None) else extra.get("longitude", "70.8022")),
            "incident_url": str(extra.get("incident_url") or url_target),
        }
        for k, v in extra.items():
            if k not in payload and v is not None:
                payload[k] = str(v)
        return payload

    def send_notification(
        self,
        title: str,
        body: str,
        tokens: Optional[List[str]] = None,
        alert: Optional[Alert] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches push notification to designated device tokens or to the global emergency topic.
        Runs safely in simulated fallback mode when Firebase credentials are not configured.
        """
        payload_data = self.format_payload(title, body, alert=alert, extra_data=data)

        if not self._is_initialized:
            logger.info(
                f"[FCM CONFIGURATION_REQUIRED] Simulated push notification: '{title}' "
                f"queued for {len(tokens) if tokens is not None else 'broadcast'} client endpoint(s)."
            )
            return {
                "status": "CONFIGURATION_REQUIRED",
                "mode": "simulated",
                "message": "Firebase credentials not configured. Simulated push notification dispatched.",
                "dispatched_count": len(tokens) if tokens is not None else 1,
                "payload": payload_data,
            }

        try:
            import firebase_admin
            from firebase_admin import messaging

            if tokens is not None and len(tokens) == 0:
                return {
                    "status": "success",
                    "mode": "live",
                    "message": "No active target tokens to dispatch.",
                    "dispatched_count": 0,
                    "payload": payload_data,
                }

            if tokens:
                # Chunk tokens into batches of 500 to adhere to FCM Multicast limit
                success_count = 0
                failure_count = 0
                batch_size = 500
                for i in range(0, len(tokens), batch_size):
                    batch = tokens[i : i + batch_size]
                    message = messaging.MulticastMessage(
                        notification=messaging.Notification(title=title, body=body),
                        data=payload_data,
                        tokens=batch,
                    )
                    if hasattr(messaging, "send_each_for_multicast"):
                        resp = messaging.send_each_for_multicast(message)
                    else:
                        resp = messaging.send_multicast(message)
                    success_count += resp.success_count
                    failure_count += resp.failure_count

                return {
                    "status": "success",
                    "mode": "live",
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "payload": payload_data,
                }
            else:
                topic = "thermal_emergency_broadcast"
                message = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data=payload_data,
                    topic=topic,
                )
                resp_id = messaging.send(message)
                return {
                    "status": "success",
                    "mode": "live",
                    "message_id": resp_id,
                    "payload": payload_data,
                }
        except (ImportError, Exception) as err:
            logger.error(f"FCM live dispatch error: {err}")
            return {
                "status": "error",
                "error": str(err),
                "payload": payload_data,
            }

    def dispatch(self, alert: Alert) -> bool:
        title = alert.title or "Emergency Thermal Alert"
        body = alert.message or "High thermal signature detected."
        res = self.send_notification(title, body, alert=alert)
        return res.get("status") in ["success", "CONFIGURATION_REQUIRED"]


class WebPushNotificationChannel(BaseNotificationChannel):
    """
    Extensible interface for browser Web Push notifications (VAPID).
    Currently inactive until VAPID public/private keypair is configured.
    """

    @property
    def channel_name(self) -> str:
        return "web_push"

    @property
    def is_active(self) -> bool:
        return False

    def dispatch(self, alert: Alert) -> bool:
        logger.info(
            f"Web Push channel simulated dispatch: Alert [ID:{alert.id}] queued for future browser push."
        )
        return False


class EmailNotificationChannel(BaseNotificationChannel):
    """
    Extensible interface for SMTP / transactional email alerting (e.g. SendGrid / AWS SES).
    Currently inactive until SMTP host or API key is configured.
    """

    @property
    def channel_name(self) -> str:
        return "email"

    @property
    def is_active(self) -> bool:
        return False

    def dispatch(self, alert: Alert) -> bool:
        logger.info(
            f"Email channel simulated dispatch: Alert [ID:{alert.id}] queued for emergency email dispatch."
        )
        return False


class SMSNotificationChannel(BaseNotificationChannel):
    """
    Extensible interface for SMS emergency broadcast (e.g. Twilio / AWS SNS / Telecom Gateway).
    Currently inactive until SMS gateway credentials are configured.
    """

    @property
    def channel_name(self) -> str:
        return "sms"

    @property
    def is_active(self) -> bool:
        return False

    def dispatch(self, alert: Alert) -> bool:
        logger.info(
            f"SMS channel simulated dispatch: Alert [ID:{alert.id}] queued for SMS dispatch."
        )
        return False


class NotificationDispatcher:
    """
    Emergency notification engine coordinating threshold evaluation,
    database persistence, and multi-channel dispatching.
    """

    def __init__(self):
        self.channels: Dict[str, BaseNotificationChannel] = {
            "database": DatabaseNotificationChannel(),
            "fcm": FCMNotificationChannel(),
            "web_push": WebPushNotificationChannel(),
            "email": EmailNotificationChannel(),
            "sms": SMSNotificationChannel(),
        }

    @property
    def is_active(self) -> bool:
        fcm = self.channels.get("fcm")
        return fcm.is_active if fcm else False

    def format_payload(
        self,
        title: str,
        body: str,
        alert: Optional[Alert] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Delegates payload construction to FCM channel or provides standard fallback."""
        fcm = self.channels.get("fcm")
        if isinstance(fcm, FCMNotificationChannel):
            return fcm.format_payload(title=title, body=body, alert=alert, extra_data=extra_data)

        extra = extra_data or {}
        event_id = str(alert.event_id if alert and alert.event_id else extra.get("event_id", "DEMO-EVT-001"))
        return {
            "title": str(title or "Emergency Thermal Alert"),
            "body": str(body or "High thermal signature detected."),
            "severity": str(alert.severity if alert and alert.severity else extra.get("severity", "High")),
            "event_id": event_id,
            "event_type": str(alert.event_type if alert and alert.event_type else extra.get("event_type", "Industrial Hazard")),
            "risk_priority": str(alert.risk_priority if alert and alert.risk_priority else extra.get("risk_priority", "High")),
            "risk_score": str(alert.risk_score if (alert and alert.risk_score is not None) else extra.get("risk_score", "78.5")),
            "latitude": str(alert.latitude if (alert and alert.latitude is not None) else extra.get("latitude", "22.3039")),
            "longitude": str(alert.longitude if (alert and alert.longitude is not None) else extra.get("longitude", "70.8022")),
            "incident_url": str(extra.get("incident_url") or (f"/?event={event_id}" if event_id else "/")),
        }

    def evaluate_and_create_alert(
        self,
        request: AlertEvaluationRequest,
        db: Session,
    ) -> Optional[Alert]:
        """
        Evaluate a thermal event's risk priority.
        Generates and stores an alert ONLY when risk_priority is 'High' or 'Critical'.
        Returns None for 'Low' or 'Moderate' events.
        """
        priority_norm = request.risk_priority.strip().capitalize()

        # Threshold Check: ONLY High or Critical events trigger alerts
        if priority_norm not in ["High", "Critical"]:
            logger.info(
                f"Thermal Event {request.event_id} with priority '{request.risk_priority}' "
                f"(score: {request.risk_score}) does not meet alert threshold (High/Critical). Skipped."
            )
            return None

        # Build dynamic title and message
        facility_str = f" at {request.facility_name}" if request.facility_name else ""
        title = f"EMERGENCY: {priority_norm.upper()} Thermal Hazard{facility_str}"

        intensity_str = f" Intensity: {request.thermal_intensity}." if request.thermal_intensity else ""
        default_message = (
            f"Anomalous heat signature designated as '{request.event_type}' detected{facility_str} "
            f"with risk score {request.risk_score:.1f}/100 ({priority_norm} Priority).{intensity_str} "
            f"Coordinates: ({request.latitude:.4f}, {request.longitude:.4f}). Immediate response required."
        )
        message = request.custom_message or default_message

        # Persist alert in database
        alert = Alert(
            thermal_event_id=request.thermal_event_id,
            event_id=request.event_id,
            title=title,
            message=message,
            severity=priority_norm,
            risk_score=request.risk_score,
            risk_priority=priority_norm,
            latitude=request.latitude,
            longitude=request.longitude,
            event_type=request.event_type,
            is_read=False,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Dispatch across registered channels
        for channel in self.channels.values():
            if channel.is_active:
                channel.dispatch(alert)

        # AI-Powered Nearby Operator Team Emergency Mobilization
        try:
            from app.services.operator_notification_service import OperatorNotificationService

            target_event = None
            if request.thermal_event_id:
                target_event = db.query(ThermalEvent).filter(ThermalEvent.id == request.thermal_event_id).first()
            elif request.event_id:
                target_event = db.query(ThermalEvent).filter(ThermalEvent.event_id == request.event_id).first()

            if not target_event:
                target_event = ThermalEvent(
                    id=request.thermal_event_id,
                    event_id=request.event_id or f"ALERT-EVT-{alert.id}",
                    latitude=request.latitude,
                    longitude=request.longitude,
                    detected_at=datetime.now(timezone.utc),
                    event_type=request.event_type,
                    thermal_intensity=request.thermal_intensity,
                    risk_score=request.risk_score,
                    risk_priority=priority_norm,
                    status="active",
                )

            dispatch_res = OperatorNotificationService.dispatch_emergency_team(
                db=db,
                thermal_event=target_event,
                alert=alert,
                force=True,
            )
            if dispatch_res:
                logger.info(
                    f"Auto-dispatched emergency operator team '{dispatch_res['team_name']}' "
                    f"for alert [ID:{alert.id}] ({dispatch_res['distance_km']} km away)."
                )
        except Exception as op_err:
            logger.warning(f"Could not auto-dispatch operator team for alert {alert.id}: {op_err}")

        logger.info(
            f"Generated {priority_norm} alert [ID:{alert.id}] for event {request.event_id} (Score: {request.risk_score})"
        )
        return alert

    def create_alert(self, alert_data: AlertCreate, db: Session) -> Alert:
        """
        Direct creation of an alert in the database with multi-channel dispatch.
        """
        alert = Alert(
            user_id=alert_data.user_id,
            thermal_event_id=alert_data.thermal_event_id,
            event_id=alert_data.event_id,
            title=alert_data.title,
            message=alert_data.message,
            severity=alert_data.severity.capitalize(),
            risk_score=alert_data.risk_score,
            risk_priority=alert_data.risk_priority,
            latitude=alert_data.latitude,
            longitude=alert_data.longitude,
            event_type=alert_data.event_type,
            is_read=alert_data.is_read,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        for channel in self.channels.values():
            if channel.is_active:
                channel.dispatch(alert)

        # Trigger operator team dispatch if High or Critical
        if alert.severity in ["High", "Critical"] and alert.latitude and alert.longitude:
            try:
                from app.services.operator_notification_service import OperatorNotificationService

                temp_event = None
                if alert.thermal_event_id:
                    temp_event = db.query(ThermalEvent).filter(ThermalEvent.id == alert.thermal_event_id).first()
                if not temp_event:
                    temp_event = ThermalEvent(
                        event_id=alert.event_id or f"ALERT-{alert.id}",
                        latitude=alert.latitude,
                        longitude=alert.longitude,
                        detected_at=alert.created_at or datetime.now(timezone.utc),
                        event_type=alert.event_type or "Thermal Anomaly",
                        risk_score=alert.risk_score or 75.0,
                        risk_priority=alert.severity,
                        status="active",
                    )
                OperatorNotificationService.dispatch_emergency_team(
                    db=db,
                    thermal_event=temp_event,
                    alert=alert,
                    force=True,
                )
            except Exception as op_err:
                logger.warning(f"Could not auto-dispatch operator team for direct alert {alert.id}: {op_err}")

        return alert

    def get_alerts(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        severity: Optional[str] = None,
        is_read: Optional[bool] = None,
    ) -> Tuple[List[Alert], int]:
        """Retrieve paginated alerts sorted from newest to oldest."""
        query = db.query(Alert)

        if severity:
            query = query.filter(Alert.severity.ilike(f"%{severity}%"))
        if is_read is not None:
            query = query.filter(Alert.is_read == is_read)

        total = query.count()
        items = (
            query.order_by(desc(Alert.created_at), desc(Alert.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_unread_alerts(self, db: Session, limit: int = 50) -> Tuple[List[Alert], int]:
        """Retrieve all unread alerts up to limit and return total unread count."""
        unread_count = db.query(func.count(Alert.id)).filter(Alert.is_read == False).scalar() or 0
        items = (
            db.query(Alert)
            .filter(Alert.is_read == False)
            .order_by(desc(Alert.created_at), desc(Alert.id))
            .limit(limit)
            .all()
        )
        return items, unread_count

    def mark_as_read(self, db: Session, alert_id: int) -> Optional[Alert]:
        """Mark a specific alert as read."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None

        alert.is_read = True
        db.commit()
        db.refresh(alert)
        logger.info(f"Alert [ID:{alert_id}] marked as read.")
        return alert

    def acknowledge_alert(
        self,
        db: Session,
        alert_id: int,
        acknowledged_by: Optional[str] = None,
        acknowledged_by_user_id: Optional[int] = None,
    ) -> Optional[Alert]:
        """Acknowledge an emergency alert and record operator details and timestamp."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None

        alert.is_read = True
        alert.is_acknowledged = True
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_at = datetime.now(timezone.utc)
        if acknowledged_by:
            alert.acknowledged_by = acknowledged_by
        elif not alert.acknowledged_by:
            alert.acknowledged_by = "Duty Watch Officer"
        if acknowledged_by_user_id:
            alert.acknowledged_by_user_id = acknowledged_by_user_id

        db.commit()
        db.refresh(alert)
        logger.info(f"Alert [ID:{alert_id}] acknowledged by {alert.acknowledged_by} at {alert.acknowledged_at}.")
        return alert

    def get_firebase_status(self) -> Dict[str, Any]:
        """Returns the current operational status of the FCM Push integration."""
        fcm_channel = self.channels.get("fcm")
        is_active = fcm_channel.is_active if isinstance(fcm_channel, FCMNotificationChannel) else False
        return {
            "status": "PASS" if is_active else "CONFIGURATION_REQUIRED",
            "is_active": is_active,
            "channel": "fcm_mobile_push",
            "mode": "live" if is_active else "simulated",
            "message": "Firebase Admin SDK active" if is_active else "Firebase credentials not configured. Running in safe simulated fallback mode.",
        }

    def send_notification(
        self,
        title: str,
        body: str,
        tokens: Optional[List[str]] = None,
        alert: Optional[Alert] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Direct push notification dispatch to specified device tokens or topic."""
        fcm_channel = self.channels.get("fcm")
        if isinstance(fcm_channel, FCMNotificationChannel):
            return fcm_channel.send_notification(title=title, body=body, tokens=tokens, alert=alert, data=data)
        return {
            "status": "CONFIGURATION_REQUIRED",
            "mode": "simulated",
            "message": "FCM channel not available.",
            "payload": self.format_payload(title, body, alert=alert, extra_data=data),
        }

    def send_to_user(
        self,
        user_id: int,
        title: str,
        body: str,
        db: Session,
        alert: Optional[Alert] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dispatches push notification to all active devices registered to a specific user."""
        from app.models.device import UserDevice

        devices = (
            db.query(UserDevice)
            .filter(
                UserDevice.user_id == user_id,
                UserDevice.is_active == True,
                UserDevice.push_token.isnot(None),
                UserDevice.push_token != "",
            )
            .all()
        )
        tokens = [d.push_token.strip() for d in devices if d.push_token and d.push_token.strip()]
        if not tokens:
            return {
                "status": "no_recipients" if self.is_active else "CONFIGURATION_REQUIRED",
                "mode": "live" if self.is_active else "simulated",
                "message": f"No active registered push tokens found for user ID {user_id}.",
                "dispatched_count": 0,
                "payload": self.format_payload(title, body, alert=alert, extra_data=data),
            }
        return self.send_notification(title=title, body=body, tokens=tokens, alert=alert, data=data)

    def send_to_team(
        self,
        team_id: int,
        title: str,
        body: str,
        db: Session,
        alert: Optional[Alert] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dispatches push notification to all registered devices belonging to an operator team."""
        from app.models.device import UserDevice
        from app.models.user import User

        team_users = db.query(User.id).filter(User.operator_team_id == team_id).all()
        user_ids = [u[0] for u in team_users]

        device_query = db.query(UserDevice).filter(
            UserDevice.is_active == True,
            UserDevice.push_token.isnot(None),
            UserDevice.push_token != "",
        )
        if user_ids:
            device_query = device_query.filter(
                (UserDevice.operator_team_id == team_id) | (UserDevice.user_id.in_(user_ids))
            )
        else:
            device_query = device_query.filter(UserDevice.operator_team_id == team_id)

        devices = device_query.all()
        tokens = [d.push_token.strip() for d in devices if d.push_token and d.push_token.strip()]
        if not tokens:
            return {
                "status": "no_recipients" if self.is_active else "CONFIGURATION_REQUIRED",
                "mode": "live" if self.is_active else "simulated",
                "message": f"No active registered push tokens found for operator team ID {team_id}.",
                "dispatched_count": 0,
                "payload": self.format_payload(title, body, alert=alert, extra_data=data),
            }
        return self.send_notification(title=title, body=body, tokens=tokens, alert=alert, data=data)

    def send_test_notification(
        self,
        title: str = "Test Emergency Notification",
        body: str = "ThermoSafe AI push notification system test.",
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Sends a test push notification to verify pipeline end-to-end."""
        test_data = {
            "severity": "High",
            "event_id": "TEST-NOTIF-001",
            "event_type": "Industrial Heat Flare",
            "risk_priority": "High",
            "risk_score": "84.2",
            "latitude": "22.3039",
            "longitude": "70.8022",
            "incident_url": "/#alerts",
        }
        if user_id and db:
            return self.send_to_user(user_id=user_id, title=title, body=body, db=db, data=test_data)
        elif team_id and db:
            return self.send_to_team(team_id=team_id, title=title, body=body, db=db, data=test_data)
        return self.send_notification(title=title, body=body, data=test_data)


_notification_service_instance: Optional[NotificationDispatcher] = None


def get_notification_service() -> NotificationDispatcher:
    """Singleton factory for notification service dependency injection."""
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = NotificationDispatcher()
    return _notification_service_instance


def get_firebase_status() -> Dict[str, Any]:
    """Module-level helper to query Firebase push integration status."""
    return get_notification_service().get_firebase_status()


def format_payload(*args, **kwargs) -> Dict[str, str]:
    """Module-level helper to build standard 10-field alert payload."""
    return get_notification_service().format_payload(*args, **kwargs)


def send_notification(*args, **kwargs) -> Dict[str, Any]:
    """Module-level helper to dispatch push notification."""
    return get_notification_service().send_notification(*args, **kwargs)


def send_to_user(*args, **kwargs) -> Dict[str, Any]:
    """Module-level helper to dispatch push notification to a specific user."""
    return get_notification_service().send_to_user(*args, **kwargs)


def send_to_team(*args, **kwargs) -> Dict[str, Any]:
    """Module-level helper to dispatch push notification to an operator team."""
    return get_notification_service().send_to_team(*args, **kwargs)


def send_test_notification(*args, **kwargs) -> Dict[str, Any]:
    """Module-level helper to dispatch a test emergency notification."""
    return get_notification_service().send_test_notification(*args, **kwargs)
