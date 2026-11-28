# Feature Specification: AI Frontend Experience Suite, AI Safety QA & Release 1.0 Go-Live

**Feature Branch**: `feat/pa5-ai-frontend-qa-golive`

**Created**: 2026-11-28

**Status**: Draft

**Input**: User description: "EcoBite Feature 007 (PA5 Sprint 5: EC5-04, EC5-05, EC5-06, EC5-07) — Deliver the Store Partner Voice Quick-Post and 2-Tier Allergen Draft Cards Editor, the Consumer Smart Recommendations Carousel, Conversational Semantic Search, and 14 EU FIC Allergen & Taste Preferences profile, the comprehensive AI Safety, Resilience, SLA Benchmark, and >=80% Coverage QA Suite, and full-system User Acceptance Testing, containerized Go-Live packaging, and Release 1.0 delivery."

## Summary *(mandatory)*

While EcoBite's backend AI services automate end-of-shift dish extraction and allergy-safe personalized meal discovery, neither Store Partners nor Consumers can benefit from those capabilities until they are exposed through intuitive, safety-transparent user interfaces and verified under strict food-safety, resilience, performance, and release-readiness gates. This feature completes **Release 1.0** across four coordinated deliverables:

1. **Store Partner Voice Quick-Post & 2-Tier Allergen Draft Cards Editor (`EC5-04`)**: Enables approved Store Partners to record a short Vietnamese voice clip (or type a brief shift-end note), inspect AI-extracted surplus dish drafts with color-coded explicit vs AI-inferred EU FIC allergen warnings, resolve unmatched catalog items or inline edits, and publish the entire batch in one tap—falling back seamlessly to manual dish entry if AI processing is temporarily unavailable.
2. **Consumer Smart Recommendations, Conversational Semantic Search & Allergen Profile (`EC5-05`)**: Gives Consumers a personalized Top 3 rescue carousel with urgent clearance callouts and concise natural-language justifications, a conversational Vietnamese semantic search bar with quick prompt chips integrated with the live discovery map and checkout flow, and a dedicated allergen & taste preferences profile covering all 14 EU FIC allergens.
3. **AI Safety, Resilience, SLA Benchmark & Coverage QA Suite (`EC5-06`)**: Verifies a strict **0.0% allergen leakage invariant** across all consumer recommendation and semantic search paths, confirms zero unhandled server crashes under AI outages or malformed outputs, validates end-to-end latency targets, tests all new interactive user flows, and enforces at least **80% automated test coverage** across the platform.
4. **Full-System UAT, Containerized Go-Live Packaging & Release 1.0 Acceptance (`EC5-07`)**: Packages all platform services into a reproducible one-command deployment stack, completes end-to-end User Acceptance Testing across all 8 Core Features and 2 AI Features, and delivers the final PA5 acceptance report, Release `1.0` tag, and Go-Live demonstration video ahead of the internal deadline (`2026-12-11`) and official submission (`2026-12-12`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Store Partner Voice Quick-Post & 2-Tier Allergen Draft Cards Editor (Priority: P1)

As an approved Store Partner wrapping up a busy shift, I want to record a short Vietnamese voice message (or type a quick text note) directly from my surplus-dish publishing screen, review each AI-extracted draft card with clearly color-coded explicit and AI-inferred allergen warnings, adjust quantities, prices, or catalog links if needed, and publish all dishes in one tap so that end-of-shift surplus posting takes seconds without risking hidden allergens.

**Why this priority**: Voice-first batch publishing with human-in-the-loop 2-tier allergen review is the merchant-facing centerpiece of EcoBite's AI suite (`EC5-04`), eliminating closing-shift friction while preserving strict food-safety accountability.

**Independent Test**: Can be fully tested by signing in as an approved Store Partner with active Base Menu Catalog items, recording or submitting a Vietnamese multi-dish clip/note, verifying that interactive Draft Cards render with distinct Red (`EXPLICIT`) and Amber (`INFERRED`) allergen badges plus tooltips and disclaimers, linking any unmatched item via the catalog dropdown, editing a quantity or override price inline, and clicking 1-Tap Batch Publish to confirm all dishes appear immediately in the active surplus list.

**Acceptance Scenarios**:

1. **Given** an approved Store Partner opens the surplus-dish publishing screen on a browser with microphone permission granted, **When** the partner starts recording a Vietnamese voice clip, stops within the duration and 10 MB file-size limit, and submits it for extraction, **Then** the interface shows a clear recording indicator and processing state, extracts the batch drafts, and displays the shared pickup window alongside one editable Draft Card per extracted dish.
2. **Given** the partner's device lacks a microphone, microphone permission is denied, or the partner prefers typing, **When** the partner encounters a microphone error or selects text mode, **Then** the interface displays an actionable Vietnamese permission/fallback message and lets the partner enter a free-text Vietnamese description to trigger the exact same extraction and Draft Cards flow.
3. **Given** an extracted Draft Card contains both partner-declared (`EXPLICIT`) and AI-reasoned (`INFERRED`) allergens across the 14 EU FIC categories, **When** the card renders, **Then** `EXPLICIT` allergens display as **Red** badges, `INFERRED` allergens display as **Amber/Yellow** badges, hovering or tapping any badge reveals its concise Vietnamese rationale, and inferred warnings display a clear disclaimer stating they are AI-inferred cues requiring partner verification rather than medical certification.
4. **Given** an extracted Draft Card has no verified catalog match (`matched_menu_id` is empty) or carries `missing_fields_warning` messages, **When** the partner reviews the Draft Cards, **Then** the card prominently displays the warning banners and a Base Menu Catalog dropdown selector; 1-Tap Batch Publish remains blocked with a clear guidance prompt until every retained card is matched to an active catalog item (or removed by the partner).
5. **Given** all retained Draft Cards have valid catalog links, positive quantities, and a valid pickup window (`pickup_end > pickup_start`), **When** the partner adjusts any quantity, optional clearance price override, or allergen badge and clicks 1-Tap Batch Publish, **Then** all reviewed dishes are published together in a single transaction, a confirmation notice appears, and the active surplus list refreshes immediately.
6. **Given** the AI extraction service returns a temporary service-unavailable error (`503`), **When** the submission fails, **Then** the interface displays a clear Vietnamese notice without crashing, preserves any typed note, and provides a one-click transition to the existing manual surplus-dish publishing form.

---

### User Story 2 - Consumer Smart Recommendations Carousel, Conversational Semantic Search & Allergen Profile (Priority: P1)

As a Consumer looking for affordable, safe nearby surplus meals, I want to maintain my 14 EU FIC allergen exclusions, dietary lifestyle, favorite categories, and meal budget in a dedicated preferences page, view a Top 3 personalized recommendation carousel with urgent clearance badges and concise AI justifications on the discovery home page, and search using natural Vietnamese phrases integrated seamlessly with the discovery map and checkout flow so that I find safe meals I love in seconds.

**Why this priority**: Personalized discovery, conversational Vietnamese search, and consumer-controlled allergen profiles form the consumer-facing centerpiece of EcoBite's AI suite (`EC5-05`) and directly protect consumers with food allergies.

**Independent Test**: Can be fully tested by signing in as a Consumer, navigating from the main navigation bar to the Allergen & Taste Preferences page, saving allergen exclusions (e.g., Peanuts and Crustaceans), dietary lifestyle, preferred categories, and maximum budget, returning to the discovery home page to verify the Top 3 Smart Recommendation Carousel displays safe urgent-deal cards with 20–30 word AI justifications, running a Vietnamese conversational semantic query via prompt chip or free text, verifying the dish list and Radar map synchronize to the matching results, and opening the checkout modal directly from either a recommendation card or a semantic search result.

**Acceptance Scenarios**:

1. **Given** an authenticated Consumer opens the Allergen & Taste Preferences page from the navigation bar, **When** the page loads, **Then** it displays all **14 EU FIC allergens** with clear bilingual English–Vietnamese labels, dietary lifestyle options (`NONE`, `VEGAN`, `VEGETARIAN`), favorite food category toggles, a non-negative VND maximum budget field, and a safety notice explaining that selected allergens are strictly excluded at the database level.
2. **Given** the Consumer updates their excluded allergens, dietary lifestyle, preferred categories, or maximum budget and saves, **When** persistence succeeds, **Then** a confirmation notice appears, reloading the page retains the saved profile, and returning to the discovery home page immediately refreshes personalized recommendations and semantic search results against the updated safety profile.
3. **Given** an authenticated Consumer visits the discovery home page with location coordinates available, **When** personalized recommendations load, **Then** a **Top 3 Smart Recommendation Carousel** renders above the main discovery feed showing each dish's name, store name, distance, discount badge (highlighting urgent `-70%` final-rush deals), remaining quantity, concise 20–30 word AI justification callout, and a direct "Rescue Now" button that opens the checkout modal.
4. **Given** any visitor (authenticated Consumer or anonymous guest) uses the **Conversational Semantic Search Bar** on the discovery home page by typing a Vietnamese query or tapping a quick prompt chip (such as *"Món nước nóng dưới 30k gần đây"* or *"Đồ chay không đậu phộng"*), **When** the search executes, **Then** the interface shows a clear loading indicator, displays the returned matching dishes synchronized with the interactive discovery map pins, allows clearing the search back to standard Radar browsing, and lets the user initiate rescue checkout directly on any result.
5. **Given** the AI personalization or semantic search layer is slow or returns a fallback state, or no dishes match the user's strict allergen and query filters, **When** the response completes, **Then** the user still sees safe, accurate dish cards (with deterministic fallback summary text when AI copy is unavailable) or an empathetic empty-state message with quick actions to broaden filters or clear the search—never an unhandled screen error or unsafe allergen suggestion.

---

### User Story 3 - AI Safety Verification, Resilience, SLA Benchmarking & >=80% Coverage QA Suite (Priority: P1)

As a QA Lead safeguarding consumer health and production reliability, I want a documented AI test plan backed by automated integration, resilience, SLA benchmark, and frontend component test suites proving 0.0% allergen leakage, zero unhandled crashes under AI faults, compliant sub-3-second latency targets, and at least 80% project-wide test coverage so that Release 1.0 meets every safety and quality gate before launch.

**Why this priority**: Medical allergen safety (0.0% leakage) and graceful degradation under external AI failures are non-negotiable release blockers (`EC5-06`) mandated by EcoBite's safety principles and Definition of Done.

**Independent Test**: Can be fully tested by reviewing the published AI Test Plan and running the automated allergen-invariant integration suite, AI resilience tests, SLA timing benchmarks, frontend component tests, and full coverage reports—verifying every safety assertion passes with 0% leakage, zero `500` responses across fault scenarios, SLA targets satisfied, and overall coverage `>= 80%`.

**Acceptance Scenarios**:

1. **Given** the Allergen Hard Invariant test suite runs across diverse Consumer profiles (single allergen, multi-allergen, accented and unaccented Vietnamese labels, bilingual EU FIC labels, explicit and inferred dish allergens), **When** both Personalized Recommendations and Conversational Semantic Search execute—including adversarial queries explicitly requesting an excluded allergen, **Then** **0.0%** of returned dishes contain any excluded allergen.
2. **Given** fault-injection tests simulate missing AI credentials, upstream request timeouts, rate-limit errors, network failures, and malformed structured outputs, **When** Quick-Post, Personalized Recommendations, and Conversational Semantic Search are invoked, **Then** the platform produces **zero unhandled `500` errors**, returning clean service-unavailable responses (`503`) for Quick-Post and safe, allergen-filtered deterministic fallback results for Recommendations and Semantic Search.
3. **Given** the SLA benchmark suite measures end-to-end processing times, **When** Quick-Post and Personalized Recommendation pipelines run under standard test/staging profiles, **Then** Quick-Post satisfies the `< 3.0s` P95 target and Personalized Recommendations satisfy `< 2.5s` P95 (with deterministic fallback completing in `< 300ms`).
4. **Given** automated frontend component tests run for the Voice Quick-Post & Draft Cards Editor, Smart Recommendations Carousel & Semantic Search Bar, and Allergen Preferences page alongside the complete backend unit, integration, and property test suites, **When** coverage reports are generated, **Then** all tests pass cleanly and overall automated test coverage meets or exceeds **80%**.

---

### User Story 4 - Full-System UAT, Containerized Go-Live Packaging & Release 1.0 Delivery (Priority: P2)

As the EcoBite delivery team preparing for final project acceptance, I want the complete multi-service platform packaged for reproducible containerized startup, validated end-to-end across all 8 Core Features and 2 AI Features via structured User Acceptance Testing, and accompanied by the final PA5 report, clean Release `1.0` tag, and Go-Live demonstration video so that stakeholders can launch, verify, and evaluate the finished product reliably.

**Why this priority**: Reproducible deployment packaging, whole-system E2E UAT evidence, and complete acceptance artifacts (`EC5-07`) convert feature code into a shippable Release `1.0` product on schedule for `2026-12-11` / `2026-12-12`.

**Independent Test**: Can be fully tested by starting the entire 4-service stack from a clean environment using the documented startup commands, executing the scripted E2E UAT checklist covering merchant KYC through voice Quick-Post, consumer allergen protection, smart recommendations, atomic ordering, cashless payment, dynamic QR pickup, verified reviews, and green points redemption, verifying all 4 Quality Gates exit clean, and confirming the final PA5 report, release tag, and demo video are complete.

**Acceptance Scenarios**:

1. **Given** a clean workstation with container runtime installed and environment variables configured from the repository templates (without committing secrets), **When** an operator launches the full stack, **Then** the geospatial database, cache store, backend service, and web application all boot to healthy status, database migrations and demo seed data initialize cleanly, and the web application communicates with the backend without manual patching.
2. **Given** the full containerized stack is running with seeded data, **When** the team executes the complete UAT script covering all 8 Core Features and both AI Features across `ADMIN`, `STORE_PARTNER`, and `CONSUMER` accounts, **Then** every UAT scenario passes with recorded evidence and zero critical or high-severity defects remain open.
3. **Given** all code, tests, UAT records, and static/security checks are complete prior to the `2026-12-11` (`23:59`) internal deadline, **When** the team compiles the final acceptance package, **Then** the PA5 report (Markdown and PDF), Release `v1.0.0` tag, and Final Go-Live Demo Video are verified and ready for official `2026-12-12` submission.

---

### Edge Cases

- **Microphone denied, unsupported, or interrupted mid-recording**: Browser denies microphone access, lacks built-in audio recording support, or hardware disconnects mid-clip; the UI catches the error gracefully, stops active media tracks to release the microphone indicator, informs the partner in clear Vietnamese, and opens the text-input fallback immediately.
- **Audio clip exceeds size or duration limits**: Partner records past the 60-second safety cap or selects an audio file exceeding 10 MB or an unsupported format; the client automatically stops recording at the cap or blocks upload pre-flight with Vietnamese guidance before making a doomed network request.
- **Unmatched menu item or deleted catalog item during Draft Card editing**: AI returns `matched_menu_id: null` (out-of-catalog dish) or a store has zero active catalog items; Draft Cards remain inspectable, display a clear call-to-action to pick a catalog item or add one to the Base Menu Catalog, and prevent invalid batch submission until resolved.
- **Partner edits Draft Cards to remove all items or enter invalid pickup times**: Removing the last Draft Card exits cleanly to the Quick-Post prompt; entering `pickup_end <= pickup_start` or quantity `<= 0` triggers inline validation before sending a batch publish request.
- **Anonymous visitor on `/` vs authenticated `CONSUMER`**: Anonymous visitors can use the Conversational Semantic Search Bar and browse public nearby Radar dishes without being forced to log in, while the Personalized Top 3 Carousel displays a gentle sign-in prompt (or stays cleanly hidden with a call-to-action to personalize and configure allergies) instead of firing failing `401` loops.
- **Non-consumer role navigating to `/profile/preferences`**: Store Partners or Admins visiting `/profile/preferences` are redirected cleanly by role-aware route protection rather than shown broken consumer preference forms.
- **Consumer excludes all 14 EU FIC allergens**: Database hard filter accurately excludes every dish containing any allergen; if zero dishes remain, the carousel and search show a helpful empty-state message explaining that active allergy filters hid matching meals, without ever relaxing the safety filter.
- **Semantic search returns dishes outside the current map viewport or with 0 remaining quantity**: Map smoothly adjusts or highlights returned pins, sold-out dishes never appear as orderable, and clearing semantic search cleanly restores the previous Radar radius and category filters.
- **Stale recommendation cache after preference update**: Saving new allergen exclusions on `/profile/preferences` immediately invalidates cached recommendation and search queries so navigating back to `/` never flashes previously cached unsafe dishes.
- **Container startup race condition**: Backend waits until the geospatial database and cache health checks report healthy before accepting requests, preventing transient boot failures during fresh UAT runs.

## Requirements *(mandatory)*

### Functional Requirements

#### Store Partner Voice Quick-Post & Draft Cards Editor (`EC5-04`)

- **FR-001**: System MUST provide an interactive Voice & Text Quick-Post panel on the Store Partner surplus-dish management screen, accessible exclusively to authenticated `STORE_PARTNER` accounts whose store KYC status is `APPROVED`.
- **FR-002**: System MUST support browser-based audio recording with start/stop controls, live elapsed timer, automatic duration ceiling (60 seconds), client-side file-size enforcement (`<= 10 MB`), automatic microphone-track cleanup on stop/unmount, and an explicit text-input fallback mode.
- **FR-003**: System MUST handle microphone permission denials, missing audio hardware, and unsupported recording capabilities gracefully with clear Vietnamese guidance and immediate fallback to Vietnamese text input.
- **FR-004**: System MUST submit recorded audio and/or Vietnamese text to Quick-Post extraction and render an editable **Draft Cards Editor** showing the shared pickup window (`pickup_start`–`pickup_end`) and one card per extracted dish.
- **FR-005**: System MUST visually distinguish 2-tier EU FIC allergen warnings on every Draft Card using **Red** badges for `EXPLICIT` (partner-declared) allergens and **Amber/Yellow** badges for `INFERRED` (AI-reasoned) allergens, including each badge's concise Vietnamese rationale tooltip/detail and an explicit non-medical-certification verification disclaimer for inferred warnings.
- **FR-006**: System MUST allow the Store Partner to edit each Draft Card before publishing: select or change the linked Base Menu Catalog item via dropdown (required whenever `matched_menu_id` is empty), adjust positive quantity, set or clear an optional fixed clearance price override (leaving blank to apply deterministic time-based discounts), review or add/remove allergen warnings and dietary notes, remove unwanted draft cards, and inspect any `missing_fields_warning` banners.
- **FR-007**: System MUST block 1-Tap Batch Publish while any retained Draft Card lacks a valid `matched_menu_id`, has non-positive quantity, or has an invalid pickup window (`pickup_end <= pickup_start`), displaying clear inline validation guidance.
- **FR-008**: System MUST submit all confirmed Draft Cards via a single atomic 1-Tap Batch Publish action, display a success summary upon creation, clear the draft queue, and refresh the store's active surplus listings immediately.
- **FR-009**: System MUST handle AI service unavailability (`503`), network timeouts, and validation errors (`413`, `415`, `422`) gracefully without crashing or discarding user context, offering a one-click switch to the existing manual surplus-dish form.

#### Consumer Smart Recommendations, Semantic Search & Allergen Profile (`EC5-05`)

- **FR-010**: System MUST provide a dedicated **Allergen & Taste Preferences** screen accessible to authenticated `CONSUMER` users from the main navigation bar (and mobile bottom navigation) allowing selection of any subset of all **14 EU FIC allergens** with bilingual English–Vietnamese labels, dietary lifestyle (`NONE`, `VEGAN`, `VEGETARIAN`), favorite food categories, and maximum per-meal budget (`>= 0` VND).
- **FR-011**: System MUST load existing Consumer preferences on entry, persist updates atomically on save with clear feedback, validate non-negative budget values, and immediately invalidate cached recommendation and search views upon saving so updated allergy exclusions take effect instantly.
- **FR-012**: System MUST display a **Smart Recommendation Top 3 Carousel** on the Consumer discovery home page for authenticated Consumers, showing distance, original vs current rescue price, discount percentage, urgent final-rush clearance badges (`-70%` / `is_urgent_deal`), remaining portions, concise 20–30 word AI justification copy (with deterministic fallback copy when AI generation degrades), and a direct rescue action opening the order checkout modal.
- **FR-013**: System MUST provide a **Conversational Semantic Search Bar** on the discovery home page with quick Vietnamese prompt chips (including budget, cuisine, warmth, and allergy-aware examples), clear loading and active-query states, a reset/clear control returning to standard Radar discovery, and seamless synchronization with the displayed dish list, interactive discovery map pins, and order checkout modal.
- **FR-014**: System MUST maintain strict dish-level transparency across recommendation cards, semantic search results, and Radar listings (removing any "mystery bag" copy and displaying verified dish identity, store details, pricing, pickup urgency, and allergen cues).

#### AI Safety, Resilience, SLA & Coverage QA Suite (`EC5-06`)

- **FR-015**: System MUST include a formal AI Test Plan documenting the allergen safety test matrix, fault-injection resilience scenarios, SLA latency methodology, frontend component test scope, and coverage targets.
- **FR-016**: System MUST provide an automated **Allergen Hard Invariant** integration test suite proving **0.0% allergen leakage** across accented/unaccented Vietnamese inputs, canonical bilingual EU FIC names, single-allergen and multi-allergen exclusions, and adversarial semantic search prompts across both Personalized Recommendations and Conversational Semantic Search.
- **FR-017**: System MUST provide automated resilience and graceful-degradation tests covering missing AI credentials, upstream timeouts, quota/rate-limit errors, network outages, and invalid AI schemas across both AI Features, proving **zero unhandled `500` server errors**.
- **FR-018**: System MUST provide automated SLA latency verification benchmarks confirming Quick-Post extraction meets `< 3.0s` (P95) and Personalized Recommendation meets `< 2.5s` (P95, fallback `< 300ms`).
- **FR-019**: System MUST provide automated frontend component tests covering the Voice Quick-Post & 2-Tier Allergen Draft Cards Editor, Smart Recommendations Carousel & Conversational Semantic Search Bar, and the 14 EU FIC Allergen Preferences screen.
- **FR-020**: System MUST achieve and report at least **80% automated test coverage** across the project's test suites alongside passing linting, formatting, static type-checking, build, and pre-commit checks.

#### Full-System UAT, Containerized Packaging & Release 1.0 Go-Live (`EC5-07`)

- **FR-021**: System MUST package all four runtime components (geospatial database, cache store, backend service, and web client) into a single reproducible container orchestration configuration with service healthchecks, environment template documentation, and zero hardcoded or committed secrets.
- **FR-022**: System MUST execute and document full-system User Acceptance Testing on the running containerized stack verifying all 8 Core Features and 2 AI Features end-to-end across `ADMIN`, `STORE_PARTNER`, and `CONSUMER` workflows.
- **FR-023**: System MUST deliver the final PA5 acceptance report (Markdown and PDF), clean `v1.0.0` release tag verified against all 4 Quality Gates, and Final Go-Live Demo Video prior to the internal deadline (`2026-12-11`) for official Moodle submission (`2026-12-12`).

### Non-Functional Requirements *(mandatory when the feature touches money, health, or personal data)*

- **NFR-001 (Food Safety & Allergen Hard Invariant)**: Consumer allergen exclusion MUST remain a **0.0% leakage** hard invariant enforced at the database query layer before AI justification or presentation; frontend state MUST immediately invalidate cached recommendations upon preference updates and MUST clearly separate `EXPLICIT` (Red) vs `INFERRED` (Amber) allergen cues with non-medical-certification disclaimers.
- **NFR-002 (Performance & Responsiveness)**: Quick-Post end-to-end latency MUST target P95 `< 3.0s` (client timeout ceiling `20s` so backend `15s` timeout cleanly returns `503` without premature client aborts); Personalized Recommendations MUST target P95 `< 2.5s` (`< 300ms` on deterministic fallback); client UI MUST remain responsive with non-blocking loading skeletons across desktop and mobile viewports (`>= 360px`).
- **NFR-003 (Security, Privacy & Role Isolation)**: Partner Quick-Post UI and API MUST remain restricted to KYC-approved `STORE_PARTNER` users; Consumer preference management and personalized recommendations MUST be restricted to authenticated `CONSUMER` sessions; browser microphone streams MUST never be recorded without explicit user action and MUST be released immediately upon stop or navigation; zero API keys, tokens, or `.env` files may be committed or exposed to client bundles.
- **NFR-004 (Reliability & Graceful Degradation)**: Any external AI outage, timeout, quota exhaustion, or schema error MUST result in zero unhandled `500` server errors and zero broken white-screen frontend crashes; partners always retain full access to manual dish publishing, and consumers always retain full access to safe Radar discovery and deterministic recommendation fallbacks.
- **NFR-005 (Accessibility & Usability)**: Color-coded allergen badges MUST pair distinct colors (Red vs Amber) with explicit text labels (`Chủ quán báo` / `AI suy luận`) and icons so color-vision-deficient users distinguish tiers accurately; interactive controls MUST support keyboard focus and clear ARIA labels.
- **NFR-006 (Maintainability & Verifiable Quality)**: Every code change MUST pass all 4 EcoBite Quality Gates (local lint/format/type-check/tests/build, pre-commit secret & 5 MB file-size hooks, peer PR review per Sprint 5 reviewer matrix, and clean CI/container verification with `>= 80%` test coverage).

### Key Entities *(include if feature involves data)*

- **Quick-Post Draft Session (Client Transient State)**: Holds active recording status, optional captured audio blob/metadata, fallback text note, shared editable pickup window (`pickup_start`, `pickup_end`), list of editable Draft Cards, per-card validation errors, and publishing progress until confirmed via 1-Tap Batch Publish or discarded.
- **Editable Surplus Dish Draft Card**: Client-side editable projection of an extracted surplus dish carrying `matched_menu_id` (nullable until matched), `dish_name`, `quantity`, inherited `original_price`, optional `override_discounted_price`, `side_components`, list of 2-tier EU FIC allergen warnings (`EXPLICIT` vs `INFERRED`), `dietary_notes`, and `missing_fields_warning`.
- **Consumer Allergen & Taste Profile (`UserPreference`)**: Persistent 1-to-1 Consumer record storing canonical `excluded_allergens` (subset of the 14 EU FIC allergens), `dietary_preference` (`NONE` / `VEGAN` / `VEGETARIAN`), `preferred_categories`, and optional `max_budget` (VND).
- **Personalized Recommendation Card**: Ranked, allergen-safe surplus dish suggestion containing dish & store identifiers, distance in meters, original and current rescue prices, discount percentage, `is_urgent_deal` flag, remaining portions, and a 20–30 word `ai_justification` (or deterministic fallback text).
- **Semantic Search Result Set**: Consumer natural-language query response containing the interpreted structured intent (budget, categories, dietary/allergen constraints, keywords), allergen-safe matching dishes with coordinates for map synchronization, and fallback/empty-state metadata.
- **AI Safety & Release Verification Evidence**: Structured QA artifacts comprising the PA5 AI Test Plan, automated test & coverage reports (`>= 80%`), SLA latency benchmark records, UAT sign-off matrix across all 8 Core + 2 AI features, and final PA5 acceptance deliverables.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Voice Quick-Post Efficiency)**: An approved Store Partner can record a multi-dish Vietnamese voice clip (or submit text), verify 2-tier allergen badges on Draft Cards, and complete 1-Tap Batch Publish in a single uninterrupted workflow, with end-to-end AI extraction completing in `< 3.0s` (P95) and `100%` of invalid/unmatched cards prevented from premature publishing.
- **SC-002 (Allergen Safety Hard Invariant)**: Automated QA across single/multi-allergen, accented/unaccented Vietnamese, bilingual EU FIC, and adversarial semantic-search scenarios records **0.0% allergen leakage** across all Personalized Recommendation and Conversational Semantic Search outputs.
- **SC-003 (Consumer AI Discovery Completion)**: A Consumer can configure any of the 14 EU FIC allergen exclusions on the preferences page, view their personalized Top 3 Recommendation Carousel (latency `< 2.5s` P95, fallback `< 300ms`), execute a Vietnamese conversational semantic search synchronized with the discovery map, and launch rescue checkout directly from a result with zero broken states.
- **SC-004 (Fault Resilience)**: Under 100% of simulated AI failure scenarios (missing credentials, upstream timeout, rate limit, network failure, invalid schema), the backend emits **0 unhandled `500` errors** and the frontend degrades cleanly without losing user context or blocking manual fallback workflows.
- **SC-005 (Quality & Coverage Gate)**: Overall automated test coverage reaches **`>= 80%`**, and 100% of mandatory verification checks (backend lint/format/type-check/tests, frontend lint/type-check/component tests/production build, and pre-commit hooks) exit cleanly with zero failures.
- **SC-006 (Containerized UAT & Release 1.0 Delivery)**: All 4 platform services boot cleanly together in containers, 100% of UAT scenarios spanning Core Features 1–8 and AI Features 1–2 pass with documented evidence, and the PA5 report (`docs/PA5.md` + `docs/PA5.pdf`), Release `v1.0.0` tag, and Final Go-Live Demo Video are completed on or before `2026-12-11` (`23:59`).

