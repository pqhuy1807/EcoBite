"""Unit tests for DiscoveryService: radar spatial aggregation + surplus dish assembly."""

import uuid
from datetime import time
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import ItemCategory
from app.models.store import KycStatus, Store
from app.models.user import UserRole
from app.repositories import store_repo, user_repo
from app.services.discovery import DiscoveryService

CENTER_LAT, CENTER_LNG = 10.7769, 106.7009

RICE_NAME = "Cơm sườn bì chả (RICE)"
BAKERY_SOLD_OUT_NAME = "Bánh croissant (SOLD_OUT)"
NOODLES_NAME = "Bún bò Huế (NOODLES)"
FAR_RICE_NAME = "Cơm xa thủ đức"


async def _create_approved_store(
    db: AsyncSession,
    suffix: str,
    *,
    latitude: float,
    longitude: float,
) -> Store:
    owner = await user_repo.create(
        db,
        email=f"disc-{suffix}-{uuid.uuid4().hex[:6]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Discovery Owner",
        role=UserRole.STORE_PARTNER,
    )
    return await store_repo.create_store(
        db,
        owner_id=owner.id,
        name=f"Discovery Store {suffix}",
        description=None,
        address="TP.HCM",
        phone=None,
        avatar_url=None,
        kyc_license_url=None,
        latitude=latitude,
        longitude=longitude,
    )


async def _add_dish(
    db: AsyncSession,
    store: Store,
    *,
    name: str,
    category: ItemCategory,
    status: DishStatus = DishStatus.ACTIVE,
    remaining_quantity: int = 2,
) -> Dish:
    dish = Dish(
        store_id=store.id,
        name=name,
        category=category,
        image_url="https://cdn.ecobite.vn/discovery.jpg",
        original_price=Decimal("50000"),
        rescue_price=Decimal("25000"),
        rule_discount_price=Decimal("15000"),
        pickup_start_time=time(14, 0),
        pickup_end_time=time(16, 0),
        total_quantity=5,
        remaining_quantity=remaining_quantity,
        status=status,
    )
    db.add(dish)
    await db.commit()
    return dish


async def _prepare_geo_fixtures(db: AsyncSession) -> tuple[Store, Store, Store]:
    """Quán GẦN (~0.2km, 1 món ACTIVE + 1 món SOLD_OUT + 1 món EXPIRED), TRUNG BÌNH (~1.5km, NOODLES), XA (~15km)."""
    near = await _create_approved_store(db, "near", latitude=10.7755, longitude=106.7015)
    mid = await _create_approved_store(db, "mid", latitude=10.7869, longitude=106.7109)
    far = await _create_approved_store(db, "far", latitude=10.8750, longitude=106.8000)

    await _add_dish(db, near, name=RICE_NAME, category=ItemCategory.RICE)
    await _add_dish(
        db,
        near,
        name=BAKERY_SOLD_OUT_NAME,
        category=ItemCategory.BAKERY,
        remaining_quantity=0,
    )
    await _add_dish(
        db,
        near,
        name="Cơm inactive (EXPIRED)",
        category=ItemCategory.RICE,
        status=DishStatus.EXPIRED,
    )
    await _add_dish(db, mid, name=NOODLES_NAME, category=ItemCategory.NOODLES)
    await _add_dish(db, far, name=FAR_RICE_NAME, category=ItemCategory.RICE)
    return near, mid, far


async def test_nearby_returns_sorted_stores_with_active_dishes(
    db_session: AsyncSession,
) -> None:
    """Radar 3km: chỉ 2 quán trong bán kính, sắp xếp gần -> xa, loại món SOLD_OUT/EXPIRED."""
    near, mid, far = await _prepare_geo_fixtures(db_session)

    result = await DiscoveryService(db_session).search_nearby_stores(
        lat=CENTER_LAT, lng=CENTER_LNG, radius_km=3.0
    )

    assert result["total"] == 2
    assert result["radius_km"] == 3.0
    assert result["user_location"] == {"lat": CENTER_LAT, "lng": CENTER_LNG}
    names = [item["name"] for item in result["results"]]
    assert names == ["Discovery Store near", "Discovery Store mid"]

    near_result = result["results"][0]
    mid_result = result["results"][1]
    assert near_result["distance_meters"] < mid_result["distance_meters"]
    assert near_result["distance_meters"] < 300.0
    dish_names = [d["name"] for d in near_result["dishes"]]
    assert dish_names == [RICE_NAME]  # SOLD_OUT và EXPIRED bị loại


