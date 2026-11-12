"""Unit tests (Test-First) for Dynamic HMAC-SHA256 QR Token repository & service."""

import hashlib
import hmac
import logging
import re
import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.dish import Dish
from app.models.menu_item import ItemCategory
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole
from app.repositories.qr_token_repo import QRTokenRepository
from app.services import qr_service as qr_service_module
from app.services.qr_service import QRService

FIXED_NOW = datetime(2026, 11, 12, 10, 0, 0, tzinfo=UTC)
PICKUP_DEADLINE = datetime(2026, 11, 12, 12, 0, 0, tzinfo=UTC)


def _as_utc(value: datetime) -> datetime:
    """Normalize SQLite naive datetimes to UTC for deterministic assertions."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def _seed_order(
    db: AsyncSession,
    *,
    pickup_deadline: datetime = PICKUP_DEADLINE,
    order_status: OrderStatus = OrderStatus.CONFIRMED,
) -> tuple[Order, User]:
    """Seed consumer, partner, store, dish and order for QR token tests."""
    suffix = uuid.uuid4().hex[:8]
    consumer = User(
        email=f"qr-consumer-{suffix}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Khách Nhận QR",
        role=UserRole.CONSUMER,
    )
    partner = User(
        email=f"qr-partner-{suffix}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Chủ Quán QR",
        role=UserRole.STORE_PARTNER,
    )
    db.add_all([consumer, partner])
    await db.flush()

    store = Store(
        owner_id=partner.id,
        name="Bếp Xanh QR",
        address="10 Nguyễn Huệ, Q.1, TP.HCM",
        location="POINT(106.700806 10.776889)",
        kyc_status=KycStatus.APPROVED,
    )
    db.add(store)
    await db.flush()

    dish = Dish(
        store_id=store.id,
        name="Cơm sườn cuối ca",
        category=ItemCategory.RICE,
        original_price=Decimal("50000.00"),
        rescue_price=Decimal("25000.00"),
        pickup_start_time=time(10, 0),
        pickup_end_time=time(20, 0),
        total_quantity=5,
        remaining_quantity=4,
    )
    db.add(dish)
    await db.flush()

    order = Order(
        order_code=f"EB-20261112-{suffix.upper()}",
        consumer_id=consumer.id,
        store_id=store.id,
        dish_id=dish.id,
        quantity=1,
        unit_price=Decimal("25000.00"),
        total_amount=Decimal("25000.00"),
        status=order_status,
        payment_method=PaymentMethod.COD,
        pickup_deadline=pickup_deadline,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order, consumer


def _rebuild_qr_payload(params: dict[str, str]) -> str:
    """Re-encode QR query parameters without altering signature behavior."""
    return f"ecobite://pickup?{urlencode(params)}"


# ==============================================================================
# 1. Token creation, payload structure, nonce & storage
# ==============================================================================


async def test_generate_order_qr_token_success_and_persists_in_db(
    db_session: AsyncSession,
) -> None:
    """Tạo QR token thành công, lưu vào bảng qr_tokens và truy xuất được."""
    order, consumer = await _seed_order(db_session)
    service = QRService(db_session)

    token = await service.generate_order_qr_token(
        order_id=order.id,
        user_id=consumer.id,
        pickup_deadline=order.pickup_deadline,
    )

    assert isinstance(token, str)
    assert token.startswith("ecobite://pickup?")

    repo = QRTokenRepository(db_session)
    stored = await repo.get_by_order_id(order.id)
    assert stored is not None
    assert stored.order_id == order.id
    assert stored.is_used is False
    assert stored.used_at is None
    assert _as_utc(stored.expires_at) == PICKUP_DEADLINE
    assert re.fullmatch(r"[0-9a-f]{32}", stored.nonce)
    assert re.fullmatch(r"[0-9a-f]{64}", stored.token_hash)

    fetched_via_service = await service.get_qr_token_by_order_id(order.id)
    assert fetched_via_service is not None
    assert fetched_via_service.id == stored.id


async def test_generate_order_qr_token_contains_required_payload_fields(
    db_session: AsyncSession,
) -> None:
    """Token QR chứa đầy đủ order_id, user_id, nonce, expires_at và chữ ký HMAC-SHA256."""
    order, consumer = await _seed_order(db_session)
    service = QRService(db_session)

    token = await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)

    parsed_url = urlparse(token)
    assert parsed_url.scheme == "ecobite"
    assert parsed_url.netloc == "pickup"

    query = parse_qs(parsed_url.query)
    assert query["order_id"][0] == str(order.id)
    assert query["user_id"][0] == str(consumer.id)
    assert re.fullmatch(r"[0-9a-f]{32}", query["nonce"][0])
    assert _as_utc(datetime.fromisoformat(query["expires_at"][0])) == PICKUP_DEADLINE
    assert re.fullmatch(r"[0-9a-f]{64}", query["sig"][0])


async def test_generate_order_qr_token_uses_secure_unique_nonce(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nonce được sinh bằng secrets.token_hex(16) và không trùng giữa các đơn."""
    calls: list[int] = []
    real_token_hex = qr_service_module.secrets.token_hex

    def spy_token_hex(nbytes: int | None = None) -> str:
        assert nbytes == 16
        calls.append(nbytes)
        return real_token_hex(nbytes)

    monkeypatch.setattr(qr_service_module.secrets, "token_hex", spy_token_hex)

    order_1, consumer_1 = await _seed_order(db_session)
    order_2, consumer_2 = await _seed_order(db_session)
    service = QRService(db_session)

    token_1 = await service.generate_order_qr_token(
        order_1.id, consumer_1.id, order_1.pickup_deadline
    )
    token_2 = await service.generate_order_qr_token(
        order_2.id, consumer_2.id, order_2.pickup_deadline
    )

    nonce_1 = parse_qs(urlparse(token_1).query)["nonce"][0]
    nonce_2 = parse_qs(urlparse(token_2).query)["nonce"][0]

    assert len(calls) == 2
    assert nonce_1 != nonce_2


