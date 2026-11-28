# Implementation Plan: Auth, Store KYC, Base Menu Catalog, Surplus Dishes & Rule-Based Time-Shift Discounting

**Branch**: `dev` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-auth-kyc-menu-pricing/spec.md`

## Summary

Deliver and harden the end-to-end **Core F1 (Auth, RBAC, Store KYC, Admin Review)**, **Core F2 (Base Menu Catalog & Surplus Dishes)**, and **Core F3 (Deterministic Rule-Based Time-Shift Discounting)** stack for EcoBite. The backend runs an async 3-tier FastAPI + SQLAlchemy 2.0 stack featuring HS256 JWT dual tokens with token-type and `is_active` enforcement, `UserCreate(extra="forbid")` privilege-escalation protection (`EC4-05`), `GET /api/v1/stores/me` self-lookup (`EC4-02`), PostGIS WGS84 store onboarding + Admin KYC approval, `StoreOwner`-isolated Base Menu CRUD, single and atomic batch menu-grounded surplus dish publishing, and deterministic `50%` / `70%` / manual-override pricing (Guardrail #5). The Next.js 14 App Router frontend delivers `/login`, `/register`, `/store/onboard`, `/admin`, `/store/menu`, `/store/dishes`, role-based `Navbar.tsx`, `AuthGuard.tsx`, `CountdownTimer.tsx`, and Vitest testing (`EC4-10`, `EC4-11`, `EC4-13` Navbar). Remaining follow-ups track client contract alignment on `/login`, `/register`, `/store/onboard`, and `types/api.ts`, dedicated Store/Admin Vitest component tests (`EC4-14`), and the wall-clock persistence edge case in `DishService._build_dish()`.

## Architecture Overview & Component Relationships

- **Layer flow**:
  - **Client (Next.js 14 App Router PWA)**: Pages (`/login`, `/register`, `/store/onboard`, `/admin`, `/store/menu`, `/store/dishes`) + shared UI (`Navbar.tsx`, `AuthGuard.tsx`, `CountdownTimer.tsx`) → typed service layer (`auth.service.ts`, `store.service.ts`, `menu.service.ts`, `dish.service.ts`) → Axios client (`@/lib/api-client`, auto Bearer token injection & 401 refresh-token retry).
  - **API Router Layer**: FastAPI routers (`auth.py`, `users.py`, `stores.py`, `menu.py`, `dishes.py`) registered in `backend/app/api/v1/router.py`, enforcing Pydantic v2 request/response schemas and `CurrentUser`, `require_roles(...)`, and `StoreOwner` (`require_store_owner`) dependencies from `backend/app/api/deps.py`.
  - **Service Layer**: `auth.py`, `user.py`, `store_service.py`, `menu_service.py`, `dish_service.py` executing credential verification, KYC validation/state transitions, approval gating, menu grounding, atomic batch coordination, and deterministic time-shift discount rules.
  - **Repository & ORM Layer**: `user_repo.py`, `store_repo.py`, `menu_repo.py`, `dish_repo.py` over SQLAlchemy 2.0 async `AsyncSession` (`models/{user,store,menu_item,dish}.py`) backed by PostgreSQL 16 + PostGIS 3.4 in Docker/production and SQLite `aiosqlite` in local dev & pytest.
- **Cross-cutting concerns**:
  - Authentication & RBAC via `get_current_user` (verifying `type == "access"` and `user.is_active`), `require_roles(...)`, and `require_store_owner` in `backend/app/api/deps.py`.
  - Per-request async session via `DBSession` (`get_db` in `backend/app/db/session.py`).
  - Environment-driven configuration strictly via `pydantic-settings` (`backend/app/core/config.py`), including fail-fast `validate_production_security()` blocking default `CHANGE_ME` secrets in production.
  - Portable column types (`JSON_TYPE` for JSONB/JSON; `LOCATION_TYPE` for PostGIS `Geometry(POINT, 4326)` / SQLite WKT string) and `ZoneInfo("Asia/Ho_Chi_Minh")` with `UTC+7` fallback.
- **Affected components & Team Ownership (Sprint 4 Traceability)**:

| Component / Module | Responsibility | Assignee & Jira ID | Current Status |
| :--- | :--- | :--- | :---: |
| `backend/app/core/{config,security}.py`, `backend/app/api/deps.py`, `backend/app/schemas/user.py`, `backend/app/services/{auth,user}.py`, `backend/app/api/v1/endpoints/{auth,users}.py` | Bcrypt hashing (`bcrypt==4.0.1`), HS256 dual tokens, `type="access"` & `is_active` checks, `UserCreate(extra="forbid")`, production secret guard, venv/deps sync | **Đàng Thế Tony** (`EC4-05`) | Implemented & Verified |
| `backend/tests/{unit/test_*_bug_exploration.py,unit/test_security.py,integration/test_api_{auth,users}.py,property/test_auth_preservation.py}` | Security regression, timezone fallback, and Hypothesis auth preservation test suites | **Đàng Thế Tony** (`EC4-05`) | Implemented & Passing |
| `backend/app/repositories/store_repo.py`, `backend/app/services/store_service.py`, `backend/app/api/v1/endpoints/stores.py` | Store onboarding (`PENDING`), static `GET /api/v1/stores/me` before `/{store_id}`, Admin pending list & KYC review (`APPROVED`/`REJECTED`) | **Đặng Trọng Phúc** (`EC4-02`) | Implemented & Verified |
| `backend/tests/{unit/test_store_{repo,service}.py,integration/test_api_stores.py}` | Store onboarding, Admin KYC review, and `GET /stores/me` (`200`/`401`/`403`/`404`) tests | **Đặng Trọng Phúc** (`EC4-02`) | Implemented & Passing |
| `backend/app/{repositories/menu_repo,services/menu_service,schemas/menu_item,api/v1/endpoints/menu}.py` & `backend/tests/{unit/test_menu_service,integration/test_api_menu}.py` | Base Menu Catalog CRUD, soft-delete, KYC approval gate, and `StoreOwner` isolation | **Đặng Trọng Phúc** / **Đàng Thế Tony** | Implemented & Passing |
| `backend/app/{repositories/dish_repo,services/dish_service,schemas/dish,api/v1/endpoints/dishes}.py` & `backend/tests/{unit/test_dish_service,integration/test_api_dishes}.py` | Single & batch surplus dish publishing, atomic stock control, deterministic 50%/70%/override pricing & countdown | **Đặng Trọng Phúc** / **Đàng Thế Tony** | Implemented (1 wall-clock bug in `_build_dish` to fix) |
| `frontend/package.json`, `frontend/vitest.{config,setup}.ts`, `frontend/src/types/api.ts`, `frontend/src/services/{auth,store,menu,dish}.service.ts` | Vitest test runner wiring + standardized DTOs and API service layer | **Võ Ngọc Thịnh** (`EC4-10`) | Implemented (Vitest runner active; `FoodCategory`/`DishStatus` enum sync pending) |
| `frontend/src/app/{admin,store/menu,store/dishes}/page.tsx`, `frontend/src/components/ui/Navbar.tsx`, `frontend/src/components/{CountdownTimer,auth/AuthGuard}.tsx` | Admin KYC Dashboard (`/admin`), Store Menu (`/store/menu`), Surplus Dishes (`/store/dishes`), role-based Navbar, AuthGuard, CountdownTimer | **Võ Ngọc Thịnh** (`EC4-11`, `EC4-13` Navbar) | Implemented (`AuthGuard` & `Navbar` Vitest passing; Store/Admin page tests tracked under `T030`) |
| `frontend/src/app/{login,register,store/onboard}/page.tsx` | Login, registration, and store KYC onboarding forms | **Võ Ngọc Thịnh** | Implemented (needs alignment to hardened backend contracts) |

- **External integrations**: None required for F1–F3 core execution (self-contained within FastAPI, PostgreSQL+PostGIS, and Next.js PWA; downstream consumers include Feature `001` Discovery/Orders/QR and Feature `007` AI Frontend Suite).

## Technical Context

**Language/Version**: Backend: Python 3.11+ (target `py311` in `backend/pyproject.toml`; local macOS venv `backend/venv_backend`); Frontend: TypeScript 5.4 (`strict: true`), Node.js `>= 18.17`

**Primary Dependencies**:
- Backend: FastAPI 0.111.0, Pydantic v2 (`2.7.4`), `pydantic-settings==2.3.4`, SQLAlchemy 2.0.30 (async), `asyncpg==0.29.0`, `aiosqlite==0.20.0`, `geoalchemy2==0.15.1`, `shapely==2.0.4`, `python-jose[cryptography]==3.3.0`, `passlib[bcrypt]==1.7.4`, `bcrypt==4.0.1`, `tzdata>=2024.1`
- Frontend: Next.js 14.2.35 (App Router), React 18.3.1, Tailwind CSS 3.4.4, Axios 1.7.2, TanStack React Query 5.45.1, `lucide-react` 0.395.0, Vitest 5.1.1, `@testing-library/react` 16.3.3, `jsdom` 31.0.1

**Storage**: PostgreSQL 16 + PostGIS 3.4 (production/Docker) and SQLite `aiosqlite` (local dev & pytest) persisting `users`, `stores`, `menu_items`, and `dishes` (already migrated in initial Alembic revision; zero new migrations required)

**Testing**: Backend: `pytest==8.2.2`, `pytest-asyncio==0.23.7` (`asyncio_mode = "auto"`), `hypothesis==6.98.3`, `httpx==0.28.1` ASGI client, `ruff==0.4.9`, `mypy==1.10.0` (`pydantic.mypy`); Frontend: `next lint`, `tsc --noEmit`, `vitest run`

**Target Platform**: Containerized Linux / macOS / Windows FastAPI ASGI backend (port 8000) + Responsive Next.js 14 PWA frontend (port 3000)

**Project Type**: Full-stack web application (`backend/` + `frontend/`)

**EcoBite Baseline (inherited from `constitution.md`)**: Python 3.11 · FastAPI (fully async) · Pydantic v2 · SQLAlchemy 2.0 async (`aiosqlite` for dev/test, `asyncpg` for PostgreSQL 16 + PostGIS; sync drivers only in Alembic) · JWT via `python-jose` HS256 with expiry · bcrypt hashing via passlib (`bcrypt==4.0.1` pinned) · pytest + pytest-asyncio + Hypothesis · ruff + mypy gates · Next.js 14 App Router + Vitest frontend

**Performance Goals**: `< 200 ms` p95 API latency on Auth, KYC, Menu CRUD, and Dish Publish/Quantity operations (NFR-001)

**Constraints**: Zero blocking I/O in async handlers; `0%` privilege escalation via registration; `0%` unapproved KYC publishing; `0%` cross-store mutation; exact `Decimal` (`ROUND_HALF_UP`) time-shift pricing; `remaining_quantity >= 0` DB `CheckConstraint`; zero secrets committed

**Scale/Scope**: 16 REST endpoints across 5 backend router modules (`auth`, `users`, `stores`, `menu`, `dishes`) + 6 frontend portal routes (`/login`, `/register`, `/store/onboard`, `/admin`, `/store/menu`, `/store/dishes`)

## Constitution Check

*GATE: Checked against `.specify/memory/constitution.md` (v1.2.0) and `AGENTS.md`.*

- [x] **Principle I (Test-First Development)**: Backend F1–F3 has comprehensive unit, integration, bug-exploration, and Hypothesis property test suites (`backend/tests/`); remaining defects (`DishService._build_dish` wall-clock fix) and frontend component tests (`frontend/__tests__/components/`) are explicitly scheduled test-first in `tasks.md` (`T030`, `T033`).
- [x] **Principle II (Security, Privacy & Access Control)**: Passwords hashed via passlib + `bcrypt==4.0.1`; HS256 JWT with `SECRET_KEY` from `pydantic-settings` + production placeholder guard; `type == "access"` and `user.is_active` enforced in `get_current_user`; `UserCreate(extra="forbid")` closes role escalation; `require_roles(...)` & `require_store_owner` protect all sensitive routes.
- [x] **Principle III (Data Integrity & Transactional Consistency)**: `Dish` enforces `CheckConstraint("remaining_quantity >= 0")`; `update_dish_quantity` uses conditional atomic `UPDATE ... WHERE id = :id AND total_quantity >= :qty`; `batch_create_dishes` commits all items in one DB transaction; `dish_repo.atomic_decrement_quantity` protects downstream checkout.
- [x] **Principle IV (Food Safety & Allergen Protection)**: Individual menu-grounded dishes replace mystery bags; `MenuItem` stores `base_allergens`/`standard_ingredients`; `Dish` preserves two-tier `AllergenWarning` (`EXPLICIT` vs `INFERRED`) and `dietary_notes`; unapproved (`PENDING`/`REJECTED`) kitchens are blocked at service layer.
- [x] **Principle V (Deterministic Business Rules & Payment Integrity)**: `DishService.calculate_time_shifted_discount` enforces deterministic `50%` standard / `70%` final 45-minute rush / explicit override rules using `Decimal` (`ROUND_HALF_UP`), with zero AI price estimation (Guardrail #5).
- [x] **Principle VI (AI Reliability, Structured Output & Model Isolation)**: Feature `003` uses zero generative AI for pricing or KYC; its `MenuItem` catalog and `POST /dishes/batch` contract cleanly ground and accept drafts from Feature `002` (`QuickPostExtractionResponse`).
- [x] **Principle VII (Clean Architecture & Async End-to-End)**: Fully async SQLAlchemy 2.0 `Mapped[T]` + `AsyncSession` (`asyncpg` / `aiosqlite`); Next.js 14 App Router with `'use client'` restricted to interactive forms/guards. Minor direct `self.db` queries inside `DishService` and `require_store_owner` are tracked transparently in Complexity Tracking below.
- [ ] **Principle VIII (Verifiable Quality & Human Accountability)**: Backend `ruff check`, `ruff format --check`, and `mypy` pass (`0` errors across `75` files), `pytest` passes (`348 passed` full suite, `63 passed` across Feature 003/001 suites on `2026-11-28`), and frontend `npm run lint`, `npm run type-check`, and `npm test` (`7 files / 20 tests`) pass, while `_build_dish()` wall-clock hardening (`T033`), Store/Admin Vitest component tests (`T030`), final `npm run build` confirmation (`T040`), and `pre-commit` (`T041`) remain tracked. **Gate will turn `[x]` once `T030`, `T033`, `T040`, and `T041` exit `0`.**

## Project Structure

### Documentation (this feature)

```text
specs/003-auth-kyc-menu-pricing/
├── spec.md              # Feature specification (Core F1, F2, F3)
├── plan.md              # This file (architecture, team ownership, Constitution check)
├── research.md          # Phase 0 design decisions & verified defect analysis
├── data-model.md        # ORM models, Pydantic schemas, TS DTOs & state machines
├── quickstart.md        # Runnable E2E verification guide
├── checklists/
│   └── requirements.md  # Spec quality validation checklist
├── contracts/
│   └── api-contracts.md # Complete REST contracts & frontend alignment notes
└── tasks.md             # Honest [X]/[ ] TDD task list with Assignee & Jira IDs
```

### Source Code (repository root)

```text
backend/
├── requirements.txt                             # Synced backend deps (bcrypt==4.0.1, tzdata, redis, hypothesis)
├── app/
│   ├── core/
│   │   ├── config.py                            # Settings + validate_production_security()
│   │   └── security.py                          # Bcrypt hashing + HS256 access/refresh JWT utilities
│   ├── api/
│   │   ├── deps.py                              # get_current_user (type/is_active), require_roles, require_store_owner
│   │   └── v1/
│   │       ├── router.py                        # Registers auth, users, stores, menu, dishes routers
│   │       └── endpoints/
│   │           ├── auth.py                      # POST /auth/{register,login,refresh}
│   │           ├── users.py                     # GET /users/me
│   │           ├── stores.py                    # POST /stores/onboard, GET /stores/me, GET /stores/{id}, /admin/stores/*
│   │           ├── menu.py                      # CRUD /stores/{id}/menu-items & /menu-items/{id}
│   │           └── dishes.py                    # POST /dishes, POST /dishes/batch, GET active, PATCH quantity
│   ├── models/
│   │   ├── user.py                              # User, UserRole, UserPreference, JSON_TYPE
│   │   ├── store.py                             # Store, KycStatus, LOCATION_TYPE (PostGIS + SQLite WKT)
│   │   ├── menu_item.py                         # MenuItem, ItemCategory, DietaryType
│   │   └── dish.py                              # Dish, DishStatus, CheckConstraint(remaining_quantity >= 0)
│   ├── schemas/
│   │   ├── user.py                              # UserCreate(extra="forbid"), UserResponse
│   │   ├── token.py                             # Token, UserLoginData, RefreshTokenRequest
│   │   ├── store.py                             # StoreOnboardRequest, StoreKycReview, StoreResponse
│   │   ├── menu_item.py                         # MenuItemBase, MenuItemUpdate, MenuItemResponse
│   │   └── dish.py                              # DishPublish, DishBatchPublish, DishQuantityUpdate, DishResponse
│   ├── repositories/
│   │   ├── user_repo.py                         # get_by_email, get_by_id, create
│   │   ├── store_repo.py                        # create_store, get_store_by_id/owner_id, get_pending_stores, update_store_status
│   │   ├── menu_repo.py                         # create, get_by_id, list_by_store, update, soft_delete
│   │   └── dish_repo.py                         # create, create_batch, list_active_by_store, atomic_decrement/increment
│   └── services/
│       ├── auth.py                              # authenticate_user, login_for_user, refresh_user_token
│       ├── user.py                              # create_user (forces UserRole.CONSUMER)
│       ├── store_service.py                     # StoreService (onboard, self-lookup, pending, KYC review)
│       ├── menu_service.py                      # MenuService (KYC-gated Base Menu CRUD)
│       └── dish_service.py                      # DishService (menu grounding, batch, stock, time-shift discounting)
└── tests/
    ├── unit/
    │   ├── test_security.py                     # Bcrypt & JWT roundtrip/expiry tests
    │   ├── test_registration_bug_exploration.py # Privilege escalation rejection (422)
    │   ├── test_inactive_user_bug_exploration.py# Deactivated user revocation (403)
    │   ├── test_token_bug_exploration.py        # Refresh-as-access & invalid type rejection (401)
    │   ├── test_config_bug_exploration.py       # Production CHANGE_ME secret rejection
    │   ├── test_timezone_bug_exploration.py     # ZoneInfo fallback to UTC+7
    │   ├── test_store_repo.py                   # WKT/Haversine & store repository tests
    │   ├── test_store_service.py                # StoreService including get_store_by_owner_id (EC4-02)
    │   ├── test_menu_service.py                 # MenuService error & KYC-gate tests
    │   └── test_dish_service.py                 # Discount rules, countdown, batch, atomic decrement tests
    ├── integration/
    │   ├── test_api_auth.py                     # Register, JSON/Form login, refresh tests
    │   ├── test_api_users.py                    # GET /users/me auth tests
    │   ├── test_api_stores.py                   # Onboarding, Admin KYC & GET /stores/me tests (EC4-02)
    │   ├── test_api_menu.py                     # Menu CRUD & cross-store ownership tests
    │   └── test_api_dishes.py                   # Dish publish, batch, active list & stock update tests
    └── property/
        └── test_auth_preservation.py            # Hypothesis auth/refresh/timezone/concurrency preservation tests

