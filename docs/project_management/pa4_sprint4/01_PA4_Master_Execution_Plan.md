# 📋 Kế hoạch Tổng thể PA4 (3 Backend + 1 Frontend, 16/11 – 28/11/2026)

> **Mốc đánh giá**: Project Assignment 4 (PA4 — Sprint 4)
> **Thời gian**: Thứ Hai `16/11/2026` – Thứ Bảy `28/11/2026` (2 tuần: Tuần 5 & Tuần 6)
> **Hạn chót nội bộ PA4**: **23:59 Thứ Sáu, 27/11/2026** *(nộp chính thức Moodle `28/11/2026`)*
> **Chiến lược Phân công**:
> - **3 Kỹ sư Backend (`Đặng Trọng Phúc`, `Đàng Thế Tony`, `Phùng Quốc Huy`)**: Chia 3 mũi song song hoàn thành **100% Backend của cả 8 Core Features + Unit Tests** ngay trong **Tuần 5 (`16/11 – 22/11`)**. Sang **Tuần 6 (`23/11 – 28/11`)**, vừa chạy **Integration/Concurrency Tests & Báo cáo PA4**, vừa **khởi động sớm AI Features của PA5** trên nhánh `feat/ai-*`.
> - **Frontend Lead (`Võ Ngọc Thịnh`)**: Triển khai toàn bộ giao diện các tính năng cơ bản + **Vitest** trải đều hợp lý trong **cả 2 tuần** (`Tuần 5`: Admin KYC + Store Menu/Dishes + VNPay Checkout/Return; `Tuần 6`: Feature 8 UI `/green-points` + Review Modal + Store Orders table + Vitest FE tests).

---

## 1. Kiểm kê Toàn bộ 8 Tính năng Cơ bản (Snapshot `16/11/2026`)

| Feature | Tên Tính năng | Hiện trạng Backend (`FastAPI`) | Hiện trạng Frontend (`Next.js 14`) | Đầu việc Cần Hoàn tất trong PA4 |
| :--- | :--- | :--- | :--- | :--- |
| **F1** | Auth, Store KYC & Admin Duyệt | Xong (`auth.py`, `users.py`, `stores.py`) | Có `/login`, `/register`, `/store/onboard` | • **BE**: Thêm `GET /api/v1/stores/me`.<br>• **FE**: Dựng Admin KYC Dashboard (`/admin`). |
| **F2 & F3** | Base Menu, Surplus Dishes & Giảm giá Rule-based | Xong (`menu.py`, `dishes.py`) | Chưa có UI Quản lý (`dish.service.ts` đang gọi sai path `/dishes`) | • **FE**: Sửa `dish.service.ts`, tạo `menu.service.ts`, dựng `/store/menu` & `/store/dishes`. |
| **F4** | PostGIS Radar Discovery | Xong (`GET /stores/nearby`) | Xong (`page.tsx`, `RadarMap.tsx`) | • Duy trì hồi quy xanh. |
| **F5** | Anti-Overselling Order & Cancel | Xong (`orders.py`, `order_service.py`) | Xong (Modal đặt món, `/orders`) | • **BE**: Tự động hoàn kho khi IPN VNPay báo thất bại. |
| **F6** | Thanh toán VNPay & Idempotent IPN | Chưa có (mới có model/schema) | Chưa có (mới có nút chọn `VNPAY`) | • **BE**: `VNP_*` config, `payment_repo.py`, `payment_service.py`, `endpoints/payments.py`.<br>• **FE**: `payment.service.ts`, redirect Sandbox, `/orders/vnpay-return`, thanh toán lại ở `/orders`. |
| **F7** | Dynamic HMAC-SHA256 QR & Web Camera Scanner | Xong (`qr_service.py`, `verify-qr`) | Xong (`QRCodeSVG`, `html5-qrcode`) | • **BE**: Khóa QR nếu `VNPAY` chưa `PAID`; `COD` xong → `PAID`.<br>• **FE**: Khóa nút QR khi `VNPAY` chưa `PAID`; thêm bảng đơn quán ở `/store/verify-qr`. |
| **F8** | Verified Reviews, Green Points, CO₂ & Vouchers | Chưa có API/Service (đã có models `gamification.py`, `interaction.py`) | Chưa có | • **BE**: Cộng điểm/CO₂ trong `verify_and_complete_order`; `review_repo/service/endpoints`, `gamification_repo/service/endpoints`.<br>• **FE**: Modal Review 1–5 sao ở `/orders` & trang `/green-points`. |

---

## 2. Biểu đồ Lộ trình 2 Tuần (16/11 – 28/11/2026)

```mermaid
gantt
    title Lộ trình PA4: 3 Backend xong Core Tuần 5, Frontend xong Core trong 2 Tuần (16/11 - 28/11)
    dateFormat  YYYY-MM-DD
    axisFormat  %d/%m

    section Tuần 5: Backend Core 100% (Phúc, Tony, Huy)
    Phúc: VNPay (HMAC-SHA512, IPN, Hoàn kho) + GET /stores/me :active, p1, 2026-11-16, 5d
    Tony: Env Sync + Payment-QR Guard + Reviews BE + Unit Tests :active, t1, 2026-11-16, 6d
    Huy: Gamification/Vouchers BE + Seed + Spec Kit + Review PRs :active, h1, 2026-11-16, 6d

    section Tuần 5-6: Frontend Core 100% (Thịnh)
    Tuần 5: Vitest + Admin KYC + Store Menu/Dishes + VNPay Checkout :active, f1, 2026-11-16, 7d
    Tuần 6: Review Modal + /green-points + /store/verify-qr + FE Tests :f2, 2026-11-23, 3d

    section Tuần 6: QA PA4, Báo cáo & Khởi động AI (Backend + All)
    Integration/Concurrency Tests (IPN, Voucher, QR <2s) + Sandbox E2E :qa, 2026-11-23, 3d
    Code Freeze Release 0.3 & Bug Fix                                 :cf, 2026-11-25, 2d
    Khởi động AI Feature 1 (Gemini Quick-Post Backend)                 :ai1, 2026-11-23, 5d
    Khởi động AI Feature 2 (Allergen SQL Hard Filter + Scoring)        :ai2, 2026-11-25, 4d
    Soạn Báo cáo PA4 (docs/PA4.md) + Video Demo Release 0.3            :rep, 2026-11-25, 3d
    Internal Deadline PA4 (27/11)                                      :milestone, 2026-11-27, 0d
    Nộp PA4 Chính thức (28/11)                                         :milestone, 2026-11-28, 0d
```

