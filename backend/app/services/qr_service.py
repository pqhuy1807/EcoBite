"""Business logic for Dynamic Single-Use HMAC-SHA256 QR Tokens (Guardrail #3)."""

import hashlib
import hmac
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlencode, urlparse

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.order import QRToken
from app.repositories.qr_token_repo import QRTokenRepository

logger = logging.getLogger(__name__)

QR_URI_SCHEME = "ecobite"
QR_URI_HOST = "pickup"
NONCE_NUM_BYTES = 16


def _ensure_utc(value: datetime) -> datetime:
    """Normalize naive (SQLite) or offset datetimes into UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _format_utc_iso(value: datetime) -> str:
    """Serialize a UTC datetime canonically with trailing `Z`."""
    return _ensure_utc(value).isoformat().replace("+00:00", "Z")


def _compute_hmac_signature(
    *,
    order_id: uuid.UUID,
    user_id: uuid.UUID,
    nonce: str,
    expires_at_raw: str,
) -> str:
    """Sign `order_id:user_id:nonce:expires_at` using the configured HMAC-SHA256 secret."""
    canonical_message = f"{order_id}:{user_id}:{nonce}:{expires_at_raw}"
    secret_bytes = settings.qr_signing_key.encode("utf-8")
    return hmac.new(
        key=secret_bytes,
        msg=canonical_message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class ParsedQRPayload:
    """Structured components decoded from an `ecobite://pickup?...` QR token string."""

    order_id: uuid.UUID
    user_id: uuid.UUID
    nonce: str
    expires_at: datetime
    expires_at_raw: str
    signature: str


class QRService:
    """Generate, store, retrieve, and cryptographically verify pickup QR tokens."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.qr_tokens = QRTokenRepository(db)

    @staticmethod
    def build_qr_payload_string(
        *,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        nonce: str,
        expires_at_raw: str,
        signature: str,
    ) -> str:
        """Assemble the canonical `ecobite://pickup?...` string encoded into QR images."""
        query = urlencode(
            {
                "order_id": str(order_id),
                "user_id": str(user_id),
                "nonce": nonce,
                "expires_at": expires_at_raw,
                "sig": signature,
            }
        )
        return f"{QR_URI_SCHEME}://{QR_URI_HOST}?{query}"

    @staticmethod
    def parse_qr_payload(qr_payload: str) -> ParsedQRPayload:
        """Decode and structurally validate an incoming QR token string."""
        if not isinstance(qr_payload, str) or not qr_payload.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã QR không hợp lệ",
            )

        parsed_url = urlparse(qr_payload.strip())
        if parsed_url.scheme != QR_URI_SCHEME or parsed_url.netloc != QR_URI_HOST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Định dạng mã QR không hợp lệ",
            )

        try:
            query_params = parse_qs(parsed_url.query, strict_parsing=True)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Định dạng mã QR không hợp lệ",
            ) from exc

        required_keys = ("order_id", "user_id", "nonce", "expires_at", "sig")
        extracted: dict[str, str] = {}
        for key in required_keys:
            values = query_params.get(key)
            if not values or len(values) != 1 or not values[0]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mã QR thiếu thông tin bắt buộc",
                )
            extracted[key] = values[0]

        try:
            order_id = uuid.UUID(extracted["order_id"])
            user_id = uuid.UUID(extracted["user_id"])
            expires_at = _ensure_utc(datetime.fromisoformat(extracted["expires_at"]))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dữ liệu mã QR không hợp lệ",
            ) from exc

        nonce = extracted["nonce"]
        if len(nonce) > 64:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dữ liệu mã QR không hợp lệ",
            )

        return ParsedQRPayload(
            order_id=order_id,
            user_id=user_id,
            nonce=nonce,
            expires_at=expires_at,
            expires_at_raw=extracted["expires_at"],
            signature=extracted["sig"],
        )

    async def generate_order_qr_token(
        self,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        pickup_deadline: datetime,
        *,
        commit: bool = True,
    ) -> str:
        """Create and persist a single-use HMAC-SHA256 QR token for an order."""
        existing = await self.qr_tokens.get_by_order_id(order_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mã QR cho đơn hàng này đã tồn tại",
            )

        expires_at = _ensure_utc(pickup_deadline)
        expires_at_raw = _format_utc_iso(expires_at)
        nonce = secrets.token_hex(NONCE_NUM_BYTES)
        signature = _compute_hmac_signature(
            order_id=order_id,
            user_id=user_id,
            nonce=nonce,
            expires_at_raw=expires_at_raw,
        )

        try:
            await self.qr_tokens.create_qr_token(
                order_id=order_id,
                token_hash=signature,
                nonce=nonce,
                expires_at=expires_at,
                is_used=False,
                commit=commit,
            )
        except IntegrityError as exc:
            if commit:
                await self.db.rollback()
            logger.warning("Duplicate QR token creation attempted for order_id=%s", order_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mã QR cho đơn hàng này đã tồn tại",
            ) from exc

        logger.info("Generated dynamic QR token for order_id=%s", order_id)
        return self.build_qr_payload_string(
            order_id=order_id,
            user_id=user_id,
            nonce=nonce,
            expires_at_raw=expires_at_raw,
            signature=signature,
        )

    async def get_qr_token_by_order_id(self, order_id: uuid.UUID) -> QRToken | None:
        """Retrieve stored QRToken metadata for an order."""
        return await self.qr_tokens.get_by_order_id(order_id)

    async def verify_qr_token(
        self,
        qr_payload: str,
        *,
        now: datetime | None = None,
    ) -> QRToken:
        """Verify HMAC-SHA256 signature, expiration, DB existence, and single-use status."""
        parsed = self.parse_qr_payload(qr_payload)

        expected_signature = _compute_hmac_signature(
            order_id=parsed.order_id,
            user_id=parsed.user_id,
            nonce=parsed.nonce,
            expires_at_raw=parsed.expires_at_raw,
        )
        if not hmac.compare_digest(parsed.signature, expected_signature):
            logger.warning("Invalid QR HMAC signature for order_id=%s", parsed.order_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chữ ký mã QR không hợp lệ",
            )

        current_time = _ensure_utc(now if now is not None else datetime.now(UTC))
        if parsed.expires_at < current_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã QR đã hết hạn sử dụng",
            )

        qr_token = await self.qr_tokens.get_by_nonce(parsed.nonce)
        if qr_token is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy mã QR",
            )

        if qr_token.order_id != parsed.order_id or not hmac.compare_digest(
            qr_token.token_hash, parsed.signature
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã QR không khớp với dữ liệu đơn hàng",
            )

        if _ensure_utc(qr_token.expires_at) < current_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã QR đã hết hạn sử dụng",
            )

        if qr_token.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã QR đã được sử dụng trước đó!",
            )

        return qr_token

