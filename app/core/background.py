"""Celery background task configuration."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "habit_coach",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    "batch-predictions-nightly": {
        "task": "app.workers.tasks.predictions_batch",
        "schedule": crontab(hour=2, minute=0),  # 2 AM UTC daily
    },
    "weekly-reports": {
        "task": "app.workers.tasks.weekly_reports_job",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),  # Monday 8 AM UTC
    },
    "send-scheduled-notifications": {
        "task": "app.workers.tasks.send_scheduled_notifications",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
}

