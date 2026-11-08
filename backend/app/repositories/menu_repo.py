"""Repository for Base Menu Catalog (MenuItem) persistence."""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import DietaryType, ItemCategory, MenuItem


async def create(
    db: AsyncSession,
    *,
    store_id: uuid.UUID,
    name: str,
    description: str | None,
    category: ItemCategory,
    original_price: Decimal,
    image_url: str,
    standard_ingredients: list[str],
    base_allergens: list[str],
    dietary_type: DietaryType = DietaryType.NON_VEGAN,
) -> MenuItem:
    """Insert a new base menu item for a store."""
    item = MenuItem(
        store_id=store_id,
        name=name,
        description=description,
        category=category,
        original_price=original_price,
        image_url=image_url,
        standard_ingredients=standard_ingredients,
        base_allergens=base_allergens,
        dietary_type=dietary_type,
        is_active=True,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_by_id(db: AsyncSession, item_id: uuid.UUID) -> MenuItem | None:
    """Retrieve a menu item by primary key UUID."""
    return await db.get(MenuItem, item_id)


async def list_by_store(
    db: AsyncSession,
    store_id: uuid.UUID,
    *,
    active_only: bool = True,
) -> list[MenuItem]:
    """List menu items belonging to a given store."""
    stmt = select(MenuItem).where(MenuItem.store_id == store_id)
    if active_only:
        stmt = stmt.where(MenuItem.is_active.is_(True))
    stmt = stmt.order_by(MenuItem.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update(
    db: AsyncSession,
    menu_item: MenuItem,
    update_data: dict[str, Any],
) -> MenuItem:
    """Apply partial updates to an existing MenuItem."""
    for field, value in update_data.items():
        if value is not None and hasattr(menu_item, field):
            setattr(menu_item, field, value)
    await db.commit()
    await db.refresh(menu_item)
    return menu_item


async def soft_delete(db: AsyncSession, menu_item: MenuItem) -> MenuItem:
    """Soft-delete a menu item by setting is_active=False."""
    menu_item.is_active = False
    await db.commit()
    await db.refresh(menu_item)
    return menu_item
