# Data Model: AI Feature 2 — Smart Food Recommendation & Conversational Semantic Search

**Feature**: `006-ai-smart-recommendation-search` | **Date**: 2026-11-28 | **Spec**: [spec.md](./spec.md)

AI Feature 2 reuses the existing 12-table EcoBite schema migrated in `backend/alembic/versions/8793a9fe3601_initial_schema_ecobite_12_tables.py` — **no new tables or breaking Alembic migrations are required**. It persists consumer profiles in `user_preferences`, queries `dishes` joined with `stores` and `menu_items` using SQL-level allergen exclusion, reads completed `orders` for taste affinity, and introduces strongly typed Pydantic v2 schemas in `backend/app/schemas/recommendation.py`.

---

## 1. Existing Persistent Entities

### `UserPreference` (`backend/app/models/user.py` — Read & Write via `preference_repo.py`)
- **Table**: `user_preferences` (1-to-1 with `users.id`, `ON DELETE CASCADE`, `UNIQUE(user_id)`)
- **Columns**:
  | Column | ORM Type | Constraints & AI-2 Semantics |
  | :--- | :--- | :--- |
  | `id` | `Mapped[uuid.UUID]` | Primary Key |
  | `user_id` | `Mapped[uuid.UUID]` | `FK -> users.id`, `UNIQUE`, `NOT NULL`, indexed |
  | `preferred_categories` | `Mapped[list[str]]` (`JSON_TYPE`) | Default `[]`. Validated against `ItemCategory` values (`RICE`, `NOODLES`, `BAKERY`, `BEVERAGE`, `VEGETARIAN`, `OTHER`) on write. |
  | `dietary_preference` | `Mapped[DietaryPreference]` | `NONE`, `VEGAN`, `VEGETARIAN` (default `NONE`). Enforced in Layer 1 SQL (`VEGAN` → only `VEGAN`; `VEGETARIAN` → `VEGAN` or `VEGETARIAN`). |
  | `excluded_allergens` | `Mapped[list[str]]` (`JSON_TYPE`) | Default `[]`. **Guardrail #7 Hard Filter Source**: normalized on write (`PUT /users/me/preferences`) to canonical `EUAllergen` values, and re-normalized/expanded on read in `recommendation_repo.py` for backward compatibility with seeded/legacy rows. |
  | `max_budget` | `Mapped[Decimal \| None]` | `Numeric(12, 2)`, nullable, `>= 0`. Used as soft budget-fit signal in Layer 2 scoring. |
  | `updated_at` | `Mapped[datetime]` | `DateTime(timezone=True)`, auto-updated on upsert. |

### `Dish` (`backend/app/models/dish.py` — Read-Only in Layer 1 & Layer 2)
- **Table**: `dishes`
- **Key columns queried in Layer 1 SQL**:
  - `id`, `store_id`, `menu_item_id` (nullable FK to `menu_items.id`)
  - `status: DishStatus` — MUST equal **`DishStatus.ACTIVE`** (excludes `SOLD_OUT`, `EXPIRED`, `INACTIVE`)
  - `remaining_quantity: int` — MUST be **`> 0`**
  - `pickup_start_time: time`, `pickup_end_time: time`, `rule_discount_start_time: time | None` — `pickup_end_time > current_time_vn` (`Asia/Ho_Chi_Minh`)
  - `original_price`, `rescue_price`, `rule_discount_price`, `override_discounted_price` — fed into `DishService.calculate_time_shifted_discount`
  - `category: ItemCategory`, `dietary_type: DietaryType` (`VEGAN`, `VEGETARIAN`, `NON_VEGAN`)
  - `name`, `description`, `image_url`, `ingredients`, `dietary_notes`
  - `allergens: list[dict[str, Any]]` (`JSON_TYPE`) — structured 2-tier warnings `[{allergen, risk_level, source: EXPLICIT|INFERRED, reason}]` (and defensively handled if legacy rows contain plain strings)

### `Store` (`backend/app/models/store.py` — Read-Only Join in Layer 1)
- **Key columns queried**:
  - `id`, `name`, `address`, `rating_avg`
  - `kyc_status: KycStatus` — MUST equal **`KycStatus.APPROVED`**
  - `location: LOCATION_TYPE` — PostGIS `Geometry(POINT, srid=4326)` on PostgreSQL (`ST_DWithin` / `ST_Distance`), WKT `String(255)` on SQLite (Haversine fallback)

### `MenuItem` (`backend/app/models/menu_item.py` — Read-Only `LEFT OUTER JOIN` in Layer 1)
- **Key columns queried**:
  - `id`, `base_allergens: list[str]` (`JSON_TYPE`) — inspected in SQL Layer 1 alongside `dishes.allergens` so dishes seeded or manually published without copying all base allergens into `dishes.allergens` still enforce **0.0% Allergen Leakage**.

