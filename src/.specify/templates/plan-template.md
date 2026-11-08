# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Architecture Overview & Component Relationships

<!-- Describes where this feature lives in the EcoBite system and how components interact. Keep technology-agnostic; details go to Technical Context. -->

- **Layer flow**: Client (Next.js PWA) → API Router (input validation via Pydantic schemas) → Service layer (business logic, framework-free) → Data access (async SQLAlchemy models) → PostgreSQL 16 + PostGIS. Side components: Redis (locks/cache), Gemini (only after DB-level safety filtering), VNPay (payment gateway).
- **Cross-cutting concerns**: authentication via `get_current_user` / `require_roles(...)` dependencies; per-request async session via `get_db`; configuration read only from `app.core.config.settings` (pydantic-settings).
- **Affected components**: [Enumerate every module the feature touches, e.g. `backend/app/api/v1/endpoints/...`, `backend/app/services/...`, `backend/app/models/...`, with one-line responsibility]
- **External integrations** (if any): [e.g., VNPay IPN — failure modes: timeout, duplicate callback (idempotency required); Gemini — failure mode: invalid structured output, must not block DB-level safety filters]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**EcoBite Baseline (inherited from `constitution.md` — override only when the feature justifiably requires it)**: Python 3.11 · FastAPI (fully async) · Pydantic v2 · SQLAlchemy 2.0 async (`aiosqlite` for dev/test, `asyncpg` for PostgreSQL 16 + PostGIS; sync drivers only in Alembic) · JWT via `python-jose` HS256 with expiry · bcrypt hashing via passlib (`bcrypt==4.0.1` pinned) · pytest + pytest-asyncio · ruff + mypy gates · Redis 7 · Google Gemini 2.5 Flash · Next.js 14 App Router frontend

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
