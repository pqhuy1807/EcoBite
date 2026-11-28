# Feature Specification: Verified Reviews, Green Points Wallet, CO₂ Impact Tracker & Atomic Voucher Redemption (Feature 8)

**Feature Branch**: `feat/fe-f8-gamification-reviews` *(Backend core merged on `dev` via `EC4-07`, `EC4-08`, `EC4-09`; Consumer UI, Vitest & concurrency QA tracked for Release 0.3 / PA4)*

**Created**: 2026-11-28

**Status**: In Progress (Backend Verified & Complete; Frontend Consumer UI, Vitest & Concurrency QA Pending)

**Input**: User description: "Feature 8 — Verified Reviews (F8A), Green Points Wallet, CO₂ Environmental Impact Tracker, Rule-Based Eco Ranking & Atomic Voucher Redemption (F8B), including demo seed data, Consumer web interface (`/green-points` wallet & `ReviewModal` on `/orders`), Vitest component tests, and concurrent voucher-redemption integrity verification."

## Summary *(mandatory)*

Food-rescue marketplaces succeed long term only when consumers trust store food quality and feel rewarded for sustainable daily choices. Without verified feedback, unverified or fake reviews erode trust in discounted surplus meals; without tangible sustainability metrics and rewards, consumers treat food rescue as a one-off bargain rather than a habit. This feature serves **Consumers** (with indirect reputation and environmental visibility for **Store Partners** and the public) through two tightly coupled capabilities:

1. **Verified Reviews (Feature 8A)**: Restricts food ratings and comments strictly to Consumers who have physically picked up and completed their order via verified QR confirmation. Each completed order allows exactly one 1–5 star review (with optional comments, quick feedback tags, and photos) and immediately recalculates the store's public average rating and review count.
2. **Green Points Wallet, CO₂ Impact Tracker & Atomic Voucher Redemption (Feature 8B)**: Converts completed food-rescue pickups into Green Points and verified CO₂-saved impact, displays a transparent wallet with transaction history and deterministic rule-based Eco Rank tiers, and allows Consumers to redeem active, unexpired discount vouchers atomically—guaranteeing that concurrent or repeated taps can never drive a consumer's point balance negative.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verified Post-Pickup Order Reviews & Store Rating Aggregation (Priority: P1)

As a Consumer who has picked up and completed a surplus-meal order, I want to submit a 1–5 star review with optional comments, quick tags, and meal photos—and browse verified reviews of any store—so that I can share authentic food quality feedback while preventing fake or duplicate reviews.

**Why this priority**: Trust in food freshness and store hygiene is essential for a non-mystery-bag food-rescue platform; restricting reviews to verified completed pickups eliminates fake ratings while immediately enriching store profiles.

**Independent Test**: Can be fully tested by signing in as a Consumer with a completed order, submitting a valid 1–5 star review, confirming that the store's average rating and review count update immediately and the new review appears first in the store's paginated review feed, while verifying that duplicate submissions, non-completed orders, non-owners, and non-Consumer accounts are rejected.

**Acceptance Scenarios**:

1. **Given** an authenticated Consumer who owns a `COMPLETED` rescue order that has not yet been reviewed, **When** the Consumer submits a review with rating `5`, a comment, quick tags, and photo URLs, **Then** the system records the verified review linked to the order, store, and dish, and atomically recalculates the store's average rating (rounded to 2 decimal places) and total review count.
2. **Given** a store has received multiple verified reviews across different completed orders (e.g., ratings `5` and `3`), **When** each new review is submitted, **Then** the store's average rating updates accurately (`4.00`) and its review count increments (`2`), while a store with zero reviews defaults to `5.00` with count `0`.
3. **Given** a Consumer attempts to submit a second review for an order that was already reviewed (including under simultaneous double-submission), **When** the request is processed, **Then** the system rejects the duplicate attempt with a conflict response and preserves the original review and store rating intact.
4. **Given** a Consumer attempts to review an order that is not yet `COMPLETED` (e.g., `CONFIRMED`, `READY_FOR_PICKUP`, `CANCELLED`, or `EXPIRED`), **When** the request is processed, **Then** the system rejects the submission with a conflict message explaining that only completed orders can be reviewed.
5. **Given** another Consumer who does not own the order, or a Store Partner / Admin account, attempts to submit a review for that order, **When** the request is checked, **Then** the system denies access immediately without modifying any records.
6. **Given** any visitor (authenticated or anonymous) requests reviews for a store, **When** pagination parameters (`skip`, `limit`) are supplied, **Then** the system returns the store's verified reviews ordered newest first (or an empty list if the store has no reviews).

