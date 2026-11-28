# Technical Research & Design Decisions: AI Feature 2 — Smart Food Recommendation & Conversational Semantic Search

**Feature**: `006-ai-smart-recommendation-search` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

This document resolves every architectural, SQL dialect, normalization, heuristic scoring, Gemini integration, faithfulness, security, and offline evaluation decision before implementation begins.

---

## Decision 1: Replacing Python-Only `AllergenHardFilterService` with SQL-Level Hard Filtering (Guardrail #7)

- **Decision**: Implement Layer 1 filtering exclusively inside `backend/app/repositories/recommendation_repo.py` using SQL `WHERE NOT EXISTS (...)` predicates executed by the database engine—covering BOTH `dishes.allergens` AND `menu_items.base_allergens` (via `LEFT OUTER JOIN menu_items`)—with portable dialect branches for **PostgreSQL 16 (JSONB)** and **SQLite (`aiosqlite` JSON1 `json_each`)**. Mark `backend/app/services/allergen_filter_service.py` as deprecated (do not invoke it from `RecommendationService`, while keeping its module/test intact so existing CI tests pass cleanly).
- **Why Python-Only Filtering MUST Be Replaced**:
  1. **Direct Guardrail #7 & Constitution Principle IV Mandate**: Allergen exclusion MUST happen at the SQL database query level before ranking or AI explanation—never filtered solely in Python memory after fetching unfiltered rows.
  2. **Database Boundary Safety**: Fetching unsafe `Dish` rows into Python violates defense-in-depth; any consumer of the repository could accidentally serialize or cache unsafe items.
  3. **Pagination / Top-K Correctness**: Applying `LIMIT` in SQL before Python filtering causes silent result shrinkage (e.g., returning 0 dishes when safe dishes exist at row 25), whereas fetching unbounded rows into Python degrades scalability.
  4. **Substring & Data-Shape Bugs in Week-5 Draft**: `allergen_filter_service.py` checks `ua in da or da in ua`, which misses composite Vietnamese terms (`"Hải sản"` fails to exclude `"Crustaceans (Tôm)"` and `"Fish (Nước mắm)"`), misses synonyms (`"lạc"` vs `"đậu phộng"`), risks false substring positives on short ASCII-folded terms (`"ca"` matching `"can tay"`), and fails to inspect `menu_items.base_allergens` (in `backend/app/db/seed.py`, `Cơm Sườn Bì Chả` lists `"Fish (Nước mắm)"` in `menu_items.base_allergens` while `dishes.allergens` only holds `"Eggs (Trứng)"`!).
