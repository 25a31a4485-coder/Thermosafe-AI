from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class EmergencyResponseTeam(Base):
    """
    Emergency Response Team (Operator Team) model representing local industrial firefighting,
    hazmat, medical, or security operator teams assigned to or stationed near industrial hubs.
    """
    __tablename__ = "emergency_response_teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    team_name = Column(String(255), nullable=True, index=True)
    organization_name = Column(String(255), nullable=True)
    team_type = Column(String(100), default="Industrial Fire Brigade", nullable=False)  # Industrial Fire Brigade, Hazmat Response, Medical Emergency Squad, Disaster Unit
    industry_type = Column(String(100), nullable=True)
    facility_id = Column(
        Integer,
        ForeignKey("industrial_facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    contact_person = Column(String(255), nullable=True)
    contact_phone = Column(String(50), default="+91-288-2234-911", nullable=False)
    phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    radio_frequency = Column(String(50), nullable=True)  # e.g. "VHF 156.800 MHz (Ch 16)"
    coverage_radius_km = Column(Float, default=50.0, nullable=False)
    response_radius_km = Column(Float, nullable=True)
    notification_enabled = Column(Boolean, default=True, nullable=False)
    call_escalation_enabled = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    status = Column(String(50), default="available", nullable=False, index=True)  # available, dispatched, on_call, off_duty
    is_demo = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    facility = relationship("IndustrialFacility", backref="emergency_teams")
    members = relationship("User", back_populates="operator_team", foreign_keys="[User.operator_team_id]")
    devices = relationship("UserDevice", back_populates="operator_team")
    dispatch_logs = relationship("EmergencyDispatchLog", back_populates="team", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_operator_teams_coords", "latitude", "longitude"),
    )

    @property
    def effective_team_name(self) -> str:
        return self.team_name or self.name

    @property
    def effective_phone(self) -> str:
        return self.phone or self.contact_phone

    @property
    def effective_email(self) -> str:
        return self.email or self.contact_email or ""

    @property
    def effective_radius(self) -> float:
        return self.response_radius_km if self.response_radius_km is not None else self.coverage_radius_km

    @property
    def effective_industry(self) -> str:
        return self.industry_type or self.team_type

    @property
    def specialization(self) -> str:
        return self.team_type or "Industrial Fire Brigade"

    def __repr__(self) -> str:
        return f"<EmergencyResponseTeam id={self.id} name={self.effective_team_name} active={self.is_active}>"


# Semantic alias
OperatorTeam = EmergencyResponseTeam



class EmergencyDispatchLog(Base):
    """
    Audit log record of emergency notifications and tasking dispatched to operator teams.
    """
    __tablename__ = "emergency_dispatch_logs"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(
        Integer,
        ForeignKey("emergency_response_teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    thermal_event_id = Column(
        Integer,
        ForeignKey("thermal_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    alert_id = Column(
        Integer,
        ForeignKey("alerts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    event_id = Column(String(100), nullable=True, index=True)
    distance_km = Column(Float, nullable=False)
    risk_priority = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=True)
    dispatch_channel = Column(String(50), default="AUTOMATED_SMS", nullable=False)  # AUTOMATED_SMS, EMAIL_ALERT, RADIO_BROADCAST, DISPATCH_CONSOLE
    status = Column(String(50), default="DISPATCHED", nullable=False, index=True)  # DISPATCHED, ACKNOWLEDGED, EN_ROUTE, RESOLVED
    message = Column(Text, nullable=False)
    dispatched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    team = relationship("EmergencyResponseTeam", back_populates="dispatch_logs")
    thermal_event = relationship("ThermalEvent")
    alert = relationship("Alert")

    def __repr__(self) -> str:
        return f"<EmergencyDispatchLog id={self.id} team_id={self.team_id} event={self.event_id} status={self.status}>"
