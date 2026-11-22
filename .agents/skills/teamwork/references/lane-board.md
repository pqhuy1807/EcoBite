# Lane Board — `<goal title>`

> The Lead owns this board. Update it before dispatch and after every integration step.

## Goal contract

- Link: `<specs/<feature>/goal.md or docs/goals/...>`
- Status: `PLANNING` | `RUNNING` | `INTEGRATING` | `DONE` | `BLOCKED`

## Lanes

| Lane | Owner | Scope | Files owned (write) | Inputs | Outputs | Acceptance check | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | general | `<scope>` | `<paths>` | `<contracts / files>` | `<deliverable>` | `<command / test>` | — | TODO |
| B | general | `<scope>` | `<paths>` | `<contracts / files>` | `<deliverable>` | `<command / test>` | A | TODO |
| C | explore | Read-only audit | none | `<questions>` | `<facts>` | `<review>` | — | TODO |
| Lead | you | Integration + shared files | `<router / schema / config>` | all lane outputs | verified change | full suite | A, B, C | TODO |

## Ownership check

- [ ] Every file appears in exactly one "Files owned" column.
- [ ] Shared files are owned by the Lead or one integration lane.
- [ ] No lane depends on an unfrozen interface.
- [ ] Every lane has at least one acceptance check.
- [ ] No two lanes run migrations or edit package manifests.

## Integration log

| Step | Action | Checks run | Result | Notes |
| --- | --- | --- | --- | --- |
| 1 | `<merge / review>` | `<command>` | PASS/FAIL | `<note>` |

## Final audit

- [ ] All lane checks pass.
- [ ] Full backend suite passes.
- [ ] Full frontend lint/type-check passes.
- [ ] Every goal acceptance criterion has evidence.
- [ ] Remaining risks and follow-ups are recorded.
