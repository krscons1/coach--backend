"""Celery background tasks."""

from datetime import date, timedelta, datetime
from typing import List

from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.prediction_service import batch_predictions
from app.services.notification_service import send_notification, get_notifications
from app.db.models import Notification, User
from app.ml.train import main as train_model_main
from app.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.workers.tasks.predictions_batch")
def predictions_batch():
    """Nightly batch prediction task."""
    logger.info("Starting batch predictions...")
    db = SessionLocal()

    try:
        predict_date = date.today()
        horizons = [3, 7, 14]

        for horizon in horizons:
            count = batch_predictions(db, predict_date, horizon, habit_ids=None)
            logger.info(f"Created {count} predictions for horizon {horizon} days")

    except Exception as e:
        logger.error(f"Error in batch predictions: {e}", exc_info=True)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.weekly_reports_job")
def weekly_reports_job():
    """Weekly report generation job."""
    logger.info("Starting weekly reports job...")
    db = SessionLocal()

    try:
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        logger.info(f"Generating weekly reports for {len(users)} users")

        # Queue email reports for each user
        from app.workers.tasks import send_weekly_report_email

        for user in users:
            # Calculate week start (Monday)
            today = date.today()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)

            send_weekly_report_email.delay(user.id, week_start, user.email)

    except Exception as e:
        logger.error(f"Error in weekly reports job: {e}", exc_info=True)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.send_scheduled_notifications")
def send_scheduled_notifications():
    """Send scheduled notifications that are due."""
    logger.info("Checking for scheduled notifications...")
    db = SessionLocal()

    try:
        now = datetime.utcnow()
        # Get pending notifications scheduled for now or earlier
        notifications = (
            db.query(Notification)
            .filter(
                Notification.status == "pending",
                Notification.scheduled_at <= now,
            )
            .limit(100)  # Process in batches
            .all()
        )

        logger.info(f"Found {len(notifications)} notifications to send")

        for notification in notifications:
            try:
                send_notification(db, notification.id)
            except Exception as e:
                logger.error(f"Error sending notification {notification.id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Error in send_scheduled_notifications: {e}", exc_info=True)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.send_notification_task")
def send_notification_task(notification_id: int):
    """Send a specific notification."""
    db = SessionLocal()
    try:
        send_notification(db, notification_id)
    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {e}", exc_info=True)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.send_weekly_report_email")
def send_weekly_report_email(user_id: int, week_start: date, recipient_email: str):
    """Send weekly report email to a user."""
    logger.info(f"Sending weekly report email to user {user_id}")
    db = SessionLocal()

    try:
        # Generate report (reuse logic from reports router)
        from app.services.habit_service import get_habits
        from app.services.prediction_service import get_prediction
        from app.services.stats_service import compute_habit_stats

        habits, _ = get_habits(db, user_id, active=True)
        week_end = week_start + timedelta(days=6)

        # Build report content
        report_content = {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "habits": [],
        }

        for habit in habits:
            stats = compute_habit_stats(db, habit.id, week_end)
            try:
                prediction = get_prediction(db, habit.id, user_id, week_end, horizon_days=7)
                at_risk = prediction.prob_maintain < 0.4
            except Exception:
                at_risk = False
                prediction = None

            report_content["habits"].append({
                "name": habit.name,
                "completion_rate": stats.get("rolling_7d_completion", 0.0),
                "streak": stats.get("streak_length", 0),
                "at_risk": at_risk,
            })

        # TODO: Send email via SMTP
        logger.info(f"Weekly report generated for user {user_id}")
        # For now, just log the report
        logger.debug(f"Report content: {report_content}")

    except Exception as e:
        logger.error(f"Error sending weekly report email: {e}", exc_info=True)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.train_model_task")
def train_model_task():
    """Train ML model (scheduled or manual trigger)."""
    logger.info("Starting model training task...")
    try:
        train_model_main()
        logger.info("Model training completed")
    except Exception as e:
        logger.error(f"Error in model training: {e}", exc_info=True)
        raise

