# EcoBite Platform - AI Pair Programming Rules & Quality Workflow

> **Áp dụng cho**: Tất cả các AI Coding Agents (Antigravity, Cursor, Copilot, Claude Code, OpenCode) khi làm việc trên repository này.
> **Nguyên tắc cốt lõi**: "AI proposes, Toolchain validates, Tests pass before commit".
> **Độ tin cậy**: Bản này đã được đối chiếu trực tiếp với codebase (`pyproject.toml`, `requirements.txt`, `package.json`, `tests/conftest.py`, `docker-compose.yml`) — mọi đường dẫn, lệnh kiểm thử dưới đây đều chạy được đúng như đã ghi.

---

## 0. Công nghệ đã kiểm chứng trong Repo (Verified Tech Stack)

| Thành phần | Công cụ / Phiên bản | Ghi chú vận hành |
| --- | --- | --- |
| Backend runtime | Python 3.11 | `ruff` và `mypy` đều cấu hình target `py311` |
| Web framework | FastAPI 0.111.0 + Uvicorn 0.30.1 | Entry `app.main:app` (factory `create_app()`), port 8000 |
| ORM & Migration | SQLAlchemy 2.0.30 (async) + Alembic 1.13.1 | App chạy `asyncpg`; Alembic chạy `psycopg2` qua `settings.sync_database_url` |
| Database | PostgreSQL 16 + PostGIS 3.4 (`postgis/postgis:16-3.4-alpine`) | GeoAlchemy2 0.15.1 + Shapely; dev/test fallback `sqlite+aiosqlite` |
| Cache | Redis 7 (`redis:7-alpine`) + redis-py 5.0.6 | Async client & distributed lock tại `app/core/redis.py`; cấu hình qua biến môi trường (`REDIS_URL`, `REDIS_LOCK_TIMEOUT_SECONDS`, `REDIS_SOCKET_TIMEOUT_SECONDS`) |
| Auth | python-jose 3.3.0 + passlib/bcrypt 4.0.1 | JWT HS256, dual token access/refresh |
| GenAI | google-genai 1.3.0 (`gemini-2.5-flash`) | Structured Output bọc trong `app/schemas/nlp.py` |
| ML runtime | torch 2.3.1 + torchvision 0.18.1 | Chỉ suy luận (inference); huấn luyện tách rời trong `ml/` (ultralytics, jupyterlab...) |
| Backend quality | pytest 8.2.2 + pytest-asyncio 0.23.7, ruff 0.4.9, mypy 1.10 | Nguồn sự thật: `backend/pyproject.toml` (`asyncio_mode = "auto"`, line-length 100, rules `E/F/I/UP/B`, plugin `pydantic.mypy`) |
| Frontend | Next.js 14.2.4 (App Router), React 18.3, TypeScript 5.4 (`strict: true`), Tailwind CSS 3.4, TanStack React Query 5, Axios 1.7, Leaflet 1.9 + react-leaflet 4.2, html5-qrcode, qrcode.react | Path alias `@/*` → `src/*`; ESLint: `eslint-config-next` |
| Git hooks | pre-commit 3.7.1 | Chặn `.env`/secrets và file > 5MB (không commit trọng số `.pt`) |

Hạ tầng khởi động bằng `docker-compose.yml` (PostGIS + Redis); biến môi trường mẫu tại `.env.example` (root) và `backend/.env.example`.

---

## 1. Quy trình Phát triển Bắt buộc (Mandatory Development Loop)

Mỗi khi người dùng yêu cầu thêm tính năng, sửa bug hoặc tái cấu trúc (refactor), AI **bắt buộc** phải tuân thủ nghiêm ngặt chu trình 5 bước sau:

```text
[ 1. Analyze & Plan ] ──> [ 2. Write Test First ] ──> [ 3. Implement Code ]
                                                              │
                                                              ▼
[ 5. Propose Commit ] <── [ 4. Execute Verification Loop (Auto-Fix if Red) ]
```

