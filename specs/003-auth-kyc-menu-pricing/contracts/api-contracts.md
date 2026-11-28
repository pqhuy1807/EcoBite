# API Contracts: Auth, Store KYC, Base Menu Catalog, Surplus Dishes & Time-Shift Discounting

**Feature**: `003-auth-kyc-menu-pricing` | **Base Path**: `/api/v1` | **Date**: 2026-11-28

All contracts below are verified directly against `backend/app/api/v1/endpoints/{auth,users,stores,menu,dishes}.py` and `backend/app/schemas/`.

---

## 1. Feature 1A: Authentication & User Profile (`auth.py`, `users.py`)

### 1.1 Register Consumer Account
- **Method & Path**: `POST /api/v1/auth/register`
- **Auth**: Public
- **Request Body (`UserCreate`, `extra="forbid"`)**:
  ```json
  {
    "email": "consumer@ecobite.vn",
    "full_name": "Nguyen Van A",
    "phone": "0901234567",
    "password": "StrongPassword123!"
  }
  ```
- **Response (`201 Created` — `UserResponse`)**:
  ```json
  {
    "id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
    "email": "consumer@ecobite.vn",
    "full_name": "Nguyen Van A",
    "phone": "0901234567",
    "role": "consumer",
    "is_active": true,
    "is_verified": false,
    "green_points_balance": 0,
    "created_at": "2026-11-28T07:30:00Z"
  }
  ```
- **Errors**: `409 Conflict` (`"Email already registered"`), `422 Unprocessable Entity` (password `< 8` chars, invalid email, or forbidden extra fields such as `role`).

