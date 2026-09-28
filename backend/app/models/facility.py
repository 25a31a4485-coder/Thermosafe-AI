from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, func, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class IndustrialFacility(Base):
    """
    Industrial Facility model representing monitored industrial sites.
    """
    __tablename__ = "industrial_facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    industry_type = Column(String(100), nullable=False)
    operator = Column(String(255), nullable=True)
    risk_level = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    thermal_events = relationship("ThermalEvent", back_populates="facility")

    __table_args__ = (
        Index("ix_facilities_coords", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<IndustrialFacility id={self.id} name={self.name} type={self.industry_type}>"