async def test_generate_order_qr_token_rejects_duplicate_token_for_same_order(
    db_session: AsyncSession,
) -> None:
    """Mỗi đơn hàng chỉ có 1 QRToken duy nhất (quan hệ 1-1 trên order_id)."""
    order, consumer = await _seed_order(db_session)
    service = QRService(db_session)
    await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)

    with pytest.raises(HTTPException) as exc_info:
        await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)

    assert exc_info.value.status_code == 409


# ==============================================================================
# 2. HMAC verification, tampering, invalid signature, expiry & not found
# ==============================================================================


async def test_hmac_signature_is_valid_and_verifies_successfully(
    db_session: AsyncSession,
) -> None:
    """Chữ ký HMAC-SHA256 khớp chuẩn và verify_qr_token xác thực thành công trước hạn."""
    order, consumer = await _seed_order(db_session)
    service = QRService(db_session)

    token = await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)
    params = {k: v[0] for k, v in parse_qs(urlparse(token).query).items()}

    canonical_msg = (
        f"{params['order_id']}:{params['user_id']}:{params['nonce']}:{params['expires_at']}"
    )
    expected_sig = hmac.new(
        settings.qr_signing_key.encode("utf-8"),
        canonical_msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert hmac.compare_digest(params["sig"], expected_sig)

    verified = await service.verify_qr_token(token, now=FIXED_NOW)
    assert verified.order_id == order.id
    assert verified.is_used is False


@pytest.mark.parametrize(
    ("field", "tampered_value"),
    [
        ("order_id", str(uuid.uuid4())),
        ("user_id", str(uuid.uuid4())),
        ("nonce", "0" * 32),
        ("expires_at", "2099-01-01T00:00:00Z"),
    ],
)
async def test_tampered_payload_is_detected_and_rejected(
    db_session: AsyncSession,
    field: str,
    tampered_value: str,
) -> None:
    """Chỉnh sửa bất kỳ trường nào trong payload phải bị từ chối với HTTP 400."""
    order, consumer = await _seed_order(db_session)
    service = QRService(db_session)
    token = await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)

    params = {k: v[0] for k, v in parse_qs(urlparse(token).query).items()}
    params[field] = tampered_value
    tampered_token = _rebuild_qr_payload(params)

    with pytest.raises(HTTPException) as exc_info:
        await service.verify_qr_token(tampered_token, now=FIXED_NOW)

    assert exc_info.value.status_code == 400


async def test_invalid_signature_and_malformed_payload_are_rejected(
    db_session: AsyncSession,
) -> None:
    """Chữ ký giả mạo hoặc payload sai định dạng phải bị từ chối với HTTP 400."""
    order, consumer = await _seed_order(db_session)
    service = QRService(db_session)
    token = await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)

    params = {k: v[0] for k, v in parse_qs(urlparse(token).query).items()}
    first_char = "1" if params["sig"][0] == "0" else "0"
    params["sig"] = first_char + params["sig"][1:]

    with pytest.raises(HTTPException) as sig_exc:
        await service.verify_qr_token(_rebuild_qr_payload(params), now=FIXED_NOW)
    assert sig_exc.value.status_code == 400

    with pytest.raises(HTTPException) as fmt_exc:
        await service.verify_qr_token("not-a-valid-ecobite-qr", now=FIXED_NOW)
    assert fmt_exc.value.status_code == 400