### 1.2 Login (Hybrid JSON & OAuth2 Form)
- **Method & Path**: `POST /api/v1/auth/login`
- **Auth**: Public
- **Request**: Accepts `application/json` (`{"email": "...", "password": "..."}`) **or** `application/x-www-form-urlencoded` (`username=...&password=...`).
- **Response (`200 OK` — `Token`)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
      "email": "consumer@ecobite.vn",
      "full_name": "Nguyen Van A",
      "role": "CONSUMER",
      "green_points_balance": 0,
      "created_at": "2026-11-28T07:30:00+00:00"
    }
  }
  ```
- **Errors**: `401 Unauthorized` + `WWW-Authenticate: Bearer` (`"Incorrect email or password"`), `422 Unprocessable Entity` (missing credentials or invalid JSON).

### 1.3 Refresh Access Token
- **Method & Path**: `POST /api/v1/auth/refresh`
- **Auth**: Public (requires valid `refresh_token` with `type == "refresh"` belonging to an active user)
- **Request Body (`RefreshTokenRequest`)**: `{"refresh_token": "<jwt_refresh_token>"}`
- **Response (`200 OK` — `Token`)**: Fresh `access_token`, `refresh_token`, `token_type`, `expires_in`, and `user`.
- **Errors**: `401 Unauthorized` + `WWW-Authenticate: Bearer` (`"Invalid or expired refresh token"` — also returned when token `type != "refresh"` or user is inactive).

### 1.4 Current Authenticated User
- **Method & Path**: `GET /api/v1/users/me`
- **Auth**: Bearer JWT (`CurrentUser`, requires `type == "access"` and `user.is_active == True`)
- **Response (`200 OK` — `UserResponse`)**: Same structure as 1.1.
- **Errors**: `401 Unauthorized` (missing/expired/invalid/refresh token), `403 Forbidden` (`"Inactive user"`).

---

## 2. Feature 1B: Store KYC Onboarding, Self-Lookup & Admin Review (`stores.py`)

### 2.1 Onboard Store (Submit KYC / ATVSTP)
- **Method & Path**: `POST /api/v1/stores/onboard` *(legacy alias: `POST /api/v1/onboard`)*
- **Auth**: `require_roles(UserRole.STORE_PARTNER, UserRole.ADMIN)`
- **Request Body (`StoreOnboardRequest`)**:
  ```json
  {
    "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
    "description": "Chuyên cơm văn phòng và bánh nướng trong ngày",
    "address": "123 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM",
    "latitude": 10.776889,
    "longitude": 106.700806,
    "phone": "02838123456",
    "kyc_license_url": "https://cdn.ecobite.vn/kyc/atvstp_license.pdf"
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
    "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
    "kyc_status": "PENDING",
    "message": "Hồ sơ đối tác đã gửi thành công và đang chờ Quản trị viên duyệt chứng nhận ATVSTP."
  }
  ```
- **Errors**: `400 Bad Request` (blank name/address or out-of-range coordinates), `401`, `403` (`CONSUMER` denied).

### 2.2 Store Partner Self-Lookup (`EC4-02`)
- **Method & Path**: `GET /api/v1/stores/me` *(registered before `/stores/{store_id}`; legacy alias: `GET /api/v1/me`)*
- **Auth**: `require_roles(UserRole.STORE_PARTNER)`
- **Response (`200 OK`)**:
  ```json
  {
    "id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
    "owner_id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
    "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
    "description": "Chuyên cơm văn phòng và bánh nướng trong ngày",
    "address": "123 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM",
    "latitude": 10.776889,
    "longitude": 106.700806,
    "phone": "02838123456",
    "avatar_url": null,
    "kyc_license_url": "https://cdn.ecobite.vn/kyc/atvstp_license.pdf",
    "kyc_status": "PENDING",
    "kyc_reject_reason": null,
    "rating_avg": 5.0,
    "rating_count": 0,
    "total_co2_saved_kg": 0.0,
    "created_at": "2026-11-28T07:35:00+00:00"
  }
  ```
- **Errors**: `401 Unauthorized`, `403 Forbidden` (non-`STORE_PARTNER` or inactive), `404 Not Found` (`"Không tìm thấy cửa hàng của bạn"`).

### 2.3 Store Detail Lookup
- **Method & Path**: `GET /api/v1/stores/{store_id}`
- **Auth**: Public
- **Response (`200 OK`)**: Same serialized store dictionary as 2.2.
- **Errors**: `404 Not Found` (`"Không tìm thấy cửa hàng"`).

### 2.4 Admin List Pending KYC Stores
- **Method & Path**: `GET /api/v1/admin/stores/pending`
- **Auth**: `require_roles(UserRole.ADMIN)`
- **Response (`200 OK`)**: `{"total": 2, "items": [ /* serialized PENDING stores newest first */ ]}`
- **Errors**: `401`, `403` (non-`ADMIN`).

### 2.5 Admin Review Store KYC
- **Method & Path**: `PATCH /api/v1/admin/stores/{store_id}/review`
- **Auth**: `require_roles(UserRole.ADMIN)`
- **Request Body (`StoreKycReview`)**: Accepts `{"decision": "APPROVED" | "REJECTED", "reject_reason": string | null}` (or aliases `kyc_status` / `kyc_reject_reason`).
- **Response (`200 OK`)**:
  ```json
  {
    "store_id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
    "kyc_status": "APPROVED",
    "reject_reason": null,
    "reviewed_at": "2026-11-28T07:40:00+00:00"
  }
  ```
- **Errors**: `401`, `403`, `404 Not Found` (`"Không tìm thấy cửa hàng cần duyệt"`), `422 Unprocessable Entity` (invalid decision value).

---

## 3. Feature 2A: Base Menu Catalog (`menu.py`)

All routes below require `StoreOwner` (`STORE_PARTNER` owning the target store; `401` unauthenticated, `403` non-owner or wrong role, `404` missing store/item).

| Method & Path | Request Payload | Success Response | Key Rules & Errors |
| :--- | :--- | :--- | :--- |
| `POST /api/v1/stores/{store_id}/menu-items` | `MenuItemBase` (`name`, `category`, `original_price > 0`, `image_url`, `description?`, `standard_ingredients[]`, `base_allergens[]`, `dietary_type`) | `201 Created` (`MenuItemResponse`) | Requires `store.kyc_status == APPROVED` (`403` otherwise); `422` on non-positive price or invalid category |
| `GET /api/v1/stores/{store_id}/menu-items` | — | `200 OK` `{"total": int, "items": MenuItemResponse[]}` | Lists only `is_active == True` items, newest first |
| `PUT /api/v1/menu-items/{item_id}` | `MenuItemUpdate` (all fields optional) | `200 OK` (`MenuItemResponse`) | Partial update (`exclude_unset=True`); `403` cross-store; `404` missing |
| `DELETE /api/v1/menu-items/{item_id}` | — | `200 OK` (`MenuItemResponse` with `is_active: false`) | Soft-delete (`is_active = False`); preserves linked historical dishes |

---

## 4. Feature 2B & 3: Surplus Dishes, Batch Publish, Stock Control & Time-Shift Pricing (`dishes.py`)

All routes below require `StoreOwner` (`STORE_PARTNER` owning the referenced store/menu item/dish).

### 4.1 Publish Single Surplus Dish
- **Method & Path**: `POST /api/v1/dishes`
- **Request Body (`DishPublish`)**:
  ```json
  {
    "menu_item_id": "m1a2b3c4-1111-4444-8888-1234567890ab",
    "total_quantity": 5,
    "remaining_quantity": 5,
    "pickup_start_time": "17:00:00",
    "pickup_end_time": "21:00:00",
    "rule_discount_start_time": "20:15:00",
    "override_discounted_price": null,
    "allergens": [
      {
        "allergen": "Eggs (Trứng)",
        "risk_level": "HIGH",
        "source": "EXPLICIT",
        "reason": "Có chả trứng chưng"
      }
    ],
    "dietary_notes": ["Có mỡ hành", "Kèm dưa chua"]
  }
  ```
- **Response (`201 Created` — `DishResponse`)**:
  ```json
  {
    "id": "d7a1b3c9-2222-4444-8888-1234567890ab",
    "store_id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
    "menu_item_id": "m1a2b3c4-1111-4444-8888-1234567890ab",
    "name": "Cơm sườn bì chả",
    "category": "RICE",
    "original_price": "45000.00",
    "rescue_price": "22500.00",
    "rule_discount_price": "13500.00",
    "override_discounted_price": null,
    "current_price": "22500.00",
    "is_rule_discount_active": false,
    "pickup_start_time": "17:00:00",
    "pickup_end_time": "21:00:00",
    "rule_discount_start_time": "20:15:00",
    "total_quantity": 5,
    "remaining_quantity": 5,
    "status": "ACTIVE"
  }
  ```
- **Errors**: `403` (non-owner or store KYC not `APPROVED`), `404` (inactive/missing menu item), `422` (`total_quantity <= 0`, `remaining_quantity > total_quantity`, `pickup_end_time <= pickup_start_time`, `rule_discount_start_time` outside pickup window, `override_discounted_price <= 0` or `> original_price`).

### 4.2 Atomic Batch Publish Surplus Dishes
- **Method & Path**: `POST /api/v1/dishes/batch`
- **Request Body (`DishBatchPublish`)**: Shared `pickup_start_time`, `pickup_end_time`, optional `rule_discount_start_time`, and non-empty `dishes: DishBatchItem[]` (`menu_item_id`, `quantity > 0`, optional `remaining_quantity`, `override_discounted_price`, `allergens`, `dietary_notes`).
- **Response (`201 Created`)**: `{"created_count": int, "dishes": DishResponse[]}`
- **Errors**: `403` (unapproved KYC or non-owner), `404` (any menu item missing/inactive), `422` (empty `dishes`, invalid window, or items spanning multiple stores — rolled back atomically).

### 4.3 List Store Active Surplus Dishes
- **Method & Path**: `GET /api/v1/stores/{store_id}/dishes/active`
- **Response (`200 OK`)**: `{"store_id": "<uuid>", "dishes": DishResponse[]}` (each item serialized with live `current_price` and `is_rule_discount_active`).

### 4.4 Update Surplus Dish Remaining Quantity
- **Method & Path**: `PATCH /api/v1/dishes/{dish_id}/quantity`
- **Request Body (`DishQuantityUpdate`)**: `{"quantity": 0}` (`ge=0`)
- **Response (`200 OK`)**:
  ```json
  {
    "dish_id": "d7a1b3c9-2222-4444-8888-1234567890ab",
    "remaining_quantity": 0,
    "status": "SOLD_OUT",
    "message": "Cập nhật số lượng thành công"
  }
  ```
- **Errors**: `403` (non-owner), `404` (missing dish), `409 Conflict` (concurrent modification), `422` (`quantity < 0` or `quantity > total_quantity`).

---

## 5. Frontend Integration Status & Tracked Contract Deltas

- **Aligned (`[X]`)**: `admin/page.tsx` (`GET /admin/stores/pending`, `PATCH /admin/stores/{id}/review`), `store/menu/page.tsx` (`GET /stores/me`, menu CRUD), `store/dishes/page.tsx` (`GET /stores/me`, `POST /dishes`, `GET active`, `PATCH quantity`), `Navbar.tsx` (role-based links).
- **Pending Alignment (`[ ]` in `tasks.md`)**:
  - `T014`: Update `frontend/src/app/login/page.tsx` to use `authService.login()` and valid routes (`/`, `/store/menu`, `/admin`), and update `frontend/src/app/register/page.tsx` + `RegisterRequest` to omit extra `role`/`workspace_id` fields rejected by `UserCreate(extra="forbid")`.
  - `T019`: Update `frontend/src/app/store/onboard/page.tsx` to call `storeService.onboardStore()` (`POST /api/v1/stores/onboard`) instead of legacy `submitKyc()` (`POST /stores/kyc`).
  - `T024`: Update `FoodCategory` (`'DRINKS'` → `'BEVERAGE'`) and `DishStatus` (`'HIDDEN'` → `'INACTIVE'`) in `frontend/src/types/api.ts` and `frontend/src/app/store/menu/page.tsx`.
