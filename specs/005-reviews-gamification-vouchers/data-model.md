# Data Model: Verified Reviews, Green Points Wallet, CO₂ Impact & Vouchers (Feature 8)

**Feature**: `005-reviews-gamification-vouchers` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

All persistent tables and aggregate columns for Feature 8 are already defined in the initial 12-table migration (`backend/alembic/versions/8793a9fe3601_initial_schema_ecobite_12_tables.py`) and ORM models (`backend/app/models/{interaction,gamification,user,store}.py`). **No new Alembic migrations are required.**

---

## 1. Persistent ORM Entities

### 1.1 `reviews` (`backend/app/models/interaction.py` → `Review`)
Stores 1-to-1 verified customer feedback for `COMPLETED` food-rescue orders.

| Column | SQLAlchemy Type | Constraints & Indexes | Notes |
| :--- | :--- | :--- | :--- |
| `id` | `Uuid` | PK, indexed, `default=uuid.uuid4` | Primary identifier |
| `order_id` | `Uuid` | FK → `orders.id` (`ON DELETE CASCADE`), **`UNIQUE`**, `NOT NULL`, indexed | Database-level anti-duplication invariant (1 review per order) |
| `consumer_id` | `Uuid` | FK → `users.id` (`ON DELETE CASCADE`), `NOT NULL`, indexed | Author (`UserRole.CONSUMER`, must match `order.consumer_id`) |
| `store_id` | `Uuid` | FK → `stores.id` (`ON DELETE CASCADE`), `NOT NULL`, indexed | Reviewed store (`order.store_id`) |
| `dish_id` | `Uuid` | FK → `dishes.id` (`ON DELETE CASCADE`), `NOT NULL`, indexed | Reviewed surplus dish (`order.dish_id`) |
| `rating` | `Integer` | `NOT NULL`, **`CHECK (rating >= 1 AND rating <= 5)`** (`ck_reviews_rating_range_1_to_5`) | 1 to 5 stars |
| `comment` | `Text` | Nullable | Optional detailed review text |
| `tags` | `JSON_TYPE` (`JSONB`/`JSON`) | `NOT NULL`, `default=list` | Quick tags, e.g., `["Ngon", "Đúng giờ", "Đóng gói kỹ"]` |
| `photo_urls` | `JSON_TYPE` (`JSONB`/`JSON`) | `NOT NULL`, `default=list` | Optional attached photo URLs |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL`, `server_default=func.now()` | Used for newest-first sorting (`created_at DESC`) |

### 1.2 `green_points_ledger` (`backend/app/models/gamification.py` → `GreenPointsLedger`)
Immutable audit log of all Green Points credits and debits.

**Enum `PointActionType(StrEnum)`**: `"ORDER_RESCUE"` | `"VOUCHER_REDEEM"` | `"SYSTEM_BONUS"`

| Column | SQLAlchemy Type | Constraints & Indexes | Notes |
| :--- | :--- | :--- | :--- |
| `id` | `Uuid` | PK, indexed, `default=uuid.uuid4` | Tie-breaker in newest-first ordering |
| `user_id` | `Uuid` | FK → `users.id` (`ON DELETE CASCADE`), `NOT NULL`, indexed | Wallet owner |
| `order_id` | `Uuid` | FK → `orders.id` (`ON DELETE SET NULL`), Nullable, indexed | Linked order for `ORDER_RESCUE`; `NULL` for `VOUCHER_REDEEM` / `SYSTEM_BONUS` |
| `points_change` | `Integer` | `NOT NULL` | Positive (`+50`) for earnings, negative (`-100`) for voucher redemption |
| `balance_after` | `Integer` | `NOT NULL` | Authoritative point balance immediately after mutation |
| `action_type` | `Enum(PointActionType, native_enum=False, length=30)` | `NOT NULL` | `"ORDER_RESCUE"`, `"VOUCHER_REDEEM"`, or `"SYSTEM_BONUS"` |
| `co2_saved_kg` | `Numeric(8, 2)` | `NOT NULL`, `default=Decimal("0.0")` | CO₂ credited on rescue; `0.00` on redemption/bonus |
| `note` | `String(255)` | Nullable | Human-readable Vietnamese audit description |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL`, `server_default=func.now()` | Primary sort key (`created_at DESC, id DESC`) |

### 1.3 `vouchers` (`backend/app/models/gamification.py` → `Voucher`)
Catalog of discount vouchers redeemable with Green Points.

