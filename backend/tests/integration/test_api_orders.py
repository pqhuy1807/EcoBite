"""Integration tests for rescue-order placement, RBAC and cancellation."""

import re
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from httpx import AsyncClient, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, PaymentMethod

# Full-day pickup window so order placement succeeds at any real test time.
ALL_DAY_WINDOW = {"pickup_start_time": "00:00:00", "pickup_end_time": "23:59:00"}


async def _create_menu_item(client: AsyncClient, store_partner: dict) -> str:
    response = await client.post(
        f"/api/v1/stores/{store_partner['store'].id}/menu-items",
        json={
            "name": "Banh mi trung",
            "category": "BAKERY",
            "original_price": "40000",
            "image_url": "https://cdn.ecobite.vn/banh-mi-trung.jpg",
            "standard_ingredients": ["bread", "egg"],
            "base_allergens": ["gluten", "egg"],
        },
        headers=store_partner["headers"],
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_rescue_dish(
    client: AsyncClient, store_partner: dict, *, total_quantity: int = 4
) -> str:
    """Publish an all-day rescue dish with a fixed override price (time-independent)."""
    menu_item_id = await _create_menu_item(client, store_partner)
    response = await client.post(
        "/api/v1/dishes",
        json={
            "menu_item_id": menu_item_id,
            "total_quantity": total_quantity,
            "override_discounted_price": "15000",
            **ALL_DAY_WINDOW,
        },
        headers=store_partner["headers"],
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _place_order(
    client: AsyncClient,
    headers: dict,
    dish_id: str,
    quantity: int = 1,
) -> Response:
    return await client.post(
        "/api/v1/orders",
        json={"dish_id": dish_id, "quantity": quantity, "payment_method": "COD"},
        headers=headers,
    )


async def _get_dish_stock(client: AsyncClient, store_partner: dict, dish_id: str) -> int:
    listed = await client.get(
        f"/api/v1/stores/{store_partner['store'].id}/dishes/active",
        headers=store_partner["headers"],
    )
    assert listed.status_code == 200
    dish = next(d for d in listed.json()["dishes"] if d["id"] == dish_id)
    return dish["remaining_quantity"]


# ==============================================================================
# 1. POST /api/v1/orders — consumer đặt đơn giải cứu
# ==============================================================================


async def test_consumer_places_order_and_stock_decrements(
    client: AsyncClient, store_partner: dict, consumer: dict
) -> None:
    """201: đơn lưu đúng giá/CO2/Điểm Xanh và tồn kho món bị trừ đúng số suất."""
    dish_id = await _create_rescue_dish(client, store_partner)

    response = await _place_order(client, consumer["headers"], dish_id, quantity=2)

    assert response.status_code == 201
    body = response.json()
    assert re.fullmatch(r"EB-\d{8}-[0-9A-F]{8}", body["order_code"])
    assert body["status"] == "CONFIRMED"
    assert body["payment_status"] == "PENDING"
    assert body["payment_method"] == "COD"
    assert body["quantity"] == 2
    assert body["unit_price"] == "15000.00"
    assert body["total_amount"] == "30000.00"
    # Tác động xanh: 2 suất × 2.5 kg CO2e = 5 kg → 50 Điểm Xanh
    assert Decimal(body["co2_saved_kg"]) == Decimal("5.00")
    assert body["green_points_earned"] == 50

    assert await _get_dish_stock(client, store_partner, dish_id) == 2


async def test_order_with_insufficient_stock_returns_409(
    client: AsyncClient, store_partner: dict, consumer: dict
) -> None:
    """409: đặt vượt tồn kho bị chặn và remaining_quantity không bao giờ bị âm."""
    dish_id = await _create_rescue_dish(client, store_partner, total_quantity=1)

    response = await _place_order(client, consumer["headers"], dish_id, quantity=2)

    assert response.status_code == 409
    assert response.json()["detail"] == "Món ăn đã hết suất hoặc số lượng còn lại không đủ"
    assert await _get_dish_stock(client, store_partner, dish_id) == 1


async def test_store_partner_cannot_place_rescue_order(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """403: STORE_PARTNER không được phép đặt đơn giải cứu."""
    dish_id = await _create_rescue_dish(client, store_partner)

    response = await _place_order(client, store_partner["headers"], dish_id, quantity=1)

    assert response.status_code == 403
    assert response.json()["detail"] == "The user does not have the required role"
    total_orders = await db_session.scalar(select(func.count()).select_from(Order))
    assert total_orders == 0


# ==============================================================================
# 2. PATCH /api/v1/orders/{order_id}/cancel — hủy đơn & hoàn kho
# ==============================================================================


async def test_consumer_can_cancel_own_order_before_deadline(
    client: AsyncClient, store_partner: dict, consumer: dict
) -> None:
    """200: chủ đơn (CONSUMER) hủy khi chưa quá hạn → CANCELLED và hoàn đủ kho."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=3)
    assert created.status_code == 201
    order_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/orders/{order_id}/cancel",
        headers=consumer["headers"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == order_id
    assert body["status"] == "CANCELLED"
    assert await _get_dish_stock(client, store_partner, dish_id) == 4  # hoàn đủ 3 suất


async def test_store_partner_can_cancel_order_for_their_store(
    client: AsyncClient, store_partner: dict, consumer: dict
) -> None:
    """200: chủ cửa hàng bán món (STORE_PARTNER) cũng được hủy đơn của quán mình."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=2)
    assert created.status_code == 201
    order_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/orders/{order_id}/cancel",
        headers=store_partner["headers"],
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert await _get_dish_stock(client, store_partner, dish_id) == 4  # hoàn đủ 2 suất


async def test_cancel_after_pickup_deadline_returns_409(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """409: đã quá hạn chót lấy món thì endpoint chặn hủy và giữ nguyên trạng thái."""
    dish_id = await _create_rescue_dish(client, store_partner)
    order = Order(
        order_code="EB-20260101-DEADBEEF",
        consumer_id=consumer["user"].id,
        store_id=store_partner["store"].id,
        dish_id=uuid.UUID(dish_id),
        quantity=1,
        unit_price=Decimal("15000.00"),
        total_amount=Decimal("15000.00"),
        payment_method=PaymentMethod.COD,
        co2_saved_kg=Decimal("2.50"),
        green_points_earned=25,
        pickup_deadline=datetime.now() - timedelta(days=1),
    )
    db_session.add(order)
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/orders/{order.id}/cancel",
        headers=consumer["headers"],
    )

    assert response.status_code == 409
    assert "quá hạn" in response.json()["detail"]
    await db_session.refresh(order)
    assert order.status == OrderStatus.CONFIRMED  # không bị chuyển CANCELLED
