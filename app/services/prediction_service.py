"""Prediction service for ML-based habit predictions."""

from datetime import date, timedelta
from typing import Optional, Dict, List

from sqlalchemy.orm import Session

from app.db.models import Habit, Prediction, HabitEntry, HabitStats
from app.core.ml_loader import predict as ml_predict
from app.ml.features import build_feature_vector
from app.schemas.prediction import PredictionResponse, PredictionExplanation
from app.logger import get_logger

logger = get_logger(__name__)


def get_prediction(
    db: Session,
    habit_id: int,
    user_id: int,
    predict_date: date,
    horizon_days: int = 7,
    use_cached: bool = True,
) -> PredictionResponse:
    """Get prediction for a habit (compute or return cached)."""
    # Verify ownership
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user_id,
        Habit.active == True,
    ).first()

    if not habit:
        raise ValueError("Habit not found or not active")

    # Check for cached prediction
    if use_cached:
        cached = db.query(Prediction).filter(
            Prediction.habit_id == habit_id,
            Prediction.predict_date == predict_date,
            Prediction.horizon_days == horizon_days,
        ).first()

        if cached:
            explanation_list = []
            if cached.explanation:
                for exp in cached.explanation:
                    if isinstance(exp, dict):
                        explanation_list.append(PredictionExplanation(**exp))
                    else:
                        explanation_list.append(exp)
            
            return PredictionResponse.from_probability(
                prob_maintain=cached.prob_maintain,
                habit_id=habit_id,
                predict_date=predict_date,
                horizon_days=horizon_days,
                explanation=explanation_list,
                created_at=cached.created_at,
            )

    # Compute new prediction
    features = build_feature_vector(db, habit_id, predict_date)
    prob_maintain, explanation_data = ml_predict(
        features, habit_id, predict_date, horizon_days
    )

    # Convert explanation to schema format
    explanation = [
        PredictionExplanation(**exp) for exp in explanation_data
    ]

    # Save prediction
    prediction = Prediction(
        habit_id=habit_id,
        user_id=user_id,
        predict_date=predict_date,
        horizon_days=horizon_days,
        prob_maintain=prob_maintain,
        explanation=[exp.model_dump() for exp in explanation],
    )
    db.add(prediction)
    db.commit()

    return PredictionResponse.from_probability(
        prob_maintain=prob_maintain,
        habit_id=habit_id,
        predict_date=predict_date,
        horizon_days=horizon_days,
        explanation=explanation,
        created_at=prediction.created_at,
    )


def batch_predictions(
    db: Session,
    predict_date: date,
    horizon_days: int = 7,
    habit_ids: Optional[List[int]] = None,
) -> int:
    """Run batch predictions for all active habits."""
    query = db.query(Habit).filter(Habit.active == True)

    if habit_ids:
        query = query.filter(Habit.id.in_(habit_ids))

    habits = query.all()
    count = 0

    for habit in habits:
        try:
            # Check if prediction already exists
            existing = db.query(Prediction).filter(
                Prediction.habit_id == habit.id,
                Prediction.predict_date == predict_date,
                Prediction.horizon_days == horizon_days,
            ).first()

            if existing:
                continue

            # Build features and predict
            features = build_feature_vector(db, habit.id, predict_date)
            prob_maintain, explanation_data = ml_predict(
                features, habit.id, predict_date, horizon_days
            )

            # Save prediction
            prediction = Prediction(
                habit_id=habit.id,
                user_id=habit.user_id,
                predict_date=predict_date,
                horizon_days=horizon_days,
                prob_maintain=prob_maintain,
                explanation=explanation_data,
            )
            db.add(prediction)
            count += 1

        except Exception as e:
            logger.error(f"Error predicting for habit {habit.id}: {e}", exc_info=True)
            continue

    db.commit()
    logger.info(f"Batch predictions completed: {count} predictions created")
    return count


def get_predictions(
    db: Session,
    user_id: int,
    predict_date: Optional[date] = None,
    horizon_days: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[Prediction], int]:
    """Get predictions for a user."""
    query = db.query(Prediction).filter(Prediction.user_id == user_id)

    if predict_date:
        query = query.filter(Prediction.predict_date == predict_date)
    if horizon_days:
        query = query.filter(Prediction.horizon_days == horizon_days)

    total = query.count()
    predictions = query.order_by(Prediction.created_at.desc()).offset(skip).limit(limit).all()

    return predictions, total

