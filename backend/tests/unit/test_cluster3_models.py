"""Unit tests for Cluster 3: Order, QRToken, and PaymentTransaction."""

import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.dish import Dish
from app.models.menu_item import ItemCategory
from app.models.order import (
    Order,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    PaymentTransaction,
    QRToken,
)
from app.models.store import Store
from app.models.user import User, UserRole
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    PaymentTransactionCreate,
    PaymentTransactionResponse,
    QRTokenResponse,
    VNPayIPNPayload,
)

# ==============================================================================
# 1. Pydantic Validation Tests (Cluster 3)
# ==============================================================================


def test_order_create_positive_quantity() -> None:
    """Test valid OrderCreate payload."""
    order_in = OrderCreate(
        dish_id=uuid.uuid4(),
        quantity=2,
        payment_method=PaymentMethod.VNPAY,
    )
    assert order_in.quantity == 2
    assert order_in.payment_method == PaymentMethod.VNPAY


def test_order_create_invalid_quantity() -> None:
    """Test that zero or negative quantity raises ValidationError."""
    with pytest.raises(ValidationError):
        OrderCreate(
            dish_id=uuid.uuid4(),
            quantity=0,
        )

    with pytest.raises(ValidationError):
        OrderCreate(
            dish_id=uuid.uuid4(),
            quantity=-3,
        )


def test_payment_transaction_create_negative_amount() -> None:
    """Test that negative or zero amount raises ValidationError."""
    with pytest.raises(ValidationError):
        PaymentTransactionCreate(
            order_id=uuid.uuid4(),
            txn_ref="TXN_123456",
            amount=Decimal("0.0"),
            vnp_response_code="00",
        )


def test_vnpay_ipn_payload_validation() -> None:
    """Test parsing incoming VNPay IPN webhook payload (Guardrail #3)."""
    ipn_data = {
        "vnp_Amount": "5000000",
        "vnp_BankCode": "NCB",
        "vnp_BankTranNo": "VNP14072234",
        "vnp_CardType": "ATM",
        "vnp_OrderInfo": "Thanh toan don hang EB-20261016-9981",
        "vnp_PayDate": "20261016143000",
        "vnp_ResponseCode": "00",
        "vnp_TmnCode": "ECOBITE01",
        "vnp_TransactionNo": "14072234",
        "vnp_TransactionStatus": "00",
        "vnp_TxnRef": "EB-20261016-9981",
        "vnp_SecureHash": "a1b2c3d4e5f67890123456789abcdef0",
    }
    payload = VNPayIPNPayload.model_validate(ipn_data)
    assert payload.vnp_ResponseCode == "00"
    assert payload.vnp_TransactionNo == "14072234"
    assert payload.vnp_TxnRef == "EB-20261016-9981"


# ==============================================================================
# 2. Database ORM & Business Invariants Tests (SQLite in-memory)
# ==============================================================================


@pytest.fixture
async def setup_cluster3_entities(db_session):
    """Fixture providing Consumer, Store Partner, Store, and Dish."""
    consumer = User(
        email="consumer_c3@ecobite.vn",
        hashed_password="hashed_consumer_pw",
        full_name="Nguyen Van Khach",
        role=UserRole.CONSUMER,
    )
    merchant = User(
        email="merchant_c3@ecobite.vn",
        hashed_password="hashed_merchant_pw",
        full_name="Pham Thi Quan",
        role=UserRole.STORE_PARTNER,
    )
    store = Store(
        owner=merchant,
        name="Quan Com Ga Tam Ky",
        address="789 Le Van Sy, Q3, TP.HCM",
        location="POINT(106.67 10.79)",
    )
    dish = Dish(
        store=store,
        name="Com Ga Xoi Mo",
        category=ItemCategory.RICE,
        original_price=Decimal("50000.00"),
        rescue_price=Decimal("25000.00"),
        pickup_start_time=time(18, 0),
        pickup_end_time=time(19, 30),
        total_quantity=10,
        remaining_quantity=10,
    )
    db_session.add_all([consumer, merchant, store, dish])
    await db_session.commit()
    await db_session.refresh(consumer)
    await db_session.refresh(store)
    await db_session.refresh(dish)
    return consumer, store, dish


