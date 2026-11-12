"""Pydantic schemas for Order, QRToken, and PaymentTransaction (Pydantic v2)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus, PaymentMethod, PaymentStatus

# ==============================================================================
# 1. Order Schemas
# ==============================================================================


class OrderBase(BaseModel):
    """Base fields for an order."""

    dish_id: uuid.UUID = Field(..., description="ID món ăn giải cứu cần mua")
    quantity: int = Field(..., gt=0, description="Số lượng suất mua (bắt buộc > 0)")
    payment_method: PaymentMethod = Field(
        default=PaymentMethod.VNPAY, description="Phương thức thanh toán: VNPAY hoặc COD"
    )


class OrderCreate(OrderBase):
    """Payload to place a new food rescue order."""

    pass


class OrderUpdate(BaseModel):
    """Payload to update order status or payment status."""

    status: OrderStatus | None = None
    payment_status: PaymentStatus | None = None
    completed_at: datetime | None = None


class OrderResponse(OrderBase):
    """Full public representation of an order."""

    id: uuid.UUID
    order_code: str
    consumer_id: uuid.UUID
    store_id: uuid.UUID
    unit_price: Decimal
    total_amount: Decimal
    status: OrderStatus
    payment_status: PaymentStatus
    vnpay_transaction_no: str | None = None
    vnpay_bank_code: str | None = None
    vnpay_pay_date: datetime | None = None
    co2_saved_kg: Decimal
    green_points_earned: int
    pickup_deadline: datetime
    completed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 2. QR Token Schemas (Guardrail #3)
# ==============================================================================


class QRTokenResponse(BaseModel):
    """Public representation of dynamic single-use QR token."""

    id: uuid.UUID
    order_id: uuid.UUID
    token_hash: str
    nonce: str
    expires_at: datetime
    is_used: bool
    used_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderDetailResponse(OrderResponse):
    """Detailed order representation with its active single-use QR token when valid."""

    qr_token: QRTokenResponse | None = None


class QRVerificationRequest(BaseModel):
    """Request payload sent when a store partner scans consumer's QR code."""

    token_hash: str = Field(..., description="Mã chữ ký HMAC-SHA256 trên mã QR")
    order_id: uuid.UUID = Field(..., description="Mã đơn hàng đối soát")


# ==============================================================================
# 3. Payment Transaction & VNPay IPN Schemas (Guardrail #3)
# ==============================================================================


class PaymentTransactionCreate(BaseModel):
    """Payload to record a VNPay transaction log."""

    order_id: uuid.UUID
    payment_provider: str = "VNPAY"
    txn_ref: str = Field(..., description="Mã tham chiếu thanh toán vnp_TxnRef")
    amount: Decimal = Field(..., gt=Decimal(0), description="Số tiền thanh toán (VNĐ)")
    vnp_response_code: str = Field(..., description="Mã phản hồi từ VNPay (00 = Thành công)")
    vnp_transaction_no: str | None = None
    vnp_bank_code: str | None = None
    is_verified: bool = Field(default=False, description="Xác thực chữ ký HMAC-SHA512 thành công")
    raw_ipn_payload: dict[str, Any] = Field(default_factory=dict)


class PaymentTransactionResponse(BaseModel):
    """Output representation of a recorded payment transaction."""

    id: uuid.UUID
    order_id: uuid.UUID
    payment_provider: str
    txn_ref: str
    amount: Decimal
    vnp_transaction_no: str | None = None
    vnp_bank_code: str | None = None
    vnp_response_code: str
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VNPayIPNPayload(BaseModel):
    """Schema for incoming VNPay IPN Webhook validation."""

    vnp_Amount: str = Field(..., description="Số tiền x100 theo chuẩn VNPay")
    vnp_BankCode: str | None = None
    vnp_BankTranNo: str | None = None
    vnp_CardType: str | None = None
    vnp_OrderInfo: str
    vnp_PayDate: str | None = None
    vnp_ResponseCode: str
    vnp_TmnCode: str
    vnp_TransactionNo: str
    vnp_TransactionStatus: str
    vnp_TxnRef: str
    vnp_SecureHash: str
