"""Unit tests for PaymentService: HMAC-SHA512, IPN processing, idempotency, atomic rollback."""

import hashlib
import hmac
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.models.order import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.services.payment_service import PaymentService

# ==============================================================================
# 1. HMAC-SHA512 Signature Tests
# ==============================================================================


class TestPaymentServiceHMACSignature:
    """Test HMAC-SHA512 signature generation and verification."""

    def test_generate_vnpay_hash_creates_valid_signature(self) -> None:
        """Test that HMAC-SHA512 signature is generated correctly."""
        mock_db = MagicMock()
        service = PaymentService(mock_db)

        # Mock VNP_HASH_SECRET
        with patch("app.services.payment_service.settings.VNP_HASH_SECRET", "test_secret"):
            # Test params (sorted alphabetically for VNPay)
            params = {
                "vnp_Amount": "1000000",
                "vnp_BankCode": "VNPAYQR",
                "vnp_CreateDate": "20261118120000",
                "vnp_CurrCode": "VND",
                "vnp_IpAddr": "127.0.0.1",
                "vnp_Locale": "vn",
                "vnp_OrderInfo": "Thanh toan don hang EB20261118",
                "vnp_ReturnUrl": "http://localhost:3000/payment/return",
                "vnp_TmnCode": "TESTTMNCODE",
                "vnp_TxnRef": "EB20261118",
                "vnp_Version": "2.1.0",
                "vnp_Command": "pay",
            }

            # Generate signature
            signature = service._generate_vnpay_hash(params)

            # Verify signature is 128-char hex string (SHA512 = 512 bits = 64 bytes = 128 hex chars)
            assert len(signature) == 128
            assert all(c in "0123456789abcdef" for c in signature)

            # Verify signature matches expected value
            sorted_params = dict(sorted(params.items()))
            hash_data = "&".join(f"{key}={value}" for key, value in sorted_params.items() if value)
            expected_hash = hmac.new(
                b"test_secret",
                hash_data.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()

            assert signature == expected_hash

    def test_verify_vnpay_ipn_signature_valid(self) -> None:
        """Test that valid HMAC-SHA512 signature is verified correctly."""
        mock_db = MagicMock()
        service = PaymentService(mock_db)

        with patch("app.services.payment_service.settings.VNP_HASH_SECRET", "test_secret"):
            params = {
                "vnp_TxnRef": "EB20261118",
                "vnp_Amount": "1000000",
                "vnp_ResponseCode": "00",
            }

            # Generate valid signature
            signature = service._generate_vnpay_hash(params)
            params["vnp_SecureHash"] = signature

            # Verify signature
            assert service._verify_vnpay_ipn_signature(params) is True

    def test_verify_vnpay_ipn_signature_invalid(self) -> None:
        """Test that invalid HMAC-SHA512 signature is rejected."""
        mock_db = MagicMock()
        service = PaymentService(mock_db)

        params = {
            "vnp_TxnRef": "EB20261118",
            "vnp_Amount": "1000000",
            "vnp_ResponseCode": "00",
            "vnp_SecureHash": "invalid_signature_here",
        }

        with patch("app.services.payment_service.settings.VNP_HASH_SECRET", "test_secret"):
            assert service._verify_vnpay_ipn_signature(params) is False

    def test_verify_vnpay_ipn_signature_missing_hash(self) -> None:
        """Test that missing vnp_SecureHash returns False."""
        mock_db = MagicMock()
        service = PaymentService(mock_db)

        params = {
            "vnp_TxnRef": "EB20261118",
            "vnp_Amount": "1000000",
        }

        assert service._verify_vnpay_ipn_signature(params) is False


# ==============================================================================
# 2. IPN Processing Tests
# ==============================================================================


class TestPaymentServiceIPNProcessing:
    """Test VNPay IPN processing with various scenarios."""

    @pytest.mark.asyncio
    async def test_process_vnpay_ipn_missing_txn_ref(self) -> None:
        """Test IPN processing rejects missing vnp_TxnRef."""
        mock_db = AsyncMock()
        service = PaymentService(mock_db)

        result = await service.process_vnpay_ipn({})

        assert result["RspCode"] == "01"
        assert result["Message"] == "Missing transaction reference"

    @pytest.mark.asyncio
    async def test_process_vnpay_ipn_invalid_signature(self) -> None:
        """Test IPN processing rejects invalid signature."""
        mock_db = AsyncMock()
        service = PaymentService(mock_db)

        # Mock VNP_HASH_SECRET
        with patch("app.services.payment_service.settings.VNP_HASH_SECRET", "test_secret"):
            params = {
                "vnp_TxnRef": "EB20261118",
                "vnp_Amount": "1000000",
                "vnp_ResponseCode": "00",
                "vnp_SecureHash": "invalid",
            }

            result = await service.process_vnpay_ipn(params)

            assert result["RspCode"] == "97"
            assert "Invalid signature" in result["Message"]

    @pytest.mark.asyncio
    async def test_process_vnpay_ipn_amount_mismatch(self) -> None:
        """Test IPN processing rejects amount mismatch."""
        mock_db = AsyncMock()
        service = PaymentService(mock_db)

        # Mock order with different amount
        mock_order = MagicMock(spec=Order)
        mock_order.total_amount = Decimal("10000.00")
        mock_order.order_code = "EB20261118"
        service.orders.get_by_order_code = AsyncMock(return_value=mock_order)

        params = {
            "vnp_TxnRef": "EB20261118",
            "vnp_Amount": "1500000",  # 15000.00 VND (mismatch)
            "vnp_ResponseCode": "00",
        }
        with patch("app.services.payment_service.settings.VNP_HASH_SECRET", "test_secret"):
            params["vnp_SecureHash"] = service._generate_vnpay_hash(params)

            result = await service.process_vnpay_ipn(params)

            assert result["RspCode"] == "04"
            assert "Amount mismatch" in result["Message"]

    @pytest.mark.asyncio
    async def test_process_vnpay_ipn_failed_payment_rollback(self) -> None:
        """Test IPN processing restores inventory when payment fails."""
        mock_db = AsyncMock()
        mock_payment_repo = MagicMock()

        service = PaymentService(mock_db)
        service.payments = mock_payment_repo

        # Mock order
        mock_order = MagicMock(spec=Order)
        mock_order.total_amount = Decimal("10000.00")
        mock_order.order_code = "EB20261118"
        mock_order.dish_id = uuid.uuid4()
        mock_order.quantity = 5
        service.orders.get_by_order_code = AsyncMock(return_value=mock_order)

        # Mock payment_repo methods
        mock_payment_repo.get_by_txn_ref = AsyncMock(return_value=None)
        mock_payment_repo.get_verified_by_txn_ref = AsyncMock(return_value=None)
        mock_payment_repo.create_transaction = AsyncMock(return_value=MagicMock())

        # Mock dish_repo.atomic_increment_quantity (module function used by the service)
        mock_atomic_increment = AsyncMock(return_value=MagicMock())

        params = {
            "vnp_TxnRef": "EB20261118",
            "vnp_Amount": "1000000",
            "vnp_ResponseCode": "05",  # Failed payment
        }
        with (
            patch("app.services.payment_service.settings.VNP_HASH_SECRET", "test_secret"),
            patch("app.services.payment_service.distributed_lock") as mock_distributed_lock,
            patch(
                "app.services.payment_service.dish_repo.atomic_increment_quantity",
                mock_atomic_increment,
            ),
        ):
            lock_context = MagicMock()
            lock_context.__aenter__ = AsyncMock(return_value=True)
            lock_context.__aexit__ = AsyncMock(return_value=None)
            mock_distributed_lock.return_value = lock_context

            params["vnp_SecureHash"] = service._generate_vnpay_hash(params)

            result = await service.process_vnpay_ipn(params)

            assert result["RspCode"] == "00"
            # Inventory should be restored atomically
            mock_atomic_increment.assert_called_once()


# ==============================================================================
# 3. Idempotency Tests (Redis Distributed Lock)
# ==============================================================================


class TestPaymentServiceIdempotency:
    """Test Redis distributed lock for IPN idempotency."""

    @pytest.mark.asyncio
    @patch("app.services.payment_service.distributed_lock")
    async def test_process_vnpay_ipn_idempotent_with_lock(
        self,
        mock_distributed_lock: MagicMock,
    ) -> None:
        """Test that duplicate IPN processing is prevented with distributed lock."""
        mock_db = AsyncMock()
        service = PaymentService(mock_db)

        # Mock distributed lock to simulate lock acquired
        lock_context = MagicMock()
        lock_context.__aenter__ = AsyncMock(return_value=True)
        lock_context.__aexit__ = AsyncMock(return_value=None)
        mock_distributed_lock.return_value = lock_context

        # Mock order with matching amount
        mock_order = MagicMock(spec=Order)
        mock_order.total_amount = Decimal("10000.00")
        mock_order.order_code = "EB20261118"
        service.orders.get_by_order_code = AsyncMock(return_value=mock_order)

        # Mock payment repo: no existing/verified transaction
        mock_payment_repo = MagicMock()
        mock_payment_repo.get_by_txn_ref = AsyncMock(return_value=None)
        mock_payment_repo.get_verified_by_txn_ref = AsyncMock(
            return_value=MagicMock(is_verified=True),
        )
        mock_payment_repo.create_transaction = AsyncMock(return_value=MagicMock())
        service.payments = mock_payment_repo

        params = {
            "vnp_TxnRef": "EB20261118",
            "vnp_Amount": "1000000",
            "vnp_ResponseCode": "00",
        }
        with patch("app.services.payment_service.settings.VNP_HASH_SECRET", "test_secret"):
            params["vnp_SecureHash"] = service._generate_vnpay_hash(params)

            result = await service.process_vnpay_ipn(params)

        # Should return success for already processed transaction
        assert result["RspCode"] == "00"
        assert "Success" in result["Message"]


# ==============================================================================
# 4. Create VNPay URL Tests
# ==============================================================================


class TestPaymentServiceCreateUrl:
    """Test VNPay payment URL generation."""

    @pytest.mark.asyncio
    async def test_create_vnpay_payment_url_success(self) -> None:
        """Test successful payment URL generation."""
        mock_db = AsyncMock()
        service = PaymentService(mock_db)

        # Mock order
        mock_order = MagicMock(spec=Order)
        mock_order.id = uuid.uuid4()
        mock_order.order_code = "EB20261118"
        mock_order.total_amount = Decimal("10000.00")
        mock_order.payment_method = PaymentMethod.VNPAY
        mock_order.payment_status = PaymentStatus.PENDING
        mock_order.status = OrderStatus.CONFIRMED
        mock_order.consumer_id = uuid.uuid4()

        # Mock orders.get_by_id
        mock_order_repo = MagicMock()
        mock_order_repo.get_by_id = AsyncMock(return_value=mock_order)
        service.orders = mock_order_repo

        with patch("app.services.payment_service.settings.VNP_HASH_SECRET", "test_secret"):
            result = await service.create_vnpay_payment_url(
                order_id=str(mock_order.id),
                consumer_id=str(mock_order.consumer_id),
                client_ip="127.0.0.1",
            )

        assert "payment_url" in result
        assert "txn_ref" in result
        assert "vnp_amount" in result
        assert "vnp_SecureHash" in result["payment_url"]
        assert "vnp_ReturnUrl" in result["payment_url"]

    @pytest.mark.asyncio
    async def test_create_vnpay_payment_url_wrong_owner(self) -> None:
        """Test that payment URL generation rejects wrong owner."""
        mock_db = AsyncMock()
        service = PaymentService(mock_db)

        # Mock order owned by different user
        mock_order = MagicMock(spec=Order)
        mock_order.id = uuid.uuid4()
        mock_order.order_code = "EB20261118"
        mock_order.total_amount = Decimal("10000.00")
        mock_order.payment_method = PaymentMethod.VNPAY
        mock_order.payment_status = PaymentStatus.PENDING
        mock_order.status = OrderStatus.CONFIRMED
        mock_order.consumer_id = uuid.uuid4()  # Different user

        mock_order_repo = MagicMock()
        mock_order_repo.get_by_id = AsyncMock(return_value=mock_order)
        service.orders = mock_order_repo

        with patch("app.services.payment_service.settings.VNP_HASH_SECRET", "test_secret"):
            with pytest.raises(HTTPException) as exc_info:
                await service.create_vnpay_payment_url(
                    order_id=str(mock_order.id),
                    consumer_id=str(uuid.uuid4()),  # Wrong consumer
                    client_ip="127.0.0.1",
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
