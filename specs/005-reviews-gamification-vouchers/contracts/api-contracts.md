# API Contracts: Verified Reviews, Green Points Wallet & Atomic Vouchers (Feature 8)

**Feature**: `005-reviews-gamification-vouchers` | **Base Path**: `/api/v1` | **Date**: 2026-11-28

> **Route Precedence Note (`backend/app/api/v1/router.py` & `endpoints/gamification.py`)**:
> 1. `gamification.router` is registered **before** `stores.router` so static `/green-points/*` and `/vouchers*` paths are never intercepted by the legacy root-level wildcard `GET /{store_id}`.
> 2. Static `GET /vouchers/me` is declared **before** parameterized `POST /vouchers/{voucher_id}/redeem`.

---

## Part A — Verified Reviews (Feature 8A · `backend/app/api/v1/endpoints/reviews.py`)

### 1. Submit a Verified Review for a Completed Order

- **Method & Path**: `POST /api/v1/orders/{order_id}/review`
- **Authorization**: `Authorization: Bearer <jwt_access_token>` · Role MUST be `CONSUMER` (`Depends(require_roles(UserRole.CONSUMER))`) · Consumer MUST own `order_id` · Order status MUST be `COMPLETED`
- **Content-Type**: `application/json`

#### Path Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `order_id` | `UUID` | Yes | Primary key UUID of the `COMPLETED` order being reviewed |

#### Request Body (`ReviewCreate`)
```json
{
  "rating": 5,
  "comment": "Cơm sườn mềm thơm, còn nóng hổi, chả rất ngon!",
  "tags": ["Tươi ngon", "Đóng gói kỹ", "Đúng giờ"],
  "photo_urls": ["https://cdn.ecobite.vn/reviews/com_suon_real.jpg"]
}
```
- `rating`: integer, required, `1 <= rating <= 5`.
- `comment`: string or `null`, optional.
- `tags`: array of strings, optional (default `[]`).
- `photo_urls`: array of strings, optional (default `[]`).
- `order_id`: optional UUID in body (ignored in favor of URL path `order_id`).

#### Success Response — `201 Created` (`ReviewResponse`)
```json
{
  "id": "9f1a2b3c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "order_id": "8b7e2c14-1111-4444-8888-1234567890ab",
  "consumer_id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
  "store_id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
  "dish_id": "d7a1b3c9-2222-4444-8888-1234567890ab",
  "rating": 5,
  "comment": "Cơm sườn mềm thơm, còn nóng hổi, chả rất ngon!",
  "tags": ["Tươi ngon", "Đóng gói kỹ", "Đúng giờ"],
  "photo_urls": ["https://cdn.ecobite.vn/reviews/com_suon_real.jpg"],
  "created_at": "2026-11-21T14:30:00Z"
}
```
**Transactional Side Effect**: Recalculates and updates `stores.rating_avg` (rounded to 2 decimal places) and `stores.rating_count` in the same DB transaction.

#### Error Responses
| HTTP Status | Trigger Condition | Exact `detail` Response |
| :---: | :--- | :--- |
| `401 Unauthorized` | Missing, expired, or invalid JWT Bearer token | `"Could not validate credentials"` |
| `403 Forbidden` | Authenticated role is not `CONSUMER` (router RBAC / service guard) | `"Not enough permissions"` / `"Chỉ người tiêu dùng (CONSUMER) mới có quyền đánh giá đơn hàng"` |
| `403 Forbidden` | Consumer does not own the order | `"Bạn không có quyền đánh giá đơn hàng này"` |
| `404 Not Found` | `order_id` does not exist | `"Order not found"` |
| `409 Conflict` | Order status is not `COMPLETED` (e.g., `CONFIRMED`, `CANCELLED`) | `"Chỉ đơn hàng ở trạng thái COMPLETED mới có thể đánh giá (trạng thái hiện tại: <STATUS>)"` |
| `409 Conflict` | Order has already been reviewed (pre-check or DB `UNIQUE` `IntegrityError`) | `"Đơn hàng đã được đánh giá trước đó"` |
| `422 Unprocessable Entity` | Invalid UUID or `rating` outside `1..5` | FastAPI/Pydantic validation detail array |

---

### 2. List Verified Reviews for a Store (Paginated)

- **Method & Path**: `GET /api/v1/stores/{store_id}/reviews`
- **Authorization**: Public (no token required)

#### Path & Query Parameters
| Parameter | In | Type | Default | Constraints |
| :--- | :---: | :--- | :---: | :--- |
| `store_id` | path | `UUID` | — | Target store UUID |
| `skip` | query | `int` | `0` | `>= 0` |
| `limit` | query | `int` | `20` | `1 <= limit <= 100` |

