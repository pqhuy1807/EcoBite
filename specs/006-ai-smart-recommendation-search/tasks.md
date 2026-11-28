---
description: "Dependency-ordered TDD task list for AI Feature 2 — Smart Food Recommendation Engine (3-Layer SQL Allergen Hard Filter + Heuristic Scoring + Gemini Justification) & Conversational Semantic Search"
---

# Tasks: AI Smart Food Recommendation Engine & Conversational Semantic Search

**Input**: Design documents from `/specs/006-ai-smart-recommendation-search/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/api-contracts.md`, `quickstart.md`

**Tests**: Test tasks are **MANDATORY** and placed **FIRST** inside every User Story phase per EcoBite Constitution Principle I (Test-First Development — Red-Green-Refactor). The Final Verification Gate phase MUST exit `0` across all checks before proposing any commit.

**Team Assignments & Jira Traceability**:
- **Đặng Trọng Phúc (`[EC5-02]`)**: Canonical allergen normalization, `UserPreference` CRUD, Layer 1 SQL/PostGIS Allergen Hard Filter, Week 6 AI-2 Golden Dataset & Research Report (`feat/ai-2-recommendation`).
- **Phùng Quốc Huy (`[EC5-03]`)**: Layer 2 Deterministic Heuristic Scoring, Layer 3 Gemini 2.5 Flash Justification + Faithfulness Guard + `< 300ms` Fallback, and Conversational Semantic Search (`POST /dishes/search-semantic`).
- **Đàng Thế Tony (`[EC5-06]`)**: Allergen Hard Invariant Integration & Hypothesis Fuzzing Suite (`test_allergen_invariant.py`), Recommendation API/SLA Suite (`test_api_recommendations.py`), and `03_PA5_AI_Test_Plan.md`.

## Format: `[ID] [P?] [Story] [Jira] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: User story label (`[US1]`–`[US5]`) — omitted in Setup, Foundational, Polish, and Verification Gate phases
- Exact repository-relative file paths included in every task

---

## Phase 1: Setup (Shared Configuration & Environment)

**Purpose**: Ensure bounded recommendation timeout configuration is documented and `google-genai` / `hypothesis` / `tzdata` are ready in `backend/venv_backend`.

- [ ] T001 [EC5-02] Verify `google-genai==1.3.0`, `hypothesis==6.98.3`, and `tzdata` import cleanly in `backend/venv_backend` (`backend/requirements.txt`) with zero heavy ML training packages added
- [ ] T002 [P] [EC5-03] Add `GEMINI_RECOMMENDATION_TIMEOUT_SECONDS: float = Field(default=2.0, gt=0)` to `Settings` in `backend/app/core/config.py` and document the variable (no secrets, trailing newline) in `backend/.env.example`

