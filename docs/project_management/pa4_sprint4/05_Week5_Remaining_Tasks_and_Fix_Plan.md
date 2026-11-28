# ✅ Danh sách Công việc Còn lại Để Hoàn thành Tuần 5 (Sprint 4 — PA4)

> **Ngày kiểm kê**: `23/11/2026`
> **Nhánh đối chiếu**: `origin/dev` (`3ba71c6`) · `origin/frontend` (`a0dda43`) · `origin/huy` (`a06fd80`)
> **Mục tiêu**: Đóng dứt điểm 100% các đầu việc và lỗi còn sót của **Tuần 5 (`EC4-01` → `EC4-12`)**, đưa toàn bộ Backend & Frontend Quality Gates về trạng thái **XANH 100%** trước khi chuyển sang triển khai Tuần 6 (`EC4-13` → `EC4-18`).

---

## 1. Tổng quan Hiện trạng Toàn Đội (Snapshot `23/11/2026`)

### 1.1. Cập nhật từ các nhánh Remote
- **Võ Ngọc Thịnh (`origin/frontend` → đã merge lên `origin/dev` & `origin/main` ngày `23/11`)**:
  - `b67023c` (`22/11`): Cài Vitest + đồng bộ `types/api.ts`, `dish.service.ts`, `menu.service.ts`, `payment.service.ts`, `store.service.ts`.
  - `aa96d43` (`22/11`): Thêm trang Admin KYC (`/admin`) và cập nhật `Navbar.tsx` phân quyền theo role.
  - `a0dda43` (`23/11`): Thêm trang quản lý thực đơn (`/store/menu`) và đăng/chỉnh tồn kho món dư (`/store/dishes`).
  - `3ba71c6` (`23/11`): Merge nhánh `frontend` vào `origin/dev` và `origin/main`.
  - ⚠️ *Lưu ý*: Thành viên nào chưa kéo mới cần chạy `git pull origin dev` (local `dev` trước đó đang dừng ở `1036124`).
- **Phùng Quốc Huy (`huy` → đã merge vào `dev` ngày `21/11`)**: Xong 100% code & test Gamification/Vouchers + `seed.py` (pass 100%).
- **Đàng Thế Tony (`feature/tony-order-payment-qr-reviews` → đã merge vào `dev` ngày `20/11`)**: Xong 100% code & test Payment↔QR Guard + Verified Reviews (pass 100%).
- **Đặng Trọng Phúc (`feat/vnpay-endpoints-tests` → đã merge vào `dev` ngày `19–20/11`)**: Đã có code VNPay & `GET /stores/me`, nhưng **còn nhiều bug nghiêm trọng trong `payment_service.py` / `payments.py`** và **9/11 unit tests VNPay đang FAIL**.

### 1.2. Bảng Tiến độ Từng Task Tuần 5 (`EC4-01` → `EC4-12`)

| Jira ID | Phụ trách | Trạng thái | Tóm tắt thiếu / lỗi cần đóng |
| :--- | :--- | :---: | :--- |
| **EC4-01** | Phúc | `DONE` | Đã có `VNP_*` settings & `payment_repo.py` (cần bổ sung hỗ trợ set `is_verified=True` khi thanh toán thành công). |
| **EC4-02** | Phúc | `PARTIAL` | Đã có `GET /stores/me`, nhưng **chưa có integration test** trong `test_api_stores.py`. |
| **EC4-03** | Phúc | `NEEDS FIX` | **6 lỗi nghiêm trọng** ở `payment_service.py` & `payments.py` (idempotency hỏng, hoàn kho 2 lần khi IPN fail retry, ký HMAC thiếu URL-encode, hardcode URL, sai timezone, dùng `MagicMock` trong production + lỗi `ruff format`). |
| **EC4-04** | Phúc | `FAIL` | `tests/unit/test_payment_service.py` **fail 9/11 test** (patch sai attribute & assert sai response keys). |
| **EC4-05** | Tony | `FAIL GATE` | `pytest tests/` đang **fail 30/300 tests** (ngoài 9 test VNPay của Phúc, còn **21 test** vỡ do thay đổi `UserCreate(extra="forbid")` + các test `*_bug_exploration.py` & `test_auth_preservation.py`). |
| **EC4-06** | Tony | `DONE` | Pass 100% unit tests (chỉ cần refactor nhẹ tách query DB trực tiếp trong `order_service.py` ra Repository nếu có thời gian). |
| **EC4-07** | Tony | `DONE` | Pass 100% unit & integration tests Verified Reviews. |
| **EC4-08** | Huy | `DONE` | Pass 100% unit & integration tests Gamification/Vouchers. |
| **EC4-09** | Huy | `DONE (thiếu PM)` | Code & test + `seed.py` xong; còn thiếu Spec Kit `002`/`003` (nếu giữ kế hoạch) và cập nhật `04_Sprint4_Progress_Tracker.md`. |
| **EC4-10** | Thịnh | `DONE (1 lỗi nhỏ)` | Đã setup Vitest + chuẩn hóa services/types; còn **lỗi trùng key `"test"`** trong `frontend/package.json`. |
| **EC4-11** | Thịnh | `DONE` | Đã hoàn thành `/admin`, `/store/menu`, `/store/dishes` và `Navbar.tsx` theo role trên `origin/dev`. |
| **EC4-12** | Thịnh | `NOT STARTED` | **Chưa làm**: redirect VNPay ở `/`, trang `/orders/vnpay-return`, nút thanh toán lại & khóa nút QR cho đơn `VNPAY` chưa `PAID` ở `/orders`. |

