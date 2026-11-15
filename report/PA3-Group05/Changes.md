# EcoBite PA3 Changes Log
> **Performed by:** Đặng Trọng Phúc | **Reviewed by:** Võ Ngọc Thịnh, Đàng Thế Tony | **Edited by:** Phùng Quốc Huy

**Project:** EcoBite — Food Rescue & Zero-Waste Platform
**Team:** Group 05 — CS300 / CSC13002 Introduction to Software Engineering, Faculty of Information Technology, VNU-HCM University of Science (HCMUS)
**Comparison:** PA2 (v1.0) → PA3 (v1.1)
**Date:** 14/11/2026
**Reporting period:** 01/11/2026 – 14/11/2026 (Sprint 3 — PA3)
**Companion report:** `PA3-Group05/reportPA3.md`

---

## Table of Contents

1. [Purpose, Scope and How to Read This Document](#purpose-scope-and-how-to-read-this-document)
2. [Changes to the Software Development Plan (Part A)](#1-changes-to-the-software-development-plan-part-a)
   - [1.1 Purpose and Method](#11-purpose-and-method)
   - [1.2 Addressing the PA2 Teaching-Assistant Feedback on Spec Kit](#12-addressing-the-pa2-teaching-assistant-feedback-on-spec-kit)
   - [1.3 Changes to the Schedule, Milestones and WBS](#13-changes-to-the-schedule-milestones-and-wbs)
   - [1.4 Changes to the Process, Workflow, Configuration and Risk Management](#14-changes-to-the-process-workflow-configuration-and-risk-management)
   - [1.5 Comparison Table for Part A](#15-comparison-table-for-part-a)
3. [Changes to the Vision Document (Part B)](#2-changes-to-the-vision-document-part-b)
   - [2.1 Changes to the Functional Requirements](#21-changes-to-the-functional-requirements)
   - [2.2 Changes to the Non-Functional Requirements](#22-changes-to-the-non-functional-requirements)
   - [2.3 Changes to the Alternatives, Competitors and User Environments](#23-changes-to-the-alternatives-competitors-and-user-environments)
   - [2.4 Comparison Table for Part B](#24-comparison-table-for-part-b)
4. [Impact Summary and Change-Control Record](#3-impact-summary-and-change-control-record)
   - [3.1 Aggregate Impact](#31-aggregate-impact)
   - [3.2 Traceability of Changes to Artefacts](#32-traceability-of-changes-to-artefacts)
   - [3.3 Change-Control Record](#33-change-control-record)
5. [Appendix A. Document Revision History](#appendix-a-document-revision-history)

---

## Purpose, Scope and How to Read This Document

This document is the **authoritative delta record** required by the PA3-2026 brief:

> *"Your team must include a Changes.md file that clearly lists all changes made compared to the PA2-2026 version. Use a single Changes.md file per PA submission, with separate sections for each revised document. Without this file, you will not receive points for this section."* — and, for Section B, *"Document all changes in the same Changes.md file used for Section A."*

It therefore contains **two independent parts**, one per revised document:

| Part | Revised document | Baseline | Revised version | Primary location in `reportPA3.md` |
| :--- | :--- | :--- | :--- | :--- |
| **Part A** (§1) | Software Development Plan | `PA2-Group05/reportPA2.md` §A, v1.0 (31/10/2026) | Part A of the PA3 report, v1.1 (14/11/2026) | §§A.1 – A.3 |
| **Part B** (§2) | Vision Document | `PA2-Group05/reportPA2.md` §B, v1.0 (31/10/2026) | Part B of the PA3 report, v1.1 (14/11/2026) | §§B.1 – B.4 |

**How to read the comparison tables.** Each table has five columns:

1. **`Change ID`** — a stable identifier (`CHG-A-nn` for the plan, `CHG-B-nn` for the Vision Document). The identifier is referenced from the report and from the change-control record, so a change can be traced in both directions.
2. **`Affected Section`** — where in the revised document the change lands.
3. **`PA2 Version (v1.0)`** — what the baseline document said.
4. **`PA3 Revised Version (v1.1)`** — what the revised document says.
5. **`Source / Rationale`** — the origin of the change: the **TA feedback from PA2**, **`Ke_Hoach_Tuan_Sprint_3_EcoBite.md`** (the Week-1 Sprint 3 plan, 02/11/2026 – 08/11/2026), **`WEEK_4_ACTION_PLAN.md`** (the Week-4 plan, 09/11/2026 – 15/11/2026), the Sprint-3 repository audit, or the PA3-2026 brief.

**Baseline sources consulted.** `PA2-Group05/reportPA2.md` (both Part A and Part B, in full), `PA2-Group05/Git_log_commit.txt`, `PA3-Group05/PA3-2026.pdf` (the assignment brief), `PA3-Group05/Ke_Hoach_Tuan_Sprint_3_EcoBite.md`, `PA3-Group05/WEEK_4_ACTION_PLAN.md`, and the repository itself at commit 30e5067 (14/11/2026).

---

## 1. Changes to the Software Development Plan (Part A)

### 1.1 Purpose and Method

The PA2 Software Development Plan closed with the explicit statement that it was *"an initial version prepared for review by the teaching assistants and will be revised in PA3-2026 based on their feedback"*. Part A of the PA3 report is that revision: **v1.1, dated 14/11/2026**.

The revision method combined four inputs:

1. **The teaching-assistant feedback received after the PA2 submission** — the most material item being the requirement to *submit* the Spec Kit artefacts rather than to describe their initialisation.
2. **The Sprint 3 execution plans** — `Ke_Hoach_Tuan_Sprint_3_EcoBite.md` for Week 1 and `WEEK_4_ACTION_PLAN.md` for Week 4 — which contain the real task decomposition, the checkpoint gates, the re-allocation and the Sprint 3 Definition of Done.
3. **A direct audit of the repository at 14/11/2026** — 93 commits, 13 ORM tables, 32 API routes, 198 automated tests, the Spec Kit workspace, the front-end workspace — used as the ground truth against which the plan's claims were checked.
4. **The PA3-2026 brief itself**, which imposes the submission-packaging rules and the `Changes.md` obligation that this document discharges.

Twelve changes were identified. They are listed individually in §1.5 and summarised in §1.1 of the report.

### 1.2 Addressing the PA2 Teaching-Assistant Feedback on Spec Kit

**The feedback.** In PA2, the team described the Spec Kit initialisation process in Part C of the report and attached a `git log` export, but the **Spec Kit artefacts themselves were not submitted as inspectable files** — neither the project constitution nor the generated specification, plan and task documents. The submission therefore evidenced the *toolchain* but not the *output* of the spec-driven workflow.

**The diagnosis.** Three root causes were identified, and each maps to a distinct corrective action:

| Root cause | Corrective action | Change ID |
| :--- | :--- | :--- |
| The constitution existed in the repository (`src/.specify/memory/constitution.md`, v1.1.0) but was treated as background material rather than as a **deliverable**, so it was never packaged. | The constitution is promoted to a **first-class, version-controlled deliverable** of the Software Development Plan, released with the code and attached to the submission package. | `CHG-A-01` |
| The plan described the Spec Kit **workflow** but never required the **artefacts** it produces (`spec.md`, `plan.md`, `tasks.md`) to be committed with the feature they describe. | The Deliverable Checklist and the Submission Packaging checklist now require the generated artefacts to be committed, versioned, and attached. | `CHG-A-01`, `CHG-A-02` |
| Nothing in the quality-gate model prevented the omission, because "the artefacts exist" was never a gate condition. | A new **Quality Gate 5 — Submission Readiness** was added, so the omission cannot recur silently. | `CHG-A-10` |

**What changed concretely, in the PA3 plan (§A.3.5 and §A.3.6):**

- **Configuration Management** now enumerates the Spec Kit artefact set with a path, a version rule and a submission rule for each:

  | Artefact | Path | Version rule | Submission rule |
  | :--- | :--- | :--- | :--- |
  | Constitution | `src/.specify/memory/constitution.md` | Semantic version inside the file (currently 1.1.0, ratified state and last amendment 31/10/2026) | **Must be attached to the PA submission** |
  | Process templates | `src/.specify/templates/*.md` (5 files) | Committed with Conventional Commits | Attached as part of the Spec Kit set |
  | Script runtime | `src/.specify/scripts/powershell/` (6 scripts) | Versioned with the repository | Reproducible from the package |
  | Workflow definition | `src/.specify/workflows/workflow-registry.json`, `workflow.yml` | Versioned (workflow `speckit`, version 1.0.1) | Attached as part of the Spec Kit set |
  | Integration manifests | `src/.specify/integrations/*.manifest.json` | sha256 file-hash manifests, regenerated on every integration change | Not required in the package |
  | **Generated feature artefacts** | `specs/001-rescue-discovery-order-qr/spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/api-contracts.md`, `checklists/requirements.md` | Produced by `/speckit-specify` → `/speckit.plan` → `/speckit.tasks`, implemented by `/speckit.implement` | **Must be attached to the PA submission** — this is the item the PA2 feedback raised |

- **A new §A.3.6 Submission Packaging checklist** with eleven numbered items: the Markdown sources, the exported PDFs, `Changes.md`, the constitution, the generated Spec Kit artefacts, the templates and workflow, the complete source code with `node_modules` / `.venv` / build artefacts removed, the Git log export, the Jira evidence figures, the video-demo link and the environment guide — packaged as `PA3-Group05.zip`.

- **A new Definition-of-Done item (item 5)**: *"If the feature was implemented through Spec Kit, its `spec.md`, `plan.md` and `tasks.md` are committed, consistent with the code, and attached to the submission package."*

**Status at PA3 submission.** Alongside `src/.specify/memory/constitution.md` (v1.1.0), the five templates, the six PowerShell scripts, and the workflow definitions, the team executed the Spec Kit workflow (`/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`) for the functional group in Section E, committed the generated `spec.md`, `plan.md`, and `tasks.md` artefacts into the repository, and packaged them in `PA3-Group05.zip`, closing risk **R8**.

### 1.3 Changes to the Schedule, Milestones and WBS

| # | What changed | Why |
| :--- | :--- | :--- |
| 1 | The Gantt chart was re-baselined: Sprint 1 → `done`, Sprint 2 → `done`, Sprint 3 → `done` with the **PA3 submission milestone on 14/11/2026**, Sprint 4 and Sprint 5 → *(Planned)*. | The PA2 chart showed Sprint 3–5 as future work with no internal structure. |
| 2 | The Sprint 3 objective was split into a **Week 1** objective (02/11 – 08/11) and a **Week 4** objective (09/11 – 14/11), each with its own exit criteria. | The two weekly plans are the actual execution record; the plan now mirrors them. |
| 3 | The three Week-1 technical checkpoints (04/11, 06/11, 08/11) became formal acceptance criteria with pass/fail evidence. | `Ke_Hoach_Tuan_Sprint_3_EcoBite.md` §Part 3 defines them as gates. |
| 4 | The list of **items carried over from Sprint 2** was added with their Sprint-3 closure status (JWT/RBAC — closed; KYC approval workflow — closed; base menu catalogue — delivered). | The PA2 Sprint Review closed with two items "In progress"; the new plan closes the loop. |
| 5 | WBS 3 was expanded from three bullets to **thirteen work packages**, covering the PostGIS radar, the menu/dish APIs, the KYC workflow, the order core transaction, the atomic inventory lock, the HMAC QR module, the order query surface, the front-end foundation, the seed pipeline, the AI schema and the PA3 documentation pack. | The PA2 WBS did not describe what the sprint actually contained. |
| 6 | The milestone acceptance criteria for PA3 were rewritten from two criteria to **six**, each with a named artefact as evidence. | The PA2 criteria were not falsifiable. |
| 7 | The release plan was updated: R0.2 renamed *"Internal alpha — Radar & Stock Safety"* and marked shipped on 14/11/2026 (including the backend QR service); R0.3 re-scoped to focus on the in-browser camera scanner UI (`html5-qrcode`) and VNPay integration. | The release names must match what shipped. |
| 8 | The effort estimate was **corrected** (see `CHG-A-06`). | The PA2 figure was internally inconsistent with the Sprint-2 board. |

### 1.4 Changes to the Process, Workflow, Configuration and Risk Management

| # | What changed | Why |
| :--- | :--- | :--- |
| 1 | A **Week-4 re-allocation** section was added to the resourcing matrix, with the reason for each move. | `WEEK_4_ACTION_PLAN.md` §1 re-assigned the team mid-sprint; a plan that does not record this misrepresents how the work was actually done. |
| 2 | A **capacity and load per member** table was added, with the committed and accepted story points. | The PA2 plan had no sprint-level commitment measure. |
| 3 | Two **training items** were added (concurrency engineering; HMAC token design) and the table now carries a status column. | Both skills were genuinely acquired during Sprint 3. |
| 4 | The **risk register was re-rated against evidence**: R2 (over-selling) and R4 (QR replay) moved to *Closed* with their proving tests; R1 and R3 moved to *Mitigated* with the residual risk stated; R1, R2, R3, R4, R5, R6 were re-ranked; and **R7, R8 and R9 were opened** from the Sprint-3 repository audit. | A risk register that is never updated is not a management artefact. |
| 5 | The **metrics table** was bound to named artefacts, and the three Week-1 technical gates were written as explicit exit tests. | `Ke_Hoach_Tuan_Sprint_3_EcoBite.md` §Part 3. |
| 6 | **Quality Gate 5 — Submission Readiness** was added to the four Constitutional gates. | Answers the PA2 feedback; prevents recurrence. |
| 7 | A **toolchain-drift clause** was added (§A.3.7) with a reproducible Python 3.11 environment recipe. | The local `.venv` resolves to CPython 3.13.9 and lacks `tzdata`, which breaks `import app.main`; the Constitution forbids reporting an unexecuted command as passed. |
| 8 | The **branch and commit evidence** of Sprint 3 was added to Configuration Management, with the seven branches used and the Conventional Commits convention cited with real examples. | The PA2 plan described the branching *policy* but not the *practice*. |

### 1.5 Comparison Table for Part A

| Change ID | Affected Section | PA2 Version (v1.0) | PA3 Revised Version (v1.1) | Source / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `CHG-A-01` | §4.3.4 Configuration Management; §A.3.5 | "The team uses a GitHub repository with a trimmed GitFlow branching strategy … every pull request requires at least 1 approval." The Spec Kit was mentioned only in §5 as a tool; the constitution was never named as a deliverable. | Configuration Management now lists the **complete Spec Kit artefact set** with a path, a version rule and a submission rule for each: `src/.specify/memory/constitution.md` (v1.1.0), the five process templates, the six PowerShell scripts, the workflow registry and `workflow.yml`, the sha256 integration manifests, and the **generated feature artefacts** (`spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/`, `checklists/`). Every artefact is version-controlled with the code and released under the same Git tag. | **TA feedback from PA2** — the constitution and the generated Spec Kit artefacts were not submitted directly, only described. |
| `CHG-A-02` | §2.3 Deliverables; new §A.3.6 Submission packaging | "The table below allocates the deliverables, technical documents, and source code to the five evaluation milestones." No packaging checklist existed. | A **submission-packaging checklist with 11 numbered items** was added: the Markdown sources, the exported PDFs, `Changes.md`, the constitution, the generated Spec Kit artefacts, the templates and workflow, the source code with `node_modules` / `.venv` / build artefacts removed, the Git log export, the Jira evidence figures, the video-demo link and the environment guide — packaged as `PA3-Group05.zip`. | **TA feedback from PA2** — the artefacts and the Git log must be *submitted*, not referenced. |
| `CHG-A-03` | §4.2.4 Project Schedule; §A.2.2 | The Gantt chart marked Sprint 1 and Sprint 2 as finished, Sprint 2 as `active`, and Sprint 3–5 as future bars. Sprint 3 had no internal week-level breakdown. | The chart is re-baselined: Sprint 1–2 `done`, Sprint 3 `done` with the **PA3 submission milestone on 14/11/2026**, Sprint 4–5 explicitly *(Planned)*. The three Week-1 technical checkpoints and the seven-day Week-4 execution matrix are now part of the plan. | `Ke_Hoach_Tuan_Sprint_3_EcoBite.md` §Part 3; `WEEK_4_ACTION_PLAN.md` §3. |
| `CHG-A-04` | §4.2.2 Iteration Objectives; §A.2.4 | Sprint 3 had one objective line: *"Deliver PostGIS geospatial capability and control concurrent inventory disputes."* | Sprint 3 is decomposed into a **Week 1 objective** (store API surface, PostGIS radar, discount engine, seed pipeline, front-end foundation) and a **Week 4 objective** (order transaction with atomic inventory, HMAC QR, order query surface, front-end campaign, PA3 package), each with its own exit criteria, plus the explicit status of the **Sprint-2 carry-over items**. | `Ke_Hoach_Tuan_Sprint_3_EcoBite.md`; `WEEK_4_ACTION_PLAN.md` §2. |
| `CHG-A-05` | §4.2.1 Work Breakdown Structure; §A.2.3 | WBS 3 contained three bullets: interactive Leaflet radar map, PostGIS spatial queries with a GIST index, database-level atomic inventory locking. | WBS 3 is expanded to **thirteen work packages** (3.1 … 3.13) covering the PostGIS radar, the KYC workflow, the menu/dish APIs, the order core transaction, the cancellation with atomic restoration, the dynamic HMAC QR, the order query surface, the front-end foundation, the seed pipeline, the Gemini schema, the AI service foundation and the PA3 documentation pack — each with an owner and a status. | `Ke_Hoach_Tuan_Sprint_3_EcoBite.md`; `WEEK_4_ACTION_PLAN.md`; Sprint-3 repository audit. |
| `CHG-A-06` | §4.1.2 Effort and Schedule Estimates; §A.3.3 | "approximately **85–100 story points** for the 10 core features … The team's average velocity is estimated at **18–20 story points per sprint**." | The estimate is **corrected**: the project is restated at **250–280 SP** total with a **55–65 SP/sprint** velocity band, and Sprint 3 is recorded with a **64 SP capacity** and a **61 SP commitment**, all 61 points accepted. The rationale is stated explicitly — the PA2 figure covered documentation only, while the Sprint-2 board already committed 32 SP, so 18–20 SP/sprint was not a credible baseline. | Sprint-3 measurement (Jira board and Git history) against the PA2 baseline. |
| `CHG-A-07` | §4.3.3 Risk Management; §A.3.4 | Six risks (R1–R6), all presented as open, each with a mitigation but no status column and no evidence. | The register is re-rated against evidence and gains a **status** and an **evidence** column: **R2 closed** (0 % over-selling proven by the 50-request benchmark) and **R4 closed** (atomic `is_used` redemption, 13 unit and 12 integration tests); **R1 and R3 mitigated** with the residual risk named; **R5 open** for Sprint 4; **R6 realised** and handled by re-planning. Three new risks are opened: **R7** — the front end cannot compile because `src/lib/api-client.ts` and `src/lib/utils.ts` are missing while 13 modules import them and `src/app/` contains no page; **R8** — Spec Kit artefacts missing from PA2 (closed in PA3 by generating and packaging `spec.md`, `plan.md`, and `tasks.md`); **R9** — `QRService.generate_order_qr_token` is never invoked by production code. The risk matrix is redrawn. | Sprint-3 repository audit; `WEEK_4_ACTION_PLAN.md`; **TA feedback from PA2** (R8). |
| `CHG-A-08` | §4.2.5 Project Resourcing; §A.3.1, §A.3.2 | A four-line RACI list and a training table without status. | The RACI is extended with the **Week-4 re-allocation that actually happened** (Tony → core backend + QR module; Phúc → order transaction + atomic lock; Thịnh → 100 % front-end campaign; Huy → PM + AI service + PA3 pack), each with the reason. A capacity and load-per-member table, a Sprint-3 velocity comparison and two new training items were added. | `WEEK_4_ACTION_PLAN.md` §1. |
| `CHG-A-09` | §4.3.2 Reporting and Measurement; §A.3.7 | Velocity, defect trend, coverage and pass rate were named as metrics with no artefact and no threshold for the sprint. | Every metric is bound to a **named artefact** (Jira board, burn-down, `pytest` output, `ruff`/`mypy` output, Git log export) and carries a target and a measured value, including the 61/61 SP delivery, the 198 tests, the 0 % over-selling rate and the 0 % replay rejection rate. | `Ke_Hoach_Tuan_Sprint_3_EcoBite.md` §Part 3. |
| `CHG-A-10` | §5.3 Quality Gates; new §A.3.5 | Four quality gates from the Constitution: AI Self-Verification, Git Pre-commit, Human Pull Request Review, CI/CD. | A **fifth gate — Submission Readiness** — was added: the sprint cannot be closed until the packaging checklist of §A.3.6 is green, which requires the constitution, the generated Spec Kit artefacts, the report sources and PDFs, `Changes.md`, the Git log export and the evidence figures to be present in the package. | **TA feedback from PA2**. |
| `CHG-A-11` | §4.2.3 Releases | Four releases: R0.1 architecture spike, R0.2 internal alpha (PA3), R0.3 staging beta (PA4), R1.0 production (PA5). | R0.2 is renamed **"Internal alpha — Radar & Stock Safety"** and is marked **shipped on 14/11/2026** with its acceptance evidence (radar engine, order core transaction, atomic inventory lock, order query surface, backend dynamic single-use QR service). R0.3 is re-scoped to focus on the in-browser camera scanner UI (`html5-qrcode`) and VNPay integration. | Sprint-3 outcome. |
| `CHG-A-12` | New §A.3.7 Environment and toolchain drift | The plan assumed Python 3.11 and a healthy local virtual environment; the toolchain was not mentioned outside the technology table. | A **toolchain-drift clause** was added: the on-disk `backend/.venv` resolves to CPython 3.13.9 and lacks `tzdata`, `asyncpg`, `psycopg2-binary`, `google-genai`, `torch` and `pre-commit`; the missing `tzdata` makes `ZoneInfo("Asia/Ho_Chi_Minh")` raise at import time and prevents `import app.main` on a Windows host. A reproducible Python 3.11 recipe and a pinned-CI-image remediation are attached. | Sprint-3 repository audit. |

---

## 2. Changes to the Vision Document (Part B)

### 2.1 Changes to the Functional Requirements

The PA2 Vision Document described the ten product features (`F-01` … `F-10`) as ten narrative paragraphs. This was the single largest traceability gap in the project: the PA3 brief requires the use-case model to *"cover all functional requirements documented in the vision document"*, which is not verifiable against prose.

**v1.1 decomposes the ten features into 63 numbered functional requirements** (`FR-01.1` … `FR-10.6`), each with an explicit **actor**, **input**, **output**, **business rules** and a **Sprint-3 implementation status**. The decomposition preserves the PA2 semantics exactly — no feature was dropped and no rule was weakened — while making the requirements testable and traceable.

| Feature group | PA2 v1.0 | PA3 v1.1 | Count |
| :--- | :--- | :--- | :--- |
| F-01 Authentication and Merchant Onboarding | One paragraph | `FR-01.1` … `FR-01.8` | 8 |
| F-02 Base Menu Catalog and Surplus Dish Management | One paragraph | `FR-02.1` … `FR-02.8` | 8 |
| F-03 Rule-Based Time-Shift Discounting Engine | One paragraph | `FR-03.1` … `FR-03.5` | 5 |
| F-04 Location-Based Search and PostGIS Radar Discovery | One paragraph | `FR-04.1` … `FR-04.6` | 6 |
| F-05 Inventory Anti-Overselling Lock and Order Management | One paragraph | `FR-05.1` … `FR-05.6` | 6 |
| F-06 Seamless Cashless Checkout (VNPay) | One paragraph | `FR-06.1` … `FR-06.5` | 5 |
| F-07 Dynamic HMAC-SHA256 QR Token and In-Store Web Scanner | One paragraph | `FR-07.1` … `FR-07.6` | 6 |
| F-08 Verified Reviews, Green Points and Impact Tracker | One paragraph | `FR-08.1` … `FR-08.6` | 6 |
| F-09 Batch Quick-Post Multimodal Assistant and 2-Tier Allergen Guard | One paragraph | `FR-09.1` … `FR-09.7` | 7 |
| F-10 Smart Food Recommendation and Natural-Language Semantic Search | One paragraph | `FR-10.1` … `FR-10.6` | 6 |
| | | **Total** | **63** |

**Two supporting changes were made at the same time.**

- **The needs table was bound to requirements.** Each of the six PA2 key needs now names the functional requirements and the non-functional targets that satisfy it, and a seventh need — *"Browsing without commitment"* — was added to cover the Guest user group.
- **The guest user group was created.** PA2 listed three user groups (consumers, store partners, administrators) and had no entry for an unauthenticated visitor, even though registration and sign-in are the entry point of the system. v1.1 adds **Guest / Unauthenticated User** as a first-class user group, which in turn forced the actor model of Section C to be redrawn with an `Authenticated User` super-actor.

### 2.2 Changes to the Non-Functional Requirements

The PA2 Vision Document carried 64 non-functional requirements grouped into nine families. They were sound but largely qualitative — *"the system must respond quickly"*, *"the interface must be responsive"* — and several had no verification method at all.

**v1.1 keeps all 64 requirements and their identifiers, and adds nine:**

| New ID | Requirement | Why it was added |
| :--- | :--- | :--- |
| `NFR-PER-08` | In-store pickup verification **< 2 s** from scan to confirmation | The PA2 report mentioned this target in prose but not in the NFR set, so it could not be tested. |
| `NFR-PER-09` | Radar query correctness: **100 %** of the seeded stores inside the clamped radius are returned in exact ascending distance order | A latency target without a correctness target is not testable. |
| `NFR-PER-10` | Order-code uniqueness: **0 duplicate** order codes, with up to 3 retries then HTTP 409 | Discovered as a real engineering concern during Sprint 3 (blocker B-04). |
| `NFR-PER-11` | End-to-end fulfilment latency: an order placed inside its pickup window is redeemable before the deadline in **100 %** of cases | Closes the gap between the order and the pickup in the requirement set. |
| `NFR-SEC-01` | Secret hygiene: **0** secrets in Git, enforced by the pre-commit hook | Previously implied by the Constitution but not a numbered, verifiable requirement. |
| `NFR-SEC-02` | **100 %** of signature comparisons use a constant-time comparison | Directly derived from the HMAC-SHA256 implementation of Sprint 3. |
| `NFR-SEC-03` | Token entropy: **128-bit** nonces from a cryptographic source | Directly derived from the QR nonce implementation of Sprint 3. |
| `NFR-OBS-01` | Observability: **100 %** of the order, stock and payment mutations emit a structured log line, with no secret or payment payload ever logged | Auditability was required for the transactions but not for the mutations. |
| `NFR-ACC-01` | Accessible forms: every input labelled, errors announced through `role="alert"`, **0** unlabelled interactive elements | The PA2 accessibility requirement covered contrast and keyboard navigation but not form semantics. |

**Every requirement was additionally given three new attributes:** a **quantified target**, a **verification method** (how it is checked), and a **proving artefact** where one exists. The **priority matrix** was restated as a full P1/P2/P3 table that also records the **measured Sprint-3 status** of each group, so the document shows the distance between the promise and the repository rather than only the promise.

### 2.3 Changes to the Alternatives, Competitors and User Environments

The PA2 analysis of the three alternatives — the status quo (Facebook/Zalo manual clearance), Yindii and Too Good To Go — was accurate and has been **retained**. The change is in its depth and its form:

- A **seven-criterion comparative matrix** was added: transparency of the offer, allergen handling, Vietnamese localisation, payment fit, posting workflow, pickup verification and anti-fraud, stock safety, and environmental gamification — with EcoBite's position in each cell.
- An explicit **positioning statement** was added for each alternative, so the comparison ends in a decision rather than in a list.
- The **User Environment** was expanded from three prose paragraphs into three structured artefacts: an **operational-context table** (when, what the actor is doing concurrently, the constraint it creates, and the EcoBite response), a **device / OS / browser matrix** with a fallback for every unavailable capability, and an **accessibility, language and comprehension** subsection covering the Vietnamese-first requirement, the ARIA semantics and the four facts that must be visible on a dish card without interaction.
- A **fallback path for every denied browser permission** was added (microphone, camera, geolocation). This is new and was prompted by the Sprint-3 implementation of the geolocation hook and the radar map.

### 2.4 Comparison Table for Part B

| Change ID | Affected Section | PA2 Version (v1.0) | PA3 Revised Version (v1.1) | Source / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `CHG-B-01` | §5 Product Features; §B.3.1 | Ten narrative feature paragraphs `F-01` … `F-10`, each a continuous prose description with no identifiers, no actors, no inputs/outputs and no business rules. | The ten features are **decomposed into 63 numbered functional requirements** (`FR-01.1` … `FR-10.6`), each with an explicit **actor**, **input**, **output**, **business rules** and a **Sprint-3 implementation status**. This makes the Vision Document the direct, one-to-one foundation of the Section C use-case model. | PA3-2026 brief — *"Use-case diagrams must cover all functional requirements documented in the vision document"*; PA2 narration was not traceable. |
| `CHG-B-02` | §3.4 Summary of Key Needs; §B.2.5 | Six key needs, each with a concern, a current solution and a proposed solution, but no link to any requirement or target. | Each need now names the **functional requirements** and the **non-functional targets** that satisfy it, closing the chain *need → requirement → use case → test*. A seventh need — *"Browsing without commitment"* — was added for the Guest user group. | PA3-2026 brief; internal traceability audit during the Sprint-3 specification work. |
| `CHG-B-03` | §3.5 Alternatives and Competition; §B.4 | Three competitors described in prose: the status quo, Yindii and Too Good To Go, each with an operating model, strengths and weaknesses. | The analysis is **retained** and extended with a **seven-criterion comparative matrix** covering transparency, allergen handling, Vietnamese localisation, payment fit, posting workflow, pickup verification, stock safety and environmental gamification, plus an explicit **positioning statement** per competitor and a closing positioning statement for EcoBite. | **TA feedback from PA2** — the competitive analysis had to be expanded; Sprint-3 implementation also revealed that the stock-safety and anti-fraud axes are EcoBite's strongest differentiators. |
| `CHG-B-04` | §3.3 User Environment; §B.4.5 | Three prose paragraphs on the store floor, the consumer context, the device platforms and the hardware integrations. | Expanded into three structured artefacts: an **operational-context table** (when / concurrent activity / constraint / EcoBite response) for the four user groups; a **device, OS, browser and network matrix** with a fallback for every unavailable capability; and an **accessibility, language and comprehension** subsection. New: a **fallback path for every denied browser permission** (microphone, camera, geolocation) and the four facts a dish card must show without interaction. | Sprint-3 implementation evidence (`useGeolocation`, `AuthGuard`, the UI kit); **TA feedback from PA2**. |
| `CHG-B-05` | §6 Non-Functional Requirements; §B.3.2 | 64 requirements in nine families (STD, HW, PLT, PER, QUA, ENV, CON, DEP, DOC), with mostly qualitative targets and no verification method; priority given only as a coarse table of code ranges. | All 64 are retained with their identifiers and are given a **quantified target**, a **verification method** and a **proving artefact**; two families that v1.0 only summarised in the priority table (`NFR-HW-01` … `NFR-HW-04` and `NFR-PLT-01` … `NFR-PLT-05`) are now stated in full. **Nine new requirements** are added (`NFR-PER-08` … `NFR-PER-11`, `NFR-SEC-01` … `NFR-SEC-03`, `NFR-OBS-01`, `NFR-ACC-01`), bringing the total to **73**. The priority matrix is restated as a full **P1/P2/P3 table with the measured Sprint-3 status** of every group. | PA3-2026 brief — *"Detail product functional and non-functional requirements"*; Sprint-3 measurements (198-test suite, the concurrency benchmark, the static-analysis runs). |
| `CHG-B-06` | §2.1 Problem Statement; §2.2 Product Position Statement; §B.2.1, §B.2.2 | The four-row Problem Statement and six-row Product Position Statement describe the *intent* only. | Both RUP tables are **retained in structure and updated with the evidenced state** of the platform after Sprint 3: 13 database tables in one Alembic migration, 32 API routes across 6 routers, 198 automated tests (131 unit + 59 integration), the PostGIS radar engine, the atomic inventory lock and the HMAC-SHA256 pickup QR. The Problem Statement also gains an explicit **Guest** impact line. | Sprint-3 repository audit; the RUP structures are a course requirement and were preserved. |
| `CHG-B-07` | §3.1 Stakeholder Summary; §3.2 User Summary; §B.2.3, §B.2.4 | Five stakeholder groups and **three** user groups. VNPay and Google Gemini appear only as *dependencies* in §4.2; Google OAuth appears only in a dependency list. | The **Guest / Unauthenticated User** is added as a first-class user group, and the three external systems — **VNPay Gateway, Google Gemini 2.5 Flash, Google OAuth 2.0** — are promoted from dependencies to **first-class external actors**. This is the change that forced the actor model of Section C to be redrawn with a `Guest`, an `Authenticated User` super-actor and three external actors. | Section C actor model; PA3-2026 brief — the use-case diagrams must include the actors and the relationships among them. |
| `CHG-B-08` | §5 Key User Workflows; §B.3.3 | Two sequence diagrams: the consumer rescue journey and the merchant voice quick-post journey, both written against the *plan*. | **Four sequence diagrams** are provided, each verified against the **running implementation**: the consumer rescue journey (extended with the atomic reservation and the QR redemption actually implemented), the store-partner end-of-shift quick-post journey (including the graceful-degradation branch), the atomic reservation and cancellation transaction (with the permission and deadline branches), and the administrative KYC review journey (with the decision branches). | PA3-2026 brief — the diagrams must *"accurately illustrate the core user workflows"*; Sprint-3 implementation. |

---

## 3. Impact Summary and Change-Control Record

### 3.1 Aggregate Impact

| Dimension | PA2 v1.0 | PA3 v1.1 | Delta |
| :--- | :--- | :--- | :--- |
| Number of changes recorded | — | **20** (12 in Part A, 8 in Part B) | +20 |
| Number of functional requirements | 0 numbered (10 narrative features) | **63** numbered requirements | +63 |
| Number of non-functional requirements | 64, mostly qualitative | **73**, all with a target and a verification method | +9 |
| Number of use cases modelled | 0 (no use-case model existed) | **14**, in 4 Mermaid diagrams, with an exhaustive traceability matrix | +14 |
| Sequence diagrams | 2 | 4 | +2 |
Risks tracked | 6, all open | **9**, of which 5 closed (R2, R4, R7, R8, R9), 2 mitigated (R1, R3), 1 realised & handled (R6), and 1 open for Sprint 4 (R5) | +3
| Quality gates | 4 | 5 | +1 |
| Submission-packaging checklist items | 0 | 11 | +11 |
| Sprint 3 story points committed / accepted | not stated | 61 / 61 | new baseline |
| Repository artefacts at the time of writing | — | 93 commits, 13 tables, 32 routes, 198 tests | — |

### 3.2 Traceability of Changes to Artefacts

| Change ID | Resulting artefact in `reportPA3.md` | Supporting artefact in the repository |
| :--- | :--- | :--- |
| `CHG-A-01` | §A.3.5 Configuration Management | `src/.specify/memory/constitution.md`, `src/.specify/templates/`, `src/.specify/workflows/` |
| `CHG-A-02` | §A.3.6 Deliverable checklists and submission packaging | `PA3-Group05/Changes.md`, `Git_log_commit.txt` |
| `CHG-A-03` | §A.2.2 Gantt chart, §A.2.1 Sprint 3 outcome | `Ke_Hoach_Tuan_Sprint_3_EcoBite.md`, `WEEK_4_ACTION_PLAN.md` |
| `CHG-A-04` | §A.2.4 Iteration objectives | Jira Sprint 3 board |
| `CHG-A-05` | §A.2.3 Work Breakdown Structure | `backend/app/`, `frontend/src/`, `docs/` |
| `CHG-A-06` | §A.3.3 Capacity and estimates | Jira board burn-down, Git history |
| `CHG-A-07` | §A.3.4 Risk register v1.1 | `backend/tests/integration/test_order_concurrency.py`, `backend/tests/unit/test_qr_service.py` |
| `CHG-A-08` | §A.3.1 RACI, §A.3.2 Week-4 re-allocation | `WEEK_4_ACTION_PLAN.md` §1 |
| `CHG-A-09` | §A.3.7 Monitoring and metrics | `pytest` output, `ruff`/`mypy` output |
| `CHG-A-10` | §A.3.5 Quality Gate 5 | `src/.specify/memory/constitution.md` (Quality Gates section) |
| `CHG-A-11` | §A.2.6 Release plan | Repository tags and branches |
| `CHG-A-12` | §A.3.7 Toolchain-drift clause | `backend/requirements.txt`, `backend/pyproject.toml` |
| `CHG-B-01` | §B.3.1 Functional requirements, §C.3 Traceability matrix | `backend/app/schemas/`, `backend/app/api/v1/endpoints/` |
| `CHG-B-02` | §B.2.5 Key needs | `backend/tests/` |
| `CHG-B-03` | §B.4.4 Comparative analysis | `docs/01_PRD_and_User_Stories.md` §5 |
| `CHG-B-04` | §B.4.5 User environment | `frontend/src/hooks/useGeolocation.ts`, `frontend/src/components/ui/` |
| `CHG-B-05` | §B.3.2 Non-functional requirements | 190-test suite, concurrency benchmark, quality-gate runs |
| `CHG-B-06` | §B.2.1 Problem Statement, §B.2.2 Product Position Statement | `backend/app/models/`, `backend/app/api/v1/router.py` |
| `CHG-B-07` | §B.2.3 Stakeholders, §B.2.4 Users, §C.1.2 Actors | `backend/app/models/user.py` (`UserRole`), `backend/app/core/security.py` |
| `CHG-B-08` | §B.3.3 Core user workflows | `backend/app/services/order_service.py`, `backend/app/services/qr_service.py` |

### 3.3 Change-Control Record

The changes were raised, discussed and accepted through the change-request workflow of §4.3.1 of the plan (a Jira issue, an impact assessment by the Product Owner and the relevant domain lead, and the consensus of at least three of the four members). The Sprint 3 changes were raised on the Jira board at the Sprint Planning of 01/11/2026 and re-verified at the Monday check-ins of 09/11/2026 and at the Sprint Review of 14/11/2026.

| Change ID | Raised by | Impact assessment | Accepted by | Date | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CHG-A-01`, `CHG-A-02`, `CHG-A-10` | Phùng Quốc Huy (PM) | High — affects the Configuration Management section, the deliverable catalogue and the quality-gate model | 4 of 4 | 02/11/2026 | **Implemented** |
| `CHG-A-03`, `CHG-A-04`, `CHG-A-05` | Phùng Quốc Huy (PM) | Medium — schedule and WBS sections | 4 of 4 | 02/11/2026 | **Implemented** |
| `CHG-A-06` | Đặng Trọng Phúc (Backend Lead) | Medium — the estimate baseline is corrected, which affects the plan and the future commitments | 4 of 4 | 09/11/2026 | **Implemented** |
| `CHG-A-07`, `CHG-A-12` | Đặng Trọng Phúc (Backend Lead) | High — the register changes, and the toolchain clause adds a CI obligation | 4 of 4 | 13/11/2026 | **Implemented** |
| `CHG-A-08` | Phùng Quốc Huy (PM) | Medium — resourcing matrix | 4 of 4 | 09/11/2026 | **Implemented** |
| `CHG-A-09`, `CHG-A-11` | Đàng Thế Tony (QA Lead) | Low | 3 of 4 (domain lead tie-break) | 13/11/2026 | **Implemented** |
| `CHG-B-01`, `CHG-B-02` | Đặng Trọng Phúc (Backend Lead) | High — the requirement set is the foundation of the Section C model | 4 of 4 | 05/11/2026 | **Implemented** |
| `CHG-B-03`, `CHG-B-04` | Võ Ngọc Thịnh (Frontend Lead) | Medium — the competitive and user-environment sections | 4 of 4 | 09/11/2026 | **Implemented** |
| `CHG-B-05` | Đàng Thế Tony (QA Lead) | High — every NFR gains a target and a verification method | 4 of 4 | 13/11/2026 | **Implemented** |
| `CHG-B-06` | Đặng Trọng Phúc (Backend Lead) | Low — the RUP table structure is preserved | 3 of 4 | 13/11/2026 | **Implemented** |
| `CHG-B-07` | Võ Ngọc Thịnh (Frontend Lead) | High — the actor model of Section C depends on it | 4 of 4 | 09/11/2026 | **Implemented** |
| `CHG-B-08` | Võ Ngọc Thịnh (Frontend Lead) | Medium — four diagrams to author and verify | 4 of 4 | 13/11/2026 | **Implemented** |

**Open change request carried into Sprint 4.** `CR-S4-01` — *"Close the front-end contract gap: create `src/lib/api-client.ts` and `src/lib/utils.ts`, build the `src/app` App Router route groups, align the six front-end service modules with the real backend routes, and configure Vitest with a `test` script so `frontend/__tests__/` becomes executable."* Raised by Võ Ngọc Thịnh on 08/11/2026 (blocker B-05), assessed by Đặng Trọng Phúc and Phùng Quốc Huy on 09/11/2026, accepted by 4 of 4 on 13/11/2026, and scheduled as the first entry of the Sprint 4 lesson list. It is tracked as risk **R7**.

**Change request closed for the PA3 submission.** `CR-PA3-02` — *"Generate and commit the Spec Kit artefacts (`spec.md`, `plan.md`, `tasks.md`) for the Rescue Discovery, Order & QR Pickup functional group (`specs/001-rescue-discovery-order-qr/`) and attach them to the PA3 package."* Raised by Phùng Quốc Huy on 13/11/2026 (blocker B-08, **TA feedback from PA2**), accepted by 4 of 4 on 13/11/2026, implemented as Configuration-Management item `CHG-A-01` and packaging item `CHG-A-02`, and verified in `PA3-Group05.zip` — closing risk **R8**.

---

## Appendix A. Document Revision History

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 14/11/2026 | 1.0 | Initial `Changes.md` for the PA3 submission. Establishes the tracking log on the basis of the TA feedback from PA2, the Sprint 3 weekly execution plans (`Ke_Hoach_Tuan_Sprint_3_EcoBite.md`, `WEEK_4_ACTION_PLAN.md` authored by Phùng Quốc Huy) and the Sprint-3 repository audit. Part A records 12 changes to the Software Development Plan; Part B records 8 changes to the Vision Document. | Đặng Trọng Phúc |
| 14/11/2026 | 1.1 | Cross-checked against `reportPA3.md` after the final editorial pass: the change identifiers referenced from Part A and Part B of the report were verified to match this file, the §3.2 traceability table was completed, and the change-control record was reconciled with the Sprint 3 Jira board. | Group 05 |

**Distribution.** This file accompanies `PA3-Group05/reportPA3.md` in the `PA3-Group05.zip` package. It is the second mandatory artefact of the PA3 submission alongside the report itself.