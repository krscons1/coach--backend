"""Reports router."""

from datetime import date, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_active_user
from app.db.models import User
from app.schemas.reports import WeeklyReportResponse, EmailReportRequest
from app.services.habit_service import get_habits
from app.services.prediction_service import get_prediction
from app.services.stats_service import compute_habit_stats

router = APIRouter()


@router.get("/weekly", response_model=WeeklyReportResponse)
def get_weekly_report(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    start: Optional[date] = Query(None, description="Start date of week (default: Monday of current week)"),
):
    """Get weekly summary report."""
    # Calculate week start (Monday)
    if start is None:
        today = date.today()
        days_since_monday = today.weekday()
        start = today - timedelta(days=days_since_monday)

    end = start + timedelta(days=6)

    # Get all active habits
    habits, total = get_habits(db, current_user.id, active=True)

    from app.schemas.reports import WeeklySummaryHabit
    from app.schemas.habit import HabitResponse
    from app.schemas.prediction import PredictionResponse

    habit_summaries = []
    at_risk_count = 0

    for habit in habits:
        # Get stats for the week
        stats = compute_habit_stats(db, habit.id, end)
        completion_rate = stats.get("rolling_7d_completion", 0.0) or 0.0
        streak = stats.get("streak_length", 0)

        # Get prediction
        prediction = None
        try:
            prediction = get_prediction(db, habit.id, current_user.id, end, horizon_days=7)
        except Exception:
            pass

        at_risk = prediction is not None and prediction.prob_maintain < 0.4
        if at_risk:
            at_risk_count += 1

        habit_summaries.append(
            WeeklySummaryHabit(
                habit=HabitResponse.model_validate(habit),
                completion_rate=completion_rate,
                streak=streak,
                prediction=prediction,
                at_risk=at_risk,
            )
        )

    # Calculate overall completion rate
    overall_completion = (
        sum(h.completion_rate for h in habit_summaries) / len(habit_summaries)
        if habit_summaries else 0.0
    )

    return WeeklyReportResponse(
        start_date=start,
        end_date=end,
        total_habits=total,
        active_habits=len(habit_summaries),
        overall_completion_rate=overall_completion,
        habits=habit_summaries,
        at_risk_count=at_risk_count,
    )


@router.post("/weekly/email", status_code=status.HTTP_202_ACCEPTED)
def send_weekly_email_report(
    request: EmailReportRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Generate and send weekly email report."""
    from app.workers.tasks import send_weekly_report_email

    recipient = request.recipient_email or current_user.email
    send_weekly_report_email.delay(current_user.id, request.start_date, recipient)

    return {"message": "Weekly report email queued"}

