# Feature Specification: Consumer Surplus Discovery, Anti-Overselling Order & Dynamic QR Pickup

**Feature Branch**: `dev`
**Created**: 2026-11-14
**Status**: Approved
**Input**: Complete end-to-end functional group covering Consumer authentication, location-based surplus dish discovery, atomic anti-overselling order placement/cancellation, and single-use HMAC-SHA256 QR pickup verification for PA3 Demo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Location-Based Surplus Discovery Radar (Priority: P1)

As a Consumer, I want to log in, view nearby partner stores on an interactive map and list sorted by distance from my current location, and filter surplus dishes by radius and food category so that I can quickly find discounted meals before they expire.

**Why this priority**: Discovery is the entry point of the entire food-rescue journey; without seeing nearby stores, live stock, and time-shifted prices, consumers cannot place orders.

**Independent Test**: Can be fully tested by opening the discovery screen, granting or falling back to a default city-center location, adjusting radius (1–10 km) and category filters, and verifying matching nearby stores and active dishes render with distance, pickup window, and discounted pricing.

**Acceptance Scenarios**:

1. **Given** a consumer opens the discovery screen with location permission granted (or falls back to default District 1 coordinates), **When** the nearby search completes, **Then** approved partner stores within the selected radius are shown on both an interactive map and a sorted list with distance, rating, and active surplus dishes.
2. **Given** nearby stores have active surplus dishes across multiple categories, **When** the consumer selects a specific food category or changes the search radius (1–10 km), **Then** the displayed stores and dishes update to match only the selected criteria.
3. **Given** a dish has entered its rule-based rush-hour discount window, **When** it is displayed in the dish list, **Then** the consumer sees the original price crossed out, the active discounted price, remaining quantity, pickup window, and allergen warnings.

---

### User Story 2 - Atomic Rescue Order Placement & Anti-Overselling (Priority: P1)

As a Consumer, I want to select a surplus dish quantity and place a rescue order so that my meal is reserved immediately while guaranteeing that two buyers or an oversized request can never oversell remaining stock.

**Why this priority**: Preventing negative inventory and double-booking during flash-sale pickups is EcoBite's core business invariant.

**Independent Test**: Can be tested by placing an order for an active dish during its pickup window, verifying remaining quantity drops immediately, and attempting to order more than remaining stock to confirm rejection without altering inventory.

**Acceptance Scenarios**:

1. **Given** an authenticated consumer selects an active dish within its pickup window with `remaining_quantity >= requested_quantity`, **When** they confirm the rescue order, **Then** the system creates the order with a unique `EB-YYYYMMDD-XXXXXXXX` code, calculates CO2 saved (`2.5 kg` per portion) and Green Points (`10 points/kg`), decrements remaining stock, and displays order confirmation details.
2. **Given** a consumer attempts to order a quantity exceeding `remaining_quantity` (or two concurrent consumers compete for the last portion), **When** the order request is processed, **Then** the system rejects the excess request with a clear "out of stock / insufficient quantity" message and never allows remaining stock to become negative.
3. **Given** a dish is outside its pickup window or no longer active, **When** a consumer attempts to place an order, **Then** the system blocks the order and explains why the dish cannot be reserved.

---

### User Story 3 - My Orders, Cancellation & Dynamic Pickup QR (Priority: P1)

As a Consumer, I want to view my rescue orders, cancel an active order before the pickup deadline to return stock, and display a dynamic single-use pickup QR code so that I can pick up my meal at the store.

**Why this priority**: Consumers need self-service visibility into their orders, the ability to release unclaimed reservations, and a scannable pickup credential.

**Independent Test**: Can be tested by navigating to the "My Orders" screen, opening a `CONFIRMED` order to render its dynamic QR code, and cancelling another `CONFIRMED` order before deadline to confirm status becomes `CANCELLED` and dish stock increases.

**Acceptance Scenarios**:

1. **Given** an authenticated consumer navigates to their order history, **When** orders load, **Then** they see each order's code, status, quantity, total amount, CO2 saved, Green Points earned, and pickup deadline, with status filtering.
2. **Given** a `CONFIRMED` order is before its pickup deadline, **When** the consumer clicks "Show Pickup QR", **Then** the system generates or retrieves a valid signed single-use QR payload and renders it as a scannable QR code alongside a copyable payload for store verification.
3. **Given** a `CONFIRMED` order is before its pickup deadline, **When** the consumer cancels the order, **Then** the order transitions to `CANCELLED` and the reserved quantity is atomically restored to the dish's available stock.

---

### User Story 4 - Store Partner QR Verification & Anti-Replay Redemption (Priority: P2)

As a Store Partner, I want to authenticate as a merchant and verify a consumer's pickup QR code (by scanning or submitting the QR payload) so that the order is marked completed once and cannot be reused.

**Why this priority**: Completes the end-to-end food-rescue lifecycle from discovery to in-store handoff and demonstrates anti-replay security in the demo.

**Independent Test**: Can be tested by signing in as the store owner, submitting a consumer's valid QR payload to mark the order `COMPLETED`, and submitting the exact same QR payload a second time to confirm it is rejected as already used.

**Acceptance Scenarios**:

