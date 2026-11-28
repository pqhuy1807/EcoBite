# Implementation Plan: Full-Stack VNPay Checkout & Order Lifecycle (SCRUM-42)

**Branch**: `main` | **Jira Issue**: `SCRUM-42` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/002-vnpay-checkout-order-lifecycle/spec.md`

## Summary

Deliver the Sprint 4 (`PA4-E`) full-stack **`SCRUM-42`** functional group — **VNPay Sandbox Checkout & Payment-Aware Order Lifecycle** (`OrderModal` dual `COD`/`VNPAY` checkout, `HMAC-SHA512` VNPay URL generation, `/payment/vnpay-return` verification, idempotent IPN webhook with atomic failed-payment stock restoration, `/orders` retry & cancellation, `409` Payment-to-QR guard, dynamic `HMAC-SHA256` QR issuance, and `/store/verify-qr` counter verification & `COD -> PAID` completion) across **FastAPI**, **SQLAlchemy 2.0 Async**, **PostgreSQL 16**, **Redis 7**, and **Next.js 14 App Router**.

## Architecture Overview & Component Relationships

- **Layer flow**:
  - **Frontend (`Next.js 14`)**: `OrderModal.tsx` (`COD`/`VNPAY` checkout + redirect), `/payment/vnpay-return/page.tsx` (client return hash verification), `/orders/page.tsx` (order history, status filters, VNPay retry button, cancel order, dynamic `<QRCodeSVG />` modal), and `/store/verify-qr/page.tsx` (`html5-qrcode` camera + manual QR payload verification) → Axios client (`@/lib/api-client`, Bearer JWT + `401` refresh) + `payment.service.ts` + `order.service.ts`.
  - **Backend (`FastAPI`)**: `payments.py` (`/payments/vnpay/create-url`, `/payments/vnpay/ipn`, `/payments/vnpay/return`) and `orders.py` (`POST /orders`, `GET /orders/me`, `GET /orders/store/{id}`, `GET /orders/{id}`, `POST /orders/{id}/qr`, `POST /orders/verify-qr`, `PATCH /orders/{id}/cancel`) → Framework-free Services (`PaymentService`, `OrderService`, `QRService`) → Async SQLAlchemy 2.0 Repositories (`PaymentTransactionRepository`, `OrderRepository`, `QRTokenRepository`, `dish_repo`) → PostgreSQL 16 (`aiosqlite` in automated test suites) + Redis 7 distributed locks.
- **Cross-cutting concerns**:
  - **RBAC**: `require_roles(UserRole.CONSUMER | STORE_PARTNER | ADMIN)` and `StoreOwner` (`backend/app/api/deps.py`), plus `<AuthGuard>` (`frontend/src/components/auth/AuthGuard.tsx`).
  - **Configuration Hygiene**: `VNP_TMN_CODE`, `VNP_HASH_SECRET`, `VNP_URL`, `VNP_RETURN_URL`, `QR_SIGNATURE_SECRET`, and `SECRET_KEY` loaded strictly via `app.core.config.settings` (`pydantic-settings`).
  - **Concurrency & Idempotency**: Redis distributed locks `lock:payment:ipn:{txn_ref}`, `lock:order:redeem:{order_id}`, and `lock:dish:{dish_id}` paired with conditional SQL updates (`WHERE remaining_quantity >= :qty`, `WHERE is_used IS FALSE`, `WHERE status IN (...)`) and `is_verified` IPN deduplication.
- **External Integration (VNPay Sandbox v2.1.0)**:
  - Mitigates tampered `vnp_SecureHash` (`"97"` via `hmac.compare_digest`), duplicate IPN retries (`"02"`), amount tampering (`"04"`), missing `tzdata` on Windows (`Asia/Ho_Chi_Minh` fallback to UTC+7), and abandoned/failed payments (`_process_failed_payment` restoring `dishes.remaining_quantity` atomically).

## Technical Context

**Language/Version**: Python 3.11 (Backend target), TypeScript 5.4 (`strict: true`, Frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), Redis (`redis-py`), Pydantic v2 (`pydantic-settings`), Next.js `14.2.35`, React `18.3.1`, TanStack React Query `^5.45.1`, Axios `^1.7.2`, `qrcode.react` `^3.1.0`, `html5-qrcode` `^2.3.8`  
**Storage**: PostgreSQL 16 (production/Docker) / SQLite `aiosqlite` (automated unit & integration tests) + Redis 7  
**Testing**: `pytest` + `pytest-asyncio` + `ruff` + `mypy` (Backend); `vitest` `5.1.1` + `vite` `8.3.8` + `@testing-library/react` `16.3.3` + `jsdom` `31.0.1` + `next lint` + `tsc --noEmit` + `next build` (Frontend)  
**Target Platform**: Web browser + FastAPI ASGI server  
**Project Type**: Full-stack web application (`backend/` + `frontend/`), `SCRUM-42` functional group

## Constitution Check

*GATE: Evaluated against `.specify/memory/constitution.md` (`v1.2.0`) and `AGENTS.md`.*

- [x] **Principle I (Test-First)**: Unit, integration, and concurrency suites cover checkout/payments (`test_payment_service.py`: 18, `test_api_payments.py`: 8, `OrderModal.test.tsx`: 3, `payment.service.test.ts`: 2) and order/QR lifecycle (`test_order_service.py`, `test_api_orders.py`, `test_qr_service.py`, `test_order_concurrency.py`).
- [x] **Principle II (Security & RBAC)**: `require_roles` + ownership checks on all checkout, retry, cancel, QR issue, and QR verify endpoints; `VNP_HASH_SECRET` & `QR_SIGNATURE_SECRET` loaded from settings with zero secrets in VCS.
- [x] **Principle III (Transactional Consistency)**: Order creation, cancellation stock restoration, failed-IPN inventory rollback, and QR handover completion each execute atomically inside single DB transactions under Redis locks.
- [x] **Principle V (Deterministic Rules & Payment Integrity)**: `HMAC-SHA512` (`hmac.compare_digest` + `quote_plus`) for VNPay; `HMAC-SHA256` (`is_used` flag) for QR; unpaid `VNPAY` orders blocked from QR (`409 Conflict`); `COD` settles to `PAID` on verified QR handover.
- [x] **Principle VII (Clean Architecture)**: Strict `Router -> Service -> Repository` separation; interactive `'use client'` boundaries limited to client modal/page components.
- [x] **Principle VIII (Honest Verification)**: Frontend `vitest`/`lint`/`type-check`/`build` and `ruff` verified directly; local `backend/.venv` `mypy`/`pytest` clearly marked for execution in an activated Python environment containing `requirements.txt`.

## Project Structure

### Documentation (`SCRUM-42` Feature Package)

```text
specs/002-vnpay-checkout-order-lifecycle/
├── spec.md
├── plan.md
├── tasks.md
└── contracts/
    └── api-contracts.md
