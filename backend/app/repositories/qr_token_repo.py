"""Repository for single-use Dynamic QRToken persistence and atomic redemption."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import QRToken


class QRTokenRepository:
    """Data access layer for `qr_tokens` with atomic anti-replay redemption."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_qr_token(
        self,
        *,
        order_id: uuid.UUID,
        token_hash: str,
        nonce: str,
        expires_at: datetime,
        is_used: bool = False,
        commit: bool = True,
    ) -> QRToken:
        """Persist a new QRToken record linked 1-to-1 with an Order."""
        qr_token = QRToken(
            order_id=order_id,
            token_hash=token_hash,
            nonce=nonce,
            expires_at=expires_at,
            is_used=is_used,
        )
        self.db.add(qr_token)
        if commit:
            await self.db.commit()
            await self.db.refresh(qr_token)
        else:
            await self.db.flush()
        return qr_token

    async def get_by_id(self, token_id: uuid.UUID) -> QRToken | None:
        """Retrieve a QRToken by primary key UUID."""
        return await self.db.get(QRToken, token_id)

    async def get_by_order_id(self, order_id: uuid.UUID) -> QRToken | None:
        """Retrieve the QRToken bound to an order, eager-loading its Order."""
        stmt = (
            select(QRToken).options(selectinload(QRToken.order)).where(QRToken.order_id == order_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_nonce(self, nonce: str) -> QRToken | None:
        """Retrieve a QRToken by its unique cryptographic single-use nonce."""
        stmt = select(QRToken).options(selectinload(QRToken.order)).where(QRToken.nonce == nonce)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> QRToken | None:
        """Retrieve a QRToken by its stored HMAC-SHA256 digest."""
        stmt = (
            select(QRToken)
            .options(selectinload(QRToken.order))
            .where(QRToken.token_hash == token_hash)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_token_as_used(
        self,
        token_id: uuid.UUID,
        *,
        used_at: datetime | None = None,
        commit: bool = True,
    ) -> QRToken | None:
        """Atomically mark a QRToken as used only if `is_used` is still False.

        Executes:
            UPDATE qr_tokens SET is_used = TRUE, used_at = :used_at
            WHERE id = :token_id AND is_used IS FALSE

        Prevents Replay Attack / concurrent double-scan race conditions (Guardrail #3).
        """
        resolved_used_at = used_at if used_at is not None else datetime.now(UTC)
        stmt = (
            update(QRToken)
            .where(
                QRToken.id == token_id,
                QRToken.is_used.is_(False),
            )
            .values(is_used=True, used_at=resolved_used_at)
            .execution_options(synchronize_session=False)
        )
        result = await self.db.execute(stmt)
        if getattr(result, "rowcount", 0) == 0:
            return None

        if commit:
            await self.db.commit()
        else:
            await self.db.flush()

        qr_token = await self.get_by_id(token_id)
        if qr_token is not None:
            await self.db.refresh(qr_token)
        return qr_token
