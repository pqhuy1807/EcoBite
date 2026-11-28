# Feature Specification: VNPay Cashless Checkout, Idempotent IPN & Payment-QR Reconciliation Guard

**Feature Branch**: `dev` (tracking `fix/vnpay-sandbox`, `feat/fe-vnpay-and-store-orders`, `test/pa4-qa-gate`)

**Created**: 2026-11-28

**Status**: In Progress (Core Backend Implemented; Sandbox Polish, Frontend Flow & QA Gate Remaining)

**Input**: User description: "EcoBite Feature 004 — VNPay Cashless Checkout, Idempotent IPN & Payment-QR Reconciliation Guard (Core F6 + Core F7 Payment Guard): end-to-end VNPay v2.1.0 cashless checkout initiation, HMAC-SHA512 server-to-server IPN webhook with Redis-locked idempotency and single atomic inventory rollback on failure, stateless return URL signature verification, strict Payment-to-QR reconciliation blocking unpaid VNPAY orders while auto-settling COD pickups with atomic Green Points and CO₂ crediting, consumer VNPay checkout/return/retry UI, store partner order queue alongside QR scanner, automated backend/frontend test suites, QR verification latency benchmark (< 2s), and real VNPay Sandbox E2E verification."

## Summary *(mandatory)*

Food-rescue consumers want a fast, cashless way to pay for end-of-shift surplus meals without risking double charges, ghost reservations that lock up scarce inventory, or fraudulent pickup attempts before payment clears. Store partners need certainty that any cashless order presented for pickup has already been settled, while cash-on-delivery (COD) orders are automatically marked paid and credited with environmental rewards at handoff.

This feature delivers **Core Feature 6 (VNPay Cashless Payment Gateway)** and the **Core Feature 7 Payment Reconciliation Extension** for **Consumers** and **Store Partners**. Consumers choosing cashless checkout are redirected to a cryptographically signed VNPay payment session and returned to a verified payment status screen. Behind the scenes, an idempotent server-to-server Instant Payment Notification (IPN) workflow authenticates every gateway callback, transitions settled orders to `PAID`, and atomically releases reserved dish inventory if a payment fails or is cancelled. Both pickup QR generation and in-store QR scanning enforce a strict reconciliation guard that blocks unpaid cashless orders, while COD handoffs automatically settle payment and credit Green Points and saved CO₂ in a single atomic transaction.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cashless VNPay Checkout Initiation & Secure Redirect (Priority: P1)

As an authenticated Consumer placing a surplus-meal rescue order with VNPay, I want the system to generate an authenticated, tamper-proof payment link for my eligible order and redirect me straight to the VNPay gateway so that I can complete cashless payment quickly and securely.

**Why this priority**: Initiating a valid, properly signed VNPay payment session is the entry point for all cashless orders; without compliant signing, ownership checks, and Vietnam timezone timestamps, consumers cannot pay through the gateway at all.

**Independent Test**: Can be fully tested by placing a `VNPAY` rescue order as a Consumer, requesting a payment URL for that order (with and without an optional bank code), verifying the returned URL targets the configured gateway host with all mandatory v2.1.0 parameters, Vietnam-local creation timestamp, exact minor-unit amount (`total_amount * 100`), and a valid HMAC-SHA512 signature, and verifying that non-owners, non-consumer roles, COD orders, already-paid orders, and cancelled/expired orders are cleanly rejected.

**Acceptance Scenarios**:

1. **Given** an authenticated Consumer owns an active `CONFIRMED` order with payment method `VNPAY` and payment status `PENDING` totaling `22,000 VND`, **When** the Consumer requests a VNPay checkout link, **Then** the system generates a signed payment URL pointing to the configured VNPay gateway endpoint with `vnp_TxnRef` matching the order code, `vnp_Amount` equal to `2200000`, `vnp_CreateDate` formatted in Vietnam local time (`UTC+7`), client IP recorded from the incoming request, and a canonical URL-encoded HMAC-SHA512 `vnp_SecureHash`.
2. **Given** an authenticated Consumer chooses `VNPAY` inside the discovery checkout dialog and confirms the order, **When** order creation succeeds, **Then** the interface immediately requests the signed payment link and redirects the browser to the VNPay gateway; if payment link generation fails, the interface surfaces a clear error notice and directs the Consumer to their orders list to retry payment without losing the order.
3. **Given** a Store Partner, Admin, anonymous visitor, or a different Consumer attempts to generate a VNPay payment link for someone else's order, **When** authorization runs, **Then** the system rejects the request immediately without disclosing order details or generating a payment link.
4. **Given** an order uses `COD`, is already `PAID` or `FAILED`, or has reached a terminal lifecycle state (`CANCELLED`, `EXPIRED`, `COMPLETED`), **When** the Consumer requests a VNPay payment link, **Then** the system rejects the request with a clear conflict or gone status explaining why the order is ineligible for checkout.

