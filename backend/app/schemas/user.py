"""Pydantic schemas for user request/response validation."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: UserRole = UserRole.CONSUMER


class UserCreate(UserBase):
    """Registration payload; passwords are plain here and hashed by the service layer."""

    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Partial profile update payload."""

    full_name: str | None = None
    role: UserRole | None = None


class UserResponse(UserBase):
    """Public representation of a user - the password hash never leaves the API."""

    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
