# API Contracts: AI Feature 1 — Batch Quick-Post Multimodal Assistant

**Feature**: `002-ai-quick-post-nlp` | **Base Path**: `/api/v1` | **Date**: 2026-11-28

---

## 1. Parse Surplus Dishes via Voice or Text (Multimodal Quick-Post)

- **Method & Path**: `POST /api/v1/ml/parse-dish-nlp`
- **Router Module**: `backend/app/api/v1/endpoints/ml.py` (registered at `prefix="/ml"`, `tags=["ML"]` in `backend/app/api/v1/router.py`)
- **Authorization**:
  - `Authorization: Bearer <jwt_access_token>` (required)
  - Role MUST be `STORE_PARTNER` via `Depends(require_roles(UserRole.STORE_PARTNER))`
  - Partner MUST own a store with `kyc_status == APPROVED`
- **Content-Type**: `multipart/form-data`

### Request Form Parameters

| Parameter | Type | Required | Validation Rules |
| :--- | :--- | :---: | :--- |
| `audio_file` | binary file (`UploadFile`) | Conditional* | Supported formats: `.m4a`, `.mp3`, `.wav`, `.webm` (`audio/mp4`, `audio/m4a`, `audio/x-m4a`, `audio/mpeg`, `audio/mp3`, `audio/wav`, `audio/x-wav`, `audio/webm`; codec suffixes like `;codecs=opus` stripped before checking). Size MUST be `> 0` bytes and `<= 10 MB` (`10_485_760` bytes). |
| `raw_text` | `string` | Conditional* | Vietnamese free-text surplus description (trimmed). |
| `current_server_time` | `string` | No | Optional backwards-compatibility parameter; server ALWAYS uses authoritative `Asia/Ho_Chi_Minh` server clock (Constitution Principle VI). |

*\*At least one of `audio_file` or non-blank `raw_text` MUST be provided.*

### Success Response — `200 OK` (`QuickPostExtractionResponse`)

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
    },
    {
      "matched_menu_id": "b5c6d7e8-2222-4444-8888-1234567890ab",
      "dish_name": "Bún thịt nướng",
      "quantity": 3,
      "original_price": 40000.0,
      "override_discounted_price": 20000.0,
      "side_components": ["đồ chua"],
      "allergens": [
        {
          "allergen": "Peanuts (Đậu phộng)",
          "risk_level": "HIGH",
          "source": "EXPLICIT",
          "reason": "Chủ quán nêu rõ có đậu phộng rang"
        },
        {
          "allergen": "Fish (Cá/Nước mắm)",
          "risk_level": "HIGH",
          "source": "INFERRED",
          "reason": "Nước mắm pha ăn kèm từ cá"
        }
      ],
      "dietary_notes": ["Có đậu phộng"],
      "missing_fields_warning": []
    }
  ]
}
```

### Error Responses

| HTTP Status | Trigger Condition | Example Response `detail` |
| :---: | :--- | :--- |
| `401 Unauthorized` | Missing, expired, or invalid JWT Bearer token | `"Could not validate credentials"` |
| `403 Forbidden` | Authenticated user role is not `STORE_PARTNER` (`CONSUMER` / `ADMIN`) | `"The user does not have the required role"` |
| `403 Forbidden` | Store partner's store KYC status is `PENDING` or `REJECTED` | `"Cửa hàng chưa được duyệt chứng nhận ATVSTP (KYC) để sử dụng Quick-Post"` |
| `404 Not Found` | Store partner has not onboarded a store yet | `"Không tìm thấy cửa hàng thuộc tài khoản đối tác này"` |
| `413 Request Entity Too Large` | Uploaded `audio_file` exceeds `10 MB` (`10_485_760` bytes) | `"File âm thanh vượt quá giới hạn tối đa 10 MB"` |
| `415 Unsupported Media Type` | Uploaded `audio_file` MIME type / extension not in `.m4a`, `.mp3`, `.wav`, `.webm` | `"Định dạng âm thanh không được hỗ trợ. Chỉ chấp nhận: .m4a, .mp3, .wav, .webm"` |
| `422 Unprocessable Entity` | Neither `audio_file` nor non-blank `raw_text` provided, or `audio_file` is 0 bytes | `"Vui lòng cung cấp file ghi âm hoặc nội dung văn bản mô tả món ăn"` |
| `503 Service Unavailable` | Gemini API key missing, upstream timeout (`> GEMINI_TIMEOUT_SECONDS`), rate limit/network failure, or malformed AI schema / invalid pickup range | `"Dịch vụ AI Quick-Post hiện tạm gián đoạn. Vui lòng thử lại sau hoặc nhập món thủ công."` |

---

## 2. Removed Prototype Endpoints (Cleanup)

The following Week-5 prototype routes in `backend/app/api/v1/endpoints/quick_post.py` are **removed** and replaced by `POST /api/v1/ml/parse-dish-nlp`:
- `POST /api/v1/quick-post/extract` *(wrong path, wrong `CONSUMER` role, wrongly filtered partner dishes)*
- `GET /api/v1/quick-post/allergen-filter/test` *(unauthenticated dev-only test route)*

---

## 3. Downstream Handoff Contract: 1-Tap Batch Publish (Existing)

After the Store Partner reviews the drafts returned by `POST /api/v1/ml/parse-dish-nlp` (confirming `matched_menu_id` and reviewing `EXPLICIT`/`INFERRED` allergen badges), the client submits directly to the existing PA4 endpoint:

- **Method & Path**: `POST /api/v1/dishes/batch` (`backend/app/api/v1/endpoints/dishes.py`)
- **Payload (`DishBatchPublish`)**:
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
- **Expected Response**: `201 Created` with `{"created_count": ..., "dishes": [...]}`.
