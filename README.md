# 🌱 EcoBite Platform - Food Rescue & Zero-Waste Platform

[![Architecture: Decoupled Three-Tier](https://img.shields.io/badge/Architecture-Decoupled_Three--Tier-00C781.svg)]()
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.111-009688.svg?logo=fastapi)]()
[![Frontend: Next.js 14](https://img.shields.io/badge/Frontend-Next.js_14-black.svg?logo=next.js)]()
[![Database: PostGIS 16](https://img.shields.io/badge/Database-PostgreSQL_16_+_PostGIS_3.4-336791.svg?logo=postgresql)]()
[![Cache: Redis 7](https://img.shields.io/badge/Cache-Redis_7-DC382D.svg?logo=redis)]()
[![ML: PyTorch / YOLOv8](https://img.shields.io/badge/AI%2FML-PyTorch_+_YOLOv8-EE4C2C.svg?logo=pytorch)]()

**EcoBite** là nền tảng công nghệ kết nối trực tiếp các cơ sở kinh doanh ăn uống (tiệm bánh, nhà hàng, quán ăn, siêu thị) với người tiêu dùng có nhu cầu mua thực phẩm cận giờ đóng cửa dưới dạng **Gói Thức ăn Bất ngờ (Surprise Bags)** với mức giá giảm sâu từ 50% - 80%. Dự án hướng tới sứ mệnh giảm lãng phí thực phẩm, cắt giảm phát thải khí nhà kính ($CO_2$) và lan toả phong cách sống xanh bền vững.

---

## 📌 8 Tính năng Cốt lõi (Core Capabilities)

1. **Xác thực & Quản trị Duyệt Quán (Auth & Partner KYC)**: Đăng ký đa vai trò (Consumer, Store Partner, Admin), xác thực JWT Dual-Token, quy trình duyệt giấy phép vệ sinh an toàn thực phẩm.
2. **Đăng Gói thức ăn Ngẫu nhiên & Giảm giá theo Khung giờ (Surprise Bags & Dynamic Pricing)**: Cho phép cửa hàng tạo gói thức ăn bất ngờ kèm cơ chế tự động hạ giá lũy tiến trong 30-45 phút cuối của khung giờ lấy hàng.
3. **Tìm kiếm Theo Vị trí Địa lý (Geo-Spatial Search)**: Tích hợp PostGIS `ST_DWithin` và GIST Spatial Index giúp người mua tìm quán gần nhất trong bán kính 1km - 10km trên bản đồ tương tác Leaflet.
4. **Đặt hàng Sinh Mã QR Bảo mật Động (Order & Dynamic QR Token)**: Cơ chế khóa tồn kho chống over-selling, mã QR chứa chữ ký HMAC-SHA256 có hạn sử dụng và chống chụp màn hình gian lận.
5. **Quét Mã QR Xác nhận Giao hàng tại Quán (QR Scanner Verification)**: Tích hợp camera web scanner (`html5-qrcode`) để chủ quán quét mã QR của khách khi nhận hàng, hoàn tất đơn tức thì.
6. **Đánh giá 1-5 Sao & Nhận xét Chất lượng (Verified Reviews)**: Đánh giá dành riêng cho người đã hoàn thành nhận đơn, kèm ảnh chụp thực tế và gắn tag nhanh.
7. **Hệ thống Thông báo Thời gian thực (Real-time Notifications)**: Cập nhật trạng thái đơn hàng và gửi cảnh báo mở bán gói thức ăn giảm sâu qua Redis Pub/Sub và WebSocket.
8. **Tích Điểm Xanh & Đo lường Giảm Phát thải CO2 (Green Points & CO2 Tracker)**: Tự động tính toán lượng $CO_2$ tiết kiệm được (1kg thức ăn $\approx$ 2.5kg $CO_2e$), tích luỹ Điểm Xanh đổi mã giảm giá voucher.

---

## 🏗️ Cấu trúc Cây Thư mục Dự án

Cấu trúc dự án được phân tách rành mạch (Decoupled Architecture), đặc biệt thư mục `ml/` nằm hoàn toàn độc lập bên ngoài `backend/`:

```text
EcoBite-Platform/
├── .gitignore                          # Cấu hình bỏ qua file nhạy cảm, cache và file trọng số lớn
├── .env.example                        # Mẫu biến môi trường chuẩn
├── .env                                # Biến môi trường cục bộ đang kích hoạt
├── docker-compose.yml                  # Cấu hình Docker cho PostGIS 16 và Redis 7
├── README.md                           # Tài liệu tổng quan dự án
├── docs/                               # Bộ tài liệu Quản lý Dự án & Kỹ thuật chi tiết
│   ├── 01_PRD_and_User_Stories.md      # Đặc tả yêu cầu sản phẩm & 8 User Stories
│   ├── 02_System_Architecture.md       # Thiết kế kiến trúc, Sequence Diagrams & Lifespan
│   ├── 03_Database_Schema_ERD.md       # Thiết kế CSDL PostgreSQL/PostGIS, ERD Mermaid
│   ├── 04_API_Specification.md         # Đặc tả chi tiết RESTful API endpoints v1
│   ├── 05_Agile_Roadmap_and_Kanban.md  # Kế hoạch Sprint (6 Sprints), DoR, DoD & Rủi ro
│   └── 06_Environment_and_ML_Setup_Guide.md # Cẩm nang cài đặt chi tiết từ A-Z
├── ml/                                 # Không gian làm việc Machine Learning độc lập
│   ├── README.md                       # Quy ước đặt tên file .pt & giao tiếp Backend
│   ├── requirements.txt                # Thư viện phục vụ huấn luyện (Ultralytics, Scikit, Jupyter)
│   ├── notebooks/                      # Jupyter Notebooks nghiên cứu & huấn luyện mô hình
│   ├── datasets/                       # Dữ liệu ảnh thực phẩm & nhãn dán (đã gitignore)
│   └── weights/                        # Lưu trữ file trọng số .pt để Backend nạp khi chạy
├── backend/                            # Ứng dụng Backend Web API (Python FastAPI)
│   ├── requirements.txt                # Thư viện phục vụ API & Inference (.pt)
│   ├── alembic.ini                     # Cấu hình Database Migrations
│   ├── alembic/                        # Thư mục chứa các phiên bản migration
│   └── app/                            # Mã nguồn ứng dụng (Chưa viết code nghiệp vụ)
│       ├── core/                       # Cấu hình bảo mật, Settings, Database Session
│       ├── models/                     # SQLAlchemy ORM Models
│       ├── schemas/                    # Pydantic Schemas / DTOs
│       ├── services/                   # Business Logic & Helpers
│       └── api/v1/endpoints/           # API Route Controllers
└── frontend/                           # Giao diện Người dùng (Next.js 14 App Router)
    ├── package.json                    # Khai báo thư viện (Leaflet, QR, TanStack Query)
    ├── .npmrc                          # Cấu hình strict engine
    ├── public/                         # Static assets (icons, illustrations)
    └── src/
        ├── app/
        │   ├── (consumer)/             # Luồng giao diện Người tiêu dùng
        │   ├── (store-partner)/        # Luồng giao diện Đối tác Cửa hàng (Scanner)
        │   └── (admin)/                # Luồng giao diện Quản trị viên
        ├── components/                 # Tái sử dụng UI components
        └── lib/                        # Axios instance, Map helpers, QR utilities
```

---

## ⚡ Hướng dẫn Khởi động Nhanh (Quick Start)

### 1. Khởi động Cơ sở Dữ liệu & Redis
```bash
# Đảm bảo bạn đang ở thư mục gốc EcoBite-Platform
docker compose up -d

# Xác nhận cả 2 container ở trạng thái Up (healthy)
docker compose ps
```

### 2. Thiết lập Backend (FastAPI)
```bash
cd backend
python3 -m venv venv_backend
source venv_backend/bin/activate
pip install -r requirements.txt
# (Tùy chọn) Chạy server khi đã có code main:
# uvicorn app.main:app --reload --port 8000
deactivate
cd ..
```

### 3. Thiết lập Machine Learning Subsystem (Huấn luyện Mô hình)
```bash
cd ml
python3 -m venv venv_ml
source venv_ml/bin/activate
pip install -r requirements.txt
# Khởi chạy JupyterLab để làm việc với Notebooks
# jupyter lab --notebook-dir=notebooks
deactivate
cd ..
```

### 4. Thiết lập Frontend (Next.js)
```bash
cd frontend
npm install
# Khởi chạy Next.js development server
# npm run dev
cd ..
```

---

## 🧠 Cơ chế Kết nối Model ML (`ml/weights/*.pt`) với Backend

1. **Tách biệt Môi trường**: `ml/` chứa bộ công cụ training nặng (`ultralytics`, `jupyterlab`), trong khi `backend/` chỉ cài đặt `torch` runtime gọn nhẹ.
2. **Cấu hình Đường dẫn**: File `.env` chứa biến `ML_WEIGHTS_DIR=../ml/weights` và `ML_MODEL_FILENAME=food_quality_yolov8.pt`.
3. **Lifespan Singleton Pattern**: File trọng số `.pt` được nạp vào RAM/VRAM **đúng một lần duy nhất** khi ứng dụng FastAPI khởi động (`lifespan startup`), lưu trữ tại `app.state.ml_model`. Mọi request suy luận chỉ việc gọi hàm dự đoán từ instance đã có sẵn trong bộ nhớ, loại bỏ hoàn toàn độ trễ đọc đĩa (Disk I/O bottleneck).
4. **Dev Fallback Mode**: Khi chưa có file `.pt` thực tế, hệ thống tự động kích hoạt chế độ Mock Inference (`ML_FALLBACK_TO_MOCK=True`) để không chặn luồng phát triển của Frontend và Mobile.

---

## 📚 Bộ Tài liệu Kỹ thuật Chi tiết (Documentation Index)

| Tài liệu | Mô tả nội dung chính |
| :--- | :--- |
| 📄 [`docs/01_PRD_and_User_Stories.md`](docs/01_PRD_and_User_Stories.md) | Mục tiêu sản phẩm, phân tích Persona, đặc tả 8 tính năng cốt lõi & User Stories. |
| 🏗️ [`docs/02_System_Architecture.md`](docs/02_System_Architecture.md) | Sơ đồ kiến trúc Clean Architecture, luồng dữ liệu Geo-Search, QR HMAC & ML Lifespan. |
| 🗄️ [`docs/03_Database_Schema_ERD.md`](docs/03_Database_Schema_ERD.md) | Thiết kế CSDL PostgreSQL/PostGIS, sơ đồ Mermaid ERD, các bảng và chiến lược GIST Index. |
| 🔌 [`docs/04_API_Specification.md`](docs/04_API_Specification.md) | Tài liệu RESTful API v1 đầy đủ Request/Response schemas, mã lỗi và phân quyền. |
| 📋 [`docs/05_Agile_Roadmap_and_Kanban.md`](docs/05_Agile_Roadmap_and_Kanban.md) | Phân chia 6 Sprint (12 tuần), Definition of Ready, Definition of Done & Ma trận Rủi ro. |
| 🛠️ [`docs/06_Environment_and_ML_Setup_Guide.md`](docs/06_Environment_and_ML_Setup_Guide.md) | Cẩm nang cài đặt chi tiết Docker, venv riêng cho Backend và ML, Lifespan code mẫu. |
| 🤖 [`ml/README.md`](ml/README.md) | Quy chuẩn đặt tên file `.pt`, metadata format, quy trình export và giao tiếp với Backend. |

---

## 👥 Nhóm Thực hiện & Nguyên tắc Phát triển (Principles)
- **Zero Business Code at Scaffolding Stage**: Tuyệt đối giữ các thư mục `app/` và `src/` sạch sẽ với các file `.gitkeep` trước khi bắt đầu Sprint 1.
- **Strict Environment Isolation**: Giữ môi trường ảo `backend/venv_backend` và `ml/venv_ml` độc lập 100%.
- **Security First**: Không commit secrets lên Git, luôn sử dụng HMAC-SHA256 cho mã QR động và mã hóa bcrypt cho mật khẩu.