| Column | SQLAlchemy Type | Constraints & Indexes | Notes |
| :--- | :--- | :--- | :--- |
| `id` | `Uuid` | PK, indexed, `default=uuid.uuid4` | Catalog voucher UUID |
| `code` | `String(50)` | **`UNIQUE`**, `NOT NULL`, indexed | Unique promotional code (e.g., `ECOBITE10K`) |
| `title` | `String(255)` | `NOT NULL` | Display title |
| `description` | `Text` | Nullable | Redemption terms & conditions |
| `discount_amount` | `Numeric(12, 2)` | `NOT NULL` | VND discount value (strictly `> 0`) |
| `points_required` | `Integer` | `NOT NULL` | Green Points cost (strictly `> 0`) |
| `min_order_amount` | `Numeric(12, 2)` | `NOT NULL`, `default=Decimal("0.0")` | Minimum order total required to apply |
| `expires_at` | `DateTime(timezone=True)` | `NOT NULL` | Active catalog filters strictly `expires_at > now` (UTC) |
| `is_active` | `Boolean` | `NOT NULL`, `default=True` | Administrative availability flag |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL`, `server_default=func.now()` | Secondary sort key on catalog |

### 1.4 `user_vouchers` (`backend/app/models/gamification.py` → `UserVoucher`)
Ownership records of vouchers redeemed by individual Consumers.

| Column | SQLAlchemy Type | Constraints & Indexes | Notes |
| :--- | :--- | :--- | :--- |
| `id` | `Uuid` | PK, indexed, `default=uuid.uuid4` | Claimed voucher UUID (`user_voucher_id`) |
| `user_id` | `Uuid` | FK → `users.id` (`ON DELETE CASCADE`), `NOT NULL`, indexed | Consumer who redeemed the voucher |
| `voucher_id` | `Uuid` | FK → `vouchers.id` (`ON DELETE CASCADE`), `NOT NULL`, indexed | Catalog `Voucher` reference (eager-loaded via `selectinload`) |
| `is_used` | `Boolean` | `NOT NULL`, `default=False` | Set `False` on redemption; reserved for future checkout application |
| `used_at` | `DateTime(timezone=True)` | Nullable | Timestamp when applied to an order |
| `claimed_at` | `DateTime(timezone=True)` | `NOT NULL`, `server_default=func.now()` | Redemption timestamp (`claimed_at DESC, id DESC`) |

### 1.5 Related Columns on Existing Tables (`users`, `stores`, `orders`)
- **`users.green_points_balance`** (`Integer`, `NOT NULL`, `default=0`): Incremented atomically during QR pickup completion (`OrderService.verify_and_complete_order`) and decremented atomically via `WHERE id = :user_id AND green_points_balance >= :point_cost RETURNING green_points_balance` during voucher redemption.
- **`stores.rating_avg`** (`Numeric(3, 2)`, `NOT NULL`, `default=Decimal("5.0")`) and **`stores.rating_count`** (`Integer`, `NOT NULL`, `default=0`): Recomputed via SQL `COUNT`/`AVG` inside `ReviewRepository.update_store_rating` in the same transaction as `Review` creation.
- **`stores.total_co2_saved_kg`** (`Numeric(10, 2)`, `NOT NULL`, `default=Decimal("0.0")`): Incremented during QR pickup completion.
- **`orders`** (`consumer_id`, `store_id`, `dish_id`, `status`, `quantity`, `co2_saved_kg`, `green_points_earned`): Authoritative source for `ReviewService` eligibility (`status == COMPLETED`) and `GamificationRepository.get_completed_rescue_stats` (`SUM(co2_saved_kg)`, `SUM(quantity)` where `status == COMPLETED`).

---

## 2. Deterministic Rule-Based Eco Rank Model

Defined in `backend/app/services/gamification_service.py`:

$$\text{effective\_score} = \max\Big(\text{balance\_points},\ \lfloor \max(\text{total\_co2\_saved\_kg}, 0) \times 20 \rfloor,\ 0\Big)$$

*(1 rescued meal = `2.5 kg CO₂` = `50 Green Points` → factor `20` points per kg CO₂; ensures spending points on vouchers never demotes a Consumer's earned Eco Rank.)*

| Effective Score Threshold | Equivalent Rescued CO₂ | `rank_title` (Exact String) |
| :---: | :---: | :--- |
| `>= 1000` | `>= 50.00 kg` (20+ meals) | `"Đại Sứ Xanh (Eco Ambassador)"` |
| `300 – 999` | `15.00 – 49.99 kg` (6–19 meals) | `"Chiến Binh Xanh (Eco Hero)"` |
| `100 – 299` | `5.00 – 14.99 kg` (2–5 meals) | `"Người Giải Cứu (Food Rescuer)"` |
| `0 – 99` | `0.00 – 4.99 kg` (0–1 meal) | `"Mầm Xanh (Eco Seedling)"` |

---

## 3. Backend Pydantic v2 Schemas (Implemented)

### `backend/app/schemas/interaction.py`
- **`ReviewCreate`**: `rating: int` (`ge=1, le=5`), `comment: str | None = None`, `tags: list[str] = []`, `photo_urls: list[str] = []`, `order_id: UUID | None = None` *(optional because `order_id` is passed via URL path)*.
- **`ReviewResponse`**: `id`, `order_id`, `consumer_id`, `store_id`, `dish_id`, `rating`, `comment`, `tags`, `photo_urls`, `created_at` (`from_attributes=True`).

### `backend/app/schemas/gamification.py`
- **`GreenPointsLedgerResponse`**: `id`, `user_id`, `order_id: UUID | None`, `points_change: int`, `balance_after: int`, `action_type: PointActionType`, `co2_saved_kg: Decimal`, `note: str | None`, `created_at: datetime`.
- **`GreenPointsSummaryResponse`**: `balance_points: int` (`ge=0`), `total_co2_saved_kg: Decimal` (`ge=0.0`), `total_meals_saved: int` (`ge=0`), `rank_title: str`, `recent_ledger: list[GreenPointsLedgerResponse]`.
- **`VoucherResponse`**: `id`, `code` (3..50), `title` (2..255), `description: str | None`, `discount_amount: Decimal` (`gt=0`), `points_required: int` (`gt=0`), `min_order_amount: Decimal` (`ge=0`), `expires_at: datetime`, `is_active: bool`, `created_at: datetime`.
- **`UserVoucherResponse`**: `id`, `user_id`, `voucher_id`, `is_used: bool`, `used_at: datetime | None`, `claimed_at: datetime`, `voucher: VoucherResponse | None`.
- **`VoucherRedeemResponse`**: `user_voucher_id: UUID`, `voucher_id: UUID`, `voucher_code: str`, `title: str`, `discount_amount: Decimal`, `points_deducted: int`, `remaining_balance: int`, `claimed_at: datetime`.

---

## 4. Frontend TypeScript DTOs (`frontend/src/types/api.ts` — Planned `EC4-13`)

```typescript
export type PointActionType = 'ORDER_RESCUE' | 'VOUCHER_REDEEM' | 'SYSTEM_BONUS';

