"""Repository for Order persistence, lookups and status lifecycle transitions."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

        Consumer, store and dish relationships are eagerly loaded with
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
            )
            .execution_options(populate_existing=True)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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
