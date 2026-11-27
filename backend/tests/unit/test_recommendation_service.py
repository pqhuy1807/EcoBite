"""Unit tests for RecommendationService (AI Feature 2 baseline)."""

from datetime import time
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import DietaryType, ItemCategory
from app.models.store import KycStatus, Store
from app.models.user import DietaryPreference, User, UserPreference, UserRole
from app.repositories import preference_repo
from app.services.recommendation_service import RecommendationService


class _FakeGeminiResponse:
    """Stand-in for a google-genai response carrying a parsed Pydantic model."""

    def __init__(self, parsed: object) -> None:
        self.parsed = parsed
        self.text = None


class _FakeGeminiClient:
    """Duck-typed Gemini client for unit tests."""

    def __init__(
        self,
        *,
        parsed: object | None = None,
        exc: Exception | None = None,
    ) -> None:
        self._parsed = parsed
        self._exc = exc

    async def generate_content(self, *, model: str, contents: str, config: Any) -> Any:  # noqa: ANN401
        if self._exc is not None:
            raise self._exc
        return _FakeGeminiResponse(self._parsed)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


async def _create_user(
    db: AsyncSession, *, email: str, role: UserRole = UserRole.CONSUMER
) -> User:
    user = User(
        email=email,
        hashed_password="not-used",
        full_name="Test User",
        role=role,
    )
    db.add(user)
    await db.flush()
    return user


async def _create_store(
    db: AsyncSession, *, owner: User, lat: float, lng: float
) -> Store:
    from app.repositories.store_repo import format_point_wkt

    store = Store(
        owner_id=owner.id,
        name="Test Store",
        address="123 Test Street",
        location=format_point_wkt(longitude=lng, latitude=lat),
        kyc_status=KycStatus.APPROVED,
    )
    db.add(store)
    await db.flush()
    return store


async def _create_dish(
    db: AsyncSession,
    *,
    store: Store,
    name: str,
    category: ItemCategory = ItemCategory.RICE,
    original_price: Decimal = Decimal("50000"),
    remaining_quantity: int = 5,
    status: DishStatus = DishStatus.ACTIVE,
    allergens: list[dict] | None = None,
    pickup_end: time | None = None,
    rescue_price: Decimal | None = None,
    rule_discount_price: Decimal | None = None,
    override_discounted_price: Decimal | None = None,
    dietary_type: DietaryType = DietaryType.NON_VEGAN,
) -> Dish:
    pickup_end = pickup_end or time(23, 59)
    dish = Dish(
        store_id=store.id,
        name=name,
        category=category,
        original_price=original_price,
        rescue_price=rescue_price or original_price * Decimal("0.5"),
        rule_discount_price=rule_discount_price,
        override_discounted_price=override_discounted_price,
        pickup_start_time=time(10, 0),
        pickup_end_time=pickup_end,
        total_quantity=remaining_quantity,
        remaining_quantity=remaining_quantity,
        status=status,
        allergens=allergens or [],
        dietary_type=dietary_type,
    )
    db.add(dish)
    await db.flush()
    return dish


async def _set_preference(
    db: AsyncSession,
    *,
    user: User,
    excluded_allergens: list[str] | None = None,
    preferred_categories: list[str] | None = None,
    dietary_preference: DietaryPreference = DietaryPreference.NONE,
) -> UserPreference:
    return await preference_repo.create_or_update(
        db,
        user.id,
        excluded_allergens=excluded_allergens,
        preferred_categories=preferred_categories,
        dietary_preference=dietary_preference,
    )


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_personalized_excludes_allergens(db_session: AsyncSession) -> None:
    """0 % of dishes whose allergens intersect excluded_allergens may appear."""
    user = await _create_user(db_session, email="allergen-test@ecobite.vn")
    store = await _create_store(db_session, owner=user, lat=10.77, lng=106.70)
    await _set_preference(
        db_session, user=user, excluded_allergens=["PEANUTS"]
    )

    safe = await _create_dish(
        db_session,
        store=store,
        name="Com bo",
        category=ItemCategory.RICE,
        allergens=[{"allergen": "Gluten", "risk_level": "MEDIUM", "source": "INFERRED"}],
    )
    unsafe = await _create_dish(
        db_session,
        store=store,
        name="Goi cuon dau phong",
        category=ItemCategory.RICE,
        allergens=[{"allergen": "Peanuts (Dau phong)", "risk_level": "HIGH", "source": "EXPLICIT"}],
    )

    service = RecommendationService(db_session)
    result = await service.get_personalized(
        user_id=str(user.id), lat=10.77, lng=106.70, radius_km=3.0, top_k=3
    )

    kept_names = {item["name"] for item in result["items"]}
    assert safe.name in kept_names
    assert unsafe.name not in kept_names
    assert result["total"] == 1


