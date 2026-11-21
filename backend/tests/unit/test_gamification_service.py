"""Unit tests for GamificationRepository and GamificationService."""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish
from app.models.gamification import GreenPointsLedger, PointActionType, Voucher
from app.models.menu_item import ItemCategory
from app.models.order import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole
from app.repositories.gamification_repo import GamificationRepository
from app.services import gamification_service
from app.services.gamification_service import GamificationService

FIXED_NOW = datetime(2026, 11, 21, 14, 0, tzinfo=UTC)


async def _create_consumer(
    db: AsyncSession,
    *,
    green_points_balance: int = 0,
    email_prefix: str = "consumer",
) -> User:
    user = User(
        email=f"{email_prefix}-{uuid.uuid4().hex[:8]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Người Dùng Xanh",
        role=UserRole.CONSUMER,
        green_points_balance=green_points_balance,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_voucher(
    db: AsyncSession,
    *,
    code: str | None = None,
    title: str = "Voucher Giảm 10K",
    discount_amount: Decimal = Decimal("10000.00"),
    points_required: int = 100,
    min_order_amount: Decimal = Decimal("30000.00"),
    expires_at: datetime | None = None,
    is_active: bool = True,
) -> Voucher:
    voucher = Voucher(
        code=code or f"ECO-{uuid.uuid4().hex[:6].upper()}",
        title=title,
        description="Ưu đãi đổi bằng Điểm Xanh",
        discount_amount=discount_amount,
        points_required=points_required,
        min_order_amount=min_order_amount,
        expires_at=expires_at if expires_at is not None else FIXED_NOW + timedelta(days=30),
        is_active=is_active,
    )
    db.add(voucher)
    await db.commit()
    await db.refresh(voucher)
    return voucher


async def _seed_orders_for_consumer(
    db: AsyncSession,
    consumer: User,
    specs: list[tuple[OrderStatus, int, Decimal]],
) -> list[Order]:
    """Create a store, dish, and multiple orders with varying statuses for stats tests."""
    partner = User(
        email=f"partner-{uuid.uuid4().hex[:8]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Chủ Quán Xanh",
        role=UserRole.STORE_PARTNER,
    )
    db.add(partner)
    await db.flush()

    store = Store(
        owner_id=partner.id,
        name="Quán Xanh Test",
        address="100 Hai Bà Trưng, Q.1",
        location="POINT(106.7005 10.7792)",
        kyc_status=KycStatus.APPROVED,
    )
    db.add(store)
    await db.flush()

    dish = Dish(
        store_id=store.id,
        name="Cơm sườn cứu hộ",
        category=ItemCategory.RICE,
        original_price=Decimal("50000.00"),
        rescue_price=Decimal("25000.00"),
        pickup_start_time=time(11, 0),
        pickup_end_time=time(14, 0),
        total_quantity=20,
        remaining_quantity=10,
    )
    db.add(dish)
    await db.flush()

    orders: list[Order] = []
    for idx, (order_status, qty, co2_kg) in enumerate(specs, start=1):
        order = Order(
            order_code=f"EB-20261121-{uuid.uuid4().hex[:6].upper()}{idx}",
            consumer_id=consumer.id,
            store_id=store.id,
            dish_id=dish.id,
            quantity=qty,
            unit_price=Decimal("25000.00"),
            total_amount=Decimal("25000.00") * qty,
            payment_method=PaymentMethod.COD,
            payment_status=PaymentStatus.PAID,
            status=order_status,
            pickup_deadline=FIXED_NOW + timedelta(hours=2),
            co2_saved_kg=co2_kg,
            green_points_earned=qty * 50,
        )
        db.add(order)
        orders.append(order)

    await db.commit()
    return orders


# ==============================================================================
# 1. compute_rank_title (Rule-Based Eco Ranking)
# ==============================================================================


@pytest.mark.parametrize(
    ("balance_points", "co2_kg", "expected_rank"),
    [
        (0, Decimal("0.00"), "Mầm Xanh (Eco Seedling)"),
        (99, Decimal("0.00"), "Mầm Xanh (Eco Seedling)"),
        (100, Decimal("0.00"), "Người Giải Cứu (Food Rescuer)"),
        (299, Decimal("5.00"), "Người Giải Cứu (Food Rescuer)"),
        (300, Decimal("0.00"), "Chiến Binh Xanh (Eco Hero)"),
        (350, Decimal("17.50"), "Chiến Binh Xanh (Eco Hero)"),
        (999, Decimal("25.00"), "Chiến Binh Xanh (Eco Hero)"),
        (1000, Decimal("0.00"), "Đại Sứ Xanh (Eco Ambassador)"),
        # Redeeming vouchers lowers balance, but rescued CO2 preserves earned rank.
        (20, Decimal("17.50"), "Chiến Binh Xanh (Eco Hero)"),
        (0, Decimal("50.00"), "Đại Sứ Xanh (Eco Ambassador)"),
    ],
)
def test_compute_rank_title_thresholds(
    balance_points: int,
    co2_kg: Decimal,
    expected_rank: str,
) -> None:
    """Rule-based Eco Rank must map points/CO2 thresholds deterministically."""
    assert GamificationService.compute_rank_title(balance_points, co2_kg) == expected_rank


# ==============================================================================
# 2. get_my_green_points
# ==============================================================================


async def test_get_my_green_points_aggregates_only_completed_orders(
    db_session: AsyncSession,
) -> None:
    """Summary must count only COMPLETED orders and sort ledger newest first."""
    consumer = await _create_consumer(db_session, green_points_balance=350)
    await _seed_orders_for_consumer(
        db_session,
        consumer,
        [
            (OrderStatus.COMPLETED, 2, Decimal("5.00")),
            (OrderStatus.COMPLETED, 5, Decimal("12.50")),
            # Must be excluded from environmental stats
            (OrderStatus.CONFIRMED, 3, Decimal("7.50")),
            (OrderStatus.CANCELLED, 4, Decimal("10.00")),
        ],
    )

    older = GreenPointsLedger(
        user_id=consumer.id,
        points_change=100,
        balance_after=100,
        action_type=PointActionType.ORDER_RESCUE,
        co2_saved_kg=Decimal("5.00"),
        note="Oldest entry",
        created_at=FIXED_NOW - timedelta(hours=2),
    )
    newer = GreenPointsLedger(
        user_id=consumer.id,
        points_change=250,
        balance_after=350,
        action_type=PointActionType.ORDER_RESCUE,
        co2_saved_kg=Decimal("12.50"),
        note="Newest entry",
        created_at=FIXED_NOW - timedelta(hours=1),
    )
    db_session.add_all([older, newer])
    await db_session.commit()

    summary = await GamificationService(db_session).get_my_green_points(consumer.id)

    assert summary.balance_points == 350
    assert summary.total_co2_saved_kg == Decimal("17.50")
    assert summary.total_meals_saved == 7
    assert summary.rank_title == "Chiến Binh Xanh (Eco Hero)"
    assert len(summary.recent_ledger) == 2
    assert summary.recent_ledger[0].note == "Newest entry"
    assert summary.recent_ledger[1].note == "Oldest entry"


async def test_get_my_green_points_empty_user_defaults(db_session: AsyncSession) -> None:
    """A brand new user with no orders/ledger returns zeros and base rank."""
    consumer = await _create_consumer(db_session, green_points_balance=0)

    summary = await GamificationService(db_session).get_my_green_points(consumer.id)

    assert summary.balance_points == 0
    assert summary.total_co2_saved_kg == Decimal("0.00")
    assert summary.total_meals_saved == 0
    assert summary.rank_title == "Mầm Xanh (Eco Seedling)"
    assert summary.recent_ledger == []


async def test_get_my_green_points_404_when_user_missing(db_session: AsyncSession) -> None:
    """Non-existent user ID must raise 404."""
    with pytest.raises(HTTPException) as exc_info:
        await GamificationService(db_session).get_my_green_points(uuid.uuid4())
    assert exc_info.value.status_code == 404


# ==============================================================================
# 3. list_available_vouchers & list_my_vouchers
# ==============================================================================


async def test_list_available_vouchers_filters_inactive_and_expired(
    db_session: AsyncSession,
) -> None:
    """Only active vouchers with expires_at > now should be returned, sorted by points."""
    high_pts = await _create_voucher(
        db_session,
        code="ECO50K",
        points_required=500,
        expires_at=FIXED_NOW + timedelta(days=10),
        is_active=True,
    )
    low_pts = await _create_voucher(
        db_session,
        code="ECO10K",
        points_required=100,
        expires_at=FIXED_NOW + timedelta(days=5),
        is_active=True,
    )
    # Inactive voucher
    await _create_voucher(
        db_session,
        code="INACTIVE10K",
        points_required=50,
        expires_at=FIXED_NOW + timedelta(days=5),
        is_active=False,
    )
    # Expired voucher (past & exact boundary)
    await _create_voucher(
        db_session,
        code="EXPIRED10K",
        points_required=50,
        expires_at=FIXED_NOW - timedelta(seconds=1),
        is_active=True,
    )
    await _create_voucher(
        db_session,
        code="BOUNDARY10K",
        points_required=50,
        expires_at=FIXED_NOW,
        is_active=True,
    )

    vouchers = await GamificationService(db_session).list_available_vouchers(now=FIXED_NOW)

    assert [v.id for v in vouchers] == [low_pts.id, high_pts.id]


async def test_list_my_vouchers_scopes_to_user_and_paginates(db_session: AsyncSession) -> None:
    """list_my_vouchers must return only the requesting user's claimed vouchers."""
    alice = await _create_consumer(db_session, green_points_balance=500, email_prefix="alice")
    bob = await _create_consumer(db_session, green_points_balance=500, email_prefix="bob")
    v1 = await _create_voucher(db_session, code="ECO10K", points_required=100)
    v2 = await _create_voucher(db_session, code="ECO20K", points_required=200)

    service = GamificationService(db_session)
    await service.redeem_voucher(alice.id, v1.id, now=FIXED_NOW)
    await service.redeem_voucher(alice.id, v2.id, now=FIXED_NOW)
    await service.redeem_voucher(bob.id, v1.id, now=FIXED_NOW)

    alice_vouchers = await service.list_my_vouchers(alice.id)
    assert len(alice_vouchers) == 2
    assert {uv.voucher.code for uv in alice_vouchers} == {"ECO10K", "ECO20K"}

    paged = await service.list_my_vouchers(alice.id, skip=1, limit=1)
    assert len(paged) == 1


# ==============================================================================
# 4. redeem_voucher & atomic_deduct_points
# ==============================================================================


async def test_redeem_voucher_success_updates_balance_ledger_and_user_voucher(
    db_session: AsyncSession,
) -> None:
    """Redemption must atomically deduct points, log negative ledger entry, and issue voucher."""
    consumer = await _create_consumer(db_session, green_points_balance=250)
    voucher = await _create_voucher(
        db_session,
        code="ECO25K",
        title="Voucher 25.000đ",
        discount_amount=Decimal("25000.00"),
        points_required=200,
    )

    response = await GamificationService(db_session).redeem_voucher(
        consumer.id, voucher.id, now=FIXED_NOW
    )

    assert response.voucher_id == voucher.id
    assert response.voucher_code == "ECO25K"
    assert response.title == "Voucher 25.000đ"
    assert response.discount_amount == Decimal("25000.00")
    assert response.points_deducted == 200
    assert response.remaining_balance == 50
    assert response.claimed_at is not None

    refreshed_user = await GamificationRepository(db_session).get_user_by_id(consumer.id)
    assert refreshed_user is not None
    assert refreshed_user.green_points_balance == 50

    ledger = await GamificationRepository(db_session).get_ledger_by_user(consumer.id)
    assert len(ledger) == 1
    assert ledger[0].points_change == -200
    assert ledger[0].balance_after == 50
    assert ledger[0].action_type == PointActionType.VOUCHER_REDEEM

    my_vouchers = await GamificationRepository(db_session).get_user_vouchers(consumer.id)
    assert len(my_vouchers) == 1
    assert my_vouchers[0].id == response.user_voucher_id
    assert my_vouchers[0].is_used is False


async def test_redeem_voucher_409_when_insufficient_points_and_no_side_effects(
    db_session: AsyncSession,
) -> None:
    """Insufficient points must return 409 without mutating balance, ledger, or user_vouchers."""
    consumer = await _create_consumer(db_session, green_points_balance=99)
    voucher = await _create_voucher(db_session, code="ECO10K", points_required=100)

    with pytest.raises(HTTPException) as exc_info:
        await GamificationService(db_session).redeem_voucher(consumer.id, voucher.id, now=FIXED_NOW)

    assert exc_info.value.status_code == 409

    repo = GamificationRepository(db_session)
    refreshed = await repo.get_user_by_id(consumer.id)
    assert refreshed is not None
    assert refreshed.green_points_balance == 99
    assert await repo.get_ledger_by_user(consumer.id) == []
    assert await repo.get_user_vouchers(consumer.id) == []


async def test_redeem_voucher_double_redeem_prevents_negative_balance(
    db_session: AsyncSession,
) -> None:
    """Two consecutive redemptions exceeding balance must succeed once and fail with 409."""
    consumer = await _create_consumer(db_session, green_points_balance=150)
    voucher = await _create_voucher(db_session, code="ECO10K", points_required=100)
    service = GamificationService(db_session)

    first = await service.redeem_voucher(consumer.id, voucher.id, now=FIXED_NOW)
    assert first.remaining_balance == 50

    with pytest.raises(HTTPException) as exc_info:
        await service.redeem_voucher(consumer.id, voucher.id, now=FIXED_NOW)
    assert exc_info.value.status_code == 409

    repo = GamificationRepository(db_session)
    refreshed = await repo.get_user_by_id(consumer.id)
    assert refreshed is not None
    assert refreshed.green_points_balance == 50
    assert len(await repo.get_user_vouchers(consumer.id)) == 1
    assert len(await repo.get_ledger_by_user(consumer.id)) == 1


async def test_redeem_voucher_404_when_voucher_missing(db_session: AsyncSession) -> None:
    """Unknown voucher UUID must raise 404."""
    consumer = await _create_consumer(db_session, green_points_balance=500)

    with pytest.raises(HTTPException) as exc_info:
        await GamificationService(db_session).redeem_voucher(
            consumer.id, uuid.uuid4(), now=FIXED_NOW
        )
    assert exc_info.value.status_code == 404


async def test_redeem_voucher_400_when_voucher_inactive(db_session: AsyncSession) -> None:
    """Inactive voucher must be rejected with 400 and leave balance untouched."""
    consumer = await _create_consumer(db_session, green_points_balance=500)
    voucher = await _create_voucher(db_session, points_required=100, is_active=False)

    with pytest.raises(HTTPException) as exc_info:
        await GamificationService(db_session).redeem_voucher(consumer.id, voucher.id, now=FIXED_NOW)

    assert exc_info.value.status_code == 400
    refreshed = await GamificationRepository(db_session).get_user_by_id(consumer.id)
    assert refreshed is not None
    assert refreshed.green_points_balance == 500


@pytest.mark.parametrize(
    "expires_at",
    [
        FIXED_NOW - timedelta(minutes=1),
        FIXED_NOW,
    ],
)
async def test_redeem_voucher_400_when_voucher_expired(
    db_session: AsyncSession,
    expires_at: datetime,
) -> None:
    """Expired voucher (including exact expiry timestamp) must raise 400."""
    consumer = await _create_consumer(db_session, green_points_balance=500)
    voucher = await _create_voucher(db_session, points_required=100, expires_at=expires_at)

    with pytest.raises(HTTPException) as exc_info:
        await GamificationService(db_session).redeem_voucher(consumer.id, voucher.id, now=FIXED_NOW)

    assert exc_info.value.status_code == 400
    refreshed = await GamificationRepository(db_session).get_user_by_id(consumer.id)
    assert refreshed is not None
    assert refreshed.green_points_balance == 500


async def test_redeem_voucher_rolls_back_points_and_ledger_when_issue_fails(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mid-transaction failure must roll back both point deduction and ledger creation."""
    consumer = await _create_consumer(db_session, green_points_balance=300)
    voucher = await _create_voucher(db_session, points_required=100)
    consumer_id = consumer.id
    voucher_id = voucher.id

    async def fail_create_user_voucher(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("Simulated DB failure while creating UserVoucher")

    monkeypatch.setattr(GamificationRepository, "create_user_voucher", fail_create_user_voucher)

    with pytest.raises(RuntimeError, match="Simulated DB failure"):
        await GamificationService(db_session).redeem_voucher(consumer_id, voucher_id, now=FIXED_NOW)

    repo = GamificationRepository(db_session)
    refreshed = await repo.get_user_by_id(consumer_id)
    assert refreshed is not None
    assert refreshed.green_points_balance == 300
    assert await repo.get_ledger_by_user(consumer_id) == []
    assert await repo.get_user_vouchers(consumer_id) == []


async def test_redeem_voucher_acquires_user_scoped_distributed_lock(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Redemption must wrap work in a user-scoped distributed lock."""
    captured: dict[str, str] = {}

    @asynccontextmanager
    async def recorder(key: str, **_kwargs: object) -> AsyncIterator[bool]:
        captured["key"] = key
        yield True

    monkeypatch.setattr(gamification_service, "distributed_lock", recorder)
    consumer = await _create_consumer(db_session, green_points_balance=200)
    voucher = await _create_voucher(db_session, points_required=100)

    await GamificationService(db_session).redeem_voucher(consumer.id, voucher.id, now=FIXED_NOW)

    assert captured["key"] == f"lock:green_points:user:{consumer.id}"


@pytest.mark.parametrize("bad_cost", [0, -10])
async def test_atomic_deduct_points_rejects_non_positive_cost(
    db_session: AsyncSession,
    bad_cost: int,
) -> None:
    """atomic_deduct_points must return None for zero or negative point costs."""
    consumer = await _create_consumer(db_session, green_points_balance=100)
    repo = GamificationRepository(db_session)

    result = await repo.atomic_deduct_points(consumer.id, bad_cost, commit=True)

    assert result is None
    refreshed = await repo.get_user_by_id(consumer.id)
    assert refreshed is not None
    assert refreshed.green_points_balance == 100
