"""MenuItem ORM model for standard restaurant catalog (Menu Grounding)."""

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
    Numeric,
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
    from app.models.store import Store


class ItemCategory(enum.StrEnum):
    """6 danh mục món ăn chuẩn theo đặc tả hệ thống EcoBite."""

    RICE = "RICE"
    NOODLES = "NOODLES"
    BAKERY = "BAKERY"
    BEVERAGE = "BEVERAGE"
    VEGETARIAN = "VEGETARIAN"
    OTHER = "OTHER"


class DietaryType(enum.StrEnum):
    """Phân loại khẩu vị ăn uống."""

    VEGAN = "VEGAN"
    VEGETARIAN = "VEGETARIAN"
    NON_VEGAN = "NON_VEGAN"


class MenuItem(Base):
    """Thực đơn gốc chuẩn của quán ăn (Menu Grounding).

    Được dùng để neo thông tin khi chủ quán đăng món ăn giải cứu bằng giọng nói,
    giúp kế thừa ảnh chất lượng cao và giá gốc niêm yết mà không cần gõ lại.
    """

    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Thuộc về cửa hàng nào",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Tên chuẩn của món ăn (Ví dụ: Cơm sườn bì chả)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả chi tiết món ăn",
    )
    category: Mapped[ItemCategory] = mapped_column(
        Enum(ItemCategory, name="itemcategory", native_enum=False, length=50),
        nullable=False,
        comment="Danh mục món ăn",
    )
    original_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Giá gốc niêm yết chuẩn tại quán",
    )
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Ảnh chụp món ăn chuẩn chất lượng cao để hiển thị trên app",
    )

    # Thành phần nguyên liệu chuẩn
    standard_ingredients: Mapped[list[str]] = mapped_column(
        JSON_TYPE,
        default=list,
        nullable=False,
        comment="Danh sách nguyên liệu chuẩn (JSON)",
    )

    # Dị ứng chuẩn đã xác định trước
    base_allergens: Mapped[list[str]] = mapped_column(
        JSON_TYPE,
        default=list,
        nullable=False,
        comment="Danh sách dị ứng chuẩn đã xác định trước (JSON)",
    )

    dietary_type: Mapped[DietaryType] = mapped_column(
        Enum(DietaryType, name="dietarytype", native_enum=False, length=50),
        default=DietaryType.NON_VEGAN,
        nullable=False,
        comment="Chế độ ăn: VEGAN, VEGETARIAN, NON_VEGAN",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Còn phục vụ trong thực đơn không",
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
        back_populates="menu_items",
        lazy="selectin",
    )
    dishes: Mapped[list["Dish"]] = relationship(
        "Dish",
        back_populates="menu_item",
        lazy="selectin",
    )
