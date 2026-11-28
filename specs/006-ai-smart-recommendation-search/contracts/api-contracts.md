# API Contracts: AI Feature 2 — Smart Food Recommendation & Conversational Semantic Search

**Feature**: `006-ai-smart-recommendation-search` | **Base Path**: `/api/v1` | **Date**: 2026-11-28

> **Router Registration Invariant**: `recommendations.router` MUST be registered **before** `stores.router` in `backend/app/api/v1/router.py` so `stores.router`'s legacy root-level wildcard `GET /{store_id}` never interferes with route matching.

---

## 1. Retrieve Current Consumer Preferences (`EC5-02`)

- **Method & Path**: `GET /api/v1/users/me/preferences`
- **Router Module**: `backend/app/api/v1/endpoints/users.py` (`prefix="/users"`, `tags=["users"]`)
- **Authorization**:
  - `Authorization: Bearer <jwt_access_token>` (required)
  - Role MUST be `CONSUMER` via `Depends(require_roles(UserRole.CONSUMER))`

### Success Response — `200 OK` (`UserPreferenceResponse`)

When the consumer has saved preferences:

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
  "preferred_categories": ["NOODLES", "RICE"],
  "dietary_preference": "NONE",
  "excluded_allergens": [
    "Peanuts (Đậu phộng)",
    "Crustaceans (Tôm/Cua)",
    "Molluscs (Nhuyễn thể: Nghêu/Sò/Ốc)",
    "Fish (Cá/Nước mắm)"
  ],
  "max_budget": "35000.00",
  "updated_at": "2026-11-28T12:10:00Z",
  "is_default": false
}
```

When the consumer has not yet saved preferences (read-only default, no DB write on `GET`):

```json
{
  "id": null,
  "user_id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
  "preferred_categories": [],
  "dietary_preference": "NONE",
  "excluded_allergens": [],
  "max_budget": null,
  "updated_at": null,
  "is_default": true
}
```

### Error Responses

| HTTP Status | Trigger Condition | Example Response `detail` |
| :---: | :--- | :--- |
| `401 Unauthorized` | Missing, expired, or invalid JWT Bearer token | `"Could not validate credentials"` |
| `403 Forbidden` | Authenticated user role is `STORE_PARTNER` or `ADMIN` | `"The user does not have the required role"` |

---

## 2. Create or Update Consumer Preferences (`EC5-02`)

- **Method & Path**: `PUT /api/v1/users/me/preferences`
- **Router Module**: `backend/app/api/v1/endpoints/users.py`
- **Authorization**:
  - `Authorization: Bearer <jwt_access_token>` (required)
  - Role MUST be `CONSUMER` via `Depends(require_roles(UserRole.CONSUMER))`
- **Content-Type**: `application/json`

### Request Body (`UserPreferenceUpdate`)

All fields are optional on update (omitted fields retain existing values or default cleanly on initial creation). Vietnamese synonyms, unaccented forms, and `"Hải sản"` are normalized and deduplicated to canonical `EUAllergen` values before persistence.

```json
{
  "preferred_categories": ["noodles", "RICE"],
  "dietary_preference": "NONE",
  "excluded_allergens": ["đậu phộng", "Hải sản"],
  "max_budget": 35000
}
```

### Success Response — `200 OK` (`UserPreferenceResponse`)

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
  "preferred_categories": ["NOODLES", "RICE"],
  "dietary_preference": "NONE",
  "excluded_allergens": [
    "Peanuts (Đậu phộng)",
    "Crustaceans (Tôm/Cua)",
    "Molluscs (Nhuyễn thể: Nghêu/Sò/Ốc)",
    "Fish (Cá/Nước mắm)"
  ],
  "max_budget": "35000.00",
  "updated_at": "2026-11-28T12:15:00Z",
  "is_default": false
}
```

### Error Responses

| HTTP Status | Trigger Condition | Example Response `detail` |
| :---: | :--- | :--- |
| `401 Unauthorized` | Missing, expired, or invalid JWT Bearer token | `"Could not validate credentials"` |
| `403 Forbidden` | Authenticated user role is not `CONSUMER` | `"The user does not have the required role"` |
| `422 Unprocessable Entity` | Unknown allergen string, invalid `ItemCategory`, invalid `DietaryPreference`, or `max_budget < 0` | `"Chất gây dị ứng không hợp lệ: 'xyz'. Vui lòng chọn trong 14 nhóm chuẩn EU FIC."` |

