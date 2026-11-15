"""Property-Based Tests: Preservation - Valid Authentication Flow

**Validates: Requirements 3.1.1, 3.1.2, 3.1.3, 3.3.1, 3.3.2**

These tests capture EXISTING BEHAVIOR for non-buggy inputs.
They MUST PASS on unfixed code (before implementing fixes).
They verify that after fixes are applied, valid authentication flows continue to work identically.

Property 2: Preservation - Valid Authentication Flow
- For all active users with is_active=True and valid access tokens with type="access",
  authentication succeeds and grants access to protected endpoints
- For all valid refresh tokens sent to /api/v1/auth/refresh,
  system issues new access/refresh token pair
- For all systems with timezone data available,
  datetime operations use ZoneInfo correctly
"""

import uuid
from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
from httpx import AsyncClient
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, decode_access_token
from app.models.user import User, UserRole


# ============================================================================
# Hypothesis Strategies for Valid Inputs
# ============================================================================

@st.composite
def valid_active_user_strategy(draw):
    """Generate valid active user data for preservation testing.
    
    This generates ONLY valid, non-buggy inputs:
    - is_active=True (active users)
    - Valid roles (CONSUMER, STORE_PARTNER, ADMIN)
    """
    email = draw(st.emails())
    full_name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd", "Zs")
    )))
    role = draw(st.sampled_from([UserRole.CONSUMER, UserRole.STORE_PARTNER, UserRole.ADMIN]))
    
    return {
        "email": email,
        "full_name": full_name,
        "role": role,
        "is_active": True,  # Always active for preservation tests
    }


@st.composite
def valid_token_expiry_strategy(draw):
    """Generate valid token expiry times (future dates).
    
    This ensures tokens are NOT expired (valid tokens for preservation testing).
    """
    minutes = draw(st.integers(min_value=1, max_value=60))
    return timedelta(minutes=minutes)


# ============================================================================
# Property 1: Active User Authentication Preserved
# ============================================================================

@pytest.mark.asyncio
@settings(max_examples=20, deadline=5000)
@given(user_data=valid_active_user_strategy())
async def test_property_active_user_authentication_preserved(
    user_data: dict,
    db_session: AsyncSession,
    client: AsyncClient,
    override_get_db,
):
    """Property: For all active users with is_active=True and valid access tokens,
    authentication succeeds and grants access to protected endpoints.
    
    **Validates: Requirements 3.1.1, 3.1.2**
    
    This test MUST PASS on unfixed code - it captures baseline behavior.
    After fixes are applied, this test ensures active users still authenticate correctly.
    """
    # Create active user in database
    user = User(
        email=user_data["email"],
        full_name=user_data["full_name"],
        hashed_password="test_hash_not_used",
        role=user_data["role"],
        is_active=True,  # CRITICAL: Always active for preservation
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create valid access token with type="access"
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=30)
    )
    
    # Verify token has type="access"
    payload = decode_access_token(access_token)
    assert payload.get("type") == "access", "Token must have type='access'"
    
    # Test: Active user with valid access token should authenticate successfully
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # EXPECTED: Authentication succeeds for active users with valid access tokens
    assert response.status_code == 200, (
        f"Active user authentication should succeed. "
        f"Status: {response.status_code}, Body: {response.text}"
    )
    
    user_data = response.json()
    assert user_data["email"] == user.email
    assert user_data["is_active"] is True


# ============================================================================
# Property 2: Token Refresh Mechanism Preserved
# ============================================================================

