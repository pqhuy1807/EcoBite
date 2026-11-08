"""Business logic for surplus meal listings and deterministic discounts."""

import uuid
from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import MenuItem
from app.models.store import KycStatus, Store


class DishService:
    """Manage rescue listings and time-based pricing.

    Complies strictly with:
    - Guardrail #4: Anti-Over-Selling inventory protection.
    - Guardrail #5: Rule-Based Time-Shift deterministic discount engine.
    - Guardrail #6: Menu Grounding from canonical menu items.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def calculate_time_shifted_discount(
        original_price: Decimal | float,
        pickup_start_time: time,
        pickup_end_time: time,
        override_discounted_price: Decimal | float | None = None,
        current_time: datetime | time | None = None,
        rule_discount_start_time: time | None = None,
    ) -> tuple[Decimal, Decimal, bool]:
        """Return active price, 70%-discount price and whether the rush price applies."""
        price = Decimal(str(original_price))
        rush_price = (price * Decimal("0.30")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if override_discounted_price is not None:
            override = Decimal(str(override_discounted_price))
            if override <= 0 or override > price:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        "Override price must be greater than zero and no higher than original price"
                    ),
                )
            return override, rush_price, False

        rescue_price = (price * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        now = current_time.time() if isinstance(current_time, datetime) else current_time
        if now is None:
            now = datetime.now().time()
        default_rush_start = max(
            pickup_start_time,
            (datetime.combine(datetime.today(), pickup_end_time) - timedelta(minutes=45)).time(),
        )
        rush_start = rule_discount_start_time or default_rush_start
        rush_active = rush_start <= now <= pickup_end_time
        return (rush_price if rush_active else rescue_price), rush_price, rush_active

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
        menu_item_id: uuid.UUID | None = None,
        dish_data: dict[str, Any] | None = None,
        store_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Kích hoạt và đăng bán suất ăn dư thừa cuối ca (hỗ trợ Menu Grounding)."""
        data = dict(dish_data or {})
        target_menu_id = menu_item_id or data.get("menu_item_id")
        if target_menu_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="menu_item_id is required",
            )
        resolved_menu_id = (
            target_menu_id
            if isinstance(target_menu_id, uuid.UUID)
            else uuid.UUID(str(target_menu_id))
        )

        menu_item = await self.db.get(MenuItem, resolved_menu_id)
        if menu_item is None or not menu_item.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active menu item not found",
            )
        store = await self.db.get(Store, menu_item.store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        self._ensure_store_approved(store)

        p_start = data.get("pickup_start_time") or time(14, 0)
        p_end = data.get("pickup_end_time") or time(15, 0)
        dish = self._build_dish(
            menu_item,
            data,
            p_start,
            p_end,
            data.get("rule_discount_start_time"),
        )
        self.db.add(dish)
        await self.db.commit()
        await self.db.refresh(dish)
        return self.serialize_dish(dish)

    async def batch_create_dishes(
        self,
        dish_items: list[dict[str, Any]],
        pickup_start_time: time,
        pickup_end_time: time,
        rule_discount_start_time: time | None = None,
    ) -> list[dict[str, Any]]:
        """Create a batch in one transaction, requiring all items to belong to one store."""
        menu_items: list[MenuItem] = []
        for item in dish_items:
            raw_id = item.get("menu_item_id")
            item_uuid = raw_id if isinstance(raw_id, uuid.UUID) else uuid.UUID(str(raw_id))
            menu_item = await self.db.get(MenuItem, item_uuid)
            if menu_item is None or not menu_item.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Active menu item not found",
                )
            menu_items.append(menu_item)

        store_id = menu_items[0].store_id
        if any(item.store_id != store_id for item in menu_items):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="All menu items in a batch must belong to the same store",
            )
        store = await self.db.get(Store, store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        self._ensure_store_approved(store)

        dishes = [
            self._build_dish(
                menu_item,
                {**item_data, "total_quantity": item_data.get("quantity", 1)},
                pickup_start_time,
                pickup_end_time,
                rule_discount_start_time,
            )
            for menu_item, item_data in zip(menu_items, dish_items, strict=False)
        ]
        self.db.add_all(dishes)
        await self.db.commit()
        for dish in dishes:
            await self.db.refresh(dish)
        return [self.serialize_dish(dish) for dish in dishes]

    @staticmethod
    def _ensure_store_approved(store: Store) -> None:
        if store.kyc_status != KycStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Store KYC must be approved before publishing dishes",
            )

    @classmethod
    def _build_dish(
        cls,
        menu_item: MenuItem,
        dish_data: dict[str, Any],
        pickup_start: time,
        pickup_end: time,
        rule_start: time | None,
    ) -> Dish:
        if pickup_end <= pickup_start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Pickup end time must be after pickup start time",
            )
        original_price = Decimal(str(dish_data.get("original_price") or menu_item.original_price))
        override_raw = dish_data.get("override_discounted_price")
        override_price = Decimal(str(override_raw)) if override_raw is not None else None
        rescue_price, rule_price, _ = cls.calculate_time_shifted_discount(
            original_price=original_price,
            pickup_start_time=pickup_start,
            pickup_end_time=pickup_end,
            override_discounted_price=override_price,
            rule_discount_start_time=rule_start,
        )
        if override_price is not None:
            rescue_price = override_price

        explicit_allergens = [
            a.model_dump() if hasattr(a, "model_dump") else a
            for a in dish_data.get("allergens", [])
        ]
        total_quantity = int(dish_data.get("total_quantity") or dish_data.get("quantity", 1))
        remaining_quantity = dish_data.get("remaining_quantity")
        if remaining_quantity is None:
            remaining_quantity = total_quantity
        dish_status = DishStatus.SOLD_OUT if remaining_quantity == 0 else DishStatus.ACTIVE
        return Dish(
            store_id=menu_item.store_id,
            menu_item_id=menu_item.id,
            name=menu_item.name,
            description=menu_item.description,
            category=menu_item.category,
            image_url=menu_item.image_url,
            original_price=original_price,
            rescue_price=rescue_price,
            rule_discount_price=rule_price,
            override_discounted_price=override_price,
            pickup_start_time=pickup_start,
            pickup_end_time=pickup_end,
            rule_discount_start_time=rule_start,
            total_quantity=total_quantity,
            remaining_quantity=remaining_quantity,
            status=dish_status,
            ingredients=list(menu_item.standard_ingredients or []),
            allergens=explicit_allergens,
            dietary_notes=list(dish_data.get("dietary_notes") or []),
            dietary_type=menu_item.dietary_type,
        )

    async def get_active_store_dishes(self, store_id: uuid.UUID) -> list[dict[str, Any]]:
        store = await self.db.get(Store, store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        result = await self.db.execute(
            select(Dish)
            .where(Dish.store_id == store_id, Dish.status == DishStatus.ACTIVE)
            .order_by(Dish.created_at, Dish.id)
        )
        return [self.serialize_dish(dish) for dish in result.scalars().all()]

    async def update_dish_quantity(self, dish_id: uuid.UUID, quantity: int) -> dict[str, Any]:
        dish = await self.db.get(Dish, dish_id)
        if dish is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
        if quantity > dish.total_quantity:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Quantity cannot exceed the originally published amount",
            )
        new_status = DishStatus.SOLD_OUT if quantity == 0 else DishStatus.ACTIVE
        result = await self.db.execute(
            update(Dish)
            .where(Dish.id == dish_id, Dish.total_quantity >= quantity)
            .values(remaining_quantity=quantity, status=new_status)
        )
        if getattr(result, "rowcount", 0) != 1:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dish quantity changed concurrently; reload and retry",
            )
        await self.db.commit()
        await self.db.refresh(dish)
        return {
            "dish_id": dish.id,
            "remaining_quantity": dish.remaining_quantity,
            "status": dish.status,
        }

    @classmethod
    def serialize_dish(cls, dish: Dish) -> dict[str, Any]:
        """Serialize a listing with the price currently active under the rush rule."""
        current_price, _, rush_active = cls.calculate_time_shifted_discount(
            original_price=dish.original_price,
            pickup_start_time=dish.pickup_start_time,
            pickup_end_time=dish.pickup_end_time,
            override_discounted_price=dish.override_discounted_price,
            rule_discount_start_time=dish.rule_discount_start_time,
        )
        return {
            "id": dish.id,
            "store_id": dish.store_id,
            "menu_item_id": dish.menu_item_id,
            "name": dish.name,
            "description": dish.description,
            "category": dish.category,
            "original_price": dish.original_price,
            "rescue_price": dish.rescue_price,
            "rule_discount_price": dish.rule_discount_price,
            "override_discounted_price": dish.override_discounted_price,
            "current_price": current_price,
            "is_rule_discount_active": rush_active,
            "pickup_start_time": dish.pickup_start_time,
            "pickup_end_time": dish.pickup_end_time,
            "rule_discount_start_time": dish.rule_discount_start_time,
            "image_url": dish.image_url,
            "ingredients": dish.ingredients,
            "allergens": dish.allergens,
            "dietary_notes": dish.dietary_notes,
            "dietary_type": dish.dietary_type,
            "estimated_co2_kg_per_dish": dish.estimated_co2_kg_per_dish,
            "total_quantity": dish.total_quantity,
            "remaining_quantity": dish.remaining_quantity,
            "status": dish.status,
            "created_at": dish.created_at,
            "updated_at": dish.updated_at,
        }
