---
description: "Dependency-ordered TDD task list for Feature 007 — AI Frontend Experience Suite, AI Safety QA & Release 1.0 Go-Live (PA5 Sprint 5: EC5-04, EC5-05, EC5-06, EC5-07)"
---

# Tasks: AI Frontend Experience Suite, AI Safety QA & Release 1.0 Go-Live

**Input**: Design documents from `/specs/007-ai-frontend-suite-and-golive/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/api-contracts.md`, `quickstart.md`

**Tests**: Test tasks are **MANDATORY** and placed **FIRST** inside every User Story phase per EcoBite Constitution Principle I (Test-First Development — Red-Green-Refactor). All tasks start unchecked `[ ]` (Sprint 5 scope). The Final Verification Gate phase MUST exit `0` across Backend, Frontend, Docker Compose, and Pre-commit checks before proposing Release `v1.0.0`.

**Team Ownership (Sprint 5 Jira Mapping)**:
- **US1 (`EC5-04`)**: Võ Ngọc Thịnh *(Reviewer: Phùng Quốc Huy)* — Store Partner Voice Quick-Post UI & 2-Tier Allergen Draft Cards Editor
- **US2 (`EC5-05`)**: Võ Ngọc Thịnh *(Reviewer: Đặng Trọng Phúc)* — Consumer Smart Recommendations Carousel, Semantic Search & `/profile/preferences`
- **US3 (`EC5-06`)**: Đàng Thế Tony *(Reviewer: Phùng Quốc Huy)* — AI Safety Allergen Hard Invariant, Resilience, SLA Benchmarks & `>= 80%` Coverage QA
- **US4 (`EC5-07`)**: Whole Team *(PM: Phùng Quốc Huy)* — Full-System UAT, Docker Compose Go-Live Packaging, `docs/PA5.md`/`PA5.pdf`, `v1.0.0` Tag & Demo Video

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`, `[US4]`) — omitted in Setup, Foundational, Polish, and Verification Gate phases
- Exact repository-relative file paths included in every task

---

## Phase 1: Setup (Frontend & Backend Test/Coverage Tooling Hygiene)

**Purpose**: Ensure Vitest coverage, duplicate script cleanup, and pytest coverage tooling are ready before TDD work starts.

- [ ] T001 Clean up duplicate `"test"` script key in `frontend/package.json`, add `"test:coverage": "vitest run --coverage"` and `@vitest/coverage-v8` devDependency, and configure v8 coverage reporting in `frontend/vitest.config.ts`
- [ ] T002 [P] Add `pytest-cov` (test coverage utility only; zero ML training packages) to `backend/requirements.txt` and verify `./venv_backend/bin/pytest --version` reports `pytest-cov` enabled

**Checkpoint**: Both frontend (`vitest --coverage`) and backend (`pytest --cov=app`) coverage runners execute cleanly.

---

## Phase 2: Foundational (Shared PA5 DTOs, 14 EU FIC Allergen Catalog & API Services)

**Purpose**: Freeze shared TypeScript DTOs, the 14 EU FIC bilingual allergen metadata module, and the 3 new `@/lib/api-client` service wrappers required by both US1 (`EC5-04`) and US2 (`EC5-05`).

**⚠️ CRITICAL**: No US1/US2 component implementation should begin until these shared contracts and service wrappers exist.

- [ ] T003 Define PA5 TypeScript DTOs (`DetectionSource`, `AllergenRiskLevel`, `NLPAllergenWarning`, `SurplusDishDraftItem`, `QuickPostExtractionResponse`, `DietaryPreference`, `UserPreferenceResponse`, `UserPreferenceUpdatePayload`, `PersonalizedRecommendationItem`, `PersonalizedRecommendationsResponse`, `SemanticSearchRequest`, `SemanticSearchIntent`, `SemanticSearchResponse`) in `frontend/src/types/api.ts`
- [ ] T004 [P] Create canonical 14 EU FIC bilingual allergen catalog (exact match to `backend/app/schemas/nlp.py::EUAllergen`) and 2-tier badge metadata helpers (`EXPLICIT` Red vs `INFERRED` Amber + non-medical disclaimer constant) in `frontend/src/lib/allergens.ts`
- [ ] T005 [P] Implement `mlService.parseDishNlp(payload)` sending `FormData` (`audio_file` and/or `raw_text`) to `POST /api/v1/ml/parse-dish-nlp` via `@/lib/api-client` with `timeout: 20000` in `frontend/src/services/ml.service.ts`
- [ ] T006 [P] Implement `preferenceService.getMyPreferences()` and `preferenceService.updateMyPreferences(payload)` calling `GET`/`PUT /api/v1/users/me/preferences` via `@/lib/api-client` in `frontend/src/services/preference.service.ts`
- [ ] T007 [P] Implement `recommendationService.getPersonalized(params)` (`GET /api/v1/recommendations/personalized`) and `recommendationService.searchSemantic(payload)` (`POST /api/v1/dishes/search-semantic`) via `@/lib/api-client` in `frontend/src/services/recommendation.service.ts`

**Checkpoint**: Foundation ready — `npm run type-check` passes with all PA5 DTOs, allergen metadata, and API services in place.

---

## Phase 3: User Story 1 - Store Partner Voice Quick-Post & 2-Tier Allergen Draft Cards Editor (`EC5-04`, Priority: P1) 🎯 MVP-Merchant

**Goal**: Approved Store Partners record a Vietnamese voice clip (or use text fallback) on `/store/dishes`, review extracted Draft Cards with Red (`EXPLICIT`) vs Amber (`INFERRED`) 2-tier EU FIC allergen badges, link unmatched catalog items, edit quantities/override prices inline, handle `503` degradation cleanly into manual entry, and execute 1-Tap Batch Publish via `POST /api/v1/dishes/batch`.

**Independent Test**: Run `cd frontend && npx vitest run __tests__/hooks/useVoiceRecorder.test.ts __tests__/components/QuickPostDraftEditor.test.tsx`; manually test `/store/dishes` as an approved `STORE_PARTNER` through recording/text extraction, 2-tier badge tooltip inspection, unmatched catalog selection, `503` manual fallback, and 1-Tap Batch Publish.

### Tests for User Story 1 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T008 [P] [US1] Write Vitest hook tests in `frontend/__tests__/hooks/useVoiceRecorder.test.ts` covering `MediaRecorder` start/stop lifecycle, MIME negotiation (`audio/webm;codecs=opus` → `audio/mp4`), 60-second auto-stop cap, `> 10 MB` file-size rejection, microphone permission denial (`NotAllowedError`) error state, and media stream track cleanup on unmount
- [ ] T009 [P] [US1] Write Vitest component tests in `frontend/__tests__/components/QuickPostDraftEditor.test.tsx` covering Red (`EXPLICIT`) vs Amber (`INFERRED`) allergen badge rendering with tooltip rationale and AI-inferred non-medical disclaimer, `missing_fields_warning` banner display, mandatory catalog dropdown guard when `matched_menu_id === null`, inline quantity/override-price editing, `503` graceful handoff to manual form preserving text note, and 1-Tap Batch Publish calling `dishService.batchCreateSurplusDishes` with exact `DishBatchPublishPayload`

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement `useVoiceRecorder` custom hook (browser `MediaRecorder`, codec probing `audio/webm;codecs=opus` → `audio/webm` → `audio/mp4` → `audio/wav`, 60s timer cap, 10 MB validation, permission/unsupported error codes, stream cleanup) in `frontend/src/hooks/useVoiceRecorder.ts`
- [ ] T011 [P] [US1] Create `AllergenBadge` component displaying Red (`variant="danger"`, `"Chủ quán báo"`) for `EXPLICIT` and Amber (`variant="warning"`, `"AI suy luận"`) for `INFERRED` with icon, accessible rationale tooltip/popover, and optional remove action in `frontend/src/components/quick-post/AllergenBadge.tsx`
- [ ] T012 [US1] Create `VoiceQuickPostPanel` (`'use client'`) integrating `useVoiceRecorder`, audio file upload picker (`.webm,.m4a,.mp3,.wav`, `<= 10 MB`), Vietnamese free-text fallback textarea, loading state, `mlService.parseDishNlp` invocation, and `503` graceful fallback banner switching to manual mode in `frontend/src/components/quick-post/VoiceQuickPostPanel.tsx`
- [ ] T013 [US1] Create `QuickPostDraftEditor` (`'use client'`) rendering editable pickup window (`pickup_start`/`pickup_end` validation), per-dish Draft Cards with `AllergenBadge` list + non-medical disclaimer for `INFERRED` items, Base Menu Catalog dropdown selector for `matched_menu_id === null`, inline quantity/override-price/dietary-notes editing, `missing_fields_warning` banners, card removal, and 1-Tap Batch Publish calling `dishService.batchCreateSurplusDishes` in `frontend/src/components/quick-post/QuickPostDraftEditor.tsx`
- [ ] T014 [US1] Integrate `VoiceQuickPostPanel` and `QuickPostDraftEditor` into `frontend/src/app/store/dishes/page.tsx` for `APPROVED` stores with seamless toggle/fallback to the existing manual dish form and immediate refresh of `activeDishes` after `201 Created` batch publish

**Checkpoint**: User Story 1 (`EC5-04`) is independently complete and all `useVoiceRecorder` & `QuickPostDraftEditor` tests pass.

---

## Phase 4: User Story 2 - Consumer Smart Recommendations Carousel, Semantic Search & Allergen Profile (`EC5-05`, Priority: P1) 🎯 MVP-Consumer

**Goal**: Consumers manage all 14 EU FIC allergen exclusions, dietary lifestyle, favorite categories, and budget on `/profile/preferences` (accessible via Navbar & BottomNavigation), view the Top 3 Smart Recommendations Carousel with urgent `-70%` deal badges and 20–30 word AI justifications on `/`, and search naturally in Vietnamese via the Conversational Semantic Search Bar synchronized with the Leaflet Radar map and `OrderModal`.

**Independent Test**: Run `cd frontend && npx vitest run __tests__/components/AllergenPreferencesForm.test.tsx __tests__/components/SmartDiscoveryAI.test.tsx`; verify `/profile/preferences` saves and invalidates cached recommendations, and `/` renders the Top 3 Carousel, Semantic Search prompt chips, synchronized Radar map pins, and working `OrderModal` checkout.

### Tests for User Story 2 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T015 [P] [US2] Write Vitest component tests in `frontend/__tests__/components/AllergenPreferencesForm.test.tsx` verifying all 14 EU FIC bilingual checkboxes render, initial preferences load via `preferenceService.getMyPreferences`, toggling allergens/dietary lifestyle/categories/`max_budget` submits `preferenceService.updateMyPreferences`, negative budget is blocked, and successful save invalidates `['recommendations']` and `['semantic-search']` React Query caches
- [ ] T016 [P] [US2] Write Vitest component tests in `frontend/__tests__/components/SmartDiscoveryAI.test.tsx` covering Top 3 Smart Recommendations Carousel (urgent `-70%` badge, distance, 20–30 word `ai_justification`, `OrderModal` rescue callback, guest CTA without firing `401`), Conversational Semantic Search Bar (prompt chip click, free-text query, loading state, parsed intent chips, map/list synchronization, clear/reset control), and graceful fallback/empty states

### Implementation for User Story 2

- [ ] T017 [P] [US2] Create `AllergenPreferencesForm` (`'use client'`) using React Query (`useQuery` + `useMutation` + immediate cache invalidation) with all 14 EU FIC bilingual checkboxes (`frontend/src/lib/allergens.ts`), `DietaryPreference` radio/pill selector (`NONE`/`VEGAN`/`VEGETARIAN`), `FoodCategory` multi-select chips, `max_budget` (VND `>= 0`) input, and hard-SQL-filter safety explanation in `frontend/src/components/preferences/AllergenPreferencesForm.tsx`
- [ ] T018 [US2] Create Server Component route `frontend/src/app/profile/preferences/page.tsx` exporting page metadata and rendering `<AuthGuard allowedRoles={['CONSUMER']}><AllergenPreferencesForm /></AuthGuard>`, and add `/profile/preferences` (`Khẩu vị & Dị ứng`) links for `CONSUMER` users in `frontend/src/components/ui/Navbar.tsx` and `frontend/src/components/ui/BottomNavigation.tsx`
- [ ] T019 [P] [US2] Create `SmartRecommendationsCarousel` (`'use client'`) fetching `recommendationService.getPersonalized(lat, lng, limit=3)` via React Query for authenticated `CONSUMER` users, rendering Top 3 cards with `-70%` urgent final-rush badges, distance, remaining count, 20–30 word `ai_justification` callout (with subtle fallback indicator when `is_fallback` is true), loading skeletons, and 1-click rescue callback opening `OrderModal` in `frontend/src/components/recommendations/SmartRecommendationsCarousel.tsx`
- [ ] T020 [P] [US2] Create `SemanticSearchBar` (`'use client'`) with Vietnamese natural-language input, quick prompt chips (*"Món nước nóng dưới 30k gần đây"*, *"Đồ chay không đậu phộng"*, *"Bánh ngọt giảm sâu dưới 25k"*), `recommendationService.searchSemantic` mutation, loading indicator, parsed intent filter chips, and clear/reset button in `frontend/src/components/search/SemanticSearchBar.tsx`
- [ ] T021 [US2] Update `frontend/src/components/DishCard.tsx` to display transparent allergen/dietary cues (no mystery bags) and integrate `SmartRecommendationsCarousel` + `SemanticSearchBar` into `frontend/src/app/page.tsx` (removing duplicate inline header and legacy `"túi bất ngờ"` wording, synchronizing semantic search results with `DynamicRadarMap` and `OrderModal`)

**Checkpoint**: User Story 2 (`EC5-05`) is independently complete and all Consumer AI Discovery & Allergen Preferences tests pass.

---

## Phase 5: User Story 3 - AI Safety Verification, Resilience, SLA Benchmarks & >=80% Coverage QA Suite (`EC5-06`, Priority: P1)

**Goal**: Publish the formal PA5 AI Test Plan and execute comprehensive automated verification proving **0.0% allergen leakage**, **zero unhandled `500` server errors** under AI fault injection, compliant SLA latency benchmarks (`Quick-Post < 3.0s`, `Recommendation < 2.5s` / fallback `< 300ms`), and **`>= 80%` project-wide test coverage**.

**Independent Test**: Run `cd backend && ./venv_backend/bin/pytest tests/integration/test_allergen_invariant.py tests/integration/test_api_ml.py tests/integration/test_api_recommendations.py -v` and `pytest tests/ --cov=app --cov-fail-under=80`, plus `cd frontend && npm run test:coverage`; confirm 0% allergen leakage, zero `500` responses, SLA pass, and `>= 80%` coverage.

### Test Plan & Automated Safety / Resilience Suites (US3)

- [ ] T022 [P] [US3] Author the formal AI Safety, Resilience, SLA Benchmark & Coverage Test Plan documenting the Allergen Invariant matrix, fault-injection matrix, SLA measurement protocol, frontend Vitest scope, and `>= 80%` coverage remediation targets in `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md`
- [ ] T023 [P] [US3] Implement comprehensive Allergen Hard Invariant integration suite in `backend/tests/integration/test_allergen_invariant.py` asserting **0.0% allergen leakage** across accented/unaccented Vietnamese inputs, canonical bilingual EU FIC keys, single & multi-allergen exclusions, `EXPLICIT` & `INFERRED` dish allergens, both `GET /api/v1/recommendations/personalized` and `POST /api/v1/dishes/search-semantic` (including adversarial prompt asking for an excluded allergen), and spy verification that excluded dishes never reach Layer 3 Gemini
- [ ] T024 [P] [US3] Expand `backend/tests/integration/test_api_ml.py` with full fault-injection resilience tests (missing API key, timeout, `429` rate limit, network error, malformed JSON/schema → clean `503`, zero `500`s) and a Quick-Post SLA timing benchmark (`< 3.0s` P95 target, opt-in `RUN_LIVE_SLA=1` live Gemini measurement + fast mocked regression check)
- [ ] T025 [P] [US3] Expand `backend/tests/integration/test_api_recommendations.py` with fault-injection resilience tests across both Personalized Recommendations and Semantic Search (missing key, timeout, rate limit, malformed schema → safe `200 OK` deterministic fallback, zero `500`s) and SLA timing benchmarks (`< 2.5s` P95 live / `< 300ms` deterministic fallback)
- [ ] T026 [US3] Run full backend coverage (`pytest tests/ --cov=app --cov-report=term-missing`) and frontend coverage (`npm run test:coverage`), close any uncovered branch gaps across services/endpoints/components until project-wide automated test coverage reaches **`>= 80%`**, and record observed metrics in `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md`

**Checkpoint**: User Story 3 (`EC5-06`) is complete — 0.0% allergen leakage, zero-500 resilience, SLA targets, and `>= 80%` coverage are verified with reproducible command output.

---

## Phase 6: User Story 4 - Full-System UAT, Docker Compose Go-Live Packaging & Release 1.0 Delivery (`EC5-07`, Priority: P2)

**Goal**: Package all 4 services (`postgres`, `redis`, `backend`, `frontend`) in Docker Compose, complete full E2E UAT across Core F1–F8 + AI-1 & AI-2, and deliver final PA5 acceptance documentation, Release `v1.0.0` tag, and Final Go-Live Demo Video ahead of Internal Deadline `2026-12-11` (`23:59`) / Moodle `2026-12-12`.

**Independent Test**: Run `docker compose config --quiet && docker compose up -d --build`, run Alembic migrations & seed inside `backend`, execute all 12 UAT scenarios in `04_PA5_UAT_Signoff_and_Demo_Script.md` against `http://localhost:3000` and `http://localhost:8000`, and verify `docs/PA5.md`, `docs/PA5.pdf`, and `v1.0.0` readiness.