- **Dual-Dialect SQL Exclusion Design**:
  - Given normalized canonical `excluded_allergens: list[EUAllergen]`, `allergens.expand_sql_exclusion_terms(excluded_allergens)` deterministically produces:
    - `exact_lower_tokens: set[str]` (all canonical EU values, known seeded variants like `"milk (sữa)"`, `"fish (nước mắm)"`, `"crustaceans (tôm)"`, `"sesame (mè)"`, `"gluten"`, `"nuts (quả hạch)"`, plus English & Vietnamese accented/unaccented terms).
    - `like_patterns: list[str]` (safe bounded word/prefix patterns such as `"peanuts%"`, `"%đậu phộng%"`, `"%Đậu phộng%"`, `"%Đậu Phộng%"`, `"%dau phong%"`, `"%trứng%"`, `"%Trứng%"`, `"eggs%"`, etc. — explicitly covering both Title Case and lowercase Vietnamese characters because **SQLite's built-in `LOWER()` only case-folds ASCII `A-Z`**, not Unicode `Đ/đ` or `Ứ/ứ`!).
  - **PostgreSQL 16 Branch (Production)**:
    - Single SQL query joining `Dish` + `Store` + `LEFT OUTER JOIN MenuItem`:
      - Geospatial filter: `ST_DWithin(cast(Store.location, Geography), user_geo, radius_m)` + `ST_Distance(...)` (reusing the exact PostGIS pattern proven in `store_repo.py`).
      - Status & inventory filter: `Store.kyc_status == KycStatus.APPROVED`, `Dish.status == DishStatus.ACTIVE`, `Dish.remaining_quantity > 0`, `Dish.pickup_end_time > current_time_vn`.
      - Allergen Hard Filter (checking both `dishes.allergens` and `menu_items.base_allergens`):
        ```sql
        AND NOT EXISTS (
          SELECT 1
          FROM jsonb_array_elements(dishes.allergens) AS elem
          WHERE lower(COALESCE(elem->>'allergen', trim(both '"' from elem::text))) = ANY(:exact_tokens)
             OR EXISTS (
                  SELECT 1 FROM unnest(:like_patterns) AS pat
                  WHERE lower(COALESCE(elem->>'allergen', trim(both '"' from elem::text))) LIKE pat
                )
        )
        AND (
          menu_items.id IS NULL OR NOT EXISTS (
            SELECT 1
            FROM jsonb_array_elements(menu_items.base_allergens) AS base_elem
            WHERE lower(trim(both '"' from base_elem::text)) = ANY(:exact_tokens)
               OR EXISTS (
                    SELECT 1 FROM unnest(:like_patterns) AS pat
                    WHERE lower(trim(both '"' from base_elem::text)) LIKE pat
                  )
          )
        )
        ```
      - Note on GIN Index Acceleration: When `dishes.allergens` contains canonical `EUAllergen` objects (all dishes created via AI-1 Quick-Post), a supplementary `NOT (dishes.allergens @> jsonb_build_array(jsonb_build_object('allergen', :canonical)))` predicate can be accelerated by `idx_dishes_allergens_gin` (`USING GIN (allergens)`), while the `NOT EXISTS (jsonb_array_elements(...))` clause guarantees 0.0% leakage even against legacy seeded short strings (`"Gluten"`, `"Milk (Sữa)"`) and plain-string arrays.
  - **SQLite Branch (`aiosqlite` in pytest & local dev)**:
    - Executes the **exact same `WHERE NOT EXISTS (...)` allergen exclusion inside SQLite's SQL engine** using built-in JSON1 `json_each(dishes.allergens)` and `json_each(menu_items.base_allergens)` with parameterized `IN` + `LIKE` predicates (including Vietnamese case variants for SQLite's ASCII-only `LOWER()`), plus `Store.kyc_status == APPROVED`, `Dish.status == ACTIVE`, `Dish.remaining_quantity > 0`, `Dish.pickup_end_time > current_time_vn`, and dietary/category SQL filters.
    - Computes exact spherical Haversine distance (`store_repo.haversine_distance_meters`) for the `radius_km` bound because SQLite lacks PostGIS `ST_DWithin` (identical to `store_repo.py`).
- **Alternatives considered**:
  - Relying solely on PostgreSQL `@>` exact JSONB containment: rejected because `seed.py` and manual dish entries contain non-canonical strings like `"Milk (Sữa)"`, `"Gluten"`, and `"Fish (Nước mắm)"`, which exact `@>` would miss (causing allergen leakage!).
  - Creating a normalized join table `dish_allergens(dish_id, eu_allergen)`: cleaner at huge scale, but requires a new migration and backfilling across `DishService`, `MenuService`, and `seed.py` outside AI-2 scope; `jsonb_array_elements` + `menu_items.base_allergens` works immediately on the existing 12-table schema with zero breaking changes.

---

## Decision 2: Canonical `EUAllergen` Normalization & Vietnamese Synonym / Composite Mapping

