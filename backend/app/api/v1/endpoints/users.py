"""User module endpoints (JWT-protected)."""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse, summary="Current authenticated user")
async def read_current_user(current_user: CurrentUser) -> User:
    """Return the profile decoded from the request's bearer token."""
    return current_user
