# EcoBite Platform - Environment, AI & ML Subsystem Setup Guide

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh
**Tác giả**: Senior DevOps Engineer & Technical Project Manager
**Phiên bản**: 2.0.0 (Cập nhật: Google Gemini 2.5 Flash Free Tier + Giảm giá Rule-based + PostGIS)
**Mục tiêu**: Hướng dẫn chi tiết thiết lập môi trường phát triển toàn diện từ A-Z.

---

## 1. Tổng quan Hạ tầng Cần Thiết (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính đã cài đặt:
- **Docker & Docker Compose**: Docker Engine >= 24.0, Docker Compose >= 2.20
- **Python**: Phiên bản **3.11** (Khuyến nghị dùng Conda hoặc `pyenv`, tránh dùng Python 3.12+ hoặc 3.15 để tránh lỗi biên dịch thư viện C như `shapely`, `psycopg2`)
- **Node.js**: Phiên bản >= 18.17.0 (LTS) kèm `npm` >= 9.0.0
- **Google AI Studio Account**: Để lấy `GEMINI_API_KEY` miễn phí (tận dụng tài khoản Google AI Pro).

---

## 2. Phần 1: Khởi chạy Cơ sở Dữ liệu & Cache bằng Docker Compose

EcoBite sử dụng **PostgreSQL 16 kết hợp PostGIS** để xử lý các phép toán không gian địa lý, và **Redis 7** để quản lý hàng đợi, distributed locks và session.

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

---

## 3. Phần 2: Thiết lập Môi trường Python 3.11 cho `backend/` và `ml/`

Để tối ưu hiệu năng và tránh xung đột thư viện, ta chia làm 2 môi trường:

### 3.1. Thiết lập Môi trường cho `backend/` (FastAPI + Gemini GenAI SDK)
Môi trường này chứa các thư viện chạy Web API, Gemini SDK và PyTorch runtime:

```bash
cd backend

# Cách 1: Sử dụng Conda (Khuyên dùng)
conda create -n ecobite_backend python=3.11 pip -y
conda activate ecobite_backend

# Cách 2: Sử dụng venv chuẩn
# python3.11 -m venv venv_backend
# source venv_backend/bin/activate

# Cài đặt toàn bộ dependencies (đã bao gồm google-genai, fastapi, pre-commit...)
pip install -r requirements.txt
cd ..
```

### 3.2. Thiết lập Môi trường cho `ml/` (Huấn luyện & Thử nghiệm Notebooks)
```bash
cd ml

# Tạo môi trường Conda riêng cho ML
conda create -n ecobite_ml python=3.11 pip -y
conda activate ecobite_ml

pip install -r requirements.txt
# (Tùy chọn) Chạy JupyterLab để làm việc với Notebooks
# jupyter lab --notebook-dir=notebooks
cd ..
```

---

## 4. Phần 3: Thiết lập Động cơ AI NLP (Google Gemini 2.5 Flash Free Tier)

EcoBite sử dụng mô hình **`gemini-2.5-flash`** với gói miễn phí từ Google AI Studio thông qua Google GenAI SDK chính thức (`google-genai`).

