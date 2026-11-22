# Subagent Brief — `<lane id>`

> A subagent starts with fresh context. If a fact is not in this brief, it does not exist for the subagent. Be explicit.

## Mission

One sentence: `<what to deliver>` for `<which goal>`.

## Goal contract

- Link: `<specs/<feature>/goal.md or docs/goals/...>`
- Relevant acceptance criteria: `AC-...`

## Context

- **Repository**: `D:\EcoBite`
- **Architecture**: Router -> Service -> Repository. No SQL in routers; no business logic in repositories.
- **Relevant paths**:
  - `<path>` — `<why it matters>`
  - `<path>` — `<existing pattern to follow>`
- **Contracts already frozen**:
  - `<signature / JSON shape / DB column / error code>`

## Ownership

### You may edit

- `<path>`
- `<path>`

### You must not touch

- `<shared file>` — owned by the Lead
- `<other lane's file>`
- `.env`, secrets, migrations unless explicitly listed above.

## Constraints

- Follow `AGENTS.md` and `.specify/memory/constitution.md`.
- No new dependency unless approved: `<approved list>`.
- Keep changes inside the ownership list. If you need another file, stop and ask.
- Preserve existing public APIs unless the brief says otherwise.
- Do not commit, push, or rewrite git history.

## Deliverable

- Code/docs: `<expected result>`
- Tests: `<which tests to add/update>`
- Verification commands: `<exact commands>`
- Report: status, files changed, commands run with results, blockers.

## Stop conditions

Stop and report instead of guessing when:

- A required file is outside your ownership.
- The frozen interface does not fit the code.
- A test fails for a reason outside your lane.
- You need a secret, destructive action, or new dependency.
- You are blocked after 2 genuine attempts.

## Report format

```text
STATUS: DONE | PARTIAL | BLOCKED
FILES CHANGED:
- <path> — <summary>
CHECKS:
- <command> — <result>
BLOCKERS / QUESTIONS:
- <none or list>
```
