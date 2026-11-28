---
description: "Dependency-ordered TDD task list for EcoBite Feature 003 — Auth, Store KYC, Base Menu Catalog, Surplus Dishes & Rule-Based Time-Shift Discounting (F1, F2, F3)"
---

# Tasks: Auth, Store KYC, Base Menu Catalog, Surplus Dishes & Rule-Based Time-Shift Discounting

**Input**: Design documents from `/specs/003-auth-kyc-menu-pricing/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/api-contracts.md`, `quickstart.md`

**Tests**: Test tasks are **MANDATORY** and listed **FIRST** inside every User Story phase per EcoBite Constitution Principle I (Test-First Development — Red-Green-Refactor). Checkbox status (`[X]` vs `[ ]`) reflects verified ground-truth repository state as of `2026-11-28` (`31 [X]` done / `10 [ ]` remaining = `41` total tasks).

**Organization**: Tasks are grouped by User Story (`US1`–`US5`) with Sprint 4 Assignee (`Phúc`, `Tony`, `Thịnh`) and Jira ID (`EC4-02`, `EC4-05`, `EC4-10`, `EC4-11`, `EC4-13`, `EC4-14`) traceability.

## Format: `[ID] [P?] [Story] (Assignee | Jira) Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: User story label (`[US1]`–`[US5]`) — omitted in Setup, Foundational, Polish, and Verification Gate phases
- Exact repository-relative file paths included in every task

---

## Phase 1: Setup (Shared Environment & Test Toolchain)

**Purpose**: Synchronize backend Python dependencies and configure the frontend Vitest test runner cleanly.

- [X] T001 (Tony | EC4-05) Sync backend virtual environment with `backend/requirements.txt` (`bcrypt==4.0.1`, `tzdata>=2024.1`, `redis==5.0.6`, `httpx==0.28.1`, `hypothesis==6.98.3`, `pytest-asyncio`, `ruff`, `mypy`) and verify baseline backend toolchain execution
- [X] T002 [P] (Thịnh | EC4-10) Configure Vitest, React Testing Library, `@testing-library/jest-dom`, and `jsdom` with `@/*` path alias in `frontend/vitest.config.ts`, `frontend/vitest.setup.ts`, and `frontend/package.json` `devDependencies`
- [ ] T003 (Thịnh | EC4-10) Remove duplicate `"test"` script key in `frontend/package.json` (lines 11–12), keeping `"test": "vitest run --passWithNoTests"`, and run `npm install` in `frontend/` so local `node_modules` resolves `vitest` and `@vitejs/plugin-react` cleanly

**Checkpoint**: Backend venv runs all tools cleanly; `T003` unlocks `npm run type-check` and `npm run test` on frontend.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core persistent models, security primitives, centralized FastAPI dependencies, and frontend API client/services shared across all F1–F3 user stories.

**⚠️ CRITICAL**: All foundational tasks are already implemented in the repository.

- [X] T004 (Tony | EC4-05) Implement core SQLAlchemy 2.0 `Mapped[T]` ORM models (`User`, `UserRole`, `Store`, `KycStatus`, `MenuItem`, `ItemCategory`, `DietaryType`, `Dish`, `DishStatus`) with portable `JSON_TYPE`, PostGIS/WKT `LOCATION_TYPE`, and `CheckConstraint("remaining_quantity >= 0")` in `backend/app/models/{user,store,menu_item,dish}.py`
- [X] T005 [P] (Tony | EC4-05) Implement bcrypt password hashing, HS256 dual-token JWT utilities (`type="access"` / `type="refresh"`), and `Settings.validate_production_security()` fail-fast guard in `backend/app/core/{security,config}.py`
- [X] T006 [P] (Tony | EC4-05) Implement shared FastAPI dependencies (`get_current_user` enforcing `token_type == "access"` & `user.is_active`, `require_roles`, `require_store_owner`) in `backend/app/api/deps.py` and `ZoneInfo("Asia/Ho_Chi_Minh")` UTC+7 fallback in `backend/app/services/order_service.py`
- [X] T007 [P] (Thịnh | EC4-10) Standardize Axios client (Bearer injection + 401 refresh-token retry) in `frontend/src/lib/api-client.ts`, shared DTOs in `frontend/src/types/api.ts`, and service clients in `frontend/src/services/{auth,store,menu,dish}.service.ts`

