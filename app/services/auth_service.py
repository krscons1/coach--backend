"""Authentication service."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.db.models import User, AuditLog
from app.schemas.auth import UserCreate
from app.logger import get_logger

logger = get_logger(__name__)


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    try:
        password_hash = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            name=user_data.name,
            timezone="UTC",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Audit log
        audit_log = AuditLog(
            event_type="user_created",
            user_id=user.id,
            payload={"email": user.email},
        )
        db.add(audit_log)
        db.commit()

        logger.info(f"User created: {user.email}")
        return user
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        return None

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Audit log
    audit_log = AuditLog(
        event_type="user_login",
        user_id=user.id,
        payload={"email": user.email},
    )
    db.add(audit_log)
    db.commit()

    return user


def create_tokens_for_user(user: User) -> dict:
    """Create access and refresh tokens for a user."""
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def rotate_refresh_token(db: Session, refresh_token: str) -> Optional[dict]:
    """Rotate refresh token and return new tokens."""
    from app.core.security import verify_refresh_token, rotate_refresh_token as rotate_token

    payload = verify_refresh_token(refresh_token)
    if not payload:
        return None

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        return None

    new_refresh_token = rotate_token(refresh_token)
    if not new_refresh_token:
        return None

    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
    }


def revoke_refresh_token(db: Session, user_id: int) -> None:
    """Revoke refresh token for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.refresh_token_hash = None
        db.commit()

        # Audit log
        audit_log = AuditLog(
            event_type="user_logout",
            user_id=user_id,
        )
        db.add(audit_log)
        db.commit()

