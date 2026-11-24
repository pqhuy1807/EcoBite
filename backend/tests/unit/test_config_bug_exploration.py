"""Bug Condition Exploration: Insecure Production Secret

This test suite demonstrates the insecure production secret vulnerability in the Settings
configuration BEFORE the fix is applied. These tests are EXPECTED TO FAIL on unfixed code,
confirming that production deployments can start with known-insecure default SECRET_KEY.

After the fix is applied, these tests should pass, confirming the vulnerability is closed.
"""

import pytest
from jose import jwt

from app.core.config import Settings


@pytest.mark.asyncio
async def test_production_starts_with_default_secret(monkeypatch) -> None:
    """Bug Exploration: Production deployment accepts default insecure SECRET_KEY.

    CURRENT BEHAVIOR (Bug): Settings instantiation succeeds with APP_ENV=production
                           and SECRET_KEY=CHANGE_ME_INSECURE_DEV_SECRET.
    EXPECTED BEHAVIOR (After Fix): Settings instantiation raises ValueError,
                                   preventing production startup with insecure secret.

    **Validates: Requirements 1.5.1, 2.5.1, 2.5.2, 2.5.3**

    This test will FAIL on unfixed code (no exception raised).
    This test will PASS after fix (ValueError raised with helpful message).
    """
    # Set environment variables to simulate production deployment with default secret
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "CHANGE_ME_INSECURE_DEV_SECRET")

    # BUG CONDITION CHECK: On unfixed code, this succeeds (BUG!)
    # After fix, this should raise ValueError
    try:
        settings = Settings()

        # If we reach here, the bug exists - production started with insecure secret
        pytest.fail(
            f"INSECURE PRODUCTION SECRET BUG DETECTED: "
            f"Production deployment (APP_ENV={settings.APP_ENV}) started successfully "
            f"with default SECRET_KEY containing 'CHANGE_ME'. "
            f"Expected: ValueError preventing startup. "
            f"Vulnerability: Production systems can deploy with known-insecure credentials, "
            f"allowing trivial JWT token forgery by attackers."
        )
    except ValueError as e:
        # This is the expected behavior after fix
        assert "SECRET_KEY must be changed in production" in str(e), (
            f"ValueError raised but with unexpected message: {e}"
        )
        # Test passes - production deployment is correctly rejected


@pytest.mark.asyncio
async def test_token_forgery_with_known_default_secret(monkeypatch) -> None:
    """Bug Exploration: Default SECRET_KEY allows attackers to forge valid JWT tokens.

    CURRENT BEHAVIOR (Bug): Tokens signed with default secret are accepted by the application.
    EXPECTED BEHAVIOR (After Fix): Production cannot start with default secret,
                                   preventing this attack vector entirely.

    **Validates: Requirements 1.5.2, 2.5.1, 2.5.2, 2.5.3**

    This test will FAIL on unfixed code (forged token is valid).
    This test will PASS after fix (Settings raises ValueError before token use).
    """
    # Simulate production environment with default secret
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "CHANGE_ME_INSECURE_DEV_SECRET")

    # BUG CONDITION CHECK: Attempt to instantiate Settings
    try:
        settings = Settings()

        # If Settings instantiation succeeds, demonstrate the attack
        default_secret = "CHANGE_ME_INSECURE_DEV_SECRET"

        # Attacker forges admin token using known default secret
        forged_payload = {
            "sub": "00000000-0000-0000-0000-000000000000",  # Arbitrary user ID
            "type": "access",
            "role": "admin",  # Escalate to admin
        }
        forged_token = jwt.encode(forged_payload, default_secret, algorithm="HS256")

        # Verify the forged token would be accepted
        decoded = jwt.decode(forged_token, settings.SECRET_KEY, algorithms=["HS256"])

        pytest.fail(
            f"INSECURE PRODUCTION SECRET BUG DETECTED: "
            f"Production deployment with default SECRET_KEY allows token forgery. "
            f"Attacker successfully forged admin token: {decoded}. "
            f"Expected: ValueError during Settings initialization. "
            f"Vulnerability: Anyone knowing the default secret can forge valid tokens, "
            f"gaining unauthorized admin access to production systems."
        )
    except ValueError as e:
        # This is the expected behavior after fix
        assert "SECRET_KEY must be changed in production" in str(e), (
            f"ValueError raised but with unexpected message: {e}"
        )
        # Test passes - production deployment is correctly rejected


