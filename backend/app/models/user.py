"""User ORM model (SQLAlchemy 2.0 Mapped[T] style)."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(enum.StrEnum):
    """Three access roles defined by the EcoBite business spec."""

    CONSUMER = "consumer"
    STORE_PARTNER = "store_partner"
    ADMIN = "admin"


class User(Base):
    """A platform account: consumer, store partner or administrator."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Stored as VARCHAR + CHECK (portable across SQLite & Postgres).
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole", native_enum=False, length=32),
        default=UserRole.CONSUMER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
