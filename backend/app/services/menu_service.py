from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

class MenuService:
    def __init__(self, db: Session):
        self.db = db

    def get_store_menu_items(self, store_id: UUID) -> List[dict]:
        """
        Lấy danh sách các món ăn trong thực đơn gốc của cửa hàng.
        """
        # return self.db.query(MenuItem).filter(MenuItem.store_id == store_id, MenuItem.is_active == True).all()
        return []

    def create_menu_item(self, store_id: UUID, item_data: dict) -> dict:
        """
        Thêm món ăn mới vào danh mục thực đơn chuẩn của quán.
        """
        if item_data.get("original_price", 0) <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giá gốc của món ăn phải lớn hơn 0"
            )

        new_item = {
            "id": "m1a2b3c4-5d6e-7f8a-9b0c-1d2e3f4a5b6c",
            "store_id": str(store_id),
            "name": item_data.get("name"),
            "category": item_data.get("category"),
            "original_price": item_data.get("original_price"),
            "image_url": item_data.get("image_url"),
            "base_allergens": item_data.get("base_allergens", []),
            "standard_ingredients": item_data.get("standard_ingredients", []),
            "is_active": True
        }
        return new_item

    def update_menu_item(self, item_id: UUID, store_id: UUID, update_data: dict) -> dict:
        """
        Cập nhật thông tin món ăn gốc.
        """
        return {"id": str(item_id), "status": "updated"}

    def delete_menu_item(self, item_id: UUID, store_id: UUID) -> bool:
        """
        Ẩn/Xóa mềm món khỏi thực đơn chuẩn.
        """
        return True