async def test_verify_qr_token_uses_hmac_compare_digest(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """So sánh chữ ký bắt buộc đi qua hmac.compare_digest chống timing attack."""
    order, consumer = await _seed_order(db_session)
    service = QRService(db_session)
    token = await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)

    compare_calls: list[tuple[str, str]] = []
    real_compare = qr_service_module.hmac.compare_digest

    def spy_compare(a: str, b: str) -> bool:
        compare_calls.append((a, b))
        return real_compare(a, b)

    monkeypatch.setattr(qr_service_module.hmac, "compare_digest", spy_compare)

    await service.verify_qr_token(token, now=FIXED_NOW)
    assert len(compare_calls) >= 1


async def test_expired_token_is_rejected(db_session: AsyncSession) -> None:
    """Token quá thời hạn sử dụng phải bị từ chối với HTTP 400."""
    order, consumer = await _seed_order(db_session, pickup_deadline=PICKUP_DEADLINE)
    service = QRService(db_session)
    token = await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)

    with pytest.raises(HTTPException) as exc_info:
        await service.verify_qr_token(token, now=PICKUP_DEADLINE + timedelta(seconds=1))

    assert exc_info.value.status_code == 400
    assert "hết hạn" in str(exc_info.value.detail).lower()


async def test_missing_token_in_database_raises_404_and_repo_returns_none(
    db_session: AsyncSession,
) -> None:
    """Không tìm thấy token trong DB phải trả None ở repo và HTTP 404 ở service."""
    repo = QRTokenRepository(db_session)
    assert await repo.get_by_order_id(uuid.uuid4()) is None
    assert await repo.get_by_nonce("nonexistent-nonce") is None

    service = QRService(db_session)
    fake_order_id = uuid.uuid4()
    fake_user_id = uuid.uuid4()
    fake_nonce = "a" * 32
    expires_raw = "2026-11-12T12:00:00Z"
    sig = hmac.new(
        settings.qr_signing_key.encode(),
        f"{fake_order_id}:{fake_user_id}:{fake_nonce}:{expires_raw}".encode(),
        hashlib.sha256,
    ).hexdigest()
    unpersisted_token = _rebuild_qr_payload(
        {
            "order_id": str(fake_order_id),
            "user_id": str(fake_user_id),
            "nonce": fake_nonce,
            "expires_at": expires_raw,
            "sig": sig,
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.verify_qr_token(unpersisted_token, now=FIXED_NOW)

    assert exc_info.value.status_code == 404


async def test_atomic_mark_token_as_used_prevents_replay_attack(
    db_session: AsyncSession,
) -> None:
    """Repository mark_token_as_used chỉ thành công 1 lần và service chặn quét lần 2."""
    order, consumer = await _seed_order(db_session)
    service = QRService(db_session)
    repo = QRTokenRepository(db_session)

    token = await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)
    stored = await repo.get_by_order_id(order.id)
    assert stored is not None

    first_mark = await repo.mark_token_as_used(stored.id, used_at=FIXED_NOW)
    assert first_mark is not None
    assert first_mark.is_used is True
    assert first_mark.used_at is not None

    second_mark = await repo.mark_token_as_used(stored.id, used_at=FIXED_NOW)
    assert second_mark is None

    with pytest.raises(HTTPException) as exc_info:
        await service.verify_qr_token(token, now=FIXED_NOW)

    assert exc_info.value.status_code == 400
    assert "đã được sử dụng" in str(exc_info.value.detail)


# ==============================================================================
# 3. Configuration secret key handling & zero secret leakage
# ==============================================================================


async def test_secret_key_comes_from_settings_not_hardcoded_and_never_leaks(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Thay đổi secret trong settings làm thay đổi chữ ký và không làm lộ key ra log/token."""
    order, consumer = await _seed_order(db_session)
    service = QRService(db_session)

    secret_one = "super-sensitive-qr-secret-alpha-001"
    secret_two = "super-sensitive-qr-secret-beta-002"

    monkeypatch.setattr(settings, "QR_SIGNATURE_SECRET", secret_one)
    with caplog.at_level(logging.DEBUG):
        token = await service.generate_order_qr_token(order.id, consumer.id, order.pickup_deadline)

    assert secret_one not in token
    assert secret_one not in caplog.text

    # Đổi secret trong settings -> chữ ký cũ phải bị từ chối ngay
    monkeypatch.setattr(settings, "QR_SIGNATURE_SECRET", secret_two)
    with caplog.at_level(logging.DEBUG), pytest.raises(HTTPException) as exc_info:
        await service.verify_qr_token(token, now=FIXED_NOW)

    assert exc_info.value.status_code == 400
    assert secret_one not in str(exc_info.value.detail)
    assert secret_two not in str(exc_info.value.detail)
    assert secret_two not in caplog.text


async def test_empty_qr_secret_in_settings_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Không tự động fallback sang chuỗi hardcode nếu secret bị cấu hình rỗng."""
    monkeypatch.setattr(settings, "QR_SIGNATURE_SECRET", "")
    monkeypatch.setattr(settings, "SECRET_KEY", "")

    with pytest.raises(ValueError):
        _ = settings.qr_signing_key
