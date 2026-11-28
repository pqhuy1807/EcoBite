# Quickstart Validation Guide: VNPay Cashless Checkout, Idempotent IPN & Payment-QR Guard

**Feature**: `004-vnpay-payment-qr-guard` | **Contracts**: [contracts/api-contracts.md](./contracts/api-contracts.md) | **Data Model**: [data-model.md](./data-model.md)

Use this guide to validate the VNPay checkout flow, idempotent IPN webhook, Payment↔QR Reconciliation Guard, frontend pages, and live VNPay Sandbox integration end-to-end.

---

## 1. Environment Configuration (Never Commit `.env`)

Copy `backend/.env.example` to `backend/.env` and set the VNPay Sandbox credentials obtained from the VNPay Sandbox Merchant Portal:

```ini
VNP_TMN_CODE="<your_sandbox_tmn_code>"
VNP_HASH_SECRET="<your_sandbox_hash_secret>"
VNP_URL="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNP_RETURN_URL="http://localhost:3000/orders/vnpay-return"
REDIS_URL="redis://localhost:6379/0"
```

Verify configuration loads cleanly without printing secrets:

```bash
cd backend
./venv_backend/bin/python -c "from app.core.config import settings; print('VNP_URL:', settings.VNP_URL, '| TMN ready:', bool(settings.VNP_TMN_CODE), '| Secret ready:', bool(settings.VNP_HASH_SECRET))"
```

---

## 2. Backend Unit, Integration & Concurrency Tests (No External Network)

1. Run existing unit tests for PaymentService & OrderService (Payment↔QR Guard + COD auto-paid + Green Points/CO₂):
   ```bash
   cd backend
   ./venv_backend/bin/pytest tests/unit/test_payment_service.py tests/unit/test_order_service.py -v
   ```
2. Run the payment API integration, concurrent IPN idempotency, single atomic stock restoration, and `< 2s` QR verification latency benchmark suite (once `EC4-15` lands):
   ```bash
   cd backend
   ./venv_backend/bin/pytest tests/integration/test_api_payments.py -v
   ```

Expected outcomes:
- Invalid IPN signature → `{"RspCode": "97", ...}`, zero DB mutations.
- Mismatched amount → `{"RspCode": "04", ...}`, zero DB mutations.
- Concurrent duplicate success IPNs → exactly 1 verified `PaymentTransaction`, `Order.payment_status == PAID`, duplicate returns `RspCode: "02"`.
- Concurrent duplicate failed IPNs → `Order.status == CANCELLED`, `Order.payment_status == FAILED`, `Dish.remaining_quantity` incremented **exactly once**.
- Unpaid `VNPAY` order → `POST /orders/{id}/qr` & `POST /orders/verify-qr` both return `409 Conflict`.
- Paid `VNPAY` order → QR issuance & verification succeed (`COMPLETED`); `POST /orders/verify-qr` finishes in `< 2000 ms`.
- `COD` order → QR verification atomically sets `status = COMPLETED`, `payment_status = PAID`, credits Consumer Green Points + `GreenPointsLedger`, and increments `Store.total_co2_saved_kg`.

---

## 3. Local Simulated End-to-End Flow (Backend + Frontend)

1. Start PostgreSQL + Redis (optional; SQLite fallback also works locally) and Backend API:
   ```bash
   docker compose up -d
   cd backend
   ./venv_backend/bin/python -m app.db.seed
   ./venv_backend/bin/uvicorn app.main:app --reload --port 8000
   ```
2. Start Frontend dev server:
   ```bash
   cd frontend
   npm run dev
   ```
3. **Consumer Cashless Checkout & QR Guard Walkthrough**:
   - Sign in as demo Consumer on `http://localhost:3000/login`.
   - On Radar (`/`), open a surplus dish checkout modal, select **`VNPAY`**, and confirm → verify `POST /api/v1/orders` creates a `PENDING` order and redirects to `sandbox.vnpayment.vn`.
   - Open `http://localhost:3000/orders` **before** IPN settlement → verify *"Xem mã QR"* is locked/hidden, badge shows *"Chờ thanh toán VNPay"*, and *"Thanh toán VNPay ngay"* is clickable.
   - Trigger a validly signed `GET /api/v1/payments/vnpay/ipn?...&vnp_ResponseCode=00` (from VNPay Sandbox or a local signed curl helper) → refresh `/orders` → verify badge updates to `PAID` and *"Xem mã QR"* now opens the HMAC-SHA256 QR modal.
4. **Store Partner Order Queue & QR Verification Walkthrough**:
   - Sign in as the owning Store Partner (`http://localhost:3000/login`) and open `http://localhost:3000/store/verify-qr`.
   - Confirm the Store Orders table displays the incoming `CONFIRMED` order with `VNPAY • PAID` (or `COD • PENDING`).
   - Scan or paste the Consumer's QR payload → confirm `COMPLETED` success banner (+Green Points & CO₂ saved) and confirm the Store Orders table refreshes automatically.
   - Re-submit the exact same QR payload → confirm Anti-Replay rejection (`400`).

---

## 4. Live VNPay Sandbox E2E Verification (`EC4-16`)

1. Expose local port `8000` over HTTPS (e.g., `ngrok http 8000`) and configure the resulting public IPN URL `https://<ngrok-host>/api/v1/payments/vnpay/ipn` in the VNPay Sandbox Merchant Portal.
2. **Success Case (`vnp_ResponseCode=00`)**:
   - Place a `VNPAY` rescue order in the UI → redirected to `sandbox.vnpayment.vn` with zero `Error 70 (Invalid Signature)` or timestamp drift errors.
   - Complete checkout using VNPay Sandbox NCB test card credentials.
   - Confirm redirect back to `http://localhost:3000/orders/vnpay-return` displays verified signature + success summary, AND confirm backend IPN logs show `RspCode: "00"` and `Order.payment_status = PAID`.
3. **Cancellation / Failure Case (`vnp_ResponseCode=24`)**:
   - Place a second `VNPAY` order (recording initial `Dish.remaining_quantity`).
   - Cancel payment on the VNPay Sandbox screen.
   - Confirm `/orders/vnpay-return` shows cancellation/stock-restore feedback, IPN logs confirm `Order.status = CANCELLED` & `Order.payment_status = FAILED`, and `Dish.remaining_quantity` returned to its exact pre-order value.
4. Capture redacted screenshots/logs (masking `VNP_HASH_SECRET` and `VNP_TMN_CODE`) for `docs/PA4.md`.

---

## 5. Mandatory Verification Gates (Before Commit / Release Tag)

### Backend (`backend/`)
```bash
cd backend
./venv_backend/bin/ruff check app/ tests/
./venv_backend/bin/ruff format --check app/ tests/
./venv_backend/bin/mypy app/
./venv_backend/bin/pytest tests/ -v
```

### Frontend (`frontend/`)
```bash
cd frontend
npm run lint
npm run type-check
npm run test
npm run build
```

### Repository Pre-Commit Hooks (repo root)
```bash
pre-commit run --all-files
```

All commands MUST exit `0`.
