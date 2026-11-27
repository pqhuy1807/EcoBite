"""Pydantic schemas for AI-2 Recommendation endpoints."""

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.menu_item import ItemCategory
from app.models.user import DietaryPreference


class DishRecommendationItem(BaseModel):
    """A single recommended dish with score and justification."""

    id: uuid.UUID
    store_id: uuid.UUID
    store_name: str
    name: str
    category: ItemCategory
    current_price: Decimal | None = None
    original_price: Decimal
    is_rule_discount_active: bool = False
    distance_meters: float
    score: float = Field(..., ge=0.0, le=1.0)
    breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Component scores: proximity, discount_urgency, taste_match",
    )
    ai_justification: str = Field(
        ..., description="Short AI/deterministic reason to order this dish"
    )

    model_config = ConfigDict(from_attributes=True)


class PersonalizedRecommendationResponse(BaseModel):
    """Response for GET /api/v1/recommendations/personalized."""

    items: list[DishRecommendationItem]
    total: int
    user_location: dict[str, float]
    radius_km: float


class SemanticSearchFilter(BaseModel):
    """Structured filters extracted from a natural-language Vietnamese query."""

    max_price: Decimal | None = Field(default=None, ge=0, description="Maximum price in VND")
    categories: list[ItemCategory] = Field(
        default_factory=list, description="Dish categories to include"
    )
    dietary: DietaryPreference | None = Field(
        default=None, description="Dietary constraint from the query"
    )
    keywords: list[str] = Field(
        default_factory=list, description="Keywords to match against dish name/description"
    )


class SemanticSearchRequest(BaseModel):
    """Request payload for POST /api/v1/dishes/search-semantic."""

    query: str = Field(..., min_length=1, description="Natural-language Vietnamese query")
    lat: float = Field(..., ge=-90.0, le=90.0, description="User latitude")
    lng: float = Field(..., ge=-180.0, le=180.0, description="User longitude")
    radius_km: float = Field(default=3.0, ge=1.0, le=10.0, description="Search radius in km")


class SemanticSearchResponse(BaseModel):
    """Response for POST /api/v1/dishes/search-semantic."""

    items: list[DishRecommendationItem]
    total: int
    extracted_filters: SemanticSearchFilter
