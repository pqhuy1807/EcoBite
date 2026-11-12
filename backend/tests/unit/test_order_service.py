"""Unit tests for OrderService: stock locking, green impact and cancellation."""

import re
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, time
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import ItemCategory
from app.models.order import OrderStatus, PaymentMethod, PaymentStatus
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole
from app.repositories import dish_repo
from app.repositories.order_repo import OrderRepository
from app.schemas.order import OrderCreate
from app.services import order_service
from app.services.order_service import OrderService

# Module-level singletons for argument defaults (avoids bugbear B008 call-in-default).
ALL_DAY_START = time(0, 0)
ALL_DAY_END = time(23, 59)

# Mốc thời gian cố định (17:30 ngày 30/03/2026) để test không phụ thuộc đồng hồ thực.
FIXED_NOW = datetime(2026, 3, 30, 17, 30)


def _as_utc(value: datetime) -> datetime:
    """Chuẩn hóa về UTC: SQLite trả datetime naive, Postgres trả tz-aware."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def _seed_rescue_dish(
    db: AsyncSession,
    *,
    dish_status: DishStatus = DishStatus.ACTIVE,
    remaining_quantity: int = 4,
    pickup_start: time = ALL_DAY_START,
    pickup_end: time = ALL_DAY_END,
    rule_discount_start_time: time | None = None,
    override_discounted_price: Decimal | None = None,
) -> tuple[Dish, uuid.UUID]:
    """Seed chuỗi consumer/partner/store/dish và trả về (dish, consumer_id)."""
    consumer = User(
        email=f"consumer-{uuid.uuid4().hex[:10]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Khách Đặt Đơn",
        role=UserRole.CONSUMER,
    )
    partner = User(
        email=f"owner-{uuid.uuid4().hex[:10]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Chủ Quán Giải Cứu",
        role=UserRole.STORE_PARTNER,
    )
    db.add_all([consumer, partner])
    await db.flush()

    store = Store(
        owner_id=partner.id,
        name="Quán Bánh Mì Hoa Hướng Dương",
        address="2 Nguyễn Trãi, Q.1, TP.HCM",
        location="POINT(106.700806 10.776889)",
        kyc_status=KycStatus.APPROVED,
    )
    db.add(store)
    await db.flush()

    dish = Dish(
        store_id=store.id,
        name="Bánh mì trứng cuối ca",
        category=ItemCategory.BAKERY,
        original_price=Decimal("40000.00"),
        rescue_price=Decimal("20000.00"),
        rule_discount_price=Decimal("12000.00"),
        override_discounted_price=override_discounted_price,
        pickup_start_time=pickup_start,
        pickup_end_time=pickup_end,
        rule_discount_start_time=rule_discount_start_time,
        total_quantity=4,
        remaining_quantity=remaining_quantity,
        status=dish_status,
    )
    db.add(dish)
    await db.commit()
    return dish, consumer.id


# ==============================================================================
# 1. create_rescue_order
# ==============================================================================


async def test_create_rescue_order_success(db_session: AsyncSession) -> None:
    """Đơn tạo thành công: giá rule-based, điểm xanh đúng và kho bị trừ đúng."""
    dish, consumer_id = await _seed_rescue_dish(db_session)
    service = OrderService(db_session)

    order = await service.create_rescue_order(
        consumer_id,
        OrderCreate(dish_id=dish.id, quantity=2, payment_method=PaymentMethod.COD),
        now=FIXED_NOW,
    )

    assert re.fullmatch(r"EB-\d{8}-[0-9A-F]{8}", order.order_code)
    assert order.order_code.startswith("EB-20260330-")
    assert order.consumer_id == consumer_id
    assert order.store_id == dish.store_id
    assert order.dish_id == dish.id
    assert order.quantity == 2
    # 17:30 nằm ngoài khung giờ chót (mặc định 45 phút cuối ca) → giá giải cứu -50%
    assert order.unit_price == Decimal("20000.00")
    assert order.total_amount == Decimal("40000.00")
    assert order.status == OrderStatus.CONFIRMED
    assert order.payment_method == PaymentMethod.COD
    assert order.payment_status == PaymentStatus.PENDING
    # Tác động môi trường: 2 suất × 2.5 kg CO2e = 5 kg → 50 Điểm Xanh
    assert order.co2_saved_kg == Decimal("5.00")
    assert order.green_points_earned == 50
    assert _as_utc(order.pickup_deadline) == datetime(2026, 3, 30, 23, 59, tzinfo=UTC)

    refreshed = await dish_repo.get_by_id(db_session, dish.id)
    assert refreshed is not None
    assert refreshed.remaining_quantity == 2


async def test_create_rescue_order_applies_rule_discount_price(
    db_session: AsyncSession,
) -> None:
    """Trong khung giờ chót, đơn giá phải là giá luật -70% (Guardrail #5)."""
    dish, consumer_id = await _seed_rescue_dish(db_session, rule_discount_start_time=time(0, 0))
    service = OrderService(db_session)

    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )

    assert order.unit_price == Decimal("12000.00")
    assert order.total_amount == Decimal("12000.00")


