"""Unit tests for deterministic surplus-dish discount rules and inventory repository."""

import uuid
from datetime import datetime, time
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import ItemCategory, MenuItem
from app.models.store import KycStatus
from app.models.user import UserRole
from app.repositories import dish_repo, store_repo, user_repo
from app.services.dish_service import DishService


async def _create_menu_item(db_session: AsyncSession, store) -> MenuItem:
    item = MenuItem(
        store_id=store.id,
        name="Com tam",
        category=ItemCategory.RICE,
        original_price=Decimal("45000"),
        image_url="https://cdn.ecobite.vn/com-tam.jpg",
        standard_ingredients=["rice"],
        base_allergens=[],
    )
    db_session.add(item)
    await db_session.commit()
    return item


def test_time_shift_standard_window_50_percent_discount() -> None:
    """Trong khung giờ vàng tiêu chuẩn, món ăn giảm 50% và cờ giờ chót bằng False."""
    current_price, rule_price, is_rush = DishService.calculate_time_shifted_discount(
        original_price=50000.0,
        pickup_start_time=time(14, 0),
        pickup_end_time=time(16, 0),
        current_time=datetime(2026, 11, 7, 14, 30),
    )

    assert current_price == 25000.0
    assert rule_price == 15000.0
    assert is_rush is False


def test_time_shift_final_rush_70_percent_discount() -> None:
    """Trong 45 phút cuối trước pickup_end_time, tự động giảm 70% và bật cờ giờ chót."""
    current_price, rule_price, is_rush = DishService.calculate_time_shifted_discount(
        original_price=50000.0,
        pickup_start_time=time(14, 0),
        pickup_end_time=time(16, 0),
        current_time=datetime(2026, 11, 7, 15, 30),
    )

    assert current_price == 15000.0
    assert rule_price == 15000.0
    assert is_rush is True


def test_time_shift_manual_override_takes_precedence() -> None:
    """Khi chủ quán đặt giá xả đồng giá thủ công, ưu tiên mức giá override."""
    current_price, rule_price, is_rush = DishService.calculate_time_shifted_discount(
        original_price=50000.0,
        pickup_start_time=time(14, 0),
        pickup_end_time=time(16, 0),
        override_discounted_price=18000.0,
        current_time=datetime(2026, 11, 7, 15, 40),
    )

    assert current_price == 18000.0
    assert rule_price == 15000.0
    assert is_rush is False


def test_countdown_to_final_rush() -> None:
    """Tính chính xác số giây đếm ngược trước khi bước vào 45 phút giờ chót."""
    remaining = DishService.get_countdown_to_final_rush(
        pickup_end_time=time(16, 0),
        current_time=datetime(2026, 11, 7, 15, 0, 0),
        rush_window_minutes=45,
    )
    assert remaining == 15 * 60

    expired_or_in_rush = DishService.get_countdown_to_final_rush(
        pickup_end_time=time(16, 0),
        current_time=datetime(2026, 11, 7, 15, 30, 0),
        rush_window_minutes=45,
    )
    assert expired_or_in_rush == 0


@pytest.mark.asyncio
async def test_dish_repo_atomic_decrement_prevents_overselling(
    db_session: AsyncSession,
) -> None:
    """Kiểm tra Guardrail #4: Atomic Decrement ngăn chặn bán vượt tồn kho."""
    partner = await user_repo.create(
        db_session,
        email="partner_atomic@ecobite.vn",
        hashed_password="hashed_password",
        full_name="Partner Atomic",
        role=UserRole.STORE_PARTNER,
    )
    store = await store_repo.create(
        db_session,
        owner_id=partner.id,
        name="Quán Cơm Atomic",
        description=None,
        address="123 Nguyễn Văn Cừ, Q.5",
        phone="0909000111",
        avatar_url=None,
        kyc_license_url=None,
        latitude=10.762622,
        longitude=106.682333,
    )

    dish = Dish(
        id=uuid.uuid4(),
        store_id=store.id,
        name="Cơm sườn nướng",
        category=ItemCategory.RICE,
        original_price=Decimal("50000"),
        rescue_price=Decimal("25000"),
        rule_discount_price=Decimal("15000"),
        pickup_start_time=time(14, 0),
        pickup_end_time=time(16, 0),
        total_quantity=2,
        remaining_quantity=2,
        status=DishStatus.ACTIVE,
    )
    await dish_repo.create(db_session, dish)

    # Lần mua 1: Mua 3 suất khi chỉ còn 2 -> Phải bị từ chối (None)
    failed = await dish_repo.atomic_decrement_quantity(db_session, dish.id, 3)
    assert failed is None

    # Lần mua 2: Mua đúng 2 suất còn lại -> Thành công và chuyển sang SOLD_OUT
    succeeded = await dish_repo.atomic_decrement_quantity(db_session, dish.id, 2)
    assert succeeded is not None
    assert succeeded.remaining_quantity == 0
    assert succeeded.status == DishStatus.SOLD_OUT


def test_standard_rescue_window_applies_fifty_percent_discount() -> None:
    current_price, rush_price, rush_active = DishService.calculate_time_shifted_discount(
        Decimal("45000"),
        time(14),
        time(15),
        current_time=time(14, 10),
    )

    assert current_price == Decimal("2.25E+4")
    assert rush_price == Decimal("1.35E+4")
    assert rush_active is False


