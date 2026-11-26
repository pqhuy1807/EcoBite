"""Business logic for VNPay payment processing: URL generation, IPN handling, return verification.

Complies strictly with:
- Guardrail #3: HMAC-SHA512 signature verification for IPN, idempotent processing.
- Guardrail #4: Redis distributed lock for idempotent IPN processing.
"""

import hashlib
import hmac
import logging
import urllib.parse
import uuid
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import distributed_lock
from app.models.order import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.repositories import dish_repo, order_repo, payment_repo

logger = logging.getLogger(__name__)

# VNPay API v2.1.0 endpoint. Override via settings.VNP_URL (sandbox by default).


class PaymentService:
    """Coordinate VNPay payment flows: generate payment URL, process IPN, verify return."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.orders = order_repo.OrderRepository(db)
        self.payments = payment_repo.PaymentTransactionRepository(db)

    async def create_vnpay_payment_url(
        self,
        order_id: str,
        consumer_id: str,
        client_ip: str,
        bank_code: str | None = None,
    ) -> dict[str, Any]:
        """Generate a VNPay payment URL for the order.

        Args:
            order_id: Order ID (string format to match VNPay expectation)
            consumer_id: Consumer ID (string format to match VNPay expectation)
            client_ip: Client IP address for VNPay audit
            bank_code: Optional bank code (e.g., "VNPAYQR", "NCB")

        Returns:
            dict with 'payment_url' and 'txn_ref' for redirection

        Raises:
            HTTPException 404: Order not found
            HTTPException 403: Order not owned by consumer
            HTTPException 409: Invalid payment method or status
            HTTPException 410: Order expired or cancelled
        """
        # 1. Retrieve order and validate ownership
        order = await self.orders.get_by_id(uuid.UUID(order_id))

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        if str(order.consumer_id) != consumer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thanh toán đơn hàng này",
            )

        # 2. Validate payment method
        if order.payment_method != PaymentMethod.VNPAY:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chỉ đơn hàng thanh toán VNPay mới có thể tạo URL thanh toán",
            )

        # 3. Validate payment status
        if order.payment_status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Đơn hàng đã được thanh toán hoặc có giao dịch thanh toán trước đó",
            )

        # 4. Check order lifecycle status
        if order.status in (
            OrderStatus.CANCELLED,
            OrderStatus.EXPIRED,
            OrderStatus.COMPLETED,
        ):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Đơn hàng không còn hiệu lực để thanh toán",
            )

        # 5. Build VNPay payment request parameters
        # Vietnam local time (Asia/Ho_Chi_Minh, UTC+7) with safe fallback.
        try:
            vietnam_tz: tzinfo = ZoneInfo("Asia/Ho_Chi_Minh")
        except ZoneInfoNotFoundError:
            # tzdata unavailable: fall back to fixed UTC+7 offset.
            vietnam_tz = timezone(timedelta(hours=7))
        now_vietnam = datetime.now(vietnam_tz)
        txn_ref = order.order_code

        # Amount in VND cents
        vnp_amount = int(order.total_amount * 100)

        # VNPay requires date/time in format: YYYYMMDDHHMMSS (Hà Nội, UTC+7)
        vnp_create_date = now_vietnam.strftime("%Y%m%d%H%M%S")

        # Build parameter dict
        vnp_params: dict[str, Any] = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": settings.VNP_TMN_CODE,
            "vnp_TxnRef": txn_ref,
            "vnp_OrderInfo": f"Thanh toan don hang {txn_ref}",
            "vnp_OrderType": "food_rescue",
            "vnp_Amount": str(vnp_amount),
            "vnp_CreateDate": vnp_create_date,
            "vnp_CurrCode": "VND",
            "vnp_BankCode": bank_code or "",
            "vnp_IpAddr": client_ip,
            "vnp_Locale": "vn",
            "vnp_ReturnUrl": settings.VNP_RETURN_URL,
        }

        # 6. Generate HMAC-SHA512 signature
        vnp_secure_hash = self._generate_vnpay_hash(vnp_params)

        vnp_params["vnp_SecureHash"] = vnp_secure_hash

        # 7. Build final payment URL
        payment_url = f"{settings.VNP_URL}?{urllib.parse.urlencode(vnp_params)}"

        return {
            "payment_url": payment_url,
            "txn_ref": txn_ref,
            "vnp_amount": vnp_amount,
        }

    @staticmethod
    def _generate_vnpay_hash(params: dict[str, Any]) -> str:
        """Generate HMAC-SHA512 signature for VNPay request/response.

        Args:
            params: Dictionary of VNPay parameters (excluding vnp_SecureHash)

        Returns:
            Hex string of HMAC-SHA512 signature
        """
        # Sort keys alphabetically
        sorted_params = dict(sorted(params.items()))

        # Build query string without vnp_SecureHash.
        # VNPay requires each value to be URL-encoded (quote_plus) before signing,
        # and verification must use the exact same encoding to stay consistent
        # with both request generation and IPN/return verification.
        hash_data = "&".join(
            f"{key}={urllib.parse.quote_plus(str(value))}"
            for key, value in sorted_params.items()
            if value
        )

        # Generate HMAC-SHA512
        secret_key = settings.VNP_HASH_SECRET
        if not secret_key:
            raise ValueError("VNP_HASH_SECRET is not configured")

        hmac_hash = hmac.new(
            secret_key.encode("utf-8"),
            hash_data.encode("utf-8"),
            hashlib.sha512,
        )

        return hmac_hash.hexdigest()

    async def process_vnpay_ipn(
        self,
        query_params: dict[str, Any],
    ) -> dict[str, Any]:
        """Process Instant Payment Notification (IPN) from VNPay.

        This endpoint must be idempotent - processing the same IPN multiple times
        must not create duplicate transactions or cause double payment.

        Args:
            query_params: Full VNPay IPN payload (dict from request query string)

        Returns:
            dict with 'RspCode' and 'Message' for VNPay IPN response

        VNPay RspCode meanings:
            "00": Success - transaction verified and processed
            "01": Missing vnp_TxnRef
            "02": Duplicate transaction (already processed)
            "04": Amount mismatch
            "09": Invalid order ID
            "15": Invalid IP address
            "24": User cancelled
            "51": Insufficient funds
            "77": Invalid card information
            "97": Invalid signature (HMAC-SHA512 verification failed)
        """
        # 1. Check required vnp_TxnRef
        txn_ref = query_params.get("vnp_TxnRef")
        if not txn_ref:
            logger.warning("IPN missing required vnp_TxnRef")
            return {"RspCode": "01", "Message": "Missing transaction reference"}

        # 2. Verify HMAC-SHA512 signature
        if not self._verify_vnpay_ipn_signature(query_params):
            logger.warning("IPN signature verification failed for txn_ref=%s", txn_ref)
            return {"RspCode": "97", "Message": "Invalid signature"}

        # 3. Extract key fields from IPN payload
        vnp_amount = query_params.get("vnp_Amount")
        vnp_response_code = query_params.get("vnp_ResponseCode", "")
        vnp_transaction_no = query_params.get("vnp_TransactionNo", "")
        vnp_bank_code = query_params.get("vnp_BankCode", "")

        if vnp_amount is None:
            logger.error("IPN missing vnp_Amount for txn_ref=%s", txn_ref)
            return {"RspCode": "04", "Message": "Missing amount"}

        # Amount in VND cents -> Decimal VND
        amount_vnd = Decimal(str(vnp_amount)) / Decimal(100)

        # 4. Retrieve order by txn_ref (order_code)
        order = await self.orders.get_by_order_code(txn_ref)

        if order is None:
            logger.warning("IPN for non-existent order txn_ref=%s", txn_ref)
            return {"RspCode": "09", "Message": "Order not found"}

        # 5. Check amount matches
        if order.total_amount != amount_vnd:
            logger.error(
                "IPN amount mismatch for txn_ref=%s: expected %s, got %s",
                txn_ref,
                order.total_amount,
                amount_vnd,
            )
            return {"RspCode": "04", "Message": "Amount mismatch"}

        # 6. Use Redis distributed lock for idempotent processing
        lock_key = f"lock:payment:ipn:{txn_ref}"

        async with distributed_lock(lock_key, timeout_seconds=30) as acquired:
            if not acquired:
                # Lock acquisition failed - another worker is processing
                logger.info("IPN processing locked for txn_ref=%s, waiting for completion", txn_ref)
                # Check if transaction already exists and is verified
                existing = await self.payments.get_verified_by_txn_ref(txn_ref)
                if existing and existing.is_verified:
                    logger.info("IPN already processed for txn_ref=%s", txn_ref)
                    return {"RspCode": "00", "Message": "Success"}
                # Another worker is still processing; avoid racing and let it
                # complete. Returning success tells VNPay not to retry while the
                # other worker finalizes the transaction.
                logger.info("IPN still being processed for txn_ref=%s", txn_ref)
                return {"RspCode": "00", "Message": "Success"}

            # 7. Check for duplicate processing
            existing_transaction = await self.payments.get_by_txn_ref(txn_ref)

            if existing_transaction and existing_transaction.is_verified:
                logger.info("Duplicate IPN already verified for txn_ref=%s", txn_ref)
                return {"RspCode": "02", "Message": "Transaction already processed"}

            # 8. Process based on VNPay response code
            if vnp_response_code == "00":
                # Payment successful
                return await self._process_successful_payment(
                    order=order,
                    txn_ref=txn_ref,
                    amount_vnd=amount_vnd,
                    vnp_transaction_no=vnp_transaction_no,
                    vnp_bank_code=vnp_bank_code,
                    raw_ipn_payload=dict(query_params),
                )
            else:
                # Payment failed - update order status and restore inventory
                return await self._process_failed_payment(
                    order=order,
                    txn_ref=txn_ref,
                    vnp_response_code=vnp_response_code,
                    vnp_amount=vnp_amount,
                    raw_ipn_payload=dict(query_params),
                )

    async def _process_successful_payment(
        self,
        order: Order,
        txn_ref: str,
        amount_vnd: Decimal,
        vnp_transaction_no: str,
        vnp_bank_code: str,
        raw_ipn_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Process successful VNPay payment - mark order as paid and record transaction."""
        # Create verified payment transaction
        transaction = await self.payments.create_transaction(
            order_id=order.id,
            txn_ref=txn_ref,
            amount=amount_vnd,
            vnp_transaction_no=vnp_transaction_no,
            vnp_bank_code=vnp_bank_code,
            vnp_response_code="00",
            raw_ipn_payload=raw_ipn_payload,
            commit=False,
        )
        # The IPN HMAC-SHA512 was already verified upstream, so mark the
        # transaction as verified. This is what makes the duplicate-IPN
        # idempotency check (`get_by_txn_ref` + `is_verified`) actually work.
        transaction.is_verified = True

        # Idempotency: do not re-confirm an order that is already paid.
        if order.payment_status == PaymentStatus.PAID:
            await self.db.commit()
            await self.db.refresh(transaction)
            await self.db.refresh(order)
            logger.info(
                "Payment already processed for order_id=%s, txn_ref=%s",
                order.id,
                txn_ref,
            )
            return {"RspCode": "02", "Message": "Transaction already processed"}

        # Update order payment status
        order.payment_status = PaymentStatus.PAID
        order.vnpay_transaction_no = vnp_transaction_no
        order.vnpay_bank_code = vnp_bank_code
        order.vnpay_pay_date = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(transaction)
        await self.db.refresh(order)

        logger.info(
            "Payment successful for order_id=%s, txn_ref=%s, amount=%s",
            order.id,
            txn_ref,
            amount_vnd,
        )

        return {"RspCode": "00", "Message": "Success"}

    async def _process_failed_payment(
        self,
        order: Order,
        txn_ref: str,
        vnp_response_code: str,
        vnp_amount: str,
        raw_ipn_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Process failed VNPay payment - mark order as failed and restore inventory."""
        # Status-transition integrity: only fail/cancel orders that are still
        # pending payment. A completed or already-cancelled order must not be
        # transitioned again, and its stock must not be restored twice.
        if order.payment_status != PaymentStatus.PENDING or order.status not in (
            OrderStatus.CONFIRMED,
            OrderStatus.READY_FOR_PICKUP,
        ):
            logger.warning(
                "Failed IPN ignored for non-pending order_id=%s, txn_ref=%s "
                "(status=%s, payment_status=%s)",
                order.id,
                txn_ref,
                order.status,
                order.payment_status,
            )
            return {"RspCode": "02", "Message": "Transaction already processed"}

        # Create unverified payment transaction for audit
        transaction = await self.payments.create_transaction(
            order_id=order.id,
            txn_ref=txn_ref,
            amount=Decimal(str(vnp_amount)) / Decimal(100),
            vnp_response_code=vnp_response_code,
            raw_ipn_payload=raw_ipn_payload,
            commit=False,
        )

        # Restore inventory atomically using dish_repo
        restored = await dish_repo.atomic_increment_quantity(
            self.db,
            order.dish_id,
            order.quantity,
            commit=False,
        )

        if restored is None:
            await self.db.rollback()
            logger.error(
                "Failed to restore inventory for failed payment txn_ref=%s, order_id=%s",
                txn_ref,
                order.id,
            )
            return {"RspCode": "09", "Message": "Failed to restore inventory"}

        # Update order status to FAILED and cancel the order
        order.payment_status = PaymentStatus.FAILED
        order.status = OrderStatus.CANCELLED

        await self.db.commit()
        await self.db.refresh(transaction)
        await self.db.refresh(order)

        logger.warning(
            "Payment failed for order_id=%s, txn_ref=%s, RspCode=%s",
            order.id,
            txn_ref,
            vnp_response_code,
        )

        return {"RspCode": "00", "Message": "Payment failed"}

    @staticmethod
    def verify_vnpay_return(
        query_params: dict[str, Any],
    ) -> tuple[bool, str, str]:
        """Verify HMAC-SHA512 signature for VNPay return URL (client-side redirect).

        This endpoint supports debugging and manual verification when IPN
        is not publicly accessible. It does NOT process the payment.

        Args:
            query_params: Full VNPay return URL query parameters

        Returns:
            Tuple of (is_valid, message, txn_ref)

        Note: This only verifies the signature. It does NOT update any order status.
        """
        # 1. Check required vnp_TxnRef
        txn_ref = query_params.get("vnp_TxnRef")
        if not txn_ref:
            return (False, "Missing transaction reference", "")

        # 2. Verify HMAC-SHA512 signature
        is_valid = PaymentService._verify_vnpay_ipn_signature(query_params)

        if not is_valid:
            logger.warning("Return URL signature verification failed for txn_ref=%s", txn_ref)
            return (False, "Invalid signature", txn_ref)

        return (True, "Signature verified", txn_ref)

    @staticmethod
    def _verify_vnpay_ipn_signature(params: dict[str, Any]) -> bool:
        """Verify HMAC-SHA512 signature for VNPay IPN/return.

        Args:
            params: VNPay parameters including vnp_SecureHash

        Returns:
            True if signature is valid, False otherwise
        """
        # Extract and remove the signature for verification
        provided_hash = params.get("vnp_SecureHash")
        if not provided_hash:
            logger.warning("Missing vnp_SecureHash in parameters")
            return False

        # Remove vnp_SecureHash and vnp_SecureHashType for hash computation (VNPay spec)
        params_without_hash = {
            k: v for k, v in params.items() if k not in ("vnp_SecureHash", "vnp_SecureHashType")
        }

        # Generate expected hash
        expected_hash = PaymentService._generate_vnpay_hash(params_without_hash)

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_hash, provided_hash)
