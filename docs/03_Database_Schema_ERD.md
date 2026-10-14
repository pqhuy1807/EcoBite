# EcoBite Platform - Database Schema & Entity-Relationship Design (ERD)

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh  
**Hệ quản trị CSDL**: PostgreSQL 16 kết hợp Không gian địa lý PostGIS 3.4  
**ORM**: SQLAlchemy 2.0 (Async Engine: `asyncpg`, Migration: `alembic`)  

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

    STORES ||--o{ FOOD_PACKAGES : publishes
    STORES ||--o{ ORDERS : fulfills
    STORES ||--o{ REVIEWS : receives

    FOOD_PACKAGES ||--o{ ORDERS : contains

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

    FOOD_PACKAGES {
        uuid id PK
        uuid store_id FK
        string title
        string description
        string category "BAKERY | MEAL | FRESH_PRODUCE | VEGETARIAN | OTHER"
        decimal original_price
        decimal rescue_price
        decimal dynamic_discount_price
        time pickup_start_time
        time pickup_end_time
        time dynamic_discount_start_time
        int total_quantity
        int remaining_quantity
        string status "ACTIVE | SOLD_OUT | EXPIRED | INACTIVE"
        string image_url
        decimal estimated_co2_kg_per_package "Default 2.5"
        timestamp created_at
        timestamp updated_at
    }

    ORDERS {
        uuid id PK
        string order_code UK
        uuid consumer_id FK
        uuid store_id FK
        uuid package_id FK
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

### 2.2. Bảng `stores` (Cửa hàng / Đối tác)
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

### 2.3. Bảng `food_packages` (Gói thức ăn Surprise Bag)
| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | PK | Mã gói hàng |
| `store_id` | `UUID` | FK -> stores.id | Thuộc cửa hàng |
| `title` | `VARCHAR(255)` | NOT NULL | Tên gói thức ăn bất ngờ |
| `category` | `VARCHAR(50)` | NOT NULL | Phân loại: BAKERY, MEAL, FRESH_PRODUCE... |
| `original_price` | `NUMERIC(12,2)` | NOT NULL | Giá gốc thị trường |
| `rescue_price` | `NUMERIC(12,2)` | NOT NULL | Giá giải cứu tiêu chuẩn (-50% đến -70%) |
| `dynamic_discount_price`| `NUMERIC(12,2)`| NULL | Giá giờ chót giảm sâu hơn trong 30 phút cuối |
| `pickup_start_time` | `TIME` | NOT NULL | Giờ bắt đầu nhận món trong ngày (VD: 19:30) |
| `pickup_end_time` | `TIME` | NOT NULL | Giờ kết thúc nhận món (VD: 21:00) |
| `remaining_quantity` | `INTEGER` | NOT NULL, CHECK (>= 0) | Số lượng suất còn lại |

### 2.4. Bảng `orders` & `qr_tokens` (Đơn hàng & Mã xác nhận)
- Trạng thái đơn hàng (`orders.status`):
  - `CONFIRMED`: Đặt hàng thành công, đã giữ tồn kho.
  - `READY_FOR_PICKUP`: Đang trong khung giờ nhận hàng.
  - `COMPLETED`: Chủ quán đã quét mã QR thành công, giao hàng xong.
  - `CANCELLED`: Người dùng hủy trước giờ hẹn hoặc quán hủy.
  - `EXPIRED`: Khách không đến lấy trước giờ kết thúc (`pickup_deadline`).
- `qr_tokens.nonce`: Mã ngẫu nhiên 32 ký tự, được đánh dấu `is_used = true` ngay khi quét để ngăn chặn quét trùng lặp (Double Claim).

---

## 3. Chiến lược Đánh Chỉ mục (Indexing Strategy)

Để đảm bảo hiệu năng truy vấn cao nhất cho hàng trăm nghìn giao dịch và tìm kiếm vị trí:

1. **Spatial GIST Index trên `stores.location`**:
   ```sql
   CREATE INDEX idx_stores_location ON stores USING GIST (location);
   ```
   *Mục đích: Cho phép truy vấn bán kính `ST_DWithin` phản hồi trong thời gian dưới 10ms.*

2. **Compound Index trên `food_packages`**:
   ```sql
   CREATE INDEX idx_packages_store_status ON food_packages (store_id, status);
   ```

3. **B-Tree Index trên `orders`**:
   ```sql
   CREATE INDEX idx_orders_consumer_created ON orders (consumer_id, created_at DESC);
   CREATE INDEX idx_orders_store_status ON orders (store_id, status);
   CREATE UNIQUE INDEX idx_orders_code ON orders (order_code);
   ```

4. **Unique Index trên `qr_tokens`**:
   ```sql
   CREATE UNIQUE INDEX idx_qr_tokens_hash ON qr_tokens (token_hash);
   ```
