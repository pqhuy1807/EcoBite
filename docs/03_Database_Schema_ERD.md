# EcoBite Platform - Database Schema & Entity-Relationship Design (ERD)

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh
**Hệ quản trị CSDL**: PostgreSQL 16 kết hợp Không gian địa lý PostGIS 3.4
**ORM**: SQLAlchemy 2.0 (Async Engine: `asyncpg`, Migration: `alembic`)
**Phiên bản**: 2.1.0 (Bổ sung bảng `user_preferences` hỗ trợ AI Recommendation Engine)

---

## 1. Sơ đồ Thực thể Liên kết (Entity-Relationship Diagram)

```mermaid
erDiagram
    USERS ||--o{ STORES : owns
    USERS ||--o{ ORDERS : places
    USERS ||--o{ REVIEWS : writes
    USERS ||--o{ GREEN_POINTS_LEDGER : earns
    USERS ||--o{ USER_VOUCHERS : claims
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o| USER_PREFERENCES : configures

    STORES ||--o{ MENU_ITEMS : maintains
    STORES ||--o{ DISHES : publishes
    STORES ||--o{ ORDERS : fulfills
    STORES ||--o{ REVIEWS : receives

    MENU_ITEMS ||--o{ DISHES : bases

    DISHES ||--o{ ORDERS : contains
    DISHES ||--o{ REVIEWS : reviewed_in

    ORDERS ||--|| QR_TOKENS : generates
    ORDERS ||--o| REVIEWS : verified_by
    ORDERS ||--o{ GREEN_POINTS_LEDGER : awards

    VOUCHERS ||--o{ USER_VOUCHERS : defines

    USERS {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        string phone
        string role "CONSUMER | STORE_PARTNER | ADMIN"
        boolean is_active
        boolean is_verified
        int green_points_balance
        timestamp created_at
        timestamp updated_at
    }

    USER_PREFERENCES {
        uuid id PK
        uuid user_id FK,UK
        jsonb preferred_categories "RICE, NOODLES, BAKERY..."
        string dietary_preference "NONE | VEGAN | VEGETARIAN"
        jsonb excluded_allergens "Đậu phộng, Mè, Sữa, Gluten..."
        decimal max_budget "Mức ngân sách ưa thích"
        timestamp updated_at
    }

    STORES {
        uuid id PK
        uuid owner_id FK
        string name
        string description
        string address
        geometry location "Point(longitude, latitude) 4326"
        string phone
        string avatar_url
        string kyc_license_url
        string kyc_status "PENDING | APPROVED | REJECTED"
        text kyc_reject_reason
        decimal rating_avg "Default 5.0"
        int rating_count "Default 0"
        decimal total_co2_saved_kg "Default 0.0"
        timestamp created_at
        timestamp updated_at
    }

    MENU_ITEMS {
        uuid id PK
        uuid store_id FK
        string name "Tên món ăn trong thực đơn chuẩn"
        string description
        string category "RICE | NOODLES | BAKERY | BEVERAGE | VEGETARIAN | OTHER"
        decimal original_price "Giá gốc niêm yết"
        string image_url "Ảnh chụp món ăn chuẩn chất lượng cao"
        jsonb standard_ingredients "Nguyên liệu chuẩn"
        jsonb base_allergens "Dị ứng chuẩn"
        string dietary_type "VEGAN | VEGETARIAN | NON_VEGAN"
        boolean is_active "Default true"
        timestamp created_at
        timestamp updated_at
    }

    DISHES {
        uuid id PK
        uuid store_id FK
        uuid menu_item_id FK "Nullable: Liên kết Menu gốc để kế thừa Ảnh & Giá"
        string name "Tên món ăn cụ thể"
        string description
        string category "RICE | NOODLES | BAKERY | BEVERAGE | VEGETARIAN | OTHER"
        decimal original_price "Giá gốc (kế thừa từ menu_items)"
        decimal rescue_price "Giá giải cứu tiêu chuẩn (-40% đến -50%)"
        decimal rule_discount_price "Giá giờ chót kích hoạt theo luật (-70%)"
        decimal override_discounted_price "Nullable: Giá xả cố định nếu chủ quán chỉ định rõ"
        time pickup_start_time "Giờ bắt đầu nhận món"
        time pickup_end_time "Giờ kết thúc nhận món"
        time rule_discount_start_time "Thời điểm kích hoạt luật giảm giá giờ chót"
        int total_quantity "Tổng số suất đăng bán"
        int remaining_quantity "Số lượng suất còn lại (Check >= 0)"
        string status "ACTIVE | SOLD_OUT | EXPIRED | INACTIVE"
        string image_url "Kế thừa từ menu_items nếu không tải ảnh mới"
        jsonb ingredients "Danh sách nguyên liệu (bóc tách từ Gemini NLP)"
        jsonb allergens "AllergenWarning: [{allergen, risk_level, source: EXPLICIT|INFERRED, reason}]"
        jsonb dietary_notes "Ghi chú khẩu vị: ['Có mỡ hành', 'Có dưa chua', 'Cay vừa']"
        string dietary_type "VEGAN | VEGETARIAN | NON_VEGAN"
        decimal estimated_co2_kg_per_dish "Default 2.5"
        timestamp created_at
        timestamp updated_at
    }

    ORDERS {
        uuid id PK
        string order_code UK
        uuid consumer_id FK
        uuid store_id FK
        uuid dish_id FK
        int quantity
        decimal unit_price
        decimal total_amount
        string status "CONFIRMED | READY_FOR_PICKUP | COMPLETED | CANCELLED | EXPIRED"
        string payment_method "COD | WALLET | BANK_TRANSFER"
        string payment_status "PENDING | PAID"
        decimal co2_saved_kg
        int green_points_earned
        timestamp pickup_deadline
        timestamp completed_at
        timestamp created_at
    }

    QR_TOKENS {
        uuid id PK
        uuid order_id FK,UK
        string token_hash UK
        string nonce UK
        timestamp expires_at
        boolean is_used "Default false"
        timestamp used_at
        timestamp created_at
    }

    REVIEWS {
        uuid id PK
        uuid order_id FK,UK
        uuid consumer_id FK
        uuid store_id FK
        uuid dish_id FK
        int rating "1 to 5"
        text comment
        jsonb tags "Array of strings"
        jsonb photo_urls "Array of image URLs"
        timestamp created_at
    }

    GREEN_POINTS_LEDGER {
        uuid id PK
        uuid user_id FK
        uuid order_id FK
        int points_change
        int balance_after
        string action_type "ORDER_RESCUE | VOUCHER_REDEEM | SYSTEM_BONUS"
        decimal co2_saved_kg
        string note
        timestamp created_at
    }

    VOUCHERS {
        uuid id PK
        string code UK
        string title
        text description
        decimal discount_amount
        int points_required
        decimal min_order_amount
        timestamp expires_at
        boolean is_active
        timestamp created_at
    }

    USER_VOUCHERS {
        uuid id PK
        uuid user_id FK
        uuid voucher_id FK
        boolean is_used "Default false"
        timestamp used_at
        timestamp claimed_at
    }

    NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        string title
        text message
        string type "ORDER_UPDATE | NEARBY_DEAL | GREEN_POINTS | SYSTEM"
        boolean is_read "Default false"
        jsonb metadata
        timestamp created_at
    }
```

