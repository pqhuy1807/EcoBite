"""Business logic for user accounts, independent of the API layer."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Return the active-or-not user matching an email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Read a user by primary key (used by the JWT auth dependency)."""
    return await db.get(User, user_id)


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Persist a new user; the plain password is hashed and never stored raw."""
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        phone=getattr(user_in, "phone", None),
        role=user_in.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
