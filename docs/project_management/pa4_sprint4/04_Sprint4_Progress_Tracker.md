# 📊 Theo dõi Tiến độ Dự án & Scrum Log — Sprint 4 (PA4)

> **Cập nhật lần cuối**: `21/11/2026` (Hoàn tất & merge 100% Backend Core F1–F8 vào `dev`)
> **Mục tiêu tệp**: Ghi nhận tiến độ thực tế theo ngày, trạng thái từng Feature/Task, blockers và biên bản các buổi họp Scrum để tổng hợp trực tiếp vào **Phần D của Báo cáo `docs/PA4.md`**.

---

## 1. Bảng Trạng thái Tổng hợp Theo Tính năng (Feature Progress)

| Phạm vi | Thành phần | Tuần 5 Target (`22/11`) | Tuần 6 Target (`27/11`) | Trạng thái Hiện tại (`16/11`) | Người phụ trách |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F1** | `GET /stores/me` + Admin KYC UI (`/admin`) | BE + FE Done | Regression + E2E | `IN PROGRESS` *(BE `/stores/me`: DONE; FE `/admin`: TO DO)* | Phúc (BE) · Thịnh (FE) |
| **F2 & F3** | Store Portal (`/store/menu`, `/store/dishes`) + sửa `dish.service.ts` | FE Done | Vitest + Polish | `TO DO` | Thịnh (FE) |
| **F4 & F5** | PostGIS Radar & Atomic Order Lock (từ PA3) | Baseline xanh | Regression + Stock Restore | `DONE (PA3)` | Phúc · Tony |
| **F6** | VNPay Gateway (HMAC-SHA512, IPN Idempotent, Checkout & Return UI) | BE + FE + Unit Test | Concurrency IPN + Sandbox E2E | `IN PROGRESS` *(BE VNPay + Tests: DONE; FE Checkout: TO DO)* | Phúc (BE) · Thịnh (FE) |
| **F7** | Dynamic QR Guard (`PAID` check, `COD` auto-paid, Store Orders table) | BE Guard + Unit Test | FE Table + Benchmark `< 2s` | `IN PROGRESS` *(BE QR Guard + Points/CO₂: DONE; FE Table: TO DO)* | Tony (BE) · Thịnh (FE) |
| **F8** | Verified Reviews, Green Points Ledger, CO₂ & Vouchers | BE + Unit Tests + Seed | FE UI (`/green-points`, Review) + Integration Test | `IN PROGRESS` *(BE Reviews + Gamification + Seed: DONE; FE UI: TO DO)* | Tony & Huy (BE) · Thịnh (FE) |
| **QA & Docs** | Env Sync, Vitest, Integration Tests, `docs/PA4.md` & Video Demo | Env Sync + Vitest Setup | Full Gate Pass + Nộp PA4 | `IN PROGRESS` | Tony (QA) · Huy (PM) |
| **PA5 Head-start** | Nhánh `feat/ai-*`: Gemini Quick-Post + Allergen Hard Filter | *(Chưa mở)* | Khởi động từ `23/11` | `PLANNED` | Huy · Phúc |

---

## 2. Sprint 4 Burn-down & Kiểm soát Mốc Thời gian

**Tổng Story Points Sprint 4**: **38 pts** *(Tuần 5: 23 pts · Tuần 6: 15 pts)*

| Mốc kiểm tra | Ngày | Điểm Còn Lại Kế hoạch (Planned Remaining) | Điểm Còn Lại Thực tế (Actual Remaining) | Ghi chú / Đánh giá Tiến độ |
| :--- | :---: | :---: | :---: | :--- |
| Khởi động Sprint 4 | `16/11` | `38 pts` | `38 pts` | Chốt kế hoạch 3 BE + 1 FE, tạo Jira Sprint 4 |
| Giữa Tuần 5 (Check-in) | `19/11` | `26 pts` | `—` | Mục tiêu: Xong VNPay Service, QR Guard, Gamification Service, Admin/Store Menu UI |
| **Chốt Tuần 5 (BE Core 100%)** | `22/11` | `15 pts` | `—` | **Gate bắt buộc**: 100% Backend F1–F8 xong & xanh `pytest` |
| Giữa Tuần 6 (**Code Freeze**) | `25/11` | `5 pts` | `—` | Đóng tính năng PA4 Release 0.3; hoàn tất Integration/Vitest & Sandbox E2E |
| **Internal Deadline PA4** | `27/11` | `0 pts` | `—` | Xong `docs/PA4.md`, Video Demo, cross-review 100% |
| **Nộp PA4 Chính thức** | `28/11` | `0 pts` | `—` | Nộp Moodle & tag `v0.3.0-pa4` |

---

## 3. Nhật ký Daily Scrum & Blocker Log

> *Quy tắc Team Contract: Báo cáo ngắn 3 ý (Hôm qua làm gì / Hôm nay làm gì / Blocker) mỗi ngày trên Zalo Group 05; blocker gắn `@all` phản hồi trong 1 giờ.*

### Các Blocker Đã Phát hiện Ngay Ngày Khởi động (`16/11/2026`)

