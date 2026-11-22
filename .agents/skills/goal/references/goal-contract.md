# Goal Contract — `<short title>`

> Copy this file, fill every section, and keep it updated. A blank section is a known risk, not a formality.

## 1. Outcome

- **One-sentence goal**: We will `<outcome>` for `<user>` so that `<value>`.
- **Work type**: feature | bug | refactor | docs | investigation | incident
- **Owner / decision maker**: `<name or role>`
- **Date opened**: `<YYYY-MM-DD>`
- **Linked artifacts**: `spec.md` | issue | PR | design doc | ADR

## 2. Why now

- **User problem**:
- **Business / technical value**:
- **Cost of not doing it**:

## 3. Scope

### In scope

- [ ] `<deliverable 1>`
- [ ] `<deliverable 2>`

### Out of scope (explicit)

- `<non-goal 1>`
- `<non-goal 2>`

### Parking lot (deferred, not lost)

- `<idea>` — reason deferred

## 4. Constraints

- **Architecture**: Router -> Service -> Repository; no SQL in routers; no business logic in repositories.
- **Security**: no secrets in code; RBAC via `require_roles(...)`; QR/payment signatures verified.
- **Data integrity**: atomic inventory updates; idempotent callbacks; transactions for related writes.
- **Frontend**: Next.js 14 App Router; API calls through `@/lib/api-client`; `strict: true`.
- **ML**: inference only in backend; no training dependencies; no model load inside request bodies.
- **Compatibility**: `<APIs, DB columns, migrations, browsers>`
- **Performance**: `<latency / throughput / payload budgets>`
- **Dependencies**: no new dependency unless approved: `<approved list>`

## 5. Acceptance criteria

| ID | Criterion (observable) | Evidence (command / file / test) | Status |
| --- | --- | --- | --- |
| AC-1 | `<behavior>` | `<command or artifact>` | ☐ |
| AC-2 | `<negative / boundary case>` | `<command or artifact>` | ☐ |
| AC-3 | `<regression check>` | `<command or artifact>` | ☐ |

Rules:

- Each criterion must be pass/fail, not a matter of opinion.
- Include at least one negative case for input validation and one boundary case.
- If a criterion cannot be automated, name the manual evidence artifact.

## 6. Verification plan

| Layer | Command | Expected result |
| --- | --- | --- |
| Backend lint | `ruff check app/` | exit 0 |
| Backend format | `ruff format --check app/` | exit 0 |
| Backend types | `mypy app/` | exit 0 |
| Backend tests | `pytest tests/ -v` | all pass |
| Frontend lint | `npm run lint` | exit 0 |
| Frontend types | `npm run type-check` | exit 0 |
| Spec-Kit | `.specify/scripts/powershell/check-prerequisites.ps1 ...` | expected JSON |

## 7. Milestones

| Milestone | Outcome | Files | Checks | Depends on | Rollback |
| --- | --- | --- | --- | --- | --- |
| M1 | `<outcome>` | `<paths>` | `<checks>` | — | `<how>` |
| M2 | `<outcome>` | `<paths>` | `<checks>` | M1 | `<how>` |

## 8. Risks

| Risk | Likelihood | Impact | Mitigation | Trigger to escalate |
| --- | --- | --- | --- | --- |
| `<risk>` | low/med/high | low/med/high | `<action>` | `<condition>` |

## 9. Stop conditions

- [ ] Conflicting requirements or guardrail violation.
- [ ] Destructive/irreversible action without approval.
- [ ] Secret or credential required.
- [ ] Same failure after 2 fix attempts.
- [ ] Scope cannot be verified in one goal.

## 10. Decision log

| Date | Decision | Alternatives considered | Rationale | Approved by |
| --- | --- | --- | --- | --- |
| `<date>` | `<decision>` | `<alternatives>` | `<why>` | `<name>` |

## 11. Completion

- **Status**: `DONE` | `PARTIAL` | `BLOCKED`
- **AC evidence**: `<link to completion report>`
- **Deviations**: `<none or list>`
- **Follow-ups**: `<issues created>`
