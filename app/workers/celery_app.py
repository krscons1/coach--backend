"""Celery app configuration."""

from app.core.background import celery_app

__all__ = ["celery_app"]

