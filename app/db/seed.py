"""Database seed script for development."""

from datetime import date, timedelta

from app.db.session import SessionLocal
from app.db.models import User, Habit, HabitEntry
from app.core.security import hash_password
from app.logger import get_logger

logger = get_logger(__name__)


def seed_database():
    """Seed database with sample data."""
    db = SessionLocal()

    try:
        # Create admin user
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                name="Admin User",
                timezone="UTC",
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info("Admin user created")

        # Create test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                password_hash=hash_password("test123"),
                name="Test User",
                timezone="UTC",
                is_active=True,
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            logger.info("Test user created")

        # Create sample habits for test user
        habits = db.query(Habit).filter(Habit.user_id == test_user.id).all()
        if not habits:
            # Morning workout habit
            habit1 = Habit(
                user_id=test_user.id,
                name="Morning Workout",
                description="30 minutes of exercise every morning",
                type="binary",
                schedule={"days": [0, 1, 2, 3, 4, 5, 6], "frequency": "daily"},
                reminder_times=["07:00"],
                difficulty="medium",
                active=True,
            )
            db.add(habit1)
            db.commit()
            db.refresh(habit1)

            # Water intake habit
            habit2 = Habit(
                user_id=test_user.id,
                name="Water Intake",
                description="Drink 8 glasses of water daily",
                type="numeric",
                target_value=8.0,
                schedule={"days": [0, 1, 2, 3, 4, 5, 6], "frequency": "daily"},
                reminder_times=["09:00", "12:00", "15:00", "18:00"],
                difficulty="easy",
                active=True,
            )
            db.add(habit2)
            db.commit()
            db.refresh(habit2)

            # Create some sample entries for the last 30 days
            today = date.today()
            for i in range(30):
                entry_date = today - timedelta(days=i)

                # Morning workout entries (completed 80% of days)
                if i % 5 != 0:  # Skip every 5th day
                    entry1 = HabitEntry(
                        habit_id=habit1.id,
                        user_id=test_user.id,
                        date=entry_date,
                        completed=True,
                    )
                    db.add(entry1)

                # Water intake entries (varying values)
                entry2 = HabitEntry(
                    habit_id=habit2.id,
                    user_id=test_user.id,
                    date=entry_date,
                    completed=True,
                    value=7.0 + (i % 3),  # Values between 7-9
                )
                db.add(entry2)

            db.commit()
            logger.info("Sample habits and entries created")

        logger.info("Database seeding completed")

    except Exception as e:
        logger.error(f"Error seeding database: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

