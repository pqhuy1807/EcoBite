# EcoBite Platform - System Architecture & Technical Design

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh
**Tác giả**: Senior DevOps Engineer & Technical Project Manager
**Phiên bản**: 2.1.0 (Bổ sung Phân hệ AI Intelligence Suite & Hệ thống Gợi ý Món ăn Thông minh)

---

## 1. Kiến trúc Hệ thống Tổng quan (High-Level Architecture)

Hệ thống EcoBite được thiết kế theo mô hình **Decoupled Three-Tier Architecture** kết hợp phân hệ **AI Intelligence Suite (Google Gemini 2.5 Flash)** và thành phần **AI/ML Inference Pipeline độc lập**.

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer (Next.js 14 App Router)"]
        ConsumerApp["Consumer Web / Mobile PWA\n(Leaflet Map, QR Viewer, Smart Recommendations)"]
        PartnerPortal["Store Partner Portal\n(Quick-Post NLP, html5-qrcode Scanner)"]
        AdminDashboard["System Admin Dashboard\n(KYC Review, Metrics, CO2 Reports)"]
    end

    subgraph Gateway ["Edge & Security"]
        NginxGateway["Reverse Proxy / SSL / CORS\n(Port 80/443)"]
    end

    subgraph BackendLayer ["Backend Application (FastAPI Asynchronous Runtime)"]
        APIEndpoints["FastAPI Routers (/api/v1)\n- Auth, Stores, Dishes, Recommendations\n- Orders, QR Verify, Reviews, GreenPoints"]
        CoreMiddleware["Core Services & Middlewares\n- JWT RBAC Guard\n- HMAC QR Signer\n- Rule-based Discount Calculator\n- Gemini GenAI Client\n- Smart Recommendation Engine"]
        DBSession["Async SQLAlchemy 2.0 Engine\n(asyncpg connection pool)"]
    end

    subgraph DataLayer ["Data & Cache Layer (Docker Compose)"]
        PostgreSQL["PostgreSQL 16 + PostGIS 3.4\n- Spatial Geometry(Point, 4326)\n- GIST Spatial Index\n- Dishes, User Preferences, Orders"]
        RedisStore["Redis 7\n- Rate Limiting\n- Inventory Locks\n- Recommendation Cache\n- QR Nonce Tracking"]
    end

    subgraph AISuite ["Phân hệ Trí tuệ Nhân tạo (AI Intelligence Suite)"]
        GeminiNLP["Google Gemini 2.5 Flash (Google AI Studio Free Tier)\n- Quick-Post NLP Extraction\n- Food Safety Allergen Tagging\n- Semantic Search Intent Parser\n- Recommendation Justification Generator"]
        MLDir["ml/weights/*.pt\n(PyTorch Computer Vision Checkpoints)"]
    end

    ClientLayer -->|HTTPS / REST / WSS| NginxGateway
    NginxGateway --> APIEndpoints
    APIEndpoints --> CoreMiddleware
    CoreMiddleware --> DBSession
    DBSession --> PostgreSQL
    APIEndpoints --> RedisStore
    CoreMiddleware -->|Google GenAI SDK| GeminiNLP
    APIEndpoints -.->|Local Inference| MLDir
