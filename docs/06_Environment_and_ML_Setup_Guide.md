# EcoBite Platform - Environment & ML Subsystem Setup Guide

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh  
**Tác giả**: Senior DevOps Engineer & Technical Project Manager  
**Mục tiêu**: Hướng dẫn chi tiết thiết lập môi trường phát triển toàn diện (PostGIS, Redis, Backend, ML, Frontend) từ đầu.

---

## 1. Tổng quan Hạ tầng Cần Thiết (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính đã cài đặt các công cụ sau:
- **Docker & Docker Compose**: Docker Engine >= 24.0, Docker Compose >= 2.20
- **Python**: Phiên bản 3.10 hoặc 3.11 (Khuyến nghị dùng `pyenv` hoặc `brew install python@3.11`)
- **Node.js**: Phiên bản >= 18.17.0 (LTS) kèm `npm` >= 9.0.0
- **Git**: Quản lý phiên bản mã nguồn

---

## 2. Phần 1: Khởi chạy Cơ sở Dữ liệu & Cache bằng Docker Compose

EcoBite sử dụng **PostgreSQL 16 kết hợp PostGIS** để xử lý các phép toán tìm kiếm vị trí địa lý, và **Redis 7** để quản lý hàng đợi, khóa phân tán (Distributed Locks) và cache.

### Bước 1: Sao chép biến môi trường
Tại thư mục gốc `EcoBite-Platform/`:
```bash
cp .env.example .env
```

### Bước 2: Khởi động các container
```bash
docker compose up -d
```

### Bước 3: Kiểm tra trạng thái hoạt động (Healthcheck)
```bash
docker compose ps
```
*Kết quả mong đợi:*
```text
NAME                IMAGE                             STATUS                    PORTS
ecobite_postgres    postgis/postgis:16-3.4-alpine     Up (healthy) 5s           0.0.0.0:5432->5432/tcp
ecobite_redis       redis:7-alpine                    Up (healthy) 5s           0.0.0.0:6379->6379/tcp
```

### Bước 4: Kiểm tra kết nối PostGIS
```bash
docker exec -it ecobite_postgres psql -U postgres -d ecobite_db -c "SELECT PostGIS_Version();"
```
*Bạn sẽ thấy phiên bản PostGIS (ví dụ: `3.4 USE_GEOS=1 USE_PROJ=1...`) được hiển thị thành công.*

---

## 3. Phần 2: Thiết lập Môi trường Ảo `venv` Độc lập

Để tránh xung đột giữa các thư viện phục vụ đào tạo mô hình (Training Toolchain) và các thư viện phục vụ chạy ứng dụng Web (FastAPI runtime), chúng ta **bắt buộc tạo 2 môi trường ảo riêng biệt**.

```text
EcoBite-Platform/
├── backend/
│   ├── venv_backend/        # Môi trường ảo Python dành riêng cho FastAPI
│   └── requirements.txt
└── ml/
    ├── venv_ml/             # Môi trường ảo Python dành riêng cho AI Training
    └── requirements.txt
```

---

### 3.1. Thiết lập Môi trường cho `backend/` (FastAPI + Async SQLAlchemy)

Môi trường này chỉ chứa các thư viện cần thiết để chạy API và nạp mô hình ở chế độ suy luận (Inference-only):

```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Tạo môi trường ảo venv_backend
python3 -m venv venv_backend

# 3. Kích hoạt môi trường ảo
# Trên macOS / Linux:
source venv_backend/bin/activate
# Trên Windows PowerShell:
# .\venv_backend\Scripts\Activate.ps1

# 4. Nâng cấp pip và cài đặt dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Thoát môi trường ảo khi hoàn tất
deactivate
cd ..
```

---

### 3.2. Thiết lập Môi trường cho `ml/` (Data Science, PyTorch & Ultralytics Training)

Môi trường này chứa các thư viện đào tạo mô hình, phân tích dữ liệu và JupyterLab:

```bash
# 1. Di chuyển vào thư mục ml
cd ml

# 2. Tạo môi trường ảo venv_ml
python3 -m venv venv_ml

# 3. Kích hoạt môi trường ảo
# Trên macOS / Linux:
source venv_ml/bin/activate
# Trên Windows PowerShell:
# .\venv_ml\Scripts\Activate.ps1

# 4. Nâng cấp pip và cài đặt dependencies huấn luyện
pip install --upgrade pip
pip install -r requirements.txt

# 5. (Tùy chọn) Khởi chạy JupyterLab để làm việc với Notebooks
jupyter lab --notebook-dir=notebooks

# 6. Thoát môi trường ảo khi hoàn tất
deactivate
cd ..
```

---

## 4. Phần 3: Cơ chế Kết nối giữa `backend/` và `ml/weights/*.pt`

Một trong những sai lầm phổ biến nhất của các hệ thống AI phục vụ Web là gọi `torch.load()` trực tiếp bên trong từng request controller. Điều này gây suy sụp hiệu năng nghiêm trọng (Disk I/O nghẽn, rò rỉ bộ nhớ RAM/VRAM).

Hệ sinh thái EcoBite giải quyết vấn đề này bằng mô hình **FastAPI Lifespan Singleton Pattern**.

