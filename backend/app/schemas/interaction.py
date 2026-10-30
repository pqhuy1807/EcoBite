"""Pydantic schemas for Interactions: Review and Notification."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.interaction import NotificationType

# ==============================================================================
# 1. Review Schemas
# ==============================================================================


class ReviewBase(BaseModel):
    """Base fields for verified order reviews."""

    rating: int = Field(..., ge=1, le=5, description="Số sao đánh giá (1-5)")
    comment: str | None = Field(default=None, description="Bình luận chi tiết")
    tags: list[str] = Field(
        default_factory=list, description="Nhãn đánh giá nhanh: ['Ngon', 'Đúng giờ']"
    )
    photo_urls: list[str] = Field(
        default_factory=list, description="Danh sách link ảnh món ăn thực tế"
    )


class ReviewCreate(ReviewBase):
    """Payload to submit a review for a completed order."""

    order_id: uuid.UUID = Field(..., description="Mã đơn hàng đã hoàn thành")


class ReviewResponse(ReviewBase):
    """Output representation of a verified review."""

    id: uuid.UUID
    order_id: uuid.UUID
    consumer_id: uuid.UUID
    store_id: uuid.UUID
    dish_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 2. Notification Schemas
# ==============================================================================


class NotificationResponse(BaseModel):
    """Output representation of a push notification."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    type: NotificationType
    is_read: bool
    metadata_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata ngữ cảnh đính kèm",
        validation_alias="metadata_payload",
        serialization_alias="metadata",
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NotificationUpdate(BaseModel):
    """Payload to mark notification as read."""

    is_read: bool = True
