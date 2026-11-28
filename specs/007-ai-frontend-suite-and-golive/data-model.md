# Data Model: AI Frontend Experience Suite, AI Safety QA & Release 1.0 Go-Live

**Feature**: `007-ai-frontend-suite-and-golive` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

Feature 007 introduces **zero new database tables or Alembic migrations**. It defines the shared **14 EU FIC allergen constant catalog**, the **TypeScript API DTOs and client-side state models** for Store Partner Quick-Post (`EC5-04`) and Consumer Smart Discovery & Preferences (`EC5-05`), and the **structured QA/UAT verification artifacts** (`EC5-06`, `EC5-07`), aligned 1-to-1 with existing backend Pydantic schemas (`backend/app/schemas/nlp.py`, `backend/app/schemas/dish.py`, `backend/app/schemas/user_preference.py`, and AI-2 recommendation/search schemas).

---

## 1. Shared 14 EU FIC Allergen Reference Catalog (`frontend/src/lib/allergens.ts`)

Every canonical `value` MUST match `EUAllergen` in `backend/app/schemas/nlp.py` verbatim so frontend checkboxes, Draft Card badges, and backend SQL hard filters speak one authoritative vocabulary:

| Key | Canonical Value (`EUAllergen`) | Short Vietnamese Label | Short English Label |
| :--- | :--- | :--- | :--- |
| `PEANUTS` | `"Peanuts (Đậu phộng)"` | Đậu phộng | Peanuts |
| `SOYBEANS` | `"Soybeans (Đậu nành)"` | Đậu nành | Soybeans |
| `EGGS` | `"Eggs (Trứng)"` | Trứng | Eggs |
| `MILK` | `"Milk/Dairy (Sữa)"` | Sữa / Chế phẩm sữa | Milk / Dairy |
| `FISH` | `"Fish (Cá/Nước mắm)"` | Cá / Nước mắm | Fish |
| `CRUSTACEANS` | `"Crustaceans (Tôm/Cua)"` | Tôm / Cua (Giáp xác) | Crustaceans |
| `MOLLUSCS` | `"Molluscs (Nhuyễn thể: Nghêu/Sò/Ốc)"` | Nghêu / Sò / Ốc | Molluscs |
| `GLUTEN` | `"Cereals containing gluten (Bột mì/Bánh mì)"` | Gluten / Bột mì | Gluten |
| `TREE_NUTS` | `"Tree nuts (Hạt cây: Điều, Hạnh nhân...)"` | Hạt cây (Điều, Hạnh nhân...) | Tree nuts |
| `SESAME` | `"Sesame (Mè/Vừng)"` | Mè / Vừng | Sesame |
| `CELERY` | `"Celery (Cần tây)"` | Cần tây | Celery |
| `MUSTARD` | `"Mustard (Mù tạt)"` | Mù tạt | Mustard |
| `SULPHITES` | `"Sulphites (Chất bảo quản Sulfit)"` | Chất bảo quản Sulfit | Sulphites |
| `LUPIN` | `"Lupin (Đậu Lupin)"` | Đậu Lupin | Lupin |

### Two-Tier Allergen Visual Mapping

| `DetectionSource` | Badge Variant (`Badge.tsx`) | Display Tag | Icon | Tooltip / Disclaimer Rule |
| :--- | :--- | :--- | :--- | :--- |
| `'EXPLICIT'` | `'danger'` (Red: `bg-red-100 text-red-800 border-red-200`) | `"Chủ quán báo"` | `ShieldAlert` | Shows `reason` on hover/click. |
| `'INFERRED'` | `'warning'` (Amber: `bg-amber-100 text-amber-800 border-amber-200`) | `"AI suy luận"` | `Sparkles` | Shows `reason` on hover/click + non-medical-certification disclaimer on Draft Card. |

---

## 2. Frontend TypeScript DTOs (`frontend/src/types/api.ts`)

### 2.1 AI Feature 1 — Quick-Post Extraction & Draft Editor (`EC5-04`)

