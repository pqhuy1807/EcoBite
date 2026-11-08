# 🌱 EcoBite Platform - Product Requirement Document (PRD) & User Stories

**Dự án**: EcoBite - Nền tảng Giải cứu Thực phẩm Thông minh & Kết nối Xanh (Food Rescue Platform)
**Nhóm thực hiện**: Group 5 - Lớp Kỹ nghệ Phần mềm / Computer Science (HCMUS)
- **Phùng Quốc Huy** (24127402 - pqhuy2425@clc.fitus.edu.vn) — *AI and Data Lead / Full-Stack Engineer*
- **Đặng Trọng Phúc** (24127495 - dtphuc2418@clc.fitus.edu.vn) — *Backend Lead & AI Engineer / Full-Stack Engineer*
- **Đàng Thế Tony** (24127561 - dttony2424@clc.fitus.edu.vn) — *QA/Tester Lead & Backend Engineer / Full-Stack Engineer*
- **Võ Ngọc Thịnh** (24127246 - vnthinh2418@clc.fitus.edu.vn) — *Frontend Lead / Full-Stack Engineer*

**Phiên bản**: 2.2.0 (Đồng bộ chuẩn hóa 100% theo Báo cáo Đề xuất Dự án - Project Proposal)
**Trạng thái**: Approved for Implementation (Sprints PA1 – PA5)

---

## 1. Giới thiệu Tổng quan (Project Proposal & Introduction)

**EcoBite** là nền tảng giải cứu thực phẩm thông minh theo mô hình Online-to-Offline (O2O), được thiết kế nhằm kết nối các cơ sở kinh doanh thực phẩm thương mại (như nhà hàng, tiệm bánh, quán cà phê và siêu thị) với người tiêu dùng địa phương đang tìm kiếm các bữa ăn chất lượng cao với mức giá ưu đãi sâu (giảm từ 40% đến 70%).

Mỗi ngày, các gian bếp thương mại tại khu vực đô thị phải bỏ đi một lượng lớn thức ăn tươi ngon, đảm bảo vệ sinh chỉ vì chúng chưa được bán hết trong ca làm việc. Sự kém hiệu quả có hệ thống này dẫn đến tổn thất tài chính trực tiếp cho các chủ cửa hàng và gây ra hậu quả nghiêm trọng về môi trường, do rác thải hữu cơ phân hủy tại các bãi chôn lấp tạo ra các loại khí nhà kính mạnh ($CH_4$ và $CO_2$).

EcoBite giải quyết cuộc khủng hoảng này thông qua phương pháp minh bạch, thực tế và dựa trên công nghệ:
- **Giải cứu minh bạch từng món ăn (Không sử dụng túi mù - No Mystery Bags)**: Khác với các nền tảng phương Tây (như Too Good To Go) sử dụng "túi mù" ngẫu nhiên vốn gặp khó khăn tại thị trường Việt Nam do thói quen ăn uống và độ nhạy cảm về chế độ ăn, EcoBite yêu cầu niêm phong và liệt kê minh bạch từng món ăn dư thừa cụ thể, kèm theo hình ảnh rõ ràng, bảng thành phần tiêu chuẩn và cảnh báo dị ứng được xác thực.
- **Cơ chế giảm giá thời gian theo quy tắc tất định (Deterministic Rule-Based Time-Shift Discounting)**: Giá bán tuân theo các lịch trình quy tắc minh bạch (ví dụ: giảm 40%–50% trong khung giờ giải cứu tiêu chuẩn, tự động chuyển sang giảm 60%–70% trong 30–45 phút cuối trước khi đóng cửa), mang lại sự dự đoán trước cho cửa hàng và tối đa hóa tỷ lệ thanh lý hàng tồn.
- **Bộ đôi trí tuệ nhân tạo AI (Được hỗ trợ bởi Google Gemini 2.5 Flash)**: Tận dụng khả năng hiểu âm thanh đa phương thức nguyên bản và Xử lý ngôn ngữ tự nhiên (NLP) giúp các chủ quán bận rộn đăng bán hàng loạt các món ăn dư cuối ca chỉ trong vòng chưa đầy 3 giây với bộ lọc dị ứng 2 tầng, kết hợp cùng hệ thống gợi ý ngữ cảnh thông minh mang lại các gợi ý giải cứu bữa ăn cá nhân hóa cho người tiêu dùng.

