# Feature Specification: AI Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard

**Feature Branch**: `feat/ai_1_quick_post`

**Created**: 2026-11-28

**Status**: Draft

**Input**: User description: "AI Feature 1 — Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard allowing approved Store Partners to submit a short Vietnamese voice clip or free-text note at the end of a shift so the system extracts multiple surplus dishes, grounds them against the store's Base Menu Catalog, resolves relative pickup times using authoritative server time, attaches 2-tier EU FIC allergen warnings (Explicit vs Inferred), and prepares verified drafts ready for 1-tap batch publishing, together with an evaluation benchmark and research report."

## Summary *(mandatory)*

Busy restaurant and bakery staff often discard unsold end-of-shift meals because manually filling out individual surplus-listing forms—dish names, quantities, prices, pickup windows, and safety warnings—takes too long during closing rush. This feature serves **approved Store Partners** (with indirect safety protection for **Consumers** browsing published dishes) by allowing a partner to record a brief Vietnamese voice message or enter a free-text note listing multiple surplus dishes at once. The system automatically extracts structured surplus-dish drafts, grounds each dish against the store's Base Menu Catalog to inherit verified pricing and canonical identity, converts relative Vietnamese time expressions into exact pickup hours using authoritative server time, and surfaces transparent two-tier allergen warnings across the 14 EU FIC categories so the partner can review and publish the entire batch in one tap.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Text-Based Batch Quick-Post with Menu Grounding & 2-Tier Allergen Guard (Priority: P1)

As an approved Store Partner wrapping up a shift, I want to type a short Vietnamese note describing several surplus dishes, quantities, optional clearance prices, and relative pickup hours so that the system immediately produces structured dish drafts matched to my store's Base Menu Catalog with two-tier allergen warnings ready for review.

**Why this priority**: Text extraction exercises the complete core intelligence pipeline—batch parsing, Vietnamese slang/price interpretation, menu-catalog grounding, anti-hallucination verification, server-time conversion, and 2-tier allergen review—and delivers immediate standalone value even without microphone hardware.

**Independent Test**: Can be fully tested by signing in as an approved Store Partner with at least two active items in their Base Menu Catalog, submitting a free-text Vietnamese description containing multiple dishes, a relative pickup window (e.g., "từ giờ đến 3h chiều"), and both explicit and implicit allergens, and verifying that the returned drafts contain exact pickup times, verified menu links, inherited original prices, and distinct Explicit/Inferred allergen warnings.

**Acceptance Scenarios**:

1. **Given** an approved Store Partner whose Base Menu Catalog contains "Cơm sườn bì chả" (45,000 VND) and "Bún thịt nướng" (40,000 VND), **When** the partner submits *"Còn 5 cơm sườn chả, 3 bún thịt nướng có đậu phộng rang, xả từ giờ đến 3h chiều, bún bán 20 cành"* at authoritative server time `13:55`, **Then** the system returns a batch draft with pickup window `13:55:00` to `15:00:00` and two dish items matched to the store's canonical menu entries.
2. **Given** a matched dish where the partner did not state the original price, **When** extraction completes, **Then** the system automatically populates the item's original price from the store's matched Base Menu Catalog entry and leaves the override discount price unset so rule-based discounting applies downstream.
3. **Given** a matched dish where the partner explicitly states a fixed clearance price (e.g., *"bán 20 cành"* / *"20k"*), **When** extraction completes, **Then** the system captures `20000` as the explicit clearance price override.
4. **Given** a dish mentioning an ingredient directly (*"có đậu phộng rang"*) alongside traditional Vietnamese ingredients not spoken aloud (e.g., egg in *chả chưng*, fish sauce in *cơm tấm*), **When** extraction completes, **Then** the system preserves the dish (never silently hiding it from the partner), labels spoken allergens as `EXPLICIT`, and labels culinary-knowledge allergens as `INFERRED` with short Vietnamese explanations mapped to the 14 EU FIC allergen categories.
5. **Given** the extraction engine proposes a menu reference that does not belong to the authenticated partner's active catalog (including another store's menu item or a fabricated identifier), **When** post-validation runs, **Then** the system clears the invalid menu link and appends a clear missing-field warning so the partner must manually review or select the menu item before publishing.

