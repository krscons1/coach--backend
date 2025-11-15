"""API v1 router registration."""

from fastapi import APIRouter

from app.api.routers import (
    auth,
    habits,
    entries,
    predictions,
    reports,
    notifications,
    admin,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(habits.router, prefix="/habits", tags=["habits"])
api_router.include_router(entries.router, prefix="/habits", tags=["entries"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

