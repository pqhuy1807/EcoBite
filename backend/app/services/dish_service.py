from datetime import datetime, time, timedelta
from typing import Optional, Tuple, List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

class DishService:
    """
    Service quản lý Suất ăn dư thừa (Dishes) và Động cơ Giảm giá Khung giờ Tất định
    (Rule-Based Time-Shift Engine - Inviolable Guardrail #5).
    """
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def calculate_time_shifted_discount(
        original_price: float,
        pickup_start_time: time,
        pickup_end_time: time,
        override_discounted_price: Optional[float] = None,
        current_time: Optional[datetime] = None
    ) -> Tuple[float, float, bool]:
        """
        Thuật toán tính giá giảm giờ chót tất định:
        - Giờ vàng giải cứu (Standard Window): Giảm 40% - 50%.
        - Giờ chót xả hàng (Final Rush - 30 đến 45 phút trước pickup_end_time): Giảm 60% - 70%.
        - Giá ghi đè thủ công (override_discounted_price): Ưu tiên nếu chủ quán chủ động nhập.
        """
        if override_discounted_price is not None and override_discounted_price > 0:
            rescue_price = override_discounted_price
            rule_discount_price = round(original_price * 0.3, -2) # Giảm 70%
            return rescue_price, rule_discount_price, False

        rescue_price = round(original_price * 0.5, -2)
        rule_discount_price = round(original_price * 0.3, -2)

        now = current_time.time() if current_time else datetime.now().time()

        dummy_date = datetime.today()
        dt_end = datetime.combine(dummy_date, pickup_end_time)
        dt_rush_start = dt_end - timedelta(minutes=45)
        rush_start_time = dt_rush_start.time()

        is_rule_discount_active = False
        if rush_start_time <= now <= pickup_end_time:
            is_rule_discount_active = True
            current_active_price = rule_discount_price
        else:
            current_active_price = rescue_price

        return current_active_price, rule_discount_price, is_rule_discount_active

    def create_surplus_dish(self, store_id: UUID, dish_data: dict) -> dict:
        """
        Kích hoạt và đăng bán suất ăn dư thừa cuối ca.
        """
        orig_price = dish_data.get("original_price", 0.0)
        p_start = dish_data.get("pickup_start_time")
        p_end = dish_data.get("pickup_end_time")

        current_price, rule_price, is_active = self.calculate_time_shifted_discount(
            original_price=orig_price,
            pickup_start_time=p_start,
            pickup_end_time=p_end,
            override_discounted_price=dish_data.get("override_discounted_price")
        )

        return {
            "id": "d7a1b3c9-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
            "store_id": str(store_id),
            "menu_item_id": str(dish_data.get("menu_item_id")),
            "name": dish_data.get("name"),
            "original_price": orig_price,
            "current_price": current_price,
            "rule_discount_price": rule_price,
            "is_rule_discount_active": is_active,
            "total_quantity": dish_data.get("total_quantity"),
            "remaining_quantity": dish_data.get("total_quantity"),
            "pickup_start_time": str(p_start),
            "pickup_end_time": str(p_end),
            "status": "AVAILABLE"
        }

    def batch_create_dishes(self, store_id: UUID, batch_data: dict) -> dict:
        """
        Đăng hàng loạt món dư cuối ca (1-Tap Batch Post).
        """
        created_dishes = []
        p_start = batch_data.get("pickup_start_time")
        p_end = batch_data.get("pickup_end_time")

        for item in batch_data.get("dishes", []):
            curr_price, rule_price, _ = self.calculate_time_shifted_discount(
                original_price=45000.0,
                pickup_start_time=p_start,
                pickup_end_time=p_end,
                override_discounted_price=item.get("override_discounted_price")
            )
            created_dishes.append({
                "id": "generated-uuid-dish",
                "name": item.get("name"),
                "remaining_quantity": item.get("quantity"),
                "current_price": curr_price
            })

        return {
            "created_count": len(created_dishes),
            "dishes": created_dishes
        }