async def test_create_rescue_order_prefers_override_price(db_session: AsyncSession) -> None:
    """Giá xả cố định do chủ quán chỉ định luôn ưu tiên hơn giá luật."""
    dish, consumer_id = await _seed_rescue_dish(
        db_session, override_discounted_price=Decimal("9999.00")
    )
    service = OrderService(db_session)

    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )

    assert order.unit_price == Decimal("9999.00")


async def test_create_rescue_order_404_when_dish_missing(db_session: AsyncSession) -> None:
    """Dish UUID không tồn tại phải trả về 404."""
    service = OrderService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_rescue_order(
            uuid.uuid4(), OrderCreate(dish_id=uuid.uuid4(), quantity=1), now=FIXED_NOW
        )
    assert exc_info.value.status_code == 404


@pytest.mark.parametrize(
    "dish_status",
    [DishStatus.INACTIVE, DishStatus.SOLD_OUT, DishStatus.EXPIRED],
)
async def test_create_rescue_order_409_when_dish_not_active(
    db_session: AsyncSession, dish_status: DishStatus
) -> None:
    """Món không ở trạng thái ACTIVE phải bị chặn với HTTP 409."""
    dish, consumer_id = await _seed_rescue_dish(db_session, dish_status=dish_status)
    service = OrderService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_rescue_order(
            consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Món ăn hiện không còn mở bán"


async def test_create_rescue_order_400_when_before_pickup_window(
    db_session: AsyncSession,
) -> None:
    """Đặt trước khung giờ đón món phải trả về 400 Bad Request."""
    dish, consumer_id = await _seed_rescue_dish(db_session, pickup_start=time(17, 31))
    service = OrderService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_rescue_order(
            consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
        )

    assert exc_info.value.status_code == 400
    assert "khung giờ" in str(exc_info.value.detail)


async def test_create_rescue_order_400_when_after_pickup_window(
    db_session: AsyncSession,
) -> None:
    """Đặt sau khi kết thúc khung giờ đón món phải trả về 400 Bad Request."""
    dish, consumer_id = await _seed_rescue_dish(db_session, pickup_end=time(17, 29))
    service = OrderService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_rescue_order(
            consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
        )

    assert exc_info.value.status_code == 400


async def test_create_rescue_order_409_when_insufficient_stock(
    db_session: AsyncSession,
) -> None:
    """Không đủ số lượng phải 409 với đúng thông báo và kho không bị trừ."""
    dish, consumer_id = await _seed_rescue_dish(db_session, remaining_quantity=1)
    service = OrderService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_rescue_order(
            consumer_id, OrderCreate(dish_id=dish.id, quantity=2), now=FIXED_NOW
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Món ăn đã hết suất hoặc số lượng còn lại không đủ"
    refreshed = await dish_repo.get_by_id(db_session, dish.id)
    assert refreshed is not None
    assert refreshed.remaining_quantity == 1


async def test_create_rescue_order_marks_sold_out_when_stock_hits_zero(
    db_session: AsyncSession,
) -> None:
    """Trừ về đúng 0 suất phải tự chuyển món sang SOLD_OUT."""
    dish, consumer_id = await _seed_rescue_dish(db_session, remaining_quantity=2)
    service = OrderService(db_session)

    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=2), now=FIXED_NOW
    )
    assert order.id is not None

    refreshed = await dish_repo.get_by_id(db_session, dish.id)
    assert refreshed is not None
    assert refreshed.remaining_quantity == 0
    assert refreshed.status == DishStatus.SOLD_OUT


