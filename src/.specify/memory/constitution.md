# EcoBite Constitution

***Project:** EcoBite – Food Rescue & Zero-Waste Platform

**Organization:** Group 05 – HCMUS
**Purpose:** Establish mandatory engineering principles, architectural constraints, quality standards, and governance rules for all contributors and AI Coding Agents.

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

All new business logic, bug fixes, and significant refactoring MUST follow a test-first development approach.

- Analyze requirements, existing architecture, user roles, and edge cases before implementation.
- Write or update relevant tests before or alongside implementation.
- Backend business logic in `backend/app/services/` and API endpoints in `backend/app/api/` MUST have corresponding tests in `backend/tests/`.
- Frontend components containing important business logic and custom hooks MUST have corresponding tests in `frontend/__tests__/`.
- Follow the Red-Green-Refactor cycle: establish a failing test, implement the solution, and refactor while keeping tests passing.
- Tests MUST cover relevant normal cases, boundary conditions, invalid inputs, and failure scenarios.

No feature is considered complete merely because its code has been written.

### II. Security, Privacy & Access Control

Security MUST be enforced at the application, API, database, and integration boundaries.

- Never commit `.env` files, API keys, passwords, tokens, private certificates, or other secrets.
- Load configuration and sensitive values through environment variables and `pydantic-settings`.
- Protect sensitive APIs with role-based authorization using the `require_roles(...)` dependency.
- Support the defined application roles: `CONSUMER`, `STORE_PARTNER`, and `ADMIN`.
- Validate and authorize user input on the server side; frontend restrictions alone are insufficient.
- Apply appropriate input validation, error handling, and secure logging. Sensitive credentials and payment data MUST NOT appear in logs.
- AI-generated code MUST NOT bypass existing authentication, authorization, or data-protection requirements.

### III. Data Integrity & Transactional Consistency

Database correctness and consistency are mandatory, especially for inventory, orders, and payments.

- Use PostgreSQL 16 with PostGIS for persistent and geospatial data.
- Use database transactions for operations that modify related business records.
- Prevent overselling through an atomic inventory update with a sufficient-quantity condition, such as:

  `UPDATE dishes SET remaining_quantity = remaining_quantity - :qty WHERE remaining_quantity >= :qty`

  The operation MUST verify the affected row count and handle insufficient inventory correctly.
- Redis distributed locks MAY be used as an additional concurrency-control mechanism where appropriate; they MUST NOT replace database-level integrity guarantees.
- Payment callbacks and other retryable operations MUST be idempotent to prevent duplicate business effects.
- Handle concurrent requests, duplicate submissions, expired orders, and network failures explicitly.

### IV. Food Safety & Allergen Protection

Food information and allergen handling MUST prioritize consumer safety and transparency.

- EcoBite MUST display identifiable surplus dishes rather than using undisclosed mystery-bag descriptions.
- Food listings SHOULD provide accurate names, images, original prices, discounted prices, ingredients, and available allergen information.
- Allergen information MUST distinguish between:
  - `EXPLICIT`: information explicitly provided by the store partner.
  - `INFERRED`: information inferred by AI from food knowledge and ingredients.
- Allergen handling MUST consider the 14 allergen categories referenced by EU FIC in the project requirements.
- The recommendation engine MUST enforce `excluded_allergens` as a hard filter at the database query level before generating AI explanations.
- Gemini MUST NOT be treated as the authority for deciding whether a dish is safe for a user with an allergy.
- Inferred allergen information MUST be identifiable as AI-inferred information and MUST NOT be presented as a medically guaranteed assessment.
- When information is incomplete or uncertain, the system MUST communicate that limitation rather than silently assuming a dish is safe.

### V. Deterministic Business Rules & Payment Integrity

Critical business and financial operations MUST use deterministic, verifiable rules.

- Discount calculation MUST follow the defined time-based business rules, not AI-generated price predictions.
- Standard rescue periods MUST apply the configured 40–50% discount range; the final 30–45 minutes before closing MUST follow the configured last-minute discount rule of up to 70%.
- The backend MUST be the authoritative source for discount and payment calculations.
- Order QR tokens MUST use HMAC-SHA256 signatures, expiration validation, and a single-use mechanism through the `is_used` state to prevent replay.
- VNPay IPN callbacks MUST verify HMAC-SHA512 signatures before accepting payment results.
- Payment processing MUST be idempotent and MUST reject invalid or duplicated callback effects.
- Order completion and review eligibility MUST be based on verified order status, including successful QR pickup confirmation.

### VI. AI Reliability, Structured Output & Model Isolation

AI features MUST support business workflows without replacing deterministic safety and integrity controls.

- Use Google Gemini 2.5 Flash through the Google GenAI SDK for the project's defined generative AI capabilities.
- AI responses used by business logic MUST follow validated structured schemas, including `QuickPostExtractionResponse` where applicable.
- Quick-post extraction MUST ground dish information against the original `menu_items` catalog when matching images and original prices.
- AI allergen extraction MUST preserve the distinction between `EXPLICIT` and `INFERRED` sources.
- Natural-language time expressions MUST be converted using authoritative server time rather than relying on an unverified client clock.
- Recommendation ranking MAY use heuristic scoring and AI-generated explanations, but database-level safety filters MUST run first.
- Machine-learning models MUST NOT be loaded inside individual request bodies. Backend inference models MUST use the application lifespan and a shared singleton such as `app.state.ml_model`, with inference executed under `torch.no_grad()` where applicable.
- Heavy model-training and notebook dependencies, including `ultralytics`, `jupyterlab`, and `matplotlib`, MUST NOT be added to `backend/requirements.txt`. Backend dependencies MUST remain focused on inference and serving.