@pytest.mark.asyncio
async def test_get_personalized_scoring_and_top_k(db_session: AsyncSession) -> None:
    """Heuristic score is computed and Top-K ranking is respected."""
    user = await _create_user(db_session, email="score-test@ecobite.vn")
    store = await _create_store(db_session, owner=user, lat=10.77, lng=106.70)
    await _set_preference(
        db_session, user=user, preferred_categories=[ItemCategory.RICE.value]
    )

    await _create_dish(
        db_session,
        store=store,
        name="Com near",
        category=ItemCategory.RICE,
        override_discounted_price=Decimal("10000"),
    )
    # Farther away (different store, still within 3 km) -> lower proximity score.
    far_store = await _create_store(db_session, owner=user, lat=10.78, lng=106.71)
    await _create_dish(
        db_session,
        store=far_store,
        name="Com far",
        category=ItemCategory.RICE,
        original_price=Decimal("50000"),
    )

    service = RecommendationService(db_session)
    result = await service.get_personalized(
        user_id=str(user.id), lat=10.77, lng=106.70, radius_km=3.0, top_k=2
    )

    assert len(result["items"]) == 2
    # nearest/highest discount first.
    assert result["items"][0]["name"] == "Com near"
    assert result["items"][1]["name"] == "Com far"
    # Every item carries a breakdown and a non-empty justification.
    for item in result["items"]:
        assert set(item["breakdown"]) == {
            "proximity",
            "discount_urgency",
            "taste_match",
            "rush_active",
        }
        assert item["ai_justification"]


@pytest.mark.asyncio
async def test_get_personalized_gemini_fallback_on_error(db_session: AsyncSession) -> None:
    """Gemini error/timeout must not crash the endpoint; template fallback used."""
    user = await _create_user(db_session, email="fallback-test@ecobite.vn")
    store = await _create_store(db_session, owner=user, lat=10.77, lng=106.70)
    await _set_preference(db_session, user=user)

    dish = await _create_dish(db_session, store=store, name="Com fallback")

    # Gemini client that raises a timeout.
    service = RecommendationService(
        db_session,
        gemini_client=_FakeGeminiClient(exc=TimeoutError("Gemini timed out")),
    )
    result = await service.get_personalized(
        user_id=str(user.id), lat=10.77, lng=106.70, radius_km=3.0, top_k=3
    )

    assert len(result["items"]) == 1
    assert result["items"][0]["name"] == "Com fallback"
    assert result["items"][0]["ai_justification"]
    assert "Com fallback" in result["items"][0]["ai_justification"]


@pytest.mark.asyncio
async def test_get_personalized_gemini_invalid_schema_fallback(db_session: AsyncSession) -> None:
    """Gemini returning a non-JustificationBatch payload falls back safely."""
    user = await _create_user(db_session, email="schema-test@ecobite.vn")
    store = await _create_store(db_session, owner=user, lat=10.77, lng=106.70)
    await _set_preference(db_session, user=user)
    dish = await _create_dish(db_session, store=store, name="Com schema")

    # Return a valid-shaped but wrong-type parsed object.
    service = RecommendationService(
        db_session,
        gemini_client=_FakeGeminiClient(parsed={"not": "a batch"}),
    )
    result = await service.get_personalized(
        user_id=str(user.id), lat=10.77, lng=106.70, radius_km=3.0, top_k=3
    )

    assert len(result["items"]) == 1
    assert result["items"][0]["ai_justification"]


@pytest.mark.asyncio
async def test_normalize_excluded_allergens_canonical_keys() -> None:
    """Raw allergen inputs normalize to EUAllergen canonical keys."""
    from app.repositories.preference_repo import normalize_excluded_allergens

    assert normalize_excluded_allergens(["Dau phong", "PEANUTS", "Peanuts (Dau phong)"]) == [
        "PEANUTS"
    ]
    assert normalize_excluded_allergens(["Hai san", "CRUSTACEANS"]) == ["CRUSTACEANS"]
    assert normalize_excluded_allergens([]) == []
    assert normalize_excluded_allergens(["Unknown allergen"]) == []