---

## 2. Công việc Cụ thể Cần Làm Theo Từng Thành viên

### 👤 1. Đặng Trọng Phúc — Backend Engineer 1 (Ưu tiên: **P0 — Blocker**)

**Mục tiêu**: Sửa triệt để các lỗi logic/bảo mật VNPay, đưa `test_payment_service.py` về PASS 100% và bổ sung test cho `GET /stores/me`.

- [ ] **1.1. Sửa lỗ hổng Idempotency & chống hoàn kho 2 lần (`backend/app/services/payment_service.py`, `backend/app/repositories/payment_repo.py`)**
  - Trong `_process_successful_payment()`: set `is_verified=True` khi tạo `PaymentTransaction` (hiện `create_transaction` luôn tạo `is_verified=False` nên check trùng ở dòng 256 không bao giờ kích hoạt).
  - Trong `process_vnpay_ipn()`: kiểm tra trạng thái đơn trước khi xử lý (`if order.payment_status != PaymentStatus.PENDING: return {"RspCode": "02", "Message": "Order already confirmed"}`) để tránh **hoàn kho 2 lần (`atomic_increment_quantity`)** khi VNPay retry IPN thất bại.
  - Sửa xử lý khi `not acquired` ở `distributed_lock`: không cho rơi thẳng xuống critical section bên dưới (trả trạng thái phù hợp hoặc kiểm tra lại an toàn, tránh 2 worker xử lý song song).
  - Kiểm tra `get_by_txn_ref()` tránh lỗi `MultipleResultsFound` nếu một đơn có nhiều lần tạo transaction log.
- [ ] **1.2. Sửa chuẩn ký HMAC-SHA512 & cấu hình VNPay v2.1.0 (`backend/app/services/payment_service.py`)**
  - URL-encode giá trị (`urllib.parse.quote_plus(str(value))`) khi ghép `hash_data` trong `_generate_vnpay_hash()` theo đúng spec VNPay v2.1.0 (tránh lỗi Invalid Signature khi chạy với VNPay Sandbox thật).
  - Trong `_verify_vnpay_ipn_signature()`: loại cả `vnp_SecureHash` **và** `vnp_SecureHashType` trước khi băm lại.
  - Dùng `settings.VNP_URL` thay vì hardcode `_VNPAY_BASE_URL`.
  - Dùng `ZoneInfo("Asia/Ho_Chi_Minh")` (có fallback `timezone(timedelta(hours=7))` giống `order_service.py`) thay vì `datetime.now(UTC).astimezone()` cho `vnp_CreateDate`.
  - Đối chiếu mã `RspCode` chuẩn VNPay (`"01"`: Order not found, `"02"`: Already confirmed, `"04"`: Invalid amount, `"97"`: Invalid signature).
