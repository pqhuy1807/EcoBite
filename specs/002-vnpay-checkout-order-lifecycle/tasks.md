# Tasks: Full-Stack VNPay Checkout & Order Lifecycle (SCRUM-42)

**Input**: Design documents from `/specs/002-vnpay-checkout-order-lifecycle/`  
**Jira Issue**: `SCRUM-42` — *Spec Kit, Full-Stack VNPay Checkout, Order Lifecycle and Demo Video*  
**Prerequisites**: `spec.md`, `plan.md`, `contracts/api-contracts.md`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable task (independent files)
- **[Story]**: User Story (`[US1]` Checkout & Redirect, `[US2]` VNPay Return/IPN/Rollback, `[US3]` Order Lifecycle & Retry/Cancel, `[US4]` Payment↔QR Guard & Verification)

---

## Phase 1: VNPay Configuration, Data Models & API Wiring

**Purpose**: Ensure VNPay configuration, persistence repositories/schemas, router mounting, and realistic sample VNPay/Order seed fixtures are ready.

- [X] T001 Configure `VNP_TMN_CODE`, `VNP_HASH_SECRET`, `VNP_URL`, and `VNP_RETURN_URL` in `backend/app/core/config.py` and `backend/.env.example`
- [X] T002 [P] Implement `PaymentTransactionRepository` (`create_transaction`, `get_verified_by_txn_ref`, `list_by_order_id`) in `backend/app/repositories/payment_repo.py` and VNPay schemas (`VNPayCreateUrlResponse`, `VNPayIPNResponse`, `VNPayReturnResponse`) in `backend/app/schemas/payment.py`
- [X] T003 [P] Register `payments.router` (`/payments`) alongside `orders.router` (`/orders`) in `backend/app/api/v1/router.py` and confirm `Order` / `PaymentTransaction` / `QRToken` models & schemas in `backend/app/models/order.py` & `backend/app/schemas/order.py`
- [X] T004 [P] Seed realistic sample `Order` (`CONFIRMED` & `COMPLETED` VNPay records), `QRToken`, and `PaymentTransaction` entries in `backend/app/db/seed.py`

---

## Phase 2: User Story 1 - Dual-Method Order Checkout (`COD` / `VNPAY`) & Redirect (Priority: P1) 🎯 SCRUM-42

**Goal**: Enable consumers to select `COD` or `VNPAY` in `OrderModal`, decrement inventory atomically, create a signed VNPay Sandbox URL, and redirect cleanly.

### Tests for User Story 1

- [X] T005 [P] [US1] Write 3 component tests (`COD` order creation, `VNPAY` payment URL redirect, `409` out-of-stock screen) in `frontend/__tests__/components/OrderModal.test.tsx` and 2 service tests (`createVnpayUrl`, `verifyVnpayReturn`) in `frontend/__tests__/services/payment.service.test.ts`

### Implementation for User Story 1

- [X] T006 [US1] Implement `PaymentService.create_vnpay_payment_url` (ownership, `VNPAY` + `PENDING` checks, `UTC+7` `vnp_CreateDate`, `quote_plus` + `HMAC-SHA512`) in `backend/app/services/payment_service.py` and expose `POST /api/v1/payments/vnpay/create-url` in `backend/app/api/v1/endpoints/payments.py`
- [X] T007 [US1] Create `frontend/src/services/payment.service.ts`, add VNPay/Order DTOs in `frontend/src/types/api.ts`, and update `frontend/src/components/OrderModal.tsx` with dual `COD`/`VNPAY` selector, VNPay redirect, and transient `vnpay_warning` fallback

---

## Phase 3: User Story 2 - VNPay Return Verification, Idempotent IPN & Failed-Payment Rollback (Priority: P1) 🎯 SCRUM-42

**Goal**: Verify client return redirects at `/payment/vnpay-return` and process `GET /api/v1/payments/vnpay/ipn` idempotently under Redis lock with atomic stock restoration on failure.

### Tests for User Story 2

- [X] T008 [P] [US2] Write 18 unit tests (HMAC signing, `UTC+7`, invalid hash `"97"`, amount mismatch `"04"`, duplicate/lock `"02"`/`"00"`, failed-payment stock rollback) in `backend/tests/unit/test_payment_service.py` and 8 API integration tests (`create-url` RBAC/401/403/404/`X-Forwarded-For` & `vnpay/return`) in `backend/tests/integration/test_api_payments.py`

### Implementation for User Story 2

- [X] T009 [US2] Implement `process_vnpay_ipn`, `_process_successful_payment`, `_process_failed_payment` (`dish_repo.atomic_increment_quantity`), `verify_vnpay_return`, and `_verify_vnpay_ipn_signature` (`hmac.compare_digest`) in `backend/app/services/payment_service.py` and expose `GET /payments/vnpay/ipn` + `GET /payments/vnpay/return` in `backend/app/api/v1/endpoints/payments.py`
- [X] T010 [P] [US2] Build `/payment/vnpay-return` verification receipt page (`useSearchParams`, `verifyVnpayReturn`, `txn_ref`, VND amount, bank code, response code, `/orders` link) in `frontend/src/app/payment/vnpay-return/page.tsx`