### `Order` (`backend/app/models/order.py` — Read-Only in Layer 2)
- **Accessed via**: `OrderRepository(db).list_by_consumer(user_id, order_status=OrderStatus.COMPLETED, limit=20)`
- **Key fields read**: `dish.category`, `store_id` for optional Taste Profile historical affinity (`0.15` share of `S_taste_match`; neutral `0.5` for cold-start users).

### Production PostgreSQL Index Plan (Performance Note)
- Existing: `ix_stores_location`, `ix_dishes_store_id`, `ix_user_preferences_user_id`.
- Recommended optional non-breaking PostgreSQL tuning indexes (per `docs/03_Database_Schema_ERD.md` Section 3):
  - `CREATE INDEX IF NOT EXISTS idx_stores_location_gist ON stores USING GIST (location);`
  - `CREATE INDEX IF NOT EXISTS idx_dishes_allergens_gin ON dishes USING GIN (allergens);`
  - `CREATE INDEX IF NOT EXISTS idx_menu_items_base_allergens_gin ON menu_items USING GIN (base_allergens);`
  - `CREATE INDEX IF NOT EXISTS idx_dishes_status_category ON dishes (status, category);`

---

## 2. Canonical Allergen Normalization & SQL Token Expansion (`backend/app/core/allergens.py`)

All allergen exclusions are normalized to the 14 `EUAllergen` values from `backend/app/schemas/nlp.py`:

| Canonical `EUAllergen` Value | Accepted English / Vietnamese Synonyms (accented & unaccented) | Seeded / Legacy SQL Match Patterns |
| :--- | :--- | :--- |
| `Peanuts (Đậu phộng)` | `peanuts`, `peanut`, `đậu phộng`, `dau phong`, `lạc`, `lac`, `đậu lạc` | `peanuts%`, `%đậu phộng%`, `%Đậu phộng%`, `%Đậu Phộng%`, `%dau phong%`, `%lạc%` |
| `Soybeans (Đậu nành)` | `soybeans`, `soy`, `soya`, `đậu nành`, `dau nanh`, `đậu tương`, `đậu phụ`, `đậu hũ`, `nước tương` | `soybeans%`, `%đậu nành%`, `%Đậu nành%`, `%dau nanh%`, `%soy%` |
| `Eggs (Trứng)` | `eggs`, `egg`, `trứng`, `trung`, `trứng gà`, `trứng vịt`, `trứng muối` | `eggs%`, `%trứng%`, `%Trứng%`, `%trung%` |
| `Milk/Dairy (Sữa)` | `milk`, `dairy`, `milk/dairy`, `sữa`, `sua`, `bơ sữa`, `phô mai`, `kem sữa`, `lactose` | `milk%`, `%dairy%`, `%sữa%`, `%Sữa%` |
| `Fish (Cá/Nước mắm)` | `fish`, `cá`, `nước mắm`, `nuoc mam`, `mắm cá` *(also expanded by `hải sản`)* | `fish%`, `%nước mắm%`, `%Nước mắm%`, `%(cá%`, `%(Cá%`, `cá`, `Cá` |
| `Crustaceans (Tôm/Cua)` | `crustaceans`, `shellfish`, `shrimp`, `prawn`, `crab`, `tôm`, `tom`, `cua`, `ghẹ`, `giáp xác` *(also expanded by `hải sản`)* | `crustaceans%`, `%tôm%`, `%Tôm%`, `%cua%`, `%Cua%`, `%shellfish%` |
| `Molluscs (Nhuyễn thể: Nghêu/Sò/Ốc)` | `molluscs`, `mollusks`, `nhuyễn thể`, `nghêu`, `sò`, `ốc`, `mực`, `bạch tuộc`, `hàu` *(also expanded by `hải sản`)* | `molluscs%`, `%nhuyễn thể%`, `%nghêu%`, `%sò%`, `%Sò%`, `%ốc%`, `%mực%` |
| `Cereals containing gluten (Bột mì/Bánh mì)` | `gluten`, `wheat`, `cereals`, `bột mì`, `bot mi`, `lúa mì`, `bánh mì` | `%gluten%`, `%bột mì%`, `%Bột mì%`, `%lúa mì%` |
| `Tree nuts (Hạt cây: Điều, Hạnh nhân...)` | `tree nuts`, `nuts`, `hạt cây`, `quả hạch`, `hạt điều`, `hạnh nhân`, `óc chó`, `hạt dẻ` | `tree nuts%`, `nuts (%`, `%hạt cây%`, `%quả hạch%`, `%Quả hạch%`, `%hạnh nhân%`, `%hạt điều%` |
| `Sesame (Mè/Vừng)` | `sesame`, `mè`, `vừng`, `vung`, `hạt mè`, `mè đen`, `dầu mè` | `sesame%`, `%(mè%`, `%(Mè%`, `%vừng%`, `%mè đen%`, `mè`, `Mè` |
| `Celery (Cần tây)` | `celery`, `cần tây`, `can tay` | `celery%`, `%cần tây%`, `%Cần tây%` |
| `Mustard (Mù tạt)` | `mustard`, `mù tạt`, `mu tat` | `mustard%`, `%mù tạt%`, `%Mù tạt%` |
| `Sulphites (Chất bảo quản Sulfit)` | `sulphites`, `sulfites`, `sulfit`, `chất bảo quản sulfit` | `sulphites%`, `sulfites%`, `%sulfit%`, `%Sulfit%` |
| `Lupin (Đậu Lupin)` | `lupin`, `đậu lupin`, `dau lupin` | `lupin%`, `%lupin%`, `%Lupin%` |
| **Composite: `Hải sản` / `Seafood`** | `hải sản`, `hai san`, `seafood` | Expands to `[Crustaceans, Molluscs, Fish]` |