### Container Packaging, UAT Execution & Release 1.0 Deliverables

- [ ] T027 [P] [US4] Create multi-stage Node 20 Alpine production container `frontend/Dockerfile` (passing `NEXT_PUBLIC_API_BASE_URL` build arg, `npm ci`, `npm run build`, `npm run start` on port `3000`, healthcheck) and `frontend/.dockerignore`
- [ ] T028 [US4] Extend root `docker-compose.yml` to add `backend` (`./backend/Dockerfile`, port `8000`, `depends_on` `postgres` & `redis` `service_healthy`, `/health` healthcheck) and `frontend` (`./frontend/Dockerfile`, port `3000`, `depends_on` `backend` `service_healthy`) on `ecobite_network`, and sync documented environment keys (zero secrets) in `.env.example`
- [ ] T029 [US4] Boot full 4-service Docker Compose stack (`docker compose up -d --build`), run `alembic upgrade head` + `python -m app.db.seed`, execute complete E2E UAT covering Core F1–F8 + AI-1 (`EC5-04`) + AI-2 (`EC5-05`) + Allergen Hard Invariant across `ADMIN`, `STORE_PARTNER`, and `CONSUMER`, and record sign-off evidence + Demo Video script in `docs/project_management/pa5_sprint5/04_PA5_UAT_Signoff_and_Demo_Script.md`
- [ ] T030 [US4] Update `docs/project_management/pa5_sprint5/02_Sprint5_Progress_Tracker.md`, compile final Release 1.0 acceptance report in `docs/PA5.md` and export `docs/PA5.pdf`, record Final Go-Live Demo Video, and prepare clean `v1.0.0` release tag prior to Internal Deadline `2026-12-11` (`23:59`) for Moodle submission `2026-12-12`

