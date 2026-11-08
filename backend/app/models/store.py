"""Store and KycStatus ORM models (SQLAlchemy 2.0 Mapped[T] style)."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
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
    from app.models.dish import Dish
    from app.models.interaction import Review
    from app.models.menu_item import MenuItem
    from app.models.order import Order
    from app.models.user import User

# Portable location type: GeoAlchemy2 Geometry on PostgreSQL, String on SQLite in-memory tests
try:
    from geoalchemy2 import Geometry

    LOCATION_TYPE = String(255).with_variant(
        Geometry(geometry_type="POINT", srid=4326), "postgresql"
    )
except ImportError:
    LOCATION_TYPE = String(255)


class KycStatus(enum.StrEnum):
    """Trạng thái kiểm duyệt an toàn vệ sinh thực phẩm (ATVSTP) của quán ăn.

    - PENDING: Quán mới đăng ký, chờ Admin xét duyệt giấy phép.
    - APPROVED: Giấy phép hợp lệ, quán được phép đăng bán món ăn giải cứu.
    - REJECTED: Giấy phép không đạt, Admin từ chối kèm lý do kyc_reject_reason.
    """

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Store(Base):
    """Cửa hàng / Đối tác đăng bán thực phẩm giải cứu trên nền tảng EcoBite."""

    __tablename__ = "stores"

    # --- 1. Khóa chính & Định danh chủ sở hữu ---
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    # Khóa ngoại liên kết tới tài khoản chủ quán (UserRole.STORE_PARTNER)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID của tài khoản chủ sở hữu cửa hàng",
    )

    # --- 2. Thông tin cơ bản của quán ---
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Tên cửa hàng / thương hiệu",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả giới thiệu về quán ăn",
    )
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Địa chỉ thực tế của quán ăn",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Số điện thoại liên hệ của quán",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Ảnh đại diện hoặc logo của quán",
    )

    # --- 3. Hồ sơ kiểm duyệt ATVSTP (KYC - Know Your Customer) ---
    kyc_license_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Đường dẫn ảnh Giấy chứng nhận Đăng ký kinh doanh / ATVSTP",
    )
    kyc_status: Mapped[KycStatus] = mapped_column(
        Enum(KycStatus, name="kycstatus", native_enum=False, length=20),
        default=KycStatus.PENDING,
        nullable=False,
        comment="Trạng thái phê duyệt quán ăn từ Admin",
    )
    kyc_reject_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do từ chối phê duyệt (nếu trạng thái là REJECTED)",
    )

    # --- 4. Toạ độ không gian địa lý PostGIS (Guardrail #2) ---
    # Phục vụ Radar quét các quán ăn trong bán kính 1km - 10km (ST_DWithin)
    location: Mapped[object] = mapped_column(
        LOCATION_TYPE,
        nullable=False,
        index=True,
        comment="Toạ độ GPS WGS84: Point(longitude, latitude) 4326",
    )

    # --- 5. Chỉ số Đánh giá & Tác động Môi trường ---
    rating_avg: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("5.0"),
        nullable=False,
        comment="Điểm đánh giá sao trung bình (1.0 đến 5.0)",
    )
    rating_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Tổng số lượt đánh giá của khách hàng",
    )
    total_co2_saved_kg: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.0"),
        nullable=False,
        comment="Tổng khối lượng khí CO2 đã giảm phát thải (kg)",
    )

    # --- 6. Dấu thời gian hệ thống ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Thời điểm quán được tạo",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Thời điểm quán cập nhật thông tin gần nhất",
    )

    # --- 7. Quan hệ ORM ---
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="stores",
        lazy="selectin",
    )
    menu_items: Mapped[list["MenuItem"]] = relationship(
        "MenuItem",
        back_populates="store",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    dishes: Mapped[list["Dish"]] = relationship(
        "Dish",
        back_populates="store",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="store",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="store",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