| Type / Interface | Field | Type | Validation / Notes |
| :--- | :--- | :--- | :--- |
| `DetectionSource` | — | `'EXPLICIT' \| 'INFERRED'` | Maps 1-to-1 to `backend/app/schemas/nlp.py::DetectionSource`. |
| `AllergenRiskLevel` | — | `'HIGH' \| 'MEDIUM' \| 'LOW'` | Maps 1-to-1 to `AllergenRiskLevel`. |
| `NLPAllergenWarning` | `allergen` | `string` | One of the 14 canonical `EUAllergen` values. |
| | `risk_level` | `AllergenRiskLevel` | Default `'HIGH'`. |
| | `source` | `DetectionSource` | Determines Red vs Amber badge styling. |
| | `reason` | `string` | Concise Vietnamese rationale displayed in tooltip/detail. |
| `SurplusDishDraftItem` | `matched_menu_id` | `string \| null` | UUID of matched active `MenuItemResponse`, or `null` requiring dropdown selection. |
| | `dish_name` | `string` | Normalized dish name extracted by Gemini. |
| | `quantity` | `number` | Integer `> 0`. |
| | `original_price` | `number \| null` | Inherited from `menu_items` when matched. |
| | `override_discounted_price` | `number \| null` | Optional fixed clearance price; `null` triggers deterministic rule-based discount. |
| | `side_components` | `string[]` | Side toppings/condiments. |
| | `allergens` | `NLPAllergenWarning[]` | Deduplicated 2-tier EU FIC warnings. |
| | `dietary_notes` | `string[]` | Local Vietnamese dietary notes (e.g., `"Có mỡ hành (Allium)"`). |
| | `missing_fields_warning` | `string[]` | Rendered as prominent amber/red callouts on the Draft Card. |
| `QuickPostExtractionResponse` | `pickup_start` | `string` | `"HH:MM:SS"` anchored to `Asia/Ho_Chi_Minh`. |
| | `pickup_end` | `string` | `"HH:MM:SS"`, strictly `> pickup_start`. |
| | `items` | `SurplusDishDraftItem[]` | Non-empty (`length >= 1`). |

### 2.2 Client-Side Draft Editor State (`QuickPostDraftEditor`)

| Entity | Field | Type | Lifecycle / Constraint |
| :--- | :--- | :--- | :--- |
| `EditableDraftCard` | `client_id` | `string` | Ephemeral local key (`crypto.randomUUID()` or deterministic index) for stable React rendering during removal/editing. |
| | `matched_menu_id` | `string \| null` | MUST be non-null & present in store's `menuItems` before 1-Tap Batch Publish is enabled. |
| | `dish_name` | `string` | Display title (auto-syncs to selected `MenuItemResponse.name` when partner selects from dropdown). |
| | `quantity` | `number` | Editable integer (`>= 1`, `<= 200`). |
| | `original_price` | `number \| null` | Auto-updates from selected `MenuItemResponse.original_price`. |
| | `override_discounted_price` | `string` | Controlled text input; empty string serializes to `null`, positive number serializes to `number`. |
| | `allergens` | `NLPAllergenWarning[]` | Partner can remove false positives or append an `EXPLICIT` allergen before publishing. |
| | `dietary_notes` | `string[]` | Editable chip/comma list passed directly to `DishBatchPublishPayload`. |
| | `missing_fields_warning` | `string[]` | Cleared/recomputed dynamically once `matched_menu_id` is linked. |
| `VoiceRecorderState` | `status` | `'idle' \| 'recording' \| 'recorded' \| 'error'` | State machine transitions: `idle → recording → recorded → idle` (or `error`). |
| | `elapsedSeconds` | `number` | `0..60`; auto-stops at `60`. |
| | `audioBlob` | `Blob \| null` | Size validated `> 0` and `<= 10_485_760` bytes (10 MB). |
| | `mimeType` | `string` | Resolved supported MIME (`audio/webm;codecs=opus`, `audio/webm`, `audio/mp4`, or `audio/wav`). |
| | `errorCode` | `'PERMISSION_DENIED' \| 'NOT_SUPPORTED' \| 'NO_MICROPHONE' \| 'FILE_TOO_LARGE' \| 'EMPTY_RECORDING' \| null` | Drives localized Vietnamese error message + text fallback cue. |