- **Decision**: Centralize allergen normalization in `backend/app/core/allergens.py` anchored strictly to the 14 `EUAllergen` enum values in `backend/app/schemas/nlp.py`.
  - Normalize inputs by lowercasing, collapsing whitespace, and stripping Vietnamese diacritics (`unicodedata.normalize("NFD")` + mapping `đ` → `d`, because Unicode NFD does NOT decompose `đ`!).
  - Map every single-category English/Vietnamese synonym deterministically to its canonical `EUAllergen` value (e.g., `"dau phong"`, `"lac"`, `"peanut"`, `"peanuts"` → `EUAllergen.PEANUTS`; `"sua"`, `"bo sua"`, `"pho mai"`, `"milk"`, `"dairy"` → `EUAllergen.MILK`; `"trung"`, `"egg"`, `"eggs"` → `EUAllergen.EGGS`; `"bot mi"`, `"lua mi"`, `"banh mi"`, `"gluten"` → `EUAllergen.GLUTEN`; `"dau nanh"`, `"dau tuong"`, `"tau hu"`, `"soy"`, `"soybeans"` → `EUAllergen.SOYBEANS`; `"ca"`, `"nuoc mam"`, `"fish"` → `EUAllergen.FISH`; `"tom"`, `"cua"`, `"ghe"`, `"giap xac"`, `"crustaceans"`, `"shellfish"`, `"shrimp"`, `"crab"` → `EUAllergen.CRUSTACEANS`; `"ngheu"`, `"so"`, `"oc"`, `"muc"`, `"bach tuoc"`, `"nhuyen the"`, `"molluscs"` → `EUAllergen.MOLLUSCS`; `"me"`, `"vung"`, `"sesame"` → `EUAllergen.SESAME`; `"hat cay"`, `"qua hach"`, `"hat dieu"`, `"hanh nhan"`, `"oc cho"`, `"tree nuts"`, `"nuts"` → `EUAllergen.TREE_NUTS`; `"can tay"`, `"celery"` → `EUAllergen.CELERY`; `"mu tat"`, `"mustard"` → `EUAllergen.MUSTARD`; `"sulfit"`, `"sulphites"`, `"sulfites"` → `EUAllergen.SULPHITES`; `"lupin"`, `"dau lupin"` → `EUAllergen.LUPIN`).
  - Map composite Vietnamese/English seafood terms (`"hai san"`, `"seafood"`) to the full 3-allergen seafood union: `[EUAllergen.CRUSTACEANS, EUAllergen.MOLLUSCS, EUAllergen.FISH]`.
  - On `PUT /api/v1/users/me/preferences`: reject unknown strings (not matching any canonical `EUAllergen` or synonym) with HTTP `422 Unprocessable Entity`, returning the list of valid allergen keys.
  - On read (inside `RecommendationRepository`): run `normalize_allergens(..., strict=False)` over persisted `UserPreference.excluded_allergens` so pre-existing seeded rows (`pref_an`, `pref_bich` in `seed.py` which store `["Đậu phộng", "Peanuts (Đậu phộng)"]` and `["Hải sản", "Milk (Sữa)"]`) still compile to complete SQL exclusion predicates with 0.0% leakage!
  - Note on `đ` decomposition: In Python, `unicodedata.normalize("NFD", "đậu")` leaves `đ` (`U+0111`) intact rather than turning it into `d`! Explicitly calling `.replace("đ", "d").replace("Đ", "d")` before stripping combining marks (`Mn`) fixes a classic Vietnamese normalization bug that existed in the Week-5 `allergen_filter_service.py` comment (`# Decompose unicode (e.g. "đ" -> "d")` did NOT actually decompose `đ`!).
- **Rationale**: Eliminates silent misses on Vietnamese `"đậu phộng"` vs `"dau phong"` and `"đậu nành"` vs `"dau nanh"`, guarantees `"Hải sản"` protects against shrimp, clams, and fish sauce, and preserves full compatibility with `seed.py` and `test_cluster1_models.py`.

---

## Decision 3: Authoritative Active-Window, Status (`DishStatus.ACTIVE`) & Pricing Grounding

