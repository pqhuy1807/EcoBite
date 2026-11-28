# API Contracts: AI Frontend Experience Suite, AI Safety QA & Release 1.0 Go-Live

**Feature**: `007-ai-frontend-suite-and-golive` | **Base Path**: `/api/v1` | **Date**: 2026-11-28

This document freezes the exact REST contracts consumed by the Sprint 5 Frontend (`EC5-04`, `EC5-05`) via `@/lib/api-client` and verified by the AI Safety, Resilience & SLA QA Suite (`EC5-06`). Backend implementations live in `EC5-01` (`specs/002-ai-quick-post-nlp`), `EC5-02`, and `EC5-03`.

---

## 1. Store Partner Multimodal Quick-Post (`EC5-04` ↔ `EC5-01`)

### 1.1 Extract Surplus Dish Drafts from Voice or Text
- **Method & Path**: `POST /api/v1/ml/parse-dish-nlp`
- **Frontend Service**: `frontend/src/services/ml.service.ts::parseDishNlp(payload)` (`timeout: 20000` ms)
- **Authorization**: `Bearer <jwt>` — Role `STORE_PARTNER` with store `kyc_status === "APPROVED"`
- **Content-Type**: `multipart/form-data` (browser sets boundary automatically via `FormData`)

#### Request Form Fields
| Field | Type | Required | Constraints |
| :--- | :--- | :---: | :--- |
| `audio_file` | `Blob \| File` | Conditional* | Supported formats: `.webm` (`audio/webm;codecs=opus` / `audio/webm`), `.m4a` (`audio/mp4` / `audio/m4a`), `.mp3`, `.wav`. Size `> 0` and `<= 10 MB` (`10_485_760` bytes). |
| `raw_text` | `string` | Conditional* | Trimmed Vietnamese surplus description (used in text fallback or alongside audio). |

*\*At least one of `audio_file` or non-blank `raw_text` MUST be sent.*

#### Success Response — `200 OK` (`QuickPostExtractionResponse`)
```json
{
  "pickup_start": "13:55:00",
  "pickup_end": "15:00:00",
  "items": [
    {
      "matched_menu_id": "m1a2b3c4-1111-4444-8888-1234567890ab",
      "dish_name": "Cơm sườn bì chả",
      "quantity": 5,
      "original_price": 45000.0,
      "override_discounted_price": null,
      "side_components": ["mỡ hành", "dưa chua"],
      "allergens": [
        {
          "allergen": "Eggs (Trứng)",
          "risk_level": "HIGH",
          "source": "INFERRED",
          "reason": "Chả chưng truyền thống có chứa trứng"
        },
        {
          "allergen": "Fish (Cá/Nước mắm)",
          "risk_level": "HIGH",
          "source": "INFERRED",
          "reason": "Nước mắm ăn kèm làm từ cá"
        }
      ],
      "dietary_notes": ["Có mỡ hành (Allium)", "Có dưa chua"],
      "missing_fields_warning": []
    }
  ]
}
```

#### Frontend Error & Degradation Handling Matrix
| HTTP Status | Trigger | Required Frontend Behavior |
| :---: | :--- | :--- |
| `401` / `403` | Expired token, wrong role, or unapproved store KYC | Refresh token (401) or display KYC/role guidance toast. |
| `413` | Audio `> 10 MB` | Display Vietnamese size-limit alert (`<= 10 MB`); keep form open. |
| `415` | Unsupported audio format | Display accepted formats (`.webm`, `.m4a`, `.mp3`, `.wav`). |
| `422` | Empty audio and blank text | Highlight required input prompt without calling API if caught client-side. |
| `503` / Timeout | Gemini unavailable, timeout (`> 15s`), or malformed schema | Display non-blocking banner *"Trợ lý AI tạm gián đoạn"*, preserve `raw_text`, and offer 1-click switch to the manual dish publishing form on `/store/dishes`. |