---

### User Story 2 - Green Points Wallet, CO₂ Environmental Impact & Deterministic Eco Rank (Priority: P1)

As a Consumer who rescues surplus meals, I want to view my current Green Points balance, total kilograms of CO₂ saved, total meals rescued, deterministic Eco Rank badge, and chronological points ledger so that I can see the real environmental impact of my completed rescues and track every point earned or spent.

**Why this priority**: Turning completed pickups into visible sustainability progress and a clear point ledger drives repeat engagement and closes the loop after QR pickup confirmation.

**Independent Test**: Can be fully tested by signing in as a Consumer who has a mix of completed, confirmed, and cancelled orders plus ledger entries, requesting their Green Points summary, and confirming that only `COMPLETED` orders count toward total CO₂ saved and meals rescued, the Eco Rank matches the deterministic tier table (even after spending points on vouchers), and the ledger lists entries newest first.

**Acceptance Scenarios**:

1. **Given** an authenticated Consumer with `COMPLETED` orders (e.g., 2 orders totaling 7 meals and `17.50 kg` CO₂) alongside `CONFIRMED` and `CANCELLED` orders, **When** the Consumer opens their Green Points summary, **Then** the system returns their current `balance_points`, aggregates `total_co2_saved_kg` (`17.50`) and `total_meals_saved` (`7`) exclusively from `COMPLETED` orders, assigns the deterministic Eco Rank (`Chiến Binh Xanh (Eco Hero)`), and returns recent ledger entries ordered newest first.
2. **Given** a newly registered Consumer with zero completed orders and zero points, **When** they view their Green Points summary, **Then** the system returns `balance_points = 0`, `total_co2_saved_kg = 0.00`, `total_meals_saved = 0`, rank `Mầm Xanh (Eco Seedling)`, and an empty ledger list.
3. **Given** a Consumer has rescued `17.50 kg` of CO₂ (equivalent to `350` eco-score points) and then redeems vouchers so their spendable balance drops to `20` points, **When** their Eco Rank is computed, **Then** the system preserves their earned `Chiến Binh Xanh (Eco Hero)` rank based on lifetime rescued CO₂ rather than demoting them for spending points.
4. **Given** an unauthenticated visitor or a non-Consumer account (e.g., Store Partner) attempts to access the personal Green Points wallet, **When** the request is checked, **Then** the system denies access immediately.

---

### User Story 3 - Voucher Catalog Browsing & Atomic Point-to-Voucher Redemption (Priority: P1)

As a Consumer with accumulated Green Points, I want to browse active, unexpired vouchers and redeem a voucher in one action—seeing my updated balance, newly claimed voucher, and negative ledger entry immediately—while the platform guarantees that double-clicks or concurrent requests can never over-spend my points.

**Why this priority**: Voucher redemption turns Green Points into real economic value; atomic deduction is a financial-integrity invariant preventing negative balances or duplicate free vouchers under race conditions.

**Independent Test**: Can be fully tested by listing active vouchers (verifying inactive and expired vouchers are excluded and sorted by ascending point cost), redeeming a voucher with sufficient points, verifying balance deduction + negative ledger entry + claimed voucher record in one transaction, confirming `409` on insufficient points and `400` on expired/inactive vouchers, and sending concurrent redemption requests to verify zero negative balance.

**Acceptance Scenarios**:

