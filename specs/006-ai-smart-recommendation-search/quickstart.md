# Quickstart Validation Guide: AI Feature 2 — Smart Food Recommendation & Conversational Semantic Search

**Feature**: `006-ai-smart-recommendation-search` | **Contracts**: [contracts/api-contracts.md](./contracts/api-contracts.md) | **Data Model**: [data-model.md](./data-model.md)

Use this guide to validate AI Feature 2 (`EC5-02`, `EC5-03`, `EC5-06`) end-to-end after implementation.

---

## 1. Prerequisites & Environment Verification

1. Ensure backend dependencies (including `google-genai==1.3.0`, `hypothesis==6.98.3`, and `tzdata`) are installed in the project virtual environment (`backend/venv_backend` on macOS or `backend/.venv`):
   ```bash
   cd backend
   ./venv_backend/bin/pip install -r requirements.txt
   ```
2. Ensure `backend/.env` configures Gemini settings matching `backend/.env.example` (never commit `backend/.env`):
   - `GEMINI_TEST_API` set for development/evaluation (`GEMINI_USE_DEMO_KEY=False`).
   - `GEMINI_DEMO_API` set only for live demo (`GEMINI_USE_DEMO_KEY=True` during demo).
   - `GEMINI_MODEL="gemini-2.5-flash"`, `GEMINI_RECOMMENDATION_TIMEOUT_SECONDS=2.0`.
3. Verify SDK & configuration load cleanly without printing secrets:
   ```bash
   cd backend
   ./venv_backend/bin/python -c "import google.genai; from app.core.config import settings; print('SDK OK | Model:', settings.GEMINI_MODEL, '| Rec timeout:', settings.GEMINI_RECOMMENDATION_TIMEOUT_SECONDS, '| Key ready:', bool(settings.gemini_key), '| Demo:', settings.GEMINI_USE_DEMO_KEY)"
   ```

---

## 2. Automated Test Suite (Zero External Network Calls)

Run the dedicated AI-2 unit, integration, and Allergen Hard Invariant suites (SQLite in-memory + SQL JSON1 `json_each` + mocked Gemini clients):

```bash
cd backend
./venv_backend/bin/pytest \
  tests/unit/test_preference_repo.py \
  tests/unit/test_recommendation_repo.py \
  tests/unit/test_recommendation_service.py \
  tests/integration/test_api_preferences.py \
  tests/integration/test_api_recommendations.py \
  tests/integration/test_allergen_invariant.py -v
```

Expected outcomes:
- `GET`/`PUT /api/v1/users/me/preferences` enforces `CONSUMER` RBAC, normalizes Vietnamese/English synonyms (including `"Hải sản"` → Crustaceans + Molluscs + Fish) to canonical `EUAllergen` values, and rejects invalid allergens with `422`.
- Layer 1 SQL query (`recommendation_repo.py`) achieves **0.0% Allergen Leakage** directly inside SQL `WHERE NOT EXISTS`, covering `dishes.allergens`, `menu_items.base_allergens`, accented/unaccented/legacy strings, `DishStatus.ACTIVE`, `remaining_quantity > 0`, active pickup windows, approved KYC stores, and dietary lifestyle (`VEGAN`/`VEGETARIAN`).
- Layer 2 deterministic scoring obeys `0.40 * proximity + 0.30 * discount_urgency + 0.30 * taste_match`, prioritizes final-rush (`-70%`, `<= 30–45 min`) deals, handles cold-start users cleanly, and breaks ties deterministically.
- Layer 3 validates numeric faithfulness (`0%` fabricated numbers) and falls back cleanly in `< 300ms` (`justification_source="FALLBACK"`) on missing key, timeout, SDK failure, or hallucinated numbers.
- `POST /api/v1/dishes/search-semantic` routes both anonymous and authenticated queries through Layer 1 SQL Allergen Hard Filter, fails closed (`401`) on invalid/expired Bearer tokens, and falls back to the deterministic Vietnamese intent parser when Gemini is unavailable.

---

## 3. Live End-to-End Smoke Test (Swagger with Seeded Consumers)

1. Seed the 23 HCMC stores and 3 demo consumers (`pref_an` with Peanut allergy, `pref_bich` Vegetarian with Seafood + Milk allergy, `pref_huy` with no exclusions) and start Uvicorn:
   ```bash
   cd backend
   ./venv_backend/bin/python -m app.db.seed --reset
   ./venv_backend/bin/uvicorn app.main:app --reload --port 8000
   ```
2. Open `http://localhost:8000/docs` and authenticate as a seeded `CONSUMER` (`POST /api/v1/auth/login`).
3. **Update & verify preferences**:
   - Call `PUT /api/v1/users/me/preferences` with:
     ```json
     {
       "preferred_categories": ["NOODLES", "VEGETARIAN"],
       "dietary_preference": "NONE",
       "excluded_allergens": ["đậu phộng", "Hải sản"],
       "max_budget": 35000
     }
     ```
   - Call `GET /api/v1/users/me/preferences` and verify `excluded_allergens` persisted as canonical EU FIC values (`Peanuts`, `Crustaceans`, `Molluscs`, `Fish`).
4. **Test Personalized Recommendations**:
   - Call `GET /api/v1/recommendations/personalized?lat=10.7769&lng=106.7009&radius_km=5.0&limit=3`.
   - Confirm `200 OK`, zero dishes containing Peanuts, Crustaceans, Molluscs, or Fish/Fish sauce (check both `allergens` and store catalog), valid `score_breakdown`, and concise 20–30 word Vietnamese `ai_justification` grounded in exact DB prices/distances.
5. **Test Conversational Semantic Search**:
   - Call `POST /api/v1/dishes/search-semantic` (with and without `Authorization` header):
     ```json
     {
       "query": "Tìm món chay thanh đạm dưới 30k gần đây",
       "latitude": 10.7769,
       "longitude": 106.7009,
       "radius_km": 5.0
     }
     ```
   - Confirm `parsed_intent` extracts `max_price=30000`, `categories=["VEGETARIAN"]`, `dietary="VEGETARIAN"`, and authenticated results strictly honor `excluded_allergens` (`0.0%` leakage).
   - Send an invalid token `Authorization: Bearer invalid-token` to `POST /api/v1/dishes/search-semantic` and confirm fail-closed **`401 Unauthorized`**.

---

## 4. Offline Golden Dataset Benchmark

Run the 15–20 scenario AI-2 offline evaluation suite (both live Gemini and fallback latency benchmark):

```bash
cd backend
./venv_backend/bin/python ../ml/eval/eval_ai2_recommendation.py --dataset ../ml/eval/golden_ai2_dataset.json
```

Expected targets (Week 6 Action Plan & Spec SC-001..SC-005):
- **Allergen Leakage Rate**: **`0.0%`** (Hard Invariant — fails run if `> 0.0%`)
- **Ranking Quality**: **`NDCG@3 >= 0.85`** (plus `Precision@3` reported)
- **Semantic Intent Extraction Accuracy**: **`>= 90%`**
- **Justification Faithfulness**: **`>= 95%`** (`0%` fabricated numeric values, 20–30 words)
- **Latency**: **P95 `< 2.5s`** (with Gemini) / **`< 300ms`** (fallback mode)

---

## 5. Mandatory Quality Gate (Before Commit)

```bash
cd backend
./venv_backend/bin/ruff check app/ tests/
./venv_backend/bin/ruff format --check app/ tests/
./venv_backend/bin/mypy app/
./venv_backend/bin/pytest tests/ -v
cd ..
pre-commit run --all-files
```

All commands MUST exit `0`.