### 4.1. Lấy API Key Miễn phí từ Google AI Studio
1. Truy cập [Google AI Studio](https://aistudio.google.com/) và đăng nhập bằng tài khoản Google (hỗ trợ tài khoản Google AI Pro).
2. Bấm vào **"Get API key"** $\rightarrow$ Tạo một API key mới.
3. Mở file `.env` tại thư mục gốc và điền key vào:
   ```env
   GEMINI_API_KEY=AIzaSyYourSecretKeyHere...
   GEMINI_MODEL=gemini-2.5-flash
   ```

### 4.2. Code Mẫu Trợ lý Bóc tách Hàng loạt Món ăn & Cảnh báo Dị ứng 2 Tầng (`backend/app/services/nlp_service.py`)

Động cơ NLP sử dụng mô hình **`gemini-2.5-flash`** với kỹ thuật Structured Outputs, giải quyết trọn vẹn 5 điểm nghẽn thực tế:
1. **Menu-Catalog Grounding**: So khớp thực đơn gốc để lấy ảnh và giá gốc.
2. **2-Tier Allergen Guard**: Tách biệt `EXPLICIT` (chủ quán đọc) và `INFERRED` (AI suy luận ẩm thực Việt).
3. **Batch Extraction**: Bóc tách nhiều món trong một lần nói (`List[SurplusDishItem]`).
4. **Relative Time Handling**: Nhận `current_server_time` để tính giờ tuyệt đối.
5. **Native Multimodal Audio**: Tiếp nhận file âm thanh trực tiếp không qua STT trung gian.

```python
import json
import os
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Định nghĩa 14 chất dị ứng theo chuẩn EU FIC (Việt hóa)
class EUAllergen(str, Enum):
    PEANUTS = "Peanuts (Đậu phộng)"
    SOYBEANS = "Soybeans (Đậu nành)"
    EGGS = "Eggs (Trứng)"
    MILK = "Milk/Dairy (Sữa)"
    FISH = "Fish (Cá/Nước mắm)"
    CRUSTACEANS = "Crustaceans (Tôm/Cua)"
    MOLLUSCS = "Molluscs (Nhuyễn thể: Nghêu/Sò/Ốc)"
    GLUTEN = "Cereals containing gluten (Bột mì/Bánh mì)"
    TREE_NUTS = "Tree nuts (Hạt cây: Điều, Hạnh nhân...)"
    SESAME = "Sesame (Mè/Vừng)"
    CELERY = "Celery (Cần tây)"
    MUSTARD = "Mustard (Mù tạt)"
    SULPHITES = "Sulphites (Chất bảo quản Sulfit)"
    LUPIN = "Lupin (Đậu Lupin)"

class DetectionSource(str, Enum):
    EXPLICIT = "EXPLICIT"  # Chủ quán trực tiếp nói ra (Độ chắc chắn 100%)
    INFERRED = "INFERRED"  # AI suy luận từ công thức món ăn Việt (Cần gắn nhãn 'Có thể chứa')

class AllergenWarning(BaseModel):
    allergen: EUAllergen
    risk_level: str = Field(description="HIGH hoặc MEDIUM")
    source: DetectionSource = Field(description="Nêu rõ do chủ quán khai báo hay AI suy luận từ món ăn")
    reason: str = Field(description="Giải thích ngắn gọn, VD: 'Có đậu phộng rang' hoặc 'Chả trứng và nước mắm thường chứa trứng, cá'")

class SurplusDishItem(BaseModel):
    matched_menu_id: Optional[str] = Field(
        None, description="ID món ăn khớp nhất trong thực đơn gốc của quán (nếu có)"
    )
    dish_name: str = Field(description="Tên món ăn đã chuẩn hóa")
    quantity: int = Field(description="Số lượng phần còn dư")
    original_price: Optional[int] = Field(
        None, description="Giá gốc (VNĐ). Để trống nếu chủ quán không nói để lấy từ Menu gốc"
    )
    override_discounted_price: Optional[int] = Field(
        None, description="Giá giảm cố định (VNĐ) nếu chủ quán chỉ định rõ. Nếu không, hệ thống tự chạy Rule-based Time-shift"
    )
    side_components: List[str] = Field(
        default_factory=list, description="Các món ăn kèm/topping như 'dưa chua', 'mỡ hành'"
    )
    allergens: List[AllergenWarning] = Field(
        default_factory=list, description="Danh sách cảnh báo dị ứng theo chuẩn 14 chất EU FIC"
    )
    dietary_notes: List[str] = Field(
        default_factory=list, description="Ghi chú khẩu vị địa phương: 'Có mỡ hành (Allium)', 'Cay', 'Chay'..."
    )
    missing_fields_warning: List[str] = Field(
        default_factory=list, description="Cảnh báo nếu thiếu thông tin bắt buộc (VD: thiếu số lượng)"
    )

class QuickPostExtractionResponse(BaseModel):
    pickup_start: str = Field(description="Giờ bắt đầu nhận món (HH:MM:SS), quy đổi từ current_time nếu nói giờ tương đối")
    pickup_end: str = Field(description="Giờ kết thúc nhận món (HH:MM:SS)")
    items: List[SurplusDishItem] = Field(description="Danh sách các món ăn dư thừa được trích xuất trong một lần nói")

# 2. System Instruction hướng dẫn Gemini 2.5 Flash
SYSTEM_PROMPT = """
Bạn là Trợ lý AI chuyên gia ẩm thực EcoBite (Nền tảng cứu trợ thực phẩm).
Nhiệm vụ của bạn là lắng nghe giọng nói hoặc đọc văn bản tiếng Việt của chủ quán để trích xuất danh sách các món ăn dư thừa cuối ca.

Quy tắc xử lý bắt buộc:
1. MENU GROUNDING:
   - Đối chiếu tên món chủ quán đọc với danh mục Menu gốc được cung cấp.
   - Nếu khớp với món trong menu, điền matched_menu_id tương ứng để hệ thống tự lấy ảnh và giá gốc.
2. XỬ LÝ THỜI GIAN TƯƠNG ĐỐI:
   - Sử dụng biến CURRENT_SERVER_TIME được truyền vào để tính toán giờ tuyệt đối (HH:MM:SS).
   - Ví dụ: Nếu current time là 13:50 mà chủ quán nói 'bán từ giờ đến 3h chiều' -> pickup_start='13:50:00', pickup_end='15:00:00'.
   - Nếu nói 'trong 1 tiếng nữa' -> pickup_end = current_time + 1 hour.
3. RÀ SOÁT DỊ ỨNG 2 TẦNG (2-TIER ALLERGEN GUARD):
   - EXPLICIT: Nếu chủ quán nhắc cụ thể thành phần (VD: 'có đậu phộng', 'sốt bơ trứng').
   - INFERRED: Dù chủ quán không nhắc, phải tự suy luận công thức món Việt:
     * Cơm sườn chả: Chả chưng có Trứng (Eggs), Nước mắm có Cá (Fish), Mỡ hành có thể có Đậu phộng (Peanuts).
     * Bún thịt nướng: Nước mắm (Fish), Đậu phộng rang (Peanuts).
     * Bánh mì: Gluten (bột mì), Bơ/Pate có thể chứa Sữa/Heo.
4. KHẨU VỊ ĐỊA PHƯƠNG (dietary_notes):
   - Ghi chú các yếu tố: 'Có mỡ hành (Allium)', 'Có đồ chua', 'Cay', 'Ăn chay'.
5. GIÁ CỐ ĐỊNH VS RULE-BASED:
   - Nếu chủ quán chỉ định giá bán xả cụ thể ('bán rẻ 20k', 'xả nhanh 15 cành') -> gán vào override_discounted_price.
   - Nếu không nói giá bán -> để override_discounted_price là null (hệ thống sẽ tự tính theo luật thời gian).
"""

class NLPService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    async def parse_surplus_batch(
        self,
        audio_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        raw_text: Optional[str] = None,
        base_menu: Optional[List[dict]] = None,
        current_time_iso: Optional[str] = None,
    ) -> QuickPostExtractionResponse:
        current_time_str = current_time_iso or datetime.now(timezone.utc).isoformat()
        menu_context = json.dumps(base_menu or [], ensure_ascii=False)

        system_instruction = f"{SYSTEM_PROMPT}\nCURRENT_SERVER_TIME: {current_time_str}\nMENU_CATALOG: {menu_context}"

        if not self.client:
            # Fallback mock mode cho môi trường dev khi chưa gắn API Key
            return QuickPostExtractionResponse(
                pickup_start="14:00:00",
                pickup_end="15:30:00",
                items=[
                    SurplusDishItem(
                        matched_menu_id=base_menu[0]["id"] if base_menu else None,
                        dish_name="Cơm sườn bì chả (Mock Dev)",
                        quantity=5,
                        original_price=45000,
                        override_discounted_price=None,
                        side_components=["mỡ hành", "dưa chua"],
                        allergens=[
                            AllergenWarning(
                                allergen=EUAllergen.EGGS,
                                risk_level="HIGH",
                                source=DetectionSource.INFERRED,
                                reason="Chả chưng chứa trứng"
                            )
                        ],
                        dietary_notes=["Có mỡ hành (Allium)"]
                    )
                ]
            )

        # Chuẩn bị nội dung đầu vào: Hỗ trợ Native Audio hoặc Raw Text
        contents = []
        if audio_bytes and mime_type:
            contents.append(
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            )
            contents.append("Hãy phân tích file âm thanh giọng nói trên để trích xuất danh sách món ăn dư thừa.")
        elif raw_text:
            contents.append(f"Hãy trích xuất danh sách món ăn dư thừa từ đoạn văn bản sau: '{raw_text}'")
        else:
            raise ValueError("Phải cung cấp audio_bytes hoặc raw_text")

        # Gọi Gemini 2.5 Flash với Pydantic Structured Outputs
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=QuickPostExtractionResponse,
                temperature=0.1,
            ),
        )

        data = json.loads(response.text)
        return QuickPostExtractionResponse(**data)
```

### 4.3. Code Mẫu Động cơ Gợi ý Món ăn Thông minh (`backend/app/services/recommendation_service.py`)

```python
from google import genai
from google.genai import types
import json
import os

RECOMMENDATION_JUSTIFICATION_PROMPT = """
Bạn là Trợ lý AI gợi ý ẩm thực EcoBite.
Nhiệm vụ: Dựa vào thông tin hồ sơ của người dùng (khẩu vị, ngân sách, tiền sử món thích) và thông tin món ăn cứu trợ đang có sẵn gần họ, hãy viết 1 câu giải thích tự nhiên, ngắn gọn và thuyết phục (khoảng 20-30 từ) tại sao món này rất hợp với họ tại thời điểm này.
Ví dụ: 'Món này gợi ý cho bạn vì bạn thích món bún vào bữa trưa, quán cách bạn 300m và đang có deal giảm 50% chỉ còn 25k!'
"""

class RecommendationService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    async def generate_justification(self, user_profile: dict, dish_info: dict) -> str:
        if not self.client:
            return f"Gợi ý phù hợp dựa trên vị trí gần bạn ({dish_info.get('distance_meters', 300)}m) và giá ưu đãi."

        prompt = f"""
        Hồ sơ người dùng: {json.dumps(user_profile, ensure_ascii=False)}
        Món ăn được chọn: {json.dumps(dish_info, ensure_ascii=False)}
        Hãy viết câu lý do ngắn giải thích tại sao món này phù hợp với họ:
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=RECOMMENDATION_JUSTIFICATION_PROMPT,
                temperature=0.3
            ),
        )
        return response.text.strip()
```

---

## 5. Phần 4: Logic Giảm Giá Theo Khung Giờ Rule-based (Deterministic Time Discount)

Thay vì dùng AI dự đoán giá, hệ thống EcoBite sử dụng hàm nghiệp vụ xác định minh bạch:

```python
from datetime import datetime, time

def calculate_current_price(
    original_price: float,
    rescue_price: float,
    rule_discount_price: float | None,
    pickup_start: time,
    pickup_end: time,
    rule_discount_start: time | None,
    check_time: time | None = None
) -> dict:
    """
    Tính giá bán hiện tại của món ăn dựa trên luật thời gian xác định (Rule-based).
    """
    now = check_time or datetime.now().time()

    # Nếu chưa tới giờ lấy hoặc đã quá giờ
    if now < pickup_start or now > pickup_end:
        return {
            "current_price": original_price,
            "discount_tier": "OUT_OF_WINDOW",
            "is_active": False
        }

    # Nếu đang trong khung giờ chót và có thiết lập luật giảm giá sâu
    if rule_discount_start and now >= rule_discount_start and rule_discount_price:
        return {
            "current_price": rule_discount_price,
            "discount_tier": "RULE_FLASH_DROP",
            "discount_percentage": round((1 - rule_discount_price / original_price) * 100),
            "is_active": True
        }

    # Khung giờ giải cứu tiêu chuẩn
    return {
        "current_price": rescue_price,
        "discount_tier": "STANDARD_RESCUE",
        "discount_percentage": round((1 - rescue_price / original_price) * 100),
        "is_active": True
    }
```

---

## 6. Phần 5: Thiết lập Frontend (Next.js 14)

```bash
cd frontend
npm install
npm run dev
```
*Truy cập trình duyệt tại:* `http://localhost:3000`

---

## 7. Kiểm thử Môi trường (System Health Check)

```bash
# 1. Kiểm tra Docker
docker compose ps

# 2. Kiểm tra Backend & Gemini SDK
cd backend
python -c "import asyncpg, redis, torch; from google import genai; print('Backend + Gemini SDK OK!')"
cd ..
```
