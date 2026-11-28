# Technical Research & Design Decisions: Verified Reviews, Green Points Wallet & Atomic Vouchers (Feature 8)

**Feature**: `005-reviews-gamification-vouchers` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

This document captures the architectural, transactional, security, database-portability, frontend state, and QA decisions governing EcoBite Feature 8 (F8A & F8B).

---

## Decision 1: Atomic SQL Conditional Point Deduction + Optional Redis Distributed Lock

- **Decision**: Enforce non-negative Green Points balances inside `GamificationRepository.atomic_deduct_points` via a single database-level conditional `UPDATE ... RETURNING`:
  ```sql
  UPDATE users
  SET green_points_balance = green_points_balance - :point_cost
  WHERE id = :user_id AND green_points_balance >= :point_cost
  RETURNING green_points_balance
  ```
  Wrap `GamificationService.redeem_voucher` in an optional user-scoped Redis distributed lock (`async with distributed_lock(f"lock:green_points:user:{user_id}"):`), commit point deduction + negative `GreenPointsLedger` creation + `UserVoucher` insertion in **one single DB transaction** (`commit=False` on repo helpers, single `await self.db.commit()`), and execute `await self.db.rollback()` on any unexpected mid-transaction exception.
- **Rationale**:
  - Directly satisfies **Constitution Principle III** and **AGENTS.md Guardrail #4** (concurrency invariants MUST live at the database layer; Redis locks are defense-in-depth, never a replacement).
  - Prevents lost updates and negative balances under rapid double-taps or concurrent HTTP requests across multiple Uvicorn workers, even when Redis is offline (since `app/core/redis.py` degrades cleanly).
  - Explicitly rejecting `point_cost <= 0` prevents inverted balance credits from malformed catalog records.
  - Refreshing any already-cached `User` instance in the SQLAlchemy session after `synchronize_session=False` keeps ORM state coherent within the same request/test session.
- **Alternatives considered**:
  - Read-modify-write in Python (`if user.green_points_balance >= cost: user.green_points_balance -= cost`): vulnerable to TOCTOU race conditions between concurrent sessions.
  - Redis-only locking without conditional SQL `WHERE`: unsafe if Redis restarts, expires a lock mid-transaction, or runs in degraded mode during local dev/tests.

---

## Decision 2: Deterministic Rule-Based Eco Rank with CO₂ Preservation