---

### User Story 2 - Native Multimodal Vietnamese Voice Clip Quick-Post (Priority: P1)

As a busy kitchen staff member or Store Partner with wet or occupied hands at closing time, I want to upload or send a short Vietnamese voice recording listing leftover meals so that I do not have to type on a phone screen while still receiving the same accurate menu-grounded drafts and 2-tier allergen warnings.

**Why this priority**: Voice-first entry is the signature operational bottleneck solver of AI Feature 1, enabling sub-3-second shift closing workflows for Vietnamese street-food vendors and bakeries using natural regional dialects and slang.

**Independent Test**: Can be fully tested by signing in as an approved Store Partner, submitting a supported voice audio clip (`.m4a`, `.mp3`, `.wav`, or `.webm` within the allowed file-size limit) without accompanying text, and verifying that structured dish drafts are extracted directly from the audio with valid pickup times, menu matches, and allergen classifications.

**Acceptance Scenarios**:

1. **Given** an approved Store Partner uploads a valid Vietnamese voice recording in a supported audio format (`.m4a`, `.mp3`, `.wav`, or `.webm`) within the maximum file-size limit (10 MB), **When** the extraction completes, **Then** the system ingests the audio directly and returns the same structured batch draft format as text input, grounded in the store's Base Menu Catalog and authoritative server time.
2. **Given** a Store Partner submits both a voice clip and a short supplemental text note, **When** extraction runs, **Then** the system considers both inputs together without dropping information from either source.
3. **Given** a Store Partner uploads an unsupported file type (such as an image or executable) or an empty/oversized audio file exceeding 10 MB, **When** submission is validated, **Then** the system rejects the file immediately before invoking AI processing and returns a clear Vietnamese guidance message explaining the accepted formats and size limit.

---

### User Story 3 - Safe Degradation, Role Enforcement & 1-Tap Batch Publish Handoff (Priority: P2)

As a Store Partner and platform operator, I want strict role and store-approval enforcement, clear error handling when the AI service is unavailable or input is incomplete, and draft outputs that map cleanly to the existing batch-publishing workflow so that the platform remains secure, reliable, and immediately usable end-to-end.

**Why this priority**: Reliable failure boundaries, strict access control, and seamless handoff to batch dish publication guarantee that AI never blocks store operations, leaks access to unauthorized roles, or produces unpublishable drafts.

**Independent Test**: Can be tested independently by attempting access as a Consumer or unapproved Store Partner (expecting denial), submitting empty input (expecting validation rejection), simulating AI timeout or missing configuration (expecting graceful unavailable feedback without crashing), and taking a valid extracted draft through batch dish publication.

**Acceptance Scenarios**:

1. **Given** an unauthenticated visitor or an authenticated Consumer or Admin attempts to invoke Quick-Post extraction, **When** the request is checked, **Then** the system denies access immediately and does not invoke AI processing.
2. **Given** a Store Partner who has not yet onboarded a store or whose store food-safety verification is still pending or rejected, **When** the partner attempts to invoke Quick-Post extraction, **Then** the system rejects the request with a clear message instructing them to complete or await store approval first.
3. **Given** a Store Partner submits a request with neither a voice clip nor non-blank text, **When** input validation runs, **Then** the system rejects the submission with a clear message requesting either voice or text input.
4. **Given** the external AI service is unconfigured, unreachable, times out, or produces output that fails structural safety validation, **When** extraction runs, **Then** the system logs the operational cause without exposing secrets, avoids an unhandled server crash, and returns a graceful service-unavailable message advising the partner to retry or use manual entry.
5. **Given** an approved Store Partner receives valid menu-grounded drafts from Quick-Post, **When** the partner reviews the allergen warnings and submits the reviewed items to batch surplus-dish publishing, **Then** all reviewed items are created in a single transaction with inherited images, pricing rules, and preserved 2-tier allergen warnings.

---

### User Story 4 - Offline Benchmark & Quality Evaluation Suite (Priority: P3)

