# EcoBite Platform - System Architecture & Technical Design

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh  
**Tác giả**: Senior DevOps Engineer & Technical Project Manager  
**Phiên bản**: 1.0.0  

---

## 1. Kiến trúc Hệ thống Tổng quan (High-Level Architecture)

Hệ thống EcoBite được thiết kế theo mô hình **Decoupled Three-Tier Architecture** kết hợp thành phần **AI/ML Inference Pipeline độc lập**.

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer (Next.js 14 App Router)"]
        ConsumerApp["Consumer Web / Mobile PWA\n(Leaflet Map, QR Viewer)"]
        PartnerPortal["Store Partner Portal\n(html5-qrcode Scanner)"]
        AdminDashboard["System Admin Dashboard\n(KYC Review, Metrics)"]
    end

    subgraph Gateway ["Edge & Security"]
        NginxGateway["Reverse Proxy / SSL / CORS\n(Port 80/443)"]
    end

    subgraph BackendLayer ["Backend Application (FastAPI Asynchronous Runtime)"]
        APIEndpoints["FastAPI Routers (/api/v1)\n- Auth, Stores, Packages\n- Orders, QR Verify, Reviews, GreenPoints"]
        CoreMiddleware["Core Services & Middlewares\n- JWT RBAC Guard\n- HMAC QR Signer\n- Lifespan State Manager"]
        DBSession["Async SQLAlchemy 2.0 Engine\n(asyncpg connection pool)"]
    end

    subgraph DataLayer ["Data & Cache Layer (Docker Compose)"]
        PostgreSQL["PostgreSQL 16 + PostGIS 3.4\n- Spatial Geometry(Point, 4326)\n- GIST Spatial Index\n- ACID Transaction Engine"]
        RedisStore["Redis 7\n- Rate Limiting\n- Inventory Locks\n- Pub/Sub Notifications\n- Session/Token Blacklist"]
    end

    subgraph MLLayer ["Decoupled Machine Learning Subsystem"]
        MLDir["ml/weights/*.pt\n(PyTorch / TorchScript Checkpoints)"]
        ModelSingleton["FastAPI Lifespan Model Loader\n(RAM / VRAM Singleton)"]
    end

    ClientLayer -->|HTTPS / REST / WSS| NginxGateway
    NginxGateway --> APIEndpoints
    APIEndpoints --> CoreMiddleware
    CoreMiddleware --> DBSession
    DBSession --> PostgreSQL
    APIEndpoints --> RedisStore
    APIEndpoints --> ModelSingleton
    ModelSingleton -.->|Loads on Startup| MLDir
```

---

## 2. Luồng Dữ liệu Nghiệp vụ Chính (Data Flow Sequences)

### 2.1. Luồng Tìm kiếm Quán Theo Bán kính Vị trí (Spatial Geo-Search)
1. **Frontend**: Trình duyệt lấy tọa độ GPS hiện tại của người dùng (`lat`, `lng`).
2. **FastAPI**: Endpoint `GET /api/v1/stores/nearby?lat=10.7769&lng=106.7009&radius_km=3` tiếp nhận yêu cầu.
3. **Database (PostGIS)**: Thực thi truy vấn không gian sử dụng hàm `ST_DWithin` và toán tử `ST_Distance` trên trường `stores.location` (kiểu dữ liệu `geometry(Point, 4326)`) được đánh chỉ mục không gian `GIST Index`.
4. **Cache**: Kết quả truy vấn các cửa hàng trong khu vực lân cận được cache tại Redis trong thời gian ngắn (TTL = 60s) để giảm tải cho database khi lưu lượng người dùng cao.

```mermaid
sequenceDiagram
    autonumber
    actor Consumer as Người tiêu dùng
    participant NextJS as Frontend (Next.js + Leaflet)
    participant FastAPI as Backend (FastAPI)
    participant Redis as Redis Cache
    participant PostGIS as PostgreSQL (PostGIS)

    Consumer->>NextJS: Mở bản đồ tìm quán gần tôi
    NextJS->>NextJS: Lấy tọa độ GPS (navigator.geolocation)
    NextJS->>FastAPI: GET /api/v1/stores/nearby?lat=10.77&lng=106.70&radius=3
    FastAPI->>Redis: Check cache "geo:3km:10.77:106.70"
    alt Cache Hit
        Redis-->>FastAPI: Trả về danh sách quán (JSON)
    else Cache Miss
        FastAPI->>PostGIS: SELECT * FROM stores WHERE ST_DWithin(location, ST_MakePoint(lng, lat)::geography, 3000)
        PostGIS-->>FastAPI: Trả về records với distance_meters
        FastAPI->>Redis: SETEX cache TTL 60s
    end
    FastAPI-->>NextJS: 200 OK + Danh sách quán & Gói Surprise Bags
    NextJS-->>Consumer: Render marker & card trên bản đồ