### VII. Clean Architecture & Maintainable Code

All implementation MUST follow the established project architecture and technology conventions.

- Frontend: Next.js 14 App Router, TypeScript, and Tailwind CSS.
- Backend: FastAPI, Python 3.11, Pydantic v2, and SQLAlchemy 2.0.
- Infrastructure: PostgreSQL 16 with PostGIS and Redis 7.
- Use asynchronous programming appropriately. FastAPI async routes MUST NOT execute blocking I/O directly.
- SQLAlchemy models SHOULD use typed mappings such as `Mapped[T]`.
- Prefer Next.js Server Components by default. Use `'use client'` only when browser APIs, state, hooks, or client-side interaction require it.
- Keep responsibilities separated between API routes, services, data access, and presentation components.
- Avoid unnecessary abstractions, duplicated business logic, and unrelated changes.
- Follow existing naming conventions and repository structure.

### VIII. Verifiable Quality & Human Accountability

Code quality MUST be demonstrated through reproducible verification, not assumptions or AI claims.

- Every change MUST pass the applicable linting, formatting, static type-checking, and automated tests before it is proposed for commit.
- Backend verification MUST include the configured Ruff checks, Ruff format check, mypy, and pytest suites.
- Frontend verification MUST include the configured lint and TypeScript type-check commands.
- Pre-commit hooks MUST be used to enforce repository checks, prevent secrets and oversized model files from being committed, and apply configured formatting.
- CI MUST validate changes in a clean environment, including the required database and Redis services where integration tests depend on them.
- The project quality workflow targets at least 80% test coverage as specified in the team's Quality Gates documentation.
- Human review MUST remain part of the Pull Request process. AI-generated code is not exempt from review.
- Contributors and AI agents MUST report verification results honestly. A command that was not executed MUST NOT be reported as passed.

## Additional Constraints

### Technology and Infrastructure

- The system follows a decoupled three-tier architecture.
- The frontend is delivered as a Progressive Web App (PWA) using Next.js 14.
- The backend exposes RESTful APIs through FastAPI.
- PostgreSQL and PostGIS are the authoritative persistent and geospatial data stores.
- Redis supports caching and distributed coordination where required.
- VNPay is the designated payment gateway.
- Google Gemini 2.5 Flash supports the project's defined AI-assisted workflows.

### Required Project Structure for Tests

Backend tests:

- `backend/tests/conftest.py`
- `backend/tests/unit/`
- `backend/tests/integration/`

Frontend tests:

- `frontend/__tests__/components/`
- `frontend/__tests__/hooks/`

Test files SHOULD follow the naming conventions defined in `AGENTS.md` and the team's quality workflow documentation.

### Git and Commit Standards

- Use Conventional Commits.
- Supported commit prefixes include `feat`, `fix`, `test`, `refactor`, and `docs`.
- Commit messages MUST clearly describe the affected scope and purpose.
- Never commit secrets, local environment files, or prohibited large model artifacts.
- Changes MUST be reviewed and validated before merging into `main`.

## Development Workflow & Quality Gates

Every feature, bug fix, or significant refactoring MUST follow this five-step development loop:

1. **Analyze & Plan:** Read relevant documentation, identify affected components, roles, dependencies, and edge cases.
2. **Write Tests First:** Add or update tests for the expected behavior and failure scenarios.
3. **Implement Code:** Make the smallest maintainable change that satisfies the requirements.
4. **Execute Verification Loop:** Run applicable checks, inspect failures, fix the underlying problems, and rerun verification.
5. **Propose Commit:** Report the changes and verification results, then propose a Conventional Commit message.

Changes MUST also pass the team's four Quality Gates:

1. **Gate 1 – AI Self-Verification:** Local tests, linting, formatting, and type-checking.
2. **Gate 2 – Git Pre-commit:** Automated checks for staged changes, secrets, oversized files, and formatting.
3. **Gate 3 – Human Pull Request Review:** Peer or Tech Lead review and Definition of Done verification.
4. **Gate 4 – CI/CD:** Automated verification in a clean GitHub Actions environment, including required services and test coverage checks.

Passing local tests does not replace human review or CI validation.

## Governance

- This Constitution defines the mandatory engineering principles for EcoBite and applies to all four team members and all AI Coding Agents contributing to the repository.
- The Constitution MUST be read together with `AGENTS.md`, the system architecture, API specification, database schema, and quality workflow documentation.
- If implementation guidance conflicts with this Constitution, the Constitution takes precedence for engineering principles and mandatory constraints. More specific technical details remain governed by the relevant project specifications unless they violate these principles.
- Every Pull Request MUST be checked for compliance with the applicable principles, security requirements, tests, and Quality Gates.
- Exceptions MUST be explicitly documented with their rationale, impact, and approval from the responsible team members before implementation.
- Amendments require team discussion and approval. Changes MUST update the version and amendment date and MUST be communicated to all contributors.
- AI Coding Agents MUST explain significant trade-offs and MUST NOT silently weaken security, food-safety, data-integrity, or testing requirements.
- The Constitution SHOULD be reviewed whenever the architecture, technology stack, or core business rules change.

**Version**: 1.0.0 | **Ratified**: Pending team approval | **Last Amended**: 2026-10-30