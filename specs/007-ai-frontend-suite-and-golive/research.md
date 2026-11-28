# Technical Research & Design Decisions: AI Frontend Experience Suite, AI Safety QA & Release 1.0 Go-Live

**Feature**: `007-ai-frontend-suite-and-golive` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

This document resolves every frontend browser-API, UX/safety, state-management, QA/coverage, and Docker Compose Go-Live architectural decision before Sprint 5 implementation begins.

---

## Decision 1: Cross-Browser `MediaRecorder` Strategy & Audio Codec Fallback (`EC5-04`)

- **Decision**: Implement a dedicated `useVoiceRecorder` custom hook (`frontend/src/hooks/useVoiceRecorder.ts`) using `navigator.mediaDevices.getUserMedia({ audio: true })` and the Web `MediaRecorder` API with deterministic MIME negotiation:
  1. Probe `MediaRecorder.isTypeSupported(...)` in priority order: `'audio/webm;codecs=opus'` → `'audio/webm'` → `'audio/mp4'` → `'audio/wav'` → browser default `''`.
  2. Cap recording duration automatically at **60 seconds** (`MAX_RECORDING_SECONDS = 60`) via interval timer and reject resulting blobs or uploaded audio files exceeding **`10_485_760` bytes (10 MB)** before calling the API.
  3. Derive the filename extension from the selected MIME type (`voice-note.webm`, `voice-note.m4a`, `voice-note.wav`) when appending `audio_file` to `FormData` so backend extension fallback and MIME normalization (`specs/002-ai-quick-post-nlp`) always succeed across Chrome/Edge/Firefox (`audio/webm;codecs=opus`) and Safari iOS/macOS (`audio/mp4`).
  4. Always call `stream.getTracks().forEach((track) => track.stop())` on stop, error, and React component unmount so the browser microphone indicator never stays active.
  5. Surface structured error codes (`PERMISSION_DENIED`, `NOT_SUPPORTED`, `NO_MICROPHONE`, `FILE_TOO_LARGE`, `EMPTY_RECORDING`) and expose a 1-click toggle to the Vietnamese text-input fallback textarea (plus optional audio file picker `.m4a,.mp3,.wav,.webm` for desktop testing).
- **Rationale**:
  - Chrome/Android produce `audio/webm;codecs=opus`, whereas Safari/iOS produce `audio/mp4` (`.m4a`). Backend `POST /api/v1/ml/parse-dish-nlp` explicitly strips `;codecs=...` suffixes and accepts `.webm`, `.m4a`, `.mp3`, `.wav` up to 10 MB.
  - A 60-second Opus/AAC voice note is typically `250 KB – 1.2 MB`, staying well within the 10 MB inline upload ceiling and preserving the `< 3.0s` P95 Quick-Post SLA.
- **Alternatives considered**:
  - Third-party audio recorder npm packages: rejected to avoid React 18/Next.js SSR hydration overhead when native `MediaRecorder` requires ~100 lines of strict TypeScript and is straightforward to unit-test with jsdom mocks.
  - Client-side Web Speech API (`SpeechRecognition`) STT before backend: rejected because it is inconsistent across browsers (especially Vietnamese regional slang) and defeats Gemini 2.5 Flash's native multimodal audio ingestion (PRD AI Feature 1).

---

## Decision 2: `mlService` Upload Timeout & Multipart Handling (`EC5-04`)

- **Decision**: Route `POST /api/v1/ml/parse-dish-nlp` through `frontend/src/services/ml.service.ts` using the existing `@/lib/api-client` (`FormData` payload with `audio_file` and/or `raw_text`), overriding per-request `timeout: 20000` (20 seconds).
- **Rationale**:
  - `frontend/src/lib/api-client.ts` already deletes `Content-Type` when `config.data instanceof FormData` so Axios lets the browser attach the exact `multipart/form-data; boundary=...` header, and automatically attaches the JWT Bearer token with `401` refresh.
  - The global `apiClient` default timeout is `15000` ms, which equals backend `GEMINI_TIMEOUT_SECONDS = 15`. Setting `timeout: 20000` specifically on `parseDishNlp` ensures that when Gemini times out on the server at 15s, the browser reliably receives the backend's structured HTTP `503 Service Unavailable` JSON payload and triggers the graceful manual-entry fallback UX instead of throwing a generic client `ECONNABORTED` network error.
