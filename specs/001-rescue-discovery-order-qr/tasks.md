# Tasks: Consumer Surplus Discovery, Anti-Overselling Order & Dynamic QR Pickup

**Input**: Design documents from `/specs/001-rescue-discovery-order-qr/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api-contracts.md`, `quickstart.md`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`, `[US4]`)

---

## Phase 1: Setup & Backend Baseline Stabilization

**Purpose**: Ensure backend static checks, transaction handling, concurrency benchmark, and demo seed data are healthy before building end-to-end features.

- [X] T001 Fix ruff lint issues (`I001`, `B904`), formatting (`ruff format`), and `OrderService` transaction/rollback handling (`MissingGreenlet` prevention and safe savepoints) in `backend/app/services/order_service.py` and `backend/tests/integration/test_order_concurrency.py`
- [X] T002 Run `ruff format` across `backend/app/repositories/dish_repo.py`, `backend/app/repositories/order_repo.py`, `backend/app/services/order_service.py`, and `backend/app/services/qr_service.py`
- [X] T003 Update selected daytime/evening demo dish pickup windows (`06:00`–`23:59`) in `backend/app/db/seed.py` so live demo ordering works at any hour

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core frontend utilities, Axios client, aligned service types, and shared root layout required by every user story.

- [X] T004 [P] Create Tailwind/formatting utility helpers (`cn`, `formatVND`, `formatDistance`, `formatPickupDeadline`) in `frontend/src/lib/utils.ts`
- [X] T005 [P] Create Axios API client with `NEXT_PUBLIC_API_BASE_URL`, automatic Bearer header injection, and 401 refresh handling in `frontend/src/lib/api-client.ts`
- [X] T006 [P] Expand shared TypeScript DTOs (`OrderResponse`, `OrderDetailResponse`, `QRPayloadResponse`, `QRVerificationResponse`, `CreateOrderPayload`) in `frontend/src/types/api.ts`
- [X] T007 [P] Create Tailwind + Leaflet global stylesheet in `frontend/src/app/globals.css` and root layout wrapping `QueryProvider`, `Navbar`, and `BottomNavigation` in `frontend/src/app/layout.tsx`
- [X] T008 Update `Navbar` (auth user state, logout, `/orders`, `/store/verify-qr`) in `frontend/src/components/ui/Navbar.tsx` and `BottomNavigation` in `frontend/src/components/ui/BottomNavigation.tsx`
- [X] T009 [P] Build Login page (`/login` with quick Demo Consumer & Store Partner fill) in `frontend/src/app/login/page.tsx` and Register page in `frontend/src/app/register/page.tsx`

**Checkpoint**: Shared layout, API client, and authentication UI ready.

---

## Phase 3: User Story 1 - Location-Based Surplus Discovery Radar (Priority: P1) 🎯 MVP

**Goal**: Consumers see approved nearby stores on an interactive Leaflet Radar map and sorted list, filtered by radius (`1–10 km`) and food category, with live time-shifted discounts.

**Independent Test**: Open `/` logged in or anonymous, adjust radius (`1–10 km`) and category chips, verify Leaflet markers/radius circle and store/dish cards update from `GET /api/v1/stores/nearby`.

- [X] T010 [P] [US1] Align `discoveryService.getNearbyStores` to call `GET /stores/nearby` with `{ lat, lng, radius_km, category }` returning `NearbyStoresResponse` in `frontend/src/services/discovery.service.ts`
- [X] T011 [P] [US1] Replace placeholder with interactive Leaflet map (`MapContainer`, `TileLayer`, `Circle`, store/user `Marker`s + `Popup`) in `frontend/src/components/radar/RadarMap.tsx` and update `frontend/src/components/radar/DynamicRadarMap.tsx`
- [X] T012 [US1] Implement Consumer Discovery Radar page with `useGeolocation`, radius slider (`1–10 km`), category filter, `DynamicRadarMap`, and store/dish cards in `frontend/src/app/page.tsx`

---

## Phase 4: User Story 2 - Atomic Rescue Order Placement & Anti-Overselling (Priority: P1)

**Goal**: Authenticated consumers can place a rescue order from a dish card (`POST /api/v1/orders`), immediately decrementing stock, calculating CO2e & Green Points, and cleanly rejecting oversell attempts (`409`).

**Independent Test**: Click "Giải cứu ngay" on a dish, place order for valid quantity -> verify `201` confirmation + stock decrement; attempt quantity > remaining stock -> verify `409` error toast and unchanged stock.

- [X] T013 [P] [US2] Align `orderService` payloads and responses (`total_amount`, `green_points_earned`, `co2_saved_kg`, `payment_method`, `createRescueOrder`, `cancelOrder`, `getMyOrders`, `getOrderDetail`, `issueOrderQr`, `verifyOrderQr`) in `frontend/src/services/order.service.ts`
- [X] T014 [US2] Add interactive Rescue Order modal (quantity picker, COD/VNPAY selector, CO2/Green Points preview, `409` anti-overselling error feedback, and React Query cache invalidation) inside `frontend/src/app/page.tsx`

---

## Phase 5: User Story 3 - My Orders, Cancellation & Dynamic Pickup QR (Priority: P1)

**Goal**: Consumers view their orders, cancel eligible orders before pickup deadline (restoring stock), and generate/display signed single-use HMAC-SHA256 QR codes.

**Independent Test**: Visit `/orders`, click "Xem mã QR" on a `CONFIRMED` order -> verify `POST /api/v1/orders/{id}/qr` returns `ecobite://pickup?...` and renders `<QRCodeSVG />`; cancel a `CONFIRMED` order -> verify status changes to `CANCELLED` and stock restores.

