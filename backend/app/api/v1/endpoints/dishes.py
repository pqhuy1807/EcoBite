"""Store-owned surplus dish endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, status

from app.api.deps import DBSession, StoreOwner
from app.schemas.dish import (
    DishBatchPublish,
    DishPublish,
    DishQuantityUpdate,
    DishResponse,
)
from app.services.dish_service import DishService

router = APIRouter()


@router.post(
    "/dishes",
    response_model=DishResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_surplus_dish(
    dish_in: DishPublish,
    db: DBSession,
    _: StoreOwner,
) -> dict[str, Any]:
    """Publish surplus stock using the selected menu item's canonical data."""
    return await DishService(db).create_surplus_dish(
        dish_in.menu_item_id,
        dish_in.model_dump(exclude={"menu_item_id"}),
    )


@router.post("/dishes/batch", status_code=status.HTTP_201_CREATED)
async def batch_create_surplus_dishes(
    batch_in: DishBatchPublish,
    db: DBSession,
    _: StoreOwner,
) -> dict[str, Any]:
    """Publish multiple menu-grounded surplus items in one transaction."""
    dishes = await DishService(db).batch_create_dishes(
        [item.model_dump() for item in batch_in.dishes],
        batch_in.pickup_start_time,
        batch_in.pickup_end_time,
        batch_in.rule_discount_start_time,
    )
    return {"created_count": len(dishes), "dishes": dishes}


@router.get("/stores/{store_id}/dishes/active")
async def get_active_store_dishes(
    store_id: uuid.UUID,
    db: DBSession,
    _: StoreOwner,
) -> dict[str, Any]:
    """List active rescue dishes belonging to the authenticated store."""
    dishes = await DishService(db).get_active_store_dishes(store_id)
    return {"store_id": store_id, "dishes": dishes}


@router.patch("/dishes/{dish_id}/quantity")
async def update_dish_quantity(
    dish_id: uuid.UUID,
    payload: DishQuantityUpdate,
    db: DBSession,
    _: StoreOwner,
) -> dict[str, Any]:
    """Atomically set available stock without allowing negative or excess quantity."""
    result = await DishService(db).update_dish_quantity(dish_id, payload.quantity)
    return {
        **result,
        "message": "Cập nhật số lượng thành công",
    }
