"""Pydantic schemas for Dish validation and serialization (Pydantic v2)."""

import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.dish import DishStatus
from app.models.menu_item import DietaryType, ItemCategory


class AllergenWarning(BaseModel):
    """Cảnh báo dị ứng 2 tầng (Guardrail #6 - EU FIC 14 allergens)."""

    allergen: str = Field(..., description="Tên chất dị ứng (e.g. Đậu phộng, Hải sản)")
    risk_level: str = Field(default="HIGH", description="Mức độ rủi ro: HIGH, MEDIUM, LOW")
    source: Literal["EXPLICIT", "INFERRED"] = Field(
        ...,
        description="Nguồn nhận diện: EXPLICIT (chủ quán đọc) hoặc INFERRED (Gemini suy luận)",
    )
    reason: str | None = Field(default=None, description="Lý do suy luận dị ứng từ AI")


class DishBase(BaseModel):
    """Base fields shared across dish requests and responses."""

    name: str = Field(..., min_length=2, max_length=255, description="Tên món ăn")
    description: str | None = Field(default=None, description="Mô tả món ăn giải cứu")
    category: ItemCategory = Field(default=ItemCategory.RICE, description="Danh mục món ăn")
    original_price: Decimal = Field(..., gt=Decimal(0), description="Giá gốc niêm yết (VNĐ)")
    rescue_price: Decimal = Field(..., gt=Decimal(0), description="Giá giải cứu (-40% đến -50%)")
    rule_discount_price: Decimal | None = Field(
        default=None, gt=Decimal(0), description="Giá giờ chót (-70%)"
    )
    override_discounted_price: Decimal | None = Field(
        default=None, gt=Decimal(0), description="Giá xả thủ công"
    )
    pickup_start_time: time = Field(..., description="Giờ bắt đầu nhận món trong ngày")
    pickup_end_time: time = Field(..., description="Giờ kết thúc nhận món")
    rule_discount_start_time: time | None = Field(
        default=None, description="Giờ kích hoạt giá giờ chót"
    )
    image_url: str | None = Field(default=None, max_length=500, description="Link ảnh món ăn")
    ingredients: list[str] = Field(default_factory=list, description="Danh sách nguyên liệu")
    allergens: list[AllergenWarning] = Field(
        default_factory=list, description="Cảnh báo dị ứng 2 tầng"
    )
    dietary_notes: list[str] = Field(
        default_factory=list, description="Ghi chú khẩu vị: ['Có mỡ hành', 'Cay vừa']"
    )
    dietary_type: DietaryType = Field(
        default=DietaryType.NON_VEGAN, description="Chế độ ăn: VEGAN, VEGETARIAN, NON_VEGAN"
    )
    estimated_co2_kg_per_dish: Decimal = Field(
        default=Decimal("2.50"), ge=Decimal(0), description="Ước tính kg CO2 giảm phát thải"
    )


class DishCreate(DishBase):
    """Payload to publish a new rescue dish batch."""

    store_id: uuid.UUID = Field(..., description="Thuộc cửa hàng nào")
    menu_item_id: uuid.UUID | None = Field(
        default=None, description="Kế thừa ảnh và giá từ Menu Grounding"
    )
    total_quantity: int = Field(..., gt=0, description="Tổng số suất mở bán ban đầu")


class DishPublish(BaseModel):
    """Fields required to publish surplus stock grounded in a menu item."""

    menu_item_id: uuid.UUID
    total_quantity: int = Field(..., gt=0)
    remaining_quantity: int | None = Field(default=None, ge=0)
    pickup_start_time: time
    pickup_end_time: time
    rule_discount_start_time: time | None = None
    override_discounted_price: Decimal | None = Field(default=None, gt=Decimal(0))
    allergens: list[AllergenWarning] = Field(default_factory=list)
    dietary_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_pickup_window(self) -> "DishPublish":
        if self.pickup_end_time <= self.pickup_start_time:
            raise ValueError("Pickup end time must be after pickup start time")
        if (
            self.rule_discount_start_time is not None
            and not self.pickup_start_time <= self.rule_discount_start_time <= self.pickup_end_time
        ):
            raise ValueError("Rule discount start time must be within the pickup window")
        if self.remaining_quantity is not None and self.remaining_quantity > self.total_quantity:
            raise ValueError("Remaining quantity cannot exceed total quantity")
        if (
            self.remaining_quantity is not None
            and self.remaining_quantity > self.total_quantity
        ):
            raise ValueError("Remaining quantity cannot exceed total quantity")
        return self


class DishQuantityUpdate(BaseModel):
    """Set the number of portions currently available for sale."""

    quantity: int = Field(..., ge=0)


class DishBatchItem(BaseModel):
    """A menu-grounded dish within a batch publication."""

    menu_item_id: uuid.UUID
    quantity: int = Field(..., gt=0)
    remaining_quantity: int | None = Field(default=None, ge=0)
    override_discounted_price: Decimal | None = Field(default=None, gt=Decimal(0))
    allergens: list[AllergenWarning] = Field(default_factory=list)
    dietary_notes: list[str] = Field(default_factory=list)


class DishBatchPublish(BaseModel):
    """Shared pickup window and non-empty set of items for batch publication."""

    pickup_start_time: time
    pickup_end_time: time
    rule_discount_start_time: time | None = None
    dishes: list[DishBatchItem] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_pickup_window(self) -> "DishBatchPublish":
        if self.pickup_end_time <= self.pickup_start_time:
            raise ValueError("Pickup end time must be after pickup start time")
        if (
            self.rule_discount_start_time is not None
            and not self.pickup_start_time <= self.rule_discount_start_time <= self.pickup_end_time
        ):
            raise ValueError("Rule discount start time must be within the pickup window")
        return self


class DishUpdate(BaseModel):
    """Partial update payload for a dish listing."""

    rescue_price: Decimal | None = Field(default=None, gt=Decimal(0))
    rule_discount_price: Decimal | None = Field(default=None, gt=Decimal(0))
    override_discounted_price: Decimal | None = Field(default=None, gt=Decimal(0))
    remaining_quantity: int | None = Field(
        default=None, ge=0, description="Tồn kho còn lại (không được âm)"
    )
    status: DishStatus | None = None
    pickup_end_time: time | None = None


class DishResponse(DishBase):
    """Output representation of a rescue dish listing."""

    id: uuid.UUID
    store_id: uuid.UUID
    menu_item_id: uuid.UUID | None = None
    total_quantity: int
    remaining_quantity: int
    status: DishStatus
    current_price: Decimal | None = None
    is_rule_discount_active: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
