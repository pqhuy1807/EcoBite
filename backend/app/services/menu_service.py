"""Business logic for Base Menu Catalog (MenuItem) management."""

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import MenuItem
from app.models.store import KycStatus
from app.repositories import menu_repo, store_repo


class MenuService:
    """Create, read and maintain canonical menu items."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_store_menu_items(self, store_id: uuid.UUID) -> list[MenuItem]:
        """List active canonical menu items belonging to the store."""
        store = await store_repo.get_store_by_id(self.db, store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        return await menu_repo.list_by_store(self.db, store_id, active_only=True)

    async def create_menu_item(
        self,
        store_id: uuid.UUID,
        item_data: dict[str, Any],
    ) -> MenuItem:
        """Add a canonical menu item to an approved store."""
        store = await store_repo.get_store_by_id(self.db, store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        if store.kyc_status != KycStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Store KYC must be approved before managing its menu",
            )

        item = MenuItem(store_id=store_id, **item_data)
        return await menu_repo.create(
            self.db,
            store_id=store_id,
            name=item.name,
            description=item.description,
            category=item.category,
            original_price=item.original_price,
            image_url=item.image_url,
            standard_ingredients=list(item.standard_ingredients or []),
            base_allergens=list(item.base_allergens or []),
            dietary_type=item.dietary_type,
        )

    async def update_menu_item(
        self,
        item_id: uuid.UUID,
        update_data: dict[str, Any],
    ) -> MenuItem:
        """Update an owned menu item."""
        menu_item = await menu_repo.get_by_id(self.db, item_id)
        if menu_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found",
            )
        return await menu_repo.update(self.db, menu_item, update_data)

    async def delete_menu_item(
        self,
        item_id: uuid.UUID,
    ) -> MenuItem:
        """Soft-delete an owned menu item from the active catalog."""
        menu_item = await menu_repo.get_by_id(self.db, item_id)
        if menu_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found",
            )
        return await menu_repo.soft_delete(self.db, menu_item)
