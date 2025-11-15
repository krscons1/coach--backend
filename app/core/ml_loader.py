"""ML model loader and prediction wrapper."""

import os
import pickle
from datetime import date
from typing import Dict, List, Optional, Tuple
import logging

import numpy as np
import pandas as pd

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Global model storage
_model: Optional[object] = None
_feature_metadata: Optional[Dict] = None
_use_fallback: bool = False


def load_model() -> bool:
    """Load ML model from disk on startup."""
    global _model, _feature_metadata, _use_fallback

    model_path = settings.ML_MODEL_PATH
    if not os.path.exists(model_path):
        logger.warning(f"Model file not found at {model_path}, using fallback predictions")
        _use_fallback = True
        return False

    try:
        with open(model_path, "rb") as f:
            model_data = pickle.load(f)
            _model = model_data.get("model")
            _feature_metadata = model_data.get("feature_metadata", {})
            _use_fallback = False
        logger.info(f"ML model loaded successfully from {model_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}", exc_info=True)
        _use_fallback = True
        return False


def get_model() -> Optional[object]:
    """Get the loaded model."""
    return _model


def is_model_loaded() -> bool:
    """Check if model is loaded."""
    return _model is not None and not _use_fallback


def predict(
    features: Dict[str, float],
    habit_id: int,
    date: date,
    horizon_days: int = 7,
) -> Tuple[float, List[Dict[str, any]]]:
    """
    Predict probability of maintaining habit and generate explanation.

    Returns:
        Tuple of (probability, explanation_list)
        probability: float between 0-1
        explanation_list: List of dicts with 'feature', 'importance', 'value'
    """
    if _use_fallback or _model is None:
        return _fallback_predict(features, habit_id, date, horizon_days)

    try:
        # Convert features dict to DataFrame in correct order
        feature_names = _feature_metadata.get("feature_names", list(features.keys()))
        feature_vector = np.array([[features.get(name, 0.0) for name in feature_names]])

        # Get prediction probability
        if hasattr(_model, "predict_proba"):
            proba = _model.predict_proba(feature_vector)[0]
            prob_maintain = float(proba[1] if len(proba) > 1 else proba[0])
        else:
            # Fallback for models without predict_proba
            prediction = _model.predict(feature_vector)[0]
            prob_maintain = float(prediction) if isinstance(prediction, (int, float)) else 0.5

        # Generate explanation using feature importance
        explanation = _generate_explanation(features, feature_names)

        return prob_maintain, explanation

    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return _fallback_predict(features, habit_id, date, horizon_days)


def _fallback_predict(
    features: Dict[str, float],
    habit_id: int,
    date: date,
    horizon_days: int,
) -> Tuple[float, List[Dict[str, any]]]:
    """Rule-based fallback prediction when model is unavailable."""
    # Simple heuristic based on completion rates
    rolling_7d = features.get("rolling_7d_completion", 0.5)
    rolling_30d = features.get("rolling_30d_completion", 0.5)
    current_streak = features.get("current_streak", 0)

    # Weighted average
    prob_maintain = (rolling_7d * 0.5 + rolling_30d * 0.3 + min(current_streak / 30, 1.0) * 0.2)
    prob_maintain = max(0.0, min(1.0, prob_maintain))

    explanation = [
        {
            "feature": "rolling_7d_completion",
            "importance": 0.5,
            "value": rolling_7d,
            "description": "7-day completion rate",
        },
        {
            "feature": "rolling_30d_completion",
            "importance": 0.3,
            "value": rolling_30d,
            "description": "30-day completion rate",
        },
        {
            "feature": "current_streak",
            "importance": 0.2,
            "value": current_streak,
            "description": "Current streak length",
        },
    ]

    return prob_maintain, explanation


def _generate_explanation(
    features: Dict[str, float], feature_names: List[str]
) -> List[Dict[str, any]]:
    """Generate explanation from feature importance."""
    explanation = []

    # Try to get feature importance from model
    if hasattr(_model, "feature_importances_"):
        importances = _model.feature_importances_
        feature_importance_map = dict(zip(feature_names, importances))
    elif hasattr(_model, "get_feature_importance"):
        feature_importance_map = _model.get_feature_importance()
    else:
        # Fallback: equal importance
        feature_importance_map = {name: 1.0 / len(feature_names) for name in feature_names}

    # Sort by importance and take top 3
    sorted_features = sorted(
        feature_importance_map.items(), key=lambda x: x[1], reverse=True
    )[:3]

    for feature_name, importance in sorted_features:
        explanation.append(
            {
                "feature": feature_name,
                "importance": float(importance),
                "value": features.get(feature_name, 0.0),
                "description": _get_feature_description(feature_name),
            }
        )

    return explanation


def _get_feature_description(feature_name: str) -> str:
    """Get human-readable description for a feature."""
    descriptions = {
        "rolling_7d_completion": "7-day completion rate",
        "rolling_30d_completion": "30-day completion rate",
        "current_streak": "Current streak length",
        "consecutive_misses": "Consecutive missed days",
        "day_of_week": "Day of week",
        "difficulty": "Habit difficulty level",
        "time_since_creation": "Days since habit creation",
    }
    return descriptions.get(feature_name, feature_name.replace("_", " ").title())