### Bước 1: Phân tích & Lên Kế hoạch (Analyze & Plan)
- Đọc kỹ tài liệu nghiệp vụ liên quan trong `docs/`: `00_Project_Proposal_Section_B.md`, `01_PRD_and_User_Stories.md`, `02_System_Architecture.md`, `03_Database_Schema_ERD.md`, `04_API_Specification.md`, `05_Agile_Roadmap_and_Kanban.md`, `06_Environment_and_ML_Setup_Guide.md`, `07_AI_Development_Workflow_and_Quality_Gates.md` (4 Quality Gates).
- Xác định rõ vai trò truy cập (`UserRole` StrEnum trong `app/models/user.py`: `CONSUMER`, `STORE_PARTNER`, `ADMIN`) và các trường hợp biên (mạng lag, trùng đơn, toạ độ âm, hết hàng → atomic update).
- Kiểm tra API đã có sẵn trước khi tạo endpoint mới. Bề mặt API hiện tại: `auth` (register / login / refresh), `users` (`/me`), `stores` (onboard, Radar `/stores/nearby`, admin duyệt quán `/admin/stores/*`), `menu` (CRUD menu-items), `dishes` (batch, active, cập nhật số lượng), `orders` (đặt đơn `POST /orders` — chỉ `CONSUMER`, hủy đơn `PATCH /orders/{order_id}/cancel` — `CONSUMER` hoặc `STORE_PARTNER`) — xem `app/api/v1/router.py`.

### Bước 2: Viết Kiểm thử Song song hoặc Trước (Test-First / TDD)
- Mọi thao tác dữ liệu trong `backend/app/repositories/`, hàm nghiệp vụ trong `backend/app/services/` hoặc endpoint trong `backend/app/api/` **bắt buộc** phải có file test tương ứng trong `backend/tests/` (`unit/` cho logic & atomic queries, `integration/` cho từng endpoint).
- pytest đã bật `asyncio_mode = "auto"` — test và fixture async **không** cần `@pytest.mark.asyncio`. CSDL test là SQLite in-memory (`aiosqlite`) dựng từ `backend/tests/conftest.py`; kiểu PostGIS/JSONB phải giữ dạng "portable" (xem Bước 3) để test xanh mà không cần Postgres thật.
- Mọi component có logic quan trọng hoặc hook trong `frontend/src/` phải có test trong `frontend/__tests__/components/` hoặc `frontend/__tests__/hooks/`.
  - ⚠️ Test runner frontend **chưa được cấu hình** (chưa có script `test` trong `package.json`): khi viết test frontend đầu tiên, phải wire Vitest (+ Testing Library, jsdom) và thêm script `test` vào `package.json` — không dừng ở việc viết file test mà không chạy được.

### Bước 3: Viết Mã Nguồn Tinh gọn (Clean Code Implementation)
- **Backend (Kiến trúc 3 tầng `Router -> Service -> Repository`)**:
  - `backend/app/api/v1/endpoints/`: Tầng HTTP Router (xử lý request/response, RBAC `require_roles`, **không chứa câu lệnh SQL**; dependencies dùng chung đặt tại `backend/app/api/deps.py`).
  - `backend/app/services/`: Tầng Nghiệp vụ (logic tính giá giờ chót, kiểm tra quyền sở hữu, điều phối giao dịch, gọi xuống Repository; không tự thao tác SQL).
  - `backend/app/repositories/`: Tầng Truy xuất Dữ liệu (`*_repo.py`, chỉ chứa câu lệnh SQLAlchemy 2.0 trên `AsyncSession` và Atomic Update — mẫu chuẩn: `dish_repo.atomic_decrement_quantity`).
  - Tuân thủ FastAPI async/await, Pydantic v2 validation, SQLAlchemy 2.0 type annotations (`Mapped[T]`); **không dùng blocking I/O trong async router** (psycopg2 chỉ dùng cho Alembic).
  - Kiểu dữ liệu "portable" bắt buộc ở model: JSON dùng `JSON_TYPE` (JSONB trên PostgreSQL, JSON trên SQLite) và toạ độ dùng `Geometry(POINT, srid=4326)` có fallback String trên SQLite — xem `app/models/user.py` và `app/models/store.py`.
