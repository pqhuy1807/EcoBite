"""Repository for PaymentTransaction persistence and VNPay IPN handling."""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import PaymentTransaction


class PaymentTransactionRepository:
    """Async data access layer for VNPay payment transactions.

    Encapsulates every SQLAlchemy command so that app.services stays free of
    persistence concerns. Lookups eagerly load the order relationship
    to avoid N+1 queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_transaction(
        self,
        order_id: uuid.UUID,
        txn_ref: str,
        amount: Decimal,
        *,
        vnp_transaction_no: str | None = None,
        vnp_bank_code: str | None = None,
        vnp_response_code: str = "00",
        raw_ipn_payload: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> PaymentTransaction:
        """Persist a new PaymentTransaction record.

        Set commit=False when the transaction must be saved together with
        other database changes in a single transaction.

        Args:
            order_id: ID of the order being paid
            txn_ref: VNPay transaction reference (vnp_TxnRef)
            amount: Payment amount in VND
            vnp_transaction_no: VNPay system transaction number (optional)
            vnp_bank_code: Customer's bank code (optional)
            vnp_response_code: VNPay response code (default "00" for success)
            raw_ipn_payload: Full VNPay IPN webhook payload for audit
            commit: Whether to commit immediately or flush only

        Returns:
            The created PaymentTransaction instance
        """
        transaction = PaymentTransaction(
            order_id=order_id,
            payment_provider="VNPAY",
            txn_ref=txn_ref,
            amount=amount,
            vnp_transaction_no=vnp_transaction_no,
            vnp_bank_code=vnp_bank_code,
            vnp_response_code=vnp_response_code,
            is_verified=False,
            raw_ipn_payload=raw_ipn_payload or {},
        )
        self.db.add(transaction)

        if commit:
            await self.db.commit()
            await self.db.refresh(transaction)
        else:
            await self.db.flush()

        return transaction

    async def get_verified_by_txn_ref(
        self,
        txn_ref: str,
    ) -> PaymentTransaction | None:
        """Retrieve a verified payment transaction by VNPay transaction reference.

        Args:
            txn_ref: VNPay transaction reference (vnp_TxnRef)

        Returns:
            PaymentTransaction if found and verified, None otherwise
        """
        stmt = (
            select(PaymentTransaction)
            .where(
                PaymentTransaction.txn_ref == txn_ref,
                PaymentTransaction.is_verified == True,
            )
            .options(
                selectinload(PaymentTransaction.order),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_order_id(
        self,
        order_id: uuid.UUID,
    ) -> list[PaymentTransaction]:
        """Retrieve payment transaction history for an order.

        Args:
            order_id: ID of the order

        Returns:
            List of payment transactions for the order, newest first
        """
        stmt = (
            select(PaymentTransaction)
            .where(PaymentTransaction.order_id == order_id)
            .order_by(PaymentTransaction.created_at.desc(), PaymentTransaction.id.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def verify_transaction(
        self,
        transaction_id: uuid.UUID,
        *,
        commit: bool = True,
    ) -> PaymentTransaction | None:
        """Mark a payment transaction as verified.

        This should be called after successfully validating the HMAC-SHA512
        signature from VNPay IPN webhook.

        Args:
            transaction_id: ID of the payment transaction
            commit: Whether to commit immediately or flush only

        Returns:
            The updated PaymentTransaction instance, or None if not found
        """
        transaction = await self.db.get(PaymentTransaction, transaction_id)

        if transaction is None:
            return None

        transaction.is_verified = True
        transaction.vnp_response_code = "00"

        if commit:
            await self.db.commit()
            await self.db.refresh(transaction)
        else:
            await self.db.flush()

        return transaction

    async def get_by_txn_ref(
        self,
        txn_ref: str,
    ) -> PaymentTransaction | None:
        """Retrieve a payment transaction by VNPay transaction reference.

        Args:
            txn_ref: VNPay transaction reference (vnp_TxnRef)

        Returns:
            PaymentTransaction if found, None otherwise
        """
        stmt = (
            select(PaymentTransaction)
            .where(PaymentTransaction.txn_ref == txn_ref)
            .options(
                selectinload(PaymentTransaction.order),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
