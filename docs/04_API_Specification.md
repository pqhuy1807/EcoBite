# EcoBite Platform - RESTful API Specification (v1)

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh
**Base URL**: `http://localhost:8000/api/v1`
**Authentication**: Bearer Token (`Authorization: Bearer <jwt_access_token>`)
**Format**: `application/json`
**Phiên bản**: 2.1.0 (Bổ sung Phân hệ AI Suite & Gợi ý Món ăn Thông minh Cá nhân hóa)

---

## 1. Xác thực & Quản lý Tài khoản (Authentication & Identity)

### 1.1. Đăng ký Tài khoản
- **Method & Path**: `POST /auth/register`
- **Quyền hạn (Role)**: Public
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "StrongPassword123!",
    "full_name": "Nguyễn Văn A",
    "phone": "0901234567",
    "role": "CONSUMER"  // "CONSUMER" | "STORE_PARTNER"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "a5e8c1b2-...",
    "email": "user@example.com",
    "full_name": "Nguyễn Văn A",
    "role": "CONSUMER",
    "green_points_balance": 0,
    "created_at": "2026-10-14T22:30:00Z"
  }
  ```

### 1.2. Đăng nhập Lấy JWT Token
- **Method & Path**: `POST /auth/login`
- **Quyền hạn**: Public
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "StrongPassword123!"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "a5e8c1b2-...",
      "email": "user@example.com",
      "role": "CONSUMER",
      "full_name": "Nguyễn Văn A"
    }
  }
  ```

---

## 2. Quản lý Đối tác & Admin Kiểm duyệt (Store KYC & Admin Review)

### 2.1. Đăng ký Thông tin Cửa hàng (Partner Onboarding)
- **Method & Path**: `POST /stores/onboard`
- **Quyền hạn**: `STORE_PARTNER`
- **Request Body**:
  ```json
  {
    "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
    "description": "Chuyên các món cơm văn phòng và bánh nướng tươi ngon trong ngày",
    "address": "123 Đường Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM",
    "latitude": 10.776889,
    "longitude": 106.700806,
    "phone": "02838123456",
    "avatar_url": "https://cdn.ecobite.vn/stores/avatar1.jpg",
    "kyc_license_url": "https://cdn.ecobite.vn/kyc/license1.pdf"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "e4f8d2a1-...",
    "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
    "kyc_status": "PENDING",
    "message": "Hồ sơ đối tác đã được gửi và đang chờ Admin kiểm duyệt."
  }
  ```

### 2.2. Admin Phê duyệt / Từ chối Cửa hàng
- **Method & Path**: `PATCH /admin/stores/{store_id}/review`
- **Quyền hạn**: `ADMIN`
- **Request Body**:
  ```json
  {
    "decision": "APPROVED",
    "reject_reason": null
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "store_id": "e4f8d2a1-...",
    "kyc_status": "APPROVED",
    "reviewed_at": "2026-10-14T22:35:00Z"
  }
  ```

---

## 3. Quản lý Món ăn Dư thừa (Dish Management)

### 3.1. Tạo Món ăn Dư thừa Mới (Dish Creation)
- **Method & Path**: `POST /dishes`
- **Quyền hạn**: `STORE_PARTNER` (Đã được duyệt KYC)
- **Request Body**:
  ```json
  {
    "name": "Cơm gà xối mỡ sốt cay",
    "description": "Đùi gà chiên xối mỡ giòn rụm, kèm dưa leo và canh súp trong ngày",
    "category": "RICE",
    "original_price": 45000.0,
    "rescue_price": 22000.0,
    "rule_discount_price": 15000.0,
    "pickup_start_time": "14:00:00",
    "pickup_end_time": "15:00:00",
    "rule_discount_start_time": "14:30:00",
    "total_quantity": 5,
    "image_url": "https://cdn.ecobite.vn/dishes/com_ga.jpg",
    "ingredients": ["cơm", "gà", "dưa leo", "sốt cay", "đậu phộng"],
    "allergens": ["Đậu phộng"],
    "dietary_type": "NON_VEGAN"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "d7a1b3c9-...",
    "name": "Cơm gà xối mỡ sốt cay",
    "remaining_quantity": 5,
    "status": "ACTIVE"
  }
  ```