---

## 3. Phân chia Nhịp Độ 2 Tuần

### Tuần 5 (`16/11 – 22/11/2026`) — Chi tiết tại [`02_Week5_Detailed_Action_Plan.md`](./02_Week5_Detailed_Action_Plan.md)
- **Backend (`Phúc`, `Tony`, `Huy`)**: Hoàn thành 100% API + Business Logic + Unit Tests cho mọi phần còn thiếu của 8 Core Features (`GET /stores/me`, Feature 6 VNPay + IPN idempotent + hoàn kho, Feature 7 Payment↔QR guard, Feature 8 Reviews + Green Points Ledger + Vouchers).
- **Frontend (`Thịnh`)**: Cài Vitest, sửa `dish.service.ts` & `types/api.ts`, dựng `/admin` (KYC), `/store/menu`, `/store/dishes`, và luồng thanh toán VNPay (`/`, `/orders/vnpay-return`, `/orders`).

### Tuần 6 (`23/11 – 28/11/2026`) — Chốt PA4 & Khởi động AI
1. **Frontend Core phần cuối (`Thịnh`, `23/11 – 25/11`)**:
   - Tạo trang `/green-points` (Ví Điểm Xanh, CO₂ đã cứu, Eco Rank, lịch sử điểm, đổi Voucher 1 chạm).
   - Thêm Modal đánh giá 1–5 sao trên `/orders` (đơn `COMPLETED`), bảng đơn hàng cần giao ở `/store/verify-qr`, cập nhật `Navbar.tsx`.
   - Hoàn thành Vitest unit tests tại `frontend/__tests__/components/` & `frontend/__tests__/hooks/`.
2. **Kiểm thử Toàn diện & Hồ sơ PA4 (`Tony`, `Phúc`, `Huy`, `23/11 – 27/11`)**:
   - **Tony**: Chạy bộ Integration Tests & Concurrency Tests (IPN gọi song song không ghi trùng, Voucher redeem đồng thời không âm điểm, Payment↔QR reconciliation, benchmark QR `< 2s`).
   - **Phúc & Thịnh**: Test E2E trên VNPay Sandbox thật (qua ngrok/staging) và sửa bug trước **Code Freeze `25/11`**.
   - **Huy**: Cập nhật `docs/04_API_Specification.md` & `AGENTS.md`, tổng hợp `docs/PA4.md` + Video Demo Release 0.3 trước Internal Deadline **23:59 Thứ Sáu `27/11`**.
3. **Khởi động Sớm AI Features cho PA5 (trên nhánh riêng `feat/ai-*`, không ảnh hưởng Code Freeze Release 0.3)**:
   - **Huy**: `backend/app/services/quick_post_service.py` + `endpoints/ml.py` (`POST /ml/parse-dish-nlp` dùng Gemini 2.5 Flash Structured Outputs từ `app/schemas/nlp.py`).
   - **Phúc & Tony (sau khi xong QA PA4 `25/11`)**: Khởi tạo `backend/app/services/recommendation_service.py` (Layer 1 SQL PostGIS Allergen Hard Filter theo Guardrail #7 + Layer 2 Heuristic Scoring).

---

## 4. Tiêu chuẩn Nghiệm thu Release 0.3 (PA4 Exit Criteria)

- [ ] **VNPay HMAC-SHA512 & Idempotent IPN**: Từ chối chữ ký giả (`RspCode: "97"`), chặn xử lý trùng (`RspCode: "02"`), hoàn kho nguyên tử khi thất bại, cập nhật `PAID` & ghi `PaymentTransaction`.
- [ ] **Payment ↔ QR Reconciliation**: Đơn `VNPAY` chưa `PAID` bị chặn cấp/quét QR; QR dùng 1 lần (`is_used = True`), 100% replay attempts bị chặn, xác thực `< 2s`.
- [ ] **Đủ 8 Core Features End-to-End**: Auth/KYC (`/admin`), Store Menu & Dishes (`/store/menu`, `/store/dishes`), Radar (`/`), Order & Cancel (`/orders`), VNPay (`/orders/vnpay-return`), QR Scanner (`/store/verify-qr`), Reviews & Green Points/Vouchers (`/green-points`).
- [ ] **Quality Gates Xanh 100%**: `ruff check`, `ruff format --check`, `mypy app/`, `pytest tests/ -v`, `npm run lint`, `npm run type-check`, `npm run test`, `npm run build`, `pre-commit run --all-files`.
- [ ] **Hồ sơ PA4**: `docs/PA4.md` + `docs/PA4.pdf` + Video Demo Release 0.3 + Jira Sprint 4 screenshots nộp trước hạn `28/11/2026`.
