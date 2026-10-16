# EcoBite Platform - Product Requirement Document (PRD) & User Stories

**Dự án**: EcoBite - Nền tảng Cứu trợ Thực phẩm Dư thừa & Kết nối Xanh (Food Rescue Platform)
**Tác giả**: Senior DevOps Engineer & Technical Project Manager
**Phiên bản**: 2.1.0 (Bổ sung Nhóm Tính năng AI Riêng biệt & Hệ thống Gợi ý Món ăn Thông minh)
**Trạng thái**: Approved for Implementation

---

## 1. Tổng quan Dự án (Executive Summary)

### 1.1. Bối cảnh & Vấn đề (Problem Statement)
Hàng ngày, hàng ngàn nhà hàng, tiệm bánh, quán ăn, quán cafe và siêu thị buộc phải tiêu hủy một lượng lớn các món ăn ngon, sạch, đảm bảo vệ sinh an toàn thực phẩm chỉ vì không bán hết trong ca kinh doanh. Điều này gây ra:
- **Tổn thất kinh tế**: Doanh nghiệp F&B mất doanh thu từ chi phí nguyên liệu và phí xử lý rác thải.
- **Tác động môi trường**: Thực phẩm hữu cơ phân hủy tại bãi rác sinh ra khí mê-tan ($CH_4$) và khí nhà kính ($CO_2$), đẩy nhanh biến đổi khí hậu.
- **Lãng phí xã hội**: Người tiêu dùng có thu nhập trung bình/thấp, sinh viên, nhân viên văn phòng gặp khó khăn trong việc tiếp cận các bữa ăn chất lượng với mức giá tiết kiệm.

### 1.2. Giải pháp EcoBite (Solution)
**EcoBite** là nền tảng O2O (Online-to-Offline) kết nối các cơ sở kinh doanh ăn uống với người tiêu dùng có nhu cầu mua **các món ăn dư thừa trong ngày (Surplus Food Dishes)** với mức giá giải cứu giảm sâu từ 40% - 70%.
- **Minh bạch thực đơn**: Người dùng biết chính xác mình đang mua món gì (ví dụ: Cơm sườn nướng, Phở gà, Bánh croissant, Trà sữa trân châu...), có thành phần và cảnh báo dị ứng rõ ràng.
- **Bộ đôi Trí tuệ Nhân tạo Đột phá (Google Gemini 2.5 Flash)**:
  1. *Phía Quán*: Trợ lý AI Quick-Post bóc tách thực đơn và cảnh báo dị ứng tự động trong 1 giây.
  2. *Phía Khách*: Động cơ Gợi ý Món ăn Thông minh Cá nhân hóa (Smart Recommendation Engine) phân tích ngữ cảnh, gu ẩm thực và sinh lý do đề xuất thuyết phục.
- **Luật giảm giá theo khung giờ (Rule-based Time-based Discounting)**: Áp dụng cơ chế hạ giá tự động theo luật thời gian minh bạch (càng gần giờ đóng cửa, giá càng giảm sâu để xả hết thực phẩm).
- **Lấy hàng bảo mật tại quán**: Khách hàng đặt mua và đến trực tiếp quán để lấy món thông qua **Mã QR động ký điện tử HMAC-SHA256**.

---

## 2. Các Nhóm Người dùng (User Personas)

1. **Người tiêu dùng (Consumer - End User)**:
   - Giới trẻ, sinh viên, nhân viên văn phòng có thói quen ăn uống tiết kiệm và quan tâm đến lối sống không rác thải (Zero-waste).
   - Nhu cầu: Nhận được gợi ý món ăn đúng gu và gần vị trí nhất, biết rõ thành phần món ăn, săn món giảm giá sâu vào khung giờ vàng, lấy hàng nhanh gọn.
