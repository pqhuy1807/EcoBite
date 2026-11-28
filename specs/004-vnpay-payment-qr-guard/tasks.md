---
description: "Dependency-ordered TDD task list for Feature 004 — VNPay Cashless Checkout, Idempotent IPN & Payment-QR Reconciliation Guard"
---

# Tasks: VNPay Cashless Checkout, Idempotent IPN & Payment-QR Reconciliation Guard

**Input**: Design documents from `/specs/004-vnpay-payment-qr-guard/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/api-contracts.md`, `quickstart.md`

**Tests**: Test tasks are **MANDATORY** and placed **FIRST** inside every User Story phase per EcoBite Constitution Principle I (Test-First Development — Red-Green-Refactor). Every `[X]` checkbox below has been audited directly against actual repository files and passing test runs as of `2026-11-28`; every `[ ]` checkbox represents verified remaining work.

**Organization**: Grouped by User Story (`US1`–`US5`) with explicit Jira IDs (`EC4-01`, `EC4-03`, `EC4-04`, `EC4-06`, `EC4-10`, `EC4-12`, `EC4-13`, `EC4-14`, `EC4-15`, `EC4-16`) and 1-1 Assignees (**Đặng Trọng Phúc**, **Đàng Thế Tony**, **Võ Ngọc Thịnh**).

## Format: `[ID] [P?] [Story] (Jira | Assignee) Description`

- **[P]**: Can run in parallel (disjoint files, no dependency on incomplete tasks)
- **[Story]**: User story label (`[US1]`–`[US5]`) — omitted in Setup, Foundational, and Final Verification Gate phases
- Exact repository-relative file paths included in every task

---

## Phase 1: Setup & Shared Configuration

**Purpose**: Ensure VNPay environment settings, frontend DTOs/services, and Vitest test harness are cleanly configured without secrets or JSON script defects.

- [X] T001 (`EC4-01` | Đặng Trọng Phúc) Add `VNP_TMN_CODE`, `VNP_HASH_SECRET`, `VNP_URL`, and `VNP_RETURN_URL` settings via `pydantic-settings` in `backend/app/core/config.py` and document template keys (no secrets) in `backend/.env.example`
- [X] T002 [P] (`EC4-10` | Võ Ngọc Thịnh) Install Vitest + `@testing-library/react` + `@testing-library/jest-dom` + `jsdom`, create `frontend/vitest.config.ts`, align `PaymentMethod`/`PaymentStatus`/VNPay DTOs in `frontend/src/types/api.ts`, and create `paymentService` (`createVnpayUrl`, `verifyVnpayReturn`) in `frontend/src/services/payment.service.ts`
- [ ] T003 [P] (`EC4-10` cleanup | Võ Ngọc Thịnh) Remove duplicate `"test": "vitest run"` script key at line 12 of `frontend/package.json`, keeping `"test": "vitest run --passWithNoTests"` cleanly

**Checkpoint**: Backend VNPay settings and Frontend Vitest + payment service foundation are clean and verified.

---

## Phase 2: Foundational (Data Access & Schemas)

**Purpose**: Payment transaction repository and Pydantic v2 payment schemas shared across US1, US2, and US5.

- [X] T004 (`EC4-01` | Đặng Trọng Phúc) Implement `PaymentTransactionRepository` (`create_transaction`, `get_verified_by_txn_ref`, `list_by_order_id`, `verify_transaction`, `get_by_txn_ref`) in `backend/app/repositories/payment_repo.py` and Pydantic schemas (`VNPayCreateUrlRequest`, `VNPayCreateUrlResponse`, `VNPayIPNRequest`, `VNPayIPNResponse`, `VNPayReturnResponse`) in `backend/app/schemas/payment.py`
- [ ] T005 (`EC4-03` hardening | Đặng Trọng Phúc) Harden `PaymentTransactionRepository.get_by_txn_ref` and `get_verified_by_txn_ref` in `backend/app/repositories/payment_repo.py` with `.order_by(PaymentTransaction.created_at.desc(), PaymentTransaction.id.desc()).limit(1)` (and optional `is_verified: bool = False` keyword param on `create_transaction`) so multi-attempt orders never trigger `MultipleResultsFound`

**Checkpoint**: Payment persistence layer is safe against multi-attempt queries.

---

## Phase 3: User Story 1 - Cashless VNPay Checkout Initiation & Secure Redirect (Priority: P1) 🎯 MVP

