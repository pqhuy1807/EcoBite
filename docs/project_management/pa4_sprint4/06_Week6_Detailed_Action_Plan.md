# 📅 Kế hoạch Hành động Chi tiết Tuần 6 (`25/11/2026 – 29/11/2026`)

> **Bối cảnh & Mục tiêu Kép**:
> - **Mốc PA4 (Release 0.3)**: Internal Deadline **23:59 Thứ Sáu `27/11/2026`** · Nộp Moodle **Thứ Bảy `28/11/2026`** (tag `v0.3.0-pa4`).
> - **Cơ cấu 2 Cụm Song song (Re-balanced Allocation)**:
>   - **Cụm FE + QA PA4 (`Võ Ngọc Thịnh` + `Đàng Thế Tony`)**: Đưa **Tony lên hỗ trợ trực tiếp Frontend cùng Thịnh** để đóng **100% giao diện Core F1–F8 + Vitest + QA Gate** trong tuần này; sau khi chốt PA4 (`28–29/11`), cả 2 cùng nghiên cứu UI & thiết kế bộ kiểm thử chuyên sâu cho PA5.
>   - **Cụm AI Baseline & Evaluation (`Phùng Quốc Huy` + `Đặng Trọng Phúc`)**: Vì Backend Core F1–F8 đã đạt ~95%, **Huy chủ trì AI Feature 1** và **Phúc chủ trì AI Feature 2** — mỗi người hoàn thiện **1 baseline chạy được end-to-end (demo qua Swagger/script)** kèm **tài liệu thiết kế chi tiết & khung đánh giá hiệu quả AI (Golden Dataset + Metrics)** để mở khóa toàn tốc cho Sprint 5 (`29/11`).

---

## 1. Quy tắc Git Hygiene & Tách nhánh Bắt buộc Trước Khi Bắt đầu

1. **Đồng bộ nhánh local**: Cả nhóm chạy `git pull origin dev` về cùng mốc mới nhất (`c04eca0`).
2. **Bảo vệ Release 0.3 (`v0.3.0-pa4`)**:
   - Không merge code AI PA5 vào nhánh nộp PA4 (`main`). Cần rà soát/tách 3 commit AI nháp (`a3c0252`, `9913f07`, `c04eca0`) ra nhánh AI riêng trước khi tag `v0.3.0-pa4`.
3. **Phân nhánh 1-1 trong Tuần 6**:
   - **Thịnh**: `feat/fe-vnpay-and-store-orders`
   - **Tony**: `feat/fe-f8-gamification-reviews` (xong FE thì mở `test/pa4-qa-gate`)
   - **Huy**: `feat/ai-1-quick-post`
   - **Phúc**: `fix/vnpay-sandbox` (merge vào `dev` trước) → `feat/ai-2-recommendation`

---

## 2. Phân công Chi tiết Từng Thành viên Trong Tuần 6

### 🎨 Cụm 1: Đóng 100% Frontend PA4 & Chuẩn bị PA5 (`Võ Ngọc Thịnh` + `Đàng Thế Tony`)

> *Nguyên tắc chia file để Thịnh và Tony code song song **không xung đột Git**: Thịnh sở hữu `page.tsx`, `orders/vnpay-return/page.tsx`, `orders/page.tsx` (luồng VNPay & QR), `store/verify-qr/page.tsx`, `Navbar.tsx`; Tony sở hữu toàn bộ file mới của Feature 8 (`gamification.service.ts`, `review.service.ts`, `green-points/page.tsx`, `components/ReviewModal.tsx`) và chỉ gắn 1 nút mở `ReviewModal` vào `orders/page.tsx` sau khi Thịnh merge `EC4-12`.*

#### 👤 1. Võ Ngọc Thịnh — Frontend Lead (VNPay Flow + Store Orders + Vitest Phần 1)
1. **Dọn `package.json` (`EC4-10` cleanup)**:
   - Xóa dòng `"test"` bị trùng trong `frontend/package.json`, giữ `"test": "vitest run --passWithNoTests"`.
