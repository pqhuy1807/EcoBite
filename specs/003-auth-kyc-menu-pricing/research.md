# Technical Research & Design Decisions: Auth, Store KYC, Base Menu Catalog, Surplus Dishes & Time-Shift Discounting

**Feature**: `003-auth-kyc-menu-pricing` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

This document records the architectural, security, data-integrity, pricing, and frontend integration decisions for Core Features `F1`, `F2`, and `F3`, including concrete defects verified against the repository during Sprint 4 (`EC4-02`, `EC4-05`, `EC4-10`, `EC4-11`, `EC4-13`).

---

## Decision 1: Privilege-Escalation Prevention on Public Registration (`EC4-05`)

- **Decision**: Define `UserCreate` in `backend/app/schemas/user.py` without a `role` field and with `model_config = ConfigDict(extra="forbid")`, while `user_service.create_user()` hard-codes `role=UserRole.CONSUMER`.
- **Rationale**:
  - Earlier iterations inherited `role` from `UserBase`, allowing an unauthenticated caller to submit `{"role": "admin"}` or `{"role": "store_partner"}` to `POST /api/v1/auth/register` and gain immediate administrative privileges.
  - Using `extra="forbid"` rejects unexpected fields loudly with HTTP `422 Unprocessable Entity` instead of silently ignoring them, making security tests (`test_registration_bug_exploration.py`) unambiguous and catching outdated frontend payloads early.
  - Privileged accounts (`STORE_PARTNER`, `ADMIN`) in tests and staging are created via DB fixtures (`conftest.py`) or `app/db/seed.py`.
- **Alternatives considered**:
  - Allowing `CONSUMER` and `STORE_PARTNER` self-registration while blocking only `ADMIN`: rejected during PA4 security hardening (`EC4-05`) because unvetted partner role elevation increases surface area; if self-signup for partners is re-introduced in a later sprint, it must be an explicit, audited onboarding flow.

---

## Decision 2: Dual-Token HS256 JWT Separation, `is_active` Revocation & Production Secret Guard (`EC4-05`)

- **Decision**:
  - Issue distinct HS256 JWTs in `backend/app/core/security.py`: access tokens carry `type="access"` (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 60 min) and refresh tokens carry `type="refresh"` (7 days), signed with `settings.SECRET_KEY`.
  - Enforce `payload.get("type") == "access"` (`401` on mismatch) and `user.is_active is True` (`403 "Inactive user"` on deactivation) inside `get_current_user` (`backend/app/api/deps.py`), and enforce `type == "refresh"` + `user.is_active` inside `auth_service.refresh_user_token()`.
  - Enforce `Settings.validate_production_security()` in `backend/app/core/config.py`, raising `ValueError` at startup if `APP_ENV == "production"` and `"CHANGE_ME"` appears in `SECRET_KEY`.
  - Pin `bcrypt==4.0.1` alongside `passlib[bcrypt]==1.7.4` in `backend/requirements.txt`.
- **Rationale**:
  - Closes three critical vulnerabilities verified by `test_token_bug_exploration.py`, `test_inactive_user_bug_exploration.py`, and `test_config_bug_exploration.py` while keeping valid auth/refresh flows preserved across Hypothesis property tests (`test_auth_preservation.py`).
  - `bcrypt>=4.1` breaks `passlib==1.7.4` metadata introspection; pinning `4.0.1` is required by EcoBite Constitution Principle II.
- **Alternatives considered**:
  - Stateful JWT blocklist in Redis: unnecessary overhead for PA4 when `get_current_user` already loads the `User` row and checks `user.is_active` on every protected request.

---

## Decision 3: Static Route Ordering for `GET /api/v1/stores/me` (`EC4-02`)

- **Decision**: Register `@router.get("/stores/me")` (and legacy alias `/me`) **before** `@router.get("/stores/{store_id}")` in `backend/app/api/v1/endpoints/stores.py`, guarded by `Depends(require_roles(UserRole.STORE_PARTNER))` and delegating to `StoreService.get_store_by_owner_id()` → `store_repo.get_store_by_owner_id()`.
- **Rationale**:
  - FastAPI matches routes in registration order; registering `/stores/{store_id: UUID}` first causes `/stores/me` to fail UUID path parsing with `422`.
  - Store portals (`/store/menu`, `/store/dishes`) need a single authoritative endpoint to resolve the logged-in partner's `store_id` and `kyc_status` without hardcoding or storing `store_id` in JWT claims.
  - Returns `200 OK` with serialized store profile, `404 Not Found` if the partner has not onboarded a store yet, `403 Forbidden` for `CONSUMER`/`ADMIN`, and `401` when unauthenticated (verified in `test_api_stores.py` and `test_store_service.py`).
