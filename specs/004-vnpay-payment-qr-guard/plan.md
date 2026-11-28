# Implementation Plan: VNPay Cashless Checkout, Idempotent IPN & Payment-QR Reconciliation Guard

**Branch**: `dev` (`fix/vnpay-sandbox`, `feat/fe-vnpay-and-store-orders`, `test/pa4-qa-gate`) | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-vnpay-payment-qr-guard/spec.md`

## Summary

Deliver and harden the end-to-end **VNPay Cashless Checkout (`Core F6`)** and **Payment ↔ QR Reconciliation Guard (`Core F7 Extension`)** for EcoBite Release 0.3 (`v0.3.0-pa4`). The backend core (`VNP_*` config, `PaymentTransactionRepository`, `PaymentService`, `payments.py` endpoints, `OrderService` Payment↔QR Guard + atomic COD settlement/Green Points/CO₂ crediting, and unit tests) is already implemented and passing 52 unit tests. Remaining work closes four VNPay Sandbox compatibility polish items (`quote_plus` HMAC hashing, `settings.VNP_URL`, `Asia/Ho_Chi_Minh` timezone, `require_roles(UserRole.CONSUMER)` + `Request` client IP extraction), implements the Consumer VNPay checkout redirect, `<Suspense>`-wrapped `/orders/vnpay-return` page, `/orders` QR Guard + retry payment UI, and `/store/verify-qr` live Store Orders table, cleans up `frontend/package.json`, adds Frontend Vitest component tests (`EC4-14`), adds Backend ASGI payment integration/concurrency tests + `< 2s` QR benchmark (`EC4-15`), and verifies live VNPay Sandbox E2E (`EC4-16`).

## Architecture Overview & Component Relationships

- **Backend 3-Tier Flow (`Router -> Service -> Repository`)**:
  - **Payment Initiation**: Consumer Web UI (`OrderModal` / `/orders`) → `POST /api/v1/payments/vnpay/create-url` (`backend/app/api/v1/endpoints/payments.py`: `require_roles(UserRole.CONSUMER)`, `Request` client IP extraction) → `PaymentService.create_vnpay_payment_url` (`backend/app/services/payment_service.py`) → `OrderRepository.get_by_id` → signed VNPay v2.1.0 URL targeting `settings.VNP_URL`.
  - **Server-to-Server IPN Settlement**: VNPay Gateway → `GET /api/v1/payments/vnpay/ipn` (public, authenticated via HMAC-SHA512) → `PaymentService.process_vnpay_ipn` → constant-time `hmac.compare_digest` → `OrderRepository.get_by_order_code` → amount validation → Redis `distributed_lock(f"lock:payment:ipn:{txn_ref}", timeout_seconds=30)` (`backend/app/core/redis.py`) → `PaymentTransactionRepository` (`backend/app/repositories/payment_repo.py`) + either `Order.payment_status = PAID` or single-transaction rollback via `dish_repo.atomic_increment_quantity(..., commit=False)` + `Order.payment_status = FAILED`, `Order.status = CANCELLED`.
  - **Stateless Return Verification**: Consumer Browser → `/orders/vnpay-return` → `GET /api/v1/payments/vnpay/return` → `PaymentService.verify_vnpay_return` (`@staticmethod`, zero DB access).
  - **Payment ↔ QR Reconciliation & COD Settlement**:
    - Consumer → `POST /api/v1/orders/{order_id}/qr` → `OrderService.issue_or_get_qr_payload` → `_validate_payment_ready_for_qr(order)` (`409` if `VNPAY` & `!= PAID`) → `QRService` (`HMAC-SHA256`).
    - Store Partner → `POST /api/v1/orders/verify-qr` → `OrderService.verify_and_complete_order` → `QRService.verify_qr_token` → store ownership check → `_validate_payment_ready_for_qr(order)` → `distributed_lock(f"lock:order:redeem:{order_id}", timeout_seconds=5)` → single DB transaction updating `QRToken.is_used`, `Order.status = COMPLETED`, `COD -> Order.payment_status = PAID`, `User.green_points_balance`, `GreenPointsLedger` (`GamificationRepository`), and `Store.total_co2_saved_kg` (`store_repo`).
- **Frontend Next.js 14 App Router Flow**:
  - `frontend/src/services/payment.service.ts` (`createVnpayUrl`, `verifyVnpayReturn`) & `frontend/src/services/order.service.ts` (`createRescueOrder`, `getMyOrders`, `getStoreOrders`, `issueOrderQr`, `verifyOrderQr`) via shared Axios `@/lib/api-client`.
  - `frontend/src/components/OrderModal.tsx` + `frontend/src/app/page.tsx`: `COD` vs `VNPAY` selector, order creation → VNPay redirect with error fallback.
  - `frontend/src/app/orders/vnpay-return/page.tsx`: `<Suspense>` boundary around `useSearchParams()` calling `paymentService.verifyVnpayReturn`.
  - `frontend/src/app/orders/page.tsx`: locks QR button & renders *"Thanh toán VNPay ngay"* for `VNPAY` + `PENDING`; unlocks QR for `PAID` `VNPAY` and `COD`.
  - `frontend/src/app/store/verify-qr/page.tsx`: fetches `storeService.getMyStore()` → `orderService.getStoreOrders(store.id)` and displays live Store Orders queue beside the `html5-qrcode` scanner.
- **External Integrations & Failure Modes**:
  - **VNPay Gateway v2.1.0 (`sandbox.vnpayment.vn` / production)**: failure modes include mismatched URL-encoding in HMAC-SHA512 (`Invalid Signature`), UTC vs `UTC+7` `vnp_CreateDate` drift, duplicate IPN retries, out-of-order return redirect before IPN, user cancellation (`vnp_ResponseCode=24`), and card failure (`05`/`51`). Handled via `quote_plus` canonical signing, `Asia/Ho_Chi_Minh` timestamps, Redis+DB idempotency, stateless return verification, and atomic stock rollback.
  - **Redis 7 (`app/core/redis.py`)**: failure mode is unreachable Redis (`RedisError`); handled via graceful degradation in `distributed_lock` while DB state guards (`is_verified`, `Order.payment_status`, conditional SQL updates) preserve transactional correctness.

## Technical Context

**Language/Version**: Backend Python 3.11 (`backend/venv_backend` / `backend/.venv`, target `py311`); Frontend TypeScript 5.4 (`strict: true`) + Node.js `>= 18.17.0`

**Primary Dependencies**:
- Backend: FastAPI 0.111+, Pydantic v2 (`pydantic-settings`), SQLAlchemy 2.0 (async), `redis-py` 5.0.6 (`redis.asyncio`), `tzdata` (`zoneinfo.ZoneInfo`), Python stdlib `hmac`/`hashlib`/`urllib.parse`
- Frontend: Next.js 14.2 (App Router), React 18.3, TanStack React Query 5, Axios 1.7, `qrcode.react`, `html5-qrcode`, Tailwind CSS 3.4

**Storage**: PostgreSQL 16 + PostGIS 3.4 (production/Docker via `asyncpg`) / SQLite `aiosqlite` (local dev & pytest); uses existing tables (`orders`, `payment_transactions`, `qr_tokens`, `dishes`, `users`, `stores`, `green_points_ledger`) — **no new Alembic migrations required**

**Testing**:
- Backend: `pytest` 8.2 + `pytest-asyncio` (`asyncio_mode = "auto"`), `httpx.AsyncClient` ASGI integration tests, `ruff` (`check` + `format --check`), `mypy` (`pydantic.mypy`)
- Frontend: `vitest` 5.1 + `@testing-library/react` 16.3 + `@testing-library/jest-dom` 8.0 + `jsdom`, ESLint (`next lint`), `tsc --noEmit`, `next build`

**Target Platform**: FastAPI ASGI backend + Next.js 14 PWA frontend (Docker Compose / Linux / macOS / Windows local dev) integrated with VNPay Sandbox v2.1.0

**Project Type**: Full-stack web feature (Backend Payment & Order Services + Frontend Checkout/Orders/Store Portal + Integration & Component Tests)

**EcoBite Baseline (inherited from `constitution.md`)**: Python 3.11 · FastAPI (fully async) · Pydantic v2 · SQLAlchemy 2.0 async · PostgreSQL 16 + PostGIS · Redis 7 · Next.js 14 App Router + TypeScript strict · JWT HS256 · pytest + ruff + mypy + Vitest + ESLint + tsc gates

**Performance Goals**: Pickup QR verification (`POST /api/v1/orders/verify-qr`) strictly `< 2.0s` (`< 2000 ms`, NFR-003, SC-005); stateless return verification `< 100 ms`

**Constraints**: Zero secrets in logs or git; HMAC-SHA512 (`quote_plus`, `compare_digest`) for VNPay; HMAC-SHA256 single-use anti-replay for QR; zero double payment confirmation or double stock restoration under concurrent IPN retries; zero unpaid `VNPAY` QR bypasses

**Scale/Scope**: 3 VNPay endpoints (`create-url`, `ipn`, `return`), 2 guarded QR endpoints (`POST /orders/{id}/qr`, `POST /orders/verify-qr`), 1 store orders listing endpoint (`GET /orders/store/{store_id}`), 4 frontend pages/modals, plus full backend/frontend QA suites & live Sandbox E2E

## Constitution Check

*GATE: Checked pre-design (Phase 0) and re-verified post-design (Phase 1) against `.specify/memory/constitution.md` (v1.2.0) and `AGENTS.md`.*

- [x] **Principle I (Test-First Development)**: Unit tests (`test_payment_service.py`, `test_order_service.py`) are verified green; every remaining implementation task (Sandbox polish, `test_api_payments.py`, QR `< 2s` benchmark, Frontend Vitest component tests) writes/updates failing tests FIRST before production code edits (Red-Green-Refactor).
- [x] **Principle II (Security, Privacy & Access Control)**: `VNP_*` secrets loaded exclusively via `pydantic-settings` (`config.py`), never logged or committed; `POST /payments/vnpay/create-url` upgraded to `Depends(require_roles(UserRole.CONSUMER))` + ownership validation; `POST /orders/verify-qr` enforces `STORE_PARTNER` + owning store check; IPN public webhook authenticated strictly by HMAC-SHA512 `hmac.compare_digest`.
- [x] **Principle III (Data Integrity & Transactional Consistency)**: IPN uses Redis `distributed_lock` + DB idempotency (`is_verified` & `Order.payment_status`) so Redis outage degrades safely; failed payment uses atomic `dish_repo.atomic_increment_quantity(..., commit=False)` in one DB transaction with order cancellation; QR verification updates `QRToken`, `Order` (`COMPLETED` + `COD -> PAID`), `User.green_points_balance`, `GreenPointsLedger`, and `Store.total_co2_saved_kg` atomically in one transaction with full rollback on error.
- [x] **Principle IV (Food Safety & Allergen Protection)**: No food-safety or allergen metadata is hidden or altered by payment checkout or pickup reconciliation; surplus dish transparency remains intact.
- [x] **Principle V (Deterministic Business Rules & Payment Integrity)**: Payment amounts derive strictly from authoritative `order.total_amount` (never client-supplied amounts); VNPay IPN verifies HMAC-SHA512 before mutating status; QR tokens retain HMAC-SHA256 + expiration + `is_used`; Payment↔QR Guard prevents unpaid `VNPAY` pickup; COD settlement happens deterministically on verified QR handoff.
- [x] **Principle VI (AI Reliability, Structured Output & Model Isolation)**: Feature is 100% deterministic financial/order logic — introduces zero AI non-determinism or ML dependencies.
- [x] **Principle VII (Clean Architecture & Async End-to-End)**: Strict `Router -> Service -> Repository` boundaries (`payments.py -> PaymentService -> PaymentTransactionRepository/OrderRepository/dish_repo`; `orders.py -> OrderService -> OrderRepository/QRTokenRepository/GamificationRepository/store_repo`), fully async SQLAlchemy 2.0 + `redis.asyncio`, Next.js 14 App Router with `'use client'` only on interactive pages/components and API calls routed through `@/lib/api-client`.
- [x] **Principle VIII (Verifiable Quality & Human Accountability)**: Mandatory Final Verification Gate requires Backend (`ruff check`, `ruff format --check`, `mypy app/`, `pytest tests/ -v`), Frontend (`npm run lint`, `npm run type-check`, `npm run test`, `npm run build`), `pre-commit run --all-files`, and live VNPay Sandbox E2E evidence before commit/release tagging.

## Project Structure

### Documentation (this feature)

```text
specs/004-vnpay-payment-qr-guard/
├── spec.md                  # Feature specification
├── plan.md                  # This file
├── research.md              # Design decisions & Sandbox compatibility analysis
├── data-model.md            # Entities, state machines, schemas & lock keys
├── quickstart.md            # End-to-end local + VNPay Sandbox validation guide
├── checklists/
│   └── requirements.md      # Spec quality checklist
├── contracts/
│   └── api-contracts.md     # REST contracts, VNPay RspCode & error matrices
└── tasks.md                 # Dependency-ordered TDD tasks with [X]/[ ] status
```

### Source Code (repository root)

```text
backend/
├── .env.example                                     # [X] VNP_TMN_CODE, VNP_HASH_SECRET, VNP_URL, VNP_RETURN_URL
├── app/
│   ├── core/
│   │   ├── config.py                                # [X] pydantic-settings VNP_* fields
│   │   └── redis.py                                 # [X] distributed_lock (SET NX EX + Lua release)
│   ├── models/
│   │   └── order.py                                 # [X] Order (VNPay fields), QRToken, PaymentTransaction
│   ├── schemas/
│   │   ├── payment.py                               # [X] VNPayCreateUrlResponse, VNPayIPNResponse, VNPayReturnResponse
│   │   └── order.py                                 # [X] OrderResponse, QRPayloadResponse, QRVerificationResponse
│   ├── repositories/
│   │   ├── payment_repo.py                          # [X] PaymentTransactionRepository (polish multi-row lookup)
│   │   ├── order_repo.py                            # [X] get_by_order_code, list_by_store, complete_if_allowed
│   │   └── dish_repo.py                             # [X] atomic_increment_quantity (stock restore)
│   ├── services/
│   │   ├── payment_service.py                       # [X] Core F6 / [ ] 4 Sandbox polish items (EC4-03)
│   │   └── order_service.py                         # [X] Payment↔QR Guard + COD auto-paid + Points/CO2 (EC4-06)
│   └── api/
│       └── v1/
│           ├── router.py                            # [X] payments.router (/payments) & orders.router (/orders)
│           └── endpoints/
│               ├── payments.py                      # [X] Core endpoints / [ ] require_roles + Request IP (EC4-03)
│               └── orders.py                        # [X] POST /{id}/qr, POST /verify-qr, GET /store/{store_id}
└── tests/
    ├── unit/
    │   ├── test_payment_service.py                  # [X] 13 passing tests / [ ] Sandbox polish cases (EC4-04)
    │   └── test_order_service.py                    # [X] 39 passing tests incl. Guard + COD + Points/CO2 (EC4-06)
    └── integration/
        └── test_api_payments.py                     # [ ] ASGI IPN concurrency, rollback, Guard & QR <2s benchmark (EC4-15)

