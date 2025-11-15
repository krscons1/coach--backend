"""SQLAlchemy database models."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    refresh_token_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    entries = relationship("HabitEntry", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Habit(Base):
    """Habit model."""

    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(20), nullable=False)  # 'binary' or 'numeric'
    target_value = Column(Float, nullable=True)  # For numeric habits
    schedule = Column(JSON, nullable=False)  # e.g., {"days": [1,2,3,4,5], "frequency": "daily"}
    reminder_times = Column(JSON, nullable=True)  # e.g., ["09:00", "21:00"]
    difficulty = Column(String(20), default="medium")  # 'easy', 'medium', 'hard'
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="habits")
    entries = relationship("HabitEntry", back_populates="habit", cascade="all, delete-orphan")
    stats = relationship("HabitStats", back_populates="habit", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="habit", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="habit")

    def __repr__(self) -> str:
        return f"<Habit(id={self.id}, name={self.name}, user_id={self.user_id})>"


class HabitEntry(Base):
    """Habit entry (daily check-in) model."""

    __tablename__ = "habit_entries"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    value = Column(Float, nullable=True)  # For numeric habits
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    habit = relationship("Habit", back_populates="entries")
    user = relationship("User", back_populates="entries")

    __table_args__ = (
        UniqueConstraint("habit_id", "date", name="unique_habit_date"),
        Index("idx_habit_date", "habit_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<HabitEntry(id={self.id}, habit_id={self.habit_id}, date={self.date})>"


class HabitStats(Base):
    """Habit statistics model (precomputed stats per day)."""

    __tablename__ = "habit_stats"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    streak_length = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    rolling_7d_completion = Column(Float, nullable=True)
    rolling_30d_completion = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    habit = relationship("Habit", back_populates="stats")

    __table_args__ = (
        UniqueConstraint("habit_id", "date", name="unique_habit_stats_date"),
        Index("idx_habit_stats_date", "habit_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<HabitStats(id={self.id}, habit_id={self.habit_id}, date={self.date})>"


class Prediction(Base):
    """ML prediction model."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    predict_date = Column(Date, nullable=False, index=True)
    horizon_days = Column(Integer, nullable=False)  # 3, 7, or 14
    prob_maintain = Column(Float, nullable=False)  # Probability of maintaining habit (0-1)
    explanation = Column(JSON, nullable=True)  # Top contributing features
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    habit = relationship("Habit", back_populates="predictions")
    user = relationship("User", back_populates="predictions")

    __table_args__ = (
        Index("idx_prediction_lookup", "habit_id", "predict_date", "horizon_days"),
    )

    def __repr__(self) -> str:
        return f"<Prediction(id={self.id}, habit_id={self.habit_id}, prob={self.prob_maintain})>"


class Notification(Base):
    """Notification model."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(50), nullable=False)  # 'reminder', 'report', 'alert', etc.
    payload = Column(JSON, nullable=True)  # Additional notification data
    scheduled_at = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")  # 'pending', 'sent', 'failed', 'dismissed'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")
    habit = relationship("Habit", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"


class AuditLog(Base):
    """Audit log for important events (optional)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type={self.event_type})>"

