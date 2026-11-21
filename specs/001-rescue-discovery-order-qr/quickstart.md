# Quickstart Validation & Demo Guide

## 1. Automated Verification Commands

### Backend (Python 3.11)
```bash
cd backend
# Kích hoạt venv chuẩn `.venv` (Windows PowerShell: .\.venv\Scripts\Activate.ps1; Linux/macOS: source .venv/bin/activate)
ruff check app/
ruff format --check app/
mypy app/
pytest tests/ -v
```

### Frontend (Next.js 14 + TypeScript)
```bash
cd frontend
npm run lint
npm run type-check
npm run build
```

## 2. Local Live Demo Setup (SQLite Fallback or Docker PostGIS + Redis)

1. **Initialize & Seed Database** (works with SQLite out of the box if Docker is stopped, or PostgreSQL/PostGIS if `docker compose up -d` is running):
   ```bash
   cd backend
   python -m app.db.seed --reset
   ```
2. **Start Backend API** (port `8000`):
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
3. **Start Frontend App** (port `3000`):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   > `NEXT_PUBLIC_API_BASE_URL` mặc định là `http://localhost:8000/api/v1` (xem `frontend/src/lib/api-client.ts`); đặt biến này nếu backend chạy ở cổng/đường dẫn khác.

## 3. End-to-End Demo Flow
1. Open `http://localhost:3000/login` and click the **Demo Consumer** quick-fill (`consumer.an@ecobite.vn` / `Password123!`) -> Sign in.
2. On `/` (Discovery Radar), inspect the interactive Leaflet map centered on District 1, adjust radius (`1–10 km`) and category filter, and view active dishes with rule-based discounts.
3. Click **Giải cứu ngay** on a dish (e.g., remaining `6`), select quantity `2`, submit -> verify stock immediately drops to `4` and CO2/Green Points summary appears.
4. Attempt to order quantity `10` (exceeding stock `4`) -> verify `409 Conflict` anti-overselling error message appears and stock remains `4`.
5. Navigate to `/orders`, click **Xem mã QR** on the newly created order -> verify dynamic `QRCodeSVG` and `ecobite://pickup?...` payload render. Copy the payload.
6. Test **Hủy đơn** on a second test order -> verify status changes to `CANCELLED` and dish stock is restored.
7. Sign in as Store Partner (`merchant.bui@ecobite.vn` / `Password123!`), open `/store/verify-qr`, paste the copied QR payload -> verify `200` Order `COMPLETED` + points awarded, then submit the exact same QR payload again -> verify `400` Anti-Replay rejection.
