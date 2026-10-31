"""User and UserPreference ORM models (SQLAlchemy 2.0 Mapped[T] style)."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.gamification import GreenPointsLedger, UserVoucher
    from app.models.interaction import Notification, Review
    from app.models.order import Order
    from app.models.store import Store

# Portable JSON type: native JSONB on PostgreSQL, standard JSON on SQLite (in-memory tests)
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class UserRole(enum.StrEnum):
    """Three access roles defined by the EcoBite business spec."""

    CONSUMER = "consumer"
    STORE_PARTNER = "store_partner"
    ADMIN = "admin"


class DietaryPreference(enum.StrEnum):
    """Dietary preferences for filtering food rescue options."""

    NONE = "NONE"
    VEGAN = "VEGAN"
    VEGETARIAN = "VEGETARIAN"


class User(Base):
    """A platform account: consumer, store partner or administrator."""

    __tablename__ = "users"

    # UUID primary key according to 03_Database_Schema_ERD.md
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Stored as VARCHAR + CHECK (portable across SQLite & Postgres)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole", native_enum=False, length=32),
        default=UserRole.CONSUMER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    green_points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 1-to-1 relationship with UserPreference
    preference: Mapped["UserPreference | None"] = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # 1-to-N relationship with Store (A STORE_PARTNER user can own multiple stores)
    stores: Mapped[list["Store"]] = relationship(
        "Store",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # 1-to-N relationship with Order (placed by this consumer)
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="consumer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Gamification & Social relationships
    green_points_records: Mapped[list["GreenPointsLedger"]] = relationship(
        "GreenPointsLedger",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    user_vouchers: Mapped[list["UserVoucher"]] = relationship(
        "UserVoucher",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="consumer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class UserPreference(Base):
    """User dietary preferences and hard allergen exclusion profile.

    Used by the recommendation engine and Gemini 2.5 Flash.
    """

    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Preferred meal categories: e.g. ["RICE", "NOODLES", "BAKERY"]
    preferred_categories: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)

    # Dietary preference: NONE, VEGAN, VEGETARIAN
    dietary_preference: Mapped[DietaryPreference] = mapped_column(
        Enum(DietaryPreference, name="dietarypreference", native_enum=False, length=50),
        default=DietaryPreference.NONE,
        nullable=False,
    )

    # AGENTS.md Guardrail #7 - Allergen Hard Invariant:
    # SQL filter strictly excludes dishes containing these allergens before AI justification
    excluded_allergens: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)

    # Preferred budget threshold
    max_budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 1-to-1 back-reference to User
    user: Mapped["User"] = relationship("User", back_populates="preference", lazy="selectin")
