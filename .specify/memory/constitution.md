# EcoBite Platform Constitution

## Core Principles

### I. Three-Tier Backend Architecture (Router -> Service -> Repository)
All backend features MUST strictly separate HTTP handling (`app/api/v1/endpoints/`), business logic (`app/services/`), and SQLAlchemy 2.0 async data access (`app/repositories/`). Endpoints must never contain direct SQL queries; repositories must remain pure data-access layers.

### II. Security & Role-Based Access Control (Inviolable Guardrails #1 & #2)
- Never commit `.env` files, secrets, or credentials; all configuration must load through `pydantic-settings`.
- All protected endpoints must enforce `require_roles(...)` or `StoreOwner` ownership checks.
- Spatial discovery queries must use PostGIS (`ST_DWithin` / `ST_Distance`) with a validated `1–10 km` radius (with portable fallback for SQLite test environments).

### III. Anti-Overselling Inventory & Rule-Based Pricing (Inviolable Guardrails #4 & #5)
- Inventory decrements (`remaining_quantity`) MUST execute atomically inside a database transaction (`UPDATE ... WHERE id = :id AND remaining_quantity >= :qty`) guarded by a Redis distributed lock (`lock:dish:{dish_id}`), returning `409 Conflict` when insufficient stock exists.
- Order cancellation before pickup deadline must atomically transition status and restore dish stock in one transaction.
- Time-shifted discounts are strictly deterministic and rule-based.

### IV. Cryptographic Single-Use Pickup QR (Inviolable Guardrail #3)
- Pickup QR payloads (`ecobite://pickup?...`) MUST be signed with HMAC-SHA256 (`QR_SIGNATURE_SECRET`), include a cryptographic nonce and expiration timestamp, and enforce single-use atomic redemption (`WHERE is_used = FALSE`) to prevent replay attacks.

### V. End-to-End Frontend Quality (Next.js 14 App Router)
- All API calls must flow through a centralized typed Axios client (`@/lib/api-client`) with `NEXT_PUBLIC_API_BASE_URL` and automatic Bearer token injection.
- Interactive components must declare `'use client'`, use TanStack React Query for server state, and pass `next lint` and `tsc --noEmit` (`strict: true`) with zero errors.

### VI. Automated Verification Before Completion
No task is complete until backend (`ruff check`, `ruff format --check`, `mypy`, `pytest`) and frontend (`npm run lint`, `npm run type-check`, `npm run build`) pass 100%.
