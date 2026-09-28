import enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(Base):
    """
    User model representing platform users (admin, operator, analyst, viewer).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.ANALYST,
        nullable=False
    )
    operator_team_id = Column(
        Integer,
        ForeignKey("emergency_response_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan", foreign_keys="[Alert.user_id]")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    operator_team = relationship("EmergencyResponseTeam", back_populates="members", foreign_keys=[operator_team_id])
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")

    @property
    def operator_team_name(self) -> Optional[str]:
        if self.operator_team:
            return self.operator_team.team_name or self.operator_team.name
        return None

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"