- **Decision**:
  - Use `DishStatus.ACTIVE` (the exact ORM enum value in `backend/app/models/dish.py`, noting that PM prose occasionally says "AVAILABLE" conceptually).
  - Resolve current time authoritatively via `datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).time()` (with optional internal `reference_time: datetime | None = None` parameter on `RecommendationService` for deterministic unit tests and offline Golden Dataset evaluation).
  - Filter active pickup windows in SQL: `Dish.pickup_end_time > now_vn_time` (allowing upcoming-today rescue dishes whose pickup window hasn't closed yet, or dishes currently inside their pickup window, while strictly excluding already-expired closing windows).
  - Compute authoritative `current_price`, `rule_discount_price`, and `is_rule_discount_active` via `DishService.calculate_time_shifted_discount(..., current_time=now_vn)` (Constitution Principle V — never letting AI compute or guess prices).
- **Rationale**: Matches `backend/app/models/dish.py` and `backend/app/services/dish_service.py` verbatim; ensures unit tests and offline eval runs are 100% reproducible regardless of host clock or timezone.

---

## Decision 4: Layer 2 Deterministic Multi-Factor Heuristic Scoring (`0.40 / 0.30 / 0.30`)

- **Decision**: Compute deterministic `[0.0, 1.0]` normalized component scores on the SQL-safe candidate list in `backend/app/services/recommendation_service.py`:
  $$\text{Score} = (0.40 \times S_{\text{proximity}}) + (0.30 \times S_{\text{discount\_urgency}}) + (0.30 \times S_{\text{taste\_match}})$$
  1. **`S_proximity` (`weight = 0.40`)**:
     $$S_{\text{proximity}} = \text{clamp}\!\left(1.0 - \frac{\text{distance\_meters}}{\text{radius\_km} \times 1000.0},\; 0.0,\; 1.0\right)$$
  2. **`S_discount_urgency` (`weight = 0.30`)**:
     - `discount_ratio = clamp((original_price - current_price) / original_price, 0.0, 1.0)`
     - `S_discount = min(1.0, discount_ratio / 0.70)` (reaches `1.0` at `-70%` final-rush discount; `-50%` yields `0.714`).
     - Let `minutes_left = (pickup_end_dt - now_vn_dt).total_seconds() / 60.0`:
       - If `is_rule_discount_active` or `minutes_left <= 45.0`: `is_urgent_deal = True`;
         - `minutes_left <= 30.0` → `S_urgency = 1.0`
         - `30.0 < minutes_left <= 45.0` → `S_urgency = 0.75 + 0.25 * (45.0 - minutes_left) / 15.0`
       - Else (`minutes_left > 45.0`): `is_urgent_deal = False`;
         - `45.0 < minutes_left <= 180.0` → `S_urgency = 0.75 * (180.0 - minutes_left) / 135.0`
         - `minutes_left > 180.0` → `S_urgency = 0.0`
     - `S_discount_urgency = 0.50 * S_discount + 0.50 * S_urgency`.
  3. **`S_taste_match` (`weight = 0.30`)**:
     - **Category preference (`0.40` share)**: `1.0` if `dish.category.value in preferred_categories`; `0.5` neutral baseline if `preferred_categories` is empty; `0.0` if non-empty and not matched.
     - **Budget fit (`0.25` share)**: if `max_budget is not None and max_budget > 0`: `1.0` when `current_price <= max_budget`, else soft linear penalty `max(0.0, 1.0 - (current_price - max_budget) / max_budget)`; `0.5` neutral baseline if `max_budget` is `None`.
     - **Dietary alignment (`0.20` share)**: `1.0` when `dietary_preference in {VEGAN, VEGETARIAN}` (already enforced in SQL Layer 1) or exact vegan bonus; `0.5` neutral baseline when `dietary_preference == NONE`.
     - **Order-history affinity (`0.15` share)**: read up to 20 recent `COMPLETED` orders via `OrderRepository(db).list_by_consumer(user_id, order_status=OrderStatus.COMPLETED, limit=20)`. If history is non-empty, compute `min(1.0, (category_hits + 0.5 * store_hits) / total_orders)`; if cold-start (0 orders), assign neutral `0.5`.
  4. **Deterministic Tie-Breaking**: Sort candidates by `(-round(total_score, 6), distance_meters, pickup_end_time, str(dish.id))` and slice `[:limit]` (`default limit=3`, bounded `1..10`).
- **Rationale**:
  - Guarantees every sub-score stays strictly in `[0.0, 1.0]`, preventing a cheap dish at the edge of a 10 km radius from overshadowing a walkable 300 m final-rush deal.
  - Cold-start users get neutral `0.5` baselines on absent taste dimensions instead of `0.0`, keeping scores well-calibrated.
  - Full deterministic tie-breaking ensures unit tests and offline `NDCG@3` benchmarks are 100% reproducible.
- **Alternatives considered**:
  - Hard-excluding dishes over `max_budget` in Personalized Recommendations: rejected for personalized feed (soft decay preserves discoverability when a dish is 2,000 VND over budget with `-70%` discount), whereas Conversational Semantic Search enforces explicit query `max_price` (e.g., *"dưới 30k"*) strictly!

---

## Decision 5: Layer 3 Async Gemini 2.5 Flash Justification, Latency Budget, Faithfulness Guard & `< 300ms` Fallback

- **Decision**:
  - Use `google-genai==1.3.0` native async interface `await client.aio.models.generate_content(...)` behind an injectable `GeminiRecommendationClient` `Protocol` + `GoogleGenAIRecommendationAdapter` (mirroring AI-1's clean adapter pattern for zero-network unit/integration tests).
  - Read credentials strictly via `settings.gemini_key` (`GEMINI_TEST_API` by default, `GEMINI_DEMO_API` only when `GEMINI_USE_DEMO_KEY=True`). Add `GEMINI_RECOMMENDATION_TIMEOUT_SECONDS: float = Field(default=2.0, gt=0)` in `backend/app/core/config.py` so the Gemini call never breaches the **P95 < 2.5s** total SLA (leaving `~500ms` headroom for SQL + scoring + serialization).
  - Send **1 single batched Gemini call** for all Top-K dishes (instead of 3 sequential RPCs!) using `response_mime_type="application/json"`, `response_schema=RecommendationJustificationBatch`, `temperature=0.3`.
  - Pass ONLY Top-K SQL-safe dish facts (`dish_id`, `dish_name`, `store_name`, `distance_meters`, `current_price`, `original_price`, `discount_percent`, `remaining_quantity`, `pickup_end_time`, `is_urgent_deal`) + non-PII taste summary (`preferred_categories`, `dietary_preference`, `max_budget`, `excluded_allergen_labels`).
  - **Server-Side Faithfulness Guard (`_is_justification_faithful`)**:
    1. Word count check: whitespace-split length MUST be within `[15, 35]` words (prompt explicitly targets strictly `20–30` words; offline eval checks strict `20–30` word compliance and `0%` fabricated numbers).
    2. Numeric grounding check: extract numbers representing prices (`18.000đ` / `18k` / `18000`), discount percentages (`67%`), distances (`350m` / `0.35km`), stock counts (`còn 2 phần`), and closing times (`13:30`) and verify every extracted figure matches the dish's authoritative DB fact (within standard rounding tolerance, e.g. `350.4m` ↔ `350m` or `0.4km`). Any invented number fails the check!
    3. Safety wording check: reject banned medical-guarantee phrases (`"đảm bảo y tế"`, `"chắc chắn 100% an toàn y tế"`) and reject mentioning an excluded allergen that is NOT in the user's `excluded_allergens`.
  - **Deterministic Template Fallback (`_build_fallback_justification`)**:
    - Triggered cleanly per-dish (or across the whole batch) when `gemini_client is None`, `TimeoutError`, SDK/network/quota error, schema error, or faithfulness rejection occurs.
    - Generates a natural 20–26 word Vietnamese sentence strictly from DB facts (e.g., *"Cách 350m tại Quán Phở Bắc, Phở gà ta đang giảm 67% chỉ còn 18.000đ (còn 2 suất đến 13:30), hợp khẩu vị và đã qua bộ lọc dị ứng của bạn."*), returning `200 OK` in `< 300ms` with `justification_source="FALLBACK"`.
- **Rationale**: Batching Top-3 into one async call cuts latency by ~3x compared to per-dish calls; the faithfulness validator guarantees `0%` fabricated numbers; and instant fallback guarantees `200 OK` availability even without a Gemini key or during upstream outages.

---

## Decision 6: Conversational Semantic Search (`POST /api/v1/dishes/search-semantic`), Fail-Closed Optional Auth & Regex Fallback

- **Decision**:
  - Expose `POST /api/v1/dishes/search-semantic` in `backend/app/api/v1/endpoints/recommendations.py` accepting `SemanticSearchRequest(query, latitude, longitude, radius_km=3.0, limit=10)`.
  - **Fail-Closed Optional Authentication (`get_optional_current_user` in `backend/app/api/deps.py`)**:
    - Uses `OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)`.
    - If `token is None` (no `Authorization` header): returns `None` (public/anonymous visitor).
    - If `token is not None`: delegates to full JWT verification + active-user check, raising **`401 Unauthorized`** if expired/malformed/inactive—NEVER silently downgrading an allergic authenticated consumer into an unfiltered anonymous search!
  - **Intent Extraction (`SemanticSearchIntent`)**:
    - Calls Gemini 2.5 Flash Structured Output (`temperature=0.0`, bounded by `GEMINI_RECOMMENDATION_TIMEOUT_SECONDS`) to extract: `max_price: int | None`, `categories: list[ItemCategory]`, `dietary: DietaryPreference | None`, `query_excluded_allergens: list[EUAllergen]`, `keywords: list[str]`, `urgent_only: bool`.
    - On Gemini unavailability/timeout/validation error, runs a deterministic Vietnamese rule-based fallback parser (`_extract_intent_fallback`) supporting budget patterns (`dưới 30k`, `<= 25 cành`, `tầm 40 nghìn`, `30.000đ`), category triggers (`phở/bún/mì/hủ tiếu/súp/món nước` → `NOODLES`; `cơm` → `RICE`; `bánh mì/bánh ngọt/croissant` → `BAKERY`; `trà sữa/cà phê/đồ uống` → `BEVERAGE`; `chay` → `VEGETARIAN`), dietary triggers (`thuần chay/vegan` → `VEGAN`; `chay` → `VEGETARIAN`), explicit query negation (`không đậu phộng`, `không hải sản`, `không sữa`, `không trứng`, `không gluten`), and urgency triggers (`giờ chót`, `giảm sâu`, `gấp`).
  - **Mandatory Layer 1 SQL Safety Routing**:
    - Combines `effective_allergens = union(user_pref.excluded_allergens, intent.query_excluded_allergens)` and `effective_dietary = stricter(user_pref.dietary_preference, intent.dietary)`.
    - Calls `recommendation_repo.fetch_safe_candidates(...)` with `effective_allergens`, `effective_dietary`, and `categories=intent.categories` (when non-empty).
    - Filters `max_price` using authoritative `DishService.calculate_time_shifted_discount` (so a 50k dish currently in `-70%` rush at 15k satisfies *"dưới 30k"*!).
    - If `intent.urgent_only` is `True`, prioritizes urgent deals (`is_urgent_deal == True`), and ranks matches combining keyword match overlap (`0.35`) with Layer 2 rescue score (`0.65`) so natural phrases like *"món súp ấm áp"* cleanly surface `"Phở Bò"` / `"Phở Gà"` in `NOODLES` without zero-result failures on non-literal adjectives.
- **Rationale**: Protects allergic consumers across both discovery surfaces, keeps semantic search resilient even offline, and handles colloquial Vietnamese budget/dish phrasing accurately.

---

## Decision 7: Router Ordering, Optional Redis Caching & Schema Migration Impact

- **Decision**:
  - Register `recommendations.router` **before** `stores.router` in `backend/app/api/v1/router.py` (just like `gamification.router`) so `stores.router`'s legacy root wildcard `GET /{store_id}` never interferes with route matching.
  - Keep database schema **migration-free** for functional delivery: `user_preferences`, `dishes`, `stores`, `menu_items`, and `orders` already exist in `8793a9fe3601_initial_schema_ecobite_12_tables.py`. Document optional PostgreSQL `GIN` index creation (`idx_dishes_allergens_gin`, `idx_user_pref_allergens_gin`) as a production performance tuning note in `data-model.md`.
  - Allow optional short-TTL (`60s`) Redis caching for identical Layer 3 Gemini justifications/intents via `app.core.redis.get_redis()` with silent degrade on `RedisError` — cache key MUST include a SHA-256 hash of `(sorted_dish_ids, prices, distances, stock, normalized_excluded_allergens, dietary_preference)` so cached text is never stale or cross-user contaminated.
- **Rationale**: Zero migration risk across team branches during Sprint 5 while keeping production PostgreSQL optimization clear.

---

## Decision 8: Offline Evaluation Harness (`ml/eval/`) & QA Safety Invariant Suite (`EC5-06`)

- **Decision**:
  - Build `ml/eval/golden_ai2_dataset.json` (15–20 Vietnamese scenarios: 10–12 Personalized Recommendation personas + 6–8 Conversational Semantic Search queries) and `ml/eval/eval_ai2_recommendation.py` (reusing `RecommendationRepository` & `RecommendationService` against an ephemeral in-memory SQLite DB seeded per scenario — zero heavy training packages added to `backend/requirements.txt`, Guardrail #8).
  - Compute all 5 Week-6 KPIs automatically:
    1. `allergen_leakage_rate` (strict **`0.0%`**)
    2. `ndcg_at_3` (target **`>= 0.85`**) & `precision_at_3`
    3. `semantic_intent_accuracy` (target **`>= 90%`**)
    4. `justification_faithfulness_rate` (target **`>= 95%`**, **`0%`** fabricated numbers, word count `20–30`)
    5. `latency_p95_ms` (`< 2500 ms`) & `fallback_latency_p95_ms` (`< 300 ms`) + Gemini token/cost summary.
  - Pair offline evaluation with Tony's automated QA suite (`EC5-06`):
    - `backend/tests/integration/test_allergen_invariant.py` (including Hypothesis property-based subset fuzzing over the 14 `EUAllergen` values + Vietnamese diacritic/synonym variants proving `0.0%` leakage on both `GET /recommendations/personalized` and `POST /dishes/search-semantic`).
    - `backend/tests/integration/test_api_recommendations.py` (full API contract, RBAC, fail-closed `401`, fallback `< 300ms` SLA, and cold-start / empty-safe-set verification).
    - `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md` (PA5 safety matrix, SLA benchmarks, and `>= 80%` project coverage plan).
- **Rationale**: Delivers objective, reproducible proof for Sprint 5 Kickoff and final PA5 Release 1.0 acceptance.