```

### Source Code Scope (`SCRUM-42` Only)

```text
backend/
├── app/
│   ├── core/config.py                         # VNP_TMN_CODE, VNP_HASH_SECRET, VNP_URL, VNP_RETURN_URL
│   ├── models/order.py                        # Order, QRToken, PaymentTransaction, PaymentMethod, PaymentStatus
│   ├── repositories/
│   │   ├── payment_repo.py                    # PaymentTransactionRepository (create_transaction, get_verified_by_txn_ref, list_by_order_id)
│   │   ├── order_repo.py                      # OrderRepository (cancel_if_allowed, complete_if_allowed, get_by_order_code)
│   │   └── qr_token_repo.py                   # QRTokenRepository (mark_token_as_used)
│   ├── schemas/
│   │   ├── payment.py                         # VNPayCreateUrlResponse, VNPayIPN*, VNPayReturnResponse
│   │   └── order.py                           # OrderCreate/Response/Detail, QRPayloadResponse, QRVerification*
│   ├── services/
│   │   ├── payment_service.py                 # VNPay v2.1.0 signing, return verification, IPN idempotency & stock rollback
│   │   ├── order_service.py                   # _validate_payment_ready_for_qr (409), cancel_order, verify_and_complete_order (COD->PAID)
│   │   └── qr_service.py                      # HMAC-SHA256 dynamic QR payload generation & hmac.compare_digest verification
│   └── api/v1/
│       ├── router.py                          # Registers payments.router (/payments) & orders.router (/orders)
│       └── endpoints/
│           ├── payments.py                    # POST /vnpay/create-url, GET /vnpay/ipn, GET /vnpay/return
│           └── orders.py                      # POST "", POST /verify-qr, GET /me, /store/{id}, /{id}, POST /{id}/qr, PATCH /{id}/cancel
└── tests/
    ├── unit/                                  # test_payment_service.py (18), test_order_service.py, test_qr_service.py
    └── integration/                           # test_api_payments.py (8), test_api_orders.py, test_order_concurrency.py (1)

frontend/
├── vitest.config.ts & package.json            # Vitest ("test": "vitest run") harness configuration
├── src/
│   ├── app/
│   │   ├── payment/vnpay-return/page.tsx      # VNPay return URL signature verification receipt page
│   │   ├── orders/page.tsx                    # Order history, status filters, VNPay retry, dynamic QR modal, cancel order
│   │   └── store/verify-qr/page.tsx           # Store Partner QR camera/manual scanner, anti-replay & handover summary
│   ├── components/
│   │   └── OrderModal.tsx                     # Dual COD/VNPAY checkout selector, stock 409 handling & VNPay redirect
│   ├── services/
│   │   ├── payment.service.ts                 # createVnpayUrl, verifyVnpayReturn
│   │   └── order.service.ts                   # createRescueOrder, cancelOrder, getMyOrders, getOrderDetail, issueOrderQr, verifyOrderQr
│   └── types/api.ts                           # OrderStatus, PaymentMethod, PaymentStatus, VNPay & QR DTOs
└── __tests__/
    ├── components/OrderModal.test.tsx         # 3 unit tests (COD flow, VNPAY redirect, 409 out-of-stock)
    └── services/payment.service.test.ts       # 2 unit tests (createVnpayUrl params, verifyVnpayReturn params)
```

**Structure Decision**: Scoped strictly to `SCRUM-42` (`VNPay Checkout`, `Order Lifecycle`, `Payment-to-QR Guard`, and `QR Verification`) inside the existing decoupled `backend/` + `frontend/` architecture. Files belonging to `SCRUM-41` (Menu/Surplus Dishes) or separate epics (`/admin`, `/green-points`, Verified Reviews, `/` Radar) remain independent.

## Complexity Tracking

No constitution violations. Every flow preserves the 3-tier backend boundary, constant-time cryptographic verification, and strict TypeScript typing.