**Goal**: Authenticated `CONSUMER` order owners generate Sandbox-compliant VNPay v2.1.0 URLs (`quote_plus` HMAC-SHA512, `settings.VNP_URL`, `Asia/Ho_Chi_Minh` timestamp, real client IP) and redirect seamlessly from the Radar checkout modal.

**Independent Test**: Run `pytest tests/unit/test_payment_service.py -k create_url -v` and place a `VNPAY` order in the UI to verify redirect URL construction, ownership/role enforcement (`403`), and lifecycle guards (`404`/`409`/`410`).

### Tests for User Story 1 (MANDATORY — Write FIRST & Verify FAIL before new code) ⚠️

- [X] T006 [P] [US1] (`EC4-04` | Đặng Trọng Phúc) Write baseline unit tests for HMAC-SHA512 generation, `create_vnpay_payment_url` success, and wrong-owner `403` rejection in `backend/tests/unit/test_payment_service.py`
- [ ] T007 [P] [US1] (`EC4-04` Sandbox polish | Đặng Trọng Phúc) Add unit tests in `backend/tests/unit/test_payment_service.py` verifying `urllib.parse.quote_plus` encoding inside `_generate_vnpay_hash` (spaces in `vnp_OrderInfo` and URL punctuation in `vnp_ReturnUrl`), `settings.VNP_URL` target host usage, `Asia/Ho_Chi_Minh` (`UTC+7`) `vnp_CreateDate` formatting, and eligibility rejections (`404` missing order, `409` `COD` or non-`PENDING`, `410` `CANCELLED`/`EXPIRED`/`COMPLETED`)

### Implementation for User Story 1

- [X] T008 [US1] (`EC4-03` | Đặng Trọng Phúc) Implement `PaymentService.create_vnpay_payment_url` and `_generate_vnpay_hash` in `backend/app/services/payment_service.py` and expose `POST /api/v1/payments/vnpay/create-url` in `backend/app/api/v1/endpoints/payments.py` (mounted under `/payments` in `backend/app/api/v1/router.py`)
- [ ] T009 [US1] (`EC4-03` Sandbox polish — 4 items | Đặng Trọng Phúc) Complete the 4 remaining VNPay Sandbox polish items in `backend/app/services/payment_service.py` and `backend/app/api/v1/endpoints/payments.py`: (1) URL-encode values with `urllib.parse.quote_plus(str(value))` inside `_generate_vnpay_hash()` and omit empty query params from the redirect URL, (2) use `settings.VNP_URL` (with Sandbox fallback only when blank) instead of hardcoded `_VNPAY_BASE_URL`, (3) compute `vnp_CreateDate` using `ZoneInfo("Asia/Ho_Chi_Minh")` with `timezone(timedelta(hours=7))` fallback, and (4) enforce `Depends(require_roles(UserRole.CONSUMER))` + extract real `client_ip` from FastAPI `Request` (`X-Forwarded-For` / `request.client.host`)
- [ ] T010 [US1] (`EC4-12` | Võ Ngọc Thịnh) Add `COD` vs `VNPAY` payment method selection and VNPay redirect flow (`POST /orders` → `paymentService.createVnpayUrl(order.id)` → `window.location.href = payment_url` with loading indicator & error fallback directing to `/orders`) in `frontend/src/components/OrderModal.tsx` and `frontend/src/app/page.tsx`

**Checkpoint**: Consumer VNPay checkout produces live Sandbox-compliant signed URLs and redirects smoothly.

---

## Phase 4: User Story 2 - Idempotent Server-to-Server VNPay IPN Settlement & Atomic Stock Rollback (Priority: P1) 🎯 MVP

**Goal**: Authenticate every VNPay IPN callback via constant-time HMAC-SHA512, prevent duplicate settlement under retries/concurrency via Redis lock + DB guard, mark paid orders `PAID`, and atomically restore dish inventory exactly once when payment fails or is cancelled.

**Independent Test**: Run `pytest tests/unit/test_payment_service.py -k "ipn or signature or return" -v` verifying `97`/`01`/`04`/`02`/`00` responses, zero double stock restore on repeated failed IPNs, and stateless return signature verification.

### Tests for User Story 2 (MANDATORY — Write FIRST & Verify FAIL before new code) ⚠️

