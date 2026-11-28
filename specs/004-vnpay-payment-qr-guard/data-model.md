# Data Model: VNPay Cashless Checkout, Idempotent IPN & Payment-QR Reconciliation Guard

**Feature**: `004-vnpay-payment-qr-guard` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

This feature builds entirely on existing persistent tables already provisioned by EcoBite's initial Alembic migration (`backend/alembic/versions/`): **no new database tables or schema migrations are required**. All models remain portable across PostgreSQL 16 (production/Docker) and SQLite `aiosqlite` (pytest).

---

## 1. Persistent ORM Entities (`backend/app/models/`)

### 1.1 `Order` (`backend/app/models/order.py` — table `orders`)

| Column | SQLAlchemy Type | Constraints / Role in Feature 004 |
| :--- | :--- | :--- |
| `id` | `Uuid` (PK) | Primary key passed to `POST /payments/vnpay/create-url` and `POST /orders/{order_id}/qr`. |
| `order_code` | `String(50)` (`UNIQUE`, indexed) | Format `EB-YYYYMMDD-XXXXXXXX`. Used directly as VNPay `vnp_TxnRef`. |
| `consumer_id` | `Uuid` (FK → `users.id`) | Verified for ownership on `create-url` and `issue_or_get_qr_payload`. |
| `store_id` | `Uuid` (FK → `stores.id`) | Verified against `Store.owner_id` on `verify_and_complete_order` and `GET /orders/store/{store_id}`. |
| `dish_id` | `Uuid` (FK → `dishes.id`) | Target for `dish_repo.atomic_increment_quantity` when a failed VNPay IPN cancels the order. |
| `quantity` | `Integer` (`> 0`) | Number of surplus portions reserved and atomically restored on failed IPN. |
| `total_amount` | `Numeric(12, 2)` (`>= 0`) | Authoritative VND order total; converted to `vnp_Amount = int(total_amount * 100)` and verified strictly on IPN (`RspCode: "04"` if mismatched). |
| `status` | `OrderStatus` | `CONFIRMED` \| `READY_FOR_PICKUP` \| `COMPLETED` \| `CANCELLED` \| `EXPIRED`. |
| `payment_method` | `PaymentMethod` | `VNPAY` \| `COD`. Determines checkout flow and Payment↔QR guard rule. |
| `payment_status` | `PaymentStatus` | `PENDING` \| `PAID` \| `FAILED`. Authoritative gate for `VNPAY` QR issuance/redemption. |
| `vnpay_transaction_no` | `String(100) \| None` | Populated on IPN `vnp_ResponseCode == "00"` from `vnp_TransactionNo`. |
| `vnpay_bank_code` | `String(50) \| None` | Populated on IPN `00` from `vnp_BankCode` (e.g., `NCB`, `VNPAYQR`). |
| `vnpay_pay_date` | `DateTime(tz=True) \| None` | Populated on IPN `00` settlement timestamp. |
| `co2_saved_kg` | `Numeric(8, 2)` | Credited to `GreenPointsLedger` and `Store.total_co2_saved_kg` atomically on QR completion. |
| `green_points_earned` | `Integer` | Credited to `User.green_points_balance` and `GreenPointsLedger` atomically on QR completion. |
| `pickup_deadline` | `DateTime(tz=True)` | Upper bound for QR validity and order eligibility. |
| `completed_at` | `DateTime(tz=True) \| None` | Set atomically during `OrderRepository.complete_if_allowed`. |

### 1.2 `PaymentTransaction` (`backend/app/models/order.py` — table `payment_transactions`)

