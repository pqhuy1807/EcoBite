"""Unit tests for Order repository: creation, lookups and status transitions."""

import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish
from app.models.menu_item import ItemCategory
from app.models.order import OrderStatus, PaymentMethod
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole
from app.repositories.order_repo import OrderRepository


async def _build_order_payload(db: AsyncSession) -> dict[str, Any]:
    """Seed consumer/store/dish và trả về payload đơn hàng hợp lệ đầy đủ."""
    consumer = User(
        email="consumer-order@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Khách Tận Tâm",
        role=UserRole.CONSUMER,
    )
    partner = User(
        email="owner-order@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Chủ Quán",
        role=UserRole.STORE_PARTNER,
    )
    db.add_all([consumer, partner])
    await db.flush()

    store = Store(
        owner_id=partner.id,
        name="Quán Bánh Mì Cô Ba",
        address="1 Lê Lợi, Q.1, TP.HCM",
        location="POINT(106.700806 10.776889)",
        kyc_status=KycStatus.APPROVED,
    )
    db.add(store)
    await db.flush()

    dish = Dish(
        store_id=store.id,
        name="Bánh mì cuối ca",
        category=ItemCategory.BAKERY,
        original_price=Decimal("30000.00"),
        rescue_price=Decimal("15000.00"),
        pickup_start_time=time(14, 0),
        pickup_end_time=time(18, 0),
        total_quantity=5,
        remaining_quantity=4,
    )
    db.add(dish)
    await db.commit()

    return {
        "order_code": f"EB-{datetime.now(UTC):%Y%m%d}-{uuid.uuid4().hex[:4].upper()}",
        "consumer_id": consumer.id,
        "store_id": store.id,
        "dish_id": dish.id,
        "quantity": 2,
        "unit_price": Decimal("15000.00"),
        "total_amount": Decimal("30000.00"),
        "pickup_deadline": datetime.now(UTC) + timedelta(hours=4),
        "payment_method": PaymentMethod.VNPAY,
    }


async def test_create_order_persists_with_lifecycle_defaults(db_session: AsyncSession) -> None:
    """create_order phải lưu default trạng thái CONFIRMED và thanh toán PENDING."""
    repo = OrderRepository(db_session)
    payload = await _build_order_payload(db_session)

    order = await repo.create_order(payload)

    assert order.id is not None
    assert order.order_code == payload["order_code"]
    assert order.quantity == 2
    assert order.total_amount == Decimal("30000.00")
    assert order.status == OrderStatus.CONFIRMED
    assert order.payment_status.name == "PENDING"


async def test_get_by_id_eager_loads_consumer_store_dish(db_session: AsyncSession) -> None:
    """get_by_id phải nạp đầy đủ quan hệ consumer/store/dish mà không N+1."""
    repo = OrderRepository(db_session)
    payload = await _build_order_payload(db_session)
    created = await repo.create_order(payload)

    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.order_code == payload["order_code"]
    assert fetched.consumer.id == payload["consumer_id"]
    assert fetched.consumer.full_name == "Khách Tận Tâm"
    assert fetched.store.name == "Quán Bánh Mì Cô Ba"
    assert fetched.dish.name == "Bánh mì cuối ca"
    assert fetched.dish.rescue_price == Decimal("15000.00")


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    """UUID không tồn tại phải trả về None thay vì raise."""
    repo = OrderRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_get_by_order_code_returns_matching_order(db_session: AsyncSession) -> None:
    """Tra cứu bằng mã đơn hiển thị phải khớp đúng đơn đã tạo."""
    repo = OrderRepository(db_session)
    payload = await _build_order_payload(db_session)
    created = await repo.create_order(payload)

    fetched = await repo.get_by_order_code(payload["order_code"])

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.total_amount == Decimal("30000.00")


async def test_get_by_order_code_returns_none_when_missing(db_session: AsyncSession) -> None:
    """Mã đơn không tồn tại phải trả về None."""
    repo = OrderRepository(db_session)
    assert await repo.get_by_order_code("EB-20770101-NULL") is None


async def test_update_status_transitions_across_lifecycle(db_session: AsyncSession) -> None:
    """update_status phải chuyển trạng thái và bền vững trong DB."""
    repo = OrderRepository(db_session)
    payload = await _build_order_payload(db_session)
    created = await repo.create_order(payload)

    picked = await repo.update_status(created.id, OrderStatus.READY_FOR_PICKUP)
    assert picked is not None
    assert picked.status == OrderStatus.READY_FOR_PICKUP

    completed = await repo.update_status(created.id, OrderStatus.COMPLETED)
    assert completed is not None
    assert completed.status == OrderStatus.COMPLETED

    cancelled = await repo.update_status(created.id, OrderStatus.CANCELLED)
    assert cancelled is not None
    assert cancelled.status == OrderStatus.CANCELLED

    expired = await repo.update_status(created.id, OrderStatus.EXPIRED)
    assert expired is not None
    assert expired.status == OrderStatus.EXPIRED

    reloaded = await repo.get_by_order_code(payload["order_code"])
    assert reloaded is not None
    assert reloaded.status == OrderStatus.EXPIRED


async def test_update_status_returns_none_when_order_missing(db_session: AsyncSession) -> None:
    """Không tìm thấy đơn phải trả về None để tầng Service quyết định HTTP response."""
    repo = OrderRepository(db_session)
    assert await repo.update_status(uuid.uuid4(), OrderStatus.COMPLETED) is None
