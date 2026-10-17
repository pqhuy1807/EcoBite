# 🌱 EcoBite Platform - Food Rescue & Zero-Waste Platform

---

## 👥 Thành viên Thực hiện (Group 05 - FIT HCMUS)

| MSSV | Họ và tên | Vai trò chính trong dự án | Email FIT |
| :--- | :--- | :--- | :--- |

| **24127402** | **Phùng Quốc Huy** | **AI & Data Lead** | `pqhuy2425@clc.fitus.edu.vn` |
| 24127561 | Đàng Thế Tony | QA/Tester Lead & Backend | `dttony2424@clc.fitus.edu.vn` |
| 24127246 | Võ Ngọc Thịnh | Frontend Lead | `vnthinh2418@clc.fitus.edu.vn` |
| 24127495 | Đặng Trọng Phúc | Backend Lead & AI Engineer | `dtphuc2418@clc.fitus.edu.vn` |

---

## 🎯 Đối tượng Sử dụng & Môi trường Vận hành

### 1. Đối tượng người dùng (Target Users)
- **Consumers (Người giải cứu thực phẩm)**: Sinh viên, nhân viên văn phòng tìm kiếm các bữa ăn chất lượng hợp vệ sinh với giá ưu đãi (giảm 40% - 70%) và có ý thức giảm thiểu lãng phí thực phẩm đô thị.
- **Store Partners (Đối tác Cửa hàng)**: Tiệm bánh, nhà hàng, quán cà phê, siêu thị muốn tối ưu hoá chi phí nguyên liệu và thu hồi doanh thu từ món ăn dư thừa cuối ca.
- **System Administrators (Quản trị viên)**: Đội ngũ vận hành chịu trách nhiệm xác minh chứng nhận An toàn Vệ sinh Thực phẩm (ATVSTP), duyệt cửa hàng và giám sát chỉ số môi trường.

### 2. Môi trường vận hành (Target Environments)
- **Client Application**: Progressive Web App (PWA) đa nền tảng xây dựng bằng Next.js 14 App Router, Tailwind CSS, tương thích di động và máy tính.
- **Backend Infrastructure**: FastAPI (Python 3.11), PostgreSQL 16 + PostGIS (truy vấn không gian địa lý), Redis 7 (lưu cache & khoá chống bán vượt tồn kho) và Google GenAI SDK (Gemini 2.5 Flash).

---

## 💡 Điểm Khác Bật Cốt Lõi của EcoBite

Khác với các nền tảng phương Tây như *Too Good To Go* hay *Yindii* (sử dụng "Túi mù" / Mystery Bags):
1. **Minh bạch 100% từng món ăn (No Mystery Bags)**: Hiển thị rõ tên món, hình ảnh chân thực, thành phần và cảnh báo dị ứng 2 tầng theo chuẩn 14 chất dị ứng EU FIC.
2. **Giảm giá theo khung giờ tất định (Rule-Based Time-Shift Discounting)**: Tự động hạ giá minh bạch (giảm 40%-50% giờ giải cứu tiêu chuẩn, giảm tới 70% trong 30-45 phút cuối trước khi đóng cửa).
3. **Đăng món siêu tốc bằng AI giọng nói**: Tận dụng Google Gemini 2.5 Flash nhận diện tiếng lóng ẩm thực Việt Nam (*"bốn lăm cành"*, *"bì chả"*), bóc tách danh mục món và rà soát dị ứng chỉ trong 3 giây.