---

## 2. Người dùng Mục tiêu & Môi trường Vận hành (Target Users and Environments)

### 2.1. Người dùng Mục tiêu (Target Users)
1. **Consumers (Người tiêu dùng / Người giải cứu thực phẩm)**:
   - Sinh viên đại học, nhân viên văn phòng và những cá nhân quan tâm đến chi phí, tìm kiếm các bữa ăn chất lượng, hợp vệ sinh với mức giá phải chăng, cũng như những công dân có ý thức sinh thái muốn tích cực giảm thiểu lãng phí thực phẩm đô thị.
2. **Store Partners (Đối tác cửa hàng / Chủ kinh doanh)**:
   - Tiệm bánh, quán cà phê, nhà hàng, quán ăn gia đình và siêu thị muốn kiếm tiền từ thực phẩm dư thừa cuối ca, thu hồi chi phí nguyên liệu, giảm thiểu phí xử lý rác thải và tiếp cận khách hàng địa phương mới.
3. **System Administrators (Quản trị viên hệ thống)**:
   - Đội ngũ vận hành nền tảng chịu trách nhiệm xác minh chứng nhận an toàn thực phẩm (ATVSTP) và thông tin xác thực kinh doanh của cửa hàng, kiểm duyệt danh sách thực phẩm, giám sát giao dịch, giảm thiểu tranh chấp và theo dõi các chỉ số môi trường tổng hợp.

### 2.2. Môi trường Mục tiêu (Target Environments)
1. **Client Application (Ứng dụng khách)**:
   - Ứng dụng Web Tiến bộ (PWA) đa nền tảng, phản hồi hoàn toàn (fully responsive) được xây dựng bằng **Next.js 14 (App Router)** và **Tailwind CSS**.
   - Tối ưu hóa cho trình duyệt di động (Apple Safari trên iOS, Google Chrome trên Android) cũng như môi trường máy tính để bàn hiện đại (Windows, macOS, Linux).
2. **Backend Infrastructure (Hạ tầng Backend)**:
   - Các dịch vụ vi mô dạng container được cung cấp bởi **FastAPI (Python 3.11)** với I/O bất đồng bộ.
   - **PostgreSQL 16 kết hợp PostGIS** để thực hiện các truy vấn không gian địa lý (geospatial).
   - **Redis 7** phục vụ việc lưu trữ cache và khóa phân tán nguyên tử (atomic locking).
   - **Google GenAI SDK** (`google-genai`) để gọi mô hình Gemini 2.5 Flash với Pydantic Structured Outputs.
   - **Cổng thanh toán VNPay** với cơ chế bảo mật chữ ký HMAC-SHA512 và Webhook IPN idempotent.

---

## 3. Danh mục Tính năng Cốt lõi (Key Features)

### Feature 1: Authentication & Merchant Onboarding (Xác thực & Đăng ký cửa hàng - KYC & Kiểm tra ATVSTP)
- **Function**: Người dùng đăng nhập qua Email/Password hoặc Google OAuth2 với Phân quyền dựa trên vai trò (`CONSUMER`, `STORE_PARTNER`, `ADMIN`) sử dụng JWT dual-tokens (Access Token ngắn hạn và Refresh Token an toàn). Các cửa hàng phải nộp Giấy chứng nhận Vệ sinh An toàn Thực phẩm (ATVSTP) chính thức và thông tin xác thực kinh doanh để quản trị viên phê duyệt bắt buộc trước khi được cấp quyền đăng bán.
- **Value**: Thiết lập niềm tin cộng đồng toàn diện, đảm bảo rằng tất cả thực phẩm dư thừa được giảm giá đều có nguồn gốc từ các cơ sở đạt chuẩn, vệ sinh và uy tín.

