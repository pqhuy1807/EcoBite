"""Repository for Surplus Dish persistence and atomic inventory control."""

import uuid

from sqlalchemy import case, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus


async def create(db: AsyncSession, dish: Dish) -> Dish:
    """Persist a single surplus dish listing."""
    db.add(dish)
    await db.commit()
    await db.refresh(dish)
    return dish


async def create_batch(db: AsyncSession, dishes: list[Dish]) -> list[Dish]:
    """Persist a batch of surplus dish listings in a single transaction."""
    db.add_all(dishes)
    await db.commit()
    for dish in dishes:
        await db.refresh(dish)
    return dishes


async def get_by_id(db: AsyncSession, dish_id: uuid.UUID) -> Dish | None:
    """Retrieve a dish by primary key UUID."""
    return await db.get(Dish, dish_id)


async def list_active_by_store(db: AsyncSession, store_id: uuid.UUID) -> list[Dish]:
    """List active surplus dishes with remaining inventory for a store."""
    stmt = (
        select(Dish)
        .where(
            Dish.store_id == store_id,
            Dish.status == DishStatus.ACTIVE,
            Dish.remaining_quantity > 0,
        )
        .order_by(Dish.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_quantity(
    db: AsyncSession,
    dish: Dish,
    new_quantity: int,
) -> Dish:
    """Manually set remaining quantity and adjust status accordingly."""
    dish.remaining_quantity = new_quantity
    if new_quantity == 0:
        dish.status = DishStatus.SOLD_OUT
    elif dish.status == DishStatus.SOLD_OUT and new_quantity > 0:
        dish.status = DishStatus.ACTIVE
    await db.commit()
    await db.refresh(dish)
    return dish


async def atomic_decrement_quantity(
    db: AsyncSession,
    dish_id: uuid.UUID,
    quantity: int,
    *,
    commit: bool = True,
) -> Dish | None:
    """Atomically decrement remaining_quantity to prevent over-selling.

    Executes:
        UPDATE dishes
        SET remaining_quantity = remaining_quantity - :quantity
        WHERE id = :dish_id AND remaining_quantity >= :quantity

    Returns the updated Dish if successful, or None if insufficient stock.

    Set commit=False when the caller needs to combine the stock change
    with another database operation in one transaction.
    """
    if quantity <= 0:
        return None

    new_rem = Dish.remaining_quantity - quantity

    stmt = (
        update(Dish)
        .where(
            Dish.id == dish_id,
            Dish.remaining_quantity >= quantity,
            Dish.status == DishStatus.ACTIVE,
        )
        .values(
            remaining_quantity=new_rem,
            status=case(
                (new_rem == 0, DishStatus.SOLD_OUT),
                else_=Dish.status,
            ),
        )
        .execution_options(synchronize_session=False)
    )

    result = await db.execute(stmt)

    if getattr(result, "rowcount", 0) == 0:
        return None

    if commit:
        await db.commit()

    dish = await db.get(Dish, dish_id)

    if dish is not None:
        await db.refresh(dish)

    return dish


async def atomic_increment_quantity(
    db: AsyncSession,
    dish_id: uuid.UUID,
    quantity: int,
    *,
    commit: bool = True,
) -> Dish | None:
    """Atomically restore remaining_quantity when an order is cancelled.

    Executes:
        UPDATE dishes
        SET remaining_quantity = remaining_quantity + :quantity
        WHERE id = :dish_id

    A SOLD_OUT dish is automatically re-activated after stock restoration.
    Other statuses (EXPIRED / INACTIVE) are preserved.

    Returns the updated Dish, or None if the dish does not exist.

    Set commit=False when the caller needs to combine stock restoration
    with another database operation in one transaction.
    """
    if quantity <= 0:
        return None

    new_rem = Dish.remaining_quantity + quantity

    stmt = (
        update(Dish)
        .where(Dish.id == dish_id)
        .values(
            remaining_quantity=new_rem,
            status=case(
                (Dish.status == DishStatus.SOLD_OUT, DishStatus.ACTIVE),
                else_=Dish.status,
            ),
        )
        .execution_options(synchronize_session=False)
    )

    result = await db.execute(stmt)

    if getattr(result, "rowcount", 0) == 0:
        return None

    if commit:
        await db.commit()

    dish = await db.get(Dish, dish_id)

    if dish is not None:
        await db.refresh(dish)

    return dish