---

## 3. Personalized Smart Food Recommendations (`EC5-02` + `EC5-03`)

- **Method & Path**: `GET /api/v1/recommendations/personalized`
- **Router Module**: `backend/app/api/v1/endpoints/recommendations.py` (registered at root of `api_router` before `stores.router`, `tags=["Recommendations"]`)
- **Authorization**:
  - `Authorization: Bearer <jwt_access_token>` (required)
  - Role MUST be `CONSUMER` via `Depends(require_roles(UserRole.CONSUMER))`

### Query Parameters

| Parameter | Type | Required | Default | Validation Rules |
| :--- | :--- | :---: | :---: | :--- |
| `lat` | `float` | Yes | — | `ge=-90.0, le=90.0` |
| `lng` | `float` | Yes | — | `ge=-180.0, le=180.0` |
| `radius_km` | `float` | No | `3.0` | `ge=1.0, le=10.0` (consistent with `DiscoveryService`) |
| `limit` | `int` | No | `3` | `ge=1, le=10` |

### Execution Guarantees
1. **Layer 1 (SQL Hard Invariant — `0.0%` Leakage)**: Filters `Store.kyc_status == APPROVED`, `Dish.status == ACTIVE`, `Dish.remaining_quantity > 0`, `Dish.pickup_end_time > now_vn`, PostGIS `ST_DWithin(radius_km)` (SQLite Haversine parity), `dietary_preference`, and SQL `WHERE NOT EXISTS` across BOTH `dishes.allergens` and `menu_items.base_allergens`.
2. **Layer 2 (Deterministic Scoring)**: `Score = 0.40 * proximity + 0.30 * discount_urgency + 0.30 * taste_match` with deterministic tie-breaking.
3. **Layer 3 (Gemini 2.5 Flash + Faithfulness Guard + `< 300ms` Fallback)**: Always returns **`200 OK`** even when Gemini is unconfigured, times out (`> 2.0s`), or returns unfaithful numbers (`justification_source="FALLBACK"`). Returns `recommendations: []` (`total: 0`) if zero safe dishes exist in radius—NEVER relaxes allergen exclusions.

### Success Response — `200 OK` (`PersonalizedRecommendationResponse`)

```json
{
  "total": 1,
  "radius_km": 3.0,
  "applied_excluded_allergens": ["Peanuts (Đậu phộng)"],
  "applied_dietary_preference": "NONE",
  "recommendations": [
    {
      "dish_id": "d7a1b3c9-1111-4444-8888-1234567890ab",
      "store_id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
      "dish_name": "Phở gà ta đùi xé",
      "store_name": "Quán Phở Bắc 1985",
      "store_address": "123 Nguyễn Huệ, Quận 1, TP.HCM",
      "category": "NOODLES",
      "dietary_type": "NON_VEGAN",
      "image_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=600",
      "distance_meters": 350.0,
      "current_price": 18000.0,
      "original_price": 55000.0,
      "discount_percent": 67,
      "remaining_quantity": 2,
      "pickup_window": "12:00 - 13:30",
      "is_urgent_deal": true,
      "allergens": [
        {
          "allergen": "Fish (Cá/Nước mắm)",
          "risk_level": "LOW",
          "source": "INFERRED",
          "reason": "Nước dùng có nêm nước mắm truyền thống"
        }
      ],
      "dietary_notes": ["Nước dùng nóng hổi", "Nhiều hành ngò"],
      "score_breakdown": {
        "proximity_score": 0.8833,
        "discount_urgency_score": 0.9786,
        "taste_match_score": 0.825,
        "total_score": 0.8944
      },
      "ai_justification": "Cách 350m tại Quán Phở Bắc 1985, Phở gà ta đang giảm 67% còn 18.000đ, chỉ còn 2 suất đến 13:30, hợp gu món nước và bộ lọc dị ứng của bạn.",
      "justification_source": "GEMINI"
    }
  ]
}
```

### Error Responses

