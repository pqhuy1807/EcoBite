"""Allergen Hard Filter service (AGENTS.md Guardrail #7).

Provides a deterministic, case-insensitive, accent-insensitive hard filter that
removes any dish whose allergens intersect the user's ``excluded_allergens``
profile.  This runs at the *database/rule layer* — never delegated to Gemini or
any fuzzy AI match — so allergen exclusion is a hard safety invariant.
"""

from __future__ import annotations

import unicodedata
from typing import Any


def _normalize(text: str) -> str:
    """Lowercase, strip accents/diacritics and collapse whitespace."""
    text = text.lower().strip()
    # Decompose unicode (e.g. "đ" -> "d" + combining mark) then drop marks.
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.split())


class AllergenHardFilterService:
    """Hard allergen exclusion filter for dish discovery / recommendation.

    The filter compares normalized (accent-stripped, lowercased) allergen names
    so that ``"Đậu phộng"``, ``"đậu phộng"``, ``"Peanuts (Đậu phộng)"`` and
    ``"peanuts"`` all match the same user-declared exclusion.
    """

    @staticmethod
    def _match_allergen(dish_allergen: str, user_exclusion: str) -> bool:
        """Return True when a dish allergen string contains the user exclusion."""
        da = _normalize(dish_allergen)
        ua = _normalize(user_exclusion)
        if not ua:
            return False
        return ua in da or da in ua

    @classmethod
    def filter_dishes_by_allergens(
        cls,
        dishes: list[dict[str, Any]],
        excluded_allergens: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Remove dishes that contain any of the user's excluded allergens.

        Args:
            dishes: List of dish dicts, each expected to carry an ``allergens``
                key holding a list of allergen dicts (with ``allergen`` field)
                or plain strings.
            excluded_allergens: User-declared exclusion list (empty/None = no
                filtering, all dishes pass).

        Returns:
            Filtered list of dishes (same dict objects, order preserved).
        """
        exclusions = excluded_allergens or []
        if not exclusions:
            return list(dishes)

        normalized_exclusions = [_normalize(e) for e in exclusions if e]
        if not normalized_exclusions:
            return list(dishes)

        kept: list[dict[str, Any]] = []
        for dish in dishes:
            raw_allergens = dish.get("allergens") or []
            dish_allergen_names: list[str] = []
            for a in raw_allergens:
                if isinstance(a, dict):
                    dish_allergen_names.append(str(a.get("allergen", "")))
                else:
                    dish_allergen_names.append(str(a))

            is_excluded = any(
                cls._match_allergen(name, excl)
                for name in dish_allergen_names
                for excl in normalized_exclusions
            )
            if not is_excluded:
                kept.append(dish)

        return kept