**Checkpoint**: Full 4-service Docker Compose stack, UAT sign-off, PA5 report (`md` + `pdf`), Demo Video, and Release `v1.0.0` deliverables are complete.

---

## Phase 7: Polish & Cross-Cutting Audit

**Purpose**: Accessibility, security hygiene, and cross-browser responsiveness audit across all new AI UI and container files.

- [ ] T031 [P] Audit mobile responsiveness (`360px`–`1440px`) and keyboard/ARIA accessibility on `/store/dishes`, `/`, and `/profile/preferences` (verifying Red/Amber allergen badges include text + icon labels and zero console/hydration warnings)
- [ ] T032 [P] Audit `backend/requirements.txt` (zero heavy ML training libraries), `frontend/src/` (zero secrets in `NEXT_PUBLIC_*`, zero raw `axios` bypassing `@/lib/api-client`), and `git status` (zero `.env` files staged, zero files `> 5 MB`)

---

## Final Phase: Verification Gate (Constitution Principle VIII) — MANDATORY

**Purpose**: Reproducible proof that all 4 EcoBite Quality Gates pass with exit code `0` before merging PRs and tagging `v1.0.0`.

### Backend (`backend/`, using `venv_backend`)

- [ ] T033 `./venv_backend/bin/ruff check app/ tests/` — lint passes with zero findings
- [ ] T034 `./venv_backend/bin/ruff format --check app/ tests/` — formatting is canonical
- [ ] T035 `./venv_backend/bin/mypy app/` — static type-check passes with zero errors
- [ ] T036 `./venv_backend/bin/pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80 -v` — full unit, integration (including `test_allergen_invariant.py`), and property suites pass with `>= 80%` coverage