As an AI Lead preparing for Sprint 5 kickoff and system acceptance, I want a reproducible Golden Dataset of Vietnamese text and voice Quick-Post scenarios paired with an automated evaluation runner and research report so that extraction accuracy, menu grounding, allergen safety recall, and latency are objectively measured before production rollout.

**Why this priority**: Measurable offline evaluation against a fixed Vietnamese dataset proves baseline effectiveness, catches prompt regressions early, and documents trade-offs (prompting Vietnamese slang, inline audio vs uploaded files, large menu catalogs) for the team.

**Independent Test**: Can be tested independently by executing the evaluation script against the 15–20 sample Golden Dataset and confirming it produces a complete metric summary covering schema validity, field extraction accuracy, menu grounding accuracy, zero fabricated menu links, allergen recall, 2-tier source accuracy, and P50/P95 latency.

**Acceptance Scenarios**:

1. **Given** a Golden Dataset of 15–20 representative Vietnamese Quick-Post scenarios (covering single/multiple dishes, slang pricing, relative pickup times, explicit and implicit Vietnamese allergens, missing quantities, and out-of-menu dishes, including audio samples), **When** the evaluation runner executes against the extraction service, **Then** it computes and outputs all six baseline quality metrics alongside per-case diagnostics.
2. **Given** the benchmark execution completes, **When** the team reviews the accompanying research report, **Then** it documents prompt design for Vietnamese dialects, inline audio sizing trade-offs, large-menu pruning strategies, post-validation safeguards, and actual observed baseline scores against target thresholds.

---

### Edge Cases

- **Missing or ambiguous quantity** (e.g., *"còn mấy hộp bánh mì"* or *"vài phần cơm"*): System either estimates a conservative positive integer with an explicit warning in `missing_fields_warning` or flags the item for partner confirmation—never producing zero or negative quantities.
- **Dish not present in the store's Base Menu Catalog** (e.g., a special daily dish not yet registered in the catalog): System still extracts the dish name, quantity, and allergen warnings, sets `matched_menu_id` to empty (`null`), and adds a warning prompting the partner to link or add it to the catalog before batch publishing.
- **Store has an empty Base Menu Catalog**: Extraction still succeeds for dish names, quantities, pickup times, and 2-tier allergen warnings, with all `matched_menu_id` values left empty (`null`) and a warning noting no catalog items were available for matching.
- **Relative time wrapping or invalid pickup range**: If spoken phrasing yields a pickup end time earlier than or equal to the pickup start time, post-validation flags or rejects the invalid window instead of passing unpublishable times downstream.
- **Allergen transparency invariant**: Unlike consumer recommendation filtering, Quick-Post MUST NOT drop or hide dishes containing common allergens; every extracted dish remains visible to the Store Partner with all `EXPLICIT` and `INFERRED` warnings intact for human sign-off.
- **Multiple duplicate allergen detections on the same dish**: Post-validation deduplicates identical allergen entries on the same item, preferring `EXPLICIT` over `INFERRED` if both sources flag the same allergen.
- **Large store menu catalog (>50 active items)**: System limits or trims catalog context sent for grounding without dropping core fields needed for accurate matching, while post-validation still checks against the store's complete active menu set.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow only authenticated users with the `STORE_PARTNER` role whose store exists and has `APPROVED` food-safety (KYC) status to invoke Quick-Post surplus-dish extraction.
- **FR-002**: System MUST accept multimodal end-of-shift input consisting of a Vietnamese voice recording, a free-text Vietnamese description, or both, and MUST reject submissions containing neither valid audio nor non-blank text.
- **FR-003**: System MUST validate uploaded audio recordings before AI processing, accepting only supported audio formats (`.m4a`, `.mp3`, `.wav`, `.webm`) and rejecting empty files or files exceeding 10 MB with clear user-facing error messages.
- **FR-004**: System MUST retrieve the authenticated partner's active Base Menu Catalog items and supply relevant dish metadata (canonical identifier, dish name, standard original price, base ingredients, and base allergens) as grounding context during extraction.
- **FR-005**: System MUST resolve relative Vietnamese time expressions (e.g., *"từ giờ đến 3h chiều"*, *"trong 1 tiếng nữa"*) into exact `HH:MM:SS` pickup start and end times using authoritative server time in the `Asia/Ho_Chi_Minh` timezone rather than trusting an unverified client clock.
- **FR-006**: System MUST enforce structured output validation for every extracted batch, containing `pickup_start`, `pickup_end`, and at least one dish item with `dish_name`, positive integer `quantity`, optional `matched_menu_id`, optional `original_price`, optional `override_discounted_price`, `side_components`, `allergens`, `dietary_notes`, and `missing_fields_warning`.
- **FR-007**: System MUST classify every detected allergen strictly within the 14 EU FIC allergen categories and MUST tag each warning with its detection source (`EXPLICIT` when directly stated by the partner; `INFERRED` when inferred from Vietnamese culinary knowledge), risk level (`HIGH`, `MEDIUM`, or `LOW`), and a concise Vietnamese explanation.
- **FR-008**: System MUST perform deterministic server-side post-validation on every extracted item:
  - Verify that any non-null `matched_menu_id` belongs to the authenticated partner's own active Base Menu Catalog; if invalid or belonging to another store, clear `matched_menu_id` to `null` and append a missing-field warning.
  - Inherit the canonical `original_price` from the matched Base Menu Catalog item whenever the extracted `original_price` is absent.
  - Preserve `override_discounted_price` as `null` whenever the partner did not explicitly announce a clearance price, deferring pricing to deterministic time-based discount rules.
  - Deduplicate repeated allergens on the same item, keeping `EXPLICIT` precedence over `INFERRED`.