- [ ] **1.3. Dọn dẹp Endpoint VNPay & Format (`backend/app/api/v1/endpoints/payments.py`)**
  - **Xóa ngay** `from unittest.mock import MagicMock` ở endpoint `GET /payments/vnpay/return` (chuyển `verify_vnpay_return` thành `@staticmethod` hoặc truyền `db: DBSession` bình thường).
  - Dùng `Depends(require_roles(UserRole.CONSUMER))` cho `POST /payments/vnpay/create-url` theo đúng Guardrail #2; lấy `client_ip` thật từ `Request` (`X-Forwarded-For` / `request.client.host`) thay vì hardcode `"127.0.0.1"`.
  - **Chốt nhanh contract `POST /payments/vnpay/create-url` với Thịnh**: Hiện Thịnh đã viết `payment.service.ts` gửi `order_id` & `bank_code` qua query params (khớp code hiện tại của Phúc). Nếu giữ query params thì xóa schema thừa `VNPayCreateUrlRequest`; nếu chuyển sang JSON body `VNPayCreateUrlRequest` thì báo Thịnh cập nhật đồng thời `payment.service.ts`.
  - Chạy `ruff format app/api/v1/endpoints/payments.py` để hết lỗi `RUFF_FMT=1`.
- [ ] **1.4. Sửa 9/11 Unit Tests đang FAIL (`backend/tests/unit/test_payment_service.py`)**
  - Sửa `patch.object(type(service), "VNP_HASH_SECRET", ...)` → patch `app.services.payment_service.settings` (ví dụ `monkeypatch.setattr(settings, "VNP_HASH_SECRET", "test_secret")`).
  - Sửa tên thuộc tính mock sai (`service._dish_repo`, `service._payment_repo` → patch `dish_repo` và `service.payments`) và assert đúng key trả về (`txn_ref`, `vnp_amount`).
  - Bổ sung test case thực sự chứng minh: (1) IPN thành công gọi 2 lần → lần 2 trả `"02"`, (2) IPN thất bại gọi 2 lần → **không** hoàn kho 2 lần.
- [ ] **1.5. Bổ sung Integration Test cho `GET /api/v1/stores/me` (`backend/tests/integration/test_api_stores.py`)**
  - Test `STORE_PARTNER` đã onboard lấy được thông tin store của mình (`200`).
  - Test `STORE_PARTNER` chưa onboard nhận `404`.
  - Test `CONSUMER` gọi `/stores/me` bị chặn `403`.

---

### 👤 2. Đàng Thế Tony — Backend Engineer 2 & QA Lead (Ưu tiên: **P0 — Blocker**)

**Mục tiêu**: Khôi phục **100% Backend Quality Gate xanh** trên nhánh `dev` (`300+/300+ tests PASS`, 0 lỗi lint/format/mypy).

- [ ] **2.1. Sửa 11 Integration Tests vỡ do `UserCreate(extra="forbid")` (commit `74986cd`)**
  - Các file bị fail:
    - `backend/tests/integration/test_api_discovery.py` (3 tests)
    - `backend/tests/integration/test_api_stores.py` (7 tests)
    - `backend/tests/integration/test_api_users.py` (1 test)
  - Nguyên nhân: helper `_register_and_login(..., role=...)` vẫn gửi trường `"role"` lên `POST /api/v1/auth/register` nhưng `UserCreate` đã chặn field `role` (`422`) để chống leo thang đặc quyền.
  - Cách xử lý: Cập nhật helper trong các file test này để tạo tài khoản `STORE_PARTNER` / `ADMIN` trực tiếp qua `db_session` fixture (giống cách làm chuẩn trong `conftest.py`), và chỉ đăng ký `CONSUMER` qua API `/auth/register` không kèm field `role`.
- [ ] **2.2. Xử lý 10 Tests Fail ở nhóm Bug Exploration & Preservation**
  - `backend/tests/unit/test_registration_bug_exploration.py` (3 fails): Đang assert `status_code == 201` khi gửi `"role": "admin"` — cần cập nhật sang assert `422` (xác nhận bug đã được vá) hoặc bỏ assertion cũ.
  - `backend/tests/unit/test_timezone_bug_exploration.py` (2 fails): Đang assert `pytest.raises(ZoneInfoNotFoundError)` khi import `order_service` — vì bug đã được fix bằng fallback `timezone(timedelta(hours=7))`, cần đổi assertion sang xác nhận import thành công và fallback đúng GMT+7.
  - `backend/tests/unit/test_inactive_user_bug_exploration.py` (1 fail): Kiểm tra & sửa `test_deactivated_user_continues_api_access` (khả năng cao cũng dùng `/auth/register` gửi kèm `role` bị `422`).
  - `backend/tests/property/test_auth_preservation.py` (4 fails): Kiểm tra và sửa lỗi trong 4 property tests Hypothesis (`test_property_active_user_authentication_preserved`, `token_refresh`, `timezone_operations`, `concurrent_valid_authentications`).
