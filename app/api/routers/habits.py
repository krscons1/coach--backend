"""Habits router."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_active_user
from app.db.models import User
from app.schemas.habit import HabitCreate, HabitUpdate, HabitResponse, HabitListResponse
from app.services.habit_service import (
    create_habit,
    get_habits,
    get_habit,
    update_habit,
    delete_habit,
)

router = APIRouter()


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
def create_habit_endpoint(
    habit_data: HabitCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new habit."""
    try:
        habit = create_habit(db, current_user.id, habit_data)
        return HabitResponse.model_validate(habit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=HabitListResponse)
def list_habits(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """List habits for current user."""
    habits, total = get_habits(db, current_user.id, active=active, skip=skip, limit=limit)
    return HabitListResponse(
        habits=[HabitResponse.model_validate(h) for h in habits],
        total=total,
    )


@router.get("/{habit_id}", response_model=HabitResponse)
def get_habit_endpoint(
    habit_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get habit by ID."""
    habit = get_habit(db, habit_id, current_user.id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )
    return HabitResponse.model_validate(habit)


@router.put("/{habit_id}", response_model=HabitResponse)
def update_habit_endpoint(
    habit_id: int,
    habit_data: HabitUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update a habit."""
    habit = update_habit(db, habit_id, current_user.id, habit_data)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )
    return HabitResponse.model_validate(habit)


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit_endpoint(
    habit_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete (deactivate) a habit."""
    success = delete_habit(db, habit_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )
    return None