| Ngày | Người phát hiện | Mô tả Blocker / Lệch Hiện trạng | Hướng Xử lý & Người phụ trách | Trạng thái |
| :---: | :--- | :--- | :--- | :---: |
| `16/11` | Huy / Tony | `backend/venv_backend` thiếu thư viện `redis` khi chạy `pytest`; đồng thời `AGENTS.md` đang chuẩn hóa tên `.venv`. | **Tony** (`EC4-05`): Đồng bộ cài đủ `backend/requirements.txt`, thống nhất lại môi trường chuẩn và cập nhật `AGENTS.md` nếu cần. | `OPEN` |
| `16/11` | Huy | Chưa có endpoint `GET /api/v1/stores/me` nên Store Partner UI không lấy được `store_id` & `kyc_status` sau khi đăng nhập. | **Phúc** (`EC4-02`): Thêm `/stores/me` trước route `/stores/{store_id}` trong `stores.py`. | `RESOLVED` |
| `16/11` | Huy | `frontend/src/services/dish.service.ts` đang gọi `/dishes` và `/dishes/{id}` (không khớp `endpoints/dishes.py`); `PaymentStatus` ở `types/api.ts` thừa `'REFUNDED'` so với backend. | **Thịnh** (`EC4-10`): Sửa `dish.service.ts` và chuẩn hóa `types/api.ts` ngay ngày 1. | `OPEN` |
| `16/11` | Huy | `OrderService.verify_and_complete_order` hiện chưa kiểm tra `PAID` với đơn `VNPAY` và chưa ghi `GreenPointsLedger` / `User.green_points_balance`. | **Tony** (`EC4-06`): Bổ sung guard `PAID` và atomic cộng điểm xanh + `CO2` khi hoàn tất đơn. | `RESOLVED` |
| `16/11` | Huy | `frontend/package.json` chưa cấu hình test runner (`Vitest`). | **Thịnh** (`EC4-10`): Cài Vitest + Testing Library + jsdom, thêm `"test"` script. | `OPEN` |

*(Thêm dòng nhật ký hàng ngày bên dưới trong suốt Sprint 4)*

| Ngày | Đặng Trọng Phúc | Đàng Thế Tony | Phùng Quốc Huy | Võ Ngọc Thịnh | Blocker mới |
| :---: | :--- | :--- | :--- | :--- | :--- |
| `16/11` | Bắt đầu `EC4-01`, `EC4-02` | Chạy `EC4-05` sync env | Mở Sprint 4, `EC4-08` | Chạy `EC4-10` Vitest + services | Chốt keys VNPay Sandbox tối `16/11` |
| `21/11` | Hoàn tất & merge `EC4-01`..`EC4-04` (VNPay endpoints + `/stores/me` + unit tests) vào `dev` | Hoàn tất & merge `EC4-06`, `EC4-07` (QR Payment Guard, cộng điểm/CO₂ & Verified Reviews + tests) vào `dev` | Hoàn tất & merge `EC4-08`, `EC4-09` (Gamification/Vouchers, `seed.py`, unit & integration tests) vào `dev` | Chưa merge `EC4-10`..`EC4-12` vào `dev` | 100% Backend Core F1–F8 đã đóng trên `dev`; cần review & merge Frontend đợt 1 của Thịnh trước họp chốt `22/11` |

---

## 4. Biên bản Các Buổi Họp Scrum (Ceremonies Log)

### 4.1. Sprint 4 Planning — Thứ Hai `16/11/2026` (20:30 – 21:30, Google Meet)
- **Thành phần dự kiến**: 4/4 thành viên (Phùng Quốc Huy — Facilitator, Đặng Trọng Phúc, Đàng Thế Tony, Võ Ngọc Thịnh).
- **Quyết định trọng tâm**:
  1. Thống nhất chiến lược đóng toàn bộ **8 Core Features** trong 2 tuần của PA4 (để dành PA5 cho 2 tính năng AI & Go-Live).
  2. Huy tham gia làm **Backend Engineer 3** (Feature 8 Gamification/Vouchers + Seed) cùng Phúc (VNPay + `/stores/me`) và Tony (QR Guard + Reviews + QA) để khóa 100% Backend Core ngay trong Tuần 5 (`22/11`).
  3. Thịnh triển khai toàn bộ Frontend Core + Vitest trải đều qua Tuần 5 (Portals + VNPay) và nửa đầu Tuần 6 (Feature 8 UI + Vitest).
  4. Nhánh `feat/ai-*` chỉ mở từ `23/11` sau khi Backend Core đã đóng và xanh test.

### 4.2. Tuần 5 Check-point & Tuần 6 Planning — Chủ Nhật `22/11/2026` (21:00)
- *(Điền kết quả nghiệm thu Backend Core F1–F8 và xác nhận phân việc Tuần 6 tại đây.)*

### 4.3. Sprint 4 Review & Retrospective — Thứ Sáu `27/11/2026` (21:00)
- *(Điền bảng đối chiếu DoD, kết quả demo Release 0.3 và bài học cải tiến cho PA5 tại đây.)*

---

## 5. Quality Gate Checklist (Cập nhật trước khi Merge & Nộp PA4)

- [ ] **Backend Tuần 5 Gate (`22/11`)**: `ruff check app/`, `ruff format --check app/`, `mypy app/`, `pytest tests/ -v` đều exit `0`.
- [ ] **Frontend Tuần 6 Gate (`25/11`)**: `npm run lint`, `npm run type-check`, `npm run test`, `npm run build` đều exit `0`.
- [ ] **Bảo mật & Pre-commit (`27/11`)**: `pre-commit run --all-files` xanh (không lộ `.env`, VNPay secret, QR secret, file > 5MB).
- [ ] **Tài liệu & Nộp bài (`27/11 – 28/11`)**: `docs/04_API_Specification.md`, `AGENTS.md`, `docs/PA4.md`, `docs/PA4.pdf`, Video Demo Release 0.3, ảnh Jira Sprint 4 & Burndown.