### Feature 2: Base Menu Catalog & Surplus Dish Management (Danh mục thực đơn cơ bản & Quản lý món dư)
- **Function**: Cửa hàng duy trì Danh mục Thực đơn Cơ bản cố định (`menu_items`) chứa hình ảnh độ phân giải cao tiêu chuẩn, giá bán lẻ gốc và thông tin thành phần cơ bản. Vào cuối ca, cửa hàng khởi tạo các Món Dư hoạt động (`dishes`) chỉ định số lượng còn lại, khung giờ nhận hàng và tùy chọn giá thanh lý cố định (`override_discounted_price`).
- **Value**: Loại bỏ gánh nặng phải tạo lại món ăn từ đầu, đảm bảo danh sách dư thừa luôn hiển thị hình ảnh chân thực, hấp dẫn và giá gốc chính xác.

### Feature 3: Rule-Based Time-Shift Discounting Engine (Công cụ giảm giá theo khung giờ dựa trên quy tắc)
- **Function**: Thực thi các quy tắc định giá giảm dần theo thời gian một cách tất định mà không có sự suy đoán giá ngẫu nhiên từ AI hộp đen. Các món ăn tự động chuyển đổi qua các mức được định nghĩa trước: khung giờ giải cứu tiêu chuẩn (giảm 40%–50%) và giờ cao điểm thanh lý cuối (giảm tới 70% trong 30–45 phút cuối) đi kèm với đồng hồ đếm ngược trực tiếp.
- **Value**: Mang lại sự minh bạch về giá rõ ràng cho người tiêu dùng và tạo động lực cấp bách để thanh lý 100% hàng tồn kho dễ hỏng trước khi nhà bếp đóng cửa.

### Feature 4: Location-Based Search & PostGIS Radar Discovery (Tìm kiếm dựa trên vị trí & Khám phá Radar PostGIS)
- **Function**: Tận dụng chỉ mục không gian PostgreSQL PostGIS (`ST_DWithin`, `ST_Distance`) để tính toán khoảng cách thời gian thực giữa người tiêu dùng và các cửa hàng lân cận trong bán kính 1–5 km (có thể mở rộng lên 10 km). Tích hợp bản đồ radar tương tác với các ghim bản đồ trực tiếp, bộ lọc ẩm thực (cơm, mì, bánh mì, chay), thanh trượt giá và chỉ báo mức độ gấp của thời gian nhận món.
- **Value**: Giúp người tiêu dùng khám phá các bữa ăn dư thừa trong khoảng cách đi bộ chỉ trong vài giây, giảm thiểu thời gian di chuyển và đảm bảo món ăn còn nóng sốt.

### Feature 5: Inventory Anti-Overselling Lock & Order Management (Khóa chống bán quá tồn kho & Quản lý đơn hàng)
- **Function**: Quản lý thanh toán của người tiêu dùng với quyền kiểm soát đồng thời cấp cơ sở dữ liệu nghiêm ngặt. Sử dụng các câu lệnh cập nhật SQL nguyên tử (`UPDATE dishes SET remaining_quantity = remaining_quantity - :qty WHERE remaining_quantity >= :qty`) được hỗ trợ bởi cơ chế khóa phân tán Redis.
- **Value**: Đảm bảo không xảy ra tình trạng bán vượt quá số lượng tồn kho (zero over-selling), loại bỏ các tình trạng tranh chấp dữ liệu (race conditions) khi nhiều người dùng cùng cố gắng mua suất ăn cuối cùng tại cùng một thời điểm.

### Feature 6: Seamless Cashless Checkout (VNPay Payment Gateway) (Thanh toán không tiền mặt liền mạch - Cổng thanh toán VNPay)
- **Function**: Tích hợp cổng thanh toán VNPay hỗ trợ quét VNPAY-QR động từ các ứng dụng ngân hàng di động, thẻ ATM nội địa và ví điện tử. Sử dụng các lệnh gọi lại Thông báo thanh toán tức thời (IPN) được mã hóa xác thực HMAC-SHA512 với quy trình xử lý webhook chống trùng lặp (idempotent).
- **Value**: Tạo điều kiện thuận lợi cho các giao dịch không tiền mặt mượt mà, phù hợp với người dùng trẻ tuổi đồng thời bảo vệ người bán khỏi gian lận thanh toán.