2. **Hoàn thiện luồng thanh toán VNPay (`EC4-12` — Ưu tiên P0)**:
   - `frontend/src/app/page.tsx`: Khi đặt đơn với `payment_method === 'VNPAY'`, gọi `POST /orders` → `paymentService.createVnpayUrl(order.id)` → redirect sang `payment_url` (có loading state & fallback toast về `/orders` nếu tạo URL lỗi).
   - Tạo `frontend/src/app/orders/vnpay-return/page.tsx`: bọc `useSearchParams()` trong `<Suspense>`, gọi `paymentService.verifyVnpayReturn(queryParams)`, hiển thị kết quả rõ ràng (thành công → nút đi tới `/orders` lấy QR; thất bại/sai chữ ký → thông báo hoàn kho & nút quay lại).
   - Cập nhật `frontend/src/app/orders/page.tsx`:
     - Với đơn `VNPAY` còn `PENDING`: **khóa nút "Xem mã QR"** (khớp Backend Guard) và hiện nút **"Thanh toán VNPay ngay"**.
     - Chỉ mở Modal QR khi `payment_method === 'COD'` hoặc `payment_status === 'PAID'`.
3. **Hoàn thiện Store Orders & Navigation (`EC4-13` phần Store)**:
   - `frontend/src/app/store/verify-qr/page.tsx`: bổ sung bảng danh sách đơn hàng của quán cần giao (`CONFIRMED` / `READY_FOR_PICKUP` / `COMPLETED`) bên cạnh khung quét QR.
   - `frontend/src/components/ui/Navbar.tsx`: đảm bảo điều hướng đầy đủ theo role (`/green-points` cho `CONSUMER`, `/store/menu`, `/store/dishes`, `/store/verify-qr` cho `STORE_PARTNER`, `/admin` cho `ADMIN`).
4. **Vitest Frontend Phần 1 (`EC4-14`)**:
   - Viết test tại `frontend/__tests__/components/` cho luồng Checkout VNPay & QR Guard ở `/orders`.

#### 👤 2. Đàng Thế Tony — FE Support (Feature 8 UI) & QA Lead (PA4 Quality Gate)
1. **Triển khai trọn bộ UI Feature 8 (`EC4-13` phần Consumer — File độc lập)**:
   - Tạo `frontend/src/services/gamification.service.ts` (`getMyGreenPoints`, `listVouchers`, `getMyVouchers`, `redeemVoucher`) và `frontend/src/services/review.service.ts` (`createReview`, `getStoreReviews`), bổ sung DTO tương ứng trong `frontend/src/types/api.ts`.
   - Dựng trang **Ví Điểm Xanh & Đổi Voucher (`frontend/src/app/green-points/page.tsx`)**:
     - Header thống kê: `balance_points`, `total_co2_saved_kg`, `total_meals_saved`, huy hiệu `rank_title`.
     - Tab **Đổi Voucher** (`GET /vouchers`): hiển thị điều kiện điểm, hạn dùng, nút đổi 1 chạm (`POST /vouchers/{id}/redeem`), vô hiệu hóa khi không đủ điểm, cập nhật số dư ngay qua React Query `invalidateQueries`.
     - Tab **Voucher của tôi** (`GET /vouchers/me`) & **Lịch sử Điểm Xanh** (`recent_ledger`).
   - Tạo component **`frontend/src/components/ReviewModal.tsx`**: chọn 1–5 sao, ô nhận xét, gọi `POST /orders/{order_id}/review`, xử lý `409 Conflict` (đã đánh giá) thân thiện; tích hợp vào nút *"Đánh giá"* của đơn `COMPLETED` ở `frontend/src/app/orders/page.tsx`.
2. **Vitest Frontend Phần 2 (`EC4-14`)**:
   - Viết test tại `frontend/__tests__/components/` cho `ReviewModal` và trang/luồng đổi Voucher `/green-points` → đảm bảo `npm run lint`, `npm run type-check`, `npm run test`, `npm run build` đều exit `0`.
