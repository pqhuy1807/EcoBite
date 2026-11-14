# Implementation Plan: Consumer Surplus Discovery, Anti-Overselling Order & Dynamic QR Pickup

**Branch**: `dev` | **Date**: 2026-11-14 | **Spec**: [spec.md](file:///Users/phungquochuy/Desktop/EcoBite-Platform/specs/001-rescue-discovery-order-qr/spec.md)
**Input**: Feature specification from `/specs/001-rescue-discovery-order-qr/spec.md`

## Summary

Deliver a complete, verified, demo-ready End-to-End functional group (**Discovery Radar $\rightarrow$ Anti-Overselling Rescue Order $\rightarrow$ Order History & Cancellation $\rightarrow$ Dynamic HMAC-SHA256 QR Pickup & Store Verification**) across FastAPI + SQLAlchemy Async + Next.js 14 App Router. The plan reconciles existing backend transaction/test regressions on `dev`, adds an idempotent `POST /api/v1/orders/{order_id}/qr` endpoint, builds missing frontend infrastructure (`api-client.ts`, `utils.ts`, service alignments, interactive Leaflet `RadarMap`), and creates the App Router pages.

## Technical Context

**Language/Version**: Python 3.11.17 (Backend), TypeScript 5.4 (`strict: true`, Frontend)
**Primary Dependencies**: FastAPI 0.111, SQLAlchemy 2.0.30 (async), GeoAlchemy2, Redis 7 (`redis-py`), Next.js 14.2.4, React 18.3, TanStack React Query 5, Axios 1.7, Leaflet 1.9 + react-leaflet 4.2, `qrcode.react` 3.1
**Storage**: PostgreSQL 16 + PostGIS 3.4 (production/Docker) / SQLite `aiosqlite` (local fallback & pytest)
**Testing**: `pytest` + `pytest-asyncio` (backend), `ruff` + `mypy` (backend static), `next lint` + `tsc --noEmit` + `next build` (frontend)
**Target Platform**: Web browser (desktop & mobile responsive) + FastAPI ASGI server
**Project Type**: Full-stack web application (`backend/` + `frontend/`)
**Constraints**: Must obey all 8 guardrails in `AGENTS.md` (no hardcoded secrets, RBAC via `require_roles`, PostGIS spatial discovery, atomic SQL decrement + Redis lock, rule-based pricing, HMAC-SHA256 single-use QR).

## Constitution Check

*GATE: Passed against `.specify/memory/constitution.md` and `AGENTS.md`.*

- [x] **3-Tier Architecture**: Router (`orders.py`) -> Service (`order_service.py`, `qr_service.py`) -> Repository (`order_repo.py`, `qr_token_repo.py`, `dish_repo.py`).
- [x] **Guardrail #1 (No Secrets)**: All config via `pydantic-settings` and `NEXT_PUBLIC_API_BASE_URL`.
- [x] **Guardrail #2 (RBAC & Spatial)**: `require_roles` on all order/QR endpoints; `ST_DWithin` / `ST_Distance` in `store_repo.py` with `1–10 km` validation.
- [x] **Guardrail #3 (HMAC QR)**: `POST /orders/{order_id}/qr` uses `QRService.generate_order_qr_token` / `build_qr_payload_string`; `POST /orders/verify-qr` uses atomic `mark_token_as_used`.
- [x] **Guardrail #4 (Anti-Overselling)**: `dish_repo.atomic_decrement_quantity` + `distributed_lock`.
- [x] **Guardrail #5 (Rule-Based Discount)**: Deterministic `DishService.calculate_time_shifted_discount`.

## Project Structure

### Documentation (this feature)

```text
specs/001-rescue-discovery-order-qr/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── checklists/
│   └── requirements.md
└── contracts/
    └── api-contracts.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/v1/endpoints/orders.py       # Add POST /{order_id}/qr
│   ├── db/seed.py                       # Ensure demo dishes span daytime+evening hours
│   ├── schemas/order.py                 # Add QRPayloadResponse
│   └── services/order_service.py        # Fix lint/format, rollback expiration, add issue_or_get_qr_payload
└── tests/
    ├── integration/test_api_orders.py   # Add QR issuance integration tests
    └── integration/test_order_concurrency.py # Ensure isolated sessions pass concurrency benchmark

frontend/
├── src/
│   ├── app/
│   │   ├── globals.css                  # Tailwind + Leaflet CSS
│   │   ├── layout.tsx                   # Root layout with QueryProvider & Navbar
│   │   ├── page.tsx                     # Consumer Discovery Radar & Rescue Order modal
│   │   ├── login/page.tsx               # Login + quick demo account selector
│   │   ├── register/page.tsx            # Account registration
│   │   ├── orders/page.tsx              # Order history, cancel, dynamic QR modal
│   │   └── store/
│   │       ├── onboard/page.tsx         # Merchant KYC onboarding form
│   │       └── verify-qr/page.tsx       # Store Partner QR verification & anti-replay demo
│   ├── components/
│   │   ├── radar/RadarMap.tsx           # Real Leaflet interactive map
│   │   └── ui/
│   │       ├── Navbar.tsx               # Role-aware links + auth state/logout
│   │       └── BottomNavigation.tsx     # Mobile nav updated with /orders & /store/verify-qr
│   ├── lib/
│   │   ├── api-client.ts                # Axios client + Bearer interceptor + refresh
│   │   └── utils.ts                     # cn(), formatVND(), formatDistance()
│   ├── services/
│   │   ├── discovery.service.ts         # Fixed /stores/nearby endpoint
│   │   └── order.service.ts             # Aligned fields + detail, QR issue & verify methods
│   └── types/api.ts                     # Added Order, QRPayload, QRVerification, Auth types
```

## Complexity Tracking

No constitution violations. All changes either fix existing regressions on `dev` or complete missing frontend/API wiring for the selected functional group.
