# EcoBite Platform - Product Requirement Document (PRD) & User Stories

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh (Food Rescue Platform)  
**Tác giả**: Senior DevOps Engineer & Technical Project Manager  
**Phiên bản**: 1.0.0  
**Trạng thái**: Approved for Implementation  

---

## 1. Tổng quan Dự án (Executive Summary)

### 1.1. Bối cảnh & Vấn đề (Problem Statement)
Hàng ngày, hàng ngàn nhà hàng, tiệm bánh, siêu thị và quán ăn buộc phải tiêu hủy một lượng lớn thực phẩm hoàn toàn đảm bảo chất lượng và vệ sinh an toàn chỉ vì không bán hết trong ngày. Điều này gây ra:
- **Tổn thất kinh tế**: Doanh nghiệp ẩm thực mất doanh thu từ chi phí nguyên liệu và xử lý rác thải.
- **Tác động môi trường**: Thực phẩm hữu cơ phân hủy tại các bãi chôn lấp tạo ra khí mê-tan ($CH_4$), một trong những tác nhân hàng đầu gây biến đổi khí hậu.
- **Lãng phí xã hội**: Người tiêu dùng có thu nhập trung bình/thấp hoặc sinh viên gặp khó khăn khi tiếp cận bữa ăn chất lượng với chi phí hợp lý.

### 1.2. Giải pháp EcoBite (Solution)
**EcoBite** là nền tảng O2O (Online-to-Offline) kết nối các cơ sở kinh doanh ăn uống với người tiêu dùng có nhu cầu mua thực phẩm cận giờ đóng cửa dưới dạng **Gói thức ăn ngẫu nhiên (Surprise Bags)** với mức giá giảm sâu (50% - 80%). Người mua đặt hàng qua ứng dụng và đến trực tiếp quán để lấy thức ăn bằng mã QR bảo mật động.

---

## 2. Các Nhóm Người dùng (User Personas)

1. **Người tiêu dùng (Consumer - End User)**:
   - Giới trẻ, sinh viên, nhân viên văn phòng quan tâm đến lối sống bền vững (Zero-waste) và muốn tiết kiệm chi phí ăn uống.
   - Nhu cầu: Tìm kiếm các quán ngon gần vị trí hiện tại, săn gói đồ ăn giá hời, thanh toán nhanh và lấy hàng tiện lợi.
2. **Đối tác Cửa hàng (Store Partner / Merchant)**:
   - Tiệm bánh mì/pastry, quán cơm, nhà hàng buffet, quán cafe, chuỗi siêu thị tiện lợi.
   - Nhu cầu: Đăng tải nhanh các suất ăn dư thừa cuối ngày, thu hồi vốn nguyên liệu, giảm chi phí rác thải và quảng bá thương hiệu.
3. **Quản trị viên Hệ thống (System Admin / Operations)**:
   - Đội ngũ vận hành EcoBite.
   - Nhu cầu: Kiểm duyệt giấy phép vệ sinh an toàn thực phẩm của quán, giám sát giao dịch, quản lý tranh chấp và theo dõi chỉ số tác động môi trường (CO2 saved).

---

## 3. Đặc tả 8 Tính năng Cốt lõi (Core Features Specification)

### Tính năng 1: Xác thực & Quản trị Duyệt Quán (Auth & Partner KYC Onboarding)
- **Đăng ký / Đăng nhập**: Hỗ trợ Email/Password và Google OAuth2 (Single Sign-On).
- **Phân quyền người dùng (RBAC)**: `CONSUMER`, `STORE_PARTNER`, `ADMIN`.
- **Quy trình Onboarding Đối tác**:
  - Đối tác tạo hồ sơ: Tên cửa hàng, địa chỉ, định vị GPS, mã số thuế/giấy phép kinh doanh, ảnh cửa hàng, chứng nhận ATVSTP.
  - Trạng thái hồ sơ: `PENDING_REVIEW` $\rightarrow$ `APPROVED` hoặc `REJECTED`.
  - Admin duyệt hồ sơ thông qua Admin Portal, gửi email thông báo kết quả.

### Tính năng 2: Đăng Gói thức ăn Ngẫu nhiên & Giảm giá theo Khung giờ (Surprise Bags & Dynamic Pricing)
- **Cơ chế Gói ngẫu nhiên (Surprise Bag)**: Đối tác không cần liệt kê từng món chi tiết; phân loại theo nhóm (Ví dụ: "Túi Bánh Ngọt Cuối Ngày", "Cơm Phần Dinh Dưỡng", "Thực Phẩm Tươi Sống").
- **Số lượng & Giới hạn**: Thiết lập số lượng gói mở bán trong ngày.
- **Khung giờ nhận hàng (Pickup Window)**: Ví dụ: `19:30 - 21:00`.
- **Giảm giá lũy tiến (Dynamic Time-based Pricing)**:
  - Cho phép cấu hình giảm giá sâu hơn khi càng gần thời điểm kết thúc giờ nhận hàng (ví dụ: 19:30 giảm 50%, sau 20:30 tự động giảm 70% để đẩy nhanh tiến độ giải cứu).