async def test_create_rescue_order_acquires_dish_scoped_lock(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Đặt đơn phải bọc khóa phân tán Redis với key `lock:dish:{dish_id}`."""
    captured: dict[str, str] = {}

    @asynccontextmanager
    async def recorder(key: str, **_kwargs: object) -> AsyncIterator[bool]:
        captured["key"] = key
        yield True

    monkeypatch.setattr(order_service, "distributed_lock", recorder)
    dish, consumer_id = await _seed_rescue_dish(db_session)
    service = OrderService(db_session)

    await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )

    assert captured["key"] == f"lock:dish:{dish.id}"


async def test_create_rescue_order_retries_when_code_collides(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Trùng mã đơn (UNIQUE) phải sinh mã khác và thử lại thay vì sập."""
    dish, consumer_id = await _seed_rescue_dish(db_session)
    service = OrderService(db_session)
    first = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )

    generated = iter([first.order_code, "EB-20260330-DEADBEEF"])
    monkeypatch.setattr(
        OrderService, "_generate_order_code", staticmethod(lambda _now: next(generated))
    )

    second = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )

    assert second.order_code == "EB-20260330-DEADBEEF"


# ==============================================================================
# 2. cancel_order
# ==============================================================================


async def test_cancel_order_restores_stock_and_marks_cancelled(
    db_session: AsyncSession,
) -> None:
    """Hủy đơn phải hoàn đúng số suất về kho và chuyển trạng thái CANCELLED."""
    dish, consumer_id = await _seed_rescue_dish(db_session, remaining_quantity=4)
    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=3), now=FIXED_NOW
    )

    cancelled = await service.cancel_order(order.id, consumer_id)

    assert cancelled.id == order.id
    assert cancelled.status == OrderStatus.CANCELLED
    refreshed = await dish_repo.get_by_id(db_session, dish.id)
    assert refreshed is not None
    assert refreshed.remaining_quantity == 4  # 1 còn lại + 3 suất hoàn về kho


async def test_cancel_order_reactivates_sold_out_dish(db_session: AsyncSession) -> None:
    """Món từng về 0 suất (SOLD_OUT) phải được kích hoạt lại khi có đơn bị hủy."""
    dish, consumer_id = await _seed_rescue_dish(db_session, remaining_quantity=1)
    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )
    sold_out = await dish_repo.get_by_id(db_session, dish.id)
    assert sold_out is not None
    assert sold_out.status == DishStatus.SOLD_OUT

    cancelled = await service.cancel_order(order.id, consumer_id)

    assert cancelled.status == OrderStatus.CANCELLED
    refreshed = await dish_repo.get_by_id(db_session, dish.id)
    assert refreshed is not None
    assert refreshed.status == DishStatus.ACTIVE
    assert refreshed.remaining_quantity == 1  # seed 1 − mua 1 + hoàn 1 = 1


async def test_cancel_order_403_when_user_is_not_the_owner(
    db_session: AsyncSession,
) -> None:
    """User khác chủ đơn phải bị từ chối với HTTP 403."""
    dish, consumer_id = await _seed_rescue_dish(db_session)
    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_order(order.id, uuid.uuid4())

    assert exc_info.value.status_code == 403


async def test_cancel_order_404_when_order_missing(db_session: AsyncSession) -> None:
    """Đơn không tồn tại phải trả về 404."""
    service = OrderService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_order(uuid.uuid4(), uuid.uuid4())
    assert exc_info.value.status_code == 404


async def test_cancel_order_409_when_already_cancelled(db_session: AsyncSession) -> None:
    """Hủy 2 lần phải 409 và tuyệt đối không hoàn kho 2 lần."""
    dish, consumer_id = await _seed_rescue_dish(db_session, remaining_quantity=3)
    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )
    await service.cancel_order(order.id, consumer_id)

    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_order(order.id, consumer_id)

    assert exc_info.value.status_code == 409
    refreshed = await dish_repo.get_by_id(db_session, dish.id)
    assert refreshed is not None
    assert refreshed.remaining_quantity == 3  # không bị hoàn thêm lần nữa


async def test_cancel_order_409_when_order_completed(db_session: AsyncSession) -> None:
    """Đơn đã COMPLETED (đã nhận món) không được phép hủy."""
    dish, consumer_id = await _seed_rescue_dish(db_session)
    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )
    await OrderRepository(db_session).update_status(order.id, OrderStatus.COMPLETED)

    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_order(order.id, consumer_id)

    assert exc_info.value.status_code == 409


