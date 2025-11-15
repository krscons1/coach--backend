"""Admin router (internal/worker endpoints)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_active_user
from app.db.models import User
from app.core.ml_loader import load_model, is_model_loaded
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/train-model", status_code=status.HTTP_202_ACCEPTED)
def train_model(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Trigger model training (admin only)."""
    # TODO: Add admin check
    from app.workers.tasks import train_model_task
    train_model_task.delay()
    return {"message": "Model training queued"}


@router.post("/reload-model", status_code=status.HTTP_200_OK)
def reload_model(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Reload ML model from disk."""
    # TODO: Add admin check
    success = load_model()
    if success:
        return {"message": "Model reloaded successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload model",
        )


@router.get("/health")
def admin_health_check(
    db: Annotated[Session, Depends(get_db)],
):
    """Detailed health check including ML model and services."""
    import redis
    from app.config import settings

    health = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "ml_model": "unknown",
    }

    # Check database
    try:
        db.execute("SELECT 1")
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health["redis"] = "connected"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    # Check ML model
    if is_model_loaded():
        health["ml_model"] = "loaded"
    else:
        health["ml_model"] = "fallback"
        health["status"] = "degraded"

    return health

