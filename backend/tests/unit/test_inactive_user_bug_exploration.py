"""Bug Condition Exploration - Inactive User Bypass.

**CRITICAL BUGFIX WORKFLOW RULES:**
- This is a **Bug Condition Exploration Test** - it verifies the bug EXISTS
- This test will **FAIL on unfixed code** - that is the EXPECTED behavior
- When this test FAILS, it proves inactive users can bypass authentication
- DO NOT fix the code when this test fails - document the counterexamples
- After the fix is implemented, this SAME test will PASS to confirm the fix works

**Property 1: Bug Condition - Inactive User Bypass**

Tests that demonstrate:
1. Users with is_active=False can still access protected endpoints (confirms bug)
2. Account deactivation is not enforced (confirms root cause)

**Validates Requirements**: 1.4.1, 1.4.2, 2.4.1, 2.4.2, 2.4.3
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_inactive_user_can_access_protected_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
    active_user: User,
) -> None:
    """Test Case 1: Inactive user with valid token can access protected endpoints.

    **Bug Condition**: User account with is_active=False
    **Current Behavior**: Request succeeds (bug exists)
    **Expected Behavior After Fix**: Returns 403 Forbidden with "Inactive user" message

    This test FAILS on unfixed code, proving the bug exists.
    After fix implementation, this test PASSES, confirming the fix works.
    """
    # Create a valid access token for the user
    token = create_access_token(active_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Verify user can access endpoint while active
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "active@ecobite.vn"

    # Now deactivate the user in the database
    active_user.is_active = False
    db_session.add(active_user)
    await db_session.commit()
    await db_session.refresh(active_user)

    # Verify user is actually inactive in DB
    assert active_user.is_active is False

    # BUG CONDITION: Inactive user attempts to access protected endpoint with valid token
    # ON UNFIXED CODE: This will succeed (status 200) - proving bug exists
    # AFTER FIX: This should return 403 Forbidden with "Inactive user" detail
    response = await client.get("/api/v1/users/me", headers=headers)

    # After fix is implemented, these assertions will pass:
    # - Status code should be 403 (Forbidden, not 401)
    # - Detail should explicitly state "Inactive user"
    assert response.status_code == 403, (
        f"Expected 403 Forbidden for inactive user, got {response.status_code}. "
        f"Response: {response.json()}"
    )
    assert response.json()["detail"] == "Inactive user", (
        f"Expected 'Inactive user' error message, got: {response.json()['detail']}"
    )


@pytest.mark.asyncio
async def test_deactivated_user_continues_api_access(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test Case 2: Admin deactivates user, but user retains API access.

    **Bug Condition**: Account deactivation not enforced
    **Current Behavior**: Deactivated user can continue making API calls
    **Expected Behavior After Fix**: All API calls return 403 Forbidden

    This test FAILS on unfixed code, proving account deactivation is not enforced.
    After fix implementation, this test PASSES, confirming deactivation is enforced.
    """
    # Create a new user account
    user = User(
        email="testuser@ecobite.vn",
        hashed_password="hashed_password_here",
        full_name="Test User",
        role=UserRole.CONSUMER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Generate valid access token
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # User successfully accesses endpoint while active
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "testuser@ecobite.vn"

    # Admin deactivates the user account
    user.is_active = False
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Verify deactivation was persisted
    assert user.is_active is False

    # BUG CONDITION: Deactivated user continues making API calls with valid token
    # ON UNFIXED CODE: This will succeed - proving deactivation is not enforced
    # AFTER FIX: Should return 403 Forbidden
    response = await client.get("/api/v1/users/me", headers=headers)

    # After fix is implemented, deactivation should be enforced
    assert response.status_code == 403, (
        f"Expected 403 Forbidden after deactivation, got {response.status_code}. "
        f"Account deactivation is not being enforced. Response: {response.json()}"
    )
    assert response.json()["detail"] == "Inactive user", (
        f"Expected 'Inactive user' error message, got: {response.json()['detail']}"
    )

    # Test another protected endpoint to confirm enforcement is global
    response = await client.get("/api/v1/stores/me", headers=headers)
    assert response.status_code == 403, (
        "Inactive user enforcement should apply to all protected endpoints"
    )


@pytest.mark.asyncio
async def test_inactive_user_with_different_roles(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test Case 3: Inactive user bypass affects all user roles.

    **Bug Condition**: is_active status not checked for any role
    **Expected Behavior After Fix**: All roles (consumer, store_partner, admin)
                                     are blocked when is_active=False

    This confirms the bug affects the entire authentication system, not just consumers.
    """
    # Test with store partner
    store_partner = User(
        email="inactive_partner@ecobite.vn",
        hashed_password="hashed_password",
        full_name="Inactive Partner",
        role=UserRole.STORE_PARTNER,
        is_active=False,  # Created as inactive
    )
    db_session.add(store_partner)
    await db_session.commit()
    await db_session.refresh(store_partner)

    token = create_access_token(store_partner.id)
    headers = {"Authorization": f"Bearer {token}"}

    # BUG CONDITION: Inactive store partner can access endpoints
    response = await client.get("/api/v1/users/me", headers=headers)

    # After fix: Should be blocked
    assert response.status_code == 403, (
        f"Inactive store partner should be blocked, got {response.status_code}"
    )
    assert response.json()["detail"] == "Inactive user"

    # Test with admin role
    admin = User(
        email="inactive_admin@ecobite.vn",
        hashed_password="hashed_password",
        full_name="Inactive Admin",
        role=UserRole.ADMIN,
        is_active=False,  # Created as inactive
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    admin_token = create_access_token(admin.id)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # BUG CONDITION: Inactive admin can access endpoints
    response = await client.get("/api/v1/users/me", headers=admin_headers)

    # After fix: Should be blocked regardless of role
    assert response.status_code == 403, (
        f"Inactive admin should be blocked, got {response.status_code}"
    )
    assert response.json()["detail"] == "Inactive user"


# Counterexamples documented from test runs:
#
# **Counterexample 1**: User with valid JWT and is_active=False successfully
# accesses /api/v1/users/me endpoint (returns 200 instead of 403)
#
# **Counterexample 2**: After admin sets is_active=False, user continues making
# successful API calls with previously issued token
#
# **Counterexample 3**: Account deactivation affects all roles (consumer,
# store_partner, admin) - the bug is systemic
#
# **Root Cause**: The get_current_user dependency in app/api/deps.py retrieves
# the user but does not check user.is_active status before returning the user object.
#
# **Expected Fix**: Add check after user retrieval:
#   if not user.is_active:
#       raise HTTPException(status_code=403, detail="Inactive user")
