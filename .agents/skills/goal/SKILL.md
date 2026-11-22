---
name: goal
description: Use when a request is ambiguous, multi-step, high-stakes, or when the user mentions goal, mục tiêu, definition of done, acceptance criteria, or planning. Convert the request into a falsifiable Goal Contract before implementation, then execute and report evidence against it.
compatibility: "OpenCode / Antigravity; reads AGENTS.md and .specify/memory/constitution.md"
---

# Goal Contract 

A goal is a contract, not a wish. Never start implementation from a vague request.

This skill turns a request into a **falsifiable execution contract**: outcome, scope, constraints, acceptance criteria, verification commands, and stop conditions. It then keeps the work anchored to that contract until every criterion has evidence.

## When to use

Use this skill when:

- The request has more than one plausible interpretation.
- Work spans multiple files, layers, sessions, or agents.
- "Done" is subjective, or the user asks for a plan, estimate, or definition of done.
- The area is high-stakes: auth, payments, inventory, allergens, migrations, secrets, production data.
- The user says: "goal", "mục tiêu", "làm cho xong", "definition of done", "acceptance criteria", "kế hoạch", "chốt yêu cầu".

Skip only for a trivial, single-step change with an obvious check (typo, one-line fix). Even then, state the check in one sentence.

## Non-negotiable rules

1. **No implementation before the contract is written** unless the user explicitly says "just do it" and the change is reversible and low-risk. State assumptions explicitly.
2. **Every acceptance criterion must be falsifiable.** It must name an observable result and the evidence that proves it (test, command, file, API response, screenshot).
3. **Scope is closed.** New requests go to "Parking lot" or a new goal; they do not silently expand the current one.
4. **No false completion.** A criterion is met only when the evidence exists in this session. If a command was not run, say so.
5. **Change control.** If the goal must change, update the contract and get explicit approval before continuing.
6. **Respect project guardrails.** Read `AGENTS.md` and `.specify/memory/constitution.md`. Secrets, RBAC, atomic inventory, QR/payment signatures, allergen hard filters, and decoupled ML are non-negotiable.

## Workflow

### 1. Restate and classify

Restate the request in one sentence:

> We will `<outcome>` for `<user>` so that `<value>`.

Classify the work: `feature` | `bug` | `refactor` | `docs` | `investigation` | `incident`.

If ambiguous, ask at most **3 blocking questions**. If the ambiguity is non-blocking, state assumptions and proceed. Do not interview the user about details that can be discovered from the repository.

### 2. Write the Goal Contract

Copy `references/goal-contract.md` and fill it. Store it at:

- Active spec-kit feature: `specs/<feature>/goal.md` (link to `spec.md`; do not duplicate requirements).
- Otherwise: `docs/goals/<YYYY-MM-DD>-<slug>.md`.

Minimum fields: outcome, user value, in scope, out of scope, constraints, acceptance criteria (`AC-1`, `AC-2`, ...), verification plan, risks, stop conditions, decision log.

### 3. Design verification before the solution

For each acceptance criterion, write the exact command or observation that will prove it. Prefer automated checks:

- Backend (from `backend/`, venv active): `ruff check app/`, `ruff format --check app/`, `mypy app/`, `pytest tests/ -v`.
- Frontend (from `frontend/`): `npm run lint`, `npm run type-check`.
- Spec-Kit: `.specify/scripts/powershell/check-prerequisites.ps1 ...`.

If a criterion cannot be automated, define a manual evidence artifact (screenshot, curl transcript, log excerpt).

### 4. Plan in milestones

Each milestone must have: outcome, files, checks, rollback. Keep milestones independently verifiable and mark dependencies. Do not plan beyond the goal.

### 5. Execute with drift control

- Re-read the contract before each milestone.
- Maintain a task list; keep exactly one item in progress.
- After each milestone, run its checks and record the result.
- If a check fails, fix and rerun. Do not proceed on red.
- If blocked after **2 genuine attempts**, stop and report options.

### 6. Final audit and report

Use `references/completion-report.md`. Map every acceptance criterion to evidence. Report:

- Status: `DONE` / `PARTIAL` / `BLOCKED`.
- AC table: criterion | evidence (command/file/test) | pass/fail.
- Commands actually run and their results.
- Deviations from the contract and why.
- Remaining risks and follow-ups.
- Proposed Conventional Commit.

Never write "all tests pass" without the command output. Never hide skipped checks.

## Acceptance criteria rules

Good:

> `POST /orders` returns `409` and leaves `remaining_quantity` unchanged when two consumers order the last item concurrently; `pytest tests/integration/test_order_concurrency.py -v` passes.

Bad:

> Ordering works well.

Use Given/When/Then when behavior is conditional. Include negative cases and boundaries. Each criterion must be independently checkable.

## Stop conditions

Stop and ask when:

- Two requirements conflict, or a guardrail would be violated.
- A destructive or irreversible action is needed (migration, data deletion, force-push).
- Secrets or credentials are required.
- The same failure persists after 2 fix attempts.
- The requested scope is too large to verify in one goal; split it.

## Anti-patterns

- Goal = restating the user's sentence without measurable criteria.
- Declaring "done" because code was written, not because checks passed.
- Silent scope creep.
- Writing tests after the fact to match the implementation.
- Treating a subagent's summary as verified fact.
- Editing the goal to match what was built without approval.

## Project integration

This skill complements the 5-step development loop and 8 guardrails in `AGENTS.md`. For multi-lane execution, pair it with the `teamwork` skill. For spec-kit features, let `spec.md` own requirements and keep `goal.md` as the execution contract that links to it.