### 1.2 1-Tap Batch Publish Reviewed Draft Cards (Existing PA4 Endpoint)
- **Method & Path**: `POST /api/v1/dishes/batch`
- **Frontend Service**: `frontend/src/services/dish.service.ts::batchCreateSurplusDishes(payload)`
- **Authorization**: `Bearer <jwt>` — Role `STORE_PARTNER` (`APPROVED` KYC)
- **Request Body (`DishBatchPublishPayload`)**:
  ```json
  {
    "pickup_start_time": "13:55:00",
    "pickup_end_time": "15:00:00",
    "dishes": [
      {
        "menu_item_id": "m1a2b3c4-1111-4444-8888-1234567890ab",
        "quantity": 5,
        "override_discounted_price": null,
        "allergens": [
          {
            "allergen": "Eggs (Trứng)",
            "risk_level": "HIGH",
            "source": "INFERRED",
            "reason": "Chả chưng truyền thống có chứa trứng"
          }
        ],
        "dietary_notes": ["Có mỡ hành (Allium)", "Có dưa chua"]
      }
    ]
  }
  ```
- **Success Response — `201 Created`**: `{"created_count": 1, "dishes": [...]}`.

---

## 2. Consumer Allergen & Taste Preferences (`EC5-05` ↔ `EC5-02`)

### 2.1 Get Current Consumer Preferences
- **Method & Path**: `GET /api/v1/users/me/preferences`
- **Frontend Service**: `frontend/src/services/preference.service.ts::getMyPreferences()`
- **Authorization**: `Bearer <jwt>` — Authenticated `CONSUMER`
- **Success Response — `200 OK` (`UserPreferenceResponse`)**:
  ```json
  {
    "id": "9f2a1b3c-1111-4444-8888-1234567890ab",
    "user_id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
    "preferred_categories": ["NOODLES", "VEGETARIAN"],
    "dietary_preference": "NONE",
    "excluded_allergens": ["Peanuts (Đậu phộng)", "Crustaceans (Tôm/Cua)"],
    "max_budget": 35000.0,
    "updated_at": "2026-11-28T08:00:00Z"
  }
  ```
  *(If no preference row exists yet, backend returns initialized defaults with empty arrays, `dietary_preference: "NONE"`, and `max_budget: null`.)*

### 2.2 Update Current Consumer Preferences
- **Method & Path**: `PUT /api/v1/users/me/preferences`
- **Frontend Service**: `frontend/src/services/preference.service.ts::updateMyPreferences(payload)`
- **Authorization**: `Bearer <jwt>` — Authenticated `CONSUMER`
- **Request Body (`UserPreferenceUpdatePayload`)**:
  ```json
  {
    "preferred_categories": ["NOODLES", "RICE"],
    "dietary_preference": "VEGETARIAN",
    "excluded_allergens": ["Peanuts (Đậu phộng)", "Fish (Cá/Nước mắm)"],
    "max_budget": 30000
  }
  ```
- **Success Response — `200 OK`**: Updated `UserPreferenceResponse`.
- **Error Responses**: `401 Unauthorized`, `403 Forbidden` (non-consumer), `422 Unprocessable Entity` (negative `max_budget` or invalid `dietary_preference`).
- **Required Client Post-Action**: Immediately invalidate React Query keys `['preferences', 'me']`, `['recommendations']`, and `['semantic-search']`.

---

## 3. Consumer Personalized Smart Recommendations (`EC5-05` ↔ `EC5-03`)

- **Method & Path**: `GET /api/v1/recommendations/personalized`
- **Frontend Service**: `frontend/src/services/recommendation.service.ts::getPersonalized(params)`
- **Authorization**: `Bearer <jwt>` — Role `CONSUMER`
- **Query Parameters**:
  - `lat` (`number`, required): Consumer latitude (`-90..90`)
  - `lng` (`number`, required): Consumer longitude (`-180..180`)
  - `radius_km` (`number`, optional, default `3.0`, range `1.0..10.0`)
  - `limit` (`integer`, optional, default `3`, range `1..10`)
- **Success Response — `200 OK`**:
  ```json
  {
    "recommendations": [
      {
        "dish_id": "d7a1b3c9-1111-4444-8888-1234567890ab",
        "dish_name": "Phở gà ta đùi xé",
        "store_id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
        "store_name": "Quán Phở Bắc 1985",
        "store_address": "45 Lê Lợi, Quận 1, TP.HCM",
        "latitude": 10.7751,
        "longitude": 106.7012,
        "image_url": "https://cdn.ecobite.vn/menu/pho_ga.jpg",
        "category": "NOODLES",
        "distance_meters": 350.0,
        "current_price": 18000.0,
        "original_price": 55000.0,
        "discount_percent": 67,
        "is_urgent_deal": true,
        "remaining_quantity": 2,
        "pickup_window": "12:30 - 13:30",
        "allergens": [],
        "ai_justification": "Gợi ý cho bạn: Bạn thích món nước nóng buổi trưa. Phở Bắc cách 350m giảm 67% còn 18.000đ, còn 2 phần đến 13:30 — hoàn toàn không đậu phộng!"
      }
    ],
    "is_fallback": false
  }
  ```
