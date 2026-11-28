# Quickstart Validation Guide: AI Feature 1 — Batch Quick-Post Multimodal Assistant

**Feature**: `002-ai-quick-post-nlp` | **Contracts**: [contracts/api-contracts.md](./contracts/api-contracts.md) | **Data Model**: [data-model.md](./data-model.md)

Use this guide to validate the AI-1 Quick-Post baseline end-to-end after implementation.

---

## 1. Prerequisites & Environment Verification

1. Ensure `google-genai==1.3.0` is installed in the backend virtual environment (`backend/venv_backend` on macOS or `backend/.venv`):
   ```bash
   cd backend
   ./venv_backend/bin/pip install google-genai==1.3.0
   ```
2. Ensure `backend/.env` configures the Gemini variables listed in `backend/.env.example` (never commit `backend/.env`):
   - `GEMINI_TEST_API` set for development/evaluation (`GEMINI_USE_DEMO_KEY=False`).
   - `GEMINI_DEMO_API` set for live demo (`GEMINI_USE_DEMO_KEY=True` only during demo).
   - `GEMINI_MODEL="gemini-2.5-flash"`, `GEMINI_TIMEOUT_SECONDS=15`.
3. Verify settings load cleanly without printing secrets:
   ```bash
   cd backend
   ./venv_backend/bin/python -c "import google.genai; from app.core.config import settings; print('SDK OK | Model:', settings.GEMINI_MODEL, '| Key ready:', bool(settings.gemini_key), '| Demo:', settings.GEMINI_USE_DEMO_KEY)"
   ```

---

## 2. Automated Test Suite (No External Network Calls)

Run the dedicated unit and integration tests using mocked Gemini clients and SQLite in-memory fixtures:

```bash
cd backend
./venv_backend/bin/pytest tests/unit/test_quick_post_service.py tests/integration/test_api_ml.py -v
```

Expected outcomes:
- Text extraction returns schema-valid `QuickPostExtractionResponse` with `EXPLICIT` and `INFERRED` allergens preserved.
- Menu-Catalog Grounding matches valid store `MenuItem` IDs, inherits missing `original_price`, and clears fabricated/cross-store UUIDs (`0%` false match).
- Native audio ingestion validates MIME/size (`<= 10 MB`, rejects unsupported types with `415`, oversized with `413`, empty with `422`) and passes `types.Part.from_bytes`.
- Unauthorized roles (`CONSUMER`, anonymous) receive `403`/`401`; unapproved KYC stores receive `403`; missing store receives `404`.
- Missing key, timeout, or invalid Gemini response returns graceful `503 Service Unavailable`.
- Extracted draft payload maps cleanly into `POST /api/v1/dishes/batch` (`201 Created`).

---

## 3. Live End-to-End Smoke Test (Swagger → `POST /api/v1/dishes/batch`)

1. Seed demo data (includes an approved `STORE_PARTNER` with active `menu_items`) and launch Uvicorn:
   ```bash
   cd backend
   ./venv_backend/bin/python -m app.db.seed
   ./venv_backend/bin/uvicorn app.main:app --reload --port 8000
   ```
2. Open `http://localhost:8000/docs`, authorize with the seeded `STORE_PARTNER` credentials (`POST /api/v1/auth/login`).
3. Invoke **`POST /api/v1/ml/parse-dish-nlp`** (`multipart/form-data`):
   - **Text test**: `raw_text="Còn 5 cơm sườn chả, 3 bún thịt nướng có đậu phộng rang xả từ giờ đến 9h tối, bún bán 20 cành"`.
   - **Audio test**: upload a 5–15s Vietnamese `.m4a` / `.wav` / `.webm` voice note.
4. Confirm `200 OK` returns valid `pickup_start`/`pickup_end` (anchored to `Asia/Ho_Chi_Minh` server time), `matched_menu_id` values matching the store's `GET /api/v1/stores/{store_id}/menu-items`, inherited `original_price`, and 2-tier allergen warnings.
5. Copy the reviewed output fields (`pickup_start`, `pickup_end`, and grounded `items`) into **`POST /api/v1/dishes/batch`** and verify `201 Created`.

---

## 4. Offline Golden Dataset Benchmark

Run the 15–20 case Vietnamese evaluation suite against live Gemini 2.5 Flash:

```bash
cd backend
./venv_backend/bin/python ../ml/eval/eval_ai1_quick_post.py --dataset ../ml/eval/golden_ai1_dataset.json
```

Expected targets (Week 6 Action Plan & Spec SC-001..SC-005):
- Schema Validity Rate: `>= 98%`
- Field Extraction Accuracy: `>= 90%`
- Menu Grounding Accuracy: `>= 90%` & False UUID Rate: `0%`
- Allergen Recall: `>= 95%`
- 2-Tier Source Accuracy: `>= 85%`
- Latency P95: `< 3.0s`

---

## 5. Mandatory Quality Gate (Before Commit)

```bash
cd backend
./venv_backend/bin/ruff check app/ tests/
./venv_backend/bin/ruff format --check app/ tests/
./venv_backend/bin/mypy app/
./venv_backend/bin/pytest tests/ -v
```

All commands MUST exit `0`.