---

## 2. Đặc tả Chi tiết các Bảng CSDL (Tables Specification)

### 2.1. Bảng `users` (Tài khoản người dùng)
| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | PK, Default gen_random_uuid() | Khóa chính |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL | Địa chỉ email đăng nhập |
| `password_hash` | `VARCHAR(255)` | NOT NULL | Mật khẩu mã hoá bằng bcrypt |
| `full_name` | `VARCHAR(100)` | NOT NULL | Họ và tên |
| `phone` | `VARCHAR(20)` | NULL | Số điện thoại liên hệ |
| `role` | `VARCHAR(20)` | NOT NULL, DEFAULT 'CONSUMER' | Vai trò: `CONSUMER`, `STORE_PARTNER`, `ADMIN` |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT true | Trạng thái hoạt động |
| `is_verified` | `BOOLEAN` | NOT NULL, DEFAULT false | Xác thực email/SĐT |
| `green_points_balance`| `INTEGER` | NOT NULL, DEFAULT 0 | Số dư Điểm Xanh hiện tại |

### 2.2. Bảng `user_preferences` (Hồ sơ Khẩu vị phục vụ AI Recommendation)
| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | PK | Khóa chính |
| `user_id` | `UUID` | FK -> users.id, UNIQUE, NOT NULL | Thuộc người dùng nào |
| `preferred_categories`| `JSONB` | DEFAULT '[]' | Các nhóm món ưa thích (VD: `["NOODLES", "RICE"]`) |
| `dietary_preference` | `VARCHAR(50)` | NOT NULL, DEFAULT 'NONE' | `NONE`, `VEGAN`, `VEGETARIAN` |
| `excluded_allergens` | `JSONB` | DEFAULT '[]' | Các chất dị ứng cần AI loại trừ (VD: `["Đậu phộng"]`) |
| `max_budget` | `NUMERIC(12,2)` | NULL | Mức ngân sách tối đa quen thuộc của người dùng |
| `updated_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Thời điểm cập nhật khẩu vị gần nhất |

### 2.3. Bảng `stores` (Cửa hàng / Đối tác)
| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | PK | Mã định danh cửa hàng |
| `owner_id` | `UUID` | FK -> users.id, NOT NULL | Chủ sở hữu cửa hàng |
| `name` | `VARCHAR(255)` | NOT NULL | Tên cửa hàng / thương hiệu |
| `address` | `VARCHAR(500)` | NOT NULL | Địa chỉ thực tế |
| `location` | `GEOMETRY(Point, 4326)`| NOT NULL | Tọa độ GPS phục vụ truy vấn không gian PostGIS |
| `kyc_status`| `VARCHAR(20)`| NOT NULL, DEFAULT 'PENDING' | Trạng thái duyệt: `PENDING`, `APPROVED`, `REJECTED` |
| `rating_avg` | `NUMERIC(3,2)` | DEFAULT 5.0 | Điểm đánh giá sao trung bình |
| `total_co2_saved_kg`| `NUMERIC(10,2)`| DEFAULT 0.0 | Tổng lượng khí CO2 đã giảm phát thải |

### 2.4. Bảng `menu_items` (Thực đơn gốc chuẩn của Quán - Phục vụ Menu Grounding)
| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | PK | Mã món trong thực đơn gốc |
| `store_id` | `UUID` | FK -> stores.id, NOT NULL | Thuộc cửa hàng nào |
| `name` | `VARCHAR(255)` | NOT NULL | Tên chuẩn của món ăn (Ví dụ: "Cơm sườn bì chả") |
| `description` | `TEXT` | NULL | Mô tả chi tiết món ăn |
| `category` | `VARCHAR(50)` | NOT NULL | `RICE`, `NOODLES`, `BAKERY`, `BEVERAGE`, `VEGETARIAN`... |
| `original_price` | `NUMERIC(12,2)` | NOT NULL | Giá gốc niêm yết tại quán |
| `image_url` | `VARCHAR(500)` | NOT NULL | Ảnh chụp món ăn chuẩn chất lượng cao để hiển thị trên app |
| `standard_ingredients`| `JSONB` | DEFAULT '[]' | Thành phần nguyên liệu chuẩn |
| `base_allergens` | `JSONB` | DEFAULT '[]' | Dị ứng cơ bản đã xác định trước |
| `dietary_type` | `VARCHAR(50)` | NOT NULL, DEFAULT 'NON_VEGAN'| `VEGAN`, `VEGETARIAN`, `NON_VEGAN` |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT true | Còn phục vụ trong thực đơn không |

### 2.5. Bảng `dishes` (Món ăn Dư thừa Cụ thể Đăng bán trong Ca)
| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | PK | Mã món ăn dư thừa đăng bán |
| `store_id` | `UUID` | FK -> stores.id, NOT NULL | Thuộc cửa hàng nào |
| `menu_item_id` | `UUID` | FK -> menu_items.id, NULL | Liên kết thực đơn gốc (để kế thừa Ảnh và Giá gốc) |
| `name` | `VARCHAR(255)` | NOT NULL | Tên món ăn (Kế thừa từ `menu_items` hoặc tên tự do) |
| `category` | `VARCHAR(50)` | NOT NULL | RICE, NOODLES, BAKERY, BEVERAGE, VEGETARIAN... |
| `original_price` | `NUMERIC(12,2)` | NOT NULL | Giá gốc thị trường (kế thừa từ `menu_items` nếu không nhập) |
| `rescue_price` | `NUMERIC(12,2)` | NOT NULL | Giá giải cứu tiêu chuẩn (ví dụ 25.000đ - giảm 50%) |
| `rule_discount_price`| `NUMERIC(12,2)`| NULL | Giá giờ chót tự động giảm sâu theo luật (ví dụ 15.000đ) |
| `override_discounted_price`| `NUMERIC(12,2)`| NULL | Giá xả cố định nếu chủ quán đọc giá cụ thể (ví dụ 20.000đ) |
| `pickup_start_time` | `TIME` | NOT NULL | Giờ bắt đầu nhận món trong ngày (VD: 14:00) |
| `pickup_end_time` | `TIME` | NOT NULL | Giờ kết thúc nhận món (VD: 15:00) |
| `rule_discount_start_time`| `TIME`| NULL | Thời điểm kích hoạt luật giảm giá giờ chót (VD: 14:30) |
| `total_quantity` | `INTEGER` | NOT NULL | Tổng số suất đăng bán ban đầu |
| `remaining_quantity` | `INTEGER` | NOT NULL, CHECK (>= 0) | Số lượng suất còn lại |
| `status` | `VARCHAR(20)` | NOT NULL, DEFAULT 'ACTIVE' | `ACTIVE`, `SOLD_OUT`, `EXPIRED`, `INACTIVE` |
| `image_url` | `VARCHAR(500)` | NULL | Kế thừa từ `menu_items.image_url` nếu không tải ảnh mới |
| `ingredients` | `JSONB` | DEFAULT '[]' | Danh sách nguyên liệu bóc tách từ Gemini NLP |
| `allergens` | `JSONB` | DEFAULT '[]' | Cảnh báo dị ứng 2 tầng `[{allergen, risk_level, source: EXPLICIT/INFERRED, reason}]` |
| `dietary_notes` | `JSONB` | DEFAULT '[]' | Ghi chú khẩu vị địa phương: `['Có mỡ hành', 'Có dưa chua', 'Cay']` |
| `dietary_type` | `VARCHAR(50)` | NOT NULL, DEFAULT 'NON_VEGAN'| `VEGAN`, `VEGETARIAN`, `NON_VEGAN` |
| `estimated_co2_kg_per_dish`| `NUMERIC(6,2)`| DEFAULT 2.5 | Ước tính giảm phát thải CO2 mỗi suất ăn (kg) |

### 2.6. Bảng `orders` & `qr_tokens` (Đơn hàng & Mã xác nhận)
- Trạng thái đơn hàng (`orders.status`):
  - `CONFIRMED`: Đặt hàng thành công, đã trừ số lượng tồn kho nguyên tử.
  - `READY_FOR_PICKUP`: Đang trong khung giờ nhận món.
  - `COMPLETED`: Chủ quán đã quét mã QR thành công, giao món xong.
  - `CANCELLED`: Người dùng hủy trước giờ hẹn hoặc quán hủy.
  - `EXPIRED`: Khách không đến lấy trước giờ kết thúc (`pickup_deadline`).
- `qr_tokens.nonce`: Mã ngẫu nhiên 32 ký tự, được đánh dấu `is_used = true` ngay khi quét để ngăn chặn quét trùng lặp (Double Claim).

---

## 3. Chiến lược Đánh Chỉ mục (Indexing Strategy)

1. **Spatial GIST Index trên `stores.location`**:
   ```sql
   CREATE INDEX idx_stores_location ON stores USING GIST (location);
   ```

2. **Compound Index trên `dishes`**:
   ```sql
   CREATE INDEX idx_dishes_store_status ON dishes (store_id, status);
   CREATE INDEX idx_dishes_category_status ON dishes (category, status);
   ```

3. **GIN Index trên các trường JSONB của `dishes` & `user_preferences`**:
   ```sql
   CREATE INDEX idx_dishes_allergens_gin ON dishes USING GIN (allergens);
   CREATE INDEX idx_dishes_ingredients_gin ON dishes USING GIN (ingredients);
   CREATE INDEX idx_user_pref_allergens_gin ON user_preferences USING GIN (excluded_allergens);
   ```

4. **B-Tree Index trên `orders`**:
   ```sql
   CREATE INDEX idx_orders_consumer_created ON orders (consumer_id, created_at DESC);
   CREATE INDEX idx_orders_store_status ON orders (store_id, status);
   CREATE UNIQUE INDEX idx_orders_code ON orders (order_code);
   ```

5. **Unique Index trên `qr_tokens`**:
   ```sql
   CREATE UNIQUE INDEX idx_qr_tokens_hash ON qr_tokens (token_hash);
   ```
