"""Shared FastAPI dependencies: DB session, current user, role gating."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services import user as user_service

# tokenUrl points at the login form so OpenAPI "Authorize" works out of the box.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Reusable annotated aliases - keeps endpoints clean of bare Depends() calls.
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DBSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Resolve the User from a Bearer JWT (`sub` = user id)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_access_token(token)
        raw_subject = payload.get("sub")
    except JWTError:
        raise credentials_exception from None
    if raw_subject is None:
        raise credentials_exception
    try:
        user_id = uuid.UUID(raw_subject)
    except ValueError:
        raise credentials_exception from None

    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


# Resolvable only after get_current_user is defined (Annotated evaluates eagerly).
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole):
    """Build a dependency that only lets whitelisted roles through.

    Usage (AGENTS.md guardrail #2):
        @router.get("/admin", dependencies=[Depends(require_roles(UserRole.ADMIN))])
    """

    async def role_checker(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have the required role",
            )
        return current_user

    return role_checker