- [X] T011 [P] [US2] (`EC4-04` | Đặng Trọng Phúc) Write baseline unit tests covering IPN HMAC-SHA512 verification (`vnp_SecureHashType` exclusion, invalid/missing hash `97`), missing `vnp_TxnRef` (`01`), amount mismatch (`04`), already-paid & duplicate-verified idempotency (`02`), Redis `distributed_lock` acquired/not-acquired paths, and failed-payment atomic stock rollback in `backend/tests/unit/test_payment_service.py`
- [ ] T012 [P] [US2] (`EC4-04` Sandbox polish | Đặng Trọng Phúc) Add unit tests in `backend/tests/unit/test_payment_service.py` proving repeated failed IPN returns `RspCode: "02"` with `dish_repo.atomic_increment_quantity` called zero additional times, unknown `vnp_TxnRef` returns standard `RspCode: "01"`, and `PaymentService.verify_vnpay_return` verifies valid/invalid/missing-ref payloads statelessly

### Implementation for User Story 2

- [X] T013 [US2] (`EC4-03` | Đặng Trọng Phúc) Implement `PaymentService.process_vnpay_ipn`, `_process_successful_payment` (`is_verified=True`, `Order.payment_status = PAID`, VNPay metadata), `_process_failed_payment` (`PENDING`/`CONFIRMED` guard + `dish_repo.atomic_increment_quantity(..., commit=False)` + `FAILED`/`CANCELLED`), `_verify_vnpay_ipn_signature` (`hmac.compare_digest`, strips `vnp_SecureHashType`), stateless `@staticmethod verify_vnpay_return` in `backend/app/services/payment_service.py`, and expose `GET /api/v1/payments/vnpay/ipn` & `GET /api/v1/payments/vnpay/return` in `backend/app/api/v1/endpoints/payments.py`
- [ ] T014 [US2] (`EC4-03` Sandbox polish | Đặng Trọng Phúc) Align non-existent order IPN response to `RspCode: "01"` (`Order not found`), switch duplicate-verified lookup to `get_verified_by_txn_ref` with up-front `order.payment_status != PaymentStatus.PENDING` check returning `RspCode: "02"`, and use case-insensitive `hmac.compare_digest` in `backend/app/services/payment_service.py`

**Checkpoint**: Server-to-server IPN settlement and atomic stock rollback are hardened and spec-aligned.

---

## Phase 5: User Story 3 - Payment ↔ Pickup QR Reconciliation Guard & Atomic COD Settlement (Priority: P1)

**Goal**: Strictly block unpaid `VNPAY` orders from QR issuance and redemption (`409 Conflict`), while allowing `PAID` `VNPAY` and `COD` orders and atomically settling `COD -> PAID` alongside Consumer Green Points, `GreenPointsLedger`, and Store CO₂ saved.

**Independent Test**: Run `pytest tests/unit/test_order_service.py -k "vnpay or cod or green_points or co2" -v` — all 9 reconciliation & atomic settlement tests pass.

### Tests for User Story 3 (MANDATORY — Verified Green)

- [X] T015 [US3] (`EC4-06` | Đàng Thế Tony) Write unit tests in `backend/tests/unit/test_order_service.py` verifying unpaid `VNPAY` blocked (`409`) on `issue_or_get_qr_payload` and `verify_and_complete_order`, `PAID` `VNPAY` & `COD` allowed, `COD` auto-setting `payment_status = PAID`, atomic `User.green_points_balance` + `GreenPointsLedger` (`ORDER_RESCUE`) + `Store.total_co2_saved_kg`, anti-replay non-duplication, and full rollback on failure

### Implementation for User Story 3

- [X] T016 [US3] (`EC4-06` | Đàng Thế Tony) Implement `OrderService._validate_payment_ready_for_qr` (`409 Conflict`) in both `issue_or_get_qr_payload` and `verify_and_complete_order`, plus atomic `COD -> PAID` transition, `GamificationRepository` Green Points/Ledger crediting, and `store_repo` CO₂ accumulation inside `distributed_lock(f"lock:order:redeem:{order_id}")` in `backend/app/services/order_service.py`

**Checkpoint**: User Story 3 backend logic and unit tests are 100% implemented and verified green.

---

## Phase 6: User Story 4 - Consumer Return Feedback, My Orders QR Guard & Store Partner Order Queue UI (Priority: P2)

**Goal**: Deliver verified VNPay return UI (`<Suspense>`), lock QR + provide VNPay retry button on `/orders`, add live Store Orders table beside the QR scanner on `/store/verify-qr`, and verify all new UI flows with Vitest component tests.

**Independent Test**: Run `cd frontend && npm run test && npm run build` and exercise `/orders/vnpay-return`, `/orders` (mixed `VNPAY PENDING` / `VNPAY PAID` / `COD`), and `/store/verify-qr` live.

