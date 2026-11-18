"""Unit tests for ReviewRepository: persistence, uniqueness, store rating calculation."""

import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import ItemCategory
from app.models.order import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole
from app.repositories.review_repo import ReviewRepository


async def _seed_test_context(
    db: AsyncSession,
) -> tuple[Store, User, Dish, Order]:
    """Helper to seed a store, consumer, dish and completed order."""
    suffix = uuid.uuid4().hex[:8]
    partner = User(
        email=f"owner-{suffix}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Chủ Quán Review",
        role=UserRole.STORE_PARTNER,
    )
    consumer = User(
        email=f"consumer-{suffix}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Khách Review",
        role=UserRole.CONSUMER,
    )
    db.add_all([partner, consumer])
    await db.flush()

    store = Store(
        owner_id=partner.id,
        name="Tiệm Cơm Tấm Sài Gòn",
        address="10 Nguyễn Thị Minh Khai, Q.1",
        location="POINT(106.698 10.782)",
        kyc_status=KycStatus.APPROVED,
        rating_avg=Decimal("5.00"),
        rating_count=0,
    )
    db.add(store)
    await db.flush()

    dish = Dish(
        store_id=store.id,
        name="Cơm tấm sườn nướng",
        category=ItemCategory.RICE,
        original_price=Decimal("50000.00"),
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
        status=OrderStatus.COMPLETED,
        payment_method=PaymentMethod.VNPAY,
        payment_status=PaymentStatus.PAID,
        pickup_deadline=datetime.now(UTC) + timedelta(hours=2),
    )
    db.add(order)
    await db.commit()
    await db.refresh(store)
    await db.refresh(order)
    return store, consumer, dish, order


async def test_create_review_success(db_session: AsyncSession) -> None:
    """Tạo review mới lưu đúng dữ liệu và liên kết quan hệ."""
    store, consumer, dish, order = await _seed_test_context(db_session)
    repo = ReviewRepository(db_session)

    review = await repo.create_review(
        order_id=order.id,
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        rating=5,
        comment="Món ăn rất ngon, đóng gói cẩn thận!",
        tags=["Ngon", "Đóng gói kỹ"],
        photo_urls=["https://cdn.ecobite.vn/photo1.jpg"],
    )

    assert review.id is not None
    assert review.order_id == order.id
    assert review.consumer_id == consumer.id
    assert review.store_id == store.id
    assert review.dish_id == dish.id
    assert review.rating == 5
    assert review.comment == "Món ăn rất ngon, đóng gói cẩn thận!"
    assert review.tags == ["Ngon", "Đóng gói kỹ"]
    assert review.photo_urls == ["https://cdn.ecobite.vn/photo1.jpg"]


async def test_get_by_order_id(db_session: AsyncSession) -> None:
    """Tra cứu review bằng order_id tải sẵn thông tin consumer và dish."""
    store, consumer, dish, order = await _seed_test_context(db_session)
    repo = ReviewRepository(db_session)

    created = await repo.create_review(
        order_id=order.id,
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        rating=4,
        comment="Khá ổn",
    )

    found = await repo.get_by_order_id(order.id)
    assert found is not None
    assert found.id == created.id
    assert found.consumer.id == consumer.id
    assert found.dish.id == dish.id


async def test_create_review_unique_order_constraint(db_session: AsyncSession) -> None:
    """Mỗi đơn hàng chỉ được đánh giá 1 lần (ràng buộc UNIQUE order_id)."""
    store, consumer, dish, order = await _seed_test_context(db_session)
    repo = ReviewRepository(db_session)

    await repo.create_review(
        order_id=order.id,
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        rating=5,
    )

    with pytest.raises(IntegrityError):
        await repo.create_review(
            order_id=order.id,
            consumer_id=consumer.id,
            store_id=store.id,
            dish_id=dish.id,
            rating=3,
        )
    await db_session.rollback()