| Column | SQLAlchemy Type | Constraints / Role in Feature 004 |
| :--- | :--- | :--- |
| `id` | `Uuid` (PK) | Unique audit record ID. |
| `order_id` | `Uuid` (FK → `orders.id`, indexed) | Links audit entry back to `Order`. |
| `payment_provider` | `String(50)` | Constant `"VNPAY"`. |
| `txn_ref` | `String(100)` (indexed) | Mirrors `vnp_TxnRef` (`order.order_code`). Queried by `PaymentTransactionRepository`. |
| `amount` | `Numeric(12, 2)` | Actual VND amount decoded from `Decimal(vnp_Amount) / 100`. |
| `vnp_transaction_no` | `String(100) \| None` | VNPay gateway transaction number. |
| `vnp_bank_code` | `String(50) \| None` | Customer payment bank/method code. |
| `vnp_response_code` | `String(10)` | VNPay response code (`"00"` = success; non-`"00"` = cancelled/failed). |
| `is_verified` | `Boolean` (default `False`) | Set `True` on verified successful IPN (`"00"`). Used alongside `Order.payment_status` for DB-level idempotency. |
| `raw_ipn_payload` | `JSON_TYPE` (JSONB / JSON) | Full raw IPN query dict persisted for financial auditability (never contains `VNP_HASH_SECRET`). |
| `created_at` | `DateTime(tz=True)` | Audit timestamp (`server_default=func.now()`). |

### 1.3 Related Entities Updated Atomically

- **`QRToken` (`qr_tokens`)**: 1-to-1 with `Order` (`order_id` unique); holds `token_hash` (HMAC-SHA256), `nonce` (unique), `expires_at`, `is_used`, `used_at`. Marked used via conditional SQL `QRTokenRepository.mark_token_as_used(..., commit=False)`.
- **`Dish` (`dishes`)**: Restored on failed IPN via `dish_repo.atomic_increment_quantity(db, order.dish_id, order.quantity, commit=False)` — increments `remaining_quantity` and reactivates `SOLD_OUT → ACTIVE` atomically.
- **`User` (`users`) & `GreenPointsLedger` (`green_points_ledger`) & `Store` (`stores`)**: Updated inside the single `OrderService.verify_and_complete_order` transaction via `GamificationRepository.get_user_by_id`, `GamificationRepository.create_ledger_entry(..., action_type=PointActionType.ORDER_RESCUE, commit=False)`, and `store_repo.get_store_by_id`.

---

## 2. Payment & Order State Transition Matrix

### 2.1 `VNPAY` Order Lifecycle

| Current `(status, payment_status)` | Trigger Event | Allowed? | Resulting `(status, payment_status)` | Side Effects |
| :--- | :--- | :---: | :--- | :--- |
| `(CONFIRMED, PENDING)` | `POST /payments/vnpay/create-url` | Yes | Unchanged `(CONFIRMED, PENDING)` | Returns signed VNPay v2.1.0 URL. |
| `(CONFIRMED, PENDING)` | `POST /orders/{id}/qr` or `POST /orders/verify-qr` | **No (`409`)** | Unchanged | Blocked by `_validate_payment_ready_for_qr`. |
| `(CONFIRMED, PENDING)` | `GET /payments/vnpay/ipn` (`vnp_ResponseCode == "00"`) | Yes | `(CONFIRMED, PAID)` | Saves verified `PaymentTransaction` + VNPay metadata on `Order`. Returns `RspCode: "00"`. |
| `(CONFIRMED, PENDING)` | `GET /payments/vnpay/ipn` (`vnp_ResponseCode != "00"`) | Yes | `(CANCELLED, FAILED)` | Saves failed `PaymentTransaction` + atomically restores `Dish.remaining_quantity`. Returns `RspCode: "00"`. |
| `(CONFIRMED, PAID)` | Duplicate `GET /payments/vnpay/ipn` | Idempotent | Unchanged `(CONFIRMED, PAID)` | Zero mutations; returns `RspCode: "02"`. |
| `(CANCELLED, FAILED)` | Duplicate failed `GET /payments/vnpay/ipn` | Idempotent | Unchanged `(CANCELLED, FAILED)` | Zero mutations, **zero double stock restore**; returns `RspCode: "02"`. |
| `(CONFIRMED, PAID)` | `POST /orders/{id}/qr` | Yes | Unchanged `(CONFIRMED, PAID)` | Issues/returns single-use HMAC-SHA256 QR URI. |
| `(CONFIRMED, PAID)` | `POST /orders/verify-qr` | Yes | `(COMPLETED, PAID)` | Marks QR `is_used=True`, credits Green Points, `GreenPointsLedger`, and `Store.total_co2_saved_kg`. |
| `(CANCELLED/EXPIRED/COMPLETED, any)` | `POST /payments/vnpay/create-url` | **No (`409`/`410`)** | Unchanged | Rejected before generating URL. |

### 2.2 `COD` Order Lifecycle

