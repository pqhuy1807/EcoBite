# 🌱 EcoBite Platform - Food Rescue & Zero-Waste Platform

[![Architecture: Decoupled Three-Tier](https://img.shields.io/badge/Architecture-Decoupled_Three--Tier-00C781.svg)]()
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.111-009688.svg?logo=fastapi)]()
[![Frontend: Next.js 14](https://img.shields.io/badge/Frontend-Next.js_14-black.svg?logo=next.js)]()
[![Database: PostGIS 16](https://img.shields.io/badge/Database-PostgreSQL_16_+_PostGIS_3.4-336791.svg?logo=postgresql)]()
[![Cache: Redis 7](https://img.shields.io/badge/Cache-Redis_7-DC382D.svg?logo=redis)]()
[![Payments: VNPay](https://img.shields.io/badge/Payment-VNPay_HMAC--SHA512-005BAA.svg)]()
[![AI: Google Gemini 2.5 Flash](https://img.shields.io/badge/AI%2FNLP-Gemini_2.5_Flash-4285F4.svg?logo=google)]()

**EcoBite** là nền tảng giải cứu thực phẩm thông minh theo mô hình **Online-to-Offline (O2O)**, được thiết kế nhằm kết nối các cơ sở kinh doanh thực phẩm thương mại (nhà hàng, tiệm bánh, quán cà phê và siêu thị) với người tiêu dùng địa phương có nhu cầu mua **các món ăn dư thừa trong ngày (Surplus Food Dishes)** với mức giá ưu đãi sâu từ **40% đến 70%**. Dự án hướng tới sứ mệnh giảm lãng phí thực phẩm, cắt giảm phát thải khí nhà kính ($CH_4$ và $CO_2$) và lan toả phong cách sống xanh bền vững.

---

## 👥 Nhóm Thực hiện Dự án (Group 05 - HCMUS)

- **Phùng Quốc Huy** (24127402 - pqhuy2425@clc.fitus.edu.vn) — *AI and Data Lead / Full-Stack Engineer*
- **Đặng Trọng Phúc** (24127495 - dtphuc2418@clc.fitus.edu.vn) — *Backend Lead & AI Engineer / Full-Stack Engineer*
- **Đàng Thế Tony** (24127561 - dttony2424@clc.fitus.edu.vn) — *QA/Tester Lead & Backend Engineer / Full-Stack Engineer*
- **Võ Ngọc Thịnh** (24127246 - vnthinh2418@clc.fitus.edu.vn) — *Frontend Lead / Full-Stack Engineer*

---

## 📌 8 Tính năng Cốt lõi (Key Features)

1. **Xác thực & Đăng ký cửa hàng - KYC & Kiểm tra ATVSTP (Authentication & Merchant Onboarding)**: Đăng nhập Email/Password hoặc Google OAuth2, phân quyền RBAC (`CONSUMER`, `STORE_PARTNER`, `ADMIN`) với JWT dual-tokens. Quán bắt buộc nộp Giấy chứng nhận ATVSTP chính thức để Admin phê duyệt trước khi được đăng bán.
2. **Danh mục Thực đơn Cơ bản & Quản lý Món Dư (Base Menu Catalog & Surplus Dish Management)**: Quán duy trì danh mục cố định (`menu_items`) chứa ảnh chuẩn độ nét cao và giá gốc niêm yết. Cuối ca, khởi tạo món dư hoạt động (`dishes`) kế thừa ảnh và giá gốc chuẩn mà không cần nhập lại.
3. **Công cụ Giảm giá theo Khung giờ Dựa trên Quy tắc (Rule-Based Time-Shift Discounting Engine)**: Định giá giảm dần theo thời gian tất định, không dùng AI đoán giá. Tự động chuyển đổi giữa khung giờ tiêu chuẩn (giảm 40%–50%) sang giờ chót xả hàng (giảm tới 70% trong 30–45 phút cuối) kèm đồng hồ đếm ngược trực tiếp.
4. **Tìm kiếm Dựa trên Vị trí & Khám phá Radar PostGIS (Location-Based Search & PostGIS Radar Discovery)**: Truy vấn không gian PostgreSQL PostGIS (`ST_DWithin`, `ST_Distance`) tính khoảng cách thực trong bán kính 1–5 km (mở rộng 10 km). Bản đồ radar Leaflet tương tác, bộ lọc ẩm thực, thanh trượt giá và chỉ báo mức độ gấp.
5. **Khóa Chống Bán Quá Tồn Kho & Quản lý Đơn Hàng (Inventory Anti-Overselling Lock & Order Management)**: Kiểm soát đồng thời cấp CSDL nghiêm ngặt bằng câu lệnh SQL nguyên tử (`UPDATE dishes SET remaining_quantity = remaining_quantity - :qty WHERE remaining_quantity >= :qty`) kết hợp Redis distributed lock đảm bảo zero over-selling.
6. **Thanh toán Không Tiền Mặt Liền Mạch - Cổng VNPay (Seamless Cashless Checkout - VNPay Payment Gateway)**: Tích hợp cổng VNPay quét VNPAY-QR động từ app ngân hàng và ví điện tử; xử lý IPN Webhook Server-to-Server mã hóa xác thực HMAC-SHA512 với quy trình idempotent chống trùng lặp.
7. **Mã QR Một Lần Động HMAC-SHA256 & Trình Quét Web tại Cửa Hàng (Dynamic Single-Use QR Token & In-Store Web Scanner)**: Sinh mã QR ký điện tử HMAC-SHA256 (`order_id`, `user_id`, `nonce`, `pickup_deadline`). Chủ quán dùng máy quét camera web (`html5-qrcode`) để xác thực đơn, đánh dấu đã dùng tức thì, chống chụp màn hình và chống Replay Attack.
8. **Đánh Giá Xác Thực, Điểm Xanh & Trình Theo Dõi Tác Động Môi Trường (Verified Reviews, Green Points & Environmental Impact Tracker)**: Chỉ đơn hàng đã quét QR thành công (`COMPLETED`) mới được đánh giá 1–5 sao. Tự động quy đổi mỗi suất ăn thành ~2.5 kg $CO_2e$ tiết kiệm, tích Điểm Xanh đổi voucher và vinh danh trên Bảng xếp hạng Xanh.

---

## 🤖 Phân hệ Trí Tuệ Nhân Tạo (AI Intelligence Suite - Powered by Google Gemini 2.5 Flash)

1. **Trợ lý Đa Phương Thức Đăng Nhanh Hàng Loạt & Bộ Bảo Vệ Dị Ứng 2 Tầng (Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard)**:
   - *Native Multimodal Audio Ingestion*: Gửi trực tiếp tệp âm thanh thô tới Gemini 2.5 Flash không qua STT trung gian, nhận diện chính xác tiếng lóng ẩm thực Việt (*"bốn lăm cành"*, *"bì chả"*).
   - *Menu-Catalog Grounding*: Tự động khớp tên món với Thực đơn gốc (`menu_items`) để kéo ảnh nét và giá gốc chuẩn.
   - *Two-Tier Allergen Guard (14 chuẩn EU FIC)*: Tách bạch rõ `EXPLICIT` (người bán nói trực tiếp) và `INFERRED` (AI suy luận công thức món Việt: chả có trứng, nước mắm có cá, mỡ hành có đậu phộng, bánh mì có gluten); kèm ghi chú khẩu vị văn hóa (`dietary_notes`: có hành/ngò, cay, chua, chay).
   - *Batch Extraction & Server-Time Grounding*: Bóc tách nhiều món (`List[SurplusDishItem]`) và quy đổi thời gian tương đối (*"từ giờ đến 3h chiều"*) thành mốc giờ ISO 8601 tuyệt đối bằng `current_server_time`.
2. **Gợi ý Món Ăn Thông Minh & Tìm Kiếm Ngữ Nghĩa Hội Thoại (Smart Food Recommendation & Conversational Semantic Search)**:
   - *Layer 1 - Hard Safety Invariant (SQL & PostGIS)*: Lọc bán kính 1–3 km và loại trừ nghiêm ngặt 100% món ăn chứa chất dị ứng của người dùng (`excluded_allergens` trong `user_preferences`) tại cấp độ truy vấn CSDL, không phụ thuộc vào AI sinh xác suất.
   - *Layer 2 - Multi-Factor Heuristic Scoring*:
     $$\text{Score} = (0.40 \times \text{Proximity}) + (0.30 \times \text{Discount Depth \& Time Urgency}) + (0.30 \times \text{Taste Profile Match})$$
     Ưu tiên các Deal Giải Cứu Cấp Bách bước vào 30 phút cuối áp dụng luật giảm 70%.
   - *Layer 3 - Generative AI Personalization*: Gemini 2.5 Flash sinh lý do đề xuất ngắn gọn (20–30 từ), giàu cảm xúc hiển thị trên thẻ giao diện UI.
   - *Conversational Semantic Search*: Người dùng gõ câu tìm kiếm tự nhiên (*"Tìm món súp ấm nóng dưới 30k ở gần đây"*), Gemini trích xuất ý định, ngân sách để truy vấn cơ sở dữ liệu PostGIS.

---

## ⚡ Hướng dẫn Khởi động Nhanh (Quick Start)

### 1. Khởi động Cơ sở Dữ liệu & Redis
```bash
docker compose up -d
docker compose ps
```

### 2. Thiết lập Biến môi trường (.env)
```bash
cp .env.example .env
# Điền GEMINI_API_KEY, VNP_TMN_CODE, VNP_HASH_SECRET
```

### 3. Thiết lập Backend (FastAPI)
```bash
cd backend
python3 -m venv venv_backend && source venv_backend/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Thiết lập Frontend (Next.js 14)
```bash
cd frontend
npm install
npm run dev
```

---

## 📚 Bộ Tài liệu Kỹ thuật Chi tiết (Documentation Index)

| Tài liệu | Mô tả nội dung chính |
| :--- | :--- |
| 📄 [`docs/01_PRD_and_User_Stories.md`](docs/01_PRD_and_User_Stories.md) | Mục tiêu sản phẩm, Persona, khảo sát ứng dụng (Yindii, Too Good To Go), 8 tính năng cốt lõi & 2 tính năng AI. |
| 🏗️ [`docs/02_System_Architecture.md`](docs/02_System_Architecture.md) | Kiến trúc Three-Tier, Sequence Diagrams (Quick-Post, Recommendation, VNPay IPN HMAC-SHA512, QR Scanner). |
| 🗄️ [`docs/03_Database_Schema_ERD.md`](docs/03_Database_Schema_ERD.md) | Thiết kế CSDL PostgreSQL/PostGIS, ERD Mermaid, bảng `payment_transactions`, `user_preferences` & GIST Index. |
| 🔌 [`docs/04_API_Specification.md`](docs/04_API_Specification.md) | Đặc tả chi tiết RESTful API v1 đầy đủ Request/Response schemas chuẩn Pydantic v2. |
| 📋 [`docs/05_Agile_Roadmap_and_Kanban.md`](docs/05_Agile_Roadmap_and_Kanban.md) | Thỏa ước hoạt động nhóm (Team Contract), Toolchain Setup (Jira, GitHub), phân chia Sprint PA1 – PA5, DoR & DoD. |
| 🛠️ [`docs/06_Environment_and_ML_Setup_Guide.md`](docs/06_Environment_and_ML_Setup_Guide.md) | Cẩm nang cài đặt chi tiết Docker, Python 3.11, venv, Gemini API Key và VNPay Sandbox. |
| 🛡️ [`docs/07_AI_Development_Workflow_and_Quality_Gates.md`](docs/07_AI_Development_Workflow_and_Quality_Gates.md) | Hướng dẫn chu trình TDD, 4 Quality Gates và cài đặt Git Pre-commit Hooks. |
| 📜 [`AGENTS.md`](AGENTS.md) | Bộ quy tắc & 8 ranh giới bất khả xâm phạm dành cho AI Coding Assistant. |
