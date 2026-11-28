# Feature Specification: Full-Stack VNPay Checkout & Order Lifecycle (SCRUM-42)

**Feature Branch**: `main` (merged from `frontend` / `dev`)  
**Jira Issue**: `SCRUM-42` — *Spec Kit, Full-Stack VNPay Checkout, Order Lifecycle and Demo Video*  
**Created**: 2026-11-28  
**Status**: Implemented (PA4 — Sprint 4)  
**Input**: End-to-end Sprint 4 (PA4) functional group owned under `SCRUM-42`, extending `specs/001-rescue-discovery-order-qr/` with real **VNPay Sandbox Checkout**, **HMAC-SHA512 Return & IPN Verification (with failed-payment stock rollback)**, and the **Payment-Aware Order Lifecycle** (`/orders` history/retry/cancellation, Payment-to-QR `409` guard, dynamic single-use QR issuance, and `/store/verify-qr` counter settlement). *(Note: Complementary Sprint 4 group `SCRUM-41` and unrelated modules are specified separately outside `SCRUM-42`.)*

## Summary *(mandatory)*

Following PA3's discovery-to-QR baseline (`specs/001-rescue-discovery-order-qr/`), `SCRUM-42` delivers EcoBite's cashless VNPay payment flow and full payment-aware order lifecycle across **Next.js 14 App Router**, **FastAPI**, **PostgreSQL 16**, **Redis 7**, and **VNPay Sandbox v2.1.0**. Consumers (`CONSUMER`) choose between Cash on Delivery (`COD`) and `VNPAY` inside `OrderModal.tsx` (`POST /api/v1/orders`), automatically obtain a signed VNPay Sandbox URL (`POST /api/v1/payments/vnpay/create-url`), verify redirect parameters on `/payment/vnpay-return` (`GET /api/v1/payments/vnpay/return`), and rely on an idempotent server-to-server webhook (`GET /api/v1/payments/vnpay/ipn`) guarded by Redis distributed locks (`lock:payment:ipn:{txn_ref}`) and constant-time `HMAC-SHA512` comparison (`hmac.compare_digest`)—atomically restoring dish inventory on failed payments. On `/orders`, consumers track status tabs, retry payment on `PENDING` VNPay orders, cancel active orders before `pickup_deadline` with atomic stock restoration (`PATCH /api/v1/orders/{id}/cancel`), and render dynamic `HMAC-SHA256` pickup QR codes (`POST /api/v1/orders/{id}/qr`), while unpaid `VNPAY` orders are strictly blocked (`409 Conflict`) until settled, and `/store/verify-qr` (`POST /api/v1/orders/verify-qr`) finalizes handover, transitions `COD` orders to `PAID`, and enforces single-use anti-replay (`is_used = True`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dual-Method Order Checkout (`COD` / `VNPAY`) & VNPay Sandbox Redirect (Priority: P1)

As a **Consumer**, I want to choose **Cash on Delivery (`COD`)** or **VNPay Sandbox (`VNPAY`)** in `OrderModal` when reserving a surplus meal, have the system decrement remaining stock atomically first, and automatically redirect me to the signed VNPay Sandbox checkout URL when I select `VNPAY`.

**Why this priority**: Prevents overselling while smoothly routing cashless buyers into the external payment gateway, with clear fallback feedback if gateway URL creation fails transiently.

**Independent Test**: Render `OrderModal` with an active dish, place a `COD` order (`POST /api/v1/orders`) to verify immediate confirmation and stock callback (`onOrderSuccess`), place a `VNPAY` order to verify `POST /api/v1/payments/vnpay/create-url` invocation and redirect, and simulate `409 Conflict` out-of-stock handling (covered in `frontend/__tests__/components/OrderModal.test.tsx` and `frontend/__tests__/services/payment.service.test.ts`).

**Acceptance Scenarios**:

1. **Given** an authenticated `CONSUMER` opens `OrderModal` and chooses **`COD`**, **When** they click **"Xác nhận cứu món"**, **Then** `POST /api/v1/orders` atomically decrements `dishes.remaining_quantity`, creates an order with code `EB-YYYYMMDD-XXXXXXXX` (`status = CONFIRMED`, `payment_status = PENDING`), updates the dish stock UI via `onOrderSuccess`, and displays the confirmation summary linking to `/orders?highlight={id}`.
2. **Given** an authenticated `CONSUMER` opens `OrderModal` and chooses **`VNPAY`**, **When** they click **"Đặt & Thanh toán VNPay"**, **Then** `POST /api/v1/orders` creates the reservation and `OrderModal` automatically calls `POST /api/v1/payments/vnpay/create-url?order_id={id}` and redirects `window.location.href` to the signed `https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?...` URL (`vnp_Version=2.1.0`, `vnp_Amount = total_amount * 100`, `vnp_CreateDate` in `Asia/Ho_Chi_Minh` UTC+7, `vnp_TxnRef = order.order_code`, `vnp_SecureHash` HMAC-SHA512).
3. **Given** `POST /api/v1/orders` creates the `VNPAY` order (`201`) but `POST /api/v1/payments/vnpay/create-url` fails transiently, **When** the error is caught in `OrderModal`, **Then** the confirmation modal stays open with an amber warning banner displaying the created `order_code` and directing the user to retry payment on `/orders`.
4. **Given** another buyer already consumed the remaining portions (`remaining_quantity < quantity`), **When** `POST /api/v1/orders` fails with `409 Conflict`, **Then** `OrderModal` switches cleanly to the out-of-stock alert screen (*"Rất tiếc, món ăn vừa hết suất!"*).

---

### User Story 2 - VNPay Return Verification, Idempotent IPN & Failed-Payment Stock Rollback (Priority: P1)

As a **Consumer** and **Platform Operator**, I want VNPay browser redirects to `/payment/vnpay-return` verified cryptographically, and server-to-server IPN callbacks processed idempotently under a Redis lock so valid payments mark the order `PAID` once, tampered or mismatched callbacks are rejected, and failed/cancelled payments automatically restore dish inventory.

**Why this priority**: Guarantees financial integrity, replay safety, and zero stuck inventory if a buyer abandons or fails payment on VNPay Sandbox.

**Independent Test**: Call `GET /api/v1/payments/vnpay/return` with valid and invalid `vnp_SecureHash`; call `GET /api/v1/payments/vnpay/ipn` with missing `vnp_TxnRef` (`"01"`), tampered hash (`"97"`), mismatched amount (`"04"`), success `"00"` followed by duplicate `"00"` (`"02"`), and failure `"05"`/`"24"` verifying `Order.status == CANCELLED`, `Order.payment_status == FAILED`, and `dishes.remaining_quantity` restoration (covered in `backend/tests/unit/test_payment_service.py` and `backend/tests/integration/test_api_payments.py`).

**Acceptance Scenarios**:

1. **Given** VNPay redirects the consumer back to `/payment/vnpay-return` (`frontend/src/app/payment/vnpay-return/page.tsx`) with `vnp_*` parameters, **When** the page sends all query parameters to `GET /api/v1/payments/vnpay/return`, **Then** `PaymentService.verify_vnpay_return` verifies the `HMAC-SHA512` signature statelessly using `hmac.compare_digest` and the UI displays signature validity (`is_valid`), `txn_ref`, parsed VND amount, `vnp_BankCode`, `vnp_ResponseCode`, and navigation links to `/orders`.
2. **Given** VNPay sends an IPN (`GET /api/v1/payments/vnpay/ipn`) with `vnp_ResponseCode = "00"`, matching `order.total_amount`, and valid `vnp_SecureHash`, **When** `PaymentService.process_vnpay_ipn` acquires `lock:payment:ipn:{txn_ref}`, **Then** it persists a `PaymentTransaction` (`is_verified = True`), sets `order.payment_status = PAID` + `vnpay_transaction_no` / `vnpay_bank_code` / `vnpay_pay_date`, commits, and returns `{"RspCode": "00", "Message": "Success"}`.
3. **Given** VNPay re-sends the same IPN for an already verified transaction or already `PAID` order, **When** `process_vnpay_ipn` inspects `existing_transaction.is_verified` or `order.payment_status == PAID`, **Then** it returns `{"RspCode": "02", "Message": "Transaction already processed"}` without duplicating side effects or touching inventory.
4. **Given** VNPay sends a failed IPN (`vnp_ResponseCode != "00"`) for a still-pending cancellable order (`CONFIRMED` or `READY_FOR_PICKUP` and `payment_status == PENDING`), **When** `PaymentService._process_failed_payment` runs, **Then** it records an audit `PaymentTransaction`, atomically restores `order.quantity` to `dishes.remaining_quantity` via `dish_repo.atomic_increment_quantity`, sets `order.payment_status = FAILED` and `order.status = CANCELLED`, and returns `{"RspCode": "00", "Message": "Payment failed"}`.

---

### User Story 3 - Payment-Aware Order Lifecycle on `/orders` (History, Retry VNPay & Cancellation) (Priority: P1)

As an **`{abstract}` Order Participant** (**Consumer** or **Store Partner**), I want to inspect paginated orders filtered by lifecycle state, retry VNPay payment directly for `PENDING` online orders, and cancel eligible active orders before `pickup_deadline` with atomic inventory restoration without allowing double-cancellation.

**Why this priority**: Keeps consumers in control of their active reservations and ensures unpaid `VNPAY` orders can be completed or cancelled cleanly instead of stranding inventory.

**Independent Test**: Load `/orders`, filter by `CONFIRMED` / `READY_FOR_PICKUP` / `COMPLETED` / `CANCELLED`, trigger **"Thanh toán VNPay"** on a `VNPAY` + `PENDING` order (`POST /api/v1/payments/vnpay/create-url`), and click **"Hủy đơn"** (`PATCH /api/v1/orders/{id}/cancel`) before deadline to assert `Order.status == CANCELLED`, `dishes.remaining_quantity` restoration, and `409 Conflict` on duplicate cancellation.

**Acceptance Scenarios**:

1. **Given** an authenticated `CONSUMER` opens `/orders` (`frontend/src/app/orders/page.tsx`), **When** `GET /api/v1/orders/me` resolves, **Then** orders render with status filter tabs (`ALL`, `CONFIRMED`, `READY_FOR_PICKUP`, `COMPLETED`, `CANCELLED`), order code, payment badges (`VNPAY • PENDING/PAID/FAILED` or `COD • PENDING/PAID`), pickup deadline, CO₂e/points preview, and action buttons.
2. **Given** an active order (`CONFIRMED` or `READY_FOR_PICKUP`) has `payment_method === 'VNPAY'` and `payment_status === 'PENDING'`, **When** it renders on `/orders`, **Then** a **"Thanh toán VNPay"** button is displayed to invoke `paymentService.createVnpayUrl(order.id)` and redirect to VNPay Sandbox.
3. **Given** a consumer owner or owning store partner calls `PATCH /api/v1/orders/{order_id}/cancel` (or clicks **"Hủy đơn"** on `/orders`) before `pickup_deadline`, **When** `OrderService.cancel_order` acquires `lock:dish:{dish_id}`, **Then** `orders.cancel_if_allowed` + `dish_repo.atomic_increment_quantity` commit atomically (`status = CANCELLED`, dish restored from `SOLD_OUT` to `ACTIVE` if needed), while repeat cancellations or past-deadline attempts fail with `409 Conflict`.
4. **Given** an authenticated `STORE_PARTNER` or `ADMIN` queries `GET /api/v1/orders/store/{store_id}` or `GET /api/v1/orders/{order_id}`, **When** ownership/RBAC checks pass, **Then** paginated store orders or full `OrderDetailResponse` (omitting `qr_token` if missing, used, or expired) are returned.

---

### User Story 4 - Payment-to-QR Reconciliation Guard, Dynamic QR Issuance & Counter Verification (`/store/verify-qr`) (Priority: P1)

As a **Consumer** and **Store Partner**, I want unpaid `VNPAY` orders blocked from generating or redeeming pickup QR codes, while settled orders (`VNPAY` `PAID` or `COD`) issue dynamic `HMAC-SHA256` QR codes (`POST /api/v1/orders/{id}/qr`) that Store Partners verify once at `/store/verify-qr` (`POST /api/v1/orders/verify-qr`) to complete the order and settle `COD` to `PAID`.

**Why this priority**: Enforces payment-to-fulfillment integrity at the pickup counter and proves single-use anti-replay protection during live demo handover.

**Independent Test**: Attempt `POST /api/v1/orders/{id}/qr` and `POST /api/v1/orders/verify-qr` on a `VNPAY` + `PENDING` order and assert `409 Conflict`; verify QR issuance succeeds once `payment_status == PAID` or for `COD`; redeem via `/store/verify-qr` to assert `Order.status == COMPLETED`, `QRToken.is_used == True`, and `COD` `payment_status == PAID`; re-submit the identical QR payload to assert replay rejection (`400` / `409`).

**Acceptance Scenarios**:

1. **Given** a `VNPAY` order still has `payment_status != PAID`, **When** the consumer clicks **"Xem mã QR"** (`POST /api/v1/orders/{id}/qr`) or a merchant attempts `POST /api/v1/orders/verify-qr`, **Then** `OrderService._validate_payment_ready_for_qr` rejects the request with `409 Conflict` (`"Đơn hàng VNPAY chưa hoàn tất thanh toán"`).
2. **Given** an active order is `COD` or `VNPAY` (`PAID`) and before `pickup_deadline`, **When** the consumer clicks **"Xem mã QR"** on `/orders`, **Then** `POST /api/v1/orders/{id}/qr` idempotently generates or returns the signed `ecobite://pickup?...` payload (`16`-byte nonce + `HMAC-SHA256` signature), rendered inside `<QRCodeSVG />` with expiry timestamp and one-click **"Sao chép"**.
3. **Given** an owning `STORE_PARTNER` opens `/store/verify-qr` (`frontend/src/app/store/verify-qr/page.tsx`), scans via `html5-qrcode` camera or pastes the QR payload, and submits **"Xác thực & Hoàn tất đơn"**, **When** `OrderService.verify_and_complete_order` validates `hmac.compare_digest`, expiration, consumer match, store ownership, and payment readiness under `lock:order:redeem:{order_id}`, **Then** `qr_tokens.mark_token_as_used` atomically sets `is_used = True`, `Order.status` becomes `COMPLETED`, `COD` transitions to `payment_status = PAID`, and handover completion data (including `green_points_earned` and `co2_saved_kg`) is committed atomically in the same order transaction.
4. **Given** the same QR payload is pasted/scanned a second time (or belongs to another store), **When** `POST /api/v1/orders/verify-qr` executes, **Then** replay attempts are rejected immediately (`400` / `409`) and cross-store scans return `403 Forbidden`.

---

### Edge Cases

- What happens when `PaymentService` receives an IPN with invalid `vnp_SecureHash`? Returns `{"RspCode": "97", "Message": "Invalid signature"}` via `hmac.compare_digest` without modifying database records.
- What happens when `PaymentService` receives an IPN whose `vnp_Amount / 100` mismatches `order.total_amount`? Returns `{"RspCode": "04", "Message": "Amount mismatch"}`.
- What happens when `ZoneInfo("Asia/Ho_Chi_Minh")` lacks OS `tzdata` (common on Windows)? Both `PaymentService` and `OrderService` safely fall back to `timezone(timedelta(hours=7))`.
- What happens when two requests attempt to verify the same QR token concurrently? Redis lock `lock:order:redeem:{order_id}` and atomic SQL `UPDATE qr_tokens SET is_used = TRUE ... WHERE id = :id AND is_used IS FALSE` ensure only one request wins (`200`), and the second fails cleanly (`400`/`409`) without double-completing.
- What happens if browser camera permissions fail on `/store/verify-qr`? `StoreVerifyQrPage` captures the camera error cleanly in `cameraError` and leaves the manual payload textarea fully operational.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow `CONSUMER` users to choose `COD` or `VNPAY` when placing an order (`POST /api/v1/orders`) with Redis lock + atomic SQL `remaining_quantity` decrement, and generate signed VNPay Sandbox v2.1.0 URLs (`POST /api/v1/payments/vnpay/create-url`).
- **FR-002**: System MUST verify VNPay return URL parameters (`GET /api/v1/payments/vnpay/return` rendered on `/payment/vnpay-return`) and server-to-server IPN callbacks (`GET /api/v1/payments/vnpay/ipn`) using `HMAC-SHA512` (`hmac.compare_digest`), Redis lock idempotency (`lock:payment:ipn:{txn_ref}`), and atomic `dish_repo.atomic_increment_quantity` stock restoration on failed payments.
- **FR-003**: System MUST provide payment-aware order management (`GET /orders/me`, `GET /orders/store/{id}`, `GET /orders/{id}`, `PATCH /orders/{id}/cancel`, and `/orders` UI) including pending VNPay payment retry and pre-deadline atomic cancellation without double-restoration.
- **FR-004**: System MUST block QR generation (`POST /api/v1/orders/{order_id}/qr`) and QR redemption (`POST /api/v1/orders/verify-qr`) for unpaid `VNPAY` orders with `409 Conflict`, issue dynamic `HMAC-SHA256` QR codes (`<QRCodeSVG />`), settle `COD` orders to `PAID` on counter handover at `/store/verify-qr`, and enforce atomic single-use `QRToken.is_used` anti-replay.
- **FR-005**: System MUST pass checkout/payment unit tests (`OrderModal.test.tsx`, `payment.service.test.ts`), Next.js `lint`/`type-check`/`build`, and backend `ruff` plus payment/order/QR unit, integration, and concurrency test suites.

### Non-Functional Requirements

- **NFR-001 (Security & Cryptography)**: VNPay signatures MUST use `HMAC-SHA512` over sorted `quote_plus`-encoded parameters excluding `vnp_SecureHash`/`vnp_SecureHashType`; QR payloads MUST use `HMAC-SHA256` with `secrets.token_hex(16)` nonces; both MUST verify via constant-time `hmac.compare_digest`, with `VNP_TMN_CODE`, `VNP_HASH_SECRET`, `QR_SIGNATURE_SECRET`, and `SECRET_KEY` loaded strictly via `pydantic-settings`.
- **NFR-002 (Concurrency & Idempotency)**: Duplicate VNPay IPNs (`RspCode: "02"`), concurrent order placements (`test_order_placement_concurrency_benchmark`), duplicate order cancellations (`cancel_if_allowed`), and concurrent QR redemptions (`mark_token_as_used`) MUST remain race-free and transactional.
- **NFR-003 (Role Isolation)**: Order placement, VNPay URL creation, and QR issuance MUST enforce `UserRole.CONSUMER` + ownership; QR verification MUST enforce `UserRole.STORE_PARTNER` + store ownership; `/store/verify-qr` and `/orders` MUST enforce `<AuthGuard>`.

### Key Entities

- **Order (`backend/app/models/order.py`)**: Stores `order_code`, `consumer_id`, `store_id`, `dish_id`, `quantity`, `unit_price`, `total_amount`, `status` (`CONFIRMED`, `READY_FOR_PICKUP`, `COMPLETED`, `CANCELLED`, `EXPIRED`), `payment_method` (`VNPAY`, `COD`), `payment_status` (`PENDING`, `PAID`, `FAILED`), `vnpay_transaction_no`, `vnpay_bank_code`, `vnpay_pay_date`, `co2_saved_kg`, `green_points_earned`, `pickup_deadline`, and `completed_at`.
- **PaymentTransaction (`backend/app/models/order.py`)**: Audit log per gateway attempt storing `order_id`, `payment_provider` (`VNPAY`), `txn_ref`, `amount`, `vnp_transaction_no`, `vnp_bank_code`, `vnp_response_code`, `is_verified`, and `raw_ipn_payload`.
- **QRToken (`backend/app/models/order.py`)**: 1-to-1 dynamic pickup credential storing `order_id`, `token_hash` (`HMAC-SHA256`), `nonce`, `expires_at`, `is_used`, and `used_at`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Invalid VNPay IPN signatures return `RspCode: "97"`, mismatched amounts return `"04"`, duplicate verified IPNs return `"02"`, and failed payments (`vnp_ResponseCode != "00"`) restore `100%` of reserved dish quantity atomically.
- **SC-002**: `0%` of unpaid `VNPAY` orders can issue or redeem a pickup QR (`409 Conflict` enforced), while `100%` of valid first-time QR handovers transition `Order.status` to `COMPLETED` (setting `COD` `payment_status = PAID`) and `100%` of repeat QR attempts are rejected.
- **SC-003**: Under `50` concurrent buyers competing for `2` portions (`test_order_placement_concurrency_benchmark`), exactly `2` orders succeed (`201`), `48` return `409 Conflict`, and final `remaining_quantity == 0`.
- **SC-004**: Checkout/payment Vitest suites (`OrderModal.test.tsx`: `3` tests; `payment.service.test.ts`: `2` tests), full frontend quality gates (`npm test`: `6` files / `17` tests, `npm run lint`, `npm run type-check`, `npm run build`), and `ruff` checks exit `0`.

## Assumptions & Scope Boundaries

- `SCRUM-42` covers **only** Spec Kit (`specs/002-vnpay-checkout-order-lifecycle/`), Full-Stack VNPay Checkout (`OrderModal`, `payments.py`, `PaymentService`, `/payment/vnpay-return`), Payment-Aware Order Lifecycle (`/orders`, `orders.py`, `OrderService`, `/store/verify-qr`), and the Demo Video script.
- `SCRUM-41` (Phùng Quốc Huy's PA4-E functional group — e.g., Surplus Dishes / Store Menu / Reviews / Gamification portals) and Admin KYC (`/admin`) are owned separately and intentionally excluded from `SCRUM-42` deliverables.
- `verify_and_complete_order` in `backend/app/services/order_service.py` updates order handover state alongside the repository's existing completion-time `green_points_balance` / `GreenPointsLedger` / `Store.total_co2_saved_kg` transaction hooks, while `/green-points` wallet UI, voucher catalog/redemption, and verified reviews remain outside `SCRUM-42`.
