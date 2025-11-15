"""Notification schemas."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """Base notification schema."""

    type: str = Field(..., description="Notification type: reminder, report, alert")
    payload: Optional[Dict[str, Any]] = None
    scheduled_at: datetime


class NotificationCreate(NotificationBase):
    """Notification creation schema."""

    habit_id: Optional[int] = None


class NotificationResponse(NotificationBase):
    """Notification response schema."""

    id: int
    user_id: int
    habit_id: Optional[int]
    sent_at: Optional[datetime]
    status: str = Field(..., description="Status: pending, sent, failed, dismissed")
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Notification list response."""

    notifications: List[NotificationResponse]
    total: int


class NotificationUpdate(BaseModel):
    """Notification update schema."""

    status: Optional[str] = Field(None, pattern="^(pending|sent|failed|dismissed)$")