- **Decision**: Compute `rank_title` purely deterministically inside `GamificationService.compute_rank_title(balance_points, total_co2_saved_kg)` using:
  - `CO2_KG_TO_SCORE_FACTOR = Decimal("20")` (mirroring EcoBite's core impact conversion: `1 rescued meal = 2.5 kg CO₂ = 50 Green Points`, so `2.5 * 20 = 50`).
  - `effective_score = max(balance_points, int(max(total_co2_saved_kg, Decimal("0")) * 20), 0)`.
  - Tier table (`RANK_THRESHOLDS`):
    - `>= 1000` (`>= 50.0 kg CO₂`) → `"Đại Sứ Xanh (Eco Ambassador)"`
    - `>= 300` (`>= 15.0 kg CO₂`) → `"Chiến Binh Xanh (Eco Hero)"`
    - `>= 100` (`>= 5.0 kg CO₂`) → `"Người Giải Cứu (Food Rescuer)"`
    - `0–99` → `"Mầm Xanh (Eco Seedling)"`
- **Rationale**:
  - Satisfies **Constitution Principle V** (deterministic business rules, zero AI unpredictability).
  - Solves a classic gamification UX trap: if rank depended solely on spendable `balance_points`, redeeming vouchers would demote loyal users (e.g., from *Eco Hero* back to *Eco Seedling*). Taking `max(balance_points, co2_score)` rewards both newly awarded points (including welcome/system bonuses) and lifetime rescued CO₂ without requiring an extra `lifetime_points_earned` column migration.
- **Alternatives considered**:
  - Ranking purely by `balance_points`: penalizes users for spending vouchers.
  - Adding a new `lifetime_points` column to `users`: requires an unnecessary Alembic migration when `COMPLETED` order CO₂ totals already capture verified rescue contribution accurately.

---

## Decision 3: Verified Reviews Integrity & Two-Layer Anti-Duplication

- **Decision**: Guard `POST /api/v1/orders/{order_id}/review` with four sequential business checks in `ReviewService.create_review` (`UserRole.CONSUMER`, order existence `404`, `order.consumer_id == consumer.id` `403`, `order.status == OrderStatus.COMPLETED` `409`), followed by an application-level duplicate pre-check (`get_by_order_id`) AND a database-level `UNIQUE(order_id)` `IntegrityError` catch that rolls back and returns `409 Conflict`. Compute and update `Store.rating_avg` (rounded to 2 decimal places, defaulting to `Decimal("5.00")` when count is `0`) and `Store.rating_count` via SQL `COUNT`/`AVG` inside the **same DB transaction** (`commit=False` on both repo methods, single `commit()`).
- **Rationale**:
  - Enforces **Constitution Principle V** (*"review eligibility MUST be based on verified order status, including successful QR pickup confirmation"*) and **Principle III** (transactional consistency).
  - Catching `IntegrityError` handles concurrent double-POST race conditions cleanly without leaking `500 Internal Server Error`.
  - Recalculating `rating_avg` and `rating_count` directly via SQL `func.avg(Review.rating)` and `func.count(Review.id)` avoids floating-point drift inherent in incremental moving-average updates.
- **Alternatives considered**:
  - Incremental rating formula `((old_avg * old_count) + rating) / (old_count + 1)`: suffers from cumulative rounding error and concurrent read-modify-write skew.
  - Background async job for store rating aggregation: introduces eventual inconsistency in UI and integration tests for minimal write volume.

---

## Decision 4: Authoritative Environmental Impact Aggregation from `COMPLETED` Orders Only

- **Decision**: Compute `total_co2_saved_kg` and `total_meals_saved` in `GamificationRepository.get_completed_rescue_stats(user_id)` via SQL `COALESCE(SUM(Order.co2_saved_kg), 0.00)` and `COALESCE(SUM(Order.quantity), 0)` filtered strictly by `Order.consumer_id == user_id` and `Order.status == OrderStatus.COMPLETED`, quantizing CO₂ to `Decimal("0.01")`.
- **Rationale**:
  - Guarantees that pending (`CONFIRMED`, `READY_FOR_PICKUP`), cancelled (`CANCELLED`), or expired (`EXPIRED`) orders never inflate environmental impact metrics—only meals physically rescued via verified QR pickup count.
  - Matches `OrderService.verify_and_complete_order` (`EC4-06`), which awards `GreenPointsLedger` (`ORDER_RESCUE`) and updates `Store.total_co2_saved_kg` only when transitioning an order to `COMPLETED`.
- **Alternatives considered**:
  - Summing `GreenPointsLedger.co2_saved_kg`: works for rescue orders, but does not directly expose `total_meals_saved` (`SUM(Order.quantity)`), which is authoritative on `orders`.

---

## Decision 5: FastAPI Route Precedence & Collision Prevention

- **Decision**:
  1. In `backend/app/api/v1/endpoints/gamification.py`, declare static `GET /vouchers/me` strictly **before** parameterized `POST /vouchers/{voucher_id}/redeem`.
  2. In `backend/app/api/v1/router.py`, include `gamification.router` strictly **before** `stores.router` because `stores.router` carries a legacy root-level wildcard `GET /{store_id}` route that would otherwise swallow `/vouchers` or `/green-points/me` and fail UUID parsing (`422`).
- **Rationale**: FastAPI matches routes in registration order; explicit precedence prevents silent shadowing bugs while keeping existing legacy routes backwards-compatible.
- **Alternatives considered**: Prefixing all gamification routes under `/gamification/...` — rejected because `docs/04_API_Specification.md` mandates exact paths `/api/v1/green-points/me` and `/api/v1/vouchers/{voucher_id}/redeem`.

---

## Decision 6: Cross-Database UTC Datetime Normalization & Portable Schema Types

- **Decision**:
  - Normalize timestamps via `_as_utc(value)` (`value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)`) in `GamificationService` before comparing `voucher.expires_at <= resolved_now`.
  - Keep `Review.tags` and `Review.photo_urls` on `JSON_TYPE` (`JSON().with_variant(JSONB, "postgresql")`) and enums with `native_enum=False`.
- **Rationale**: SQLite (`aiosqlite` in dev/pytest) strips timezone info when returning `DateTime(timezone=True)` columns, whereas PostgreSQL (`asyncpg`) returns tz-aware datetimes. Without `_as_utc`, comparing naive vs aware datetimes raises `TypeError` in SQLite tests.
- **Alternatives considered**: Storing naive UTC everywhere — rejected because PostgreSQL production columns are `TIMESTAMPTZ` (`DateTime(timezone=True)`).

---

## Decision 7: Consumer Feature 8 Frontend Architecture & Zero-Conflict File Split (`EC4-13`)

- **Decision**:
  - Add typed Feature 8 DTOs to `frontend/src/types/api.ts` matching exact backend Pydantic field names (including `Decimal`-serialized `string | number` monetary/CO₂ fields formatted via `@/lib/utils` `formatVND` / `Number(...).toFixed(2)`).
  - Implement thin REST wrappers `frontend/src/services/gamification.service.ts` (`getMyGreenPoints`, `listVouchers`, `getMyVouchers`, `redeemVoucher`) and `frontend/src/services/review.service.ts` (`createReview`, `getStoreReviews`) using `@/lib/api-client`.
  - Build `frontend/src/app/green-points/page.tsx` as a `'use client'` page wrapped in `<AuthGuard allowedRoles={['CONSUMER']}>` with:
    - Top summary banner (`balance_points`, `total_co2_saved_kg`, `total_meals_saved`, `rank_title` badge).
    - Three tabbed panels (`redeem` / `my-vouchers` / `ledger`).
    - Per-voucher mutation state disabling the button while pending OR when `summary.balance_points < voucher.points_required`, and invalidating `['green-points-me']`, `['vouchers-me']`, and `['vouchers-available']` via `queryClient.invalidateQueries` on success.
  - Build reusable `frontend/src/components/ReviewModal.tsx` over existing `@/components/ui/Modal` with interactive 1–5 star buttons (accessible `aria-label` per star), optional quick-tag chips (`"Tươi ngon"`, `"Đóng gói kỹ"`, `"Đúng giờ"`, `"Giá tốt"`), optional comment textarea, mutation loading guard, and explicit `409 Conflict` detection (`axios.isAxiosError(err) && err.response?.status === 409`) surfacing a friendly notice and disabling re-submission for that order.
  - Wire a single *"Đánh giá"* button on `COMPLETED` orders in `frontend/src/app/orders/page.tsx` (coordinating merge order after Thịnh's `EC4-12` edits per Week 6 Action Plan).
- **Rationale**: Maximizes reuse of existing EcoBite UI primitives (`AuthGuard`, `Card`, `Badge`, `Button`, `Modal`, `Toast`, `Navbar`), preserves full TypeScript strictness, and guarantees zero merge conflicts between Tony and Thịnh during parallel Week 6 execution.
- **Alternatives considered**: Embedding review form inline inside each order card — rejected because it clutters the `/orders` list and prevents reuse of `ReviewModal` on future order-detail views.

---

## Decision 8: Concurrency Integration Test (`EC4-15`) & Vitest Component Suite (`EC4-14`)

- **Decision**:
  - **Backend Concurrent Voucher Burst Test (`EC4-15`)**: Add a multi-session concurrency integration test in `backend/tests/integration/test_api_gamification.py` modeled directly on `backend/tests/integration/test_order_concurrency.py` (temporary file-backed SQLite DB with `NullPool` + per-request independent `AsyncSession` override + `asyncio.gather` firing 10 concurrent `POST /api/v1/vouchers/{voucher_id}/redeem` requests for a consumer with `150` points on a `100`-point voucher). Assert exactly `1` HTTP `200`, `9` HTTP `409`, `0` other status codes, final `green_points_balance == 50`, `1` `UserVoucher`, and `1` `GreenPointsLedger` row.
  - **Frontend Vitest Component Suites (`EC4-14`)**: Leverage the already-configured `frontend/vitest.config.ts` (`jsdom`, `globals: true`, `vitest.setup.ts`) to author:
    1. `frontend/__tests__/components/ReviewModal.test.tsx`: mocks `reviewService.createReview`, verifies 1–5 star selection, payload submission, `onSuccess` callback, and friendly `409 Conflict` handling.
    2. `frontend/__tests__/components/GreenPointsPage.test.tsx`: wraps page in a fresh `QueryClientProvider`, mocks `gamificationService` + `localStorage` Consumer session, verifies stats header (`balance_points`, `total_co2_saved_kg`, `total_meals_saved`, `rank_title`), disabled button when points are insufficient, 1-tap redemption triggering `redeemVoucher` and query refetch, and switching between **Đổi Voucher**, **Voucher của tôi**, and **Lịch sử Điểm Xanh** tabs.
- **Rationale**: Proves both backend concurrency invariants and frontend UX guardrails automatically in CI without external browser or Redis dependencies.
- **Alternatives considered**: Testing concurrent redemptions on an in-memory shared single-session SQLite fixture — rejected because SQLAlchemy `AsyncSession` is not safe for concurrent use on one session; separate sessions over a temp file DB with `NullPool` accurately simulate concurrent production requests.
