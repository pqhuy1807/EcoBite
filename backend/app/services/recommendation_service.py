"""Recommendation service: Layer 2 heuristic scoring + Layer 3 Gemini justification.

Implements AI Feature 2 baseline:

* Layer 1 (SQL hard safety invariant): delegated to
  ``recommendation_repo.list_candidate_dishes`` — allergen exclusion is a hard
  invariant, never delegated to Gemini (Guardrail #7).
* Layer 2 (deterministic multi-factor scoring):
  ``Score = 0.40 * S_proximity + 0.30 * S_discount_urgency + 0.30 * S_taste_match``.
* Layer 3 (Gemini 2.5 Flash justification): generates a short Vietnamese
  ``ai_justification`` for each Top-K dish. Falls back to a deterministic
  template when Gemini is unconfigured, errors, times out or returns invalid
  output — the endpoint never crashes because of the LLM.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ValidationError

from app.models.user import DietaryPreference, UserPreference
from app.repositories import preference_repo, recommendation_repo

logger = logging.getLogger(__name__)

PROXIMITY_WEIGHT = 0.40
DISCOUNT_WEIGHT = 0.30
TASTE_WEIGHT = 0.30
DEFAULT_TOP_K = 3
GEMINI_MODEL = "gemini-2.5-flash"


@runtime_checkable
class GeminiClient(Protocol):
    """Duck-typed Gemini client — only ``generate_content`` is required."""

    async def generate_content(
        self,
        *,
        model: str,
        contents: str,
        config: Any,
    ) -> Any:  # pragma: no cover - protocol stub
        """Generate content and return an object with ``.parsed`` / ``.text``."""
        ...


class _DishJustification(BaseModel):
    dish_id: str
    justification: str


class _JustificationBatch(BaseModel):
    justifications: list[_DishJustification]


class RecommendationService:
    """Multi-factor recommendation engine with Gemini-powered justifications."""

    def __init__(
        self,
        db,
        *,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.db = db
        self.gemini_client = gemini_client

    # ------------------------------------------------------------------ #
    # Public API: personalized recommendations (GET /recommendations/personalized)
    # ------------------------------------------------------------------ #

    async def get_personalized(
        self,
        *,
        user_id: str,
        lat: float,
        lng: float,
        radius_km: float = 3.0,
        top_k: int = DEFAULT_TOP_K,
    ) -> dict[str, Any]:
        """Return Top-K personalized, allergen-safe dish recommendations.

        Pipeline:
          1. Load user preference (excluded allergens, taste, budget).
          2. Layer 1: SQL candidate selection + allergen hard filter.
          3. Layer 2: heuristic scoring and Top-K ranking.
          4. Layer 3: Gemini justification (deterministic fallback).
        """
        # 1. User preference (allergen exclusions are canonical EUAllergen keys).
        pref: UserPreference | None = await preference_repo.get_by_user_id(
            self.db, uuid.UUID(user_id)
        )
        excluded_allergens = list(pref.excluded_allergens or []) if pref else []
        preferred_categories = list(pref.preferred_categories or []) if pref else []
        dietary_preference = pref.dietary_preference if pref else DietaryPreference.NONE
        max_budget = pref.max_budget if pref else None

        # 2. Layer 1 — SQL candidates (allergen-safe already).
        candidates = await recommendation_repo.list_candidate_dishes(
            self.db,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            excluded_allergens=excluded_allergens,
            limit=max(top_k * 5, 20),
        )

        # 3. Layer 2 — deterministic multi-factor scoring.
        scored = []
        for dish, dist_m, store in candidates:
            score, breakdown = self._score_dish(
                dish=dish,
                dist_m=dist_m,
                radius_km=radius_km,
                preferred_categories=preferred_categories,
                dietary_preference=dietary_preference,
                max_budget=max_budget,
            )
            scored.append((score, dish, store, dist_m, breakdown))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[:top_k]

        # 4. Layer 3 — Gemini justification with deterministic fallback.
        top_dishes = [(d, store, _) for _, d, store, _, _ in top]
        justification_map = await self._generate_justifications(
            user_pref=pref,
            candidates=top_dishes,
        )

        items = []
        for score, dish, store, dist_m, breakdown in top:
            items.append(
                {
                    "id": str(dish.id),
                    "store_id": str(dish.store_id),
                    "store_name": store.name,
                    "name": dish.name,
                    "category": dish.category,
                    "current_price": self._current_price(dish)[0],
                    "original_price": dish.original_price,
                    "is_rule_discount_active": breakdown.get("rush_active", False),
                    "distance_meters": round(dist_m, 1),
                    "score": round(score, 4),
                    "breakdown": breakdown,
                    "ai_justification": justification_map.get(
                        str(dish.id), self._fallback_justification(dish)
                    ),
                }
            )

        return {
            "items": items,
            "total": len(items),
            "user_location": {"lat": lat, "lng": lng},
            "radius_km": radius_km,
        }

    # ------------------------------------------------------------------ #
    # Layer 2 — deterministic heuristic scoring
    # ------------------------------------------------------------------ #

    def _score_dish(
        self,
        *,
        dish: Any,
        dist_m: float,
        radius_km: float,
        preferred_categories: list[str],
        dietary_preference: DietaryPreference,
        max_budget: object | None,
    ) -> tuple[float, dict[str, float]]:
        """Return (total_score, component_breakdown) for a single dish."""
        # Current active price + whether rush discount is active.
        current_price, rush_active = self._current_price(dish)

        # --- S_proximity: closer = higher (clamped [0, 1]) ---
        radius_m = radius_km * 1000.0
        s_proximity = max(0.0, 1.0 - min(dist_m / radius_m, 1.0))

        # --- S_discount_urgency: rush/discounted price = higher ---
        original_price = dish.original_price
        if rush_active:
            s_discount = 1.0
        elif original_price > 0 and current_price is not None and current_price < original_price:
            s_discount = float(min(1.0, (original_price - current_price) / original_price))
        else:
            s_discount = 0.0

        # --- S_taste_match: category + dietary preference ---
        s_category = 1.0 if dish.category.value in preferred_categories else 0.0
        s_dietary = self._dietary_match(dish.dietary_type, dietary_preference)
        s_taste = 0.6 * s_category + 0.4 * s_dietary

        total = (
            PROXIMITY_WEIGHT * s_proximity + DISCOUNT_WEIGHT * s_discount + TASTE_WEIGHT * s_taste
        )
        breakdown = {
            "proximity": round(s_proximity, 4),
            "discount_urgency": round(s_discount, 4),
            "taste_match": round(s_taste, 4),
            "rush_active": rush_active,
        }
        return total, breakdown

    @staticmethod
    def _dietary_match(dish_dietary, user_dietary: DietaryPreference) -> float:
        """1.0 when the dish satisfies the user's dietary preference."""
        if user_dietary == DietaryPreference.NONE:
            return 1.0
        if user_dietary == DietaryPreference.VEGAN:
            return 1.0 if dish_dietary == DietaryPreference.VEGAN else 0.0
        if user_dietary == DietaryPreference.VEGETARIAN:
            return (
                1.0
                if dish_dietary
                in (
                    DietaryPreference.VEGAN,
                    DietaryPreference.VEGETARIAN,
                )
                else 0.0
            )
        return 1.0

    @classmethod
    def _current_price(cls, dish: Any) -> tuple[object, bool]:
        """Return the currently active price and whether rush pricing applies."""
        try:
            from app.services.dish_service import DishService

            current_price, _, rush_active = DishService.calculate_time_shifted_discount(
                original_price=dish.original_price,
                pickup_start_time=dish.pickup_start_time,
                pickup_end_time=dish.pickup_end_time,
                override_discounted_price=dish.override_discounted_price,
                rule_discount_start_time=dish.rule_discount_start_time,
            )
            return current_price, rush_active
        except Exception:  # pragma: no cover - defensive
            return dish.rescue_price if dish.rescue_price else dish.original_price, False

    # ------------------------------------------------------------------ #
    # Layer 3 — Gemini justification (with deterministic fallback)
    # ------------------------------------------------------------------ #

    async def _generate_justifications(
        self,
        *,
        user_pref: UserPreference | None,
        candidates: list[tuple[Any, Any, Any]],
    ) -> dict[str, str]:
        """Return ``{dish_id: justification}`` via Gemini or fallback template."""
        if self.gemini_client is None:
            logger.warning("Recommendation: no Gemini client configured — using fallback")
            return {str(d.id): self._fallback_justification(d) for d, _, _ in candidates}

        try:
            prompt = self._build_justification_prompt(user_pref, candidates)
            response = await self.gemini_client.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": _JustificationBatch,
                },
            )
            parsed = getattr(response, "parsed", None)
            if parsed is None:
                raw = getattr(response, "text", "") or ""
                parsed = _JustificationBatch.model_validate_json(raw)
            if not isinstance(parsed, _JustificationBatch):
                raise ValueError("Gemini did not return a JustificationBatch")

            return {j.dish_id: j.justification for j in parsed.justifications}
        except (ValidationError, ValueError) as exc:
            logger.warning("Recommendation: Gemini output failed schema validation: %s", exc)
        except Exception as exc:  # timeout, network, quota, etc.
            logger.warning("Recommendation: Gemini call failed (%s) — fallback", exc)

        return {str(d.id): self._fallback_justification(d) for d, _, _ in candidates}

    @staticmethod
    def _build_justification_prompt(
        user_pref: UserPreference | None,
        candidates: list[tuple[Any, float, Any]],
    ) -> str:
        excluded = ", ".join(user_pref.excluded_allergens) if user_pref else "không có"
        lines = [
            "Bạn là trợ lý ẩm thực của EcoBite (giảm lãng thực thực).",
            f"Khiév dị ứng của người dùng: {excluded}.",
            "Dưới đây là Top 3 món đã được lọc sạch dị ứng và tính điểm gợi ý.",
            "Hãy viết lý do ngắn gọn (20-30 từ tiếng Việt) tại sao nên chọn từng món,",
            "không nhắc đến dị ứng đã loại trừ. Trả về CHỈ JSON theo schema:",
            "{justifications: [{dish_id, justification}]}.",
        ]
        for dish, _score, _store in candidates:
            lines.append(
                f"- {dish.id}: {dish.name} ({dish.category.value}), "
                f"giá {dish.original_price} VND, kho còn {dish.remaining_quantity}"
            )
        return "\n".join(lines)

    @staticmethod
    def _fallback_justification(dish: Any) -> str:
        """Deterministic template used when Gemini is unavailable."""
        return (
            f"{dish.name} ({dish.category.value}) là lựa chọn ăn cứu vặt hoàn hảo, "
            f"giá đã giảm sâu và còn {dish.remaining_quantity} suất — hãy nhanh tay đặt món!"
        )
