from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class RiskAssessment(Base):
    """
    Risk Assessment model storing detailed multi-factor risk scores and factor weights.
    """
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    thermal_event_id = Column(
        Integer,
        ForeignKey("thermal_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    risk_score = Column(Float, nullable=False, index=True)
    risk_priority = Column(String(50), nullable=False, index=True)
    thermal_factor = Column(Float, nullable=True)
    persistence_factor = Column(Float, nullable=True)
    industrial_proximity_factor = Column(Float, nullable=True)
    population_proximity_factor = Column(Float, nullable=True)
    historical_factor = Column(Float, nullable=True)
    explanation = Column(Text, nullable=True)
    methodology = Column(String(200), nullable=True, default="ThermalSafe Prototype Risk Index v1.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    thermal_event = relationship("ThermalEvent", back_populates="risk_assessments")

    __table_args__ = (
        Index("ix_risk_assessment_score_priority", "risk_score", "risk_priority"),
    )

    def __repr__(self) -> str:
        return f"<RiskAssessment id={self.id} event_id={self.thermal_event_id} score={self.risk_score}>"
