# Feature Specification: Auth, Store KYC, Base Menu Catalog, Surplus Dishes & Rule-Based Time-Shift Discounting

**Feature Branch**: `dev`

**Created**: 2026-11-28

**Status**: In Progress (Core Backend & Admin/Store Portals Delivered; Frontend Polish & Verification Remaining)

**Input**: User description: "EcoBite Feature 003 — Core F1 (JWT Dual-Token Auth, RBAC, Store KYC Onboarding, store self-lookup, Admin KYC Review), Core F2 (Base Menu Catalog CRUD, Surplus Dish creation, 1-tap batch publish, real-time stock control), and Core F3 (Deterministic Rule-Based Time-Shift Discounting: 40–50% standard rescue, 70% last-minute 30–45 minute rush, live countdown, optional fixed clearance price override)."

## Summary *(mandatory)*

Food-rescue marketplaces fail in Vietnam when consumers cannot trust food hygiene, merchants face friction re-entering dish details every shift, or unpredictable pricing undermines transparency. This feature establishes the foundational trust, supply, and deterministic pricing backbone across all three EcoBite user roles—**Consumers**, **Store Partners**, and **System Administrators**. It provides secure account registration, dual-token session management, and strict role enforcement; mandatory food-safety verification (KYC / ATVSTP) where administrators approve or reject partner applications before selling is unlocked; a persistent Base Menu Catalog so approved merchants maintain verified retail prices, photos, ingredients, and base allergens once; single and atomic batch surplus-dish publishing with real-time stock control; and a deterministic rule-based time-shift discounting engine that transparently shifts prices from a standard 50% rescue discount to a 70% last-minute clearance discount in the final 45 minutes before pickup closes, accompanied by a live countdown.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Account Registration, Dual-Token Authentication & Role-Based Access Control (Priority: P1)

As a platform user (Consumer, Store Partner, or Administrator), I want to register safely, sign in with email and password to receive short-lived access credentials paired with a renewable session credential, view my own profile, and have navigation and actions restricted strictly to my assigned role so that accounts cannot be hijacked or escalated to privileged roles.

**Why this priority**: Identity verification and strict server-side role boundaries are the non-negotiable foundation protecting merchant KYC approvals, store catalog ownership, order placement, and administrative controls.

**Independent Test**: Can be fully tested by registering a new consumer account, attempting to inject a privileged role during public registration (expecting rejection), logging in to obtain access and refresh credentials, inspecting the authenticated profile, refreshing an expiring session, verifying that refresh credentials cannot be used directly on protected resources, and confirming deactivated users are immediately denied access.

**Acceptance Scenarios**:

1. **Given** a new visitor provides a unique email address, full name, optional phone number, and a password of at least 8 characters, **When** they register an account, **Then** the system creates an active `CONSUMER` account, stores only an irreversible password hash, and returns the public user profile without ever exposing password data.
2. **Given** an untrusted client submits an unauthorized field such as `role: "admin"` or `role: "store_partner"` during public registration, **When** the registration payload is validated, **Then** the system rejects the request immediately and refuses to create an elevated account.
3. **Given** a registered user submits valid credentials (email and password), **When** they sign in, **Then** the system returns both a short-lived access token and a longer-lived refresh token alongside essential profile details including their role; invalid credentials return an authentication error without revealing whether the email exists.
4. **Given** an authenticated user holds a valid refresh token and an active account, **When** they request a session refresh, **Then** the system issues a fresh access and refresh token pair; if a refresh token is presented directly as a bearer credential on a protected action, the system rejects it as unauthorized.
5. **Given** an administrator deactivates a user account (`is_active = false`), **When** that user presents a previously issued, unexpired access token or refresh token, **Then** the system denies access across all protected actions immediately.
6. **Given** an authenticated user views the application navigation bar, **When** their role is `CONSUMER`, `STORE_PARTNER`, or `ADMIN`, **Then** they see only the navigation destinations corresponding to their role and protected pages redirect unauthorized visitors away.

---

### User Story 2 - Store Partner KYC Onboarding, Self-Lookup & Admin Food-Safety Verification (Priority: P1)

