"""Pydantic schemas for Gemini 2.5 Flash Structured Output and NLP Quick-Post.

Complies strictly with:
- Inviolable Guardrail #6: Pydantic Schema Structured Output (QuickPostExtractionResponse)
  and 2-Tier Allergen Review (EXPLICIT vs INFERRED).
- Inviolable Guardrail #7: Allergen safety and 14 EU FIC compliance standards.
"""

import re
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# 1. 14 EU FIC REGULATION ALLERGENS (Song ngữ Anh - Việt)
# ==============================================================================
class EUAllergen(StrEnum):
    """14 nhóm chất dị ứng bắt buộc công khai theo Regulation (EU) No 1169/2011."""

    PEANUTS = "Peanuts (Đậu phộng)"
    SOYBEANS = "Soybeans (Đậu nành)"
    EGGS = "Eggs (Trứng)"
    MILK = "Milk/Dairy (Sữa)"
    FISH = "Fish (Cá/Nước mắm)"
    CRUSTACEANS = "Crustaceans (Tôm/Cua)"
    MOLLUSCS = "Molluscs (Nhuyễn thể: Nghêu/Sò/Ốc)"
    GLUTEN = "Cereals containing gluten (Bột mì/Bánh mì)"
    TREE_NUTS = "Tree nuts (Hạt cây: Điều, Hạnh nhân...)"
    SESAME = "Sesame (Mè/Vừng)"
    CELERY = "Celery (Cần tây)"
    MUSTARD = "Mustard (Mù tạt)"
    SULPHITES = "Sulphites (Chất bảo quản Sulfit)"
    LUPIN = "Lupin (Đậu Lupin)"


class DetectionSource(StrEnum):
    """Nguồn nhận diện dị ứng (2-Tier Allergen Guard)."""

    EXPLICIT = "EXPLICIT"  # Chủ quán trực tiếp khai báo bằng lời nói/văn bản
    INFERRED = "INFERRED"  # Gemini suy luận từ tri thức món ăn Việt Nam


class AllergenRiskLevel(StrEnum):
    """Mức độ rủi ro dị ứng."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ==============================================================================
# 2. SUB-MODELS (Cảnh báo dị ứng & Từng món ăn bóc tách)
# ==============================================================================
class NLPAllergenWarning(BaseModel):
    """Cảnh báo dị ứng chi tiết gắn nhãn nguồn nhận diện và giải thích từ AI."""

    allergen: EUAllergen = Field(
        ...,
        description="Loại dị ứng theo 14 chuẩn EU FIC",
    )
    risk_level: AllergenRiskLevel = Field(
        default=AllergenRiskLevel.HIGH,
        description="Mức độ rủi ro (HIGH, MEDIUM, LOW)",
    )
    source: DetectionSource = Field(
        ...,
        description="Nguồn phát hiện: EXPLICIT (chủ quán đọc) hoặc INFERRED (AI suy luận)",
    )
    reason: str = Field(
        ...,
        description="Giải thích ngắn gọn (VD: 'Chả chưng có trứng vịt', 'Có nước mắm cá cơm')",
    )

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class SurplusDishItem(BaseModel):
    """Từng món ăn dư thừa được bóc tách từ giọng nói / văn bản."""

    matched_menu_id: UUID | None = Field(
        default=None,
        description="UUID món ăn khớp nhất trong thực đơn gốc của quán (Menu Grounding)",
    )
    dish_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Tên món ăn đã được chuẩn hóa",
    )
    quantity: int = Field(
        ...,
        gt=0,
        description="Số lượng suất ăn còn dư cần mở bán giải cứu",
    )
    original_price: float | None = Field(
        default=None,
        gt=0,
        description="Giá gốc niêm yết (VNĐ). Để None nếu hệ thống sẽ kế thừa từ menu_items",
    )
    override_discounted_price: float | None = Field(
        default=None,
        gt=0,
        description="Giá bán xả cố định nếu chủ quán ấn định rõ. Để None để chạy Rule-based",
    )
    side_components: list[str] = Field(
        default_factory=list,
        description="Món ăn kèm/topping phụ (VD: 'mỡ hành', 'dưa chua', 'súp')",
    )
    allergens: list[NLPAllergenWarning] = Field(
        default_factory=list,
        description="Danh sách cảnh báo dị ứng 2 tầng cho món này",
    )
    dietary_notes: list[str] = Field(
        default_factory=list,
        description="Ghi chú khẩu vị địa phương: 'Có mỡ hành (Allium)', 'Cay', 'Chay'...",
    )
    missing_fields_warning: list[str] = Field(
        default_factory=list,
        description="Cảnh báo nếu lời nói thiếu thông tin quan trọng (VD: 'Chưa rõ số lượng')",
    )

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 3. ROOT SCHEMA: GEMINI 2.5 FLASH STRUCTURED OUTPUT
# ==============================================================================
TIME_REGEX = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d(:[0-5]\d)?$")


class QuickPostExtractionResponse(BaseModel):
    """Root Schema bắt buộc cho Gemini 2.5 Flash Structured Output (Batch Quick-Post).

    Quy định tại docs/04_API_Specification.md và docs/06_Environment_and_ML_Setup_Guide.md.
    """

    pickup_start: str = Field(
        ...,
        description="Giờ bắt đầu nhận món dạng HH:MM:SS (Quy đổi từ server time nếu nói tương đối)",
    )
    pickup_end: str = Field(
        ...,
        description="Giờ kết thúc nhận món dạng HH:MM:SS",
    )
    items: list[SurplusDishItem] = Field(
        ...,
        min_length=1,
        description="Danh sách các món ăn dư thừa bóc tách được trong ca",
    )

    @field_validator("pickup_start", "pickup_end")
    @classmethod
    def validate_time_format(cls, value: str) -> str:
        """Validate và chuẩn hóa chuỗi thời gian về format HH:MM:SS."""
        val = value.strip()
        if not TIME_REGEX.match(val):
            raise ValueError(
                f"Định dạng thời gian không hợp lệ: '{value}'. Yêu cầu 'HH:MM:SS' hoặc 'HH:MM'"
            )
        parts = val.split(":")
        if len(parts) == 2:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}:00"
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2]):02d}"

    model_config = ConfigDict(from_attributes=True)