### 3.2. Đăng Hàng loạt Món ăn Dư thừa (Batch Dish Publishing - 1-Tap Post)
Sau khi AI bóc tách danh sách món, chủ quán duyệt các Draft Cards và bấm "Đăng tất cả".
- **Method & Path**: `POST /dishes/batch`
- **Quyền hạn**: `STORE_PARTNER`
- **Request Body**:
  ```json
  {
    "pickup_start_time": "13:55:00",
    "pickup_end_time": "15:00:00",
    "dishes": [
      {
        "menu_item_id": "m1a2b3c4-...",
        "name": "Cơm sườn bì chả",
        "quantity": 5,
        "override_discounted_price": null,
        "allergens": [
          {"allergen": "Eggs (Trứng)", "risk_level": "HIGH", "source": "INFERRED", "reason": "Chả chưng có trứng"},
          {"allergen": "Fish (Cá/Nước mắm)", "risk_level": "HIGH", "source": "INFERRED", "reason": "Nước mắm từ cá"}
        ],
        "dietary_notes": ["Có mỡ hành (Allium)", "Có dưa chua"]
      },
      {
        "menu_item_id": "b5c6d7e8-...",
        "name": "Bún thịt nướng",
        "quantity": 3,
        "override_discounted_price": 20000.0,
        "allergens": [
          {"allergen": "Peanuts (Đậu phộng)", "risk_level": "HIGH", "source": "INFERRED", "reason": "Rắc đậu phộng rang"}
        ],
        "dietary_notes": ["Có hành phi", "Có đậu phộng"]
      }
    ]
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "created_count": 2,
    "dishes": [
      {"id": "d7a1...", "name": "Cơm sườn bì chả", "remaining_quantity": 5},
      {"id": "c2b3...", "name": "Bún thịt nướng", "remaining_quantity": 3}
    ]
  }
  ```

### 3.3. Quản lý Thực đơn Gốc của Quán (Base Menu Catalog)
- **Method & Path**: `GET /stores/{store_id}/menu-items` (Lấy danh mục món chuẩn) & `POST /stores/{store_id}/menu-items` (Thêm món vào menu gốc)
- **Quyền hạn**: `STORE_PARTNER`
- **Request Body (POST)**:
  ```json
  {
    "name": "Cơm sườn bì chả",
    "description": "Cơm tấm truyền thống sườn nướng mật ong, bì thơm và chả trứng",
    "category": "RICE",
    "original_price": 45000.0,
    "image_url": "https://cdn.ecobite.vn/menu/com_suon_bi_cha.jpg",
    "standard_ingredients": ["gạo tấm", "sườn heo", "bì", "chả trứng", "mỡ hành", "dưa chua", "nước mắm"],
    "base_allergens": ["Eggs (Trứng)", "Fish (Cá/Nước mắm)"],
    "dietary_type": "NON_VEGAN"
  }
  ```

### 3.4. Lấy Chi tiết Món ăn Dư thừa
- **Method & Path**: `GET /dishes/{dish_id}`
- **Quyền hạn**: Public
- **Response (200 OK)**:
  ```json
  {
    "id": "d7a1b3c9-...",
    "name": "Cơm gà xối mỡ sốt cay",
    "store_id": "e4f8d2a1-...",
    "store_name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
    "current_price": 22000.0,
    "original_price": 45000.0,
    "pickup_window": "14:00 - 15:00",
    "remaining_quantity": 5,
    "allergens": ["Đậu phộng"],
    "dietary_type": "NON_VEGAN"
  }
  ```

---

## 4. Phân hệ Trí tuệ Nhân tạo & Gợi ý Thông minh (AI Intelligence Suite)

### 4.1. Trợ lý AI Bóc tách Hàng loạt Món ăn & Cảnh báo Dị ứng 2 Tầng (Batch Quick-Post NLP)
Chủ quán gửi file ghi âm ngắn (Native Audio) hoặc văn bản tự do, AI sử dụng `gemini-2.5-flash` đối soát với Thực đơn gốc (`menu_items`) và thời gian thực của server để trả về danh sách các món ăn kèm cảnh báo an toàn thực phẩm.

