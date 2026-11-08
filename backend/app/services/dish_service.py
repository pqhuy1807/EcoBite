"""Business logic for Surplus Dishes and Rule-Based Time-Shift Discount Engine."""

from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import DietaryType, ItemCategory
from app.repositories import dish_repo, menu_repo


def _parse_time_value(raw: time | str | None, default: time) -> time:
    """Parse an ISO time string ('HH:MM:SS' or 'HH:MM') or return a time object."""
    if isinstance(raw, time):
        return raw
    if isinstance(raw, str) and raw.strip():
        parts = [int(p) for p in raw.strip().split(":")]
        if len(parts) == 2:
            return time(parts[0], parts[1], 0)
        if len(parts) >= 3:
            return time(parts[0], parts[1], parts[2])
    return default


class DishService:
    """Service quản lý Suất ăn dư thừa (Dishes) và Động cơ Giảm giá Khung giờ Tất định.

    Tuân thủ nghiêm ngặt Inviolable Guardrail #4 (Anti-Over-Selling),
    Guardrail #5 (Rule-Based Time-Shift Pricing) và Guardrail #6 (Menu Grounding).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def calculate_time_shifted_discount(
        original_price: float,
        pickup_start_time: time,
        pickup_end_time: time,
        override_discounted_price: float | None = None,
        current_time: datetime | None = None,
    ) -> tuple[float, float, bool]:
        """Thuật toán tính giá giảm giờ chót tất định (Rule-Based Time-Shift Engine).

        - Giờ vàng giải cứu (Standard Window): Giảm 50% so với giá gốc.
        - Giờ chót xả hàng (Final Rush - 45 phút trước pickup_end_time): Giảm 70%.
        - Giá ghi đè thủ công (override_discounted_price): Ưu tiên nếu chủ quán chỉ định.
        """
        rule_discount_price = float(round(original_price * 0.3, -2))
        if rule_discount_price <= 0:
            rule_discount_price = round(original_price * 0.3, 2)

        if override_discounted_price is not None and override_discounted_price > 0:
            return float(override_discounted_price), rule_discount_price, False

        rescue_price = float(round(original_price * 0.5, -2))
        if rescue_price <= 0:
            rescue_price = round(original_price * 0.5, 2)

        now_time = current_time.time() if current_time else datetime.now().time()
        ref_date = current_time.date() if current_time else datetime.today().date()
        dt_end = datetime.combine(ref_date, pickup_end_time)
        dt_rush_start = dt_end - timedelta(minutes=45)
        rush_start_time = dt_rush_start.time()

        is_rule_discount_active = False
        if rush_start_time <= now_time <= pickup_end_time:
            is_rule_discount_active = True
            current_active_price = rule_discount_price
        else:
            current_active_price = rescue_price

        return current_active_price, rule_discount_price, is_rule_discount_active

    @staticmethod
    def get_countdown_to_final_rush(
        pickup_end_time: time,
        current_time: datetime | None = None,
        rush_window_minutes: int = 45,
    ) -> int:
        """Tính số giây còn lại trước khi bước vào khung Giờ Chót (-70%).

        Trả về 0 nếu đã bước vào khung giờ chót hoặc đã quá giờ đóng cửa.
        """
        now_dt = current_time if current_time else datetime.now()
        dt_end = datetime.combine(now_dt.date(), pickup_end_time)
        dt_rush_start = dt_end - timedelta(minutes=rush_window_minutes)
        remaining_seconds = int((dt_rush_start - now_dt).total_seconds())
        return max(0, remaining_seconds)

    async def create_surplus_dish(
        self,
        store_id: UUID,
        dish_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Kích hoạt và đăng bán suất ăn dư thừa cuối ca (hỗ trợ Menu Grounding)."""
        total_qty = int(dish_data.get("total_quantity", 1))
        if total_qty <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số lượng suất ăn mở bán phải lớn hơn 0",
            )

        p_start = _parse_time_value(dish_data.get("pickup_start_time"), time(14, 0))
        p_end = _parse_time_value(dish_data.get("pickup_end_time"), time(15, 0))
        if p_end <= p_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Khung giờ kết thúc nhận món phải sau giờ bắt đầu",
            )

        # Menu Grounding: kế thừa từ menu_items nếu có menu_item_id
        menu_item_id_raw = dish_data.get("menu_item_id")
        menu_item_uuid: UUID | None = None
        if menu_item_id_raw:
            menu_item_uuid = (
                menu_item_id_raw
                if isinstance(menu_item_id_raw, UUID)
                else UUID(str(menu_item_id_raw))
            )

        grounded_item = (
            await menu_repo.get_by_id(self.db, menu_item_uuid)
            if menu_item_uuid is not None
            else None
        )

        orig_price = float(
            dish_data.get("original_price")
            or (grounded_item.original_price if grounded_item else 45000.0)
        )
        name = str(
            dish_data.get("name") or (grounded_item.name if grounded_item else "Món giải cứu")
        )
        image_url = dish_data.get("image_url") or (
            grounded_item.image_url if grounded_item else None
        )
        raw_cat = dish_data.get("category") or (
            grounded_item.category.value if grounded_item else "RICE"
        )
        try:
            category = ItemCategory(str(raw_cat).upper())
        except ValueError:
            category = ItemCategory.OTHER

        override_raw = dish_data.get("override_discounted_price")
        override_price = float(override_raw) if override_raw is not None else None

        current_price, rule_price, is_active = self.calculate_time_shifted_discount(
            original_price=orig_price,
            pickup_start_time=p_start,
            pickup_end_time=p_end,
            override_discounted_price=override_price,
        )

        rescue_price_val = float(dish_data.get("rescue_price") or current_price)
        rule_discount_val = float(dish_data.get("rule_discount_price") or rule_price)

        dt_rush = datetime.combine(datetime.today().date(), p_end) - timedelta(minutes=45)
        rule_start = _parse_time_value(dish_data.get("rule_discount_start_time"), dt_rush.time())

        dish = Dish(
            store_id=store_id,
            menu_item_id=menu_item_uuid,
            name=name,
            description=dish_data.get("description"),
            category=category,
            image_url=image_url,
            original_price=Decimal(str(orig_price)),
            rescue_price=Decimal(str(rescue_price_val)),
            rule_discount_price=Decimal(str(rule_discount_val)),
            override_discounted_price=(
                Decimal(str(override_price)) if override_price is not None else None
            ),
            pickup_start_time=p_start,
            pickup_end_time=p_end,
            rule_discount_start_time=rule_start,
            total_quantity=total_qty,
            remaining_quantity=total_qty,
            status=DishStatus.ACTIVE,
            ingredients=list(dish_data.get("ingredients") or []),
            allergens=list(dish_data.get("allergens") or []),
            dietary_notes=list(dish_data.get("dietary_notes") or []),
            dietary_type=DietaryType.NON_VEGAN,
        )
        saved = await dish_repo.create(self.db, dish)

        return {
            "id": str(saved.id),
            "store_id": str(saved.store_id),
            "menu_item_id": str(saved.menu_item_id) if saved.menu_item_id else None,
            "name": saved.name,
            "original_price": float(saved.original_price),
            "current_price": current_price,
            "rule_discount_price": float(saved.rule_discount_price or rule_price),
            "is_rule_discount_active": is_active,
            "total_quantity": saved.total_quantity,
            "remaining_quantity": saved.remaining_quantity,
            "pickup_start_time": saved.pickup_start_time.strftime("%H:%M:%S"),
            "pickup_end_time": saved.pickup_end_time.strftime("%H:%M:%S"),
            "status": "AVAILABLE" if saved.status == DishStatus.ACTIVE else saved.status.value,
            "created_at": saved.created_at.isoformat() if saved.created_at else None,
        }

    async def batch_create_dishes(
        self,
        store_id: UUID,
        batch_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Đăng hàng loạt món dư cuối ca (1-Tap Batch Post)."""
        p_start = _parse_time_value(batch_data.get("pickup_start_time"), time(13, 55))
        p_end = _parse_time_value(batch_data.get("pickup_end_time"), time(15, 0))
        if p_end <= p_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Khung giờ kết thúc nhận món phải sau giờ bắt đầu",
            )

        dishes_to_save: list[Dish] = []
        price_map: list[float] = []
        raw_items: list[dict[str, Any]] = list(batch_data.get("dishes") or [])

        for item in raw_items:
            qty = int(item.get("quantity", 1))
            if qty <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Số lượng từng món trong batch phải lớn hơn 0",
                )

            menu_item_id_raw = item.get("menu_item_id")
            menu_uuid: UUID | None = None
            if menu_item_id_raw:
                menu_uuid = (
                    menu_item_id_raw
                    if isinstance(menu_item_id_raw, UUID)
                    else UUID(str(menu_item_id_raw))
                )

            grounded = (
                await menu_repo.get_by_id(self.db, menu_uuid) if menu_uuid is not None else None
            )
            raw_orig_price = item.get("original_price")
            orig_price = (
                float(raw_orig_price)
                if raw_orig_price is not None
                else (float(grounded.original_price) if grounded else 45000.0)
            )
            override_raw = item.get("override_discounted_price")
            override_price = float(override_raw) if override_raw is not None else None

            curr_price, rule_price, _ = self.calculate_time_shifted_discount(
                original_price=orig_price,
                pickup_start_time=p_start,
                pickup_end_time=p_end,
                override_discounted_price=override_price,
            )
            price_map.append(curr_price)

            dishes_to_save.append(
                Dish(
                    store_id=store_id,
                    menu_item_id=menu_uuid,
                    name=str(item.get("name") or (grounded.name if grounded else "Món giải cứu")),
                    category=grounded.category if grounded else ItemCategory.RICE,
                    image_url=grounded.image_url if grounded else None,
                    original_price=Decimal(str(orig_price)),
                    rescue_price=Decimal(str(curr_price)),
                    rule_discount_price=Decimal(str(rule_price)),
                    override_discounted_price=(
                        Decimal(str(override_price)) if override_price is not None else None
                    ),
                    pickup_start_time=p_start,
                    pickup_end_time=p_end,
                    total_quantity=qty,
                    remaining_quantity=qty,
                    status=DishStatus.ACTIVE,
                    allergens=list(item.get("allergens") or []),
                    dietary_notes=list(item.get("dietary_notes") or []),
                )
            )

        saved_dishes = await dish_repo.create_batch(self.db, dishes_to_save)
        response_items = [
            {
                "id": str(d.id),
                "name": d.name,
                "remaining_quantity": d.remaining_quantity,
                "current_price": price_map[idx],
            }
            for idx, d in enumerate(saved_dishes)
        ]

        return {
            "created_count": len(response_items),
            "dishes": response_items,
        }

    async def get_active_store_dishes(self, store_id: UUID) -> dict[str, Any]:
        """Lấy danh sách các món đang mở bán giải cứu trong ca của cửa hàng."""
        dishes = await dish_repo.list_active_by_store(self.db, store_id)
        serialized = []
        for d in dishes:
            override_val = (
                float(d.override_discounted_price)
                if d.override_discounted_price is not None
                else None
            )
            curr_price, _, is_active = self.calculate_time_shifted_discount(
                original_price=float(d.original_price),
                pickup_start_time=d.pickup_start_time,
                pickup_end_time=d.pickup_end_time,
                override_discounted_price=override_val,
            )
            serialized.append(
                {
                    "id": str(d.id),
                    "name": d.name,
                    "category": d.category.value,
                    "original_price": float(d.original_price),
                    "current_price": curr_price,
                    "rule_discount_price": (
                        float(d.rule_discount_price) if d.rule_discount_price else None
                    ),
                    "is_rule_discount_active": is_active,
                    "remaining_quantity": d.remaining_quantity,
                    "status": "AVAILABLE" if d.status == DishStatus.ACTIVE else d.status.value,
                }
            )
        return {
            "store_id": str(store_id),
            "dishes": serialized,
        }

    async def update_dish_quantity(
        self,
        dish_id: UUID,
        new_quantity: int,
    ) -> dict[str, Any]:
        """Cập nhật nhanh số lượng suất ăn thủ công."""
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số lượng không được nhỏ hơn 0",
            )
        dish = await dish_repo.get_by_id(self.db, dish_id)
        if dish is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy suất ăn",
            )
        updated = await dish_repo.update_quantity(self.db, dish, new_quantity)
        return {
            "dish_id": str(updated.id),
            "updated_quantity": updated.remaining_quantity,
            "status": updated.status.value,
            "message": "Cập nhật số lượng thành công",
        }
