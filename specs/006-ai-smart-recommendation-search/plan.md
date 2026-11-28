# Implementation Plan: AI Smart Food Recommendation Engine & Conversational Semantic Search

**Branch**: `feat/ai-2-recommendation` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-ai-smart-recommendation-search/spec.md`

## Summary

Deliver EcoBite's **AI Feature 2 — Smart Food Recommendation Engine & Conversational Semantic Search** (`EC5-02`, `EC5-03`, `EC5-06`), enforcing **Guardrail #7 (Allergen Hard Invariant — 0.0% Leakage)** strictly at the database query layer. The implementation adds:
1. **Canonical Allergen Normalization & `UserPreference` CRUD (`EC5-02` — Đặng Trọng Phúc)**: `backend/app/core/allergens.py` (14 `EUAllergen` canonical keys + bilingual/Vietnamese synonym & `"Hải sản"` expansion), `backend/app/repositories/preference_repo.py`, schema validation in `backend/app/schemas/user_preference.py`, and `GET`/`PUT /api/v1/users/me/preferences` (`CONSUMER`) in `backend/app/api/v1/endpoints/users.py`.
2. **Layer 1 — SQL & PostGIS Allergen Hard Filter (`EC5-02` — Đặng Trọng Phúc)**: `backend/app/repositories/recommendation_repo.py` executing a single SQL query joining `dishes`, `stores`, and `LEFT OUTER JOIN menu_items` with `Store.kyc_status == APPROVED`, `Dish.status == ACTIVE`, `Dish.remaining_quantity > 0`, active `Asia/Ho_Chi_Minh` pickup window, PostGIS `ST_DWithin`/`ST_Distance` (`1–10 km`, portable SQLite Haversine parity), dietary lifestyle filtering, and **SQL-level `WHERE NOT EXISTS` allergen exclusion** (PostgreSQL JSONB `jsonb_array_elements` / `@>` + portable SQLite JSON1 `json_each` — explicitly superseding the Week-5 Python-only `allergen_filter_service.py` draft).
3. **Layer 2 Heuristic Scoring, Layer 3 Gemini Justification + Fallback & Conversational Semantic Search (`EC5-03` — Phùng Quốc Huy)**: `backend/app/schemas/recommendation.py`, `backend/app/services/recommendation_service.py` (deterministic `0.40 * proximity + 0.30 * discount_urgency + 0.30 * taste_match` scoring, async `google-genai` Gemini 2.5 Flash justification with dual-key config + numeric faithfulness guard + `< 300ms` deterministic template fallback, and semantic intent extraction + regex fallback), and `backend/app/api/v1/endpoints/recommendations.py` (`GET /api/v1/recommendations/personalized` + `POST /api/v1/dishes/search-semantic` with fail-closed optional auth in `backend/app/api/deps.py`).
4. **Offline Benchmark, Research Report & QA Safety Invariant Suite (`EC5-02` / `EC5-06` — Đặng Trọng Phúc & Đàng Thế Tony)**: `ml/eval/golden_ai2_dataset.json`, `ml/eval/eval_ai2_recommendation.py`, `docs/project_management/pa5_sprint5/research_ai2_recommendation_eval.md`, `backend/tests/integration/test_allergen_invariant.py`, `backend/tests/integration/test_api_recommendations.py`, and `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md`.

## Why Week-5 Python-Only `allergen_filter_service.py` MUST Be Replaced by SQL-Level Hard Filtering

The Week-5 draft `backend/app/services/allergen_filter_service.py` filters in-memory Python `list[dict]` structures using naive substring matching (`ua in da or da in ua`). Using it as the primary recommendation filter directly violates **AGENTS.md Guardrail #7** and **EcoBite Constitution Principle IV** (*"The recommendation engine MUST enforce `excluded_allergens` as a hard filter at the database query level before generating AI explanations"*) for four concrete engineering reasons:
1. **Boundary & Defense-in-Depth Violation**: Any query returning `Dish` rows before Python filtering leaks allergen-contaminated objects across the repository boundary, creating a systemic risk whenever another endpoint, cache, or service reuses the repository.
2. **Broken `LIMIT` / Pagination Semantics**: Applying `LIMIT N` in SQL and filtering allergens afterward in Python can return fewer than `K` (or zero) dishes even when safe dishes exist later in the result set; avoiding truncation forces unbounded full-table loads into Python memory.
3. **Lost Database Index Acceleration**: Python filtering cannot utilize PostgreSQL's `GIN` index (`idx_dishes_allergens_gin`) combined with PostGIS's spatial `GIST` index (`idx_stores_location`) inside one query plan.
4. **False Matches & Missing Safety Coverage**: Substring matching (`ua in da`) fails on composite Vietnamese terms (`"Hải sản"` does not substring-match `"Crustaceans (Tôm)"` or `"Fish (Nước mắm)"`), misses regional synonyms (`"lạc"` vs `"đậu phộng"`), risks false substring collisions on short unaccented tokens (`"ca"` inside `"can tay"`), and ignores `menu_items.base_allergens` inherited by seeded dishes.

**Migration Strategy**: `RecommendationRepository` (`recommendation_repo.py`) enforces 100% SQL-level allergen exclusion across both PostgreSQL (`jsonb_array_elements` / `@>`) and SQLite (`json_each`), checking BOTH `dishes.allergens` AND `menu_items.base_allergens`. The legacy `allergen_filter_service.py` and its unit test `test_allergen_filter_service.py` are explicitly marked deprecated (unused by `RecommendationService`) so existing CI tests stay green without blocking the PR, and may be retired once PA5 stabilizes.

## Architecture Overview & Component Relationships

- **Layer flow (`Router -> Service -> Repository`)**:
  - **Preferences flow (`EC5-02`)**: Client → `users.py` (`GET`/`PUT /api/v1/users/me/preferences`, `Depends(require_roles(UserRole.CONSUMER))`) → `preference_repo.py` + `allergens.py` normalizer → `user_preferences` table.
  - **Personalized Recommendations flow (`EC5-02` + `EC5-03`)**: Client → `recommendations.py` (`GET /api/v1/recommendations/personalized`, `Depends(require_roles(UserRole.CONSUMER))`) → `RecommendationService` →
    - **Layer 1 (SQL Hard Invariant)**: `preference_repo.get_by_user_id` → `allergens.expand_excluded_sql_tokens` → `recommendation_repo.fetch_safe_candidates` (SQL `WHERE` + PostGIS `ST_DWithin` / SQLite Haversine + `NOT EXISTS` on `dishes.allergens` and `menu_items.base_allergens` + `dietary_preference`).
    - **Layer 2 (Deterministic Scoring)**: `OrderRepository.list_by_consumer(order_status=COMPLETED, limit=20)` + `DishService.calculate_time_shifted_discount` (authoritative `Asia/Ho_Chi_Minh` clock) → `0.40 * proximity + 0.30 * discount_urgency + 0.30 * taste_match` → deterministic Top-K (`K=3`).
    - **Layer 3 (Gemini Justification + Fallback)**: `GoogleGenAIRecommendationAdapter` (`client.aio.models.generate_content`, bounded timeout `<= 2.0s`, structured schema) → `_validate_justification_faithfulness` → deterministic Vietnamese template fallback on any error/timeout/hallucination.
  - **Conversational Semantic Search flow (`EC5-03`)**: Client → `recommendations.py` (`POST /api/v1/dishes/search-semantic`, `Depends(get_optional_current_user)` — fail-closed `401` on invalid JWT) → `RecommendationService.search_semantic` → Gemini Structured Output intent extraction (`SemanticSearchIntent`) with deterministic Vietnamese regex fallback → merges `UserPreference.excluded_allergens ∪ intent.query_excluded_allergens` & stricter dietary lifestyle → **MANDATORY Layer 1 SQL Hard Filter** (`recommendation_repo.fetch_safe_candidates`) → Layer 2 hybrid keyword + heuristic ranking.
- **Cross-cutting concerns**:
  - Role gating (`require_roles(UserRole.CONSUMER)`) and new fail-closed `get_optional_current_user` in `backend/app/api/deps.py`.
  - Router registration order in `backend/app/api/v1/router.py`: register `recommendations.router` **before** `stores.router` to prevent any interference from `stores.router`'s legacy root wildcard `GET /{store_id}`.
  - Dual-key Gemini config via `app.core.config.settings` (`GEMINI_TEST_API`, `GEMINI_DEMO_API`, `GEMINI_USE_DEMO_KEY`, `GEMINI_MODEL`, `GEMINI_TIMEOUT_SECONDS`, plus bounded `GEMINI_RECOMMENDATION_TIMEOUT_SECONDS: float = 2.0`).
  - Optional short-TTL Redis caching (`app.core.redis.get_redis`, graceful degradation when Redis is down) for identical Layer 3 justifications/intents keyed by `(dish_ids, price_bucket, taste_hash)` — never caching across different `excluded_allergens` profiles!
- **Affected components**:
  - **New files**:
    - `backend/app/core/allergens.py` (`EC5-02`, Phúc)
    - `backend/app/repositories/preference_repo.py` (`EC5-02`, Phúc)
    - `backend/app/repositories/recommendation_repo.py` (`EC5-02`, Phúc)
    - `backend/app/schemas/recommendation.py` (`EC5-03`, Huy)
    - `backend/app/services/recommendation_service.py` (`EC5-03`, Huy)
    - `backend/app/api/v1/endpoints/recommendations.py` (`EC5-03`, Huy)
    - `backend/tests/unit/test_preference_repo.py` (`EC5-02`, Phúc)
    - `backend/tests/unit/test_recommendation_repo.py` (`EC5-02`, Phúc)
    - `backend/tests/unit/test_recommendation_service.py` (`EC5-03`, Huy)
    - `backend/tests/integration/test_api_preferences.py` (`EC5-02`, Phúc)
    - `backend/tests/integration/test_api_recommendations.py` (`EC5-06`, Tony)
    - `backend/tests/integration/test_allergen_invariant.py` (`EC5-06`, Tony)
    - `ml/eval/golden_ai2_dataset.json` (`EC5-02`, Phúc)
    - `ml/eval/eval_ai2_recommendation.py` (`EC5-02`, Phúc)
    - `docs/project_management/pa5_sprint5/research_ai2_recommendation_eval.md` (`EC5-02`, Phúc)
    - `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md` (`EC5-06`, Tony)
  - **Modified files**:
    - `backend/app/core/config.py` & `backend/.env.example`: add `GEMINI_RECOMMENDATION_TIMEOUT_SECONDS: float = Field(default=2.0, gt=0)`.
    - `backend/app/schemas/user_preference.py`: add canonical `preferred_categories` & `excluded_allergens` validation/normalization on write schemas (`UserPreferenceCreate`, `UserPreferenceUpdate`) while keeping `UserPreferenceResponse` backward-compatible with legacy ORM rows (`test_cluster1_models.py`).
    - `backend/app/api/deps.py`: add `oauth2_scheme_optional` (`auto_error=False`) and `get_optional_current_user` (returns `None` when no `Authorization` header; raises `401` if a malformed/expired Bearer token is sent).
    - `backend/app/api/v1/endpoints/users.py`: add `GET /me/preferences` and `PUT /me/preferences` (`CONSUMER`).
    - `backend/app/api/v1/router.py`: register `recommendations.router` before `stores.router`.
    - `backend/app/services/allergen_filter_service.py`: add deprecation docstring pointing to `recommendation_repo.py` (preserving existing test compatibility).
- **External integrations**:
  - **Google Gemini 2.5 Flash (`google-genai==1.3.0`)**: failure modes include missing key, upstream latency `> 2.0s`, network failure, rate limit (`429`), schema mismatch, partial justifications, and hallucinated numeric values. Every failure mode is contained by `asyncio.wait_for`, Pydantic validation, `_validate_justification_faithfulness`, and `< 300ms` deterministic fallbacks—never crashing or compromising safety.

## Technical Context

**Language/Version**: Python 3.11+ (`target-version = "py311"` in `backend/pyproject.toml`; local dev venv `backend/venv_backend` / `backend/.venv`)

**Primary Dependencies**: FastAPI 0.111+, Pydantic v2, SQLAlchemy 2.0 (async), GeoAlchemy2 0.15.1, `google-genai==1.3.0`, `redis==5.0.6` (optional graceful-degrade cache), `tzdata` (`zoneinfo.ZoneInfo`), `hypothesis==6.98.3` (for allergen invariant fuzzing)

**Storage**: PostgreSQL 16 + PostGIS 3.4 (production/Docker, JSONB + GIN/GIST indexes) / SQLite `aiosqlite` + JSON1 (`json_each`, in-memory pytest); reuses existing `user_preferences`, `dishes`, `stores`, `menu_items`, and `orders` tables (**zero schema-breaking migrations required**; optional non-breaking PostgreSQL GIN/GIST index migration documented in `data-model.md`)

**Testing**: `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"`), `hypothesis`, `httpx.AsyncClient` ASGI integration tests with `backend/tests/conftest.py`, `ruff` (lint + format), `mypy` (`pydantic.mypy`)