2. **Đối tác Cửa hàng (Store Partner / Merchant)**:
   - Quán cơm, nhà hàng, tiệm bánh mì/bánh ngọt, quán cafe, chuỗi bán lẻ F&B.
   - Nhu cầu: Đăng tải cực nhanh các phần thức ăn còn dư cuối ca làm việc mà không mất thời gian nhập liệu phức tạp, thu hồi vốn nguyên liệu, giảm lãng phí và xây dựng hình ảnh thương hiệu xanh.
3. **Quản trị viên Hệ thống (System Admin / Operations)**:
   - Đội ngũ vận hành EcoBite.
   - Nhu cầu: Kiểm duyệt giấy phép kinh doanh và chứng nhận an toàn vệ sinh thực phẩm (ATVSTP), theo dõi giao dịch, xử lý khiếu nại và đo lường chỉ số giảm phát thải $CO_2$ toàn hệ thống.

---

## 3. Đặc tả Danh mục Tính năng Hệ thống

---

### PHÂN HỆ I: NHÓM TÍNH NĂNG NỀN TẢNG & VẬN HÀNH O2O (CORE PLATFORM)

#### Tính năng 1: Xác thực & Quản trị Duyệt Quán (Auth & Partner KYC Onboarding)
- **Đăng ký / Đăng nhập**: Hỗ trợ Email/Password và Google OAuth2 (Single Sign-On).
- **Phân quyền người dùng (RBAC)**: `CONSUMER`, `STORE_PARTNER`, `ADMIN`.
- **Quy trình Onboarding Đối tác**:
  - Đối tác tạo hồ sơ: Tên cửa hàng, địa chỉ, định vị GPS, số điện thoại, ảnh cửa hàng, chứng nhận ATVSTP.
  - Trạng thái hồ sơ: `PENDING_REVIEW` $\rightarrow$ `APPROVED` hoặc `REJECTED`.
  - Admin duyệt hồ sơ thông qua Admin Portal, gửi email thông báo kết quả. Quán chỉ được đăng món sau khi được duyệt.

#### Tính năng 2: Quản lý Món ăn Cụ thể & Giảm giá Theo Khung giờ Rule-based (Dish Management & Rule-based Discounting)
- **Thông tin món ăn cụ thể**: Tên món, danh mục (Cơm, Bún/Phở, Bánh mì, Đồ ngọt, Đồ uống...), mô tả, ảnh món ăn, số lượng suất còn lại.
- **Khung giờ nhận món (Pickup Window)**: Ví dụ: Ca trưa từ `13:30 - 15:00`, ca tối từ `20:00 - 21:30`.
- **Luật giảm giá theo khung giờ (Rule-based Time-based Discounting)**:
  - *Giá giải cứu tiêu chuẩn (`rescue_price`)*: Áp dụng trong suốt khung giờ mở bán (giảm 40% - 50% so với giá gốc).
  - *Giá giờ chót (`rule_discount_price`)*: Tự động kích hoạt khi bước vào 30-45 phút cuối trước giờ kết thúc (ví dụ từ 20:45 tự động giảm còn 70% giá gốc) theo luật xác định trước để thúc đẩy giải cứu toàn bộ lượng thức ăn còn lại.

#### Tính năng 3: Tìm kiếm Không gian Địa lý (Geo-Spatial Search with PostGIS)
- **Truy vấn PostGIS**: Sử dụng hàm `ST_DWithin` và GIST Spatial Index trên trường toạ độ `stores.location` để tìm các quán và món ăn đang giảm giá trong bán kính 1km, 3km, 5km, 10km.
- **Bản đồ Leaflet tương tác**: Ghim các quán xung quanh, xem danh sách món ăn còn suất và giá ưu đãi ngay trên popup marker.

#### Tính năng 4: Đặt hàng & Khóa Tồn kho Chống Bán Vượt (Order Placement & Atomic Inventory Lock)
- Khách chọn từng món cụ thể, số lượng và phương thức thanh toán.
- **Chống Over-selling**: Sử dụng Database Transaction với câu lệnh nguyên tử (`UPDATE dishes SET remaining_quantity = remaining_quantity - :qty WHERE remaining_quantity >= :qty`) hoặc Redis Distributed Lock. Nếu 2 khách cùng bấm mua 1 suất cuối cùng, chỉ 1 người thành công.