- **Method & Path**: `POST /ml/parse-dish-nlp`
- **Quyền hạn**: `STORE_PARTNER`
- **Content-Type**: `multipart/form-data` HOẶC `application/json`
- **Request Parameters / Body**:
  - `audio_file`: *(Tùy chọn)* File ghi âm giọng nói định dạng `.m4a`, `.mp3`, `.wav`.
  - `raw_text`: *(Tùy chọn)* Văn bản tiếng Việt tự do (Ví dụ: *"Còn 5 cơm sườn bì chả, 3 bún thịt nướng xả từ giờ đến 3h chiều"*).
  - `current_server_time`: *(Tùy chọn, mặc định server tự lấy thời gian hiện tại)*: ISO 8601 (Ví dụ: `2026-10-16T13:55:00+07:00`).

- **Response (200 OK - Pydantic `QuickPostExtractionResponse`)**:
  ```json
  {
    "pickup_start": "13:55:00",
    "pickup_end": "15:00:00",
    "items": [
      {
        "matched_menu_id": "m1a2b3c4-...",
        "dish_name": "Cơm sườn bì chả",
        "quantity": 5,
        "original_price": 45000.0,
        "override_discounted_price": null,
        "side_components": ["mỡ hành", "dưa chua", "nước mắm"],
        "allergens": [
          {
            "allergen": "Eggs (Trứng)",
            "risk_level": "HIGH",
            "source": "INFERRED",
            "reason": "Chả chưng theo công thức truyền thống chứa trứng gà/vịt"
          },
          {
            "allergen": "Fish (Cá/Nước mắm)",
            "risk_level": "HIGH",
            "source": "INFERRED",
            "reason": "Nước mắm ăn kèm có nguồn gốc từ cá"
          },
          {
            "allergen": "Peanuts (Đậu phộng)",
            "risk_level": "HIGH",
            "source": "INFERRED",
            "reason": "Mỡ hành ăn kèm cơm tấm Sài Gòn thường có đậu phộng rang"
          }
        ],
        "dietary_notes": ["Có mỡ hành (Allium)", "Có dưa chua", "Không cay"],
        "missing_fields_warning": []
      },
      {
        "matched_menu_id": "b5c6d7e8-...",
        "dish_name": "Bún thịt nướng",
        "quantity": 3,
        "original_price": 40000.0,
        "override_discounted_price": 20000.0,
        "side_components": ["rau sống", "đậu phộng", "nước mắm chua ngọt"],
        "allergens": [
          {
            "allergen": "Peanuts (Đậu phộng)",
            "risk_level": "HIGH",
            "source": "INFERRED",
            "reason": "Bún thịt nướng rắc đậu phộng rang giã nhuyễn"
          },
          {
            "allergen": "Fish (Cá/Nước mắm)",
            "risk_level": "HIGH",
            "source": "INFERRED",
            "reason": "Nước mắm chua ngọt làm từ cá"
          }
        ],
        "dietary_notes": ["Có hành phi", "Có đậu phộng", "Có ớt"],
        "missing_fields_warning": []
      }
    ]
  }
  ```

### 4.2. Gợi ý Món ăn Thông minh Cá nhân hóa (AI Smart Personalized Recommendations)
Động cơ gợi ý Hybrid phân tích vị trí thực tế, thời điểm ăn uống, gu ẩm thực và gọi Gemini 2.5 Flash sinh lý do đề xuất.
- **Method & Path**: `GET /recommendations/personalized`
- **Quyền hạn**: `CONSUMER` (hoặc Public nếu chưa đăng nhập)
- **Query Parameters**:
  - `lat`: Tọa độ vĩ độ người dùng (Ví dụ: `10.7769`)
  - `lng`: Tọa độ kinh độ người dùng (Ví dụ: `106.7009`)
  - `limit`: Số lượng món gợi ý (Mặc định: `5`)
