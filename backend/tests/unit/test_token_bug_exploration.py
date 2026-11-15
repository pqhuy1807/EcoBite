"""Bug Condition Exploration Test: Token Type Confusion Attack

This test demonstrates that the current implementation DOES NOT validate the token type claim.
It will FAIL on unfixed code (refresh tokens will authenticate), confirming the bug exists.

After the fix is applied, this test should PASS (refresh tokens will be rejected with 401).

**CRITICAL**: This test encodes the EXPECTED behavior (rejection of non-access tokens).
When run on UNFIXED code, it will FAIL - this failure PROVES the bug exists.
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.models.user import User


class TestTokenTypeConfusionBugExploration:
    """Exploration tests to demonstrate token type confusion vulnerability."""

    @pytest.mark.asyncio
    async def test_refresh_token_used_as_bearer_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        active_user: User,
    ) -> None:
        """Test Case 1: Refresh token can be used as access token on protected endpoint.
        
        Bug Condition: When a refresh token (type="refresh") is used as Bearer token,
        the system SHOULD reject it with 401, but currently ACCEPTS it.
        
        This test encodes the EXPECTED behavior (rejection).
        On unfixed code, it will FAIL because refresh tokens currently work as access tokens.
        After fix, it will PASS when refresh tokens are properly rejected.
        """
        # Create a REFRESH token for the user (type="refresh")
        refresh_token = security.create_refresh_token(subject=str(active_user.id))
        
        # Attempt to use the REFRESH token as a Bearer token on a protected endpoint
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        
        # EXPECTED behavior (after fix): Should return 401 Unauthorized
        # CURRENT behavior (bug): Returns 200 OK
        # This assertion will FAIL on unfixed code, confirming the bug exists
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Expected 401 Unauthorized when using refresh token as access token, "
            f"but got {response.status_code}. This confirms the bug: refresh tokens "
            f"can be used as access tokens, violating security boundaries."
        )
        assert response.json()["detail"] == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_invalid_token_type_accepted(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        active_user: User,
    ) -> None:
        """Test Case 2: Token with invalid type claim is accepted.
        
        Bug Condition: When a JWT with type="invalid" is used,
        the system SHOULD reject it with 401, but currently ACCEPTS it.
        
        This test encodes the EXPECTED behavior (rejection).
        On unfixed code, it will FAIL because invalid token types are accepted.
        After fix, it will PASS when invalid token types are properly rejected.
        """
        from datetime import UTC, datetime, timedelta
        from jose import jwt
        
        from app.core.config import settings
        
        # Manually craft a JWT with an INVALID type claim
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=30)
        payload = {
            "sub": str(active_user.id),
            "iat": now,
            "exp": expire,
            "type": "invalid",  # Invalid token type
        }
        invalid_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Attempt to authenticate with the invalid token
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
        
        # EXPECTED behavior (after fix): Should return 401 Unauthorized
        # CURRENT behavior (bug): Returns 200 OK if signature is valid
        # This assertion will FAIL on unfixed code, confirming the bug exists
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Expected 401 Unauthorized when using token with type='invalid', "
            f"but got {response.status_code}. This confirms the bug: token type "
            f"claim is not validated, allowing arbitrary token types."
        )
        assert response.json()["detail"] == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_token_without_type_claim(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        active_user: User,
    ) -> None:
        """Test Case 3: Token without type claim is accepted.
        
        Bug Condition: When a JWT has no "type" claim at all,
        the system SHOULD reject it with 401, but currently ACCEPTS it.
        
        This test encodes the EXPECTED behavior (rejection).
        On unfixed code, it will FAIL because tokens without type claims are accepted.
        After fix, it will PASS when tokens without type claims are properly rejected.
        """
        from datetime import UTC, datetime, timedelta
        from jose import jwt
        
        from app.core.config import settings
        
        # Manually craft a JWT WITHOUT a type claim
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=30)
        payload = {
            "sub": str(active_user.id),
            "iat": now,
            "exp": expire,
            # No "type" claim
        }
        no_type_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Attempt to authenticate with the token lacking type claim
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {no_type_token}"},
        )
        
        # EXPECTED behavior (after fix): Should return 401 Unauthorized
        # CURRENT behavior (bug): Returns 200 OK if signature is valid
        # This assertion will FAIL on unfixed code, confirming the bug exists
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Expected 401 Unauthorized when using token without type claim, "
            f"but got {response.status_code}. This confirms the bug: tokens "
            f"without type claims are accepted."
        )
        assert response.json()["detail"] == "Could not validate credentials"


# Counterexample Documentation
"""
EXPECTED COUNTEREXAMPLES (on unfixed code):

1. Refresh Token as Bearer Token:
   - Input: Refresh token (type="refresh") used in Authorization header
   - Current Behavior: Returns 200 OK, grants access to protected endpoint
   - Expected Behavior: Returns 401 Unauthorized
   - Counterexample: "Refresh tokens can be used as access tokens, violating security boundaries"

2. Invalid Token Type:
   - Input: JWT with type="invalid"
   - Current Behavior: Returns 200 OK if signature is valid
   - Expected Behavior: Returns 401 Unauthorized
   - Counterexample: "Tokens with arbitrary type claims are accepted"

3. Missing Token Type:
   - Input: JWT without type claim
   - Current Behavior: Returns 200 OK if signature is valid
   - Expected Behavior: Returns 401 Unauthorized
   - Counterexample: "Tokens without type claims are accepted"

These counterexamples demonstrate that the current implementation does not validate
the token type claim, allowing refresh tokens and invalid tokens to authenticate
protected endpoints. This violates the security boundary between access and refresh tokens.
"""
