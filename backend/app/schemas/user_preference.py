"""Pydantic schemas for user dietary preferences and allergen exclusions."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import DietaryPreference


class UserPreferenceBase(BaseModel):
    preferred_categories: list[str] = Field(
        default_factory=list,
        description="List of favorite categories, e.g. ['RICE', 'NOODLES', 'BAKERY']",
    )
    dietary_preference: DietaryPreference = Field(
        default=DietaryPreference.NONE,
        description="Dietary lifestyle: NONE, VEGAN, VEGETARIAN",
    )
    excluded_allergens: list[str] = Field(
        default_factory=list,
        description="Hard SQL filter list of allergens to avoid (e.g. ['Đậu phộng', 'Hải sản'])",
    )
    max_budget: Decimal | None = Field(
        default=None,
        ge=0,
        description="Preferred maximum spending per meal",
    )


class UserPreferenceCreate(UserPreferenceBase):
    """Payload to create or initialize preferences."""

    pass


class UserPreferenceUpdate(BaseModel):
    """Partial preference update payload."""

    preferred_categories: list[str] | None = None
    dietary_preference: DietaryPreference | None = None
    excluded_allergens: list[str] | None = None
    max_budget: Decimal | None = Field(default=None, ge=0)


class UserPreferenceResponse(UserPreferenceBase):
    """Output schema for user preference settings."""

    id: uuid.UUID
    user_id: uuid.UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