**Checkpoint**: Foundation ready — models, JWT/RBAC dependencies, and typed frontend service layer are in place.

---

## Phase 3: User Story 1 - Secure Auth, Dual-Token Refresh & Role-Based Access Control (Priority: P1) 🎯 MVP

**Goal**: Prevent privilege escalation on registration, enforce dual-token HS256 authentication and inactive-user revocation, expose `GET /api/v1/users/me`, and deliver role-based frontend navigation and auth screens.

**Independent Test**: Run `pytest tests/unit/test_security.py tests/unit/test_*_bug_exploration.py tests/integration/test_api_auth.py tests/integration/test_api_users.py tests/property/test_auth_preservation.py -v` and verify login/register/navbar role flows in browser.

### Tests for User Story 1 (MANDATORY — TDD First) ⚠️

- [X] T008 [P] [US1] (Tony | EC4-05) Author unit and security regression tests covering bcrypt/JWT expiry, `UserCreate(extra="forbid")` role-escalation rejection (`422`), `is_active=False` revocation (`403`), refresh-as-access token confusion (`401`), production `CHANGE_ME` secret guard, and timezone fallback in `backend/tests/unit/{test_security,test_registration_bug_exploration,test_inactive_user_bug_exploration,test_token_bug_exploration,test_config_bug_exploration,test_timezone_bug_exploration}.py`
- [X] T009 [P] [US1] (Tony | EC4-05) Author integration and Hypothesis property-based preservation tests for register/login/refresh, `/users/me`, and concurrent active authentications in `backend/tests/integration/{test_api_auth,test_api_users}.py` and `backend/tests/property/test_auth_preservation.py`

### Implementation for User Story 1

- [X] T010 [US1] (Tony | EC4-05) Enforce `UserCreate(extra="forbid")` in `backend/app/schemas/user.py` and hard-assign `UserRole.CONSUMER` in `backend/app/services/user.py` and `backend/app/repositories/user_repo.py`
- [X] T011 [US1] (Tony | EC4-05) Implement dual-token authentication service and endpoints (`POST /auth/register`, hybrid JSON/Form `POST /auth/login`, `POST /auth/refresh`, `GET /users/me`) in `backend/app/services/auth.py`, `backend/app/schemas/token.py`, and `backend/app/api/v1/endpoints/{auth,users}.py`
- [X] T012 [US1] (Thịnh | EC4-13) Implement role-aware top navigation (`CONSUMER`, `STORE_PARTNER`, `ADMIN`) in `frontend/src/components/ui/Navbar.tsx` and client route guard in `frontend/src/components/auth/AuthGuard.tsx`
- [X] T013 [US1] (Thịnh) Build login and registration pages in `frontend/src/app/login/page.tsx` and `frontend/src/app/register/page.tsx`
- [ ] T014 [US1] (Thịnh) Align `frontend/src/app/login/page.tsx` (delegate to `authService.login()` so `refresh_token` is saved and `ecobite-auth-change` fires; redirect `CONSUMER` → `/`, `STORE_PARTNER` → `/store/menu`, `ADMIN` → `/admin`) and align `frontend/src/app/register/page.tsx` + `RegisterRequest` in `frontend/src/types/api.ts` to omit `role`/`workspace_id` fields rejected with `422` by `UserCreate(extra="forbid")`

**Checkpoint**: Backend Auth/RBAC & `Navbar.tsx` are verified; `T014` completes frontend `/login` and `/register` alignment.

---

## Phase 4: User Story 2 - Store Partner KYC Onboarding, Self-Lookup & Admin Verification (Priority: P1)

**Goal**: Enable Store Partners to submit food-safety (`ATVSTP`) KYC applications and query their own store status (`GET /api/v1/stores/me`), while Admins review pending applications on `/admin`.

**Independent Test**: Run `pytest tests/unit/test_store_repo.py tests/unit/test_store_service.py tests/integration/test_api_stores.py -v` and test Approve/Reject flows on `http://localhost:3000/admin`.

### Tests for User Story 2 (MANDATORY — TDD First) ⚠️