#### Tính năng 5: Sinh Mã QR Bảo mật Động (Dynamic HMAC-SHA256 QR Token)
- Khi đặt hàng thành công, hệ thống sinh mã QR trên app của khách.
- Token được ký điện tử bằng thuật toán **HMAC-SHA256** chứa `order_id`, `consumer_id`, `pickup_deadline`, và chuỗi ngẫu nhiên `nonce`.
- Mã QR chỉ có hiệu lực đúng trong khung giờ nhận hàng (`pickup_window`), ngăn chặn hoàn toàn việc chụp màn hình gửi bừa bãi.

#### Tính năng 6: Quét Mã QR Xác nhận Giao Hàng tại Quán (Camera QR Scanner Verification)
- Ứng dụng phía Store Partner tích hợp Camera Web Scanner (`html5-qrcode`).
- Khi khách đến quán nhận món, chủ quán dùng camera quét mã QR của khách.
- Hệ thống giải mã chữ ký, kiểm tra tính hợp lệ và đổi trạng thái đơn sang `COMPLETED`.
- **Chống Replay Attack**: Mỗi mã QR chỉ quét được 1 lần duy nhất. Nếu quét lại lần 2, hệ thống từ chối và báo lỗi đỏ.

#### Tính năng 7: Đánh giá Món ăn Thực tế (Verified Dish Reviews & Rating)
- Chỉ người dùng đã nhận món thành công (`COMPLETED`) mới có quyền gửi đánh giá (Verified Purchase).
- Đánh giá 1 - 5 sao kèm hình ảnh thực tế cho **từng món ăn cụ thể** và thái độ phục vụ của quán.
- Điểm đánh giá trung bình tự động cập nhật vào trang cửa hàng và ảnh hưởng đến thứ tự ưu tiên hiển thị.

#### Tính năng 8: Tích Điểm Xanh & Đo lường Giảm Phát thải CO2 (Green Points & CO2 Tracker)
- **Công thức quy đổi**: Mỗi suất ăn được giải cứu thành công tương đương giảm phát thải $\approx 2.5\text{ kg } CO_2$ ra môi trường.
- Người dùng nhận Điểm Xanh (`Green Points`) vào ví cá nhân sau mỗi đơn hàng hoàn tất.
- **Đổi Voucher**: Dùng Điểm Xanh để đổi các mã giảm giá cho các đơn mua tiếp theo.
- **Bảng vinh danh (Green Leaderboard)**: Tôn vinh các cá nhân và quán ăn cứu trợ nhiều thực phẩm nhất.

---

### PHÂN HỆ II: NHÓM TÍNH NĂNG TRÍ TUỆ NHÂN TẠO (AI INTELLIGENCE SUITE)
> **Động cơ**: Google Gemini 2.5 Flash (Gói Free Tier qua Google AI Studio / Google AI Pro) + Google GenAI SDK (`google-genai`)

#### Tính năng AI 1: Trợ lý Bóc tách Món ăn & Cảnh báo An toàn Dị ứng Siêu tốc (Smart Menu Parser & Allergen Guard)
> **Động cơ**: Google Gemini 2.5 Flash (Gói Free Tier qua Google AI Studio / Pro) + Google GenAI SDK (`google-genai`) với Native Audio Multimodal & Structured Outputs (Pydantic Schema).

Tính năng giải quyết triệt để 5 điểm nghẽn vận hành thực tế tại các quán ăn Việt Nam:
1. **Menu-Catalog Grounding (Kế thừa Thực đơn gốc & Ảnh món ăn)**:
   - Quán ăn đã có Thực đơn gốc (`menu_items`) gồm: Tên chuẩn, Ảnh đại diện món, Giá gốc và Thành phần chuẩn.
   - Khi chủ quán đọc danh sách món dư, Gemini trích xuất tên món và thực hiện so khớp ngữ nghĩa (*Semantic/Fuzzy Matching*) với `menu_item_id` của quán để tự động kéo **Ảnh món ăn + Giá gốc** và kích hoạt Luật giảm giá theo thời gian.
   - Nếu chủ quán đọc giá giảm cụ thể (*"xả nhanh 20k"*), hệ thống ghi nhận vào `override_discounted_price` để ghi đè lên quy tắc mặc định.
