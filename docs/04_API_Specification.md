# EcoBite Platform - RESTful API Specification (v1)

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh  
**Base URL**: `http://localhost:8000/api/v1`  
**Authentication**: Bearer Token (`Authorization: Bearer <jwt_access_token>`)  
**Format**: `application/json`  

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
    "name": "Tiệm Bánh Mì Xanh Sài Gòn",
    "description": "Chuyên các loại bánh mì ngọt, sandwich tươi trong ngày",
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
    "name": "Tiệm Bánh Mì Xanh Sài Gòn",
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

## 3. Gói Thức ăn Bất ngờ & Giảm giá Theo Giờ (Surprise Bags & Dynamic Pricing)

### 3.1. Tạo Gói Thức ăn Bất ngờ (Partner)
- **Method & Path**: `POST /packages`
- **Quyền hạn**: `STORE_PARTNER` (Đã được Approved)
- **Request Body**:
  ```json
  {
    "title": "Túi Bánh Ngọt Cuối Ngày (Surprise Pastry Bag)",
    "description": "Gồm 3-4 loại bánh nướng hảo hạng nướng trong ngày",
    "category": "BAKERY",
    "original_price": 120000.0,
    "rescue_price": 45000.0,
    "dynamic_discount_price": 30000.0,
    "pickup_start_time": "19:30:00",
    "pickup_end_time": "21:00:00",
    "dynamic_discount_start_time": "20:30:00",
    "total_quantity": 8,
    "image_url": "https://cdn.ecobite.vn/packages/pastry_bag.jpg"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "c1a9e3d8-...",
    "title": "Túi Bánh Ngọt Cuối Ngày (Surprise Pastry Bag)",
    "remaining_quantity": 8,
    "status": "ACTIVE"
  }
  ```

### 3.2. AI Kiểm tra Chất lượng Hình ảnh Thực phẩm (ML Inference)
- **Method & Path**: `POST /ml/inspect-quality`
- **Quyền hạn**: `STORE_PARTNER`
- **Request Format**: `multipart/form-data` (`image: [file]`)
- **Response (200 OK)**:
  ```json
  {
    "prediction": "fresh_packaged_food",
    "confidence": 0.94,
    "quality_pass": true,
    "message": "Hình ảnh đạt chuẩn an toàn thực phẩm để đăng tải."
  }
  ```

---

## 4. Tìm kiếm Theo Vị trí Không gian (Geo-Spatial Search)

### 4.1. Lấy Danh sách Quán Gần Đây
- **Method & Path**: `GET /stores/nearby`
- **Quyền hạn**: Public
- **Query Parameters**:
  - `lat`: Tọa độ vĩ độ người dùng (Ví dụ: `10.7769`)
  - `lng`: Tọa độ kinh độ người dùng (Ví dụ: `106.7009`)
  - `radius_km`: Bán kính tìm kiếm (Mặc định: `3.0`)
  - `category`: Lọc danh mục món (Tùy chọn: `BAKERY`, `MEAL`...)
- **Response (200 OK)**:
  ```json
  {
    "total": 1,
    "results": [
      {
        "id": "e4f8d2a1-...",
        "name": "Tiệm Bánh Mì Xanh Sài Gòn",
        "address": "123 Đường Nguyễn Huệ, Quận 1",
        "distance_meters": 320.5,
        "rating_avg": 4.9,
        "total_co2_saved_kg": 145.2,
        "available_packages_count": 2,
        "packages": [
          {
            "id": "c1a9e3d8-...",
            "title": "Túi Bánh Ngọt Cuối Ngày",
            "current_price": 45000.0,
            "pickup_time": "19:30 - 21:00",
            "remaining": 8
          }
        ]
      }
    ]
  }
  ```

---

## 5. Đơn hàng & Xác thực Mã QR (Orders & QR Verification)

### 5.1. Đặt Mua Gói Thức ăn (Place Order)
- **Method & Path**: `POST /orders`
- **Quyền hạn**: `CONSUMER`
- **Request Body**:
  ```json
  {
    "package_id": "c1a9e3d8-...",
    "quantity": 1,
    "payment_method": "COD",
    "voucher_code": null
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "order_id": "8b7e2c14-...",
    "order_code": "EB-20261014-9981",
    "total_amount": 45000.0,
    "status": "CONFIRMED",
    "co2_saved_kg": 2.5,
    "green_points_to_earn": 50,
    "pickup_window": "19:30 - 21:00"
  }
  ```

### 5.2. Lấy Mã QR Xác nhận Đơn hàng (Consumer App)
- **Method & Path**: `GET /orders/{order_id}/qr-token`
- **Quyền hạn**: `CONSUMER` (Chính chủ đơn hàng)
- **Response (200 OK)**:
  ```json
  {
    "order_code": "EB-20261014-9981",
    "qr_token": "ecobite://pickup?oid=8b7e2c14&nonce=7a8b...&sig=9f3d...",
    "expires_at": "2026-10-14T21:00:00Z"
  }
  ```

### 5.3. Đối tác Quét Mã QR Xác nhận Giao Hàng (Partner Scanner)
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
    "order_code": "EB-20261014-9981",
    "customer_name": "Nguyễn Văn A",
    "package_title": "Túi Bánh Ngọt Cuối Ngày",
    "status": "COMPLETED",
    "points_awarded": 50,
    "message": "Xác thực đơn hàng thành công! Đã giao gói cứu trợ."
  }
  ```

---

## 6. Đánh giá Món ăn (Reviews)

### 6.1. Gửi Đánh giá Sau Khi Lấy Hàng
- **Method & Path**: `POST /orders/{order_id}/review`
- **Quyền hạn**: `CONSUMER` (Đơn hàng phải là `COMPLETED`)
- **Request Body**:
  ```json
  {
    "rating": 5,
    "comment": "Bánh rất ngon, còn ấm giòn. Chủ quán thân thiện!",
    "tags": ["Tươi ngon", "Đúng giờ", "Đóng gói kỹ"],
    "photo_urls": ["https://cdn.ecobite.vn/reviews/rev1.jpg"]
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

## 7. Điểm Xanh & Đổi Voucher (Green Points & Rewards)

### 7.1. Lấy Thông tin Điểm Xanh & Lịch sử Đóng góp Môi trường
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
        "date": "2026-10-14T21:05:00Z"
      }
    ]
  }
  ```

### 7.2. Đổi Điểm Lấy Voucher Giảm Giá
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
