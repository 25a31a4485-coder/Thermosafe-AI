from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AIClassification(Base):
    """
    AI Classification model storing machine learning model predictions and classifications.
    """
    __tablename__ = "ai_classifications"

    id = Column(Integer, primary_key=True, index=True)
    thermal_event_id = Column(
        Integer,
        ForeignKey("thermal_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    classification = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    explanation = Column(Text, nullable=True)
    model_name = Column(String(100), default="ThermalWatch-AI-v1", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    thermal_event = relationship("ThermalEvent", back_populates="classifications")

    def __repr__(self) -> str:
        return f"<AIClassification id={self.id} event_id={self.thermal_event_id} class={self.classification}>"