frontend/
├── package.json                                 # Next.js 14 + Vitest scripts (`"test": "vitest run"` active)
├── vitest.config.ts                             # jsdom + @/* alias configuration (EC4-10)
├── vitest.setup.ts                              # @testing-library/jest-dom setup (EC4-10)
├── src/
│   ├── lib/api-client.ts                        # Axios client with Bearer injection & 401 refresh interceptor
│   ├── types/api.ts                             # Shared Auth, Store, Menu, Dish TypeScript DTOs
│   ├── services/
│   │   ├── auth.service.ts                      # register, login, logout, getCurrentUser
│   │   ├── store.service.ts                     # onboardStore, getMyStore, getPendingStores, reviewStoreKyc
│   │   ├── menu.service.ts                      # Base Menu Catalog REST client (EC4-10)
│   │   └── dish.service.ts                      # Surplus Dish & stock REST client (EC4-10)
│   ├── components/
│   │   ├── CountdownTimer.tsx                   # Live HH:MM:SS countdown timer (Core F3)
│   │   ├── auth/AuthGuard.tsx                   # Client-side token & role route guard
│   │   └── ui/Navbar.tsx                        # Role-aware top navigation (EC4-13 Navbar)
│   └── app/
│       ├── login/page.tsx                       # Sign-in page
│       ├── register/page.tsx                    # Account registration page
│       ├── admin/page.tsx                       # Admin KYC Verification Dashboard (EC4-11)
│       └── store/
│           ├── onboard/page.tsx                 # Store Partner KYC onboarding form
│           ├── menu/page.tsx                    # Store Base Menu Catalog portal (EC4-11)
│           └── dishes/page.tsx                  # Store Surplus Dish publish & stock portal (EC4-11)
└── __tests__/
    └── components/                              # Vitest component tests to be added (EC4-14)