1. **Given** the catalog contains active unexpired vouchers, inactive vouchers, and expired vouchers, **When** any user browses available vouchers, **Then** only active vouchers whose expiration timestamp is strictly in the future are returned, sorted by ascending point requirement.
2. **Given** an authenticated Consumer has `250` Green Points and redeems an active, unexpired `200`-point voucher, **When** redemption completes, **Then** in a single atomic transaction the system deducts `200` points (leaving `50`), records a negative `-200` `VOUCHER_REDEEM` ledger entry with `balance_after = 50`, creates an unused claimed voucher owned by the Consumer, and returns confirmation details (`user_voucher_id`, `voucher_code`, `title`, `discount_amount`, `points_deducted`, `remaining_balance`, `claimed_at`).
3. **Given** a Consumer has `150` Green Points and fires multiple concurrent redemption requests for a `100`-point voucher (e.g., accidental double-click or parallel API burst), **When** all requests finish, **Then** exactly one redemption succeeds (`remaining_balance = 50`), all competing requests fail with a conflict response (`409`), exactly one claimed voucher and one negative ledger entry exist, and the balance never drops below zero.
4. **Given** a Consumer attempts to redeem a voucher with fewer points than required, **When** redemption is attempted, **Then** the system rejects the request with a conflict response (`409`) and makes zero changes to the Consumer's balance, ledger, or claimed vouchers.
5. **Given** a Consumer attempts to redeem an inactive voucher, an expired voucher (including at the exact expiration timestamp), or a non-existent voucher, **When** redemption is attempted, **Then** the system rejects the request (`400` for inactive/expired, `404` for unknown) without deducting any points.
6. **Given** an unexpected storage failure occurs after points are deducted but before the claimed voucher is saved, **When** the transaction aborts, **Then** the system rolls back the entire transaction so the Consumer's point balance and ledger remain completely unchanged.
7. **Given** an authenticated Consumer requests their claimed vouchers list, **When** pagination (`skip`, `limit`) is applied, **Then** the system returns only that Consumer's claimed vouchers ordered newest first, complete with each voucher's catalog details and usage status.

---

### User Story 4 - Consumer Green Points Dashboard, In-Order Review Modal & UI Verification (Priority: P2)

As a Consumer using the EcoBite web application, I want a dedicated Green Points & Vouchers page and an interactive Review modal directly on my completed orders so that I can monitor my CO₂ impact, redeem vouchers in one tap, and submit verified food reviews seamlessly from mobile or desktop browsers.

**Why this priority**: Exposes the completed Feature 8 backend to real Consumers for the Release 0.3 / PA4 milestone and ensures UI safety behaviors (insufficient-point button disabling, duplicate-review handling, automatic balance refresh) are locked in with automated component tests.

**Independent Test**: Can be fully tested by logging in as a Consumer (`consumer.an@ecobite.vn` or `consumer.huy@ecobite.vn` from seeded demo data), navigating to `/green-points` to inspect stats, redeem an affordable voucher (seeing immediate balance, My Vouchers, and Ledger updates), verifying unaffordable vouchers are disabled, opening `/orders` to review a `COMPLETED` order via the Review modal (and seeing friendly handling if already reviewed), and executing the automated frontend component test suite.

**Acceptance Scenarios**:

1. **Given** an authenticated Consumer opens the Green Points page (`/green-points`), **When** data loads, **Then** the header displays current Green Points balance, total CO₂ saved (kg), total meals rescued, and the Consumer's Eco Rank badge, alongside three switchable tabs: **Đổi Voucher** (Redeem Vouchers), **Voucher của tôi** (My Vouchers), and **Lịch sử Điểm Xanh** (Points Ledger).
2. **Given** the Consumer views the **Đổi Voucher** tab, **When** a voucher requires more points than the Consumer's current balance, **Then** its redeem button is clearly disabled with an explanation; when the Consumer taps redeem on an affordable voucher and succeeds, the wallet balance, My Vouchers list, and Points Ledger refresh automatically with a success notification.
3. **Given** an authenticated Consumer views their orders list (`/orders`), **When** an order has status `COMPLETED`, **Then** a *"Đánh giá"* (Review) action button is displayed on that order card (while non-completed orders do not show the review action).
4. **Given** the Consumer opens the Review modal for a completed order, **When** they choose a 1–5 star rating, enter an optional comment (and optional quick tags), and submit, **Then** a successful submission closes the modal and displays a confirmation toast, while a `409 Conflict` (already reviewed) response shows a friendly Vietnamese notice without crashing or losing page state.
5. **Given** the Review modal and Green Points wallet page are covered by automated frontend component tests, **When** the test suite runs, **Then** star selection, submission, `409` duplicate-review feedback, insufficient-points button disabling, voucher redemption cache invalidation, and tab switching all pass deterministically.

---

### Edge Cases