---

### User Story 2 - Idempotent Server-to-Server VNPay IPN Settlement & Atomic Stock Rollback (Priority: P1)

As a platform operator and Store Partner, I want every server-to-server VNPay payment notification to be cryptographically authenticated, validated against the order's authoritative amount, processed at most once even under duplicate or concurrent retries, and automatically return reserved meals to active inventory when payment fails so that financial records and dish stock always remain exact.

**Why this priority**: Payment webhooks are retryable public callbacks touching real money and scarce surplus inventory. Signature forgery, amount tampering, duplicate processing, or double stock restoration would directly cause financial loss or inventory corruption.

**Independent Test**: Can be fully tested by dispatching signed and tampered IPN callbacks (valid success `00`, invalid signature, mismatched amount, unknown order reference, duplicate sequential and concurrent success callbacks, and duplicate sequential/concurrent failed callbacks) and inspecting the gateway acknowledgment code (`RspCode`), persisted payment transaction audit log, order status, and dish remaining inventory.

**Acceptance Scenarios**:

1. **Given** a `PENDING` `VNPAY` order exists for `10,000 VND`, **When** VNPay sends a valid IPN callback with `vnp_ResponseCode = "00"`, matching `vnp_TxnRef`, matching `vnp_Amount = 1000000`, and a valid HMAC-SHA512 signature, **Then** the system marks the order `payment_status = PAID`, records gateway transaction number, bank code, payment timestamp, and a verified payment transaction audit record with the raw IPN payload, and replies `{"RspCode": "00", "Message": "Success"}`.
2. **Given** an incoming IPN callback has a missing or forged HMAC-SHA512 signature (even if all other fields look valid), **When** signature verification executes using constant-time comparison (excluding both `vnp_SecureHash` and `vnp_SecureHashType`), **Then** the system rejects the callback with `RspCode: "97"` and leaves the order and inventory untouched.
3. **Given** an incoming IPN callback carries a valid signature but a non-matching order reference or a tampered `vnp_Amount` that does not equal `order.total_amount * 100`, **When** validation executes, **Then** the system rejects the callback (`RspCode: "01"` for missing/unknown reference, `RspCode: "04"` for amount mismatch) without mutating database state.
4. **Given** a `VNPAY` order has already been settled (`PAID` with a verified payment transaction), **When** VNPay delivers a duplicate IPN sequentially or two workers receive the same IPN concurrently, **Then** distributed locking and database state checks ensure payment confirmation executes exactly once and duplicate callbacks return `RspCode: "02"` (or safe in-progress acknowledgment) with zero duplicate side effects.
5. **Given** a `PENDING` `VNPAY` order for `5` surplus meals receives a valid signed IPN with a failure or user-cancellation code (e.g., `vnp_ResponseCode = "24"` or `"05"`), **When** the failure handler runs, **Then** within a single database transaction the system logs the failed payment attempt, transitions the order to `payment_status = FAILED` and `status = CANCELLED`, and atomically restores `+5` meals to the dish's remaining inventory (reactivating `SOLD_OUT` dishes back to `ACTIVE`).
6. **Given** a failed `VNPAY` order has already been cancelled and its stock restored, **When** VNPay retries the failed IPN callback a second time (sequentially or concurrently), **Then** the system detects that the order is no longer `PENDING`/`CONFIRMED`, replies `RspCode: "02"`, and MUST NOT restore inventory a second time.

---

### User Story 3 - Payment ↔ Pickup QR Reconciliation Guard & Atomic COD Settlement (Priority: P1)