async def test_cancel_order_allows_ready_for_pickup(db_session: AsyncSession) -> None:
    """Đơn đang chờ nhận món (READY_FOR_PICKUP) vẫn được phép hủy."""
    dish, consumer_id = await _seed_rescue_dish(db_session)
    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )
    await OrderRepository(db_session).update_status(order.id, OrderStatus.READY_FOR_PICKUP)

    cancelled = await service.cancel_order(order.id, consumer_id)

    assert cancelled.status == OrderStatus.CANCELLED


# ==============================================================================
# 3. cancel_order — phân quyền chủ quán (STORE_PARTNER) & hạn chót lấy món
# ==============================================================================


async def test_cancel_order_allows_the_store_owner_of_the_dish(
    db_session: AsyncSession,
) -> None:
    """Chủ cửa hàng bán món (STORE_PARTNER) được hủy đơn của khách tại quán mình."""
    dish, consumer_id = await _seed_rescue_dish(db_session, remaining_quantity=4)
    store = await db_session.get(Store, dish.store_id)
    assert store is not None
    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=2), now=FIXED_NOW
    )

    cancelled = await service.cancel_order(order.id, store.owner_id, now=FIXED_NOW)

    assert cancelled.id == order.id
    assert cancelled.status == OrderStatus.CANCELLED
    refreshed = await dish_repo.get_by_id(db_session, dish.id)
    assert refreshed is not None
    assert refreshed.remaining_quantity == 4  # 2 còn lại + 2 suất hoàn về kho


async def test_cancel_order_403_when_partner_owns_a_different_store(
    db_session: AsyncSession,
) -> None:
    """Đối tác của quán khác không được hủy đơn của quán mình."""
    dish, consumer_id = await _seed_rescue_dish(db_session, remaining_quantity=3)
    stranger = User(
        email=f"stranger-{uuid.uuid4().hex[:10]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Chủ Quán Lân Cận",
        role=UserRole.STORE_PARTNER,
    )
    db_session.add(stranger)
    await db_session.flush()
    stranger_store = Store(
        owner_id=stranger.id,
        name="Quán Phở Quanh Đường",
        address="88 Đường Láng, Đống Đa, Hà Nội",
        location="POINT(105.806788 21.028128)",
        kyc_status=KycStatus.APPROVED,
    )
    db_session.add(stranger_store)
    await db_session.commit()

    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_order(order.id, stranger.id, now=FIXED_NOW)

    assert exc_info.value.status_code == 403
    refreshed = await dish_repo.get_by_id(db_session, dish.id)
    assert refreshed is not None
    assert refreshed.remaining_quantity == 2  # 3 seed − 1 đơn; không hoàn khi bị chặn


async def test_cancel_order_409_when_past_pickup_deadline(db_session: AsyncSession) -> None:
    """Quá hạn chót lấy món (pickup_deadline) phải bị chặn 409 và không hoàn kho."""
    dish, consumer_id = await _seed_rescue_dish(db_session, remaining_quantity=3)
    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )

    # Deadline của đơn = 23:59 ngày 30/03 (cuối khung giờ đón món khi đặt).
    too_late = datetime(2026, 3, 31, 8, 0)
    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_order(order.id, consumer_id, now=too_late)

    assert exc_info.value.status_code == 409
    assert "quá hạn" in str(exc_info.value.detail)
    refreshed = await dish_repo.get_by_id(db_session, dish.id)
    assert refreshed is not None
    assert refreshed.remaining_quantity == 2  # 3 seed − 1 đơn; không hoàn khi bị chặn


async def test_cancel_order_allows_exactly_at_pickup_deadline(db_session: AsyncSession) -> None:
    """Ranh giới: đúng thời điểm hạn chót (now == pickup_deadline) vẫn được hủy."""
    dish, consumer_id = await _seed_rescue_dish(db_session)
    service = OrderService(db_session)
    order = await service.create_rescue_order(
        consumer_id, OrderCreate(dish_id=dish.id, quantity=1), now=FIXED_NOW
    )

    cancelled = await service.cancel_order(order.id, consumer_id, now=datetime(2026, 3, 30, 23, 59))

    assert cancelled.status == OrderStatus.CANCELLED