- **Frontend**: Next.js 14 App Router (`src/app/`). Client Component chỉ đánh dấu `'use client'` khi có tương tác (state, hook, browser API), còn lại ưu tiên Server Components. Gọi API bắt buộc đi qua axios client `@/lib/api-client` (⚠️ file này **chưa tồn tại** — phải tạo trước khi import); state phía client dùng TanStack React Query (`providers/QueryProvider.tsx`).
- **Machine Learning**: Tuyệt đối không load model `.pt` trong request body. Model chỉ nạp đúng một lần trong lifespan (`app.main` lifespan hook), lưu Singleton `app.state.ml_model`, suy luận bọc `torch.no_grad()`. Trọng số nằm ngoài git tại `../ml/weights` (biến `ML_WEIGHTS_DIR` / `ML_MODEL_FILENAME`), naming `.pt` theo `ml/README.md`.

### Bước 4: Tự Chạy Kiểm thử trong Terminal (The Automated Verification Loop)
**Trước khi thông báo "Đã xong" cho người dùng, AI phải tự chạy các lệnh kiểm tra sau bằng Terminal:**

#### Kiểm tra Backend (Python 3.11):
```bash
cd backend
.venv\Scripts\activate             # Windows CMD
# hoặc: .\.venv\Scripts\Activate.ps1   (Windows PowerShell)
# hoặc: source .venv/bin/activate      (Linux / macOS / Git Bash)

# 1. Kiểm tra Linter & Format (ruff theo pyproject.toml)
ruff check app/
ruff format --check app/

# 2. Kiểm tra Kiểu dữ liệu tĩnh (mypy + plugin pydantic.mypy)
mypy app/

# 3. Chạy toàn bộ Unit Tests & Integration Tests
pytest tests/ -v
```

> Virtualenv chuẩn của dự án tên `.venv`, đặt trong thư mục `backend/` (đã tồn tại, hướng dẫn tại `backend/SETUP.md`).

#### Kiểm tra Frontend (Next.js 14 & TypeScript):
```bash
cd frontend

# 1. Kiểm tra Linter (next lint + eslint-config-next)
npm run lint

# 2. Bắt buộc Type-Check (tsc --noEmit, strict: true — không được có bất kỳ lỗi đỏ nào)
npm run type-check
```

#### Cổng bổ trợ — Pre-commit hooks:
```bash
pre-commit run --all-files
```

> ⚠️ **Quy tắc Tự sửa lỗi (Auto-Fix Rule)**: Nếu lệnh chạy test hoặc type-check trả về lỗi đỏ (Exit code != 0), AI **phải tự động đọc log lỗi Terminal, phân tích nguyên nhân và sửa lại code ngay lập tức**, sau đó chạy lại lệnh test cho đến khi XANH 100%.

### Bước 5: Báo cáo & Đề xuất Commit
- Chỉ khi toàn bộ test đã PASS (Xanh 100%), AI mới được thông báo hoàn thành nhiệm vụ.
- Đề xuất câu lệnh Git Commit chuẩn định dạng **Conventional Commits** (ví dụ: `feat(order): add dynamic hmac qr signature verification and unit tests`).

---

## 2. 8 Ranh giới Bất khả Xâm phạm (Inviolable Guardrails)

