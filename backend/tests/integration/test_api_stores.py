"""Integration tests for Store Onboarding and Admin KYC verification endpoints."""

from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


async def _register_and_login(
    client: AsyncClient,
    email: str,
    role: str,
) -> str:
    password = "StrongPassword123!"
    await client.post(
        REGISTER_URL,
        json={
            "email": email,
            "password": password,
            "full_name": f"User {role}",
            "role": role,
        },
    )
    resp = await client.post(
        LOGIN_URL,
        data={"username": email, "password": password},
    )
    return str(resp.json()["access_token"])


async def test_store_onboarding_success(client: AsyncClient) -> None:
    """Đối tác cửa hàng (STORE_PARTNER) gửi hồ sơ đăng ký KYC thành công."""
    partner_token = await _register_and_login(client, "partner_kyc@ecobite.vn", "store_partner")

    payload = {
        "name": "Tiệm Bánh Mì Sài Gòn",
        "description": "Chuyên bánh mì tươi trong ngày",
        "address": "123 Nguyễn Huệ, Q.1, TP.HCM",
        "latitude": 10.776889,
        "longitude": 106.700806,
        "phone": "02838123456",
        "kyc_license_url": "https://cdn.ecobite.vn/kyc/license.pdf",
    }
    response = await client.post(
        "/api/v1/stores/onboard",
        json=payload,
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tiệm Bánh Mì Sài Gòn"
    assert data["kyc_status"] == "PENDING"
    assert "id" in data


async def test_consumer_cannot_onboard_store_returns_403(client: AsyncClient) -> None:
    """Tài khoản CONSUMER không được phép gọi API onboard cửa hàng (Guardrail #2)."""
    consumer_token = await _register_and_login(client, "consumer_kyc@ecobite.vn", "consumer")

    response = await client.post(
        "/api/v1/stores/onboard",
        json={"name": "Quán Test", "address": "123 Lê Lợi, Q.1"},
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert response.status_code == 403


async def test_admin_review_store_kyc(client: AsyncClient) -> None:
    """Admin xem danh sách chờ duyệt và phê duyệt (APPROVED) hồ sơ quán."""
    partner_token = await _register_and_login(client, "partner_rev@ecobite.vn", "store_partner")
    admin_token = await _register_and_login(client, "admin_rev@ecobite.vn", "admin")

    onboard_resp = await client.post(
        "/api/v1/stores/onboard",
        json={
            "name": "Quán Cơm Tấm Bụi",
            "address": "45 Đinh Tiên Hoàng, Q.1, TP.HCM",
            "latitude": 10.788,
            "longitude": 106.698,
        },
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    store_id = onboard_resp.json()["id"]

    # Admin lấy danh sách quán chờ duyệt
    pending_resp = await client.get(
        "/api/v1/admin/stores/pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pending_resp.status_code == 200
    assert pending_resp.json()["total"] >= 1

    # Admin phê duyệt KYC
    review_resp = await client.patch(
        f"/api/v1/admin/stores/{store_id}/review",
        json={"decision": "APPROVED", "reject_reason": None},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["kyc_status"] == "APPROVED"

    # Kiểm tra chi tiết quán sau khi duyệt
    detail_resp = await client.get(f"/api/v1/stores/{store_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["kyc_status"] == "APPROVED"