### Tests for User Story 4 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T017 [P] [US4] (`EC4-14` | Võ Ngọc Thịnh) Write Vitest + Testing Library component tests verifying `COD` vs `VNPAY` checkout submission, `paymentService.createVnpayUrl` redirect trigger, and error fallback notice in `frontend/__tests__/components/VnpayCheckout.test.tsx`
- [ ] T018 [P] [US4] (`EC4-14` | Võ Ngọc Thịnh) Write Vitest + Testing Library component tests verifying `/orders` locks *"Xem mã QR"* & renders *"Thanh toán VNPay ngay"* for `VNPAY` + `PENDING` orders while enabling *"Xem mã QR"* for `VNPAY` + `PAID` and `COD` orders in `frontend/__tests__/components/OrdersQrGuard.test.tsx`
- [ ] T019 [P] [US4] (`EC4-14` | Võ Ngọc Thịnh) Write Vitest + Testing Library component tests verifying `/orders/vnpay-return` calls `paymentService.verifyVnpayReturn` and renders verified success vs tampered/failed-with-stock-restore UI in `frontend/__tests__/components/VnpayReturnPage.test.tsx`

### Implementation for User Story 4

- [ ] T020 [P] [US4] (`EC4-12` | Võ Ngọc Thịnh) Create `<Suspense>`-wrapped VNPay return verification page reading `useSearchParams()`, calling `paymentService.verifyVnpayReturn(queryParams)`, and rendering clear success (txn_ref, amount, link to `/orders`) or failure/stock-restored states in `frontend/src/app/orders/vnpay-return/page.tsx`
- [ ] T021 [US4] (`EC4-12` | Võ Ngọc Thịnh) Update `frontend/src/app/orders/page.tsx` to lock/hide *"Xem mã QR"* (and skip `?highlight=` auto-open) for active `VNPAY` + `PENDING` orders, display *"Chờ thanh toán VNPay"* badge and *"Thanh toán VNPay ngay"* retry redirect button, and keep QR modal openable for `PAID` `VNPAY` and `COD` orders
- [ ] T022 [US4] (`EC4-13` Store portion | Võ Ngọc Thịnh) Add `getStoreOrders(storeId, status?)` (`GET /orders/store/${storeId}`) in `frontend/src/services/order.service.ts` and render a live Store Orders queue table (`CONFIRMED`, `READY_FOR_PICKUP`, `COMPLETED` filters + payment method/status badges + React Query invalidation after QR verification) alongside the scanner in `frontend/src/app/store/verify-qr/page.tsx`
- [X] T023 [P] [US4] (`EC4-13` Navigation | Võ Ngọc Thịnh) Implement role-aware top navigation links (`/`, `/orders`, `/green-points` for `CONSUMER`; `/store/menu`, `/store/dishes`, `/store/verify-qr`, `/store/onboard` for `STORE_PARTNER`; `/admin` for `ADMIN`) in `frontend/src/components/ui/Navbar.tsx`

**Checkpoint**: Consumer VNPay checkout/return/QR-guard UI and Store Partner order queue UI pass Vitest and production build checks.

---

## Phase 7: User Story 5 - Concurrency QA Gate, QR `< 2s` Benchmark & Real VNPay Sandbox E2E (Priority: P2)

**Goal**: Prove concurrent IPN idempotency, single atomic stock restoration, Payment↔QR Guard API enforcement, `< 2s` QR verification latency SLA, and live VNPay Sandbox interoperability before PA4 release freeze.

**Independent Test**: Run `pytest tests/integration/test_api_payments.py -v` and complete the two live VNPay Sandbox test flows (`00` success & `24` cancel) per `specs/004-vnpay-payment-qr-guard/quickstart.md`.

