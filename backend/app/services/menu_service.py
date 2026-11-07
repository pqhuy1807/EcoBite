"""Business logic for Base Menu Catalog (MenuItem) management."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import DietaryType, ItemCategory, MenuItem
from app.repositories import menu_repo, store_repo


def _serialize_menu_item(item: MenuItem) -> dict[str, Any]:
    """Serialize a MenuItem ORM object into an API dictionary."""
    return {
        "id": str(item.id),
        "store_id": str(item.store_id),
        "name": item.name,
        "description": item.description,
        "category": item.category.value,
        "original_price": float(item.original_price),
        "image_url": item.image_url,
        "standard_ingredients": list(item.standard_ingredients or []),
        "base_allergens": list(item.base_allergens or []),
        "dietary_type": item.dietary_type.value,
        "is_active": item.is_active,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


class MenuService:
    """Service quản lý Danh mục Thực đơn Chuẩn (Base Menu Catalog)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_store_menu_items(self, store_id: UUID) -> dict[str, Any]:
        """Lấy danh sách các món ăn trong thực đơn gốc của cửa hàng."""
        items = await menu_repo.list_by_store(self.db, store_id, active_only=True)
        serialized = [_serialize_menu_item(item) for item in items]
        return {
            "total": len(serialized),
            "items": serialized,
        }

    async def create_menu_item(
        self,
        store_id: UUID,
        item_data: dict[str, Any],
        current_user_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Thêm món ăn mới vào danh mục thực đơn chuẩn của quán."""
        store = await store_repo.get_by_id(self.db, store_id)
        if store is not None and current_user_id is not None and store.owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền chỉnh sửa thực đơn của cửa hàng này",
            )

        raw_price = float(item_data.get("original_price", 0))
        if raw_price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giá gốc của món ăn phải lớn hơn 0",
            )

        raw_category = str(item_data.get("category", "RICE")).upper()
        try:
            category = ItemCategory(raw_category)
        except ValueError:
            category = ItemCategory.OTHER

        raw_dietary = str(item_data.get("dietary_type", "NON_VEGAN")).upper()
        try:
            dietary_type = DietaryType(raw_dietary)
        except ValueError:
            dietary_type = DietaryType.NON_VEGAN

        item = await menu_repo.create(
            self.db,
            store_id=store_id,
            name=str(item_data.get("name", "")).strip() or "Món ăn chuẩn",
            description=item_data.get("description"),
            category=category,
            original_price=Decimal(str(raw_price)),
            image_url=str(item_data.get("image_url") or "https://cdn.ecobite.vn/menu/default.jpg"),
            standard_ingredients=list(item_data.get("standard_ingredients") or []),
            base_allergens=list(item_data.get("base_allergens") or []),
            dietary_type=dietary_type,
        )
        return _serialize_menu_item(item)

    async def update_menu_item(
        self,
        item_id: UUID,
        update_data: dict[str, Any],
        current_user_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Cập nhật thông tin món ăn gốc."""
        menu_item = await menu_repo.get_by_id(self.db, item_id)
        if menu_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy món ăn trong thực đơn",
            )

        if current_user_id is not None:
            store = await store_repo.get_by_id(self.db, menu_item.store_id)
            if store is not None and store.owner_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền chỉnh sửa món ăn của cửa hàng khác",
                )

        cleaned: dict[str, Any] = {}
        if "name" in update_data and update_data["name"] is not None:
            cleaned["name"] = str(update_data["name"]).strip()
        if "description" in update_data:
            cleaned["description"] = update_data["description"]
        if "original_price" in update_data and update_data["original_price"] is not None:
            price = float(update_data["original_price"])
            if price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Giá gốc của món ăn phải lớn hơn 0",
                )
            cleaned["original_price"] = Decimal(str(price))
        if "category" in update_data and update_data["category"] is not None:
            cleaned["category"] = ItemCategory(str(update_data["category"]).upper())
        if "image_url" in update_data and update_data["image_url"] is not None:
            cleaned["image_url"] = str(update_data["image_url"])
        if "standard_ingredients" in update_data:
            cleaned["standard_ingredients"] = list(update_data["standard_ingredients"] or [])
        if "base_allergens" in update_data:
            cleaned["base_allergens"] = list(update_data["base_allergens"] or [])

        updated = await menu_repo.update(self.db, menu_item, cleaned)
        return _serialize_menu_item(updated)

    async def delete_menu_item(
        self,
        item_id: UUID,
        current_user_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Ẩn/Xóa mềm món khỏi thực đơn chuẩn."""
        menu_item = await menu_repo.get_by_id(self.db, item_id)
        if menu_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy món ăn trong thực đơn",
            )

        if current_user_id is not None:
            store = await store_repo.get_by_id(self.db, menu_item.store_id)
            if store is not None and store.owner_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền xóa món ăn của cửa hàng khác",
                )

        await menu_repo.soft_delete(self.db, menu_item)
        return {
            "message": "Xóa món khỏi thực đơn thành công",
            "item_id": str(item_id),
        }
