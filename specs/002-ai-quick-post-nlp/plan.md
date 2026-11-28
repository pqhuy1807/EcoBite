# Implementation Plan: AI Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard

**Branch**: `feat/ai_1_quick_post` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-ai-quick-post-nlp/spec.md`

## Summary

Deliver the production-aligned **AI Feature 1 Baseline (`POST /api/v1/ml/parse-dish-nlp`)** and its **Offline Evaluation Suite** for EcoBite. The implementation refactors the Week-5 prototype into a strict 3-tier async FastAPI feature powered by **Google Gemini 2.5 Flash** (`google-genai==1.3.0`), adding `STORE_PARTNER` + approved-KYC access control, multimodal input (`audio_file` inline via `types.Part.from_bytes` up to 10 MB and/or `raw_text`), Menu-Catalog Grounding from `menu_repo` with deterministic anti-hallucination UUID validation and price inheritance, authoritative `Asia/Ho_Chi_Minh` server-time grounding, 2-tier EU FIC allergen classification (`EXPLICIT` vs `INFERRED`), cost-safe dual-key configuration (`GEMINI_TEST_API` vs `GEMINI_DEMO_API`), graceful `503` degradation, and a 15–20 case Vietnamese Golden Dataset benchmark (`ml/eval/eval_ai1_quick_post.py`) + research report (`docs/project_management/pa5_sprint5/research_ai1_quick_post_eval.md`).

## Architecture Overview & Component Relationships

- **Layer flow**: Client (Swagger / Next.js Store Portal in Sprint 5) → API Router (`backend/app/api/v1/endpoints/ml.py`: `require_roles(UserRole.STORE_PARTNER)`, multipart audio/text validation, HTTP status mapping) → Service layer (`backend/app/services/quick_post_service.py`: store/KYC verification, menu grounding, prompt assembly, async Gemini 2.5 Flash call, deterministic post-validation) → Read-only Data Access (`store_repo.get_store_by_owner_id`, `menu_repo.list_by_store`) → PostgreSQL 16 (production) / SQLite `aiosqlite` (dev & pytest). External AI integration: Google Gemini 2.5 Flash via `google-genai` async client (`client.aio.models.generate_content`).
- **Cross-cutting concerns**:
  - Role gating via `Depends(require_roles(UserRole.STORE_PARTNER))` and JWT verification via `get_current_user` in `backend/app/api/deps.py`.
  - Per-request async DB session via `DBSession` (`get_db`).
  - Environment-driven credentials & model config read solely from `app.core.config.settings` (`GEMINI_TEST_API`, `GEMINI_DEMO_API`, `GEMINI_USE_DEMO_KEY`, `GEMINI_MODEL`, `GEMINI_TIMEOUT_SECONDS`).
  - Structured logging via Python `logging` capturing `store_id`, input mode, latency, item count, and error class without logging secrets or audio binaries.
- **Affected components**:
  - `backend/app/core/config.py` & `backend/.env.example`: finalize Gemini settings (`gemini_key` stripping, formatting).
  - `backend/app/services/quick_post_service.py`: refactor into `GoogleGenAIQuickPostAdapter` + `QuickPostService.parse_dish_nlp(...)` with Menu Grounding, Server-Time Grounding, Native Audio, Post-Validation, and `QuickPostInputError` / `QuickPostUnavailableError`.
  - `backend/app/api/v1/endpoints/ml.py`: new canonical endpoint `POST /api/v1/ml/parse-dish-nlp` (`multipart/form-data`, RBAC, MIME/size checks, HTTP error mapping).
  - `backend/app/api/v1/endpoints/quick_post.py`: remove legacy prototype routes (`/quick-post/extract`, `/quick-post/allergen-filter/test`).
  - `backend/app/api/v1/router.py`: replace `quick_post.router` registration with `ml.router` under `prefix="/ml"`.
  - `backend/tests/unit/test_quick_post_service.py`: rewrite & expand unit tests (TDD) covering text, audio bytes, menu grounding, price inheritance, anti-hallucination UUID reset, allergen deduplication, server time, KYC/store guards, and failure modes.
  - `backend/tests/integration/test_api_ml.py`: integration tests for RBAC (`401`/`403`), KYC (`403`/`404`), multipart validation (`413`/`415`/`422`), `503` fallback, `200 OK` contract, and end-to-end handoff into `POST /api/v1/dishes/batch`.
  - `ml/eval/golden_ai1_dataset.json` & `ml/eval/eval_ai1_quick_post.py`: 15–20 Vietnamese benchmark cases + automated metric computation script.
  - `docs/project_management/pa5_sprint5/research_ai1_quick_post_eval.md`: AI-1 deep-dive research report & observed baseline metrics.
- **External integrations**:
  - **Google Gemini 2.5 Flash (`google-genai==1.3.0`)**: failure modes include missing API key, network outage, request timeout (`> GEMINI_TIMEOUT_SECONDS`), rate limit (`429`), malformed JSON/schema, hallucinated menu UUIDs, and inverted pickup times. Every failure mode is handled explicitly by `asyncio.wait_for`, schema validation, deterministic post-validation, and HTTP `503` degradation without crashing or corrupting DB state.

## Technical Context

**Language/Version**: Python 3.11+ (target `py311` in `backend/pyproject.toml`; local dev venv `backend/venv_backend`)

**Primary Dependencies**: FastAPI 0.111+, Pydantic v2 (`QuickPostExtractionResponse` in `app/schemas/nlp.py`), SQLAlchemy 2.0 (async), `google-genai==1.3.0`, `python-multipart`, `tzdata` (`zoneinfo.ZoneInfo`)

**Storage**: PostgreSQL 16 + PostGIS 3.4 (production/Docker) / SQLite `aiosqlite` (local dev & pytest); read-only access to `stores` and `menu_items` (no new migrations)

**Testing**: `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"`), `httpx.AsyncClient` ASGI integration tests with `backend/tests/conftest.py`, `ruff` (lint + format), `mypy` (`pydantic.mypy`)