#### Success Response — `200 OK` (`list[ReviewResponse]`)
Returns verified reviews ordered **newest first** (`created_at DESC`), or `[]` if the store has no reviews.
```json
[
  {
    "id": "9f1a2b3c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
    "order_id": "8b7e2c14-1111-4444-8888-1234567890ab",
    "consumer_id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
    "store_id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
    "dish_id": "d7a1b3c9-2222-4444-8888-1234567890ab",
    "rating": 5,
    "comment": "Cơm sườn mềm thơm, còn nóng hổi, chả rất ngon!",
    "tags": ["Tươi ngon", "Đóng gói kỹ", "Đúng giờ"],
    "photo_urls": ["https://cdn.ecobite.vn/reviews/com_suon_real.jpg"],
    "created_at": "2026-11-21T14:30:00Z"
  }
]
```

---

## Part B — Green Points Wallet, CO₂ Impact & Vouchers (Feature 8B · `backend/app/api/v1/endpoints/gamification.py`)

### 3. Get Current Consumer's Green Points Summary & CO₂ Impact

- **Method & Path**: `GET /api/v1/green-points/me`
- **Authorization**: `Authorization: Bearer <jwt_access_token>` · Role MUST be `CONSUMER`

#### Query Parameters
| Parameter | Type | Default | Constraints | Description |
| :--- | :--- | :---: | :--- | :--- |
| `limit` | `int` | `20` | `1 <= limit <= 100` | Maximum recent ledger entries returned |

#### Success Response — `200 OK` (`GreenPointsSummaryResponse`)
```json
{
  "balance_points": 350,
  "total_co2_saved_kg": "17.50",
  "total_meals_saved": 7,
  "rank_title": "Chiến Binh Xanh (Eco Hero)",
  "recent_ledger": [
    {
      "id": "c1d2e3f4-5678-4abc-9def-0123456789ab",
      "user_id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
      "order_id": "8b7e2c14-1111-4444-8888-1234567890ab",
      "points_change": 350,
      "balance_after": 350,
      "action_type": "ORDER_RESCUE",
      "co2_saved_kg": "17.50",
      "note": "Cộng 350 Điểm Xanh giải cứu 7 suất Cơm Sườn Bì Chả",
      "created_at": "2026-11-20T14:30:00Z"
    }
  ]
}
```

#### Error Responses
| HTTP Status | Trigger Condition | Example `detail` |
| :---: | :--- | :--- |
| `401 Unauthorized` | Missing, expired, or invalid JWT token | `"Could not validate credentials"` |
| `403 Forbidden` | Authenticated role is not `CONSUMER` | `"Not enough permissions"` |
| `404 Not Found` | User record missing in DB | `"Không tìm thấy người dùng"` |
| `422 Unprocessable Entity` | `limit` outside `1..100` | Validation detail array |

---

### 4. List Active, Unexpired Vouchers (Public Catalog)

- **Method & Path**: `GET /api/v1/vouchers`
- **Authorization**: Public (no token required)

#### Success Response — `200 OK` (`list[VoucherResponse]`)
Filters strictly `is_active == True` and `expires_at > now (UTC)`, sorted by `points_required ASC, created_at DESC`.
```json
[
  {
    "id": "11111111-2222-4333-8444-555555555555",
    "code": "ECOBITE10K",
    "title": "Voucher Giải Cứu Xanh 10.000đ",
    "description": "Giảm ngay 10.000đ cho đơn món giải cứu từ 30.000đ",
    "discount_amount": "10000.00",
    "points_required": 100,
    "min_order_amount": "30000.00",
    "expires_at": "2027-01-27T14:00:00Z",
    "is_active": true,
    "created_at": "2026-11-21T14:00:00Z"
  }
]
```

---

### 5. List Current Consumer's Claimed Vouchers

- **Method & Path**: `GET /api/v1/vouchers/me`
- **Authorization**: `Authorization: Bearer <jwt_access_token>` · Role MUST be `CONSUMER`

#### Query Parameters
| Parameter | Type | Default | Constraints |
| :--- | :--- | :---: | :--- |
| `skip` | `int` | `0` | `>= 0` |
| `limit` | `int` | `20` | `1 <= limit <= 100` |

#### Success Response — `200 OK` (`list[UserVoucherResponse]`)
Ordered newest first (`claimed_at DESC, id DESC`), embedding catalog `voucher` details.
```json
[
  {
    "id": "77777777-8888-4999-8aaa-bbbbbbbbbbbb",
    "user_id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
    "voucher_id": "11111111-2222-4333-8444-555555555555",
    "is_used": false,
    "used_at": null,
    "claimed_at": "2026-11-21T14:35:00Z",
    "voucher": {
      "id": "11111111-2222-4333-8444-555555555555",
      "code": "ECOBITE10K",
      "title": "Voucher Giải Cứu Xanh 10.000đ",
      "description": "Giảm ngay 10.000đ cho đơn món giải cứu từ 30.000đ",
      "discount_amount": "10000.00",
      "points_required": 100,
      "min_order_amount": "30000.00",
      "expires_at": "2027-01-27T14:00:00Z",
      "is_active": true,
      "created_at": "2026-11-21T14:00:00Z"
    }
  }
]
```

