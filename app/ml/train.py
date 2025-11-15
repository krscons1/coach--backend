"""ML model training script."""

import os
import pickle
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
import lightgbm as lgb

from app.db.session import SessionLocal
from app.db.models import Habit, HabitEntry, HabitStats
from app.ml.features import build_feature_vector
from app.ml.model_registry import get_registry
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


def export_training_data(db) -> pd.DataFrame:
    """Export training data from database."""
    logger.info("Exporting training data from database...")

    # Get all active habits with entries
    habits = db.query(Habit).filter(Habit.active == True).all()
    logger.info(f"Found {len(habits)} active habits")

    training_data = []

    for habit in habits:
        # Get entries
        entries = (
            db.query(HabitEntry)
            .filter(HabitEntry.habit_id == habit.id)
            .order_by(HabitEntry.date.asc())
            .all()
        )

        if len(entries) < 7:  # Need at least 7 days of data
            continue

        # For each entry date (after first week), build features and label
        for i in range(7, len(entries)):
            entry_date = entries[i].date
            # Label: did they maintain the habit in the next 7 days?
            future_entries = [
                e for e in entries[i + 1 : i + 8]
                if e.date <= entry_date + pd.Timedelta(days=7)
            ]
            label = 1.0 if all(e.completed for e in future_entries) else 0.0

            try:
                features = build_feature_vector(db, habit.id, entry_date)
                features["label"] = label
                features["habit_id"] = habit.id
                features["date"] = entry_date
                training_data.append(features)
            except Exception as e:
                logger.warning(f"Error building features for habit {habit.id}, date {entry_date}: {e}")
                continue

    df = pd.DataFrame(training_data)
    logger.info(f"Exported {len(df)} training samples")
    return df


def train_model(df: pd.DataFrame) -> tuple[lgb.LGBMClassifier, list, dict]:
    """Train LightGBM model."""
    logger.info("Training model...")

    # Prepare features and labels
    feature_cols = [
        "rolling_7d_completion",
        "rolling_14d_completion",
        "rolling_30d_completion",
        "current_streak",
        "consecutive_misses",
        "day_of_week",
        "time_since_creation",
        "difficulty",
        "is_numeric",
        "streak_length",
        "best_streak",
        "total_entries",
        "completion_rate_all_time",
    ]

    X = df[feature_cols].fillna(0.0)
    y = df["label"]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train model
    model = lgb.LGBMClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
        verbose=-1,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        eval_metric="auc",
        callbacks=[lgb.early_stopping(stopping_rounds=10)],
    )

    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    metrics = {
        "auc": float(roc_auc_score(y_test, y_pred_proba)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }

    logger.info(f"Model metrics: {metrics}")

    return model, feature_cols, metrics


def save_model(model, feature_names: list, metrics: dict, output_dir: str) -> str:
    """Save trained model to disk."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    model_filename = f"model_{timestamp}.pkl"
    model_path = output_path / model_filename

    model_data = {
        "model": model,
        "feature_names": feature_names,
        "feature_metadata": {
            "feature_names": feature_names,
        },
        "metrics": metrics,
        "trained_at": datetime.utcnow().isoformat(),
    }

    with open(model_path, "wb") as f:
        pickle.dump(model_data, f)

    # Also save as latest_model.pkl
    latest_path = output_path / "latest_model.pkl"
    with open(latest_path, "wb") as f:
        pickle.dump(model_data, f)

    logger.info(f"Model saved to {model_path}")
    return str(model_path)


def main():
    """Main training function."""
    logger.info("Starting model training...")

    # Get database session
    db = SessionLocal()

    try:
        # Export data
        df = export_training_data(db)

        if len(df) < 100:
            logger.warning(f"Insufficient training data: {len(df)} samples. Need at least 100.")
            return

        # Train model
        model, feature_names, metrics = train_model(df)

        # Save model
        output_dir = "app/ml/saved_models"
        model_path = save_model(model, feature_names, metrics, output_dir)

        # Register model
        registry = get_registry()
        registry.register_model(
            model_path=model_path,
            metrics=metrics,
            feature_names=feature_names,
        )

        logger.info("Model training completed successfully")

    except Exception as e:
        logger.error(f"Error during training: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

