# Data Model: AI Feature 1 — Batch Quick-Post Multimodal Assistant

**Feature**: `002-ai-quick-post-nlp` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

Quick-Post is a **read-only extraction pipeline**: it introduces **no new database tables or Alembic migrations**. It reads existing `Store` and `MenuItem` ORM entities for authorization and Menu-Catalog Grounding, validates Gemini 2.5 Flash outputs against Pydantic v2 schemas in `backend/app/schemas/nlp.py`, and produces drafts that map directly into `DishBatchPublish` (`backend/app/schemas/dish.py`).

---

## 1. Existing Persistent Entities (Read-Only Dependencies)

### `Store` (`backend/app/models/store.py`)
- **Accessed via**: `store_repo.get_store_by_owner_id(db, owner_id)`
- **Key fields read**:
  - `id: UUID` — store primary key used to scope menu catalog lookup.
  - `owner_id: UUID` — matched against authenticated `User.id`.
  - `kyc_status: KycStatus` — MUST equal `KycStatus.APPROVED` (otherwise rejected with `403`).

### `MenuItem` (`backend/app/models/menu_item.py`)
- **Accessed via**: `menu_repo.list_by_store(db, store.id, active_only=True)`
- **Key fields read for grounding & post-validation**:
  - `id: UUID` — authoritative valid set for verifying `matched_menu_id`.
  - `store_id: UUID` — guarantees strict store isolation (cross-store UUIDs rejected).
  - `name: str` — canonical dish name provided in prompt context.
  - `original_price: Decimal` — authoritative retail price inherited when extracted `original_price` is `None`.
  - `standard_ingredients: list[str]` — grounding hint for implicit allergen reasoning.
  - `base_allergens: list[str]` — baseline allergen hints from the store's catalog.
  - `is_active: bool` — only `True` items are eligible for grounding.

---

## 2. Transient Extraction Schemas (`backend/app/schemas/nlp.py` — Existing)

### Enumerations

1. **`EUAllergen(StrEnum)`** — 14 mandatory EU FIC allergen categories (bilingual EN/VI values):
   - `"Peanuts (Đậu phộng)"`, `"Soybeans (Đậu nành)"`, `"Eggs (Trứng)"`, `"Milk/Dairy (Sữa)"`, `"Fish (Cá/Nước mắm)"`, `"Crustaceans (Tôm/Cua)"`, `"Molluscs (Nhuyễn thể: Nghêu/Sò/Ốc)"`, `"Cereals containing gluten (Bột mì/Bánh mì)"`, `"Tree nuts (Hạt cây: Điều, Hạnh nhân...)"`, `"Sesame (Mè/Vừng)"`, `"Celery (Cần tây)"`, `"Mustard (Mù tạt)"`, `"Sulphites (Chất bảo quản Sulfit)"`, `"Lupin (Đậu Lupin)"`.
2. **`DetectionSource(StrEnum)`**:
   - `"EXPLICIT"` — directly stated by Store Partner in voice/text.
   - `"INFERRED"` — inferred by Gemini 2.5 Flash from Vietnamese culinary knowledge or base menu ingredients.
3. **`AllergenRiskLevel(StrEnum)`**:
   - `"HIGH"`, `"MEDIUM"`, `"LOW"`.

### `NLPAllergenWarning`
| Field | Type | Constraints |
| :--- | :--- | :--- |
| `allergen` | `EUAllergen` | Required; must be one of the 14 EU FIC enum values (`use_enum_values=True`). |
| `risk_level` | `AllergenRiskLevel` | Default `"HIGH"`; `"HIGH" \| "MEDIUM" \| "LOW"`. |
| `source` | `DetectionSource` | Required; `"EXPLICIT"` or `"INFERRED"`. |
| `reason` | `str` | Required; concise Vietnamese explanation (e.g., `"Chả chưng có trứng vịt"`). |

### `SurplusDishItem`
| Field | Type | Constraints & Post-Validation Rules |
| :--- | :--- | :--- |
| `matched_menu_id` | `UUID \| None` | Default `None`. Post-validation MUST verify membership in the store's active `MenuItem` IDs; otherwise reset to `None` + append warning. |
| `dish_name` | `str` | Required; `min_length=1`, `max_length=255`. |
| `quantity` | `int` | Required; strictly `gt=0`. |
| `original_price` | `float \| None` | Default `None`; when set, strictly `gt=0`. Post-validation inherits `float(menu_item.original_price)` if `None` and `matched_menu_id` is valid. |
| `override_discounted_price` | `float \| None` | Default `None`; when set, strictly `gt=0`. Remains `None` unless partner specifies a fixed clearance price. |
| `side_components` | `list[str]` | Default `[]`. |
| `allergens` | `list[NLPAllergenWarning]` | Default `[]`. Post-validation deduplicates by `allergen`, prioritizing `EXPLICIT` over `INFERRED`. |
| `dietary_notes` | `list[str]` | Default `[]`. |
| `missing_fields_warning` | `list[str]` | Default `[]`. Receives deterministic warnings (unmatched menu item, empty catalog, ambiguous input). |

