"""Business logic service for customer verified reviews (Feature 8A).

Guarantees:
- Only CONSUMER role can author reviews.
- Consumer must own the completed order.
- Order must be in COMPLETED status.
- One review per order_id (idempotent / unique constraint).
- Store rating_avg and rating_count are automatically updated in the same transaction.
"""

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Review
from app.models.order import OrderStatus
from app.models.user import User, UserRole
from app.repositories.order_repo import OrderRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.interaction import ReviewCreate

logger = logging.getLogger(__name__)


class ReviewService:
    """Service handling business workflows for verified food reviews."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.review_repo = ReviewRepository(db)
        self.order_repo = OrderRepository(db)

    async def create_review(
        self,
        order_id: uuid.UUID,
        consumer: User,
        payload: ReviewCreate,
    ) -> Review:
        """Create a verified review for a completed order.

        Enforces:
        1. Role must be CONSUMER.
        2. Consumer must be the order owner.
        3. Order status must be COMPLETED.
        4. Exactly one review per order (checks existing + catches DB IntegrityError).
        5. Atomically aggregates and updates the store's rating average.
        """
        # 1. RBAC: Only CONSUMER role is allowed to review
        if consumer.role != UserRole.CONSUMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ người tiêu dùng (CONSUMER) mới có quyền đánh giá đơn hàng",
            )

        # 2. Look up the order
        order = await self.order_repo.get_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # 3. Ownership: Current consumer must own the order
        if order.consumer_id != consumer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền đánh giá đơn hàng này",
            )

        # 4. Status invariant: Only COMPLETED orders can be reviewed
        if order.status != OrderStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Chỉ đơn hàng ở trạng thái COMPLETED mới có thể đánh giá "
                    f"(trạng thái hiện tại: {order.status.value})"
                ),
            )

        # 5. Pre-check: Verify no existing review for this order
        existing = await self.review_repo.get_by_order_id(order_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Đơn hàng đã được đánh giá trước đó",
            )

        # 6. Atomic creation and rating aggregation with IntegrityError safety backstop
        try:
            review = await self.review_repo.create_review(
                order_id=order.id,
                consumer_id=consumer.id,
                store_id=order.store_id,
                dish_id=order.dish_id,
                rating=payload.rating,
                comment=payload.comment,
                tags=payload.tags,
                photo_urls=payload.photo_urls,
                commit=False,
            )
            await self.review_repo.update_store_rating(
                order.store_id,
                commit=False,
            )
            await self.db.commit()
            await self.db.refresh(review)
            return review
        except IntegrityError as exc:
            await self.db.rollback()
            logger.warning(
                "IntegrityError on review creation for order_id=%s: %s",
                order_id,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Đơn hàng đã được đánh giá trước đó",
            ) from exc
        except Exception:
            await self.db.rollback()
            raise

    async def get_by_order_id(self, order_id: uuid.UUID) -> Review | None:
        """Retrieve review by order_id."""
        return await self.review_repo.get_by_order_id(order_id)

    async def list_store_reviews(
        self,
        store_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Review]:
        """List reviews for a store, newest first, with pagination."""
        return await self.review_repo.list_by_store(
            store_id,
            skip=skip,
            limit=limit,
        )