- **Alternatives considered**:
  - Embedding `store_id` in the JWT payload at login: stale immediately after onboarding or multi-store expansion, and would require re-login after `POST /stores/onboard`.

---

## Decision 4: Portable PostGIS Coordinates & JSONB Columns Across PostgreSQL and SQLite

- **Decision**:
  - Store coordinates in `stores.location` using `LOCATION_TYPE = String(255).with_variant(Geometry("POINT", srid=4326), "postgresql")` (`backend/app/models/store.py`), formatting coordinates as standard WKT `POINT(longitude latitude)` and decoding both WKB (`geoalchemy2.shape.to_shape`) and WKT strings in `store_repo.parse_point_wkt()`.
  - Store JSON arrays (`standard_ingredients`, `base_allergens`, `ingredients`, `allergens`, `dietary_notes`) using `JSON_TYPE = JSON().with_variant(JSONB, "postgresql")` (`backend/app/models/user.py`).
- **Rationale**:
  - Satisfies Guardrail #2 (PostGIS `Geometry(POINT, 4326)` with GIST indexing in PostgreSQL 16) while allowing the entire `pytest` suite to execute fast in-memory against `sqlite+aiosqlite` (`backend/tests/conftest.py`) without requiring a live Postgres container for unit/integration development.
- **Alternatives considered**:
  - Storing separate `latitude`/`longitude` float columns instead of PostGIS `Geometry`: violates Guardrail #2 and sacrifices native PostGIS `ST_DWithin` / GIST spatial indexing used by Feature `001` Radar Discovery.

---

## Decision 5: Centralized `StoreOwner` Dependency & Soft-Delete Menu Grounding

- **Decision**:
  - Centralize store-ownership authorization in `require_store_owner` (`StoreOwner` annotated alias in `backend/app/api/deps.py`), resolving target `store_id` from path `store_id`, path `item_id` (`MenuItem`), path `dish_id` (`Dish`), or request body `menu_item_id` (`POST /dishes`, `POST /dishes/batch`), and asserting `current_user.role == UserRole.STORE_PARTNER` and `store.owner_id == current_user.id`.
  - Soft-delete `MenuItem` records (`is_active = False`) in `menu_repo.soft_delete()` and declare `Dish.menu_item_id` with `ForeignKey("menu_items.id", ondelete="SET NULL")`.
  - Enforce `store.kyc_status == KycStatus.APPROVED` inside `MenuService.create_menu_item()` and `DishService._ensure_store_approved()`.
- **Rationale**:
  - Guarantees consistent `403 Forbidden` isolation across all menu and surplus-dish endpoints (verified in `test_api_menu.py` and `test_api_dishes.py`) without repeating ownership boilerplate.
  - Soft-deleting catalog items keeps historical `dishes` and `orders` intact while preventing newly published surplus dishes from grounding against retired menu items (`menu_item.is_active` check in `DishService`).
- **Alternatives considered**:
  - Hard-deleting `MenuItem` rows: breaks audit trails and merchant analytics; rejected.

---

## Decision 6: Deterministic Rule-Based Time-Shift Discounting & Verified `_build_dish()` Wall-Clock Defect

- **Decision**:
  - Implement all pricing purely deterministically in `DishService.calculate_time_shifted_discount()` (`backend/app/services/dish_service.py`) using `Decimal` with `ROUND_HALF_UP` quantization (`Decimal("0.01")`):
    - `rescue_price = original_price * 0.50` (`-50%` standard rescue tier)
    - `rule_discount_price = original_price * 0.30` (`-70%` final rush tier)
    - Default rush threshold: `max(pickup_start_time, pickup_end_time - 45 minutes)`, overridable by explicit `rule_discount_start_time` within `[pickup_start_time, pickup_end_time]`
    - If `override_discounted_price` is set (`0 < override <= original_price`), it takes fixed precedence (`current_price = override`, `is_rule_discount_active = False`)
  - **Verified Defect to Fix (`T033`)**: During live verification at `14:50` local time, `test_api_dishes.py::test_create_dish_grounds_menu_data_and_calculates_prices` failed (`AssertionError: assert '13500.00' == '22500.00'`). Root cause: `DishService._build_dish()` (line 197 of `backend/app/services/dish_service.py`) calls `calculate_time_shifted_discount()` with default `current_time=datetime.now().time()` and persists the returned *active* price directly into `dish.rescue_price`. When a dish with pickup window `14:00–15:00` is published between `14:15` and `15:00`, `dish.rescue_price` gets overwritten with the 70% rush price (`13500.00`) instead of preserving the canonical 50% standard `rescue_price` (`22500.00`), even though `serialize_dish()` already computes `current_price` dynamically on read!
  - **Fix design**: In `DishService._build_dish()`, persist canonical `rescue_price = override_price if override_price is not None else (original_price * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` (still validating `override_price` via `calculate_time_shifted_discount` or an explicit guard), while `serialize_dish()` continues computing live `current_price` and `is_rule_discount_active` dynamically.