**Target Platform**: FastAPI ASGI backend service (Linux Docker / macOS & Windows local dev) + offline CLI evaluation script in `ml/eval/`

**Project Type**: Backend web service extension + offline ML evaluation harness (Frontend UI deferred to Sprint 5 `EC5-04`)

**EcoBite Baseline (inherited from `constitution.md`)**: Python 3.11 · FastAPI (fully async) · Pydantic v2 · SQLAlchemy 2.0 async (`aiosqlite` for dev/test, `asyncpg` for PostgreSQL 16 + PostGIS) · JWT via `python-jose` HS256 · pytest + pytest-asyncio · ruff + mypy gates · Google Gemini 2.5 Flash

**Performance Goals**: End-to-end extraction P95 latency `< 3.0s` (NFR-001, SC-001); upstream timeout ceiling `15s` (`GEMINI_TIMEOUT_SECONDS`)

**Constraints**: Zero blocking I/O in async routes; `<= 10 MB` inline audio cap; `0%` fabricated/cross-store `matched_menu_id` pass-through; zero heavy training dependencies in `backend/requirements.txt`; zero secrets logged or committed

**Scale/Scope**: Single canonical ML endpoint (`POST /api/v1/ml/parse-dish-nlp`), supporting stores with 0 to >50 active menu items (50-item prompt cap with full-catalog post-validation), validated offline against 15–20 Golden Dataset cases

## Constitution Check

*GATE: Checked pre-design (Phase 0) and re-verified post-design (Phase 1) against `.specify/memory/constitution.md` (v1.2.0) and `AGENTS.md`.*

