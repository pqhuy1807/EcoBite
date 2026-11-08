"""Unit tests for DishService (Rule-Based Time-Shift Pricing) and dish_repo."""

import uuid
from datetime import datetime, time
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishStatus
from app.models.menu_item import ItemCategory
from app.models.user import UserRole
from app.repositories import dish_repo, store_repo, user_repo
from app.services.dish_service import DishService


def test_time_shift_standard_window_50_percent_discount() -> None:
    """Trong khung giờ vàng tiêu chuẩn, món ăn giảm 50% và cờ giờ chót bằng False."""
    current_price, rule_price, is_rush = DishService.calculate_time_shifted_discount(
        original_price=50000.0,
        pickup_start_time=time(14, 0),
        pickup_end_time=time(16, 0),
        current_time=datetime(2026, 11, 7, 14, 30),
    )

    assert current_price == 25000.0
    assert rule_price == 15000.0
    assert is_rush is False


def test_time_shift_final_rush_70_percent_discount() -> None:
    """Trong 45 phút cuối trước pickup_end_time, tự động giảm 70% và bật cờ giờ chót."""
    current_price, rule_price, is_rush = DishService.calculate_time_shifted_discount(
        original_price=50000.0,
        pickup_start_time=time(14, 0),
        pickup_end_time=time(16, 0),
        current_time=datetime(2026, 11, 7, 15, 30),
    )

    assert current_price == 15000.0
    assert rule_price == 15000.0
    assert is_rush is True


def test_time_shift_manual_override_takes_precedence() -> None:
    """Khi chủ quán đặt giá xả đồng giá thủ công, ưu tiên mức giá override."""
    current_price, rule_price, is_rush = DishService.calculate_time_shifted_discount(
        original_price=50000.0,
        pickup_start_time=time(14, 0),
        pickup_end_time=time(16, 0),
        override_discounted_price=18000.0,
        current_time=datetime(2026, 11, 7, 15, 40),
    )

    assert current_price == 18000.0
    assert rule_price == 15000.0
    assert is_rush is False


def test_countdown_to_final_rush() -> None:
    """Tính chính xác số giây đếm ngược trước khi bước vào 45 phút giờ chót."""
    remaining = DishService.get_countdown_to_final_rush(
        pickup_end_time=time(16, 0),
        current_time=datetime(2026, 11, 7, 15, 0, 0),
        rush_window_minutes=45,
    )
    assert remaining == 15 * 60

    expired_or_in_rush = DishService.get_countdown_to_final_rush(
        pickup_end_time=time(16, 0),
        current_time=datetime(2026, 11, 7, 15, 30, 0),
        rush_window_minutes=45,
    )
    assert expired_or_in_rush == 0


@pytest.mark.asyncio
async def test_dish_repo_atomic_decrement_prevents_overselling(
    db_session: AsyncSession,
) -> None:
    """Kiểm tra Guardrail #4: Atomic Decrement ngăn chặn bán vượt tồn kho."""
    partner = await user_repo.create(
        db_session,
        email="partner_atomic@ecobite.vn",
        hashed_password="hashed_password",
        full_name="Partner Atomic",
        role=UserRole.STORE_PARTNER,
    )
    store = await store_repo.create(
        db_session,
        owner_id=partner.id,
        name="Quán Cơm Atomic",
        description=None,
        address="123 Nguyễn Văn Cừ, Q.5",
        phone="0909000111",
        avatar_url=None,
        kyc_license_url=None,
        latitude=10.762622,
        longitude=106.682333,
    )

    dish = Dish(
        id=uuid.uuid4(),
        store_id=store.id,
        name="Cơm sườn nướng",
        category=ItemCategory.RICE,
        original_price=Decimal("50000"),
        rescue_price=Decimal("25000"),
        rule_discount_price=Decimal("15000"),
        pickup_start_time=time(14, 0),
        pickup_end_time=time(16, 0),
        total_quantity=2,
        remaining_quantity=2,
        status=DishStatus.ACTIVE,
    )
    await dish_repo.create(db_session, dish)

    # Lần mua 1: Mua 3 suất khi chỉ còn 2 -> Phải bị từ chối (None)
    failed = await dish_repo.atomic_decrement_quantity(db_session, dish.id, 3)
    assert failed is None

    # Lần mua 2: Mua đúng 2 suất còn lại -> Thành công và chuyển sang SOLD_OUT
    succeeded = await dish_repo.atomic_decrement_quantity(db_session, dish.id, 2)
    assert succeeded is not None
    assert succeeded.remaining_quantity == 0
    assert succeeded.status == DishStatus.SOLD_OUT
