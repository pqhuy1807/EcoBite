# Quickstart Validation Guide: Verified Reviews, Green Points Wallet & Atomic Vouchers (Feature 8)

**Feature**: `005-reviews-gamification-vouchers` | **Contracts**: [contracts/api-contracts.md](./contracts/api-contracts.md) | **Data Model**: [data-model.md](./data-model.md)

Use this guide to validate Feature 8 end-to-end across Backend APIs, Concurrency Safety, Demo Seed Data, Frontend Consumer UI, and Quality Gates.

---

## 1. Prerequisites & Demo Data Seeding

1. Ensure the backend virtual environment (`backend/.venv` or `backend/venv_backend`) has all dependencies from `backend/requirements.txt` installed.
2. Reset and populate comprehensive demo data (includes 4 active vouchers `ECOBITE10K`/`GREENHERO20K`/`ECO25K`/`ECO50K`, `COMPLETED` orders, a sample verified `Review`, claimed `UserVoucher`, and consistent `GreenPointsLedger` entries):
   ```bash
   cd backend
   ./venv_backend/bin/python -m app.db.seed --reset
   ```
   *(On Windows/standard `.venv`, substitute `.venv/bin/python` or `.venv\Scripts\python`.)*

### Seeded Test Accounts (Password: `Password123!`)
| Email | Role | Starting Points | Completed Orders | Best Used For |
| :--- | :--- | :---: | :---: | :--- |
| `consumer.huy@ecobite.vn` | `CONSUMER` | `350` | `1` (`7` meals, `17.50 kg` CO₂, **unreviewed**) | Testing `ReviewModal` `201` + duplicate `409`, `Chiến Binh Xanh (Eco Hero)` rank, redeeming `ECOBITE10K`/`ECO25K` |
| `consumer.an@ecobite.vn` | `CONSUMER` | `180` | `1` (`2` meals, `5.00 kg` CO₂, **already reviewed**) | Testing `409` already-reviewed order, My Vouchers (`ECOBITE10K`), multi-entry Ledger (`+180`, `-100`, `+100`) |
| `consumer.bich@ecobite.vn` | `CONSUMER` | `90` | `0` | Testing disabled redeem buttons (`< 100` pts) & `Mầm Xanh (Eco Seedling)` rank |
| `merchant.bui@ecobite.vn` | `STORE_PARTNER` | `0` | — | Testing `403 Forbidden` RBAC enforcement on Consumer-only Feature 8 endpoints |

---

## 2. Backend Automated Tests (Unit, Integration & Concurrency)

Run the dedicated Feature 8 test suites (SQLite in-memory & file-backed concurrency test, zero external network dependencies):

```bash
cd backend
./venv_backend/bin/pytest \
  tests/unit/test_review_repo.py \
  tests/unit/test_review_service.py \
  tests/integration/test_api_reviews.py \
  tests/unit/test_gamification_service.py \
  tests/integration/test_api_gamification.py -v
```

Expected verified behaviors:
- `POST /api/v1/orders/{order_id}/review`: `201 Created` updates `Store.rating_avg` & `rating_count` transactionally; `403` for non-Consumer or non-owner; `404` for unknown order; `409` for non-`COMPLETED` or duplicate review (including simulated `IntegrityError` race).
- `GET /api/v1/stores/{store_id}/reviews`: `200 OK` paginated newest-first list (`[]` when empty).
- `GET /api/v1/green-points/me`: `200 OK` aggregates only `COMPLETED` orders, returns exact rule-based `rank_title` (preserving rank via CO₂ after spending points), and blocks `401`/`403`.
- `GET /api/v1/vouchers` & `GET /api/v1/vouchers/me`: filters inactive/expired vouchers (`expires_at > now`), sorts ascending by `points_required`, and scopes claimed vouchers to requesting Consumer.
- `POST /api/v1/vouchers/{voucher_id}/redeem`: atomically deducts points, logs negative `VOUCHER_REDEEM` ledger entry, creates `UserVoucher`, rolls back on mid-tx error, and returns `409` on insufficient points / `400` on expired or inactive voucher.
- **Concurrent Redemption Burst (`EC4-15`)**: 10 simultaneous HTTP requests from a 150-point consumer on a 100-point voucher produce **exactly 1 `200 OK`**, **9 `409 Conflict`**, final balance `50` (never `< 0`), `1` `UserVoucher`, and `1` negative ledger entry.

