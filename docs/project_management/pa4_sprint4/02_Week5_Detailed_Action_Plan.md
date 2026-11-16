# 📅 Kế hoạch Hành động Chi tiết Tuần 5 (16/11/2026 – 22/11/2026)

> **Cơ cấu Phân công Tuần 5**:
> - **3 Thành viên Backend (`Đặng Trọng Phúc`, `Đàng Thế Tony`, `Phùng Quốc Huy`)**: Chia 3 mảng độc lập để **hoàn thành 100% Backend của toàn bộ 8 Core Features + Unit Tests** ngay trong tuần này.
> - **Frontend Lead (`Võ Ngọc Thịnh`)**: Triển khai phần **Admin / Store Portals & VNPay Checkout** trong Tuần 5 (phần UI Feature 8 & bộ test Vitest hoàn tất ở đầu Tuần 6 — vẫn đảm bảo xong hết Core Features trước mốc PA4 `28/11`).

---

## 1. Phân công Chi tiết Từng Thành viên Trong Tuần 5

### 👤 1. Đặng Trọng Phúc — Backend Engineer 1 (Feature 6: VNPay Core + `GET /stores/me`)
1. **Cấu hình & Repository VNPay**:
   - Bổ sung `VNP_TMN_CODE`, `VNP_HASH_SECRET`, `VNP_URL`, `VNP_RETURN_URL` vào `backend/app/core/config.py` và `backend/.env.example`.
   - Tạo `backend/app/repositories/payment_repo.py` (`PaymentTransactionRepository`): `create_transaction`, `get_verified_by_txn_ref`, `list_by_order_id`.
2. **Dịch vụ Thanh toán (`backend/app/services/payment_service.py`)**:
   - `create_vnpay_payment_url(order_id, consumer_id, client_ip, bank_code=None)`: kiểm tra quyền sở hữu đơn, `payment_method == VNPAY`, `payment_status == PENDING`, đơn còn hiệu lực; tạo URL VNPay v2.1.0 (`vnp_Amount = int(total_amount * 100)`, `vnp_TxnRef = order.order_code`, giờ `Asia/Ho_Chi_Minh`, ký **HMAC-SHA512**).
   - `process_vnpay_ipn(query_params)`: kiểm tra chữ ký `hmac.compare_digest` (`RspCode: "97"` nếu sai), kiểm tra `vnp_TxnRef` (`"01"` nếu không có), kiểm tra `vnp_Amount` (`"04"` nếu sai số tiền), dùng `distributed_lock(f"lock:payment:ipn:{txn_ref}")` đảm bảo **idempotent** (`"02"` nếu đã xử lý).
     - `vnp_ResponseCode == "00"` → `Order.payment_status = PAID` + lưu `vnpay_transaction_no`, `vnpay_bank_code`, `vnpay_pay_date` + tạo `PaymentTransaction(is_verified=True)`.
     - `vnp_ResponseCode != "00"` → `Order.payment_status = FAILED`, `Order.status = CANCELLED` + **hoàn kho nguyên tử** (`dish_repo.atomic_increment_quantity`) trong cùng transaction.
   - `verify_vnpay_return(query_params)`: xác thực chữ ký cho endpoint `return` (hỗ trợ đối soát khi test trên `localhost` không có IPN public).
3. **Endpoints & Unit Test**:
   - Tạo `backend/app/api/v1/endpoints/payments.py` (`POST /payments/vnpay/create-url`, `GET /payments/vnpay/ipn`, `GET /payments/vnpay/return`), gắn vào `backend/app/api/v1/router.py`.
   - Thêm `GET /api/v1/stores/me` vào `backend/app/api/v1/endpoints/stores.py` (đặt **trước** `/stores/{store_id}`).
   - Viết `backend/tests/unit/test_payment_service.py` (ký/verify HMAC-SHA512, sai hash, lệch số tiền, idempotency, hoàn kho khi failed).

---

### 👤 2. Đàng Thế Tony — Backend Engineer 2 & QA (Env Sync + Payment↔QR Guard + Feature 8 Reviews)
1. **Đồng bộ Môi trường Backend (Ngày 1)**:
   - Sửa môi trường `backend/venv_backend` / `.venv` (cài đủ `requirements.txt` gồm `redis`) để `ruff check app/`, `ruff format --check app/`, `mypy app/`, `pytest tests/ -q` chạy xanh 100% làm baseline.
