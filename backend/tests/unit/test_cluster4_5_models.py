"""Unit tests for Cluster 4 & 5: Gamification & Interactions.

Covers: GreenPoints, Vouchers, Reviews, Notifications.
"""

import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models.dish import Dish
from app.models.gamification import (
    GreenPointsLedger,
    PointActionType,
    UserVoucher,
    Voucher,
)
from app.models.interaction import Notification, NotificationType, Review
from app.models.menu_item import ItemCategory
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.store import Store
from app.models.user import User, UserRole
from app.schemas.gamification import (
    GreenPointsLedgerResponse,
    UserVoucherResponse,
    VoucherCreate,
    VoucherResponse,
)
from app.schemas.interaction import (
    NotificationResponse,
    ReviewCreate,
    ReviewResponse,
)

# ==============================================================================
# 1. Pydantic Validation Tests (Cluster 4 & 5)
# ==============================================================================


def test_voucher_create_validation() -> None:
    """Test valid VoucherCreate payload."""
    expires = datetime.now(UTC) + timedelta(days=30)
    voucher_in = VoucherCreate(
        code="SAVE20K",
        title="Giảm 20.000đ cho đơn giải cứu",
        discount_amount=Decimal("20000.00"),
        points_required=200,
        min_order_amount=Decimal("50000.00"),
        expires_at=expires,
    )
    assert voucher_in.code == "SAVE20K"
    assert voucher_in.discount_amount == Decimal("20000.00")
    assert voucher_in.points_required == 200


def test_voucher_create_negative_points_fails() -> None:
    """Test that zero or negative points_required raises ValidationError."""
    with pytest.raises(ValidationError):
        VoucherCreate(
            code="INVALID",
            title="Voucher loi",
            discount_amount=Decimal("10000.00"),
            points_required=0,  # Must be gt 0
            expires_at=datetime.now(UTC),
        )


def test_review_create_rating_bounds() -> None:
    """Test Review rating must be strictly in 1..5."""
    valid_review = ReviewCreate(
        order_id=uuid.uuid4(),
        rating=5,
        comment="Mon an rat ngon va dong goi can than",
        tags=["Ngon", "Đóng gói kỹ"],
    )
    assert valid_review.rating == 5

    with pytest.raises(ValidationError):
        ReviewCreate(
            order_id=uuid.uuid4(),
            rating=6,  # Out of bounds (> 5)
        )

    with pytest.raises(ValidationError):
        ReviewCreate(
            order_id=uuid.uuid4(),
            rating=0,  # Out of bounds (< 1)
        )


# ==============================================================================
# 2. Database ORM Persistence & Relationships Tests (SQLite in-memory)
# ==============================================================================


@pytest.fixture
async def setup_cluster4_5_entities(db_session):
    """Fixture providing Consumer, Store Partner, Store, Dish, and Order."""
    consumer = User(
        email="consumer_c45@ecobite.vn",
        hashed_password="pw",
        full_name="Hoang Khach Hang",
        role=UserRole.CONSUMER,
    )
    merchant = User(
        email="merchant_c45@ecobite.vn",
        hashed_password="pw",
        full_name="Chu Quan An",
        role=UserRole.STORE_PARTNER,
    )
    store = Store(
        owner=merchant,
        name="Tiem Com Nieu Sai Gon",
        address="12 Ho Xuan Huong, Q3",
        location="POINT(106.69 10.78)",
    )
    dish = Dish(
        store=store,
        name="Com Nieu Ca Kho To",
        category=ItemCategory.RICE,
        original_price=Decimal("60000.00"),
        rescue_price=Decimal("30000.00"),
        pickup_start_time=time(11, 30),
        pickup_end_time=time(13, 0),
        total_quantity=5,
        remaining_quantity=5,
    )
    order = Order(
        order_code="EB-20261030-9901",
        consumer=consumer,
        store=store,
        dish=dish,
        quantity=1,
        unit_price=Decimal("30000.00"),
        total_amount=Decimal("30000.00"),
        status=OrderStatus.COMPLETED,
        payment_method=PaymentMethod.VNPAY,
        pickup_deadline=datetime.now(UTC) + timedelta(hours=1),
    )
    db_session.add_all([consumer, merchant, store, dish, order])
    await db_session.commit()
    await db_session.refresh(consumer)
    await db_session.refresh(store)
    await db_session.refresh(dish)
    await db_session.refresh(order)
    return consumer, store, dish, order


