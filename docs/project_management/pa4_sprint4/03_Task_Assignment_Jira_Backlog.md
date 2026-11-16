# 📌 Bảng Giao việc & Jira Sprint 4 Backlog (1-1 Assignee Rule)

> **Quy tắc Jira (theo `docs/05_Agile_Roadmap_and_Kanban.md`)**:
> - **1-1 Assignee Rule**: Mỗi task chỉ gán duy nhất 1 người chịu trách nhiệm chính (Assignee) và 1 người Review (Reviewer).
> - **Date Lifecycle**: Tạo issue ngay ngày bắt đầu (`16/11`), cập nhật đầy đủ `Start Date`, `Story Points` và `Resolution Date` khi chuyển sang `Done`.
> - **Tổng Story Points cam kết Sprint 4**: **38 pts** (Tuần 5: `23 pts` · Tuần 6: `15 pts`).

---

## 1. Backlog Tuần 5 (`16/11 – 22/11/2026`) — Tổng 23 Story Points

### 🔹 Mảng Backend 1: VNPay & Store Self-Lookup (`Đặng Trọng Phúc` — 7 pts)

| Jira ID | Task / Story | Assignee | Reviewer | Pts | Hạn nội bộ | File Mục tiêu & Tiêu chí Hoàn thành (DoD) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **EC4-01** | Cấu hình VNPay Settings & `PaymentTransactionRepository` | Phúc | Tony | 2 | `17/11` | • Thêm `VNP_TMN_CODE`, `VNP_HASH_SECRET`, `VNP_URL`, `VNP_RETURN_URL` vào `backend/app/core/config.py` & `backend/.env.example`.<br>• Tạo `backend/app/repositories/payment_repo.py` (`create_transaction`, `get_verified_by_txn_ref`, `list_by_order_id`). |
| **EC4-02** | Endpoint `GET /api/v1/stores/me` cho Store Partner | Phúc | Huy | 1 | `16/11` | • Thêm route tĩnh `/stores/me` trước `/stores/{store_id}` tại `backend/app/api/v1/endpoints/stores.py`.<br>• Trả về store của `current_user` (hoặc `404` nếu chưa onboard); có test tích hợp. |
| **EC4-03** | `PaymentService` (HMAC-SHA512, IPN Idempotent & Hoàn kho khi Failed) | Phúc | Tony | 3 | `19/11` | • Tạo `backend/app/services/payment_service.py`: sinh URL VNPay v2.1.0, `hmac.compare_digest` kiểm tra hash, `distributed_lock` IPN chống trùng (`RspCode: "02"`), hoàn kho nguyên tử khi `vnp_ResponseCode != "00"`.<br>• Tạo `backend/app/api/v1/endpoints/payments.py` (`create-url`, `ipn`, `return`), gắn vào `router.py`. |
| **EC4-04** | Unit Tests cho `PaymentService` (VNPay Signing & IPN Logic) | Phúc | Tony | 1 | `20/11` | • Tạo `backend/tests/unit/test_payment_service.py`: test ký SHA-512, sai hash (`97`), sai tiền (`04`), idempotent (`02`), hoàn kho khi failed. |

---

### 🔹 Mảng Backend 2: Env Sync, Payment↔QR Guard & Verified Reviews (`Đàng Thế Tony` — 6 pts)

| Jira ID | Task / Story | Assignee | Reviewer | Pts | Hạn nội bộ | File Mục tiêu & Tiêu chí Hoàn thành (DoD) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **EC4-05** | Đồng bộ Python virtualenv Backend & xác nhận Baseline Test PA3 | Tony | Phúc | 1 | `16/11` | • Cài đủ `backend/requirements.txt` (bao gồm `redis`) vào `.venv` / `venv_backend`.<br>• `ruff check`, `ruff format --check`, `mypy app/`, `pytest tests/ -q` chạy xanh 100%. |
| **EC4-06** | Khóa Payment↔QR & Cộng Điểm Xanh/CO₂ thật khi Quét QR | Tony | Phúc | 2 | `18/11` | • Cập nhật `backend/app/services/order_service.py`: chặn `issue_or_get_qr_payload` & `verify_and_complete_order` với đơn `VNPAY` chưa `PAID` (`409`); `COD` xong → `PAID`; cộng `User.green_points_balance`, ghi `GreenPointsLedger`, cộng `Store.total_co2_saved_kg` trong 1 transaction.<br>• Cập nhật `backend/tests/unit/test_order_service.py`. |
| **EC4-07** | Module Verified Reviews (`ReviewRepo`, `ReviewService`, Endpoints & Tests) | Tony | Huy | 3 | `20/11` | • Tạo `review_repo.py`, `review_service.py`, `endpoints/reviews.py` (`POST /orders/{id}/review`, `GET /stores/{id}/reviews`), gắn `router.py`.<br>• Chỉ đơn `COMPLETED` của chính chủ mới được review; chặn trùng; tự tính lại `Store.rating_avg`.<br>• Viết `backend/tests/unit/test_review_service.py`. |

---

### 🔹 Mảng Backend 3: Gamification/Vouchers, Seed & PM (`Phùng Quốc Huy` — 5 pts)

