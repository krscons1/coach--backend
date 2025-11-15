"""Habit schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator


class HabitBase(BaseModel):
    """Base habit schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: str = Field(..., pattern="^(binary|numeric)$")
    target_value: Optional[float] = Field(None, gt=0)
    schedule: Dict[str, Any] = Field(..., description="Schedule configuration as JSON")
    reminder_times: Optional[List[str]] = Field(None, description="List of reminder times (HH:MM)")
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schedule structure."""
        if not isinstance(v, dict):
            raise ValueError("Schedule must be a JSON object")
        if "days" not in v and "frequency" not in v:
            raise ValueError("Schedule must contain 'days' or 'frequency'")
        return v

    @field_validator("reminder_times")
    @classmethod
    def validate_reminder_times(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate reminder times format."""
        if v is None:
            return v
        for time_str in v:
            try:
                hour, minute = time_str.split(":")
                int(hour)
                int(minute)
                if not (0 <= int(hour) < 24 and 0 <= int(minute) < 60):
                    raise ValueError
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM")
        return v


class HabitCreate(HabitBase):
    """Habit creation schema."""

    pass


class HabitUpdate(BaseModel):
    """Habit update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_value: Optional[float] = Field(None, gt=0)
    schedule: Optional[Dict[str, Any]] = None
    reminder_times: Optional[List[str]] = None
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    active: Optional[bool] = None


class HabitResponse(HabitBase):
    """Habit response schema."""

    id: int
    user_id: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class HabitListResponse(BaseModel):
    """Habit list response with optional embeddings."""

    habits: List[HabitResponse]
    total: int