3. **Chốt PA4 QA Gate (`EC4-15`)**:
   - Bổ sung `backend/tests/integration/test_api_payments.py` (IPN hợp lệ, sai chữ ký `97`, sai tiền `04`, gọi đồng thời 2 IPN không ghi trùng, hoàn kho đúng 1 lần khi thất bại) + test benchmark xác thực QR `< 2s`.
   - Chạy xác nhận xanh toàn bộ Gate trước khi tag `v0.3.0-pa4`: `ruff check`, `ruff format --check`, `mypy app/`, `pytest tests/ -v`, `pre-commit run --all-files`.

#### 🔬 Nhiệm vụ Nghiên cứu & Chuẩn bị Test PA5 cho Thịnh + Tony (`28/11 – 29/11`)
Sau khi đóng xong FE & PA4, 2 bạn phối hợp chuẩn bị tài liệu đầu vào cho Sprint 5:
- **Thịnh (FE PA5 Design)**:
  - Nghiên cứu `MediaRecorder` Web API (ghi âm trình duyệt xuất `.webm`/`.m4a`, giới hạn kích thước/thời lượng, fallback nhập text nếu không có mic) để gọi `POST /api/v1/ml/parse-dish-nlp`.
  - Phác thảo wireframe/component specs cho: (a) **Quick-Post Draft Cards Editor** có badge màu phân biệt dị ứng `EXPLICIT` (đỏ) vs `INFERRED` (vàng) cho phép chủ quán duyệt/sửa trước khi gọi `POST /dishes/batch`, (b) **Smart Recommendation Carousel + Semantic Search Bar** trên `/`, và (c) trang **`/profile/preferences`** (chọn 14 chất gây dị ứng EU FIC + ngân sách + khẩu vị).
- **Tony (QA PA5 AI Safety & Test Plan)**:
  - Thiết kế kế hoạch kiểm thử AI tại `docs/project_management/pa5_sprint5/03_PA5_AI_Test_Plan.md`:
    - **Allergen Hard Invariant Suite** (0% rò rỉ dị ứng trên mọi tổ hợp `excluded_allergens` có dấu/không dấu, đơn/đa dị ứng, kể cả qua Semantic Search).
    - **Resilience & Fallback Tests** (Gemini timeout, API key rỗng, output lỗi schema → hệ thống không crash 500).
    - **SLA Benchmarks** (`Quick-Post < 3s`, `Recommendation < 2.5s`) và kế hoạch kéo test coverage toàn dự án đạt `>= 80%`.

---

### 🤖 Cụm 2: Baseline Chạy được + Nghiên cứu & Đánh giá AI-1 & AI-2 (`Phùng Quốc Huy` + `Đặng Trọng Phúc`)

#### 👤 3. Phùng Quốc Huy — AI Lead (AI Feature 1 Baseline & Evaluation) + PM PA4

1. **Hoàn tất Hồ sơ PA4 (PM — `EC4-17`)**:
   - Cập nhật `04_Sprint4_Progress_Tracker.md` & `00_Overall_Roadmap_and_PA_Tracker.md`.
   - Phối hợp cả nhóm hoàn thiện `docs/PA4.md` + xuất `docs/PA4.pdf` + quay Video Demo Release 0.3 trước `23:59` `27/11`.