### Feature 7: Dynamic HMAC-SHA256 Single-Use QR Token & In-Store Web Scanner (Mã QR một lần mã hóa động HMAC-SHA256 & Trình quét web tại cửa hàng)
- **Function**: Tạo mã QR được ký mã hóa động chứa mã thông báo HMAC-SHA256 được dẫn xuất từ mã định danh đơn hàng, danh tính người dùng, mã ngẫu nhiên (`nonce`) và thời gian hết hạn (`pickup_deadline`). Chủ cửa hàng quét mã QR của khách hàng thông qua máy quét camera web tích hợp sẵn (`html5-qrcode`).
- **Value**: Xác thực chữ ký trong thời gian thực, đánh dấu mã thông báo đã được sử dụng ngay lập tức và loại bỏ việc chia sẻ ảnh chụp màn hình hoặc các cuộc tấn công phát lại (gian lận nhận trùng lặp).

### Feature 8: Verified Reviews, Green Points & Environmental Impact Tracker (Đánh giá xác thực, Điểm Xanh & Trình theo dõi tác động môi trường)
- **Function**: Chỉ những người dùng có giao dịch nhận hàng qua quét QR trực tiếp tại cửa hàng đã được xác minh mới có thể gửi đánh giá và xếp hạng từ 1 đến 5 sao. Đồng thời, nền tảng quy đổi các bữa ăn được giải cứu thành các chỉ số sinh thái được xác thực (khoảng 2.5 kg $CO_2e$ được tiết kiệm cho mỗi 1 kg thực phẩm được giải cứu) và cộng Điểm Xanh (Green Points) vào tài khoản người dùng để đổi voucher trên Bảng xếp hạng Xanh công khai.
- **Value**: Gam hóa hành vi tiêu dùng bền vững và cung cấp báo cáo môi trường rõ ràng cho các cửa hàng tham gia.

---

## 4. Danh mục Tính năng Trí Tuệ Nhân Tạo (AI Features - Powered by Google Gemini 2.5 Flash)

### AI Feature 1: Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard (Trợ lý đa phương thức đăng nhanh hàng loạt & Bộ bảo vệ dị ứng 2 tầng)
- **Function**: Giải quyết điểm nghẽn vận hành quan trọng khi nhân viên bếp bận rộn không có thời gian gõ biểu mẫu thủ công vào cuối ca. Người bán chỉ cần ghi âm một đoạn clip giọng nói trò chuyện ngắn (ví dụ: *"Còn 5 cơm sườn chả, 3 bún thịt nướng xả từ giờ đến 3h chiều nhé"*):
  1. **Native Multimodal Audio Ingestion (Nhập âm thanh đa phương thức nguyên bản)**: Gửi trực tiếp tệp âm thanh thô tới Gemini 2.5 Flash mà không qua phần mềm chuyển đổi giọng nói thành văn bản (STT) trung gian, diễn giải chính xác các phương ngữ vùng miền Việt Nam, từ lóng (*"bốn lăm cành"*, *"bì chả"*) và các sắc thái ẩm thực.
  2. **Menu-Catalog Grounding (Neo ngữ cảnh theo danh mục thực đơn)**: Gemini so sánh tên món ăn được trích xuất với Danh mục Thực đơn Cơ bản của cửa hàng trong ngữ cảnh câu lệnh để gán `matched_menu_id`, tự động kế thừa hình ảnh món ăn đã xác thực, giá bán lẻ tiêu chuẩn và kích hoạt các mức giảm giá theo quy tắc.
  3. **Two-Tier Allergen Guard (14 EU FIC Standards) (Bộ lọc dị ứng 2 tầng theo chuẩn 14 chất gây dị ứng của EU)**:
     - **Explicit Detection (Phát hiện rõ ràng)**: Nắm bắt các chất gây dị ứng được người bán nêu trực tiếp bằng giọng nói (ví dụ: *"chứa đậu phộng nghiền"*).
     - **Inferred Culinary Knowledge (Kiến thức ẩm thực suy luận)**: Tự động suy luận các chất gây dị ứng ẩn dựa trên công thức truyền thống Việt Nam: ví dụ, Cơm sườn chả chứa Trứng (trong chả trứng hấp) và Cá (trong nước mắm); Bún thịt nướng chứa Đậu phộng và Nước mắm; Bánh mì chứa Gluten.
     - **Local Dietary Notes (Ghi chú chế độ ăn uống địa phương)**: Gắn cờ các sở thích mang tính văn hóa quan trọng (`dietary_notes`): Sự hiện diện của hành lá/hành tỏi (Có mỡ hành), mức độ cay, dưa chua và trạng thái món chay.
  4. **Batch Extraction & Server-Time Grounding (Trích xuất hàng loạt & Neo thời gian máy chủ)**: Trích xuất đồng thời nhiều món ăn dư thừa (`List[SurplusDishItem]`) và chuyển đổi các biểu thức thời gian tương đối (*"từ giờ đến 3 giờ chiều"*) thành dấu thời gian chuẩn ISO 8601 tuyệt đối bằng cách sử dụng `current_server_time` được cung cấp.