1. ❌ **CẤM COMMIT SECRETS**: Tuyệt đối không đọc, ghi hoặc commit file `.env`, token, key bảo mật vào git staging. Mọi cấu hình nạp qua `pydantic-settings` tại `app/core/config.py`; template giá trị chỉ nằm trong `.env.example` (root và `backend/`). Pre-commit hook `forbid-env-files` sẽ chặn commit `.env` thật.
2. ❌ **CẤM HARDCODE TOẠ ĐỘ & QUYỀN**: Mọi logic vị trí địa lý phải thông qua hàm PostGIS `ST_DWithin` hoặc `ST_Distance` (thực thi trong `store_repo.py`, `Geometry(POINT, srid=4326)`) — không tính khoảng cách thủ công ngay trong Python. Mọi API nhạy cảm phải bọc dependency phân quyền `require_roles(...)` hoặc `require_store_owner` từ `app/api/deps.py` (bán kính Radar chuẩn hoá 1–10 km trong `DiscoveryService`).
3. ❌ **BẢO MẬT MÃ QR & THANH TOÁN VNPAY**: Mã QR xác nhận đơn hàng phải dùng thuật toán HMAC-SHA256 (secret: `QR_SIGNATURE_SECRET`), có thời hạn hiệu lực (`expires_at`, TTL: `QR_TOKEN_VALIDITY_MINUTES`) và kiểm tra cờ `is_used` để chống Replay Attack (quét 2 lần). Webhook VNPay IPN bắt buộc xác thực chữ ký HMAC-SHA512 (secret: `VNP_HASH_SECRET`) và xử lý idempotent chống ghi nhận giao dịch trùng lặp.
4. ❌ **CHỐNG OVER-SELLING (TRANH CHẤP TỒN KHO MÓN ĂN)**: Khi trừ số lượng món ăn `remaining_quantity` trong bảng `dishes`, bắt buộc dùng `dish_repo.atomic_decrement_quantity` (Atomic Update `UPDATE ... SET remaining_quantity = remaining_quantity - :qty WHERE id = :dish_id AND remaining_quantity >= :qty` trong một DB Transaction) hoặc Redis Distributed Lock (Redis 7 đã có trong docker-compose; khi code Redis phải cấu hình qua biến môi trường, không hardcode host/port).
5. ❌ **GIẢM GIÁ THEO KHUNG GIỜ LÀ RULE-BASED**: Tuyệt đối không dùng mô hình AI phỏng đoán giá gây bất định. Luôn tính giá theo luật thời gian xác định (Rule-based: giờ vàng giảm 40-50%, giờ chót giảm 70%).
6. ❌ **AI GENAI BẢO MẬT & CẤU TRÚC (MENU GROUNDING & 2-TIER ALLERGENS)**: Khi gọi Google Gemini 2.5 Flash, bắt buộc sử dụng Pydantic Schema Structured Output (`QuickPostExtractionResponse` tại `app/schemas/nlp.py`, đối chiếu 14 nhóm dị ứng EU FIC qua enum `EUAllergen`). Rà soát dị ứng phải chia rõ 2 nguồn: `EXPLICIT` (chủ quán đọc trực tiếp) và `INFERRED` (AI suy luận tri thức món Việt) qua enum `DetectionSource`. Bắt buộc đối chiếu Thực đơn gốc (`menu_items`) để kế thừa ảnh và giá gốc chuẩn xác.
7. ❌ **AN TOÀN DỊ ỨNG TRONG GỢI Ý MÓN ĂN (ALLERGEN HARD INVARIANT)**: Khi chạy engine gợi ý món (`RecommendationService` — *chưa triển khai, thi hành nghiêm ngặt ngay khi code*), bộ lọc loại trừ dị ứng (`excluded_allergens` trong `UserPreference` — `app/models/user.py`) bắt buộc thực thi ở tầng Database SQL (Hard Filter), không lọc bằng Python thay cho SQL. Gemini 2.5 Flash chỉ nhận dữ liệu đã lọc sạch dị ứng để sinh lời bình (`ai_justification`), tuyệt đối không phó thác an toàn sức khỏe cho AI phỏng đoán.
8. ❌ **DECOUPLED ML**: Không cài đặt thư viện đào tạo nặng (`ultralytics`, `jupyterlab`, `matplotlib`) vào `backend/requirements.txt` — toàn bộ nằm trong `ml/requirements.txt` (workspace huấn luyện độc lập). Backend chỉ phục vụ suy luận (`torch` runtime + `google-genai` SDK). Pre-commit chặn mọi file > 5MB để tránh commit trọng số `.pt`.

---

## 3. Quy chuẩn Đặt tên File & Cấu trúc Thư mục

### 3.1 Backend (`backend/`)

