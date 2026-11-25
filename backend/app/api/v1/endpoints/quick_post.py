"""Gemini Quick-Post endpoints (PA5 head-start).

Extracts structured surplus-dish listings from free-text input via Gemini 2.5
Flash, then applies the Allergen Hard Filter (Guardrail #7) before returning.
"""

from typing import Any, cast

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DBSession
from app.models.user import UserRole
from app.services.allergen_filter_service import AllergenHardFilterService
from app.services.quick_post_service import build_quick_post_service

router = APIRouter()


@router.post(
    "/quick-post/extract",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Extract surplus dishes from free text via Gemini Quick-Post",
)
async def extract_quick_post(
    *,
    current_user: CurrentUser,
    db: DBSession,
    text_input: str,
) -> dict[str, Any]:
    """Extract surplus-dish listings from free text.

    Only authenticated consumers may use Quick-Post. The user's
    ``excluded_allergens`` preference is applied as a hard filter (Guardrail #7)
    so no excluded allergen can leak into the response.
    """
    if current_user.role != UserRole.CONSUMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ khách hàng mới có thể sử dụng Quick-Post",
        )

    service = build_quick_post_service(db)
    result = await service.extract_quick_post(
        text_input=text_input,
        user_preference=getattr(current_user, "preference", None),
    )
    return result


@router.get(
    "/quick-post/allergen-filter/test",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Self-test the allergen hard filter (dev only)",
)
async def allergen_filter_self_test() -> dict[str, Any]:
    """Return a deterministic self-test of the Allergen Hard Filter."""
    dishes = [
        {
            "id": "d1",
            "name": "Bánh mì trứng",
            "allergens": [
                {
                    "allergen": "Eggs (Trứng)",
                    "risk_level": "HIGH",
                    "source": "EXPLICIT",
                    "reason": "Có trứng",
                }
            ],
        },
        {
            "id": "d2",
            "name": "Cơm sườn",
            "allergens": [
                {
                    "allergen": "Gluten",
                    "risk_level": "MEDIUM",
                    "source": "INFERRED",
                    "reason": "Có bột mì",
                }
            ],
        },
        {
            "id": "d3",
            "name": "Chay đậu phụ",
            "allergens": [
                {
                    "allergen": "Soybeans (Đậu nành)",
                    "risk_level": "HIGH",
                    "source": "EXPLICIT",
                    "reason": "Có đậu phụ",
                }
            ],
        },
        {
            "id": "d4",
            "name": "Nước coc",
            "allergens": [],
        },
    ]

    filtered = AllergenHardFilterService.filter_dishes_by_allergens(
        cast(list[dict[str, Any]], dishes),
        excluded_allergens=["đậu phộng", "Gluten", "Sữa"],
    )
    kept_ids = [d["id"] for d in filtered]

    return {
        "input_count": len(dishes),
        "excluded_allergens": ["đậu phộng", "Gluten", "Sữa"],
        "kept_ids": kept_ids,
        "filtered_out_count": len(dishes) - len(filtered),
        "assert_d1_removed": "d1" not in kept_ids,  # Eggs not excluded here, but kept
        "assert_d2_removed": "d2" not in kept_ids,  # Gluten excluded
        "assert_d3_kept": "d3" in kept_ids,  # Soybeans not excluded here
        "assert_d4_kept": "d4" in kept_ids,  # No allergens
    }