- **Value**: Giảm thời gian đăng từ 3 phút cho mỗi món xuống dưới 3 giây cho toàn bộ lô thực đơn, đồng thời ngăn ngừa các phản ứng dị ứng nguy hiểm đến tính mạng thông qua các cảnh báo y tế chuẩn hóa.

### AI Feature 2: Smart Food Recommendation & Natural Language Semantic Search (Gợi ý món ăn thông minh & Tìm kiếm ngữ nghĩa bằng ngôn ngữ tự nhiên)
- **Function**: Cung cấp khả năng khám phá bữa ăn dư thừa được cá nhân hóa, nhận biết ngữ cảnh thông qua kiến trúc kết hợp 3 lớp mạnh mẽ:
  1. **Layer 1 - Hard Safety Invariant (SQL & PostGIS) (Lớp 1 - Bất biến an toàn cứng)**: Lọc các món ăn có sẵn trong bán kính 1–3 km và loại trừ nghiêm ngặt 100% các món ăn khớp với hồ sơ dị ứng y tế của người tiêu dùng (`excluded_allergens` trong `user_preferences`). Tính an toàn y tế được đảm bảo nghiêm ngặt ngay tại cấp độ truy vấn cơ sở dữ liệu và không bao giờ ủy quyền cho việc sinh văn bản AI xác suất.
  2. **Layer 2 - Multi-Factor Heuristic Scoring (Lớp 2 - Chấm điểm heuristic đa yếu tố)**: Xếp hạng các món ăn ứng viên bằng cách sử dụng công thức tổng hợp trọng số khách quan:
     $$\text{Score} = (0.40 \times \text{Proximity}) + (0.30 \times \text{Discount Depth \& Time Urgency}) + (0.30 \times \text{Taste Profile Match})$$
     Ưu tiên các Giao dịch Giải cứu Cấp bách bước vào 30 phút cuối của đợt xả hàng giảm giá 70% để ngăn chặn thực phẩm hết hạn.
  3. **Layer 3 - Generative AI Personalization (Lớp 3 - Cá nhân hóa bằng AI tạo sinh)**: 3 món ăn ứng viên được xếp hạng hàng đầu và hồ sơ khẩu vị của người dùng được gửi tới Gemini 2.5 Flash để tổng hợp một lời giải thích ngắn gọn, mang tính thuyết phục cảm xúc (20–30 từ) hiển thị trên thẻ giao diện người dùng (ví dụ: *"Gợi ý cho bạn: Bạn thường xuyên thích các món súp mì nóng vào buổi trưa. Quán Phở Bắc cách 350m đang cung cấp ưu đãi thanh lý 67% chỉ với 18.000 VND, còn 2 phần đến 13:30 — cam kết hoàn toàn không chứa đậu phộng theo sở thích của bạn!"*).
  4. **Conversational Semantic Search (Tìm kiếm ngữ nghĩa hội thoại)**: Cho phép người tiêu dùng truy vấn bằng ngôn ngữ tự nhiên (ví dụ: *"Tìm cho tôi một món súp ấm áp dễ chịu dưới 30k ở gần đây"*), trong đó Gemini trích xuất ý định, ngân sách và các ràng buộc chế độ ăn uống để lọc cơ sở dữ liệu PostGIS.