- **Application Layers (`Router -> Service -> Repository`)**:
  - `backend/app/api/v1/endpoints/<domain>.py` — Tầng HTTP Router & RBAC. Hiện tại: `auth.py`, `users.py`, `stores.py`, `menu.py`, `dishes.py`, `orders.py`; mọi router phải đăng ký tại `backend/app/api/v1/router.py`.
  - `backend/app/services/<domain>_service.py` — Tầng Business Logic, viết theo dạng class `XxxService(db: AsyncSession)` (mẫu chuẩn: `DiscoveryService`, `DishService`). ⚠️ Ba mô-đun cũ đang dùng tên ngắn `user.py`, `auth.py`, `discovery.py` (function-style) — giữ nguyên đường dẫn import, **không đổi tên riêng lẻ**; dịch vụ mới bắt buộc theo chuẩn `<domain>_service.py`.
  - `backend/app/repositories/<domain>_repo.py` — Tầng Data Access / SQLAlchemy 2.0 `AsyncSession`. Bên trong dùng dạng hàm module (`user_repo.get_by_email`) hoặc 1 class duy nhất (`OrderRepository`) — mỗi file thống nhất một phong cách, không trộn.
  - `backend/app/models/<domain>.py` — Tầng ORM Models (`Mapped[T]`, UUID PK). Hiện tại: `user`, `store`, `menu_item`, `dish`, `order`, `interaction`, `gamification`.
  - `backend/app/schemas/<domain>.py` — Tầng Pydantic v2 DTOs. Hiện tại: `user`, `token`, `store`, `menu_item`, `dish`, `order`, `nlp`, `gamification`, `interaction`, `user_preference`.
- **Hạ tầng nội bộ backend**:
  - `backend/app/core/` — `config.py` (`pydantic-settings`), `security.py` (JWT/passlib), `logging.py`, `redis.py` (async Redis client lười + `distributed_lock`: `SET NX EX` + Lua compare-and-delete; Redis chết thì degrade an toàn, DB atomic update vẫn là backstop cuối).
  - `backend/app/db/` — `base.py` (Metadata), `session.py` (`get_db`), `seed.py` (seed dữ liệu demo).
  - `backend/alembic/` — các migration nằm trong `versions/` (migration đầu tiên dựng schema đầy đủ 12 bảng; migration kiểu PostGIS phải giữ tính portable trên SQLite như file mẫu).
- **Backend Tests**:
  - `backend/tests/unit/test_<service_or_repo_name>.py` (kèm `test_security.py`, `test_nlp_schemas.py`).
  - `backend/tests/integration/test_api_<endpoint>.py`.
  - `backend/tests/conftest.py` — fixtures chuẩn: SQLite in-memory (`db_engine`, `db_session`), override `get_db`, HTTP client (ASGI), giả lập JWT qua headers `Authorization` (`store_partner`, `other_store_partner`, `consumer`). ⚠️ Chưa có mock Redis dùng chung trong conftest: test lock dùng fake client nội bộ tại `tests/unit/test_redis_lock.py`; service test chạy ở chế độ degrade (không có Redis server → DB atomic update là backstop). Chỉ thêm fixture mới khi test thật sự cần.
- **Cấu hình công cụ** tập trung tại `backend/pyproject.toml` và `backend/requirements.txt`. Không thêm cấu hình pytest/ruff/mypy ở file khác.

### 3.2 Frontend (`frontend/`)

- `frontend/src/app/` — Next.js 14 App Router (⚠️ **chưa tạo** — trang đầu tiên phải được khởi tạo theo chuẩn App Router, không dùng Pages Router).
- `frontend/src/components/<Component>.tsx` — UI building blocks (Button, Card, Input, Modal, Toast, Navbar, Badge, BottomNavigation). Đặt `'use client'` ngay trên file khi component có state/hook/browser API.
- `frontend/src/services/<domain>.service.ts` — Service layer gọi REST API backend qua `@/lib/api-client`. ⚠️ `src/lib/api-client.ts` **chưa tồn tại** — phải tạo instance axios đọc thêm biến môi trường `NEXT_PUBLIC_API_BASE_URL` trước khi import.
- `frontend/src/types/api.ts` — DTO TypeScript dùng chung cho mọi service.
- `frontend/src/providers/QueryProvider.tsx` — TanStack React Query provider (bọc trong root layout).
- **Frontend Tests**:
  - `frontend/__tests__/components/<ComponentName>.test.tsx`
  - `frontend/__tests__/hooks/<hookName>.test.ts`
  - ⚠️ Hai thư mục này hiện chỉ là scaffold (rỗng), test runner **chưa cấu hình** (mục 1, Bước 2).
