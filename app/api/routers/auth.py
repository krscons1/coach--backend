"""Authentication router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_active_user
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.services.auth_service import (
    create_user,
    authenticate_user,
    create_tokens_for_user,
    rotate_refresh_token,
    revoke_refresh_token,
)
from app.db.models import User

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new user."""
    try:
        user = create_user(db, user_data)
        tokens = create_tokens_for_user(user)
        return TokenResponse(
            access_token=tokens["access_token"],
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    """Login and get access token."""
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    tokens = create_tokens_for_user(user)

    # Set refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    http_request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    """Refresh access token using refresh token."""
    # Try to get refresh token from cookie or body
    refresh_token = request.refresh_token
    if not refresh_token:
        # Try to get from cookie
        refresh_token = http_request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided",
        )

    tokens = rotate_refresh_token(db, refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Set new refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )

    return RefreshTokenResponse(
        access_token=tokens["access_token"],
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Logout and revoke refresh token."""
    revoke_refresh_token(db, current_user.id)
    response.delete_cookie(key="refresh_token")
    return None

