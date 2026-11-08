# 🔌 EcoBite Platform - RESTful API Specification (v1)

**Dự án**: EcoBite - Nền tảng Giải cứu Thực phẩm Thông minh & Kết nối Xanh (Food Rescue Platform)
**Nhóm thực hiện**: Group 5 - Lớp Kỹ nghệ Phần mềm / Computer Science (HCMUS)
- **Phùng Quốc Huy** (24127402) — *AI and Data Lead / Full-Stack Engineer*
- **Đặng Trọng Phúc** (24127495) — *Backend Lead & AI Engineer / Full-Stack Engineer*
- **Đàng Thế Tony** (24127561) — *QA/Tester Lead & Backend Engineer / Full-Stack Engineer*
- **Võ Ngọc Thịnh** (24127246) — *Frontend Lead / Full-Stack Engineer*

**Base URL**: `http://localhost:8000/api/v1`
**Authentication**: Bearer Token (`Authorization: Bearer <jwt_access_token>`)
**Format**: `application/json` (Hỗ trợ `multipart/form-data` cho Native Audio và ảnh)
**Phiên bản**: 2.2.0 (Chuẩn hóa 8 Tính năng Cốt lõi, Cổng VNPay IPN HMAC-SHA512 & 2 Tính năng AI Gemini 2.5 Flash)

---

## 1. Feature 1: Authentication & Merchant Onboarding (Xác thực & KYC Quán)

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
    "id": "a5e8c1b2-9d3e-4b2a-8c1f-2e3d4c5b6a7b",
    "email": "user@example.com",
    "full_name": "Nguyễn Văn A",
    "role": "CONSUMER",
    "green_points_balance": 0,
    "created_at": "2026-10-14T22:30:00Z"
  }
  ```

### 1.2. Đăng nhập Lấy JWT Dual-Tokens
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
    "refresh_token": "def50200a7b4...",
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

### 1.3. Đăng ký Cửa hàng & Nộp Chứng nhận ATVSTP (Store KYC Onboarding)
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
    "kyc_license_url": "https://cdn.ecobite.vn/kyc/atvstp_license1.pdf"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
    "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
    "kyc_status": "PENDING",
    "message": "Hồ sơ đối tác đã gửi thành công và đang chờ Quản trị viên duyệt chứng nhận ATVSTP."
  }
  ```

### 1.4. Admin Duyệt Hồ sơ Đối tác (Admin KYC Verification)
- **Method & Path**: `PATCH /admin/stores/{store_id}/review`
- **Quyền hạn**: `ADMIN`
- **Request Body**:
  ```json
  {
    "decision": "APPROVED",  // "APPROVED" | "REJECTED"
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

## 2. Feature 2 & 3: Base Menu Catalog, Surplus Dishes & Rule-Based Discounting

### 2.1. Thêm Món vào Thực đơn Chuẩn của Quán (Menu Catalog)
- **Method & Path**: `POST /stores/{store_id}/menu-items`
- **Quyền hạn**: `STORE_PARTNER` (Cửa hàng đã được duyệt KYC)
- **Request Body**:
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

### 2.2. Đăng Bán Món Dư Cuối Ca Thủ Công (Create Surplus Dish)
- **Method & Path**: `POST /dishes`
- **Quyền hạn**: `STORE_PARTNER`
- **Request Body**:
  ```json
  {
    "menu_item_id": "m1a2b3c4-...",
    "name": "Cơm sườn bì chả",
    "category": "RICE",
    "original_price": 45000.0,
    "rescue_price": 22000.0,
    "rule_discount_price": 13500.0,
    "pickup_start_time": "14:00:00",
    "pickup_end_time": "15:00:00",
    "rule_discount_start_time": "14:30:00",
    "total_quantity": 5,
    "allergens": [
      {"allergen": "Eggs (Trứng)", "risk_level": "HIGH", "source": "INFERRED", "reason": "Chả có trứng"},
      {"allergen": "Fish (Cá)", "risk_level": "HIGH", "source": "INFERRED", "reason": "Nước mắm làm từ cá"}
    ],
    "dietary_notes": ["Có mỡ hành (Allium)", "Có dưa chua"]
  }
  ```

### 2.3. Đăng Hàng Loạt Món Dư sau khi Duyệt Draft Cards (1-Tap Batch Post)
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
          {"allergen": "Peanuts (Đậu phộng)", "risk_level": "HIGH", "source": "INFERRED", "reason": "Đậu phộng rang"}
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

---

## 3. Feature 4: Location-Based Search & PostGIS Radar Discovery

### 3.1. Tìm kiếm Radar Quán & Món ăn Xung quanh theo Tọa độ GPS
- **Method & Path**: `GET /stores/nearby`
- **Quyền hạn**: Public
- **Query Parameters**:
  - `lat`: Tọa độ vĩ độ người dùng (Ví dụ: `10.7769`)
  - `lng`: Tọa độ kinh độ người dùng (Ví dụ: `106.7009`)
  - `radius_km`: Bán kính tìm kiếm (Mặc định: `3.0`, hỗ trợ 1.0 đến 10.0)
  - `category`: Lọc danh mục (`RICE`, `NOODLES`, `BAKERY`, `VEGETARIAN`...)
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
        "dishes": [
          {
            "id": "d7a1b3c9-...",
            "name": "Cơm sườn bì chả",
            "current_price": 22000.0,
            "original_price": 45000.0,
            "pickup_window": "13:55 - 15:00",
            "is_rule_discount_active": false,
            "remaining_quantity": 5,
            "allergens": ["Eggs (Trứng)", "Fish (Cá/Nước mắm)"]
          }
        ]
      }
    ]
  }
  ```