As a Store Partner, I want to submit my storefront details, geographic location, and food-safety certification (ATVSTP) and check my own approval status, and as a System Administrator, I want to review pending applications and approve or reject them with a clear reason so that only verified, hygienic merchants can list surplus food.

**Why this priority**: Mandatory food-safety verification builds consumer trust and prevents unverified kitchens from publishing surplus meals onto the public rescue marketplace.

**Independent Test**: Can be fully tested by authenticating as a Store Partner, submitting a store onboarding application with valid coordinates and license reference, checking self-lookup status (`PENDING`), attempting to manage menu items while pending (expecting denial), signing in as an Admin on the KYC review dashboard to approve or reject the store, and verifying that approval immediately unlocks store catalog operations while rejection records the reason and removes the store from the pending queue.

**Acceptance Scenarios**:

1. **Given** an authenticated `STORE_PARTNER` provides a valid store name, physical address, WGS84 geographic coordinates (`latitude` within `[-90, 90]`, `longitude` within `[-180, 180]`), optional contact details, and food-safety license reference, **When** they submit store onboarding, **Then** the system creates the store with `kyc_status = PENDING` and informs the partner that administrative review is pending.
2. **Given** an authenticated `CONSUMER` attempts to submit store onboarding or query merchant self-lookup, **When** the system verifies permissions, **Then** the request is denied as forbidden.
3. **Given** an authenticated `STORE_PARTNER` checks their own store profile, **When** they own an onboarded store, **Then** the system returns their full storefront details, decoded coordinates, and current `kyc_status` (plus any `kyc_reject_reason`); if they have not onboarded a store yet, the system returns a clear not-found status prompting onboarding.
4. **Given** an authenticated `ADMIN` opens the KYC Review Dashboard, **When** pending store applications exist, **Then** the dashboard lists all `PENDING` stores newest-first with address, contact info, and food-safety certificate link, and allows one-click approval (`APPROVED`) or rejection (`REJECTED`) with a required rejection reason.
5. **Given** a non-admin user (`CONSUMER` or `STORE_PARTNER`) attempts to list pending KYC applications or submit a review decision, **When** the request is processed, **Then** the system denies access as forbidden.

---

### User Story 3 - Base Menu Catalog Management with Store Ownership Isolation (Priority: P1)

As an approved Store Partner, I want to create, view, update, and retire canonical items in my store's Base Menu Catalog—complete with standard retail prices, verified high-resolution images, categories, ingredients, base allergens, and dietary classification—so that end-of-shift surplus listings automatically inherit accurate data and prevent inflated original prices.

**Why this priority**: A verified Base Menu Catalog eliminates repetitive shift-end data entry, guarantees transparent dish-by-dish listings ("No Mystery Bags"), prevents fake inflated retail prices, and serves as the authoritative grounding catalog for downstream AI Quick-Post.

**Independent Test**: Can be fully tested by signing in as an approved Store Partner, opening the Store Menu portal, creating a canonical menu item, listing active items, updating its name or price, soft-deleting it so it leaves the active list, and verifying that another Store Partner cannot view, modify, or delete items belonging to this store.

**Acceptance Scenarios**:

1. **Given** an authenticated `STORE_PARTNER` owns an `APPROVED` store, **When** they add a menu item with name, category (`RICE`, `NOODLES`, `BAKERY`, `BEVERAGE`, `VEGETARIAN`, or `OTHER`), strictly positive `original_price`, image link, standard ingredients, base allergens, and dietary type, **Then** the item is persisted as active and appears in the store's catalog listing.
2. **Given** a `STORE_PARTNER` whose store is `PENDING` or `REJECTED` attempts to add a menu item, **When** the request is checked, **Then** the system blocks the action and explains that food-safety (KYC) approval is required first.
3. **Given** an approved `STORE_PARTNER` edits an existing menu item they own or soft-deletes it, **When** the update or deletion completes, **Then** modified fields are saved immediately and soft-deleted items (`is_active = false`) disappear from active catalog listings without breaking historical surplus dishes referencing them.
4. **Given** Store Partner B attempts to create, list, update, or delete menu items belonging to Store Partner A, **When** ownership validation executes on the server, **Then** the system rejects every cross-store attempt as forbidden.

