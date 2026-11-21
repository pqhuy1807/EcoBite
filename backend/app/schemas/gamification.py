"""Pydantic schemas for Gamification (GreenPointsLedger, Voucher, and UserVoucher)."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.gamification import PointActionType

# ==============================================================================
# 1. Green Points Ledger Schemas
# ==============================================================================


class GreenPointsLedgerBase(BaseModel):
    """Base fields for points ledger records."""

    points_change: int = Field(..., description="Số điểm biến động (+ hoặc -)")
    action_type: PointActionType = Field(..., description="Lý do biến động điểm")
    co2_saved_kg: Decimal = Field(
        default=Decimal("0.0"), ge=Decimal(0), description="Lượng CO2 giảm phát thải (kg)"
    )
    note: str | None = Field(default=None, description="Ghi chú giao dịch")


class GreenPointsLedgerCreate(GreenPointsLedgerBase):
    """Payload to record a points adjustment."""

    user_id: uuid.UUID
    order_id: uuid.UUID | None = None
    balance_after: int = Field(..., description="Số dư Điểm Xanh sau khi thay đổi")


class GreenPointsLedgerResponse(GreenPointsLedgerBase):
    """Output representation of points ledger entry."""

    id: uuid.UUID
    user_id: uuid.UUID
    order_id: uuid.UUID | None = None
    balance_after: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 2. Voucher Schemas
# ==============================================================================


class VoucherBase(BaseModel):
    """Base fields for vouchers."""

    code: str = Field(..., min_length=3, max_length=50, description="Mã voucher khuyến mãi")
    title: str = Field(..., min_length=2, max_length=255, description="Tiêu đề ưu đãi")
    description: str | None = None
    discount_amount: Decimal = Field(..., gt=Decimal(0), description="Số tiền giảm (VNĐ)")
    points_required: int = Field(..., gt=0, description="Số điểm xanh cần để đổi")
    min_order_amount: Decimal = Field(
        default=Decimal("0.0"), ge=Decimal(0), description="Giá trị đơn tối thiểu"
    )
    expires_at: datetime = Field(..., description="Thời điểm voucher hết hạn")
    is_active: bool = Field(default=True, description="Voucher còn hoạt động")


class VoucherCreate(VoucherBase):
    """Payload for Admin to issue a new voucher."""

    pass


class VoucherResponse(VoucherBase):
    """Output representation of a voucher."""

    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 3. User Voucher Schemas (Claimed Vouchers)
# ==============================================================================


class UserVoucherResponse(BaseModel):
    """Output representation of a voucher claimed by a user."""

    id: uuid.UUID
    user_id: uuid.UUID
    voucher_id: uuid.UUID
    is_used: bool
    used_at: datetime | None = None
    claimed_at: datetime
    voucher: VoucherResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 4. Green Points Summary & Voucher Redemption Responses
# ==============================================================================


class GreenPointsSummaryResponse(BaseModel):
    """Summary of consumer's Green Points balance, CO2 impact, rank, and ledger."""

    balance_points: int = Field(..., ge=0, description="Số dư Điểm Xanh hiện tại")
    total_co2_saved_kg: Decimal = Field(
        ..., ge=Decimal("0.0"), description="Tổng lượng khí thải CO2 đã cắt giảm (kg)"
    )
    total_meals_saved: int = Field(..., ge=0, description="Tổng số suất ăn đã giải cứu thành công")
    rank_title: str = Field(..., description="Danh hiệu xếp hạng Xanh theo mốc đóng góp")
    recent_ledger: list[GreenPointsLedgerResponse] = Field(
        default_factory=list, description="Lịch sử giao dịch Điểm Xanh gần nhất"
    )


class VoucherRedeemResponse(BaseModel):
    """Response returned after atomically redeeming a voucher with Green Points."""

    user_voucher_id: uuid.UUID = Field(..., description="ID bản ghi voucher đã sở hữu")
    voucher_id: uuid.UUID = Field(..., description="ID mẫu voucher trong danh mục")
    voucher_code: str = Field(..., description="Mã voucher đã đổi")
    title: str = Field(..., description="Tiêu đề ưu đãi")
    discount_amount: Decimal = Field(..., gt=Decimal(0), description="Số tiền giảm giá (VNĐ)")
    points_deducted: int = Field(..., gt=0, description="Số Điểm Xanh đã khấu trừ")
    remaining_balance: int = Field(..., ge=0, description="Số dư Điểm Xanh còn lại")
    claimed_at: datetime = Field(..., description="Thời điểm đổi voucher thành công")
