from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserDevice(Base):
    """
    User Device model representing browser / mobile push notification endpoints.
    Allows sending targeted alerts to authenticated users and operational teams.
    """
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    operator_team_id = Column(
        Integer,
        ForeignKey("emergency_response_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    device_identifier = Column(String(255), nullable=False, index=True)
    push_token = Column(Text, nullable=True)
    platform = Column(String(50), default="web", nullable=False)  # web, android, ios
    browser = Column(String(100), nullable=True)  # Chrome, Edge, Firefox, Safari
    notification_permission = Column(String(50), default="default", nullable=False)  # granted, denied, default
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="devices")
    operator_team = relationship("EmergencyResponseTeam", back_populates="devices")

    __table_args__ = (
        Index("ix_devices_user_identifier", "user_id", "device_identifier"),
    )

    def __repr__(self) -> str:
        return f"<UserDevice id={self.id} user_id={self.user_id} platform={self.platform} active={self.is_active}>"