---

## Phase 4: User Story 3 - Payment-Aware Order Lifecycle (`/orders` History, Retry & Cancel) (Priority: P1) 🎯 SCRUM-42

**Goal**: Allow consumers to browse orders by status, retry pending VNPay payments, and cancel eligible orders atomically before `pickup_deadline`.

### Tests for User Story 3

- [X] T011 [P] [US3] Maintain unit and integration test coverage for atomic order creation, `get_my_orders`, `get_store_orders`, `get_order_detail` QR visibility, `cancel_order` stock restoration, and 50-buyer concurrency in `backend/tests/unit/test_order_service.py`, `backend/tests/integration/test_api_orders.py`, and `backend/tests/integration/test_order_concurrency.py`

### Implementation for User Story 3

- [X] T012 [US3] Align `frontend/src/services/order.service.ts` and implement status tabs (`ALL`, `CONFIRMED`, `READY_FOR_PICKUP`, `COMPLETED`, `CANCELLED`), **"Thanh toán VNPay"** retry button (`VNPAY` + `PENDING`), and **"Hủy đơn"** (`PATCH /orders/{id}/cancel` with cache invalidation) in `frontend/src/app/orders/page.tsx`

---

## Phase 5: User Story 4 - Payment-to-QR Guard, Dynamic QR Modal & Store Verification (`/store/verify-qr`) (Priority: P1) 🎯 SCRUM-42

**Goal**: Prevent unpaid `VNPAY` orders from issuing or redeeming pickup QRs, issue dynamic `HMAC-SHA256` QR codes, settle `COD` to `PAID` on verification, and reject QR replays.

### Tests for User Story 4

- [X] T013 [P] [US4] Add unit and integration tests for Payment-to-QR `409` guard, `COD -> PAID` settlement, atomic handover transaction rollback, concurrent QR double-redeem, and anti-replay in `backend/tests/unit/test_order_service.py`, `backend/tests/unit/test_qr_service.py`, and `backend/tests/integration/test_api_orders.py`

### Implementation for User Story 4

- [X] T014 [US4] Enforce `_validate_payment_ready_for_qr` (`409`), `issue_or_get_qr_payload`, and `verify_and_complete_order` (`mark_token_as_used`, `complete_if_allowed`, `COD -> PAID` transition) in `backend/app/services/order_service.py` and `backend/app/services/qr_service.py`
- [X] T015 [P] [US4] Wire **"Xem mã QR"** `<QRCodeSVG />` modal + one-click copy (`ecobite://pickup?...`) in `frontend/src/app/orders/page.tsx` and `/store/verify-qr` (`html5-qrcode` camera toggle + manual payload paste + anti-replay error card) in `frontend/src/app/store/verify-qr/page.tsx`

---

## Final Phase: Quality Gates & SCRUM-42 Demo Video (Constitution Principle VIII)

**Purpose**: Verify code quality and deliver the narrated 3–4 minute `SCRUM-42` demo walkthrough.

### Frontend Gates (`frontend/`) — Executed on `main` (`2026-11-28`, no TS/TSX edits since)

- [X] T016 `npm test` (`vitest run`) — **PASS (`exit 0`)**: workspace suite passed (`6` files / `17` tests), including `SCRUM-42` suites `__tests__/components/OrderModal.test.tsx` (`3` tests) and `__tests__/services/payment.service.test.ts` (`2` tests)
- [X] T017 `npm run lint` (`next lint`) — **PASS (`exit 0`)**: `0` ESLint warnings or errors
- [X] T018 `npm run type-check` (`tsc --noEmit`) — **PASS (`exit 0`)**: `0` TypeScript errors
- [X] T019 `npm run build` (`next build`) — **PASS (`exit 0`)**: `14/14` production routes compiled cleanly (including `/orders`, `/payment/vnpay-return`, `/store/verify-qr`)

### Backend Gates (`backend/`) — Observed Checks & Local `.venv` Checklist

- [X] T020 `ruff check app/` — **PASS (`exit 0`)**: `All checks passed!` across `75` source files
- [X] T021 `ruff format --check app/` — **PASS (`exit 0`)**: `75 files already formatted`
- [X] T022 `mypy app/` — **PASS (`exit 0`)**: `Success: no issues found in 75 source files` via `E:\anaconda\envs\ecobite\Scripts\mypy.exe` (Python 3.11 `ecobite` env)
- [X] T023 `pytest tests/ -v` — **PASS (`exit 0`)**: `348 passed, 1 warning in 282.34s (0:04:42)` via `E:\anaconda\envs\ecobite\Scripts\pytest.exe` (includes all `SCRUM-42` VNPay, Order Lifecycle, QR, and Concurrency suites)

### Demo Video (`SCRUM-42`)

- [ ] T024 Record & upload the 3–4 minute narrated English demo video (`docs/PA4_Section_E_and_Demo_Script.md` §E.5) demonstrating Spec Kit `002`, `OrderModal` VNPay Sandbox checkout, `/payment/vnpay-return`, `/orders` lifecycle (QR guard `409`, QR issue, VNPay retry, cancel stock restore), `/store/verify-qr` anti-replay, and passing test gates.