---

### User Story 4 - Surplus Dish Publishing, Atomic Batch Post & Real-Time Stock Control (Priority: P1)

As an approved Store Partner wrapping up a shift, I want to publish individual surplus dish listings or an entire multi-dish batch grounded in my Base Menu Catalog and adjust remaining stock in real time so that leftover food reaches nearby consumers accurately without overselling.

**Why this priority**: Converting Base Menu items into live, inventory-controlled surplus listings is the core supply-side workflow feeding both the consumer Radar and atomic order checkout.

**Independent Test**: Can be fully tested by signing in as an approved Store Partner on the Surplus Dishes portal, selecting an active Base Menu item, publishing a single surplus listing with quantity and pickup window, publishing a multi-item batch in one transaction, confirming canonical name/image/original price/ingredients are inherited automatically, adjusting remaining quantity down to `0` (`SOLD_OUT`) and back within `total_quantity`, and verifying invalid stock or cross-store operations are rejected.

**Acceptance Scenarios**:

1. **Given** an approved `STORE_PARTNER` publishes a surplus dish referencing an active `menu_item_id` from their own store with `total_quantity > 0` and `pickup_end_time > pickup_start_time`, **When** the listing is created, **Then** it automatically inherits canonical `name`, `description`, `category`, `image_url`, `original_price`, `ingredients`, and `dietary_type` from the Base Menu item, stores two-tier `allergens` (`EXPLICIT` / `INFERRED`) and `dietary_notes`, and opens as `ACTIVE` (or `SOLD_OUT` if initial `remaining_quantity == 0`).
2. **Given** an approved `STORE_PARTNER` submits a batch of one or more surplus dishes sharing a pickup window, **When** all referenced menu items are active and belong to the same store, **Then** all dishes are created atomically in a single transaction; if any item is missing, inactive, or belongs to a different store, the entire batch is rejected with zero partial writes.
3. **Given** an approved `STORE_PARTNER` adjusts the remaining quantity of an active dish they own, **When** the new quantity is between `0` and `total_quantity` inclusive, **Then** remaining stock updates atomically and status transitions automatically to `SOLD_OUT` at `0` (hiding it from active listings) or back to `ACTIVE` when raised above `0`; negative values or values exceeding `total_quantity` are rejected.
4. **Given** Store Partner B attempts to publish a dish using Store Partner A's menu item, view Store Partner A's active dishes, or modify Store Partner A's stock, **When** ownership is checked, **Then** the request is rejected as forbidden.

---

### User Story 5 - Deterministic Rule-Based Time-Shift Discounting & Live Countdown (Priority: P2)

As a Store Partner and Consumer, I want surplus dish prices to follow transparent, deterministic time-shift rules—50% off during the standard rescue window and 70% off during the final 45-minute rush before closing (or an optional partner-set fixed clearance price)—with a live countdown so that consumers see trustworthy discounts and kitchens clear 100% of perishable inventory before closing.

**Why this priority**: Deterministic time-shifted pricing removes unpredictable black-box price guessing, creates clear urgency to rescue meals before closing, and ensures merchants and consumers agree on exact prices at every minute of the shift.

**Independent Test**: Can be fully tested by evaluating pricing rules at timestamps before and inside the final 45-minute window (confirming 50% standard discount and 70% last-minute rush discount with `is_rule_discount_active` toggling cleanly), supplying a custom `rule_discount_start_time` inside the pickup window, supplying a valid `override_discounted_price` (confirming fixed precedence over time-shift rules), verifying `override_discounted_price > original_price` is rejected, and checking the live countdown timer reaching zero once rush/closing arrives.

**Acceptance Scenarios**:

1. **Given** a surplus dish with `original_price = 50,000 VND`, pickup window `14:00–16:00`, and no manual price override, **When** evaluated at `14:30` (outside the final 45-minute rush window), **Then** the active price is `25,000 VND` (`-50%`), the scheduled last-minute price is `15,000 VND` (`-70%`), and the rush flag is inactive (`false`).
2. **Given** the same surplus dish, **When** evaluated at `15:30` (within the final 45 minutes before `16:00`, or on/after a custom `rule_discount_start_time` inside the pickup window), **Then** the active price automatically drops to `15,000 VND` (`-70%`) and the rush flag becomes active (`true`).
3. **Given** a Store Partner explicitly provides `override_discounted_price = 18,000 VND` (`0 < override <= original_price`), **When** the dish is evaluated at any time during the pickup window (including the final 45 minutes), **Then** the active price remains `18,000 VND` with the rush flag inactive (`false`), while still recording the reference 70% price (`15,000 VND`).
4. **Given** a Store Partner submits an `override_discounted_price` that is less than or equal to `0` or greater than `original_price`, **When** validation runs, **Then** the system rejects the listing with a clear validation error.
5. **Given** a dish is published during its own final 45-minute rush window, **When** the listing is persisted and later queried, **Then** its baseline standard rescue price (`rescue_price`) remains the canonical 50% price (or explicit override) while its live `current_price` dynamically reflects the active 70% rush discount.
6. **Given** a dish has time remaining before its last-minute rush or pickup deadline, **When** viewed by a user, **Then** the countdown calculation returns the exact non-negative remaining seconds (`HH:MM:SS` in the UI) and clamps cleanly to `0` once the threshold has passed.

---

### Edge Cases