2. **Xây dựng Baseline chạy được cho AI Feature 1 (`feat/ai-1-quick-post`)**:
   - Refactor bản nháp hiện có cho **đúng tuyệt đối `04_API_Specification.md` & Guardrail #6**:
     - Endpoint chuẩn: `POST /api/v1/ml/parse-dish-nlp` trong `backend/app/api/v1/endpoints/ml.py` (gỡ route test public `/quick-post/allergen-filter/test`).
     - **RBAC bắt buộc**: `Depends(require_roles(UserRole.STORE_PARTNER))` *(sửa lỗi bản nháp đang để `CONSUMER`)*.
     - **Input đa phương thức**: chấp nhận `multipart/form-data` gồm `audio_file` (`.m4a`/`.mp3`/`.wav`/`.webm`, kiểm tra MIME & dung lượng) **hoặc** `text_input` (hỗ trợ test nhanh không cần file âm thanh).
     - **Menu-Catalog Grounding**: tự động lấy danh sách `menu_items` của quán (`store_repo.get_store_by_owner_id` → `menu_repo.list_by_store`) truyền vào prompt; sau khi Gemini trả về, **backend xác thực lại `matched_menu_id`** thuộc đúng quán (nếu không hợp lệ thì set `None` chống hallucination) và tự điền `original_price` kế thừa nếu thiếu.
     - **Server-Time Grounding**: inject `current_server_time` theo múi giờ `Asia/Ho_Chi_Minh` để quy đổi giờ tương đối (*"từ giờ tới 9h tối"*) thành `HH:MM:SS`.
     - **Gemini 2.5 Flash Structured Output**: gọi `google-genai` với `response_schema=QuickPostExtractionResponse` (`app/schemas/nlp.py`), bắt buộc phân loại dị ứng 2 tầng (`EXPLICIT` vs `INFERRED`) theo 14 chuẩn `EUAllergen`.
     - **Unit & Smoke Tests**: `backend/tests/unit/test_quick_post_service.py` (mock Gemini SDK: text, audio bytes, menu grounding, chống bịa `matched_menu_id`, degraded fallback) + chạy thử thành công với Gemini API key thật qua Swagger/script nối sang `POST /api/v1/dishes/batch`.
3. **Nghiên cứu Chuyên sâu & Khung Đánh giá Hiệu quả AI-1 (`docs/project_management/pa5_sprint5/research_ai1_quick_post_eval.md`)**:
   - **Thiết kế chi tiết (Deep-dive)**:
     - Chiến lược Prompt Engineering cho khẩu ngữ/phương ngữ tiếng Việt (*"bốn lăm cành"*, *"cơm sườn bì chả"*, *"mấy hộp bánh mì"*).
     - So sánh kỹ thuật gửi audio trực tiếp inline (`types.Part.from_bytes`) vs Gemini Files API (ngưỡng dung lượng, độ trễ).
     - Chiến lược xử lý thực đơn lớn (menu pruning / top-K retrieval nếu quán có >50 món) và cơ chế kiểm duyệt hậu kỳ (post-validation).
   - **Khung Đánh giá Hiệu quả (Evaluation Framework + Script `ml/eval/eval_ai1_quick_post.py` với Golden Dataset 15–20 mẫu tiếng Việt gồm cả text & audio)**:
     | Chỉ số (Metric) | Cách đo | Ngưỡng Mục tiêu |
     | :--- | :--- | :---: |
     | **Schema Validity Rate** | % output khớp 100% `QuickPostExtractionResponse` không cần retry | `>= 98%` |
     | **Field Extraction Accuracy** | Exact/Normalized Match cho `dish_name`, `quantity`, `pickup_start/end`, `price` | `>= 90%` |
     | **Menu Grounding Accuracy** | Top-1 khớp đúng `matched_menu_id` & tỷ lệ bịa UUID (False Match = `0%`) | `>= 90%` |
     | **Allergen Recall (Ưu tiên An toàn)** | % chất dị ứng thật (cả explicit & implicit món Việt) được AI phát hiện không bỏ sót | `>= 95%` |
     | **2-Tier Source Accuracy** | % gắn đúng nhãn `EXPLICIT` vs `INFERRED` | `>= 85%` |
     | **Latency (P50 / P95) & Cost** | Thời gian phản hồi đầu-cuối (kèm audio upload) & token/chi phí mỗi lượt đăng | `P95 < 3.0s` |

#### 👤 4. Đặng Trọng Phúc — Backend Lead (Vá VNPay PA4 + AI Feature 2 Baseline & Evaluation)

1. **Đóng dứt điểm VNPay PA4 (`EC4-03` cleanup & `EC4-16` — Sáng Thứ Năm `26/11`)**:
   - Vá 4 điểm còn sót trong `payment_service.py` & `payments.py`: (1) URL-encode `urllib.parse.quote_plus(str(value))` trong `_generate_vnpay_hash()`, (2) dùng `settings.VNP_URL` thay vì hardcode, (3) dùng `ZoneInfo("Asia/Ho_Chi_Minh")` (fallback UTC+7) cho `vnp_CreateDate`, (4) lấy `client_ip` từ `Request` & dùng `Depends(require_roles(UserRole.CONSUMER))`.
   - Chạy test E2E 1 lượt trên **VNPay Sandbox thật** (lưu ảnh/log đối soát cho `docs/PA4.md`) và merge vào `dev`.
