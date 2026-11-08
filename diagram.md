```mermaid
graph TD
    %% Tầng Client
    subgraph Tang_Client ["Tầng Ứng Dụng Client (Next.js 14 PWA)"]
        ConsumerUI["Ứng Dụng Web Người Tiêu Dùng<br/>(Tìm Radar, Thanh Toán, Hiển Thị QR)"]
        MerchantUI["Ứng Dụng Web Cửa Hàng / Đối Tác<br/>(Đăng Bằng Giọng Nói, Quét Mã QR)"]
        AdminUI["Bảng Quản Trị Hệ Thống<br/>(Duyệt Hồ Sơ ATVSTP, Kiểm Soát Nền Tảng)"]
    end

    %% Tầng Core Backend
    subgraph Core_Backend ["Hệ Thống Cốt Lõi EcoBite"]
        API["Máy Chủ FastAPI Backend<br/>(Python 3.11 Async REST APIs)"]
        Postgres["PostgreSQL 16 + PostGIS<br/>(CSDL Quan Hệ & Truy Vấn Không Gian)"]
        Redis["Redis 7<br/>(Bộ Đệm & Khóa Phân Tán Atomic)"]
    end

    %% Tầng Dịch Vụ Bên Ngoài
    subgraph DichVu_BenNgoai ["Giao Diện Dịch Vụ Bên Ngoài"]
        Gemini["Google Gemini 2.5 Flash API<br/>(Xử Lý Âm Thanh, NLP & Cảnh Báo Dị Ứng)"]
        VNPay["Cổng Thanh Toán VNPay<br/>(HMAC-SHA512 IPN Webhooks)"]
        MapService["Dịch Vụ Bản Đồ Tile<br/>(OpenStreetMap / Leaflet)"]
    end

    %% Mối quan hệ Client -> Backend
    ConsumerUI -->|HTTPS / API RESTful| API
    MerchantUI -->|HTTPS / Luồng Âm Thanh / Chữ Ký QR| API
    AdminUI -->|HTTPS / API RESTful| API

    %% Mối quan hệ Nội bộ Backend
    API -->|Truy Vấn SQL & Tìm Kiếm Không Gian| Postgres
    API -->|Khóa Phân Tán & Bộ Đệm Phiên| Redis

    %% Mối quan hệ Backend -> Dịch vụ Bên ngoài
    API -->|Luồng Dữ Liệu Google GenAI SDK| Gemini
    API -->|Khởi Tạo Thanh Toán & Webhook IPN| VNPay
    ConsumerUI -->|Dữ Liệu Hiển Thị Bản Đồ| MapService
```

```mermaid
graph TD
    %% Giai đoạn 1: Khám phá
    A["Truy cập Web PWA EcoBite<br/>(Cấp quyền vị trí GPS)"] --> B["Trang Chủ: Bản đồ Radar PostGIS (1-5km)<br/>& Danh sách AI Gợi ý Cá nhân hóa"]
    
    B --> C{"Hình thức tìm kiếm?"}
    C -- "Tìm tự nhiên (Natural Language)" --> D["Gõ câu hỏi: 'Món nóng dưới 30k gần đây'<br/>(Gemini bóc tách tham số & Lọc PostGIS)"]
    C -- "Lướt xem trực tiếp" --> E["Xem Danh sách Thẻ Món Ăn Giảm Giá<br/>(Kèm lý do gợi ý từ AI)"]
    D --> E

    %% Giai đoạn 2: Chi tiết & Chọn món
    E --> F["Trang Chi Tiết Món Ăn<br/>- Kiểm tra Cảnh báo Dị ứng (Allergen Guard)<br/>- Đếm ngược Khung giờ giảm giá (Time-Shift)"]
    F --> G["Bấm 'Đặt Hàng'<br/>(Hệ thống tự khóa kho chống trùng Redis)"]

    %% Giai đoạn 3: Thanh toán
    G --> H["Thanh Toán Qua Cổng VNPAY-QR / Ví Điện Tử"]
    H --> I{"Thanh toán thành công?"}
    I -- "Thất bại / Hủy" --> F
    I -- "Thành công" --> J["Trang Chi Tiết Đơn Hàng<br/>(Sinh mã QR Động HMAC-SHA256)"]

    %% Giai đoạn 4 & 5: Nhận hàng & Tương tác AI
    J --> K["Đến Cửa Hàng: Đưa Mã QR Cho Bếp Quét Khóa Mã"]
    K --> L["Hoàn Tất Đơn Hàng<br/>(Tích Điểm Xanh & Cộng Chỉ Số Giảm CO2e)"]
    
    J --> M["Tương Tác Với Trợ Lý AI Bảo Quản & Hâm Nóng<br/>- Đọc Thẻ Mẹo AI sinh tự động<br/>- Bấm Nút Hỏi Nhanh (Quick Chips)<br/>- Hoặc Gõ Nhắn Tin Hỏi Trực Tiếp AI"]