2. **Hoàn thiện `OrderService` (`backend/app/services/order_service.py`)**:
   - **Khóa Payment ↔ QR**: `issue_or_get_qr_payload` và `verify_and_complete_order` phải kiểm tra nếu `order.payment_method == PaymentMethod.VNPAY` và `order.payment_status != PaymentStatus.PAID` → raise `409 Conflict` (*"Đơn hàng VNPAY chưa hoàn tất thanh toán"*).
   - **Thanh toán COD & Cộng Điểm Xanh khi Quét QR (`verify_and_complete_order`)**:
     - Nếu `payment_method == COD` → set `payment_status = PaymentStatus.PAID`.
     - Trong cùng DB transaction: cộng `User.green_points_balance += order.green_points_earned`, tạo bản ghi `GreenPointsLedger` (`PointActionType.ORDER_RESCUE`, `co2_saved_kg=order.co2_saved_kg`), và cộng `Store.total_co2_saved_kg += order.co2_saved_kg`.
3. **Module Verified Reviews (Feature 8A)**:
   - Tạo `backend/app/repositories/review_repo.py` (`create_review`, `get_by_order_id`, `list_by_store`, cập nhật `Store.rating_avg` trung bình).
   - Tạo `backend/app/services/review_service.py`: chỉ cho phép `CONSUMER` chủ đơn đánh giá khi đơn đã `COMPLETED`, chặn đánh giá 2 lần (`409 Conflict` theo ràng buộc `order_id` unique).
   - Tạo `backend/app/api/v1/endpoints/reviews.py` (`POST /api/v1/orders/{order_id}/review`, `GET /api/v1/stores/{store_id}/reviews`) & gắn vào `router.py`.
4. **Unit Tests**:
   - Cập nhật `tests/unit/test_order_service.py` (case `VNPAY` chưa `PAID` bị chặn QR, case `COD` hoàn tất chuyển `PAID` + ghi `GreenPointsLedger`).
   - Viết `tests/unit/test_review_service.py`.

---

### 👤 3. Phùng Quốc Huy — Backend Engineer 3 & PM (Feature 8 Gamification/Vouchers + Seed + Spec/PRs)
1. **Module Green Points & Vouchers (Feature 8B)**:
   - Tạo `backend/app/repositories/gamification_repo.py`:
     - Truy vấn `GreenPointsLedger` theo `user_id` (lịch sử mới nhất), tính tổng `total_co2_saved_kg` và `total_meals_saved` từ các đơn `COMPLETED`.
     - Truy vấn danh sách `Voucher` còn hạn (`is_active == True`, `expires_at > now`) & `UserVoucher` của user.
     - Hàm **atomic point deduction** trên `User` (`UPDATE users SET green_points_balance = green_points_balance - :cost WHERE id = :uid AND green_points_balance >= :cost`) để chống trừ âm điểm khi bấm đúp.
   - Tạo `backend/app/services/gamification_service.py`:
     - `get_my_green_points(user_id)`: trả về `balance_points`, `total_co2_saved_kg`, `total_meals_saved`, `rank_title` (rule-based theo mốc điểm/CO₂), `recent_ledger`.
     - `list_available_vouchers()`, `list_my_vouchers(user_id)`.
     - `redeem_voucher(user_id, voucher_id)`: kiểm tra voucher còn hạn/active, trừ điểm nguyên tử, ghi `GreenPointsLedger` (`PointActionType.VOUCHER_REDEEM`, số âm), tạo `UserVoucher` trong cùng DB transaction.
   - Tạo `backend/app/api/v1/endpoints/gamification.py`:
     - `GET /api/v1/green-points/me` (`CONSUMER`)
     - `GET /api/v1/vouchers` (Public/Authenticated) & `GET /api/v1/vouchers/me` (`CONSUMER`)
     - `POST /api/v1/vouchers/{voucher_id}/redeem` (`CONSUMER`)
   - Viết `backend/tests/unit/test_gamification_service.py` (tính rank, trừ điểm nguyên tử, không đủ điểm trả `409`, voucher hết hạn trả `400/409`).
