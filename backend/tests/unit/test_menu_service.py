"""Unit tests for menu catalog service error and no-op paths."""

import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.menu_item import ItemCategory
from app.models.store import KycStatus
from app.services.menu_service import MenuService


def _menu_item_data() -> dict[str, object]:
    return {
        "name": "Com tam",
        "category": ItemCategory.RICE,
        "original_price": Decimal("45000"),
        "image_url": "https://cdn.ecobite.vn/com-tam.jpg",
        "standard_ingredients": ["rice"],
        "base_allergens": [],
    }


async def test_menu_service_not_found_paths(db_session) -> None:
    service = MenuService(db_session)
    missing_id = uuid.uuid4()

    for action in (
        service.get_store_menu_items(missing_id),
        service.create_menu_item(missing_id, _menu_item_data()),
        service.update_menu_item(missing_id, {"name": "Missing"}),
        service.delete_menu_item(missing_id),
    ):
        with pytest.raises(HTTPException) as error:
            await action
        assert error.value.status_code == 404


async def test_menu_service_rejects_pending_store(store_partner, db_session) -> None:
    store = store_partner["store"]
    store.kyc_status = KycStatus.PENDING
    await db_session.commit()

    with pytest.raises(HTTPException) as error:
        await MenuService(db_session).create_menu_item(store.id, _menu_item_data())

    assert error.value.status_code == 403


async def test_menu_service_empty_update_is_a_no_op(store_partner, db_session) -> None:
    service = MenuService(db_session)
    item = await service.create_menu_item(store_partner["store"].id, _menu_item_data())

    unchanged = await service.update_menu_item(item.id, {})

    assert unchanged.name == item.name
