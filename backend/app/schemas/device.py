from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    device_identifier: str = Field(..., min_length=1, max_length=255, description="Unique client device or browser fingerprint")
    push_token: Optional[str] = Field(None, description="FCM device push token or Web Push endpoint")
    platform: str = Field("web", max_length=50, description="Operating platform (web, android, ios)")
    browser: Optional[str] = Field(None, max_length=100, description="Client browser identifier")
    notification_permission: str = Field("default", max_length=50, description="Permission state: granted, denied, default")
    operator_team_id: Optional[int] = Field(None, description="Associated operator team ID")


class DeviceRegisterRequest(DeviceBase):
    pass


class DeviceUpdateRequest(BaseModel):
    push_token: Optional[str] = None
    notification_permission: Optional[str] = None
    operator_team_id: Optional[int] = None
    is_active: Optional[bool] = None


class DeviceResponse(DeviceBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime
    operator_team_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
