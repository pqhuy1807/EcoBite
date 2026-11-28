"""AI-2 Recommendation endpoints (baseline).

* ``GET /api/v1/recommendations/personalized`` — Top-K personalized,
  allergen-safe dish recommendations (Layers 1-3).
* ``POST /api/v1/dishes/search-semantic`` — natural-language Vietnamese dish
  search with Gemini Structured Output extraction + Layer 1 SQL Allergen Hard
  Filter (Guardrail #7).

The Gemini client is injected optionally; when unavailable the endpoints
degrade to deterministic templates and never crash.
"""

import logging
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DBSession
from app.models.user import DietaryPreference, UserRole
from app.repositories import preference_repo
from app.schemas.recommendation import (
    DishRecommendationItem,
    PersonalizedRecommendationResponse,
    SemanticSearchFilter,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_recommendation_service(db: DBSession) -> RecommendationService:
    """Factory — keeps the endpoint layer free of Gemini client details.

    No Gemini client is wired by default, so the endpoints gracefully fall
    back to deterministic justifications/templates until a client is
    configured in ``app.state``.
    """
    return RecommendationService(db)


# ------------------------------------------------------------------ #
# Personalized recommendations (GET /recommendations/personalized)
# ------------------------------------------------------------------ #


@router.get(
    "/recommendations/personalized",
    response_model=PersonalizedRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Top-K personalized allergen-safe dish recommendations",
)
async def get_personalized_recommendations(
    current_user: CurrentUser,
    db: DBSession,
    lat: float = Query(..., ge=-90.0, le=90.0, description="User latitude"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="User longitude"),
    radius_km: float = Query(default=3.0, ge=1.0, le=10.0, description="Search radius in km"),
    top_k: int = Query(default=3, ge=1, le=20, description="Number of results"),
) -> PersonalizedRecommendationResponse:
    """Return Top-K personalized dish recommendations.

    Only consumers may call this endpoint. The response contains dishes that
    have already passed the Layer 1 SQL Allergen Hard Filter, ranked by the
    Layer 2 heuristic score, each with a Layer 3 ``ai_justification``
    (Gemini 2.5 Flash or deterministic fallback).
    """
    if current_user.role != UserRole.CONSUMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ khách hàng mới có thể xem gợi ý cá nhân hóa",
        )

    service = _build_recommendation_service(db)
    result = await service.get_personalized(
        user_id=str(current_user.id),
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        top_k=top_k,
    )

    items = [
        DishRecommendationItem(
            id=item["id"],
            store_id=item["store_id"],
            store_name=item["store_name"],
            name=item["name"],
            category=item["category"],
            current_price=item["current_price"],
            original_price=item["original_price"],
            is_rule_discount_active=item["is_rule_discount_active"],
            distance_meters=item["distance_meters"],
            score=item["score"],
            breakdown=item["breakdown"],
            ai_justification=item["ai_justification"],
        )
        for item in result["items"]
    ]
    return PersonalizedRecommendationResponse(
        items=items,
        total=result["total"],
        user_location=result["user_location"],
        radius_km=result["radius_km"],
    )


# ------------------------------------------------------------------ #
# Semantic dish search (POST /dishes/search-semantic)
# ------------------------------------------------------------------ #