- [X] T015 [P] [US2] (Phúc | EC4-02) Author repository and service unit tests for WGS84 WKT/Haversine, onboarding validation, `get_store_by_owner_id` (`200`/`404`), pending queue, and KYC approval/rejection in `backend/tests/unit/test_store_repo.py` and `backend/tests/unit/test_store_service.py`
- [X] T016 [P] [US2] (Phúc | EC4-02) Author integration tests for `POST /stores/onboard`, `CONSUMER` `403`, Admin pending/review (`APPROVED`/`REJECTED`/`422`), and `GET /api/v1/stores/me` (`200`/`401`/`403`/`404`) in `backend/tests/integration/test_api_stores.py`

### Implementation for User Story 2

- [X] T017 [US2] (Phúc | EC4-02) Implement `store_repo.get_store_by_owner_id`, `StoreService` onboarding/self-lookup/review workflows, and static route `GET /api/v1/stores/me` ordered before dynamic `GET /api/v1/stores/{store_id}` in `backend/app/repositories/store_repo.py`, `backend/app/services/store_service.py`, `backend/app/schemas/store.py`, and `backend/app/api/v1/endpoints/stores.py`
- [X] T018 [US2] (Thịnh | EC4-11) Build Admin KYC Verification Dashboard (`ADMIN`-guarded, Approve/Reject with mandatory reason) in `frontend/src/app/admin/page.tsx` and Store KYC Onboarding form in `frontend/src/app/store/onboard/page.tsx`
- [ ] T019 [US2] (Thịnh) Wire `frontend/src/app/store/onboard/page.tsx` to `storeService.onboardStore()` (`POST /api/v1/stores/onboard` JSON contract) wrapped in `AuthGuard` with real API error handling instead of legacy `submitKyc()` (`/stores/kyc`) silent fallback

**Checkpoint**: Backend Store KYC + `GET /stores/me` (`EC4-02`) and Admin Dashboard (`/admin`, `EC4-11`) pass; `T019` wires `/store/onboard` to the canonical backend endpoint.

---

## Phase 5: User Story 3 - Base Menu Catalog Management & Store Ownership Isolation (Priority: P1)

**Goal**: Enable approved Store Partners to maintain canonical Base Menu items (`menu_items`) with verified retail prices, photos, ingredients, and base allergens while blocking unapproved kitchens and cross-store access.

**Independent Test**: Run `pytest tests/unit/test_menu_service.py tests/integration/test_api_menu.py -v` and exercise add/edit/soft-delete on `http://localhost:3000/store/menu`.

### Tests for User Story 3 (MANDATORY — TDD First) ⚠️

- [X] T020 [P] [US3] (Tony) Author unit tests for `MenuService` (`404` missing store/item, `403` `PENDING` KYC gate, empty partial-update no-op) in `backend/tests/unit/test_menu_service.py`
- [X] T021 [P] [US3] (Tony) Author integration tests for menu CRUD, soft-delete, non-positive price rejection (`422`), `401` unauthenticated, and cross-store `403` isolation in `backend/tests/integration/test_api_menu.py`

### Implementation for User Story 3

- [X] T022 [US3] (Phúc) Implement `menu_repo.py`, `MenuService`, schemas (`MenuItemBase`, `MenuItemUpdate`, `MenuItemResponse`), and `StoreOwner`-protected CRUD endpoints in `backend/app/repositories/menu_repo.py`, `backend/app/services/menu_service.py`, `backend/app/schemas/menu_item.py`, and `backend/app/api/v1/endpoints/menu.py`
- [X] T023 [US3] (Thịnh | EC4-11) Build Store Base Menu Catalog portal (self-lookup via `GET /stores/me`, KYC status gate banners, create/edit/soft-delete list) in `frontend/src/app/store/menu/page.tsx`
- [ ] T024 [US3] (Thịnh) Align `FoodCategory` (`'DRINKS'` → `'BEVERAGE'`) and `DishStatus` (`'HIDDEN'` → `'INACTIVE'`) in `frontend/src/types/api.ts` and `frontend/src/app/store/menu/page.tsx` to match backend `ItemCategory` and `DishStatus` enums

**Checkpoint**: Backend Base Menu Catalog and `/store/menu` work end-to-end; `T024` eliminates category enum mismatch on beverage items.

---

## Phase 6: User Story 4 - Surplus Dish Publishing, Atomic Batch Post & Real-Time Stock Control (Priority: P1)

**Goal**: Enable approved Store Partners to publish single or atomic multi-dish surplus listings grounded in their Base Menu Catalog and adjust live remaining stock with non-negative and upper-bound invariants.