2. **Dữ liệu Mẫu & Quản trị Dự án**:
   - Cập nhật `backend/app/db/seed.py`: seed 3–4 `Voucher` mẫu (`ECO10K`, `ECO25K`, `ECO50K`), 1 cửa hàng `PENDING` để test Admin KYC, và mẫu `Review` + `GreenPointsLedger`.
   - Chủ trì Sprint 4 Planning (`20:30 Thứ Hai 16/11`), tạo Spec Kit `002` & `003`, cấu hình Jira Sprint 4, review PR cho Phúc/Tony/Thịnh.

---

### 👤 4. Võ Ngọc Thịnh — Frontend Lead (Lộ trình 2 tuần: Tuần 5 xong Portals & VNPay + Setup Vitest)
1. **Setup Test & Chuẩn hóa Services (Ngày 1–2)**:
   - Cài `vitest`, `@vitejs/plugin-react`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`; tạo `frontend/vitest.config.ts` và script `"test": "vitest run"` trong `frontend/package.json`.
   - Sửa `frontend/src/types/api.ts` (chuẩn hóa `PaymentStatus` thành `'PENDING' | 'PAID' | 'FAILED'`, thêm DTO MenuItem/Dish/Store/VNPay).
   - Sửa `frontend/src/services/dish.service.ts` gọi đúng endpoints ở `backend/app/api/v1/endpoints/dishes.py`; tạo `menu.service.ts`, `payment.service.ts`, bổ sung `getMyStore`, `getPendingStores`, `reviewStoreKyc` vào `store.service.ts`.
2. **Admin KYC & Store Partner Portals (Ngày 2–4)**:
   - `/admin`: Danh sách quán chờ duyệt (`GET /admin/stores/pending`), xem chứng nhận ATVSTP, duyệt (`APPROVED`) hoặc từ chối kèm lý do (`REJECTED`).
   - `/store/menu`: Lấy `store_id` từ `GET /stores/me`, CRUD món gốc (`menu_items`).
   - `/store/dishes`: Đăng món dư cuối ca (`POST /dishes`) kế thừa từ `menu_items`, preview giảm giá 50%/70%, chỉnh sửa số lượng còn lại (`PATCH /dishes/{id}/quantity`).
   - Cập nhật `Navbar.tsx` điều hướng rõ ràng theo role (`CONSUMER`, `STORE_PARTNER`, `ADMIN`).
3. **VNPay Checkout Flow (Ngày 5–7)**:
   - `frontend/src/app/page.tsx`: khi user chọn `VNPAY` → tạo đơn (`POST /orders`) → gọi `POST /payments/vnpay/create-url` → chuyển hướng sang cổng VNPay Sandbox.
   - Tạo `frontend/src/app/orders/vnpay-return/page.tsx`: hiển thị kết quả thanh toán, đối soát trạng thái đơn, nút đi tới QR nhận món.
   - Cập nhật `frontend/src/app/orders/page.tsx`: hiển thị nút "Thanh toán VNPay ngay" cho đơn `VNPAY` đang `PENDING`, và chỉ mở nút "Xem mã QR" khi `PAID` (hoặc `COD`).

---

## 2. Lịch trình Chi tiết Từng Ngày trong Tuần 5 (`16/11 – 22/11/2026`)

| Ngày | Đặng Trọng Phúc (BE: VNPay & `/stores/me`) | Đàng Thế Tony (BE: QR Guard & Reviews) | Phùng Quốc Huy (BE: Gamification & PM) | Võ Ngọc Thịnh (FE: Portals & VNPay) |
| :--- | :--- | :--- | :--- | :--- |
| **Thứ Hai (16/11)** | Thêm `VNP_*` vào `config.py`, `.env.example`; tạo `payment_repo.py` & `GET /stores/me` | Đồng bộ `.venv` / `venv_backend`, chạy xanh toàn bộ test PA3 | **20:30 Họp Planning**; tạo Jira Sprint 4, Spec Kit `002`/`003`; khởi tạo `gamification_repo.py` | Cài **Vitest**; sửa `types/api.ts` & `dish.service.ts`; tạo `menu.service.ts`, `payment.service.ts` |
| **Thứ Ba (17/11)** | Viết `payment_service.py` (tạo URL HMAC-SHA512 + verify signature) | Cập nhật `OrderService`: chặn QR khi `VNPAY` chưa `PAID`; `COD` xong → `PAID` + ghi `GreenPointsLedger` | Hoàn thiện `gamification_repo.py` (atomic deduct points) & `gamification_service.py` | Dựng trang **Admin KYC (`/admin`)** + nối `GET /admin/stores/pending` & `PATCH review` |
| **Thứ Tư (18/11)** | Viết logic IPN idempotent + hoàn kho khi thanh toán thất bại; test unit local | Viết `review_repo.py` & `review_service.py` (chỉ đơn `COMPLETED`, 1 lần/đơn, update `Store.rating_avg`) | Tạo `endpoints/gamification.py` (`green-points/me`, `vouchers`, `redeem`), gắn `router.py` | Dựng trang **Store Menu (`/store/menu`)** lấy `store_id` từ `/stores/me` & CRUD `menu_items` |
| **Thứ Năm (19/11)** | Tạo `endpoints/payments.py` (`create-url`, `ipn`, `return`), gắn `router.py` | Tạo `endpoints/reviews.py` (`POST /orders/{id}/review`, `GET /stores/{id}/reviews`), gắn `router.py` | Cập nhật `seed.py` (Vouchers + Pending Store + Ledger); viết `test_gamification_service.py` | Dựng trang **Store Dishes (`/store/dishes`)** (đăng món dư, preview 50%/70%, chỉnh tồn kho) |
| **Thứ Sáu (20/11)** | Viết `test_payment_service.py` & test URL VNPay Sandbox thật | Viết `test_review_service.py` & cập nhật `test_order_service.py` (QR Guard + Ledger) | Review PR Backend của Phúc & Tony; test Swagger toàn bộ API mới | Nối Checkout `VNPAY` ở `page.tsx` → redirect Sandbox & tạo `/orders/vnpay-return` |
| **Thứ Bảy (21/11)** | Fix edge case VNPay & hỗ trợ Thịnh nối API return/IPN | Hỗ trợ review chéo PR & bổ sung test case thiếu cho F6/F7/F8 | Review PR Frontend đợt 1 của Thịnh; kiểm thử thủ công E2E flow BE | Cập nhật `/orders` (nút thanh toán lại `VNPAY`, khóa QR khi chưa `PAID`) & `Navbar.tsx` |
| **Chủ Nhật (22/11)** | Đóng toàn bộ PR Backend VNPay & `/stores/me` | Chạy full Backend Quality Gate (`ruff`, `mypy`, `pytest tests/ -v`) | **21:00 Họp Chốt Tuần 5**: Nghiệm thu **100% Backend Core**; phân việc Tuần 6 (Integration/AI cho BE + F8 UI/Vitest cho FE) | Chạy `npm run lint`, `type-check`, `build`, kiểm tra Vitest sẵn sàng cho tuần 6 |

---

## 3. Tiêu chí Chốt Mốc Cuối Tuần 5 (`22/11/2026`)

1. **Backend Core 100% Done**:
   - Đủ mọi API của cả 8 Core Features trên `/docs` Swagger (`GET /stores/me`, VNPay `create-url`/`ipn`/`return`, QR Payment Guard, Reviews, Green Points & Vouchers).
   - Toàn bộ `ruff check app/`, `ruff format --check app/`, `mypy app/`, `pytest tests/ -v` đều **PASS 100%**.
2. **Frontend Core Đạt 75% (Đúng nhịp 2 tuần)**:
   - Xong Admin KYC (`/admin`), Store Menu & Dishes (`/store/menu`, `/store/dishes`), VNPay Checkout & `/orders/vnpay-return`, Vitest đã chạy được (`npm run test`).
   - Tuần 6 Thịnh làm nốt UI Feature 8 (`/green-points`, Modal Review, bảng đơn ở `/store/verify-qr`) + bộ Vitest component/hook tests trước Code Freeze `25/11`.
3. **Mở khóa Tuần 6**:
   - Ngay thứ Hai `23/11`, 3 người Backend chuyển sang chạy **Integration/Concurrency Tests + E2E Sandbox + Báo cáo PA4** và **khởi động code AI Features (PA5)** trên nhánh riêng `feat/ai-*`.