- [X] T015 [P] [US3] Add `QRPayloadResponse` schema in `backend/app/schemas/order.py`
- [X] T016 [US3] Implement `OrderService.issue_or_get_qr_payload` in `backend/app/services/order_service.py` and expose `POST /api/v1/orders/{order_id}/qr` in `backend/app/api/v1/endpoints/orders.py`
- [X] T017 [US3] Add integration tests for `POST /api/v1/orders/{order_id}/qr` (generation, idempotency, RBAC 403, invalid status 409) in `backend/tests/integration/test_api_orders.py`
- [X] T018 [US3] Build Consumer My Orders page (`/orders`) with status filters, order cards, Cancel action, and Dynamic QR Modal (`QRCodeSVG` + copy payload) in `frontend/src/app/orders/page.tsx`

---

## Phase 6: User Story 4 - Store Partner QR Verification & Anti-Replay Redemption (Priority: P2)

**Goal**: Store Partners verify consumer QR payloads via `POST /api/v1/orders/verify-qr`, completing valid orders once and rejecting replays (`is_used == True`) or cross-store QR codes.

**Independent Test**: Log in as Store Partner (`merchant.bui@ecobite.vn`), open `/store/verify-qr`, submit copied QR payload -> `200` `COMPLETED`; submit same QR again -> `400` replay error.

- [X] T019 [P] [US4] Build Store Partner QR Verification page (`/store/verify-qr`) with QR payload input, camera scan toggle (`html5-qrcode` optional fallback), verification result card, and store orders quick list in `frontend/src/app/store/verify-qr/page.tsx`
- [X] T020 [P] [US4] Build Store KYC Onboarding page (`/store/onboard`) matching `POST /api/v1/stores/onboard` so existing Navbar route works cleanly in `frontend/src/app/store/onboard/page.tsx`

---

## Phase 7: Polish, Full Verification & Git Push

**Purpose**: Run full backend and frontend verification suites, test live end-to-end API/UI flow, update `AGENTS.md` if needed, and push clean commit to `dev`.

- [X] T021 Run full backend checks (`ruff check app/`, `ruff format --check app/`, `mypy app/`, `pytest tests/ -v`) and ensure 100% pass
- [X] T022 Run full frontend checks (`npm run lint`, `npm run type-check`, `npm run build`) and fix any warnings/errors
- [X] T023 Seed demo DB, run live E2E smoke test (`login` -> `stores/nearby` -> `POST /orders` -> `POST /orders/{id}/qr` -> `POST /orders/verify-qr` -> replay rejection -> `cancel` stock restore), and verify frontend pages serve HTTP 200
- [X] T024 Update task checkboxes in `specs/001-rescue-discovery-order-qr/tasks.md`, check `git status` (no secrets/build artifacts), commit to `dev`, and `git push origin dev`