### Frontend (`frontend/`)

- [ ] T037 `npm run lint` — ESLint (`next/core-web-vitals`) passes with zero errors
- [ ] T038 `npm run type-check` — TypeScript `tsc --noEmit` (`strict: true`) passes with zero errors
- [ ] T039 `npm run test:coverage` — all Vitest component & hook tests pass with coverage report generated
- [ ] T040 `npm run build` — Next.js 14 production build completes with exit code `0`

### Containerization & Repository Hooks (repo root)

- [ ] T041 `docker compose config --quiet` — 4-service Docker Compose manifest validates cleanly
- [ ] T042 `pre-commit run --all-files` — secrets detection, `< 5 MB` file-size guard, formatting, and `.env` blocker pass with exit code `0`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup: `T001`–`T002`)**: Start immediately; unlocks frontend & backend coverage execution.
- **Phase 2 (Foundational: `T003`–`T007`)**: Depends on `T001` — BLOCKS US1 (`EC5-04`) and US2 (`EC5-05`) implementation.
- **Phase 3 (US1 — Merchant Quick-Post UI `EC5-04`: `T008`–`T014`)**: Depends on Phase 2; can run in parallel with Phase 5 backend QA tasks (`T022`–`T025`).
- **Phase 4 (US2 — Consumer AI Discovery & Preferences `EC5-05`: `T015`–`T021`)**: Depends on Phase 2; can execute immediately after Phase 3 (or in parallel on separate files with `T017`–`T020`).
- **Phase 5 (US3 — AI Safety, Resilience, SLA & Coverage QA `EC5-06`: `T022`–`T026`)**: `T022`–`T025` can run in parallel with Phases 3–4 once backend `EC5-01`..`EC5-03` are merged; `T026` final coverage closure runs after Phases 3–4 complete.
- **Phase 6 (US4 — Docker Packaging, UAT & Release 1.0 `EC5-07`: `T027`–`T030`)**: `T027`–`T028` can be prepared alongside Phase 5; `T029`–`T030` depend on Phases 3–5 passing cleanly.
- **Phase 7 (Polish: `T031`–`T032`)** & **Final Phase (Verification Gate: `T033`–`T042`)**: Depend on all preceding phases completing.