@pytest.mark.asyncio
async def test_order_creation_and_relationships(db_session, setup_cluster3_entities) -> None:
    """Test creating an Order, checking relations to User, Store, and Dish."""
    consumer, store, dish = setup_cluster3_entities
    now = datetime.now(UTC)
    deadline = now + timedelta(hours=1)

    order = Order(
        order_code="EB-20261030-0001",
        consumer=consumer,
        store=store,
        dish=dish,
        quantity=2,
        unit_price=Decimal("25000.00"),
        total_amount=Decimal("50000.00"),
        status=OrderStatus.CONFIRMED,
        payment_method=PaymentMethod.VNPAY,
        payment_status=PaymentStatus.PAID,
        co2_saved_kg=Decimal("5.00"),
        green_points_earned=50,
        pickup_deadline=deadline,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    assert isinstance(order.id, uuid.UUID)
    assert order.order_code == "EB-20261030-0001"
    assert order.consumer.id == consumer.id
    assert order.store.id == store.id
    assert order.dish.id == dish.id
    assert order.total_amount == Decimal("50000.00")
    assert order.co2_saved_kg == Decimal("5.00")

    # Verify Pydantic Response Serialization
    dto = OrderResponse.model_validate(order)
    assert dto.id == order.id
    assert dto.total_amount == Decimal("50000.00")
    assert dto.status == OrderStatus.CONFIRMED


@pytest.mark.asyncio
async def test_qr_token_single_use_guardrail(db_session, setup_cluster3_entities) -> None:
    """Test Guardrail #3: QRToken is_used anti-replay protection."""
    consumer, store, dish = setup_cluster3_entities
    now = datetime.now(UTC)

    order = Order(
        order_code="EB-20261030-0002",
        consumer=consumer,
        store=store,
        dish=dish,
        quantity=1,
        unit_price=Decimal("25000.00"),
        total_amount=Decimal("25000.00"),
        status=OrderStatus.CONFIRMED,
        payment_method=PaymentMethod.COD,
        pickup_deadline=now + timedelta(hours=2),
    )
    qr_token = QRToken(
        order=order,
        token_hash="hmac_sha256_mock_hash_abc123",
        nonce="single_use_nonce_xyz789",
        expires_at=order.pickup_deadline,
        is_used=False,
    )
    db_session.add_all([order, qr_token])
    await db_session.commit()
    await db_session.refresh(order)
    await db_session.refresh(qr_token)

    assert order.qr_token is not None
    assert order.qr_token.is_used is False
    assert qr_token.token_hash == "hmac_sha256_mock_hash_abc123"

    # Simulate merchant scanning QR code successfully
    qr_token.is_used = True
    qr_token.used_at = datetime.now(UTC)
    order.status = OrderStatus.COMPLETED
    order.completed_at = qr_token.used_at
    await db_session.commit()
    await db_session.refresh(qr_token)

    assert qr_token.is_used is True
    assert qr_token.used_at is not None

    # Test QRTokenResponse serialization
    qr_dto = QRTokenResponse.model_validate(qr_token)
    assert qr_dto.is_used is True
    assert qr_dto.token_hash == "hmac_sha256_mock_hash_abc123"


@pytest.mark.asyncio
async def test_payment_transaction_persistence(db_session, setup_cluster3_entities) -> None:
    """Test PaymentTransaction persistence with JSONB raw_ipn_payload."""
    consumer, store, dish = setup_cluster3_entities
    order = Order(
        order_code="EB-20261030-0003",
        consumer=consumer,
        store=store,
        dish=dish,
        quantity=1,
        unit_price=Decimal("25000.00"),
        total_amount=Decimal("25000.00"),
        pickup_deadline=datetime.now(UTC) + timedelta(hours=1),
        payment_method=PaymentMethod.VNPAY,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    transaction = PaymentTransaction(
        order=order,
        payment_provider="VNPAY",
        txn_ref="EB-20261030-0003",
        amount=Decimal("25000.00"),
        vnp_transaction_no="14072235",
        vnp_bank_code="NCB",
        vnp_response_code="00",
        is_verified=True,
        raw_ipn_payload={"vnp_Amount": "2500000", "vnp_ResponseCode": "00"},
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    await db_session.refresh(order)

    assert len(order.payment_transactions) == 1
    assert order.payment_transactions[0].is_verified is True
    assert order.payment_transactions[0].raw_ipn_payload["vnp_ResponseCode"] == "00"

    # Test DTO serialization
    txn_dto = PaymentTransactionResponse.model_validate(transaction)
    assert txn_dto.is_verified is True
    assert txn_dto.amount == Decimal("25000.00")

    # Cascade delete test: Deleting order removes payment transaction
    await db_session.delete(order)
    await db_session.commit()

    deleted_txn = await db_session.get(PaymentTransaction, transaction.id)
    assert deleted_txn is None
