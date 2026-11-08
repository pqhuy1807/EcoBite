"""Order, QRToken, and PaymentTransaction ORM models (SQLAlchemy 2.0)."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import JSON_TYPE

if TYPE_CHECKING:
    from app.models.dish import Dish
    from app.models.gamification import GreenPointsLedger
    from app.models.interaction import Review
    from app.models.store import Store
    from app.models.user import User


class OrderStatus(enum.StrEnum):
    """Vòng đời trạng thái của đơn hàng giải cứu thực phẩm."""

    CONFIRMED = "CONFIRMED"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PaymentMethod(enum.StrEnum):
    """Phương thức thanh toán hỗ trợ."""

    VNPAY = "VNPAY"
    COD = "COD"


class PaymentStatus(enum.StrEnum):
    """Trạng thái xử lý thanh toán."""

    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


class Order(Base):
    """Đơn hàng giải cứu suất ăn (Rescue Food Order).

    Liên kết người tiêu dùng, cửa hàng đối tác và món ăn trong ca giải cứu.
    """

    __tablename__ = "orders"

    # --- 1. Định danh & Mã đơn hiển thị ---
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    order_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Mã đơn hiển thị thân thiện (e.g. EB-20261016-9981)",
    )

    # --- 2. Khóa ngoại liên kết ---
    consumer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID người tiêu dùng đặt đơn",
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID cửa hàng nhận đơn",
    )
    dish_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dishes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID món ăn giải cứu được đặt",
    )

    # --- 3. Số lượng & Giá trị đơn hàng ---
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Số lượng suất đặt mua (bắt buộc > 0)",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Đơn giá tại thời điểm đặt (VNĐ)",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Tổng tiền đơn hàng = unit_price * quantity",
    )

    # --- 4. Trạng thái & Thanh toán ---
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="orderstatus", native_enum=False, length=30),
        default=OrderStatus.CONFIRMED,
        nullable=False,
        comment="Trạng thái đơn hàng",
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="paymentmethod", native_enum=False, length=20),
        nullable=False,
        comment="Phương thức thanh toán: VNPAY hoặc COD",
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="paymentstatus", native_enum=False, length=20),
        default=PaymentStatus.PENDING,
        nullable=False,
        comment="Trạng thái thanh toán: PENDING, PAID, FAILED",
    )

    # Thông tin đối soát cổng VNPay
    vnpay_transaction_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Mã giao dịch cổng VNPay",
    )
    vnpay_bank_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Mã ngân hàng thanh toán (VCB, TCB, VNPAYQR...)",
    )
    vnpay_pay_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Thời gian thanh toán ghi nhận tại VNPay",
    )

    # --- 5. Tác động Xanh & Gamification ---
    co2_saved_kg: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        default=Decimal("0.0"),
        nullable=False,
        comment="Lượng CO2 giảm phát thải đạt được từ đơn hàng (kg)",
    )
    green_points_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Điểm Xanh tích luỹ được thưởng cho đơn hàng này",
    )

    # --- 6. Mốc thời gian ---
    pickup_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Hạn chót khách phải đến lấy món",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Thời điểm khách hoàn tất nhận món tại quán",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    consumer: Mapped["User"] = relationship(
        "User",
        back_populates="orders",
        lazy="selectin",
    )
    store: Mapped["Store"] = relationship(
        "Store",
        back_populates="orders",
        lazy="selectin",
    )
    dish: Mapped["Dish"] = relationship(
        "Dish",
        back_populates="orders",
        lazy="selectin",
    )
    qr_token: Mapped["QRToken | None"] = relationship(
        "QRToken",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    payment_transactions: Mapped[list["PaymentTransaction"]] = relationship(
        "PaymentTransaction",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    review: Mapped["Review | None"] = relationship(
        "Review",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    green_points_records: Mapped[list["GreenPointsLedger"]] = relationship(
        "GreenPointsLedger",
        back_populates="order",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_orders_quantity_positive"),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
    )


class QRToken(Base):
    """Mã QR xác nhận nhận món dùng một lần (Single-Use Dynamic QR).

    Bảo mật theo Guardrail #3: HMAC-SHA256, nonce ngẫu nhiên,
    kiểm tra cờ is_used chống Replay Attack.
    """

    __tablename__ = "qr_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Mã đơn hàng liên kết (Quan hệ 1-1)",
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Chữ ký HMAC-SHA256 băm an toàn",
    )
    nonce: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="Chuỗi ngẫu nhiên dùng 1 lần (Single-use nonce)",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Thời điểm mã QR hết hạn (đồng bộ với pickup_deadline)",
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Đã quét nhận món chưa (chống Replay Attack quét 2 lần)",
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Thời điểm đối tác quét hoàn tất tại quán",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="qr_token",
        lazy="selectin",
    )


class PaymentTransaction(Base):
    """Nhật ký giao dịch cổng thanh toán VNPay IPN (Guardrail #3).

    Lưu trữ đầy đủ payload callback, chữ ký HMAC-SHA512 để phục vụ đối soát và xử lý idempotent.
    """

    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Mã đơn hàng được thanh toán",
    )
    payment_provider: Mapped[str] = mapped_column(
        String(50),
        default="VNPAY",
        nullable=False,
        comment="Cổng thanh toán: VNPAY",
    )
    txn_ref: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Mã tham chiếu thanh toán gửi sang VNPay (vnp_TxnRef)",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Số tiền thanh toán thực tế (VNĐ)",
    )
    vnp_transaction_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Mã giao dịch phía hệ thống VNPay (vnp_TransactionNo)",
    )
    vnp_bank_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Mã ngân hàng khách dùng (vnp_BankCode)",
    )
    vnp_response_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Mã phản hồi từ VNPay (00 là thành công)",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Đã xác thực chữ ký HMAC-SHA512 hợp lệ từ VNPay IPN",
    )
    raw_ipn_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        default=dict,
        nullable=False,
        comment="Toàn bộ payload Webhook VNPay IPN phục vụ kiểm toán",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="payment_transactions",
        lazy="selectin",
    )
