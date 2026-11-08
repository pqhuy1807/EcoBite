"""Pydantic schemas for user request/response validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str | None = None
    role: UserRole = UserRole.CONSUMER

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: object) -> object:
        """Allow both uppercase and lowercase roles (e.g. 'CONSUMER' or 'consumer')."""
        if isinstance(value, str):
            return value.lower()
        return value


class UserCreate(UserBase):
    """Registration payload; passwords are plain here and hashed by the service layer."""

    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Partial profile update payload."""

    full_name: str | None = None
    phone: str | None = None
    role: UserRole | None = None

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()
        return value


class UserResponse(UserBase):
    """Public representation of a user - the password hash never leaves the API."""

    id: uuid.UUID
    is_active: bool
    is_verified: bool = False
    green_points_balance: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