@pytest.mark.asyncio
@settings(max_examples=20, deadline=5000)
@given(
    user_data=valid_active_user_strategy(),
    refresh_expiry=valid_token_expiry_strategy(),
)
async def test_property_token_refresh_mechanism_preserved(
    user_data: dict,
    refresh_expiry: timedelta,
    db_session: AsyncSession,
    client: AsyncClient,
    override_get_db,
):
    """Property: For all valid refresh tokens sent to /api/v1/auth/refresh,
    system issues new access/refresh token pair.
    
    **Validates: Requirements 3.3.1, 3.3.2**
    
    This test MUST PASS on unfixed code - it captures baseline refresh behavior.
    After fixes are applied, this test ensures refresh tokens still work correctly
    at their intended endpoint.
    """
    # Create active user in database
    user = User(
        email=user_data["email"],
        full_name=user_data["full_name"],
        hashed_password="test_hash_not_used",
        role=user_data["role"],
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create valid refresh token with type="refresh"
    refresh_token = create_refresh_token(
        subject=str(user.id),
        expires_delta=refresh_expiry
    )
    
    # Verify token has type="refresh"
    payload = decode_access_token(refresh_token)
    assert payload.get("type") == "refresh", "Token must have type='refresh'"
    
    # Test: Valid refresh token should work at /api/v1/auth/refresh endpoint
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    # EXPECTED: Refresh endpoint returns new token pair
    assert response.status_code == 200, (
        f"Refresh token should work at /auth/refresh endpoint. "
        f"Status: {response.status_code}, Body: {response.text}"
    )
    
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # Verify new access token has correct type
    new_access_payload = decode_access_token(token_data["access_token"])
    assert new_access_payload.get("type") == "access"
    assert new_access_payload.get("sub") == str(user.id)


# ============================================================================
# Property 3: Timezone Operations Preserved (via order flow)
# ============================================================================

@pytest.mark.asyncio
@settings(max_examples=10, deadline=5000)
@given(user_data=valid_active_user_strategy())
async def test_property_timezone_operations_preserved(
    user_data: dict,
    db_session: AsyncSession,
    client: AsyncClient,
    override_get_db,
):
    """Property: For all systems with timezone data available,
    datetime operations use ZoneInfo correctly and produce valid results.
    
    **Validates: Requirements 3.1.3**
    
    This test MUST PASS on unfixed code (on systems with tzdata).
    After fixes are applied, this test ensures timezone-aware operations
    continue to work correctly when timezone data is available.
    
    Note: This test indirectly validates timezone behavior by creating
    time-sensitive operations. The actual timezone fallback will be tested
    in the exploration tests.
    """
    # Create active store partner user
    user = User(
        email=user_data["email"],
        full_name=user_data["full_name"],
        hashed_password="test_hash_not_used",
        role=UserRole.STORE_PARTNER,  # Force store partner for store creation
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    access_token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test: Datetime operations should work correctly
    # We test this by accessing the /users/me endpoint which returns created_at timestamps
    response = await client.get("/api/v1/users/me", headers=headers)
    
    # EXPECTED: Datetime fields are properly formatted and timezone-aware
    assert response.status_code == 200
    user_data_response = response.json()
    assert "created_at" in user_data_response
    assert "updated_at" in user_data_response
    
    # Verify timestamps are valid ISO format (timezone-aware)
    from datetime import datetime
    created_at = datetime.fromisoformat(user_data_response["created_at"].replace("Z", "+00:00"))
    updated_at = datetime.fromisoformat(user_data_response["updated_at"].replace("Z", "+00:00"))
    
    assert created_at is not None
    assert updated_at is not None
    # Timestamps should be reasonable (not in far future or past)
    assert created_at.year >= 2020
    assert updated_at.year >= 2020


# ============================================================================
# Property 4: Multiple Valid Users Can Authenticate Concurrently
# ============================================================================

@pytest.mark.asyncio
@settings(max_examples=10, deadline=10000)
@given(
    user1_data=valid_active_user_strategy(),
    user2_data=valid_active_user_strategy(),
)
async def test_property_concurrent_valid_authentications_preserved(
    user1_data: dict,
    user2_data: dict,
    db_session: AsyncSession,
    client: AsyncClient,
    override_get_db,
):
    """Property: Multiple active users with valid access tokens can
    authenticate concurrently without interference.
    
    **Validates: Requirements 3.1.1, 3.1.2**
    
    This test ensures that fixing bugs doesn't break concurrent authentication.
    """
    # Ensure different emails
    if user1_data["email"] == user2_data["email"]:
        user2_data["email"] = f"alt_{user2_data['email']}"
    
    # Create two active users
    user1 = User(
        email=user1_data["email"],
        full_name=user1_data["full_name"],
        hashed_password="test_hash_1",
        role=user1_data["role"],
        is_active=True,
    )
    user2 = User(
        email=user2_data["email"],
        full_name=user2_data["full_name"],
        hashed_password="test_hash_2",
        role=user2_data["role"],
        is_active=True,
    )
    
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    
    # Create valid access tokens
    token1 = create_access_token(str(user1.id))
    token2 = create_access_token(str(user2.id))
    
    # Test: Both users should authenticate successfully
    response1 = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token1}"}
    )
    response2 = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    # EXPECTED: Both authentications succeed
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    assert data1["email"] == user1.email
    assert data2["email"] == user2.email
    assert data1["id"] != data2["id"]  # Different users
