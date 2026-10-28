# EcoBite Platform - AI Development Workflow & Quality Gates

**Dự án**: EcoBite - Nền tảng Giải cứu Thực phẩm Thông minh & Kết nối Xanh (Food Rescue Platform)
**Nhóm thực hiện**: Group 5 - Lớp Kỹ nghệ Phần mềm / Computer Science (HCMUS)
- **Phùng Quốc Huy** (24127402) — *AI and Data Lead / Full-Stack Engineer*
- **Đặng Trọng Phúc** (24127495) — *Backend Lead & AI Engineer / Full-Stack Engineer*
- **Đàng Thế Tony** (24127561) — *QA/Tester Lead & Backend Engineer / Full-Stack Engineer*
- **Võ Ngọc Thịnh** (24127246) — *Frontend Lead / Full-Stack Engineer*

**Phiên bản**: 2.2.0 (Chuẩn hoá Quy trình TDD & Quality Gates)
**Mục tiêu**: Hướng dẫn quy trình phát triển tính năng chuẩn Big Tech khi kết hợp cùng AI Coding Assistants (Antigravity, Cursor, Copilot).

---

## 1. Triết lý Vận hành: "AI Code, Toolchain Kiểm duyệt"

Trong dự án EcoBite, chúng ta không tin tưởng code một cách mù quáng. Bất kỳ đoạn mã nguồn nào do AI hoặc con người viết ra đều phải đi qua **4 Cửa kiểm soát chất lượng (Quality Gates)** trước khi được phép gộp vào nhánh chính (`main`):

```
+--------------------------------------------------------------------------+
| Gate 1: AI Self-Verification Loop (Trên máy dev / Terminal)              |
|         - AI tự viết Unit Test song song                                 |
|         - Tự chạy ruff, mypy, pytest, tsc                                |
|         - Tự sửa lỗi nếu có test đỏ                                      |
+--------------------------------------------------------------------------+
                                     │
                                     ▼
+--------------------------------------------------------------------------+
| Gate 2: Git Pre-commit Hook (.pre-commit-config.yaml)                    |
|         - Chặn file .env hoặc secrets                                    |
|         - Chặn file nặng > 5MB (trọng số ml/weights/*.pt)                |
|         - Auto format code trước khi ghi nhận commit                     |
+--------------------------------------------------------------------------+
                                     │
                                     ▼
+--------------------------------------------------------------------------+
| Gate 3: Pull Request Review (Human-in-the-loop)                          |
|         - Tech Lead / Peer xem xét tính logic và kiến trúc               |
|         - Kiểm tra thỏa mãn Definition of Done (DoD)                     |
+--------------------------------------------------------------------------+
                                     │
                                     ▼
+--------------------------------------------------------------------------+
| Gate 4: CI/CD Pipeline (GitHub Actions - Clean Hermetic Environment)     |
|         - Khởi tạo container PostGIS & Redis thật                        |
|         - Chạy toàn bộ test suites và kiểm tra coverage >= 80%           |
+--------------------------------------------------------------------------+
```

---

## 2. Chuẩn bị Thư mục Tests cho Dự án

Để sẵn sàng cho quy trình TDD, dự án sử dụng cấu trúc thư mục kiểm thử tiêu chuẩn sau:

```text
backend/
└── tests/
    ├── conftest.py                   # Setup database test, Redis mock & JWT test fixtures
    ├── unit/                         # Unit tests logic độc lập (tính giá, ký QR, điểm xanh)
    │   └── .gitkeep
    └── integration/                  # Integration tests gọi API và kết nối CSDL PostGIS thật
        └── .gitkeep

frontend/
└── __tests__/
    ├── components/                   # Test hiển thị UI & tương tác nút bấm
    │   └── .gitkeep
    └── hooks/                        # Test logic state, React Query hooks
        └── .gitkeep
```

---

## 3. Hướng dẫn Cài đặt & Kích hoạt Git Pre-commit Hook

Để kích hoạt chốt chặn tự động trên máy tính của bạn:

### Bước 1: Cài đặt công cụ `pre-commit`
```bash
# Có thể cài đặt qua brew hoặc pip
pip install pre-commit
# Hoặc trên macOS:
# brew install pre-commit
```

### Bước 2: Kích hoạt hook vào thư mục Git của dự án
Tại thư mục gốc `Desktop/EcoBite-Platform/`:
```bash
pre-commit install
```
*Kết quả thông báo:* `pre-commit installed at .git/hooks/pre-commit`

### Bước 3: Chạy thử kiểm tra toàn bộ file hiện tại
```bash
pre-commit run --all-files
```
*Từ thời điểm này, mỗi khi bạn hoặc AI gõ lệnh `git commit`, hệ thống sẽ tự động quét qua tất cả các file đã stage. Nếu phát hiện file `.env` hoặc file mô hình `.pt` nặng > 5MB bị lọt vào, lệnh commit sẽ bị huỷ ngay lập tức!*

---

## 4. Bảng Tra cứu Lệnh Kiểm thử Thường dùng

| Mục đích kiểm tra | Lệnh thực thi (Terminal) | Kết quả mong đợi |
| :--- | :--- | :--- |
| **Lint & Format Backend** | `cd backend && ruff check app/ && ruff format --check app/` | `All checks passed!` |
| **Type-Check Backend** | `cd backend && mypy app/` | `Success: no issues found` |
| **Chạy Test Backend** | `cd backend && pytest tests/ -v` | `PASSED` (Màu xanh lá 100%) |
| **Type-Check Frontend** | `cd frontend && npm run type-check` | Không có thông báo lỗi |
| **Lint Frontend** | `cd frontend && npm run lint` | Không có cảnh báo/lỗi |
| **Kiểm tra Pre-commit** | `pre-commit run --all-files` | `Passed` trên tất cả các hooks |

---

## 5. Mẫu Prompt Chuẩn dành cho Bạn khi Giao việc cho AI

Khi bạn bắt đầu Sprint 1 và muốn AI code một tính năng mới, hãy sử dụng mẫu prompt sau để AI tự động kích hoạt toàn bộ quy trình chuyên nghiệp:

> **Mẫu Prompt Khuyến nghị:**
> *"Hãy đọc file `AGENTS.md` và triển khai tính năng [TÊN_TÍNH_NĂNG]. Hãy viết test case trước trong `backend/tests/`, sau đó viết code nghiệp vụ, tự chạy kiểm thử bằng Terminal và chỉ thông báo hoàn thành khi toàn bộ test đã Pass."*
