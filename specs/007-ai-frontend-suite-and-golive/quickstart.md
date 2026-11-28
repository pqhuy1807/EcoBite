# Quickstart Validation Guide: AI Frontend Suite, AI Safety QA & Release 1.0 Go-Live

**Feature**: `007-ai-frontend-suite-and-golive` | **Contracts**: [contracts/api-contracts.md](./contracts/api-contracts.md) | **Data Model**: [data-model.md](./data-model.md)

Use this guide to validate the Store Partner AI Quick-Post UI (`EC5-04`), Consumer Smart Discovery & Allergen Preferences UI (`EC5-05`), AI Safety / Resilience / Coverage QA Suite (`EC5-06`), and Full-System Docker Compose Release 1.0 UAT (`EC5-07`).

---

## 1. Prerequisites & Environment Verification

1. Configure environment files locally from templates (NEVER commit `.env` or `backend/.env`):
   - Root `.env` from `.env.example` (`POSTGRES_*`, `REDIS_*`, `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`).
   - `backend/.env` from `backend/.env.example` (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `QR_SIGNATURE_SECRET`, `VNP_*`, `GEMINI_TEST_API`, `GEMINI_USE_DEMO_KEY=False` for dev/QA; toggle `True` with `GEMINI_DEMO_API` strictly for live demo recording).
2. Confirm backend venv (`backend/venv_backend` on macOS or `backend/.venv`) and frontend dependencies (`frontend/node_modules`) are installed:
   ```bash
   cd backend && ./venv_backend/bin/pip install -r requirements.txt
   cd ../frontend && npm install
   ```

---

## 2. Frontend Automated Verification (`EC5-04`, `EC5-05`, `EC5-06`)

Run linting, strict TypeScript checking, Vitest component/hook tests with coverage, and production build:

```bash
cd frontend
npm run lint
npm run type-check
npm run test:coverage
npm run build
```

Expected outcomes:
- `useVoiceRecorder.test.ts`: verifies `MediaRecorder` start/stop lifecycle, MIME fallback (`audio/webm;codecs=opus` → `audio/mp4`), 60s auto-stop, `<= 10 MB` cap, microphone permission denial recovery, and media track cleanup on unmount.
- `QuickPostDraftEditor.test.tsx`: verifies **Red** (`EXPLICIT`) vs **Amber** (`INFERRED`) allergen badges + tooltip rationale & non-medical disclaimer, catalog dropdown requirement when `matched_menu_id === null`, inline quantity/override-price edits, `503` manual fallback handoff, and 1-Tap Batch Publish payload (`POST /api/v1/dishes/batch`).
- `SmartDiscoveryAI.test.tsx`: verifies Top 3 Smart Recommendations Carousel (`-70%` urgent deal badge, 20–30 word `ai_justification`, `OrderModal` trigger), Conversational Semantic Search prompt chips & Radar map sync, and graceful fallback/empty states.
- `AllergenPreferencesForm.test.tsx`: verifies all 14 EU FIC bilingual checkboxes, dietary lifestyle & budget persistence (`PUT /api/v1/users/me/preferences`), and immediate React Query cache invalidation of recommendations/search.

---

## 3. Backend AI Safety, Resilience, SLA & >=80% Coverage Gate (`EC5-06`)

Run the dedicated AI Safety & Resilience tests followed by the full backend coverage gate:

```bash
cd backend
# 1. Allergen Hard Invariant (0.0% leakage) & AI resilience suites
./venv_backend/bin/pytest tests/integration/test_allergen_invariant.py tests/integration/test_api_ml.py tests/integration/test_api_recommendations.py -v

# 2. Static quality gates
./venv_backend/bin/ruff check app/ tests/
./venv_backend/bin/ruff format --check app/ tests/
./venv_backend/bin/mypy app/

# 3. Full suite with mandatory >= 80% coverage enforcement
./venv_backend/bin/pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
```

Expected outcomes:
- `test_allergen_invariant.py`: **0.0%** allergen leakage across single/multi-allergen profiles, accented/unaccented Vietnamese inputs, canonical EU FIC keys, and adversarial semantic search queries.
- Fault-injection tests (missing API key, timeout, quota/rate limit, malformed schema): **0** unhandled `500` responses.
- Overall backend coverage exits `0` at **`>= 80%`**.

### Optional Live SLA Benchmark Verification (uses `GEMINI_TEST_API`)

```bash
cd backend
RUN_LIVE_SLA=1 ./venv_backend/bin/pytest tests/integration/test_api_ml.py tests/integration/test_api_recommendations.py -k sla -v -s
```

Verify observed P95 latencies meet:
- Quick-Post extraction: `< 3.0s`
- Personalized Recommendation (with Gemini): `< 2.5s` (deterministic fallback `< 300ms`)

---

## 4. Full-System Docker Compose Packaging & E2E UAT (`EC5-07`)

1. Validate Compose config and boot all 4 services (`postgres`, `redis`, `backend`, `frontend`):
   ```bash
   docker compose config --quiet
   docker compose up -d --build
   docker compose ps
   ```
   Confirm all 4 containers report `healthy` / `running`.
2. Run Alembic migrations and demo seed data inside the running backend container:
   ```bash
   docker compose exec backend alembic upgrade head
   docker compose exec backend python -m app.db.seed
   ```
3. Execute the full Release 1.0 E2E UAT walkthrough in the browser (`http://localhost:3000`):
   - **Store Partner (`EC5-04`)**: Login as approved `STORE_PARTNER` → open `/store/dishes` → record Vietnamese voice clip (or use text fallback) → verify Red (`EXPLICIT`) vs Amber (`INFERRED`) allergen badges + catalog dropdown + inline edits → click **1-Tap Batch Publish** → confirm new surplus dishes appear live on `/store/dishes` and `/`.
   - **Consumer Preferences & AI Discovery (`EC5-05`)**: Login as `CONSUMER` → open `/profile/preferences` via Navbar → exclude `Peanuts (Đậu phộng)` and set `max_budget = 35000` → Save → navigate to `/` → confirm Top 3 Smart Recommendations Carousel displays zero peanut dishes with `-70%` urgent deal badges and 20–30 word AI justification → tap semantic prompt chip *"Món nước nóng dưới 30k gần đây"* → confirm dish list and Leaflet Radar map pins synchronize → rescue a dish via `OrderModal`.
   - **Core Closure (F5–F8)**: Complete checkout (VNPay Sandbox or COD) → inspect dynamic HMAC QR on `/orders` → scan/verify QR as `STORE_PARTNER` on `/store/verify-qr` (confirm replay scan rejected) → submit verified review & verify Green Points + CO₂e update on `/green-points`.
4. Tear down cleanly when finished:
   ```bash
   docker compose down
   ```

---

## 5. Final Repository Gate & Release Tag Checklist

```bash
# From repo root
pre-commit run --all-files
git status
```

Confirm:
- Zero `.env` files staged, zero files `> 5 MB`.
- `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md`, `docs/project_management/pa5_sprint5/04_PA5_UAT_Signoff_and_Demo_Script.md`, `docs/PA5.md`, and `docs/PA5.pdf` are complete before Internal Deadline `2026-12-11` (`23:59`).
- Tag clean `main` commit as `v1.0.0` for Moodle submission (`2026-12-12`).