- **Rating out of bounds**: Submitting a star rating below `1` or above `5` (or non-integer) is rejected at request validation (`422`) and backed by a database check constraint (`rating >= 1 AND rating <= 5`).
- **Concurrent duplicate review race**: Two simultaneous `POST` review requests for the same completed order cannot insert two rows; the database `UNIQUE(order_id)` constraint catches any race that slips past the initial lookup, rolls back cleanly, and returns `409 Conflict`.
- **Store with zero reviews**: Querying reviews for a store with no reviews (or an unknown store ID) returns `200 OK` with an empty array `[]`; recalculating rating on zero reviews resets to default `rating_avg = 5.00`, `rating_count = 0`.
- **Voucher expired at exact boundary (`expires_at == now`)**: Treated as expired—excluded from the available catalog (`expires_at > now`) and rejected on redemption (`400 Bad Request`).
- **Non-positive voucher point cost**: Internal repository atomic deduction explicitly refuses `point_cost <= 0` so a misconfigured record can never credit points through a deduction path.
- **Redemption after rank earned**: Spending Green Points lowers `balance_points` but never lowers `total_co2_saved_kg`; because Eco Rank uses `max(balance_points, floor(total_co2_saved_kg * 20))`, Consumers retain their achieved Eco Rank title.
- **Redis temporarily unavailable during voucher redemption**: Optional distributed locking degrades gracefully without blocking requests, while the conditional atomic SQL update (`WHERE green_points_balance >= :cost`) remains the authoritative database-level concurrency guard.
- **Unauthenticated or non-Consumer navigating to `/green-points`**: Client-side route protection redirects or blocks non-Consumer users, reinforced by server-side `401`/`403` enforcement on every protected endpoint.
- **Consistent demo seed data**: Seeding demo records must populate active vouchers (`ECOBITE10K`, `GREENHERO20K`, `ECO25K`, `ECO50K`), completed orders, a verified review, claimed voucher, and ledger entries whose `balance_after` matches the seeded consumer's `green_points_balance`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow only authenticated users with the `CONSUMER` role who own the target order and whose order status is `COMPLETED` to submit a verified review for that order.
- **FR-002**: System MUST enforce a strict one-review-per-order invariant at both the application layer and persistent storage layer (`UNIQUE(order_id)`), returning a `409 Conflict` response on any duplicate or concurrent review attempt without altering existing reviews or store ratings.
- **FR-003**: System MUST validate that every submitted review has an integer `rating` between `1` and `5` inclusive, an optional text `comment`, optional `tags` list, and optional `photo_urls` list.
- **FR-004**: System MUST recalculate and persist the reviewed store's `rating_avg` (rounded to 2 decimal places, defaulting to `5.00` when count is `0`) and `rating_count` within the same atomic database transaction as review creation.
- **FR-005**: System MUST expose a public paginated store-reviews query ordered newest first (`skip >= 0`, `1 <= limit <= 100`, default `limit = 20`), returning an empty list when no reviews exist.
- **FR-006**: System MUST expose an authenticated `CONSUMER`-only Green Points summary returning current `balance_points`, `total_co2_saved_kg` and `total_meals_saved` aggregated exclusively from `COMPLETED` orders, deterministic `rank_title`, and newest-first `recent_ledger` entries (`1 <= limit <= 100`, default `20`).
- **FR-007**: System MUST compute `rank_title` using deterministic rule-based thresholds (`effective_score = max(balance_points, int(max(total_co2_saved_kg, 0) * 20), 0)`):
  - `>= 1000` → `"Đại Sứ Xanh (Eco Ambassador)"`
  - `>= 300` → `"Chiến Binh Xanh (Eco Hero)"`
  - `>= 100` → `"Người Giải Cứu (Food Rescuer)"`
  - `0–99` → `"Mầm Xanh (Eco Seedling)"`
- **FR-008**: System MUST expose a public catalog of currently redeemable vouchers containing only records where `is_active` is true and `expires_at` is strictly greater than current UTC time, sorted by ascending `points_required` (then newest `created_at`).
- **FR-009**: System MUST expose an authenticated `CONSUMER`-only paginated list of that Consumer's claimed vouchers (`skip >= 0`, `1 <= limit <= 100`, default `20`), ordered newest first, embedding catalog voucher metadata and usage flags (`is_used`, `used_at`, `claimed_at`).
- **FR-010**: System MUST implement voucher redemption for authenticated `CONSUMER` accounts as a single atomic transaction that:
  1. Verifies the voucher exists (`404`), is active (`400`), and is unexpired (`400`).
  2. Executes an atomic conditional point deduction (`WHERE green_points_balance >= :cost`), rejecting insufficient points with `409 Conflict`.
  3. Writes a negative `GreenPointsLedger` record (`action_type = VOUCHER_REDEEM`, `points_change = -points_required`, `balance_after = new_balance`, `co2_saved_kg = 0.00`).
  4. Creates an unused `UserVoucher` ownership record (`is_used = False`).
  5. Rolls back all mutations atomically if any step fails.
