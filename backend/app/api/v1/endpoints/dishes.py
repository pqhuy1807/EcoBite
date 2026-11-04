from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()

@router.post("/dishes", status_code=status.HTTP_201_CREATED)
def create_surplus_dish(dish_in: dict) -> Any:
    """
    Đăng bán suất ăn dư thừa cuối ca (Tạo lẻ).
    """
    return {
        "id": "d7a1b3c9-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
        "store_id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
        "menu_item_id": dish_in.get("menu_item_id"),
        "name": dish_in.get("name", "Cơm sườn bì chả"),
        "original_price": dish_in.get("original_price", 45000.0),
        "current_price": dish_in.get("rescue_price", 22000.0),
        "rule_discount_price": dish_in.get("rule_discount_price", 13500.0),
        "is_rule_discount_active": False,
        "total_quantity": dish_in.get("total_quantity", 5),
        "remaining_quantity": dish_in.get("total_quantity", 5),
        "pickup_start_time": dish_in.get("pickup_start_time", "14:00:00"),
        "pickup_end_time": dish_in.get("pickup_end_time", "15:00:00"),
        "status": "AVAILABLE"
    }

@router.post("/dishes/batch", status_code=status.HTTP_201_CREATED)
def batch_create_surplus_dishes(batch_in: dict) -> Any:
    """
    Đăng hàng loạt món dư cuối ca (1-Tap Batch Post).
    """
    dishes = batch_in.get("dishes", [])
    created_list = []
    for dish in dishes:
        created_list.append({
            "id": "d7a1b3c9-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
            "name": dish.get("name"),
            "remaining_quantity": dish.get("quantity", 1),
            "current_price": dish.get("override_discounted_price") or 22000.0
        })

    return {
        "created_count": len(created_list),
        "dishes": created_list
    }

@router.get("/stores/{store_id}/dishes/active")
def get_active_store_dishes(store_id: UUID) -> Any:
    """
    Lấy danh sách các món đang mở bán giải cứu trong ca của cửa hàng.
    """
    return {
        "store_id": str(store_id),
        "dishes": [
            {
                "id": "d7a1b3c9-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
                "name": "Cơm sườn bì chả",
                "original_price": 45000.0,
                "current_price": 22000.0,
                "remaining_quantity": 5,
                "status": "AVAILABLE"
            }
        ]
    }

@router.patch("/dishes/{dish_id}/quantity")
def update_dish_quantity(dish_id: UUID, payload: dict) -> Any:
    """
    Cập nhật nhanh số lượng suất ăn thủ công.
    """
    new_qty = payload.get("quantity", 0)
    if new_qty < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số lượng không được nhỏ hơn 0"
        )
    return {
        "dish_id": str(dish_id),
        "updated_quantity": new_qty,
        "message": "Cập nhật số lượng thành công"
    }