### Tính năng 3: Tìm kiếm Theo Vị trí Địa lý (Geo-spatial Location-based Search)
- Sử dụng tiện ích không gian PostGIS để tính khoảng cách theo bán kính thực tế (Haversine / Spatial Indexing).
- Người dùng xem danh sách và bản đồ trực quan các quán xung quanh (1km, 3km, 5km, 10km).
- Bộ lọc nâng cao: Khoảng cách, Danh mục (Bánh mặn/ngọt, Chay, Đồ uống), Khoảng giá, Đánh giá sao, Trạng thái (Đang mở bán / Đã hết hàng).

### Tính năng 4: Đặt hàng & Sinh Mã QR Bảo mật Động (Order & Dynamic QR Token)
- Giỏ hàng & Thanh toán (COD / Chuyển khoản hoặc Cổng thanh toán tích hợp).
- Khoá số lượng tồn kho (Inventory Lock) với cơ chế Atomicity tránh tình trạng over-selling khi nhiều người cùng đặt món cuối cùng.
- Sinh **Mã QR bảo mật động**:
  - Token được ký điện tử bằng thuật toán HMAC-SHA256 (`order_id`, `user_id`, `pickup_timestamp`, `secret_salt`).
  - Mã QR có hạn sử dụng theo đúng khung giờ nhận hàng (`pickup_window`), ngăn chặn chụp màn hình chia sẻ trái phép hoặc tái sử dụng.

### Tính năng 5: Quét Mã QR Xác nhận Giao hàng tại Quán (QR Scanner Verification)
- Ứng dụng phía Store Partner tích hợp camera scanner trực tiếp trên nền web (`html5-qrcode`).
- Khi khách đến nhận hàng, chủ quán quét mã QR trên điện thoại khách.
- Hệ thống giải mã, đối soát token HMAC, kiểm tra trạng thái đơn:
  - Chuyển trạng thái từ `CONFIRMED` $\rightarrow$ `COMPLETED`.
  - Ghi nhận thời gian nhận hàng thực tế và kích hoạt quy trình tích điểm xanh.

### Tính năng 6: Đánh giá 1-5 Sao & Nhận xét Chất lượng (Rating & Reviews)
- Chỉ người tiêu dùng đã hoàn tất đơn hàng (`COMPLETED`) mới có quyền gửi đánh giá (Verified Purchase).
- Thang điểm: 1 - 5 sao.
- Thuộc tính đánh giá nhanh: "Chất lượng tươi ngon", "Đóng gói cẩn thận", "Thái độ phục vụ tốt", "Lượng thức ăn nhiều".
- Tải ảnh minh chứng thực tế món ăn nhận được.
- Điểm đánh giá trung bình tự động cập nhật vào trang cửa hàng và ảnh hưởng đến xếp hạng tìm kiếm.

### Tính năng 7: Hệ thống Thông báo Thời gian thực (Real-time Notification Engine)
- Thông báo trạng thái đơn hàng: "Đơn hàng đã sẵn sàng để lấy", "Còn 30 phút trước khi kết thúc giờ nhận".
- Thông báo đẩy vị trí (Geo-push): "Quán A cách bạn 500m vừa mở bán 3 Gói Cứu Trợ giảm 60%!".
- Kênh truyền thông: In-app Notification, Web Push qua WebSocket / Redis PubSub.

### Tính năng 8: Tích Điểm Xanh & Đo lường Giảm Phát thải CO2 (Green Points & CO2 Calculator)
- **Công thức quy đổi môi trường**:
  - Trung bình mỗi 1 kg thực phẩm cứu trợ thành công tương đương giảm phát thải khoảng 2.5 kg $CO_2$ tương đương ($CO_2e$) ra môi trường.
  - Mỗi đơn hàng giải cứu thành công tích luỹ Điểm Xanh (`Green Points`) vào ví cá nhân.
- **Ứng dụng của Điểm Xanh**:
  - Đổi mã giảm giá (Vouchers) cho các đơn hàng tiếp theo.
  - Bảng vinh danh (Green Leaderboard) tôn vinh các cá nhân và cửa hàng giải cứu nhiều thực phẩm nhất.

---

## 4. User Stories & Acceptance Criteria

