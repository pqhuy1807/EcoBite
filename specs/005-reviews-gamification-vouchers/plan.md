# Implementation Plan: Verified Reviews, Green Points Wallet, CO₂ Impact Tracker & Atomic Voucher Redemption (Feature 8)

**Branch**: `feat/fe-f8-gamification-reviews` *(Backend core merged on `dev`; Consumer UI, Vitest & Concurrency QA in progress for PA4 Release 0.3)* | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-reviews-gamification-vouchers/spec.md`

## Summary

Deliver the complete full-stack **Feature 8 (Verified Reviews, Green Points Wallet, CO₂ Impact Tracker & Atomic Voucher Redemption)** for EcoBite PA4 Release 0.3. The **backend** (`EC4-07`, `EC4-08`, `EC4-09`) is implemented and verified following the strict 3-tier async FastAPI architecture (`Router -> Service -> Repository`): Verified Reviews (`POST /api/v1/orders/{order_id}/review`, `GET /api/v1/stores/{store_id}/reviews`) enforce `COMPLETED`-order ownership, DB-backed `UNIQUE(order_id)` anti-duplication, and transactional `Store.rating_avg`/`rating_count` aggregation; Gamification & Vouchers (`GET /api/v1/green-points/me`, `GET /api/v1/vouchers`, `GET /api/v1/vouchers/me`, `POST /api/v1/vouchers/{voucher_id}/redeem`) enforce deterministic Eco Rank thresholds (with CO₂ rank preservation), `COMPLETED`-only impact aggregation, and atomic SQL point deduction (`WHERE green_points_balance >= :cost RETURNING green_points_balance`) paired with a user-scoped Redis distributed lock (`lock:green_points:user:{user_id}`) and rich demo seed data in `backend/app/db/seed.py`. The remaining **Week 6 scope** (`EC4-13` Consumer UI, `EC4-14` Vitest Part 2, `EC4-15` concurrent voucher verification) adds typed frontend DTOs & services (`gamification.service.ts`, `review.service.ts`), the `/green-points` wallet/voucher page, `ReviewModal.tsx` wired into `/orders` for `COMPLETED` orders, Vitest + React Testing Library component tests, and a multi-session concurrent redemption integration test.

## Architecture Overview & Component Relationships

- **Backend Layer Flow (Implemented)**:
  - **Reviews (F8A)**: Client → `backend/app/api/v1/endpoints/reviews.py` (`require_roles(UserRole.CONSUMER)` on `POST`, public paginated `GET`) → `ReviewService` (`backend/app/services/review_service.py`: role, order lookup, ownership, `OrderStatus.COMPLETED`, pre-check + `IntegrityError` rollback backstop) → `ReviewRepository` (`backend/app/repositories/review_repo.py`: `create_review`, `get_by_order_id`, `list_by_store`, `update_store_rating`) + `OrderRepository` → PostgreSQL 16 / SQLite `aiosqlite`.
  - **Gamification & Vouchers (F8B)**: Client → `backend/app/api/v1/endpoints/gamification.py` (registered in `router.py` BEFORE `stores.router` to prevent legacy `GET /{store_id}` wildcard interception; static `/vouchers/me` declared BEFORE `/vouchers/{voucher_id}/redeem`) → `GamificationService` (`backend/app/services/gamification_service.py`: deterministic `RANK_THRESHOLDS`, `_as_utc` normalization, `distributed_lock`, atomic voucher redemption orchestration) → `GamificationRepository` (`backend/app/repositories/gamification_repo.py`: `atomic_deduct_points`, `get_completed_rescue_stats`, `get_ledger_by_user`, `create_ledger_entry`, `list_available_vouchers`, `get_user_vouchers`, `create_user_voucher`) → PostgreSQL 16 / SQLite `aiosqlite` + optional Redis 7.
  - **Upstream Earning Trigger (Existing `EC4-06`)**: `OrderService.verify_and_complete_order` (`backend/app/services/order_service.py`) atomically increments `User.green_points_balance`, inserts an `ORDER_RESCUE` row into `green_points_ledger`, and accumulates `Store.total_co2_saved_kg` upon QR pickup confirmation.
- **Frontend Layer Flow (Pending `EC4-13` / `EC4-14`)**:
  - **Navigation (Already Wired)**: `frontend/src/components/ui/Navbar.tsx` already links `CONSUMER` users to `/green-points` ("Điểm Xanh") and `/orders` ("Đơn của tôi").
  - **Typed API Services**: `frontend/src/types/api.ts` (new Review + Gamification DTOs) → `frontend/src/services/gamification.service.ts` and `frontend/src/services/review.service.ts` → shared Axios instance `@/lib/api-client` (auto Bearer JWT, 401 refresh, `extractApiErrorMessage`).
  - **Consumer Wallet Page**: `frontend/src/app/green-points/page.tsx` (`'use client'`, wrapped in `<AuthGuard allowedRoles={['CONSUMER']}>`) using TanStack React Query (`useQuery` for `['green-points-me']`, `['vouchers-available']`, `['vouchers-me']`; `useMutation` for `redeemVoucher` invalidating all 3 query keys on success).
  - **In-Order Verified Review Modal**: `frontend/src/components/ReviewModal.tsx` (`'use client'`, built over `@/components/ui/Modal`, `Button`, `Toast`) mounted inside `frontend/src/app/orders/page.tsx` with a *"Đánh giá"* trigger button shown exclusively on `order.status === 'COMPLETED'`.
- **Cross-Cutting Concerns**:
  - Server-side RBAC via `Depends(require_roles(UserRole.CONSUMER))` and JWT auth via `get_current_user` (`backend/app/api/deps.py`).
  - Per-request async DB session (`DBSession` / `get_db`) with explicit transaction boundaries (`commit=False` on repository helpers, single `await self.db.commit()` / `rollback()` in services).
  - Optional Redis lock (`app.core.redis.distributed_lock`) degrades safely when Redis is unavailable; database atomic `UPDATE` and `UNIQUE` constraints remain authoritative invariants.
  - Disjoint file ownership in Week 6: Tony owns `gamification.service.ts`, `review.service.ts`, `green-points/page.tsx`, `ReviewModal.tsx`, Feature 8 types, Feature 8 Vitest files, and only attaches the Review button to `orders/page.tsx` after Thịnh merges `EC4-12`.
- **External Integrations**:
  - **Redis 7 (Optional Distributed Lock)**: Failure modes (connection refused, timeout) are swallowed gracefully by `distributed_lock()` in `app/core/redis.py`, falling back seamlessly to PostgreSQL/SQLite row-level atomic SQL execution without returning `500`.

## Technical Context

**Language/Version**:
- Backend: Python 3.11+ (`target = py311` in `backend/pyproject.toml`; local venv `backend/.venv` / `backend/venv_backend`)
- Frontend: TypeScript 5.4 (`strict: true`), Next.js 14.2 (`App Router`), React 18.3, Tailwind CSS 3.4

**Primary Dependencies**:
- Backend: FastAPI 0.111+, Pydantic v2 (`ConfigDict(from_attributes=True)`), SQLAlchemy 2.0 (async), `redis-py` 5.0.6, `python-jose` (HS256)
- Frontend: `@tanstack/react-query` 5.45, `axios` 1.7, `lucide-react` 0.395, Vitest 5.1 + `@testing-library/react` 16.3 + `@testing-library/jest-dom` 8.0 + `jsdom` 31.0

**Storage**: PostgreSQL 16 + PostGIS 3.4 (production/Docker) / SQLite `aiosqlite` (dev & pytest). Reuses existing tables from `8793a9fe3601_initial_schema_ecobite_12_tables.py` (`reviews`, `green_points_ledger`, `vouchers`, `user_vouchers`, `users`, `stores`, `orders`) — **no new Alembic migrations needed**.

**Testing**:
- Backend: `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"`), `httpx.AsyncClient` ASGI tests (`conftest.py`), multi-session `NullPool` SQLite concurrency test, `ruff` (lint + format), `mypy` (`pydantic.mypy`)
- Frontend: `vitest run` (`frontend/vitest.config.ts`, `jsdom`, `vitest.setup.ts`), `npm run lint` (`next lint`), `npm run type-check` (`tsc --noEmit`), `npm run build`