2. **Xây dựng Baseline chạy được cho AI Feature 2 (`feat/ai-2-recommendation`)**:
   - **`UserPreference` CRUD**:
     - Tạo `backend/app/repositories/preference_repo.py` và thêm `GET /api/v1/users/me/preferences`, `PUT /api/v1/users/me/preferences` vào `backend/app/api/v1/endpoints/users.py` (dùng `app/schemas/user_preference.py`, chuẩn hóa danh sách `excluded_allergens` về canonical keys theo `EUAllergen`).
   - **Layer 1 — SQL Hard Safety Invariant (`Guardrail #7` — sửa đúng hướng)**:
     - Tạo `backend/app/repositories/recommendation_repo.py` thực thi lọc ứng viên **ngay tại tầng SQL Database** (không dùng Python lọc thay cho SQL như `allergen_filter_service.py` cũ):
       - Lọc món `AVAILABLE`, `remaining_quantity > 0`, còn trong `pickup_end`, nằm trong bán kính PostGIS `ST_DWithin` (có fallback portable cho SQLite in-memory khi chạy pytest).
       - **SQL Allergen Hard Filter**: loại trừ 100% món có bất kỳ chất dị ứng nào giao với `UserPreference.excluded_allergens` ngay trong mệnh đề `WHERE` của SQL.
   - **Layer 2 — Multi-Factor Heuristic Scoring (`backend/app/services/recommendation_service.py`)**:
     - Tính điểm tất định (deterministic) trên tập ứng viên đã sạch dị ứng:
       $$\text{Score} = (0.40 \times S_{\text{proximity}}) + (0.30 \times S_{\text{discount\_urgency}}) + (0.30 \times S_{\text{taste\_match}})$$
     - Xếp hạng và chọn Top $K$ (mặc định $K=3$).
   - **Layer 3 — Gemini 2.5 Flash Justification + Baseline Semantic Search**:
     - Endpoint `GET /api/v1/recommendations/personalized?lat=...&lng=...&radius_km=3`: gửi **chỉ Top 3 món đã lọc sạch dị ứng** + tóm tắt khẩu vị cho Gemini sinh `ai_justification` ngắn 20–30 từ (có template fallback deterministic nếu Gemini lỗi/chậm).
     - Endpoint `POST /api/v1/dishes/search-semantic`: nhận câu truy vấn tự nhiên (*"tìm món nước nóng dưới 30k gần đây"*), dùng Gemini Structured Output bóc tách bộ lọc (`max_price`, `categories`, `dietary`, `keywords`) rồi **bắt buộc đẩy qua Layer 1 SQL Allergen Hard Filter** trước khi trả kết quả.
   - **Unit & Integration Tests**: `test_recommendation_service.py` + `test_api_recommendations.py` (chứng minh 0% dị ứng lọt qua ở SQL, đúng công thức điểm, fallback an toàn khi Gemini lỗi).
