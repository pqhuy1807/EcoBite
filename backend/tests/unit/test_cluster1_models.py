"""Unit tests for Cluster 1: User, UserPreference, and Store models & schemas."""

import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models.store import KycStatus, Store
from app.models.user import DietaryPreference, User, UserPreference, UserRole
from app.schemas.store import StoreCreate, StoreResponse
from app.schemas.user import UserCreate, UserResponse
from app.schemas.user_preference import UserPreferenceCreate, UserPreferenceResponse

# ==============================================================================
# 1. Pydantic Schemas Validation Tests
# ==============================================================================


def test_user_schema_role_normalization() -> None:
    """Test that role accepts both uppercase and lowercase strings."""
    user_upper = UserCreate(
        email="test@ecobite.vn",
        password="ValidPassword123!",
        full_name="Nguyen Van A",
        role="CONSUMER",  # type: ignore[arg-type]
    )
    assert user_upper.role == UserRole.CONSUMER

    user_lower = UserCreate(
        email="test2@ecobite.vn",
        password="ValidPassword123!",
        full_name="Nguyen Van B",
        role="consumer",  # type: ignore[arg-type]
    )
    assert user_lower.role == UserRole.CONSUMER


def test_user_schema_invalid_email_and_password() -> None:
    """Test invalid email format and password min length."""
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            password="ValidPassword123!",
            full_name="Nguyen Van A",
        )

    with pytest.raises(ValidationError):
        UserCreate(
            email="valid@ecobite.vn",
            password="123",  # Too short (< 8 chars)
            full_name="Nguyen Van A",
        )


def test_user_preference_schema_defaults() -> None:
    """Test default values for preferences (empty lists and NONE dietary)."""
    pref = UserPreferenceCreate()
    assert pref.preferred_categories == []
    assert pref.excluded_allergens == []
    assert pref.dietary_preference == DietaryPreference.NONE
    assert pref.max_budget is None


def test_store_schema_gps_coordinates_validation() -> None:
    """Test that latitude must be in [-90, 90] and longitude in [-180, 180]."""
    valid_store = StoreCreate(
        name="Quan Com 123",
        address="123 Nguyen Trai, Q1, TP.HCM",
        latitude=10.762622,
        longitude=106.682333,
    )
    assert valid_store.latitude == 10.762622
    assert valid_store.longitude == 106.682333

    # Latitude out of bounds (> 90)
    with pytest.raises(ValidationError):
        StoreCreate(
            name="Quan Com Out of Bounds",
            address="123 Nguyen Trai, Q1",
            latitude=95.0,
            longitude=106.682333,
        )


# ==============================================================================
# 2. Database ORM Persistence & Relationships Tests (SQLite in-memory)
# ==============================================================================


@pytest.mark.asyncio
async def test_create_user_orm(db_session) -> None:
    """Test creating and persisting a User model with UUID primary key."""
    user = User(
        email="user_test@ecobite.vn",
        hashed_password="hashed_pw_secret",
        full_name="Le Van C",
        phone="0912345678",
        role=UserRole.CONSUMER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.email == "user_test@ecobite.vn"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.green_points_balance == 0
    assert user.created_at is not None

    # Serialization to Pydantic response
    response_dto = UserResponse.model_validate(user)
    assert response_dto.id == user.id
    assert response_dto.email == user.email


@pytest.mark.asyncio
async def test_user_email_unique_constraint(db_session) -> None:
    """Test that registering duplicate email raises IntegrityError."""
    user1 = User(
        email="duplicate@ecobite.vn",
        hashed_password="pw1",
        full_name="User One",
    )
    db_session.add(user1)
    await db_session.commit()

    user2 = User(
        email="duplicate@ecobite.vn",
        hashed_password="pw2",
        full_name="User Two",
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_user_preference_one_to_one_relationship(db_session) -> None:
    """Test 1-to-1 relationship between User and UserPreference with cascade delete."""
    user = User(
        email="foodie@ecobite.vn",
        hashed_password="secure_pw",
        full_name="Food Lover",
    )
    pref = UserPreference(
        user=user,
        preferred_categories=["RICE", "NOODLES"],
        dietary_preference=DietaryPreference.VEGAN,
        excluded_allergens=["Đậu phộng", "Hải sản"],
        max_budget=Decimal("50000.00"),
    )
    db_session.add_all([user, pref])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(pref)

    assert user.preference is not None
    assert user.preference.dietary_preference == DietaryPreference.VEGAN
    assert "Đậu phộng" in user.preference.excluded_allergens
    assert pref.user.id == user.id

    # Verify Pydantic response serialization
    pref_dto = UserPreferenceResponse.model_validate(pref)
    assert pref_dto.user_id == user.id
    assert pref_dto.max_budget == Decimal("50000.00")

    # Test cascade delete: deleting user removes preference
    await db_session.delete(user)
    await db_session.commit()

    deleted_pref = await db_session.get(UserPreference, pref.id)
    assert deleted_pref is None


@pytest.mark.asyncio
async def test_store_orm_creation_and_cascade(db_session) -> None:
    """Test Store creation, KYC defaults, owner relationship and cascade delete."""
    owner = User(
        email="merchant@ecobite.vn",
        hashed_password="merchant_secret",
        full_name="Chủ Quán Cơm",
        role=UserRole.STORE_PARTNER,
    )
    store = Store(
        owner=owner,
        name="Cơm Tấm Đêm Sài Gòn",
        address="456 Tran Hung Dao, Q5, TP.HCM",
        phone="02838383838",
        avatar_url="https://ecobite.vn/static/stores/com_tam.jpg",
        kyc_license_url="https://ecobite.vn/static/kyc/license_01.jpg",
        location="POINT(106.682333 10.762622)",
    )
    db_session.add_all([owner, store])
    await db_session.commit()
    await db_session.refresh(store)
    await db_session.refresh(owner)

    assert isinstance(store.id, uuid.UUID)
    assert store.kyc_status == KycStatus.PENDING
    assert store.rating_avg == Decimal("5.0")
    assert store.rating_count == 0
    assert store.total_co2_saved_kg == Decimal("0.0")
    assert store.owner.id == owner.id
    assert len(owner.stores) == 1
    assert owner.stores[0].id == store.id

    # Verify Pydantic StoreResponse serialization
    store_dto = StoreResponse.model_validate(store)
    assert store_dto.id == store.id
    assert store_dto.name == "Cơm Tấm Đêm Sài Gòn"
    assert store_dto.kyc_status == KycStatus.PENDING

    # Test cascade delete: removing owner deletes their stores
    await db_session.delete(owner)
    await db_session.commit()

    deleted_store = await db_session.get(Store, store.id)
    assert deleted_store is None