- **FR-011**: System MUST provide idempotent demo seed data containing at least 4 active vouchers (`ECOBITE10K`, `GREENHERO20K`, `ECO25K`, `ECO50K`), sample completed orders, a sample verified review, a sample claimed voucher, and internally consistent Green Points ledger entries aligned with seeded Consumer balances.
- **FR-012**: The Consumer web interface MUST provide a dedicated Green Points & Vouchers page (`/green-points`) displaying the Consumer's balance, CO₂ impact, meals saved, and Eco Rank header, plus tabs for **Đổi Voucher** (with automatic disablement when points are insufficient and 1-tap redemption), **Voucher của tôi**, and **Lịch sử Điểm Xanh**, refreshing displayed state immediately after successful redemption.
- **FR-013**: The Consumer orders page (`/orders`) MUST display a *"Đánh giá"* action on `COMPLETED` orders that opens an interactive `ReviewModal` supporting 1–5 star selection, optional comments/tags, review submission, and graceful handling of `409 Conflict` (already reviewed).
- **FR-014**: The frontend codebase MUST include typed API client services and DTOs for both Verified Reviews and Gamification/Vouchers, plus automated component unit tests verifying `ReviewModal` and `/green-points` voucher-redemption flows.
- **FR-015**: The backend test suite MUST include automated multi-session concurrency verification proving zero negative balances and exact single-success enforcement under parallel voucher redemption requests.

### Non-Functional Requirements *(mandatory when the feature touches money, health, or personal data)*

- **NFR-001 (Transactional Consistency & Concurrency Safety)**: Point balance deductions and review uniqueness MUST be enforced at the database layer (conditional atomic `UPDATE` and `UNIQUE(order_id)` constraint), guaranteeing `0%` negative balances and `0%` duplicate reviews even under concurrent bursts or when optional distributed lock caches are unavailable.
- **NFR-002 (Security & Access Control)**: All state-mutating and personal-data operations (submitting reviews, reading personal Green Points wallets, reading personal claimed vouchers, and redeeming vouchers) MUST enforce server-side authentication and strict `CONSUMER` role checks, plus order ownership validation on reviews; unauthenticated calls return `401` and unauthorized roles or non-owners return `403`.
- **NFR-003 (Deterministic Financial & Sustainability Accounting)**: Eco Rank tiers, CO₂ impact totals (summed strictly over `COMPLETED` orders), store rating averages, and voucher point deductions MUST be 100% deterministic rule-based calculations with exact two-decimal-place fixed-point precision—never probabilistic AI estimates.
- **NFR-004 (Responsiveness & Non-Blocking I/O)**: All backend queries and transactions MUST execute asynchronously without blocking the event loop; frontend interactions MUST surface immediate loading states, disabled duplicate-click guards, and accessible Vietnamese error/success notifications.

### Key Entities *(include if feature involves data)*

