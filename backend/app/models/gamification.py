"""Gamification ORM models: GreenPointsLedger, Voucher, and UserVoucher."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class PointActionType(enum.StrEnum):
    """Loại giao dịch biến động Điểm Xanh."""

    ORDER_RESCUE = "ORDER_RESCUE"
    VOUCHER_REDEEM = "VOUCHER_REDEEM"
    SYSTEM_BONUS = "SYSTEM_BONUS"


class GreenPointsLedger(Base):
    """Sổ cái lịch sử cộng/trừ Điểm Xanh và ghi nhận giảm phát thải CO2."""

    __tablename__ = "green_points_ledger"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Người dùng sở hữu điểm",
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Đơn hàng liên kết (nếu có)",
    )
    points_change: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Số điểm biến động (+ để cộng, - để trừ)",
    )
    balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Số dư Điểm Xanh sau biến động",
    )
    action_type: Mapped[PointActionType] = mapped_column(
        Enum(PointActionType, name="pointactiontype", native_enum=False, length=30),
        nullable=False,
        comment="Lý do biến động: ORDER_RESCUE, VOUCHER_REDEEM, SYSTEM_BONUS",
    )
    co2_saved_kg: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        default=Decimal("0.0"),
        nullable=False,
        comment="Lượng CO2 giảm phát thải ghi nhận thêm (kg)",
    )
    note: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Ghi chú chi tiết giao dịch điểm",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship(
        "User",
        back_populates="green_points_records",
        lazy="selectin",
    )
    order: Mapped["Order | None"] = relationship(
        "Order",
        back_populates="green_points_records",
        lazy="selectin",
    )


class Voucher(Base):
    """Danh mục mã ưu đãi / voucher đổi bằng Điểm Xanh."""

    __tablename__ = "vouchers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Mã voucher khuyến mãi (e.g. ECOBITE10K)",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Tiêu đề ưu đãi",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả chi tiết thể lệ ưu đãi",
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Số tiền giảm giá (VNĐ)",
    )
    points_required: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Số Điểm Xanh cần để đổi voucher",
    )
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.0"),
        nullable=False,
        comment="Giá trị đơn hàng tối thiểu để áp dụng",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Thời điểm voucher hết hạn",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Voucher còn hiệu lực trên hệ thống không",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    claims: Mapped[list["UserVoucher"]] = relationship(
        "UserVoucher",
        back_populates="voucher",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class UserVoucher(Base):
    """Voucher người dùng đã đổi bằng Điểm Xanh."""

    __tablename__ = "user_vouchers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Người dùng sở hữu voucher",
    )
    voucher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("vouchers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Voucher gốc đã đổi",
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Đã sử dụng khi đặt đơn chưa",
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Thời điểm áp dụng voucher vào đơn hàng",
    )
    claimed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Thời điểm người dùng đổi voucher",
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_vouchers",
        lazy="selectin",
    )
    voucher: Mapped["Voucher"] = relationship(
        "Voucher",
        back_populates="claims",
        lazy="selectin",
    )