- Cấu hình: alias `@/*` → `src/*` trong `tsconfig.json`; ESLint `eslint-config-next` (`.eslintrc.json`); Tailwind config tại `tailwind.config.js`.

### 3.3 Máy học (`ml/`)

- `ml/` là workspace độc lập phục vụ huấn luyện: `notebooks/`, `datasets/` (gitignore), `weights/` (gitignore), `requirements.txt` riêng (PyTorch, Ultralytics, JupyterLab...). Backend chỉ nạp trọng số từ đây, không huấn luyện trong `backend/`.
- Quy tắc naming file trọng số `<task>_<backbone>_<version>_<metric>.pt` + tên alias production `food_quality_yolov8.pt` — chi tiết đọc tại `ml/README.md`.

### 3.4 Tài liệu (`docs/`)

| File | Nội dung nghiệp vụ |
| --- | --- |
| `00_Project_Proposal_Section_B.md` | Tổng quan đề xuất dự án (Proposal) |
| `01_PRD_and_User_Stories.md` | PRD & User Stories |
| `02_System_Architecture.md` | Kiến trúc hệ thống 3 tầng |
| `03_Database_Schema_ERD.md` | ERD & Schema CSDL |
| `04_API_Specification.md` | Spec API (`/api/v1`) |
| `05_Agile_Roadmap_and_Kanban.md` | Roadmap & Kanban Agile |
| `06_Environment_and_ML_Setup_Guide.md` | Hướng dẫn môi trường & ML setup |
| `07_AI_Development_Workflow_and_Quality_Gates.md` | Quy trình AI & 4 Quality Gates |

### 3.5 Git Commit Message Format (Conventional Commits)

- `feat(...)`: Tính năng mới
- `fix(...)`: Sửa lỗi
- `test(...)`: Bổ sung hoặc cập nhật test
- `refactor(...)`: Tái cấu trúc code nhưng không thay đổi hành vi
- `docs(...)`: Cập nhật tài liệu
- `chore(...)`: Công việc phụ trợ (cấu hình, CI, dependency) — không thay đổi hành vi nghiệp vụ

---

## 4. Ghi chú Trạng thái Repo (Snapshot — cập nhật 2026-11-14)

- **Backend**: đã có đầy đủ auth/users/stores (onboard, Radar `/stores/nearby`, admin duyệt quán)/menu/dishes/orders (`POST /orders`, `GET /orders/me`, `GET /orders/store/{store_id}`, `GET /orders/{order_id}`, `POST /orders/{order_id}/qr`, `POST /orders/verify-qr`, `PATCH /orders/{order_id}/cancel`) + `DiscoveryService`, `OrderService`, `QRService` (HMAC-SHA256 + anti-replay). Vẫn **chưa có**: VNPay webhook, `RecommendationService` — khi triển khai phải tuân thủ đúng Guardrails #3, #4, #7.
- **Frontend**: đã triển khai đầy đủ luồng SDD `001-rescue-discovery-order-qr` (`src/lib/api-client.ts`, `src/lib/utils.ts`, `src/app/` với `/`, `/login`, `/register`, `/orders`, `/store/verify-qr`, `/store/onboard`, `RadarMap.tsx` tích hợp Leaflet). **Chưa cấu hình** test runner frontend (mục 1, Bước 2).
- Bất kỳ thay đổi nào làm lệch cấu trúc/lệnh trong file này (đổi venv, đổi tên tầng, thêm công cụ validation) phải **cập nhật lại `AGENTS.md`** ngay trong cùng commit.

---

*Bản hữu hiệu nhất của quy trình này luôn nằm trên `main`. Phát hiện sai lệch giữa `AGENTS.md` và thực tế codebase → cập nhật ngay, không để tồn tại hai chuẩn.*
