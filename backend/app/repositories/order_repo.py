
"""Repository for Order persistence, lookups and status lifecycle transitions."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.order import Order, OrderStatus


class OrderRepository:
    """Async data access layer for food rescue orders.

    Encapsulates every SQLAlchemy command so that app.services stays free of
    persistence concerns. Lookups eagerly load the consumer/store/dish graph
    to avoid N+1 queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_order(
        self,
        order_data: dict[str, Any],
        *,
        commit: bool = True,
    ) -> Order:
        """Persist a new Order record.

        Set commit=False when the order must be saved together with other
        database changes in a single transaction.
        """
        order = Order(**order_data)
        self.db.add(order)

        if commit:
            await self.db.commit()
            await self.db.refresh(order)
        else:
            await self.db.flush()

        return order

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Retrieve an order by primary key, or None when missing.

        Consumer, store, dish and QR token relationships are eagerly loaded
        to avoid N+1 queries.
        """
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.consumer),
                selectinload(Order.store),
                selectinload(Order.dish),
                selectinload(Order.qr_token),
            )
            .execution_options(populate_existing=True)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_consumer(
        self,
        consumer_id: uuid.UUID,
        *,
        order_status: OrderStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:
        """List paginated orders placed by a consumer, newest first."""
        return await self._list_orders(
            Order.consumer_id == consumer_id,
            order_status=order_status,
            skip=skip,
            limit=limit,
        )

    async def list_by_store(
        self,
        store_id: uuid.UUID,
        *,
        order_status: OrderStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:
        """List paginated orders received by a store, newest first."""
        return await self._list_orders(
            Order.store_id == store_id,
            order_status=order_status,
            skip=skip,
            limit=limit,
        )

    async def _list_orders(
        self,
        scope_filter: ColumnElement[bool],
        *,
        order_status: OrderStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:
        """Execute shared paginated and status-filtered order history query."""
        stmt = select(Order).where(scope_filter)

        if order_status is not None:
            stmt = stmt.where(Order.status == order_status)

        stmt = (
            stmt.order_by(Order.created_at.desc(), Order.id.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_order_code(self, code: str) -> Order | None:
        """Retrieve an order by its display code."""
        result = await self.db.execute(
            select(Order).where(Order.order_code == code)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        order_id: uuid.UUID,
        new_status: OrderStatus,
    ) -> Order | None:
        """Update an order status.

        Returns None when the order does not exist.
        """
        order = await self.db.get(Order, order_id)

        if order is None:
            return None

        order.status = new_status
        await self.db.commit()
        await self.db.refresh(order)

        return order

    async def cancel_if_allowed(
        self,
        order_id: uuid.UUID,
        allowed_statuses: tuple[OrderStatus, ...],
        *,
        commit: bool = True,
    ) -> Order | None:
        """Atomically move an order to CANCELLED.

        The order is updated only when its current status belongs to
        allowed_statuses. This prevents concurrent cancellation requests
        from restoring inventory more than once.

        Set commit=False when cancellation and inventory restoration
        must be committed in the same transaction.

        Returns None when the order is missing or cannot be cancelled.
        """
        stmt = (
            update(Order)
            .where(
                Order.id == order_id,
                Order.status.in_(allowed_statuses),
            )
            .values(status=OrderStatus.CANCELLED)
            .execution_options(synchronize_session=False)
        )

        result = await self.db.execute(stmt)

        if getattr(result, "rowcount", 0) == 0:
            return None

        if commit:
            await self.db.commit()
        else:
            await self.db.flush()

        order = await self.get_by_id(order_id)

        if order is not None:
            await self.db.refresh(order)

        return order

    async def complete_if_allowed(
        self,
        order_id: uuid.UUID,
        allowed_statuses: tuple[OrderStatus, ...],
        *,
        completed_at: datetime | None = None,
        commit: bool = True,
    ) -> Order | None:
        """Atomically transition order to COMPLETED.

        The order is updated only when its current status belongs to
        allowed_statuses.

        Returns None when the order is missing or cannot be completed.
        """
        resolved_at = (
            completed_at
            if completed_at is not None
            else datetime.now(UTC)
        )

        stmt = (
            update(Order)
            .where(
                Order.id == order_id,
                Order.status.in_(allowed_statuses),
            )
            .values(
                status=OrderStatus.COMPLETED,
                completed_at=resolved_at,
            )
            .execution_options(synchronize_session=False)
        )

        result = await self.db.execute(stmt)

        if getattr(result, "rowcount", 0) == 0:
            return None

        if commit:
            await self.db.commit()
        else:
            await self.db.flush()

        order = await self.get_by_id(order_id)

        if order is not None:
            await self.db.refresh(order)

        return order