@pytest.mark.asyncio
async def test_green_points_ledger_persistence(db_session, setup_cluster4_5_entities) -> None:
    """Test GreenPointsLedger recording points earned from completed rescue order."""
    consumer, _, _, order = setup_cluster4_5_entities

    ledger_entry = GreenPointsLedger(
        user=consumer,
        order=order,
        points_change=30,
        balance_after=30,
        action_type=PointActionType.ORDER_RESCUE,
        co2_saved_kg=Decimal("2.50"),
        note="Thuong diem xanh tu don hang cuu tro",
    )
    db_session.add(ledger_entry)
    await db_session.commit()
    await db_session.refresh(ledger_entry)
    await db_session.refresh(consumer)

    assert isinstance(ledger_entry.id, uuid.UUID)
    assert ledger_entry.points_change == 30
    assert ledger_entry.action_type == PointActionType.ORDER_RESCUE
    assert len(consumer.green_points_records) == 1
    assert consumer.green_points_records[0].id == ledger_entry.id

    # Verify DTO serialization
    dto = GreenPointsLedgerResponse.model_validate(ledger_entry)
    assert dto.points_change == 30
    assert dto.balance_after == 30


@pytest.mark.asyncio
async def test_voucher_and_claim_flow(db_session, setup_cluster4_5_entities) -> None:
    """Test Voucher creation, UserVoucher claim, and usage."""
    consumer, _, _, _ = setup_cluster4_5_entities
    expires = datetime.now(UTC) + timedelta(days=14)

    voucher = Voucher(
        code="GREENBITE15",
        title="Giam 15.000d",
        discount_amount=Decimal("15000.00"),
        points_required=150,
        expires_at=expires,
    )
    db_session.add(voucher)
    await db_session.commit()
    await db_session.refresh(voucher)

    # User claims voucher
    user_voucher = UserVoucher(
        user=consumer,
        voucher=voucher,
        is_used=False,
    )
    db_session.add(user_voucher)
    await db_session.commit()
    await db_session.refresh(user_voucher)
    await db_session.refresh(consumer)

    assert len(consumer.user_vouchers) == 1
    assert consumer.user_vouchers[0].is_used is False
    assert consumer.user_vouchers[0].voucher.code == "GREENBITE15"

    # Mark as used in checkout
    user_voucher.is_used = True
    user_voucher.used_at = datetime.now(UTC)
    await db_session.commit()
    await db_session.refresh(user_voucher)

    assert user_voucher.is_used is True

    # DTO Response Validation
    voucher_dto = VoucherResponse.model_validate(voucher)
    assert voucher_dto.code == "GREENBITE15"
    claim_dto = UserVoucherResponse.model_validate(user_voucher)
    assert claim_dto.is_used is True


@pytest.mark.asyncio
async def test_review_unique_per_order_and_check_constraint(
    db_session, setup_cluster4_5_entities
) -> None:
    """Test verified Review 1-to-1 with Order and rating 1..5 constraint."""
    consumer, store, dish, order = setup_cluster4_5_entities

    review = Review(
        order=order,
        consumer=consumer,
        store=store,
        dish=dish,
        rating=5,
        comment="Com ngon, nong hoi, phuc vu nhanh",
        tags=["Ngon", "Nóng hổi"],
        photo_urls=["https://ecobite.vn/reviews/com_01.jpg"],
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    await db_session.refresh(order)

    assert order.review is not None
    assert order.review.id == review.id
    assert review.rating == 5

    # Test DTO serialization
    dto = ReviewResponse.model_validate(review)
    assert dto.rating == 5
    assert dto.tags == ["Ngon", "Nóng hổi"]

    # Test duplicate review on same order fails (Unique Constraint)
    duplicate_review = Review(
        order=order,
        consumer=consumer,
        store=store,
        dish=dish,
        rating=4,
    )
    db_session.add(duplicate_review)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_notification_persistence_and_read(db_session, setup_cluster4_5_entities) -> None:
    """Test Notification creation, payload serialization, and read status."""
    consumer, _, _, order = setup_cluster4_5_entities

    notif = Notification(
        user=consumer,
        title="Đơn hàng sẵn sàng!",
        message=f"Đơn hàng {order.order_code} đã sẵn sàng nhận món.",
        type=NotificationType.ORDER_UPDATE,
        metadata_payload={"order_id": str(order.id), "order_code": order.order_code},
        is_read=False,
    )
    db_session.add(notif)
    await db_session.commit()
    await db_session.refresh(notif)
    await db_session.refresh(consumer)

    assert len(consumer.notifications) == 1
    assert consumer.notifications[0].is_read is False
    assert consumer.notifications[0].type == NotificationType.ORDER_UPDATE

    # Mark as read
    notif.is_read = True
    await db_session.commit()
    await db_session.refresh(notif)
    assert notif.is_read is True

    # DTO Response serialization
    dto = NotificationResponse.model_validate(notif)
    assert dto.title == "Đơn hàng sẵn sàng!"
    assert dto.metadata_payload["order_code"] == order.order_code