- **Value**: Tối đa hóa tỷ lệ chuyển đổi, loại bỏ sự mệt mỏi khi lướt tìm kiếm cho những người dùng đang đói, đồng thời nhanh chóng giải phóng hàng hóa dễ hỏng trước khi nhà bếp đóng cửa mà không làm ảnh hưởng đến sức khỏe người tiêu dùng.

---

## 5. Khảo sát Ứng dụng Hiện tại & Cơ hội Phát triển (Existing App Survey)

### 5.1. Khảo sát Yindii (Đông Nam Á)
- **Mô hình Yindii**:
  - Người dùng lựa chọn giữa 2 phương thức: Mua hàng khô (`Dry goods`) hoặc Mua suất ăn dư (`Surplus meals`).
  - Hỗ trợ cả 2 hình thức: Tự đến lấy (`Yindii Pickup`) hoặc Giao hàng tận nơi (`Yindii Drop`).
  - Động cơ gợi ý món: Gợi ý các món ăn ngẫu nhiên cho từng bữa (`Recommend random foods for each meal`).
- **Sự khác biệt của EcoBite**:
  - **Tập trung 100% vào Pickup Surplus Meals**: Chỉ phục vụ hình thức đến nhận trực tiếp tại quán đối với món ăn dư thừa trong ngày (không làm hàng khô, không giao hàng đường dài để đảm bảo thực phẩm nóng hổi và không phát sinh rác thải bao bì vận chuyển).
  - **Cá nhân hóa bằng AI**: Gợi ý món ăn thông minh theo khẩu vị cá nhân, vị trí GPS và lịch sử đơn hàng bằng Gemini 2.5 Flash, loại trừ hoàn toàn yếu tố gợi ý ngẫu nhiên thiếu ngữ cảnh.

### 5.2. Khảo sát Too Good To Go (Âu Mỹ)
- **Ưu điểm**:
  - Quy trình từ tìm kiếm đến nhận thực phẩm rõ ràng, tập trung vào thực phẩm dư thừa và giá ưu đãi sâu.
  - Có tìm kiếm theo khu vực, bộ lọc và thông tin khung giờ nhận món rõ ràng; khơi gợi ý thức bảo vệ môi trường.
- **Nhược điểm lớn khi áp dụng tại Việt Nam**:
  - Mô hình "Túi mù" (Surplus Mystery Bag / Surprise Bag) ngẫu nhiên không phù hợp với văn hóa ẩm thực Việt Nam (người dùng kén chọn món ăn, nhiều thói quen kiêng kỵ như không ăn hành mỡ, ăn chay vào ngày rằm, dị ứng hải sản/đậu phộng).
- **Cơ hội Đột phá của EcoBite**:
  - **Minh bạch 100% (No Mystery Bags)**: Bán từng món ăn cụ thể, niêm phong rõ ràng, có hình ảnh chất lượng cao kế thừa từ thực đơn gốc.
  - **Cảnh báo Dị ứng 2 Tầng**: Rà soát dị ứng và ghi chú khẩu vị văn hóa Việt Nam (hành, tỏi, cay, chua).
  - **Bản địa hóa thanh toán**: Tích hợp VNPay (quét VNPAY-QR qua app ngân hàng) và tiền tệ Việt Nam Đồng (VNĐ).
  - **Luật giảm giá giờ chót minh bạch**: Người dùng chủ động canh khung giờ giảm 70% để tiết kiệm tối đa.

---

## 6. User Stories & Acceptance Criteria

### US-01: Authentication & Merchant KYC Onboarding
**As a** Chủ cơ sở kinh doanh F&B,
**I want** Đăng ký tài khoản đối tác và nộp giấy phép ATVSTP cùng thông tin kinh doanh,
**So that** Quản trị viên duyệt hồ sơ và cấp quyền cho tôi đăng bán thực phẩm dư thừa trên nền tảng.
- **Acceptance Criteria**:
  - *Given*: Chủ quán cung cấp đầy đủ: Tên quán, địa chỉ, toạ độ GPS, SĐT và ảnh Giấy chứng nhận ATVSTP.
  - *When*: Bấm nút "Gửi hồ sơ kiểm duyệt".
  - *Then*: Trạng thái cửa hàng chuyển sang `PENDING`. Tài khoản bị chặn quyền tạo món cho đến khi Admin chuyển trạng thái sang `APPROVED`.

