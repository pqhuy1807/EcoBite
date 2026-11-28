# Feature Specification: AI Smart Food Recommendation Engine & Conversational Semantic Search

**Feature Branch**: `feat/ai-2-recommendation`

**Created**: 2026-11-28

**Status**: Draft

**Input**: User description: "AI Feature 2 — Smart Food Recommendation Engine (3-Layer SQL Allergen Hard Filter + Deterministic Multi-Factor Heuristic Scoring + Gemini 2.5 Flash Justification with Deterministic Fallback) & Conversational Semantic Search, together with Consumer Allergen & Taste Preference Management, an Offline Golden Dataset Evaluation Harness, an AI Safety & Invariant Test Suite, and a Technical Research Report."

## Summary *(mandatory)*

Hungry consumers browsing urban surplus-food listings often face choice overload—scrolling through dozens of time-sensitive meals while worrying about hidden allergens (such as peanuts, fish sauce, shellfish, dairy, or gluten), dietary restrictions (vegetarian/vegan), walking distance, and fast-expiring closing deals. This feature serves **Consumers** (and public visitors performing quick natural-language discovery) by combining four cohesive capabilities: (1) personal allergen and dietary preference management aligned to the 14 EU FIC allergen categories, (2) a strict **3-Layer Hybrid Recommendation Engine** where medical allergen safety is guaranteed as a **0.0% leakage hard invariant** directly at the database query layer before deterministic multi-factor scoring (40% proximity, 30% discount depth and closing-time urgency, 30% taste profile match) and concise Vietnamese generative justifications (20–30 words) with instant deterministic fallback, (3) **Conversational Semantic Search** translating natural Vietnamese queries (e.g., *"Tìm món nước nóng dưới 30k gần đây"*) into structured discovery filters always routed through the same allergen safety invariant, and (4) an **Offline Evaluation Harness & Safety Verification Suite** objectively proving zero allergen leakage, high ranking quality, high semantic intent accuracy, factual justification faithfulness, and sub-2.5-second responsiveness.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consumer Allergen & Dietary Preference Profile Management (Priority: P1)

As a Consumer with food allergies, dietary rules, or a meal budget, I want to view and save my excluded allergens, preferred meal categories, dietary lifestyle (none, vegetarian, or vegan), and maximum per-meal budget so that the platform remembers my safety and taste profile across every recommendation and search.

**Why this priority**: Accurate, normalized personal allergen and dietary profiles are the mandatory prerequisite for enforcing consumer food safety and personalizing meal rankings.

**Independent Test**: Can be fully tested by authenticating as a Consumer, retrieving the default preference profile, updating it with Vietnamese or English allergen names (including accented, unaccented, and composite terms such as *"đậu phộng"* or *"hải sản"*), preferred categories, dietary lifestyle, and maximum budget, and verifying that the saved profile persists with canonical EU FIC allergen categories while non-consumer roles are denied access.

**Acceptance Scenarios**:

1. **Given** a newly registered Consumer who has not yet saved preferences, **When** the consumer requests their preference profile, **Then** the system returns a valid default profile with empty preferred categories, `NONE` dietary lifestyle, empty excluded allergens, and unset maximum budget.
2. **Given** an authenticated Consumer submits preference updates containing Vietnamese or English allergen expressions (e.g., `["đậu phộng", "Hải sản", "sữa"]`), preferred categories (`["NOODLES", "RICE"]`), dietary lifestyle (`"NONE"`), and a positive budget (`35000`), **When** the update is processed, **Then** the system normalizes and deduplicates every allergen to canonical 14 EU FIC categories (expanding *"Hải sản"* to cover crustaceans, molluscs, and fish/fish sauce), persists the profile, and returns the updated canonical profile.
3. **Given** a Consumer submits an unrecognized allergen label, an invalid meal category, or a negative budget, **When** input validation runs, **Then** the system rejects the update with a clear validation error without modifying existing saved preferences.
4. **Given** an unauthenticated visitor or a non-consumer account (Store Partner or Admin) attempts to access or modify consumer preferences, **When** authorization runs, **Then** the system denies access immediately.

---

### User Story 2 - Hard Safety Invariant Filtering at Data Query Boundary (Priority: P1)

