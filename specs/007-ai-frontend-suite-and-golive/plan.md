# Implementation Plan: AI Frontend Experience Suite, AI Safety QA & Release 1.0 Go-Live

**Branch**: `feat/pa5-ai-frontend-qa-golive` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-ai-frontend-suite-and-golive/spec.md`

## Summary

Complete **EcoBite PA5 Sprint 5 (`EC5-04`, `EC5-05`, `EC5-06`, `EC5-07`)** to ship **Release 1.0 (Production / Final Acceptance)**:

1. **Merchant AI Quick-Post UI (`EC5-04` — Võ Ngọc Thịnh, Reviewer: Phùng Quốc Huy)**: Build `frontend/src/services/ml.service.ts`, browser `MediaRecorder` hook (`frontend/src/hooks/useVoiceRecorder.ts`), and interactive Voice/Text Quick-Post + 2-Tier Allergen Draft Cards Editor (`frontend/src/components/quick-post/`) integrated into `frontend/src/app/store/dishes/page.tsx` with 1-Tap Batch Publish via existing `dishService.batchCreateSurplusDishes` (`POST /api/v1/dishes/batch`) and seamless `503` manual fallback.
2. **Consumer AI Discovery & Allergen Profile UI (`EC5-05` — Võ Ngọc Thịnh, Reviewer: Đặng Trọng Phúc)**: Build `frontend/src/services/preference.service.ts`, `frontend/src/services/recommendation.service.ts`, the 14 EU FIC Allergen & Taste Preferences page (`frontend/src/app/profile/preferences/page.tsx`), the Smart Recommendations Top 3 Carousel (`frontend/src/components/recommendations/SmartRecommendationsCarousel.tsx`), and the Conversational Semantic Search Bar (`frontend/src/components/search/SemanticSearchBar.tsx`) integrated into `frontend/src/app/page.tsx` alongside `DynamicRadarMap`, `DishCard`, `OrderModal`, `Navbar.tsx`, and `BottomNavigation.tsx`.
3. **AI Safety, Resilience, SLA & Coverage QA Suite (`EC5-06` — Đàng Thế Tony, Reviewer: Phùng Quốc Huy)**: Author `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md`, implement `backend/tests/integration/test_allergen_invariant.py` (0.0% allergen leakage across Personalized & Semantic Search), expand resilience & SLA benchmark suites (`backend/tests/integration/test_api_ml.py`, `backend/tests/integration/test_api_recommendations.py`), add Vitest + Testing Library component/hook tests in `frontend/__tests__/`, and enforce `>= 80%` project-wide test coverage (`pytest-cov` + `@vitest/coverage-v8`).
4. **Full-System UAT, Docker Compose Go-Live & Release 1.0 (`EC5-07` — Whole Team, PM: Phùng Quốc Huy)**: Add multi-stage `frontend/Dockerfile`, extend root `docker-compose.yml` to run all 4 services (`postgres`, `redis`, `backend`, `frontend`) with healthchecks, run full E2E UAT across Core F1–F8 + AI-1 & AI-2, and deliver `docs/PA5.md`, `docs/PA5.pdf`, tag `v1.0.0`, and the Final Go-Live Demo Video before Internal Deadline `2026-12-11` (`23:59`) / Moodle `2026-12-12`.

## Architecture Overview & Component Relationships

- **Store Partner Quick-Post Flow (`EC5-04`)**:
  `StoreSurplusDishesPage` (`/store/dishes`) → `VoiceQuickPostPanel` (uses `useVoiceRecorder` hook with `MediaRecorder` `audio/webm;codecs=opus` / `audio/mp4` fallback + text fallback) → `mlService.parseDishNlp(FormData)` (`@/lib/api-client`, 20s timeout) → `POST /api/v1/ml/parse-dish-nlp` → `QuickPostDraftEditor` (renders `DraftDishCard` items with `AllergenBadge` Red=`EXPLICIT` / Amber=`INFERRED`, catalog dropdown when `matched_menu_id === null`, inline qty/override price edit, `missing_fields_warning` banners) → `dishService.batchCreateSurplusDishes` → `POST /api/v1/dishes/batch` (`201 Created`) → refreshes active dishes list. On `503`, smoothly hands off to the existing manual single-dish form while keeping text notes intact.
- **Consumer Smart Discovery & Preferences Flow (`EC5-05`)**:
  - **Preferences**: `Navbar` / `BottomNavigation` (`CONSUMER`) → `/profile/preferences` (`AuthGuard allowedRoles={['CONSUMER']}`) → `AllergenPreferencesForm` (14 EU FIC bilingual checkboxes from shared `frontend/src/lib/allergens.ts`, `DietaryPreference`, `FoodCategory` chips, `max_budget` VND) → `useQuery`/`useMutation` via `preferenceService.getMyPreferences()` / `updateMyPreferences()` → `GET`/`PUT /api/v1/users/me/preferences` → invalidates `['preferences', 'me']`, `['recommendations', 'personalized']`, and `['dishes', 'semantic-search']` in TanStack React Query.
  - **Discovery Home (`/`)**: Server shell or lean client container integrating `SmartRecommendationsCarousel` (`useQuery` → `recommendationService.getPersonalized(lat, lng, limit=3)` → `GET /api/v1/recommendations/personalized`, enabled only for authenticated `CONSUMER`) + `SemanticSearchBar` (`useMutation` → `recommendationService.searchSemantic(query, lat, lng)` → `POST /api/v1/dishes/search-semantic`, public or authenticated) → feeds normalized `RescueDishItem[]` into `DishCard`, `DynamicRadarMap`, and `OrderModal` (removing duplicate inline header and legacy "túi bất ngờ" copy).
- **QA & Safety Verification Architecture (`EC5-06`)**:
  - Backend: `pytest` + `pytest-asyncio` + `pytest-cov` running against isolated SQLite in-memory (`backend/tests/conftest.py`) with injectable fake Gemini clients for deterministic safety/resilience assertions (`test_allergen_invariant.py`, `test_api_ml.py`, `test_api_recommendations.py`) plus optional live SLA benchmark marker/harness.
  - Frontend: `vitest` + `@testing-library/react` + `@testing-library/jest-dom` + `jsdom` + `@vitest/coverage-v8` mocking `MediaRecorder`, `navigator.mediaDevices`, and service modules (`mlService`, `dishService`, `preferenceService`, `recommendationService`).
- **Containerized Release 1.0 Packaging (`EC5-07`)**:
  - `docker-compose.yml` orchestrates `postgres` (`postgis/postgis:16-3.4-alpine`, port `5432`), `redis` (`redis:7-alpine`, port `6379`), `backend` (`./backend/Dockerfile`, port `8000`, healthcheck `GET /health`), and `frontend` (`./frontend/Dockerfile`, port `3000`, depends on `backend` healthy, `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`), all joined on `ecobite_network`.
- **Cross-cutting concerns**:
  - Auth & RBAC: Frontend uses `AuthGuard` + role-filtered `Navbar`/`BottomNavigation`; Backend remains the authoritative security boundary (`require_roles(...)`, KYC checks, JWT `HS256`).
  - HTTP & Multipart: All client requests flow exclusively through `@/lib/api-client` (Bearer token injection, automatic `401` refresh, automatic `Content-Type` removal for `FormData`).
  - Client State & Caching: TanStack React Query (`@tanstack/react-query` v5 via `QueryProvider.tsx`) manages server state, loading/error states, and cross-page cache invalidation (crucial for allergen preference changes).
  - Accessibility & Safety UX: 2-tier allergen badges pair color + icon + Vietnamese source label + tooltip rationale + AI-inferred disclaimer.

## Technical Context

**Language/Version**: TypeScript 5.4 (`strict: true`, Next.js 14.2 App Router, React 18.3) · Python 3.11 (FastAPI 0.111, SQLAlchemy 2.0 async, Pydantic v2) · Docker Compose v2

**Primary Dependencies**:
- Frontend: `next@14.2.35`, `react@18.3.1`, `@tanstack/react-query@^5.45.1`, `axios@^1.7.2`, `lucide-react@^0.395.0`, `tailwindcss@^3.4.4`, `leaflet@^1.9.4`, `react-leaflet@^4.2.1`
- Frontend Testing: `vitest@5.1.1`, `@testing-library/react@16.3.3`, `@testing-library/jest-dom@8.0.0`, `jsdom@31.0.1`, `@vitest/coverage-v8` (added for coverage gate)
- Backend QA & Coverage: `pytest==8.2.2`, `pytest-asyncio==0.23.7`, `hypothesis==6.98.3`, `httpx==0.28.1`, `pytest-cov` (dev/QA coverage tool), `ruff==0.4.9`, `mypy==1.10.0`

**Storage**: Existing PostgreSQL 16 + PostGIS 3.4 & Redis 7 (no new Alembic migrations required by Feature 007; consumes existing `stores`, `menu_items`, `dishes`, `users`, `user_preferences` tables); browser `localStorage` used only for existing JWT/user session metadata.

**Testing**:
- Backend: `pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80` + `ruff check` + `ruff format --check` + `mypy app/`
- Frontend: `npm run lint` + `npm run type-check` + `npm run test` (with Vitest coverage report) + `npm run build`
- Repository & Deployment: `pre-commit run --all-files` + `docker compose config` + full-stack E2E UAT

**Target Platform**: Responsive PWA in modern mobile/desktop browsers (Chrome, Safari, Firefox; viewport `>= 360px`) + Dockerized Linux containers (`postgis/postgis:16-3.4-alpine`, `redis:7-alpine`, `python:3.11-slim`, `node:20-alpine`).

**EcoBite Baseline (inherited from `constitution.md`)**: Next.js 14 App Router + Tailwind CSS + `@/lib/api-client` + React Query · Python 3.11 + FastAPI async + Pydantic v2 + SQLAlchemy 2.0 async · PostgreSQL 16 + PostGIS + Redis 7 · Google Gemini 2.5 Flash · 4 Quality Gates with `>= 80%` coverage.

**Performance Goals**:
- Quick-Post end-to-end SLA: P95 `< 3.0s` (frontend axios timeout `20s` matching backend `15s` Gemini timeout + upload buffer)
- Personalized Recommendation SLA: P95 `< 2.5s` (deterministic fallback `< 300ms`)
- Frontend UI render: Zero layout thrashing; immediate skeleton feedback while AI requests run

**Constraints**:
- Prefer Next.js Server Components by default; mark `'use client'` strictly on interactive leaves/shells (hooks, `MediaRecorder`, React Query, event handlers)
- Zero `.env` files, API keys, or secrets committed or bundled in `NEXT_PUBLIC_*` variables
- Zero heavy ML training packages in `backend/requirements.txt`; zero files `> 5 MB` committed (`pre-commit` enforced)
- Strict `0.0%` allergen leakage invariant across all consumer endpoints and UI views

**Scale/Scope**: 3 new/enhanced frontend routes (`/store/dishes`, `/`, `/profile/preferences`), 3 frontend service modules, 1 custom browser audio hook, 6 modular UI components, 1 formal AI Test Plan, 3+ backend QA/safety test files, 4 frontend Vitest suites, 1 frontend Dockerfile + full 4-service `docker-compose.yml`, and Release `v1.0.0` PA5 acceptance deliverables.

## Constitution Check

*GATE: Checked pre-design (Phase 0) and re-verified post-design (Phase 1) against `.specify/memory/constitution.md` (v1.2.0) and `AGENTS.md`.*

- [x] **Principle I (Test-First Development)**: Every user story phase in `tasks.md` schedules Vitest component/hook tests and/or pytest safety/resilience/SLA tests **BEFORE** implementation (Red-Green-Refactor), including cleaning up the duplicate `"test"` key in `frontend/package.json`.
- [x] **Principle II (Security, Privacy & Access Control)**: Role-based `AuthGuard` and role-filtered `Navbar`/`BottomNavigation` enforce UX boundaries while backend `require_roles(...)` + KYC checks remain authoritative; zero secrets in frontend env vars or git; `MediaRecorder` tracks are strictly user-initiated and released on stop/unmount.
- [x] **Principle III (Data Integrity & Transactional Consistency)**: Draft Cards publish through the existing atomic `POST /api/v1/dishes/batch` endpoint; preference saves invalidate React Query caches immediately; checkout from Recommendation/Semantic Search cards reuses the existing atomic `POST /api/v1/orders` flow (`OrderModal`).
- [x] **Principle IV (Food Safety & Allergen Protection)**: All 14 EU FIC allergens are exposed in `/profile/preferences`; Draft Cards visibly separate `EXPLICIT` (Red) vs `INFERRED` (Amber) with Vietnamese rationale and non-medical disclaimer; `test_allergen_invariant.py` proves `0.0%` leakage at SQL level across both Personalized and Semantic Search; legacy "túi bất ngờ" mystery-bag copy in `page.tsx` is replaced with transparent dish-level phrasing.
- [x] **Principle V (Deterministic Business Rules & Payment Integrity)**: Draft Cards keep `override_discounted_price` optional (`null` = backend deterministic 40–50% / 70% time-shift discounting); UI never computes authoritative prices; UAT verifies VNPay HMAC-SHA512 & Dynamic HMAC-SHA256 QR end-to-end.
- [x] **Principle VI (AI Reliability, Structured Output & Model Isolation)**: Frontend consumes validated Pydantic schemas (`QuickPostExtractionResponse`, recommendation & semantic search contracts), degrades cleanly on `503` (Quick-Post → manual entry) and fallback justifications (Recommendations), and introduces zero ML training dependencies to `backend/requirements.txt`.
- [x] **Principle VII (Clean Architecture & Async End-to-End)**: Clean separation across `services/*.service.ts` (HTTP via `@/lib/api-client`), `hooks/` (`useVoiceRecorder`), `lib/allergens.ts` (shared 14 EU FIC metadata), and focused `'use client'` components under thin Server Component page wrappers where applicable (`profile/preferences/page.tsx`).
- [x] **Principle VIII (Verifiable Quality & Human Accountability)**: Mandatory Final Verification Gate runs `ruff check`, `ruff format --check`, `mypy app/`, `pytest --cov=app --cov-fail-under=80`, `npm run lint`, `npm run type-check`, `npm run test` (with coverage), `npm run build`, `docker compose config`, and `pre-commit run --all-files`, plus PR peer review per Sprint 5 matrix.

## Project Structure

### Documentation (this feature)

```text
specs/007-ai-frontend-suite-and-golive/
├── spec.md              # Feature specification (/speckit-specify)
├── plan.md              # This file (/speckit-plan)
├── research.md          # Phase 0 design & tooling decisions (/speckit-plan)
├── data-model.md        # Client/API DTOs, EU FIC catalog & QA/UAT entities (/speckit-plan)
├── quickstart.md        # Step-by-step verification, QA & Docker UAT guide (/speckit-plan)
├── checklists/
│   └── requirements.md  # Spec quality validation checklist
├── contracts/
│   └── api-contracts.md # Frozen REST contracts consumed by FE & tested by QA
└── tasks.md             # Dependency-ordered TDD tasks (/speckit-tasks)
```

### Source Code & Deliverables (repository root)

```text
frontend/
├── Dockerfile                                               # New (EC5-07): multi-stage Node 20 Alpine Next.js 14 production image
├── .dockerignore                                            # New (EC5-07): exclude node_modules, .next, .env*
├── package.json                                             # Clean duplicate "test" key; add "test:coverage" & @vitest/coverage-v8
├── vitest.config.ts                                         # Add v8 coverage configuration (include src/**, threshold reporting)
├── src/
│   ├── types/
│   │   └── api.ts                                           # Extend with PA5 AI-1, AI-2 & UserPreference TypeScript DTOs
│   ├── lib/
│   │   └── allergens.ts                                     # Shared 14 EU FIC bilingual catalog + EXPLICIT/INFERRED badge helpers
│   ├── hooks/
│   │   └── useVoiceRecorder.ts                              # MediaRecorder hook (webm/opus -> mp4 fallback, 60s/10MB caps, cleanup)
│   ├── services/
│   │   ├── ml.service.ts                                    # POST /ml/parse-dish-nlp (multipart/form-data, 20s timeout)
│   │   ├── preference.service.ts                            # GET/PUT /users/me/preferences
│   │   └── recommendation.service.ts                        # GET /recommendations/personalized & POST /dishes/search-semantic
│   ├── components/
│   │   ├── quick-post/
│   │   │   ├── AllergenBadge.tsx                            # Color-coded Red (EXPLICIT) / Amber (INFERRED) badge + tooltip + disclaimer
│   │   │   ├── VoiceQuickPostPanel.tsx                      # Mic recorder + file upload + text fallback + 503 graceful handoff
│   │   │   └── QuickPostDraftEditor.tsx                     # Editable Draft Cards, catalog dropdown, warnings & 1-Tap Batch Publish
│   │   ├── recommendations/
│   │   │   └── SmartRecommendationsCarousel.tsx             # Top 3 AI carousel, -70% urgent badge, 20–30w justification, Rescue CTA
│   │   ├── search/
│   │   │   └── SemanticSearchBar.tsx                        # Vietnamese NL search bar, prompt chips, loading/intent/clear controls
│   │   ├── preferences/
│   │   │   └── AllergenPreferencesForm.tsx                  # 14 EU FIC checkboxes, dietary lifestyle, categories, max_budget form
│   │   ├── DishCard.tsx                                     # Enhance with transparent allergen/dietary cues (no mystery bags)
│   │   └── ui/
│   │       ├── Navbar.tsx                                   # Add /profile/preferences link for CONSUMER
│   │       └── BottomNavigation.tsx                         # Add /profile/preferences quick link for authenticated CONSUMER
│   └── app/
│       ├── page.tsx                                         # Integrate SmartRecommendationsCarousel + SemanticSearchBar + clean header
│       ├── store/dishes/page.tsx                            # Integrate VoiceQuickPostPanel + QuickPostDraftEditor + manual fallback
│       └── profile/preferences/page.tsx                     # Server Component metadata wrapper rendering AuthGuard + AllergenPreferencesForm
└── __tests__/
    ├── hooks/
    │   └── useVoiceRecorder.test.ts                         # MediaRecorder start/stop, MIME fallback, permission denied, 10MB/60s caps
    └── components/
        ├── QuickPostDraftEditor.test.tsx                    # 2-tier badges (Red/Amber), catalog guard, inline edit, 503 fallback, batch publish
        ├── SmartDiscoveryAI.test.tsx                        # Top 3 Carousel, Semantic Search chips/map sync, fallback & empty states
        └── AllergenPreferencesForm.test.tsx                 # All 14 EU FIC checkboxes, save mutation, React Query cache invalidation

backend/
├── requirements.txt                                         # Add pytest-cov for coverage gate (no heavy ML training packages)
└── tests/
    └── integration/
        ├── test_allergen_invariant.py                       # New (EC5-06): 0.0% leakage matrix (accented/unaccented, multi-allergen, adversarial)
        ├── test_api_ml.py                                   # Expand (EC5-06): resilience fault-injection & Quick-Post < 3s SLA benchmark
        └── test_api_recommendations.py                      # Expand (EC5-06): resilience fallback, zero-500 matrix & < 2.5s / < 300ms SLA

docker-compose.yml                                           # Extend (EC5-07): add backend & frontend services with healthchecks alongside postgres & redis
.env.example                                                 # Verify/document full-stack Docker Compose variables (zero secrets)

docs/
├── PA5.md                                                   # Final PA5 Release 1.0 acceptance report (EC5-07)
├── PA5.pdf                                                  # Exported PDF for Moodle submission (EC5-07)
└── project_management/
    └── pa5_sprint5/
        ├── 02_Sprint5_Progress_Tracker.md                   # Updated Sprint 5 status & Scrum logs (EC5-07)
        ├── 03_PA5_AI_Test_Plan.md                           # Formal AI Safety, Resilience, SLA & >=80% Coverage Test Plan (EC5-06)
        └── 04_PA5_UAT_Signoff_and_Demo_Script.md            # Full-system E2E UAT execution log & Go-Live Demo Video script (EC5-07)
```

**Structure Decision**: Strictly follows EcoBite's Next.js 14 App Router layout (`frontend/src/{app,components,hooks,lib,services,types}` + `frontend/__tests__/{components,hooks}`), backend test layout (`backend/tests/integration/`), root Docker Compose orchestration, and `docs/project_management/pa5_sprint5/` governance layout from `AGENTS.md` Section 3.

## Complexity Tracking

No Constitution violations. All 8 Core Principles and all 8 Guardrails in `AGENTS.md` are satisfied without exceptions.
