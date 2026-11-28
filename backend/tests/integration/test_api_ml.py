"""TDD integration tests for POST /api/v1/ml/parse-dish-nlp (specs/002-ai-quick-post-nlp).

Covers:
- Phase 4 (T011): Multipart audio upload (200 OK for valid audio / audio+text;
  413 >10 MB, 415 unsupported format, 422 0-byte audio without calling Gemini).
- Phase 5 (T015): 401 unauthenticated, 403 for CONSUMER/ADMIN, 403 for PENDING/REJECTED
  store KYC, 404 for STORE_PARTNER without store, 422 missing both text & audio,
  503 AI unavailability, 404 for removed legacy /quick-post/* prototype routes,
  and full E2E handoff into POST /api/v1/dishes/batch (201 Created).
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.main import app
from app.models.menu_item import DietaryType, ItemCategory, MenuItem
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole
from app.schemas.nlp import (
    AllergenRiskLevel,
    DetectionSource,
    EUAllergen,
    NLPAllergenWarning,
    QuickPostExtractionResponse,
    SurplusDishItem,
)
from app.services.quick_post_service import QuickPostService

MAX_AUDIO_BYTES = 10 * 1024 * 1024


class FakeResponse:
    def __init__(self, parsed: Any = None, text: str | None = None) -> None:
        self.parsed = parsed
        self.text = text


class FakeGeminiClient:
    def __init__(self, response: Any = None, exc: Exception | None = None) -> None:
        self._response = response
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    async def generate_content(self, *, model: str, contents: Any, config: Any) -> Any:
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self._exc is not None:
            raise self._exc
        return self._response


@contextmanager
def _override_ml_service(
    db_session: AsyncSession,
    gemini_client: FakeGeminiClient | None,
) -> Iterator[None]:
    """Override `get_quick_post_service` in `app.api.v1.endpoints.ml` without real Gemini calls."""
    try:
        ml_module = importlib.import_module("app.api.v1.endpoints.ml")
    except ModuleNotFoundError:
        pytest.fail(
            "TDD RED: Chưa tạo module `backend/app/api/v1/endpoints/ml.py` "
            "và dependency `get_quick_post_service`."
        )

    dep = getattr(ml_module, "get_quick_post_service", None)
    if dep is None:
        pytest.fail(
            "TDD RED: `get_quick_post_service` chưa được định nghĩa trong "
            "`app.api.v1.endpoints.ml`."
        )

    def _provider() -> QuickPostService:
        return QuickPostService(db_session, gemini_client=gemini_client)

    app.dependency_overrides[dep] = _provider
    try:
        yield
    finally:
        app.dependency_overrides.pop(dep, None)


async def _create_menu_item(
    db_session: AsyncSession,
    store: Store,
    *,
    name: str,
    original_price: Decimal,
    category: ItemCategory = ItemCategory.RICE,
) -> MenuItem:
    item = MenuItem(
        store_id=store.id,
        name=name,
        category=category,
        original_price=original_price,
        image_url="https://cdn.ecobite.vn/sample.jpg",
        standard_ingredients=["cơm", "thịt"],
        base_allergens=["Fish (Cá/Nước mắm)"],
        dietary_type=DietaryType.NON_VEGAN,
        is_active=True,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _create_user_with_headers(
    db_session: AsyncSession,
    *,
    email: str,
    role: UserRole,
    store_kyc: KycStatus | None = None,
) -> dict[str, Any]:
    user = User(
        email=email,
        hashed_password="not-used-by-tests",
        full_name="Test User",
        role=role,
    )
    db_session.add(user)
    await db_session.flush()
    store: Store | None = None
    if store_kyc is not None:
        store = Store(
            owner_id=user.id,
            name=f"Store {store_kyc.value}",
            address="100 Nguyen Hue",
            location="POINT(106.7 10.77)",
            kyc_status=store_kyc,
        )
        db_session.add(store)
    await db_session.commit()
    return {
        "user": user,
        "store": store,
        "headers": {"Authorization": f"Bearer {create_access_token(user.id)}"},
    }


# ==============================================================================
# Happy Paths: Text, Audio-Only, Audio + Text
# ==============================================================================
async def test_parse_dish_nlp_text_success_200(
    client: AsyncClient,
    db_session: AsyncSession,
    store_partner: dict[str, Any],
) -> None:
    menu_item = await _create_menu_item(
        db_session,
        store_partner["store"],
        name="Cơm sườn bì chả",
        original_price=Decimal("45000.00"),
    )
    extracted = QuickPostExtractionResponse(
        pickup_start="18:00:00",
        pickup_end="20:30:00",
        items=[
            SurplusDishItem(
                matched_menu_id=menu_item.id,
                dish_name="Cơm sườn bì chả",
                quantity=5,
                original_price=None,
                allergens=[
                    NLPAllergenWarning(
                        allergen=EUAllergen.EGGS,
                        risk_level=AllergenRiskLevel.HIGH,
                        source=DetectionSource.INFERRED,
                        reason="Chả trứng có trứng vịt",
                    )
                ],
                dietary_notes=["Có mỡ hành (Allium)"],
            )
        ],
    )
    fake_client = FakeGeminiClient(response=FakeResponse(parsed=extracted))

    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            data={
                "raw_text": "Còn 5 cơm sườn chả từ 6h đến 8h30 tối",
                "current_server_time": "01:00:00",  # Optional legacy param — ignored by server
            },
            headers=store_partner["headers"],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["pickup_start"] == "18:00:00"
    assert body["pickup_end"] == "20:30:00"
    assert len(body["items"]) == 1
    assert body["items"][0]["matched_menu_id"] == str(menu_item.id)
    assert body["items"][0]["original_price"] == pytest.approx(45000.0)
    assert body["items"][0]["allergens"][0]["source"] == "INFERRED"


@pytest.mark.parametrize(
    ("filename", "mime_type"),
    [
        ("clip.m4a", "audio/m4a"),
        ("clip.mp3", "audio/mpeg"),
        ("clip.wav", "audio/wav"),
        ("clip.webm", "audio/webm;codecs=opus"),
    ],
)
async def test_parse_dish_nlp_audio_only_success_200(
    client: AsyncClient,
    db_session: AsyncSession,
    store_partner: dict[str, Any],
    filename: str,
    mime_type: str,
) -> None:
    extracted = QuickPostExtractionResponse(
        pickup_start="18:00:00",
        pickup_end="20:00:00",
        items=[SurplusDishItem(dish_name="Bánh mì thịt", quantity=4)],
    )
    fake_client = FakeGeminiClient(response=FakeResponse(parsed=extracted))

    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            files={"audio_file": (filename, b"fake-audio-bytes", mime_type)},
            headers=store_partner["headers"],
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["dish_name"] == "Bánh mì thịt"
    assert len(fake_client.calls) == 1


async def test_parse_dish_nlp_audio_and_text_combined_200(
    client: AsyncClient,
    db_session: AsyncSession,
    store_partner: dict[str, Any],
) -> None:
    extracted = QuickPostExtractionResponse(
        pickup_start="19:00:00",
        pickup_end="21:00:00",
        items=[SurplusDishItem(dish_name="Phở gà", quantity=2)],
    )
    fake_client = FakeGeminiClient(response=FakeResponse(parsed=extracted))

    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            data={"raw_text": "Không hành lá"},
            files={"audio_file": ("voice.webm", b"fake-webm-bytes", "audio/webm;codecs=opus")},
            headers=store_partner["headers"],
        )

    assert response.status_code == 200
    assert len(fake_client.calls) == 1


# ==============================================================================
# Multipart Audio & Input Validation (413 / 415 / 422)
# ==============================================================================
async def test_parse_dish_nlp_rejects_unsupported_file_type_415(
    client: AsyncClient,
    db_session: AsyncSession,
    store_partner: dict[str, Any],
) -> None:
    fake_client = FakeGeminiClient()

    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            files={"audio_file": ("photo.png", b"\x89PNG\r\n", "image/png")},
            headers=store_partner["headers"],
        )

    assert response.status_code == 415
    assert fake_client.calls == []


async def test_parse_dish_nlp_rejects_oversized_audio_413(
    client: AsyncClient,
    db_session: AsyncSession,
    store_partner: dict[str, Any],
) -> None:
    fake_client = FakeGeminiClient()

    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            files={"audio_file": ("huge.mp3", b"x" * (MAX_AUDIO_BYTES + 1), "audio/mpeg")},
            headers=store_partner["headers"],
        )

    assert response.status_code == 413
    assert fake_client.calls == []


async def test_parse_dish_nlp_rejects_empty_audio_422(
    client: AsyncClient,
    db_session: AsyncSession,
    store_partner: dict[str, Any],
) -> None:
    fake_client = FakeGeminiClient()

    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            files={"audio_file": ("empty.wav", b"", "audio/wav")},
            headers=store_partner["headers"],
        )

    assert response.status_code == 422
    assert fake_client.calls == []


async def test_parse_dish_nlp_rejects_missing_both_text_and_audio_422(
    client: AsyncClient,
    db_session: AsyncSession,
    store_partner: dict[str, Any],
) -> None:
    fake_client = FakeGeminiClient()

    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            data={"raw_text": "   "},
            headers=store_partner["headers"],
        )

    assert response.status_code == 422
    assert fake_client.calls == []


# ==============================================================================
# RBAC, Store KYC, 503 Degradation & Legacy Route Removal
# ==============================================================================
async def test_parse_dish_nlp_requires_authentication_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ml/parse-dish-nlp",
        data={"raw_text": "Còn 3 cơm tấm"},
    )
    assert response.status_code == 401


async def test_parse_dish_nlp_forbids_consumer_and_admin_403(
    client: AsyncClient,
    db_session: AsyncSession,
    consumer: dict[str, Any],
) -> None:
    admin = await _create_user_with_headers(
        db_session,
        email="admin@ecobite.vn",
        role=UserRole.ADMIN,
    )
    fake_client = FakeGeminiClient()

    with _override_ml_service(db_session, fake_client):
        consumer_res = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            data={"raw_text": "Còn 3 cơm tấm"},
            headers=consumer["headers"],
        )
        admin_res = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            data={"raw_text": "Còn 3 cơm tấm"},
            headers=admin["headers"],
        )

    assert consumer_res.status_code == 403
    assert admin_res.status_code == 403
    assert fake_client.calls == []


@pytest.mark.parametrize("kyc_status", [KycStatus.PENDING, KycStatus.REJECTED])
async def test_parse_dish_nlp_forbids_unapproved_store_kyc_403(
    client: AsyncClient,
    db_session: AsyncSession,
    kyc_status: KycStatus,
) -> None:
    partner = await _create_user_with_headers(
        db_session,
        email=f"kyc-{kyc_status.value.lower()}@ecobite.vn",
        role=UserRole.STORE_PARTNER,
        store_kyc=kyc_status,
    )
    fake_client = FakeGeminiClient()

    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            data={"raw_text": "Còn 3 cơm tấm"},
            headers=partner["headers"],
        )

    assert response.status_code == 403
    assert fake_client.calls == []


async def test_parse_dish_nlp_returns_404_when_partner_has_no_store(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    partner = await _create_user_with_headers(
        db_session,
        email="no-store-partner@ecobite.vn",
        role=UserRole.STORE_PARTNER,
        store_kyc=None,
    )
    fake_client = FakeGeminiClient()

    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            data={"raw_text": "Còn 3 cơm tấm"},
            headers=partner["headers"],
        )

    assert response.status_code == 404
    assert fake_client.calls == []


@pytest.mark.parametrize(
    "fake_client",
    [
        None,
        FakeGeminiClient(exc=TimeoutError("upstream timeout")),
        FakeGeminiClient(response=FakeResponse(parsed=None, text="{bad-json")),
    ],
)
async def test_parse_dish_nlp_returns_503_on_gemini_unavailability(
    client: AsyncClient,
    db_session: AsyncSession,
    store_partner: dict[str, Any],
    fake_client: FakeGeminiClient | None,
) -> None:
    with _override_ml_service(db_session, fake_client):
        response = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            data={"raw_text": "Còn 3 cơm tấm"},
            headers=store_partner["headers"],
        )

    assert response.status_code == 503


async def test_legacy_prototype_quick_post_routes_are_removed_404(
    client: AsyncClient,
    store_partner: dict[str, Any],
) -> None:
    extract_res = await client.post(
        "/api/v1/quick-post/extract",
        params={"text_input": "Còn 3 cơm tấm"},
        headers=store_partner["headers"],
    )
    self_test_res = await client.get("/api/v1/quick-post/allergen-filter/test")

    assert extract_res.status_code == 404
    assert self_test_res.status_code == 404


# ==============================================================================
# E2E Handoff: POST /api/v1/ml/parse-dish-nlp -> POST /api/v1/dishes/batch (201)
# ==============================================================================
async def test_parse_dish_nlp_output_hands_off_directly_to_dishes_batch_201(
    client: AsyncClient,
    db_session: AsyncSession,
    store_partner: dict[str, Any],
) -> None:
    store: Store = store_partner["store"]
    com_suon = await _create_menu_item(
        db_session,
        store,
        name="Cơm sườn bì chả",
        original_price=Decimal("45000.00"),
    )
    bun_thit = await _create_menu_item(
        db_session,
        store,
        name="Bún thịt nướng",
        original_price=Decimal("40000.00"),
        category=ItemCategory.NOODLES,
    )

    extracted = QuickPostExtractionResponse(
        pickup_start="18:00:00",
        pickup_end="20:30:00",
        items=[
            SurplusDishItem(
                matched_menu_id=com_suon.id,
                dish_name="Cơm sườn bì chả",
                quantity=5,
                original_price=None,
                override_discounted_price=None,
                allergens=[
                    NLPAllergenWarning(
                        allergen=EUAllergen.EGGS,
                        risk_level=AllergenRiskLevel.HIGH,
                        source=DetectionSource.INFERRED,
                        reason="Chả trứng có trứng",
                    )
                ],
                dietary_notes=["Có mỡ hành (Allium)"],
            ),
            SurplusDishItem(
                matched_menu_id=bun_thit.id,
                dish_name="Bún thịt nướng",
                quantity=3,
                original_price=40000.0,
                override_discounted_price=20000.0,
                allergens=[
                    NLPAllergenWarning(
                        allergen=EUAllergen.PEANUTS,
                        risk_level=AllergenRiskLevel.HIGH,
                        source=DetectionSource.EXPLICIT,
                        reason="Có đậu phộng rang",
                    )
                ],
                dietary_notes=["Có đậu phộng"],
            ),
        ],
    )
    fake_client = FakeGeminiClient(response=FakeResponse(parsed=extracted))

    with _override_ml_service(db_session, fake_client):
        parse_res = await client.post(
            "/api/v1/ml/parse-dish-nlp",
            data={"raw_text": "Còn 5 cơm sườn chả, 3 bún thịt nướng 20k từ 6h đến 8h30 tối"},
            headers=store_partner["headers"],
        )

    assert parse_res.status_code == 200
    parsed_body = parse_res.json()

    batch_payload = {
        "pickup_start_time": parsed_body["pickup_start"],
        "pickup_end_time": parsed_body["pickup_end"],
        "dishes": [
            {
                "menu_item_id": item["matched_menu_id"],
                "quantity": item["quantity"],
                "override_discounted_price": item["override_discounted_price"],
                "allergens": item["allergens"],
                "dietary_notes": item["dietary_notes"],
            }
            for item in parsed_body["items"]
        ],
    }

    publish_res = await client.post(
        "/api/v1/dishes/batch",
        json=batch_payload,
        headers=store_partner["headers"],
    )

    assert publish_res.status_code == 201
    published = publish_res.json()
    assert published["created_count"] == 2
    assert len(published["dishes"]) == 2
