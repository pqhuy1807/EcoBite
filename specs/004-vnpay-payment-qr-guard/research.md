# Technical Research & Design Decisions: VNPay Cashless Checkout, Idempotent IPN & Payment-QR Reconciliation Guard

**Feature**: `004-vnpay-payment-qr-guard` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

This document records the verified engineering decisions, security tradeoffs, and Sandbox interoperability fixes discovered by auditing the actual codebase against VNPay v2.1.0 specifications and EcoBite Constitution v1.2.0.

---

## Decision 1: VNPay v2.1.0 Canonical HMAC-SHA512 Signing & Sandbox Compliance

- **Decision**: Update `PaymentService._generate_vnpay_hash()` and `create_vnpay_payment_url()` in `backend/app/services/payment_service.py` to:
  1. Sort non-empty parameter pairs alphabetically by key and URL-encode every value using `urllib.parse.quote_plus(str(value))` when constructing `hash_data`:
     ```python
     hash_data = "&".join(
         f"{key}={urllib.parse.quote_plus(str(value))}"
         for key, value in sorted(params.items())
         if value is not None and str(value) != ""
     )
     ```
  2. Build the final redirect URL using the exact same sorted parameter sequence (excluding empty values such as unset `vnp_BankCode`) and `settings.VNP_URL` (falling back to `"https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"` only when `settings.VNP_URL` is blank in unit tests).
  3. Generate `vnp_CreateDate` using `ZoneInfo("Asia/Ho_Chi_Minh")` with deterministic fallback `timezone(timedelta(hours=7))` (matching `VIETNAM_TZ` in `backend/app/services/order_service.py`), never relying on host-local `datetime.now(UTC).astimezone()`.
  4. Exclude BOTH `vnp_SecureHash` and `vnp_SecureHashType` during `_verify_vnpay_ipn_signature()`, and verify using constant-time `hmac.compare_digest(expected_hash.lower(), provided_hash.lower())`.
- **Rationale**:
  - Direct inspection of `backend/app/services/payment_service.py` revealed three real Sandbox blockers still present on `dev`: (a) line 158 joins unencoded `f"{key}={value}"` while line 136 uses `urllib.parse.urlencode(vnp_params)` — because `vnp_OrderInfo` contains spaces (`"Thanh toan don hang ..."`) and `vnp_ReturnUrl` contains `://`, VNPay Sandbox computes HMAC over `quote_plus`-encoded values and rejects raw-concatenated hashes with **Error 70 (Invalid Signature)**; (b) line 28 hardcodes `_VNPAY_BASE_URL` ignoring `settings.VNP_URL`; (c) line 104 uses `datetime.now(UTC).astimezone()`, which evaluates to UTC inside Linux/Docker containers (7 hours behind Vietnam time).
  - Case-insensitive comparison (`lower()`) handles gateways returning uppercase hex while preserving constant-time security via `hmac.compare_digest`.
- **Alternatives considered**:
  - Computing hash over raw unencoded strings: fails on live VNPay v2.1.0 Sandbox whenever `vnp_OrderInfo` or `vnp_ReturnUrl` has spaces or URL punctuation.

---

## Decision 2: Dual-Layer IPN Idempotency (Redis Distributed Lock + DB State Backstop)

- **Decision**: Retain and harden the two-layer idempotency design in `PaymentService.process_vnpay_ipn()`:
  - **Layer 1 (Coordination)**: `async with distributed_lock(f"lock:payment:ipn:{txn_ref}", timeout_seconds=30) as acquired:` (`backend/app/core/redis.py`). When Redis is reachable and another worker already holds the lock (`acquired is False`), immediately check `get_verified_by_txn_ref(txn_ref)` and return without entering the critical section (avoiding parallel mutations).
  - **Layer 2 (Authoritative DB Guard)**: Inside the critical section (and when Redis is offline in degraded mode / SQLite tests), check:
    1. `existing_verified = await self.payments.get_verified_by_txn_ref(txn_ref)` (not `get_by_txn_ref` with `scalar_one_or_none()`, which could raise `MultipleResultsFound` if multiple unverified/failed audit rows exist for the same `txn_ref`).
    2. `order.payment_status != PaymentStatus.PENDING` (for both success and failure paths). If already `PAID` or `FAILED`, immediately return `{"RspCode": "02", "Message": "Order already confirmed"}` (without creating duplicate rows or restoring stock).
