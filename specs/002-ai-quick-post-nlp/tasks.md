---
description: "Dependency-ordered TDD task list for AI Feature 1 — Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard"
---

# Tasks: AI Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard

**Input**: Design documents from `/specs/002-ai-quick-post-nlp/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/api-contracts.md`, `quickstart.md`

**Tests**: Test tasks are **MANDATORY** and placed **FIRST** inside every User Story phase per EcoBite Constitution Principle I (Test-First Development — Red-Green-Refactor). The Final Verification Gate phase MUST exit `0` across all checks before proposing any commit.

**Organization**: Tasks are grouped by User Story (`US1`–`US4`) so each increment is independently testable and deliverable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`, `[US4]`) — omitted in Setup, Foundational, Polish, and Verification Gate phases
- Exact repository-relative file paths included in every task

---

## Phase 1: Setup (Shared Environment & Configuration)

**Purpose**: Ensure the Gemini SDK is installed in `backend/venv_backend` and dual-key environment settings pass all static checks cleanly.

- [ ] T001 Install `google-genai==1.3.0` into `backend/venv_backend` (`backend/requirements.txt`) and verify `import google.genai` succeeds without error
- [ ] T002 Polish `Settings.gemini_key` to return `key.strip()`, run `ruff format` on `backend/app/core/config.py`, and confirm `GEMINI_DEMO_API`, `GEMINI_TEST_API`, `GEMINI_MODEL="gemini-2.5-flash"`, `GEMINI_TIMEOUT_SECONDS=15`, and `GEMINI_USE_DEMO_KEY=False` (with trailing newline) in `backend/.env.example`

**Checkpoint**: `backend/venv_backend` imports `google.genai`, `config.py` passes `ruff check`, `ruff format --check`, and `mypy`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core service exceptions, async Gemini SDK protocol/adapter, and verified NLP schemas required before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [ ] T003 Define `QuickPostInputError(ValueError)` (with `status_code` attribute for `413`/`415`/`422`), `QuickPostUnavailableError(RuntimeError)`, duck-typed `GeminiQuickPostClient` protocol, async `GoogleGenAIQuickPostAdapter` wrapping `genai.Client(api_key=...).aio.models.generate_content(...)` with `asyncio.wait_for(..., timeout=settings.GEMINI_TIMEOUT_SECONDS)` and `types.GenerateContentConfig(response_mime_type="application/json", response_schema=QuickPostExtractionResponse, temperature=0.1)`, and fault-tolerant `build_quick_post_service` factory (catching `ValueError` from `settings.gemini_key` so missing keys yield `gemini_client=None`) in `backend/app/services/quick_post_service.py`
- [ ] T004 [P] Verify existing schema constraints (`QuickPostExtractionResponse` `items` `min_length=1` and `HH:MM:SS` time validator; `SurplusDishItem` `dish_name` `min_length=1, max_length=255`, `quantity` `gt=0`, `original_price` `gt=0`, `override_discounted_price` `gt=0`; `NLPAllergenWarning` with 14 `EUAllergen` values, `DetectionSource` `EXPLICIT`/`INFERRED`, `AllergenRiskLevel` `HIGH`/`MEDIUM`/`LOW`) in `backend/app/schemas/nlp.py` by running `backend/tests/unit/test_nlp_schemas.py`

**Checkpoint**: Foundation ready — async Gemini client abstraction and validated NLP schemas are in place.

---

## Phase 3: User Story 1 - Text-Based Batch Quick-Post with Menu Grounding & 2-Tier Allergen Guard (Priority: P1) 🎯 MVP

**Goal**: Approved Store Partners submit Vietnamese free text listing multiple surplus dishes and receive structured `QuickPostExtractionResponse` drafts grounded in their store's active `MenuItem` catalog, anchored to authoritative `Asia/Ho_Chi_Minh` server time, with verified UUIDs, inherited `original_price`, and preserved 2-tier EU FIC allergen warnings (`EXPLICIT` vs `INFERRED`).

**Independent Test**: Run `pytest tests/unit/test_quick_post_service.py -v` for US1 tests; invoke `POST /api/v1/ml/parse-dish-nlp` with `raw_text` as an approved `STORE_PARTNER` and confirm `200 OK` returns schema-valid drafts with verified `matched_menu_id`, inherited `original_price`, `Asia/Ho_Chi_Minh` pickup window, and both `EXPLICIT`/`INFERRED` allergens intact.

### Tests for User Story 1 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T005 [P] [US1] Write unit tests in `backend/tests/unit/test_quick_post_service.py` using `FakeGeminiClient` + SQLite `db_session`/`store_partner` fixtures verifying: multi-dish text extraction returns `QuickPostExtractionResponse`, preserves ALL dishes and 2-tier `EUAllergen` warnings (`EXPLICIT` and `INFERRED`, confirming consumer allergen filtering is NOT applied), preserves spoken `override_discounted_price` while keeping unspoken ones `None`, and injects authoritative `Asia/Ho_Chi_Minh` timestamp into the Gemini prompt
- [ ] T006 [P] [US1] Write unit tests in `backend/tests/unit/test_quick_post_service.py` verifying Menu-Catalog Grounding and deterministic post-validation: valid `matched_menu_id` inherits `float(menu_item.original_price)` when `original_price` is `None`, fabricated or cross-store `matched_menu_id` is reset to `None` with warning in `missing_fields_warning` (`0%` false UUID pass-through), empty store catalog appends a warning without failing, >50 active menu items caps prompt context to 50 while validating against the full active catalog, and duplicate allergens on the same item deduplicate with `EXPLICIT` taking precedence over `INFERRED`

### Implementation for User Story 1

- [ ] T007 [US1] Implement `QuickPostService.parse_dish_nlp` store & active catalog lookup (`store_repo.get_store_by_owner_id`, `menu_repo.list_by_store(active_only=True)`), compact JSON catalog serialization with >50-item pruning, Vietnamese culinary system prompt (Menu Grounding, Vietnamese price slang, `Asia/Ho_Chi_Minh` relative-time conversion, 14 EU FIC 2-tier `EXPLICIT`/`INFERRED` rules, `dietary_notes`), and remove `AllergenHardFilterService` filtering in `backend/app/services/quick_post_service.py`
- [ ] T008 [US1] Implement deterministic `_post_validate_extraction` in `backend/app/services/quick_post_service.py` verifying `matched_menu_id` against the store's full active catalog map, inheriting `original_price`, adding missing-catalog/unmatched warnings, deduplicating `allergens` (`EXPLICIT` > `INFERRED`), and asserting `time.fromisoformat(pickup_end) > time.fromisoformat(pickup_start)`
- [ ] T009 [US1] Create `backend/app/api/v1/endpoints/ml.py` implementing `POST /api/v1/ml/parse-dish-nlp` (`multipart/form-data`, `response_model=QuickPostExtractionResponse`, `Depends(require_roles(UserRole.STORE_PARTNER))`, authoritative `Asia/Ho_Chi_Minh` server clock ignoring optional `current_server_time`), register `ml.router` under `prefix="/ml"` in `backend/app/api/v1/router.py`, and remove legacy prototype `backend/app/api/v1/endpoints/quick_post.py`

**Checkpoint**: User Story 1 (MVP) is complete and independently testable end-to-end for Vietnamese text Quick-Post.

---

## Phase 4: User Story 2 - Native Multimodal Vietnamese Voice Clip Quick-Post (Priority: P1)

**Goal**: Approved Store Partners upload Vietnamese voice recordings (`.m4a`, `.mp3`, `.wav`, `.webm`, `<= 10 MB`) alone or alongside text, validated before AI invocation and passed natively via `types.Part.from_bytes` to Gemini 2.5 Flash.

**Independent Test**: Run `pytest tests/unit/test_quick_post_service.py tests/integration/test_api_ml.py -k audio -v`; verify valid audio clips pass `types.Part.from_bytes` with normalized MIME to Gemini while invalid formats (`415`), >10 MB clips (`413`), and 0-byte files (`422`) are rejected before calling Gemini.

### Tests for User Story 2 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T010 [P] [US2] Write unit tests in `backend/tests/unit/test_quick_post_service.py` verifying inline audio ingestion via `types.Part.from_bytes` (audio-only and audio + `raw_text` combined), MIME codec-suffix stripping (`audio/webm;codecs=opus` → `audio/webm`, `audio/m4a`/`audio/x-m4a` → `audio/mp4`), and rejection (`QuickPostInputError`) for 0-byte audio, >`10_485_760` bytes (>10 MB), and unsupported MIME types
- [ ] T011 [P] [US2] Write integration tests in `backend/tests/integration/test_api_ml.py` verifying `POST /api/v1/ml/parse-dish-nlp` succeeds (`200 OK`) with valid `.m4a`/`.mp3`/`.wav`/`.webm` multipart `audio_file` (with and without `raw_text`) and rejects unsupported file types (`415`), oversized audio >`10_485_760` bytes (`413`), and 0-byte audio (`422`) without invoking Gemini

### Implementation for User Story 2

- [ ] T012 [US2] Implement audio MIME normalization (whitelist `audio/mp4`, `audio/m4a`, `audio/x-m4a`, `audio/mpeg`, `audio/mp3`, `audio/wav`, `audio/x-wav`, `audio/webm` + extension fallback `.m4a`/`.mp3`/`.wav`/`.webm`), strict byte-size validation (`0 < len(audio_bytes) <= 10_485_760`), and multimodal `types.Part.from_bytes` request assembly in `backend/app/services/quick_post_service.py`
- [ ] T013 [US2] Add `audio_file: UploadFile | None = File(default=None)` reading and explicit `413`/`415`/`422` HTTP error mapping in `backend/app/api/v1/endpoints/ml.py`

**Checkpoint**: User Stories 1 and 2 both work independently — both text and native voice Quick-Post pass automated tests.

---

## Phase 5: User Story 3 - Safe Degradation, Role Enforcement & 1-Tap Batch Publish Handoff (Priority: P2)

**Goal**: Enforce strict `STORE_PARTNER` + `APPROVED` KYC guards, return graceful `503` on AI unavailability/timeout/invalid schema without leaking secrets, remove legacy `/quick-post/*` routes, and prove direct compatibility between `POST /api/v1/ml/parse-dish-nlp` and `POST /api/v1/dishes/batch`.

**Independent Test**: Run `pytest tests/integration/test_api_ml.py -v` verifying all negative security/error status codes (`401`, `403`, `404`, `422`, `503`), `404` on removed `/quick-post/*` paths, and `201 Created` when feeding extracted output into `POST /api/v1/dishes/batch`.

### Tests for User Story 3 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T014 [P] [US3] Write unit tests in `backend/tests/unit/test_quick_post_service.py` covering missing store, store with `KycStatus.PENDING` or `KycStatus.REJECTED`, missing `gemini_client` (`None`), `TimeoutError`, generic upstream SDK exception, invalid JSON/Pydantic `ValidationError`, and inverted pickup window (`pickup_end <= pickup_start`) raising clean domain exceptions without mutating DB
- [ ] T015 [P] [US3] Write integration tests in `backend/tests/integration/test_api_ml.py` verifying `401` unauthenticated, `403` for `CONSUMER` and `ADMIN` roles, `403` for `PENDING`/`REJECTED` store KYC, `404` for `STORE_PARTNER` without a store, `422` when both `raw_text` (blank/None) and `audio_file` are omitted, `503` when Gemini is unavailable/times out/returns invalid schema, `404` for removed `/api/v1/quick-post/extract` and `/api/v1/quick-post/allergen-filter/test`, and full E2E handoff submitting `POST /api/v1/ml/parse-dish-nlp` output directly to `POST /api/v1/dishes/batch` (`201 Created`)

### Implementation for User Story 3

- [ ] T016 [US3] Implement store existence & `KycStatus.APPROVED` enforcement, structured operational logging (`store_id`, input mode, `item_count`, `latency_ms`, sanitized error class — never logging API keys or audio binaries), and `QuickPostUnavailableError` translation for timeout/SDK/validation/window errors in `backend/app/services/quick_post_service.py`
- [ ] T017 [US3] Wire injectable `get_quick_post_service` FastAPI dependency and complete `403`/`404`/`413`/`415`/`422`/`503` HTTP exception mapping in `backend/app/api/v1/endpoints/ml.py`

**Checkpoint**: All backend security, error handling, observability, and batch-publish handoff contracts are verified.

---

## Phase 6: User Story 4 - Offline Benchmark & AI-1 Research Report (Priority: P3)

**Goal**: Build a 15–20 case Vietnamese Golden Dataset (text + voice clips), run an automated evaluation harness measuring all 6 Week-6 KPIs, and document prompt/audio/pruning research findings and baseline scores for Sprint 5 Planning.

**Independent Test**: Run `backend/venv_backend/bin/python ml/eval/eval_ai1_quick_post.py --dataset ml/eval/golden_ai1_dataset.json` and confirm it outputs a complete metric table (Schema Validity, Field Extraction, Menu Grounding + 0% False UUID, Allergen Recall, 2-Tier Source Accuracy, Latency P50/P95 & token cost) and matches the report in `docs/project_management/pa5_sprint5/research_ai1_quick_post_eval.md`.

### Fixtures & Evaluation Script for User Story 4

- [ ] T018 [P] [US4] Create Golden Dataset with 15–20 Vietnamese Quick-Post ground-truth cases (covering single/multi-dish, price slang, relative times, `EXPLICIT` & `INFERRED` Vietnamese allergens, out-of-menu dishes, ambiguous quantity, and 3–5 short voice clips in `ml/eval/audio/` each `< 5 MB`) in `ml/eval/golden_ai1_dataset.json`
- [ ] T019 [US4] Implement automated benchmark script computing Schema Validity Rate (`>= 98%`), Field Extraction Accuracy (`>= 90%`), Menu Grounding Accuracy (`>= 90%`) & False UUID Rate (`0%`), Allergen Recall (`>= 95%`), 2-Tier Source Accuracy (`>= 85%`), and Latency P50/P95 (`P95 < 3.0s`) + token/cost summary in `ml/eval/eval_ai1_quick_post.py`
- [ ] T020 [US4] Run `ml/eval/eval_ai1_quick_post.py` against live Gemini 2.5 Flash and write the AI-1 deep-dive research & baseline evaluation report (Vietnamese dialect/slang prompting, inline audio `Part.from_bytes` vs Files API, large-menu pruning >50 items, post-validation anti-hallucination, and observed benchmark table) in `docs/project_management/pa5_sprint5/research_ai1_quick_post_eval.md`

**Checkpoint**: AI-1 baseline metrics are measured and documented for Sprint 5 Kickoff (`29/11`).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end live verification and guardrail compliance audit across the feature.

- [ ] T021 Execute live Swagger E2E smoke test (`POST /api/v1/ml/parse-dish-nlp` with text & audio → `POST /api/v1/dishes/batch` `201 Created`) following `specs/002-ai-quick-post-nlp/quickstart.md`
- [ ] T022 [P] Audit `backend/requirements.txt` (zero heavy ML training libraries: `ultralytics`, `jupyterlab`, `matplotlib`) and `git status` (no `.env` staged, no audio/binary file `> 5 MB`)

---

## Final Phase: Verification Gate (Constitution Principle VIII) — MANDATORY

**Purpose**: Reproducible evidence that every Quality Gate passes. All commands MUST exit `0` before proposing a commit.

### Backend (`backend/`, using `venv_backend`)

- [ ] T023 `./venv_backend/bin/ruff check app/ tests/` — lint passes with zero findings
- [ ] T024 `./venv_backend/bin/ruff format --check app/ tests/` — formatting is canonical
- [ ] T025 `./venv_backend/bin/mypy app/` — static type-check passes with zero errors
- [ ] T026 `./venv_backend/bin/pytest tests/ -v` — full unit, integration, and property suite passes with zero regressions

### Repository Hooks (repo root)

- [ ] T027 `pre-commit run --all-files` — secrets check, file size (`< 5 MB`), and formatting hooks pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Start immediately (`T001`–`T002`).
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories (`T003`–`T004`).
- **Phase 3 (US1 — Text Quick-Post 🎯 MVP)**: Depends on Phase 2 (`T005`–`T009`).
- **Phase 4 (US2 — Native Audio)**: Depends on Phase 3 (`T010`–`T013`).
- **Phase 5 (US3 — Degradation, RBAC & Batch Handoff)**: Depends on Phases 3–4 (`T014`–`T017`).
- **Phase 6 (US4 — Golden Dataset & Research Report)**: `T018` can be prepared in parallel once Phase 2 is ready; `T019`–`T020` depend on Phases 3–5 being runnable.
- **Phase 7 (Polish)** & **Final Phase (Verification Gate)**: Depend on all selected user stories completing.

### Within Each User Story (Strict TDD Loop)

1. Write unit/integration tests FIRST (`[P]` test tasks can be authored together) and confirm they FAIL (Red).
2. Implement service logic (`quick_post_service.py`) before router wiring (`ml.py`).
3. Re-run tests to confirm PASS (Green) and refactor cleanly.

### Parallel Opportunities

```bash
# Phase 3 (US1) tests can be written together before implementation:
T005: Unit tests for text extraction, 2-tier allergens & server-time grounding
T006: Unit tests for menu grounding, price inheritance, anti-hallucination & deduplication

# Phase 4 (US2) unit & integration audio tests can be written in parallel:
T010: Unit tests for audio bytes/MIME validation & Part.from_bytes in tests/unit/test_quick_post_service.py
T011: Integration tests for multipart audio validation (200/413/415/422) in tests/integration/test_api_ml.py

# Phase 5 (US3) unit & integration error/RBAC tests can be written in parallel:
T014: Unit tests for store/KYC guards & Gemini failure modes
T015: Integration tests for RBAC, 503 degradation, legacy route removal & dishes/batch handoff
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup: `T001`–`T002`) + Phase 2 (Foundational: `T003`–`T004`).
2. Complete Phase 3 (US1: `T005`–`T009`) → **STOP & VALIDATE**: text-based `POST /api/v1/ml/parse-dish-nlp` works end-to-end with Menu Grounding, Server-Time Grounding, and 2-Tier Allergens.

### Incremental Delivery

1. MVP (US1) → Add Native Audio (US2) → Harden Security, Degradation & `dishes/batch` Handoff (US3) → Run Golden Dataset Benchmark & Research Report (US4) → Pass Mandatory Verification Gate (`T023`–`T027`).