1. **Given** an authenticated store partner submits a valid, unexpired, unused QR payload belonging to their own store, **When** verification runs, **Then** the QR token is marked used, the order transitions to `COMPLETED`, and a confirmation summary with Green Points awarded is displayed.
2. **Given** the same QR payload has already been redeemed, **When** the store partner submits it again, **Then** the system rejects the second attempt with an "already used" warning (anti-replay protection).
3. **Given** a store partner attempts to verify a QR code belonging to a different store, or an invalid/tampered QR payload, **When** verification runs, **Then** the system rejects the request with an authorization or invalid-signature error.

---

### Edge Cases

- What happens when the browser denies geolocation or has no GPS hardware? The application falls back cleanly to default District 1, Ho Chi Minh City coordinates (`10.7769, 106.7009`) and notifies the user with an option to retry.
- What happens when an unauthenticated user browses the discovery map and clicks "Rescue Now"? The user is prompted or redirected to `/login` and returned to continue their flow after signing in.
- What happens when a consumer tries to cancel an order that is already `COMPLETED`, `CANCELLED`, or past `pickup_deadline`? The cancellation button is disabled where applicable, and any direct request is rejected with a conflict status (`409`) without restoring stock twice.
- What happens when `remaining_quantity` reaches `0` after an order? The dish transitions to `SOLD_OUT` and is removed from active purchasable stock until cancelled or restocked.
- What happens when a consumer requests a pickup QR for an order that does not yet have a stored QR token? The system issues a signed single-use QR token bound to `order_id`, `consumer_id`, and `pickup_deadline` idempotently (reusing an active valid token if one already exists).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to register and sign in as `CONSUMER` or `STORE_PARTNER` and persist session tokens for authenticated requests.
- **FR-002**: System MUST return approved stores within a configurable radius (`1–10 km`) around given coordinates, optionally filtered by food category, sorted by distance ascending.
- **FR-003**: System MUST display active surplus dishes with deterministic time-shifted pricing, remaining quantity, pickup window, and allergen notes.
- **FR-004**: System MUST allow `CONSUMER` users to place rescue orders (`POST /orders`) with atomic stock decrement so `remaining_quantity` never drops below `0`.
- **FR-005**: System MUST compute environmental impact (`2.5 kg CO2e` per dish) and Green Points (`10 points per kg CO2e`) on every created order.
- **FR-006**: System MUST allow `CONSUMER` owners and `STORE_PARTNER` owners to cancel eligible orders (`CONFIRMED` / `READY_FOR_PICKUP`) before `pickup_deadline`, atomically restoring dish stock.
- **FR-007**: System MUST allow `CONSUMER` order owners to retrieve or generate a signed, single-use, time-bounded pickup QR payload (`ecobite://pickup?...`) for an active order.
- **FR-008**: System MUST allow `STORE_PARTNER` owners to verify pickup QR payloads (`POST /orders/verify-qr`), validating cryptographic signature, expiration, store ownership, and single-use status before completing the order.
- **FR-009**: Frontend MUST provide cohesive navigable screens for Login/Register, Radar Discovery & Order Placement, Consumer Order History & QR Display, and Store Partner QR Verification.

### Key Entities

- **User**: Authenticated actor with role (`CONSUMER`, `STORE_PARTNER`, `ADMIN`) and Green Points balance.
- **Store**: Approved F&B partner with geographic point coordinates (`latitude`, `longitude`), KYC status, and rating/impact metrics.
- **Dish**: Time-bound surplus meal listing linked to a Store and base MenuItem, tracking `original_price`, `rescue_price`, `rule_discount_price`, `pickup_start_time`, `pickup_end_time`, `remaining_quantity`, and `status` (`ACTIVE`, `SOLD_OUT`, etc.).
- **Order**: Food rescue reservation binding Consumer, Store, and Dish with unique `order_code`, `quantity`, `total_amount`, `co2_saved_kg`, `green_points_earned`, `pickup_deadline`, and `status` (`CONFIRMED`, `COMPLETED`, `CANCELLED`).
- **QRToken**: Single-use cryptographic pickup credential linked 1-to-1 with an Order, containing `nonce`, `token_hash` (HMAC-SHA256 signature), `expires_at`, and `is_used`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A consumer can log in, discover nearby stores within 1–10 km, place a rescue order, and view the generated pickup QR code end-to-end in under 60 seconds.
- **SC-002**: Under 50 concurrent purchase requests for a dish with stock `2`, exactly 2 orders succeed (`201`), 48 requests fail cleanly (`409`), and final stock equals `0` with zero overselling.
- **SC-003**: Cancelling a `CONFIRMED` order restores 100% of its reserved quantity to the dish inventory atomically; repeated cancellation attempts are rejected.
- **SC-004**: Store partner QR verification completes a valid order on the first scan and rejects 100% of replay attempts or cross-store scans.
- **SC-005**: All automated backend quality checks (`ruff`, `mypy`, full `pytest` suite) and frontend checks (`eslint`, `tsc --noEmit`, `next build`) pass with zero errors.

## Assumptions

- Local demo execution uses realistic seeded HCMC stores (with dishes covering active daytime/evening demo hours) and seeded demo accounts (`consumer.an@ecobite.vn` and `merchant.bui@ecobite.vn`).
- Payment integration (VNPay gateway callback) is out of scope for this functional group; orders default to `COD` or simulated `VNPAY` status for the rescue-to-QR pickup flow.