- **FR-009**: System MUST NOT remove or filter out extracted dishes based on consumer allergen preferences during Quick-Post; all extracted dishes MUST be returned to the Store Partner for explicit review and sign-off.
- **FR-010**: System MUST separate test/development AI credentials from paid demo AI credentials via environment-driven configuration so development and automated testing do not inadvertently consume paid demo quota, and MUST NEVER log or expose credentials.
- **FR-011**: System MUST handle missing AI credentials, network errors, request timeouts, quota errors, and unparseable/invalid AI outputs gracefully without crashing, returning an accurate service-unavailable response and logging structured diagnostic context.
- **FR-012**: System MUST produce extracted draft items whose identifiers, quantities, pickup times, override prices, allergen warnings, and dietary notes map directly into the existing 1-tap batch surplus-dish publishing flow without manual schema translation loss.
- **FR-013**: System MUST include a reproducible Golden Dataset (15–20 Vietnamese text and audio cases), an automated evaluation runner computing all six baseline metrics, and a technical research report documenting prompting, audio ingestion, menu pruning, and observed baseline results.

### Non-Functional Requirements *(mandatory when the feature touches money, health, or personal data)*

- **NFR-001 (Performance)**: End-to-end Quick-Post extraction (including inline audio ingestion for typical 10–30 second partner clips) MUST target P95 latency under 3.0 seconds under normal AI service responsiveness, with a bounded upstream timeout (default 15 seconds) so requests never hang indefinitely.
- **NFR-002 (Security & Access Control)**: Quick-Post extraction MUST be protected server-side by role-based access control restricted exclusively to `STORE_PARTNER` with server-verified JWT authentication and store KYC approval checks; AI keys and raw credentials MUST be loaded exclusively from environment configuration and NEVER logged, returned to clients, or committed to version control.
- **NFR-003 (Food Safety & Data Integrity)**: Fabricated or cross-store menu identifiers MUST have a 0% pass-through rate after server-side post-validation; inferred allergens MUST remain visibly distinguished from explicit partner declarations and MUST NOT be presented as a medically guaranteed safety certification; Quick-Post MUST NOT perform database mutations (read-only until the partner explicitly confirms batch publishing).
- **NFR-004 (Observability & Non-Blocking Execution)**: Request handling and external AI calls MUST execute asynchronously without blocking concurrent server requests; structured logs MUST record store identifier (never secrets or raw audio binaries), input mode (text/audio/both), item count, latency, and sanitized failure category for triage.

