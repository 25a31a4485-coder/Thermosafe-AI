from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alert(Base):
    """
    Alert model representing emergency notifications dispatched for high-priority thermal events.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    thermal_event_id = Column(
        Integer,
        ForeignKey("thermal_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    assigned_team_id = Column(
        Integer,
        ForeignKey("emergency_response_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    event_id = Column(String(100), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)  # Critical, High, Moderate, Low
    risk_score = Column(Float, nullable=True)
    risk_priority = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    event_type = Column(String(100), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False, index=True)  # ACTIVE, ACKNOWLEDGED, RESOLVED
    delivery_status = Column(String(50), default="SENT", nullable=False, index=True)  # PENDING, SENT, DELIVERED, FAILED, NO_NEARBY_TEAM, CONFIGURATION_REQUIRED
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="alerts", foreign_keys=[user_id])
    thermal_event = relationship("ThermalEvent", back_populates="alerts")
    assigned_team = relationship("EmergencyResponseTeam", foreign_keys=[assigned_team_id])
    delivery_logs = relationship("NotificationDeliveryLog", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Alert id={self.id} event_id={self.event_id or self.thermal_event_id} severity={self.severity} status={self.status} is_acknowledged={self.is_acknowledged}>"


class NotificationDeliveryLog(Base):
    """
    Audit log tracking lifecycle and delivery status of multi-channel emergency notifications.
    Tracks: PENDING, SENT, DELIVERED, FAILED, NO_NEARBY_TEAM, CONFIGURATION_REQUIRED.
    """
    __tablename__ = "notification_delivery_logs"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(
        Integer,
        ForeignKey("alerts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    event_id = Column(String(100), nullable=True, index=True)
    team_id = Column(
        Integer,
        ForeignKey("emergency_response_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    notification_type = Column(String(50), default="THERMAL_ALERT", nullable=False)
    risk_priority = Column(String(50), nullable=True)
    dedup_key = Column(String(255), nullable=True, index=True)
    channel = Column(String(50), default="fcm_push", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, SENT, DELIVERED, FAILED, NO_NEARBY_TEAM, CONFIGURATION_REQUIRED
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    provider_response = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    alert = relationship("Alert", back_populates="delivery_logs")
    team = relationship("EmergencyResponseTeam")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<NotificationDeliveryLog id={self.id} event_id={self.event_id} status={self.status} channel={self.channel}>"
