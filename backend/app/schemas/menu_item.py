"""Pydantic schemas for MenuItem validation and serialization (Pydantic v2)."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.menu_item import DietaryType, ItemCategory


class MenuItemBase(BaseModel):
    """Base fields shared across request and response."""

    name: str = Field(..., min_length=2, max_length=255, description="Tên món ăn chuẩn")
    description: str | None = Field(default=None, description="Mô tả chi tiết món ăn")
    category: ItemCategory = Field(default=ItemCategory.RICE, description="Danh mục món ăn")
    original_price: Decimal = Field(
        ..., gt=Decimal(0), description="Giá gốc niêm yết tại quán (VNĐ)"
    )
    image_url: str = Field(..., min_length=5, max_length=500, description="Link ảnh chất lượng cao")
    standard_ingredients: list[str] = Field(
        default_factory=list, description="Thành phần nguyên liệu chuẩn"
    )
    base_allergens: list[str] = Field(
        default_factory=list, description="Danh sách dị ứng chuẩn đã xác định"
    )
    dietary_type: DietaryType = Field(
        default=DietaryType.NON_VEGAN, description="Chế độ ăn: VEGAN, VEGETARIAN, NON_VEGAN"
    )
    is_active: bool = Field(default=True, description="Còn phục vụ trong menu không")


class MenuItemCreate(MenuItemBase):
    """Payload to add a new item to store catalog."""

    store_id: uuid.UUID = Field(..., description="Thuộc cửa hàng nào")


class MenuItemUpdate(BaseModel):
    """Partial update payload for a menu item."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    category: ItemCategory | None = None
    original_price: Decimal | None = Field(default=None, gt=Decimal(0))
    image_url: str | None = Field(default=None, min_length=5, max_length=500)
    standard_ingredients: list[str] | None = None
    base_allergens: list[str] | None = None
    dietary_type: DietaryType | None = None
    is_active: bool | None = None


class MenuItemResponse(MenuItemBase):
    """Output representation of a standard menu item."""

    id: uuid.UUID
    store_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