def test_final_45_minute_window_applies_seventy_percent_discount() -> None:
    current_price, rush_price, rush_active = DishService.calculate_time_shifted_discount(
        Decimal("45000"),
        time(14),
        time(15),
        current_time=time(14, 30),
    )

    assert current_price == Decimal("1.35E+4")
    assert rush_price == Decimal("1.35E+4")
    assert rush_active is True


def test_override_price_is_used_without_enabling_rule_discount() -> None:
    current_price, rush_price, rush_active = DishService.calculate_time_shifted_discount(
        Decimal("45000"),
        time(14),
        time(15),
        override_discounted_price=Decimal("20000"),
        current_time=time(14, 30),
    )

    assert current_price == Decimal("20000")
    assert rush_price == Decimal("1.35E+4")
    assert rush_active is False


def test_override_price_above_original_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        DishService.calculate_time_shifted_discount(
            Decimal("45000"),
            time(14),
            time(15),
            override_discounted_price=Decimal("50000"),
        )

    assert error.value.status_code == 422


async def test_dish_service_rejects_missing_menu_item(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as error:
        await DishService(db_session).create_surplus_dish(uuid.uuid4(), {})

    assert error.value.status_code == 404


async def test_dish_service_rejects_unapproved_store(
    store_partner, db_session: AsyncSession
) -> None:
    store = store_partner["store"]
    item = await _create_menu_item(db_session, store)
    store.kyc_status = KycStatus.PENDING
    await db_session.commit()

    with pytest.raises(HTTPException) as error:
        await DishService(db_session).create_surplus_dish(item.id, {})

    assert error.value.status_code == 403


async def test_dish_service_validates_window_and_override(
    store_partner, db_session: AsyncSession
) -> None:
    item = await _create_menu_item(db_session, store_partner["store"])
    service = DishService(db_session)

    with pytest.raises(HTTPException) as invalid_window:
        await service.create_surplus_dish(
            item.id,
            {
                "pickup_start_time": time(15),
                "pickup_end_time": time(14),
                "total_quantity": 1,
            },
        )
    with pytest.raises(HTTPException) as invalid_override:
        await service.create_surplus_dish(
            item.id,
            {
                "pickup_start_time": time(14),
                "pickup_end_time": time(15),
                "total_quantity": 1,
                "override_discounted_price": Decimal("50000"),
            },
        )

    assert invalid_window.value.status_code == 422
    assert invalid_override.value.status_code == 422


async def test_dish_service_rejects_cross_store_batch(
    store_partner, other_store_partner, db_session: AsyncSession
) -> None:
    first_item = await _create_menu_item(db_session, store_partner["store"])
    second_item = await _create_menu_item(db_session, other_store_partner["store"])

    with pytest.raises(HTTPException) as error:
        await DishService(db_session).batch_create_dishes(
            [
                {"menu_item_id": first_item.id, "quantity": 2},
                {"menu_item_id": second_item.id, "quantity": 1},
            ],
            time(14),
            time(15),
        )

    assert error.value.status_code == 422


async def test_dish_service_persists_and_lists_single_and_batch_dishes(
    store_partner, db_session: AsyncSession
) -> None:
    item = await _create_menu_item(db_session, store_partner["store"])
    service = DishService(db_session)
    window = {"pickup_start_time": time(14), "pickup_end_time": time(15)}

    created = await service.create_surplus_dish(item.id, {**window, "total_quantity": 3})
    created_with_remaining = await service.create_surplus_dish(
        item.id, {**window, "total_quantity": 5, "remaining_quantity": 2}
    )
    created_sold_out = await service.create_surplus_dish(
        item.id, {**window, "total_quantity": 5, "remaining_quantity": 0}
    )
    active = await service.get_active_store_dishes(store_partner["store"].id)
    update = await service.update_dish_quantity(created["id"], 0)
    batch = await service.batch_create_dishes(
        [{"menu_item_id": item.id, "quantity": 2}],
        time(14),
        time(15),
    )

    assert created_with_remaining["remaining_quantity"] == 2
    assert created_sold_out["status"] == "SOLD_OUT"
    assert any(d["id"] == created["id"] and d["remaining_quantity"] == 3 for d in active)
    assert update["remaining_quantity"] == 0
    assert batch[0]["remaining_quantity"] == 2


async def test_dish_service_rejects_missing_dish_and_excess_quantity(
    store_partner, db_session: AsyncSession
) -> None:
    service = DishService(db_session)
    with pytest.raises(HTTPException) as missing:
        await service.update_dish_quantity(uuid.uuid4(), 0)
    assert missing.value.status_code == 404

    dish = Dish(
        store_id=store_partner["store"].id,
        name="Direct test dish",
        category=ItemCategory.RICE,
        original_price=Decimal("100"),
        rescue_price=Decimal("50"),
        pickup_start_time=time(14),
        pickup_end_time=time(15),
        total_quantity=1,
        remaining_quantity=1,
    )
    db_session.add(dish)
    await db_session.flush()
    with pytest.raises(HTTPException) as excess:
        await service.update_dish_quantity(dish.id, 2)

    assert excess.value.status_code == 422
