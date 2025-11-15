"""Habit entry schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class HabitEntryBase(BaseModel):
    """Base habit entry schema."""

    date: date
    completed: bool = False
    value: Optional[float] = Field(None, ge=0)
    note: Optional[str] = Field(None, max_length=1000)


class HabitEntryCreate(HabitEntryBase):
    """Habit entry creation schema."""

    pass


class HabitEntryUpdate(BaseModel):
    """Habit entry update schema."""

    completed: Optional[bool] = None
    value: Optional[float] = Field(None, ge=0)
    note: Optional[str] = Field(None, max_length=1000)


class HabitEntryResponse(HabitEntryBase):
    """Habit entry response schema."""

    id: int
    habit_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class HabitEntryListResponse(BaseModel):
    """Habit entry list response."""

    entries: list[HabitEntryResponse]
    total: int


class HabitStatsResponse(BaseModel):
    """Habit statistics response schema."""

    habit_id: int
    date: date
    streak_length: int
    best_streak: int
    rolling_7d_completion: Optional[float]
    rolling_30d_completion: Optional[float]

    class Config:
        from_attributes = True


class CheckInResponse(BaseModel):
    """Check-in response with updated stats."""

    entry: HabitEntryResponse
    stats: HabitStatsResponse


class HabitStatsSeriesResponse(BaseModel):
    """Habit statistics series for charts."""

    stats: list[HabitStatsResponse]
    date_range: dict[str, date]