- **Alternatives considered**: Raising global `apiClient` timeout to 20s for all endpoints — rejected because core transactional endpoints (`POST /orders`, `GET /stores/nearby`) should fail fast within 15s.

---

## Decision 3: 2-Tier Allergen Visual Hierarchy & Draft Cards Validation (`EC5-04`)

- **Decision**: Centralize all 14 EU FIC bilingual allergen definitions in `frontend/src/lib/allergens.ts` (matching `EUAllergen` in `backend/app/schemas/nlp.py` verbatim) and build `AllergenBadge.tsx` + `QuickPostDraftEditor.tsx` with strict visual and safety rules:
  - **`EXPLICIT` (Partner-declared)**: Rendered with `Badge variant="danger"` (Red: `bg-red-100 text-red-800 border-red-200`), shield/alert icon, and explicit text tag `"Chủ quán báo"`.
  - **`INFERRED` (AI-reasoned)**: Rendered with `Badge variant="warning"` (Amber: `bg-amber-100 text-amber-800 border-amber-200`), sparkle/info icon, explicit text tag `"AI suy luận"`, accessible hover/click rationale tooltip (`warning.reason`), and a visible card footer disclaimer: *"Cảnh báo AI suy luận chỉ mang tính hỗ trợ, không thay thế xác nhận y tế — chủ quán vui lòng kiểm tra trước khi đăng."*
  - **Catalog Grounding Guard**: When `matched_menu_id === null`, highlight the card with an amber border, show `missing_fields_warning` banners, and render a required `<select>` populated from the store's active `menuItems`. Disable **"Đăng hàng loạt (1 chạm)"** until every retained card has a valid `matched_menu_id`, `quantity > 0`, and `pickup_end > pickup_start`.
  - **Graceful `503` Fallback**: When `parseDishNlp` returns `503`, render a non-destructive warning banner inside `/store/dishes` preserving any entered text note and offering a single button to switch focus to the existing manual form on the same page.
- **Rationale**: Directly enforces Constitution Principle IV (food safety transparency, non-medical disclaimer for inferred allergens), Principle V (blank `override_discounted_price` defers to rule-based discounting), and WCAG color-plus-label accessibility (NFR-005).
- **Alternatives considered**: Auto-publishing drafts immediately without human review — strictly rejected by Constitution Principle IV and Guardrail #6 (human-in-the-loop sign-off is mandatory).

---

## Decision 4: React Query Cache Invalidation & Discovery Home Integration (`EC5-05`)

- **Decision**:
  - Use TanStack React Query (`@tanstack/react-query` v5, already wired in `QueryProvider.tsx`) with standardized query keys:
    - `['preferences', 'me']` → `preferenceService.getMyPreferences()`
    - `['recommendations', 'personalized', coords.lat, coords.lng]` → `recommendationService.getPersonalized(...)` (enabled ONLY when authenticated user role is `CONSUMER`)
    - `['stores', 'nearby', coords.lat, coords.lng, radiusKm, category]` → `discoveryService.getNearbyStores(...)`
  - On `PUT /api/v1/users/me/preferences` success in `AllergenPreferencesForm`, call:
    ```ts
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['preferences', 'me'] }),
      queryClient.invalidateQueries({ queryKey: ['recommendations'] }),
      queryClient.invalidateQueries({ queryKey: ['semantic-search'] }),
    ]);
    ```
  - On `frontend/src/app/page.tsx`:
    1. Remove the duplicate inline `<header>` (root `layout.tsx` already renders the role-aware `<Navbar />`) and replace the legacy `"túi bất ngờ"` copy with transparent dish-level wording (*"món ăn dư thừa minh bạch"* — Constitution Principle IV).
    2. Mount `SmartRecommendationsCarousel` above the split-screen Radar list/map for `CONSUMER` users (showing a concise personalization CTA banner for guests without firing unauthenticated `401` calls).
    3. Mount `SemanticSearchBar` with Vietnamese prompt chips (*"Món nước nóng dưới 30k gần đây"*, *"Đồ chay không đậu phộng"*, *"Bánh ngọt giảm sâu dưới 25k"*). While a semantic search is active, map the returned allergen-safe dishes into `RescueDishItem[]` so BOTH the left dish list and right `DynamicRadarMap` pins synchronize seamlessly and clicking any card/pin opens `OrderModal`. Clearing the search restores standard PostGIS Radar discovery immediately.
