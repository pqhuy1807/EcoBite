# EcoBite Platform - Machine Learning & AI Quality Assurance Subsystem

Thư mục `ml/` là một không gian làm việc độc lập (decoupled workspace) dành riêng cho các kỹ sư AI/ML để nghiên cứu, tiền xử lý dữ liệu, thử nghiệm notebook và huấn luyện mô hình (Model Training). Thư mục này hoàn toàn tách rời khỏi logic nghiệp vụ của `backend/`.

---

## 1. Cấu trúc thư mục

```text
ml/
├── README.md                 # Tài liệu quy chuẩn ML & giao tiếp với Backend
├── requirements.txt          # Thư viện phục vụ huấn luyện (PyTorch, Ultralytics, Jupyter, Pandas...)
├── notebooks/                # Jupyter Notebooks phục vụ EDA, thử nghiệm và training
│   └── .gitkeep
├── datasets/                 # Tập dữ liệu mẫu/huấn luyện (hình ảnh, annotations) - Đã bị .gitignore
│   └── .gitkeep
└── weights/                  # Thư mục chứa các trọng số model (.pt) để Backend nạp khi chạy
    └── .gitkeep
```

---

## 2. Quy ước đặt tên file mô hình (`.pt` Naming Convention)

Để đảm bảo tính nhất quán giữa khâu huấn luyện và khâu triển khai (Serving/Inference), tất cả các file trọng số xuất ra trong `ml/weights/` phải tuân theo cú pháp:

```text
<task>_<backbone>_<version>_<metric-score>.<ext>
```

### Các ví dụ chuẩn:
- `food_quality_yolov8n_v1.0.0_map78.pt`: Mô hình nhận diện chất lượng thức ăn, backbone YOLOv8 nano, version 1.0.0, mAP50 = 0.78.
- `freshness_classifier_resnet50_v2.1.pt`: Mô hình phân loại độ tươi của thực phẩm.
- **Production Alias (Tên cố định được Backend gọi)**:
  - `food_quality_yolov8.pt`
  *(Trong môi trường dev/staging, symlink hoặc đổi tên file release tốt nhất thành `food_quality_yolov8.pt` để khớp với biến `ML_MODEL_FILENAME` trong file `.env`).*

### Metadata đi kèm (.json):
Mỗi file `.pt` khi bàn giao lên staging/production nên đi kèm một file metadata cùng tên (ví dụ `food_quality_yolov8.json`):
```json
{
  "model_name": "food_quality_yolov8",
  "version": "1.0.0",
  "framework": "PyTorch / Ultralytics",
  "input_size": [640, 640],
  "classes": ["fresh_food", "packaged_meal", "bakery", "spoiled_expired"],
  "confidence_threshold": 0.5,
  "trained_date": "2026-10-14",
  "metrics": {
    "precision": 0.82,
    "recall": 0.79,
    "mAP50": 0.805
  }
}
```

---

## 3. Cách Backend nạp và gọi Model (Inference Protocol)

### 3.1. Đường dẫn liên kết qua Biến Môi trường (`.env`)
Backend FastAPI không lưu cứng (hardcode) đường dẫn tới file mô hình. Thay vào đó, đường dẫn được cấu hình linh hoạt trong `.env`:

```env
# Đường dẫn tương đối từ thư mục backend/ sang ml/weights/
ML_WEIGHTS_DIR=../ml/weights
ML_MODEL_FILENAME=food_quality_yolov8.pt
ML_DEVICE=cpu                   # 'cpu' | 'cuda' | 'mps' (Apple Silicon)
ML_CONFIDENCE_THRESHOLD=0.5
ML_FALLBACK_TO_MOCK=True        # Nếu chưa có file .pt, backend tự chuyển sang mock inference
```

### 3.2. Cơ chế Singleton & FastAPI Lifespan
- **Nguyên tắc nạp 1 lần (Single Load)**: File trọng số `.pt` có dung lượng từ hàng chục đến hàng trăm MB. **Tuyệt đối không load model trong từng request/endpoint**.
- **FastAPI Lifespan Context Manager**:
  1. Khi ứng dụng FastAPI khởi động (`startup`), service đọc file cấu hình, xác định thiết bị tính toán (`device`), và nạp model vào bộ nhớ RAM/VRAM một lần duy nhất.
  2. Instance mô hình được lưu vào `app.state.ml_model` hoặc thông qua một class Singleton `MLModelService`.
  3. Khi có request kiểm tra hình ảnh từ Store Partner (ví dụ lúc đăng món ăn cứu trợ), controller gọi method `predict()` của instance đã có sẵn trong memory.
  4. Khi ứng dụng tắt (`shutdown`), giải phóng bộ nhớ (CUDA cache / memory cleanup).