As a Consumer with life-threatening food allergies or a vegetarian/vegan diet, I want the system to eliminate 100% of unsafe, sold-out, expired, unapproved-store, or out-of-radius dishes directly at the database query layer—never relying on probabilistic AI text generation or after-the-fact application filtering—so that zero unsafe dishes can ever enter ranking, AI prompting, or my screen.

**Why this priority**: Consumer health safety is a non-negotiable platform invariant (0.0% allergen leakage). Performing hard exclusion directly in the persistent query prevents unsafe dishes from ever reaching downstream ranking or AI models and ensures pagination/top-K limits never return truncated or unsafe sets.

**Independent Test**: Can be fully tested by seeding approved and unapproved stores at multiple distances with active, sold-out, and expired dishes carrying explicit, inferred, legacy-formatted, and base-menu allergens, querying candidates for consumers with single and multi-allergen exclusions (including accented/unaccented Vietnamese inputs and `"Hải sản"`), and verifying **0.0% allergen leakage** directly in the database query result set.

**Acceptance Scenarios**:

1. **Given** a Consumer whose profile excludes Peanuts and five nearby active dishes where two contain peanuts (one marked `EXPLICIT` on the dish and one marked `INFERRED` or inherited from the store's base menu), **When** candidate dishes are retrieved within the requested radius, **Then** the database query returns only the three peanut-free dishes and excludes 100% of peanut-containing dishes (`0.0%` leakage).
2. **Given** a Consumer whose profile excludes `"Hải sản"` (seafood) and nearby dishes containing shrimp (crustaceans), clams (molluscs), or fish sauce (fish), **When** candidate dishes are retrieved, **Then** all three seafood-bearing dishes are excluded at the database query layer.
3. **Given** nearby stores that include a pending/rejected KYC store, a sold-out dish (`remaining_quantity = 0`), an inactive dish, a dish whose pickup window has already ended, and a dish outside the requested radius (e.g., 4.2 km when searching 3.0 km), **When** candidate dishes are retrieved, **Then** all ineligible dishes are excluded directly at the query boundary.
4. **Given** a Consumer with dietary preference `VEGAN` or `VEGETARIAN`, **When** candidate dishes are retrieved, **Then** `VEGAN` consumers receive only `VEGAN` dishes and `VEGETARIAN` consumers receive only `VEGAN` or `VEGETARIAN` dishes.
5. **Given** every active dish within the requested radius contains at least one of the Consumer's excluded allergens, **When** recommendations are requested, **Then** the system returns an empty recommendation list rather than relaxing safety rules or substituting an unsafe dish.

---

### User Story 3 - Deterministic Multi-Factor Scoring & Personalized AI Justification with Safe Fallback (Priority: P1)

As a Consumer deciding what surplus meal to rescue right now, I want the top nearby safe dishes ranked transparently by proximity (40%), discount depth and closing-time urgency (30%), and my personal taste profile (30%), accompanied by a concise 20–30 word Vietnamese explanation grounded strictly in real meal facts, so I can pick the best meal in seconds even if the AI explanation service slows down or is unavailable.

**Why this priority**: This story delivers the core end-to-end consumer value of AI Feature 2—eliminating browsing fatigue, accelerating rescue of urgent closing-hour deals (-70% in the final 30–45 minutes), and keeping latency predictable through strict faithfulness validation and fast deterministic fallback.

**Independent Test**: Can be fully tested by authenticating as a Consumer with known preferences and GPS coordinates, calling personalized recommendations with both a mocked AI explanation client and a simulated AI timeout/failure, and verifying deterministic Top-K ranking order (40/30/30 weights), exact DB-grounded fields, 20–30 word faithful Vietnamese justifications, and fast (`< 300ms`) deterministic fallback on AI errors or hallucinated numbers.

**Acceptance Scenarios**:

1. **Given** an authenticated Consumer at known GPS coordinates with preferences (`preferred_categories=["NOODLES"]`, `max_budget=30000`, `excluded_allergens=["Peanuts (Đậu phộng)"]`) and multiple safe dishes in radius, **When** the consumer requests personalized recommendations (`limit=3`), **Then** the system ranks candidates deterministically using `Score = 0.40 * proximity + 0.30 * discount_urgency + 0.30 * taste_match`, prioritizes walkable urgent final-rush deals (`<= 30–45` minutes remaining, `-70%`), and returns Top-3 dishes with exact pricing, distance, discount percentage, urgency flag, and transparent allergen warnings.
2. **Given** Top-3 safe ranked candidates are passed to the generative explanation step, **When** the AI responds within the latency budget, **Then** each dish includes a persuasive Vietnamese `ai_justification` of 20–30 words whose mentioned price, discount percentage, distance, and remaining quantity match exact database facts (`0%` fabricated numbers) and never make ungrounded medical certification claims.
3. **Given** the generative AI returns a justification containing a fabricated price, wrong distance, wrong discount percentage, or violates length/schema bounds, **When** server-side faithfulness verification runs, **Then** the system discards the unfaithful sentence and seamlessly replaces it with a deterministic DB-grounded Vietnamese template justification.
4. **Given** the external AI service is unconfigured, unreachable, rate-limited, or exceeds its timeout budget, **When** the consumer requests personalized recommendations, **Then** the system still returns `200 OK` with the exact Top-K SQL-safe, heuristically ranked dishes and deterministic Vietnamese fallback justifications in under 300 milliseconds without crashing.
5. **Given** a Consumer with no saved preferences and no prior completed orders (cold-start user), **When** personalized recommendations are requested, **Then** the system applies neutral taste baselines without penalizing the user and ranks safe nearby dishes primarily by proximity and discount/closing-time urgency.

---

### User Story 4 - Conversational Natural-Language Semantic Search with Mandatory Allergen Safety (Priority: P2)

As a Consumer or public visitor craving a specific type of surplus meal, I want to search using everyday Vietnamese phrases (such as *"Tìm món nước nóng dưới 30k gần đây"* or *"Cơm trưa không đậu phộng dưới 35 cành"*) so that the system understands my budget, food category, dietary intent, and keywords while strictly protecting me from allergens.

**Why this priority**: Conversational search unlocks intuitive discovery beyond rigid filter dropdowns while reinforcing the same non-negotiable food-safety barrier across all consumer discovery entry points.

**Independent Test**: Can be fully tested by submitting natural Vietnamese queries both anonymously and with an authenticated allergic Consumer's credentials, verifying extracted structured intent (`max_price`, `categories`, `dietary`, `keywords`, query-level exclusions), verifying `0.0%` allergen leakage against both persisted user preferences and query-stated exclusions, verifying deterministic regex fallback when AI intent parsing is unavailable, and confirming fail-closed `401` denial if an invalid/expired bearer token is supplied.

**Acceptance Scenarios**:

1. **Given** a visitor submits *"Tìm món nước nóng dưới 30k gần đây"* with GPS coordinates and `radius_km=3.0`, **When** semantic search executes, **Then** the system extracts `max_price=30000`, `categories=["NOODLES"]`, and relevant warmth/soup keywords, filters eligible nearby dishes in the database, ranks matches by keyword relevance plus rescue value, and returns both the interpreted filter summary and matching dishes.
2. **Given** an authenticated Consumer allergic to Peanuts submits a generic query (*"Tìm món ăn tối rẻ gần đây"*) that does not mention peanuts, **When** semantic search executes, **Then** the system automatically loads the Consumer's persisted `excluded_allergens` and excludes 100% of peanut-containing dishes at the database query layer.
3. **Given** a public or authenticated user explicitly states an exclusion or dietary constraint in the query (e.g., *"Đồ chay thanh đạm không đậu nành dưới 25 cành"*), **When** semantic search executes, **Then** the system combines query-level constraints with any persisted user preferences and enforces all exclusions at the database query layer.
4. **Given** a request arrives with a malformed or expired authorization credential, **When** semantic search authenticates the request, **Then** the system rejects the request (`401 Unauthorized`) rather than silently falling back to an unfiltered anonymous search that could expose an allergic user to unsafe dishes.
5. **Given** the generative AI intent parser times out or is unavailable, **When** semantic search runs, **Then** a deterministic Vietnamese rule-based parser extracts budget, category, dietary, and keyword filters and executes the same SQL safety pipeline without failing the search.

---

### User Story 5 - Offline Evaluation Harness, Research Report & Allergen Safety QA Suite (Priority: P3)

As an AI Engineer and QA Lead preparing for Sprint 5 acceptance and production go-live, I want a reproducible 15–20 case Vietnamese Golden Dataset, an automated offline evaluation runner measuring all five AI-2 KPIs, an automated Allergen Hard Invariant verification suite, and a technical research report so that safety, ranking quality, intent accuracy, faithfulness, and latency are objectively proven before release.

**Why this priority**: Measurable offline benchmarks and adversarial safety invariant tests provide auditable proof that zero allergen leakage holds across every input variant and prevent ranking or prompt regressions during Sprint 5 iteration.

**Independent Test**: Can be tested independently by executing the offline evaluation runner against the 15–20 case Golden Dataset and executing the dedicated allergen invariant and recommendation integration test suites, confirming every KPI report metric is generated and 0.0% allergen leakage passes across all adversarial test cases.

**Acceptance Scenarios**:

1. **Given** a Golden Dataset of 15–20 Vietnamese user personas and natural-language semantic queries covering single/multi-allergen profiles, Vietnamese diacritics/synonyms, vegan/vegetarian lifestyles, tight budgets, urgent closing deals, cold-start profiles, and all-unsafe catalogs, **When** the offline evaluation runner executes, **Then** it computes and prints all five KPI metrics (Allergen Leakage Rate, `NDCG@3` & `Precision@3`, Semantic Intent Extraction Accuracy, Justification Faithfulness & word-count adherence, and P95 / Fallback Latency).
2. **Given** the dedicated Allergen Hard Invariant integration and property-based test suite runs against both personalized recommendations and semantic search, **When** adversarial inputs (accented, unaccented, mixed-case, `"Hải sản"`, legacy dish allergen strings, base-menu allergens, empty safe set) are tested, **Then** 100% of assertions verify `0.0%` allergen leakage.
3. **Given** the evaluation completes, **When** the team reviews the AI-2 research report and PA5 AI test plan, **Then** both documents record the canonical normalization design, database query optimization strategy, heuristic weight sensitivity analysis, faithfulness guard mechanics, and actual observed baseline scores against target thresholds.

---

### Edge Cases

- **All nearby dishes contain the user's excluded allergens**: System MUST return `200 OK` with an empty `recommendations` / `results` list and an informative metadata message—never relaxing allergen exclusions or surfacing an unsafe fallback dish.
- **Dish allergen recorded only on Base Menu or in legacy/shortened format**: A dish whose `allergens` array uses a shortened label (e.g., `"Milk (Sữa)"`, `"Fish (Nước mắm)"`, `"Gluten"`, `"Sesame (Mè)"`) or whose allergen is present on its linked Base Menu entry (`base_allergens`) MUST still be excluded by the SQL hard filter (`0.0%` leakage).
- **Composite Vietnamese allergen term (`"Hải sản"`) and regional synonyms (`"lạc"`, `"vừng"`, `"đậu tương"`)**: System normalizes regional synonyms to their exact EU FIC category and expands `"Hải sản"` / `"seafood"` across Crustaceans, Molluscs, and Fish so shrimp, clams, squid, and fish sauce are all blocked.
- **Expired or invalid token on public-capable Semantic Search**: Fail-closed `401 Unauthorized` prevents silently dropping an allergic consumer's safety profile into an unfiltered anonymous query.
- **Invalid GPS coordinates or out-of-bounds radius/limit**: Coordinates outside `lat [-90, 90]` / `lng [-180, 180]`, radius outside `1.0–10.0 km`, or `limit` outside valid bounds (`1–10` for personalized, `1–30` for semantic search) are rejected with `422 Unprocessable Entity`.
- **Blank or overly long semantic search query**: Whitespace-only queries, queries shorter than 2 characters, or queries exceeding 300 characters are rejected with `422 Unprocessable Entity` before calling AI.
- **Pickup window expiring or zero remaining stock**: Dishes whose `pickup_end_time` has passed relative to authoritative `Asia/Ho_Chi_Minh` server time or whose `remaining_quantity == 0` or `status != ACTIVE` are excluded directly at the database query layer.
- **Dish with explicit clearance price override (`override_discounted_price`)**: Scoring computes `current_price` and `discount_percent` using the authoritative deterministic rule-based pricing engine (`DishService.calculate_time_shifted_discount`) so urgent `-70%` rush discounts and fixed partner overrides are scored consistently without AI price guessing.
- **Tied heuristic scores**: Deterministic tie-breaking (`total_score DESC`, `distance_meters ASC`, `pickup_end_time ASC`, `dish_id ASC`) guarantees stable, reproducible ordering.
- **Gemini partial response (missing justification for 1 of 3 dishes)**: Only the missing or unfaithful dish falls back to the deterministic template while valid faithful justifications for the remaining dishes are preserved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide authenticated `CONSUMER` endpoints to read (`GET`) and create/update (`PUT`) their `UserPreference` profile (`preferred_categories`, `dietary_preference`, `excluded_allergens`, `max_budget`) and MUST reject unauthenticated or non-consumer requests.
- **FR-002**: System MUST normalize every entry in `excluded_allergens` to canonical values from the 14 EU FIC allergen categories (`EUAllergen`), supporting bilingual English/Vietnamese names, accented and unaccented forms, regional synonyms (e.g., *"lạc"* → Peanuts, *"vừng"* → Sesame), and composite seafood mapping (*"Hải sản"* → Crustaceans, Molluscs, and Fish), while rejecting unrecognized allergen labels with a validation error.
- **FR-003**: System MUST execute Layer 1 candidate filtering directly inside the persistent database query (`WHERE` clause), returning ONLY dishes that simultaneously satisfy:
  - Owning store has `APPROVED` food-safety (KYC) status and lies within the requested radius (`1.0–10.0 km`, default `3.0 km`) computed via geospatial distance (`ST_DWithin` / `ST_Distance` on PostgreSQL PostGIS, with exact geodesic Haversine parity for portable in-memory testing).
  - Dish status is `ACTIVE`, `remaining_quantity > 0`, and `pickup_end_time` is strictly after authoritative `Asia/Ho_Chi_Minh` server time.
  - **Allergen Hard Invariant (`0.0%` leakage)**: Zero intersection between the user's normalized/expanded `excluded_allergens` and EITHER the dish's `allergens` OR its linked base menu item's `base_allergens` (handling both structured warning objects and legacy/seeded string variants directly in SQL).
  - **Dietary Lifestyle Enforcement**: When `dietary_preference` is `VEGAN`, return only `VEGAN` dishes; when `VEGETARIAN`, return only `VEGAN` or `VEGETARIAN` dishes.
- **FR-004**: System MUST NOT rely on Python-only post-filtering (`allergen_filter_service.py`) as the primary allergen safety barrier and MUST NEVER delegate allergen safety decisions to generative AI.
- **FR-005**: System MUST rank Layer 1 safe candidates in Layer 2 using the deterministic multi-factor formula:
  $$\text{Score} = (0.40 \times S_{\text{proximity}}) + (0.30 \times S_{\text{discount\_urgency}}) + (0.30 \times S_{\text{taste\_match}})$$
  where each sub-score is normalized to `[0.0, 1.0]`, active prices and rush flags come from the authoritative deterministic time-shifted pricing engine, final-rush deals (`<= 30–45` minutes before closing, `-70%`) receive maximum urgency priority, cold-start consumers receive neutral taste baselines, and Top-K (`default K=3`, bounded `1–10`) selection uses deterministic tie-breaking.
- **FR-006**: System MUST send ONLY the Top-K already SQL-safe, ranked dish facts and a sanitized taste summary (never raw personal identifiers or unsafe dishes) to Layer 3 generative AI to synthesize a concise Vietnamese `ai_justification` targeting 20–30 words per dish.
- **FR-007**: System MUST run a deterministic server-side faithfulness check on every generated justification verifying that all numeric claims (price, original price, discount percentage, distance, remaining stock, closing time) match authoritative database facts (`0%` fabricated numbers) and that length and safety wording comply with guidelines; any unfaithful or missing justification MUST be replaced by a deterministic DB-grounded Vietnamese fallback template.
- **FR-008**: System MUST degrade gracefully when the generative AI service is unconfigured, times out, hits rate limits, or errors, returning `200 OK` with Top-K SQL-safe heuristically ranked recommendations and deterministic Vietnamese fallback justifications.
- **FR-009**: System MUST provide Conversational Semantic Search accepting natural Vietnamese query text (`2–300` characters) plus GPS coordinates and radius (`1.0–10.0 km`), extracting structured search intent (`max_price`, `categories`, `dietary`, `query_excluded_allergens`, `keywords`, `urgent_only`) via generative AI structured output with a deterministic Vietnamese rule-based fallback parser when AI is unavailable.
- **FR-010**: System MUST route every Conversational Semantic Search execution through Layer 1 SQL Allergen Hard Filtering—automatically applying the authenticated user's persisted `UserPreference.excluded_allergens` (unioned with any query-stated exclusions) when a valid token is present, defaulting cleanly for unauthenticated public visitors, and failing closed (`401 Unauthorized`) if an invalid or expired authorization token is supplied.
- **FR-011**: System MUST load all AI credentials exclusively from environment configuration using separate test/development and paid demo keys (`GEMINI_TEST_API` vs `GEMINI_DEMO_API`, default test key) and MUST NEVER log, expose, or commit secrets.
- **FR-012**: System MUST deliver an offline Golden Dataset (15–20 Vietnamese persona and semantic query cases), an automated evaluation runner measuring all five AI-2 KPIs, an automated Allergen Hard Invariant & Recommendation QA test suite, a PA5 AI Test Plan, and a technical research report documenting observed baseline scores.

### Non-Functional Requirements *(mandatory when the feature touches money, health, or personal data)*

- **NFR-001 (Food Safety & Health Invariant)**: Allergen Leakage Rate MUST be strictly **0.0%** across both Personalized Recommendations and Conversational Semantic Search under all valid and adversarial allergen representations. Inferred allergen warnings on returned dishes MUST remain clearly labeled and justifications MUST NEVER claim medical allergy certification.
- **NFR-002 (Performance & Latency SLA)**: End-to-end Personalized Recommendation and Semantic Search latency MUST target **P95 < 2.5 seconds** when generative AI is active (enforced via bounded upstream AI timeout budget) and **< 300 milliseconds** when falling back to deterministic templates/rules. Database candidate queries MUST leverage PostGIS spatial indexing and JSONB indexing on PostgreSQL without N+1 query storms.
- **NFR-003 (Security, Privacy & Fail-Closed Auth)**: Consumer preference endpoints and personalized recommendations MUST enforce server-side `CONSUMER` role checks with JWT verification. Semantic search MUST fail closed (`401`) on invalid/expired tokens. Prompts sent to external AI MUST contain only dish facts and non-identifying preference summaries (no email, phone, password hash, or raw token).
- **NFR-004 (Async Execution & Observability)**: All database queries and external AI requests MUST execute asynchronously without blocking the event loop. Structured operational logs MUST record request mode, candidate counts (pre-rank/returned), justification/intent source (`GEMINI` vs `FALLBACK`), faithfulness fallback count, and latency without leaking secrets or user PII.
- **NFR-005 (Dependency Isolation & Portability)**: No heavy ML training libraries (`ultralytics`, `jupyterlab`, `matplotlib`) may be added to backend runtime dependencies. SQL hard filtering MUST operate portably across both PostgreSQL 16 (PostGIS + JSONB) and SQLite in-memory automated tests (`aiosqlite` + JSON1) without bypassing SQL-level exclusion.

### Key Entities *(include if feature involves data)*

- **User Preference (`UserPreference`)**: A 1-to-1 persisted consumer profile holding `preferred_categories`, `dietary_preference` (`NONE` / `VEGAN` / `VEGETARIAN`), normalized canonical `excluded_allergens` (14 EU FIC categories), and optional `max_budget`.
- **Rescue Dish Candidate (`Dish` + `Store` + `MenuItem`)**: An active surplus meal from an `APPROVED` nearby store with `remaining_quantity > 0` and unelapsed pickup window, combining authoritative time-shifted pricing, 2-tier `allergens`, linked `base_allergens`, `dietary_type`, and geodesic distance.
- **Heuristic Score Breakdown**: Deterministic `[0.0, 1.0]` component scores (`proximity_score`, `discount_urgency_score`, `taste_match_score`) and weighted composite `total_score` explaining why each dish ranked in the Top-K.
- **Personalized Recommendation Item**: A ranked safe dish returned to the consumer with exact pricing, discount percentage, urgency indicator, transparent 2-tier allergen annotations, concise Vietnamese `ai_justification`, and provenance flag (`GEMINI` or `FALLBACK`).
- **Semantic Search Intent**: Structured filter criteria extracted from natural Vietnamese text (`max_price`, `categories`, `dietary`, `query_excluded_allergens`, `keywords`, `urgent_only`, plus provenance `GEMINI` or `FALLBACK`).
- **Evaluation Golden Scenario**: A curated offline test case pairing a consumer profile (allergens, diet, budget, preferred categories, optional order history) or Vietnamese semantic search query against a controlled catalog of nearby dishes and expected ground-truth safety/ranking/intent targets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Zero Allergen Leakage — Hard Invariant)**: **0.0%** Allergen Leakage Rate across all 15–20 Golden Dataset scenarios and 100% of automated adversarial safety invariant tests (both Personalized Recommendations and Conversational Semantic Search).
- **SC-002 (Ranking Quality)**: Achieve **`NDCG@3 >= 0.85`** (and report `Precision@3`) against expected ground-truth persona rankings on the 15–20 case Vietnamese Golden Dataset.
- **SC-003 (Semantic Intent Extraction Accuracy)**: Achieve **`>= 90%`** normalized extraction accuracy across `max_price`, `categories`, `dietary`, and explicit exclusions on Vietnamese natural-language search queries in the Golden Dataset.
- **SC-004 (Justification Faithfulness)**: Achieve **`>= 95%`** factual faithfulness with **0%** fabricated numeric claims (price, discount %, distance, quantity) and 20–30 word Vietnamese conciseness across generated recommendations.
- **SC-005 (Response Time & Resilience)**: Achieve **P95 latency < 2.5 seconds** with live generative AI and **< 300 milliseconds** under deterministic fallback, with zero unhandled `500` errors across AI timeout, missing credential, rate-limit, and invalid-output fault injections.
- **SC-006 (Verification & Coverage Compliance)**: All new backend repositories, services, schemas, and endpoints pass automated linting, formatting, strict static type checking, unit/integration/safety-invariant tests, and contribute toward the `>= 80%` project test coverage gate.