- **Verified Review (`Review`)**: Authentic 1–5 star post-pickup evaluation tied 1-to-1 to a `COMPLETED` Order, referencing its Consumer, Store, and Dish, with optional text comment, quick tags, and photo URLs.
- **Green Points Ledger Entry (`GreenPointsLedger`)**: Immutable audit record of every positive or negative Green Points mutation (`ORDER_RESCUE`, `VOUCHER_REDEEM`, `SYSTEM_BONUS`), recording `points_change`, post-transaction `balance_after`, associated `co2_saved_kg`, optional `order_id`, and Vietnamese note.
- **Voucher (`Voucher`)**: Catalog reward definition identified by a unique `code`, holding title, description, VND `discount_amount`, `points_required` cost, `min_order_amount`, `expires_at` deadline, and `is_active` toggle.
- **Claimed User Voucher (`UserVoucher`)**: Record of a Voucher redeemed by a specific Consumer, tracking `claimed_at`, `is_used`, and `used_at` metadata.
- **Consumer Wallet & Impact Profile (`User` + `COMPLETED` Orders)**: Consumer's live spendable `green_points_balance` paired with completed-order aggregates (`total_co2_saved_kg`, `total_meals_saved`) and deterministic Eco Rank title.
- **Store Reputation Metrics (`Store`)**: Aggregate `rating_avg` (1.00–5.00, default 5.00) and `rating_count` maintained transactionally whenever a verified review is created, plus `total_co2_saved_kg` incremented on pickup completion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Zero Unverified or Duplicate Reviews)**: 100% of review attempts on non-completed orders, other consumers' orders, or already-reviewed orders are rejected (`403`/`409`), and 100% of accepted reviews update the target store's `rating_avg` and `rating_count` accurately within the same transaction.
- **SC-002 (Zero Negative Balances Under Concurrency)**: Under a concurrent burst of parallel voucher-redemption requests exceeding a Consumer's balance (e.g., 10 simultaneous requests for a 100-point voucher with 150 points available), **exactly 1** redemption succeeds (`200 OK`), **all remaining requests** return `409 Conflict`, final `green_points_balance` equals `50` (never `< 0`), and exactly 1 `UserVoucher` and 1 negative `GreenPointsLedger` record are persisted.
- **SC-003 (100% Deterministic Sustainability & Rank Accuracy)**: Green Points wallet summaries count exclusively `COMPLETED` orders for `total_co2_saved_kg` and `total_meals_saved`, match all four Eco Rank threshold tiers across boundary values, and preserve earned rank when spendable points decrease after voucher redemption.
- **SC-004 (Voucher Validity Enforcement)**: 100% of inactive and expired vouchers (including exact expiry timestamp) are excluded from the public catalog and rejected (`400 Bad Request`) upon direct redemption attempts with zero point deduction.
- **SC-005 (End-to-End Consumer Web Experience)**: A Consumer logged into the web app can view their Green Points wallet & CO₂ impact, redeem an eligible voucher and see live balance/My Vouchers/Ledger updates without full-page reload, and submit a verified 1–5 star review on a completed order from `/orders` with graceful handling of duplicate-review feedback.
- **SC-006 (Automated Verification Coverage)**: All backend unit, integration, and concurrency tests plus frontend component tests (`ReviewModal` and `/green-points`), linters, static type-checks, production build, and pre-commit hooks pass with zero errors (`exit 0`).

## Assumptions

- **Existing Upstream Earning Trigger (`EC4-06`, Complete)**: Green Points awarding (`+green_points_earned`), `ORDER_RESCUE` ledger creation, and `Store.total_co2_saved_kg` accumulation already execute atomically inside QR pickup completion (`POST /api/v1/orders/verify-qr`) from earlier Sprint 4 work; Feature 8 builds directly on those persisted records.
- **Existing Database Schema**: All four Feature 8 tables (`reviews`, `green_points_ledger`, `vouchers`, `user_vouchers`) and aggregate columns (`users.green_points_balance`, `stores.rating_avg`, `stores.rating_count`, `stores.total_co2_saved_kg`) were created in the initial 12-table migration, so no new schema migration is required.
- **Voucher Application at Checkout Out of Scope for PA4**: Feature 8 covers redeeming Green Points into claimed `UserVoucher` records (`is_used = False`) and displaying them in the Consumer's wallet; applying a claimed voucher code to reduce checkout order totals in `POST /api/v1/orders` is deferred beyond PA4.
- **Photo Upload Storage**: `photo_urls` on reviews accepts validated URL strings; dedicated binary image upload storage/CDN endpoints are outside Feature 8 scope and optional in the Consumer `ReviewModal` UI.
- **Team Ownership Split (Week 6 Action Plan)**: Backend Feature 8A (`EC4-07`, Đàng Thế Tony) and Feature 8B + seed data (`EC4-08`/`EC4-09`, Phùng Quốc Huy) are complete and merged on `dev`; Consumer Feature 8 UI (`EC4-13`), Vitest Part 2 (`EC4-14`), and concurrent voucher QA (`EC4-15`) are assigned to Đàng Thế Tony using disjoint frontend files to avoid merge conflicts with Võ Ngọc Thịnh's VNPay/Store Orders work.
