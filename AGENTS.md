# EcoBite Platform - AI Pair Programming Rules & Quality Workflow

> **Áp dụng cho**: Tất cả các AI Coding Agents (Antigravity, Cursor, Copilot, Claude Code) khi làm việc trên repository này.  
> **Nguyên tắc cốt lõi**: "AI proposes, Toolchain validates, Tests pass before commit".

---

## 1. Quy trình Phát triển Bắt buộc (Mandatory Development Loop)

Mỗi khi người dùng yêu cầu thêm tính năng, sửa bug hoặc tái cấu trúc (refactor), AI **bắt buộc** phải tuân thủ nghiêm ngặt chu trình 5 bước sau:

```
[ 1. Analyze & Plan ] ──> [ 2. Write Test First ] ──> [ 3. Implement Code ]
                                                              │
                                                              ▼
[ 5. Propose Commit ] <── [ 4. Execute Verification Loop (Auto-Fix if Red) ]
```

### Bước 1: Phân tích & Lên Kế hoạch (Analyze & Plan)
- Đọc kỹ tài liệu nghiệp vụ liên quan trong `docs/` (`01_PRD`, `02_Architecture`, `03_ERD`, `04_API`).
- Xác định rõ vai trò truy cập (Role: `CONSUMER`, `STORE_PARTNER`, `ADMIN`) và các trường hợp biên (Edge Cases: mạng lag, trùng đơn, toạ độ âm, hết hàng).

### Bước 2: Viết Kiểm thử Song song hoặc Trước (Test-First / TDD)
- Mọi hàm nghiệp vụ mới trong `backend/app/services/` hoặc endpoint trong `backend/app/api/` **bắt buộc** phải có file test tương ứng trong `backend/tests/`.
- Mọi component có logic quan trọng hoặc hook trong `frontend/src/` phải có test trong `frontend/__tests__/`.

### Bước 3: Viết Mã Nguồn Tinh gọn (Clean Code Implementation)
- **Backend**: Tuân thủ FastAPI async/await, Pydantic v2 validation, SQLAlchemy 2.0 type annotations (`Mapped[T]`), không dùng hàm đồng bộ (blocking I/O) trong async router.
- **Frontend**: Next.js 14 App Router, Client Component chỉ đánh dấu `'use client'` khi có tương tác (state, hook, browser API), còn lại ưu tiên Server Components.
- **Machine Learning**: Tuyệt đối không load model `.pt` trong request body. Sử dụng cơ chế Lifespan Singleton nạp từ `app.state.ml_model` với `torch.no_grad()`.

### Bước 4: Tự Chạy Kiểm thử trong Terminal (The Automated Verification Loop)
**Trước khi thông báo "Đã xong" cho người dùng, AI phải tự chạy các lệnh kiểm tra sau bằng Terminal:**

#### Kiểm tra Backend (Python):
```bash
cd backend
source venv_backend/bin/activate

# 1. Kiểm tra Linter & Format
ruff check app/
ruff format --check app/

# 2. Kiểm tra Kiểu dữ liệu tĩnh
mypy app/

# 3. Chạy toàn bộ Unit Tests & Integration Tests
pytest tests/ -v
```

#### Kiểm tra Frontend (Next.js & TypeScript):
```bash
cd frontend

# 1. Kiểm tra Linter
npm run lint

# 2. Bắt buộc Type-Check (Không được có bất kỳ lỗi đỏ nào)
npm run type-check
```

> ⚠️ **Quy tắc Tự sửa lỗi (Auto-Fix Rule)**: Nếu lệnh chạy test hoặc type-check trả về lỗi đỏ (Exit code != 0), AI **phải tự động đọc log lỗi Terminal, phân tích nguyên nhân và sửa lại code ngay lập tức**, sau đó chạy lại lệnh test cho đến khi XANH 100%.

### Bước 5: Báo cáo & Đề xuất Commit
- Chỉ khi toàn bộ test đã PASS (Xanh 100%), AI mới được thông báo hoàn thành nhiệm vụ.
- Đề xuất câu lệnh Git Commit chuẩn định dạng **Conventional Commits** (ví dụ: `feat(order): add dynamic hmac qr signature verification and unit tests`).

---

## 2. 5 Ranh giới Bất khả Xâm phạm (Inviolable Guardrails)

1. ❌ **CẤM COMMIT SECRETS**: Tuyệt đối không đọc, ghi hoặc commit file `.env`, token, key bảo mật vào git staging. Luôn sử dụng biến môi trường qua `pydantic-settings`.
2. ❌ **CẤM HARDCODE TOẠ ĐỘ & QUYỀN**: Mọi logic vị trí địa lý phải thông qua hàm PostGIS `ST_DWithin` hoặc `ST_Distance`. Mọi API nhạy cảm phải bọc Dependency phân quyền `require_roles(...)`.
3. ❌ **BẢO MẬT MÃ QR**: Mã QR xác nhận đơn hàng phải dùng thuật toán HMAC-SHA256, có thời hạn hiệu lực (`expires_at`), và phải kiểm tra cờ `is_used` để chống Replay Attack (quét 2 lần).
4. ❌ **CHỐNG OVER-SELLING (TRANH CHẤP TỒN KHO)**: Khi trừ số lượng gói thức ăn `remaining_quantity`, bắt buộc sử dụng DB Transaction với Atomic Update (`WHERE remaining_quantity >= :qty`) hoặc Redis Distributed Lock.
5. ❌ **DECOUPLED ML**: Không cài đặt các thư viện đào tạo nặng (`ultralytics`, `jupyterlab`, `matplotlib`) vào `backend/requirements.txt`. Backend chỉ phục vụ suy luận (`torch` runtime).

---

## 3. Quy chuẩn Đặt tên File & Cấu trúc Thư mục

- **Backend Tests**:
  - `backend/tests/unit/test_<service_name>.py`
  - `backend/tests/integration/test_api_<endpoint>.py`
  - `backend/tests/conftest.py` (Chứa fixtures CSDL test, mock Redis, fake JWT tokens)
- **Frontend Tests**:
  - `frontend/__tests__/components/<ComponentName>.test.tsx`
  - `frontend/__tests__/hooks/<hookName>.test.ts`
- **Git Commit Message Format**:
  - `feat(...)`: Tính năng mới
  - `fix(...)`: Sửa lỗi
  - `test(...)`: Bổ sung hoặc cập nhật test
  - `refactor(...)`: Tái cấu trúc code nhưng không thay đổi hành vi
  - `docs(...)`: Cập nhật tài liệu