### 2.3 Consumer Preferences (`EC5-05` — Matches `backend/app/schemas/user_preference.py`)

| Type / Interface | Field | Type | Constraints |
| :--- | :--- | :--- | :--- |
| `DietaryPreference` | — | `'NONE' \| 'VEGAN' \| 'VEGETARIAN'` | Matches `app.models.user.DietaryPreference`. |
| `UserPreferenceResponse` | `id` | `string` | UUID. |
| | `user_id` | `string` | Authenticated `CONSUMER` UUID. |
| | `preferred_categories` | `Array<FoodCategory \| string>` | Subset of `['RICE', 'NOODLES', 'BAKERY', 'VEGETARIAN', 'DRINKS', 'OTHER']`. |
| | `dietary_preference` | `DietaryPreference` | Default `'NONE'`. |
| | `excluded_allergens` | `string[]` | Canonical 14 EU FIC strings enforced as Layer 1 SQL Hard Filter. |
| | `max_budget` | `number \| string \| null` | Nullable; `>= 0` VND. |
| | `updated_at` | `string` | ISO 8601 timestamp. |
| `UserPreferenceUpdatePayload` | `preferred_categories` | `string[]` | Optional/full replacement list. |
| | `dietary_preference` | `DietaryPreference` | Optional/full replacement enum. |
| | `excluded_allergens` | `string[]` | Canonical 14 EU FIC strings. |
| | `max_budget` | `number \| null` | `null` clears budget cap; otherwise `>= 0`. |

### 2.4 AI Feature 2 — Personalized Recommendations & Semantic Search (`EC5-05`)

| Type / Interface | Field | Type | Notes |
| :--- | :--- | :--- | :--- |
| `PersonalizedRecommendationItem` | `dish_id` | `string` | UUID matching `dishes.id` for `OrderModal`. |
| | `dish_name` | `string` | Verified dish title (no mystery bags). |
| | `store_id` | `string` | Store UUID. |
| | `store_name` | `string` | Store display name. |
| | `store_address` | `string \| null` | Store address for card & map popup. |
| | `latitude` | `number \| null` | Store latitude for map focus. |
| | `longitude` | `number \| null` | Store longitude for map focus. |
| | `image_url` | `string \| null` | Inherited catalog dish image. |
| | `category` | `FoodCategory \| string` | Category tag. |
| | `distance_meters` | `number` | PostGIS `ST_Distance` output. |
| | `current_price` | `number` | Authoritative backend rescue/rule price (VND). |
| | `original_price` | `number` | Retail baseline price (VND). |
| | `discount_percent` | `number` | Integer `0..100` (e.g., `67`, `70`). |
| | `is_urgent_deal` | `boolean` | `true` during final 30–45m `-70%` rush → renders urgent flame badge. |
| | `remaining_quantity` | `number` | Strictly `> 0`. |
| | `pickup_window` | `string \| null` | e.g., `"13:55 - 15:00"`. |
| | `allergens` | `Array<string \| DishAllergenNote>` | Displayed transparently; guaranteed disjoint from user's `excluded_allergens`. |
| | `ai_justification` | `string` | Concise 20–30 word Gemini justification (or deterministic template fallback). |
| `PersonalizedRecommendationsResponse` | `recommendations` | `PersonalizedRecommendationItem[]` | Length `0..limit` (default `limit=3`). |
| | `is_fallback` | `boolean` | Optional indicator whether deterministic justification template was used. |
| `SemanticSearchRequest` | `query` | `string` | Trimmed Vietnamese natural-language query (`min_length=2`, `max_length=300`). |
| | `latitude` | `number` | User GPS latitude (`-90..90`). |
| | `longitude` | `number` | User GPS longitude (`-180..180`). |
| | `radius_km` | `number` | Optional search radius (`1.0..10.0`, default `5.0`). |
| `SemanticSearchIntent` | `max_price` | `number \| null` | Extracted VND budget (e.g., `30000`). |
| | `categories` | `string[]` | Extracted `FoodCategory` tags (e.g., `['NOODLES']`). |
| | `dietary_preference` | `DietaryPreference \| null` | Extracted lifestyle constraint (e.g., `'VEGETARIAN'`). |
| | `excluded_allergens` | `string[]` | Allergens parsed from query text (unioned with user profile exclusions on backend). |
| | `keywords` | `string[]` | Descriptive keywords (e.g., `['nóng', 'nước']`). |
| `SemanticSearchResponse` | `query` | `string` | Echoed query string. |
| | `parsed_intent` | `SemanticSearchIntent \| null` | Rendered as transparent filter chips under the search bar. |
| | `total` | `number` | Count of safe matching dishes. |
| | `is_fallback` | `boolean` | `true` if backend used deterministic keyword fallback while Gemini was unavailable. |
| | `results` | `PersonalizedRecommendationItem[]` | Normalized directly into `RescueDishItem[]` for list + `DynamicRadarMap` + `OrderModal`. |

