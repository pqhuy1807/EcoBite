"""Base Menu Catalog CRUD endpoints (/stores/{store_id}/menu-items and /menu-items/{item_id})."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import DBSession, require_roles
from app.models.user import User, UserRole
from app.services.menu_service import MenuService

router = APIRouter()


@router.post(
    "/stores/{store_id}/menu-items",
    status_code=status.HTTP_201_CREATED,
)
async def create_menu_item(
    store_id: UUID,
    item_in: dict[str, Any],
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.STORE_PARTNER, UserRole.ADMIN)),
    ],
) -> dict[str, Any]:
    """Thêm món vào danh mục gốc của cửa hàng (chỉ chủ quán hoặc Admin)."""
    service = MenuService(db)
    owner_check_id = None if current_user.role == UserRole.ADMIN else current_user.id
    return await service.create_menu_item(
        store_id=store_id,
        item_data=item_in,
        current_user_id=owner_check_id,
    )


@router.get("/stores/{store_id}/menu-items")
async def get_store_menu_items(
    store_id: UUID,
    db: DBSession,
) -> dict[str, Any]:
    """Lấy danh sách tất cả món trong thực đơn chuẩn của quán."""
    service = MenuService(db)
    return await service.get_store_menu_items(store_id)


@router.put("/menu-items/{item_id}")
async def update_menu_item(
    item_id: UUID,
    item_in: dict[str, Any],
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.STORE_PARTNER, UserRole.ADMIN)),
    ],
) -> dict[str, Any]:
    """Cập nhật thông tin món ăn gốc."""
    service = MenuService(db)
    owner_check_id = None if current_user.role == UserRole.ADMIN else current_user.id
    return await service.update_menu_item(
        item_id=item_id,
        update_data=item_in,
        current_user_id=owner_check_id,
    )


@router.delete("/menu-items/{item_id}")
async def delete_menu_item(
    item_id: UUID,
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.STORE_PARTNER, UserRole.ADMIN)),
    ],
) -> dict[str, Any]:
    """Ẩn/Xóa mềm món khỏi thực đơn."""
    service = MenuService(db)
    owner_check_id = None if current_user.role == UserRole.ADMIN else current_user.id
    return await service.delete_menu_item(
        item_id=item_id,
        current_user_id=owner_check_id,
    )