@pytest.mark.asyncio
async def test_production_with_variants_of_insecure_secret(monkeypatch) -> None:
    """Bug Exploration: Verify bug affects different variations of default secret.

    CURRENT BEHAVIOR (Bug): Production starts with any secret containing "CHANGE_ME".
    EXPECTED BEHAVIOR (After Fix): Production rejects any SECRET_KEY containing "CHANGE_ME".

    **Validates: Requirements 2.5.1, 2.5.2, 2.5.3**

    This test will FAIL on unfixed code (all variants succeed).
    This test will PASS after fix (all variants raise ValueError).
    """
    insecure_variants = [
        "CHANGE_ME_INSECURE_DEV_SECRET",  # Exact default
        "CHANGE_ME",  # Minimal insecure pattern
        "CHANGE_ME_PRODUCTION",  # User attempted to customize but kept marker
        "my_secret_CHANGE_ME_later",  # Partial customization
    ]

    failed_checks = []

    for insecure_secret in insecure_variants:
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("SECRET_KEY", insecure_secret)

        try:
            # Attempt to create Settings with insecure secret
            settings = Settings()

            # If we reach here, the bug exists for this variant
            failed_checks.append(
                {
                    "secret_variant": insecure_secret,
                    "app_env": settings.APP_ENV,
                    "vulnerability": "Production started with insecure secret",
                }
            )
        except ValueError as e:
            # Expected behavior after fix - production deployment rejected
            assert "SECRET_KEY must be changed in production" in str(e)
            # This variant is correctly handled

        # Clear environment for next test
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)

    # This assertion will FAIL on unfixed code (failed_checks is not empty)
    # This assertion will PASS after fix (failed_checks is empty)
    assert len(failed_checks) == 0, (
        f"INSECURE PRODUCTION SECRET BUG DETECTED: "
        f"{len(failed_checks)} secret variant(s) allowed production startup: "
        f"{failed_checks}. "
        f"All secrets containing 'CHANGE_ME' should be rejected in production."
    )


@pytest.mark.asyncio
async def test_development_allows_default_secret(monkeypatch) -> None:
    """Preservation Check: Development environment should accept default SECRET_KEY.

    This test verifies that the fix does NOT break development workflows.

    **Validates: Requirements 3.4.1, 3.4.2**

    This test should PASS both before and after the fix.
    """
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "CHANGE_ME_INSECURE_DEV_SECRET")

    # Development should accept default secret (this is intentional for local dev)
    settings = Settings()

    assert settings.APP_ENV == "development"
    assert settings.SECRET_KEY == "CHANGE_ME_INSECURE_DEV_SECRET"
    # Test passes - development flexibility is preserved


@pytest.mark.asyncio
async def test_staging_allows_default_secret(monkeypatch) -> None:
    """Preservation Check: Staging environment should accept default SECRET_KEY.

    This test verifies that the fix does NOT break staging environments.

    **Validates: Requirements 3.4.1, 3.4.2**

    This test should PASS both before and after the fix.
    """
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("SECRET_KEY", "CHANGE_ME_INSECURE_DEV_SECRET")

    # Staging should accept default secret (this is intentional for testing)
    settings = Settings()

    assert settings.APP_ENV == "staging"
    assert settings.SECRET_KEY == "CHANGE_ME_INSECURE_DEV_SECRET"
    # Test passes - staging flexibility is preserved


@pytest.mark.asyncio
async def test_production_with_custom_secret_succeeds(monkeypatch) -> None:
    """Preservation Check: Production with secure SECRET_KEY should work correctly.

    This test verifies that the fix does NOT break legitimate production deployments.

    **Validates: Requirements 3.4.1, 3.4.2**

    This test should PASS both before and after the fix.
    """
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6")

    # Production should accept custom, secure SECRET_KEY
    settings = Settings()

    assert settings.APP_ENV == "production"
    assert settings.SECRET_KEY == "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
    assert "CHANGE_ME" not in settings.SECRET_KEY
    # Test passes - legitimate production deployments work correctly
