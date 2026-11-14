# Data Model: Consumer Surplus Discovery, Anti-Overselling Order & Dynamic QR Pickup

**Feature**: `001-rescue-discovery-order-qr`
**Date**: 2026-11-14

All entities already exist in `backend/app/models/` and are migrated via Alembic. No breaking schema migrations are required.

## Core Entities & Relationships

### 1. User (`backend/app/models/user.py`)
- **Fields**: `id (UUID PK)`, `email (unique)`, `hashed_password`, `full_name`, `phone`, `role (CONSUMER | STORE_PARTNER | ADMIN)`, `green_points_balance (int)`, `is_active`, `is_verified`
- **Relationships**: Owns `Store` (1-to-many), places `Order` (1-to-many).

### 2. Store (`backend/app/models/store.py`)
- **Fields**: `id (UUID PK)`, `owner_id (FK -> users.id)`, `name`, `address`, `location (Geometry POINT SRID 4326 / WKT fallback)`, `kyc_status (PENDING | APPROVED | REJECTED)`, `rating_avg`, `total_co2_saved_kg`
- **Validation**: Only `APPROVED` stores appear in `GET /stores/nearby`.

### 3. Dish (`backend/app/models/dish.py`)
- **Fields**: `id (UUID PK)`, `store_id (FK -> stores.id)`, `menu_item_id`, `name`, `category (ItemCategory)`, `original_price`, `rescue_price`, `rule_discount_price`, `override_discounted_price`, `pickup_start_time (TIME)`, `pickup_end_time (TIME)`, `rule_discount_start_time (TIME)`, `total_quantity`, `remaining_quantity`, `status (ACTIVE | SOLD_OUT | EXPIRED | INACTIVE)`, `estimated_co2_kg_per_dish (Decimal, default 2.50)`
- **State Transitions**:
  - `ACTIVE -> SOLD_OUT` automatically when `atomic_decrement_quantity` reduces `remaining_quantity` to `0`.
  - `SOLD_OUT -> ACTIVE` automatically when `atomic_increment_quantity` restores stock on cancellation.

### 4. Order (`backend/app/models/order.py`)
- **Fields**: `id (UUID PK)`, `order_code (unique, EB-YYYYMMDD-XXXXXXXX)`, `consumer_id (FK -> users.id)`, `store_id (FK -> stores.id)`, `dish_id (FK -> dishes.id)`, `quantity (> 0)`, `unit_price`, `total_amount`, `payment_method (VNPAY | COD)`, `payment_status`, `status (CONFIRMED | READY_FOR_PICKUP | COMPLETED | CANCELLED | EXPIRED)`, `co2_saved_kg`, `green_points_earned`, `pickup_deadline (DateTime UTC)`, `completed_at`
- **State Transitions**:
  - Initial: `CONFIRMED`
  - Cancel (`PATCH /orders/{id}/cancel` before `pickup_deadline`): `CONFIRMED | READY_FOR_PICKUP -> CANCELLED` (atomically restores dish `remaining_quantity`).
  - Redeem (`POST /orders/verify-qr`): `CONFIRMED | READY_FOR_PICKUP -> COMPLETED` (sets `completed_at`).

### 5. QRToken (`backend/app/models/order.py`)
- **Fields**: `id (UUID PK)`, `order_id (FK -> orders.id, unique)`, `token_hash (HMAC-SHA256 hex)`, `nonce (32-char hex)`, `expires_at (DateTime UTC)`, `is_used (bool)`, `used_at (DateTime UTC | None)`
- **Canonical Payload Format**: `ecobite://pickup?order_id=<uuid>&user_id=<uuid>&nonce=<hex>&expires_at=<isoZ>&sig=<hmac_hex>`
- **Invariant**: Atomic redemption `UPDATE qr_tokens SET is_used = TRUE, used_at = :now WHERE id = :id AND is_used = FALSE` prevents replay attacks.