export interface ReviewCreatePayload {
    rating: number; // integer 1..5
    comment?: string | null;
    tags?: string[];
    photo_urls?: string[];
}

export interface ReviewResponse {
    id: string;
    order_id: string;
    consumer_id: string;
    store_id: string;
    dish_id: string;
    rating: number;
    comment: string | null;
    tags: string[];
    photo_urls: string[];
    created_at: string;
}

export interface GreenPointsLedgerEntry {
    id: string;
    user_id: string;
    order_id: string | null;
    points_change: number;
    balance_after: number;
    action_type: PointActionType;
    co2_saved_kg: string | number;
    note: string | null;
    created_at: string;
}

export interface GreenPointsSummaryResponse {
    balance_points: number;
    total_co2_saved_kg: string | number;
    total_meals_saved: number;
    rank_title: string;
    recent_ledger: GreenPointsLedgerEntry[];
}

export interface VoucherResponse {
    id: string;
    code: string;
    title: string;
    description: string | null;
    discount_amount: string | number;
    points_required: number;
    min_order_amount: string | number;
    expires_at: string;
    is_active: boolean;
    created_at: string;
}

export interface UserVoucherResponse {
    id: string;
    user_id: string;
    voucher_id: string;
    is_used: boolean;
    used_at: string | null;
    claimed_at: string;
    voucher: VoucherResponse | null;
}

export interface VoucherRedeemResponse {
    user_voucher_id: string;
    voucher_id: string;
    voucher_code: string;
    title: string;
    discount_amount: string | number;
    points_deducted: number;
    remaining_balance: number;
    claimed_at: string;
}
```

---

## 5. Demo Seed Fixtures (`backend/app/db/seed.py` — Implemented `EC4-09`)

- **4 Active Vouchers**:
  1. `ECOBITE10K` — `10,000đ` off (min `30,000đ`), `100` pts, expires `+60` days.
  2. `GREENHERO20K` — `20,000đ` off (min `50,000đ`), `180` pts, expires `+90` days.
  3. `ECO25K` — `25,000đ` off (min `60,000đ`), `250` pts, expires `+90` days.
  4. `ECO50K` — `50,000đ` off (min `100,000đ`), `500` pts, expires `+120` days.
- **Seeded Consumers (Password: `Password123!`)**:
  - `consumer.an@ecobite.vn`: `green_points_balance = 180`, 1 `COMPLETED` order (`EB-20261101-0001`, 2 meals, `5.00 kg` CO₂, already reviewed with 5 stars & tags `["Ngon", "Giá tốt", "Đúng giờ"]`), 1 `CONFIRMED` order (`EB-20261102-0001`), 1 claimed `UserVoucher` (`ECOBITE10K`), and 3 consistent ledger entries (`+180 SYSTEM_BONUS` → `-100 VOUCHER_REDEEM` → `+100 ORDER_RESCUE`, ending `balance_after = 180`).
  - `consumer.huy@ecobite.vn`: `green_points_balance = 350`, 1 `COMPLETED` order (`EB-20261101-0002`, 7 meals, `17.50 kg` CO₂, unreviewed — ideal for live demo of `ReviewModal`!), rank `"Chiến Binh Xanh (Eco Hero)"`, and 1 ledger entry (`+350 ORDER_RESCUE`).
  - `consumer.bich@ecobite.vn`: `green_points_balance = 90`, rank `"Mầm Xanh (Eco Seedling)"` (ideal for testing disabled redeem buttons on `>= 100`-point vouchers).
