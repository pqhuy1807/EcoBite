"""Verified review endpoints: submit reviews and list store feedback (Feature 8A)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DBSession, require_roles
from app.models.user import User, UserRole
from app.schemas.interaction import ReviewCreate, ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter()

SkipQuery = Annotated[int, Query(ge=0, description="Số lượng bản ghi bỏ qua")]
LimitQuery = Annotated[
    int,
    Query(ge=1, le=100, description="Số lượng bản ghi tối đa (1-100)"),
]


@router.post(
    "/orders/{order_id}/review",
    status_code=status.HTTP_201_CREATED,
    response_model=ReviewResponse,
    summary="Đăng đánh giá cho đơn hàng giải cứu",
    description="Chỉ người tiêu dùng (CONSUMER) sở hữu đơn hàng COMPLETED mới được đánh giá.",
)
async def create_order_review(
    order_id: uuid.UUID,
    payload: ReviewCreate,
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.CONSUMER)),
    ],
) -> ReviewResponse:
    """Submit a verified review for a completed food rescue order."""
    review = await ReviewService(db).create_review(order_id, current_user, payload)
    return ReviewResponse.model_validate(review)


@router.get(
    "/stores/{store_id}/reviews",
    status_code=status.HTTP_200_OK,
    response_model=list[ReviewResponse],
    summary="Lấy danh sách đánh giá của cửa hàng",
    description="Xem các đánh giá đã xác thực của cửa hàng, sắp xếp mới nhất với phân trang.",
)
async def list_store_reviews(
    store_id: uuid.UUID,
    db: DBSession,
    skip: SkipQuery = 0,
    limit: LimitQuery = 20,
) -> list[ReviewResponse]:
    """Retrieve verified reviews for a store, newest first."""
    reviews = await ReviewService(db).list_store_reviews(store_id, skip=skip, limit=limit)
    return [ReviewResponse.model_validate(r) for r in reviews]