**Target Platform**: Containerized FastAPI ASGI backend + responsive Next.js 14 PWA (mobile Safari/Chrome & desktop browsers)

**Project Type**: Full-stack web feature (Backend REST API + Seed Data + Consumer PWA UI + Automated QA)

**EcoBite Baseline (inherited from `constitution.md`)**: Python 3.11 · FastAPI (fully async) · Pydantic v2 · SQLAlchemy 2.0 async (`aiosqlite` for dev/test, `asyncpg` for PostgreSQL 16) · Redis 7 optional lock · JWT HS256 (`python-jose`) · Next.js 14 App Router + TypeScript strict + Tailwind CSS + TanStack React Query · pytest + Vitest + ruff + mypy + ESLint gates

**Performance Goals**: Instant interactive UI state refresh after redemption/review via targeted React Query invalidation; non-blocking async SQL aggregations; concurrent redemption stress test (10+ parallel requests) completing cleanly with zero deadlocks and zero negative balances.

**Constraints**: Zero negative Green Points balances; zero duplicate reviews per order; zero client-side-only security enforcement; zero blocking I/O in async routes; zero secrets committed; zero Git merge conflicts across parallel Week 6 frontend lanes.

**Scale/Scope**: 6 REST endpoints (2 Reviews + 4 Gamification/Vouchers), 1 new Next.js route (`/green-points`), 1 reusable client modal (`ReviewModal.tsx`), 2 frontend service modules, 1 existing route integration (`/orders`), 5 backend test suites + 2 frontend Vitest suites.

