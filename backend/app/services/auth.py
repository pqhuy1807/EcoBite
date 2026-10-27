"""Authentication business logic (credential check + token issuing)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.token import Token
from app.services import user as user_service


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
    """Issue a bearer token; returns None when credentials are invalid."""
    user = await authenticate_user(db, email, password)
    if user is None:
        return None
    # `sub` carries the user id; the auth dependency resolves it per request.
    return Token(access_token=create_access_token(subject=str(user.id)))