```

---

## 2. Luồng Dữ liệu Nghiệp vụ Chính (Data Flow Sequences)

### 2.1. Luồng Trợ lý AI Bóc tách Hàng loạt Món ăn & Khớp Thực đơn Gốc (Batch Quick-Post & Menu Grounding)
1. **Frontend**: Chủ quán bấm ghi âm 1 câu ngắn (hoặc nhập text): *"Còn 5 cơm sườn chả, 3 bún thịt nướng xả từ giờ đến 3h chiều nhé"*.
2. **FastAPI (`POST /api/v1/ml/parse-dish-nlp`)**: Tiếp nhận file audio hoặc text, lấy thời gian thực `current_server_time` của server và truy vấn Thực đơn gốc (`menu_items`) của quán từ PostgreSQL.
3. **Gemini 2.5 Flash (Native Audio & Structured Outputs)**:
   - Nhận trực tiếp luồng Audio + Danh mục Menu gốc + `current_server_time` trong System Prompt.
   - Phân tích ngữ nghĩa, tự động giải mã giờ tương đối (*"từ giờ đến 3h chiều"* $\rightarrow$ `13:55:00` - `15:00:00`).
   - Khớp `matched_menu_id` với từng món trong thực đơn để tự động kế thừa **Ảnh món ăn và Giá gốc**.
   - **Rà soát dị ứng 2 tầng (2-Tier Allergen Guard)**:
     - `EXPLICIT`: Thành phần chủ quán đọc rõ.
     - `INFERRED`: AI suy luận từ công thức món Việt (Trứng trong chả, Nước mắm cá, Đậu phộng trong mỡ hành...) theo chuẩn 14 chất EU FIC.
     - Tách riêng `dietary_notes` (Có hành ngò, cay vừa, ăn chay).
4. **Frontend Preview (Draft Cards)**: Hiển thị danh sách các thẻ món ăn đã có sẵn ảnh đại diện từ Menu gốc, lộ trình giảm giá theo giờ và nút gạt xác nhận dị ứng. Chủ quán chỉ cần 1 chạm **"Đăng tất cả"** để lưu hàng loạt vào bảng `dishes`.

```mermaid
sequenceDiagram
    autonumber
    actor Partner as Chủ cửa hàng
    participant Frontend as Partner Portal (Next.js)
    participant Backend as FastAPI Server
    participant DB as PostgreSQL (menu_items & dishes)
    participant Gemini as Google Gemini 2.5 Flash API

    Partner->>Frontend: Ghi âm giọng nói: "Còn 5 cơm sườn, 3 bún thịt nướng từ giờ đến 3h chiều"
    Frontend->>Backend: POST /api/v1/ml/parse-dish-nlp (audio_file / multipart)
    Backend->>DB: SELECT * FROM menu_items WHERE store_id = :store_id
    DB-->>Backend: Danh sách thực đơn gốc (Tên, Ảnh, Giá gốc, Thành phần)
    Backend->>Gemini: generate_content(model="gemini-2.5-flash", contents=[Audio, MenuContext, current_time], schema=QuickPostExtractionResponse)
    Gemini-->>Backend: JSON: {pickup_start, pickup_end, items: [SurplusDishItem, ...]}
    Backend-->>Frontend: 200 OK (Danh sách món đã khớp Menu ID, ảnh, giá và dị ứng 2 tầng)
    Frontend-->>Partner: Hiển thị Draft Cards (Có ảnh gốc + Tag dị ứng Explicit/Inferred)
    Partner->>Frontend: Bấm "Đăng tất cả (1-Tap Batch Post)"
    Frontend->>Backend: POST /api/v1/dishes/batch
    Backend->>DB: INSERT INTO dishes (menu_item_id, name, original_price, qty, allergens...)
    Backend-->>Frontend: 201 Created (Các món ăn xuất hiện tức thì trên Radar PostGIS)
```

---

### 2.2. Luồng Hệ thống Gợi ý Món ăn Thông minh Cá nhân hóa (AI Smart Recommendation)
Động cơ gợi ý hoạt động theo mô hình **Hybrid Context-Aware Matcher**:
1. **Frontend**: Gửi tọa độ GPS hiện tại của người dùng kèm JWT token xác thực: `GET /api/v1/recommendations/personalized?lat=10.77&lng=106.70`.
2. **Backend**:
   - Truy vấn thông tin `user_preferences` (chế độ ăn, danh sách dị ứng cần tránh, ngân sách ưa thích) và lịch sử 5 đơn hàng gần nhất.
   - Truy vấn PostGIS: Lấy các món ăn khả dụng (`remaining_quantity > 0`) trong bán kính 2km.
   - **Bộ lọc An toàn & Ngữ cảnh**:
     - Loại trừ hoàn toàn các món có chứa chất dị ứng của người dùng.
     - Ưu tiên các món đang bước vào 30 phút cuối của luật giảm giá 70% (Deal khẩn cấp).
   - **Bộ xếp hạng (Scoring)**: Tính điểm phù hợp dựa trên: Khoảng cách (40%) + Mức giảm giá (30%) + Khớp khẩu vị (30%).
3. **Gemini 2.5 Flash**: Nhận thông tin Top 3 món điểm cao nhất và profile tóm tắt của user, sinh ra câu văn giải thích tự nhiên, ngắn gọn (Justification) để hiển thị lên UI.
4. **Trả kết quả**: Trả về danh sách món gợi ý kèm tag "Lý do AI gợi ý".

```mermaid
sequenceDiagram
    autonumber
    actor Consumer as Khách hàng
    participant Frontend as Consumer App (Next.js)
    participant Backend as FastAPI Server
    participant PostGIS as PostgreSQL (Dishes + Preferences)
    participant Gemini as Google Gemini 2.5 Flash API

    Consumer->>Frontend: Mở trang chủ EcoBite
    Frontend->>Backend: GET /api/v1/recommendations/personalized?lat=10.77&lng=106.70
    Backend->>PostGIS: 1. Lấy user_preferences & lịch sử món\n2. Query PostGIS lấy món trong bán kính 2km
    PostGIS-->>Backend: Trả về danh sách ứng viên
    Backend->>Backend: Lọc dị ứng + Chấm điểm Ranking Top 3
    Backend->>Gemini: Yêu cầu sinh câu lý do gợi ý cho Top 3 món
    Gemini-->>Backend: Trả về lý do tự nhiên ("Bạn thích bún vào trưa...")
    Backend-->>Frontend: 200 OK + Danh sách Top 3 kèm ai_justification
    Frontend-->>Consumer: Hiển thị mục "Gợi ý thông minh cho bạn"
