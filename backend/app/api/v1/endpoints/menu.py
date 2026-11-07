"""Store-owned menu catalog endpoints."""

import uuid

from fastapi import APIRouter, status

from app.api.deps import DBSession, StoreOwner
from app.models.menu_item import MenuItem
from app.schemas.menu_item import MenuItemBase, MenuItemResponse, MenuItemUpdate
from app.services.menu_service import MenuService

router = APIRouter()


@router.post(
    "/stores/{store_id}/menu-items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_menu_item(
    store_id: uuid.UUID,
    item_in: MenuItemBase,
    db: DBSession,
    _: StoreOwner,
) -> MenuItem:
    """Add a canonical menu item to an approved store."""
    return await MenuService(db).create_menu_item(
        store_id, item_in.model_dump(exclude={"is_active"})
    )


@router.get("/stores/{store_id}/menu-items")
async def get_store_menu_items(
    store_id: uuid.UUID,
    db: DBSession,
    _: StoreOwner,
) -> dict[str, object]:
    """List active canonical menu items belonging to the authenticated store."""
    items = await MenuService(db).get_store_menu_items(store_id)
    return {
        "total": len(items),
        "items": [MenuItemResponse.model_validate(item) for item in items],
    }


@router.put("/menu-items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: uuid.UUID,
    item_in: MenuItemUpdate,
    db: DBSession,
    _: StoreOwner,
) -> MenuItem:
    """Update an owned menu item."""
    return await MenuService(db).update_menu_item(item_id, item_in.model_dump(exclude_unset=True))


@router.delete("/menu-items/{item_id}", response_model=MenuItemResponse)
async def delete_menu_item(
    item_id: uuid.UUID,
    db: DBSession,
    _: StoreOwner,
) -> MenuItem:
    """Soft-delete an owned menu item from the active catalog."""
    return await MenuService(db).delete_menu_item(item_id)
