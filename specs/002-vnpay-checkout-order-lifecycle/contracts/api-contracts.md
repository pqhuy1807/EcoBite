# API & UI Contracts: Full-Stack VNPay Checkout & Order Lifecycle (SCRUM-42)

**Base URL**: `/api/v1`  
**Jira Scope**: `SCRUM-42` — *Spec Kit, Full-Stack VNPay Checkout, Order Lifecycle and Demo Video*

---

## 1. VNPay Payment Gateway (`backend/app/api/v1/endpoints/payments.py`)

### `POST /payments/vnpay/create-url` (`CONSUMER` order owner only)
- **Query Params**: `order_id` (UUID string, required), `bank_code` (string, optional — e.g., `VNPAYQR`, `NCB`).
- **Preconditions**: Caller owns order; `order.payment_method == "VNPAY"`; `order.payment_status == "PENDING"`; `order.status` not in `("CANCELLED", "EXPIRED", "COMPLETED")`.
- **Client IP Extraction**: Reads first address in `X-Forwarded-For`, fallback `request.client.host`, fallback `"127.0.0.1"`.
- **Response `200`** (`VNPayCreateUrlResponse`):
  ```json
  {
    "payment_url": "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_Amount=2500000&vnp_CreateDate=20261128140000&vnp_TxnRef=EB-20261128-XXXXXXXX&vnp_SecureHash=...",
    "txn_ref": "EB-20261128-XXXXXXXX",
    "vnp_amount": 2500000
  }
  ```
- **Errors**: `401` unauthenticated, `403` non-`CONSUMER` or non-owner, `404` order not found, `409` non-`VNPAY` method or `payment_status != PENDING`, `410` order `CANCELLED`/`EXPIRED`/`COMPLETED`.

### `GET /payments/vnpay/ipn` (Public Server-to-Server Webhook, HMAC-SHA512 Protected)
- **Query Params**: VNPay IPN query parameters (`vnp_TxnRef`, `vnp_Amount`, `vnp_ResponseCode`, `vnp_TransactionNo`, `vnp_BankCode`, `vnp_SecureHash`, optional `vnp_SecureHashType`).
- **Behavior**:
  - Verifies `vnp_TxnRef`, constant-time `HMAC-SHA512` over sorted `quote_plus`-encoded params (`hmac.compare_digest`), order existence, and exact `order.total_amount == Decimal(vnp_Amount) / 100`.
  - Acquires Redis distributed lock `lock:payment:ipn:{vnp_TxnRef}`.
  - Checks existing verified `PaymentTransaction` (`is_verified=True`) for idempotency (`RspCode: "02"`).
  - `vnp_ResponseCode == "00"` → inserts `PaymentTransaction` (`is_verified=True`), updates `Order.payment_status = "PAID"`, `vnpay_transaction_no`, `vnpay_bank_code`, `vnpay_pay_date`.
  - `vnp_ResponseCode != "00"` (for `PENDING` order in `CONFIRMED`/`READY_FOR_PICKUP`) → inserts unverified `PaymentTransaction`, atomically restores `dishes.remaining_quantity` via `dish_repo.atomic_increment_quantity`, sets `Order.payment_status = "FAILED"` and `Order.status = "CANCELLED"`.
- **Response `200`** (`VNPayIPNResponse`):
  - `"00"` `Success` / `Payment failed` handled
  - `"01"` `Missing transaction reference`
  - `"02"` `Transaction already processed` (idempotent)
  - `"04"` `Missing amount` / `Amount mismatch`
  - `"09"` `Order not found` / `Failed to restore inventory`
  - `"97"` `Invalid signature`

### `GET /payments/vnpay/return` (Stateless Client Return Signature Verification)
- **Query Params**: Redirect query params (`vnp_TxnRef`, `vnp_SecureHash`, etc.).
- **Response `200`** (`VNPayReturnResponse`):
  ```json
  {
    "is_valid": true,
    "message": "Signature verified",
    "txn_ref": "EB-20261128-XXXXXXXX"
  }
  ```
- **Note**: Verifies cryptographic signature without mutating database state (`"Missing transaction reference"` or `"Invalid signature"` when invalid).

---

## 2. Payment-Aware Order Lifecycle & QR (`backend/app/api/v1/endpoints/orders.py`)

### `POST /orders` (`CONSUMER` only)
- **Request** (`OrderCreate`):
  ```json
  {
    "dish_id": "uuid",
    "quantity": 1,
    "payment_method": "VNPAY"
  }
  ```