### US-02: Base Menu Catalog & Surplus Dish Management
**As a** Đối tác cửa hàng đã được duyệt KYC,
**I want** Duy trì danh mục thực đơn chuẩn (`menu_items`) và tạo món dư (`dishes`) cuối ca từ danh mục này,
**So that** Món ăn dư thừa tự động kế thừa ảnh đại diện chất lượng cao và giá gốc chuẩn mà không phải nhập lại từ đầu.
- **Acceptance Criteria**:
  - *Given*: Quán đã khởi tạo món "Bánh Croissant Bơ Pháp" (giá gốc 40.000đ, ảnh chuẩn) trong `menu_items`.
  - *When*: Cuối ca, chủ quán chọn món này để tạo món dư, nhập số lượng 8 và khung giờ nhận 20:00 - 21:30.
  - *Then*: Món ăn mới xuất hiện trong bảng `dishes` với đầy đủ ảnh chuẩn, giá gốc 40.000đ và giá giải cứu 20.000đ.

### US-03: Rule-Based Time-Shift Discounting Engine
**As a** Đối tác tiệm bánh,
**I want** Món ăn tự động áp dụng giá giải cứu 50% trong ca và tự động hạ sâu 70% trong 30 phút cuối trước khi đóng cửa,
**So that** Kích thích khách mua nhanh và thanh lý sạch 100% hàng tồn kho dễ hỏng.
- **Acceptance Criteria**:
  - *Given*: Món bánh mì có giá gốc 30.000đ, mở bán từ 19:30 - 21:00.
  - *When*: Thời gian thực của hệ thống bước qua mốc 20:30 (30 phút cuối).
  - *Then*: Giá hiển thị tự động chuyển từ 15.000đ (giảm 50%) sang 9.000đ (giảm 70%) kèm đồng hồ đếm ngược trực tiếp trên UI.

### US-04: Location-Based Search & PostGIS Radar Discovery
**As a** Người tiêu dùng,
**I want** Mở bản đồ radar định vị GPS để xem các món ăn dư thừa đang giảm giá quanh tôi trong bán kính 1–5 km,
**So that** Tôi chọn được món ăn nóng hổi trong khoảng cách đi bộ ngắn nhất.
- **Acceptance Criteria**:
  - *Given*: Người dùng bật định vị GPS trên trình duyệt di động.
  - *When*: Người dùng mở tab Bản đồ Radar trên app EcoBite.
  - *Then*: Bản đồ Leaflet tải danh sách các quán trong bán kính 3km thông qua PostGIS `ST_DWithin`, hiển thị ghim màu và popup thông tin món cùng mức giảm giá.

### US-05: Inventory Anti-Overselling Lock & Order Placement
**As a** Người tiêu dùng đang săn suất ăn cuối cùng,
**I want** Đặt hàng với cơ chế khóa tồn kho nguyên tử cấp cơ sở dữ liệu,
**So that** Đơn hàng của tôi không bị tranh chấp hoặc rơi vào tình trạng bán vượt quá số lượng tồn (zero over-selling).
- **Acceptance Criteria**:
  - *Given*: Món ăn chỉ còn đúng 1 suất (`remaining_quantity = 1`) và có 2 người cùng bấm mua đồng thời.
  - *When*: Câu lệnh `UPDATE dishes SET remaining_quantity = remaining_quantity - 1 WHERE remaining_quantity >= 1` được thực thi.
  - *Then*: Chỉ đúng 1 người nhận được mã đơn hàng `CONFIRMED`, người thứ hai nhận phản hồi `409 Conflict` báo hết hàng.

### US-06: Seamless Cashless Checkout (VNPay Payment Gateway)
**As a** Người tiêu dùng,
**I want** Thanh toán không tiền mặt bằng cách quét mã VNPAY-QR từ ứng dụng ngân hàng di động,
**So that** Giao dịch được xử lý liền mạch, an toàn và tức thì.
- **Acceptance Criteria**:
  - *Given*: Người dùng chọn phương thức thanh toán VNPay tại màn hình Checkout.
  - *When*: Bấm "Thanh toán", hệ thống chuyển hướng đến cổng VNPay và người dùng quét QR hoàn tất chuyển khoản.
  - *Then*: VNPay gửi webhook IPN có chữ ký HMAC-SHA512 về server; hệ thống xử lý idempotent, đổi trạng thái đơn sang `PAID` và hiển thị mã nhận món.

