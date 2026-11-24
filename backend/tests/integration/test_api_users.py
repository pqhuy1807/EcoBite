"""Integration tests for /api/v1/users endpoints (JWT-protected routes)."""

LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/users/me"
REGISTER_URL = "/api/v1/auth/register"

USER_PAYLOAD: dict[str, str] = {
    "email": "me@ecobite.vn",
    "password": "S3curePass!2024",
    "full_name": "Tran Thi B",
}


async def _login_token(client) -> str:
    await client.post(REGISTER_URL, json=USER_PAYLOAD)
    response = await client.post(
        LOGIN_URL,
        data={"username": USER_PAYLOAD["email"], "password": USER_PAYLOAD["password"]},
    )
    return response.json()["access_token"]


async def test_get_me_with_valid_token(client) -> None:
    token = await _login_token(client)

    response = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == USER_PAYLOAD["email"]


async def test_get_me_without_token_returns_401(client) -> None:
    response = await client.get(ME_URL)

    assert response.status_code == 401


async def test_get_me_with_invalid_token_returns_401(client) -> None:
    response = await client.get(ME_URL, headers={"Authorization": "Bearer not-a-real-jwt"})

    assert response.status_code == 401
