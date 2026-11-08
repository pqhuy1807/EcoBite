"""Pydantic schemas for Store validation and serialization (Pydantic v2)."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.store import KycStatus


class StoreOnboardRequest(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=255, examples=["Tiệm Bánh Mì & Cơm Trưa Sài Gòn"]
    )
    description: str | None = None
    address: str = Field(..., min_length=5, max_length=500)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    phone: str = Field(..., max_length=20)
    kyc_license_url: str = Field(..., max_length=500)

    model_config = ConfigDict(from_attributes=True)


class StoreOnboardResponse(BaseModel):
    id: uuid.UUID
    name: str
    kyc_status: str
    message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class StoreBase(BaseModel):
    """Base fields shared across store requests and responses."""

    name: str = Field(..., min_length=2, max_length=255, description="Tên cửa hàng")
    description: str | None = Field(default=None, description="Mô tả giới thiệu quán")
    address: str = Field(..., min_length=5, max_length=500, description="Địa chỉ thực tế")
    phone: str | None = Field(default=None, max_length=20, description="Số điện thoại liên hệ")
    avatar_url: str | None = Field(
        default=None, max_length=500, description="Ảnh đại diện hoặc logo"
    )


class StoreCreate(StoreBase):
    """Payload to register a new store partner account."""

    # Tọa độ GPS phục vụ chuyển đổi sang PostGIS Point(longitude, latitude)
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Vĩ độ GPS (Latitude)",
        examples=[10.762622],
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Kinh độ GPS (Longitude)",
        examples=[106.682333],
    )
    kyc_license_url: str | None = Field(
        default=None,
        max_length=500,
        description="Đường dẫn ảnh Giấy chứng nhận ATVSTP",
    )


class StoreUpdate(BaseModel):
    """Payload to partially update store information."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    address: str | None = Field(default=None, min_length=5, max_length=500)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    kyc_license_url: str | None = None


class StoreKycReview(BaseModel):
    """Schema for Admin to approve or reject merchant KYC."""

    kyc_status: KycStatus = Field(..., description="Trạng thái phê duyệt: APPROVED hoặc REJECTED")
    kyc_reject_reason: str | None = Field(
        default=None,
        description="Lý do từ chối (bắt buộc nếu kyc_status là REJECTED)",
    )


class StoreResponse(StoreBase):
    """Public representation of a store."""

    id: uuid.UUID
    owner_id: uuid.UUID
    kyc_status: KycStatus
    kyc_license_url: str | None = None
    kyc_reject_reason: str | None = None
    rating_avg: Decimal
    rating_count: int
    total_co2_saved_kg: Decimal
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