As a Store Partner handing over rescued meals and a Consumer collecting an order, I want pickup QR generation and in-store QR verification to strictly refuse unpaid VNPay orders while seamlessly allowing paid VNPay orders and COD orders—and automatically settling COD payment alongside Green Points and CO₂ rewards when the store scans the QR—so that unpaid online orders can never be picked up and every legitimate rescue immediately earns verified green impact.

**Why this priority**: Without a server-side reconciliation guard between payment status and pickup QR issuance/redemption, a Consumer could create a `VNPAY` order, skip payment, generate a QR code, and walk away with unpaid food. Equally, COD pickups must record settlement and environmental impact atomically so reviews and gamification ledgers stay consistent.

**Independent Test**: Can be fully tested by creating both `VNPAY` (`PENDING` and `PAID`) and `COD` (`PENDING`) orders, attempting QR issuance and QR redemption on each, confirming unpaid `VNPAY` is blocked with a conflict error in both steps without changing order status, confirming paid `VNPAY` and `COD` complete successfully, and confirming COD completion atomically transitions `payment_status` to `PAID`, credits consumer `green_points_balance`, inserts a single `ORDER_RESCUE` ledger entry, and increments store `total_co2_saved_kg`.

**Acceptance Scenarios**:

1. **Given** a Consumer owns a `CONFIRMED` order with `payment_method = VNPAY` and `payment_status = PENDING` (or `FAILED`), **When** the Consumer requests a pickup QR code, **Then** the system rejects the request with conflict status and message `"Đơn hàng VNPAY chưa hoàn tất thanh toán"` without issuing a QR token.
2. **Given** a QR token somehow exists for an unpaid `VNPAY` order, **When** a Store Partner scans and submits that QR token for pickup verification, **Then** the system rejects redemption with conflict status `"Đơn hàng VNPAY chưa hoàn tất thanh toán"`, keeps the order in its prior status, keeps the QR token unused, and awards zero points or CO₂.
3. **Given** a `VNPAY` order has been confirmed `PAID` by IPN, **When** the Consumer requests the pickup QR code and the owning Store Partner scans it, **Then** QR issuance succeeds and QR verification transitions the order to `COMPLETED`, marks the QR token single-use (`is_used = true`), and atomically credits Consumer Green Points, ledger record, and Store CO₂ saved.
4. **Given** a Consumer owns an active `COD` order with `payment_status = PENDING`, **When** the Consumer requests the pickup QR code and the owning Store Partner scans it at handoff, **Then** QR issuance is permitted prior to cash payment, and QR verification atomically marks the QR token used, transitions `status = COMPLETED`, updates `payment_status = PAID`, credits `User.green_points_balance`, inserts one `GreenPointsLedger` (`ORDER_RESCUE`) record, and accumulates `Store.total_co2_saved_kg`—rolling back all updates if any step fails.
5. **Given** a pickup QR code has already been redeemed once, **When** the Store Partner scans the same QR payload a second time, **Then** anti-replay protection rejects the scan and MUST NOT duplicate Green Points, ledger entries, or Store CO₂ totals.

---

### User Story 4 - Consumer Return Feedback, My Orders QR Guard & Store Partner Order Queue UI (Priority: P2)

As a Consumer returning from VNPay or managing my orders, and as a Store Partner operating the pickup counter, I want clear payment confirmation feedback, locked QR codes with one-click payment retry for pending VNPay orders, and a live store order list right beside the QR scanner so that both sides always see accurate real-time order and payment status.

**Why this priority**: Translates backend payment security and reconciliation guarantees into clear, trustworthy user workflows and eliminates counter confusion when customers arrive with pending vs paid orders.

**Independent Test**: Can be fully tested in browser and automated component tests by: (a) loading the VNPay return route with valid success parameters vs invalid/failed parameters and verifying stateless signature verification UI; (b) opening My Orders with mixed `VNPAY PENDING`, `VNPAY PAID`, and `COD PENDING` orders and verifying QR button gating and VNPay retry action; and (c) signing in as a Store Partner on the QR verification page and verifying the live store order queue refreshes automatically after scanning a QR code.

**Acceptance Scenarios**:

