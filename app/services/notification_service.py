"""Notification service."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import Notification, User, Habit
from app.schemas.notification import NotificationCreate, NotificationUpdate
from app.logger import get_logger
from app.core.background import celery_app

logger = get_logger(__name__)


def create_notification(
    db: Session,
    user_id: int,
    notification_data: NotificationCreate,
) -> Notification:
    """Create a notification."""
    notification = Notification(
        user_id=user_id,
        habit_id=notification_data.habit_id,
        type=notification_data.type,
        payload=notification_data.payload,
        scheduled_at=notification_data.scheduled_at,
        status="pending",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Schedule task if scheduled_at is in the future
    if notification.scheduled_at > datetime.utcnow():
        from app.workers.tasks import send_notification_task
        send_notification_task.apply_async(
            args=[notification.id],
            eta=notification.scheduled_at,
        )

    logger.info(f"Notification created: {notification.id}")
    return notification


def get_notifications(
    db: Session,
    user_id: int,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[Notification], int]:
    """Get notifications for a user."""
    query = db.query(Notification).filter(Notification.user_id == user_id)

    if status:
        query = query.filter(Notification.status == status)

    total = query.count()
    notifications = (
        query.order_by(Notification.scheduled_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return notifications, total


def send_notification(db: Session, notification_id: int) -> bool:
    """Send a notification (called by worker)."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not notification:
        logger.warning(f"Notification {notification_id} not found")
        return False

    if notification.status != "pending":
        logger.info(f"Notification {notification_id} already processed")
        return False

    try:
        # Send via appropriate channel based on type
        if notification.type == "reminder":
            _send_reminder(notification)
        elif notification.type == "report":
            _send_report(notification)
        elif notification.type == "alert":
            _send_alert(notification)

        notification.status = "sent"
        notification.sent_at = datetime.utcnow()
        db.commit()
        logger.info(f"Notification {notification_id} sent successfully")
        return True

    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {e}", exc_info=True)
        notification.status = "failed"
        db.commit()
        return False


def _send_reminder(notification: Notification) -> None:
    """Send reminder notification."""
    # TODO: Implement FCM push or email
    logger.info(f"Sending reminder notification {notification.id}")


def _send_report(notification: Notification) -> None:
    """Send report notification."""
    # TODO: Implement email report
    logger.info(f"Sending report notification {notification.id}")


def _send_alert(notification: Notification) -> None:
    """Send alert notification."""
    # TODO: Implement push notification
    logger.info(f"Sending alert notification {notification.id}")


def dismiss_notification(db: Session, notification_id: int, user_id: int) -> bool:
    """Dismiss a notification."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    ).first()

    if not notification:
        return False

    notification.status = "dismissed"
    db.commit()
    return True

