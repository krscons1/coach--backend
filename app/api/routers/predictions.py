"""Predictions router."""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_active_user
from app.db.models import User
from app.schemas.prediction import (
    PredictionResponse,
    PredictionListResponse,
    BatchPredictionRequest,
    PredictionExplanation,
)
from app.services.prediction_service import (
    get_prediction,
    get_predictions,
    batch_predictions,
)
from app.services.habit_service import get_habit

router = APIRouter()


@router.get("/habits/{habit_id}/prediction", response_model=PredictionResponse)
def get_habit_prediction(
    habit_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    horizon: int = Query(7, ge=1, le=30, description="Prediction horizon in days"),
    predict_date: Optional[date] = Query(None, description="Date to predict from (default: today)"),
    use_cached: bool = Query(True, description="Use cached prediction if available"),
):
    """Get prediction for a habit."""
    predict_date = predict_date or date.today()

    try:
        prediction = get_prediction(
            db, habit_id, current_user.id, predict_date, horizon, use_cached
        )
        return prediction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("", response_model=PredictionListResponse)
def list_predictions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    predict_date: Optional[date] = Query(None),
    horizon_days: Optional[int] = Query(None, ge=1, le=30),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """List predictions for current user."""
    predictions, total = get_predictions(
        db, current_user.id, predict_date, horizon_days, skip, limit
    )
    prediction_responses = []
    for p in predictions:
        explanation_list = []
        if p.explanation:
            for exp in p.explanation:
                if isinstance(exp, dict):
                    explanation_list.append(PredictionExplanation(**exp))
                else:
                    explanation_list.append(exp)
        
        prediction_responses.append(
            PredictionResponse.from_probability(
                prob_maintain=p.prob_maintain,
                habit_id=p.habit_id,
                predict_date=p.predict_date,
                horizon_days=p.horizon_days,
                explanation=explanation_list,
                created_at=p.created_at,
            )
        )
    
    return PredictionListResponse(
        predictions=prediction_responses,
        total=total,
    )


@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
def batch_predictions_endpoint(
    request: BatchPredictionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Trigger batch predictions (admin/worker endpoint)."""
    # TODO: Add admin check
    count = batch_predictions(
        db, request.predict_date, request.horizon_days, request.habit_ids
    )
    return {"message": f"Batch prediction initiated, {count} predictions created"}