**Independent Test**: Run `pytest tests/unit/test_dish_service.py tests/integration/test_api_dishes.py -v` and publish/adjust stock on `http://localhost:3000/store/dishes`.

### Tests for User Story 4 (MANDATORY — TDD First) ⚠️

- [X] T025 [P] [US4] (Tony) Author unit tests for menu grounding, KYC approval gate, cross-store batch rejection, single/batch creation, excess stock rejection, and `dish_repo.atomic_decrement_quantity` in `backend/tests/unit/test_dish_service.py`
- [X] T026 [P] [US4] (Tony) Author integration tests for `POST /dishes`, `POST /dishes/batch`, `GET /stores/{store_id}/dishes/active`, `PATCH /dishes/{dish_id}/quantity`, invalid window/quantity (`422`), and cross-store `403` isolation in `backend/tests/integration/test_api_dishes.py`

### Implementation for User Story 4

- [X] T027 [US4] (Phúc) Implement `dish_repo.py` (including atomic stock decrement/increment), `DishService` single & transactional batch publication + atomic quantity adjustment, schemas (`DishPublish`, `DishBatchPublish`, `DishQuantityUpdate`, `DishResponse`), and `StoreOwner`-protected routes in `backend/app/repositories/dish_repo.py`, `backend/app/services/dish_service.py`, `backend/app/schemas/dish.py`, and `backend/app/api/v1/endpoints/dishes.py`
- [X] T028 [US4] (Thịnh | EC4-11) Build Store Surplus Dishes & Real-Time Stock portal (Base Menu selector, `-50%` preview, pickup/rush/override fields, active list with `-/+` stock buttons) in `frontend/src/app/store/dishes/page.tsx`

**Checkpoint**: Single/batch surplus publishing and real-time stock control are operational across backend and `/store/dishes`.

---

## Phase 7: User Story 5 - Deterministic Rule-Based Time-Shift Discounting & Live Countdown (Priority: P2)

