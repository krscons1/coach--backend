"""Habit service."""

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import Habit, HabitEntry, HabitStats
from app.schemas.habit import HabitCreate, HabitUpdate
from app.logger import get_logger

logger = get_logger(__name__)


def create_habit(db: Session, user_id: int, habit_data: HabitCreate) -> Habit:
    """Create a new habit for a user."""
    try:
        habit = Habit(
            user_id=user_id,
            name=habit_data.name,
            description=habit_data.description,
            type=habit_data.type,
            target_value=habit_data.target_value,
            schedule=habit_data.schedule,
            reminder_times=habit_data.reminder_times,
            difficulty=habit_data.difficulty,
            active=True,
        )
        db.add(habit)
        db.commit()
        db.refresh(habit)
        logger.info(f"Habit created: {habit.id} for user {user_id}")
        return habit
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error creating habit: {e}")
        raise ValueError("Failed to create habit")


def get_habits(
    db: Session,
    user_id: int,
    active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[Habit], int]:
    """Get habits for a user."""
    query = db.query(Habit).filter(Habit.user_id == user_id)

    if active is not None:
        query = query.filter(Habit.active == active)

    total = query.count()
    habits = query.order_by(Habit.created_at.desc()).offset(skip).limit(limit).all()

    return habits, total


def get_habit(db: Session, habit_id: int, user_id: int) -> Optional[Habit]:
    """Get a habit by ID (with ownership check)."""
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == user_id,
    ).first()
    return habit


def update_habit(
    db: Session, habit_id: int, user_id: int, habit_data: HabitUpdate
) -> Optional[Habit]:
    """Update a habit."""
    habit = get_habit(db, habit_id, user_id)
    if not habit:
        return None

    update_data = habit_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(habit, field, value)

    db.commit()
    db.refresh(habit)
    logger.info(f"Habit updated: {habit_id}")
    return habit


def delete_habit(db: Session, habit_id: int, user_id: int) -> bool:
    """Soft delete a habit (deactivate)."""
    habit = get_habit(db, habit_id, user_id)
    if not habit:
        return False

    habit.active = False
    db.commit()
    logger.info(f"Habit deactivated: {habit_id}")
    return True


def checkin_habit(
    db: Session,
    habit_id: int,
    user_id: int,
    checkin_date: date,
    completed: bool,
    value: Optional[float] = None,
    note: Optional[str] = None,
) -> tuple[HabitEntry, HabitStats]:
    """Create or update a habit check-in and update stats."""
    # Get or create entry
    entry = db.query(HabitEntry).filter(
        HabitEntry.habit_id == habit_id,
        HabitEntry.date == checkin_date,
    ).first()

    if entry:
        entry.completed = completed
        entry.value = value
        entry.note = note
    else:
        entry = HabitEntry(
            habit_id=habit_id,
            user_id=user_id,
            date=checkin_date,
            completed=completed,
            value=value,
            note=note,
        )
        db.add(entry)

    db.commit()
    db.refresh(entry)

    # Update stats
    stats = _update_habit_stats(db, habit_id, checkin_date)
    db.commit()

    return entry, stats


def _update_habit_stats(db: Session, habit_id: int, stats_date: date) -> HabitStats:
    """Update or create habit statistics."""
    from app.services.stats_service import compute_habit_stats

    stats = db.query(HabitStats).filter(
        HabitStats.habit_id == habit_id,
        HabitStats.date == stats_date,
    ).first()

    computed_stats = compute_habit_stats(db, habit_id, stats_date)

    if stats:
        stats.streak_length = computed_stats["streak_length"]
        stats.best_streak = computed_stats["best_streak"]
        stats.rolling_7d_completion = computed_stats["rolling_7d_completion"]
        stats.rolling_30d_completion = computed_stats["rolling_30d_completion"]
    else:
        stats = HabitStats(
            habit_id=habit_id,
            date=stats_date,
            streak_length=computed_stats["streak_length"],
            best_streak=computed_stats["best_streak"],
            rolling_7d_completion=computed_stats["rolling_7d_completion"],
            rolling_30d_completion=computed_stats["rolling_30d_completion"],
        )
        db.add(stats)

    db.commit()
    db.refresh(stats)
    return stats


def get_habit_entries(
    db: Session,
    habit_id: int,
    user_id: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[HabitEntry], int]:
    """Get habit entries for a date range."""
    # Verify ownership
    habit = get_habit(db, habit_id, user_id)
    if not habit:
        return [], 0

    query = db.query(HabitEntry).filter(HabitEntry.habit_id == habit_id)

    if from_date:
        query = query.filter(HabitEntry.date >= from_date)
    if to_date:
        query = query.filter(HabitEntry.date <= to_date)

    total = query.count()
    entries = query.order_by(HabitEntry.date.desc()).offset(skip).limit(limit).all()

    return entries, total