- [ ] T024 [US5] (`EC4-15` | Đàng Thế Tony) Create `backend/tests/integration/test_api_payments.py` covering: `POST /payments/vnpay/create-url` (`200`, `401`, `403`, `404`, `409`, `410`), `GET /payments/vnpay/ipn` (valid `00`, invalid hash `97`, wrong amount `04`, unknown ref `01`, sequential & concurrent duplicate IPNs via `asyncio.gather` + isolated sessions, failed IPN restoring dish stock atomically **exactly once** even under concurrent retries), stateless `GET /payments/vnpay/return`, and E2E Payment↔QR Guard (`409` unpaid `VNPAY` → IPN `00` → `200` QR issue & verify → `COMPLETED` + Green Points/CO₂)
- [ ] T025 [P] [US5] (`EC4-15` | Đàng Thế Tony) Add automated QR verification latency benchmark asserting `POST /api/v1/orders/verify-qr` finishes strictly under `2.0 seconds` (`< 2000 ms`) in `backend/tests/integration/test_api_payments.py`
- [ ] T026 [US5] (`EC4-16` | Đặng Trọng Phúc) Execute live E2E verification against real **VNPay Sandbox** (`sandbox.vnpayment.vn` with staging/ngrok IPN callback) covering 1 successful NCB test-card transaction (`vnp_ResponseCode=00`) and 1 cancelled transaction (`vnp_ResponseCode=24`), confirming live signature acceptance, IPN settlement, and atomic stock rollback, and archive redacted evidence logs/screenshots for `docs/PA4.md`

**Checkpoint**: Backend concurrency QA, QR `< 2s` SLA, and real VNPay Sandbox E2E are objectively verified.

---

## Final Phase: Verification Gate (Constitution Principle VIII) — MANDATORY

**Purpose**: Reproducible proof that all Backend, Frontend, and Repository Quality Gates exit `0` before proposing commits or tagging `v0.3.0-pa4`.

### Backend (`backend/`, using `.venv` or `venv_backend`)

- [ ] T027 (`EC4-15` | Đàng Thế Tony) Run `ruff check app/ tests/` — zero lint findings
- [ ] T028 (`EC4-15` | Đàng Thế Tony) Run `ruff format --check app/ tests/` — formatting is canonical
- [ ] T029 (`EC4-15` | Đàng Thế Tony) Run `mypy app/` — static type-check passes with zero errors
- [ ] T030 (`EC4-15` | Đàng Thế Tony) Run `pytest tests/ -v` — 100% pass across all unit, integration (including `test_api_payments.py` & QR `< 2s` benchmark), and property tests

### Frontend (`frontend/`)

- [ ] T031 (`EC4-14` | Võ Ngọc Thịnh) Run `npm run lint` — zero ESLint warnings or errors
- [ ] T032 (`EC4-14` | Võ Ngọc Thịnh) Run `npm run type-check` — zero TypeScript strict errors (`tsc --noEmit`)
- [ ] T033 (`EC4-14` | Võ Ngọc Thịnh) Run `npm run test` — 100% pass across all Vitest component tests (`VnpayCheckout`, `OrdersQrGuard`, `VnpayReturnPage`)
- [ ] T034 (`EC4-14` | Võ Ngọc Thịnh) Run `npm run build` — clean Next.js 14 production build (verifying `<Suspense>` on `/orders/vnpay-return`)

### Repository Hooks (repo root)

- [ ] T035 (`EC4-15` | Đàng Thế Tony) Run `pre-commit run --all-files` — secrets check (zero `.env`/VNPay keys), `< 5 MB` file-size guard, and formatting hooks pass

---

## Dependencies & Parallel Execution Order

- **Track A — Backend VNPay Sandbox Polish & E2E (Đặng Trọng Phúc, branch `fix/vnpay-sandbox`)**:
  - `T005` → `T007` + `T012` (TDD Red) → `T009` + `T014` (Green) → `T026` (Live VNPay Sandbox E2E) → merge into `dev`.
- **Track B — Frontend VNPay Flow, Store Orders & Vitest Part 1 (Võ Ngọc Thịnh, branch `feat/fe-vnpay-and-store-orders`)**:
  - `T003` (fix `package.json`) → `T017` + `T018` + `T019` (TDD Red) → `T010` + `T020` + `T021` + `T022` (Green) → `T031`–`T034` (FE Gate) → merge into `dev`.
- **Track C — Backend Payment Integration, Concurrency & PA4 QA Gate (Đàng Thế Tony, branch `test/pa4-qa-gate`)**:
  - Starts after Track A merges `T009`+`T014` into `dev`: `T024` + `T025` → `T027`–`T030` + `T035` (Full PA4 QA Gate).
- **Zero-Conflict File Ownership**: Phúc owns `payment_repo.py`, `payment_service.py`, `endpoints/payments.py`, `test_payment_service.py`; Thịnh owns `frontend/package.json`, `OrderModal.tsx`, `page.tsx`, `orders/vnpay-return/page.tsx`, `orders/page.tsx`, `store/verify-qr/page.tsx`, `order.service.ts`, and `frontend/__tests__/components/`; Tony owns `order_service.py`, `test_order_service.py`, and `tests/integration/test_api_payments.py`.