- [ ] **2.3. Kiểm tra & Chốt Gate Backend (`EC4-05`)**
  - Rà soát lại môi trường chuẩn (thống nhất dùng `.venv` theo `AGENTS.md` hoặc cập nhật lại `AGENTS.md` nếu nhóm chốt tên khác; chốt phiên bản `httpx` trong `backend/requirements.txt`).
  - *(Khuyến nghị kiến trúc — P2)*: Trong `backend/app/services/order_service.py` (dòng 548–568), cân nhắc chuyển các lệnh `self.db.get(User/Store)` và `self.db.add(GreenPointsLedger)` sang gọi qua `GamificationRepository` & `StoreRepository` để đảm bảo triệt để kiến trúc 3 tầng `Router -> Service -> Repository`.
  - Chạy lại toàn bộ 4 lệnh Gate sau khi Phúc merge fix VNPay:
    ```bash
    cd backend
    ruff check app/
    ruff format --check app/
    mypy app/
    pytest tests/ -v
    ```

---

### 👤 3. Võ Ngọc Thịnh — Frontend Lead (Ưu tiên: **P0 — Hoàn tất `EC4-12`**)

**Mục tiêu**: Đóng nốt **task duy nhất còn thiếu của FE Tuần 5 (`EC4-12`)**, sửa lỗi nhỏ trong `package.json`, và verify toàn bộ Frontend Gate xanh.

- [ ] **3.1. Sửa lỗi duplicate key trong `frontend/package.json` (`EC4-10` cleanup)**
  - Xóa 1 trong 2 dòng `"test"` bị lặp ở `frontend/package.json` (dòng 11–12), giữ lại:
    ```json
    "test": "vitest run --passWithNoTests"
    ```
    *(để `npm run test` exit `0` trước khi viết các file test ở Tuần 6 `EC4-14`)*.
- [ ] **3.2. Hoàn thiện VNPay Checkout Redirect trên trang Radar (`frontend/src/app/page.tsx`) — `EC4-12`**
  - Khi người dùng đặt đơn trong `OrderModal` với phương thức `payment_method === 'VNPAY'`:
    1. Gọi `POST /api/v1/orders` tạo đơn.
    2. Gọi `paymentService.createVnpayUrl(order.id)` để lấy `payment_url`.
    3. Redirect trình duyệt sang `payment_url` (`window.location.href = payment_url`) — hiển thị trạng thái loading/toast rõ ràng và bắt lỗi nếu tạo URL thất bại (chuyển user về `/orders` để thanh toán lại).
- [ ] **3.3. Tạo trang kết quả trả về VNPay (`frontend/src/app/orders/vnpay-return/page.tsx`) — `EC4-12`**
  - Đọc toàn bộ query params từ URL (`useSearchParams()`, bọc trong `<Suspense>` để không lỗi `next build`).
  - Gọi `paymentService.verifyVnpayReturn(queryParams)` để xác thực chữ ký.
  - Hiển thị trạng thái rõ ràng:
    - Thành công (`is_valid && vnp_ResponseCode === '00'`): hiển thị mã đơn (`txn_ref`), số tiền, nút đi tới `/orders` để lấy mã QR nhận món.
    - Thất bại / chữ ký không hợp lệ: hiển thị lý do, thông báo tồn kho đã được hoàn lại (nếu đơn bị hủy), nút quay lại Radar hoặc `/orders`.
- [ ] **3.4. Cập nhật trang Đơn hàng của tôi (`frontend/src/app/orders/page.tsx`) — `EC4-12`**
  - Với đơn có `payment_method === 'VNPAY'` và `payment_status === 'PENDING'` (và chưa `CANCELLED`/`EXPIRED`):
    - **Khóa/ẩn nút "Xem mã QR"** (hiển thị badge *"Chờ thanh toán VNPay"*), khớp với Backend Guard ở `OrderService`.
    - **Thêm nút "Thanh toán VNPay ngay"** gọi `paymentService.createVnpayUrl(order.id)` → redirect sang cổng VNPay.
  - Chỉ cho phép mở Modal QR khi `payment_method === 'COD'` hoặc `payment_status === 'PAID'`.