- **Response `201`** (`OrderResponse`): Atomically decrements dish stock under `lock:dish:{dish_id}` and returns `id`, `order_code`, `status: "CONFIRMED"`, `payment_method`, `payment_status: "PENDING"`, `total_amount`, `co2_saved_kg`, `green_points_earned`, `pickup_deadline`, display store/dish fields.
- **Errors**: `400` outside pickup window, `401`/`403` auth/role, `404` dish not found, `409` dish inactive or insufficient remaining stock.

### `GET /orders/me`, `GET /orders/store/{store_id}`, `GET /orders/{order_id}`
- `GET /orders/me?status={optional}&skip=0&limit=20` (`CONSUMER`): Paginated consumer order history.
- `GET /orders/store/{store_id}?status={optional}&skip=0&limit=20` (`StoreOwner`): Paginated store orders.
- `GET /orders/{order_id}` (`CONSUMER` owner / `STORE_PARTNER` owner / `ADMIN`): `OrderDetailResponse` (omits `qr_token` if missing, used, expired, or order inactive).

### `POST /orders/{order_id}/qr` (`CONSUMER` owner only — Payment-Guarded)
- **Preconditions**: Owning consumer; `_validate_payment_ready_for_qr` (`payment_method == "COD"` or `payment_status == "PAID"`); status in `("CONFIRMED", "READY_FOR_PICKUP")`; `now <= pickup_deadline`.
- **Response `200`** (`QRPayloadResponse`):
  ```json
  {
    "order_id": "uuid",
    "order_code": "EB-20261128-XXXXXXXX",
    "qr_payload": "ecobite://pickup?order_id=...&user_id=...&nonce=...&expires_at=...&sig=...",
    "nonce": "32-hex-chars",
    "expires_at": "2026-11-28T21:00:00Z",
    "is_used": false
  }
  ```
- **Errors**: `403` non-owner, `404` not found, `409` `"Đơn hàng VNPAY chưa hoàn tất thanh toán"`, invalid status, past deadline, or QR already used/expired.

### `POST /orders/verify-qr` (`STORE_PARTNER` owner only)
- **Request** (`QRVerificationRequest`): `{ "qr_token": "ecobite://pickup?..." }` (accepts `qr_token` or `qr_payload` alias).
- **Behavior**: Validates `HMAC-SHA256` signature (`hmac.compare_digest`), expiry, consumer match, store ownership, `_validate_payment_ready_for_qr`, and inside `lock:order:redeem:{order_id}` atomically marks `QRToken.is_used = True`, sets `Order.status = "COMPLETED"`, transitions `COD` `payment_status` to `"PAID"`, and settles completion impact records in one DB transaction.
- **Response `200`** (`QRVerificationResponse`): `{ "success": true, "order_id", "order_code", "status": "COMPLETED", "points_awarded", "co2_saved_kg", "message", "order" }`.
- **Errors**: `400` malformed/tampered/expired/reused QR, `403` wrong store or role, `404` missing token/order, `409` unpaid `VNPAY` (`"Đơn hàng VNPAY chưa hoàn tất thanh toán"`) or non-cancellable order state.

### `PATCH /orders/{order_id}/cancel` (`CONSUMER` owner or `STORE_PARTNER` owner)
- **Behavior**: Enforces ownership and `now <= pickup_deadline`; inside `lock:dish:{dish_id}` executes `orders.cancel_if_allowed` + `dish_repo.atomic_increment_quantity` atomically.
- **Response `200`**: `OrderResponse` (`status: "CANCELLED"`).
- **Errors**: `403` unauthorized user, `404` order missing, `409` non-cancellable status or past `pickup_deadline`.

---

## 3. Frontend Component & Route Contracts (`SCRUM-42` Scope)

| Surface | Route / File | Connected Backend APIs | Role Guard |
| :--- | :--- | :--- | :--- |
| **Order Checkout Modal** | `frontend/src/components/OrderModal.tsx` | `POST /orders`, `POST /payments/vnpay/create-url` | Consumer action |
| **VNPay Return Page** | `/payment/vnpay-return` | `GET /payments/vnpay/return` | Public callback |
| **Consumer Order Lifecycle** | `/orders` (`frontend/src/app/orders/page.tsx`) | `GET /orders/me`, `POST /payments/vnpay/create-url`, `POST /orders/{id}/qr`, `PATCH /orders/{id}/cancel` | `AuthGuard` (`CONSUMER`, `ADMIN`) |
| **Store QR Verification** | `/store/verify-qr` (`frontend/src/app/store/verify-qr/page.tsx`) | `POST /orders/verify-qr` (`html5-qrcode` camera + manual paste) | `AuthGuard` (`STORE_PARTNER`, `ADMIN`) |
