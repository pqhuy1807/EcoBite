# Phase 0 Research: Consumer Surplus Discovery, Anti-Overselling Order & Dynamic QR Pickup

**Feature**: `001-rescue-discovery-order-qr`
**Date**: 2026-11-14

## 1. Existing Codebase Audit & Integration Findings

### Decision 1: Reconcile Frontend Service Contracts with Actual FastAPI Endpoints
- **Finding**: Pre-existing `frontend/src/services/discovery.service.ts` called `/discovery/nearby` and `order.service.ts` used mismatched field names (`total_price`, `green_points`), while `frontend/src/lib/api-client.ts` and `frontend/src/lib/utils.ts` were missing.
- **Decision**: Create `src/lib/api-client.ts` and `src/lib/utils.ts`, update `discovery.service.ts` to call `GET /stores/nearby` returning `NearbyStoresResponse` (already typed accurately in `src/types/api.ts`), and align `order.service.ts` with backend `OrderResponse`, `OrderDetailResponse`, `QRPayloadResponse`, and `QRVerificationResponse`.
- **Rationale**: Keeps the backend REST contract canonical (`backend/app/api/v1/endpoints/`) and eliminates runtime 404/NaN mismatches in the UI.
- **Alternatives considered**: Adding duplicate alias endpoints in FastAPI; rejected to avoid polluting the API surface.

### Decision 2: Idempotent `POST /api/v1/orders/{order_id}/qr` Endpoint for Pickup QR Payload
- **Finding**: `QRService.generate_order_qr_token` exists in `backend/app/services/qr_service.py`, and `OrderDetailResponse` exposes `QRTokenResponse` (`token_hash`, `nonce`, `expires_at`), but `OrderService.create_rescue_order` intentionally does not auto-create `QRToken` rows because `tests/integration/test_api_orders.py` explicitly tests manual `QRService.generate_order_qr_token` calls after order placement.
- **Decision**: Add `POST /api/v1/orders/{order_id}/qr` (`CONSUMER` owner only) backed by `OrderService.issue_or_get_qr_payload`. If no `QRToken` exists for an eligible (`CONFIRMED` / `READY_FOR_PICKUP`, unexpired) order, it calls `QRService.generate_order_qr_token`; if a valid unused `QRToken` already exists, it reconstructs and returns the canonical `ecobite://pickup?...` URI string from the stored `nonce`, `expires_at`, and `token_hash` (signature).
- **Rationale**: Zero regression on existing 12 QR integration tests while providing a deterministic, single-call endpoint for the Frontend `/orders` QR modal.
- **Alternatives considered**: Auto-generating QR tokens inside `create_rescue_order`; rejected because it breaks existing integration test assumptions (`test_api_orders.py` expects no pre-existing QR token after `POST /orders`).

### Decision 3: Fix `OrderService` Transaction Rollback & `MissingGreenlet` / SQLite Concurrency Issues
- **Finding**: Baseline checks on `dev` showed 2 `ruff` errors in `order_service.py`, 4 unformatted backend files, and 7 `pytest` failures caused by calling `await self.db.rollback()` on no-op `409` paths (expiring `store`/`dish`/`order` ORM objects in `db_session` -> `MissingGreenlet`) and `begin_nested()` savepoint contention on SQLite `StaticPool` during the 50-request concurrency benchmark.
- **Decision**:
  1. Never call `self.db.rollback()` when `atomic_decrement_quantity` or `cancel_if_allowed` matched 0 rows (no write occurred).
  2. Capture `order_status_value` before any state mutation/rollback.
  3. Use savepoint-scoped rollback / non-expiring rollback handling so failed writes roll back atomically without breaking caller-held ORM references, and ensure `test_order_concurrency.py` uses independent connection-per-session behavior cleanly.
- **Rationale**: Restores 100% green backend test suite (including the 50-request concurrency benchmark) while preserving atomic multi-step transactions in production.

### Decision 4: Interactive Leaflet Map & Demo-Friendly Seed Hours
- **Finding**: `RadarMap.tsx` is a placeholder div, and `backend/app/db/seed.py` seeds all dishes with pickup times between `13:00` and `21:00`, which blocks live demo ordering if demonstrated in the morning.
- **Decision**: Implement `RadarMap.tsx` with `react-leaflet` (`MapContainer`, `TileLayer`, `Circle`, `Marker`, `Popup`) and adjust selected District 1/5/Thu Duc demo dishes in `seed.py` to span `06:00–23:59` so live E2E ordering works at any time of day.
- **Alternatives considered**: Hardcoding mock dishes in frontend; rejected because PA3 requires real end-to-end API + DB persistence.
