"""Repository for User account persistence (AsyncSession SQLAlchemy 2.0)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """Return the user matching an email address, or None if not found."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Read a user by primary key UUID."""
    return await db.get(User, user_id)


async def create(
    db: AsyncSession,
    *,
    email: str,
    hashed_password: str,
    full_name: str,
    phone: str | None = None,
    role: UserRole = UserRole.CONSUMER,
) -> User:
    """Persist a new User record in the database."""
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        phone=phone,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