[![Architecture: Decoupled Three-Tier](https://img.shields.io/badge/Architecture-Decoupled_Three--Tier-00C781.svg)]()
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.111-009688.svg?logo=fastapi)]()
[![Frontend: Next.js 14](https://img.shields.io/badge/Frontend-Next.js_14-black.svg?logo=next.js)]()
[![Database: PostGIS 16](https://img.shields.io/badge/Database-PostgreSQL_16_+_PostGIS_3.4-336791.svg?logo=postgresql)]()
[![Cache: Redis 7](https://img.shields.io/badge/Cache-Redis_7-DC382D.svg?logo=redis)]()
[![AI: Google Gemini 2.5 Flash](https://img.shields.io/badge/AI%2FNLP-Gemini_2.5_Flash-4285F4.svg?logo=google)]()
[![ML: PyTorch](https://img.shields.io/badge/AI%2FML-PyTorch-EE4C2C.svg?logo=pytorch)]()

**EcoBite** là nền tảng công nghệ kết nối trực tiếp các cơ sở kinh doanh ăn uống (tiệm bánh, nhà hàng, quán ăn, siêu thị) với người tiêu dùng có nhu cầu mua **các món ăn dư thừa trong ngày (Surplus Food Dishes)** với mức giá giải cứu giảm sâu từ 40% - 70%. Dự án hướng tới sứ mệnh giảm lãng phí thực phẩm, cắt giảm phát thải khí nhà kính ($CO_2$) và lan toả phong cách sống xanh bền vững.

---

## 📌 Nhóm Tính năng Nền tảng & Vận hành O2O (Core Platform)

1. **Xác thực & Quản trị Duyệt Quán (Auth & Partner KYC)**: Đăng ký đa vai trò (`CONSUMER`, `STORE_PARTNER`, `ADMIN`), xác thực JWT Dual-Token, quy trình kiểm duyệt giấy phép vệ sinh an toàn thực phẩm.
2. **Quản lý Món ăn & Giảm giá theo Khung giờ Rule-based (Dish Management & Rule-based Discounting)**: Đăng từng món ăn cụ thể còn dư trong ngày. Cài đặt luật giảm giá theo khung giờ (ví dụ: giờ vàng giảm 40%-50%; 30-45 phút cuối trước giờ đóng cửa tự động áp dụng luật hạ giá sâu 70% để xả sạch thực phẩm).
3. **Tìm kiếm Theo Vị trí Địa lý (Geo-Spatial Search)**: Tích hợp PostGIS `ST_DWithin` và GIST Spatial Index giúp người mua tìm các quán và món ăn đang giảm giá gần nhất trong bán kính 1km - 10km trên bản đồ tương tác Leaflet.
4. **Đặt hàng & Khóa Tồn kho Chống Bán Vượt (Inventory Atomic Lock)**: Cơ chế Transaction/Redis Lock bảo đảm tính toàn vẹn tồn kho khi nhiều người cùng đặt món cuối cùng.
5. **Sinh Mã QR Bảo mật Động (Dynamic HMAC QR Token)**: Mã QR chứa chữ ký HMAC-SHA256 theo đơn hàng và khung giờ lấy món, chống chụp màn hình chia sẻ bừa bãi.
6. **Quét Mã QR Xác nhận Giao hàng tại Quán (QR Scanner Verification)**: Tích hợp camera web scanner (`html5-qrcode`) để chủ quán quét mã QR của khách khi nhận món, đổi trạng thái sang `COMPLETED`, chống Replay Attack (quét 2 lần).
7. **Đánh giá Món ăn Thực tế (Verified Dish Reviews)**: Đánh giá 1-5 sao dành riêng cho người đã nhận món thành công, kèm ảnh chụp thực tế và gắn tag nhanh.
8. **Tích Điểm Xanh & Đo lường Giảm Phát thải CO2 (Green Points & CO2 Tracker)**: Tự động tính toán lượng $CO_2$ tiết kiệm được (1 suất ăn $\approx$ 2.5kg $CO_2e$), tích luỹ Điểm Xanh đổi mã giảm giá voucher.

---

## 🤖 Nhóm Tính năng Trí Tuệ Nhân Tạo (AI Intelligence Suite - Powered by Google Gemini 2.5 Flash)

1. **Trợ lý AI Đăng Món Siêu Tốc & Rà Soát Dị Ứng 2 Tầng (Batch Quick-Post NLP & Allergen Guard)**:
   - *Menu-Catalog Grounding*: So khớp ngữ nghĩa với Thực đơn gốc (`menu_items`) của quán để tự động kéo Ảnh món ăn chất lượng cao, Giá gốc và kích hoạt Luật giảm giá theo thời gian; hỗ trợ ghi đè giá (`override_discounted_price`) nếu chủ quán đọc giá xả cố định.
   - *Suy luận Dị ứng 2 Tầng (2-Tier Allergen Guard)*: Tách bạch rõ `EXPLICIT` (chủ quán đọc) và `INFERRED` (AI suy luận tri thức ẩm thực Việt: trứng trong chả, cá trong nước mắm, đậu phộng trong mỡ hành...) theo chuẩn 14 chất dị ứng quốc tế EU FIC; bổ sung nhãn khẩu vị địa phương `dietary_notes` (hành/ngò Allium, đồ cay, đồ chua, ăn chay).
   - *Trích xuất Hàng loạt (Batch Extraction)*: Cho phép chủ quán thu âm một mạch nhiều món dư cuối ca (`List[SurplusDishItem]`) và áp dụng chung khung giờ chỉ trong 1 lần nói.
   - *Xử lý Thời gian Tương đối (Relative Time)*: Tiếp nhận `current_server_time` để tự động tính toán giờ bắt đầu và kết thúc nhận món tuyệt đối từ câu nói tương đối (*"bán từ giờ đến 3h chiều"* $\rightarrow$ `13:55:00` - `15:00:00`).
   - *Native Multimodal Audio*: Gửi trực tiếp file ghi âm ngắn sang Gemini 2.5 Flash kèm ngữ cảnh thực đơn, nhận diện chính xác tiếng lóng ẩm thực Việt Nam (*"bốn lăm cành"*, *"bì chả"*) mà không phụ thuộc vào STT trung gian dễ sai lệch.
2. **Hệ thống Gợi ý Món ăn Thông minh Cá nhân hóa (AI Smart Food Recommendation Engine)**:
   - *Context-Aware Matching*: Tự động đề xuất các món ăn ngon gần vị trí hiện tại (1km - 3km) phù hợp với thời điểm trong ngày (bữa trưa/bữa tối) và ưu tiên các món đang bước vào khung giờ chót xả hàng gấp (Urgent Rescue Deals).
   - *Sở thích & Chế độ ăn*: Học từ lịch sử đặt món, ngân sách trung bình và tự động loại trừ các món có thành phần dị ứng của khách hàng (Hard Filter ở tầng SQL).
   - *AI Justification Generator*: Gemini 2.5 Flash sinh ra lời giải thích tự nhiên thuyết phục cho từng gợi ý (*"Món này gợi ý cho bạn vì bạn thích món bún vào bữa trưa và quán cách bạn chỉ 300m đang có deal giảm 50% chỉ còn 25k!"*).

---

## 🏗️ Cấu trúc Cây Thư mục Dự án

```text
EcoBite-Platform/
├── .gitignore                          # Cấu hình bỏ qua file nhạy cảm, cache và file trọng số lớn
├── .env.example                        # Mẫu biến môi trường chuẩn (Postgres, Redis, Gemini API)
├── .env                                # Biến môi trường cục bộ đang kích hoạt
├── .pre-commit-config.yaml             # Chốt chặn Git Hook tự động (Ruff, Secrets, File size)
├── AGENTS.md                           # Bộ quy tắc & Chu trình phát triển TDD bắt buộc cho AI
├── docker-compose.yml                  # Cấu hình Docker cho PostGIS 16 và Redis 7
├── README.md                           # Tài liệu tổng quan dự án
├── docs/                               # Bộ tài liệu Quản lý Dự án & Kỹ thuật chi tiết
│   ├── 01_PRD_and_User_Stories.md      # Đặc tả yêu cầu sản phẩm & 8 User Stories
│   ├── 02_System_Architecture.md       # Thiết kế kiến trúc, Sequence Diagrams, Gemini NLP & Lifespan
│   ├── 03_Database_Schema_ERD.md       # Thiết kế CSDL PostgreSQL/PostGIS (bảng dishes, orders...), ERD Mermaid
│   ├── 04_API_Specification.md         # Đặc tả chi tiết RESTful API v1 (/dishes, /ml/parse-dish-nlp...)
│   ├── 05_Agile_Roadmap_and_Kanban.md  # Kế hoạch Sprint (6 Sprints), DoR, DoD & Rủi ro
│   ├── 06_Environment_and_ML_Setup_Guide.md # Cẩm nang cài đặt chi tiết (Docker, venv, Gemini API Key)
│   └── 07_AI_Development_Workflow_and_Quality_Gates.md # Hướng dẫn chu trình TDD & Hooks
├── ml/                                 # Không gian làm việc Machine Learning độc lập
│   ├── README.md                       # Quy chuẩn ML/NLP & giao tiếp Backend
│   ├── requirements.txt                # Thư viện phục vụ huấn luyện (Ultralytics, Scikit, Jupyter)
│   ├── notebooks/                      # Jupyter Notebooks nghiên cứu & thử nghiệm mô hình
│   ├── datasets/                       # Dữ liệu ảnh & văn bản thực phẩm (đã gitignore)
│   └── weights/                        # Lưu trữ file trọng số (.pt) nạp khi chạy
├── backend/                            # Ứng dụng Backend Web API (Python FastAPI)
│   ├── requirements.txt                # Thư viện phục vụ API, Gemini SDK & PyTorch runtime
│   ├── alembic.ini                     # Cấu hình Database Migrations
│   ├── alembic/                        # Thư mục chứa các phiên bản migration
│   ├── app/                            # Mã nguồn ứng dụng
│   │   ├── core/                       # Cấu hình bảo mật, Settings, Database Session
│   │   ├── models/                     # SQLAlchemy ORM Models (Dish, Order, User...)
│   │   ├── schemas/                    # Pydantic Schemas / DTOs
│   │   ├── services/                   # Business Logic, NLP Service & Helpers
│   │   └── api/v1/endpoints/           # API Route Controllers
│   └── tests/                          # Hệ thống kiểm thử tự động Backend
│       ├── unit/                       # Unit tests logic độc lập (NLP parser, rule discount, QR HMAC)
│       └── integration/                # Integration tests kết nối DB PostGIS & API
└── frontend/                           # Giao diện Người dùng (Next.js 14 App Router)
    ├── package.json                    # Khai báo thư viện (Leaflet, QR, TanStack Query)
    ├── .npmrc                          # Cấu hình strict engine
    ├── public/                         # Static assets (icons, illustrations)
    ├── src/
    │   ├── app/
    │   │   ├── (consumer)/             # Luồng giao diện Người tiêu dùng
    │   │   ├── (store-partner)/        # Luồng giao diện Đối tác (Quick-Post AI, Scanner)
    │   │   └── (admin)/                # Luồng giao diện Quản trị viên
    │   ├── components/                 # Tái sử dụng UI components
    │   └── lib/                        # Axios instance, Map helpers, QR utilities
    └── __tests__/                      # Hệ thống kiểm thử tự động Frontend
        ├── components/                 # Test giao diện người dùng
        └── hooks/                      # Test custom hooks & query logic
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

### 2. Thiết lập Biến môi trường (.env)
```bash
cp .env.example .env
# Mở file .env và điền GEMINI_API_KEY (lấy miễn phí từ Google AI Studio với tài khoản Google AI Pro)
```

### 3. Thiết lập Backend (FastAPI)
```bash
cd backend
# Tạo và kích hoạt môi trường ảo Python 3.11
conda activate ecobite_backend
# hoặc: python3 -m venv venv_backend && source venv_backend/bin/activate

pip install -r requirements.txt
# Khởi chạy server:
# uvicorn app.main:app --reload --port 8000
cd ..
```

### 4. Thiết lập Frontend (Next.js)
```bash
cd frontend
npm install
# Khởi chạy Next.js development server:
# npm run dev
cd ..
```

---

## 🤖 Động cơ AI NLP (Google Gemini 2.5 Flash Free Tier)

1. **Model Phù hợp**: Sử dụng model **`gemini-2.5-flash`** thông qua Google GenAI SDK chính thức (`google-genai`).
2. **Tận dụng Gói Miễn phí (Free Tier)**:
   - Tài khoản Google AI Pro / Google AI Studio cung cấp hạn ngạch miễn phí cực lớn (15 RPM, 1M TPM, 1,500 RPD hoàn toàn miễn phí), đủ chạy cho toàn bộ quá trình phát triển, kiểm thử và bảo vệ đồ án.
3. **Tính năng Structured Output**: Áp dụng cơ chế Pydantic Schema Enforcement để đảm bảo mô hình trả về dữ liệu JSON có cấu trúc chính xác 100%, không bị văng lỗi định dạng văn bản.
4. **Quy tắc Giảm giá theo Khung giờ (Rule-based Time-based Discounting)**:
   - Thay vì dùng mô hình AI phỏng đoán giá gây bất định và khó giải trình, hệ thống dùng **luật thời gian tường minh (Deterministic Rule-based Logic)**:
     - Giá giải cứu (`rescue_price`): Giảm 40% - 50% trong suốt khung giờ mở bán.
     - Giá giờ chót (`rule_discount_price`): Tự động giảm 70% trong 30-45 phút cuối trước giờ đóng cửa để xả hết thực phẩm.

---

## 📚 Bộ Tài liệu Kỹ thuật Chi tiết (Documentation Index)

| Tài liệu | Mô tả nội dung chính |
| :--- | :--- |
| 📄 [`docs/01_PRD_and_User_Stories.md`](docs/01_PRD_and_User_Stories.md) | Mục tiêu sản phẩm, Persona, đặc tả 9 tính năng cốt lõi (Món ăn thông thường + AI NLP) & User Stories. |
| 🏗️ [`docs/02_System_Architecture.md`](docs/02_System_Architecture.md) | Sơ đồ kiến trúc Clean Architecture, luồng dữ liệu Geo-Search, QR HMAC, Gemini NLP Pipeline. |
| 🗄️ [`docs/03_Database_Schema_ERD.md`](docs/03_Database_Schema_ERD.md) | Thiết kế CSDL PostgreSQL/PostGIS (bảng `dishes`, `orders`), Mermaid ERD và chiến lược GIST Index. |
| 🔌 [`docs/04_API_Specification.md`](docs/04_API_Specification.md) | Tài liệu RESTful API v1 đầy đủ Request/Response schemas (`/dishes`, `/ml/parse-dish-nlp`). |
| 📋 [`docs/05_Agile_Roadmap_and_Kanban.md`](docs/05_Agile_Roadmap_and_Kanban.md) | Phân chia 6 Sprint (12 tuần), Definition of Ready, Definition of Done & Ma trận Rủi ro. |
| 🛠️ [`docs/06_Environment_and_ML_Setup_Guide.md`](docs/06_Environment_and_ML_Setup_Guide.md) | Cẩm nang cài đặt chi tiết Docker, venv, cấu hình Gemini API Key và code mẫu NLP Parser. |
| 🛡️ [`docs/07_AI_Development_Workflow_and_Quality_Gates.md`](docs/07_AI_Development_Workflow_and_Quality_Gates.md) | Quy trình kiểm thử TDD, hướng dẫn cài đặt Git Pre-commit Hook & Quality Gates. |
| 🤖 [`ml/README.md`](ml/README.md) | Quy chuẩn ML/NLP, cấu trúc metadata format và hướng dẫn Backend gọi model inference. |
| 📜 [`AGENTS.md`](AGENTS.md) | Bộ quy tắc & chu trình kiểm thử tự động bắt buộc dành cho AI Coding Assistant. |

## Hướng dẫn cài đặt Backend

1. **Khởi tạo môi trường ảo Python:**
   ```bash
   python -m venv venv

   .\venv\Scripts\activate

   pip install -r backend/requirements.txt