| Current `(status, payment_status)` | Trigger Event | Allowed? | Resulting `(status, payment_status)` | Side Effects |
| :--- | :--- | :---: | :--- | :--- |
| `(CONFIRMED, PENDING)` | `POST /payments/vnpay/create-url` | **No (`409`)** | Unchanged | Rejected (`payment_method != VNPAY`). |
| `(CONFIRMED, PENDING)` | `POST /orders/{id}/qr` | Yes | Unchanged `(CONFIRMED, PENDING)` | Issues/returns single-use HMAC-SHA256 QR URI. |
| `(CONFIRMED, PENDING)` | `POST /orders/verify-qr` | Yes | `(COMPLETED, PAID)` | Marks QR `is_used=True`, transitions `payment_status = PAID`, credits Green Points, `GreenPointsLedger`, and `Store.total_co2_saved_kg` atomically. |
| `(COMPLETED, PAID)` | Repeat `POST /orders/verify-qr` | **No (`400`/`409`)** | Unchanged | Anti-replay rejects scan; zero duplicate points or CO₂. |

---

## 3. Distributed Lock Keys (`backend/app/core/redis.py`)

| Lock Key Pattern | TTL | Acquired In | Purpose & Degraded Backstop |
| :--- | :---: | :--- | :--- |
| `lock:payment:ipn:{txn_ref}` | `30s` | `PaymentService.process_vnpay_ipn` | Serializes concurrent VNPay IPN deliveries for the same order. Backstop: DB `is_verified` + `Order.payment_status == PENDING` check. |
| `lock:order:redeem:{order_id}` | `5s` | `OrderService.verify_and_complete_order` | Serializes concurrent QR scan attempts on the same order. Backstop: conditional SQL `WHERE is_used = FALSE` & `WHERE status IN ('CONFIRMED', 'READY_FOR_PICKUP')`. |

---

## 4. Backend Pydantic v2 Schemas

### `backend/app/schemas/payment.py`

- **`VNPayCreateUrlRequest`**: `order_id: str`, `bank_code: str | None = None`
- **`VNPayCreateUrlResponse`**: `payment_url: str`, `txn_ref: str`, `vnp_amount: int`
- **`VNPayIPNRequest`**: `vnp_Amount: str`, `vnp_BankCode: str | None`, `vnp_BankTranNo: str | None`, `vnp_CardType: str | None`, `vnp_OrderInfo: str | None`, `vnp_PayDate: str | None`, `vnp_ResponseCode: str`, `vnp_TmnCode: str`, `vnp_TransactionNo: str | None`, `vnp_TransactionType: str | None`, `vnp_TxnRef: str`, `vnp_SecureHash: str`
- **`VNPayIPNResponse`**: `RspCode: str`, `Message: str`
- **`VNPayReturnResponse`**: `is_valid: bool`, `message: str`, `txn_ref: str`

### `backend/app/schemas/order.py` (Relevant F7 Guard Schemas)

- **`OrderResponse`**: includes `id`, `order_code`, `payment_method`, `payment_status`, `status`, `vnpay_transaction_no`, `vnpay_bank_code`, `vnpay_pay_date`, `total_amount`, `co2_saved_kg`, `green_points_earned`, `store_name`, `dish_name`, `pickup_deadline`, `completed_at`.
- **`QRPayloadResponse`**: `order_id`, `order_code`, `qr_payload`, `nonce`, `expires_at`, `is_used`.
- **`QRVerificationRequest`**: `qr_token: str` (accepts alias `qr_payload`).
- **`QRVerificationResponse`**: `success: bool`, `order_id`, `order_code`, `status`, `points_awarded`, `co2_saved_kg`, `message`, `order: OrderResponse | None`.

---

## 5. Frontend TypeScript DTOs (`frontend/src/types/api.ts` & `frontend/src/services/payment.service.ts`)

```ts
export type PaymentMethod = 'VNPAY' | 'COD';
export type PaymentStatus = 'PENDING' | 'PAID' | 'FAILED';

export interface VNPayCreateUrlResponse {
    payment_url: string;
    txn_ref: string;
    vnp_amount?: number;
}

export interface VNPayReturnResponse {
    is_valid: boolean;
    message: string;
    txn_ref: string | null;
}
```