**Checkpoint**: Backend settings load cleanly and pass `ruff` + `mypy`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared canonical 14 EU FIC allergen normalizer & SQL token expander, fail-closed optional JWT dependency, Pydantic recommendation/search schemas, and injectable async Gemini adapter required before user stories execute.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [ ] T003 [EC5-02] Create `backend/app/core/allergens.py` implementing Vietnamese-safe diacritic folding (`đ`/`Đ` → `d` before NFD mark stripping), canonical `normalize_allergens(values, *, strict: bool = True) -> list[str]` mapping all 14 `EUAllergen` values + English/Vietnamese accented & unaccented synonyms + composite `"Hải sản"`/`"seafood"` → `[CRUSTACEANS, MOLLUSCS, FISH]`, and `expand_sql_exclusion_terms(canonical_allergens) -> tuple[list[str], list[str]]` generating exact lowercase tokens and bounded `LIKE` patterns (including Title Case/lowercase Vietnamese variants for SQLite's ASCII-only `LOWER()`)
- [ ] T004 [P] [EC5-03] Add `oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)` and fail-closed `get_optional_current_user` (returns `None` when no `Authorization` header is present; raises `401 Unauthorized` when a malformed, expired, non-access, or inactive-user Bearer token is supplied) in `backend/app/api/deps.py`
- [ ] T005 [P] [EC5-03] Create `backend/app/schemas/recommendation.py` defining `ScoreBreakdown`, `RecommendedDishItem`, `PersonalizedRecommendationResponse`, `SemanticSearchRequest` (trimmed query `2–300` chars, GPS bounds, `radius_km` `1.0–10.0`, `limit` `1–30`), `SemanticSearchIntent`, `SemanticSearchDishItem`, `SemanticSearchResponse`, and internal Gemini structured output schemas `DishJustificationItem` & `RecommendationJustificationBatch`

**Checkpoint**: Canonical allergen normalization, fail-closed optional auth, and typed AI-2 DTOs are ready.

---

## Phase 3: User Story 1 - Consumer Allergen & Dietary Preference Profile Management (Priority: P1) 🎯 MVP-1

**Goal**: Authenticated `CONSUMER` users read (`GET`) and upsert (`PUT`) their `UserPreference` profile with canonical 14 EU FIC allergen normalization and category validation (`EC5-02`, Phúc).

**Independent Test**: Run `pytest tests/unit/test_preference_repo.py tests/integration/test_api_preferences.py -v` verifying default read-only response, Vietnamese/English/composite `"Hải sản"` normalization, persistence across requests, `422` on invalid allergen/category/negative budget, and `401`/`403` RBAC enforcement.

### Tests for User Story 1 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T006 [P] [US1] [EC5-02] Write unit tests in `backend/tests/unit/test_preference_repo.py` covering `normalize_allergens` (all 14 `EUAllergen` values, `"đậu phộng"`/`"dau phong"`/`"lạc"`, `"Hải sản"` → 3 seafood categories, deduplication, `strict=True` error on unknown string), `expand_sql_exclusion_terms` (no unsafe `"%ca%"` wildcard), and `preference_repo.get_by_user_id` / `upsert_for_user` create-and-update atomicity on SQLite
- [ ] T007 [P] [US1] [EC5-02] Write integration tests in `backend/tests/integration/test_api_preferences.py` verifying `GET /api/v1/users/me/preferences` (default `is_default=True` without mutating DB, then persisted profile), `PUT /api/v1/users/me/preferences` (normalizing `["đậu phộng", "Hải sản"]` and lowercase categories, partial updates preserving unset fields, `422` on invalid allergen/category/negative `max_budget`), `401` unauthenticated, and `403` for `STORE_PARTNER` / `ADMIN` while confirming `tests/unit/test_cluster1_models.py` stays green

### Implementation for User Story 1

- [ ] T008 [US1] [EC5-02] Update `backend/app/schemas/user_preference.py` adding `preferred_categories` (`ItemCategory` uppercase validation + deduplication) and `excluded_allergens` (`normalize_allergens(..., strict=True)`) validators on `UserPreferenceCreate` and `UserPreferenceUpdate`, and adding optional `id: uuid.UUID | None = None`, `updated_at: datetime | None = None`, `is_default: bool = False` on `UserPreferenceResponse` (preserving `test_cluster1_models.py` compatibility)
- [ ] T009 [US1] [EC5-02] Create `backend/app/repositories/preference_repo.py` implementing async `get_by_user_id(db, user_id)` and `upsert_for_user(db, user_id, ...)` using SQLAlchemy 2.0 `AsyncSession`
- [ ] T010 [US1] [EC5-02] Add `GET /me/preferences` and `PUT /me/preferences` protected by `Depends(require_roles(UserRole.CONSUMER))` in `backend/app/api/v1/endpoints/users.py`

**Checkpoint**: User Story 1 (`EC5-02` Preferences CRUD) is complete and passes all unit and integration tests.

---

## Phase 4: User Story 2 - Hard Safety Invariant Filtering at Data Query Boundary (Priority: P1) 🎯 MVP-2

**Goal**: Replace Python-only filtering (`allergen_filter_service.py`) with a portable SQL-level Layer 1 Hard Filter in `recommendation_repo.py` executing `WHERE NOT EXISTS` across BOTH `dishes.allergens` and `menu_items.base_allergens` alongside PostGIS `ST_DWithin` (SQLite Haversine parity), `Store.kyc_status == APPROVED`, `DishStatus.ACTIVE`, `remaining_quantity > 0`, active `Asia/Ho_Chi_Minh` pickup window, and `dietary_preference` (`EC5-02`, Phúc).

**Independent Test**: Run `pytest tests/unit/test_recommendation_repo.py -v` verifying SQL-level `0.0%` Allergen Leakage on single/multi/Vietnamese/legacy/`base_allergens` cases, exclusion of unapproved stores, sold-out/expired/out-of-radius dishes, vegan/vegetarian enforcement, and non-empty SQL `NOT EXISTS` predicate emission.

### Tests for User Story 2 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T011 [P] [US2] [EC5-02] Write repository unit tests in `backend/tests/unit/test_recommendation_repo.py` seeding approved/pending/rejected stores at varying distances, `ACTIVE`/`SOLD_OUT`/`EXPIRED` dishes, past and active pickup windows, structured `EXPLICIT`/`INFERRED` dish allergens, legacy seeded allergen strings (`"Milk (Sữa)"`, `"Fish (Nước mắm)"`, `"Gluten"`, `"Sesame (Mè)"`, `"Crustaceans (Tôm)"`), and `menu_items.base_allergens`-only allergens — asserting **0.0% allergen leakage**, strict `VEGAN`/`VEGETARIAN` enforcement, radius filtering, and empty result `[]` when all nearby dishes are unsafe
- [ ] T012 [P] [US2] [EC5-02] Add SQL query inspection test in `backend/tests/unit/test_recommendation_repo.py` capturing compiled SQL statements via SQLAlchemy `before_cursor_execute` event listener to prove `NOT EXISTS` + `json_each` (SQLite) executes inside the SQL `WHERE` clause (and verify the PostgreSQL branch compiles valid `jsonb_array_elements` + `ST_DWithin` SQL) — proving allergen safety is NOT delegated to Python post-filtering

### Implementation for User Story 2

- [ ] T013 [US2] [EC5-02] Create `backend/app/repositories/recommendation_repo.py` implementing `SafeDishCandidate` dataclass and async `fetch_safe_candidates(db, *, lat, lng, radius_km, current_time_vn, excluded_allergens, dietary_preference=DietaryPreference.NONE, categories=None)` with dual-dialect SQL (`PostgreSQL` PostGIS `ST_DWithin`/`ST_Distance` + `jsonb_array_elements` AND `SQLite` JSON1 `json_each` + Haversine radius parity) checking BOTH `dishes.allergens` and `LEFT OUTER JOIN menu_items.base_allergens` in `WHERE NOT EXISTS`
- [ ] T014 [P] [US2] [EC5-02] Add deprecation docstring header to `backend/app/services/allergen_filter_service.py` explaining that Guardrail #7 SQL-level hard filtering now lives in `backend/app/repositories/recommendation_repo.py` (without breaking existing `tests/unit/test_allergen_filter_service.py`)

**Checkpoint**: User Story 2 (`EC5-02` Layer 1 SQL Allergen Hard Filter) guarantees `0.0%` allergen leakage directly at the SQL boundary.

---

## Phase 5: User Story 3 - Deterministic Multi-Factor Scoring & Personalized AI Justification with Safe Fallback (Priority: P1) 🎯 MVP-3

**Goal**: Deliver `GET /api/v1/recommendations/personalized` (`CONSUMER`) implementing Layer 2 deterministic scoring (`0.40 * proximity + 0.30 * discount_urgency + 0.30 * taste_match`), Layer 3 async Gemini 2.5 Flash batched justification (`<= 2.0s` timeout, dual-key config), server-side numeric faithfulness verification (`0%` fabricated numbers), and `< 300ms` deterministic Vietnamese fallback (`EC5-03`, Huy).

**Independent Test**: Run `pytest tests/unit/test_recommendation_service.py -k personalized -v` verifying exact 40/30/30 scores, urgent `-70%` rush prioritization, cold-start neutral baseline, deterministic tie-breaking, Gemini faithfulness rejection triggering fallback, and graceful `200 OK` fallback when Gemini is `None`/times out/errors.

### Tests for User Story 3 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T015 [P] [US3] [EC5-03] Write Layer 2 unit tests in `backend/tests/unit/test_recommendation_service.py` verifying `[0, 1]` normalization for `S_proximity`, `S_discount_urgency` (final-rush `<= 30–45 min` & `-70%` via `DishService.calculate_time_shifted_discount`), and `S_taste_match` (preferred categories, soft budget decay, dietary bonus, completed `OrderRepository` history affinity, cold-start `0.5` neutral baseline), exact weighted sum `0.40/0.30/0.30`, deterministic tie-breaking, and Top-K slicing
- [ ] T016 [P] [US3] [EC5-03] Write Layer 3 unit tests in `backend/tests/unit/test_recommendation_service.py` using `FakeGeminiRecommendationClient` verifying: only Top-K SQL-safe dishes (and zero PII) are sent to Gemini, valid 20–30 word DB-grounded Vietnamese justifications return `justification_source="GEMINI"`, fabricated price/distance/discount/stock numbers or out-of-range length or banned medical-guarantee phrases fail `_is_justification_faithful` and trigger per-dish fallback (`justification_source="FALLBACK"`), partial Gemini responses fall back only for missing dishes, and missing key (`None`)/`TimeoutError`/SDK error degrade cleanly to `200 OK` deterministic fallback templates

### Implementation for User Story 3

- [ ] T017 [US3] [EC5-03] Create `backend/app/services/recommendation_service.py` implementing injectable `GeminiRecommendationClient` protocol, async `GoogleGenAIRecommendationAdapter` (`client.aio.models.generate_content`, `asyncio.wait_for(..., timeout=settings.GEMINI_RECOMMENDATION_TIMEOUT_SECONDS)`, dual-key `settings.gemini_key`, fault-tolerant `build_recommendation_service(db)`), Layer 2 deterministic scorer (`score_candidates`), Layer 3 batched justification synthesizer, `_is_justification_faithful` numeric/length/safety validator, `_build_fallback_justification` 20–26 word Vietnamese template, optional graceful-degrade Redis short-TTL cache keyed by `(dish_ids, prices, distances, stock, normalized_excluded_allergens, dietary_preference)`, and `get_personalized_recommendations(...)`
- [ ] T018 [US3] [EC5-03] Create `backend/app/api/v1/endpoints/recommendations.py` implementing `GET /recommendations/personalized` (`Depends(require_roles(UserRole.CONSUMER))`, query params `lat`, `lng`, `radius_km=3.0`, `limit=3`, injectable `get_recommendation_service` dependency)
- [ ] T019 [US3] [EC5-03] Register `recommendations.router` in `backend/app/api/v1/router.py` **before** `stores.router` (avoiding legacy wildcard `GET /{store_id}` interference)

**Checkpoint**: User Story 3 (`EC5-03` Personalized Recommendations) is complete end-to-end with verified Layer 1 + Layer 2 + Layer 3 + fallback.

---

## Phase 6: User Story 4 - Conversational Natural-Language Semantic Search with Mandatory Allergen Safety (Priority: P2)

**Goal**: Deliver `POST /api/v1/dishes/search-semantic` supporting natural Vietnamese queries via Gemini 2.5 Flash Structured Output (`SemanticSearchIntent`) with deterministic Vietnamese regex fallback, fail-closed optional JWT auth, and mandatory routing through Layer 1 SQL Allergen Hard Filter (`EC5-03`, Huy).

**Independent Test**: Run `pytest tests/unit/test_recommendation_service.py -k semantic -v` verifying Gemini intent parsing, deterministic Vietnamese fallback parser (slang budget `"30k"`/`"25 cành"`, categories, dietary, query exclusions `"không đậu phộng"`), mandatory union of persisted `UserPreference.excluded_allergens` + `intent.query_excluded_allergens` in SQL Layer 1, and keyword + rescue ranking.

### Tests for User Story 4 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T020 [P] [US4] [EC5-03] Write unit tests in `backend/tests/unit/test_recommendation_service.py` covering `search_semantic` with `FakeGeminiRecommendationClient` (extracting `max_price`, `categories`, `dietary`, `query_excluded_allergens`, `keywords`, `urgent_only`), verifying `max_price` filtering against authoritative time-shifted `current_price`, verifying union of authenticated `UserPreference.excluded_allergens` + query exclusions is passed to `recommendation_repo.fetch_safe_candidates` (`0.0%` leakage), and verifying anonymous search (`user=None`) applies query-level exclusions cleanly
- [ ] T021 [P] [US4] [EC5-03] Write unit tests in `backend/tests/unit/test_recommendation_service.py` for `_extract_intent_fallback` (when Gemini is `None`/times out/errors) verifying Vietnamese budget regex (`"dưới 30k"`, `"tầm 25 cành"`, `"40 nghìn"`, `"35.000đ"`), category triggers (`"món nước nóng"`/`"phở"` → `NOODLES`, `"cơm"` → `RICE`, `"bánh mì"` → `BAKERY`, `"trà sữa"` → `BEVERAGE`, `"chay"` → `VEGETARIAN`), vegan/vegetarian detection, explicit `"không <allergen>"` negation, and `intent_source="FALLBACK"`

### Implementation for User Story 4

- [ ] T022 [US4] [EC5-03] Implement `search_semantic(...)`, Gemini `extract_semantic_intent` (`response_schema=SemanticSearchIntent`, `temperature=0.0`), deterministic Vietnamese `_extract_intent_fallback`, stricter-dietary & allergen-union merging, authoritative `max_price` filtering, and hybrid keyword + heuristic relevance ranking in `backend/app/services/recommendation_service.py`
- [ ] T023 [US4] [EC5-03] Add `POST /dishes/search-semantic` (`Depends(get_optional_current_user)`, `SemanticSearchRequest` → `SemanticSearchResponse`) in `backend/app/api/v1/endpoints/recommendations.py`

**Checkpoint**: User Story 4 (`EC5-03` Conversational Semantic Search) works for both public and authenticated users with mandatory SQL allergen safety and offline resilience.

---

## Phase 7: User Story 5 - Offline Evaluation Harness, Research Report & Allergen Safety QA Suite (Priority: P3)

**Goal**: Prove all 5 AI-2 KPIs via a reproducible 15–20 scenario Golden Dataset + runner + technical research report (`EC5-02`, Phúc) and harden production readiness with a dedicated Allergen Hard Invariant QA suite, full API/SLA integration suite, and PA5 AI Test Plan (`EC5-06`, Tony).

**Independent Test**: Run `pytest tests/integration/test_allergen_invariant.py tests/integration/test_api_recommendations.py -v` and `backend/venv_backend/bin/python ml/eval/eval_ai2_recommendation.py --dataset ml/eval/golden_ai2_dataset.json`, confirming `0.0%` Allergen Leakage, `NDCG@3 >= 0.85`, Semantic Intent `>= 90%`, Justification Faithfulness `>= 95%` (`0%` fabricated numbers), and Latency P95 `< 2.5s` / Fallback `< 300ms`.

### QA Integration & Invariant Tests (`EC5-06` — Đàng Thế Tony)

- [ ] T024 [P] [US5] [EC5-06] Create `backend/tests/integration/test_allergen_invariant.py` verifying strict **0.0% Allergen Leakage** across both `GET /api/v1/recommendations/personalized` and `POST /api/v1/dishes/search-semantic` for: all 14 `EUAllergen` categories, Vietnamese accented/unaccented/slang synonyms (`"đậu phộng"`, `"dau phong"`, `"lạc"`, `"hải sản"`), single & multi-allergen exclusions, dishes with allergens only in `menu_items.base_allergens` or legacy seeded strings, all-unsafe catalog returning `[]`, and a Hypothesis property-based test fuzzing random subsets of `EUAllergen`
- [ ] T025 [P] [US5] [EC5-06] Create `backend/tests/integration/test_api_recommendations.py` testing full REST contracts: `401`/`403` RBAC on `/recommendations/personalized`, fail-closed `401` on invalid/expired Bearer token for `/dishes/search-semantic`, `200 OK` public anonymous semantic search, `422` validation on invalid coordinates/radius/limit/blank query, graceful `200 OK` deterministic fallback on Gemini timeout/error/missing key asserting fallback latency `< 300ms`, and cold-start consumer ranking
- [ ] T026 [P] [US5] [EC5-06] Write comprehensive PA5 AI Safety, Resilience & Coverage Test Plan (`Allergen Hard Invariant` matrix, Gemini failure/fallback tests, SLA `< 3.0s` AI-1 / `< 2.5s` AI-2 / `< 300ms` fallback benchmarks, and roadmap to `>= 80%` repo coverage) in `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md`

### Offline Evaluation Harness & Research Report (`EC5-02` — Đặng Trọng Phúc)

- [ ] T027 [P] [US5] [EC5-02] Create Golden Dataset with 15–20 Vietnamese scenarios (10–12 Personalized Recommendation personas covering single/multi-allergen, `"Hải sản"`, legacy strings, vegan/vegetarian, budget student, urgent `-70%` final rush, cold-start, returning affinity, all-unsafe catalog + 6–8 Conversational Semantic Search queries) in `ml/eval/golden_ai2_dataset.json`
- [ ] T028 [US5] [EC5-02] Implement offline benchmark runner in `ml/eval/eval_ai2_recommendation.py` spinning up ephemeral in-memory SQLite scenarios through real `RecommendationRepository` + `RecommendationService` and computing all 5 KPIs: Allergen Leakage Rate (assert `0.0%`), `NDCG@3` (`>= 0.85`) & `Precision@3`, Semantic Intent Accuracy (`>= 90%`), Justification Faithfulness (`>= 95%`, `0%` fabricated numbers, `20–30` word compliance), and Latency P95 (`< 2.5s` Gemini / `< 300ms` fallback) + token/cost summary
- [ ] T029 [US5] [EC5-02] Run `ml/eval/eval_ai2_recommendation.py` (both live Gemini 2.5 Flash and fallback mode) and author technical deep-dive & baseline evaluation report (why Python-only filtering fails Guardrail #7, canonical `EUAllergen` + PostgreSQL JSONB/GIN + PostGIS GIST + SQLite JSON1 design, `(0.40/0.30/0.30)` sensitivity analysis, Layer 3 faithfulness guard & cache/fallback strategy, and observed 5-KPI benchmark table) in `docs/project_management/pa5_sprint5/research_ai2_recommendation_eval.md`

**Checkpoint**: All 5 KPIs are objectively measured and adversarial 0.0% allergen leakage is automated in CI.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Live Swagger validation with seeded HCMC data and guardrail hygiene audit.

- [ ] T030 Execute live Swagger E2E smoke test (`PUT /users/me/preferences` → `GET /recommendations/personalized` → `POST /dishes/search-semantic` public, authenticated & fail-closed `401`) against seeded HCMC data following `specs/006-ai-smart-recommendation-search/quickstart.md`
- [ ] T031 [P] Audit `backend/requirements.txt` (zero heavy ML training libraries: `ultralytics`, `jupyterlab`, `matplotlib`), confirm `RecommendationService` never imports `allergen_filter_service`, and check `git status` (no `.env` staged, no file `> 5 MB`)

---

## Final Phase: Verification Gate (Constitution Principle VIII) — MANDATORY

**Purpose**: Reproducible evidence that every Quality Gate passes. All commands MUST exit `0` before proposing a commit.

### Backend (`backend/`, using `venv_backend`)

- [ ] T032 `./venv_backend/bin/ruff check app/ tests/` — lint passes with zero findings
- [ ] T033 `./venv_backend/bin/ruff format --check app/ tests/` — formatting is canonical
- [ ] T034 `./venv_backend/bin/mypy app/` — static type-check passes with zero errors
- [ ] T035 `./venv_backend/bin/pytest tests/ -v` — full unit, integration, allergen-invariant, and property test suites pass with zero regressions

### Repository Hooks (repo root)

- [ ] T036 `pre-commit run --all-files` — secrets check, file size (`< 5 MB`), and formatting hooks pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Start immediately (`T001`–`T002`).
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories (`T003`–`T005`).
- **Phase 3 (US1 — `UserPreference` CRUD, `EC5-02`)**: Depends on `T003` (`T006`–`T010`).
- **Phase 4 (US2 — Layer 1 SQL Hard Filter, `EC5-02`)**: Depends on `T003` and can proceed immediately after or alongside `T008`–`T010` (`T011`–`T014`).
- **Phase 5 (US3 — Layer 2 Scoring + Layer 3 Gemini & Fallback, `EC5-03`)**: Depends on `T005`, Phase 3 (`preference_repo`), and Phase 4 (`recommendation_repo`) (`T015`–`T019`).
- **Phase 6 (US4 — Conversational Semantic Search, `EC5-03`)**: Depends on `T004` and Phase 5 (`T020`–`T023`).
- **Phase 7 (US5 — QA Invariant Suite `EC5-06` + Offline Eval `EC5-02`)**: `T026` and `T027` can be authored once Phase 2 contracts freeze; `T024`, `T025`, `T028`, `T029` execute once Phases 3–6 are complete.
- **Phase 8 (Polish)** & **Final Phase (Verification Gate)**: Depend on all selected phases completing.

### Within Each User Story (Strict TDD Loop)

1. Write unit/integration tests FIRST (`[P]` test tasks can be authored together) and confirm they FAIL (Red).
2. Implement Repository before Service, and Service before Router wiring.
3. Re-run tests to confirm PASS (Green) and refactor cleanly.

### Parallel Opportunities Across Team Lanes

```bash
# Phase 2 (Foundational) — disjoint files across Phúc & Huy:
T003 [EC5-02, Phúc]: backend/app/core/allergens.py
T004 [EC5-03, Huy]:  backend/app/api/deps.py (get_optional_current_user)
T005 [EC5-03, Huy]:  backend/app/schemas/recommendation.py

# Phase 7 (US5) — disjoint files across Tony & Phúc:
T024 [EC5-06, Tony]: backend/tests/integration/test_allergen_invariant.py
T025 [EC5-06, Tony]: backend/tests/integration/test_api_recommendations.py
T026 [EC5-06, Tony]: docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md
T027 [EC5-02, Phúc]: ml/eval/golden_ai2_dataset.json
```

---

## Implementation Strategy

### MVP First (Safety & Personalized Core — US1 + US2 + US3)

1. Complete Phase 1 (Setup: `T001`–`T002`) + Phase 2 (Foundational: `T003`–`T005`).
2. Complete Phase 3 (US1 `EC5-02`: `T006`–`T010`) + Phase 4 (US2 `EC5-02`: `T011`–`T014`) → **STOP & VALIDATE**: Consumer preferences persist canonically and Layer 1 SQL Hard Filter guarantees `0.0%` allergen leakage.
3. Complete Phase 5 (US3 `EC5-03`: `T015`–`T019`) → **STOP & VALIDATE**: `GET /api/v1/recommendations/personalized` runs end-to-end with 40/30/30 scoring, Gemini faithfulness guard, and `< 300ms` fallback.

### Incremental Delivery

1. MVP (US1 + US2 + US3) → Add Conversational Semantic Search (US4: `T020`–`T023`) → Run Allergen Invariant QA Suite (`EC5-06`: `T024`–`T026`) + Offline Golden Dataset Benchmark & Research Report (`EC5-02`: `T027`–`T029`) → Execute Live Smoke & Mandatory Verification Gate (`T030`–`T036`).