### Key Entities *(include if feature involves data)*

- **Partner Store**: An approved merchant storefront owned by an authenticated `STORE_PARTNER`; determines eligibility (approved food-safety verification) and owns the Base Menu Catalog used for grounding.
- **Base Menu Item**: A canonical dish record belonging to a Partner Store, holding verified name, standard original price, image, standard ingredients, and base allergens; read-only grounding reference during Quick-Post.
- **Quick-Post Extraction Batch**: A transient, structured draft result containing the resolved pickup window (`pickup_start`, `pickup_end`) and one or more extracted Surplus Dish Drafts; not persisted until the partner reviews and publishes.
- **Surplus Dish Draft**: An individual extracted leftover-dish entry containing normalized dish name, positive quantity, verified optional link to a Base Menu Item, original price (spoken or inherited), optional explicit clearance price override, side components, local dietary notes, two-tier allergen warnings, and missing-field warnings.
- **Two-Tier Allergen Warning**: A food-safety annotation bound to one of the 14 EU FIC allergen categories, carrying risk severity (`HIGH` / `MEDIUM` / `LOW`), provenance (`EXPLICIT` vs `INFERRED`), and a short Vietnamese rationale.
- **Evaluation Golden Case**: A curated test fixture pairing Vietnamese partner input (text and/or audio), mock store menu context, fixed reference server time, and expected ground-truth fields/allergens used to benchmark AI-1 quality offline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Extraction Speed)**: Store Partners receive structured, review-ready surplus dish drafts in under 3.0 seconds at the 95th percentile for typical end-of-shift Vietnamese voice or text notes.
- **SC-002 (Structural Reliability)**: At least 98% of valid partner submissions in the Golden Dataset produce fully schema-valid batch drafts on the first attempt without manual repair.
- **SC-003 (Field Accuracy)**: At least 90% normalized accuracy across core extracted fields (dish name, quantity, pickup start/end times, and price) on the 15–20 case Vietnamese Golden Dataset.
- **SC-004 (Menu Grounding & Zero Fabrication)**: At least 90% top-1 menu matching accuracy for dishes present in the store's catalog, with **0%** invalid or cross-store menu identifiers passing server-side post-validation.
- **SC-005 (Food-Safety Allergen Recall)**: At least 95% recall on true allergens (both spoken and implicit Vietnamese culinary allergens) and at least 85% accuracy distinguishing `EXPLICIT` vs `INFERRED` detection sources across the Golden Dataset.
- **SC-006 (End-to-End Task Completion)**: An approved Store Partner can go from submitting a multi-dish Vietnamese Quick-Post input to confirming published surplus listings in a single batch flow with zero unhandled server errors across all negative, security, and failure scenarios.

## Assumptions

- **Existing Core Platform Reuse**: User authentication, role enforcement (`STORE_PARTNER`), Store food-safety (KYC) onboarding, Base Menu Catalog management, and 1-tap batch surplus-dish publishing are already implemented and stable from earlier milestones.
- **Backend & Evaluation Scope for Week 6**: This specification covers the complete Backend AI-1 baseline, automated verification tests, Golden Dataset, evaluation runner, and technical research report; the Store Partner client-side voice recording interface and interactive Draft Cards editor are scheduled separately in Sprint 5 and will consume the contract defined by this feature.
- **Read-Only Draft Generation**: Quick-Post extraction intentionally does not modify persisted surplus listings; publishing surplus dishes remains strictly a human-in-the-loop action after the partner reviews the 2-tier allergen warnings and confirms batch publishing.
- **Primary Language & Timezone**: Partner speech and text inputs are primarily Vietnamese (including Southern/Northern regional variants and common price slang such as *"cành"*, *"chục"*, *"k"*), and all store shift schedules operate in the `Asia/Ho_Chi_Minh` (`UTC+7`) timezone.
- **Legacy Draft Cleanup**: Early prototype Quick-Post routes that erroneously required the `CONSUMER` role or applied consumer allergen filtering will be replaced by the canonical `STORE_PARTNER` Quick-Post workflow without breaking existing core regression tests.