#### Error Responses
| HTTP Status | Trigger Condition | Example `detail` |
| :---: | :--- | :--- |
| `401 Unauthorized` | Missing or invalid JWT token | `"Could not validate credentials"` |
| `403 Forbidden` | Authenticated role is not `CONSUMER` | `"Not enough permissions"` |
| `422 Unprocessable Entity` | `skip < 0` or `limit` outside `1..100` | Validation detail array |

---

### 6. Atomically Redeem Green Points for a Voucher

- **Method & Path**: `POST /api/v1/vouchers/{voucher_id}/redeem`
- **Authorization**: `Authorization: Bearer <jwt_access_token>` · Role MUST be `CONSUMER`
- **Request Body**: None (empty body)

#### Path Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `voucher_id` | `UUID` | Yes | Primary key UUID of the catalog `Voucher` to redeem |

#### Success Response — `200 OK` (`VoucherRedeemResponse`)
```json
{
  "user_voucher_id": "77777777-8888-4999-8aaa-bbbbbbbbbbbb",
  "voucher_id": "11111111-2222-4333-8444-555555555555",
  "voucher_code": "ECOBITE10K",
  "title": "Voucher Giải Cứu Xanh 10.000đ",
  "discount_amount": "10000.00",
  "points_deducted": 100,
  "remaining_balance": 150,
  "claimed_at": "2026-11-21T14:35:00Z"
}
```
**Transactional Guarantees**:
1. Wrapped in user-scoped `distributed_lock(f"lock:green_points:user:{user_id}")` (degrades gracefully if Redis offline).
2. Executes atomic conditional SQL `UPDATE users SET green_points_balance = green_points_balance - :cost WHERE id = :user_id AND green_points_balance >= :cost RETURNING green_points_balance`.
3. Inserts negative `GreenPointsLedger` (`action_type = "VOUCHER_REDEEM"`, `points_change = -points_required`, `balance_after = remaining_balance`, `co2_saved_kg = 0.00`).
4. Inserts `UserVoucher(user_id, voucher_id, is_used=False)` and commits all three in one transaction (full rollback on failure).

#### Error Responses
| HTTP Status | Trigger Condition | Exact `detail` Response |
| :---: | :--- | :--- |
| `400 Bad Request` | Voucher `is_active == False` | `"Voucher hiện không còn hoạt động"` |
| `400 Bad Request` | Voucher `expires_at <= now (UTC)` | `"Voucher đã hết hạn sử dụng"` |
| `401 Unauthorized` | Missing, expired, or invalid JWT token | `"Could not validate credentials"` |
| `403 Forbidden` | Authenticated role is not `CONSUMER` | `"Not enough permissions"` |
| `404 Not Found` | `voucher_id` not found (or user not found) | `"Không tìm thấy voucher"` / `"Không tìm thấy người dùng"` |
| `409 Conflict` | Insufficient Green Points (including concurrent double-redeem race) | `"Không đủ Điểm Xanh để đổi voucher này"` |

---

## Part C — Frontend Service Layer Mapping (`EC4-13`)

| Frontend Service & Method | HTTP Call | Request / Response Type | React Query Key / Invalidation |
| :--- | :--- | :--- | :--- |
| `reviewService.createReview(orderId, payload)` | `POST /orders/${orderId}/review` | `ReviewCreatePayload` → `ReviewResponse` | Invalidates `['my-orders']`, `['store-reviews', storeId]` |
| `reviewService.getStoreReviews(storeId, skip?, limit?)` | `GET /stores/${storeId}/reviews` | Query params → `ReviewResponse[]` | `['store-reviews', storeId, skip, limit]` |
| `gamificationService.getMyGreenPoints(limit?)` | `GET /green-points/me` | Query params → `GreenPointsSummaryResponse` | `['green-points-me']` |
| `gamificationService.listVouchers()` | `GET /vouchers` | — → `VoucherResponse[]` | `['vouchers-available']` |
| `gamificationService.getMyVouchers(skip?, limit?)` | `GET /vouchers/me` | Query params → `UserVoucherResponse[]` | `['vouchers-me']` |
| `gamificationService.redeemVoucher(voucherId)` | `POST /vouchers/${voucherId}/redeem` | — → `VoucherRedeemResponse` | Invalidates `['green-points-me']`, `['vouchers-me']`, `['vouchers-available']` |
