from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base


class ThermalEvent(Base):
    """
    Thermal Event model representing detected thermal anomalies and incidents.
    Mapped with SQLAlchemy 2.0 type descriptors for strict type-checking and mutability.
    """
    __tablename__ = "thermal_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    thermal_intensity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    persistence: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    risk_priority: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    facility_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("industrial_facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    land_cover: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    data_source: Mapped[str] = mapped_column(String(100), default="NASA FIRMS", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    facility = relationship("IndustrialFacility", back_populates="thermal_events")
    classifications = relationship("AIClassification", back_populates="thermal_event", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="thermal_event", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="thermal_event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_thermal_events_coords", "latitude", "longitude"),
        Index("ix_thermal_events_risk_score_priority", "risk_score", "risk_priority"),
    )

    def __repr__(self) -> str:
        return f"<ThermalEvent id={self.id} event_id={self.event_id} type={self.event_type} risk={self.risk_priority}>"