```

---

### 2.2. Luồng Sinh & Quét Mã QR Xác nhận Nhận hàng (Pickup Verification)

Để chống gian lận (chụp màn hình gửi người khác, tái sử dụng mã nhiều lần), mã QR không lưu plain text `order_id` mà sử dụng chuỗi ký điện tử **HMAC-SHA256 Token**.

```mermaid
sequenceDiagram
    autonumber
    actor Consumer as Khách mua hàng
    actor Partner as Chủ cửa hàng
    participant FrontendCust as App Khách (qrcode.react)
    participant FrontendPart as App Chủ quán (html5-qrcode)
    participant Backend as FastAPI Server
    participant DB as PostgreSQL + Redis

    Consumer->>FrontendCust: Bấm xem mã nhận đơn #EB-1024
    FrontendCust->>Backend: GET /api/v1/orders/1024/qr-token
    Backend->>Backend: Tạo Token: HMAC_SHA256(order_id + user_id + timestamp + nonce, SECRET)
    Backend-->>FrontendCust: Trả về QR payload signed token
    FrontendCust-->>Consumer: Hiển thị mã QR động

    Partner->>FrontendPart: Bật camera quét mã QR của khách
    FrontendPart->>Backend: POST /api/v1/orders/verify-qr { qr_token: "..." }
    Backend->>Backend: 1. Giải mã & đối soát chữ ký HMAC\n2. Kiểm tra hạn sử dụng (Timestamp check)\n3. Kiểm tra Replay Attack trong Redis
    Backend->>DB: UPDATE orders SET status = 'COMPLETED', completed_at = NOW()
    Backend->>DB: Cộng Green Points cho User & Store
    Backend-->>FrontendPart: 200 OK - Xác nhận giao hàng thành công!
    Backend-->>FrontendCust: Push Notification: "Đơn hàng đã hoàn tất! Bạn được cộng +50 Điểm Xanh"
```

---

## 3. Kiến trúc Tích hợp Machine Learning (Decoupled ML Lifespan Architecture)

### 3.1. Phân tách Trách nhiệm (Decoupling)
- **Thư mục `ml/`**: Là môi trường dành cho việc phát triển mô hình, chứa các công cụ đào tạo nặng (`ultralytics`, `jupyterlab`, `scikit-learn`, `pandas`).
- **Thư mục `backend/`**: Là môi trường Web API gọn nhẹ. Chỉ cài đặt `torch` và `torchvision` (runtime inference) nhằm tối ưu dung lượng container và tốc độ khởi động.

### 3.2. Cơ chế Singleton & FastAPI Lifespan Manager
Để đảm bảo hiệu năng xử lý cực đại, Backend tuyệt đối không nạp file trọng số `.pt` ở từng request. Toàn bộ trọng số được nạp sẵn vào bộ nhớ (RAM/VRAM) trong sự kiện khởi động ứng dụng:

```python
# Minh họa luồng nạp Lifespan trong FastAPI
from contextlib import asynccontextmanager
from fastapi import FastAPI
import torch
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    weights_dir = os.getenv("ML_WEIGHTS_DIR", "../ml/weights")
    model_name = os.getenv("ML_MODEL_FILENAME", "food_quality_yolov8.pt")
    weights_path = os.path.join(weights_dir, model_name)
    device = torch.device(os.getenv("ML_DEVICE", "cpu"))

    if os.path.exists(weights_path):
        # Nạp mô hình một lần duy nhất vào memory
        app.state.ml_model = torch.load(weights_path, map_location=device)
        app.state.ml_model.eval()
        app.state.ml_ready = True
    else:
        # Fallback chế độ mô phỏng cho môi trường dev khi chưa có weights thật
        app.state.ml_model = None
        app.state.ml_ready = False

    yield  # Ứng dụng tiếp nhận các HTTP requests

    # --- SHUTDOWN LOGIC ---
    # Thu dọn tài nguyên, giải phóng VRAM
    if hasattr(app.state, "ml_model") and app.state.ml_model is not None:
        del app.state.ml_model
```

---

## 4. Kiến trúc Bảo mật & Phân quyền (Security & Authorization)

1. **JWT Dual-Token Authentication**:
   - `Access Token`: Hạn dùng 1 ngày (1440 phút), mang thông tin `sub` (user_id), `role`, `email`.
   - `Refresh Token`: Hạn dùng 30 ngày, lưu mã băm an toàn trong database.
2. **Role-Based Access Control (RBAC)**:
   - Áp dụng cơ chế FastAPI Dependency Injection (`get_current_active_user`, `require_roles(["ADMIN"])`).
3. **Chống Tấn công Đặt hàng Đồng thời (Race Conditions & Over-selling)**:
   - Áp dụng Redis Distributed Lock hoặc PostgreSQL `SELECT ... FOR UPDATE` khi xử lý đơn hàng gói Surprise Bag cuối cùng.
4. **Bảo mật Mã QR Xác nhận Đơn**:
   - Sử dụng thuật toán HMAC-SHA256 với secret key riêng biệt `QR_SIGNATURE_SECRET`.
   - Mỗi token có hạn sử dụng ngắn và chỉ được chấp nhận 1 lần duy nhất (Single-use Nonce lưu trong Redis với TTL 24 giờ).