## Constitution Check

*GATE: Checked against `.specify/memory/constitution.md` (v1.2.0) and `AGENTS.md` (all 8 Principles & 8 Guardrails).*

- [x] **Principle I (Test-First Development)**: Backend unit & integration tests (`test_review_repo.py`, `test_review_service.py`, `test_api_reviews.py`, `test_gamification_service.py`, `test_api_gamification.py`) are implemented; remaining concurrency integration test (`EC4-15`) and frontend Vitest component tests (`EC4-14`: `ReviewModal.test.tsx`, `GreenPointsPage.test.tsx`) are scheduled FIRST (Red-Green-Refactor) inside their respective User Story phases in `tasks.md`.
- [x] **Principle II (Security, Privacy & Access Control)**: All write and personal endpoints enforce `Depends(require_roles(UserRole.CONSUMER))` with server-verified JWT HS256; `ReviewService` additionally enforces `order.consumer_id == consumer.id`; frontend `<AuthGuard allowedRoles={['CONSUMER']}>` complements (never replaces) server-side authorization; zero secrets in code or `.env` commits.
- [x] **Principle III (Data Integrity & Transactional Consistency)**: `GamificationRepository.atomic_deduct_points` executes conditional SQL `UPDATE users SET green_points_balance = green_points_balance - :cost WHERE id = :uid AND green_points_balance >= :cost RETURNING green_points_balance` inside a single DB transaction together with ledger & `UserVoucher` creation, backed by optional `distributed_lock(f"lock:green_points:user:{user_id}")` and full rollback on failure. `ReviewService.create_review` commits review creation + `Store.rating_avg`/`rating_count` update in one transaction with DB `UNIQUE(order_id)` `IntegrityError` recovery.
- [x] **Principle IV (Food Safety & Allergen Protection)**: Not directly mutating dish allergens; verified reviews increase community transparency around real food freshness and packaging quality without introducing mystery-bag opacity.
- [x] **Principle V (Deterministic Business Rules & Payment Integrity)**: Eco Rank (`RANK_THRESHOLDS` + `CO2_KG_TO_SCORE_FACTOR = 20`), CO₂/meal totals (`SUM` over `COMPLETED` orders), store rating averages, and review eligibility (strictly `OrderStatus.COMPLETED` after verified QR pickup) are 100% deterministic backend rules.
- [x] **Principle VI (AI Reliability, Structured Output & Model Isolation)**: No generative AI or ML models are used for reviews, rankings, CO₂ accounting, or voucher redemptions—preserving determinism and keeping ML dependencies isolated.
- [x] **Principle VII (Clean Architecture & Async End-to-End)**: Backend strictly separates `endpoints/{reviews,gamification}.py` → `services/{review,gamification}_service.py` → `repositories/{review,gamification}_repo.py` using SQLAlchemy 2.0 `Mapped[T]` and `AsyncSession` end-to-end with zero blocking I/O. Frontend uses Next.js 14 App Router, TypeScript strict DTOs, `@/lib/api-client`, TanStack React Query, and `'use client'` only on interactive views/modals.
- [x] **Principle VIII (Verifiable Quality & Human Accountability)**: Mandatory Verification Gate in `tasks.md` requires `ruff check`, `ruff format --check`, `mypy app/`, `pytest tests/ -v`, `npm run lint`, `npm run type-check`, `npm run test`, `npm run build`, and `pre-commit run --all-files` to exit `0` before commit/PR review.

## Project Structure

### Documentation (this feature)