2. **Suy luận Dị ứng 2 Tầng (2-Tier Allergen Guard) & Nhãn Khẩu vị Địa phương**:
   - **Tầng 1 (EXPLICIT - Khai báo trực tiếp)**: Bắt các thành phần do chủ quán đọc ra (*"có đậu phộng rang"*, *"sốt bơ trứng"*).
   - **Tầng 2 (INFERRED - Suy luận tri thức ẩm thực Việt)**: Dù chủ quán chỉ đọc *"Cơm sườn chả"*, AI kết hợp công thức ẩm thực để tự suy luận: Chả chưng có **Trứng (Eggs)**, Nước mắm có **Cá (Fish)**, Mỡ hành có **Đậu phộng (Peanuts)** theo chuẩn 14 chất dị ứng EU FIC.
   - **Mở rộng nhãn khẩu vị (`dietary_notes`)**: Bổ sung các nhóm kiêng ăn phổ biến tại Việt Nam: Có Hành/Ngò (*Allium*), Đồ cay, Đồ chua, Ăn chay.
3. **Trích xuất Hàng loạt (Batch Extraction Schema)**:
   - Thiết kế Schema dạng danh sách `List[SurplusDishItem]`, cho phép chủ quán nói một mạch: *"Hôm nay dư 5 cơm sườn, 3 bún thịt nướng và 4 bánh flan, bán từ 2h đến 4h chiều nhé"*. Cả 3 món cùng được bóc tách và kế thừa khung giờ chung `14:00 - 16:00`.
4. **Xử lý Thời gian Tương đối (Relative Time Ingestion)**:
   - Backend truyền biến `current_server_time` (chuẩn ISO 8601, ví dụ: `2026-10-16T13:55:00+07:00`) vào System Prompt của Gemini 2.5 Flash. Khi chủ quán nói *"bán từ giờ đến 3h chiều"* hoặc *"xả trong 1 tiếng nữa"*, mô hình tự tính toán ra mốc thời gian tuyệt đối `pickup_start` và `pickup_end` chính xác 100%.
5. **Xử lý Trực tiếp Luồng Âm thanh (Native Multimodal Audio Understanding)**:
   - Thay vì dùng STT trung gian dễ nhận diện sai tên món và tiếng lóng (*"bốn lăm cành"*, *"bì chả"*), ứng dụng gửi file ghi âm ngắn trực tiếp sang Gemini 2.5 Flash kèm danh sách thực đơn trong Prompt để mô hình nghe và đối soát ngữ cảnh chuẩn xác.

#### Tính năng AI 2: Hệ thống Gợi ý Món ăn Thông minh Cá nhân hóa (AI Smart Food Recommendation Engine)
Động cơ gợi ý Hybrid kết hợp 3 lớp phân tích thông minh:
1. **Lớp Ngữ cảnh Thời gian thực (Context-Aware Layer)**:
   - Xác định toạ độ GPS của user: Ưu tiên quán trong bán kính đi bộ/xe máy gần nhất (1km - 3km).
   - Xác định thời điểm trong ngày: Bữa trưa (11h - 13h30), Bữa xế (14h - 16h), Bữa tối (18h - 20h30).
   - **Ưu tiên Deal Cứu trợ Khẩn cấp (Urgent Rescue Deals)**: Đẩy lên đầu danh sách các món ăn thuộc gu của user đang bước vào 30 phút cuối của luật giảm giá 70%.
2. **Lớp Sở thích & Hồ sơ Cá nhân (User Profile & Taste Layer)**:
   - Đọc lịch sử đặt món: Tần suất chọn món nước, món khô, đồ ngọt hay đồ ăn mặn.
   - Tự động loại trừ các món có thành phần chứa chất dị ứng của người dùng (dựa trên bảng `user_preferences`).
   - Khớp khung ngân sách quen thuộc của người dùng.
