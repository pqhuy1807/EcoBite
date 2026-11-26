"""Integration tests for VNPay payment endpoints: create-url, IPN/return, RBAC."""

import urllib.parse
import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models.order import OrderStatus, PaymentMethod, PaymentStatus
from app.models.user import User, UserRole
from app.services.payment_service import PaymentService

ALL_DAY_WINDOW = {"pickup_start_time": "00:00:00", "pickup_end_time": "23:59:00"}


def _set_vnp_hash_secret() -> patch:
    return patch.object(settings, "VNP_HASH_SECRET", "test_secret")


async def _create_menu_item(client: AsyncClient, store_partner: dict) -> str:
    response = await client.post(
        f"/api/v1/stores/{store_partner['store'].id}/menu-items",
        json={
            "name": "Banh mi trung",
            "category": "BAKERY",
            "original_price": "40000",
            "image_url": "https://cdn.ecobite.vn/banh-mi-trung.jpg",
            "standard_ingredients": ["bread", "egg"],
            "base_allergens": ["gluten", "egg"],
        },
        headers=store_partner["headers"],
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_rescue_dish(client: AsyncClient, store_partner: dict) -> str:
    menu_item_id = await _create_menu_item(client, store_partner)
    response = await client.post(
        "/api/v1/dishes",
        json={
            "menu_item_id": menu_item_id,
            "total_quantity": 4,
            "override_discounted_price": "15000",
            **ALL_DAY_WINDOW,
        },
        headers=store_partner["headers"],
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _place_vnpay_order(
    client: AsyncClient, headers: dict, dish_id: str, quantity: int = 1
):
    return await client.post(
        "/api/v1/orders",
        json={"dish_id": dish_id, "quantity": quantity, "payment_method": "VNPAY"},
        headers=headers,
    )


# ==============================================================================
# 1. POST /api/v1/payments/vnpay/create-url
# ==============================================================================


async def test_create_vnpay_payment_url_consumer_success(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
) -> None:
    """200: consumer nhận URL thanh toán bắt đầu bằng settings.VNP_URL, có chữ ký."""
    with _set_vnp_hash_secret():
        dish_id = await _create_rescue_dish(client, store_partner)
        order_resp = await _place_vnpay_order(client, consumer["headers"], dish_id)
        assert order_resp.status_code == 201
        order = order_resp.json()
        assert order["payment_method"] == PaymentMethod.VNPAY
        assert order["payment_status"] == PaymentStatus.PENDING

        response = await client.post(
            f"/api/v1/payments/vnpay/create-url?order_id={order['id']}",
            headers=consumer["headers"],
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["txn_ref"] == order["order_code"]
    assert body["payment_url"].startswith(settings.VNP_URL + "?")
    assert "vnp_SecureHash=" in body["payment_url"]
    assert "vnp_CreateDate=" in body["payment_url"]
    assert "vnp_TmnCode=" in body["payment_url"]
    assert "vnp_Amount=" in body["payment_url"]


async def test_create_vnpay_payment_url_client_ip_from_x_forwarded_for(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
) -> None:
    """client_ip lấy từ header X-ForwardedFor và nằm trong vnp_IpAddr của URL."""
    with _set_vnp_hash_secret():
        dish_id = await _create_rescue_dish(client, store_partner)
        order_resp = await _place_vnpay_order(client, consumer["headers"], dish_id)
        order = order_resp.json()

        client_ip = "203.0.113.5"
        response = await client.post(
            f"/api/v1/payments/vnpay/create-url?order_id={order['id']}",
            headers={**consumer["headers"], "X-Forwarded-For": client_ip},
        )

    assert response.status_code == 200, response.text
    assert f"vnp_IpAddr={client_ip}" in response.json()["payment_url"]


async def test_create_vnpay_payment_url_store_partner_forbidden(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
) -> None:
    """403: store partner không được tạo URL thanh toán (RBAC CONSUMER)."""
    with _set_vnp_hash_secret():
        dish_id = await _create_rescue_dish(client, store_partner)
        order_resp = await _place_vnpay_order(client, consumer["headers"], dish_id)
        order = order_resp.json()

        response = await client.post(
            f"/api/v1/payments/vnpay/create-url?order_id={order['id']}",
            headers=store_partner["headers"],
        )

    assert response.status_code == 403


async def test_create_vnpay_payment_url_unauthorized_returns_401(
    client: AsyncClient,
    store_partner: dict,
    consumer: dict,
) -> None:
    """401: không kèm token JWT."""
    with _set_vnp_hash_secret():
        dish_id = await _create_rescue_dish(client, store_partner)
        order_resp = await _place_vnpay_order(client, consumer["headers"], dish_id)
        order = order_resp.json()

        response = await client.post(
            f"/api/v1/payments/vnpay/create-url?order_id={order['id']}",
        )

    assert response.status_code == 401


async def test_create_vnpay_payment_url_order_not_found_returns_404(
    client: AsyncClient,
    consumer: dict,
) -> None:
    """404: order_id không tồn tại."""
    with _set_vnp_hash_secret():
        response = await client.post(
            f"/api/v1/payments/vnpay/create-url?order_id={uuid.uuid4()}",
            headers=consumer["headers"],
        )

    assert response.status_code == 404


# ==============================================================================
# 2. GET /api/v1/payments/vnpay/return (chỉ xác thực chữ ký, không xử lý đơn)
# ==============================================================================


async def test_vnpay_return_valid_signature(client: AsyncClient) -> None:
    """200 + is_valid=True khi chữ ký HMAC-SHA512 hợp lệ."""
    with _set_vnp_hash_secret():
        params = {
            "vnp_TxnRef": "EB-INTEGRATION-001",
            "vnp_Amount": "1000000",
            "vnp_ResponseCode": "00",
            "vnp_TmnCode": "TESTTMNCODE",
            "vnp_TransactionNo": "987654321",
        }
        params["vnp_SecureHash"] = PaymentService._generate_vnpay_hash(params)

        query = urllib.parse.urlencode(params)
        response = await client.get(f"/api/v1/payments/vnpay/return?{query}")

    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is True
    assert body["txn_ref"] == "EB-INTEGRATION-001"
    assert "verified" in body["message"].lower()


async def test_vnpay_return_invalid_signature(client: AsyncClient) -> None:
    """200 + is_valid=False khi chữ ký sai."""
    with _set_vnp_hash_secret():
        params = {
            "vnp_TxnRef": "EB-INTEGRATION-002",
            "vnp_Amount": "1000000",
            "vnp_ResponseCode": "00",
            "vnp_SecureHash": "invalid_signature",
        }

        query = urllib.parse.urlencode(params)
        response = await client.get(f"/api/v1/payments/vnpay/return?{query}")

    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is False
    assert body["txn_ref"] == "EB-INTEGRATION-002"


async def test_vnpay_return_missing_txn_ref(client: AsyncClient) -> None:
    """200 + is_valid=False khi thiếu vnp_TxnRef."""
    with _set_vnp_hash_secret():
        params = {
            "vnp_Amount": "1000000",
            "vnp_ResponseCode": "00",
            "vnp_SecureHash": PaymentService._generate_vnpay_hash(
                {"vnp_Amount": "1000000", "vnp_ResponseCode": "00"}
            ),
        }

        query = urllib.parse.urlencode(params)
        response = await client.get(f"/api/v1/payments/vnpay/return?{query}")

    assert response.status_code == 200
    assert response.json()["is_valid"] is False
    assert response.json()["txn_ref"] == ""
