"""Business logic for a store's canonical menu catalog."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import MenuItem
from app.models.store import KycStatus, Store


class MenuService:
    """Create, read and maintain canonical menu items."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_store_menu_items(self, store_id: uuid.UUID) -> list[MenuItem]:
        store = await self.db.get(Store, store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        result = await self.db.execute(
            select(MenuItem)
            .where(MenuItem.store_id == store_id, MenuItem.is_active.is_(True))
            .order_by(MenuItem.created_at, MenuItem.id)
        )
        return list(result.scalars().all())

    async def create_menu_item(self, store_id: uuid.UUID, item_data: dict) -> MenuItem:
        store = await self.db.get(Store, store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        if store.kyc_status != KycStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Store KYC must be approved before managing its menu",
            )

        item = MenuItem(store_id=store_id, **item_data)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_menu_item(self, item_id: uuid.UUID, update_data: dict) -> MenuItem:
        item = await self.db.get(MenuItem, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        if update_data:
            for field, value in update_data.items():
                setattr(item, field, value)
            await self.db.commit()
            await self.db.refresh(item)
        return item

    async def delete_menu_item(self, item_id: uuid.UUID) -> MenuItem:
        item = await self.db.get(MenuItem, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        item.is_active = False
        await self.db.commit()
        await self.db.refresh(item)
        return item
