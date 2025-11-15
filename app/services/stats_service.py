"""Statistics service for computing habit statistics."""

from datetime import date, timedelta
from typing import Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Habit, HabitEntry, HabitStats


def compute_habit_stats(db: Session, habit_id: int, stats_date: date) -> Dict:
    """Compute habit statistics for a given date."""
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise ValueError(f"Habit {habit_id} not found")

    # Get all entries up to stats_date
    entries = (
        db.query(HabitEntry)
        .filter(
            HabitEntry.habit_id == habit_id,
            HabitEntry.date <= stats_date,
        )
        .order_by(HabitEntry.date.desc())
        .all()
    )

    if not entries:
        return {
            "streak_length": 0,
            "best_streak": 0,
            "rolling_7d_completion": None,
            "rolling_30d_completion": None,
        }

    # Compute current streak
    streak_length = _compute_streak(entries, stats_date)

    # Compute best streak
    best_streak = _compute_best_streak(entries)

    # Compute rolling completion rates
    rolling_7d = _compute_rolling_completion(entries, stats_date, days=7)
    rolling_30d = _compute_rolling_completion(entries, stats_date, days=30)

    return {
        "streak_length": streak_length,
        "best_streak": best_streak,
        "rolling_7d_completion": rolling_7d,
        "rolling_30d_completion": rolling_30d,
    }


def _compute_streak(entries: list, current_date: date) -> int:
    """Compute current streak length."""
    if not entries:
        return 0

    # Sort entries by date descending
    entries_by_date = {entry.date: entry for entry in entries}
    sorted_dates = sorted(entries_by_date.keys(), reverse=True)

    streak = 0
    check_date = current_date

    # Check backwards from current date
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


def _compute_rolling_completion(
    entries: list, current_date: date, days: int
) -> float:
    """Compute rolling completion rate for last N days."""
    start_date = current_date - timedelta(days=days - 1)

    relevant_entries = [
        e for e in entries
        if start_date <= e.date <= current_date
    ]

    if not relevant_entries:
        return None

    completed_count = sum(1 for e in relevant_entries if e.completed)
    total_count = len(relevant_entries)

    return completed_count / total_count if total_count > 0 else 0.0


def get_habit_stats_series(
    db: Session,
    habit_id: int,
    from_date: date,
    to_date: date,
) -> list:
    """Get habit stats series for a date range."""
    stats = (
        db.query(HabitStats)
        .filter(
            HabitStats.habit_id == habit_id,
            HabitStats.date >= from_date,
            HabitStats.date <= to_date,
        )
        .order_by(HabitStats.date.asc())
        .all()
    )

    return stats

