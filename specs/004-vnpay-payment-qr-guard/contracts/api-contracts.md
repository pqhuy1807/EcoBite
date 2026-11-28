# API Contracts: VNPay Cashless Checkout, Idempotent IPN & Payment-QR Reconciliation Guard

**Feature**: `004-vnpay-payment-qr-guard` | **Base Path**: `/api/v1` | **Date**: 2026-11-28

All contracts below are verified against `backend/app/api/v1/endpoints/payments.py`, `backend/app/api/v1/endpoints/orders.py`, `backend/app/api/v1/endpoints/stores.py`, and `frontend/src/services/payment.service.ts`.

---

## 1. Create VNPay Payment URL (`POST /api/v1/payments/vnpay/create-url`)

- **Router Module**: `backend/app/api/v1/endpoints/payments.py` (mounted at `prefix="/payments"`, `tags=["payments"]`)
- **Authorization**:
  - `Authorization: Bearer <jwt_access_token>` (required)
  - Role MUST be `CONSUMER` (target polish: `Depends(require_roles(UserRole.CONSUMER))`)
  - Authenticated user MUST own `order_id` (`order.consumer_id == current_user.id`)
- **Request Parameters (Aligned with `frontend/src/services/payment.service.ts`)**:

| Parameter | Location | Type | Required | Description |
| :--- | :---: | :---: | :---: | :--- |
| `order_id` | Query | `string` (UUID) | Yes | Order UUID created via `POST /api/v1/orders` with `payment_method="VNPAY"`. |
| `bank_code` | Query | `string \| null` | No | Optional VNPay bank/channel code (e.g. `VNPAYQR`, `NCB`, `VNBANK`). |

- **Client IP Resolution (Sandbox Polish)**: Extracted from `X-Forwarded-For` (first hop, trimmed) → `request.client.host` → fallback `"127.0.0.1"`.
- **VNPay v2.1.0 Signing Rules**:
  - Gateway URL from `settings.VNP_URL` (default Sandbox `https://sandbox.vnpayment.vn/paymentv2/vpcpay.html`).
  - `vnp_TxnRef = order.order_code`, `vnp_Amount = str(int(order.total_amount * 100))`, `vnp_CreateDate` in `Asia/Ho_Chi_Minh` (`%Y%m%d%H%M%S`), `vnp_ReturnUrl = settings.VNP_RETURN_URL`.
  - Sorted non-empty parameters hashed with HMAC-SHA512 using `urllib.parse.quote_plus(str(value))` and `settings.VNP_HASH_SECRET`.

### Success Response — `200 OK` (`VNPayCreateUrlResponse`)

```json
{
  "payment_url": "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_Amount=2200000&vnp_Command=pay&vnp_CreateDate=20261128140500&vnp_CurrCode=VND&vnp_IpAddr=127.0.0.1&vnp_Locale=vn&vnp_OrderInfo=Thanh+toan+don+hang+EB-20261128-A1B2C3D4&vnp_OrderType=food_rescue&vnp_ReturnUrl=http%3A%2F%2Flocalhost%3A3000%2Forders%2Fvnpay-return&vnp_TmnCode=TESTCODE&vnp_TxnRef=EB-20261128-A1B2C3D4&vnp_Version=2.1.0&vnp_SecureHash=7f6a...",
  "txn_ref": "EB-20261128-A1B2C3D4",
  "vnp_amount": 2200000
}
```

### Error Responses

| HTTP Status | Trigger Condition | Example `detail` |
| :---: | :--- | :--- |
| `401 Unauthorized` | Missing, expired, or invalid JWT | `"Could not validate credentials"` |
| `403 Forbidden` | Role is not `CONSUMER` or order belongs to another user | `"The user does not have the required role"` / `"Bạn không có quyền thanh toán đơn hàng này"` |
| `404 Not Found` | `order_id` does not exist | `"Order not found"` |
| `409 Conflict` | `order.payment_method != VNPAY` or `order.payment_status != PENDING` | `"Chỉ đơn hàng thanh toán VNPay mới có thể tạo URL thanh toán"` / `"Đơn hàng đã được thanh toán hoặc có giao dịch thanh toán trước đó"` |
| `410 Gone` | Order is `CANCELLED`, `EXPIRED`, or `COMPLETED` | `"Đơn hàng không còn hiệu lực để thanh toán"` |

---

## 2. VNPay Server-to-Server IPN Webhook (`GET /api/v1/payments/vnpay/ipn`)

- **Router Module**: `backend/app/api/v1/endpoints/payments.py`
- **Authorization**: Public webhook authenticated strictly by HMAC-SHA512 (`vnp_SecureHash` compared via `hmac.compare_digest` after stripping `vnp_SecureHash` and `vnp_SecureHashType`).
- **Query Parameters**: Standard VNPay v2.1.0 IPN callback parameters (`vnp_TxnRef`, `vnp_Amount`, `vnp_ResponseCode`, `vnp_TmnCode`, `vnp_TransactionNo`, `vnp_BankCode`, `vnp_PayDate`, `vnp_OrderInfo`, `vnp_TransactionStatus`, `vnp_SecureHash`, optional `vnp_SecureHashType`).

### Response — `200 OK` (`VNPayIPNResponse` — Always HTTP 200 per VNPay IPN Spec)

```json
{
  "RspCode": "00",
  "Message": "Success"
}
```

### VNPay `RspCode` Contract Matrix