---

## 3. Live API Smoke Test (Swagger UI)

1. Start the FastAPI server:
   ```bash
   cd backend
   ./venv_backend/bin/uvicorn app.main:app --reload --port 8000
   ```
2. Open `http://localhost:8000/docs` and authenticate via `POST /api/v1/auth/login` as `consumer.huy@ecobite.vn` (`Password123!`).
3. Verify **Gamification & Vouchers**:
   - `GET /api/v1/green-points/me` → confirm `balance_points: 350`, `total_co2_saved_kg: "17.50"`, `total_meals_saved: 7`, `rank_title: "Chiến Binh Xanh (Eco Hero)"`.
   - `GET /api/v1/vouchers` → confirm 4 active vouchers sorted `ECOBITE10K` (100) → `GREENHERO20K` (180) → `ECO25K` (250) → `ECO50K` (500).
   - `POST /api/v1/vouchers/{ECOBITE10K_id}/redeem` → confirm `200 OK`, `points_deducted: 100`, `remaining_balance: 250`.
   - Re-check `GET /api/v1/green-points/me` (balance `250`, rank still `"Chiến Binh Xanh (Eco Hero)"`, newest ledger entry `-100 VOUCHER_REDEEM`) and `GET /api/v1/vouchers/me` (contains `ECOBITE10K`, `is_used: false`).
   - Attempt `POST /api/v1/vouchers/{ECO50K_id}/redeem` → confirm `409 Conflict` (`"Không đủ Điểm Xanh để đổi voucher này"`).
4. Verify **Verified Reviews**:
   - Look up `consumer.huy`'s `COMPLETED` order ID (`EB-20261101-0002`) via `GET /api/v1/orders/me`.
   - Submit `POST /api/v1/orders/{order_id}/review` with `{"rating": 5, "comment": "Cơm sườn nóng hổi!", "tags": ["Ngon", "Đúng giờ"]}` → confirm `201 Created`.
   - Repeat the exact same request → confirm `409 Conflict` (`"Đơn hàng đã được đánh giá trước đó"`).
   - Call `GET /api/v1/stores/{store_id}/reviews` → confirm the new review appears first.

---

## 4. Frontend Consumer UI Walkthrough & Vitest (`EC4-13` / `EC4-14`)

1. Start the Next.js dev server (`http://localhost:3000`):
   ```bash
   cd frontend
   npm run dev
   ```
2. Log in at `/login` as `consumer.huy@ecobite.vn` (`Password123!`).
3. Click **"Điểm Xanh"** in the navbar (`/green-points`):
   - Confirm header shows live points balance, CO₂ saved (kg), meals saved, and Eco Rank badge.
   - In **Đổi Voucher** tab, verify `ECO50K` (500 pts) button is disabled (`balance < 500`), then click redeem on `ECOBITE10K` (100 pts) and verify balance drops immediately, voucher appears in **Voucher của tôi**, and `-100` entry appears in **Lịch sử Điểm Xanh** without manual reload.
4. Navigate to **"Đơn của tôi"** (`/orders`):
   - Filter to **Hoàn thành** (`COMPLETED`) and click **"Đánh giá"** to open `ReviewModal`.
   - Select 5 stars, add a comment, submit → confirm success toast and modal close.
   - Log in as `consumer.an@ecobite.vn` and attempt to review the already-reviewed `COMPLETED` order → confirm friendly Vietnamese `409` duplicate feedback.
5. Run Vitest component tests:
   ```bash
   cd frontend
   npm run test
   ```

---

## 5. Mandatory Quality Gate (All Must Exit `0` Before Commit)

```bash
# Backend Quality Gate
cd backend
./venv_backend/bin/ruff check app/ tests/
./venv_backend/bin/ruff format --check app/ tests/
./venv_backend/bin/mypy app/
./venv_backend/bin/pytest tests/ -v

# Frontend Quality Gate
cd ../frontend
npm run lint
npm run type-check
npm run test
npm run build

# Repository Pre-Commit Gate
cd ..
pre-commit run --all-files
```
