# EcoBite Backend Setup

This guide explains how to prepare the local Python environment for the EcoBite backend.

## Prerequisites

- Python 3.11 or another version supported by the project dependencies
- Git
- A terminal (Command Prompt, PowerShell, or Bash)

## 1. Navigate to the backend directory

```bash
cd backend
```

Run this command from the root directory of the EcoBite repository.

## 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows Command Prompt:

```bat
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure environment variables

Check the project documentation and `../.env.example` for the required environment variables.

Create a local `.env` file only if required by the application. Do not commit passwords, API keys, tokens, or other secrets.

## 5. Run tests

Check the project instructions for the supported test command. If the project uses pytest, run:

```bash
python -m pytest
```

## Notes

- Keep the virtual environment inside `.venv`.
- Do not commit the virtual environment or local secrets.
- Follow the root `README.md` and existing backend documentation for database migrations and application startup commands.

# Hướng Dẫn Setup Môi Trường Backend (FastAPI)

## 1. Khởi tạo & Kích hoạt Môi trường ảo (Virtual Environment)

Mở Terminal tại thư mục `backend/`:

```powershell
python -m venv venv
```

* **Nếu dùng PowerShell bị lỗi chặn script (`UnauthorizedAccess`):**  
  Chạy lệnh mở quyền trước:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
  Sau đó kích hoạt:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

* **Nếu dùng Command Prompt (CMD):**
  ```cmd
  .\venv\Scripts\activate.bat
  ```

*(Thành công khi xuất hiện chữ `(venv)` ở đầu dòng lệnh).*

---

## 2. Cài đặt Thư viện (Dependencies)

Nâng cấp `pip` và cài đặt các thư viện dự án:

```cmd
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

> **Mẹo sửa lỗi `psycopg2-binary`**: Nếu lệnh `pip install` báo lỗi build wheel, hãy mở file `requirements.txt`, đổi dòng `psycopg2-binary==2.9.9` thành `psycopg2-binary` (bỏ số phiên bản) rồi chạy lại lệnh trên.

---

## 3. Cấu hình VS Code (Sửa lỗi gạch chân vàng `MissingImports`)

Nếu file Python bị gạch chân màu vàng ở các câu lệnh `import`:

1. Nhấn **`Ctrl + Shift + P`**.
2. Tìm và chọn **`Python: Select Interpreter`**.
3. Chọn môi trường `.\venv\Scripts\python.exe` (hoặc tên có chữ `'venv': venv`).