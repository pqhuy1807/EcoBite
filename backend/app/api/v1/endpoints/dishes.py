"""Surplus Dishes activation and Rule-Based Time-Shift Pricing endpoints."""

import uuid
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import DBSession, require_roles
from app.models.user import User, UserRole
from app.services.dish_service import DishService

router = APIRouter()


@router.post("/dishes", status_code=status.HTTP_201_CREATED)
async def create_surplus_dish(
    dish_in: dict[str, Any],
    db: DBSession,
    _current_user: Annotated[
        User,
        Depends(require_roles(UserRole.STORE_PARTNER, UserRole.ADMIN)),
    ],
) -> dict[str, Any]:
    """Đăng bán suất ăn dư thừa cuối ca (Tạo lẻ)."""
    raw_store_id = dish_in.get("store_id")
    store_id = UUID(str(raw_store_id)) if raw_store_id else uuid.uuid4()
    service = DishService(db)
    return await service.create_surplus_dish(store_id=store_id, dish_data=dish_in)


@router.post("/dishes/batch", status_code=status.HTTP_201_CREATED)
async def batch_create_surplus_dishes(
    batch_in: dict[str, Any],
    db: DBSession,
    _current_user: Annotated[
        User,
        Depends(require_roles(UserRole.STORE_PARTNER, UserRole.ADMIN)),
    ],
) -> dict[str, Any]:
    """Đăng hàng loạt món dư cuối ca (1-Tap Batch Post)."""
    raw_store_id = batch_in.get("store_id")
    store_id = UUID(str(raw_store_id)) if raw_store_id else uuid.uuid4()
    service = DishService(db)
    return await service.batch_create_dishes(store_id=store_id, batch_data=batch_in)


@router.get("/stores/{store_id}/dishes/active")
async def get_active_store_dishes(
    store_id: UUID,
    db: DBSession,
) -> dict[str, Any]:
    """Lấy danh sách các món đang mở bán giải cứu trong ca của cửa hàng."""
    service = DishService(db)
    return await service.get_active_store_dishes(store_id)


@router.patch(
    "/dishes/{dish_id}/quantity",
    dependencies=[Depends(require_roles(UserRole.STORE_PARTNER, UserRole.ADMIN))],
)
async def update_dish_quantity(
    dish_id: UUID,
    payload: dict[str, Any],
    db: DBSession,
) -> dict[str, Any]:
    """Cập nhật nhanh số lượng suất ăn thủ công."""
    new_qty = int(payload.get("quantity", 0))
    service = DishService(db)
    return await service.update_dish_quantity(dish_id=dish_id, new_quantity=new_qty)