---

## 3. Handoff Mapping: `EditableDraftCard[]` → `DishBatchPublishPayload`

| `QuickPostDraftEditor` State | `POST /api/v1/dishes/batch` (`DishBatchPublishPayload`) | Validation Rule |
| :--- | :--- | :--- |
| `pickupStart` (`"HH:MM"` or `"HH:MM:SS"`) | `pickup_start_time` (`"HH:MM:SS"`) | Normalized to `HH:MM:SS`. |
| `pickupEnd` (`"HH:MM"` or `"HH:MM:SS"`) | `pickup_end_time` (`"HH:MM:SS"`) | MUST satisfy `pickupEnd > pickupStart`. |
| `cards[i].matched_menu_id` | `dishes[i].menu_item_id` | Non-null UUID from active `menuItems`. |
| `cards[i].quantity` | `dishes[i].quantity` | Integer `> 0`. |
| `cards[i].override_discounted_price` | `dishes[i].override_discounted_price` | `null` if blank; `Number(...) > 0` if provided. |
| `cards[i].allergens` | `dishes[i].allergens` | Exact `{ allergen, risk_level, source, reason }` preserving `EXPLICIT` / `INFERRED`. |
| `cards[i].dietary_notes` | `dishes[i].dietary_notes` | Trimmed non-empty string array. |

---

## 4. QA, SLA & Release 1.0 Verification Records (`EC5-06`, `EC5-07`)

- **Allergen Invariant Matrix Record (`test_allergen_invariant.py`)**: Captures `(profile_variant, excluded_allergens_input, dish_allergen_format, endpoint, query_text, leaked_count)` — required assertion `leaked_count == 0` on every row.
- **Fault Resilience Matrix Record**: Captures `(endpoint, injected_fault ∈ {MISSING_KEY, TIMEOUT, RATE_LIMIT, NETWORK_ERROR, INVALID_SCHEMA}, expected_http_status, actual_http_status, fallback_usable)` — required assertion `actual_http_status != 500`.
- **SLA Benchmark Record**: Captures `(pipeline, sample_count, p50_ms, p95_ms, target_p95_ms, passed)` — Quick-Post `p95_ms < 3000`, Recommendation `p95_ms < 2500`, Fallback `p95_ms < 300`.
- **UAT Acceptance Matrix (`04_PA5_UAT_Signoff_and_Demo_Script.md`)**: Covers `UAT-01` through `UAT-12` spanning Core F1–F8, AI-1, AI-2, Allergen Hard Invariant, and Docker Compose Go-Live recovery with `(uat_id, feature, role, steps, expected, evidence_artifact, status, tester, date)`.