### US-07: Dynamic HMAC-SHA256 Single-Use QR Token & In-Store Web Scanner
**As a** Nhân viên cửa hàng,
**I want** Dùng camera trình duyệt quét mã QR động của khách khi khách đến lấy món,
**So that** Xác thực chữ ký điện tử hợp lệ, hoàn tất đơn hàng và chống gian lận quét lại (Replay Attack).
- **Acceptance Criteria**:
  - *Given*: Khách hàng xuất trình mã QR động chứa chữ ký HMAC-SHA256 trong khung giờ nhận món.
  - *When*: Nhân viên quét mã bằng máy quét camera web (`html5-qrcode`).
  - *Then*: Hệ thống xác thực chữ ký thành công, đánh dấu `is_used = true`, đổi trạng thái đơn sang `COMPLETED`. Nếu khách quét lại lần 2, hệ thống từ chối ngay lập tức.

### US-08: Verified Reviews, Green Points & Environmental Impact Tracker
**As a** Người tiêu dùng đã hoàn tất đơn hàng,
**I want** Nhận Điểm Xanh (tương ứng với lượng $CO_2$ giảm phát thải) và viết đánh giá cho món ăn,
**So that** Tích luỹ điểm đổi voucher và chia sẻ đánh giá thực tế cho cộng đồng.
- **Acceptance Criteria**:
  - *Given*: Đơn hàng chuyển sang trạng thái `COMPLETED` sau khi quét QR.
  - *When*: Hệ thống hoàn tất giao dịch.
  - *Then*: Tài khoản khách được cộng Điểm Xanh (quy đổi 2.5 kg $CO_2e$ cho mỗi suất ăn) và form đánh giá 1–5 sao kèm ảnh chụp được mở ra.

### US-09: Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard (AI Feature 1)
**As a** Chủ quán bận rộn cuối ca,
**I want** Gửi 1 đoạn ghi âm giọng nói ngắn liệt kê nhiều món ăn dư thừa (*"Còn 5 cơm sườn chả, 3 bún thịt nướng xả từ giờ đến 3h chiều"*),
**So that** Gemini 2.5 Flash bóc tách hàng loạt, khớp thực đơn gốc để lấy ảnh và giá, tự động gắn cảnh báo dị ứng 2 tầng (Explicit + Inferred) để tôi đăng bài chỉ trong 3 giây.
- **Acceptance Criteria**:
  - *Given*: File ghi âm giọng nói và `current_server_time = 13:55:00`.
  - *When*: Gửi tới `POST /api/v1/ml/parse-dish-nlp`.
  - *Then*: Trả về `QuickPostExtractionResponse` gồm danh sách món đã khớp `matched_menu_id`, cảnh báo dị ứng Trứng/Cá/Đậu phộng và thời gian tuyệt đối `13:55:00 - 15:00:00`. Chủ quán bấm 1 nút đăng toàn bộ lên CSDL.

### US-10: Smart Food Recommendation & Conversational Semantic Search (AI Feature 2)
**As a** Người tiêu dùng chuẩn bị ăn trưa,
**I want** Nhận gợi ý món ăn thông minh theo ngữ cảnh (gần vị trí, loại trừ dị ứng của tôi) kèm lý do giải thích tự nhiên, hoặc gõ câu tự nhiên để tìm kiếm,
**So that** Tôi chọn được món ăn phù hợp nhất mà không tốn công tìm kiếm.
- **Acceptance Criteria**:
  - *Given*: Người dùng có hồ sơ dị ứng Đậu phộng trong `user_preferences`.
  - *When*: Gọi `GET /api/v1/recommendations/personalized?lat=10.77&lng=106.70`.
  - *Then*: Hệ thống SQL lọc cứng loại bỏ toàn bộ món có đậu phộng, chọn Top 3 món có điểm cao nhất theo công thức Heuristic, và Gemini sinh lý do ngắn gọn (20–30 từ) hiển thị trên giao diện.
