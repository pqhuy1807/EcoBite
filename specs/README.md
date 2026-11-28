# Spec-Kit Master Index — EcoBite Platform (`001` – `007`)

> **Dự án**: EcoBite — Nền tảng Giải cứu Thực phẩm Thông minh & Kết nối Xanh (Group 05 — HCMUS)
> **Hiến chương kỹ thuật**: [`.specify/memory/constitution.md`](../.specify/memory/constitution.md) (v1.2.0) · **Quy tắc AI**: [`AGENTS.md`](../AGENTS.md)
> **Feature đang active**: xem [`.specify/feature.json`](../.specify/feature.json) *(hiện trỏ tới `specs/002-ai-quick-post-nlp`)*
> **Cập nhật**: `2026-11-28`

Thư mục `specs/` chứa toàn bộ đặc tả theo quy trình **Spec-Driven Development (Spec-Kit 1.2.1)** bao phủ **100% 8 Tính năng Cốt lõi (`F1`–`F8`), 2 Tính năng AI Gemini 2.5 Flash (`AI-1`, `AI-2`), và Giao diện AI + Kiểm thử + Go-Live Release 1.0 (`PA5`)**, bám sát phân công 1-1 trong [`docs/project_management/`](../docs/project_management/README.md).

---

## 1. Bảng Tổng hợp Toàn bộ 7 Bộ Spec-Kit

Mỗi thư mục đều có đủ **8 tài liệu chuẩn Spec-Kit**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `tasks.md`, `checklists/requirements.md`, và `contracts/api-contracts.md`.