async def test_list_by_store_with_pagination(db_session: AsyncSession) -> None:
    """Liệt kê review theo store_id, sắp xếp mới nhất và hỗ trợ phân trang."""
    store, consumer, dish, order1 = await _seed_test_context(db_session)
    repo = ReviewRepository(db_session)

    # Tạo thêm đơn hàng thứ 2
    order2 = Order(
        order_code=f"EB-20261118-{uuid.uuid4().hex[:8].upper()}",
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        quantity=1,
        unit_price=Decimal("25000.00"),
        total_amount=Decimal("25000.00"),
        status=OrderStatus.COMPLETED,
        payment_method=PaymentMethod.COD,
        payment_status=PaymentStatus.PAID,
        pickup_deadline=datetime.now(UTC) + timedelta(hours=2),
    )
    db_session.add(order2)
    await db_session.commit()

    rev1 = await repo.create_review(
        order_id=order1.id,
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        rating=4,
        comment="Đánh giá 1",
    )
    rev1.created_at = datetime.now(UTC) - timedelta(minutes=10)
    await db_session.commit()

    rev2 = await repo.create_review(
        order_id=order2.id,
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        rating=5,
        comment="Đánh giá 2",
    )
    rev2.created_at = datetime.now(UTC)
    await db_session.commit()

    # Lấy toàn bộ (mới nhất lên đầu)
    reviews = await repo.list_by_store(store.id, skip=0, limit=10)
    assert len(reviews) == 2
    assert reviews[0].id == rev2.id
    assert reviews[1].id == rev1.id

    # Phân trang: limit=1
    first_page = await repo.list_by_store(store.id, skip=0, limit=1)
    assert len(first_page) == 1
    assert first_page[0].id == rev2.id

    second_page = await repo.list_by_store(store.id, skip=1, limit=1)
    assert len(second_page) == 1
    assert second_page[0].id == rev1.id


async def test_update_store_rating_aggregates_average_and_count(
    db_session: AsyncSession,
) -> None:
    """Tính toán rating_avg và rating_count chính xác khi quán có nhiều review."""
    store, consumer, dish, order1 = await _seed_test_context(db_session)
    repo = ReviewRepository(db_session)

    # Đơn 2 và Đơn 3
    order2 = Order(
        order_code=f"EB-20261118-{uuid.uuid4().hex[:8].upper()}",
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        quantity=1,
        unit_price=Decimal("25000.00"),
        total_amount=Decimal("25000.00"),
        status=OrderStatus.COMPLETED,
        payment_method=PaymentMethod.VNPAY,
        payment_status=PaymentStatus.PAID,
        pickup_deadline=datetime.now(UTC) + timedelta(hours=2),
    )
    order3 = Order(
        order_code=f"EB-20261118-{uuid.uuid4().hex[:8].upper()}",
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        quantity=1,
        unit_price=Decimal("25000.00"),
        total_amount=Decimal("25000.00"),
        status=OrderStatus.COMPLETED,
        payment_method=PaymentMethod.VNPAY,
        payment_status=PaymentStatus.PAID,
        pickup_deadline=datetime.now(UTC) + timedelta(hours=2),
    )
    db_session.add_all([order2, order3])
    await db_session.commit()

    # Đánh giá: 5, 4, 4 -> Trung bình: (5 + 4 + 4) / 3 = 4.33
    await repo.create_review(
        order_id=order1.id,
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        rating=5,
    )
    await repo.create_review(
        order_id=order2.id,
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        rating=4,
    )
    await repo.create_review(
        order_id=order3.id,
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        rating=4,
    )

    avg_rating, total_count = await repo.update_store_rating(store.id)
    assert avg_rating == Decimal("4.33")
    assert total_count == 3

    # Kiểm tra trực tiếp trong DB
    refreshed_store = await db_session.get(Store, store.id)
    assert refreshed_store is not None
    assert refreshed_store.rating_avg == Decimal("4.33")
    assert refreshed_store.rating_count == 3


async def test_update_store_rating_handles_empty_store(
    db_session: AsyncSession,
) -> None:
    """Quán chưa có review nào được trả về mặc định rating_avg=5.00 và count=0."""
    store, _consumer, _dish, _order = await _seed_test_context(db_session)
    repo = ReviewRepository(db_session)

    # Đặt giá trị khác để kiểm tra hàm có reset về mặc định không
    store.rating_avg = Decimal("3.50")
    store.rating_count = 10
    await db_session.commit()

    avg_rating, total_count = await repo.update_store_rating(store.id)
    assert avg_rating == Decimal("5.00")
    assert total_count == 0

    refreshed_store = await db_session.get(Store, store.id)
    assert refreshed_store is not None
    assert refreshed_store.rating_avg == Decimal("5.00")
    assert refreshed_store.rating_count == 0
