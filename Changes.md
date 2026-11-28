# EcoBite PA4 Changes Log

*Performed by: Võ Ngọc Thịnh | Reviewed by: Đặng Trọng Phúc, Đàng Thế Tony | Edited by: Phùng Quốc Huy*

**Project:** EcoBite — Food Rescue & Zero-Waste Platform  
**Team:** Group 05 — CS300 / CSC13002 Introduction to Software Engineering, Faculty of Information Technology, VNU-HCM University of Science (HCMUS)  
**Comparison:** PA3 (`v1.1`, 14/11/2026) → PA4 (`v2.0`, 28/11/2026)  
**Reporting Period:** 15/11/2026 – 28/11/2026 (Sprint 4 — PA4)  
**Companion Report:** `PA4-Group05/reportPA4.md` *(plus `.pdf` export)*

---

## Table of Contents

1. [Purpose, Scope and How to Read This Document](#purpose-scope-and-how-to-read-this-document)
2. [Part A — Changes to Use-Case Model & Specifications (PA3 §§C–D v1.1 → PA4 Section A v2.0)](#part-a--changes-to-use-case-model--specifications-pa3-cd-v11--pa4-section-a-v20)
   - [1.1 Addressing PA3 TA Feedback on Use-Case Specification (14/45 pts)](#11-addressing-pa3-ta-feedback-on-use-case-specification-1445-pts)
   - [1.2 PA3 to PA4 Use-Case ID Reconciliation](#12-pa3-to-pa4-use-case-id-reconciliation)
   - [1.3 Comparison Table for Revised Use-Case Specification (Part A)](#13-comparison-table-for-revised-use-case-specification-part-a)
3. [Part B — Changes to Implementation, Spec Kit & Packaging (PA3 §E v1.1 → PA4 Section E v2.0)](#part-b--changes-to-implementation-spec-kit--packaging-pa3-e-v11--pa4-section-e-v20)
   - [2.1 Addressing PA3 TA Feedback on Feature & Spec Kit (15/20 pts)](#21-addressing-pa3-ta-feedback-on-feature--spec-kit-1520-pts)
   - [2.2 Comparison Table for Section E Functional Groups, Spec Kit & Platform Codebase (Part B)](#22-comparison-table-for-section-e-functional-groups-spec-kit--platform-codebase-part-b)
4. [Impact Summary, Traceability & Change-Control Record](#impact-summary-traceability--change-control-record)

---

## Purpose, Scope and How to Read This Document

*Performed by: Võ Ngọc Thịnh | Reviewed by: Đặng Trọng Phúc, Đàng Thế Tony | Edited by: Phùng Quốc Huy*

This `Changes.md` file is the consolidated delta record mandated by the **PA4-2026** brief:

> *"Your team must include a Changes.md file that clearly lists all changes made compared to the PA3-2026 version. Use a single Changes.md file per PA submission, with separate sections for each revised document. Without this file, you will not receive points for this section."*

It covers every revision and extension between **PA3 (`v1.1`, 14/11/2026)** and the final **PA4 (`v2.0`, 28/11/2026)** submission package *(Sections B–D Software Architecture & Deployment and Section F Sprint 4 AI Usage / Weekly Report are newly introduced in `reportPA4.md` rather than revisions of PA3 §§C–E)*:

| Part | Revised Deliverable / Section | PA3 Baseline (`v1.1`, 14/11/2026) | PA4 Revised Version (`v2.0`, 28/11/2026) |
| :--- | :--- | :--- | :--- |
| **Part A** | Use-Case Model & Specifications | `report/PA3-Group05/reportPA3.md` §§C–D | `reportPA4.md` §A — all 14 system UCs (`UC-01`–`UC-14`) |
| **Part B** | Section E Functional Groups, Spec Kit Artifacts, Codebase & Packaging | `report/PA3-Group05/reportPA3.md` §E, `docs/PA3_Section_E_Functional_Group_Demo.md`, `specs/001-rescue-discovery-order-qr/` | `reportPA4.md` §E (`E1` `005-reviews-gamification-vouchers` + `E2` `003-auth-kyc-menu-pricing` & `001-rescue-discovery-order-qr`), `.specify/memory/constitution.md` (`v1.2.0`), `specs/001`–`007`, and clean `PA4-Group05.zip` |

**Column Convention:** `Change ID` | `Affected Section` | `PA3 Version (v1.1)` | `PA4 Revised Version (v2.0)` | `Source / Rationale`.

---

## Part A — Changes to Use-Case Model & Specifications (PA3 §§C–D v1.1 → PA4 Section A v2.0)

*Performed by: Võ Ngọc Thịnh | Reviewed by: Đặng Trọng Phúc, Đàng Thế Tony | Edited by: Phùng Quốc Huy*

### 1.1 Addressing PA3 TA Feedback on Use-Case Specification (14/45 pts)

In PA3, **Part D (Use-Case Specification)** received **14/45 points** due to three structural defects:

1. **Severe Coverage Gap (4/14 UCs)**: Although Part C defined **14 system Use Cases (`UC-01` – `UC-14`)**, Part D only specified **5 screen-level flows (`D.1` – `D.5`)** covering 4 underlying system UCs, leaving **10 Use Cases** (`UC-04`, `UC-05`, `UC-06`, `UC-07`, `UC-09`, `UC-10`, `UC-11`, `UC-12`, `UC-13`, `UC-14`) unspecified.
2. **Use-Case ID & Naming Drift**: Part D split `UC-01` into `D.1 UC-01 (User Registration)` and `D.2 UC-02 (User Authentication / Login)`, shifting `UC-02 (Discovery)` to `D.4 UC-04` and `UC-08 (Order)` to `D.5 UC-05`.
3. **Outdated Behavioral Scope**: PA3 Part D described pre-Sprint-4 stubs (such as order placement without VNPay Sandbox checkout, missing Payment-to-QR guard, and missing completed Sprint 4 modules).

PA4 Section A (`reportPA4.md` §A) resolves all three issues: it restores **exact 1-to-1 parity** with all 14 Use Case IDs and names from PA3 Part C, provides complete **6-part specifications** for every UC (`UC-01` through `UC-14`), and synchronizes every flow, UI route, and HTTP status code with the actual Sprint 4 codebase.

### 1.2 PA3 to PA4 Use-Case ID Reconciliation

| PA3 Part D Heading (Old / Drifted) | PA3 Part C Canonical ID | PA4 Section A Revised ID & Title (`v2.0`) | Disposition |
| :--- | :--- | :--- | :--- |
| `D.1 UC-01: User Registration` + `D.2 UC-02: User Authentication / Login` | `UC-01` | **`UC-01`: User Registration, Authentication & Session Management** | **Merged & Realigned** (+ dual-token refresh, `AuthGuard`, role `Navbar`, `UserCreate` `extra="forbid"`) |
| `D.4 UC-04: Discover Nearby Surplus Food via Radar` | `UC-02` | **`UC-02`: Discover Nearby Stores & View Surplus Dish Details** | **Re-numbered** to `UC-02` (+ live `GET /stores/nearby`, store detail & store reviews) |
| `D.3 UC-03: Submit Store Partner KYC` | `UC-03` | **`UC-03`: Store KYC Onboarding** | **Retained** as `UC-03` (+ `GET /api/v1/stores/me` self-lookup) |
| `D.5 UC-05: Place a Surplus Food Rescue Order` | `UC-08` | **`UC-08`: Place Rescue Order & Pay via VNPay** | **Re-numbered** to `UC-08` (+ `COD`/`VNPAY` selector, VNPay URL, HMAC-SHA512 IPN, `/orders/vnpay-return` & `/payment/vnpay-return`) |
| *(Not specified in PA3 Part D)* | `UC-04`–`UC-07`, `UC-09`–`UC-14` | **`UC-04` – `UC-07`, `UC-09` – `UC-14` (10 Full 6-Part Specs Added)** | **Added** to reach **14/14 (100%)** coverage |

### 1.3 Comparison Table for Revised Use-Case Specification (Part A)

| Change ID | Affected Section | PA3 Version (`v1.1`) | PA4 Revised Version (`v2.0`) | Source / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `CHG-UC-01` | Document Structure & Coverage (`§D` → `§A`) | Specified only 5 screen-level UCs (`D.1`–`D.5`), leaving 10 of 14 system UCs from Part C undocumented. | Expands to **14/14 complete Use Cases (`UC-01` – `UC-14`)** in strict sequential order, each containing all 6 required subsections (Brief Description, Flow of Events [Basic + Alternative], Special Requirements, Preconditions, Postconditions, Extension Points). | **PA3 TA feedback (14/45 pts)**; PA4 Section A rubric requiring complete, consistent UC specifications. |
| `CHG-UC-02` | `UC-01` *(formerly `D.1` & `D.2`)* | Split registration and login into `D.1 UC-01` and `D.2 UC-02`, causing downstream ID shift across Part D; omitted `POST /auth/refresh` and `UserCreate` schema restrictions. | Consolidates into **`UC-01: User Registration, Authentication & Session Management`**, covering `/register`, `/login`, `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/users/me`, `AuthGuard`, `Navbar`, and noting `UserCreate` (`extra="forbid"`) + planned Google OAuth 2.0. | **PA3 ID alignment fix**; codebase verification (`auth.py`, `users.py`, `api-client.ts`, `user.py`). |
| `CHG-UC-03` | `UC-02` *(formerly `D.4 UC-04`)* | Numbered `D.4 UC-04`; focused only on initial radar discovery prototype and omitted store reviews (`GET /stores/{id}/reviews`). | Restored to **`UC-02: Discover Nearby Stores & View Surplus Dish Details`**, matching live `GET /api/v1/stores/nearby` on `frontend/src/app/page.tsx`, `useGeolocation` fallback (`10.7769, 106.7009`), 1/3/5/10 km radius controls, `GET /stores/{id}`, `GET /stores/{id}/reviews`, and demo fallback banner. | **PA3 ID alignment fix**; Sprint 4 codebase verification (`stores.py`, `discovery.py`, `page.tsx`). |
| `CHG-UC-04` | `UC-03` *(formerly `D.3`)* | Described `/store/onboard` form submission (`POST /stores/onboard`) without store self-lookup endpoint. | Retained as **`UC-03: Store KYC Onboarding`** and updated with Sprint 4 endpoint `GET /api/v1/stores/me`, GPS bounds (`[-90, 90]`, `[-180, 180]`), 5 MB file limit, and note distinguishing `storeService.onboardStore` (`/stores/onboard`) from `storeService.submitKyc` (`/stores/kyc`). | Codebase audit (`stores.py`, `store.service.ts`, `store/onboard/page.tsx`). |
| `CHG-UC-05` | New `UC-04` | Missing in PA3 Part D (menu CRUD and surplus dish publishing had no UC specification). | Added full 6-part spec **`UC-04: Manage Base Menu & Active Surplus Dishes`**, documenting `/store/menu` (`GET/POST/PUT/DELETE` menu items), `/store/dishes` (`POST /dishes`, `POST /dishes/batch`, `GET /stores/{id}/dishes/active`, `PATCH /dishes/{id}/quantity`), `APPROVED` KYC gate, Menu Grounding, and deterministic 50%/70% pricing. | **PA3 TA feedback (missing UC)**; Sprint 4 codebase verification (`menu.py`, `dishes.py`, `/store/menu`, `/store/dishes`). |
| `CHG-UC-06` | New `UC-05` | Missing in PA3 Part D (AI Quick-Post was only an unimplemented schema in PA3). | Added **`UC-05: AI Voice Quick-Post Surplus Batch`** (`<<extend>>` `UC-04`), aligned with `POST /api/v1/quick-post/extract`, `QuickPostService`, `QuickPostExtractionResponse` (`14` EU FIC groups, `EXPLICIT`/`INFERRED`), `AllergenHardFilterService`, graceful fallback, and accurate scope note that voice audio & Store UI are planned for PA5. | **PA3 TA feedback (missing UC)**; codebase audit (`quick_post.py`, `quick_post_service.py`). |
| `CHG-UC-07` | New `UC-06` | Missing in PA3 Part D (`user_preferences` had no API or UC specification). | Added **`UC-06: Manage Dietary & Allergen Preferences`**, specifying `GET /api/v1/users/me/preferences` and `PUT /api/v1/users/me/preferences`, canonical `EUAllergen` normalization, `DietaryPreference` validation (`422`), and noting Sprint 5 Consumer UI scope. | **PA3 TA feedback (missing UC)**; codebase audit (`users.py`, `preference_repo.py`). |
| `CHG-UC-08` | New `UC-07` | Missing in PA3 Part D (Smart Recommendations and Semantic Search had no UC spec). | Added **`UC-07: AI Semantic Search & Personalized Recommendations`** (`<<extend>>` `UC-02`), specifying `GET /api/v1/recommendations/personalized`, `POST /api/v1/dishes/search-semantic`, Layer 1 SQL/PostGIS + `AllergenHardFilterService`, Layer 2 `0.40/0.30/0.30` scoring, Layer 3 Gemini justification fallback, and Sprint 5 UI scope. | **PA3 TA feedback (missing UC)**; codebase audit (`recommendations.py`, `recommendation_service.py`). |
| `CHG-UC-09` | `UC-08` *(formerly `D.5 UC-05`)* | Numbered `D.5 UC-05`; covered only `POST /orders` without VNPay URL generation, HMAC-SHA512 IPN webhook, failed-payment stock rollback, or VNPay return page. | Restored to **`UC-08: Place Rescue Order & Pay via VNPay`**, reflecting `OrderModal.tsx` (`COD`/`VNPAY`), `POST /api/v1/orders`, `POST /api/v1/payments/vnpay/create-url`, `GET /api/v1/payments/vnpay/ipn` (constant-time HMAC-SHA512, Redis lock `lock:payment:ipn:{txn_ref}`, idempotency `"02"`, atomic stock restore on failed IPN), and `/orders/vnpay-return` + `/payment/vnpay-return` (`GET /api/v1/payments/vnpay/return`). | **PA3 ID alignment fix**; Sprint 4 VNPay checkout implementation. |
| `CHG-UC-10` | New `UC-09` | Missing in PA3 Part D (Order listing and cancellation existed in code/Part E but lacked a UC spec). | Added **`UC-09: View & Cancel Rescue Orders`**, specifying `/orders` status tabs, `GET /orders/me`, `GET /orders/store/{id}`, `GET /orders/{id}` (`qr_token` visibility rule), `PATCH /orders/{id}/cancel` (ownership, `pickup_deadline`, atomic stock restoration), and VNPay pending payment retry. | **PA3 TA feedback (missing UC)**; `orders.py`, `order_service.py`, `orders/page.tsx`. |
| `CHG-UC-11` | New `UC-10` | Missing in PA3 Part D (QR issuance/verification existed in Part E only; lacked Payment-to-QR guard). | Added **`UC-10: Verify Pickup QR & Complete Handover`**, covering `POST /orders/{id}/qr`, `<QRCodeSVG />`, unpaid `VNPAY` `409` guard (`_validate_payment_ready_for_qr`), `/store/verify-qr` `html5-qrcode` camera + manual entry + live Store Orders table, `POST /orders/verify-qr`, atomic `mark_token_as_used` anti-replay, `COD -> PAID`, and atomic handover settlement. | **PA3 TA feedback (missing UC)**; `order_service.py`, `qr_service.py`, `store/verify-qr/page.tsx`. |
| `CHG-UC-12` | New `UC-11` | Missing in PA3 Part D (Reviews & Green Points/Vouchers were not yet implemented). | Added **`UC-11: Submit Verified Review & Redeem Green Vouchers`** (`<<extend>>` `UC-09`), specifying `/orders` `ReviewModal` (`POST /orders/{id}/review`, `COMPLETED`-only `409`, 1 review/order, atomic `Store.rating_avg`) and `/green-points` (`GET /green-points/me`, `GET /vouchers`, `GET /vouchers/me`, `POST /vouchers/{id}/redeem` atomic points deduction + `GreenPointsLedger`). | **PA3 TA feedback (missing UC)**; Sprint 4 `reviews.py`, `gamification.py`, `/green-points`. |
| `CHG-UC-13` | New `UC-12` | Missing in PA3 Part D (Admin KYC review had only a backend endpoint and no UI or UC spec). | Added **`UC-12: Review & Moderate Store KYC Applications`**, reflecting `/admin` (`AuthGuard allowedRoles={['ADMIN']}`), `GET /api/v1/admin/stores/pending`, and `PATCH /api/v1/admin/stores/{id}/review` (`APPROVED` / `REJECTED` with `reject_reason`). | **PA3 TA feedback (missing UC)**; Sprint 4 `admin/page.tsx`. |
| `CHG-UC-14` | New `UC-13` | Missing in PA3 Part D (Admin supervision had no UC specification). | Added **`UC-13: Supervise Transactions, Disputes & Accounts`**, grounding it in implemented `ADMIN` `GET /orders/{id}`, `PaymentTransaction` audit records, `User.is_active` auth enforcement, and explicitly documenting planned PA5 bulk Admin supervision views. | **PA3 TA feedback (missing UC)**; codebase audit (`orders.py`, `order.py`, `auth.py`). |
| `CHG-UC-15` | New `UC-14` | Missing in PA3 Part D (Green Impact Dashboard had no UC specification). | Added **`UC-14: Monitor Platform Green Impact Dashboard`**, grounding it in `Order.co2_saved_kg`, `Store.total_co2_saved_kg`, `GreenPointsLedger`, and `GamificationRepository.get_completed_rescue_stats`, while clearly marking the Admin ESG UI for PA5. | **PA3 TA feedback (missing UC)**; codebase audit (`order_service.py`, `gamification_repo.py`). |
| `CHG-UC-16` | Attribution & Format Compliance | PA3 headings used blockquote attribution (`> **Performed by:** ...`) and mixed section numbering (`D.1`–`D.5`). | Standardized every section header with the exact italicized attribution line (`*Performed by: ... | Reviewed by: ... | Edited by: ...*`), unified Mermaid overview diagram, and 100% English Markdown structure. | **PA4-2026 Submission Guidelines**. |

---

## Part B — Changes to Implementation, Spec Kit & Packaging (PA3 §E v1.1 → PA4 Section E v2.0)

*Performed by: Võ Ngọc Thịnh | Reviewed by: Đặng Trọng Phúc, Đàng Thế Tony | Edited by: Phùng Quốc Huy*

### 2.1 Addressing PA3 TA Feedback on Feature & Spec Kit (15/20 pts)

In PA3, **Feature & Spec Kit** received **15/20 points** because the submitted `.zip` relied primarily on a GitHub repository link instead of including a clean, self-contained source tree alongside inspectable Spec Kit feature artifacts.

For **PA4 (`v2.0`)**, the team directly remedies that feedback and fulfills **PA4 Section E** (*"Implement 2 Functional Groups using Spec Kit"*):

1. **Unified `.specify/` Root & Constitution `v1.2.0`**: Consolidated Spec Kit configuration at `.specify/` (`templates/`, `workflows/`, `memory/`) and amended `.specify/memory/constitution.md` to **`v1.2.0`** (`2026-11-20`), adding VNPay `HMAC-SHA512` idempotency, verified review eligibility, and `backend/tests/property/` test structure rules.
2. **Two Complete Full-Stack Functional Groups Documented in `reportPA4.md §E`**:
   - **Functional Group 1 (`E1` — Phùng Quốc Huy, `specs/005-reviews-gamification-vouchers/`)**: Verified Post-Pickup Reviews (`F8A`), Green Points Wallet, CO₂ Impact Tracker, and Atomic Voucher Redemption (`F8B`).
   - **Functional Group 2 (`E2` — Võ Ngọc Thịnh, `specs/003-auth-kyc-menu-pricing/` + `specs/001-rescue-discovery-order-qr/`)**: Admin KYC Moderation & Store Unlock Gate (`/admin`), Base Menu Grounding (`/store/menu`), Surplus Dish Publishing & Live Stock Adjustment (`/store/dishes`), and Live PostGIS Radar Sync (`/`), with narrated YouTube demo (`https://youtu.be/NILywFWzqB0`).
3. **Full Sprint 4 Spec Kit Portfolio & Cashless Checkout (`specs/001`–`007`)**: Expanded the codebase alongside `specs/002-vnpay-checkout-order-lifecycle/` and `specs/004-vnpay-payment-qr-guard/` (VNPay Sandbox checkout redirect, `/orders/vnpay-return` + `/payment/vnpay-return`, idempotent IPN webhook, `409` Payment↔QR guard, and `/store/verify-qr` live store order queue) as well as AI baseline specs (`006`–`007`).
4. **Reproducible Verification & Clean Archive Protocol (`PA4-Group05.zip`)**: Verified all backend/frontend quality gates on the clean checkout (`348 passed` pytest, `75` backend files passing `ruff` & `mypy`, `9` Vitest files / `35` tests passing, `15/15` Next.js static pages built cleanly, `0` ESLint/TypeScript errors), exported up-to-date `Git_log_commit.txt` (`2140+` lines through `00ea613` & `2e13962`), and excluded build/runtime/secret artifacts (`frontend/node_modules/`, `frontend/.next/`, `backend/.venv/`, `backend/venv_backend/`, `backend/ecobite.db`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.hypothesis/`, `.env`, `.env.local`, `ml/weights/*.pt`).

### 2.2 Comparison Table for Section E Functional Groups, Spec Kit & Platform Codebase (Part B)

| Change ID | Affected Artifact / Area | PA3 Version (`v1.1`) | PA4 Revised Version (`v2.0`) | Source / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `CHG-SYS-01` | Spec Kit Functional Groups (`specs/` & `§E`) | Documented only 1 functional group (`specs/001-rescue-discovery-order-qr/`) for Discovery, Order, and QR Pickup. | Delivers **2 new PA4 Section E Functional Groups** alongside the full `001`–`007` Spec Kit index (`specs/README.md`): **Group 1 (`E1`: `005-reviews-gamification-vouchers/`)** for Verified Reviews, Green Points & Vouchers; and **Group 2 (`E2`: `003-auth-kyc-menu-pricing/` + `001-rescue-discovery-order-qr/`)** for Store KYC, Menu Grounding, Surplus Dishes & Live PostGIS Radar. | **PA4-2026 Section E (30 pts)** & **PA3 TA feedback (15/20 pts)** on Spec Kit artifacts. |
| `CHG-SYS-02` | Spec Kit Root & Constitution | Referenced legacy `src/.specify/memory/constitution.md` (`v1.1.0`) alongside root `.specify/`. | Consolidated at root `.specify/` (`memory/`, `templates/`, `workflows/`) with `.specify/memory/constitution.md` **`v1.2.0`** (amended `2026-11-20`), adding VNPay `HMAC-SHA512` idempotency, verified review integrity, and `backend/tests/property/`. | `.specify/memory/constitution.md` & `AGENTS.md`. |
| `CHG-SYS-03` | `E1` — Verified Reviews, Green Points & Vouchers (`F8A` + `F8B`) | `reviews`, `vouchers`, `user_vouchers`, and `green_points_ledger` existed only in DB models/design without API endpoints or Consumer UI. | Implemented `ReviewRepository`, `ReviewService`, `endpoints/reviews.py` (`POST /orders/{id}/review`, `GET /stores/{id}/reviews`), `GamificationRepository`, `GamificationService`, `endpoints/gamification.py` (`GET /green-points/me`, `/vouchers`, `/vouchers/me`, `POST /vouchers/{id}/redeem` atomic `WHERE green_points_balance >= :cost`), `ReviewModal` (`/orders`), `/green-points` wallet/voucher tabs, and synced seed data. | **PA4 Section E — Functional Group 1 (`E1`)**. |
| `CHG-SYS-04` | `E2` — Store KYC Moderation, Base Menu, Surplus Dishes & Live Radar (`F1`–`F4`) | Radar `/` fell back to static `FALLBACK_DEMO_DISHES`; `/admin`, `/store/menu`, and `/store/dishes` UI portals were not yet wired end-to-end. | Built `/admin` KYC review (`GET /admin/stores/pending`, `PATCH /admin/stores/{id}/review` `APPROVED`/`REJECTED` + live unlock), `/store/menu` (`GET /stores/me` KYC gate + `StoreOwner` `menu.py` CRUD + soft delete), `/store/dishes` (`POST /dishes`, `/dishes/batch`, `-50%`/`-70%` time-shift rules, `PATCH /dishes/{id}/quantity` `422` + conditional SQL `WHERE id = :dish_id AND total_quantity >= :qty` `409` concurrency guard & `SOLD_OUT`), and live `/` PostGIS Radar (`GET /stores/nearby`, `1/3/5/10 km`, keyword search, 5 UI category tabs filtering `DishStatus.ACTIVE` & `remaining_quantity > 0`). | **PA4 Section E — Functional Group 2 (`E2`)**; video `https://youtu.be/NILywFWzqB0`. |
| `CHG-SYS-05` | VNPay Sandbox Checkout & Payment↔QR Guard (`specs/002`, `004`) | Orders supported only `COD` / simulated `VNPAY` without payment URL signing, IPN webhook, return verification, or QR payment guard. | Implemented `PaymentService`, `PaymentTransactionRepository`, `endpoints/payments.py` (`create-url`, idempotent `HMAC-SHA512` `ipn` + atomic failed-payment rollback, `return`), `/orders/vnpay-return` & `/payment/vnpay-return`, `OrderService._validate_payment_ready_for_qr` (`409` guard + `COD -> PAID` handover), `/orders` retry UI, and `/store/verify-qr` Store Orders queue. | Sprint 4 codebase verification (`payments.py`, `order_service.py`, `OrderModal.tsx`, `orders/page.tsx`). |
| `CHG-SYS-06` | Automated Test Suites & Quality Gates (`Backend` + `Frontend`) | PA3 had `198` backend tests across `57` backend files and `0` Vitest tests (`frontend/` had no `"test"` script). | Configured Vitest (`vitest.config.ts`) with **`9` test files / `35` passing tests** (`AuthGuard`, `Navbar`, `OrderModal`, `OrdersPage`, `ReviewModal`, `GreenPointsPage`, `payment.service`, `review.service`, `gamification.service`), `15/15` `next build` static routes, and `0` `next lint` & `tsc --noEmit` errors; expanded backend to **`348 passed` pytest tests** (including **`63 passed`** across Group 2's 8 test files) and `0` `ruff`/`mypy` errors across **`75` source files**. | Observed `pytest`, `mypy`, `ruff`, `vitest`, `next lint`, `tsc --noEmit`, and `next build` verification (`28/11/2026`). |
| `CHG-SYS-07` | Clean Archive, Updated Git Log & Narrated YouTube Demos | PA3 relied mainly on a GitHub repo link and lacked unified exclusion of runtime artifacts. | Bundled clean self-contained source tree + Spec Kit `001`–`007` + `.specify/` + updated `Git_log_commit.txt` (`2140` lines up to `0eeab28`) + YouTube demo links (`E1` + `E2` `https://youtu.be/NILywFWzqB0`), explicitly excluding `node_modules/`, `.next/`, `.venv/`, `venv_backend/`, `backend/ecobite.db`, `__pycache__/`, cache dirs, `.hypothesis/`, `.env*`, and `ml/weights/*.pt`. | **PA3 TA feedback (15/20 pts)** & **PA4-2026 Submission Guidelines**. |

---

## Impact Summary, Traceability & Change-Control Record

*Performed by: Võ Ngọc Thịnh | Reviewed by: Đặng Trọng Phúc, Đàng Thế Tony | Edited by: Phùng Quốc Huy*

### Aggregate Impact (`PA3 v1.1` → `PA4 v2.0`)

| Dimension | PA3 Baseline (`v1.1`, 14/11/2026) | PA4 Revised Version (`v2.0`, 28/11/2026) | Delta (`PA3 → PA4`) |
| :--- | :--- | :--- | :--- |
| Detailed Use-Case Specifications (`§A`) | 5 screen UCs (`4/14` system UCs, ID drift) | **14/14 system UCs (`UC-01` – `UC-14`)**, 1-1 parity with PA3 §C | +10 UCs specified; IDs aligned |
| Spec Kit Packages (`specs/`) | 1 (`001-rescue-discovery-order-qr`) | **`specs/001`–`007`** (including §E `005`, `003` & `001` + `002`/`004`/`006`/`007`) | +6 SDD packages + `specs/README.md` |
| Constitution Version | `1.1.0` (`src/.specify/` + root `.specify/`) | **`1.2.0`** (`2026-11-20`, unified at root `.specify/`) | Amended for VNPay, Reviews & `tests/property/` |
| Backend Codebase & Quality Gates | `57` source files; `198` pytest tests | **`75` source files** (`ruff`, `mypy`: `0` errors); **`348 passed`** full pytest (`63 passed` in Group 2) | +18 backend files; +150 passing tests |
| Frontend Routes & Vitest Suites | No runnable Vitest `"test"` script (`0` tests) | **12 `page.tsx` routes / `15/15` `next build` static pages** (`next lint` & `tsc --noEmit`: `0` errors); **`9` Vitest files / `35` tests passed** | +9 Vitest test suites & full PA4 UI portals |
| Git Log Export (`Git_log_commit.txt`) | Exported at PA3 (`14/11/2026`, `1189` lines) | Updated through PA4 merge & rebase on `main` (`28/11/2026`) | Full Sprint 4 commit traceability |

### Change-Control Sign-Off

| Change Group | Author(s) | Reviewers | Editor | Date | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CHG-UC-01` … `CHG-UC-16` *(PA4 Section A)* | Võ Ngọc Thịnh | Đặng Trọng Phúc, Đàng Thế Tony | Phùng Quốc Huy | 28/11/2026 | **Synchronized for PA4 Submission** |
| `CHG-SYS-01` … `CHG-SYS-07` *(PA4 Section E & Codebase)* | Phùng Quốc Huy (`E1`), Võ Ngọc Thịnh (`E2`) | Đặng Trọng Phúc, Đàng Thế Tony | Phùng Quốc Huy | 28/11/2026 | **Verified & Synchronized for PA4 Submission** |