```

---

### 2.3. Luồng Luật Giảm giá Theo Khung giờ (Rule-based Time-based Discounting)
Hệ thống EcoBite sử dụng **Luật Thời gian Xác định (Deterministic Business Rules)**:
- Mỗi món ăn có 3 mức giá:
  1. `original_price`: Giá niêm yết ban đầu (ví dụ: `50.000đ`).
  2. `rescue_price`: Giá giải cứu tiêu chuẩn trong khung giờ mở bán (ví dụ: `25.000đ` - giảm 50%).
  3. `rule_discount_price`: Giá giờ chót giảm sâu hơn trong 30-45 phút cuối (ví dụ: `15.000đ` - giảm 70%).
- **Công thức tính giá tại thời điểm $T_{\text{current}}$**:
  $$\text{Current Price} = \begin{cases}
  \text{rule\_discount\_price} & \text{nếu } T_{\text{current}} \ge \text{rule\_discount\_start\_time} \\
  \text{rescue\_price} & \text{nếu } \text{pickup\_start\_time} \le T_{\text{current}} < \text{rule\_discount\_start\_time} \\
  \text{original\_price} & \text{trường hợp khác}
  \end{cases}$$

---

### 2.4. Luồng Sinh & Quét Mã QR Xác nhận Nhận hàng (Pickup Verification)

Để chống gian lận (chụp màn hình gửi người khác, tái sử dụng mã nhiều lần), mã QR sử dụng chữ ký điện tử **HMAC-SHA256 Token**.

```mermaid
sequenceDiagram
    autonumber
    actor Consumer as Khách mua hàng
    actor Partner as Chủ cửa hàng
    participant FrontendCust as App Khách (qrcode.react)
    participant FrontendPart as App Chủ quán (html5-qrcode)
    participant Backend as FastAPI Server
    participant DB as PostgreSQL + Redis

    Consumer->>FrontendCust: Bấm xem mã nhận món #EB-1024
    FrontendCust->>Backend: GET /api/v1/orders/1024/qr-token
    Backend->>Backend: Tạo Token: HMAC_SHA256(order_id + user_id + timestamp + nonce, SECRET)
    Backend-->>FrontendCust: Trả về QR payload signed token
    FrontendCust-->>Consumer: Hiển thị mã QR động

    Partner->>FrontendPart: Bật camera quét mã QR của khách
    FrontendPart->>Backend: POST /api/v1/orders/verify-qr { qr_token: "..." }
    Backend->>Backend: 1. Đối soát chữ ký HMAC\n2. Kiểm tra hạn sử dụng (Timestamp check)\n3. Kiểm tra Replay Attack trong Redis
    Backend->>DB: UPDATE orders SET status = 'COMPLETED', completed_at = NOW()
    Backend->>DB: Cộng Green Points cho User & Store
    Backend-->>FrontendPart: 200 OK - Xác nhận giao hàng thành công!
    Backend-->>FrontendCust: Push Notification: "Đơn hàng đã hoàn tất! Bạn được cộng +50 Điểm Xanh"
```

---

## 3. Kiến trúc Bảo mật & Phân quyền (Security & Authorization)

1. **JWT Dual-Token Authentication**:
   - `Access Token`: Hạn dùng 1 ngày (1440 phút), mang thông tin `sub` (user_id), `role`, `email`.
   - `Refresh Token`: Hạn dùng 30 ngày, lưu mã băm an toàn trong database.
2. **Role-Based Access Control (RBAC)**:
   - Áp dụng cơ chế FastAPI Dependency Injection (`get_current_active_user`, `require_roles(["ADMIN"])`).
3. **Chống Tấn công Đặt hàng Đồng thời (Race Conditions & Over-selling)**:
   - Áp dụng Redis Distributed Lock hoặc PostgreSQL `SELECT ... FOR UPDATE` khi xử lý đơn hàng món ăn cuối cùng.
4. **Bảo mật Mã QR Xác nhận Đơn**:
   - Sử dụng thuật toán HMAC-SHA256 với secret key riêng biệt `QR_SIGNATURE_SECRET`.
   - Mỗi token có hạn sử dụng ngắn và chỉ được chấp nhận 1 lần duy nhất (Single-use Nonce lưu trong Redis với TTL 24 giờ).
