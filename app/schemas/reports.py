"""Reports schemas."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.habit import HabitResponse
from app.schemas.prediction import PredictionResponse


class WeeklySummaryHabit(BaseModel):
    """Habit summary for weekly report."""

    habit: HabitResponse
    completion_rate: float
    streak: int
    prediction: Optional[PredictionResponse] = None
    at_risk: bool = False


class WeeklyReportResponse(BaseModel):
    """Weekly report response schema."""

    start_date: date
    end_date: date
    total_habits: int
    active_habits: int
    overall_completion_rate: float
    habits: List[WeeklySummaryHabit]
    at_risk_count: int


class EmailReportRequest(BaseModel):
    """Email report request schema."""

    start_date: date
    recipient_email: Optional[str] = None  # Defaults to current user