### `QuickPostExtractionResponse` (Root Schema)
| Field | Type | Constraints & Validation Rules |
| :--- | :--- | :--- |
| `pickup_start` | `str` | Required; normalized to `"HH:MM:SS"` (`00:00:00`–`23:59:59`) via `validate_time_format`. |
| `pickup_end` | `str` | Required; normalized to `"HH:MM:SS"` (`00:00:00`–`23:59:59`) via `validate_time_format`. Service post-validation verifies `time.fromisoformat(pickup_end) > time.fromisoformat(pickup_start)`. |
| `items` | `list[SurplusDishItem]` | Required; `min_length=1`. |

---

## 3. Request Input Constraints (`POST /api/v1/ml/parse-dish-nlp`)

| Form Field | Type | Constraints |
| :--- | :--- | :--- |
| `audio_file` | `UploadFile \| None` | Optional; if provided, MUST be non-empty (`> 0` bytes), `<= 10_485_760` bytes (10 MB), and normalized MIME in `{"audio/mp4", "audio/m4a", "audio/x-m4a", "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/webm"}` (or matching extension `.m4a`, `.mp3`, `.wav`, `.webm` when MIME is generic). |
| `raw_text` | `str \| None` | Optional; trimmed of leading/trailing whitespace. At least one of `audio_file` or non-blank `raw_text` MUST be supplied (`422` if both missing/blank). |
| `current_server_time` | `str \| None` | Optional legacy compatibility form field; ignored by the server in favor of authoritative `datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))` (Constitution Principle VI). |

---

## 4. Service Domain Exceptions (`backend/app/services/quick_post_service.py`)

- **`QuickPostInputError(ValueError)`**: Raised when neither `raw_text` nor `audio_bytes` is provided, or when audio MIME/size constraints fail (mapped to `413` / `415` / `422` at router layer).
- **`QuickPostUnavailableError(RuntimeError)`**: Raised when Gemini credentials are not configured, Gemini times out / errors, or extracted output fails schema / pickup-window post-validation (mapped to `503 Service Unavailable` at router layer).

---

## 5. Handoff Mapping to `DishBatchPublish` (`POST /api/v1/dishes/batch`)

| `QuickPostExtractionResponse` Field | `DishBatchPublish` (`backend/app/schemas/dish.py`) Field | Notes |
| :--- | :--- | :--- |
| `pickup_start` (`"HH:MM:SS"`) | `pickup_start_time` (`datetime.time`) | Directly accepted by Pydantic v2 time parser. |
| `pickup_end` (`"HH:MM:SS"`) | `pickup_end_time` (`datetime.time`) | Guaranteed `> pickup_start_time` by post-validation. |
| `items[i].matched_menu_id` | `dishes[i].menu_item_id` | Must be non-null when publishing; partner picks from catalog if `None`. |
| `items[i].quantity` | `dishes[i].quantity` | Both enforce `gt=0`. |
| `items[i].override_discounted_price` | `dishes[i].override_discounted_price` | `None` triggers rule-based discounting in `DishService`. |
| `items[i].allergens` | `dishes[i].allergens` | Exact 4-field structural match (`allergen`, `risk_level`, `source`, `reason`). |
| `items[i].dietary_notes` | `dishes[i].dietary_notes` | Passed through verbatim. |

---

## 6. Offline Evaluation Fixture Schema (`ml/eval/golden_ai1_dataset.json`)

Each Golden Case object contains:
- `case_id: str` (e.g., `"AI1-01"`)
- `category: str` (`"text_single"`, `"text_batch"`, `"slang_price"`, `"relative_time"`, `"allergen_implicit"`, `"out_of_menu"`, `"ambiguous_qty"`, `"audio_clip"`)
- `raw_text: str | None`
- `audio_path: str | None` (relative path under `ml/eval/audio/`, e.g., `"audio/sample_01.m4a"`)
- `audio_mime_type: str | None`
- `reference_server_time: str` (ISO 8601 `+07:00`, e.g., `"2026-11-28T13:55:00+07:00"`)
- `menu_catalog: list[dict]` (mock active `MenuItem` records with deterministic UUIDs)
- `expected: dict` (`pickup_start`, `pickup_end`, `items` with expected `matched_menu_id`, `dish_name`, `quantity`, `original_price`, `override_discounted_price`, `expected_allergens` with `{allergen, source}`)