## Assumptions

- **Existing Core Platform Reuse**: User JWT authentication, role enforcement (`CONSUMER`, `STORE_PARTNER`, `ADMIN`), Store KYC (`APPROVED`), `MenuItem` catalog, `Dish` listings with deterministic `DishService.calculate_time_shifted_discount`, `Order` history, and the `user_preferences` database table are already implemented and migrated from earlier milestones (PA1–PA4).
- **Backend, Evaluation & QA Scope**: This specification covers the complete Backend AI-2 system (`EC5-02`, `EC5-03`), Offline Golden Dataset & Research Report (Week 6 Baseline), and Allergen Safety / API QA Suite (`EC5-06`). Consumer frontend components (Smart Recommendation Carousel, Semantic Search Bar on `/`, and `/profile/preferences` UI) are tracked separately under `EC5-05` and will consume the REST contracts defined here.
- **Authoritative Timezone & Currency**: All pickup window checks and closing-time urgency calculations operate in `Asia/Ho_Chi_Minh` (`UTC+7`) authoritative server time, and all meal prices and budgets are denominated in Vietnamese Dong (`VND`).
- **Backward Compatibility with Legacy Tests**: Existing Week-5 utility tests (`test_allergen_filter_service.py`) and cluster model tests (`test_cluster1_models.py`) remain passing during migration, while `RecommendationRepository` and `RecommendationService` enforce SQL-level allergen exclusion exclusively and never depend on Python-only filtering for safety.
- **Team Assignment Alignment**: Work aligns cleanly across `EC5-02` (Đặng Trọng Phúc — `UserPreference` CRUD, Layer 1 SQL Hard Filter, Week 6 AI-2 Baseline & Research Report), `EC5-03` (Phùng Quốc Huy — Layer 2 Scoring, Layer 3 Gemini Justification & Semantic Search refinement), and `EC5-06` (Đàng Thế Tony — Allergen Hard Invariant test suite, API integration & SLA suite, and PA5 AI Test Plan).
