"""Integration tests for Base Menu Catalog and Surplus Dishes endpoints."""

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


async def test_menu_crud_and_ownership_protection(client: AsyncClient) -> None:
    """Kiểm tra CRUD thực đơn gốc và chặn quyền khi quán B cố sửa menu của quán A."""
    token_owner_a = await _register_and_login(client, "owner_a@ecobite.vn", "store_partner")
    token_owner_b = await _register_and_login(client, "owner_b@ecobite.vn", "store_partner")

    store_resp = await client.post(
        "/api/v1/stores/onboard",
        json={
            "name": "Quán Của Owner A",
            "address": "100 Lê Lợi, Q.1, TP.HCM",
            "latitude": 10.773,
            "longitude": 106.698,
        },
        headers={"Authorization": f"Bearer {token_owner_a}"},
    )
    store_id = store_resp.json()["id"]

    # Owner A tạo món vào thực đơn gốc
    create_resp = await client.post(
        f"/api/v1/stores/{store_id}/menu-items",
        json={
            "name": "Cơm sườn bì chả",
            "category": "RICE",
            "original_price": 45000.0,
            "image_url": "https://cdn.ecobite.vn/menu/com_suon.jpg",
            "base_allergens": ["Eggs (Trứng)", "Fish (Nước mắm)"],
        },
        headers={"Authorization": f"Bearer {token_owner_a}"},
    )
    assert create_resp.status_code == 201
    item_id = create_resp.json()["id"]

    # Owner B cố tình sửa món của Owner A -> Phải bị chặn 403 Forbidden
    forbidden_resp = await client.put(
        f"/api/v1/menu-items/{item_id}",
        json={"name": "Món bị hack", "original_price": 1000.0},
        headers={"Authorization": f"Bearer {token_owner_b}"},
    )
    assert forbidden_resp.status_code == 403

    # Owner A cập nhật và xóa mềm thành công
    update_resp = await client.put(
        f"/api/v1/menu-items/{item_id}",
        json={"original_price": 50000.0},
        headers={"Authorization": f"Bearer {token_owner_a}"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["original_price"] == 50000.0

    del_resp = await client.delete(
        f"/api/v1/menu-items/{item_id}",
        headers={"Authorization": f"Bearer {token_owner_a}"},
    )
    assert del_resp.status_code == 200


async def test_surplus_dishes_menu_grounding_and_batch_post(client: AsyncClient) -> None:
    """Kiểm tra đăng món giải cứu kế thừa Menu Grounding và đăng hàng loạt (Batch Post)."""
    partner_token = await _register_and_login(client, "partner_dish@ecobite.vn", "store_partner")

    store_resp = await client.post(
        "/api/v1/stores/onboard",
        json={
            "name": "Bếp Xanh Sài Gòn",
            "address": "50 Pasteur, Q.1, TP.HCM",
            "latitude": 10.778,
            "longitude": 106.701,
        },
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    store_id = store_resp.json()["id"]

    menu_resp = await client.post(
        f"/api/v1/stores/{store_id}/menu-items",
        json={
            "name": "Bún thịt nướng chả giò",
            "category": "NOODLES",
            "original_price": 50000.0,
            "image_url": "https://cdn.ecobite.vn/menu/bun_thit_nuong.jpg",
        },
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    menu_item_id = menu_resp.json()["id"]

    # Đăng lẻ kế thừa giá gốc 50,000đ từ menu_item_id
    dish_resp = await client.post(
        "/api/v1/dishes",
        json={
            "store_id": store_id,
            "menu_item_id": menu_item_id,
            "pickup_start_time": "14:00:00",
            "pickup_end_time": "16:00:00",
            "total_quantity": 5,
        },
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert dish_resp.status_code == 201
    dish_data = dish_resp.json()
    assert dish_data["name"] == "Bún thịt nướng chả giò"
    assert dish_data["original_price"] == 50000.0
    assert dish_data["remaining_quantity"] == 5

    # Cập nhật số lượng thủ công
    dish_id = dish_data["id"]
    qty_resp = await client.patch(
        f"/api/v1/dishes/{dish_id}/quantity",
        json={"quantity": 3},
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert qty_resp.status_code == 200
    assert qty_resp.json()["updated_quantity"] == 3

    # Đăng hàng loạt (Batch Post)
    batch_resp = await client.post(
        "/api/v1/dishes/batch",
        json={
            "store_id": store_id,
            "pickup_start_time": "18:00:00",
            "pickup_end_time": "20:00:00",
            "dishes": [
                {"menu_item_id": menu_item_id, "quantity": 4},
                {
                    "name": "Cơm chiên dương châu",
                    "quantity": 2,
                    "override_discounted_price": 20000.0,
                },
            ],
        },
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert batch_resp.status_code == 201
    assert batch_resp.json()["created_count"] == 2

    # Kiểm tra danh sách món đang mở bán của quán
    active_resp = await client.get(f"/api/v1/stores/{store_id}/dishes/active")
    assert active_resp.status_code == 200
    assert len(active_resp.json()["dishes"]) == 3
