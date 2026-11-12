"""Repository for Order persistence, lookups and status lifecycle transitions."""

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.order import Order, OrderStatus


class OrderRepository:
    """Async data access layer for food rescue orders.

    Encapsulates every SQLAlchemy command so that `app.services` stays free of
    persistence concerns. Lookups eagerly load the consumer/store/dish graph
    (avoiding N+1 queries) as required for QR confirmation and notifications.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_order(self, order_data: dict[str, Any]) -> Order:
        """Persist a new Order record built from the given payload."""
        order = Order(**order_data)
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Retrieve an order by primary key, or None when missing.

        Consumer, store, dish and QR token relationships are eagerly loaded with
        `selectinload` so serialising a detailed response never triggers
        per-relationship lazy queries (N+1 prevention).
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
        stmt = stmt.order_by(Order.created_at.desc(), Order.id.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_order_code(self, code: str) -> Order | None:
        """Retrieve an order by its display code (e.g. `EB-20261109-XXXX`)."""
        result = await self.db.execute(select(Order).where(Order.order_code == code))
        return result.scalar_one_or_none()

    async def update_status(self, order_id: uuid.UUID, new_status: OrderStatus) -> Order | None:
        """Move an order to `new_status` (CONFIRMED/READY_FOR_PICKUP/.../EXPIRED).

        Returns the refreshed Order, or None when the order does not exist —
        following the repository convention where the service layer decides
        whether missing data becomes an HTTP error.
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
    ) -> Order | None:
        """Atomically move an order to CANCELLED, but only from `allowed_statuses`.

        Executes a conditional update:
            UPDATE orders SET status = 'CANCELLED'
            WHERE id = :order_id AND status IN (:allowed_statuses)

        The condition makes concurrent cancel requests race for a single winner,
        so the stock restoration performed by the service right after this call
        can never run twice (anti double-refund, Guardrail #4 mindset).

        Returns the refreshed Order, or None when the order is missing or already
        in a non-cancellable state — the service layer maps that to HTTP errors.
        """
        stmt = (
            update(Order)
            .where(Order.id == order_id, Order.status.in_(allowed_statuses))
            .values(status=OrderStatus.CANCELLED)
            .execution_options(synchronize_session=False)
        )
        result = await self.db.execute(stmt)
        if getattr(result, "rowcount", 0) == 0:
            return None
        await self.db.commit()
        return await self.get_by_id(order_id)
