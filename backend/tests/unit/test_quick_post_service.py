"""TDD unit tests for AI Feature 1 — QuickPostService (specs/002-ai-quick-post-nlp).

Covers:
- Phase 2 (T003): Domain exceptions, Gemini adapter, fault-tolerant factory.
- Phase 3 (T005–T006): Vietnamese text extraction, 2-tier EU FIC allergens
  (EXPLICIT vs INFERRED without consumer filtering), authoritative Asia/Ho_Chi_Minh
  server time, Menu-Catalog Grounding, price inheritance, anti-hallucination UUID
  validation, >50-item catalog pruning, and allergen deduplication.
- Phase 4 (T010): Native inline audio ingestion (`types.Part.from_bytes`), MIME
  normalization/extension fallback, and 413/415/422 validation before Gemini call.
- Phase 5 (T014): Store/KYC guards and graceful unavailability error translation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.quick_post_service as quick_post_module
from app.core.config import settings
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
from app.services.quick_post_service import QuickPostService, build_quick_post_service

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
MAX_AUDIO_BYTES = 10 * 1024 * 1024


def _require_symbol(name: str) -> Any:
    """Fetch a TDD target symbol from quick_post_service or fail cleanly (RED)."""
    symbol = getattr(quick_post_module, name, None)
    if symbol is None:
        pytest.fail(
            f"TDD RED: `{name}` chưa được định nghĩa trong `app.services.quick_post_service`."
        )
    return symbol


class FakeResponse:
    """Minimal stand-in for a google-genai GenerateContentResponse."""

    def __init__(self, parsed: Any = None, text: str | None = None) -> None:
        self.parsed = parsed
        self.text = text


class FakeGeminiClient:
    """Deterministic fake async Gemini client that records every call."""

    def __init__(
        self,
        response: Any = None,
        exc: Exception | None = None,
    ) -> None:
        self._response = response
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    async def generate_content(
        self,
        *,
        model: str,
        contents: Any,
        config: Any,
    ) -> Any:
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self._exc is not None:
            raise self._exc
        return self._response


def _extract_prompt_text(contents: Any) -> str:
    """Flatten string parts from Gemini `contents` for prompt assertions."""
    if isinstance(contents, str):
        return contents
    if isinstance(contents, list):
        parts: list[str] = []
        for item in contents:
            if isinstance(item, str):
                parts.append(item)
            elif getattr(item, "text", None):
                parts.append(str(item.text))
        return "\n".join(parts)
    return str(contents)


def _extract_binary_parts(contents: Any) -> list[types.Part]:
    """Return all inline-binary `types.Part` objects sent to Gemini."""
    if not isinstance(contents, list):
        return []
    return [
        part for part in contents if isinstance(part, types.Part) and part.inline_data is not None
    ]


async def _seed_menu_item(
    db_session: AsyncSession,
    store_id: uuid.UUID,
    *,
    name: str,
    original_price: Decimal = Decimal("45000.00"),
    category: ItemCategory = ItemCategory.RICE,
    standard_ingredients: list[str] | None = None,
    base_allergens: list[str] | None = None,
    is_active: bool = True,
) -> MenuItem:
    item = MenuItem(
        store_id=store_id,
        name=name,
        description=f"Mô tả {name}",
        category=category,
        original_price=original_price,
        image_url=f"https://cdn.ecobite.vn/{uuid.uuid4().hex[:8]}.jpg",
        standard_ingredients=standard_ingredients or ["gạo", "thịt heo"],
        base_allergens=base_allergens or [],
        dietary_type=DietaryType.NON_VEGAN,
        is_active=is_active,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _seed_partner_with_store_status(
    db_session: AsyncSession,
    *,
    email: str,
    kyc_status: KycStatus | None,
) -> User:
    user = User(
        email=email,
        hashed_password="not-used-by-tests",
        full_name="Partner Test",
        role=UserRole.STORE_PARTNER,
    )
    db_session.add(user)
    await db_session.flush()
    if kyc_status is not None:
        store = Store(
            owner_id=user.id,
            name=f"Store {kyc_status.value}",
            address="789 Test Street",
            location="POINT(106.7 10.77)",
            kyc_status=kyc_status,
        )
        db_session.add(store)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ==============================================================================
# Phase 2 (T003): Foundation & Factory
# ==============================================================================
class TestQuickPostFoundation:
    def test_domain_exceptions_protocol_and_adapter_exist(self) -> None:
        input_err = _require_symbol("QuickPostInputError")
        unavail_err = _require_symbol("QuickPostUnavailableError")
        not_found_err = _require_symbol("QuickPostStoreNotFoundError")
        not_approved_err = _require_symbol("QuickPostStoreNotApprovedError")
        _require_symbol("GeminiQuickPostClient")
        _require_symbol("GoogleGenAIQuickPostAdapter")

        assert issubclass(input_err, ValueError)
        assert issubclass(unavail_err, RuntimeError)
        assert issubclass(not_found_err, LookupError)
        assert issubclass(not_approved_err, PermissionError)

        err = input_err("File quá lớn", status_code=413)
        assert err.status_code == 413

    def test_build_quick_post_service_degrades_when_gemini_key_missing(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "GEMINI_TEST_API", "")
        monkeypatch.setattr(settings, "GEMINI_DEMO_API", "")
        monkeypatch.setattr(settings, "GEMINI_USE_DEMO_KEY", False)

        svc = build_quick_post_service(db_session)

        assert isinstance(svc, QuickPostService)
        assert svc.gemini_client is None

    def test_build_quick_post_service_wires_adapter_when_key_configured(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        adapter_cls = _require_symbol("GoogleGenAIQuickPostAdapter")
        monkeypatch.setattr(settings, "GEMINI_TEST_API", "test-api-key-123")
        monkeypatch.setattr(settings, "GEMINI_USE_DEMO_KEY", False)

        svc = build_quick_post_service(db_session)

        assert isinstance(svc, QuickPostService)
        assert isinstance(svc.gemini_client, adapter_cls)


# ==============================================================================
# Phase 3 (T005 & T006): US1 Text Extraction, Menu Grounding & 2-Tier Allergens
# ==============================================================================
class TestQuickPostTextAndMenuGrounding:
    async def test_multi_dish_text_preserves_all_dishes_two_tier_allergens_and_prices(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        store: Store = store_partner["store"]
        owner: User = store_partner["user"]

        com_suon = await _seed_menu_item(
            db_session,
            store.id,
            name="Cơm sườn bì chả",
            original_price=Decimal("45000.00"),
            standard_ingredients=["cơm tấm", "sườn nướng", "chả trứng", "nước mắm"],
            base_allergens=["Eggs (Trứng)", "Fish (Cá/Nước mắm)"],
        )
        bun_thit = await _seed_menu_item(
            db_session,
            store.id,
            name="Bún thịt nướng",
            original_price=Decimal("40000.00"),
            category=ItemCategory.NOODLES,
            standard_ingredients=["bún", "thịt nướng", "đậu phộng", "nước mắm"],
            base_allergens=["Peanuts (Đậu phộng)", "Fish (Cá/Nước mắm)"],
        )

        extracted = QuickPostExtractionResponse(
            pickup_start="13:55:00",
            pickup_end="15:00:00",
            items=[
                SurplusDishItem(
                    matched_menu_id=com_suon.id,
                    dish_name="Cơm sườn bì chả",
                    quantity=5,
                    original_price=None,  # Must inherit 45000.0 from catalog
                    override_discounted_price=None,  # Rule-based pricing
                    side_components=["mỡ hành", "dưa chua"],
                    allergens=[
                        NLPAllergenWarning(
                            allergen=EUAllergen.EGGS,
                            risk_level=AllergenRiskLevel.HIGH,
                            source=DetectionSource.INFERRED,
                            reason="Chả trứng có trứng vịt",
                        ),
                        NLPAllergenWarning(
                            allergen=EUAllergen.FISH,
                            risk_level=AllergenRiskLevel.HIGH,
                            source=DetectionSource.INFERRED,
                            reason="Nước mắm pha từ cá cơm",
                        ),
                    ],
                    dietary_notes=["Có mỡ hành (Allium)"],
                ),
                SurplusDishItem(
                    matched_menu_id=bun_thit.id,
                    dish_name="Bún thịt nướng",
                    quantity=3,
                    original_price=40000.0,
                    override_discounted_price=20000.0,
                    side_components=["đồ chua"],
                    allergens=[
                        NLPAllergenWarning(
                            allergen=EUAllergen.PEANUTS,
                            risk_level=AllergenRiskLevel.HIGH,
                            source=DetectionSource.EXPLICIT,
                            reason="Chủ quán nêu rõ có đậu phộng rang",
                        ),
                        NLPAllergenWarning(
                            allergen=EUAllergen.FISH,
                            risk_level=AllergenRiskLevel.HIGH,
                            source=DetectionSource.INFERRED,
                            reason="Nước mắm ăn kèm từ cá",
                        ),
                    ],
                    dietary_notes=["Có đậu phộng"],
                ),
            ],
        )

        fake_client = FakeGeminiClient(response=FakeResponse(parsed=extracted))
        service = QuickPostService(db_session, gemini_client=fake_client)
        ref_time = datetime(2026, 11, 28, 13, 55, 0, tzinfo=VN_TZ)

        result = await service.parse_dish_nlp(
            owner_id=owner.id,
            raw_text=(
                "Còn 5 cơm sườn chả, 3 bún thịt nướng có đậu phộng rang, "
                "xả từ giờ đến 3h chiều, bún bán 20 cành"
            ),
            reference_time=ref_time,
        )

        assert isinstance(result, QuickPostExtractionResponse)
        assert result.pickup_start == "13:55:00"
        assert result.pickup_end == "15:00:00"
        # All dishes MUST be preserved — never consumer-filtered during Quick-Post.
        assert len(result.items) == 2

        item1, item2 = result.items
        assert item1.matched_menu_id == com_suon.id
        assert item1.original_price == pytest.approx(45000.0)
        assert item1.override_discounted_price is None
        assert {a.source for a in item1.allergens} == {"INFERRED"}

        assert item2.matched_menu_id == bun_thit.id
        assert item2.override_discounted_price == pytest.approx(20000.0)
        assert {a.source for a in item2.allergens} == {"EXPLICIT", "INFERRED"}

        # Prompt must include authoritative Asia/Ho_Chi_Minh time & store catalog IDs.
        assert len(fake_client.calls) == 1
        prompt_text = _extract_prompt_text(fake_client.calls[0]["contents"])
        assert "13:55:00" in prompt_text
        assert str(com_suon.id) in prompt_text
        assert str(bun_thit.id) in prompt_text

    async def test_post_validation_clears_fabricated_uuid_and_appends_warning(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        store: Store = store_partner["store"]
        owner: User = store_partner["user"]
        await _seed_menu_item(db_session, store.id, name="Bánh mì thịt")

        fabricated_id = uuid.uuid4()
        extracted = QuickPostExtractionResponse(
            pickup_start="17:00:00",
            pickup_end="19:00:00",
            items=[
                SurplusDishItem(
                    matched_menu_id=fabricated_id,
                    dish_name="Bánh bao đặc biệt",
                    quantity=4,
                )
            ],
        )
        service = QuickPostService(
            db_session,
            gemini_client=FakeGeminiClient(response=FakeResponse(parsed=extracted)),
        )

        result = await service.parse_dish_nlp(
            owner_id=owner.id,
            raw_text="Còn 4 bánh bao đặc biệt từ 5h đến 7h tối",
        )

        item = result.items[0]
        assert item.matched_menu_id is None
        assert len(item.missing_fields_warning) >= 1

    async def test_post_validation_rejects_cross_store_and_inactive_menu_uuid(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
        other_store_partner: dict[str, Any],
    ) -> None:
        owner: User = store_partner["user"]
        own_store: Store = store_partner["store"]
        other_store: Store = other_store_partner["store"]

        other_menu = await _seed_menu_item(db_session, other_store.id, name="Phở bò quán khác")
        inactive_menu = await _seed_menu_item(
            db_session,
            own_store.id,
            name="Món đã ngưng bán",
            is_active=False,
        )

        extracted = QuickPostExtractionResponse(
            pickup_start="18:00:00",
            pickup_end="20:00:00",
            items=[
                SurplusDishItem(matched_menu_id=other_menu.id, dish_name="Phở bò", quantity=2),
                SurplusDishItem(
                    matched_menu_id=inactive_menu.id,
                    dish_name="Món cũ",
                    quantity=1,
                ),
            ],
        )
        service = QuickPostService(
            db_session,
            gemini_client=FakeGeminiClient(response=FakeResponse(parsed=extracted)),
        )

        result = await service.parse_dish_nlp(
            owner_id=owner.id,
            raw_text="Còn 2 phở bò và 1 món cũ từ 6h đến 8h tối",
        )

        for item in result.items:
            assert item.matched_menu_id is None
            assert len(item.missing_fields_warning) >= 1

    async def test_empty_store_catalog_succeeds_with_warning(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        owner: User = store_partner["user"]
        extracted = QuickPostExtractionResponse(
            pickup_start="18:00:00",
            pickup_end="20:00:00",
            items=[SurplusDishItem(matched_menu_id=None, dish_name="Bánh su kem", quantity=6)],
        )
        service = QuickPostService(
            db_session,
            gemini_client=FakeGeminiClient(response=FakeResponse(parsed=extracted)),
        )

        result = await service.parse_dish_nlp(
            owner_id=owner.id,
            raw_text="Còn 6 bánh su kem từ 6h đến 8h tối",
        )

        assert result.items[0].matched_menu_id is None
        assert len(result.items[0].missing_fields_warning) >= 1

    async def test_large_catalog_caps_prompt_to_50_but_validates_full_active_catalog(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        store: Store = store_partner["store"]
        owner: User = store_partner["user"]

        seeded: list[MenuItem] = []
        for idx in range(55):
            item = MenuItem(
                store_id=store.id,
                name=f"Món số {idx:02d}",
                category=ItemCategory.RICE,
                original_price=Decimal("35000.00") + Decimal(idx * 1000),
                image_url=f"https://cdn.ecobite.vn/item-{idx}.jpg",
                standard_ingredients=["cơm"],
                base_allergens=[],
                dietary_type=DietaryType.NON_VEGAN,
                is_active=True,
            )
            db_session.add(item)
            seeded.append(item)
        await db_session.commit()
        for item in seeded:
            await db_session.refresh(item)

        # Pick an item from the catalog; even if pruned from prompt, full-catalog
        # post-validation MUST still recognize it as valid and inherit its price.
        target_item = seeded[0]
        extracted = QuickPostExtractionResponse(
            pickup_start="18:00:00",
            pickup_end="20:00:00",
            items=[
                SurplusDishItem(
                    matched_menu_id=target_item.id,
                    dish_name=target_item.name,
                    quantity=2,
                    original_price=None,
                )
            ],
        )
        fake_client = FakeGeminiClient(response=FakeResponse(parsed=extracted))
        service = QuickPostService(db_session, gemini_client=fake_client)

        result = await service.parse_dish_nlp(
            owner_id=owner.id,
            raw_text="Còn 2 suất ăn cuối ca từ 6h đến 8h tối",
        )

        prompt_text = _extract_prompt_text(fake_client.calls[0]["contents"])
        included_count = sum(1 for item in seeded if str(item.id) in prompt_text)
        assert included_count <= 50

        assert result.items[0].matched_menu_id == target_item.id
        assert result.items[0].original_price == pytest.approx(float(target_item.original_price))

    async def test_allergen_deduplication_prefers_explicit_over_inferred(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        store: Store = store_partner["store"]
        owner: User = store_partner["user"]
        menu_item = await _seed_menu_item(db_session, store.id, name="Bún thịt nướng")

        extracted = QuickPostExtractionResponse(
            pickup_start="17:00:00",
            pickup_end="19:00:00",
            items=[
                SurplusDishItem(
                    matched_menu_id=menu_item.id,
                    dish_name="Bún thịt nướng",
                    quantity=3,
                    allergens=[
                        NLPAllergenWarning(
                            allergen=EUAllergen.PEANUTS,
                            risk_level=AllergenRiskLevel.MEDIUM,
                            source=DetectionSource.INFERRED,
                            reason="Suy luận bún thịt nướng hay có đậu phộng",
                        ),
                        NLPAllergenWarning(
                            allergen=EUAllergen.PEANUTS,
                            risk_level=AllergenRiskLevel.HIGH,
                            source=DetectionSource.EXPLICIT,
                            reason="Chủ quán nói rõ có đậu phộng rang",
                        ),
                        NLPAllergenWarning(
                            allergen=EUAllergen.FISH,
                            risk_level=AllergenRiskLevel.HIGH,
                            source=DetectionSource.INFERRED,
                            reason="Nước mắm cá",
                        ),
                    ],
                )
            ],
        )
        service = QuickPostService(
            db_session,
            gemini_client=FakeGeminiClient(response=FakeResponse(parsed=extracted)),
        )

        result = await service.parse_dish_nlp(
            owner_id=owner.id,
            raw_text="3 bún thịt nướng có đậu phộng rang",
        )

        allergens = result.items[0].allergens
        assert len(allergens) == 2
        peanut_warnings = [a for a in allergens if a.allergen == EUAllergen.PEANUTS.value]
        assert len(peanut_warnings) == 1
        assert peanut_warnings[0].source == DetectionSource.EXPLICIT.value


# ==============================================================================
# Phase 4 (T010): US2 Native Multimodal Audio Ingestion & Validation
# ==============================================================================
class TestQuickPostNativeAudio:
    @pytest.mark.parametrize(
        ("input_mime", "filename", "expected_mime"),
        [
            ("audio/m4a", "clip.m4a", "audio/mp4"),
            ("audio/x-m4a", "clip.m4a", "audio/mp4"),
            ("audio/webm;codecs=opus", "clip.webm", "audio/webm"),
            ("audio/mpeg", "clip.mp3", "audio/mpeg"),
            ("audio/x-wav", "clip.wav", "audio/wav"),
            ("application/octet-stream", "voice_note.wav", "audio/wav"),
        ],
    )
    async def test_valid_audio_normalizes_mime_and_sends_inline_part(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
        input_mime: str,
        filename: str,
        expected_mime: str,
    ) -> None:
        owner: User = store_partner["user"]
        audio_payload = b"RIFF-fake-vietnamese-voice-clip"
        extracted = QuickPostExtractionResponse(
            pickup_start="18:00:00",
            pickup_end="20:00:00",
            items=[SurplusDishItem(dish_name="Bánh mì pate", quantity=4)],
        )
        fake_client = FakeGeminiClient(response=FakeResponse(parsed=extracted))
        service = QuickPostService(db_session, gemini_client=fake_client)

        result = await service.parse_dish_nlp(
            owner_id=owner.id,
            audio_bytes=audio_payload,
            audio_mime_type=input_mime,
            audio_filename=filename,
        )

        assert result.items[0].dish_name == "Bánh mì pate"
        assert len(fake_client.calls) == 1
        binary_parts = _extract_binary_parts(fake_client.calls[0]["contents"])
        assert len(binary_parts) == 1
        assert binary_parts[0].inline_data is not None
        assert binary_parts[0].inline_data.data == audio_payload
        assert binary_parts[0].inline_data.mime_type == expected_mime

    async def test_audio_plus_raw_text_includes_both_in_gemini_request(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        owner: User = store_partner["user"]
        audio_payload = b"fake-webm-audio"
        extracted = QuickPostExtractionResponse(
            pickup_start="18:00:00",
            pickup_end="20:30:00",
            items=[SurplusDishItem(dish_name="Cơm gà", quantity=3)],
        )
        fake_client = FakeGeminiClient(response=FakeResponse(parsed=extracted))
        service = QuickPostService(db_session, gemini_client=fake_client)

        await service.parse_dish_nlp(
            owner_id=owner.id,
            raw_text="Nhớ ghi chú không hành lá",
            audio_bytes=audio_payload,
            audio_mime_type="audio/webm;codecs=opus",
            audio_filename="note.webm",
        )

        contents = fake_client.calls[0]["contents"]
        assert "Nhớ ghi chú không hành lá" in _extract_prompt_text(contents)
        assert len(_extract_binary_parts(contents)) == 1

    async def test_rejects_empty_audio_with_422_before_calling_gemini(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        input_err = _require_symbol("QuickPostInputError")
        fake_client = FakeGeminiClient()
        service = QuickPostService(db_session, gemini_client=fake_client)

        with pytest.raises(input_err) as exc_info:
            await service.parse_dish_nlp(
                owner_id=store_partner["user"].id,
                audio_bytes=b"",
                audio_mime_type="audio/wav",
                audio_filename="empty.wav",
            )

        assert exc_info.value.status_code == 422
        assert fake_client.calls == []

    async def test_rejects_oversized_audio_over_10mb_with_413_before_calling_gemini(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        input_err = _require_symbol("QuickPostInputError")
        fake_client = FakeGeminiClient()
        service = QuickPostService(db_session, gemini_client=fake_client)

        with pytest.raises(input_err) as exc_info:
            await service.parse_dish_nlp(
                owner_id=store_partner["user"].id,
                audio_bytes=b"a" * (MAX_AUDIO_BYTES + 1),
                audio_mime_type="audio/mpeg",
                audio_filename="huge.mp3",
            )

        assert exc_info.value.status_code == 413
        assert fake_client.calls == []

    async def test_rejects_unsupported_audio_mime_with_415_before_calling_gemini(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        input_err = _require_symbol("QuickPostInputError")
        fake_client = FakeGeminiClient()
        service = QuickPostService(db_session, gemini_client=fake_client)

        with pytest.raises(input_err) as exc_info:
            await service.parse_dish_nlp(
                owner_id=store_partner["user"].id,
                audio_bytes=b"not-audio",
                audio_mime_type="image/png",
                audio_filename="photo.png",
            )

        assert exc_info.value.status_code == 415
        assert fake_client.calls == []

    async def test_rejects_missing_both_text_and_audio_with_422(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        input_err = _require_symbol("QuickPostInputError")
        fake_client = FakeGeminiClient()
        service = QuickPostService(db_session, gemini_client=fake_client)

        with pytest.raises(input_err) as exc_info:
            await service.parse_dish_nlp(
                owner_id=store_partner["user"].id,
                raw_text="   ",
                audio_bytes=None,
            )

        assert exc_info.value.status_code == 422
        assert fake_client.calls == []


# ==============================================================================
# Phase 5 (T014): US3 Store/KYC Guards & Failure Mode Translation
# ==============================================================================
class TestQuickPostGuardsAndFailures:
    async def test_partner_without_store_raises_not_found(
        self,
        db_session: AsyncSession,
    ) -> None:
        not_found_err = _require_symbol("QuickPostStoreNotFoundError")
        partner = await _seed_partner_with_store_status(
            db_session,
            email="nostore@ecobite.vn",
            kyc_status=None,
        )
        fake_client = FakeGeminiClient()
        service = QuickPostService(db_session, gemini_client=fake_client)

        with pytest.raises(not_found_err):
            await service.parse_dish_nlp(owner_id=partner.id, raw_text="Còn 2 cơm tấm")

        assert fake_client.calls == []

    @pytest.mark.parametrize("kyc_status", [KycStatus.PENDING, KycStatus.REJECTED])
    async def test_unapproved_store_raises_not_approved(
        self,
        db_session: AsyncSession,
        kyc_status: KycStatus,
    ) -> None:
        not_approved_err = _require_symbol("QuickPostStoreNotApprovedError")
        partner = await _seed_partner_with_store_status(
            db_session,
            email=f"{kyc_status.value.lower()}@ecobite.vn",
            kyc_status=kyc_status,
        )
        fake_client = FakeGeminiClient()
        service = QuickPostService(db_session, gemini_client=fake_client)

        with pytest.raises(not_approved_err):
            await service.parse_dish_nlp(owner_id=partner.id, raw_text="Còn 2 cơm tấm")

        assert fake_client.calls == []

    async def test_none_gemini_client_raises_unavailable_error(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        unavail_err = _require_symbol("QuickPostUnavailableError")
        service = QuickPostService(db_session, gemini_client=None)

        with pytest.raises(unavail_err):
            await service.parse_dish_nlp(
                owner_id=store_partner["user"].id,
                raw_text="Còn 3 bánh mì",
            )

    @pytest.mark.parametrize(
        "exc",
        [TimeoutError("Gemini request timed out"), RuntimeError("503 Service Unavailable")],
    )
    async def test_gemini_timeout_or_sdk_error_raises_unavailable_error(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
        exc: Exception,
    ) -> None:
        unavail_err = _require_symbol("QuickPostUnavailableError")
        service = QuickPostService(db_session, gemini_client=FakeGeminiClient(exc=exc))

        with pytest.raises(unavail_err):
            await service.parse_dish_nlp(
                owner_id=store_partner["user"].id,
                raw_text="Còn 3 bánh mì",
            )

    async def test_invalid_gemini_json_raises_unavailable_error(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
    ) -> None:
        unavail_err = _require_symbol("QuickPostUnavailableError")
        service = QuickPostService(
            db_session,
            gemini_client=FakeGeminiClient(response=FakeResponse(parsed=None, text="not-json")),
        )

        with pytest.raises(unavail_err):
            await service.parse_dish_nlp(
                owner_id=store_partner["user"].id,
                raw_text="Còn 3 bánh mì",
            )

    @pytest.mark.parametrize(
        ("pickup_start", "pickup_end"),
        [("18:00:00", "17:00:00"), ("18:00:00", "18:00:00")],
    )
    async def test_inverted_or_equal_pickup_window_raises_unavailable_error(
        self,
        db_session: AsyncSession,
        store_partner: dict[str, Any],
        pickup_start: str,
        pickup_end: str,
    ) -> None:
        unavail_err = _require_symbol("QuickPostUnavailableError")
        extracted = QuickPostExtractionResponse(
            pickup_start=pickup_start,
            pickup_end=pickup_end,
            items=[SurplusDishItem(dish_name="Cơm gà", quantity=2)],
        )
        service = QuickPostService(
            db_session,
            gemini_client=FakeGeminiClient(response=FakeResponse(parsed=extracted)),
        )

        with pytest.raises(unavail_err):
            await service.parse_dish_nlp(
                owner_id=store_partner["user"].id,
                raw_text="Còn 2 cơm gà",
            )
