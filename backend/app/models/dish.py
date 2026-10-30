"""Dish ORM model for rescue meal shift listings."""

import enum
import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.menu_item import DietaryType, ItemCategory
from app.models.user import JSON_TYPE

if TYPE_CHECKING:
    from app.models.interaction import Review
    from app.models.menu_item import MenuItem
    from app.models.order import Order
    from app.models.store import Store


class DishStatus(enum.StrEnum):
    """Trạng thái mở bán của món ăn giải cứu trong ca."""

    ACTIVE = "ACTIVE"
    SOLD_OUT = "SOLD_OUT"
    EXPIRED = "EXPIRED"
    INACTIVE = "INACTIVE"


class Dish(Base):
    """Món ăn dư thừa cụ thể đăng bán trong ca giải cứu (Rescue Dish).

    - Kế thừa ảnh & giá gốc từ `menu_items` (Menu Grounding).
    - Có ràng buộc kiểm tra CheckConstraint chống over-selling (Guardrail #4).
    - Lưu cảnh báo dị ứng 2 tầng EXPLICIT và INFERRED (Guardrail #6).
    """

    __tablename__ = "dishes"

    # --- 1. Định danh & Liên kết quán / thực đơn gốc ---
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Thuộc cửa hàng nào",
    )
    menu_item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("menu_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Liên kết Menu gốc để kế thừa Ảnh & Giá gốc (Menu Grounding)",
    )

    # --- 2. Thông tin hiển thị & Phân loại ---
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Tên món ăn (Kế thừa từ menu_items hoặc tên tự do)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả món ăn trong ca",
    )
    category: Mapped[ItemCategory] = mapped_column(
        Enum(ItemCategory, name="itemcategory", native_enum=False, length=50),
        nullable=False,
        comment="Danh mục món ăn",
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Kế thừa từ menu_items nếu không tải ảnh mới",
    )

    # --- 3. Cơ chế Định giá Rule-based (Guardrail #5) ---
    original_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Giá gốc niêm yết",
    )
    rescue_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Giá giải cứu tiêu chuẩn (-40% đến -50%)",
    )
    rule_discount_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Giá giờ chót kích hoạt theo luật (-70%)",
    )
    override_discounted_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Giá xả cố định nếu chủ quán chỉ định rõ",
    )

    # --- 4. Khung giờ nhận món & Kích hoạt giảm giá ---
    pickup_start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="Giờ bắt đầu nhận món trong ngày",
    )
    pickup_end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="Giờ kết thúc nhận món",
    )
    rule_discount_start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
        comment="Thời điểm kích hoạt luật giảm giá giờ chót",
    )

    # --- 5. Kiểm soát Tồn kho chống Bán vượt (Guardrail #4: Anti-Over-Selling) ---
    total_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Tổng số suất đăng bán ban đầu",
    )
    remaining_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Số lượng suất còn lại (bắt buộc >= 0)",
    )
    status: Mapped[DishStatus] = mapped_column(
        Enum(DishStatus, name="dishstatus", native_enum=False, length=20),
        default=DishStatus.ACTIVE,
        nullable=False,
        comment="Trạng thái món: ACTIVE, SOLD_OUT, EXPIRED, INACTIVE",
    )

    # --- 6. Dị ứng 2 tầng & Nguyên liệu NLP Gemini (Guardrail #6 & #7) ---
    ingredients: Mapped[list[str]] = mapped_column(
        JSON_TYPE,
        default=list,
        nullable=False,
        comment="Danh sách nguyên liệu (bóc tách từ Gemini NLP)",
    )
    # AllergenWarning: [{allergen, risk_level, source: EXPLICIT|INFERRED, reason}]
    allergens: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON_TYPE,
        default=list,
        nullable=False,
        comment="Cảnh báo dị ứng 2 tầng EXPLICIT và INFERRED theo 14 chuẩn EU FIC",
    )
    dietary_notes: Mapped[list[str]] = mapped_column(
        JSON_TYPE,
        default=list,
        nullable=False,
        comment="Ghi chú khẩu vị: ['Có mỡ hành', 'Có dưa chua', 'Cay vừa']",
    )
    dietary_type: Mapped[DietaryType] = mapped_column(
        Enum(DietaryType, name="dietarytype", native_enum=False, length=50),
        default=DietaryType.NON_VEGAN,
        nullable=False,
        comment="Chế độ ăn: VEGAN, VEGETARIAN, NON_VEGAN",
    )

    # --- 7. Tác động môi trường & Thời gian ---
    estimated_co2_kg_per_dish: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        default=Decimal("2.50"),
        nullable=False,
        comment="Ước tính giảm phát thải CO2 mỗi suất ăn giải cứu (kg)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    store: Mapped["Store"] = relationship(
        "Store",
        back_populates="dishes",
        lazy="selectin",
    )
    menu_item: Mapped["MenuItem | None"] = relationship(
        "MenuItem",
        back_populates="dishes",
        lazy="selectin",
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="dish",
        lazy="selectin",
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="dish",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Ràng buộc toàn vẹn dữ liệu: Số lượng suất ăn còn lại không bao giờ được âm
    __table_args__ = (
        CheckConstraint(
            "remaining_quantity >= 0",
            name="ck_dishes_remaining_qty_non_negative",
        ),
    )