```text
+-------------------+        Startup        +----------------------+
|  FastAPI Lifespan | --------------------> | Read .env            |
|  (Backend Start)  |                       | Load ../ml/weights/*.pt
+-------------------+                       +----------------------+
          |                                            |
          | Stores in RAM                              v
          +---------------------------------> [ app.state.ml_model ]
                                                       |
+-------------------+     POST /api/v1/...             |
| Client Request    | ---------------------------------> Inference
| (Image Upload)    | <--------------------------------- (Fast Response)
+-------------------+        JSON Result
```

---

## 4. Hướng dẫn thiết lập Môi trường ML độc lập

Thư mục `ml/` sở hữu môi trường ảo Python hoàn toàn độc lập với `backend/` để tránh xung đột thư viện huấn luyện (training toolchains) với thư viện web runtime.

### Bước 1: Tạo môi trường ảo riêng cho ML
```bash
# Di chuyển vào thư mục ml
cd ml

# Khởi tạo virtual environment
python3 -m venv venv_ml

# Kích hoạt môi trường ảo
# Trên macOS / Linux:
source venv_ml/bin/activate
# Trên Windows:
# .\venv_ml\Scripts\activate
```

### Bước 2: Cài đặt thư viện huấn luyện
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 3: Khởi chạy JupyterLab để thử nghiệm
```bash
jupyter lab --notebook-dir=notebooks
```

### Bước 4: Xuất Model sang `weights/`
Sau khi hoàn tất training notebook, lưu checkpoint hoặc export file `.pt` trực tiếp vào thư mục `ml/weights/`:
```python
# Ví dụ xuất model sau huấn luyện:
model.save("../weights/food_quality_yolov8.pt")
```
Sau đó khởi động Backend để kiểm tra tính tương thích và độ trễ phản hồi (latency).

---

## 5. Tích hợp AI Ngôn ngữ Tự nhiên & Đa phương thức (Google Gemini 2.5 Flash GenAI Service)

Bên cạnh mô hình thị giác máy tính cục bộ trong `ml/weights/*.pt`:
- **Nhiệm vụ AI Suite**:
  1. **Trợ lý Đăng món Siêu tốc & Rà soát Dị ứng 2 Tầng (Batch Quick-Post NLP & Allergen Guard)**:
     - **Native Audio Multimodal**: Lắng nghe trực tiếp file ghi âm của chủ quán, không qua STT trung gian, nhận diện chính xác tiếng lóng và món ăn Việt.
     - **Menu-Catalog Grounding**: So khớp ngữ nghĩa với Thực đơn gốc (`menu_items`) để tự động kéo Ảnh món ăn chất lượng cao, Giá gốc và kích hoạt Luật giảm giá theo thời gian; hỗ trợ `override_discounted_price` khi quán đọc giá xả cố định.
     - **2-Tier Allergen Guard**: Kết hợp khai báo trực tiếp (`EXPLICIT`) và AI suy luận tri thức ẩm thực Việt (`INFERRED`: trứng trong chả, cá trong nước mắm, đậu phộng trong mỡ hành...) theo 14 chuẩn EU FIC, đồng thời phân tách nhãn khẩu vị địa phương `dietary_notes` (hành/ngò Allium, đồ cay, đồ chua, ăn chay).
     - **Batch Extraction Schema**: Trích xuất nhiều món cùng lúc trong một lần nói (`QuickPostExtractionResponse` với `List[SurplusDishItem]`).
     - **Relative Time Resolution**: Tự động quy đổi giờ tương đối ("từ giờ đến 3h chiều") thành giờ tuyệt đối ISO 8601 dựa trên `current_server_time`.
  2. **Hệ thống Gợi ý Món ăn Thông minh (AI Smart Recommendation Engine)**:
     - Kết hợp lọc cứng PostGIS (khoảng cách 1-3km, loại trừ chất dị ứng ở tầng SQL) và Gemini 2.5 Flash sinh lý do gợi ý cá nhân hóa (`ai_justification`, 20-30 từ).
- **Mô hình triển khai**: **`gemini-2.5-flash`** thông qua Google GenAI SDK (`google-genai`) với gói Free Tier từ Google AI Studio.
- **Vị trí Service**: Được tổ chức gọn nhẹ trong `backend/app/services/nlp_service.py` và `backend/app/services/recommendation_service.py`.
- **Ràng buộc Schema**: Bắt buộc tuân thủ schema Pydantic `QuickPostExtractionResponse` với tính năng Native Structured Output của Gemini 2.5 Flash.