- **Safety & Resilience Invariants (`EC5-06`)**:
  - **0.0% Allergen Leakage**: Layer 1 SQL Hard Filter strictly excludes 100% of dishes matching `UserPreference.excluded_allergens` before Layer 2 Heuristic Scoring and Layer 3 Gemini Justification.
  - **Zero `500` on AI Fault**: If Gemini times out, errors, or lacks a key, endpoint MUST still return `200 OK` with the identical safe SQL-filtered Top 3 dishes and deterministic Vietnamese template `ai_justification` (`is_fallback: true`) within `< 300ms`.

---

## 4. Consumer Conversational Semantic Search (`EC5-05` ↔ `EC5-03`)

- **Method & Path**: `POST /api/v1/dishes/search-semantic`
- **Frontend Service**: `frontend/src/services/recommendation.service.ts::searchSemantic(payload)`
- **Authorization**: Optional `Bearer <jwt>` (Public access allowed for guest exploration; when authenticated as `CONSUMER`, backend MUST automatically enforce the user's `UserPreference.excluded_allergens` at SQL Layer 1 in addition to any query-mentioned exclusions).
- **Request Body (`SemanticSearchRequest`)**:
  ```json
  {
    "query": "Món nước nóng dưới 30k gần đây không đậu phộng",
    "latitude": 10.7769,
    "longitude": 106.7009,
    "radius_km": 5.0
  }
  ```
- **Success Response — `200 OK` (`SemanticSearchResponse`)**:
  ```json
  {
    "query": "Món nước nóng dưới 30k gần đây không đậu phộng",
    "parsed_intent": {
      "max_price": 30000.0,
      "categories": ["NOODLES"],
      "dietary_preference": null,
      "excluded_allergens": ["Peanuts (Đậu phộng)"],
      "keywords": ["nước", "nóng"]
    },
    "total": 1,
    "is_fallback": false,
    "results": [
      {
        "dish_id": "d7a1b3c9-1111-4444-8888-1234567890ab",
        "dish_name": "Phở gà ta đùi xé",
        "store_id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
        "store_name": "Quán Phở Bắc 1985",
        "store_address": "45 Lê Lợi, Quận 1, TP.HCM",
        "latitude": 10.7751,
        "longitude": 106.7012,
        "image_url": "https://cdn.ecobite.vn/menu/pho_ga.jpg",
        "category": "NOODLES",
        "distance_meters": 350.0,
        "current_price": 18000.0,
        "original_price": 55000.0,
        "discount_percent": 67,
        "is_urgent_deal": true,
        "remaining_quantity": 2,
        "pickup_window": "12:30 - 13:30",
        "allergens": [],
        "ai_justification": "Phở nóng 18.000đ dưới ngân sách 30k, cách 350m, không chứa đậu phộng."
      }
    ]
  }
  ```
- **Error & Resilience Matrix (`EC5-06`)**:
  - `422 Unprocessable Entity`: Blank query (`< 2` chars) or invalid coordinates (`lat` outside `-90..90`, `lng` outside `-180..180`).
  - **AI Fault Fallback**: If Gemini fails/times out, backend executes deterministic keyword + SQL Allergen Hard Filter fallback and returns `200 OK` (`is_fallback: true`) — never `500`.

---

## 5. Health & Container Readiness Endpoints (`EC5-07`)

- **Backend Healthcheck**: `GET http://127.0.0.1:8000/health` → `200 OK` (`{"status": "ok"}`) used by `docker-compose.yml` `backend` healthcheck before `frontend` starts.
- **Frontend Readiness**: `GET http://127.0.0.1:3000/` → `200 OK` HTML response verifying Next.js production server readiness in Docker Compose UAT.
