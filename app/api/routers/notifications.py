"""Notifications router."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_active_user
from app.db.models import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationUpdate,
)
from app.services.notification_service import (
    create_notification,
    get_notifications,
    dismiss_notification,
)

router = APIRouter()


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification_endpoint(
    notification_data: NotificationCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Schedule a notification."""
    notification = create_notification(db, current_user.id, notification_data)
    return NotificationResponse.model_validate(notification)


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """List notifications for current user."""
    notifications, total = get_notifications(
        db, current_user.id, status=status, skip=skip, limit=limit
    )
    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
    )


@router.post("/{notification_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_notification_endpoint(
    notification_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Dismiss a notification."""
    success = dismiss_notification(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return None

