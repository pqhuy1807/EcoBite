# Quickstart Validation Guide: Auth, Store KYC, Base Menu Catalog, Surplus Dishes & Time-Shift Discounting

**Feature**: `003-auth-kyc-menu-pricing` | **Contracts**: [contracts/api-contracts.md](./contracts/api-contracts.md) | **Data Model**: [data-model.md](./data-model.md)

Use this guide to validate Core Features `F1`, `F2`, and `F3` end-to-end across backend APIs, automated tests, and Next.js portals.

---

## 1. Prerequisites & Environment Verification

1. **Backend virtual environment (`backend/venv_backend` on macOS or `backend/.venv`)**:
   ```bash
   cd backend
   ./venv_backend/bin/pip install -r requirements.txt
   ```
2. **Backend environment file**: Copy `backend/.env.example` to `backend/.env` if not present (never commit `.env`). Ensure `SECRET_KEY`, `DATABASE_URL` (SQLite default or Postgres PostGIS), and `CORS_ORIGINS` include `http://localhost:3000`.
3. **Frontend dependencies**:
   ```bash
   cd frontend
   npm install
   ```
   Ensure `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` (default in `frontend/src/lib/api-client.ts`).

---

## 2. Automated Backend Verification (F1, F2, F3)

Run all Feature `003` unit, integration, security regression, and Hypothesis property tests against SQLite in-memory fixtures:

```bash
cd backend
./venv_backend/bin/pytest \
  tests/unit/test_security.py \
  tests/unit/test_registration_bug_exploration.py \
  tests/unit/test_inactive_user_bug_exploration.py \
  tests/unit/test_token_bug_exploration.py \
  tests/unit/test_config_bug_exploration.py \
  tests/unit/test_timezone_bug_exploration.py \
  tests/unit/test_store_repo.py \
  tests/unit/test_store_service.py \
  tests/unit/test_menu_service.py \
  tests/unit/test_dish_service.py \
  tests/integration/test_api_auth.py \
  tests/integration/test_api_users.py \
  tests/integration/test_api_stores.py \
  tests/integration/test_api_menu.py \
  tests/integration/test_api_dishes.py \
  tests/property/test_auth_preservation.py -v
```

Expected verifications:
- Public registration rejects `role` injection (`422`), hashes passwords with bcrypt, and blocks duplicate emails (`409`).
- Refresh tokens cannot access `/api/v1/users/me` (`401`), deactivated users receive `403`, and production `CHANGE_ME` secret fails fast.
- `GET /api/v1/stores/me` returns `200` for an onboarded partner, `404` without a store, `403` for consumers, and `401` when unauthenticated (`EC4-02`).
- Admin KYC review approves/rejects pending stores; pending stores cannot add menu items or publish surplus dishes (`403`).
- Menu CRUD and surplus dish publishing enforce strict `StoreOwner` isolation (`403` cross-store) and deterministic `50%` / `70%` / override pricing (once `T033` fixes the `14:15–15:00` wall-clock bug in `DishService._build_dish`).

---

## 3. Live End-to-End Walkthrough (Backend + Frontend Portals)

1. **Seed realistic demo accounts and launch both servers**:
   ```bash
   # Terminal 1 — Backend (port 8000)
   cd backend
   ./venv_backend/bin/python -m app.db.seed --reset
   ./venv_backend/bin/uvicorn app.main:app --reload --port 8000

   # Terminal 2 — Frontend (port 3000)
   cd frontend
   npm run dev
   ```
   Seeded demo accounts (all use password `Password123!`):
   - **Admin**: `admin@ecobite.vn`
   - **Approved Store Partner**: `merchant.bui@ecobite.vn` (*Cơm Tấm Bụi Sài Gòn - Hai Bà Trưng*)
   - **Consumer**: `consumer.an@ecobite.vn`
   - **Pending KYC Stores**: 2 seeded `PENDING` storefronts ready in the Admin review queue.

2. **Verify Core F1 — Auth, Self-Lookup & Admin KYC (`/admin`)**:
   - Open `http://localhost:8000/docs` and test `POST /api/v1/auth/register` (consumer only; verify `role: "admin"` returns `422`), `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, and `GET /api/v1/users/me`.
   - Sign in on `http://localhost:3000/login` as `admin@ecobite.vn` → navigate to `http://localhost:3000/admin` (visible in `Navbar` only for `ADMIN`).
   - Verify pending stores load from `GET /api/v1/admin/stores/pending`; approve one store (`APPROVED`) and reject another with a reason (`REJECTED`).

3. **Verify Core F2 & F3 — Base Menu Catalog (`/store/menu`) & Surplus Dishes (`/store/dishes`)**:
   - Sign in as `merchant.bui@ecobite.vn` → verify `Navbar` shows `Thực đơn gốc`, `Món dư cuối ca`, `Quét QR Quán`, and `Hồ sơ KYC`.
   - Open `http://localhost:3000/store/menu`: confirm `GET /api/v1/stores/me` resolves the store, add a new Base Menu item (`Cơm sườn bì chả`, `45,000 VND`), edit its name, and verify soft-delete removes it from active listings.
   - Open `http://localhost:3000/store/dishes`: select a Base Menu item, confirm the live `-50%` rescue price preview, publish a surplus batch with a pickup window and `-70%` rush start time (or explicit override price), verify the newly published card renders, and decrement/increment remaining quantity (`PATCH /dishes/{id}/quantity`) down to `0` (`HẾT SUẤT`) and back within `total_quantity`.

---

## 4. Mandatory Quality Gates (Before Commit)

### Backend (`backend/`)
```bash
cd backend
./venv_backend/bin/ruff check app/
./venv_backend/bin/ruff format --check app/
./venv_backend/bin/mypy app/
./venv_backend/bin/pytest tests/ -v
```

### Frontend (`frontend/`, after `T003` & `T030`)
```bash
cd frontend
npm run lint
npm run type-check
npm run test
npm run build
```

### Repository Pre-Commit Hooks (repo root)
```bash
pre-commit run --all-files
```

All commands MUST exit `0` before proposing a commit.