- **Rationale**: Prevents stale-cache allergen flashes after a user updates allergies on `/profile/preferences`, eliminates double navigation bars on `/`, and reuses `DynamicRadarMap`, `DishCard`, and `OrderModal` with zero duplicated checkout logic.
- **Alternatives considered**: Fetching recommendations in `useEffect` with local `useState` — rejected because navigating from `/profile/preferences` back to `/` could display stale un-invalidated data or duplicate in-flight Gemini requests.

---

## Decision 5: Server Component Shell Pattern (`EC5-05` & Constitution Principle VII)

- **Decision**: Author `frontend/src/app/profile/preferences/page.tsx` as a **Server Component** exporting page `metadata` (`title`, `description`) that renders the client leaf `<AuthGuard allowedRoles={['CONSUMER']}><AllergenPreferencesForm /></AuthGuard>`. Keep interactive state, hooks, `MediaRecorder`, and React Query strictly inside `'use client'` leaf components (`VoiceQuickPostPanel`, `QuickPostDraftEditor`, `SmartRecommendationsCarousel`, `SemanticSearchBar`, `AllergenPreferencesForm`).
- **Rationale**: Satisfies Constitution Principle VII (*"Prefer Next.js Server Components by default. Use `'use client'` only when browser APIs, state, hooks, or client-side interaction require it"*) while remaining compatible with `frontend/src/app/page.tsx` and `frontend/src/app/store/dishes/page.tsx`.
- **Alternatives considered**: Making every page and subcomponent `'use client'` indiscriminately — rejected to minimize client JS bundle size and adhere to the Constitution.

---

## Decision 6: Allergen Hard Invariant Verification Matrix (`EC5-06`)

- **Decision**: Author `backend/tests/integration/test_allergen_invariant.py` to test **0.0% allergen leakage** systematically across a Cartesian safety matrix:
  1. **Encoding & Normalization variants**: canonical bilingual EU FIC strings (`"Peanuts (Đậu phộng)"`), Vietnamese accented (`"đậu phộng"`), Vietnamese unaccented (`"dau phong"`), English lowercase (`"peanuts"`), and multi-allergen exclusions (`["Peanuts (Đậu phộng)", "Crustaceans (Tôm/Cua)", "Eggs (Trứng)"]`).
  2. **Dish allergen storage variants**: both `EXPLICIT` and `INFERRED` warnings on `Dish.allergens`, plus dishes whose allergens were inherited from `MenuItem.base_allergens`.
  3. **Both AI-2 read paths**: `GET /api/v1/recommendations/personalized` AND `POST /api/v1/dishes/search-semantic`.
  4. **Adversarial semantic query**: Consumer excludes Peanuts, then submits *"Tìm bún thịt nướng có nhiều đậu phộng rang dưới 30k"* — database hard filter MUST still return `0` peanut-containing dishes, proving medical exclusions strictly override user query text and Gemini intent extraction.
  5. **Spy verification**: Assert that the candidate list passed into the mocked Layer 3 Gemini justification adapter NEVER contains any excluded-allergen dish (proving filtering occurred at SQL Layer 1, never in Layer 3).