- [x] **Principle I (Test-First Development)**: `tasks.md` schedules unit tests (`test_quick_post_service.py`) and integration tests (`test_api_ml.py`) BEFORE implementation inside each User Story phase (Red-Green-Refactor).
- [x] **Principle II (Security, Privacy & Access Control)**: Endpoint protected by `Depends(require_roles(UserRole.STORE_PARTNER))` + store ownership & `APPROVED` KYC check; Gemini keys loaded solely via `pydantic-settings` (`GEMINI_TEST_API` / `GEMINI_DEMO_API` / `GEMINI_USE_DEMO_KEY`) and never logged; legacy unauthenticated `/quick-post/allergen-filter/test` removed.
- [x] **Principle III (Data Integrity & Transactional Consistency)**: Quick-Post is read-only; no mutations occur until the partner reviews drafts and calls the existing transactional `POST /api/v1/dishes/batch`.
- [x] **Principle IV (Food Safety & Allergen Protection)**: All 14 EU FIC allergens mapped via `EUAllergen`; `EXPLICIT` vs `INFERRED` distinction strictly preserved and never silently dropped; no consumer-style dish removal during partner Quick-Post.
- [x] **Principle V (Deterministic Business Rules)**: AI never guesses discounted prices—`override_discounted_price` stays `None` unless spoken by the partner so `DishService` applies deterministic time-based discount rules; `original_price` is authoritatively inherited from `menu_items`.
- [x] **Principle VI (AI Reliability, Structured Output & Model Isolation)**: Uses `gemini-2.5-flash` via `google-genai` with `response_schema=QuickPostExtractionResponse`, Menu-Catalog Grounding with deterministic UUID anti-hallucination verification, authoritative `Asia/Ho_Chi_Minh` server clock (ignoring unverified client clocks), and zero heavy ML training packages added to `backend/requirements.txt`.
- [x] **Principle VII (Clean Architecture & Async End-to-End)**: Strict `Router (ml.py) -> Service (quick_post_service.py) -> Repository (store_repo, menu_repo)` separation; async `client.aio.models.generate_content` avoids blocking I/O in FastAPI event loop.
- [x] **Principle VIII (Verifiable Quality & Human Accountability)**: Mandatory Final Verification Gate runs `ruff check`, `ruff format --check`, `mypy app/`, `pytest tests/ -v`, and `pre-commit` before commit proposal.

## Project Structure

### Documentation (this feature)

```text
specs/002-ai-quick-post-nlp/
├── spec.md              # Feature specification (/speckit-specify)
├── plan.md              # This file (/speckit-plan)
├── research.md          # Phase 0 design decisions (/speckit-plan)
├── data-model.md        # Entities, schemas & constraints (/speckit-plan)
├── quickstart.md        # Runnable validation guide (/speckit-plan)
├── checklists/
│   └── requirements.md  # Spec quality validation checklist
├── contracts/
│   └── api-contracts.md # REST contract & error matrix
└── tasks.md             # Dependency-ordered TDD tasks (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── .env.example                                 # Documented Gemini env vars (no secrets)
├── app/
│   ├── core/
│   │   └── config.py                            # GEMINI_TEST_API, GEMINI_DEMO_API, GEMINI_USE_DEMO_KEY, GEMINI_MODEL, GEMINI_TIMEOUT_SECONDS
│   ├── schemas/
│   │   └── nlp.py                               # Existing QuickPostExtractionResponse, SurplusDishItem, NLPAllergenWarning, EUAllergen
│   ├── repositories/
│   │   ├── store_repo.py                        # Reused: get_store_by_owner_id()
│   │   └── menu_repo.py                         # Reused: list_by_store(active_only=True)
│   ├── services/
│   │   └── quick_post_service.py                # Refactored: GoogleGenAIQuickPostAdapter, QuickPostService.parse_dish_nlp(), post-validation
│   └── api/
│       └── v1/
│           ├── router.py                        # Register ml.router (/ml), remove quick_post.router
│           └── endpoints/
│               ├── ml.py                        # New: POST /api/v1/ml/parse-dish-nlp (STORE_PARTNER, multipart/form-data)
│               └── quick_post.py                # Removed legacy prototype router
└── tests/
    ├── unit/
    │   └── test_quick_post_service.py           # TDD unit suite (mock Gemini client + SQLite store/menu fixtures)
    └── integration/
        └── test_api_ml.py                       # TDD API contract, RBAC, audio validation, 503 & batch-handoff tests

ml/
└── eval/
    ├── audio/                                   # Short Vietnamese voice clips (.m4a/.wav) < 5MB each for benchmark
    ├── golden_ai1_dataset.json                  # 15–20 curated Vietnamese Quick-Post ground-truth cases
    └── eval_ai1_quick_post.py                   # Offline benchmark runner computing 6 Week-6 KPIs

docs/
└── project_management/
    └── pa5_sprint5/
        └── research_ai1_quick_post_eval.md      # Deep-dive research report + baseline benchmark results
```

**Structure Decision**: Extends the existing EcoBite 3-tier backend layout (`backend/app/{core,schemas,repositories,services,api/v1/endpoints}` + `backend/tests/{unit,integration}`) and places offline evaluation artifacts under `ml/eval/` and `docs/project_management/pa5_sprint5/` per `AGENTS.md` Section 3 and the Week 6 Action Plan.

## Complexity Tracking

No Constitution violations. All 8 Core Principles and all 8 Guardrails in `AGENTS.md` are satisfied without exceptions.
