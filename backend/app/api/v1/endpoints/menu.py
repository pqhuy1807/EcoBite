from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()

@router.post("/stores/{store_id}/menu-items", status_code=status.HTTP_201_CREATED)
def create_menu_item(store_id: UUID, item_in: dict) -> Any:
    """
    Thêm món vào danh mục gốc của cửa hàng.
    """
    return {
        "id": "m1a2b3c4-5d6e-7f8a-9b0c-1d2e3f4a5b6c",
        "store_id": str(store_id),
        "name": item_in.get("name", "Cơm sườn bì chả"),
        "category": item_in.get("category", "RICE"),
        "original_price": item_in.get("original_price", 45000.0),
        "image_url": item_in.get("image_url"),
        "base_allergens": item_in.get("base_allergens", []),
        "is_active": True
    }

@router.get("/stores/{store_id}/menu-items")
def get_store_menu_items(store_id: UUID) -> Any:
    """
    Lấy danh sách tất cả món trong thực đơn chuẩn của quán.
    """
    return {
        "total": 1,
        "items": [
            {
                "id": "m1a2b3c4-5d6e-7f8a-9b0c-1d2e3f4a5b6c",
                "name": "Cơm sườn bì chả",
                "description": "Cơm tấm truyền thống sườn nướng mật ong",
                "category": "RICE",
                "original_price": 45000.0,
                "base_allergens": ["Eggs (Trứng)", "Fish (Cá/Nước mắm)"],
                "is_active": True
            }
        ]
    }

@router.put("/menu-items/{item_id}")
def update_menu_item(item_id: UUID, item_in: dict) -> Any:
    """
    Cập nhật thông tin món ăn gốc.
    """
    return {"message": "Cập nhật thông tin món ăn thành công", "item_id": str(item_id)}

@router.delete("/menu-items/{item_id}")
def delete_menu_item(item_id: UUID) -> Any:
    """
    Ẩn/Xóa mềm món khỏi thực đơn.
    """
    return {"message": "Xóa món khỏi thực đơn thành công", "item_id": str(item_id)}