- [ ] **3.5. Xác nhận đồng bộ API & chạy Frontend Quality Gate**
  - Phối hợp với Phúc về contract `POST /payments/vnpay/create-url` (query params vs JSON body) và kiểm tra thực tế các trang `/admin`, `/store/menu`, `/store/dishes`, `/orders`, `/orders/vnpay-return` với Backend thật.
  - Chạy xanh 100% 4 lệnh trước khi tạo PR vào `dev` *(lưu ý: chỉ merge vào `dev`, không merge trực tiếp lên `main` trước khi chốt release)*:
    ```bash
    cd frontend
    npm run lint
    npm run type-check
    npm run test
    npm run build
    ```

---

### 👤 4. Phùng Quốc Huy — Backend Engineer 3 & PM (Ưu tiên: **P1**)

**Mục tiêu**: Đồng bộ nhánh, review chất lượng các PR fix của Phúc/Tony/Thịnh, và khép sổ hồ sơ Tuần 5.

- [ ] **4.1. Đồng bộ nhánh local & xử lý thay đổi uncommitted**
  - Kiểm tra thay đổi uncommitted ở `backend/requirements.txt` (`httpx>=0.28.1,<1.0.0`), quyết định commit riêng hoặc revert để đồng nhất với Tony (`EC4-05`).
  - Chạy `git pull origin dev` để đồng bộ các commit mới của Thịnh & Phúc về local `dev`.
- [ ] **4.2. Review & Nghiệm thu PRs đóng Tuần 5**
  - Review PR sửa VNPay của **Phúc** (kiểm tra kỹ 6 bug ở mục 2.1 + test pass 100%).
  - Review PR sửa 21 tests & baseline của **Tony** (xác nhận toàn bộ `pytest tests/ -v` xanh 100%).
  - Review PR `EC4-12` + fix `package.json` của **Thịnh** (chạy thử flow đặt đơn VNPay + Admin KYC + Store Menu/Dishes).
- [ ] **4.3. Đồng bộ Tài liệu Quản trị & Spec Kit**
  - Cập nhật [04_Sprint4_Progress_Tracker.md](./04_Sprint4_Progress_Tracker.md): điền bảng Burn-down thực tế (Actual Remaining), cập nhật trạng thái blocker (`EC4-05`, `EC4-10`, VNPay bugs), và hoàn thiện mục **4.2 Biên bản Chốt Tuần 5 & Planning Tuần 6**.
  - Quyết định và xử lý hạng mục Spec Kit `002` & `003` (trong `specs/` hiện mới có `001-rescue-discovery-order-qr`): tạo spec cho VNPay & Gamification/Reviews hoặc cập nhật rõ phạm vi trong kế hoạch PA4.
  - Sau khi cả 2 Gate (BE + FE) xanh 100% trên `dev`, mở khóa Tuần 6 và khởi tạo nhánh riêng `feat/ai-*` cho `EC4-18`.

---

## 3. Tiêu chuẩn Chốt Hoàn thành Tuần 5 (Exit Checklist)

Chỉ xác nhận **HOÀN THÀNH TUẦN 5** khi toàn bộ các mục sau đều được tick `[x]` trên nhánh `dev`:

- [ ] **Backend Lint & Format**: `ruff check app/` và `ruff format --check app/` exit `0`.
- [ ] **Backend Type-Check**: `mypy app/` exit `0`.
- [ ] **Backend Full Test Suite**: `pytest tests/ -v` **PASS 100%** (0 failed, bao gồm toàn bộ `test_payment_service.py`, `test_api_stores.py` có `/stores/me`, `test_api_discovery.py`, `test_api_users.py`, `test_auth_preservation.py`).
- [ ] **Frontend Tuần 5 đủ 100%**: Xong `EC4-10` (Vitest + services, không trùng key `package.json`), `EC4-11` (`/admin`, `/store/menu`, `/store/dishes`), và `EC4-12` (VNPay redirect, `/orders/vnpay-return`, QR guard & nút thanh toán lại ở `/orders`).
- [ ] **Frontend Quality Gate**: `npm run lint`, `npm run type-check`, `npm run test`, `npm run build` đều exit `0`.
- [ ] **Git Hygiene**: Các nhánh feature merge sạch vào `dev` (không push/merge thẳng vào `main` trước mốc Release 0.3 `v0.3.0-pa4`).
