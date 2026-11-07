"""Business logic for user accounts, delegating persistence to user_repo."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Return the active-or-not user matching an email address."""
    return await user_repo.get_by_email(db, email)


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Read a user by primary key (used by the JWT auth dependency)."""
    return await user_repo.get_by_id(db, user_id)


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Hash the plain password and persist a new user via user_repo."""
    return await user_repo.create(
        db,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        phone=getattr(user_in, "phone", None),
        role=user_in.role,
    )
