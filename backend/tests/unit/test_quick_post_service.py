"""Unit tests for QuickPostService (PA5 head-start) — Gemini extraction + allergen filter."""

from typing import Any

import pytest

from app.models.user import UserPreference
from app.schemas.nlp import QuickPostExtractionResponse
from app.services.allergen_filter_service import AllergenHardFilterService
from app.services.quick_post_service import QuickPostService, build_quick_post_service


class FakeGeminiClient:
    """Stand-in for google-genai client; exposes `generate_content`."""

    def __init__(self, response: Any = None, exc: Exception | None = None) -> None:
        self._response = response
        self._exc = exc
        self.called = False

    async def generate_content(self, *, model: str, contents: str, config: Any) -> Any:
        self.called = True
        if self._exc is not None:
            raise self._exc
        return self._response


class FakeResponse:
    def __init__(self, parsed: Any) -> None:
        self.parsed = parsed


class TestQuickPostService:
    @pytest.fixture
    def db(self) -> object:
        return object()

    async def test_successful_extraction_returns_parsed_items(self, db: object) -> None:
        """Gemini returns valid QuickPostExtractionResponse -> passed through."""
        parsed = QuickPostExtractionResponse(
            pickup_start="14:00:00",
            pickup_end="16:00:00",
            items=[
                {
                    "dish_name": "Cơm tấm",
                    "quantity": 3,
                    "allergens": [],
                    "dietary_notes": [],
                    "missing_fields_warning": [],
                }
            ],
        )
        client = FakeGeminiClient(response=FakeResponse(parsed))
        service = QuickPostService(db, gemini_client=client)

        result = await service.extract_quick_post("Cơm tấm 3 suất, buổi chiều")

        assert result["pickup_start"] == "14:00:00"
        assert len(result["items"]) == 1
        assert result["items"][0]["dish_name"] == "Cơm tấm"
        assert client.called is True

    async def test_no_gemini_client_uses_fallback(self, db: object) -> None:
        """No Gemini client -> fallback response with empty items."""
        service = QuickPostService(db, gemini_client=None)

        result = await service.extract_quick_post("anything")

        assert result["items"] == []
        assert result["allergen_filter_applied"] is False
        assert result["filtered_out_count"] == 0

    async def test_gemini_timeout_uses_fallback(self, db: object) -> None:
        """Gemini raises TimeoutError -> fallback, app does not crash."""
        client = FakeGeminiClient(exc=TimeoutError("Gemini timed out"))
        service = QuickPostService(db, gemini_client=client)

        result = await service.extract_quick_post("anything")

        assert result["items"] == []
        assert result["filtered_out_count"] == 0

    async def test_gemini_invalid_json_uses_fallback(self, db: object) -> None:
        """Gemini returns unparseable output -> fallback."""
        client = FakeGeminiClient(exc=ValueError("Not JSON"))
        service = QuickPostService(db, gemini_client=client)

        result = await service.extract_quick_post("anything")

        assert result["items"] == []

    async def test_extract_quick_post_applies_allergen_filter(self, db: object) -> None:
        """Items containing excluded allergens are removed (Guardrail #7)."""
        parsed = QuickPostExtractionResponse(
            pickup_start="14:00:00",
            pickup_end="16:00:00",
            items=[
                {
                    "dish_name": "Bánh mì trứng",
                    "quantity": 2,
                    "allergens": [
                        {
                            "allergen": "Eggs (Trứng)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Có trứng",
                        }
                    ],
                    "dietary_notes": [],
                    "missing_fields_warning": [],
                },
                {
                    "dish_name": "Nước coc",
                    "quantity": 1,
                    "allergens": [],
                    "dietary_notes": [],
                    "missing_fields_warning": [],
                },
            ],
        )
        client = FakeGeminiClient(response=FakeResponse(parsed))
        service = QuickPostService(db, gemini_client=client)

        pref = UserPreference(
            id="pref-1",
            user_id="user-1",
            excluded_allergens=["trứng"],
        )

        result = await service.extract_quick_post("text", user_preference=pref)

        assert result["allergen_filter_applied"] is True
        assert result["filtered_out_count"] == 1
        assert [i["dish_name"] for i in result["items"]] == ["Nước coc"]

    async def test_build_quick_post_service_factory(self, db: object) -> None:
        """Factory returns a QuickPostService instance."""
        svc = build_quick_post_service(db)
        assert isinstance(svc, QuickPostService)


class TestAllergenFilterIntegration:
    def test_exact_allergen_match_removed(self) -> None:
        dishes = [
            {"id": "1", "name": "A", "allergens": [{"allergen": "Đậu phộng"}]},
            {"id": "2", "name": "B", "allergens": []},
        ]
        result = AllergenHardFilterService.filter_dishes_by_allergens(
            dishes, excluded_allergens=["đậu phộng"]
        )
        assert [d["id"] for d in result] == ["2"]
