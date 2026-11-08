"""Authentication business logic (credential check + token issuing)."""

import uuid

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    verify_password,
)
from app.models.user import User
from app.schemas.token import Token, UserLoginData
from app.services import user as user_service


def _build_token_response(user: User) -> Token:
    """Build a complete dual-token response matching the Sprint 3 API spec."""
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    raw_role = user.role.value if hasattr(user.role, "value") else str(user.role)
    role_val = str(raw_role).upper()
    return Token(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=UserLoginData(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=role_val,
            green_points_balance=user.green_points_balance,
            created_at=user.created_at.isoformat() if user.created_at else None,
        ),
    )


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Return the user only when both email exists and password verifies."""
    user = await user_service.get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


async def login_for_user(db: AsyncSession, email: str, password: str) -> Token | None:
    """Issue bearer access & refresh tokens; returns None when credentials are invalid."""
    user = await authenticate_user(db, email, password)
    if user is None:
        return None
    return _build_token_response(user)


async def refresh_user_token(db: AsyncSession, refresh_token: str) -> Token | None:
    """Validate a refresh token and issue a fresh token pair."""
    try:
        payload = decode_access_token(refresh_token)
        raw_sub = payload.get("sub")
        token_type = payload.get("type")
        if not raw_sub or token_type != "refresh":
            return None
        user_id = uuid.UUID(str(raw_sub))
    except (JWTError, ValueError):
        return None

    user = await user_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        return None
    return _build_token_response(user)