@router.post(
    "/dishes/search-semantic",
    response_model=SemanticSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic dish search from natural-language Vietnamese query",
)
async def search_semantic_dishes(
    current_user: CurrentUser,
    db: DBSession,
    payload: SemanticSearchRequest,
) -> SemanticSearchResponse:
    """Parse a Vietnamese query into structured filters via Gemini, then return
    allergen-safe, ranked dishes.

    Gemini extraction errors fall back to empty filters; the Layer 1 SQL
    Allergen Hard Filter is always enforced before results are returned.
    """
    from app.repositories import recommendation_repo
    from app.services.allergen_filter_service import AllergenHardFilterService

    # 1. Extract structured filters (Gemini with deterministic fallback).
    extracted = SemanticSearchFilter()
    service = _build_recommendation_service(db)
    if service.gemini_client is not None:
        try:
            prompt = (
                "Bạn là trợ lý trích xuất bộ lọc món ăn cho EcoBite. "
                "Nhập truy vấn tiếng Việt dưới đây và bóc tách thành JSON theo schema: "
                "{max_price (VND, số), categories (danh sách trong RICE/NOODLES/"
                "BAKERY/BEVERAGE/VEGETARIAN/OTHER), dietary (NONE/VEGAN/"
                "VEGETARIAN), keywords (danh sách từ khóa)}. "
                f'Truy vấn: """{payload.query}"""\n'
                "Trả về CHỈ JSON."
            )
            response = await service.gemini_client.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": SemanticSearchFilter,
                },
            )
            parsed = getattr(response, "parsed", None)
            if parsed is None:
                raw = getattr(response, "text", "") or ""
                parsed = SemanticSearchFilter.model_validate_json(raw)
            if isinstance(parsed, SemanticSearchFilter):
                extracted = parsed
        except Exception as exc:  # timeout, network, schema, etc.
            logger.warning("Semantic search: Gemini extraction failed: %s", exc)
            extracted = SemanticSearchFilter()

    # 2. Layer 1 candidates (SQL allergen hard filter applied inside).
    candidates = await recommendation_repo.list_candidate_dishes(
        db,
        lat=payload.lat,
        lng=payload.lng,
        radius_km=payload.radius_km,
        excluded_allergens=[],  # consumer preference not available here; enforced below if known
        limit=100,
    )

    # Apply consumer's excluded allergens if available (hard invariant).
    pref = await preference_repo.get_by_user_id(db, current_user.id)
    excluded_allergens = list(pref.excluded_allergens or []) if pref else []
    if excluded_allergens:
        candidates = [
            (d, dist, s)
            for d, dist, s in candidates
            if AllergenHardFilterService.filter_dishes_by_allergens(
                [{"allergens": d.allergens or []}], excluded_allergens
            )
        ]

    # 3. Additional semantic filters from extraction.
    def _matches(dish: Any, dist_m: float) -> bool:
        if extracted.max_price is not None:
            price = service._current_price(dish)[0]
            if price is not None and Decimal(str(price)) > extracted.max_price:
                return False
        if extracted.categories and dish.category not in extracted.categories:
            return False
        if extracted.dietary is not None:
            ok = service._dietary_match(dish.dietary_type, extracted.dietary)
            if not ok:
                return False
        if extracted.keywords:
            haystack = " ".join(
                [dish.name or "", dish.description or "", " ".join(dish.ingredients or [])]
            ).lower()
            if not any(k.lower() in haystack for k in extracted.keywords):
                return False
        return True

    filtered = [(d, dist, s) for d, dist, s in candidates if _matches(d, dist)]

    # 4. Score and rank (reuse Layer 2 scoring).
    preferred_categories = list(pref.preferred_categories or []) if pref else []
    dietary_preference = pref.dietary_preference if pref else DietaryPreference.NONE
    max_budget = pref.max_budget if pref else None

    scored = []
    for dish, dist_m, store in filtered:
        score, breakdown = service._score_dish(
            dish=dish,
            dist_m=dist_m,
            radius_km=payload.radius_km,
            preferred_categories=preferred_categories,
            dietary_preference=dietary_preference,
            max_budget=max_budget,
        )
        scored.append((score, dish, store, dist_m, breakdown))
    scored.sort(key=lambda item: item[0], reverse=True)

    items = []
    for score, dish, store, dist_m, breakdown in scored:
        items.append(
            DishRecommendationItem(
                id=str(dish.id),
                store_id=str(dish.store_id),
                store_name=store.name,
                name=dish.name,
                category=dish.category,
                current_price=service._current_price(dish)[0],
                original_price=dish.original_price,
                is_rule_discount_active=breakdown.get("rush_active", False),
                distance_meters=round(dist_m, 1),
                score=round(score, 4),
                breakdown=breakdown,
                ai_justification=service._fallback_justification(dish),
            )
        )

    return SemanticSearchResponse(
        items=items,
        total=len(items),
        extracted_filters=extracted,
    )