frontend/
├── package.json                                     # [ ] Remove duplicate "test" script key (EC4-10 cleanup)
├── vitest.config.ts                                 # [X] Vitest + jsdom + @/* alias configured
├── src/
│   ├── types/
│   │   └── api.ts                                   # [X] PaymentMethod, PaymentStatus, VNPay DTOs
│   ├── services/
│   │   ├── payment.service.ts                       # [X] createVnpayUrl, verifyVnpayReturn
│   │   └── order.service.ts                         # [X] Core order calls / [ ] add getStoreOrders (EC4-13)
│   ├── components/
│   │   ├── OrderModal.tsx                           # [ ] COD/VNPAY selector + VNPay redirect trigger (EC4-12)
│   │   └── ui/Navbar.tsx                            # [X] Role-based navigation links
│   └── app/
│       ├── page.tsx                                 # [ ] Wire OrderModal VNPay checkout & error fallback (EC4-12)
│       ├── orders/
│       │   ├── page.tsx                             # [ ] Lock QR & show "Thanh toán VNPay ngay" for VNPAY PENDING (EC4-12)
│       │   └── vnpay-return/
│       │       └── page.tsx                         # [ ] New <Suspense>-wrapped VNPay return verification page (EC4-12)
│       └── store/
│           └── verify-qr/
│               └── page.tsx                         # [ ] Add live Store Orders table beside QR scanner (EC4-13)
└── __tests__/
    └── components/
        ├── VnpayCheckout.test.tsx                   # [ ] Vitest tests for VNPay checkout redirect & fallback (EC4-14)
        ├── OrdersQrGuard.test.tsx                   # [ ] Vitest tests for /orders QR guard & retry button (EC4-14)
        └── VnpayReturnPage.test.tsx                 # [ ] Vitest tests for /orders/vnpay-return signature UI (EC4-14)
```

**Structure Decision**: Extends the verified EcoBite 3-tier backend (`backend/app/{core,models,schemas,repositories,services,api/v1/endpoints}` + `backend/tests/{unit,integration}`) and Next.js 14 App Router frontend (`frontend/src/{types,services,components,app}` + `frontend/__tests__/components`) with clean 1-to-1 file ownership across **Đặng Trọng Phúc** (Backend VNPay & Sandbox), **Đàng Thế Tony** (Backend Order Guard & PA4 QA Gate), and **Võ Ngọc Thịnh** (Frontend VNPay, Store Orders & Vitest Part 1).

## Complexity Tracking

No Constitution violations. All 8 Core Principles and all 8 Guardrails in `AGENTS.md` are satisfied without exceptions.