1. **Given** VNPay redirects a Consumer back to the return page with query parameters, **When** the return page loads, **Then** it verifies the return signature via the stateless backend verification endpoint (without altering database state directly) and displays either a clear payment-received summary (order code, amount, button to open My Orders and display the pickup QR) or a clear failure/tampered-signature notice explaining that failed payments automatically release reserved stock, with navigation back to My Orders or Radar.
2. **Given** a Consumer opens My Orders and has an active `VNPAY` order whose `payment_status` is `PENDING`, **When** the order card renders, **Then** the *"Xem mã QR"* button is locked/hidden, a *"Chờ thanh toán VNPay"* badge is shown, and a *"Thanh toán VNPay ngay"* action initiates a fresh VNPay redirect link; navigating with `?highlight=<orderId>` also respects this guard and does not auto-request a QR for unpaid `VNPAY` orders.
3. **Given** a Consumer opens My Orders and has an active `COD` order or a `PAID` `VNPAY` order, **When** the order card renders, **Then** the *"Xem mã QR"* button is active and opens the signed HMAC-SHA256 QR modal.
4. **Given** a Store Partner opens the QR verification portal, **When** the page loads, **Then** it displays the store's live order queue (filterable across `CONFIRMED`, `READY_FOR_PICKUP`, and `COMPLETED`, showing order code, dish, quantity, amount, payment method, and payment status) alongside the camera/manual QR scanner, and automatically refreshes the order list after a successful QR verification.

---

### User Story 5 - Concurrency QA Gate, QR `< 2s` Benchmark & Real VNPay Sandbox E2E (Priority: P2)

As a QA Lead and Backend Lead preparing Release 0.3 (PA4), I want automated integration and concurrency tests for the full payment and QR guard lifecycle, a latency benchmark proving pickup QR verification completes under 2 seconds, frontend component tests, and documented real VNPay Sandbox E2E evidence so that release readiness is objectively verified before code freeze.

**Why this priority**: Provides reproducible proof under EcoBite's four Quality Gates that payment idempotency, atomic rollback, and real external gateway interoperability work end-to-end—not just under unit mocks.

**Independent Test**: Can be independently executed by running the full backend integration payment suite, QR latency benchmark assertion, frontend Vitest component suite, and executing one successful payment plus one cancelled payment against the live VNPay Sandbox environment with captured verification evidence.

**Acceptance Scenarios**:

1. **Given** the automated payment integration suite runs against the FastAPI application, **When** it exercises create-URL RBAC/lifecycle errors, invalid IPN signature (`97`), wrong amount (`04`), concurrent duplicate IPNs, and concurrent failed IPNs, **Then** every assertion passes with zero duplicate transactions and exact single stock restoration.
2. **Given** a valid active order and signed QR payload exist, **When** the QR verification latency benchmark executes against the verification endpoint, **Then** verification succeeds with `COMPLETED` status in strictly under `2.0 seconds` (`< 2000 ms`).
3. **Given** the frontend component test suite runs via the configured test runner, **When** VNPay checkout redirect, return verification, and `/orders` QR guard tests execute, **Then** all tests pass cleanly alongside lint, strict TypeScript type-check, and production build checks.
4. **Given** live VNPay Sandbox credentials are configured in the local environment (never committed) and IPN callback routing is active, **When** a developer completes one real Sandbox test-card payment (`00`) and cancels one Sandbox payment (`24`), **Then** both redirect return verification and server-to-server IPN settlement/stock-rollback succeed end-to-end with captured logs/screenshots for release documentation.

---

### Edge Cases

