"""Unit tests for Gemini 2.5 Flash Structured Output Schemas (Pydantic v2).

Tests compliance with:
- Guardrail #6: Pydantic Schema Structured Output & 2-Tier Allergen Review.
- Guardrail #7: 14 EU FIC compliance standards.
"""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.nlp import (
    AllergenRiskLevel,
    DetectionSource,
    EUAllergen,
    NLPAllergenWarning,
    QuickPostExtractionResponse,
    SurplusDishItem,
)


def test_eu_allergen_14_categories_completeness():
    """Đảm bảo đầy đủ 14 danh mục dị ứng bắt buộc theo chuẩn EU FIC."""
    expected_categories = [
        EUAllergen.PEANUTS,
        EUAllergen.SOYBEANS,
        EUAllergen.EGGS,
        EUAllergen.MILK,
        EUAllergen.FISH,
        EUAllergen.CRUSTACEANS,
        EUAllergen.MOLLUSCS,
        EUAllergen.GLUTEN,
        EUAllergen.TREE_NUTS,
        EUAllergen.SESAME,
        EUAllergen.CELERY,
        EUAllergen.MUSTARD,
        EUAllergen.SULPHITES,
        EUAllergen.LUPIN,
    ]
    assert len(expected_categories) == 14
    assert len(EUAllergen) == 14


def test_detection_source_2_tier_allergen_guard():
    """Kiểm tra 2 tầng nguồn phát hiện dị ứng (EXPLICIT và INFERRED)."""
    assert DetectionSource.EXPLICIT == "EXPLICIT"
    assert DetectionSource.INFERRED == "INFERRED"

    warning_explicit = NLPAllergenWarning(
        allergen=EUAllergen.PEANUTS,
        risk_level=AllergenRiskLevel.HIGH,
        source=DetectionSource.EXPLICIT,
        reason="Chủ quán nói có rắc đậu phộng rang",
    )
    assert warning_explicit.source == DetectionSource.EXPLICIT

    warning_inferred = NLPAllergenWarning(
        allergen=EUAllergen.FISH,
        risk_level=AllergenRiskLevel.HIGH,
        source=DetectionSource.INFERRED,
        reason="Nước mắm ăn kèm làm từ cá cơm",
    )
    assert warning_inferred.source == DetectionSource.INFERRED


def test_quick_post_extraction_response_valid_payload():
    """Kiểm tra serialize / deserialize payload mẫu từ Gemini 2.5 Flash."""
    menu_id = uuid.uuid4()
    payload = {
        "pickup_start": "13:55:00",
        "pickup_end": "15:00:00",
        "items": [
            {
                "matched_menu_id": str(menu_id),
                "dish_name": "Cơm sườn bì chả",
                "quantity": 5,
                "original_price": 45000.0,
                "override_discounted_price": None,
                "side_components": ["mỡ hành", "dưa chua"],
                "allergens": [
                    {
                        "allergen": "Eggs (Trứng)",
                        "risk_level": "HIGH",
                        "source": "INFERRED",
                        "reason": "Chả chưng có trứng",
                    },
                    {
                        "allergen": "Fish (Cá/Nước mắm)",
                        "risk_level": "HIGH",
                        "source": "INFERRED",
                        "reason": "Nước mắm làm từ cá",
                    },
                ],
                "dietary_notes": ["Có mỡ hành (Allium)", "Có dưa chua"],
                "missing_fields_warning": [],
            },
            {
                "matched_menu_id": None,
                "dish_name": "Bún thịt nướng",
                "quantity": 3,
                "original_price": 40000.0,
                "override_discounted_price": 20000.0,
                "side_components": ["đồ chua", "rau sống"],
                "allergens": [
                    {
                        "allergen": "Peanuts (Đậu phộng)",
                        "risk_level": "HIGH",
                        "source": "EXPLICIT",
                        "reason": "Rắc đậu phộng trên mặt",
                    }
                ],
                "dietary_notes": ["Có hành phi", "Có đậu phộng"],
            },
        ],
    }

    model = QuickPostExtractionResponse.model_validate(payload)
    assert model.pickup_start == "13:55:00"
    assert model.pickup_end == "15:00:00"
    assert len(model.items) == 2

    # Check item 1 (Menu Grounding & Inferred allergens)
    item_1 = model.items[0]
    assert item_1.matched_menu_id == menu_id
    assert item_1.quantity == 5
    assert len(item_1.allergens) == 2
    assert item_1.allergens[0].source == DetectionSource.INFERRED
    assert item_1.override_discounted_price is None

    # Check item 2 (Manual Override Price & Explicit allergen)
    item_2 = model.items[1]
    assert item_2.matched_menu_id is None
    assert item_2.override_discounted_price == 20000.0
    assert item_2.allergens[0].source == DetectionSource.EXPLICIT


def test_quick_post_time_format_normalization():
    """Kiểm tra chuẩn hóa định dạng thời gian 'HH:MM' thành 'HH:MM:SS'."""
    payload = {
        "pickup_start": "14:00",
        "pickup_end": "15:30",
        "items": [
            {
                "dish_name": "Bánh mì pate",
                "quantity": 10,
            }
        ],
    }
    model = QuickPostExtractionResponse.model_validate(payload)
    assert model.pickup_start == "14:00:00"
    assert model.pickup_end == "15:30:00"


def test_quick_post_invalid_time_raises_validation_error():
    """Thời gian không đúng định dạng 24h phải bắn lỗi ValidationError."""
    payload = {
        "pickup_start": "25:00:00",
        "pickup_end": "15:00:00",
        "items": [{"dish_name": "Bánh mì", "quantity": 1}],
    }
    with pytest.raises(ValidationError):
        QuickPostExtractionResponse.model_validate(payload)


def test_surplus_dish_item_invalid_quantity_fails():
    """Số lượng suất ăn <= 0 phải báo lỗi validation."""
    with pytest.raises(ValidationError):
        SurplusDishItem(dish_name="Cơm tấm", quantity=0)

    with pytest.raises(ValidationError):
        SurplusDishItem(dish_name="Cơm tấm", quantity=-5)


def test_gemini_json_schema_generation():
    """Đảm bảo model có thể xuất JSON Schema tương thích hoàn hảo với google-genai SDK."""
    schema = QuickPostExtractionResponse.model_json_schema()
    assert schema["type"] == "object"
    assert "pickup_start" in schema["properties"]
    assert "pickup_end" in schema["properties"]
    assert "items" in schema["properties"]
    assert schema["properties"]["items"]["type"] == "array"