*Note*: Normalization strips accents via `.lower().replace("đ", "d")` followed by NFD combining-mark removal so Vietnamese `"đ"` is handled accurately. SQL patterns avoid overly short wildcards (e.g., never `"%ca%"` which would false-match `"can tay"` or `"cà phê"`).

---

## 3. Updated Preference Schemas (`backend/app/schemas/user_preference.py`)

- **`UserPreferenceCreate`** and **`UserPreferenceUpdate`**:
  - `preferred_categories`: validates every entry against `ItemCategory` (case-insensitive → uppercase, deduplicated). Rejects unknown category with `422`.
  - `excluded_allergens`: validates & normalizes every entry via `normalize_allergens(values, strict=True)` to deduplicated canonical `EUAllergen` strings. Rejects unrecognized strings with `422`.
  - `dietary_preference`: `DietaryPreference` (`NONE | VEGAN | VEGETARIAN`).
  - `max_budget`: `Decimal | None = Field(default=None, ge=0)`.
- **`UserPreferenceResponse`**:
  - Keeps existing fields (`id: uuid.UUID | None = None`, `user_id: uuid.UUID`, `preferred_categories`, `dietary_preference`, `excluded_allergens`, `max_budget`, `updated_at: datetime | None = None`, `is_default: bool = False`) with `ConfigDict(from_attributes=True)` so existing `test_cluster1_models.py` (`UserPreferenceResponse.model_validate(pref)`) passes unchanged AND `GET /users/me/preferences` can cleanly return a default response before the first `PUT` without mutating DB on `GET`.

---

## 4. New Recommendation & Semantic Search Schemas (`backend/app/schemas/recommendation.py`)

### `ScoreBreakdown`
| Field | Type | Constraints |
| :--- | :--- | :--- |
| `proximity_score` | `float` | `ge=0.0, le=1.0` (weight `0.40`) |
| `discount_urgency_score` | `float` | `ge=0.0, le=1.0` (weight `0.30`) |
| `taste_match_score` | `float` | `ge=0.0, le=1.0` (weight `0.30`) |
| `total_score` | `float` | `ge=0.0, le=1.0`, rounded to 4 decimals |

### `RecommendedDishItem`
| Field | Type | Constraints & Notes |
| :--- | :--- | :--- |
| `dish_id` | `UUID` | Safe active `Dish.id` |
| `store_id` | `UUID` | Approved `Store.id` |
| `dish_name` | `str` | Canonical dish name |
| `store_name` | `str` | Approved store name |
| `store_address` | `str` | Store address for pickup clarity |
| `category` | `ItemCategory` | Dish category |
| `dietary_type` | `DietaryType` | `VEGAN \| VEGETARIAN \| NON_VEGAN` |
| `image_url` | `str \| None` | Inherited high-res photo |
| `distance_meters` | `float` | Geodesic distance from user (`>= 0`) |
| `current_price` | `float` | Authoritative active price (`DishService`) |
| `original_price` | `float` | Retail original price |
| `discount_percent` | `int` | `0..100` integer discount percentage |
| `remaining_quantity` | `int` | `> 0` |
| `pickup_window` | `str` | Formatted `"HH:MM - HH:MM"` |
| `is_urgent_deal` | `bool` | `True` when in final rush (`<= 45` min or `-70%` rule active) |
| `allergens` | `list[dict[str, Any]]` | Transparent 2-tier allergen warnings (never containing any excluded allergen) |
| `dietary_notes` | `list[str]` | Cultural notes (`"Có mỡ hành"`, `"Thuần chay"`, etc.) |
| `score_breakdown` | `ScoreBreakdown` | Deterministic Layer 2 score components |
| `ai_justification` | `str` | Concise Vietnamese 20–30 word DB-grounded explanation |
| `justification_source` | `Literal["GEMINI", "FALLBACK"]` | Provenance indicator for observability & SLA verification |