- **Duplicate email registration**: Attempting to register with an email already present returns a conflict error (`409`) without revealing stored account metadata.
- **Short or weak password / invalid email**: Passwords shorter than 8 characters or malformed email addresses are rejected during validation before hashing.
- **Production misconfiguration of signing secret**: Starting the system in a production environment with a default placeholder signing secret MUST fail fast at startup so forged tokens can never be accepted.
- **Missing OS timezone database**: Running on environments lacking system IANA timezone files MUST fall back gracefully to UTC+7 (`Asia/Ho_Chi_Minh`) without crashing module imports or time-based calculations.
- **Out-of-range GPS coordinates or blank store metadata**: Onboarding with blank store name/address or latitude outside `[-90, 90]` / longitude outside `[-180, 180]` is rejected before persistence.
- **Admin review with invalid decision or nonexistent store**: Submitting a decision other than `APPROVED` or `REJECTED`, or reviewing an unknown store identifier, returns a clean validation or not-found error.
- **Soft-deleted menu item referenced at publish time**: Attempting to create a single or batch surplus dish from a soft-deleted (`is_active = false`) menu item is rejected (`404`), while previously created surplus dishes retain their copied snapshot data.
- **Invalid pickup or rush discount windows**: Submitting `pickup_end_time <= pickup_start_time`, or `rule_discount_start_time` outside `[pickup_start_time, pickup_end_time]`, is rejected with a validation error.
- **Concurrent stock modification or excess quantity update**: Setting remaining quantity below `0` or above `total_quantity` is rejected (`422`), and concurrent updates that fail the atomic row check return a conflict error (`409`) rather than corrupting stock.
- **Zero-portion initial publish (`remaining_quantity = 0`)**: Permitted when `total_quantity > 0`, immediately initializing the dish status as `SOLD_OUT`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Public Consumer Registration)**: System MUST allow public registration of new accounts with validated email, full name, optional phone number, and password (`8–128` characters), MUST hash passwords irreversibly before persistence, MUST reject duplicate emails, and MUST strictly forbid clients from supplying or escalating the `role` field (always assigning `CONSUMER`).
- **FR-002 (Dual-Token Authentication & Refresh)**: System MUST authenticate registered users with email and password (supporting both JSON and standard form credentials), issue a signed short-lived access token (`type = "access"`) and a longer-lived refresh token (`type = "refresh"`), and allow active users to exchange a valid refresh token for a fresh token pair.
- **FR-003 (Token Type, Active-User & Role Enforcement)**: System MUST verify token signature, expiration, `type == "access"`, and `user.is_active == true` on every protected request (rejecting invalid/refresh tokens as unauthorized and deactivated accounts as forbidden), and MUST enforce server-side role checks across `CONSUMER`, `STORE_PARTNER`, and `ADMIN`.
- **FR-004 (Current User Profile)**: System MUST allow any authenticated, active user to retrieve their own profile without ever returning password hashes.
- **FR-005 (Store Partner KYC Onboarding)**: System MUST allow authenticated `STORE_PARTNER` (or `ADMIN`) accounts to register a store with non-empty name and address, validated WGS84 coordinates (`latitude` in `[-90, 90]`, `longitude` in `[-180, 180]`), optional contact details, and food-safety license reference, initializing `kyc_status` to `PENDING`.
- **FR-006 (Store Self-Lookup)**: System MUST allow an authenticated `STORE_PARTNER` to retrieve their own onboarded store profile, decoded coordinates, and KYC status (including rejection reason if rejected), returning not-found when no store has been onboarded yet and forbidden for non-partner roles.
- **FR-007 (Admin KYC Verification Workflow)**: System MUST allow only `ADMIN` users to list all `PENDING` store applications (newest first) and record an `APPROVED` or `REJECTED` decision (storing `kyc_reject_reason` on rejection and clearing it on approval), and MUST provide an Admin KYC Dashboard supporting this workflow.
- **FR-008 (KYC Approval Gate)**: System MUST prevent stores whose `kyc_status != APPROVED` from adding Base Menu items or publishing single/batch surplus dishes, returning a clear forbidden error explaining that KYC approval is required.
- **FR-009 (Base Menu Catalog CRUD)**: System MUST allow an approved store's owner to create, list active, partially update, and soft-delete (`is_active = false`) canonical Base Menu items containing name, description, category (6 standard categories), strictly positive `original_price`, image link, standard ingredients, base allergens, and dietary classification.
- **FR-010 (Strict Store Ownership Isolation)**: System MUST verify on the server that the authenticated `STORE_PARTNER` owns the target store (directly via `store_id` or indirectly via `menu_item_id` or `dish_id`) for every menu catalog and surplus dish mutation or private listing, rejecting cross-store access as forbidden.
- **FR-011 (Single Surplus Dish Publishing with Menu Grounding)**: System MUST allow approved store owners to publish a surplus dish grounded in an active owned Base Menu item, automatically inheriting canonical name, description, category, image, original price, standard ingredients, and dietary type, while storing pickup window, quantities, optional override price, two-tier allergen warnings (`EXPLICIT` / `INFERRED`), and dietary notes.
- **FR-012 (Atomic Multi-Dish Batch Publishing)**: System MUST allow approved store owners to publish one or more menu-grounded surplus dishes sharing a pickup window inside a single atomic transaction, rejecting the entire batch if any item is missing, inactive, or belongs to a different store.
- **FR-013 (Active Surplus Listing & Real-Time Stock Control)**: System MUST allow approved store owners to list their `ACTIVE` surplus dishes and atomically update `remaining_quantity` within `[0, total_quantity]`, automatically toggling status between `SOLD_OUT` (`0`) and `ACTIVE` (`> 0`) and rejecting negative or excess quantities.
- **FR-014 (Deterministic Rule-Based Time-Shift Discounting)**: System MUST compute surplus dish pricing strictly via deterministic time rules (never AI price estimation):
  - Standard rescue window: `50%` off `original_price` (rounded half-up to 2 decimal places).
  - Final rush window (default final `45` minutes before `pickup_end_time`, clamped to `pickup_start_time`, or custom `rule_discount_start_time` within `[pickup_start_time, pickup_end_time]`): `70%` off `original_price` with `is_rule_discount_active = true`.
  - Explicit manual clearance override (`override_discounted_price`): when provided and valid (`0 < override <= original_price`), MUST take fixed precedence over time-shift tiers with `is_rule_discount_active = false`.