| `RspCode` | Condition | Database Effect |
| :---: | :--- | :--- |
| `"00"` | Valid signature & amount; `vnp_ResponseCode == "00"` | Sets `Order.payment_status = PAID`, stores VNPay metadata, creates verified `PaymentTransaction`. |
| `"00"` | Valid signature & amount; `vnp_ResponseCode != "00"` on `PENDING` order | Creates failed `PaymentTransaction`, sets `Order.payment_status = FAILED` & `Order.status = CANCELLED`, atomically restores dish stock (`atomic_increment_quantity`). |
| `"01"` | Missing `vnp_TxnRef` or order not found *(polish aligns unknown order from legacy `"09"` to `"01"`)* | None. |
| `"02"` | Duplicate IPN: verified transaction already exists, or `Order.payment_status != PENDING` (already `PAID` or `FAILED`/`CANCELLED`) | None (strictly idempotent; zero double payment or double stock restore). |
| `"04"` | Missing `vnp_Amount` or `Decimal(vnp_Amount) / 100 != order.total_amount` | None. |
| `"97"` | Missing or invalid HMAC-SHA512 `vnp_SecureHash` | None. |

---

## 3. VNPay Return URL Stateless Verification (`GET /api/v1/payments/vnpay/return`)

- **Router Module**: `backend/app/api/v1/endpoints/payments.py`
- **Authorization**: Public (stateless HMAC-SHA512 check; performs **zero** DB reads or writes).
- **Query Parameters**: Full raw query string forwarded by `frontend/src/app/orders/vnpay-return/page.tsx` from VNPay's browser redirect.

### Response — `200 OK` (`VNPayReturnResponse`)

```json
{
  "is_valid": true,
  "message": "Signature verified",
  "txn_ref": "EB-20261128-A1B2C3D4"
}
```

Invalid/missing signature returns `200 OK` with `{"is_valid": false, "message": "Invalid signature", "txn_ref": "EB-..."}` (or `"Missing transaction reference"` with `txn_ref: ""`).

---

## 4. Guarded Pickup QR Issuance (`POST /api/v1/orders/{order_id}/qr`)

- **Router Module**: `backend/app/api/v1/endpoints/orders.py`
- **Authorization**: `Depends(require_roles(UserRole.CONSUMER))` + order owner (`order.consumer_id == current_user.id`).
- **Payment ↔ QR Guard (F7 Extension)**:
  - `VNPAY` + `PENDING` or `FAILED` → **`409 Conflict`**: `{"detail": "Đơn hàng VNPAY chưa hoàn tất thanh toán"}`.
  - `VNPAY` + `PAID` or `COD` + `PENDING` (active order before `pickup_deadline`) → **`200 OK`** (`QRPayloadResponse`):
    ```json
    {
      "order_id": "8b7e2c14-...",
      "order_code": "EB-20261128-A1B2C3D4",
      "qr_payload": "ecobite://pickup?order_id=...&user_id=...&nonce=...&expires_at=...&sig=...",
      "nonce": "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d",
      "expires_at": "2026-11-28T15:00:00Z",
      "is_used": false
    }
    ```

---

## 5. Guarded In-Store QR Verification & COD Settlement (`POST /api/v1/orders/verify-qr`)

- **Router Module**: `backend/app/api/v1/endpoints/orders.py`
- **Authorization**: `Depends(require_roles(UserRole.STORE_PARTNER))` + owning store (`order.store.owner_id == current_user.id`).
- **Request Body (`QRVerificationRequest`)**:
  ```json
  {
    "qr_token": "ecobite://pickup?order_id=...&user_id=...&nonce=...&expires_at=...&sig=..."
  }
  ```
- **Payment ↔ QR Guard & Atomic Settlement**:
  - `VNPAY` + `payment_status != PAID` → **`409 Conflict`**: `{"detail": "Đơn hàng VNPAY chưa hoàn tất thanh toán"}` (token stays unused, order stays `CONFIRMED`, zero points awarded).
  - Valid `PAID` `VNPAY` or `COD` → **`200 OK`** (`QRVerificationResponse`, SLA `< 2.0s`):
    ```json
    {
      "success": true,
      "order_id": "8b7e2c14-...",
      "order_code": "EB-20261128-A1B2C3D4",
      "status": "COMPLETED",
      "points_awarded": 50,
      "co2_saved_kg": "5.00",
      "message": "Xác thực chữ ký hợp lệ! Đã giao món ăn thành công và cộng điểm xanh cho khách.",
      "order": {
        "id": "8b7e2c14-...",
        "payment_method": "COD",
        "payment_status": "PAID",
        "status": "COMPLETED"
      }
    }
    ```
  - Replay attempt (`is_used == True`) → **`400 Bad Request`**: `{"detail": "Mã QR đã được sử dụng trước đó!"}` (zero duplicate points/CO₂).

---

## 6. Store Orders Queue Endpoints (Consumed by `/store/verify-qr`)

- **`GET /api/v1/stores/me`** (`STORE_PARTNER`): resolves the authenticated partner's `store.id`.
- **`GET /api/v1/orders/store/{store_id}`** (`StoreOwner` dependency; optional query params `status=CONFIRMED|READY_FOR_PICKUP|COMPLETED`, `skip=0`, `limit=20`): returns `list[OrderResponse]` including `order_code`, `dish_name`, `quantity`, `total_amount`, `payment_method`, `payment_status`, `status`, and `pickup_deadline` for display alongside the QR scanner at `/store/verify-qr`.