async def test_nearby_lower_radius_excludes_far_and_mid_stores(
    db_session: AsyncSession,
) -> None:
    """Radar 1km: quán ~1.5km bị loại, chỉ còn quán Gần."""
    await _prepare_geo_fixtures(db_session)

    result = await DiscoveryService(db_session).search_nearby_stores(
        lat=CENTER_LAT, lng=CENTER_LNG, radius_km=1.0
    )
    assert result["total"] == 1
    assert result["results"][0]["name"] == "Discovery Store near"


async def test_nearby_category_filter_matches_and_skips_empty_stores(
    db_session: AsyncSession,
) -> None:
    """Lọc category: chỉ trả quán còn món khớp danh mục; quán khổng lồ danh mục bị loại."""
    await _prepare_geo_fixtures(db_session)
    service = DiscoveryService(db_session)

    rice = await service.search_nearby_stores(
        lat=CENTER_LAT, lng=CENTER_LNG, radius_km=3.0, category="RICE"
    )
    assert rice["total"] == 1
    assert rice["results"][0]["name"] == "Discovery Store near"
    assert rice["results"][0]["dishes"][0]["category"] == ItemCategory.RICE.value

    noodles = await service.search_nearby_stores(
        lat=CENTER_LAT, lng=CENTER_LNG, radius_km=3.0, category="NOODLES"
    )
    assert noodles["total"] == 1
    assert noodles["results"][0]["name"] == "Discovery Store mid"

    # Danh mục không món nào khớp (OTHER): cả 2 quán trong bán kính đều bị loại -> total 0
    other = await service.search_nearby_stores(
        lat=CENTER_LAT, lng=CENTER_LNG, radius_km=3.0, category="OTHER"
    )
    assert other["total"] == 0


async def test_nearby_category_filter_is_case_insensitive(
    db_session: AsyncSession,
) -> None:
    await _prepare_geo_fixtures(db_session)

    result = await DiscoveryService(db_session).search_nearby_stores(
        lat=CENTER_LAT, lng=CENTER_LNG, radius_km=3.0, category="rice"
    )
    assert result["total"] == 1


async def test_nearby_rejects_radius_out_of_bounds(db_session: AsyncSession) -> None:
    """SLA bảo vệ: bán kính phải nằm trong 1-10km."""
    service = DiscoveryService(db_session)

    with pytest.raises(HTTPException) as too_small:
        await service.search_nearby_stores(lat=CENTER_LAT, lng=CENTER_LNG, radius_km=0.5)
    assert too_small.value.status_code == 422

    with pytest.raises(HTTPException) as too_large:
        await service.search_nearby_stores(lat=CENTER_LAT, lng=CENTER_LNG, radius_km=10.5)
    assert too_large.value.status_code == 422


async def test_nearby_rejects_unknown_category(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as error:
        await DiscoveryService(db_session).search_nearby_stores(
            lat=CENTER_LAT, lng=CENTER_LNG, radius_km=3.0, category="DIET"
        )
    assert error.value.status_code == 422


async def test_nearby_dish_payload_contains_pricing_fields(db_session: AsyncSession) -> None:
    """Dish trả về kèm giá hiện tại theo rule-based và khung giờ nhận món."""
    await _prepare_geo_fixtures(db_session)

    result = await DiscoveryService(db_session).search_nearby_stores(
        lat=CENTER_LAT, lng=CENTER_LNG, radius_km=3.0, category="RICE"
    )
    dish = result["results"][0]["dishes"][0]
    assert dish["original_price"] == 50000.0
    # Giá hiện tại phụ thuộc thời điểm chạy test: 50% (tiêu chuẩn) hoặc 70% (giờ chót).
    assert dish["current_price"] in (25000.0, 15000.0)
    assert "pickup_window" in dish
    assert dish["remaining_quantity"] >= 1
    assert dish["image_url"].startswith("https://")
