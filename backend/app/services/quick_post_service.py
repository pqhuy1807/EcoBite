"""Gemini Quick-Post service (PA5 head-start).

Extracts surplus-dish listings from free-text input via Google Gemini 2.5 Flash
with Pydantic Structured Output, then applies the Allergen Hard Filter
(Guardrail #7) before returning results to the caller.

The Gemini client is injected (optional) so the service can be unit-tested with
a fake client and degrades gracefully when the LLM is unavailable or returns
malformed output — the app never crashes because of Quick-Post.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from pydantic import ValidationError

from app.models.user import UserPreference
from app.schemas.nlp import (
    QuickPostExtractionResponse,
)
from app.services.allergen_filter_service import AllergenHardFilterService

logger = logging.getLogger(__name__)


@runtime_checkable
class GeminiClient(Protocol):
    """Duck-typed Gemini client — only `generate_content` is required."""

    async def generate_content(
        self,
        *,
        model: str,
        contents: str,
        config: Any,
    ) -> Any:  # pragma: no cover - protocol stub
        """Generate content and return an object with `.parsed` (Pydantic model)."""
        ...


class QuickPostService:
    """Extract structured surplus-dish data from free text via Gemini 2.5 Flash.

    Falls back to an empty (but schema-valid) response when Gemini is
    unavailable, times out, or returns unparseable output — callers can inspect
    ``missing_fields_warning`` on each item to surface UX hints.
    """

    GEMINI_MODEL = "gemini-2.5-flash"

    def __init__(
        self,
        db,
        *,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.db = db
        self.gemini_client = gemini_client

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def extract_quick_post(
        self,
        text_input: str,
        user_preference: UserPreference | None = None,
    ) -> dict[str, Any]:
        """Extract and filter surplus-dish listings from free text.

        Returns a dict compatible with ``QuickPostExtractionResponse`` plus an
        ``allergen_filter_applied`` flag and ``filtered_out_count``.
        """
        extracted = await self._call_gemini(text_input)

        # Apply Allergen Hard Filter (Guardrail #7) — never delegated to AI.
        excluded = (
            [str(a) for a in (user_preference.excluded_allergens or [])]
            if user_preference is not None
            else []
        )
        before = len(extracted.get("items", []))
        extracted["items"] = AllergenHardFilterService.filter_dishes_by_allergens(
            extracted.get("items", []),
            excluded,
        )
        extracted["allergen_filter_applied"] = bool(excluded)
        extracted["filtered_out_count"] = before - len(extracted["items"])

        return extracted

    # ------------------------------------------------------------------ #
    # Gemini call + fallback
    # ------------------------------------------------------------------ #

    async def _call_gemini(self, text_input: str) -> dict[str, Any]:
        """Call Gemini with Structured Output, or return a safe fallback."""
        if self.gemini_client is None:
            logger.warning("Quick-Post: no Gemini client configured — using fallback")
            return self._fallback_response(
                reason="Gemini client not configured",
                items=[],
            )

        try:
            response = await self.gemini_client.generate_content(
                model=self.GEMINI_MODEL,
                contents=self._build_prompt(text_input),
                config={
                    "response_mime_type": "application/json",
                    "response_schema": QuickPostExtractionResponse,
                },
            )
            parsed = getattr(response, "parsed", None)
            if parsed is None:
                # Some client versions return `.text` instead of `.parsed`.
                raw = getattr(response, "text", "") or ""
                parsed = QuickPostExtractionResponse.model_validate_json(raw)

            if not isinstance(parsed, QuickPostExtractionResponse):
                raise ValueError("Gemini did not return a QuickPostExtractionResponse")

            return parsed.model_dump()

        except (ValidationError, ValueError) as exc:
            logger.warning("Quick-Post: Gemini output failed schema validation: %s", exc)
            return self._fallback_response(
                reason=f"LLM output validation failed: {exc}",
                items=[],
            )
        except Exception as exc:  # timeout, network, quota, etc.
            logger.warning("Quick-Post: Gemini call failed (%s) — using fallback", exc)
            return self._fallback_response(
                reason=f"LLM unavailable: {exc}",
                items=[],
            )

    @staticmethod
    def _build_prompt(text_input: str) -> str:
        """Build the extraction prompt fed to Gemini 2.5 Flash."""
        return (
            "Bạn là trợ trích xuất thực phẩm dư thừa cho ứng dụng EcoBite. "
            "Nhập sau đây là mô tả tự do (giọng nói hoặc văn bản) của chủ quán "
            "về các món ăn còn dư cần mở bán giải cứu.\n"
            "Hãy trích xuất thành JSON theo schema sau:\n"
            "- pickup_start, pickup_end: giờ bắt đầu / kết thúc nhận món (HH:MM:SS)\n"
            "- items: danh sách món ăn, mỗi món có dish_name, quantity, "
            "original_price (nếu có), override_discounted_price (nếu có), "
            "side_components, allergens (danh sách {allergen, risk_level, "
            "source, reason}), dietary_notes, missing_fields_warning\n"
            'Với allergens: source = "EXPLICIT" nếu chủ quán nói rõ, "INFERRED" '
            "nếu bạn suy luận từ tri thức món Việt.\n"
            f'Văn bản đầu vào: """{text_input}"""\n'
            "Trả về CHỈ JSON, không giải thích thêm."
        )

    @staticmethod
    def _fallback_response(*, reason: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Build a schema-valid empty response when Gemini cannot be used."""
        for item in items:
            item.setdefault("missing_fields_warning", []).append(reason)
        return {
            "pickup_start": "00:00:00",
            "pickup_end": "23:59:00",
            "items": items,
            "allergen_filter_applied": False,
            "filtered_out_count": 0,
        }


def build_quick_post_service(db, gemini_client: GeminiClient | None = None) -> QuickPostService:
    """Factory for ``QuickPostService`` — keeps endpoint layer dependency-free."""
    return QuickPostService(db, gemini_client=gemini_client)