3. **Lớp Sinh lý tưởng Gợi ý bằng GenAI (AI Justification Generator)**:
   - **Gemini 2.5 Flash** nhận đầu vào gồm hồ sơ user và top 3 món ăn phù hợp nhất quanh khu vực, sinh ra câu văn giải thích tự nhiên, ngắn gọn và cực kỳ thuyết phục hiển thị trực tiếp trên thẻ món ăn (UI Card):
     *Ví dụ: "💡 Gợi ý cho bạn: Bạn thường chọn bún/phở vào buổi trưa. Quán Phở Bắc cách bạn 400m đang có deal giảm 50% chỉ còn 25.000đ (còn 2 suất cuối đến 14h), rất hợp khẩu vị thanh đạm của bạn!"*

---

## 4. User Stories & Acceptance Criteria

### US-01: Đăng ký & Xét duyệt Cửa hàng (Partner Onboarding)
**As a** Chủ quán cơm trưa văn phòng,
**I want** đăng ký tài khoản đối tác và nộp giấy phép ATVSTP,
**So that** tôi có thể mở bán các suất cơm trưa còn dư sau khi được Admin phê duyệt.

- **Acceptance Criteria**:
  - *Given*: Chủ quán cung cấp đầy đủ thông tin (Tên quán, Địa chỉ, Tọa độ GPS, Ảnh chứng nhận ATVSTP).
  - *When*: Bấm nút "Gửi hồ sơ kiểm duyệt".
  - *Then*: Trạng thái cửa hàng chuyển sang `PENDING_REVIEW`, Admin nhận thông báo có quán mới. Quán chỉ có thể đăng món khi trạng thái chuyển sang `APPROVED`.

### US-02: Đăng Món ăn Cụ thể với Luật Giảm giá theo Khung giờ
**As a** Đối tác tiệm bánh mì,
**I want** đăng bán 10 ổ bánh mì kẹp thịt xá xíu giá gốc 35k, giá giải cứu 18k từ 19:30 - 21:00 và tự động giảm tiếp còn 10k trong 30 phút cuối,
**So that** tôi có thể thu hồi vốn và bán hết sạch bánh mì trong ngày.

- **Acceptance Criteria**:
  - *Given*: Cửa hàng ở trạng thái `APPROVED`.
  - *When*: Cửa hàng nhập thông tin món cụ thể, số lượng 10, chọn khung giờ nhận 19:30 - 21:00, và tick chọn "Kích hoạt luật giảm giá giờ chót 10.000đ sau 20:30".
  - *Then*: Hệ thống lưu món vào CSDL; từ 19:30 khách thấy giá 18k, từ đúng 20:30 giá tự động hiển thị 10k kèm đồng hồ đếm ngược.

### US-03: Trợ lý AI Bóc tách Hàng loạt Món ăn & Khớp Thực đơn Gốc (Batch Quick-Post & Menu Grounding)
**As a** Chủ quán ăn đang bận rộn dọn dẹp cuối ca,
**I want** thu âm một câu nói ngắn liệt kê nhiều món ăn dư thừa cùng lúc (*"Còn 5 cơm sườn, 3 bún chả và 4 chè đậu xả từ giờ đến 3h chiều"*),
**So that** Trợ lý AI tự động khớp thực đơn gốc để lấy ảnh và giá, rà soát dị ứng 2 tầng (Explicit + Inferred) và tạo danh sách thẻ món ăn để tôi đăng bài trong 1 chạm.