### US-01: Đăng ký & Xét duyệt Cửa hàng
**As a** Chủ tiệm bánh,  
**I want** đăng ký tài khoản cửa hàng và gửi giấy phép kinh doanh,  
**So that** tôi có thể mở bán các phần bánh mì thừa trên EcoBite sau khi được duyệt.

- **Acceptance Criteria**:
  - *Given*: Chủ quán cung cấp đầy đủ thông tin (Tên quán, Địa chỉ, GPS, Ảnh ATVSTP).
  - *When*: Bấm nút "Gửi hồ sơ kiểm duyệt".
  - *Then*: Trạng thái cửa hàng chuyển sang `PENDING_REVIEW`, Admin nhận thông báo có quán mới cần duyệt. Quán chưa thể tạo gói thức ăn cho đến khi trạng thái là `APPROVED`.

### US-02: Đăng Gói Thức ăn Surprise Bag với Giảm giá Khung giờ
**As a** Đối tác cửa hàng,  
**I want** tạo một đợt bán Gói Bất Ngờ với thời gian lấy hàng từ 20:00 - 21:00 và tự động hạ giá thêm sau 20:30,  
**So that** tôi có thể tối đa hoá khả năng bán hết hàng trước giờ đóng cửa.

- **Acceptance Criteria**:
  - *Given*: Cửa hàng ở trạng thái `APPROVED`.
  - *When*: Cửa hàng nhập số lượng 5 suất, giá gốc 100k, giá ưu đãi 40k, và tick chọn "Giảm thêm còn 25k trong 30 phút cuối".
  - *Then*: Hệ thống lên lịch cập nhật giá tự động dựa trên thời gian thực và hiển thị đếm ngược (countdown) cho người mua.

### US-03: Tìm kiếm Quán Gần Đây trên Bản đồ
**As a** Người tiêu dùng,  
**I want** bật định vị GPS và xem các quán có đồ ăn cứu trợ trong bán kính 3km,  
**So that** tôi có thể đi bộ hoặc đi xe máy lấy hàng nhanh chóng.

- **Acceptance Criteria**:
  - *Given*: Người dùng cấp quyền truy cập vị trí trên trình duyệt.
  - *When*: Người dùng mở trang Tìm kiếm.
  - *Then*: Hệ thống sử dụng PostGIS truy vấn các quán có gói hàng khả dụng trong bán kính 3km, sắp xếp theo khoảng cách từ gần nhất đến xa nhất và ghim vị trí lên bản đồ Leaflet.

### US-04: Đặt hàng & Nhận Mã QR Đơn hàng
**As a** Người tiêu dùng,  
**I want** thanh toán 1 gói thức ăn và nhận mã QR có chữ ký bảo mật,  
**So that** tôi mang mã này tới quán để nhân viên xác thực và giao hàng.

- **Acceptance Criteria**:
  - *Given*: Gói thức ăn còn số lượng tồn kho > 0.
  - *When*: Người dùng xác nhận đặt hàng.
  - *Then*: Số lượng tồn kho giảm 1 trong một transaction nguyên tử, mã QR chứa token HMAC-SHA256 được tạo và hiển thị trong mục "Đơn hàng của tôi".

### US-05: Quán Quét Mã QR Xác nhận Đơn
**As a** Nhân viên cửa hàng,  
**I want** dùng camera trên điện thoại quét mã QR của khách hàng,  
**So that** xác thực đơn hàng hợp lệ và giao gói thức ăn.

- **Acceptance Criteria**:
  - *Given*: Khách hàng đưa mã QR hợp lệ trong khung giờ nhận hàng.
  - *When*: Nhân viên quét mã bằng camera của web app.
  - *Then*: Hệ thống kiểm tra chữ ký HMAC thành công, cập nhật đơn hàng thành `COMPLETED`, phát âm thanh báo thành công và cộng điểm xanh cho người dùng.
  - *Given (Trường hợp lỗi)*: Khách đưa mã QR đã quét rồi hoặc đã hết hạn, hệ thống hiển thị cảnh báo đỏ từ chối giao dịch.

### US-06: Đánh giá Sau Khi Nhận Hàng
**As a** Người tiêu dùng,  
**I want** chấm 5 sao và viết lời khen ngợi cho tiệm bánh sau khi ăn xong,  
**So that** cộng đồng có thêm thông tin tham khảo và tiệm bánh được nâng cao uy tín.

- **Acceptance Criteria**:
  - *Given*: Đơn hàng có trạng thái `COMPLETED`.
  - *When*: Người dùng gửi form đánh giá (sao + nội dung + ảnh chụp).
  - *Then*: Đánh giá xuất hiện công khai trên trang cửa hàng, điểm đánh giá trung bình của quán được tự động tính lại.
