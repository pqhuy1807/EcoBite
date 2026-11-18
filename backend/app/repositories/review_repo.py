"""Repository for Verified Reviews persistence and store rating aggregation."""

import uuid
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interaction import Review
from app.models.store import Store

DEFAULT_STORE_RATING = Decimal("5.00")


class ReviewRepository:
    """Async data access layer for customer verified reviews.

    Encapsulates all SQLAlchemy commands for reviews and store rating aggregation
    so that services remain decoupled from database persistence.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_review(
        self,
        *,
        order_id: uuid.UUID,
        consumer_id: uuid.UUID,
        store_id: uuid.UUID,
        dish_id: uuid.UUID,
        rating: int,
        comment: str | None = None,
        tags: list[str] | None = None,
        photo_urls: list[str] | None = None,
        commit: bool = True,
    ) -> Review:
        """Persist a new Review record for a completed order.

        Args:
            order_id: Unique UUID of the completed order being reviewed.
            consumer_id: UUID of the consumer authoring the review.
            store_id: UUID of the store receiving the review.
            dish_id: UUID of the rescue dish being reviewed.
            rating: Star rating between 1 and 5.
            comment: Optional text feedback.
            tags: List of feedback tags (e.g. ['Ngon', 'Đúng giờ']).
            photo_urls: List of attached image URLs.
            commit: Whether to commit immediately or flush only.
        """
        review = Review(
            order_id=order_id,
            consumer_id=consumer_id,
            store_id=store_id,
            dish_id=dish_id,
            rating=rating,
            comment=comment,
            tags=tags or [],
            photo_urls=photo_urls or [],
        )
        self.db.add(review)

        if commit:
            await self.db.commit()
            await self.db.refresh(review)
        else:
            await self.db.flush()

        return review

    async def get_by_id(self, review_id: uuid.UUID) -> Review | None:
        """Retrieve a review by its primary key UUID."""
        return await self.db.get(Review, review_id)

    async def get_by_order_id(self, order_id: uuid.UUID) -> Review | None:
        """Retrieve the unique review associated with an order, or None."""
        stmt = (
            select(Review)
            .where(Review.order_id == order_id)
            .options(
                selectinload(Review.consumer),
                selectinload(Review.dish),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_store(
        self,
        store_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Review]:
        """List reviews for a store, newest first, with pagination and eager relationships."""
        stmt = (
            select(Review)
            .where(Review.store_id == store_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Review.consumer),
                selectinload(Review.dish),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_store_rating(
        self,
        store_id: uuid.UUID,
        *,
        commit: bool = True,
    ) -> tuple[Decimal, int]:
        """Calculate and update Store.rating_avg and Store.rating_count from verified reviews.

        If the store has no reviews, defaults to rating_avg=5.00 and rating_count=0.

        Returns:
            A tuple of (new_rating_avg, new_rating_count).
        """
        agg_stmt = select(
            func.count(Review.id).label("total_count"),
            func.avg(Review.rating).label("avg_rating"),
        ).where(Review.store_id == store_id)

        agg_result = await self.db.execute(agg_stmt)
        row = agg_result.one()
        total_count: int = row.total_count or 0
        avg_val = row.avg_rating

        if total_count == 0 or avg_val is None:
            new_rating_avg = DEFAULT_STORE_RATING
            new_rating_count = 0
        else:
            new_rating_avg = round(Decimal(str(avg_val)), 2)
            new_rating_count = total_count

        update_stmt = (
            update(Store)
            .where(Store.id == store_id)
            .values(
                rating_avg=new_rating_avg,
                rating_count=new_rating_count,
            )
        )
        await self.db.execute(update_stmt)

        if commit:
            await self.db.commit()
        else:
            await self.db.flush()

        return new_rating_avg, new_rating_count

