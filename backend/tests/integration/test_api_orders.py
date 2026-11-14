"""Integration tests for rescue-order placement, RBAC and cancellation."""

import asyncio
import re
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import create_access_token
from app.models.order import Order, OrderStatus, PaymentMethod, QRToken
from app.models.user import User, UserRole
from app.services.qr_service import QRService

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


# ==============================================================================
# 3. GET /api/v1/orders/me — lịch sử đơn hàng cá nhân, phân trang & lọc status
# ==============================================================================


async def _create_user_with_headers(
    db_session: AsyncSession,
    *,
    role: UserRole,
) -> tuple[User, dict[str, str]]:
    """Persist an arbitrary-role user and return (user, Authorization headers)."""
    suffix = uuid.uuid4().hex[:8]
    user = User(
        email=f"{role.value}-{suffix}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name=f"User {role.value}",
        role=role,
    )
    db_session.add(user)
    await db_session.commit()
    return user, {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def test_consumer_gets_own_orders_with_pagination_and_status_filter(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """200: consumer chỉ xem đơn của mình, hỗ trợ phân trang (skip/limit) và lọc status."""
    dish_id = await _create_rescue_dish(client, store_partner, total_quantity=10)
    _, other_consumer_headers = await _create_user_with_headers(db_session, role=UserRole.CONSUMER)

    base_time = datetime(2026, 11, 12, 8, 0, tzinfo=UTC)
    created_ids: list[str] = []
    for idx in range(3):
        resp = await _place_order(client, consumer["headers"], dish_id, quantity=1)
        assert resp.status_code == 201
        oid = resp.json()["id"]
        created_ids.append(oid)
        db_order = await db_session.get(Order, uuid.UUID(oid))
        assert db_order is not None
        db_order.created_at = base_time + timedelta(minutes=idx)
    await db_session.commit()

    # Hủy đơn thứ 2 (index 1) để kiểm thử lọc theo status
    cancel_resp = await client.patch(
        f"/api/v1/orders/{created_ids[1]}/cancel",
        headers=consumer["headers"],
    )
    assert cancel_resp.status_code == 200

    # Tạo đơn của consumer khác để xác nhận không bị rò rỉ sang /orders/me
    other_order = await _place_order(client, other_consumer_headers, dish_id, quantity=1)
    assert other_order.status_code == 201
    other_order_id = other_order.json()["id"]

    # Lấy tất cả đơn của consumer hiện tại (mới nhất trước: index 2 -> 1 -> 0)
    all_resp = await client.get("/api/v1/orders/me", headers=consumer["headers"])
    assert all_resp.status_code == 200
    all_items = all_resp.json()
    assert [item["id"] for item in all_items] == [created_ids[2], created_ids[1], created_ids[0]]
    assert all(item["id"] != other_order_id for item in all_items)

    # Phân trang: skip=1, limit=1 -> đúng đơn ở giữa
    page_resp = await client.get("/api/v1/orders/me?skip=1&limit=1", headers=consumer["headers"])
    assert page_resp.status_code == 200
    assert [item["id"] for item in page_resp.json()] == [created_ids[1]]

    # Lọc theo status=CANCELLED
    cancelled_resp = await client.get(
        "/api/v1/orders/me?status=CANCELLED",
        headers=consumer["headers"],
    )
    assert cancelled_resp.status_code == 200
    assert [item["id"] for item in cancelled_resp.json()] == [created_ids[1]]

    # Lọc theo status=CONFIRMED
    confirmed_resp = await client.get(
        "/api/v1/orders/me?status=CONFIRMED",
        headers=consumer["headers"],
    )
    assert confirmed_resp.status_code == 200
    assert [item["id"] for item in confirmed_resp.json()] == [created_ids[2], created_ids[0]]


async def test_orders_me_requires_authentication_and_consumer_role(
    client: AsyncClient,
    store_partner: dict,
    db_session: AsyncSession,
) -> None:
    """401 khi thiếu token; 403 khi STORE_PARTNER hoặc ADMIN gọi /orders/me."""
    unauth = await client.get("/api/v1/orders/me")
    assert unauth.status_code == 401

    partner_resp = await client.get("/api/v1/orders/me", headers=store_partner["headers"])
    assert partner_resp.status_code == 403

    _, admin_headers = await _create_user_with_headers(db_session, role=UserRole.ADMIN)
    admin_resp = await client.get("/api/v1/orders/me", headers=admin_headers)
    assert admin_resp.status_code == 403


# ==============================================================================
# 4. GET /api/v1/orders/{order_id} — chi tiết đơn hàng, QR token hợp lệ & RBAC
# ==============================================================================


async def test_get_order_detail_includes_valid_qr_token_for_owner(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """200: chủ đơn xem chi tiết kèm QRTokenResponse khi QR còn hạn và chưa dùng."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    assert created.status_code == 201
    order_id = uuid.UUID(created.json()["id"])

    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    # Đảm bảo deadline còn ở tương lai xa so với đồng hồ thực của hệ thống
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    await QRService(db_session).generate_order_qr_token(
        order_id=db_order.id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )

    detail_resp = await client.get(f"/api/v1/orders/{order_id}", headers=consumer["headers"])
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert body["id"] == str(order_id)
    assert body["order_code"] == db_order.order_code
    assert body["qr_token"] is not None
    assert body["qr_token"]["order_id"] == str(order_id)
    assert body["qr_token"]["is_used"] is False


async def test_get_order_detail_omits_used_or_expired_qr_token(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """QR đã sử dụng hoặc đã hết hạn không được trả như QR hợp lệ (qr_token=None)."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    assert created.status_code == 201
    order_id = uuid.UUID(created.json()["id"])

    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    qr_token = QRToken(
        order_id=db_order.id,
        token_hash="a" * 64,
        nonce="b" * 32,
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
        is_used=False,
    )
    db_session.add(qr_token)
    await db_session.commit()

    expired_resp = await client.get(f"/api/v1/orders/{order_id}", headers=consumer["headers"])
    assert expired_resp.status_code == 200
    assert expired_resp.json()["qr_token"] is None

    qr_token.expires_at = datetime.now(UTC) + timedelta(hours=1)
    qr_token.is_used = True
    await db_session.commit()

    used_resp = await client.get(f"/api/v1/orders/{order_id}", headers=consumer["headers"])
    assert used_resp.status_code == 200
    assert used_resp.json()["qr_token"] is None


async def test_get_order_detail_rbac_and_404(
    client: AsyncClient,
    store_partner: dict,
    other_store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """Kiểm tra phân quyền xem chi tiết đơn và 404 khi order không tồn tại."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    assert created.status_code == 201
    order_id = created.json()["id"]

    # Store Partner chủ quán & Admin được xem (200)
    owner_resp = await client.get(f"/api/v1/orders/{order_id}", headers=store_partner["headers"])
    assert owner_resp.status_code == 200

    _, admin_headers = await _create_user_with_headers(db_session, role=UserRole.ADMIN)
    admin_resp = await client.get(f"/api/v1/orders/{order_id}", headers=admin_headers)
    assert admin_resp.status_code == 200

    # Consumer khác & Store Partner quán khác bị chặn (403)
    _, other_consumer_headers = await _create_user_with_headers(db_session, role=UserRole.CONSUMER)
    other_consumer_resp = await client.get(
        f"/api/v1/orders/{order_id}", headers=other_consumer_headers
    )
    assert other_consumer_resp.status_code == 403

    other_partner_resp = await client.get(
        f"/api/v1/orders/{order_id}", headers=other_store_partner["headers"]
    )
    assert other_partner_resp.status_code == 403

    # Thiếu token -> 401; không tồn tại -> 404
    unauth = await client.get(f"/api/v1/orders/{order_id}")
    assert unauth.status_code == 401

    missing_resp = await client.get(
        f"/api/v1/orders/{uuid.uuid4()}",
        headers=consumer["headers"],
    )
    assert missing_resp.status_code == 404


# ==============================================================================
# 5. GET /api/v1/orders/store/{store_id} — danh sách đơn của cửa hàng
# ==============================================================================


async def test_store_partner_gets_own_store_orders_with_filter_and_pagination(
    client: AsyncClient,
    store_partner: dict,
    other_store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """200: chủ quán xem đơn của quán mình, tách biệt với quán khác, có lọc & phân trang."""
    dish_id = await _create_rescue_dish(client, store_partner, total_quantity=10)
    other_dish_id = await _create_rescue_dish(client, other_store_partner, total_quantity=5)

    order_1 = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_2 = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    other_store_order = await _place_order(client, consumer["headers"], other_dish_id, quantity=1)
    assert order_1.status_code == 201
    assert order_2.status_code == 201
    assert other_store_order.status_code == 201

    id_1 = order_1.json()["id"]
    id_2 = order_2.json()["id"]
    other_id = other_store_order.json()["id"]

    # Gắn timestamp tường minh để sắp xếp mới nhất trước luôn tất định
    db_o1 = await db_session.get(Order, uuid.UUID(id_1))
    db_o2 = await db_session.get(Order, uuid.UUID(id_2))
    assert db_o1 is not None and db_o2 is not None
    db_o1.created_at = datetime(2026, 11, 12, 9, 0, tzinfo=UTC)
    db_o2.created_at = datetime(2026, 11, 12, 9, 5, tzinfo=UTC)
    await db_session.commit()

    cancel_resp = await client.patch(
        f"/api/v1/orders/{id_1}/cancel",
        headers=store_partner["headers"],
    )
    assert cancel_resp.status_code == 200

    store_id = store_partner["store"].id
    list_resp = await client.get(
        f"/api/v1/orders/store/{store_id}",
        headers=store_partner["headers"],
    )
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert [item["id"] for item in items] == [id_2, id_1]
    assert all(item["id"] != other_id for item in items)

    # Phân trang & lọc status
    paged = await client.get(
        f"/api/v1/orders/store/{store_id}?skip=1&limit=1",
        headers=store_partner["headers"],
    )
    assert paged.status_code == 200
    assert [item["id"] for item in paged.json()] == [id_1]

    confirmed_only = await client.get(
        f"/api/v1/orders/store/{store_id}?status=CONFIRMED",
        headers=store_partner["headers"],
    )
    assert confirmed_only.status_code == 200
    assert [item["id"] for item in confirmed_only.json()] == [id_2]


async def test_store_orders_enforces_ownership_role_and_404(
    client: AsyncClient,
    store_partner: dict,
    other_store_partner: dict,
    consumer: dict,
) -> None:
    """401/403/404 cho /orders/store/{store_id} khi thiếu quyền hoặc không sở hữu quán."""
    store_id = store_partner["store"].id

    unauth = await client.get(f"/api/v1/orders/store/{store_id}")
    assert unauth.status_code == 401

    consumer_resp = await client.get(
        f"/api/v1/orders/store/{store_id}",
        headers=consumer["headers"],
    )
    assert consumer_resp.status_code == 403

    other_partner_resp = await client.get(
        f"/api/v1/orders/store/{store_id}",
        headers=other_store_partner["headers"],
    )
    assert other_partner_resp.status_code == 403

    missing_store_resp = await client.get(
        f"/api/v1/orders/store/{uuid.uuid4()}",
        headers=store_partner["headers"],
    )
    assert missing_store_resp.status_code == 404


# ==============================================================================
# 6. POST /api/v1/orders/verify-qr — xác thực mã QR nhận món & hoàn tất đơn hàng
# ==============================================================================


async def test_verify_qr_success_as_store_owner(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """200: Chủ quán quét mã QR hợp lệ -> Order hoàn tất (COMPLETED), token đã dùng."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    assert created.status_code == 201
    order_id = uuid.UUID(created.json()["id"])

    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=db_order.id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )

    verify_resp = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": qr_payload},
        headers=store_partner["headers"],
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["success"] is True
    assert data["order_id"] == str(order_id)
    assert data["order_code"] == db_order.order_code
    assert data["status"] == "COMPLETED"

    # Kiểm tra DB: token đã dùng, order đã COMPLETED
    stored_token = await QRService(db_session).get_qr_token_by_order_id(order_id)
    assert stored_token is not None
    assert stored_token.is_used is True
    assert stored_token.used_at is not None

    refreshed_order = await db_session.get(Order, order_id)
    assert refreshed_order is not None
    assert refreshed_order.status == OrderStatus.COMPLETED
    assert refreshed_order.completed_at is not None


async def test_verify_qr_invalid_signature_rejected(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """400: Chữ ký HMAC giả mạo/không hợp lệ bị từ chối."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )
    # Giả mạo signature
    tampered_payload = re.sub(r"sig=[0-9a-f]+", "sig=0123456789abcdef" * 4, qr_payload)

    resp = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": tampered_payload},
        headers=store_partner["headers"],
    )
    assert resp.status_code == 400
    assert "chữ ký" in resp.json()["detail"].lower()


async def test_verify_qr_tampered_payload_rejected(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """400: Payload QR bị sửa đổi trường (nonce, order_id...) bị phát hiện."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )
    # Sửa nonce trong query string
    tampered_payload = re.sub(
        r"nonce=[0-9a-f]+", "nonce=ffffffffffffffffffffffffffffffff", qr_payload
    )

    resp = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": tampered_payload},
        headers=store_partner["headers"],
    )
    assert resp.status_code == 400


async def test_verify_qr_expired_token_rejected(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """400: Token đã quá thời hạn expires_at bị từ chối."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])

    # Tạo QR token với hạn đã qua
    past_time = datetime.now(UTC) - timedelta(minutes=10)
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = past_time
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=consumer["user"].id,
        pickup_deadline=past_time,
    )

    resp = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": qr_payload},
        headers=store_partner["headers"],
    )
    assert resp.status_code == 400
    assert "hết hạn" in resp.json()["detail"].lower()


async def test_verify_qr_nonexistent_token_rejected(
    client: AsyncClient,
    store_partner: dict,
) -> None:
    """404: Quét token không tồn tại trong hệ thống."""
    fake_token = (
        f"ecobite://pickup?order_id={uuid.uuid4()}&user_id={uuid.uuid4()}"
        f"&nonce={'a' * 32}&expires_at=2099-01-01T00%3A00%3A00Z&sig={'b' * 64}"
    )
    resp = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": fake_token},
        headers=store_partner["headers"],
    )
    assert resp.status_code in (400, 404)


async def test_verify_qr_already_used_token_rejected(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """400: Quét mã QR đã được sử dụng trước đó (chống Replay Attack)."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )

    # Quét lần 1 -> 200 OK
    resp1 = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": qr_payload},
        headers=store_partner["headers"],
    )
    assert resp1.status_code == 200

    # Quét lần 2 -> 400 hoặc 409
    resp2 = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": qr_payload},
        headers=store_partner["headers"],
    )
    assert resp2.status_code in (400, 409)
    detail = resp2.json()["detail"].lower()
    assert "đã được sử dụng" in detail or "hoàn tất" in detail


async def test_verify_qr_wrong_user_or_order(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """400: user_id trong payload không khớp với consumer_id của đơn hàng."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    different_user_id = uuid.uuid4()
    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=different_user_id,
        pickup_deadline=db_order.pickup_deadline,
    )

    resp = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": qr_payload},
        headers=store_partner["headers"],
    )
    assert resp.status_code == 400
    assert "không khớp" in resp.json()["detail"].lower()


async def test_verify_qr_wrong_store_partner_forbidden(
    client: AsyncClient,
    store_partner: dict,
    other_store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """403: Quán khác quét mã của quán này bị từ chối."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )

    resp = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": qr_payload},
        headers=other_store_partner["headers"],
    )
    assert resp.status_code == 403
    assert "không có quyền" in resp.json()["detail"].lower()


async def test_verify_qr_unauthenticated_and_consumer_rejected(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """401 khi thiếu auth; 403 khi role CONSUMER gọi verify-qr."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )

    unauth = await client.post("/api/v1/orders/verify-qr", json={"qr_token": qr_payload})
    assert unauth.status_code == 401

    consumer_call = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": qr_payload},
        headers=consumer["headers"],
    )
    assert consumer_call.status_code == 403


async def test_verify_qr_invalid_order_status_rejected(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """409: Đơn hàng ở trạng thái CANCELLED không thể nhận món."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )

    # Hủy đơn trước
    cancel_resp = await client.patch(
        f"/api/v1/orders/{order_id}/cancel",
        headers=consumer["headers"],
    )
    assert cancel_resp.status_code == 200

    # Thử quét QR đơn đã hủy
    verify_resp = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": qr_payload},
        headers=store_partner["headers"],
    )
    assert verify_resp.status_code == 409
    assert "không thể nhận món" in verify_resp.json()["detail"].lower()


async def test_verify_qr_concurrent_double_redeem(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """Chống race condition: Hai request đồng thời quét 1 mã QR thì chỉ 1 request thắng."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)

    async def concurrent_get_db():
        async with session_factory() as s:
            yield s

    from app.db.session import get_db
    from app.main import app

    orig_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = concurrent_get_db

    try:
        task1 = client.post(
            "/api/v1/orders/verify-qr",
            json={"qr_token": qr_payload},
            headers=store_partner["headers"],
        )
        task2 = client.post(
            "/api/v1/orders/verify-qr",
            json={"qr_token": qr_payload},
            headers=store_partner["headers"],
        )
        resp1, resp2 = await asyncio.gather(task1, task2)
    finally:
        if orig_override is not None:
            app.dependency_overrides[get_db] = orig_override
        else:
            app.dependency_overrides.pop(get_db, None)

    statuses = {resp1.status_code, resp2.status_code}
    assert 200 in statuses
    assert statuses in ({200, 400}, {200, 409})

    refreshed_order = await db_session.get(Order, order_id)
    assert refreshed_order is not None
    await db_session.refresh(refreshed_order)
    assert refreshed_order.status == OrderStatus.COMPLETED


async def test_verify_qr_transaction_rollback_when_order_update_fails(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Transaction rollback: Nếu bước cập nhật Order thất bại, token KHÔNG được đánh dấu đã dùng."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    order_id = uuid.UUID(created.json()["id"])
    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    qr_payload = await QRService(db_session).generate_order_qr_token(
        order_id=order_id,
        user_id=consumer["user"].id,
        pickup_deadline=db_order.pickup_deadline,
    )

    # Giả lập complete_if_allowed bị lỗi bất ngờ
    async def fake_complete_if_allowed(*args, **kwargs):
        raise RuntimeError("Simulated failure during order completion")

    from app.repositories.order_repo import OrderRepository

    monkeypatch.setattr(OrderRepository, "complete_if_allowed", fake_complete_if_allowed)

    try:
        resp = await client.post(
            "/api/v1/orders/verify-qr",
            json={"qr_token": qr_payload},
            headers=store_partner["headers"],
        )
        assert resp.status_code == 500
    except RuntimeError:
        pass

    # Kiểm tra DB: Token KHÔNG được đánh dấu là used do transaction đã rollback
    stored_token = await QRService(db_session).get_qr_token_by_order_id(order_id)
    assert stored_token is not None
    await db_session.refresh(stored_token)
    assert stored_token.is_used is False

    refreshed_order = await db_session.get(Order, order_id)
    assert refreshed_order is not None
    await db_session.refresh(refreshed_order)
    assert refreshed_order.status == OrderStatus.CONFIRMED


# ==============================================================================
# 7. POST /api/v1/orders/{order_id}/qr — cấp/lấy lại QR payload ký HMAC
# ==============================================================================


async def test_issue_order_qr_payload_is_idempotent_and_verifiable(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """200: Consumer lấy QR payload cho đơn CONFIRMED; gọi lại trả cùng payload & verify OK."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    assert created.status_code == 201
    order_id = uuid.UUID(created.json()["id"])

    db_order = await db_session.get(Order, order_id)
    assert db_order is not None
    db_order.pickup_deadline = datetime.now(UTC) + timedelta(hours=2)
    await db_session.commit()

    first_qr = await client.post(f"/api/v1/orders/{order_id}/qr", headers=consumer["headers"])
    assert first_qr.status_code == 200
    body1 = first_qr.json()
    assert body1["order_id"] == str(order_id)
    assert body1["qr_payload"].startswith("ecobite://pickup?")
    assert body1["is_used"] is False

    second_qr = await client.post(f"/api/v1/orders/{order_id}/qr", headers=consumer["headers"])
    assert second_qr.status_code == 200
    assert second_qr.json()["qr_payload"] == body1["qr_payload"]

    verify_resp = await client.post(
        "/api/v1/orders/verify-qr",
        json={"qr_token": body1["qr_payload"]},
        headers=store_partner["headers"],
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "COMPLETED"


async def test_issue_order_qr_payload_blocks_non_owner_and_cancelled_order(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """403 nếu không phải consumer chủ đơn; 409 nếu đơn đã hủy."""
    dish_id = await _create_rescue_dish(client, store_partner)
    created = await _place_order(client, consumer["headers"], dish_id, quantity=1)
    assert created.status_code == 201
    order_id = uuid.UUID(created.json()["id"])

    forbidden = await client.post(f"/api/v1/orders/{order_id}/qr", headers=store_partner["headers"])
    assert forbidden.status_code == 403

    cancel_resp = await client.patch(
        f"/api/v1/orders/{order_id}/cancel", headers=consumer["headers"]
    )
    assert cancel_resp.status_code == 200

    conflict = await client.post(f"/api/v1/orders/{order_id}/qr", headers=consumer["headers"])
    assert conflict.status_code == 409
