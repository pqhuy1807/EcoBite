"""Integration tests for AI Feature 2 recommendation endpoints."""

from datetime import time
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.dish import Dish, DishStatus
from app.models.menu_item import DietaryType, ItemCategory
from app.models.store import KycStatus, Store
from app.models.user import UserRole
from app.repositories import preference_repo
from app.repositories.store_repo import format_point_wkt


async def _seed_consumer_with_dishes(
    db_session: Any,
    *,
    excluded_allergens: list[str] | None = None,
) -> dict[str, Any]:
    """Create a consumer, an approved store and two dishes (one unsafe allergen)."""
    from app.models.user import User

    consumer = User(
        email=f"{uuid4().hex[:8]}@ecobite.vn",
        hashed_password="not-used",
        full_name="Consumer",
        role=UserRole.CONSUMER,
    )
    db_session.add(consumer)
    await db_session.flush()

    store = Store(
        owner_id=consumer.id,
        name="Test Store",
        address="123 Test Street",
        location=format_point_wkt(longitude=106.70, latitude=10.77),
        kyc_status=KycStatus.APPROVED,
    )
    db_session.add(store)
    await db_session.flush()

    safe = Dish(
        store_id=store.id,
        name="Com bo an toan",
        category=ItemCategory.RICE,
        original_price=Decimal("50000"),
        rescue_price=Decimal("25000"),
        pickup_start_time=time(10, 0),
        pickup_end_time=time(23, 59),
        total_quantity=5,
        remaining_quantity=5,
        status=DishStatus.ACTIVE,
        allergens=[
            {
                "allergen": "Gluten",
                "risk_level": "MEDIUM",
                "source": "INFERRED",
                "reason": "Co bot mi",
            }
        ],
        dietary_type=DietaryType.NON_VEGAN,
    )
    unsafe = Dish(
        store_id=store.id,
        name="Goi cuon dau phong",
        category=ItemCategory.RICE,
        original_price=Decimal("40000"),
        rescue_price=Decimal("20000"),
        pickup_start_time=time(10, 0),
        pickup_end_time=time(23, 59),
        total_quantity=5,
        remaining_quantity=5,
        status=DishStatus.ACTIVE,
        allergens=[
            {
                "allergen": "Peanuts (Dau phong)",
                "risk_level": "HIGH",
                "source": "EXPLICIT",
                "reason": "Co dau phong",
            }
        ],
        dietary_type=DietaryType.NON_VEGAN,
    )
    db_session.add_all([safe, unsafe])
    await db_session.commit()

    return {
        "consumer_id": str(consumer.id),
        "store_id": str(store.id),
        "safe_name": safe.name,
        "unsafe_name": unsafe.name,
    }


# --------------------------------------------------------------------------- #
# Preference CRUD
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_preferences_returns_defaults_when_none(
    client: AsyncClient, consumer: dict[str, object], db_session: Any
) -> None:
    response = await client.get("/api/v1/users/me/preferences", headers=consumer["headers"])
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(consumer["user"].id)
    assert body["excluded_allergens"] == []
    assert body["dietary_preference"] == "NONE"


@pytest.mark.asyncio
async def test_put_and_get_preferences_normalizes_allergens(
    client: AsyncClient, consumer: dict[str, object], db_session: Any
) -> None:
    response = await client.put(
        "/api/v1/users/me/preferences",
        headers=consumer["headers"],
        params={
            "excluded_allergens": ["dau phong", "PEANUTS", "Hai san"],
            "dietary_preference": "VEGAN",
            "preferred_categories": ["RICE"],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    # Canonical EUAllergen keys, duplicates removed.
    assert body["excluded_allergens"] == ["PEANUTS", "CRUSTACEANS"]
    assert body["dietary_preference"] == "VEGAN"
    assert body["preferred_categories"] == ["RICE"]

    get_resp = await client.get("/api/v1/users/me/preferences", headers=consumer["headers"])
    assert get_resp.status_code == 200
    assert get_resp.json()["excluded_allergens"] == ["PEANUTS", "CRUSTACEANS"]


# --------------------------------------------------------------------------- #
# Personalized recommendations
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_personalized_excludes_allergens_and_ranks(
    client: AsyncClient,
    consumer: dict[str, object],
    db_session: Any,
) -> None:
    seeded = await _seed_consumer_with_dishes(db_session)
    # Set preference for the *requesting* consumer (fixture user), not the
    # seed-created user — the endpoint resolves preferences from the JWT sub.
    await preference_repo.create_or_update(
        db_session,
        consumer["user"].id,
        excluded_allergens=["PEANUTS"],
    )

    response = await client.get(
        "/api/v1/recommendations/personalized",
        headers=consumer["headers"],
        params={"lat": 10.77, "lng": 106.70, "radius_km": 3, "top_k": 3},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    names = {item["name"] for item in body["items"]}
    assert seeded["safe_name"] in names
    assert seeded["unsafe_name"] not in names
    for item in body["items"]:
        assert "ai_justification" in item and item["ai_justification"]
        assert "breakdown" in item


@pytest.mark.asyncio
async def test_personalized_store_partner_forbidden(
    client: AsyncClient, store_partner: dict[str, object]
) -> None:
    response = await client.get(
        "/api/v1/recommendations/personalized",
        headers=store_partner["headers"],
        params={"lat": 10.77, "lng": 106.70, "radius_km": 3},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_personalized_unauthorized(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/recommendations/personalized",
        params={"lat": 10.77, "lng": 106.70, "radius_km": 3},
    )
    assert response.status_code == 401


# --------------------------------------------------------------------------- #
# Semantic dish search
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_semantic_search_excludes_allergens(
    client: AsyncClient,
    consumer: dict[str, object],
    db_session: Any,
) -> None:
    seeded = await _seed_consumer_with_dishes(db_session)
    # Set preference for the *requesting* consumer (fixture user).
    await preference_repo.create_or_update(
        db_session,
        consumer["user"].id,
        excluded_allergens=["PEANUTS"],
    )

    response = await client.post(
        "/api/v1/dishes/search-semantic",
        headers=consumer["headers"],
        json={"query": "com bo", "lat": 10.77, "lng": 106.70, "radius_km": 3},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    names = {item["name"] for item in body["items"]}
    assert seeded["safe_name"] in names
    assert seeded["unsafe_name"] not in names
    assert "extracted_filters" in body


@pytest.mark.asyncio
async def test_semantic_search_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/dishes/search-semantic",
        json={"query": "com bo", "lat": 10.77, "lng": 106.70, "radius_km": 3},
    )
    assert response.status_code == 401