### 4.1. Cơ chế Đọc Đường dẫn từ Biến Môi trường (`.env`)
Trong file `.env`:
```env
# Đường dẫn tương đối từ backend/ trỏ sang ml/weights/
ML_WEIGHTS_DIR=../ml/weights
ML_MODEL_FILENAME=food_quality_yolov8.pt
ML_DEVICE=cpu                   # 'cpu', 'cuda' (NVIDIA GPU), hoặc 'mps' (Apple Silicon)
ML_CONFIDENCE_THRESHOLD=0.5
ML_FALLBACK_TO_MOCK=True        # Cho phép chạy ở chế độ giả lập nếu chưa có weights thực tế
```

Tại `backend/app/core/config.py`, module cấu hình sẽ tự động giải quyết đường dẫn tuyệt đối (Absolute Path):
```python
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ML_WEIGHTS_DIR: str = "../ml/weights"
    ML_MODEL_FILENAME: str = "food_quality_yolov8.pt"
    ML_DEVICE: str = "cpu"
    ML_FALLBACK_TO_MOCK: bool = True

    @property
    def resolved_model_path(self) -> Path:
        base_dir = Path(__file__).resolve().parent.parent.parent  # Thư mục backend/
        return (base_dir / self.ML_WEIGHTS_DIR / self.ML_MODEL_FILENAME).resolve()

settings = Settings()
```

### 4.2. Nguyên tắc Nạp Model Duy nhất 1 Lần (Lifespan Singleton)
Mô hình `.pt` được nạp sẵn vào bộ nhớ trong sự kiện `startup` của FastAPI thông qua hàm `lifespan`:

```python
# Minh họa thiết kế Lifespan trong backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import torch
import logging

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==================== STARTUP EVENT ====================
    model_path = settings.resolved_model_path
    logger.info(f"Đang kiểm tra trọng số mô hình ML tại: {model_path}")

    device = torch.device(settings.ML_DEVICE)

    if model_path.exists():
        try:
            logger.info(f"Đang nạp mô hình AI vào {settings.ML_DEVICE.upper()}...")
            # Nạp model và lưu trữ trên app.state (Tồn tại xuyên suốt vòng đời ứng dụng)
            app.state.ml_model = torch.load(str(model_path), map_location=device)
            if hasattr(app.state.ml_model, "eval"):
                app.state.ml_model.eval()
            app.state.ml_ready = True
            logger.info("Nạp mô hình AI thành công! Sẵn sàng nhận diện chất lượng thức ăn.")
        except Exception as e:
            logger.error(f"Lỗi khi nạp mô hình: {e}")
            app.state.ml_model = None
            app.state.ml_ready = False
    else:
        logger.warning(f"Không tìm thấy file trọng số {model_path}.")
        if settings.ML_FALLBACK_TO_MOCK:
            logger.info("Kích hoạt chế độ AI Giả lập (Mock Fallback) cho môi trường phát triển.")
            app.state.ml_model = "MOCK_MODE"
            app.state.ml_ready = True
        else:
            app.state.ml_model = None
            app.state.ml_ready = False

    yield  # Ứng dụng xử lý các HTTP API request tại đây

    # ==================== SHUTDOWN EVENT ====================
    logger.info("Đang giải phóng tài nguyên mô hình AI khỏi bộ nhớ...")
    if hasattr(app.state, "ml_model"):
        del app.state.ml_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Dừng dịch vụ an toàn.")

app = FastAPI(lifespan=lifespan)
```

### 4.3. Gọi Inference trong Request Controller
Khi người dùng tải ảnh lên kiểm định chất lượng (`POST /api/v1/ml/inspect-quality`), controller lấy trực tiếp mô hình đã có sẵn trong `request.app.state.ml_model`:

```python
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
import torch
from PIL import Image
import io

router = APIRouter()

@router.post("/inspect-quality")
async def inspect_food_quality(request: Request, image: UploadFile = File(...)):
    if not request.app.state.ml_ready:
        raise HTTPException(status_code=503, detail="Hệ thống AI tạm thời chưa sẵn sàng")

    model = request.app.state.ml_model
    if model == "MOCK_MODE":
        # Giả lập phản hồi cho môi trường Dev khi chưa có file .pt thật
        return {
            "prediction": "fresh_packaged_food",
            "confidence": 0.95,
            "quality_pass": True,
            "note": "Kết quả suy luận từ Dev Mock Model"
        }

    # Đọc dữ liệu ảnh và xử lý nhanh
    image_bytes = await image.read()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    with torch.no_grad():  # Tắt tính toán gradient để tối ưu tốc độ và tiết kiệm RAM
        # Thực hiện inference
        prediction_result = model(img)

    return {"status": "success", "result": prediction_result}
```

---

## 5. Phần 4: Thiết lập Frontend (Next.js 14)

```bash
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt các gói npm
npm install

# 3. Khởi chạy máy chủ phát triển
npm run dev
```
*Truy cập trình duyệt tại:* `http://localhost:3000`

---

## 6. Lệnh Kiểm thử Toàn bộ Môi trường (System Health Check)

Để xác nhận hệ sinh thái đã sẵn sàng, thực hiện lần lượt:

```bash
# 1. Kiểm tra Docker services
docker compose ps

# 2. Kiểm tra Backend có thể kết nối DB và Redis
cd backend
source venv_backend/bin/activate
python -c "import asyncpg, redis, torch; print('Backend dependencies OK! PyTorch Version:', torch.__version__)"
deactivate
cd ..

# 3. Kiểm tra ML environment
cd ml
source venv_ml/bin/activate
python -c "import ultralytics, sklearn, pandas; print('ML dependencies OK! Ultralytics Version:', ultralytics.__version__)"
deactivate
cd ..
```