- **Spaces and special characters in VNPay signed fields**: `vnp_OrderInfo` (`"Thanh toan don hang EB-..."`) and `vnp_ReturnUrl` (`"http://localhost:3000/orders/vnpay-return"`) contain spaces, colons, and slashes; HMAC-SHA512 hash construction MUST URL-encode values (`quote_plus`) per VNPay v2.1.0 specification so the signature matches VNPay Sandbox verbatim.
- **Host server running in UTC (Docker/CI) vs local Vietnam machine**: Creating `vnp_CreateDate` using the container's local timezone causes 7-hour drift and Sandbox rejection (`Expired` / invalid timestamp); timestamp formatting MUST explicitly anchor to `Asia/Ho_Chi_Minh` (`UTC+7`, with fixed `+07:00` fallback if OS `tzdata` is absent).
- **Reverse-proxied client IP addresses**: Requests routed through ngrok, Vercel, or reverse proxies carry `X-Forwarded-For` containing comma-separated IPs; client IP extraction MUST take the first valid client IP (trimmed) and fall back safely to the socket peer host or `"127.0.0.1"`.
- **Redis temporarily unavailable during IPN arrival**: If Redis is unreachable when `distributed_lock` attempts acquisition, the system MUST NOT crash with `500`; database state checks (`is_verified` and `Order.payment_status == PENDING`) MUST still act as the authoritative idempotency backstop, while an active lock held by another concurrent worker returns safely without racing into the critical section.
- **Multiple payment attempts on the same order**: If a consumer opens the VNPay checkout page twice or a failed audit row already exists for `txn_ref`, transaction lookup MUST NOT raise an unhandled `MultipleResultsFound` error.
- **Return URL reached before IPN arrives (eventual consistency)**: On localhost or slow networks, the Consumer's browser may hit `/orders/vnpay-return` milliseconds before or without VNPay's IPN reaching the backend; the return endpoint MUST remain strictly stateless (verify signature only, never trust browser query params to mark an order `PAID`), and the UI MUST clearly guide the user to refresh `/orders` once IPN confirmation settles.
- **Failed IPN arriving for an already-completed or already-cancelled order**: Must be ignored idempotently (`RspCode: "02"`) without mutating order status or incrementing dish stock.
- **Unconfigured `VNP_HASH_SECRET` or `VNP_TMN_CODE`**: System must fail safely with a controlled error rather than signing with an empty secret key or leaking environment values in logs or HTTP responses.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load all VNPay gateway configuration (`VNP_TMN_CODE`, `VNP_HASH_SECRET`, `VNP_URL`, `VNP_RETURN_URL`) exclusively from environment configuration and MUST NEVER hardcode credentials or commit live environment files.
- **FR-002**: System MUST allow only authenticated users with the `CONSUMER` role who own the target order to initiate a VNPay payment URL, and MUST reject orders that are not `VNPAY`, not `PENDING` payment, or in a terminal lifecycle state (`CANCELLED`, `EXPIRED`, `COMPLETED`).
- **FR-003**: System MUST construct VNPay v2.1.0 payment URLs using the configured `VNP_URL`, `vnp_TxnRef` equal to `order.order_code`, `vnp_Amount` equal to `int(order.total_amount * 100)`, `vnp_CreateDate` anchored to `Asia/Ho_Chi_Minh` (`UTC+7`), request-derived client IP, and an alphabetically sorted, URL-encoded (`quote_plus`) HMAC-SHA512 `vnp_SecureHash`.
- **FR-004**: System MUST expose a public server-to-server VNPay IPN endpoint that authenticates every callback via constant-time HMAC-SHA512 verification (excluding `vnp_SecureHash` and `vnp_SecureHashType`), returning `RspCode: "97"` on missing or invalid signatures without mutating data.
- **FR-005**: System MUST validate IPN payload integrity before processing—returning `RspCode: "01"` for missing or non-existent order references and `RspCode: "04"` when `vnp_Amount / 100` does not exactly match the authoritative `order.total_amount`.
- **FR-006**: System MUST enforce idempotent IPN processing using a per-transaction distributed lock keyed by `vnp_TxnRef` combined with database state verification (`PaymentTransaction.is_verified` and `Order.payment_status`), ensuring duplicate sequential or concurrent IPN deliveries never record duplicate payment effects and return `RspCode: "02"` once already finalized.
- **FR-007**: On a verified successful IPN (`vnp_ResponseCode == "00"`), the system MUST atomically update `Order.payment_status = PAID`, store `vnpay_transaction_no`, `vnpay_bank_code`, and `vnpay_pay_date`, and persist a verified `PaymentTransaction` audit record containing the raw IPN payload.
- **FR-008**: On a verified failed or cancelled IPN (`vnp_ResponseCode != "00"`), the system MUST guard against non-pending or already-cancelled orders, and for eligible pending orders MUST atomically persist an audit `PaymentTransaction`, restore `order.quantity` back to the dish via atomic database increment (reactivating `SOLD_OUT` dishes to `ACTIVE`), and transition the order to `payment_status = FAILED` and `status = CANCELLED` inside one transaction—rolling back completely if stock restoration fails.
- **FR-009**: System MUST expose a stateless VNPay return verification endpoint that checks the return URL's HMAC-SHA512 signature and returns verification status and `txn_ref` without performing any database mutations.
- **FR-010**: System MUST enforce a server-side Payment ↔ QR Reconciliation Guard on BOTH pickup QR issuance and in-store QR verification: any order with `payment_method == VNPAY` and `payment_status != PAID` MUST be rejected with HTTP `409 Conflict` (`"Đơn hàng VNPAY chưa hoàn tất thanh toán"`), while `PAID` `VNPAY` orders and `COD` orders remain eligible.
- **FR-011**: On successful in-store QR pickup verification, the system MUST atomically (within one database transaction under a per-order redemption lock): mark the QR token single-use (`is_used = true`), transition the order to `COMPLETED`, automatically update `payment_status = PAID` when `payment_method == COD`, credit `User.green_points_balance`, insert an `ORDER_RESCUE` record into `GreenPointsLedger`, and accumulate `Store.total_co2_saved_kg`.
- **FR-012**: Consumer web interface MUST allow choosing `VNPAY` or `COD` during order checkout, automatically redirect `VNPAY` orders to the signed VNPay gateway URL, render a `<Suspense>`-safe VNPay return confirmation page verifying the signature, and in My Orders lock the QR action while presenting a *"Thanh toán VNPay ngay"* retry action for `VNPAY` + `PENDING` orders.
- **FR-013**: Store Partner QR verification interface MUST display the partner's live store order list (with order status, payment method, and payment status) alongside the camera/manual QR scanner and refresh automatically upon completing a pickup scan.
- **FR-014**: System MUST provide automated unit tests, ASGI payment integration & concurrency tests, a `< 2s` QR verification latency benchmark, and frontend component tests verifying VNPay checkout, return feedback, and QR gating.