| # | Thư mục Spec-Kit | Phạm vi Tính năng | Mốc PA / Sprint | Phụ trách chính (Jira IDs) | Tiến độ `tasks.md` |
| :---: | :--- | :--- | :---: | :--- | :---: |
| **001** | [`001-rescue-discovery-order-qr/`](./001-rescue-discovery-order-qr/spec.md) | **F4, F5, F7 Core** — PostGIS Radar Discovery (`ST_DWithin` + Leaflet), Đặt đơn chống bán quá tồn kho (Atomic Lock + Redis + Cancel), Mã QR động HMAC-SHA256 & Web Scanner | **PA3** *(Release `v0.2`)* | Đặng Trọng Phúc · Đàng Thế Tony · Võ Ngọc Thịnh | `24 / 24` (`[X]` Done) |
| **002** | [`002-ai-quick-post-nlp/`](./002-ai-quick-post-nlp/spec.md) | **AI-1 Backend & Eval** — Gemini 2.5 Flash Native Audio/Text Quick-Post (`POST /ml/parse-dish-nlp`), Menu-Catalog Grounding (`0%` bịa UUID), Server-Time `Asia/Ho_Chi_Minh`, 2-Tier EU FIC Allergens (`EXPLICIT`/`INFERRED`), Golden Dataset & Benchmark | **PA4 W6 → PA5** | **Phùng Quốc Huy** (`EC4-18`, `EC5-01`) · *Rev: Phúc* | `0 / 27` *(In Progress)* |
| **003** | [`003-auth-kyc-menu-pricing/`](./003-auth-kyc-menu-pricing/spec.md) | **F1, F2, F3** — JWT Dual-Token Auth (`extra="forbid"`), Store KYC Onboarding & `GET /stores/me`, Admin KYC Dashboard (`/admin`), Base Menu Catalog (`/store/menu`), Surplus Dishes (`/store/dishes`) & Rule-Based Time-Shift Discounting (`50%`/`70%`) | **PA2 → PA4** | **Phúc** (`EC4-02`) · **Tony** (`EC4-05`) · **Thịnh** (`EC4-10`, `EC4-11`, `EC4-13` Navbar) | `31 / 41` (`10` còn lại) |
| **004** | [`004-vnpay-payment-qr-guard/`](./004-vnpay-payment-qr-guard/spec.md) | **F6 + F7 Payment Guard** — VNPay HMAC-SHA512 Create-URL, Idempotent IPN + Redis Lock + Hoàn kho nguyên tử khi thất bại, Return URL, Khóa QR khi `VNPAY` chưa `PAID` (`409`), `COD` tự `PAID`, FE Checkout/`/orders/vnpay-return`/`/store/verify-qr` bảng đơn quán, Sandbox E2E & Concurrency QA | **PA4** *(Release `v0.3`)* | **Phúc** (`EC4-01`, `EC4-03`, `EC4-04`, `EC4-16`) · **Tony** (`EC4-06`, `EC4-15`) · **Thịnh** (`EC4-12`, `EC4-13` Store, `EC4-14`) | `10 / 35` (`25` còn lại) |
| **005** | [`005-reviews-gamification-vouchers/`](./005-reviews-gamification-vouchers/spec.md) | **F8** — Verified Reviews (`POST /orders/{id}/review`, `Store.rating_avg`), Ví Điểm Xanh (`GET /green-points/me`, `2.5 kg CO₂/suất`, Eco Rank), Đổi Voucher trừ điểm nguyên tử (`POST /vouchers/{id}/redeem`), Seed dữ liệu, FE `/green-points` & `ReviewModal.tsx` & Vitest | **PA4** *(Release `v0.3`)* | **Huy** (`EC4-08`, `EC4-09`) · **Tony** (`EC4-07`, `EC4-13` Consumer FE, `EC4-14` P2, `EC4-15`) | `21 / 39` (`18` còn lại) |
| **006** | [`006-ai-smart-recommendation-search/`](./006-ai-smart-recommendation-search/spec.md) | **AI-2 Backend & Eval** — `UserPreference` CRUD (`/users/me/preferences`), **Layer 1 SQL PostGIS Allergen Hard Filter** (Guardrail #7 — `0.0%` leakage), **Layer 2 Heuristic Scoring (`0.40/0.30/0.30`)**, **Layer 3 Gemini 2.5 Flash Justification + Fallback**, Semantic Search (`POST /dishes/search-semantic`), Golden Dataset & Allergen Invariant QA | **PA4 W6 → PA5** | **Phúc** (W6 Baseline, `EC5-02`) · **Huy** (`EC5-03`) · **Tony** (`EC5-06`) | `0 / 36` *(Planned)* |
| **007** | [`007-ai-frontend-suite-and-golive/`](./007-ai-frontend-suite-and-golive/spec.md) | **FE AI Suite, AI Safety QA & Go-Live** — `MediaRecorder` Voice Quick-Post + 2-Tier Draft Cards Editor (`/store/dishes`), Top 3 AI Carousel + Semantic Search Bar (`/`), Trang hồ sơ dị ứng 14 EU FIC (`/profile/preferences`), QA Allergen Invariant/SLA `< 3s`/Coverage `>= 80%`, UAT 4-Service Docker Compose & Release `v1.0.0` (`docs/PA5.md`) | **PA5** *(Release `v1.0`)* | **Thịnh** (`EC5-04`, `EC5-05`) · **Tony** (`EC5-06`, `03_PA5_AI_Test_Plan.md`) · **Cả nhóm / Huy PM** (`EC5-07`) | `0 / 42` *(Planned)* |

**Tổng cộng toàn dự án**: **7 bộ Spec-Kit** · **56 tài liệu đặc tả** · **244 tasks TDD** (`86` đã hoàn tất `[X]`, `158` đang/sắp triển khai `[ ]`).

---

## 2. Phân bổ Spec-Kit Theo Thành viên (Tra cứu Nhanh)

| Thành viên | Vai trò | Các bộ Spec-Kit phụ trách chính |
| :--- | :--- | :--- |
| **Phùng Quốc Huy** (`24127402`) | PM · AI & Data Lead · BE | [`002`](./002-ai-quick-post-nlp/tasks.md) *(chủ trì AI-1)* · [`005`](./005-reviews-gamification-vouchers/tasks.md) *(BE Gamification/Seed — đã xong)* · [`006`](./006-ai-smart-recommendation-search/tasks.md) *(`EC5-03` Scoring/Justification/Search)* · [`007`](./007-ai-frontend-suite-and-golive/tasks.md) *(`EC5-07` PM/Go-Live)* |
| **Đặng Trọng Phúc** (`24127495`) | Backend & Architecture Lead | [`003`](./003-auth-kyc-menu-pricing/tasks.md) *(`EC4-02` `/stores/me` + fix `DishService._build_dish`)* · [`004`](./004-vnpay-payment-qr-guard/tasks.md) *(VNPay Core + 4 Sandbox fixes + `EC4-16`)* · [`006`](./006-ai-smart-recommendation-search/tasks.md) *(chủ trì W6 AI-2 Baseline, `EC5-02` SQL Hard Filter & Eval)* |
| **Đàng Thế Tony** (`24127561`) | QA Lead · Backend / FE Support | [`003`](./003-auth-kyc-menu-pricing/tasks.md) *(`EC4-05` Backend QA Gate)* · [`004`](./004-vnpay-payment-qr-guard/tasks.md) *(`EC4-06` QR Guard + `EC4-15` IPN/QR Benchmark)* · [`005`](./005-reviews-gamification-vouchers/tasks.md) *(`EC4-07` Reviews BE + `EC4-13`/`EC4-14` F8 FE & Vitest)* · [`006`](./006-ai-smart-recommendation-search/tasks.md) & [`007`](./007-ai-frontend-suite-and-golive/tasks.md) *(`EC5-06` Allergen Invariant & Coverage `>= 80%`)* |
| **Võ Ngọc Thịnh** (`24127246`) | Frontend & UI/UX Lead | [`001`](./001-rescue-discovery-order-qr/tasks.md) *(PA3 FE — xong)* · [`003`](./003-auth-kyc-menu-pricing/tasks.md) *(`EC4-10`/`EC4-11` Portals & cleanup)* · [`004`](./004-vnpay-payment-qr-guard/tasks.md) *(`EC4-12` VNPay UI, `/store/verify-qr` bảng đơn, Vitest P1)* · [`007`](./007-ai-frontend-suite-and-golive/tasks.md) *(chủ trì `EC5-04`, `EC5-05` AI Frontend Suite)* |

---

## 3. Lưu ý Quan trọng Từ Kiểm kê Codebase (Đã ghi nhận trong Spec-Kit)

Trong quá trình đối chiếu 100% giữa tài liệu giao việc và mã nguồn hiện tại (`28/11/2026`), các đặc tả đã khoanh vùng sẵn một số lệch chuẩn thực tế để các thành viên xử lý dứt điểm:

1. **Trong [`003-auth-kyc-menu-pricing`](./003-auth-kyc-menu-pricing/research.md)**:
   - `DishService._build_dish()` hiện lưu nhầm `rule_discount_price` (`-70%`) vào cột `rescue_price` nếu tạo món đúng trong khung giờ chót 45 phút cuối (`T033`).
   - `frontend/package.json` đang có 2 dòng `"test"` bị trùng (`T003`); trang `/store/onboard` gọi path cũ `/stores/kyc` (`T019`); `/register` gửi field `role` bị `UserCreate(extra="forbid")` chặn `422` (`T014`); `FoodCategory`/`DishStatus` lệch enum `'DRINKS'`→`'BEVERAGE'`, `'HIDDEN'`→`'INACTIVE'` (`T024`).
2. **Trong [`004-vnpay-payment-qr-guard`](./004-vnpay-payment-qr-guard/research.md)**:
   - Còn 4 điểm vá VNPay Sandbox của Phúc (`quote_plus`, `settings.VNP_URL`, `ZoneInfo("Asia/Ho_Chi_Minh")`, `Request` client IP & `require_roles(UserRole.CONSUMER)`), hoàn thiện FE VNPay & Store Orders của Thịnh, và `test_api_payments.py` + QR `< 2s` của Tony.
3. **Trong [`006-ai-smart-recommendation-search`](./006-ai-smart-recommendation-search/research.md)**:
   - Bắt buộc thay thế bộ lọc Python cũ (`allergen_filter_service.py`) bằng **SQL Hard Filter** truy vấn cả `dishes.allergens` lẫn `menu_items.base_allergens` (kèm chuẩn hóa `đ`/`Đ` và `"Hải sản"` → 3 nhóm EU FIC), dùng đúng enum `DishStatus.ACTIVE`, và đăng ký `recommendations.router` **trước** `stores.router` (tránh bị wildcard `GET /{store_id}` nuốt route).

---

## 4. Cách Sử dụng Spec-Kit Cho Từng Thành viên

1. **Chuyển feature đang làm**: Cập nhật `.specify/feature.json` trỏ tới thư mục của bạn (ví dụ `"feature_directory": "specs/004-vnpay-payment-qr-guard"`).
2. **Làm đúng vòng lặp TDD**: Đọc `spec.md` → `contracts/api-contracts.md` → `data-model.md` → mở `tasks.md`, viết test trước (Red) rồi code (Green), tích `[X]` ngay khi task hoàn tất và chạy xanh toàn bộ **Final Verification Gate** trước khi tạo PR.
3. **Bảo vệ nhánh phát hành**: Nhánh `feat/ai-*` (`002`, `006`, `007`) phát triển tách biệt khỏi nhánh Release 0.3 PA4 (`v0.3.0-pa4`).
