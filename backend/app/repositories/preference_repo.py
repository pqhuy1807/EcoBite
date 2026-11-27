"""Repository for UserPreference CRUD operations.

Exposed via ``GET /api/v1/users/me/preferences`` and
``PUT /api/v1/users/me/preferences``.
"""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import DietaryPreference, UserPreference
from app.schemas.nlp import EUAllergen
from app.services.allergen_filter_service import _normalize

# Common Vietnamese / English synonyms → EUAllergen canonical keys.
# Allows inputs like "Hải sản", "Đậu phộng", "Trứng", "Sữa" to resolve to the
# canonical enum key used for the hard SQL allergen invariant (Guardrail #7).
_ALLERGEN_SYNONYMS: dict[str, str] = {
    "dau phong": "PEANUTS",
    "peanuts": "PEANUTS",
    "hai san": "CRUSTACEANS",
    "seafood": "CRUSTACEANS",
    "tom": "CRUSTACEANS",
    "cua": "CRUSTACEANS",
    "tom cua": "CRUSTACEANS",
    "trung": "EGGS",
    "eggs": "EGGS",
    "trung ga": "EGGS",
    "sua": "MILK",
    "milk": "MILK",
    "sua bo": "MILK",
    "ca": "FISH",
    "fish": "FISH",
    "ca nguoc mam ca": "FISH",
    "nuoc mam": "FISH",
}


def normalize_excluded_allergens(values: list[str]) -> list[str]:
    """Map raw allergen input strings to EUAllergen canonical keys (enum names).

    Accepts Vietnamese names, English names or the full ``EUAllergen`` value
    (e.g. ``"Đậu phộng"``, ``"peanuts"``, ``"Peanuts (Đậu phộng)"``) and
    normalizes them to the canonical enum key (e.g. ``"PEANUTS"``). Duplicates
    are removed while preserving first-seen order.
    """
    result: list[str] = []
    for value in values:
        key = _match_eu_allergen(value)
        if key and key not in result:
            result.append(key)
    return result


def _match_eu_allergen(value: str) -> str | None:
    normalized = _normalize(value or "")
    if not normalized:
        return None
    # 1. Direct synonym lookup (fast path for common Vietnamese/English names).
    if normalized in _ALLERGEN_SYNONYMS:
        return _ALLERGEN_SYNONYMS[normalized]
    # 2. Fall back to matching against EUAllergen enum name / value.
    for member in EUAllergen:
        enum_name_norm = _normalize(member.name)
        enum_value_norm = _normalize(member.value)
        if (
            normalized == enum_name_norm
            or normalized == enum_value_norm
            or normalized in enum_value_norm
            or enum_value_norm in normalized
        ):
            return member.name
    return None


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> UserPreference | None:
    """Read the preference row for a user, or None when not set yet."""
    stmt = select(UserPreference).where(UserPreference.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_or_update(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    preferred_categories: list[str] | None = None,
    dietary_preference: DietaryPreference | None = None,
    excluded_allergens: list[str] | None = None,
    max_budget: Decimal | None = None,
) -> UserPreference:
    """Create (if missing) or partially update a user's preference row.

    ``excluded_allergens`` is always normalized to EUAllergen canonical keys
    before persisting, keeping the allergen hard-invariant stable across the
    platform (Guardrail #7).
    """
    pref = await get_by_user_id(db, user_id)
    if pref is None:
        pref = UserPreference(
            user_id=user_id,
            preferred_categories=preferred_categories or [],
            dietary_preference=dietary_preference or DietaryPreference.NONE,
            excluded_allergens=normalize_excluded_allergens(excluded_allergens or []),
            max_budget=max_budget,
        )
        db.add(pref)
    else:
        if preferred_categories is not None:
            pref.preferred_categories = preferred_categories
        if dietary_preference is not None:
            pref.dietary_preference = dietary_preference
        if excluded_allergens is not None:
            pref.excluded_allergens = normalize_excluded_allergens(excluded_allergens)
        if max_budget is not None:
            pref.max_budget = max_budget
    await db.commit()
    await db.refresh(pref)
    return pref