### Non-Functional Requirements *(mandatory — feature touches money and payment data)*

- **NFR-001 (Cryptographic & Payment Integrity)**: All VNPay signatures MUST use HMAC-SHA512 compared with constant-time `hmac.compare_digest`; all pickup QR tokens MUST retain HMAC-SHA256 signing with single-use anti-replay enforcement; browser return parameters MUST NEVER mutate order payment status.
- **NFR-002 (Financial Consistency & Zero Double-Restore)**: Under concurrent duplicate IPN callbacks (success or failure), order state transitions, payment audit logs, and atomic inventory increments MUST execute at most once (`0%` double-payment recording, `0%` double-stock restoration).
- **NFR-003 (Performance SLA)**: In-store pickup QR verification (`POST /api/v1/orders/verify-qr`, including payment guard check, HMAC verification, single-use update, COD settlement, and Green Points/CO₂ crediting) MUST complete in strictly under `2.0 seconds` (`< 2000 ms`).
- **NFR-004 (Secret Hygiene & Auditability)**: `VNP_HASH_SECRET`, `VNP_TMN_CODE`, and raw auth tokens MUST NEVER appear in application logs, API error responses, or git commits; structured logs MUST record sanitized `txn_ref`, `order_id`, and `RspCode` for payment triage.
- **NFR-005 (Async Non-Blocking Execution & Portability)**: All payment and order endpoints/services MUST execute asynchronously without blocking I/O and remain portable across PostgreSQL 16 (production/Docker) and SQLite `aiosqlite` (automated pytest suite).

### Key Entities *(feature involves persistent financial & order records)*