- **Rationale**: Eliminates wall-clock flakiness in `test_api_dishes.py` and keeps the database column `dishes.rescue_price` true to its documented semantics ("standard 40–50% rescue price") at every minute of the day (Guardrail #5).

---

## Decision 7: Cross-Platform Timezone Handling (`EC4-05`)

- **Decision**: Pin `tzdata>=2024.1` in `backend/requirements.txt` and wrap `ZoneInfo("Asia/Ho_Chi_Minh")` initialization with a `ZoneInfoNotFoundError` fallback to `timezone(timedelta(hours=7))` (verified by `test_timezone_bug_exploration.py` and `test_auth_preservation.py`).
- **Rationale**: Prevents startup/import crashes on minimal Windows and Docker slim Python environments lacking OS-level IANA timezone packages.

---

## Decision 8: Frontend Test Toolchain (`EC4-10`) & Verified Frontend-Backend Contract Gaps

- **Decision**: Use Vitest (`5.1.1`) + `@testing-library/react` (`16.3.3`) + `@testing-library/jest-dom` (`8.0.0`) + `jsdom` (`31.0.1`) configured in `frontend/vitest.config.ts` and `frontend/vitest.setup.ts`, with Axios auto-refresh in `frontend/src/lib/api-client.ts` and role-based portals in `frontend/src/app/{admin,store/menu,store/dishes}/page.tsx` and `Navbar.tsx`.
- **Verified Codebase Gaps Tracked as `[ ]` in `tasks.md`**:
  1. **Duplicate `"test"` script key & uninstalled devDependencies (`T003`, `EC4-10` cleanup)**: `frontend/package.json` currently has two `"test"` entries on lines 11–12 (`"vitest run --passWithNoTests"` and `"vitest run"`), and `node_modules` lacks `vitest` / `@vitejs/plugin-react` until `npm install` is run—causing `tsc --noEmit` to fail on `vitest.config.ts` and `npm run test` to exit `127`.
  2. **`/login` & `/register` contract drift (`T014`)**: `frontend/src/app/login/page.tsx` posts directly via `apiClient` instead of `authService.login()`, skips persisting `refresh_token` and dispatching `ecobite-auth-change`, and redirects to non-existent `/onboard` and `/radar` routes instead of `/store/menu`, `/admin`, and `/`. Meanwhile, `frontend/src/app/register/page.tsx` still sends `role` and `workspace_id`, which now return `422` due to `UserCreate(extra="forbid")`.
  3. **`/store/onboard` endpoint drift (`T019`)**: `frontend/src/app/store/onboard/page.tsx` calls legacy `storeService.submitKyc()` (`POST /stores/kyc` FormData, which does not exist on the backend, silently swallowing errors in a `catch` block) instead of `storeService.onboardStore()` (`POST /stores/onboard` JSON).
  4. **Category & Status enum mismatch (`T024`)**: `frontend/src/types/api.ts` and `frontend/src/app/store/menu/page.tsx` use `'DRINKS'` and `'HIDDEN'`, whereas backend `ItemCategory` defines `'BEVERAGE'` and `DishStatus` defines `'INACTIVE'`. Selecting `'DRINKS'` on `/store/menu` would trigger a backend `422`.
  5. **Frontend Vitest suite empty (`T030`, `EC4-14`)**: `frontend/__tests__/components/` currently contains only `.gitkeep`; unit tests for `CountdownTimer`, `Navbar`, and portal logic remain to be authored.
- **Alternatives considered**:
  - Jest instead of Vitest: rejected because Vitest aligns with Vite/ESM ergonomics, runs faster in CI, and was explicitly adopted in `AGENTS.md` and `EC4-10`.
