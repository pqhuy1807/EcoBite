# Technical Research & Design Decisions: AI Feature 1 — Batch Quick-Post Multimodal Assistant

**Feature**: `002-ai-quick-post-nlp` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

This document resolves every architectural, SDK, validation, safety, and evaluation unknown before implementation begins.

---

## Decision 1: Async Google GenAI SDK & Injectable Protocol Adapter

- **Decision**: Use `google-genai==1.3.0` (`from google import genai; from google.genai import types`) via its native async interface `await client.aio.models.generate_content(...)`, wrapped in `asyncio.wait_for(..., timeout=settings.GEMINI_TIMEOUT_SECONDS)` and hidden behind a thin `GeminiQuickPostClient` `Protocol` + concrete `GoogleGenAIQuickPostAdapter`.
- **Rationale**:
  - **Constitution Principle VII** strictly prohibits blocking I/O inside FastAPI `async` routes/services; calling synchronous `client.models.generate_content(...)` would block the Uvicorn event loop for 1–3 seconds per request.
  - Injecting a `GeminiQuickPostClient` protocol lets unit and integration tests pass a deterministic `FakeGeminiClient` with zero network calls while recording the exact prompt, audio `Part`, model name, and `GenerateContentConfig`.
  - Using `types.GenerateContentConfig(response_mime_type="application/json", response_schema=QuickPostExtractionResponse, system_instruction=..., temperature=0.1)` enforces Pydantic Structured Output directly at the Gemini API layer (Guardrail #6).
- **Alternatives considered**:
  - Calling sync `client.models.generate_content` inside `asyncio.to_thread(...)`: works, but adds threadpool overhead when `google-genai` already provides first-class `client.aio`.
  - Direct raw `httpx` REST calls to Gemini: duplicates schema-to-JSON-Schema serialization and response parsing already maintained by the official `google-genai` SDK.

---

## Decision 2: Native Inline Audio (`types.Part.from_bytes`) vs Gemini Files API

- **Decision**: Ingest partner audio clips inline using `types.Part.from_bytes(data=audio_bytes, mime_type=normalized_mime)` with a strict **10 MB** maximum file size and an explicit MIME whitelist (`audio/mp4`, `audio/m4a`, `audio/x-m4a`, `audio/mpeg`, `audio/mp3`, `audio/wav`, `audio/x-wav`, `audio/webm`). Normalize MIME strings by stripping codec parameters (e.g., `audio/webm;codecs=opus` → `audio/webm`) and mapping `audio/m4a`/`audio/x-m4a` → `audio/mp4` when sending to Gemini if needed.
- **Rationale**:
  - Partner shift-end voice notes are 5–30 seconds long (`~100 KB – 1.5 MB`), well below Gemini's 20 MB inline payload ceiling.
  - Inline bytes require **1 single RPC round-trip** (no separate upload + poll-active + delete lifecycle), directly supporting the **P95 < 3.0s** latency target (NFR-001, SC-001).
  - Browsers using `MediaRecorder` frequently emit `audio/webm;codecs=opus` or `audio/mp4;codecs=mp4a.40.2`, so stripping `;...` parameters prevents false `415 Unsupported Media Type` rejections.
  - Checking both MIME type and non-empty byte length (`0 < len(audio_bytes) <= 10 * 1024 * 1024`) before calling Gemini prevents wasted quota and rejects bad uploads immediately.
- **Alternatives considered**:
  - Gemini Files API (`client.aio.files.upload`): adds 500ms–1.5s latency overhead and requires cleanup jobs; only justified for multi-minute recordings (`> 20 MB`), which are out of scope for Quick-Post.
  - External Speech-to-Text (Whisper / Google STT) before LLM: adds extra dependency, latency, and drops Vietnamese culinary/tonal context that Gemini 2.5 Flash handles natively.

---

## Decision 3: Dual-Key Configuration (`GEMINI_TEST_API` vs `GEMINI_DEMO_API`)

- **Decision**: Retain the environment-driven two-key design in `backend/app/core/config.py`:
  - `GEMINI_TEST_API` (free-tier for development/testing)
  - `GEMINI_DEMO_API` (paid-tier reserved for live demo)
  - `GEMINI_USE_DEMO_KEY: bool = False` (default `False` so tests/dev never consume paid demo quota)
  - `GEMINI_MODEL: str = "gemini-2.5-flash"`
  - `GEMINI_TIMEOUT_SECONDS: int = 15`
  - `settings.gemini_key` strips whitespace and raises `ValueError` when empty; `build_quick_post_service(db)` catches `ValueError` so missing keys construct `QuickPostService(db, gemini_client=None)` instead of crashing app startup or imports.
- **Rationale**: Complies with Guardrail #1 (no hardcoded secrets, `.env` never committed) and FR-010 (cost-safe separation between dev testing and demo).
- **Alternatives considered**: Single `GEMINI_API_KEY` variable — rejected because accidental paid-tier usage during automated eval runs or local iteration is a real team cost risk.

---

## Decision 4: Graceful Degradation Contract (`503 Service Unavailable`)

- **Decision**: When `gemini_client is None` (unconfigured key), Gemini times out (`TimeoutError`), encounters network/quota/API errors, or returns output failing `QuickPostExtractionResponse` validation (or yielding `pickup_end <= pickup_start`), `QuickPostService` logs a sanitized diagnostic warning (no API keys, no raw audio bytes) and raises `QuickPostUnavailableError`, which the endpoint translates to **HTTP `503 Service Unavailable`** with an actionable Vietnamese message advising the partner to retry or enter dishes manually.
- **Rationale**:
  - `QuickPostExtractionResponse` in `backend/app/schemas/nlp.py` enforces `items: list[SurplusDishItem] = Field(..., min_length=1)`. Returning an empty `items: []` dict (as the old prototype did) violates the Pydantic response schema and forces endpoints to return untyped `dict[str, Any]`.
  - Returning fake hardcoded dishes (as in the early `docs/06` sketch) is unsafe in production because a busy partner could accidentally publish fabricated food items with wrong allergens.
  - HTTP `503` cleanly signals transient AI unavailability while keeping `200 OK` strictly guaranteed to conform to `QuickPostExtractionResponse`.
- **Alternatives considered**:
  - Relaxing `min_length=1` on `QuickPostExtractionResponse` to return empty items on error: weakens schema validation and forces frontend callers to distinguish "error" from "no dishes spoken" via ad-hoc extra fields.

---

## Decision 5: Authoritative Server-Time Grounding (`Asia/Ho_Chi_Minh`)

- **Decision**:
  - At the HTTP endpoint (`POST /api/v1/ml/parse-dish-nlp`), the server ALWAYS resolves authoritative time via `datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))` (with `tzdata` already pinned in `backend/requirements.txt`).
  - `QuickPostService.parse_dish_nlp(...)` accepts an optional internal `reference_time: datetime | None = None` parameter strictly for deterministic unit testing and offline Golden Dataset evaluation; when `None`, it computes `datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))`.
  - If an older API client passes the optional `current_server_time` form field from `docs/04_API_Specification.md`, the endpoint accepts it as an optional ignored field (logging a debug note) so existing Swagger/client forms remain backwards-compatible while strictly obeying Constitution Principle VI (*"Natural-language time expressions MUST be converted using authoritative server time rather than relying on an unverified client clock"*).
- **Rationale**: Eliminates clock-spoofing bugs where a misconfigured partner phone clock produces expired or inverted pickup windows, while preserving full testability.
- **Alternatives considered**: Trusting client-supplied `current_server_time` directly — rejected because it directly violates Constitution Principle VI.

---

## Decision 6: Menu-Catalog Grounding, Context Pruning & Anti-Hallucination Post-Validation

- **Decision**:
  1. Fetch the authenticated `STORE_PARTNER`'s store via `store_repo.get_store_by_owner_id(db, owner_id)`.
     - Missing store → `404 Not Found`.
     - Store `kyc_status != KycStatus.APPROVED` → `403 Forbidden`.
  2. Fetch active menu items via `menu_repo.list_by_store(db, store.id, active_only=True)`.
  3. Build compact grounding context (`id`, `name`, `original_price`, `standard_ingredients`, `base_allergens`) capped at **50 items** in the prompt (if a store has `> 50` active items and `raw_text` is provided, rank by normalized token overlap first and take top 50; otherwise take the 50 most recently created active items).
  4. **Deterministic Post-Validation** against the full `valid_menu_map = {item.id: item for item in active_menu_items}`:
     - **UUID Verification (0% False Match)**: If `item.matched_menu_id is not None` and `item.matched_menu_id not in valid_menu_map`, set `item.matched_menu_id = None` and append `"Món ăn chưa khớp thực đơn gốc của quán, vui lòng chọn món từ danh mục."` to `item.missing_fields_warning`.
     - **Price Inheritance**: If `item.matched_menu_id in valid_menu_map` and `item.original_price is None`, populate `item.original_price = float(valid_menu_map[item.matched_menu_id].original_price)`.
     - **Empty Catalog Hint**: If `not active_menu_items`, append `"Quán chưa có món nào trong thực đơn gốc để đối chiếu tự động."` to `item.missing_fields_warning`.
     - **Allergen Deduplication**: Deduplicate `item.allergens` by `allergen` enum value; if both `EXPLICIT` and `INFERRED` appear for the same allergen, retain `EXPLICIT` (higher certainty).
     - **Pickup Window Validation**: Parse `pickup_start` and `pickup_end` via `time.fromisoformat(...)`; if `pickup_end <= pickup_start`, raise `QuickPostUnavailableError` (malformed extraction).
- **Rationale**: Enforces Guardrail #6, Constitution Principles IV & VI, and SC-004 (`0%` fabricated UUIDs).
- **Alternatives considered**: Trusting Gemini's `matched_menu_id` blindly — rejected because LLMs can hallucinate plausible UUIDs or partially mutate hex digits.

---

## Decision 7: Separating Guardrail #6 (Quick-Post) from Guardrail #7 (Consumer Allergen Hard Filter) & Legacy Route Cleanup

- **Decision**:
  - Remove `AllergenHardFilterService` invocation from `QuickPostService` (Guardrail #6 requires showing ALL extracted dishes with transparent 2-tier allergen warnings to the Store Partner; Guardrail #7 SQL hard filtering belongs exclusively to AI Feature 2 `RecommendationService`).
  - Create `backend/app/api/v1/endpoints/ml.py` exposing `POST /api/v1/ml/parse-dish-nlp` with `dependencies` / `Depends(require_roles(UserRole.STORE_PARTNER))`.
  - Remove the prototype `backend/app/api/v1/endpoints/quick_post.py` (which erroneously required `UserRole.CONSUMER` and exposed a public `/quick-post/allergen-filter/test` route) and swap its registration in `backend/app/api/v1/router.py` to `ml.router` with `prefix="/ml"`, `tags=["ML"]`.
  - Leave `backend/app/services/allergen_filter_service.py` and `backend/tests/unit/test_allergen_filter_service.py` intact so existing tests do not break while Phúc migrates AI-2 filtering to SQL in his separate branch (`feat/ai-2-recommendation`).
- **Rationale**: Directly fulfills the Week 6 Action Plan refactor checklist without causing cross-branch merge conflicts with AI Feature 2.
- **Alternatives considered**: Keeping `/quick-post/extract` alongside `/ml/parse-dish-nlp` — rejected because leaving an unauthenticated dev self-test route and a consumer-gated duplicate violates API spec and security hygiene.

---

## Decision 8: Direct Compatibility with `POST /api/v1/dishes/batch`

- **Decision**: Keep `QuickPostExtractionResponse` (`backend/app/schemas/nlp.py`) as the exact `response_model` of `POST /api/v1/ml/parse-dish-nlp` and verify end-to-end payload compatibility with `DishBatchPublish` (`backend/app/schemas/dish.py`) via an integration handoff test:
  - `pickup_start` / `pickup_end` (`"HH:MM:SS"`) parse cleanly into `DishBatchPublish.pickup_start_time` / `pickup_end_time` (`datetime.time`).
  - Each `SurplusDishItem` with non-null `matched_menu_id` maps directly into `DishBatchItem` (`menu_item_id`, `quantity`, `override_discounted_price`, `allergens`, `dietary_notes`) because `NLPAllergenWarning` uses `use_enum_values=True` matching `AllergenWarning`'s exact fields (`allergen`, `risk_level`, `source`, `reason`).
- **Rationale**: Zero translation friction for the Frontend Draft Cards editor (`EC5-04`) and instant Swagger demoability (`parse-dish-nlp` → `dishes/batch`).

---

## Decision 9: Offline Evaluation Harness & Golden Dataset (`ml/eval/`)

- **Decision**: Place the Golden Dataset (`ml/eval/golden_ai1_dataset.json`, 15–20 Vietnamese cases including text and short local audio fixtures in `ml/eval/audio/`) and benchmark script (`ml/eval/eval_ai1_quick_post.py`) inside the `ml/eval/` workspace, reusing `QuickPostService` + `backend/app/schemas/nlp.py` directly without adding any heavy ML training packages to `backend/requirements.txt` (Guardrail #8).
- **Metrics Computed**:
  1. `schema_validity_rate` (target `>= 98%`)
  2. `field_extraction_accuracy` (`dish_name`, `quantity`, `pickup_start`, `pickup_end`, `price`; target `>= 90%`)
  3. `menu_grounding_accuracy` (`>= 90%`) & `false_uuid_rate` (strict `0%`)
  4. `allergen_recall` (`>= 95%`, prioritizing safety)
  5. `two_tier_source_accuracy` (`EXPLICIT` vs `INFERRED`; target `>= 85%`)
  6. `latency_p50_ms`, `latency_p95_ms` (`P95 < 3000 ms`) & token/cost estimate from Gemini `usage_metadata`.
- **Rationale**: Satisfies User Story 4 and Week 6 Exit Criteria with objective, repeatable evidence documented in `docs/project_management/pa5_sprint5/research_ai1_quick_post_eval.md`.