- **FR-015 (Countdown Calculation)**: System MUST compute non-negative seconds remaining until the last-minute discount threshold or pickup deadline so client interfaces can display a live countdown timer.
- **FR-016 (Role-Aware Portal Interfaces)**: System MUST provide dedicated client workflows for authentication (`/login`, `/register`), Store KYC onboarding (`/store/onboard`), Admin KYC verification (`/admin`), Base Menu Catalog management (`/store/menu`), and Surplus Dish publishing & stock adjustment (`/store/dishes`), plus role-aware navigation surfacing only destinations permitted for the signed-in role.
- **FR-017 (Allergen Transparency on Surplus Listings)**: System MUST preserve two-tier allergen annotations (`EXPLICIT` vs `INFERRED`) and local dietary notes on published surplus dishes so consumers receive transparent safety warnings rather than mystery-bag descriptions.
- **FR-018 (Frontend Automated Test Readiness)**: System MUST provide a clean, working frontend automated test configuration so critical authentication, navigation, pricing preview, and countdown components are verifiable through automated tests.

### Non-Functional Requirements *(mandatory when the feature touches money, health, or personal data)*

- **NFR-001 (Performance)**: Standard authentication, store lookup, menu catalog CRUD, and surplus dish publish/stock-update endpoints MUST complete within `< 200 ms` at the 95th percentile under normal local/staging load using fully asynchronous database I/O with zero blocking calls.
- **NFR-002 (Security & Privacy)**: Passwords MUST be hashed with bcrypt and never logged or returned in responses; JWT tokens MUST be signed with environment-managed secrets (`SECRET_KEY`), fail fast in production if left at default placeholders, include explicit `iat`/`exp`/`type` claims, and reject invalid tokens with `401` + `WWW-Authenticate: Bearer`; all privileged routes MUST enforce server-side role and ownership checks.
- **NFR-003 (Data Integrity & Concurrency)**: Surplus dish inventory MUST enforce a database-level non-negative constraint (`remaining_quantity >= 0`), stock updates MUST execute atomically with upper-bound checks (`total_quantity >= quantity`), and batch dish publication MUST commit or roll back as a single atomic transaction.
- **NFR-004 (Food Safety & Pricing Determinism)**: Unapproved stores (`PENDING`/`REJECTED`) MUST have 0% ability to create menu items or publish surplus dishes; time-shift pricing MUST be 100% deterministic with exact decimal arithmetic (`Decimal`, `ROUND_HALF_UP`) and zero AI-based price guessing.
- **NFR-005 (Observability & Portability)**: Errors MUST surface via accurate HTTP status codes (`400`, `401`, `403`, `404`, `409`, `422`) with clear user-facing diagnostics; geographic coordinates, JSON fields, and timezone logic MUST operate seamlessly across both production PostgreSQL+PostGIS and local/CI SQLite test environments without platform crashes.

### Key Entities *(include if feature involves data)*

