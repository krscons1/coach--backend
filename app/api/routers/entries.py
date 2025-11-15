"""Habit entries router."""

from datetime import date, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_active_user
from app.db.models import User
from app.schemas.entry import (
    HabitEntryCreate,
    HabitEntryResponse,
    HabitEntryListResponse,
    CheckInResponse,
    HabitStatsResponse,
    HabitStatsSeriesResponse,
)
from app.services.habit_service import checkin_habit, get_habit_entries, get_habit
from app.services.stats_service import get_habit_stats_series

router = APIRouter()


@router.post("/{habit_id}/checkin", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def checkin(
    habit_id: int,
    entry_data: HabitEntryCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create or update a habit check-in."""
    # Verify ownership
    habit = get_habit(db, habit_id, current_user.id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )

    try:
        entry, stats = checkin_habit(
            db,
            habit_id,
            current_user.id,
            entry_data.date,
            entry_data.completed,
            entry_data.value,
            entry_data.note,
        )
        return CheckInResponse(
            entry=HabitEntryResponse.model_validate(entry),
            stats=HabitStatsResponse.model_validate(stats),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{habit_id}/entries", response_model=HabitEntryListResponse)
def get_entries(
    habit_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    from_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    to_date: Optional[date] = Query(None, description="End date (inclusive)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """Get historical entries for a habit."""
    entries, total = get_habit_entries(
        db, habit_id, current_user.id, from_date, to_date, skip, limit
    )
    return HabitEntryListResponse(
        entries=[HabitEntryResponse.model_validate(e) for e in entries],
        total=total,
    )


@router.get("/{habit_id}/stats", response_model=HabitStatsSeriesResponse)
def get_stats(
    habit_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    range: Optional[str] = Query("30d", description="Predefined range: 7d, 30d, 90d, all"),
):
    """Get habit statistics series."""
    habit = get_habit(db, habit_id, current_user.id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )

    # Determine date range
    if range == "7d":
        to_date = to_date or date.today()
        from_date = from_date or (to_date - timedelta(days=7))
    elif range == "30d":
        to_date = to_date or date.today()
        from_date = from_date or (to_date - timedelta(days=30))
    elif range == "90d":
        to_date = to_date or date.today()
        from_date = from_date or (to_date - timedelta(days=90))
    else:
        # Get all stats
        from_date = from_date or habit.created_at.date()
        to_date = to_date or date.today()

    stats = get_habit_stats_series(db, habit_id, from_date, to_date)
    return HabitStatsSeriesResponse(
        stats=[HabitStatsResponse.model_validate(s) for s in stats],
        date_range={"from": from_date, "to": to_date},
    )

