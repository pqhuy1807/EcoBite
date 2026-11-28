"""User module endpoints (JWT-protected), including preference CRUD."""

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DBSession
from app.models.user import DietaryPreference, User
from app.repositories import preference_repo
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse, summary="Current authenticated user")
async def read_current_user(current_user: CurrentUser) -> User:
    """Return the profile decoded from the request's bearer token."""
    return current_user


# ------------------------------------------------------------------ #
# Preference CRUD
# ------------------------------------------------------------------ #


@router.get(
    "/me/preferences",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Current user's preference profile",
)
async def read_my_preferences(
    current_user: CurrentUser,
    db: DBSession,
) -> dict[str, Any]:
    """Return the authenticated user's preference profile."""
    pref = await preference_repo.get_by_user_id(db, current_user.id)
    if pref is None:
        return {
            "id": None,
            "user_id": str(current_user.id),
            "preferred_categories": [],
            "dietary_preference": "NONE",
            "excluded_allergens": [],
            "max_budget": None,
            "updated_at": None,
        }
    return {
        "id": str(pref.id),
        "user_id": str(pref.user_id),
        "preferred_categories": list(pref.preferred_categories),
        "dietary_preference": pref.dietary_preference.value,
        "excluded_allergens": list(pref.excluded_allergens),
        "max_budget": float(pref.max_budget) if pref.max_budget is not None else None,
        "updated_at": pref.updated_at.isoformat() if pref.updated_at else None,
    }


@router.put(
    "/me/preferences",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update current user's preference profile",
)
async def update_my_preferences(
    current_user: CurrentUser,
    db: DBSession,
    *,
    preferred_categories: Annotated[
        list[str] | None, Query(description="Favorite categories such as RICE and NOODLES")
    ] = None,
    dietary_preference: Annotated[
        str | None, Query(description="NONE, VEGAN or VEGETARIAN")
    ] = None,
    excluded_allergens: Annotated[
        list[str] | None, Query(description="Allergens to exclude (canonical EUAllergen keys)")
    ] = None,
    max_budget: Annotated[
        float | None, Query(ge=0, description="Preferred maximum spending per meal (VND)")
    ] = None,
) -> dict[str, Any]:
    """Create or partially update the authenticated user's preferences.

    ``excluded_allergens`` is normalized to EUAllergen canonical keys before
    persistence (Guardrail #7).
    """
    diet = None
    if dietary_preference is not None:
        try:
            diet = DietaryPreference(dietary_preference.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid dietary_preference: {dietary_preference}",
            ) from None

    pref = await preference_repo.create_or_update(
        db,
        current_user.id,
        preferred_categories=preferred_categories,
        dietary_preference=diet,
        excluded_allergens=excluded_allergens,
        max_budget=Decimal(str(max_budget)) if max_budget is not None else None,
    )
    return {
        "id": str(pref.id),
        "user_id": str(pref.user_id),
        "preferred_categories": list(pref.preferred_categories),
        "dietary_preference": pref.dietary_preference.value,
        "excluded_allergens": list(pref.excluded_allergens),
        "max_budget": float(pref.max_budget) if pref.max_budget is not None else None,
        "updated_at": pref.updated_at.isoformat() if pref.updated_at else None,
    }
