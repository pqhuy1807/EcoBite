---
description: "Dependency-ordered TDD task list for Feature 8 — Verified Reviews, Green Points Wallet, CO₂ Impact Tracker & Atomic Voucher Redemption"
---

# Tasks: Verified Reviews, Green Points Wallet, CO₂ Impact Tracker & Atomic Voucher Redemption (Feature 8)

**Input**: Design documents from `/specs/005-reviews-gamification-vouchers/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/api-contracts.md`, `quickstart.md`

**Tests**: Test tasks are **MANDATORY** and placed **FIRST** inside every User Story phase per EcoBite Constitution Principle I (Test-First Development — Red-Green-Refactor). The Final Verification Gate phase MUST exit `0` across Backend, Frontend, and Pre-commit checks before proposing any commit.

**Status Legend**:
- `[X]` = Verified implemented & present in the current repository (`dev` / PA4 Backend Core & Seed Data).
- `[ ]` = Pending Week 6 implementation (`EC4-13` Consumer UI, `EC4-14` Vitest Part 2, `EC4-15` concurrent voucher burst test, and PA4 Final Verification Gate).

**Team Assignments (per Sprint 4 Jira Backlog & Week 6 Re-balanced Action Plan)**:
- **Đàng Thế Tony**: `EC4-07` (Reviews BE + tests `[X]`), `EC4-13` (Consumer F8 UI `[ ]`), `EC4-14` (Vitest Part 2 `[ ]`), `EC4-15` (Concurrent voucher redemption QA `[ ]`).
- **Phùng Quốc Huy**: `EC4-08` (Gamification/Vouchers BE `[X]`), `EC4-09` (Gamification tests + `seed.py` `[X]`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`, `[US4]`) — omitted in Setup/Foundational, Polish, and Verification Gate phases
- Exact repository-relative file paths included in every task

---

## Phase 1: Setup & Foundational Infrastructure (Shared Models, Schemas & Test Harness)

**Purpose**: Verify persistent ORM tables, Pydantic v2 schemas, upstream QR earning bridge, and frontend Vitest/Navbar wiring required before User Stories.

- [X] T001 Verify Feature 8 ORM models (`Review` with `UNIQUE(order_id)` & `CHECK rating 1..5`, `PointActionType`, `GreenPointsLedger`, `Voucher`, `UserVoucher`, `User.green_points_balance`, `Store.rating_avg`/`rating_count`/`total_co2_saved_kg`) in `backend/app/models/interaction.py`, `backend/app/models/gamification.py`, `backend/app/models/user.py`, `backend/app/models/store.py`, and initial migration `backend/alembic/versions/8793a9fe3601_initial_schema_ecobite_12_tables.py`
- [X] T002 [P] Verify Pydantic v2 DTOs (`ReviewBase`, `ReviewCreate`, `ReviewResponse`, `GreenPointsLedgerResponse`, `GreenPointsSummaryResponse`, `VoucherResponse`, `UserVoucherResponse`, `VoucherRedeemResponse`) in `backend/app/schemas/interaction.py` and `backend/app/schemas/gamification.py`
- [X] T003 [P] (`EC4-06`, Tony) Verify upstream QR pickup completion awards `User.green_points_balance`, inserts `PointActionType.ORDER_RESCUE` into `GreenPointsLedger`, and increments `Store.total_co2_saved_kg` atomically in `backend/app/services/order_service.py`
- [X] T004 [P] (`EC4-10`, Thịnh) Verify frontend Vitest configuration (`jsdom`, `@testing-library/jest-dom`, `@/*` alias) and `CONSUMER` `/green-points` navigation link in `frontend/vitest.config.ts`, `frontend/vitest.setup.ts`, and `frontend/src/components/ui/Navbar.tsx`

**Checkpoint**: Shared schema foundation, QR earning trigger, and frontend test/navigation harness are in place.

---

## Phase 2: User Story 1 - Verified Post-Pickup Order Reviews & Store Rating Aggregation (Priority: P1) 🎯 F8A Backend (`EC4-07`, Tony)

**Goal**: Allow authenticated `CONSUMER` owners of `COMPLETED` orders to submit a single 1–5 star verified review that transactionally recalculates `Store.rating_avg` & `rating_count`, and expose public paginated newest-first store reviews.

**Independent Test**: Run `pytest tests/unit/test_review_repo.py tests/unit/test_review_service.py tests/integration/test_api_reviews.py -v` and confirm all 20 tests pass (`201`, `200`, `403`, `404`, `409` duplicate & non-`COMPLETED`, and accurate store rating recalculation).

### Tests for User Story 1 (MANDATORY — TDD First)

- [X] T005 [P] [US1] (`EC4-07`, Tony) Write unit tests for `ReviewRepository` (`create_review`, `get_by_order_id`, `UNIQUE(order_id)` `IntegrityError`, newest-first paginated `list_by_store`, `update_store_rating` avg/count & `5.00` empty default) in `backend/tests/unit/test_review_repo.py`
- [X] T006 [P] [US1] (`EC4-07`, Tony) Write unit tests for `ReviewService` (`CONSUMER` role guard `403`, non-owner `403`, non-`COMPLETED` `409`, missing order `404`, duplicate review `409`, race-condition `IntegrityError` -> `409`, multi-review store average update) in `backend/tests/unit/test_review_service.py`
- [X] T007 [P] [US1] (`EC4-07`, Tony) Write API integration tests for `POST /api/v1/orders/{order_id}/review` and `GET /api/v1/stores/{store_id}/reviews` in `backend/tests/integration/test_api_reviews.py`

### Implementation for User Story 1

- [X] T008 [US1] (`EC4-07`, Tony) Implement `ReviewRepository` (`create_review`, `get_by_id`, `get_by_order_id`, `list_by_store`, `update_store_rating`) in `backend/app/repositories/review_repo.py`
- [X] T009 [US1] (`EC4-07`, Tony) Implement `ReviewService` (`create_review` with single-transaction review + store rating commit & `IntegrityError` rollback, `get_by_order_id`, `list_store_reviews`) in `backend/app/services/review_service.py`
- [X] T010 [US1] (`EC4-07`, Tony) Implement `POST /api/v1/orders/{order_id}/review` (`201 Created`, `CONSUMER`) and `GET /api/v1/stores/{store_id}/reviews` (`200 OK`, public paginated) in `backend/app/api/v1/endpoints/reviews.py` and register in `backend/app/api/v1/router.py`

**Checkpoint**: Feature 8A Backend (Verified Reviews) is complete and verified.

---

## Phase 3: User Story 2 - Green Points Wallet, CO₂ Impact Tracker & Deterministic Eco Rank (Priority: P1) 🎯 F8B Wallet Backend (`EC4-08`/`EC4-09`, Huy)

**Goal**: Provide authenticated `CONSUMER` accounts with their live Green Points balance, `COMPLETED`-order CO₂ saved (kg) and meals rescued totals, deterministic rule-based Eco Rank (preserving earned rank via rescued CO₂), and newest-first ledger history.

**Independent Test**: Run `pytest tests/unit/test_gamification_service.py tests/integration/test_api_gamification.py -k "rank or green_points" -v` and verify deterministic rank tiers, `COMPLETED`-only aggregation, empty defaults, and `401`/`403`/`404` guards.

### Tests for User Story 2 (MANDATORY — TDD First)

- [X] T011 [P] [US2] (`EC4-09`, Huy) Write unit tests for `GamificationService.compute_rank_title` (all 4 thresholds + CO₂ rank preservation after voucher spend) and `get_my_green_points` (`COMPLETED`-only stats, newest-first ledger, empty defaults, `404` missing user) in `backend/tests/unit/test_gamification_service.py`
- [X] T012 [P] [US2] (`EC4-09`, Huy) Write API integration tests for `GET /api/v1/green-points/me` (`200 OK`, `401` anonymous, `403` non-`CONSUMER`) in `backend/tests/integration/test_api_gamification.py`

### Implementation for User Story 2

- [X] T013 [US2] (`EC4-08`, Huy) Implement `GamificationRepository` wallet & ledger methods (`get_user_by_id`, `get_ledger_by_user`, `create_ledger_entry`, `get_completed_rescue_stats`) in `backend/app/repositories/gamification_repo.py`
- [X] T014 [US2] (`EC4-08`, Huy) Implement `GamificationService.compute_rank_title` (`RANK_THRESHOLDS`, `CO2_KG_TO_SCORE_FACTOR = Decimal("20")`) and `get_my_green_points` in `backend/app/services/gamification_service.py`
- [X] T015 [US2] (`EC4-08`, Huy) Implement `GET /api/v1/green-points/me` (`CONSUMER`, `limit` `1..100`) in `backend/app/api/v1/endpoints/gamification.py` and register `gamification.router` BEFORE `stores.router` in `backend/app/api/v1/router.py`

**Checkpoint**: Green Points Wallet & CO₂ Impact backend is complete and verified.

---

## Phase 4: User Story 3 - Voucher Catalog, Atomic Redemption, Seed Data & Concurrency QA (Priority: P1) 🎯 F8B Vouchers Backend (`EC4-08`/`EC4-09` Huy, `EC4-15` Tony)

**Goal**: Expose active unexpired voucher catalog, consumer claimed vouchers, and atomic single-transaction voucher redemption (`WHERE green_points_balance >= :cost RETURNING green_points_balance` + negative ledger + `UserVoucher`), backed by consistent demo seed data and multi-session concurrent redemption stress verification.

**Independent Test**: Run `pytest tests/unit/test_gamification_service.py tests/integration/test_api_gamification.py -v` and confirm catalog filtering, E2E redemption, rollback integrity, seed consistency, and 10-way concurrent redemption producing exactly `1` `200 OK`, `9` `409 Conflict`, and zero negative balance.

### Tests for User Story 3 (MANDATORY — TDD First)

- [X] T016 [P] [US3] (`EC4-09`, Huy) Write unit tests for `list_available_vouchers`, `list_my_vouchers`, `atomic_deduct_points` (non-positive cost guard), and `redeem_voucher` (atomic balance/ledger/`UserVoucher`, `409` insufficient points, sequential double-redeem, `404` missing, `400` inactive/expired/exact boundary, mid-tx rollback, user-scoped `distributed_lock` key) in `backend/tests/unit/test_gamification_service.py`
- [X] T017 [P] [US3] (`EC4-09`, Huy) Write API integration tests for `GET /api/v1/vouchers`, `GET /api/v1/vouchers/me`, `POST /api/v1/vouchers/{voucher_id}/redeem` E2E flow + error matrix (`400`/`401`/`403`/`404`/`409`) and `seed_data()` consistency check in `backend/tests/integration/test_api_gamification.py`

### Implementation for User Story 3

- [X] T018 [US3] (`EC4-08`, Huy) Implement `GamificationRepository` voucher & atomic deduction methods (`atomic_deduct_points` with `WHERE id = :uid AND green_points_balance >= :cost RETURNING green_points_balance`, `get_voucher_by_id`, `list_available_vouchers`, `get_user_vouchers`, `create_user_voucher`) in `backend/app/repositories/gamification_repo.py`
- [X] T019 [US3] (`EC4-08`, Huy) Implement `GamificationService` voucher methods (`list_available_vouchers`, `list_my_vouchers`, `redeem_voucher` with `_as_utc`, `distributed_lock(f"lock:green_points:user:{user_id}")`, single-transaction commit/rollback) in `backend/app/services/gamification_service.py`
- [X] T020 [US3] (`EC4-08`, Huy) Implement `GET /api/v1/vouchers` (public), `GET /api/v1/vouchers/me` (`CONSUMER`, placed ahead of `{voucher_id}`), and `POST /api/v1/vouchers/{voucher_id}/redeem` (`CONSUMER`, `200 OK`) in `backend/app/api/v1/endpoints/gamification.py`
- [X] T021 [US3] (`EC4-09`, Huy) Update `backend/app/db/seed.py` with 4 active vouchers (`ECOBITE10K`, `GREENHERO20K`, `ECO25K`, `ECO50K`), sample `UserVoucher`, `COMPLETED` orders for `consumer.an` & `consumer.huy`, verified `Review`, consistent `GreenPointsLedger` entries, and `PENDING`/`REJECTED` KYC stores

### Concurrency QA Hardening for User Story 3 (`EC4-15`)

- [ ] T022 [US3] (`EC4-15`, Assignee: Đàng Thế Tony, Reviewer: Đặng Trọng Phúc) Add multi-session concurrent voucher-redemption integration stress test in `backend/tests/integration/test_api_gamification.py` (modeled on `test_order_concurrency.py`: temp file SQLite + `NullPool` + per-request `AsyncSession` override + `asyncio.gather` sending 10 parallel `POST /api/v1/vouchers/{voucher_id}/redeem` calls for a 150-point consumer on a 100-point voucher; assert exactly `1` HTTP `200`, `9` HTTP `409`, final `green_points_balance == 50`, `1` `UserVoucher`, and `1` negative `GreenPointsLedger` row)

**Checkpoint**: Feature 8B Backend + Seed Data + Multi-Session Concurrency Integrity are 100% verified.

---

## Phase 5: User Story 4 - Consumer Green Points Dashboard, ReviewModal & Vitest Component Tests (Priority: P2) (`EC4-13` & `EC4-14`, Re-allocated to Đàng Thế Tony)

**Goal**: Deliver the complete Consumer web UI for Feature 8 (`/green-points` wallet & voucher exchange + `ReviewModal` wired into `/orders` for `COMPLETED` orders) with typed API services and deterministic Vitest component tests.

**Independent Test**: Run `cd frontend && npm run test` (both `ReviewModal.test.tsx` and `GreenPointsPage.test.tsx` pass 100%); log in at `/login` as `consumer.huy@ecobite.vn` to redeem a voucher on `/green-points` (verifying immediate cache refresh) and submit a 5-star review on `/orders` (verifying `409` duplicate handling).

### Tests for User Story 4 (MANDATORY — Write FIRST & Verify FAIL) ⚠️

- [ ] T023 [P] [US4] (`EC4-14`, Tony) Write Vitest component tests in `frontend/__tests__/components/ReviewModal.test.tsx` covering: rendering modal for a `COMPLETED` order, interactive 1–5 star rating selection, optional quick tags & comment submission calling `reviewService.createReview(order.id, payload)`, success callback + toast, friendly Vietnamese handling on `409 Conflict` (already reviewed), and disabled submit guard while loading or before rating selection
- [ ] T024 [P] [US4] (`EC4-14`, Tony) Write Vitest component tests in `frontend/__tests__/components/GreenPointsPage.test.tsx` covering: rendering stats header (`balance_points`, `total_co2_saved_kg`, `total_meals_saved`, `rank_title`), **Đổi Voucher** tab disabling redeem button when `balance_points < points_required`, 1-tap redeem invoking `gamificationService.redeemVoucher` and triggering React Query invalidation/refetch of balance, My Vouchers, and Ledger, switching between **Đổi Voucher**, **Voucher của tôi**, and **Lịch sử Điểm Xanh** tabs, and error toast on `409`/`400`

### Implementation for User Story 4 (`EC4-13`, Tony)

- [ ] T025 [P] [US4] (`EC4-13`, Tony) Append Feature 8 TypeScript DTOs (`PointActionType`, `ReviewCreatePayload`, `ReviewResponse`, `GreenPointsLedgerEntry`, `GreenPointsSummaryResponse`, `VoucherResponse`, `UserVoucherResponse`, `VoucherRedeemResponse`) to `frontend/src/types/api.ts`
- [ ] T026 [P] [US4] (`EC4-13`, Tony) Create typed API client services `frontend/src/services/gamification.service.ts` (`getMyGreenPoints`, `listVouchers`, `getMyVouchers`, `redeemVoucher`) and `frontend/src/services/review.service.ts` (`createReview`, `getStoreReviews`) using `@/lib/api-client`
- [ ] T027 [US4] (`EC4-13`, Tony) Build Consumer Green Points Wallet & Voucher Exchange page in `frontend/src/app/green-points/page.tsx` (`'use client'`, `<AuthGuard allowedRoles={['CONSUMER']}>`, stats header displaying `balance_points`, `total_co2_saved_kg`, `total_meals_saved`, `rank_title`; 3 tabs: **Đổi Voucher** with insufficient-point disablement & 1-tap `useMutation` invalidating `['green-points-me']`, `['vouchers-me']`, `['vouchers-available']`; **Voucher của tôi**; **Lịch sử Điểm Xanh**)
- [ ] T028 [US4] (`EC4-13`, Tony) Build reusable `ReviewModal` component in `frontend/src/components/ReviewModal.tsx` (`'use client'`, built over `@/components/ui/Modal`, interactive 1–5 star selector, optional quick-tag chips & comment textarea, submission loading state, and graceful `409 Conflict` duplicate-review notice)
- [ ] T029 [US4] (`EC4-13`, Tony — integrate after Thịnh merges `EC4-12`) Wire *"Đánh giá"* action button on `order.status === 'COMPLETED'` cards in `frontend/src/app/orders/page.tsx` to open `ReviewModal`, show success toast, and mark locally reviewed orders

**Checkpoint**: Consumer Feature 8 UI and Vitest component suite are complete and green.

---

## Phase 6: Polish & Cross-Cutting E2E Validation

**Purpose**: End-to-end full-stack verification across seeded Consumer flows before final PA4 Quality Gate.

- [ ] T030 Execute full-stack E2E walkthrough following `specs/005-reviews-gamification-vouchers/quickstart.md` (seeded `consumer.huy@ecobite.vn` & `consumer.an@ecobite.vn`: inspect `/green-points`, redeem `ECOBITE10K`, verify live balance/My Vouchers/Ledger updates, submit 5-star review on `COMPLETED` order from `/orders`, confirm `409` duplicate notice & updated `Store.rating_avg`)

---

## Final Phase: Verification Gate (Constitution Principle VIII) — MANDATORY

**Purpose**: Reproducible evidence that every Quality Gate passes across Backend, Frontend, and Repository Hooks. All commands MUST exit `0` before proposing a commit or tagging Release 0.3 (`v0.3.0-pa4`).

### Backend (`backend/`)

- [ ] T031 `./venv_backend/bin/ruff check app/ tests/` — lint passes with zero findings
- [ ] T032 `./venv_backend/bin/ruff format --check app/ tests/` — formatting is canonical
- [ ] T033 `./venv_backend/bin/mypy app/` — static type-check passes with zero errors
- [ ] T034 `./venv_backend/bin/pytest tests/ -v` — full backend suite (including `test_review_*`, `test_gamification_service.py`, `test_api_reviews.py`, `test_api_gamification.py` concurrent burst) passes with zero regressions

### Frontend (`frontend/`)

- [ ] T035 `npm run lint` — Next.js ESLint passes with zero errors
- [ ] T036 `npm run type-check` — strict `tsc --noEmit` passes with zero errors
- [ ] T037 `npm run test` — Vitest suite (`ReviewModal.test.tsx`, `GreenPointsPage.test.tsx`, and sibling PA4 tests) passes 100%
- [ ] T038 `npm run build` — production Next.js build succeeds cleanly

### Repository Hooks (repo root)

- [ ] T039 `pre-commit run --all-files` — secrets check, file-size (`< 5 MB`), and formatting hooks pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup & Foundational)**: Complete (`T001`–`T004` `[X]`).
- **Phase 2 (US1 — Verified Reviews BE)**: Complete (`T005`–`T010` `[X]`).
- **Phase 3 (US2 — Green Points Wallet & Rank BE)**: Complete (`T011`–`T015` `[X]`).
- **Phase 4 (US3 — Vouchers BE, Seed & Concurrency QA)**: Core & Seed complete (`T016`–`T021` `[X]`); `T022` (`EC4-15` concurrent burst test) can run immediately in parallel with Phase 5.
- **Phase 5 (US4 — Consumer FE UI & Vitest)**: Depends on Phase 1–4 backend APIs (already complete). Author `T023` & `T024` (Vitest RED tests) alongside `T025` & `T026` (DTOs & services), then build `T027` (`/green-points`) and `T028` (`ReviewModal.tsx`), and finish with `T029` (`/orders` integration after Thịnh merges `EC4-12`).
- **Phase 6 (Polish E2E)** & **Final Phase (Verification Gate `T031`–`T039`)**: Run once `T022`–`T029` are complete.

### Parallel Opportunities (Remaining Week 6 Work)

```bash
# Independent files that Tony can execute concurrently with zero Git conflict against Thịnh:
T022: Concurrent voucher-redemption burst test in backend/tests/integration/test_api_gamification.py
T023: Vitest suite (RED) in frontend/__tests__/components/ReviewModal.test.tsx
T024: Vitest suite (RED) in frontend/__tests__/components/GreenPointsPage.test.tsx
T025: Feature 8 DTOs in frontend/src/types/api.ts
T026: REST services in frontend/src/services/{gamification,review}.service.ts

# After T025-T026, build pages/components in parallel:
T027: frontend/src/app/green-points/page.tsx
T028: frontend/src/components/ReviewModal.tsx
# Then wire T029 into frontend/src/app/orders/page.tsx after EC4-12 merges, verify T030-T039!
```

---

## Progress Summary

- **Total Tasks**: `39`
- **Completed (`[X]`)**: `21` (`T001`–`T021`: Shared Foundation, F8A Reviews BE + 20 tests, F8B Gamification/Vouchers BE + 20 tests, Demo Seed Data)
- **Pending (`[ ]`)**: `18` (`T022` Concurrency QA `EC4-15`, `T023`–`T024` Vitest `EC4-14`, `T025`–`T029` Consumer F8 UI `EC4-13`, `T030` E2E Walkthrough, `T031`–`T039` Mandatory Verification Gate)