3. **Nghiên cứu Chuyên sâu & Khung Đánh giá Hiệu quả AI-2 (`docs/project_management/pa5_sprint5/research_ai2_recommendation_eval.md`)**:
   - **Thiết kế chi tiết (Deep-dive)**:
     - Thiết kế chuẩn hóa dữ liệu dị ứng (`EUAllergen` canonical keys + mapping tiếng Việt/đồng nghĩa) và truy vấn SQL tối ưu trên PostgreSQL JSONB (`@>` / `jsonb_array_elements`, GIN index) kết hợp PostGIS GIST index.
     - Phân tích độ nhạy trọng số `(0.40 / 0.30 / 0.30)` và công thức chuẩn hóa `[0, 1]` cho từng thành phần (tránh món cực rẻ nhưng ở xa hoặc sắp hết giờ bị lệch hạng).
     - Cơ chế chống *hallucination* ở Layer 3 (kiểm tra số liệu giá/khoảng cách trong câu bình) & chiến lược cache/fallback.
   - **Khung Đánh giá Hiệu quả (Evaluation Framework + Script `ml/eval/eval_ai2_recommendation.py` với Golden Dataset 15–20 kịch bản user profile + truy vấn ngữ nghĩa)**:
     | Chỉ số (Metric) | Cách đo | Ngưỡng Mục tiêu |
     | :--- | :--- | :---: |
     | **Allergen Leakage Rate (Hard Invariant)** | % món vi phạm `excluded_allergens` xuất hiện trong kết quả (cả Personalized & Semantic) | **Bắt buộc `0.0%`** |
     | **Ranking Quality (`NDCG@3`, `Precision@3`)** | So sánh Top 3 xếp hạng với ground-truth kỳ vọng của từng persona (ăn chay, ngân sách thấp, gần nhà, gấp giờ) | `NDCG@3 >= 0.85` |
     | **Semantic Intent Extraction Accuracy** | % bóc tách đúng `max_budget`, `category`, `dietary` từ câu tự nhiên tiếng Việt | `>= 90%` |
     | **Justification Faithfulness** | % câu bình khớp sự thật DB (giá, % giảm, khoảng cách, không tự hứa sai về dị ứng) & độ dài 20–30 từ | `>= 95%` (`0%` bịa số) |
     | **Latency (P95) & Fallback Latency** | Thời gian phản hồi tổng (có Gemini) và khi Gemini timeout/fallback | `< 2.5s` / `< 300ms` |

---

## 3. Lịch trình Tác chiến Từng Ngày (`25/11 – 29/11/2026`)

| Ngày | Võ Ngọc Thịnh (FE Lead) | Đàng Thế Tony (FE Support + QA) | Phùng Quốc Huy (AI-1 + PM) | Đặng Trọng Phúc (VNPay Fix + AI-2) |
| :--- | :--- | :--- | :--- | :--- |
| **Tối Thứ Tư (`25/11`)** | Pull `dev`; sửa trùng `"test"` ở `package.json`; làm `EC4-12` (VNPay redirect ở `/` + `/orders/vnpay-return`). | Pull `dev`; tạo `gamification.service.ts`, `review.service.ts`, cập nhật `types/api.ts`; dựng khung `/green-points`. | Pull `dev`; cập nhật tracker; tạo nhánh `feat/ai-1-quick-post`; thiết kế prompt + sửa RBAC `STORE_PARTNER` & Menu Grounding. | Vá nốt 4 lỗi VNPay Sandbox (`EC4-03`); chạy thử tạo URL & đối soát chữ ký trên Sandbox thật (`EC4-16`). |
| **Thứ Năm (`26/11`)** | Xong `/orders` (nút thanh toán lại + khóa QR) → merge `EC4-12`; thêm bảng đơn quán ở `/store/verify-qr` + `Navbar.tsx`. | Hoàn thiện `/green-points` (ví điểm, CO₂, đổi voucher 1 chạm) + `ReviewModal.tsx` & gắn vào `/orders`; viết `test_api_payments.py`. | Code xong **Baseline AI-1** (`POST /ml/parse-dish-nlp` hỗ trợ text + audio + Menu Grounding + Server-Time + unit tests) và test với Gemini thật. | Merge fix VNPay vào `dev`; tạo `feat/ai-2-recommendation`; làm `/users/me/preferences` + **Layer 1 SQL Allergen Hard Filter** + **Layer 2 Scoring**. |
| **Thứ Sáu (`27/11`) — *Internal Deadline PA4*** | Viết Vitest phần 1 (VNPay & QR guard); sửa bug UI từ QA; chạy `lint`, `type-check`, `test`, `build` xanh 100%. | Viết Vitest phần 2 (`ReviewModal`, `/green-points`); chạy **Full PA4 Quality Gate** (BE + FE + `pre-commit`); hỗ trợ quay demo. | Hoàn thiện `docs/PA4.md` + `PA4.pdf` + Video Demo Release 0.3; chốt **Baseline AI-1** demo chạy mượt qua Swagger → `POST /dishes/batch`. | Hoàn thiện **Baseline AI-2** (`GET /recommendations/personalized` có Layer 3 Gemini + fallback & `POST /dishes/search-semantic` + unit/integration tests). |
| **Thứ Bảy (`28/11`) — *Nộp PA4*** | Chốt nộp PA4 (`v0.3.0-pa4`); bắt đầu nghiên cứu `MediaRecorder` audio & wireframe UI PA5 (Draft Cards 2-tier allergen + Preferences). | Chốt nộp PA4; bắt đầu soạn `03_PA5_AI_Test_Plan.md` (Allergen Invariant suite, SLA `< 3s`, kế hoạch coverage `>= 80%`). | Nộp Moodle PA4; viết tài liệu nghiên cứu AI-1 + xây **Golden Dataset (15–20 mẫu)** & chạy benchmark script đo chỉ số baseline AI-1. | Tách/dọn nhánh release PA4 sạch; viết tài liệu nghiên cứu AI-2 + xây **Golden Dataset (15–20 kịch bản)** & chạy benchmark script đo `NDCG@3` & `0%` leakage. |
| **Chủ Nhật (`29/11`) — *Sprint 5 Kickoff*** | Hoàn thiện thiết kế FE PA5 & chốt API contract với Huy (AI-1) và Phúc (AI-2). | Hoàn thiện PA5 AI Test Plan & đối chiếu Golden Dataset cùng Huy/Phúc. | **20:30 Họp Sprint 5 Planning**: Demo Baseline AI-1 & trình bày báo cáo đánh giá hiệu quả ban đầu; chốt Sprint 5 Backlog. | **20:30 Họp Sprint 5 Planning**: Demo Baseline AI-2 & trình bày báo cáo đánh giá `0%` Allergen Leakage + `NDCG@3`. |

