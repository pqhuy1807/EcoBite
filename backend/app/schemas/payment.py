"""Pydantic schemas for VNPay payment requests/responses."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class VNPayCreateUrlRequest(BaseModel):
    """Request payload for creating VNPay payment URL."""

    order_id: str
    bank_code: str | None = None


class VNPayCreateUrlResponse(BaseModel):
    """Response with VNPay payment URL."""

    payment_url: str
    txn_ref: str
    vnp_amount: int


class VNPayIPNRequest(BaseModel):
    """VNPay IPN webhook request payload."""

    vnp_Amount: str
    vnp_BankCode: str | None = None
    vnp_BankTranNo: str | None = None
    vnp_CardType: str | None = None
    vnp_OrderInfo: str | None = None
    vnp_PayDate: str | None = None
    vnp_ResponseCode: str
    vnp_TmnCode: str
    vnp_TransactionNo: str | None = None
    vnp_TransactionType: str | None = None
    vnp_TxnRef: str
    vnp_SecureHash: str


class VNPayIPNResponse(BaseModel):
    """Response for VNPay IPN endpoint."""

    RspCode: str
    Message: str


class VNPayReturnResponse(BaseModel):
    """Response for VNPay return URL verification."""

    is_valid: bool
    message: str
    txn_ref: str