- **Acceptance Criteria**:
  - *Given*: Quán đã có Thực đơn gốc (`menu_items`) và micro ghi âm hoạt động.
  - *When*: Chủ quán gửi file ghi âm ngắn kèm `current_server_time = 13:55:00`.
  - *Then*: API gọi Gemini 2.5 Flash (Native Audio) trả về cấu trúc `QuickPostExtractionResponse`:
    - Khung giờ nhận: `13:55:00` - `15:00:00`.
    - Trích xuất đủ 3 món: Tự động gắn `matched_menu_id` để lấy ảnh và giá gốc từ thực đơn.
    - Cảnh báo dị ứng 2 tầng: Cơm sườn chả có nhãn `INFERRED` cảnh báo Trứng (trong chả) và Cá (trong nước mắm).
    - Màn hình hiển thị danh sách 3 thẻ món ăn kèm nút gạt xác nhận dị ứng; chủ quán bấm **"Đăng tất cả" trong 3 giây**.

### US-04: Hệ thống Gợi ý Món ăn Thông minh Cá nhân hóa (AI Smart Recommendation)
**As a** Người tiêu dùng chuẩn bị ăn trưa,
**I want** mở app và thấy ngay danh sách "Món Ngon Gợi Ý Cho Bạn" kèm lý do AI giải thích,
**So that** tôi chọn được món ngon hợp khẩu vị gần nhất mà không mất thời gian tìm kiếm.

- **Acceptance Criteria**:
  - *Given*: Người dùng đã đăng nhập và bật GPS.
  - *When*: Người dùng mở Trang chủ ứng dụng.
  - *Then*: Hệ thống chạy thuật toán Recommendation lọc các món trong bán kính 2km, loại trừ món chứa dị ứng trong hồ sơ của user, hiển thị Top 3 món kèm lời giải thích tự nhiên từ Gemini 2.5 Flash (*"Gợi ý vì bạn thích món nước vào buổi trưa và quán cách bạn 300m đang giảm 50%"*).

### US-05: Đặt hàng & Nhận Mã QR Đơn hàng
**As a** Người tiêu dùng,
**I want** đặt mua 2 suất cơm sườn nướng và nhận mã QR có chữ ký bảo mật,
**So that** tôi mang mã này tới quán để nhận đúng món ăn đã đặt.

- **Acceptance Criteria**:
  - *Given*: Món ăn còn số lượng tồn kho $\ge 2$.
  - *When*: Người dùng bấm "Xác nhận đặt hàng".
  - *Then*: Số lượng món giảm 2 ngay lập tức trong một transaction nguyên tử, mã QR chứa token HMAC-SHA256 được tạo và hiển thị trong mục "Đơn hàng của tôi".

### US-06: Quán Quét Mã QR Xác nhận Đơn
**As a** Nhân viên quán ăn,
**I want** dùng camera trên điện thoại quét mã QR của khách khi khách đến lấy món,
**So that** xác thực đơn hàng hợp lệ và giao món.

- **Acceptance Criteria**:
  - *Given*: Khách hàng đưa mã QR hợp lệ trong khung giờ nhận món.
  - *When*: Nhân viên quét mã bằng camera web app.
  - *Then*: Hệ thống kiểm tra chữ ký HMAC thành công, cập nhật đơn hàng thành `COMPLETED`, phát âm thanh báo thành công và cộng điểm xanh cho người dùng.
  - *Given (Trường hợp lỗi)*: Khách đưa mã QR đã quét rồi hoặc đã hết hạn, hệ thống hiển thị cảnh báo đỏ từ chối giao dịch.

### US-07: Đánh giá Món ăn Sau Khi Thưởng thức
**As a** Người tiêu dùng,
**I want** chấm 5 sao và đánh giá món cơm gà xối mỡ sau khi ăn xong,
**So that** cộng đồng có thêm review thực tế và quán ăn được nâng cao uy tín.

- **Acceptance Criteria**:
  - *Given*: Đơn hàng có trạng thái `COMPLETED`.
  - *When*: Người dùng gửi form đánh giá (chọn số sao + viết nhận xét + tải ảnh món ăn thực tế).
  - *Then*: Đánh giá xuất hiện công khai trên trang chi tiết món ăn và trang cửa hàng, điểm đánh giá trung bình của quán được tự động cập nhật.