**Target Platform**: FastAPI ASGI backend service (Linux Docker / macOS & Windows local dev) + offline CLI evaluation script in `ml/eval/`

**Project Type**: Backend web service extension + offline ML evaluation harness + safety QA test suite (Frontend UI tracked separately under `EC5-05`)

**EcoBite Baseline (inherited from `constitution.md`)**: Python 3.11 · FastAPI (fully async) · Pydantic v2 · SQLAlchemy 2.0 async (`aiosqlite` for dev/test, `asyncpg` for PostgreSQL 16 + PostGIS) · JWT via `python-jose` HS256 · pytest + pytest-asyncio + Hypothesis · ruff + mypy gates · Google Gemini 2.5 Flash

**Performance Goals**: End-to-end P95 latency `< 2.5s` (with live Gemini) and `< 300ms` (deterministic fallback); Layer 1 SQL query `< 100ms`

**Constraints**: Strict `0.0%` Allergen Leakage Rate at SQL layer; `0%` fabricated numeric values in `ai_justification`; zero blocking I/O in async routes; zero heavy ML training packages in `backend/requirements.txt`; zero secrets logged or committed; fail-closed `401` on invalid Bearer token during semantic search

**Scale/Scope**: 4 REST endpoints (`GET`/`PUT /users/me/preferences`, `GET /recommendations/personalized`, `POST /dishes/search-semantic`), 14 canonical EU FIC allergens + bilingual/Vietnamese synonym table, Top-K (`K=3`, max `10`) personalized results, up to `30` semantic search results, validated offline against 15–20 Golden Dataset scenarios

