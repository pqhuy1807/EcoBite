"""Unit tests for deterministic surplus-dish discount rules."""

import uuid
from datetime import time
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.dish import Dish
from app.models.menu_item import ItemCategory, MenuItem
from app.models.store import KycStatus
from app.services.dish_service import DishService


async def _create_menu_item(db_session, store) -> MenuItem:
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


async def test_dish_service_rejects_missing_menu_item(db_session) -> None:
    with pytest.raises(HTTPException) as error:
        await DishService(db_session).create_surplus_dish(uuid.uuid4(), {})

    assert error.value.status_code == 404


async def test_dish_service_rejects_unapproved_store(store_partner, db_session) -> None:
    store = store_partner["store"]
    item = await _create_menu_item(db_session, store)
    store.kyc_status = KycStatus.PENDING
    await db_session.commit()

    with pytest.raises(HTTPException) as error:
        await DishService(db_session).create_surplus_dish(item.id, {})

    assert error.value.status_code == 403


async def test_dish_service_validates_window_and_override(store_partner, db_session) -> None:
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
    store_partner, other_store_partner, db_session
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
    store_partner, db_session
) -> None:
    item = await _create_menu_item(db_session, store_partner["store"])
    service = DishService(db_session)
    window = {"pickup_start_time": time(14), "pickup_end_time": time(15)}

    created = await service.create_surplus_dish(
        item.id, {**window, "total_quantity": 3}
    )
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
    store_partner, db_session
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
