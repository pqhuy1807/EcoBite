# ✅ Tổng kết PA3 (Sprint 3): PostGIS Radar, Anti-Overselling & Dynamic QR Preview

- **Thời gian**: `01/11/2026 – 14/11/2026`
- **Chủ trì chính**: Võ Ngọc Thịnh (`FE Lead`) & Đặng Trọng Phúc (`BE Lead`), phối hợp Đàng Thế Tony (`BE/QA`) & Phùng Quốc Huy (`PM`)
- **Trạng thái**: `DONE` (Đã nghiệm thu trên nhánh `dev`, Release `0.2`)

## Sản phẩm Đã Bàn giao
- **Spec Kit SDD `001-rescue-discovery-order-qr`**: Hoàn tất toàn bộ `spec.md`, `plan.md`, `data-model.md`, `contracts/api-contracts.md`, `tasks.md` (`T001`–`T024`).
- **Feature 4 (PostGIS Radar Discovery)**: `GET /api/v1/stores/nearby` (`ST_DWithin` / `ST_Distance` trong bán kính 1–10 km) + giao diện Leaflet Map (`RadarMap.tsx`, `page.tsx`).
- **Feature 5 (Anti-Overselling Order & Cancel)**: `OrderService` + `OrderRepository` + `dish_repo.atomic_decrement_quantity` + `distributed_lock` Redis; bài test tranh chấp 50 concurrent requests (`test_order_concurrency.py`).
- **Feature 7 Preview (Dynamic HMAC-SHA256 QR & Web Scanner)**: `QRService` (`POST /orders/{id}/qr`, `POST /orders/verify-qr`), `QRCodeSVG` trên `/orders`, máy quét camera `html5-qrcode` trên `/store/verify-qr`.
- **Tài liệu & Video Demo**:
  - Kế hoạch triển khai: [`docs/WEEK_4_ACTION_PLAN.md`](../../WEEK_4_ACTION_PLAN.md)
  - Báo cáo Functional Group Demo: [`docs/PA3_Section_E_Functional_Group_Demo.md`](../../PA3_Section_E_Functional_Group_Demo.md)
  - Video Demo PA3: <https://youtu.be/PsYfFS2f_fY>

## Tồn đọng Chuyển sang PA4 (Đã đưa vào [`pa4_sprint4/`](../pa4_sprint4/README.md))
- Hoàn thiện môi trường `backend` virtualenv (`redis`), thêm `GET /stores/me`, sửa path `dish.service.ts`, dựng UI Admin KYC & Store Menu/Dishes, tích hợp VNPay (F6) & khóa QR chưa thanh toán, hoàn thiện Feature 8 (Reviews/Green Points/Vouchers) và cấu hình Vitest cho Frontend.
