"""Integration tests for /api/v1/auth endpoints (register + login + refresh)."""

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"

USER_PAYLOAD: dict[str, str] = {
    "email": "consumer@ecobite.vn",
    "password": "S3curePass!2024",
    "full_name": "Nguyen Van A",
}

FORM_CREDENTIALS: dict[str, str] = {
    "username": USER_PAYLOAD["email"],
    "password": USER_PAYLOAD["password"],
}


async def test_register_user_success(client) -> None:
    response = await client.post(REGISTER_URL, json=USER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == USER_PAYLOAD["email"]
    assert body["role"] == "consumer"
    # The hashed password must never leak through the API response.
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_email_returns_409(client) -> None:
    await client.post(REGISTER_URL, json=USER_PAYLOAD)

    response = await client.post(REGISTER_URL, json=USER_PAYLOAD)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


async def test_register_short_password_returns_422(client) -> None:
    response = await client.post(
        REGISTER_URL, json={**USER_PAYLOAD, "email": "short@ecobite.vn", "password": "123"}
    )

    assert response.status_code == 422


async def test_login_success_returns_bearer_token(client) -> None:
    await client.post(REGISTER_URL, json=USER_PAYLOAD)

    response = await client.post(LOGIN_URL, data=FORM_CREDENTIALS)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] == 3600
    assert body["user"]["email"] == USER_PAYLOAD["email"]
    assert body["user"]["role"] == "CONSUMER"


async def test_login_with_json_payload_success(client) -> None:
    """Frontend React calls /auth/login with JSON body { email, password }."""
    await client.post(REGISTER_URL, json=USER_PAYLOAD)

    response = await client.post(
        LOGIN_URL,
        json={"email": USER_PAYLOAD["email"], "password": USER_PAYLOAD["password"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["full_name"] == USER_PAYLOAD["full_name"]


async def test_login_refresh_token_flow(client) -> None:
    """Validate exchanging refresh token for a new valid access token."""
    await client.post(REGISTER_URL, json=USER_PAYLOAD)

    login_resp = await client.post(
        LOGIN_URL,
        json={"email": USER_PAYLOAD["email"], "password": USER_PAYLOAD["password"]},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        REFRESH_URL,
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    refreshed_body = refresh_resp.json()
    assert refreshed_body["access_token"]
    assert refreshed_body["user"]["email"] == USER_PAYLOAD["email"]


async def test_login_wrong_password_returns_401(client) -> None:
    await client.post(REGISTER_URL, json=USER_PAYLOAD)

    response = await client.post(
        LOGIN_URL, data={"username": FORM_CREDENTIALS["username"], "password": "TotallyWrong"}
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_login_unknown_email_returns_401(client) -> None:
    response = await client.post(
        LOGIN_URL, data={"username": "ghost@ecobite.vn", "password": "S3curePass!2024"}
    )

    assert response.status_code == 401
