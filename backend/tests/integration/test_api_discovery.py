"""Integration tests for PostGIS / Spatial Radar Discovery (/api/v1/stores/nearby)."""

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


async def _setup_approved_store_with_dish(
    client: AsyncClient,
    partner_token: str,
    admin_token: str,
    *,
    name: str,
    lat: float,
    lng: float,
    dish_name: str,
    category: str,
) -> str:
    onboard = await client.post(
        "/api/v1/stores/onboard",
        json={
            "name": name,
            "address": "TP.HCM",
            "latitude": lat,
            "longitude": lng,
        },
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    store_id = str(onboard.json()["id"])

    await client.patch(
        f"/api/v1/admin/stores/{store_id}/review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    menu_resp = await client.post(
        f"/api/v1/stores/{store_id}/menu-items",
        json={
            "name": dish_name,
            "category": category,
            "original_price": 45000.0,
            "image_url": "https://cdn.ecobite.vn/menu/sample.jpg",
        },
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    menu_item_id = menu_resp.json()["id"]

    await client.post(
        "/api/v1/dishes",
        json={
            "menu_item_id": menu_item_id,
            "pickup_start_time": "14:00:00",
            "pickup_end_time": "22:00:00",
            "total_quantity": 5,
        },
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    return store_id


async def test_discovery_nearby_stores_success(client: AsyncClient) -> None:
    """Tìm kiếm quán lân cận bằng tọa độ GPS trong bán kính 3km."""
    partner_token = await _register_and_login(client, "partner_disc@ecobite.vn", "store_partner")
    admin_token = await _register_and_login(client, "admin_disc@ecobite.vn", "admin")

    # Quán 1: Cách tâm Nguyễn Huệ ~200m (Trong bán kính 3km)
    await _setup_approved_store_with_dish(
        client,
        partner_token,
        admin_token,
        name="Cơm Tấm Nguyễn Huệ",
        lat=10.7755,
        lng=106.7015,
        dish_name="Cơm sườn bì chả",
        category="RICE",
    )

    # Quán 2: Ở Thủ Đức cách ~15km (Ngoài bán kính 3km)
    await _setup_approved_store_with_dish(
        client,
        partner_token,
        admin_token,
        name="Bún Bò Làng Đại Học",
        lat=10.8750,
        lng=106.8000,
        dish_name="Bún bò Huế",
        category="NOODLES",
    )

    response = await client.get(
        "/api/v1/stores/nearby",
        params={"lat": 10.7769, "lng": 106.7009, "radius_km": 3.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["name"] == "Cơm Tấm Nguyễn Huệ"
    assert data["results"][0]["distance_meters"] < 3000


async def test_discovery_nearby_stores_with_category_filter(client: AsyncClient) -> None:
    """Tìm kiếm quán lân cận kết hợp bộ lọc danh mục ẩm thực (RICE vs BAKERY)."""
    partner_token = await _register_and_login(client, "partner_cat@ecobite.vn", "store_partner")
    admin_token = await _register_and_login(client, "admin_cat@ecobite.vn", "admin")

    await _setup_approved_store_with_dish(
        client,
        partner_token,
        admin_token,
        name="Tiệm Bánh Ngọt Bến Nghé",
        lat=10.7768,
        lng=106.7008,
        dish_name="Bánh Croissant Bơ Pháp",
        category="BAKERY",
    )

    resp_bakery = await client.get(
        "/api/v1/stores/nearby",
        params={"lat": 10.7769, "lng": 106.7009, "radius_km": 3.0, "category": "BAKERY"},
    )
    assert resp_bakery.status_code == 200
    assert resp_bakery.json()["total"] == 1

    resp_rice = await client.get(
        "/api/v1/stores/nearby",
        params={"lat": 10.7769, "lng": 106.7009, "radius_km": 3.0, "category": "RICE"},
    )
    assert resp_rice.status_code == 200
    assert resp_rice.json()["total"] == 0