## Assumptions

- **Backend AI Dependencies Ready from Sprint 5 Core Tasks**: Backend endpoints `POST /api/v1/ml/parse-dish-nlp` (`EC5-01`, `specs/002-ai-quick-post-nlp`), `GET`/`PUT /api/v1/users/me/preferences` (`EC5-02`), `GET /api/v1/recommendations/personalized`, and `POST /api/v1/dishes/search-semantic` (`EC5-03`) are implemented and merged before final integration; frontend development and component tests can proceed immediately in parallel against the frozen API contracts in `contracts/api-contracts.md`.
- **PA4 Core Frontend & Testing Baseline**: Core F1–F8 frontend screens (`/`, `/login`, `/register`, `/orders`, `/orders/vnpay-return`, `/green-points`, `/store/onboard`, `/store/menu`, `/store/dishes`, `/store/verify-qr`, `/admin`), the centralized HTTP client (`@/lib/api-client`), React Query provider, and Vitest test runner are in place from PA4.
- **Browser Capabilities**: Modern Chromium, Safari, and Firefox browsers support `navigator.mediaDevices.getUserMedia` and `MediaRecorder` over `localhost` or HTTPS; devices lacking support or permissions automatically use the built-in Vietnamese text-input fallback.
- **Team Assignment & Review Matrix (Sprint 5)**: `EC5-04` is assigned to Võ Ngọc Thịnh (Reviewer: Phùng Quốc Huy); `EC5-05` is assigned to Võ Ngọc Thịnh (Reviewer: Đặng Trọng Phúc); `EC5-06` is assigned to Đàng Thế Tony (Reviewer: Phùng Quốc Huy); `EC5-07` is executed by the whole team coordinated by Phùng Quốc Huy (PM) ahead of Internal Deadline `2026-12-11` and Moodle submission `2026-12-12`.
