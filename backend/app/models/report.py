from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Report(Base):
    """
    Report model storing generated incident and analytics reports.
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    report_type = Column(String(100), default="incident_report", nullable=False)
    title = Column(String(255), nullable=False)
    parameters = Column(JSON, nullable=True)
    summary = Column(JSON, nullable=True)
    content = Column(JSON, nullable=True)
    status = Column(String(50), default="completed", nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report id={self.id} title={self.title} type={self.report_type}>"
