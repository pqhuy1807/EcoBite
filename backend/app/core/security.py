"""Security utilities: password hashing (bcrypt) and JWT creation/verification."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt is the de-facto standard for password storage; "deprecated=auto"
# lets passlib re-hash on next login when the scheme evolves.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain password for safe persistence (never store the plain text)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain candidate password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | Any,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT whose `sub` claim identifies the user.

    The expiry comes from settings.ACCESS_TOKEN_EXPIRE_MINUTES unless a
    custom timedelta is provided (useful for tests).
    """
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {"sub": str(subject), "iat": now, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT signature/expiry.

    Raises:
        jose.JWTError: if the signature, format or expiration is invalid.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
