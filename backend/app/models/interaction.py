"""Social & Interaction ORM models: Review and Notification."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import JSON_TYPE

if TYPE_CHECKING:
    from app.models.dish import Dish
    from app.models.order import Order
    from app.models.store import Store
    from app.models.user import User


class NotificationType(enum.StrEnum):
    """Các loại thông báo hệ thống."""

    ORDER_UPDATE = "ORDER_UPDATE"
    NEARBY_DEAL = "NEARBY_DEAL"
    GREEN_POINTS = "GREEN_POINTS"
    SYSTEM = "SYSTEM"


class Review(Base):
    """Đánh giá và phản hồi của khách hàng sau khi hoàn tất đơn hàng."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    # Ràng buộc UNIQUE 1-1 với Order: Mỗi đơn hoàn tất chỉ được đánh giá 1 lần
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Mã đơn hàng được xác thực đánh giá",
    )
    consumer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Người tiêu dùng viết đánh giá",
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Cửa hàng nhận đánh giá",
    )
    dish_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dishes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Món ăn được đánh giá",
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Số sao đánh giá (1 đến 5)",
    )
    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Bình luận chi tiết",
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON_TYPE,
        default=list,
        nullable=False,
        comment="Danh sách nhãn đánh giá nhanh: ['Ngon', 'Đúng giờ', 'Đóng gói kỹ']",
    )
    photo_urls: Mapped[list[str]] = mapped_column(
        JSON_TYPE,
        default=list,
        nullable=False,
        comment="Danh sách link ảnh đính kèm",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="review",
        lazy="selectin",
    )
    consumer: Mapped["User"] = relationship(
        "User",
        back_populates="reviews",
        lazy="selectin",
    )
    store: Mapped["Store"] = relationship(
        "Store",
        back_populates="reviews",
        lazy="selectin",
    )
    dish: Mapped["Dish"] = relationship(
        "Dish",
        back_populates="reviews",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range_1_to_5"),
    )


class Notification(Base):
    """Thông báo đẩy dành cho người dùng trên nền tảng EcoBite."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Người nhận thông báo",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Tiêu đề thông báo",
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Nội dung thông báo",
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notificationtype", native_enum=False, length=30),
        default=NotificationType.SYSTEM,
        nullable=False,
        comment="Phân loại: ORDER_UPDATE, NEARBY_DEAL, GREEN_POINTS, SYSTEM",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Người dùng đã đọc thông báo chưa",
    )
    # Map to DB column 'metadata' while avoiding collision with Base.metadata
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON_TYPE,
        default=dict,
        nullable=False,
        comment="Dữ liệu ngữ cảnh đi kèm (deep-link, order_id...)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
        lazy="selectin",
    )