- **Response (200 OK)**:
  ```json
  {
    "total_recommendations": 3,
    "recommendations": [
      {
        "dish_id": "d7a1b3c9-...",
        "dish_name": "Cơm gà xối mỡ sốt cay",
        "store_name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
        "distance_meters": 320.0,
        "current_price": 22000.0,
        "original_price": 45000.0,
        "pickup_window": "14:00 - 15:00",
        "remaining": 4,
        "ai_match_score": 0.94,
        "is_urgent_deal": false,
        "ai_justification": "Món này rất hợp với bạn vì bạn thường thích ăn cơm vào bữa trưa, quán chỉ cách bạn 320m và có deal giảm 51% an toàn không chứa chất dị ứng của bạn."
      },
      {
        "dish_id": "c1a9e3d8-...",
        "dish_name": "Phở gà ta đùi xé",
        "store_name": "Quán Phở Bắc 1985",
        "distance_meters": 450.0,
        "current_price": 18000.0,
        "original_price": 55000.0,
        "pickup_window": "13:30 - 14:30",
        "remaining": 2,
        "ai_match_score": 0.91,
        "is_urgent_deal": true,
        "ai_justification": "🔥 Cứu trợ khẩn cấp: Quán đang áp dụng luật giảm 67% trong 25 phút cuối, còn đúng 2 tô nước nóng sốt gần bạn!"
      }
    ]
  }
  ```

### 4.3. Quản lý Hồ sơ Khẩu vị & Dị ứng Người dùng (User Preferences)
- **Method & Path**: `GET /users/preferences` & `PUT /users/preferences`
- **Quyền hạn**: `CONSUMER`
- **Request Body (PUT)**:
  ```json
  {
    "preferred_categories": ["RICE", "NOODLES"],
    "dietary_preference": "NONE",  // "NONE" | "VEGAN" | "VEGETARIAN"
    "excluded_allergens": ["Đậu phộng", "Hải sản"],
    "max_budget": 40000.0
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "updated_at": "2026-10-16T14:30:00Z",
    "message": "Đã cập nhật hồ sơ khẩu vị thành công. Các gợi ý AI sẽ tự động điều chỉnh theo tiêu chí này."
  }
  ```

### 4.4. Tìm kiếm Ngữ nghĩa Món ăn bằng Câu nói Tự nhiên (Semantic Food Search)
- **Method & Path**: `POST /dishes/search-semantic`
- **Quyền hạn**: Public
- **Request Body**:
  ```json
  {
    "query": "tìm món nước thanh đạm dưới 35k gần đây",
    "latitude": 10.7769,
    "longitude": 106.7009,
    "radius_km": 3.0
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "parsed_intent": {
      "category": "NOODLES",
      "dietary": "VEGETARIAN",
      "max_price": 35000.0
    },
    "total_found": 1,
    "dishes": [
      {
        "id": "c1a9e3d8-...",
        "name": "Hủ tiếu chay rau củ nấm",
        "store_name": "Quán Chay An Lạc",
        "distance_meters": 450.0,
        "current_price": 25000.0,
        "original_price": 50000.0,
        "pickup_time": "19:30 - 21:00",
        "remaining": 4
      }
    ]
  }
  ```

---

## 5. Tìm kiếm Theo Vị trí Không gian (Geo-Spatial Search)

### 5.1. Lấy Danh sách Quán & Món ăn Gần Đây
- **Method & Path**: `GET /stores/nearby`
- **Quyền hạn**: Public
- **Query Parameters**:
  - `lat`: Tọa độ vĩ độ người dùng (Ví dụ: `10.7769`)
  - `lng`: Tọa độ kinh độ người dùng (Ví dụ: `106.7009`)
  - `radius_km`: Bán kính tìm kiếm (Mặc định: `3.0`)
  - `category`: Lọc danh mục món (Tùy chọn: `RICE`, `NOODLES`, `BAKERY`...)
- **Response (200 OK)**:
  ```json
  {
    "total": 1,
    "results": [
      {
        "id": "e4f8d2a1-...",
        "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
        "address": "123 Đường Nguyễn Huệ, Quận 1",
        "distance_meters": 320.5,
        "rating_avg": 4.9,
        "total_co2_saved_kg": 145.2,
        "available_dishes_count": 2,
        "dishes": [
          {
            "id": "d7a1b3c9-...",
            "name": "Cơm gà xối mỡ sốt cay",
            "current_price": 22000.0,
            "original_price": 45000.0,
            "pickup_time": "14:00 - 15:00",
            "rule_discount_active": false,
            "remaining": 5,
            "allergens": ["Đậu phộng"]
          }
        ]
      }
    ]
  }
  ```

