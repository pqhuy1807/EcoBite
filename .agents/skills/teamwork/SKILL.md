---
name: teamwork
description: Use for large, multi-file, or parallelizable work, or when the user mentions teamwork, chia việc, nhiều agent, parallel, or subagent. Act as team lead: define lanes with disjoint file ownership, brief subagents, run discovery in parallel, serialize shared-file edits, integrate, and verify.
compatibility: "OpenCode subagents (explore / general); reads AGENTS.md and .specify/memory/constitution.md"
---

# Teamwork Orchestration

You are the **Team Lead**. Your job is not to make every edit yourself; it is to make parallel work safe, integrate it, and prove it works.

## When to use
 
Use this skill when:

- Work naturally splits into independent modules (backend endpoint + frontend page + tests + docs).
- Discovery is broad (find all call sites, map a module, compare patterns).
- Time-to-result matters and lanes do not share files.
- An independent review or verification pass is useful.

Do **not** use it for a small single-file change, a tightly coupled refactor, or work where every step depends on the previous one. Do it directly.

## Non-negotiable rules

1. **One writer per file.** No two lanes may edit the same file. Shared files (routers, schemas, package manifests, migrations, config) are owned by the Lead or a single integration lane.
2. **Interface first.** Freeze contracts (function signatures, API shapes, DTOs, file paths, error codes) before parallel implementation.
3. **Self-contained briefs.** A subagent starts with fresh context; include every path, constraint, and acceptance check it needs.
4. **No blind trust.** Subagent reports are claims. The Lead reviews diffs and runs final verification.
5. **Bounded fan-out.** Start with 2–4 lanes; add more only when ownership is disjoint. Keep delegation depth at 1 unless explicitly allowed.
6. **Goal before team.** Use the `goal` skill to define the Goal Contract. No contract, no dispatch.

## Workflow

### 1. Establish the Goal Contract

Outcome, acceptance criteria, constraints, stop conditions. Link it in every brief.

### 2. Freeze interfaces

Write the shared contract down: file paths, signatures, JSON shapes, DB columns, error codes. If interfaces are unstable, do recon first, then freeze.

### 3. Build the Lane Board

Use `references/lane-board.md`. Columns: Lane, Owner, Scope, Files owned, Inputs, Outputs, Acceptance check, Depends on.

Rules:

- Every file has exactly one owner.
- Every lane has at least one check.
- Shared files are assigned to the Lead/integration lane.
- If two lanes need the same file, merge them or serialize.

### 4. Recon in parallel (read-only)

Dispatch 1–3 `explore` subagents with narrow questions:

- "Map the order creation flow from router to repository; list files and tests."
- "Find every frontend call site of `/orders`; list types and error handling."

Ask for a concise fact list with `file:line`, not opinions. Reconcile findings before planning edits.

### 5. Write briefs

Use `references/subagent-brief.md`. A good brief has:

- **Mission** in one sentence.
- **Context**: goal, architecture, exact paths, relevant patterns.
- **Ownership**: files you may edit; files you must not touch.
- **Constraints**: `AGENTS.md` guardrails, style, no new dependencies unless approved.
- **Deliverable**: code/docs + tests + commands run + results.
- **Stop conditions**: ask instead of guessing.
- **Report format**: status, files changed, checks, blockers.

### 6. Dispatch

- Run independent lanes in parallel; serialize dependent lanes.
- In OpenCode, use the `subagent` tool: `explore` for read-only discovery, `general` for implementation. Pass `sessionID` for follow-ups.
- Subagents run in the background. Keep working on non-overlapping tasks and do not poll.
- If a lane stalls, ask a specific status question. Do not spawn a duplicate lane.

### 7. Integrate

- Review every diff before accepting it.
- Resolve conflicts at the interface, not by overwriting a lane.
- Run the full verification suite, not only per-lane checks.
- Re-run affected checks after each integration step.

### 8. Report

Lane table: lane | owner | status | evidence. Then the goal-level AC table. List unresolved risks and follow-ups.

## Conflict protocol

When two lanes disagree or overlap:

1. Stop both edits to the contested file.
2. The Lead decides the interface and records the decision.
3. One lane implements; the other adapts.
4. Re-run both lanes' checks.

Never "merge" by letting both agents edit and hoping git resolves it.

## Anti-patterns

- Spawning agents before the goal and interfaces are clear.
- Vague briefs ("improve the backend").
- Two agents editing the same router, schema, or migration.
- Parallel database migrations.
- Trusting "done" without diffs and command output.
- Too many lanes; coordination cost exceeds the work.
- Nested subagents with unclear ownership.

## EcoBite lane example

Feature: "Add order cancellation API + UI".

| Lane | Owner | Scope | Files owned |
| --- | --- | --- | --- |
| A | general | Backend service/repo/tests | `backend/app/services/order_service.py`, `backend/app/repositories/order_repo.py`, `backend/tests/...` |
| B | general | Frontend service/UI (+ tests nếu Vitest đã wire) | `frontend/src/services/order.service.ts`, `frontend/src/app/orders/...`, `frontend/__tests__/...` |
| C | explore | Contract/consistency audit | read-only |
| Lead | you | Router, shared schemas, integration, final verification | `backend/app/api/v1/endpoints/orders.py`, `backend/app/schemas/order.py`, `backend/app/api/v1/router.py` |

If Lane A and Lane B both need a DTO, the Lead freezes it first. If both need the router, only the Lead edits it. If the frontend test runner is not configured yet, Lane B runs `npm run lint` and `npm run type-check`, and reports the missing test runner as a known limitation instead of claiming test coverage.

## Project integration

Pair this skill with `goal` for the contract and with the verification loop in `AGENTS.md`. The Lead always runs the final backend and frontend checks before reporting completion.