### Parallel Execution Lanes (Team Coordination)

```bash
# Lane A — Võ Ngọc Thịnh (Frontend Lead: EC5-04 -> EC5-05):
T001 -> T003..T007 -> T008..T014 (US1 Quick-Post UI) -> T015..T021 (US2 Recommendations/Search/Preferences)

# Lane B — Đàng Thế Tony (QA Lead: EC5-06):
T002 -> T022 (Test Plan) + T023 (test_allergen_invariant.py) + T024 (ML resilience/SLA) + T025 (Recs resilience/SLA) -> T026 (>=80% Coverage Gate)

# Lane C — Phùng Quốc Huy & Đặng Trọng Phúc (Go-Live Packaging & Reviews: EC5-07):
PR Reviews for EC5-04 (Huy), EC5-05 (Phúc), EC5-06 (Huy) + T027..T028 (Docker Compose 4-service stack) -> Whole-team T029..T030 (UAT, docs/PA5.md/pdf, Video, v1.0.0)
```

---

## Implementation Strategy

### Incremental Delivery Order

1. **Setup & Contracts (`T001`–`T007`)**: Clean coverage tooling + freeze PA5 TypeScript DTOs, 14 EU FIC allergen module, and 3 API service modules.
2. **Merchant AI MVP (`US1 / EC5-04`: `T008`–`T014`)** → **STOP & VALIDATE**: Voice/Text Quick-Post → 2-Tier Draft Cards → 1-Tap Batch Publish + `503` manual fallback passes Vitest and works live on `/store/dishes`.
3. **Consumer AI MVP (`US2 / EC5-05`: `T015`–`T021`)** → **STOP & VALIDATE**: `/profile/preferences` (14 EU FIC) + Top 3 Smart Recommendations Carousel + Conversational Semantic Search synced with Leaflet Radar & `OrderModal` passes Vitest and works live on `/`.
4. **AI Safety & Coverage Gate (`US3 / EC5-06`: `T022`–`T026`)** → **STOP & VALIDATE**: 0.0% allergen leakage, zero-500 resilience, SLA benchmarks, and `>= 80%` project-wide coverage verified.
5. **Docker Go-Live & Release 1.0 (`US4 / EC5-07`: `T027`–`T042`)**: 4-service Docker Compose UAT → Final Verification Gate (`T033`–`T042`) → `docs/PA5.md` + `docs/PA5.pdf` + Go-Live Demo Video + tag `v1.0.0` before `2026-12-11` (`23:59`).