- **Rationale**: Directly validates Guardrail #7, Constitution Principle IV, and Week 6 Action Plan `EC5-06` criteria with falsifiable automated evidence.
- **Alternatives considered**: Testing only happy-path single allergen in unit tests — insufficient because SQL normalization edge cases (diacritics, multi-allergen JSONB/JSON containment, adversarial semantic queries) require end-to-end integration verification.

---

## Decision 7: Coverage Tooling & `>= 80%` Gate Enforcement (`EC5-06`)

- **Decision**:
  - **Backend**: Add `pytest-cov==5.0.0` (test utility only — zero ML training bloat) to `backend/requirements.txt` and run:
    `pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80`.
  - **Frontend**: Fix the duplicate `"test"` key in `frontend/package.json` (`"test": "vitest run"`, `"test:coverage": "vitest run --coverage"`), add `@vitest/coverage-v8` as a `devDependency`, and configure `test.coverage` in `frontend/vitest.config.ts` targeting `src/services/**`, `src/hooks/**`, `src/lib/**`, and new AI components (`quick-post/**`, `recommendations/**`, `search/**`, `preferences/**`).
  - **SLA Benchmarks**: Include deterministic timing assertions in pytest (`test_api_ml.py` / `test_api_recommendations.py`) for local CI (`< 300ms` deterministic fallback, zero-blocking async execution) plus an opt-in live benchmark runner (`RUN_LIVE_SLA=1`) recording actual P50/P95 latencies (`Quick-Post < 3.0s`, `Recommendation < 2.5s`) into `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md` and `docs/PA5.md`.
- **Rationale**: Satisfies Constitution Principle VIII (*"targets at least 80% test coverage"*) and `docs/07_AI_Development_Workflow_and_Quality_Gates.md` Gate 4 with reproducible, non-flaky commands.
- **Alternatives considered**: Requiring live Gemini API calls during every CI test run — rejected because CI should remain hermetic, fast, and quota-safe (`GEMINI_USE_DEMO_KEY=False`), while live SLA measurements are executed explicitly during QA/UAT sign-off.

---

## Decision 8: Full-Stack Docker Compose Go-Live Packaging (`EC5-07`)

- **Decision**:
  - Create a multi-stage **`frontend/Dockerfile`** (`node:20-alpine`):
    - Stage `deps`: `npm ci`
    - Stage `builder`: accepts `ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`, runs `npm run build`
    - Stage `runner`: copies `.next`, `public`, `package.json`, `node_modules` (production), exposes `3000`, runs `npm run start` with a container healthcheck probing `http://127.0.0.1:3000`.
  - Extend root **`docker-compose.yml`** to orchestrate all 4 services on `ecobite_network`:
    - `postgres` (`postgis/postgis:16-3.4-alpine`, existing healthcheck)
    - `redis` (`redis:7-alpine`, existing healthcheck)
    - `backend` (builds `./backend`, depends on `postgres` and `redis` `service_healthy`, passes `DATABASE_URL` pointing to `postgres:5432` and `REDIS_URL` pointing to `redis:6379`, reads optional `backend/.env` for secrets like `GEMINI_TEST_API` / `VNP_HASH_SECRET` without committing them, healthcheck on `GET http://127.0.0.1:8000/health`)
    - `frontend` (builds `./frontend` with `NEXT_PUBLIC_API_BASE_URL`, depends on `backend` `service_healthy`, exposes port `3000`)
  - Keep database-only dev workflow effortless via `docker compose up -d postgres redis` while `docker compose up --build` boots the complete Release 1.0 stack for UAT and demo.
- **Rationale**: Preserves backwards compatibility for developers running local `uvicorn` + `next dev` while delivering a single-command Release 1.0 deployment for UAT (`EC5-07`) and instructor evaluation.
- **Alternatives considered**: Deploying Kubernetes/Helm manifests — out of scope and over-engineered for EcoBite's CS300 Release 1.0 Docker Compose packaging requirement.
