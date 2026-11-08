"""Integration tests for surplus dish publication and stock management."""

DISH_TIMES = {"pickup_start_time": "14:00:00", "pickup_end_time": "15:00:00"}


async def _create_menu_item(client, store_partner) -> str:
    response = await client.post(
        f"/api/v1/stores/{store_partner['store'].id}/menu-items",
        json={
            "name": "Com tam",
            "category": "RICE",
            "original_price": "45000",
            "image_url": "https://cdn.ecobite.vn/com-tam.jpg",
            "standard_ingredients": ["rice", "pork"],
            "base_allergens": ["fish"],
        },
        headers=store_partner["headers"],
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_create_dish_grounds_menu_data_and_calculates_prices(client, store_partner) -> None:
    menu_item_id = await _create_menu_item(client, store_partner)
    response = await client.post(
        "/api/v1/dishes",
        json={
            "menu_item_id": menu_item_id,
            "total_quantity": 5,
            **DISH_TIMES,
        },
        headers=store_partner["headers"],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Com tam"
    assert body["original_price"] == "45000.00"
    assert body["rescue_price"] == "22500.00"
    assert body["rule_discount_price"] == "13500.00"
    assert body["total_quantity"] == body["remaining_quantity"] == 5
    assert body["ingredients"] == ["rice", "pork"]

    # Test explicit remaining_quantity lower than total_quantity
    response_with_remaining = await client.post(
        "/api/v1/dishes",
        json={
            "menu_item_id": menu_item_id,
            "total_quantity": 10,
            "remaining_quantity": 7,
            **DISH_TIMES,
        },
        headers=store_partner["headers"],
    )
    assert response_with_remaining.status_code == 201
    assert response_with_remaining.json()["total_quantity"] == 10
    assert response_with_remaining.json()["remaining_quantity"] == 7


async def test_dish_rejects_invalid_quantity_and_pickup_window(client, store_partner) -> None:
    menu_item_id = await _create_menu_item(client, store_partner)
    invalid_quantity = await client.post(
        "/api/v1/dishes",
        json={"menu_item_id": menu_item_id, "total_quantity": 0, **DISH_TIMES},
        headers=store_partner["headers"],
    )
    invalid_window = await client.post(
        "/api/v1/dishes",
        json={
            "menu_item_id": menu_item_id,
            "total_quantity": 2,
            "pickup_start_time": "15:00:00",
            "pickup_end_time": "14:00:00",
        },
        headers=store_partner["headers"],
    )
    invalid_remaining = await client.post(
        "/api/v1/dishes",
        json={
            "menu_item_id": menu_item_id,
            "total_quantity": 5,
            "remaining_quantity": 8,
            **DISH_TIMES,
        },
        headers=store_partner["headers"],
    )

    assert invalid_quantity.status_code == 422
    assert invalid_window.status_code == 422
    assert invalid_remaining.status_code == 422


async def test_active_dishes_and_quantity_update(client, store_partner) -> None:
    menu_item_id = await _create_menu_item(client, store_partner)
    created = await client.post(
        "/api/v1/dishes",
        json={"menu_item_id": menu_item_id, "total_quantity": 5, **DISH_TIMES},
        headers=store_partner["headers"],
    )

    updated = await client.patch(
        f"/api/v1/dishes/{created.json()['id']}/quantity",
        json={"quantity": 0},
        headers=store_partner["headers"],
    )
    listed = await client.get(
        f"/api/v1/stores/{store_partner['store'].id}/dishes/active",
        headers=store_partner["headers"],
    )
    invalid = await client.patch(
        f"/api/v1/dishes/{created.json()['id']}/quantity",
        json={"quantity": -1},
        headers=store_partner["headers"],
    )

    assert updated.status_code == 200
    assert updated.json()["remaining_quantity"] == 0
    assert listed.status_code == 200
    assert listed.json()["dishes"] == []
    assert invalid.status_code == 422


async def test_dish_mutations_require_store_owner(
    client, store_partner, other_store_partner
) -> None:
    menu_item_id = await _create_menu_item(client, store_partner)

    # Store B tries to publish dish for Store A's menu item -> 403
    forbidden_create = await client.post(
        "/api/v1/dishes",
        json={"menu_item_id": menu_item_id, "total_quantity": 5, **DISH_TIMES},
        headers=other_store_partner["headers"],
    )
    assert forbidden_create.status_code == 403

    created = await client.post(
        "/api/v1/dishes",
        json={"menu_item_id": menu_item_id, "total_quantity": 5, **DISH_TIMES},
        headers=store_partner["headers"],
    )

    # Store B tries to view active dishes of Store A -> 403
    forbidden_list = await client.get(
        f"/api/v1/stores/{store_partner['store'].id}/dishes/active",
        headers=other_store_partner["headers"],
    )
    assert forbidden_list.status_code == 403

    # Store B tries to patch quantity of Store A's dish -> 403
    forbidden_patch = await client.patch(
        f"/api/v1/dishes/{created.json()['id']}/quantity",
        json={"quantity": 3},
        headers=other_store_partner["headers"],
    )
    assert forbidden_patch.status_code == 403


async def test_batch_dishes_are_persisted_from_menu_items(client, store_partner) -> None:
    menu_item_id = await _create_menu_item(client, store_partner)
    response = await client.post(
        "/api/v1/dishes/batch",
        json={
            **DISH_TIMES,
            "dishes": [{"menu_item_id": menu_item_id, "quantity": 3}],
        },
        headers=store_partner["headers"],
    )

    assert response.status_code == 201
    assert response.json()["created_count"] == 1
    assert response.json()["dishes"][0]["remaining_quantity"] == 3
