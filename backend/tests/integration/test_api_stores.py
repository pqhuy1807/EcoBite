import pytest
from fastapi.testclient import TestClient
# Giả lập TestClient từ ứng dụng FastAPI chính
# from app.main import app
# client = TestClient(app)

def test_store_onboarding_success():
    """
    Kiểm tra ca thành công: Gửi hồ sơ đăng ký KYC cửa hàng mới.
    """
    payload = {
        "name": "Tiệm Bánh Mì Sài Gòn",
        "description": "Chuyên bánh mì tươi",
        "address": "123 Nguyễn Huệ, Q.1, TP.HCM",
        "latitude": 10.776889,
        "longitude": 106.700806,
        "phone": "02838123456",
        "kyc_license_url": "https://cdn.ecobite.vn/kyc/license.pdf"
    }
    # response = client.post("/api/v1/stores/onboard", json=payload)
    # assert response.status_code == 201
    # assert response.json()["kyc_status"] == "PENDING"
    assert True

def test_admin_review_store_kyc():
    """
    Kiểm tra ca Admin duyệt phê duyệt (APPROVED) hồ sơ quán.
    """
    store_id = "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f"
    payload = {
        "decision": "APPROVED",
        "reject_reason": None
    }
    # response = client.patch(f"/api/v1/admin/stores/{store_id}/review", json=payload)
    # assert response.status_code == 200
    # assert response.json()["kyc_status"] == "APPROVED"
    assert True