- **User Account**: Represents an authenticated platform participant (`CONSUMER`, `STORE_PARTNER`, or `ADMIN`) with unique email, irreversibly hashed password, full name, optional phone, active/verified flags, Green Points balance, and timestamps.
- **Partner Store**: Represents an F&B merchant storefront owned by a `STORE_PARTNER`, holding business identity, physical address, geographic point coordinates (WGS84), food-safety license link, KYC status (`PENDING`, `APPROVED`, `REJECTED`), optional rejection reason, and aggregated rating/CO₂ metrics.
- **Base Menu Item**: Represents a canonical dish in a Partner Store's permanent menu catalog, holding standard name, description, category, verified retail `original_price`, high-resolution image, standard ingredients, base allergens, dietary type, and soft-delete active flag.
- **Surplus Dish Listing**: Represents an active shift-end rescue offer derived from a Base Menu Item, holding inherited display/pricing metadata, deterministic standard (`rescue_price`) and last-minute (`rule_discount_price`) prices, optional `override_discounted_price`, pickup and rush-start times, `total_quantity`, `remaining_quantity` (`>= 0`), lifecycle status (`ACTIVE`, `SOLD_OUT`, `EXPIRED`, `INACTIVE`), two-tier allergen warnings, and dietary notes.
- **Time-Shift Discount Schedule**: A deterministic pricing calculation over `(original_price, pickup_start_time, pickup_end_time, rule_discount_start_time, override_discounted_price, current_time)` producing `(current_price, rule_discount_price, is_rule_discount_active)` and countdown seconds.
- **Two-Tier Allergen Warning**: A food-safety warning attached to a Surplus Dish Listing identifying the allergen, risk severity (`HIGH`, `MEDIUM`, `LOW`), provenance (`EXPLICIT` vs `INFERRED`), and optional explanation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Zero Privilege Escalation & Token Confusion)**: `100%` of public registration attempts attempting to assign elevated roles (`ADMIN` / `STORE_PARTNER`), `100%` of refresh tokens presented as bearer access tokens, and `100%` of requests from deactivated accounts (`is_active = false`) are rejected server-side across unit, integration, and property-based tests.
- **SC-002 (100% KYC Food-Safety Gating)**: `0%` of `PENDING` or `REJECTED` stores can add Base Menu items or publish surplus dishes; an Administrator can review and approve or reject a pending store application in under 30 seconds on the Admin KYC Dashboard.
- **SC-003 (100% Store Ownership Isolation)**: `0%` of cross-store menu catalog or surplus dish reads/mutations succeed when initiated by a different authenticated Store Partner.
- **SC-004 (Menu-Grounded Publish Speed & Integrity)**: An approved Store Partner can create a Base Menu item and publish a grounded surplus dish (inheriting canonical name, image, retail price, and ingredients with zero manual re-entry) in under 60 seconds, with `100%` batch atomicity on multi-dish publication.
- **SC-005 (100% Deterministic Pricing Accuracy)**: Time-shift discount calculations match the configured `50%` standard, `70%` final 45-minute rush, and explicit override rules with exact decimal precision (`0` rounding drift and `0` wall-clock persistence defects) across all hours of the day.
- **SC-006 (Automated Quality Gate Compliance)**: All backend lint, format, static type-check, and automated unit/integration/property tests, plus frontend lint, TypeScript strict type-check, Vitest component tests, and production build pass with `0` errors.

## Assumptions

- **Scope Boundary with Existing Features**: PostGIS Radar Discovery (`GET /stores/nearby`), atomic order placement/cancellation, VNPay checkout, HMAC-SHA256 QR pickup, Verified Reviews, and Green Points/Vouchers are covered by Feature `001` (`specs/001-rescue-discovery-order-qr/`) and subsequent PA4 specs; AI multimodal voice/text extraction (`POST /ml/parse-dish-nlp`) is covered by Feature `002` (`specs/002-ai-quick-post-nlp/`). Feature `003` focuses strictly on Core F1 (Auth & KYC), Core F2 (Base Menu Catalog & Surplus Dishes), and Core F3 (Rule-Based Time-Shift Discounting).
- **Privileged Account Provisioning**: Because public self-registration strictly creates `CONSUMER` accounts to prevent privilege escalation (`EC4-05`), `STORE_PARTNER` and `ADMIN` accounts are provisioned via administrative seeding or dedicated partner-upgrade workflows rather than self-selecting `role` on the public registration endpoint.
- **Local Currency & Timezone**: All monetary amounts represent Vietnamese Dong (`VND`) stored with `Numeric(12, 2)` precision, and store shift pickup windows operate within a single calendar day in `Asia/Ho_Chi_Minh` (`UTC+7`).
- **Certificate Reference Storage**: In PA3/PA4, store food-safety certificates (`kyc_license_url`) are submitted as validated document/image URLs on `POST /api/v1/stores/onboard`; dedicated cloud object-storage upload middleware is outside the scope of this feature.
- **Frontend Alignment Scope**: Core backend endpoints and tests (`EC4-02`, `EC4-05`) and primary Admin/Store portals (`EC4-11`, `Navbar` from `EC4-13`) are already implemented in the repository; remaining work tracked in `tasks.md` covers frontend `package.json` cleanup (`EC4-10`), aligning legacy `/login`, `/register`, and `/store/onboard` client payloads with hardened backend contracts, fixing the wall-clock persistence bug in `DishService._build_dish`, and adding Vitest component tests (`EC4-14`).
