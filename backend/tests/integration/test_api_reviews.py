"""Integration tests for verified reviews endpoints (Feature 8A)."""

import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import ItemCategory
from app.models.order import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole


async def _seed_test_order(
    db: AsyncSession,
    consumer: User,
    *,
    status: OrderStatus = OrderStatus.COMPLETED,
) -> tuple[Store, Dish, Order]:
    """Helper to seed store, dish, and order for API tests."""
    suffix = uuid.uuid4().hex[:8]
    partner = User(
        email=f"merchant-{suffix}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Merchant",
        role=UserRole.STORE_PARTNER,
    )
    db.add(partner)
    await db.flush()

    store = Store(
        owner_id=partner.id,
        name="Quán Cơm Tấm Đêm",
        address="123 Đinh Tiên Hoàng, Q.1",
        location="POINT(106.699 10.791)",
        kyc_status=KycStatus.APPROVED,
        rating_avg=Decimal("5.00"),
        rating_count=0,
    )
    db.add(store)
    await db.flush()

    dish = Dish(
        store_id=store.id,
        name="Cơm tấm sườn chả",
        category=ItemCategory.RICE,
        original_price=Decimal("45000.00"),
        rescue_price=Decimal("25000.00"),
        pickup_start_time=time(0, 0),
        pickup_end_time=time(23, 59),
        remaining_quantity=5,
        total_quantity=5,
        status=DishStatus.ACTIVE,
    )
    db.add(dish)
    await db.flush()

    order = Order(
        order_code=f"EB-20261118-{suffix[:8].upper()}",
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        quantity=1,
        unit_price=Decimal("25000.00"),
        total_amount=Decimal("25000.00"),
        status=status,
        payment_method=PaymentMethod.VNPAY,
        payment_status=PaymentStatus.PAID,
        pickup_deadline=datetime.now(UTC) + timedelta(hours=2),
    )
    db.add(order)
    await db.commit()
    await db.refresh(store)
    await db.refresh(dish)
    await db.refresh(order)
    return store, dish, order


# ==============================================================================
# 1. POST /api/v1/orders/{order_id}/review
# ==============================================================================


async def test_create_review_success(
    client: AsyncClient,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """201: Consumer là chủ đơn COMPLETED tạo review thành công."""
    store, dish, order = await _seed_test_order(db_session, consumer["user"])

    response = await client.post(
        f"/api/v1/orders/{order.id}/review",
        json={
            "rating": 5,
            "comment": "Món ăn tuyệt vời, phục vụ chu đáo!",
            "tags": ["Ngon", "Đóng gói kỹ"],
            "photo_urls": ["https://cdn.ecobite.vn/reviews/img1.jpg"],
        },
        headers=consumer["headers"],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] is not None
    assert body["order_id"] == str(order.id)
    assert body["consumer_id"] == str(consumer["user"].id)
    assert body["store_id"] == str(store.id)
    assert body["dish_id"] == str(dish.id)
    assert body["rating"] == 5
    assert body["comment"] == "Món ăn tuyệt vời, phục vụ chu đáo!"
    assert body["tags"] == ["Ngon", "Đóng gói kỹ"]
    assert body["photo_urls"] == ["https://cdn.ecobite.vn/reviews/img1.jpg"]


async def test_create_review_403_when_not_consumer(
    client: AsyncClient,
    store_partner: dict,
    db_session: AsyncSession,
) -> None:
    """403: Role không phải CONSUMER (ví dụ STORE_PARTNER) bị chặn."""
    _store, _dish, order = await _seed_test_order(db_session, store_partner["user"])

    response = await client.post(
        f"/api/v1/orders/{order.id}/review",
        json={"rating": 5, "comment": "Chủ quán tự đánh giá"},
        headers=store_partner["headers"],
    )

    assert response.status_code == 403


async def test_create_review_403_when_not_owner(
    client: AsyncClient,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """403: Consumer khác không phải chủ đơn hàng bị từ chối."""
    stranger = User(
        email=f"stranger-{uuid.uuid4().hex[:8]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Stranger Consumer",
        role=UserRole.CONSUMER,
    )
    db_session.add(stranger)
    await db_session.commit()
    _store, _dish, order = await _seed_test_order(db_session, stranger)

    response = await client.post(
        f"/api/v1/orders/{order.id}/review",
        json={"rating": 4, "comment": "Đánh giá đơn của người khác"},
        headers=consumer["headers"],
    )

    assert response.status_code == 403
    assert "không có quyền" in response.json()["detail"]


async def test_create_review_409_when_order_not_completed(
    client: AsyncClient,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """409: Đơn hàng ở trạng thái CONFIRMED (chưa nhận món) bị chặn đánh giá."""
    _store, _dish, order = await _seed_test_order(
        db_session, consumer["user"], status=OrderStatus.CONFIRMED
    )

    response = await client.post(
        f"/api/v1/orders/{order.id}/review",
        json={"rating": 5, "comment": "Chưa nhận món đã đánh giá"},
        headers=consumer["headers"],
    )

    assert response.status_code == 409
    assert "COMPLETED" in response.json()["detail"]


async def test_create_review_409_when_duplicate(
    client: AsyncClient,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """409: Một đơn hàng chỉ được đánh giá duy nhất 1 lần (chặn trùng lặp)."""
    _store, _dish, order = await _seed_test_order(db_session, consumer["user"])

    first_resp = await client.post(
        f"/api/v1/orders/{order.id}/review",
        json={"rating": 5, "comment": "Lần 1"},
        headers=consumer["headers"],
    )
    assert first_resp.status_code == 201

    second_resp = await client.post(
        f"/api/v1/orders/{order.id}/review",
        json={"rating": 4, "comment": "Lần 2"},
        headers=consumer["headers"],
    )
    assert second_resp.status_code == 409
    assert "đã được đánh giá" in second_resp.json()["detail"]


# ==============================================================================
# 2. GET /api/v1/stores/{store_id}/reviews
# ==============================================================================


async def test_list_store_reviews_success(
    client: AsyncClient,
    consumer: dict,
    db_session: AsyncSession,
) -> None:
    """200: Lấy danh sách đánh giá của cửa hàng với phân trang."""
    store, _dish, order = await _seed_test_order(db_session, consumer["user"])

    await client.post(
        f"/api/v1/orders/{order.id}/review",
        json={"rating": 5, "comment": "Rất ngon!"},
        headers=consumer["headers"],
    )

    response = await client.get(f"/api/v1/stores/{store.id}/reviews")
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 1
    assert reviews[0]["rating"] == 5
    assert reviews[0]["comment"] == "Rất ngon!"
    assert reviews[0]["store_id"] == str(store.id)


async def test_list_store_reviews_empty_store(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """200: Quán chưa có đánh giá nào trả về mảng rỗng []."""
    random_store_id = uuid.uuid4()
    response = await client.get(f"/api/v1/stores/{random_store_id}/reviews")
    assert response.status_code == 200
    assert response.json() == []
