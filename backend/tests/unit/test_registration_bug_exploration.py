"""Bug Condition Exploration: Privilege Escalation via Registration API

This test suite demonstrates the privilege escalation vulnerability in the registration
endpoint BEFORE the fix is applied. These tests are EXPECTED TO FAIL on unfixed code,
confirming that malicious clients can self-assign admin and store_partner roles.

After the fix is applied, these tests should pass, confirming the vulnerability is closed.
"""

import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"


@pytest.mark.asyncio
async def test_admin_self_assignment_via_registration(client: AsyncClient) -> None:
    """Bug Exploration: Client can create admin account via public registration API.

    CURRENT BEHAVIOR (Bug): Registration accepts role='admin' and creates admin account.
    EXPECTED BEHAVIOR (After Fix): Registration ignores/rejects role field, creates consumer only.

    **Validates: Requirements 1.2.1, 2.2.1, 2.2.2, 2.2.3**

    This test will FAIL on unfixed code (user.role == "admin").
    This test will PASS after fix (user.role == "consumer").
    """
    # Malicious registration request with admin role
    malicious_payload = {
        "email": "attacker@test.com",
        "password": "Pass123!",
        "full_name": "Attacker",
        "role": "admin",  # Attempting privilege escalation
    }

    response = await client.post(REGISTER_URL, json=malicious_payload)

    # UserCreate(extra="forbid") rejects unpermitted role field with 422
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"


@pytest.mark.asyncio
async def test_store_partner_self_assignment_via_registration(client: AsyncClient) -> None:
    """Bug Exploration: Client can create store_partner account via public registration.

    CURRENT BEHAVIOR (Bug): Registration accepts role='store_partner' and creates
    privileged account.
    EXPECTED BEHAVIOR (After Fix): Registration ignores/rejects role field, creates consumer only.

    **Validates: Requirements 1.2.2, 2.2.1, 2.2.2, 2.2.3**

    This test will FAIL on unfixed code (user.role == "store_partner").
    This test will PASS after fix (user.role == "consumer").
    """
    # Malicious registration request with store_partner role
    malicious_payload = {
        "email": "hacker@test.com",
        "password": "Pass456!",
        "full_name": "Hacker",
        "role": "store_partner",  # Attempting privilege escalation
    }

    response = await client.post(REGISTER_URL, json=malicious_payload)

    # UserCreate(extra="forbid") rejects unpermitted role field with 422
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"


@pytest.mark.asyncio
async def test_multiple_privilege_escalation_attempts(client: AsyncClient) -> None:
    """Bug Exploration: Verify bug affects both admin and store_partner roles consistently.

    CURRENT BEHAVIOR (Bug): Multiple malicious registrations succeed with elevated roles.
    EXPECTED BEHAVIOR (After Fix): All registrations result in consumer role only.

    **Validates: Requirements 2.2.1, 2.2.2, 2.2.3**

    This test will FAIL on unfixed code (finding elevated roles).
    This test will PASS after fix (all users have consumer role).
    """
    malicious_attempts = [
        {
            "email": "admin1@evil.com",
            "password": "AdminPass1!",
            "full_name": "Evil Admin 1",
            "role": "admin",
        },
        {
            "email": "admin2@evil.com",
            "password": "AdminPass2!",
            "full_name": "Evil Admin 2",
            "role": "ADMIN",  # Test uppercase variant
        },
        {
            "email": "partner1@evil.com",
            "password": "PartnerPass1!",
            "full_name": "Evil Partner 1",
            "role": "store_partner",
        },
        {
            "email": "partner2@evil.com",
            "password": "PartnerPass2!",
            "full_name": "Evil Partner 2",
            "role": "STORE_PARTNER",  # Test uppercase variant
        },
    ]

    for payload in malicious_attempts:
        response = await client.post(REGISTER_URL, json=payload)
        assert response.status_code == 422, (
            f"Registration should fail with 422 for {payload['email']}"
        )