| HTTP Status | Trigger Condition | Example Response `detail` |
| :---: | :--- | :--- |
| `401 Unauthorized` | Missing, expired, or invalid JWT Bearer token | `"Could not validate credentials"` |
| `403 Forbidden` | Authenticated user role is not `CONSUMER` | `"The user does not have the required role"` |
| `422 Unprocessable Entity` | `lat`/`lng` missing or out of bounds, `radius_km` outside `[1.0, 10.0]`, or `limit` outside `[1, 10]` | FastAPI Pydantic validation detail |

---

## 4. Conversational Semantic Search (`EC5-03`)

- **Method & Path**: `POST /api/v1/dishes/search-semantic`
- **Router Module**: `backend/app/api/v1/endpoints/recommendations.py`
- **Authorization**:
  - **Public with Fail-Closed Optional Bearer JWT** (`Depends(get_optional_current_user)`):
    - **No `Authorization` header**: Allowed as public anonymous search (enforces query-stated exclusions & dietary constraints in Layer 1 SQL; returns all 2-tier allergen warnings transparently).
    - **Valid `Authorization: Bearer <token>`**: Automatically loads persisted `UserPreference.excluded_allergens` & `dietary_preference`, merges with query-stated constraints, and enforces 100% SQL Hard Filtering (`0.0%` leakage).
    - **Invalid / Expired `Authorization` header**: **MUST return `401 Unauthorized`** (fail-closed food-safety guard so an allergic user never silently degrades to an unfiltered anonymous search!).
- **Content-Type**: `application/json`

### Request Body (`SemanticSearchRequest`)

```json
{
  "query": "Tìm món nước nóng dưới 30k gần đây",
  "latitude": 10.7769,
  "longitude": 106.7009,
  "radius_km": 3.0,
  "limit": 10
}
```

### Success Response — `200 OK` (`SemanticSearchResponse`)

```json
{
  "query": "Tìm món nước nóng dưới 30k gần đây",
  "parsed_intent": {
    "max_price": 30000,
    "categories": ["NOODLES"],
    "dietary": null,
    "query_excluded_allergens": [],
    "keywords": ["món nước", "nóng", "súp", "phở", "bún"],
    "urgent_only": false
  },
  "intent_source": "GEMINI",
  "applied_excluded_allergens": ["Peanuts (Đậu phộng)"],
  "applied_dietary_preference": "NONE",
  "total": 1,
  "results": [
    {
      "dish_id": "d7a1b3c9-1111-4444-8888-1234567890ab",
      "store_id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
      "dish_name": "Phở gà ta đùi xé",
      "store_name": "Quán Phở Bắc 1985",
      "store_address": "123 Nguyễn Huệ, Quận 1, TP.HCM",
      "category": "NOODLES",
      "dietary_type": "NON_VEGAN",
      "image_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=600",
      "distance_meters": 350.0,
      "current_price": 18000.0,
      "original_price": 55000.0,
      "discount_percent": 67,
      "remaining_quantity": 2,
      "pickup_window": "12:00 - 13:30",
      "is_urgent_deal": true,
      "allergens": [
        {
          "allergen": "Fish (Cá/Nước mắm)",
          "risk_level": "LOW",
          "source": "INFERRED",
          "reason": "Nước dùng có nêm nước mắm truyền thống"
        }
      ],
      "dietary_notes": ["Nước dùng nóng hổi", "Nhiều hành ngò"],
      "relevance_score": 0.9125
    }
  ]
}
```

### Error Responses

| HTTP Status | Trigger Condition | Example Response `detail` |
| :---: | :--- | :--- |
| `401 Unauthorized` | `Authorization` header supplied, but JWT is malformed, expired, wrong token type, or user is inactive (fail-closed safety) | `"Could not validate credentials"` |
| `422 Unprocessable Entity` | Blank/`< 2` or `> 300` char `query`, invalid `latitude`/`longitude`, `radius_km` outside `[1.0, 10.0]`, or `limit` outside `[1, 30]` | FastAPI Pydantic validation detail |

---

## 5. Deprecation Note: Week-5 Python-Only Filter

- `backend/app/services/allergen_filter_service.py` (`AllergenHardFilterService`) is **deprecated for recommendation/search pipelines** and MUST NOT be used as the primary safety barrier (Guardrail #7). All allergen exclusion for `GET /api/v1/recommendations/personalized` and `POST /api/v1/dishes/search-semantic` executes directly inside SQL in `backend/app/repositories/recommendation_repo.py`.
