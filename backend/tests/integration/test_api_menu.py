"""Integration tests for the merchant menu catalog endpoints."""

import uuid

MENU_PAYLOAD = {
    "name": "Com tam",
    "description": "Com tam suon",
    "category": "RICE",
    "original_price": "45000",
    "image_url": "https://cdn.ecobite.vn/com-tam.jpg",
    "standard_ingredients": ["rice", "pork"],
    "base_allergens": ["fish"],
    "dietary_type": "NON_VEGAN",
}


async def test_create_and_list_menu_items(client, store_partner) -> None:
    store_id = store_partner["store"].id
    headers = store_partner["headers"]

    created = await client.post(
        f"/api/v1/stores/{store_id}/menu-items", json=MENU_PAYLOAD, headers=headers
    )

    assert created.status_code == 201
    assert created.json()["name"] == MENU_PAYLOAD["name"]
    assert created.json()["store_id"] == str(store_id)

    listed = await client.get(f"/api/v1/stores/{store_id}/menu-items", headers=headers)

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created.json()["id"]


async def test_menu_item_update_and_soft_delete(client, store_partner) -> None:
    store_id = store_partner["store"].id
    headers = store_partner["headers"]
    created = await client.post(
        f"/api/v1/stores/{store_id}/menu-items", json=MENU_PAYLOAD, headers=headers
    )
    item_id = created.json()["id"]

    updated = await client.put(
        f"/api/v1/menu-items/{item_id}",
        json={"name": "Com tam dac biet"},
        headers=headers,
    )
    deleted = await client.delete(f"/api/v1/menu-items/{item_id}", headers=headers)
    listed = await client.get(f"/api/v1/stores/{store_id}/menu-items", headers=headers)

    assert updated.status_code == 200
    assert updated.json()["name"] == "Com tam dac biet"
    assert deleted.status_code == 200
    assert listed.json()["total"] == 0


async def test_menu_rejects_nonpositive_price(client, store_partner) -> None:
    response = await client.post(
        f"/api/v1/stores/{store_partner['store'].id}/menu-items",
        json={**MENU_PAYLOAD, "original_price": "0"},
        headers=store_partner["headers"],
    )

    assert response.status_code == 422


async def test_menu_mutations_require_owner_and_authentication(
    client, store_partner, other_store_partner
) -> None:
    # User of Store B tries to add a menu item to Store A -> 403 Forbidden
    create_forbidden = await client.post(
        f"/api/v1/stores/{store_partner['store'].id}/menu-items",
        json=MENU_PAYLOAD,
        headers=other_store_partner["headers"],
    )
    assert create_forbidden.status_code == 403

    created = await client.post(
        f"/api/v1/stores/{store_partner['store'].id}/menu-items",
        json=MENU_PAYLOAD,
        headers=store_partner["headers"],
    )

    # User of Store B tries to modify Store A's menu item -> 403 Forbidden
    put_forbidden = await client.put(
        f"/api/v1/menu-items/{created.json()['id']}",
        json={"name": "Hijacked"},
        headers=other_store_partner["headers"],
    )
    assert put_forbidden.status_code == 403

    # User of Store B tries to delete Store A's menu item -> 403 Forbidden
    delete_forbidden = await client.delete(
        f"/api/v1/menu-items/{created.json()['id']}",
        headers=other_store_partner["headers"],
    )
    assert delete_forbidden.status_code == 403

    unauthenticated = await client.get(f"/api/v1/stores/{store_partner['store'].id}/menu-items")
    assert unauthenticated.status_code == 401


async def test_missing_menu_item_returns_404(client, store_partner) -> None:
    response = await client.put(
        f"/api/v1/menu-items/{uuid.uuid4()}",
        json={"name": "Missing"},
        headers=store_partner["headers"],
    )

    assert response.status_code == 404