- **Rationale**:
  - Satisfies **Constitution Principle III** (*"Redis distributed locks MAY be used as an additional concurrency-control mechanism where appropriate; they MUST NOT replace database-level integrity guarantees"*) and **Guardrail #3/#4**.
  - Direct audit of `backend/app/repositories/payment_repo.py` showed `get_by_txn_ref` calls `result.scalar_one_or_none()` without `.limit(1)` — if an order ever accumulated >1 `PaymentTransaction` audit row, a subsequent IPN would crash with SQLAlchemy `MultipleResultsFound`. Switching the idempotency check to `get_verified_by_txn_ref(txn_ref)` (ordering newest first with `.limit(1)`) and guarding `order.payment_status != PaymentStatus.PENDING` up front eliminates this failure mode completely.
  - Also standardize missing/unknown `vnp_TxnRef` lookup response to VNPay's documented `RspCode: "01"` (`Order not found`), replacing the non-standard `"09"` currently at line 229 of `payment_service.py`.
- **Alternatives considered**:
  - Relying exclusively on Redis locks without DB status checks: unsafe when Redis restarts or runs in degraded mode (pytest / local dev without Redis).

---

## Decision 3: Single-Transaction Failure Rollback & Atomic Stock Restoration

- **Decision**: When a verified IPN reports payment failure or user cancellation (`vnp_ResponseCode != "00"`):
  1. Guard strictly on `order.payment_status == PaymentStatus.PENDING` and `order.status in (OrderStatus.CONFIRMED, OrderStatus.READY_FOR_PICKUP)`; otherwise return `RspCode: "02"` immediately without touching inventory.
  2. Within a single DB transaction (`commit=False` on intermediate repository operations):
     - Insert an audit `PaymentTransaction` (`is_verified=False`, recording `vnp_response_code` and `raw_ipn_payload`).
     - Call `dish_repo.atomic_increment_quantity(self.db, order.dish_id, order.quantity, commit=False)` — which atomically executes `UPDATE dishes SET remaining_quantity = remaining_quantity + :qty, status = CASE WHEN status = 'SOLD_OUT' THEN 'ACTIVE' ELSE status END WHERE id = :dish_id`.
     - If restoration returns `None`, `await self.db.rollback()` and return an error code.
     - Update `order.payment_status = PaymentStatus.FAILED` and `order.status = OrderStatus.CANCELLED`.
     - Execute one final `await self.db.commit()`.
- **Rationale**: Guarantees that failed cashless orders immediately release scarce end-of-shift meals back to the Radar map for other consumers, while guaranteeing that VNPay failure retries can NEVER over-inflate `remaining_quantity` beyond `total_quantity`.
- **Alternatives considered**:
  - Restoring stock in a separate transaction after cancelling the order: risks orphaned stock loss if the process crashes between commits.

---

## Decision 4: Stateless Return URL Verification vs Authoritative IPN

- **Decision**: Keep `GET /api/v1/payments/vnpay/return` strictly stateless (`PaymentService.verify_vnpay_return(query_params)` as a `@staticmethod` requiring no `DBSession`). It verifies `vnp_TxnRef` presence and HMAC-SHA512 signature only, returning `{"is_valid": bool, "message": str, "txn_ref": str}`. Order status mutations happen ONLY inside `GET /api/v1/payments/vnpay/ipn`.
- **Rationale**:
  - Browser redirects can be replayed, dropped when a user closes their tab mid-redirect, or manipulated in the address bar. Keeping `return` read-only prevents client-side spoofing while still giving `/orders/vnpay-return` cryptographically verified feedback (paired with `vnp_ResponseCode` and `vnp_Amount` displayed to the user).
  - Note: Audit confirmed the earlier `MagicMock` workaround in `payments.py` has already been removed — `vnpay_return` cleanly calls `PaymentService.verify_vnpay_return(query_params)` directly.