```text
specs/005-reviews-gamification-vouchers/
├── spec.md              # Feature specification (/speckit-specify)
├── plan.md              # This file (/speckit-plan)
├── research.md          # Phase 0 design decisions (/speckit-plan)
├── data-model.md        # ORM models, Pydantic schemas, TS DTOs & seed fixtures
├── quickstart.md        # Runnable E2E & QA validation guide
├── checklists/
│   └── requirements.md  # Spec quality validation checklist
├── contracts/
│   └── api-contracts.md # REST contracts, error matrices & FE service mapping
└── tasks.md             # Dependency-ordered TDD tasks with [X] vs [ ] status
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   ├── interaction.py                       # [Implemented] Review ORM (UNIQUE order_id, CHECK rating 1..5)
│   │   ├── gamification.py                      # [Implemented] PointActionType, GreenPointsLedger, Voucher, UserVoucher
│   │   ├── user.py                              # [Implemented] User.green_points_balance
│   │   └── store.py                             # [Implemented] Store.rating_avg, rating_count, total_co2_saved_kg
│   ├── schemas/
│   │   ├── interaction.py                       # [Implemented] ReviewBase, ReviewCreate, ReviewResponse
│   │   └── gamification.py                      # [Implemented] GreenPointsSummaryResponse, VoucherResponse, UserVoucherResponse, VoucherRedeemResponse
│   ├── repositories/
│   │   ├── review_repo.py                       # [Implemented - EC4-07] ReviewRepository (CRUD + update_store_rating)
│   │   └── gamification_repo.py                 # [Implemented - EC4-08] GamificationRepository (atomic_deduct_points, stats, ledger, vouchers)
│   ├── services/
│   │   ├── order_service.py                     # [Implemented - EC4-06] QR completion awards points + ledger + store CO2
│   │   ├── review_service.py                    # [Implemented - EC4-07] ReviewService (RBAC, ownership, COMPLETED guard, IntegrityError 409)
│   │   └── gamification_service.py              # [Implemented - EC4-08] GamificationService (rank tiers, summary, atomic redeem + Redis lock)
│   ├── api/v1/
│   │   ├── router.py                            # [Implemented] Registers gamification.router (before stores) & reviews.router
│   │   └── endpoints/
│   │       ├── reviews.py                       # [Implemented - EC4-07] POST /orders/{order_id}/review, GET /stores/{store_id}/reviews
│   │       └── gamification.py                  # [Implemented - EC4-08] GET /green-points/me, /vouchers, /vouchers/me, POST /vouchers/{id}/redeem
│   └── db/
│       └── seed.py                              # [Implemented - EC4-09] 4 vouchers, completed orders, verified review, ledger, user_voucher
└── tests/
    ├── unit/
    │   ├── test_review_repo.py                  # [Implemented - EC4-07] ReviewRepository unit suite (5 tests)
    │   ├── test_review_service.py               # [Implemented - EC4-07] ReviewService unit suite (8 tests)
    │   └── test_gamification_service.py         # [Implemented - EC4-09] Gamification unit suite (13 test functions)
    └── integration/
        ├── test_api_reviews.py                  # [Implemented - EC4-07] Reviews API integration suite (7 tests)
        └── test_api_gamification.py             # [Implemented - EC4-09; Pending EC4-15 concurrent burst test] Gamification API + seed suite

frontend/
├── vitest.config.ts                             # [Implemented - EC4-10] Vitest + React plugin + jsdom + @/* alias
├── vitest.setup.ts                              # [Implemented - EC4-10] @testing-library/jest-dom
├── src/
│   ├── types/
│   │   └── api.ts                               # [Pending - EC4-13] Append Review & Gamification/Voucher TypeScript DTOs
│   ├── services/
│   │   ├── gamification.service.ts              # [Pending - EC4-13] getMyGreenPoints, listVouchers, getMyVouchers, redeemVoucher
│   │   └── review.service.ts                    # [Pending - EC4-13] createReview, getStoreReviews
│   ├── components/
│   │   ├── ui/Navbar.tsx                        # [Implemented] Already links CONSUMER role to /green-points & /orders
│   │   └── ReviewModal.tsx                      # [Pending - EC4-13] Interactive 1-5 star rating, comment/tags, 409 handling
│   └── app/
│       ├── green-points/
│       │   └── page.tsx                         # [Pending - EC4-13] Stats header + Redeem Voucher / My Vouchers / Ledger tabs
│       └── orders/
│           └── page.tsx                         # [Pending - EC4-13] Wire "Đánh giá" button + ReviewModal for COMPLETED orders
└── __tests__/
    └── components/
        ├── ReviewModal.test.tsx                 # [Pending - EC4-14] Star selector, submit, 409 duplicate handling
        └── GreenPointsPage.test.tsx             # [Pending - EC4-14] Stats header, insufficient points disable, redeem & cache invalidation, tabs
```

**Structure Decision**: Follows the verified EcoBite 3-tier backend layout (`backend/app/{models,schemas,repositories,services,api/v1/endpoints}` + `backend/tests/{unit,integration}`) and Next.js 14 App Router frontend layout (`frontend/src/{types,services,components,app}` + `frontend/__tests__/components`) per `AGENTS.md` Section 3 and the Week 6 Action Plan disjoint-ownership allocation.

## Complexity Tracking

No Constitution violations. All 8 Core Principles (Constitution v1.2.0) and all 8 Guardrails in `AGENTS.md` are satisfied without exceptions.
