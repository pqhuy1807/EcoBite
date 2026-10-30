"""Unit tests for Cluster 2: MenuItem (Menu Grounding) and Dish (Rescue Meals)."""

import uuid
from datetime import time
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models.dish import Dish, DishStatus
from app.models.menu_item import DietaryType, ItemCategory, MenuItem
from app.models.store import Store
from app.models.user import User, UserRole
from app.schemas.dish import AllergenWarning, DishCreate, DishResponse
from app.schemas.menu_item import MenuItemCreate, MenuItemResponse

# ==============================================================================
# 1. Pydantic Validation Tests (Cluster 2)
# ==============================================================================


def test_menu_item_create_validation() -> None:
    """Test valid MenuItemCreate schema."""
    item_in = MenuItemCreate(
        store_id=uuid.uuid4(),
        name="Cơm Sườn Nướng Chả Trứng",
        original_price=Decimal("45000.00"),
        image_url="https://ecobite.vn/static/dishes/com_suon.jpg",
        category=ItemCategory.RICE,
        standard_ingredients=["Gạo tấm", "Sườn heo", "Trứng"],
        base_allergens=["Trứng"],
        dietary_type=DietaryType.NON_VEGAN,
    )
    assert item_in.name == "Cơm Sườn Nướng Chả Trứng"
    assert item_in.original_price == Decimal("45000.00")
    assert "Trứng" in item_in.base_allergens


def test_dish_two_tier_allergen_schema() -> None:
    """Test AllergenWarning schema with EXPLICIT and INFERRED sources (Guardrail #6)."""
    explicit_warning = AllergenWarning(
        allergen="Đậu phộng",
        risk_level="HIGH",
        source="EXPLICIT",
        reason="Chủ quán khai báo trực tiếp có rắc đậu phộng",
    )
    assert explicit_warning.source == "EXPLICIT"

    inferred_warning = AllergenWarning(
        allergen="Gluten",
        risk_level="MEDIUM",
        source="INFERRED",
        reason="AI nhận diện nước tương truyền thống có chứa lúa mì",
    )
    assert inferred_warning.source == "INFERRED"


def test_dish_create_negative_price_fails() -> None:
    """Test that zero or negative prices raise ValidationError."""
    with pytest.raises(ValidationError):
        DishCreate(
            store_id=uuid.uuid4(),
            name="Cơm tấm lỗi giá",
            original_price=Decimal("-1000.00"),  # Negative price
            rescue_price=Decimal("20000.00"),
            pickup_start_time=time(14, 0),
            pickup_end_time=time(15, 0),
            total_quantity=5,
        )


# ==============================================================================
# 2. Database ORM & Anti-Over-Selling Tests (SQLite in-memory)
# ==============================================================================


@pytest.fixture
async def sample_store(db_session) -> Store:
    """Create a verified merchant and store fixture."""
    owner = User(
        email="merchant_c2@ecobite.vn",
        hashed_password="hashed_merchant_pw",
        full_name="Chủ Tiệm Bánh Mì",
        role=UserRole.STORE_PARTNER,
    )
    store = Store(
        owner=owner,
        name="Bánh Mì Sài Gòn 1985",
        address="100 Cach Mang Thang 8, Q3, TP.HCM",
        location="POINT(106.68 10.77)",
    )
    db_session.add_all([owner, store])
    await db_session.commit()
    await db_session.refresh(store)
    return store


@pytest.mark.asyncio
async def test_menu_item_orm_persistence(db_session, sample_store: Store) -> None:
    """Test persisting MenuItem and relationship with Store."""
    menu_item = MenuItem(
        store=sample_store,
        name="Bánh Mì Thịt Nướng Đặc Biệt",
        description="Bánh mì giòn kèm thịt nướng than hoa",
        category=ItemCategory.BAKERY,
        original_price=Decimal("35000.00"),
        image_url="https://ecobite.vn/static/menu/banh_mi.jpg",
        standard_ingredients=["Bột mì", "Thịt heo", "Dưa leo", "Đồ chua"],
        base_allergens=["Gluten"],
    )
    db_session.add(menu_item)
    await db_session.commit()
    await db_session.refresh(menu_item)

    assert isinstance(menu_item.id, uuid.UUID)
    assert menu_item.store.id == sample_store.id
    assert menu_item.is_active is True
    assert "Gluten" in menu_item.base_allergens

    # Test Pydantic Response Serialization
    dto = MenuItemResponse.model_validate(menu_item)
    assert dto.id == menu_item.id
    assert dto.original_price == Decimal("35000.00")


@pytest.mark.asyncio
async def test_dish_menu_grounding_inheritance(db_session, sample_store: Store) -> None:
    """Test Dish inheriting image & original price from MenuItem (Menu Grounding)."""
    menu_item = MenuItem(
        store=sample_store,
        name="Bánh Mì Xíu Mại",
        original_price=Decimal("30000.00"),
        image_url="https://ecobite.vn/static/menu/xiu_mai.jpg",
        category=ItemCategory.BAKERY,
    )
    db_session.add(menu_item)
    await db_session.commit()
    await db_session.refresh(menu_item)

    # Dish posted in afternoon shift inheriting from menu_item
    dish = Dish(
        store=sample_store,
        menu_item=menu_item,
        name=menu_item.name,
        category=menu_item.category,
        original_price=menu_item.original_price,
        rescue_price=Decimal("15000.00"),  # 50% discount
        rule_discount_price=Decimal("9000.00"),  # 70% last-minute deal
        image_url=menu_item.image_url,
        pickup_start_time=time(15, 0),
        pickup_end_time=time(16, 30),
        rule_discount_start_time=time(16, 0),
        total_quantity=10,
        remaining_quantity=10,
        ingredients=["Bánh mì", "Xíu mại", "Sốt cà chua"],
        allergens=[
            {"allergen": "Gluten", "risk_level": "HIGH", "source": "INFERRED", "reason": "Bột mì"}
        ],
        dietary_notes=["Có ngò rí", "Ít cay"],
    )
    db_session.add(dish)
    await db_session.commit()
    await db_session.refresh(dish)

    assert dish.menu_item is not None
    assert dish.menu_item.id == menu_item.id
    assert dish.original_price == Decimal("30000.00")
    assert dish.rescue_price == Decimal("15000.00")
    assert dish.status == DishStatus.ACTIVE

    # DTO Response Validation
    dto = DishResponse.model_validate(dish)
    assert dto.menu_item_id == menu_item.id
    assert dto.allergens[0].source == "INFERRED"


@pytest.mark.asyncio
async def test_dish_anti_over_selling_check_constraint(db_session, sample_store: Store) -> None:
    """Test Guardrail #4: remaining_quantity cannot be negative (Database CheckConstraint)."""
    dish = Dish(
        store=sample_store,
        name="Món Ăn Hết Hàng",
        category=ItemCategory.RICE,
        original_price=Decimal("40000.00"),
        rescue_price=Decimal("20000.00"),
        pickup_start_time=time(17, 0),
        pickup_end_time=time(18, 0),
        total_quantity=5,
        remaining_quantity=-1,  # ILLEGAL: Violates ck_dishes_remaining_qty_non_negative
    )
    db_session.add(dish)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
