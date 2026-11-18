"""Unit tests for ReviewService: RBAC, ownership, order status, anti-duplication."""

import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import ItemCategory
from app.models.order import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole
from app.schemas.interaction import ReviewCreate
from app.services.review_service import ReviewService


async def _seed_review_context(
    db: AsyncSession,
    *,
    order_status: OrderStatus = OrderStatus.COMPLETED,
) -> tuple[Store, User, User, Dish, Order]:
    """Seed partner, consumer, store, dish, and order for review service testing."""
    suffix = uuid.uuid4().hex[:8]
    partner = User(
        email=f"partner-{suffix}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Chủ Quán Cơm",
        role=UserRole.STORE_PARTNER,
    )
    consumer = User(
        email=f"consumer-{suffix}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Khách Hàng Ăn Cơm",
        role=UserRole.CONSUMER,
    )
    db.add_all([partner, consumer])
    await db.flush()

    store = Store(
        owner_id=partner.id,
        name="Cơm Gà Xối Mỡ 77",
        address="77 Võ Văn Ngân, Thủ Đức",
        location="POINT(106.765 10.852)",
        kyc_status=KycStatus.APPROVED,
        rating_avg=Decimal("5.00"),
        rating_count=0,
    )
    db.add(store)
    await db.flush()

    dish = Dish(
        store_id=store.id,
        name="Cơm gà xối mỡ đùi góc tư",
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
        status=order_status,
        payment_method=PaymentMethod.VNPAY,
        payment_status=PaymentStatus.PAID,
        pickup_deadline=datetime.now(UTC) + timedelta(hours=2),
    )
    db.add(order)
    await db.commit()
    await db.refresh(store)
    await db.refresh(order)
    return store, consumer, partner, dish, order


async def test_create_review_success_by_consumer_owner(
    db_session: AsyncSession,
) -> None:
    """Consumer là chủ đơn COMPLETED tạo review thành công và cập nhật rating quán."""
    store, consumer, _partner, _dish, order = await _seed_review_context(
        db_session, order_status=OrderStatus.COMPLETED
    )
    service = ReviewService(db_session)

    payload = ReviewCreate(
        order_id=order.id,
        rating=5,
        comment="Đồ ăn nóng hổi, rất ngon!",
        tags=["Ngon", "Đóng gói kỹ"],
        photo_urls=["https://cdn.ecobite.vn/review-1.jpg"],
    )

    review = await service.create_review(order.id, consumer, payload)

    assert review.id is not None
    assert review.order_id == order.id
    assert review.consumer_id == consumer.id
    assert review.store_id == store.id
    assert review.rating == 5
    assert review.comment == "Đồ ăn nóng hổi, rất ngon!"

    # Kiểm tra store rating được cập nhật
    refreshed_store = await db_session.get(Store, store.id)
    assert refreshed_store is not None
    assert refreshed_store.rating_avg == Decimal("5.00")
    assert refreshed_store.rating_count == 1


async def test_create_review_403_when_user_not_owner(
    db_session: AsyncSession,
) -> None:
    """User không phải chủ sở hữu của đơn hàng bị từ chối với HTTP 403."""
    _store, _consumer, _partner, _dish, order = await _seed_review_context(
        db_session, order_status=OrderStatus.COMPLETED
    )
    service = ReviewService(db_session)

    stranger = User(
        email=f"stranger-{uuid.uuid4().hex[:8]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Người Khác",
        role=UserRole.CONSUMER,
    )
    db_session.add(stranger)
    await db_session.commit()

    payload = ReviewCreate(
        order_id=order.id,
        rating=5,
        comment="Thử đánh giá đơn của người khác",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_review(order.id, stranger, payload)

    assert exc_info.value.status_code == 403
    assert "không có quyền" in exc_info.value.detail


async def test_create_review_409_when_order_not_completed(
    db_session: AsyncSession,
) -> None:
    """Đơn chưa COMPLETED (ví dụ CONFIRMED) không được phép đánh giá (HTTP 409)."""
    _store, consumer, _partner, _dish, order = await _seed_review_context(
        db_session, order_status=OrderStatus.CONFIRMED
    )
    service = ReviewService(db_session)

    payload = ReviewCreate(
        order_id=order.id,
        rating=4,
        comment="Đánh giá trước khi nhận món",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_review(order.id, consumer, payload)

    assert exc_info.value.status_code == 409
    assert "COMPLETED" in exc_info.value.detail


async def test_create_review_403_when_user_not_consumer(
    db_session: AsyncSession,
) -> None:
    """Tài khoản không phải CONSUMER (ví dụ STORE_PARTNER) bị từ chối với HTTP 403."""
    _store, _consumer, partner, _dish, order = await _seed_review_context(
        db_session, order_status=OrderStatus.COMPLETED
    )
    service = ReviewService(db_session)

    payload = ReviewCreate(
        order_id=order.id,
        rating=5,
        comment="Đối tác tự đánh giá",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_review(order.id, partner, payload)

    assert exc_info.value.status_code == 403
    assert "CONSUMER" in exc_info.value.detail


async def test_create_review_409_when_duplicate_order_id(
    db_session: AsyncSession,
) -> None:
    """Đơn đã được đánh giá thì lần gửi thứ 2 bị từ chối với HTTP 409."""
    _store, consumer, _partner, _dish, order = await _seed_review_context(
        db_session, order_status=OrderStatus.COMPLETED
    )
    service = ReviewService(db_session)

    payload = ReviewCreate(
        order_id=order.id,
        rating=5,
        comment="Lần 1",
    )
    await service.create_review(order.id, consumer, payload)

    # Thử gửi đánh giá lần 2
    with pytest.raises(HTTPException) as exc_info:
        await service.create_review(order.id, consumer, payload)

    assert exc_info.value.status_code == 409
    assert "đã được đánh giá" in exc_info.value.detail


async def test_create_review_404_when_order_not_found(
    db_session: AsyncSession,
) -> None:
    """Đơn hàng không tồn tại trả về HTTP 404."""
    _store, consumer, _partner, _dish, _order = await _seed_review_context(db_session)
    service = ReviewService(db_session)

    random_id = uuid.uuid4()
    payload = ReviewCreate(
        order_id=random_id,
        rating=5,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_review(random_id, consumer, payload)

    assert exc_info.value.status_code == 404
    assert "Order not found" in exc_info.value.detail


async def test_create_review_handles_race_condition_integrity_error(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rào chắn CSDL (IntegrityError) chống race condition trả về HTTP 409 chuẩn xác."""
    _store, consumer, _partner, _dish, order = await _seed_review_context(
        db_session, order_status=OrderStatus.COMPLETED
    )
    service = ReviewService(db_session)

    payload = ReviewCreate(
        order_id=order.id,
        rating=5,
    )

    # Giả lập 2 request đồng thời vượt qua check ban đầu nhưng DB ném IntegrityError
    async def mock_fail_unique(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("mock unique constraint", orig=Exception(), params={})

    monkeypatch.setattr(service.review_repo, "create_review", mock_fail_unique)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_review(order.id, consumer, payload)

    assert exc_info.value.status_code == 409
    assert "đã được đánh giá" in exc_info.value.detail