```

**Structure Decision**: Follows EcoBite's canonical monorepo layout (`backend/app/{core,api,models,schemas,repositories,services}` + `backend/tests/{unit,integration,property}` and `frontend/src/{app,components,services,lib,types}` + `frontend/__tests__/{components,hooks}`) per `AGENTS.md` Section 3 and EcoBite Constitution v1.2.0.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| `DishService` (`backend/app/services/dish_service.py`) executes direct `self.db.get`/`select`/`update` statements alongside `dish_repo.py` | Existing PA3 implementation consolidated atomic conditional `UPDATE ... WHERE total_quantity >= quantity` and multi-item batch lookup inside `DishService` | Refactoring all `DishService` DB calls into `dish_repo.py` is deferred to post-PA4 cleanup to avoid introducing regression risk during Release 0.3 freeze; new code must stay strictly in repositories |
| `require_store_owner` (`backend/app/api/deps.py`) queries `MenuItem`, `Dish`, and `Store` via `AsyncSession` inside a router dependency | Centralizes cross-store ownership authorization across `/stores/{store_id}`, `/menu-items/{item_id}`, `/dishes/{dish_id}`, `/dishes`, and `/dishes/batch` in one reusable `StoreOwner` dependency | Repeating ownership queries inside every service method would risk inconsistent `403`/`404` enforcement across endpoints |
