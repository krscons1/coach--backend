"""Feature engineering for ML predictions."""

from datetime import date, timedelta
from typing import Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Habit, HabitEntry, HabitStats


def build_feature_vector(db: Session, habit_id: int, predict_date: date) -> Dict[str, float]:
    """
    Build feature vector for a habit at a given date.

    Returns a dictionary of feature names and values.
    """
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise ValueError(f"Habit {habit_id} not found")

    # Get entries up to predict_date
    entries = (
        db.query(HabitEntry)
        .filter(
            HabitEntry.habit_id == habit_id,
            HabitEntry.date <= predict_date,
        )
        .order_by(HabitEntry.date.desc())
        .all()
    )

    # Get latest stats if available
    latest_stats = (
        db.query(HabitStats)
        .filter(
            HabitStats.habit_id == habit_id,
            HabitStats.date <= predict_date,
        )
        .order_by(HabitStats.date.desc())
        .first()
    )

    # Compute features
    features = {}

    # Rolling completion rates
    features["rolling_7d_completion"] = _compute_rolling_completion(entries, predict_date, days=7)
    features["rolling_14d_completion"] = _compute_rolling_completion(entries, predict_date, days=14)
    features["rolling_30d_completion"] = _compute_rolling_completion(entries, predict_date, days=30)

    # Current streak
    features["current_streak"] = float(_compute_streak(entries, predict_date))

    # Consecutive misses
    features["consecutive_misses"] = float(_compute_consecutive_misses(entries, predict_date))

    # Day of week (0=Monday, 6=Sunday)
    features["day_of_week"] = float(predict_date.weekday())

    # Time since creation
    days_since_creation = (predict_date - habit.created_at.date()).days
    features["time_since_creation"] = float(days_since_creation)

    # Difficulty encoding
    difficulty_map = {"easy": 0.0, "medium": 0.5, "hard": 1.0}
    features["difficulty"] = difficulty_map.get(habit.difficulty, 0.5)

    # Habit type encoding
    features["is_numeric"] = 1.0 if habit.type == "numeric" else 0.0

    # Use stats if available
    if latest_stats:
        features["streak_length"] = float(latest_stats.streak_length)
        features["best_streak"] = float(latest_stats.best_streak)
    else:
        features["streak_length"] = features["current_streak"]
        features["best_streak"] = float(_compute_best_streak(entries))

    # Engagement metrics
    total_entries = len(entries)
    features["total_entries"] = float(total_entries)
    features["completion_rate_all_time"] = (
        sum(1 for e in entries if e.completed) / total_entries
        if total_entries > 0 else 0.0
    )

    return features


def _compute_rolling_completion(entries: list, current_date: date, days: int) -> float:
    """Compute rolling completion rate for last N days."""
    start_date = current_date - timedelta(days=days - 1)
    relevant_entries = [e for e in entries if start_date <= e.date <= current_date]

    if not relevant_entries:
        return 0.0

    completed_count = sum(1 for e in relevant_entries if e.completed)
    return completed_count / len(relevant_entries)


def _compute_streak(entries: list, current_date: date) -> int:
    """Compute current streak length."""
    if not entries:
        return 0

    entries_by_date = {entry.date: entry for entry in entries}
    sorted_dates = sorted(entries_by_date.keys(), reverse=True)

    streak = 0
    check_date = current_date

    while check_date >= sorted_dates[-1]:
        entry = entries_by_date.get(check_date)
        if entry and entry.completed:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return streak


def _compute_best_streak(entries: list) -> int:
    """Compute best streak from all entries."""
    if not entries:
        return 0

    entries_by_date = {entry.date: entry for entry in entries}
    sorted_dates = sorted(entries_by_date.keys())

    best_streak = 0
    current_streak = 0

    for d in sorted_dates:
        entry = entries_by_date.get(d)
        if entry and entry.completed:
            current_streak += 1
            best_streak = max(best_streak, current_streak)
        else:
            current_streak = 0

    return best_streak


def _compute_consecutive_misses(entries: list, current_date: date) -> int:
    """Compute consecutive missed days from current date backwards."""
    if not entries:
        return 0

    entries_by_date = {entry.date: entry for entry in entries}
    sorted_dates = sorted(entries_by_date.keys(), reverse=True)

    misses = 0
    check_date = current_date

    while check_date >= sorted_dates[-1]:
        entry = entries_by_date.get(check_date)
        if not entry or not entry.completed:
            misses += 1
            check_date -= timedelta(days=1)
        else:
            break

    return misses

