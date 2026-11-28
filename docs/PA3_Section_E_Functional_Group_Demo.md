# Section E: Functional Group Using Spec Kit and Demo on YouTube

**Project:** EcoBite Platform — Surplus Food Rescue & Sustainability Marketplace
**Feature Group:** `001-rescue-discovery-order-qr` — *Consumer Surplus Discovery, Anti-Overselling Order & Dynamic QR Pickup*
**Assignee:** Phùng Quốc Huy
**Reviewer:** Đặng Trọng Phúc
**Branch:** `dev`

---

## E1. The Chosen Functional Group for Demo

### 1. Feature Group Overview

Rather than demonstrating an isolated endpoint, we implemented a **complete, end-to-end Functional Group** using **Spec Kit (Spec-Driven Development)** covering the full food-rescue lifecycle from discovery to physical counter pickup:

> **Location-Based Surplus Discovery Radar → Atomic Anti-Overselling Order → Dynamic HMAC-SHA256 Single-Use QR Token → In-Store Web Scanner & Anti-Replay Verification**

| Component | Function | Business & Engineering Value |
| :--- | :--- | :--- |
| **1. Surplus Discovery Radar (`US1`)** | Consumers search approved nearby stores within a `1–10 km` radius on an interactive Leaflet map (`GET /api/v1/stores/nearby`) with category filtering and time-shifted discounts. | Helps users quickly locate discounted surplus meals around them with real-time distance and remaining stock. |
| **2. Atomic Rescue Order (`US2`)** | Authenticated consumers place orders (`POST /api/v1/orders`) backed by atomic SQL stock decrement (`WHERE remaining_quantity >= qty`) and environmental impact calculation (`CO₂` saved & Green Points). | Eliminates race conditions and overselling under concurrent requests (`409 Conflict` when stock is insufficient) and restores inventory on cancellation (`PATCH /api/v1/orders/{order_id}/cancel`). |
| **3. Dynamic Single-Use QR Token (`US3`)** | On `/orders`, consumers view store/dish details and generate an **HMAC-SHA256** signed pickup QR payload (`POST /api/v1/orders/{order_id}/qr`) containing `order_id`, `user_id`, a cryptographic `nonce`, and an expiration timestamp (`exp`). | Prevents forged or tampered pickup tokens and supports seamless counter handover via `<QRCodeSVG />`. |
| **4. In-Store Web Scanner & Anti-Replay (`US4`)** | Store Partners authenticate on `/store/verify-qr` and scan customer QR codes via an integrated web camera scanner (`html5-qrcode`) or manual payload input (`POST /api/v1/orders/verify-qr`). | Validates HMAC signatures in real time using constant-time comparison, enforces store ownership (`403 Forbidden` for cross-store scans), immediately marks `is_used = True`, and blocks screenshot sharing or replay attacks (`400 Bad Request`). |

---

### 2. Spec Kit (SDD) Artifacts

All specifications, architecture decisions, API contracts, and task tracking were produced under the Spec Kit workflow prior to and alongside implementation:

- **Project Constitution:** `.specify/memory/constitution.md`
- **Feature Specification & Checklist:** `specs/001-rescue-discovery-order-qr/spec.md`, `specs/001-rescue-discovery-order-qr/checklists/requirements.md`
- **Technical Plan & Research:** `specs/001-rescue-discovery-order-qr/plan.md`, `specs/001-rescue-discovery-order-qr/research.md`
- **Data Model & API Contracts:** `specs/001-rescue-discovery-order-qr/data-model.md`, `specs/001-rescue-discovery-order-qr/contracts/api-contracts.md`
- **Execution Tasks & Quickstart:** `specs/001-rescue-discovery-order-qr/tasks.md` (`T001`–`T024` completed), `specs/001-rescue-discovery-order-qr/quickstart.md`

---

### 3. Verification & Quality Summary

- **Backend (`FastAPI` + `SQLAlchemy 2.0 Async`):**
  - `ruff check app/` & `ruff format --check app/` — passed (`57` source files).
  - `mypy app/` — passed with `0` errors (`57` source files).
  - `pytest tests/ -q` — **198 passed** (unit + integration + concurrency & QR anti-replay tests).
- **Frontend (`Next.js 14 App Router` + `TypeScript Strict`):**
  - `npm run lint` — `0` ESLint warnings or errors.
  - `npm run type-check` (`tsc --noEmit`) — `0` TypeScript errors.
  - `npm run build` — production build succeeded (`9/9` routes: `/`, `/login`, `/register`, `/orders`, `/store/verify-qr`, `/store/onboard`).

---

## E2. Video Demo (on YouTube)

- **YouTube Link:** [Click here to watch the Demo Video](https://youtu.be/PsYfFS2f_fY)

### Demo Walkthrough Outline

1. **Discovery Radar (`/`):** Filter nearby approved stores by radius (`1–10 km`) and food category on the interactive Leaflet map.
2. **Consumer Order & Anti-Overselling:** Sign in as Demo Consumer (`consumer.an@ecobite.vn`), place a rescue order, observe live stock decrement, and demonstrate `409 Conflict` when requesting more than remaining stock.
3. **My Orders & Dynamic QR (`/orders`):** View dish name, store name/address, and `EB-...` order code; open the dynamic **HMAC-SHA256** QR code modal.
4. **Store Partner Verification & Anti-Replay (`/store/verify-qr`):** Sign in as Demo Store Partner (`merchant.bui@ecobite.vn`), verify the QR payload to complete the order (`COMPLETED` + Green Points awarded), and re-submit the same QR token to demonstrate **Anti-Replay** rejection.

---

## E3. GitHub Repository (Complete Source Code)

- **Repository:** [https://github.com/pqhuy1807/EcoBite](https://github.com/pqhuy1807/EcoBite) (Branch: `dev`)
- **Access Note:** The repository is currently set to **private**. Please send an access request (or share your GitHub username) so we can grant collaborator access for review.