- **Order**: Existing rescue order record linking Consumer, Store, and Dish; carries `order_code` (used as `vnp_TxnRef`), `total_amount`, `status` (`CONFIRMED`, `READY_FOR_PICKUP`, `COMPLETED`, `CANCELLED`, `EXPIRED`), `payment_method` (`VNPAY` | `COD`), `payment_status` (`PENDING` | `PAID` | `FAILED`), VNPay settlement metadata (`vnpay_transaction_no`, `vnpay_bank_code`, `vnpay_pay_date`), and environmental impact (`co2_saved_kg`, `green_points_earned`).
- **PaymentTransaction**: Immutable audit record for every VNPay IPN callback processed against an Order, capturing `txn_ref`, `amount`, `vnp_transaction_no`, `vnp_bank_code`, `vnp_response_code`, `is_verified`, and `raw_ipn_payload`.
- **QRToken**: Single-use HMAC-SHA256 pickup credential bound 1-to-1 to an Order (`nonce`, `token_hash`, `expires_at`, `is_used`, `used_at`); gated by the Payment ↔ QR Reconciliation Guard for `VNPAY` orders.
- **Dish**: Surplus meal listing whose `remaining_quantity` and `status` (`ACTIVE` ↔ `SOLD_OUT`) are atomically incremented inside the failed-IPN rollback transaction.
- **User & GreenPointsLedger & Store**: Updated atomically upon QR pickup completion to credit `User.green_points_balance`, append an `ORDER_RESCUE` ledger entry, and accumulate `Store.total_co2_saved_kg`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Cryptographic & Sandbox Interoperability)**: 100% of generated VNPay URLs pass signature validation on the live VNPay Sandbox gateway (including `vnp_OrderInfo` spaces and return URLs), and 100% of tampered or missing-hash IPN callbacks are rejected with `RspCode: "97"` and zero database mutations.
- **SC-002 (Idempotency & Zero Double Stock Restoration)**: 100% of sequential and concurrent duplicate IPN deliveries (both success `00` and failure non-`00`) result in at most one order state transition and at most one atomic inventory increment (`0%` duplicate payment settlements and `0%` over-restored dish counts).
- **SC-003 (Zero Unpaid Cashless Pickups)**: 100% of QR issuance and QR redemption attempts on `VNPAY` orders with `payment_status != PAID` are blocked with `409 Conflict` across both backend APIs and the consumer UI.
- **SC-004 (Atomic COD Settlement & Green Impact)**: 100% of verified `COD` pickups transition simultaneously to `status = COMPLETED` and `payment_status = PAID` while crediting exact Green Points, a single `GreenPointsLedger` record, and Store CO₂ saved, with 100% rollback on mid-transaction failure.
- **SC-005 (Pickup Verification Latency)**: Automated benchmark verifies end-to-end pickup QR verification completes in `< 2.0 seconds` (`< 2000 ms`).
- **SC-006 (Full Quality Gate Pass)**: 100% of backend checks (`ruff check`, `ruff format --check`, `mypy`, `pytest tests/ -v`), frontend checks (`npm run lint`, `npm run type-check`, `npm run test`, `npm run build`), repository `pre-commit` hooks, and live VNPay Sandbox E2E walkthrough pass cleanly before PA4 release tagging (`v0.3.0-pa4`).

## Assumptions

- **Existing Schema & Migrations**: The `orders` (including VNPay reconciliation columns), `payment_transactions`, `qr_tokens`, `dishes`, `users`, `stores`, and `green_points_ledger` tables are already defined in `backend/app/models/` and provisioned by the initial Alembic migration; no new database migrations are required for this feature.
- **Order-to-Transaction Reference Mapping**: Each rescue order maps `vnp_TxnRef` directly to its unique `order.order_code` (`EB-YYYYMMDD-XXXXXXXX`). If a Consumer retries payment on a `PENDING` order before any failure IPN cancels it, the same `order_code` is reused cleanly; once a failed IPN cancels the order and restores stock, the Consumer places a new order.
- **IPN vs Return Authority**: In local development without a public tunnel, developers validate return URL signatures via `GET /api/v1/payments/vnpay/return` and simulate IPN via local curl/Swagger or expose the local backend through `ngrok`/staging for live VNPay Sandbox E2E (`EC4-16`). Production and staging always rely exclusively on server-to-server IPN for `PAID`/`FAILED` transitions.
- **Scope Boundary with Feature 8 UI**: While this specification owns the atomic Green Points/CO₂ crediting during QR verification (`EC4-06`) and the Store Orders table at `/store/verify-qr` (`EC4-13` store portion), the Consumer Green Points wallet page (`/green-points`) and Verified Reviews modal (`ReviewModal.tsx`) are tracked separately under Core Feature 8 (`EC4-13` consumer portion).