## Constitution Check

*GATE: Checked pre-design (Phase 0) and re-verified post-design (Phase 1) against `.specify/memory/constitution.md` (v1.2.0) and `AGENTS.md`.*

- [x] **Principle I (Test-First Development)**: `tasks.md` schedules unit, repository, integration, and allergen-invariant tests BEFORE implementation inside every User Story phase (Red-Green-Refactor).
- [x] **Principle II (Security, Privacy & Access Control)**: `GET`/`PUT /users/me/preferences` and `GET /recommendations/personalized` require `Depends(require_roles(UserRole.CONSUMER))`; `POST /dishes/search-semantic` uses fail-closed `get_optional_current_user` (`401` on bad JWT); Gemini keys read solely from `pydantic-settings` (`GEMINI_TEST_API` / `GEMINI_DEMO_API`) and never logged; prompts exclude user PII.
- [x] **Principle III (Data Integrity & Transactional Consistency)**: `preference_repo.upsert_for_user` executes atomic upsert with commit/refresh; recommendation and search endpoints are strictly read-only on `dishes`/`stores`/`orders`.
- [x] **Principle IV (Food Safety & Allergen Protection)**: Layer 1 SQL `WHERE NOT EXISTS` eliminates 100% of excluded allergens across both `dishes.allergens` and `menu_items.base_allergens` before scoring or AI invocation; Gemini NEVER decides safety; 2-tier `EXPLICIT`/`INFERRED` warnings stay intact on returned dishes; justifications never make ungrounded medical guarantees.
- [x] **Principle V (Deterministic Business Rules)**: Pricing, discount percentage, and final-rush urgency flags come exclusively from `DishService.calculate_time_shifted_discount` using authoritative `Asia/Ho_Chi_Minh` time; Layer 2 ranking formula (`0.40 / 0.30 / 0.30`) is 100% deterministic.
- [x] **Principle VI (AI Reliability, Structured Output & Model Isolation)**: Uses `gemini-2.5-flash` via async `google-genai` with Pydantic Structured Outputs (`RecommendationJustificationBatch`, `SemanticSearchIntent`), bounded timeout, faithfulness validator, deterministic fallback, and zero heavy ML training packages added to `backend/requirements.txt`.
- [x] **Principle VII (Clean Architecture & Async End-to-End)**: Strict `Router (users.py, recommendations.py) -> Service (recommendation_service.py) -> Repository (preference_repo.py, recommendation_repo.py, order_repo.py)` separation; async `AsyncSession` and async `client.aio.models.generate_content` with zero blocking I/O.
- [x] **Principle VIII (Verifiable Quality & Human Accountability)**: Mandatory Final Verification Gate runs `ruff check`, `ruff format --check`, `mypy app/`, `pytest tests/ -v` (including `test_allergen_invariant.py`), and `pre-commit run --all-files` before any commit proposal.