---

## 6. Đơn hàng & Xác thực Mã QR (Orders & QR Verification)

### 6.1. Đặt Mua Món ăn Cụ thể (Place Order)
- **Method & Path**: `POST /orders`
- **Quyền hạn**: `CONSUMER`
- **Request Body**:
  ```json
  {
    "dish_id": "d7a1b3c9-...",
    "quantity": 1,
    "payment_method": "COD",
    "voucher_code": null
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "order_id": "8b7e2c14-...",
    "order_code": "EB-20261016-9981",
    "dish_name": "Cơm gà xối mỡ sốt cay",
    "total_amount": 22000.0,
    "status": "CONFIRMED",
    "co2_saved_kg": 2.5,
    "green_points_to_earn": 50,
    "pickup_window": "14:00 - 15:00"
  }
  ```

### 6.2. Lấy Mã QR Xác nhận Đơn hàng (Consumer App)
- **Method & Path**: `GET /orders/{order_id}/qr-token`
- **Quyền hạn**: `CONSUMER` (Chính chủ đơn hàng)
- **Response (200 OK)**:
  ```json
  {
    "order_code": "EB-20261016-9981",
    "qr_token": "ecobite://pickup?oid=8b7e2c14&nonce=7a8b...&sig=9f3d...",
    "expires_at": "2026-10-16T15:00:00Z"
  }
  ```

### 6.3. Đối tác Quét Mã QR Xác nhận Giao Món (Partner Scanner)
- **Method & Path**: `POST /orders/verify-qr`
- **Quyền hạn**: `STORE_PARTNER`
- **Request Body**:
  ```json
  {
    "qr_token": "ecobite://pickup?oid=8b7e2c14&nonce=7a8b...&sig=9f3d..."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "order_code": "EB-20261016-9981",
    "customer_name": "Nguyễn Văn A",
    "dish_name": "Cơm gà xối mỡ sốt cay",
    "status": "COMPLETED",
    "points_awarded": 50,
    "message": "Xác thực đơn hàng thành công! Đã giao món ăn cho khách."
  }
  ```

---

## 7. Đánh giá Món ăn (Reviews)

### 7.1. Gửi Đánh giá Sau Khi Lấy Món
- **Method & Path**: `POST /orders/{order_id}/review`
- **Quyền hạn**: `CONSUMER` (Đơn hàng phải là `COMPLETED`)
- **Request Body**:
  ```json
  {
    "rating": 5,
    "comment": "Cơm gà giòn ngon, còn nóng hổi, rất đáng tiền!",
    "tags": ["Tươi ngon", "Đóng gói kỹ", "Đúng giờ"],
    "photo_urls": ["https://cdn.ecobite.vn/reviews/com_ga_rev.jpg"]
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "review_id": "7d2b1f89-...",
    "rating": 5,
    "store_new_rating_avg": 4.95
  }
  ```

---

## 8. Điểm Xanh & Đổi Voucher (Green Points & Rewards)

### 8.1. Lấy Thông tin Điểm Xanh & Lịch sử Đóng góp Môi trường
- **Method & Path**: `GET /green-points/me`
- **Quyền hạn**: `CONSUMER`
- **Response (200 OK)**:
  ```json
  {
    "balance_points": 350,
    "total_co2_saved_kg": 17.5,
    "total_meals_saved": 7,
    "rank_title": "Chiến Binh Xanh (Eco Hero)",
    "recent_ledger": [
      {
        "points": +50,
        "action": "ORDER_RESCUE",
        "co2_saved_kg": 2.5,
        "date": "2026-10-16T14:30:00Z"
      }
    ]
  }
  ```

### 8.2. Đổi Điểm Lấy Voucher Giảm Giá
- **Method & Path**: `POST /vouchers/{voucher_id}/redeem`
- **Quyền hạn**: `CONSUMER`
- **Response (200 OK)**:
  ```json
  {
    "voucher_code": "GREEN-20K-X98A",
    "discount_amount": 20000.0,
    "points_deducted": 200,
    "remaining_balance": 150
  }
  ```
