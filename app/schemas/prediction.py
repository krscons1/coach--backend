"""Prediction schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class PredictionExplanation(BaseModel):
    """Prediction explanation feature."""

    feature: str
    importance: float
    value: float
    description: str


class PredictionResponse(BaseModel):
    """Prediction response schema."""

    habit_id: int
    predict_date: date
    horizon_days: int
    prob_maintain: float = Field(..., ge=0.0, le=1.0, description="Probability of maintaining habit")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    explanation: List[PredictionExplanation]
    created_at: Optional[datetime] = None

    @classmethod
    def from_probability(cls, prob_maintain: float, **kwargs) -> PredictionResponse:
        """Create response with risk level determined from probability."""
        if prob_maintain >= 0.7:
            risk_level = "low"
        elif prob_maintain >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "high"
        return cls(prob_maintain=prob_maintain, risk_level=risk_level, **kwargs)


class PredictionListResponse(BaseModel):
    """Prediction list response."""

    predictions: List[PredictionResponse]
    total: int


class BatchPredictionRequest(BaseModel):
    """Batch prediction request schema."""

    predict_date: date
    horizon_days: int = Field(7, ge=1, le=30)
    habit_ids: Optional[List[int]] = None  # None means all active habits