## Project Structure

### Documentation (this feature)

```text
specs/006-ai-smart-recommendation-search/
├── spec.md              # Feature specification (/speckit-specify)
├── plan.md              # This file (/speckit-plan)
├── research.md          # Phase 0 design decisions (/speckit-plan)
├── data-model.md        # Entities, schemas, SQL patterns & constraints (/speckit-plan)
├── quickstart.md        # Runnable validation guide (/speckit-plan)
├── checklists/
│   └── requirements.md  # Spec quality validation checklist
├── contracts/
│   └── api-contracts.md # REST contracts & error matrices (4 endpoints)
└── tasks.md             # Dependency-ordered TDD tasks (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── .env.example                                     # Document GEMINI_RECOMMENDATION_TIMEOUT_SECONDS
├── app/
│   ├── core/
│   │   ├── allergens.py                             # New [EC5-02]: Canonical 14 EU FIC normalizer + VI synonyms + SQL match tokens
│   │   └── config.py                                # Add GEMINI_RECOMMENDATION_TIMEOUT_SECONDS = 2.0
│   ├── schemas/
│   │   ├── user_preference.py                       # Add canonical allergen & category validation on write schemas
│   │   └── recommendation.py                        # New [EC5-03]: PersonalizedRecommendationResponse, ScoreBreakdown, SemanticSearchRequest/Response, Gemini structured outputs
│   ├── repositories/
│   │   ├── preference_repo.py                       # New [EC5-02]: Async UserPreference get/upsert repository
│   │   └── recommendation_repo.py                   # New [EC5-02]: Layer 1 SQL/PostGIS + JSONB/SQLite JSON1 Allergen Hard Filter repository
│   ├── services/
│   │   ├── allergen_filter_service.py               # Deprecation notice pointing to recommendation_repo.py (preserves legacy unit test)
│   │   └── recommendation_service.py                # New [EC5-03]: Layer 2 Heuristic Scoring, Layer 3 Gemini Justification + Faithfulness Guard + Fallback, Semantic Search
│   └── api/
│       ├── deps.py                                  # Add fail-closed get_optional_current_user dependency
│       └── v1/
│           ├── router.py                            # Register recommendations.router before stores.router
│           └── endpoints/
│               ├── users.py                         # Add GET/PUT /api/v1/users/me/preferences [EC5-02]
│               └── recommendations.py               # New [EC5-03]: GET /recommendations/personalized, POST /dishes/search-semantic
└── tests/
    ├── unit/
    │   ├── test_preference_repo.py                  # New [EC5-02]: Allergen normalizer & preference upsert unit tests
    │   ├── test_recommendation_repo.py              # New [EC5-02]: Layer 1 SQL WHERE allergen/PostGIS/window/dietary unit tests
    │   └── test_recommendation_service.py           # New [EC5-03]: Layer 2 scoring math, Layer 3 faithfulness/fallback, semantic intent unit tests
    └── integration/
        ├── test_api_preferences.py                  # New [EC5-02]: GET/PUT /users/me/preferences RBAC & normalization tests
        ├── test_api_recommendations.py              # New [EC5-06]: Personalized & semantic API contract, RBAC, fail-closed 401, fallback & SLA tests
        └── test_allergen_invariant.py               # New [EC5-06]: Adversarial & Hypothesis 0.0% Allergen Leakage invariant suite

ml/
└── eval/
    ├── golden_ai2_dataset.json                      # New [EC5-02]: 15–20 Vietnamese persona & semantic search benchmark cases
    └── eval_ai2_recommendation.py                   # New [EC5-02]: Offline benchmark runner computing all 5 Week-6 KPIs

docs/
└── project_management/
    └── pa5_sprint5/
        ├── research_ai2_recommendation_eval.md      # New [EC5-02]: AI-2 deep-dive design & observed baseline evaluation report
        └── 03_PA5_AI_Test_Plan.md                   # New [EC5-06]: Comprehensive PA5 AI safety, SLA & >=80% coverage test plan
```

**Structure Decision**: Extends the established 3-tier EcoBite backend structure (`core`, `schemas`, `repositories`, `services`, `api/v1/endpoints`, `tests/{unit,integration}`) with disjoint file ownership across team lanes: Đặng Trọng Phúc owns `core/allergens.py`, `preference_repo.py`, `recommendation_repo.py`, `endpoints/users.py`, `ml/eval/*ai2*`, and `research_ai2_recommendation_eval.md` (`EC5-02`); Phùng Quốc Huy owns `schemas/recommendation.py`, `recommendation_service.py`, `endpoints/recommendations.py`, and `api/deps.py` optional auth (`EC5-03`); Đàng Thế Tony owns `test_allergen_invariant.py`, `test_api_recommendations.py`, and `03_PA5_AI_Test_Plan.md` (`EC5-06`).

## Complexity Tracking

No Constitution violations. All 8 Core Principles and all 8 Guardrails in `AGENTS.md` (with special focus on Guardrail #7 Allergen Hard Invariant) are satisfied without exceptions.