- **Alternatives considered**:
  - Mutating `Order.payment_status = PAID` inside `/vnpay/return` as a localhost shortcut: rejected because it duplicates IPN state transitions and introduces race conditions between browser return and gateway IPN.

---

## Decision 5: `POST /payments/vnpay/create-url` Contract, RBAC & Real Client IP

- **Decision**:
  1. **RBAC (Guardrail #2)**: Replace manual `if consumer.role != UserRole.CONSUMER:` in `backend/app/api/v1/endpoints/payments.py` with `current_user: Annotated[User, Depends(require_roles(UserRole.CONSUMER))]`.
  2. **Real Client IP**: Inject `request: Request` into `create_vnpay_payment_url` and extract the client IP safely from `X-Forwarded-For` (first comma-separated entry, stripped) → `request.client.host` → fallback `"127.0.0.1"`.
  3. **Request Parameter Contract Alignment**: Both existing backend `payments.py` (`order_id: str, bank_code: str | None = Query(None)`) AND existing frontend `frontend/src/services/payment.service.ts` (`apiClient.post('/payments/vnpay/create-url', null, { params: { order_id, bank_code } })`) ALREADY agree on query parameters! To keep zero breaking friction with Thịnh's `payment.service.ts` while also remaining friendly to Swagger JSON callers (per `docs/04_API_Specification.md`), keep query parameters as the primary working contract (or support optional `VNPayCreateUrlRequest` JSON body fallback if `order_id` query param is absent, documenting the canonical contract explicitly in `contracts/api-contracts.md`).
- **Rationale**: Prevents breaking the already-merged `frontend/src/services/payment.service.ts` right before PA4 freeze while enforcing Constitution Principle II (`require_roles`) and authentic `vnp_IpAddr` auditing for VNPay Sandbox.
- **Alternatives considered**:
  - Breaking change to JSON-body-only without updating frontend simultaneously: unnecessary cross-branch conflict risk during Week 6 freeze.

---

## Decision 6: Payment ↔ QR Reconciliation Guard & Atomic COD Settlement (`OrderService`)

- **Decision**: Verified already implemented and green in `backend/app/services/order_service.py`:
  1. `_validate_payment_ready_for_qr(order)` raises `HTTP 409 Conflict` (`"Đơn hàng VNPAY chưa hoàn tất thanh toán"`) whenever `order.payment_method == PaymentMethod.VNPAY and order.payment_status != PaymentStatus.PAID`.
  2. Invoked at BOTH gates: `issue_or_get_qr_payload()` (before generating or returning a signed QR URI) AND `verify_and_complete_order()` (defense-in-depth at store pickup scan).
  3. Inside `verify_and_complete_order()`, wrapped in `distributed_lock(f"lock:order:redeem:{order_id}", timeout_seconds=5)` and a single SQLAlchemy transaction:
     - `self.qr_tokens.mark_token_as_used(..., commit=False)` (conditional SQL `WHERE id = :id AND is_used = FALSE`)
     - `self.orders.complete_if_allowed(..., commit=False)` (conditional SQL `WHERE id = :id AND status IN ('CONFIRMED', 'READY_FOR_PICKUP')`)
     - `if completed_order.payment_method == PaymentMethod.COD: completed_order.payment_status = PaymentStatus.PAID`
     - Credit `consumer.green_points_balance += completed_order.green_points_earned` and append `GreenPointsLedger` (`PointActionType.ORDER_RESCUE`) via `GamificationRepository` (`commit=False`)
     - Accumulate `store.total_co2_saved_kg += completed_order.co2_saved_kg` via `store_repo.get_store_by_id`
     - Single `await self.db.commit()`, rolling back everything on any exception.
- **Rationale**: Audit confirmed all 9 Payment↔QR Guard and atomic COD/Gamification unit tests in `backend/tests/unit/test_order_service.py` already pass (`39/39` order unit tests green), and repository boundaries (`GamificationRepository`, `store_repo`) are already clean!

---

## Decision 7: Frontend VNPay Flow, `<Suspense>` Return Page & Store Orders Table

- **Decision**:
  1. **Duplicate key cleanup**: Remove duplicate `"test": "vitest run"` line in `frontend/package.json`, keeping `"test": "vitest run --passWithNoTests"`.
  2. **Checkout Modal (`OrderModal.tsx` & `page.tsx`)**: Add explicit `payment_method` toggle (`COD` vs `VNPAY`), pass `payment_method` into `orderService.createRescueOrder(...)`, and remove the silent mock-order catch block for real errors. When `payment_method === 'VNPAY'`, call `paymentService.createVnpayUrl(order.id)` and redirect via `window.location.href = payment_url` (with loading state and error fallback directing to `/orders`).
  3. **Return Page (`frontend/src/app/orders/vnpay-return/page.tsx`)**: Wrap the inner `useSearchParams()` reader component in `<Suspense fallback={...}>` so Next.js 14 static/App Router production builds (`npm run build`) succeed without `CSR bailout` errors. Call `paymentService.verifyVnpayReturn(queryParams)` and evaluate both `is_valid` and `vnp_ResponseCode === '00'` to display clear success or failure/rollback messaging.
  4. **My Orders QR Guard (`frontend/src/app/orders/page.tsx`)**: Define helper `isVnpayPending = order.payment_method === 'VNPAY' && order.payment_status === 'PENDING'`. Hide/lock *"Xem mã QR"* (and skip `?highlight=` auto-QR open) when `isVnpayPending`, display *"Chờ thanh toán VNPay"* badge and *"Thanh toán VNPay ngay"* button invoking `paymentService.createVnpayUrl(order.id)`.
  5. **Store Orders Queue (`frontend/src/app/store/verify-qr/page.tsx` + `order.service.ts`)**: Add `getStoreOrders(storeId, status?)` (`GET /orders/store/${storeId}`) to `order.service.ts`; query `storeService.getMyStore()` then `orderService.getStoreOrders(store.id, filterStatus)` via React Query inside `/store/verify-qr`, displaying order status + payment method/status badges alongside the scanner and calling `queryClient.invalidateQueries({ queryKey: ['store-orders'] })` on successful QR redemption.
- **Rationale**: Eliminates the current UX mismatch where `/orders` renders *"Xem mã QR"* on pending `VNPAY` orders only to fail with `409 Conflict` when clicked, gives partners real-time visibility into incoming pickup orders at the counter, and keeps `npm run build` green under Next.js 14 App Router rules.

---

## Decision 8: Integration/Concurrency Test Strategy & `< 2s` QR Latency Benchmark

- **Decision**: Author `backend/tests/integration/test_api_payments.py` using isolated per-request `async_sessionmaker` sessions over a temp-file SQLite `NullPool` engine (reusing the proven pattern in `backend/tests/integration/test_order_concurrency.py`) for concurrent IPN tests (`asyncio.gather`), plus standard `conftest.py` `client` fixtures for API contract, Payment↔QR Guard E2E, and QR verification `< 2.0s` latency benchmark (`time.perf_counter()` asserting single & P95 `< 2000 ms`).
- **Rationale**: Using separate `AsyncSession` instances per concurrent request accurately tests real concurrent IPN contention without hitting SQLAlchemy single-session concurrency errors, proving idempotency and single atomic stock restoration under real race conditions.