---

## 4. AI Features: AI Intelligence Suite (Powered by Google Gemini 2.5 Flash)

### 4.1. AI Feature 1: Trợ lý Bóc tách Đa phương thức & Rà soát Dị ứng 2 Tầng (Batch Quick-Post NLP)
- **Method & Path**: `POST /ml/parse-dish-nlp`
- **Quyền hạn**: `STORE_PARTNER`
- **Content-Type**: `multipart/form-data` hoặc `application/json`
- **Request Parameters / Body**:
  - `audio_file`: *(Tùy chọn)* File ghi âm giọng nói định dạng `.m4a`, `.mp3`, `.wav`.
  - `raw_text`: *(Tùy chọn)* Đoạn hội thoại tự do: *"Còn 5 cơm sườn chả, 3 bún thịt nướng xả từ giờ đến 3h chiều nhé"*.
  - `current_server_time`: ISO 8601 server timestamp (VD: `2026-10-16T13:55:00+07:00`).
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
        "allergens": [
          {
            "allergen": "Eggs (Trứng)",
            "risk_level": "HIGH",
            "source": "INFERRED",
            "reason": "Chả chưng có chứa trứng theo công thức truyền thống Việt"
          },
          {
            "allergen": "Fish (Cá/Nước mắm)",
            "risk_level": "HIGH",
            "source": "INFERRED",
            "reason": "Nước mắm ăn kèm có nguồn gốc từ cá"
          }
        ],
        "dietary_notes": ["Có mỡ hành (Allium)", "Có dưa chua"]
      },
      {
        "matched_menu_id": "b5c6d7e8-...",
        "dish_name": "Bún thịt nướng",
        "quantity": 3,
        "original_price": 40000.0,
        "override_discounted_price": 20000.0,
        "allergens": [
          {
            "allergen": "Peanuts (Đậu phộng)",
            "risk_level": "HIGH",
            "source": "INFERRED",
            "reason": "Bún thịt nướng rắc đậu phộng rang"
          }
        ],
        "dietary_notes": ["Có hành phi", "Có đậu phộng"]
      }
    ]
  }
  ```

### 4.2. AI Feature 2: Gợi ý Món ăn Thông minh Cá nhân hóa (Smart Food Recommendation)
- **Method & Path**: `GET /recommendations/personalized`
- **Quyền hạn**: `CONSUMER`
- **Query Parameters**: `lat`, `lng`, `limit` (mặc định: `3`)
- **Thuật toán**: SQL PostGIS Hard Filter loại trừ 100% dị ứng của người dùng $\rightarrow$ Multi-Factor Heuristic Scoring:
  $$\text{Score} = (0.40 \times \text{Proximity}) + (0.30 \times \text{Discount Depth \& Time Urgency}) + (0.30 \times \text{Taste Profile Match})$$
  $\rightarrow$ Gemini 2.5 Flash sinh lý do thuyết phục ngắn gọn (20–30 từ).
- **Response (200 OK)**:
  ```json
  {
    "recommendations": [
      {
        "dish_id": "d7a1b3c9-...",
        "dish_name": "Phở gà ta đùi xé",
        "store_name": "Quán Phở Bắc 1985",
        "distance_meters": 350.0,
        "current_price": 18000.0,
        "original_price": 55000.0,
        "discount_percent": 67,
        "is_urgent_deal": true,
        "ai_justification": "Gợi ý cho bạn: Bạn thường xuyên thích các món súp mì nóng vào buổi trưa. Quán Phở Bắc cách 350m đang cung cấp ưu đãi thanh lý 67% chỉ với 18.000 VND, còn 2 phần đến 13:30 — cam kết hoàn toàn không chứa đậu phộng theo sở thích của bạn!"
      }
    ]
  }
  ```

### 4.3. Tìm kiếm Ngữ nghĩa Hội thoại (Conversational Semantic Search)
- **Method & Path**: `POST /dishes/search-semantic`
- **Quyền hạn**: Public
- **Request Body**:
  ```json
  {
    "query": "Tìm cho tôi một món súp ấm áp dễ chịu dưới 30k ở gần đây",
    "latitude": 10.7769,
    "longitude": 106.7009
  }
  ```

---

## 5. Feature 5: Inventory Anti-Overselling Lock & Order Management

### 5.1. Đặt Mua Món Dư Thừa với Khóa Tồn Kho Nguyên Tử (Place Order)
- **Method & Path**: `POST /orders`
- **Quyền hạn**: `CONSUMER`
- **Request Body**:
  ```json
  {
    "dish_id": "d7a1b3c9-...",
    "quantity": 1,
    "payment_method": "VNPAY"  // "VNPAY" | "COD"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "order_id": "8b7e2c14-...",
    "order_code": "EB-20261016-9981",
    "total_amount": 22000.0,
    "status": "CONFIRMED",
    "payment_status": "PENDING",
    "co2_saved_kg": 2.5,
    "green_points_to_earn": 50,
    "pickup_deadline": "2026-10-16T15:00:00Z"
  }
  ```

---

## 6. Feature 6: Seamless Cashless Checkout (VNPay Payment Gateway)

### 6.1. Khởi tạo URL Thanh toán VNPay (Generate VNPay Payment URL)
- **Method & Path**: `POST /payments/vnpay/create-url`
- **Quyền hạn**: `CONSUMER`
- **Request Body**:
  ```json
  {
    "order_id": "8b7e2c14-...",
    "bank_code": "VNPAYQR"  // Tuỳ chọn: "VNPAYQR", "NCB", "VCOMBANK"...
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "payment_url": "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_Amount=2200000&vnp_Command=pay&vnp_CreateDate=20261016140500&vnp_CurrCode=VND&vnp_IpAddr=127.0.0.1&vnp_Locale=vn&vnp_OrderInfo=Thanh+toan+don+hang+EB-20261016-9981&vnp_OrderType=food&vnp_ReturnUrl=...&vnp_TmnCode=...&vnp_TxnRef=...&vnp_Version=2.1.0&vnp_SecureHash=7f6a..."
  }
  ```

### 6.2. Webhook IPN Server-to-Server từ VNPay (Idempotent Webhook Handler)
- **Method & Path**: `GET /payments/vnpay/ipn`
- **Quyền hạn**: Public (Được bảo vệ bởi chữ ký bí mật HMAC-SHA512 `vnp_SecureHash`)
- **Query Parameters**: Nhận toàn bộ query parameters chuẩn từ VNPay (`vnp_TxnRef`, `vnp_Amount`, `vnp_ResponseCode`, `vnp_TransactionNo`, `vnp_SecureHash`...)
- **Quy trình xử lý**:
  1. Kiểm tra chữ ký HMAC-SHA512.
  2. Kiểm tra Idempotent: Giao dịch đã xử lý chưa.
  3. Cập nhật `orders.payment_status = 'PAID'`.
- **Response**:
  ```json
  {
    "RspCode": "00",
    "Message": "Confirm Success"
  }
  ```

---

## 7. Feature 7: Dynamic HMAC-SHA256 Single-Use QR Token & In-Store Web Scanner

### 7.1. Lấy Mã QR Nhận Món Động (Dynamic HMAC-SHA256 Token)
- **Method & Path**: `GET /orders/{order_id}/qr-token`
- **Quyền hạn**: `CONSUMER` (Chính chủ đơn hàng)
- **Response (200 OK)**:
  ```json
  {
    "order_code": "EB-20261016-9981",
    "qr_token": "ecobite://pickup?oid=8b7e2c14&nonce=7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d&deadline=1760626800&sig=9f3d5c6b7a8e...",
    "expires_at": "2026-10-16T15:00:00Z"
  }
  ```

### 7.2. Chủ Quán Dùng Camera Web Quét Xác Nhận Đơn (In-Store Camera Scanner)
- **Method & Path**: `POST /orders/verify-qr`
- **Quyền hạn**: `STORE_PARTNER`
- **Request Body**:
  ```json
  {
    "qr_token": "ecobite://pickup?oid=8b7e2c14&nonce=7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d&deadline=1760626800&sig=9f3d5c6b7a8e..."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "order_code": "EB-20261016-9981",
    "status": "COMPLETED",
    "points_awarded": 50,
    "co2_saved_kg": 2.5,
    "message": "Xác thực chữ ký hợp lệ! Đã giao món ăn thành công và cộng 50 Điểm Xanh cho khách."
  }
  ```

---

## 8. Feature 8: Verified Reviews, Green Points & Environmental Impact Tracker

### 8.1. Đánh giá Món ăn Sau Khi Nhận (Verified Reviews)
- **Method & Path**: `POST /orders/{order_id}/review`
- **Quyền hạn**: `CONSUMER` (Đơn hàng phải ở trạng thái `COMPLETED`)
- **Request Body**:
  ```json
  {
    "rating": 5,
    "comment": "Cơm sườn mềm thơm, còn nóng hổi, chả rất ngon!",
    "tags": ["Tươi ngon", "Đóng gói kỹ", "Nóng sốt"],
    "photo_urls": ["https://cdn.ecobite.vn/reviews/com_suon_real.jpg"]
  }
  ```

### 8.2. Tra cứu Số Dư Điểm Xanh & Lượng Phát Thải $CO_2$ Cắt Giảm
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
        "created_at": "2026-10-16T14:30:00Z"
      }
    ]
  }
  ```

### 8.3. Đổi Điểm Xanh Lấy Voucher Giảm Giá
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