**Goal**: Enforce deterministic `50%` standard / `70%` final 45-minute rush / explicit override pricing (Guardrail #5), expose live countdown calculation, and eliminate the wall-clock defect in `DishService._build_dish()`.

**Independent Test**: Run `pytest tests/unit/test_dish_service.py tests/integration/test_api_dishes.py -v` at any time of day (including `14:15–15:00`) and run `npm run test` for `CountdownTimer` and `Navbar` Vitest suites.

### Tests for User Story 5 (MANDATORY — TDD First) ⚠️

- [X] T029 [P] [US5] (Tony) Author deterministic pricing and countdown unit tests (`50%` standard, `70%` final 45-minute rush, override precedence, `override > original_price` `422`, and `get_countdown_to_final_rush`) in `backend/tests/unit/test_dish_service.py`
- [ ] T030 [P] [US5] (Thịnh | EC4-14) Author Vitest component tests in `frontend/__tests__/components/` covering `CountdownTimer` (live ticking & zero clamp), `Navbar` role-based links (`CONSUMER`, `STORE_PARTNER`, `ADMIN`), and Store Portal / Admin KYC flows

### Implementation for User Story 5

- [X] T031 [US5] (Phúc) Implement deterministic `DishService.calculate_time_shifted_discount`, `get_countdown_to_final_rush`, and dynamic `current_price` / `is_rule_discount_active` serialization in `backend/app/services/dish_service.py`
- [X] T032 [US5] (Thịnh) Implement live `CountdownTimer` component (`frontend/src/components/CountdownTimer.tsx`) and `-50%` / `-70%` rush badge UI in `frontend/src/app/store/dishes/page.tsx` and `frontend/src/components/DishCard.tsx`
- [ ] T033 [US5] (Phúc | Tony) Fix wall-clock persistence bug in `DishService._build_dish()` (`backend/app/services/dish_service.py`) so `dish.rescue_price` always stores the canonical `50%` standard rescue price (or explicit `override_discounted_price`) even when created during the final 45-minute rush window, while `serialize_dish()` computes dynamic `current_price`, and add a regression test in `backend/tests/unit/test_dish_service.py`

**Checkpoint**: Pricing engine is 100% deterministic at every hour of the day and covered by both pytest and Vitest.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Seeded demo readiness and end-to-end walkthrough validation across F1–F3.

- [X] T034 (Phúc | Tony) Provide seeded demo accounts (`admin@ecobite.vn`, `merchant.bui@ecobite.vn`, `consumer.an@ecobite.vn`), approved and `PENDING` KYC stores, Base Menu items, and surplus dishes in `backend/app/db/seed.py`
- [ ] T035 [P] (Thịnh | Tony) Execute end-to-end manual smoke walkthrough from `specs/003-auth-kyc-menu-pricing/quickstart.md` across Auth, Admin KYC (`/admin`), Store Menu (`/store/menu`), Store Dishes (`/store/dishes`), and Time-Shift Pricing

---

## Final Phase: Verification Gate (Constitution Principle VIII) — MANDATORY

**Purpose**: Reproducible evidence that every Backend, Frontend, and Repository Quality Gate exits `0`. Do NOT mark unchecked items `[X]` without executing and passing them.

### Backend (`backend/`, using `venv_backend` or `.venv`)

- [X] T036 (Tony | EC4-05) `./venv_backend/bin/ruff check app/` — verified zero lint findings on all F1–F3 modules
- [X] T037 (Tony | EC4-05) `./venv_backend/bin/mypy app/` — verified zero static type errors across all 12 F1–F3 modules
- [ ] T038 (Tony | EC4-05) `./venv_backend/bin/ruff format --check app/` and `./venv_backend/bin/pytest tests/ -v` — full suite PASS 100% after `T033` fixes the `14:15–15:00` wall-clock failure in `test_api_dishes.py`

### Frontend (`frontend/`)

- [X] T039 (Thịnh | EC4-10) `npm run lint` — verified zero ESLint warnings or errors
- [ ] T040 (Thịnh | EC4-10) `npm run type-check`, `npm run test`, and `npm run build` — all exit `0` after `T003` (`package.json` cleanup + `npm install`) and `T030` (Vitest suites)

### Repository Hooks (repo root)

- [ ] T041 (Tony) `pre-commit run --all-files` — secrets check, file size (`< 5 MB`), and formatting hooks pass with exit `0`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)** → **Phase 2 (Foundational)** → **Phases 3–7 (US1–US5)** → **Phase 8 (Polish)** → **Final Phase (Verification Gate)**.
- All Backend foundations (`T001`, `T004`–`T006`) and primary implementations (`T010`–`T011`, `T017`, `T022`, `T027`, `T031`) are already complete; remaining work splits cleanly into two parallel tracks:
  - **Backend Track (`Phúc` / `Tony`)**: `T033` (fix `_build_dish()` wall-clock bug + regression test) → `T038` (full backend verification gate) → `T041` (`pre-commit`).
  - **Frontend Track (`Thịnh`)**: `T003` (`package.json` duplicate `"test"` key cleanup + `npm install`) → parallel client fixes `T014`, `T019`, `T024` + Vitest tests `T030` → `T035` (E2E walkthrough) → `T040` (`type-check`, `test`, `build`).

### Parallel Opportunities

```bash
# Independent remaining tasks that can execute concurrently without file conflicts:
Backend (Phúc/Tony): T033 -> backend/app/services/dish_service.py + backend/tests/unit/test_dish_service.py
Frontend (Thịnh):    T003 -> frontend/package.json (unblocks T030 & T040)
Frontend (Thịnh):    T014 -> frontend/src/app/{login,register}/page.tsx
Frontend (Thịnh):    T019 -> frontend/src/app/store/onboard/page.tsx
Frontend (Thịnh):    T024 -> frontend/src/types/api.ts + frontend/src/app/store/menu/page.tsx
Frontend (Thịnh):    T030 -> frontend/__tests__/components/*.test.tsx
```

---

## Implementation Strategy

1. **Close P0 Blockers First**: Run `T003` (`frontend/package.json` cleanup + `npm install`) and `T033` (`DishService._build_dish()` fix) immediately so both automated verification gates turn green.
2. **Close Frontend Contract Alignment**: Ship `T014`, `T019`, and `T024` so every F1–F3 frontend route (`/login`, `/register`, `/store/onboard`, `/admin`, `/store/menu`, `/store/dishes`) speaks the exact hardened PA4 backend contract.
3. **Lock Quality Gates**: Complete `T030` (Vitest tests), run `T035` (quickstart E2E), and pass `T038`, `T040`, and `T041` with `0` errors before Release 0.3 (`v0.3.0-pa4`).