---

## 4. Tiêu chí Nghiệm thu Cuối Tuần 6 (Exit Criteria)

### A. Chốt PA4 (`27/11 – 28/11`)
- [ ] **100% Frontend Core F1–F8 xong trên `dev`**: `/admin`, `/store/menu`, `/store/dishes`, `/`, `/orders` (VNPay + QR Guard + Review Modal), `/orders/vnpay-return`, `/store/verify-qr` (có bảng đơn quán), `/green-points`.
- [ ] **Full Quality Gate Xanh 100%**:
  - Backend: `ruff check app/`, `ruff format --check app/`, `mypy app/`, `pytest tests/ -v` (bao gồm `test_api_payments.py`).
  - Frontend: `npm run lint`, `npm run type-check`, `npm run test` (Vitest pass các test mới), `npm run build`.
  - Repo: `pre-commit run --all-files` xanh; VNPay Sandbox E2E đã kiểm chứng thực tế.
- [ ] **Hồ sơ nộp PA4**: `docs/PA4.md` + `docs/PA4.pdf` + Video Demo Release 0.3 + tag `v0.3.0-pa4` (sạch code AI PA5).

### B. Chốt Tiền đề PA5 (`29/11`)
- [ ] **AI-1 Baseline (Huy)**: Gọi `POST /api/v1/ml/parse-dish-nlp` (role `STORE_PARTNER`, nhận text/audio) trả về JSON chuẩn `QuickPostExtractionResponse` có `matched_menu_id` khớp DB + dị ứng 2 tầng (`EXPLICIT`/`INFERRED`), kèm báo cáo nghiên cứu & kết quả chạy thử Golden Dataset.
- [ ] **AI-2 Baseline (Phúc)**: Gọi `PUT /users/me/preferences` → `GET /recommendations/personalized` và `POST /dishes/search-semantic` chạy end-to-end với **SQL Allergen Hard Filter (`0%` leakage)**, Heuristic Scoring + Gemini Justification có fallback, kèm báo cáo nghiên cứu & kết quả benchmark ban đầu.
- [ ] **FE + QA PA5 Readiness (Thịnh + Tony)**: Có wireframe/contract UI PA5 rõ ràng và `03_PA5_AI_Test_Plan.md` sẵn sàng triển khai ngay đầu Tuần 7 (`30/11`).