### `PersonalizedRecommendationResponse`
| Field | Type | Notes |
| :--- | :--- | :--- |
| `total` | `int` | Count of returned recommendations (`0..limit`) |
| `radius_km` | `float` | Applied search radius (`1.0..10.0`) |
| `applied_excluded_allergens` | `list[str]` | Canonical `EUAllergen` list enforced in Layer 1 SQL |
| `applied_dietary_preference` | `DietaryPreference` | Dietary filter enforced in Layer 1 SQL |
| `recommendations` | `list[RecommendedDishItem]` | Ordered Top-K list (empty `[]` if no safe dishes exist) |

### `SemanticSearchRequest`
| Field | Type | Constraints |
| :--- | :--- | :--- |
| `query` | `str` | Trimmed, `min_length=2`, `max_length=300` |
| `latitude` | `float` | `ge=-90.0, le=90.0` |
| `longitude` | `float` | `ge=-180.0, le=180.0` |
| `radius_km` | `float` | Default `3.0`, `ge=1.0, le=10.0` |
| `limit` | `int` | Default `10`, `ge=1, le=30` |

### `SemanticSearchIntent` (Gemini Structured Output & Response Echo)
| Field | Type | Constraints & Notes |
| :--- | :--- | :--- |
| `max_price` | `int \| None` | Default `None`, `gt=0` when set (VND) |
| `categories` | `list[ItemCategory]` | Default `[]` |
| `dietary` | `DietaryPreference \| None` | Default `None` (`VEGAN` / `VEGETARIAN` when requested) |
| `query_excluded_allergens` | `list[EUAllergen]` | Default `[]` (unioned with user profile in SQL Layer 1) |
| `keywords` | `list[str]` | Default `[]` (semantic tokens for relevance boost) |
| `urgent_only` | `bool` | Default `False` |

### `SemanticSearchDishItem` & `SemanticSearchResponse`
- `SemanticSearchDishItem`: Same safe dish presentation fields as `RecommendedDishItem` (`dish_id`, `store_id`, `dish_name`, `store_name`, `store_address`, `category`, `dietary_type`, `image_url`, `distance_meters`, `current_price`, `original_price`, `discount_percent`, `remaining_quantity`, `pickup_window`, `is_urgent_deal`, `allergens`, `dietary_notes`, `relevance_score: float`).
- `SemanticSearchResponse`:
  - `query: str`
  - `parsed_intent: SemanticSearchIntent`
  - `intent_source: Literal["GEMINI", "FALLBACK"]`
  - `applied_excluded_allergens: list[str]` (canonical union of user profile + query exclusions enforced in SQL)
  - `applied_dietary_preference: DietaryPreference`
  - `total: int`
  - `results: list[SemanticSearchDishItem]`

### Internal Gemini Batch Justification Schema
- `DishJustificationItem(dish_id: UUID, ai_justification: str)`
- `RecommendationJustificationBatch(justifications: list[DishJustificationItem])`

---

## 5. Offline Golden Dataset Fixture Schema (`ml/eval/golden_ai2_dataset.json`)

Each scenario object in the 15–20 case dataset contains:
- `case_id: str` (e.g., `"AI2-REC-01"`, `"AI2-SEM-01"`)
- `mode: Literal["personalized", "semantic"]`
- `description: str`
- `reference_server_time: str` (ISO 8601 `+07:00`, e.g., `"2026-11-28T12:35:00+07:00"`)
- `user_location: {"lat": float, "lng": float, "radius_km": float}`
- `user_preference: {"preferred_categories": list[str], "dietary_preference": str, "excluded_allergens": list[str], "max_budget": int | None}`
- `completed_order_categories: list[str]` (optional order-history seed for affinity tests)
- `semantic_query: str | None` (populated for `mode == "semantic"`)
- `catalog: list[dict]` (stores + menu items + surplus dishes with GPS, pricing, pickup windows, `allergens`, `base_allergens`, `dietary_type`, `status`, `remaining_quantity`)
- `expected: dict`:
  - `forbidden_dish_keys: list[str]` (any dish containing an excluded allergen — MUST have `0` appearances!)
  - `ideal_ranking_relevance: dict[str, int]` (graded relevance `0..3` per dish key for computing `NDCG@3` & `Precision@3`)
  - `expected_intent: dict | None` (`max_price`, `categories`, `dietary`, `query_excluded_allergens` for semantic cases)