| Jira ID | Task / Story | Assignee | Reviewer | Pts | Hạn nội bộ | File Mục tiêu & Tiêu chí Hoàn thành (DoD) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **EC4-08** | `GamificationRepository` & `GamificationService` (Points, Rank, Vouchers) | Huy | Tony | 3 | `18/11` | • Tạo `gamification_repo.py` (bao gồm atomic SQL `WHERE green_points_balance >= :cost`) và `gamification_service.py`.<br>• Tạo `endpoints/gamification.py` (`GET /green-points/me`, `GET /vouchers`, `GET /vouchers/me`, `POST /vouchers/{id}/redeem`), gắn `router.py`. |
| **EC4-09** | Unit Tests Gamification & Cập nhật `db/seed.py` | Huy | Phúc | 2 | `20/11` | • Tạo `backend/tests/unit/test_gamification_service.py` (test rank, trừ điểm nguyên tử, thiếu điểm `409`, voucher hết hạn).<br>• Cập nhật `backend/app/db/seed.py` thêm `Voucher` mẫu, 1 store `PENDING` cho Admin KYC, mẫu `Review` & `GreenPointsLedger`. |

---

### 🔹 Mảng Frontend Tuần 5: Vitest Setup, Portals & VNPay Flow (`Võ Ngọc Thịnh` — 5 pts)

| Jira ID | Task / Story | Assignee | Reviewer | Pts | Hạn nội bộ | File Mục tiêu & Tiêu chí Hoàn thành (DoD) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **EC4-10** | Setup Vitest + Chuẩn hóa `types/api.ts` & API Services | Thịnh | Huy | 1 | `17/11` | • Cài Vitest + Testing Library + jsdom, thêm `"test"` vào `frontend/package.json` & `vitest.config.ts`.<br>• Sửa `dish.service.ts` khớp `endpoints/dishes.py`, chuẩn hóa `PaymentStatus`, tạo `menu.service.ts`, `payment.service.ts`, cập nhật `store.service.ts`. |
| **EC4-11** | Admin KYC Dashboard (`/admin`) & Store Portal (`/store/menu`, `/store/dishes`) | Thịnh | Huy | 2 | `19/11` | • Tạo `frontend/src/app/admin/page.tsx` (duyệt/từ chối store `PENDING`).<br>• Tạo `/store/menu/page.tsx` & `/store/dishes/page.tsx` (lấy `store_id` từ `/stores/me`, CRUD menu, đăng món dư preview 50%/70%, chỉnh tồn kho). |
| **EC4-12** | VNPay Checkout Redirect, `/orders/vnpay-return` & Guard QR ở `/orders` | Thịnh | Phúc | 2 | `21/11` | • `page.tsx`: chọn `VNPAY` → gọi `create-url` → redirect Sandbox.<br>• Tạo `frontend/src/app/orders/vnpay-return/page.tsx`.<br>• `/orders/page.tsx`: nút thanh toán lại `VNPAY`, khóa nút QR khi `VNPAY` chưa `PAID`. |

---

## 2. Backlog Tuần 6 (`23/11 – 28/11/2026`) — Tổng 15 Story Points

| Jira ID | Task / Story | Assignee | Reviewer | Pts | Hạn nội bộ | Phạm vi & Tiêu chí Hoàn thành (DoD) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **EC4-13** | Frontend Feature 8 (`/green-points`, Review Modal ở `/orders`) & Store Orders tại `/store/verify-qr` | Thịnh | Huy | 3 | `25/11` | • Trang `/green-points` (Ví điểm, CO₂, Rank, lịch sử, đổi Voucher).<br>• Modal Review 1–5 sao ở `/orders` (đơn `COMPLETED`); bảng đơn quán ở `/store/verify-qr`; cập nhật `Navbar.tsx`. |
| **EC4-14** | Bộ Unit Tests Frontend bằng Vitest (`__tests__/components/`, `__tests__/hooks/`) | Thịnh | Tony | 2 | `25/11` | • Tối thiểu 3 file test cho các luồng mới (Checkout/VNPay, Orders/QR guard, GreenPoints/Voucher) pass 100% qua `npm run test`. |
| **EC4-15** | Integration & Concurrency Tests cho Payments, Voucher & QR Benchmark `< 2s` | Tony | Phúc | 3 | `25/11` | • `tests/integration/test_api_payments.py`, `test_api_reviews.py`, `test_api_gamification.py`.<br>• Test IPN đồng thời không ghi trùng, Voucher redeem đồng thời không âm điểm, QR verify `< 2s`. |
| **EC4-16** | Test E2E VNPay Sandbox thật (ngrok/staging) & Bug Fix trước Code Freeze | Phúc | Tony | 2 | `25/11` | • Chụp log/ảnh đối soát IPN thành công & thất bại thật trên Sandbox; fix mọi lỗi phát sinh trước `25/11`. |
| **EC4-17** | Đồng bộ Docs (`04_API_Specification.md`, `AGENTS.md`), Quay Demo & Biên soạn `docs/PA4.md` | Huy | Cả nhóm | 3 | `27/11` | • `docs/PA4.md` + `docs/PA4.pdf` + Video Demo Release 0.3 hoàn tất trước `23:59` `27/11`. |
| **EC4-18** | *(Khởi động sớm PA5 — Nhánh riêng `feat/ai-*`)* AI Quick-Post Service & Allergen Hard Filter | Huy *(hỗ trợ Phúc từ `26/11`)* | Phúc | 2 | `28/11` | • Tạo `quick_post_service.py` + `endpoints/ml.py` (`POST /ml/parse-dish-nlp` dùng `app/schemas/nlp.py`) và khung `recommendation_service.py` (SQL PostGIS Hard Filter theo Guardrail #7) trên nhánh tách biệt, không ảnh hưởng Release 0.3. |
