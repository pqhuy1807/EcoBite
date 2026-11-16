# 🤖 Kế hoạch & Bảng Giao việc PA5 (Sprint 5): AI Intelligence Suite & Go-Live

> **Thời gian chính thức**: Chủ Nhật `29/11/2026` – Thứ Bảy `12/12/2026`
> **Khởi động sớm (Early AI Kickoff)**: Từ Thứ Hai `23/11/2026` (trên nhánh riêng `feat/ai-*`, sau khi Backend Core F1–F8 đã đóng ở Tuần 5)
> **Hạn chót nội bộ PA5**: **23:59 Thứ Sáu, `11/12/2026`** *(nộp Moodle `12/12/2026`)*
> **Mục tiêu Release**: **Release 1.0 (Production / Final Acceptance)** — Hoàn thiện 2 Tính năng AI Gemini 2.5 Flash, UAT toàn diện, đóng gói Docker/Deploy và Video Demo cuối kỳ.

---

## 1. Trọng tâm Kỹ thuật & Guardrails Bắt buộc của PA5

1. **AI Feature 1 — Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard** *(Guardrail #6)*:
   - Endpoint `POST /api/v1/ml/parse-dish-nlp` nhận file ghi âm tiếng Việt (`.m4a`, `.mp3`, `.wav`) hoặc văn bản tự do + `current_server_time`.
   - Gọi Google Gemini 2.5 Flash Structured Output dùng schema `QuickPostExtractionResponse` đã có tại `backend/app/schemas/nlp.py` (14 chất gây dị ứng EU FIC, phân loại rõ `EXPLICIT` và `INFERRED`, gắn `matched_menu_id` từ `menu_items`, thời gian tuyệt đối theo server time).
   - Kết hợp với `POST /api/v1/dishes/batch` (đã có sẵn ở `endpoints/dishes.py`) để chủ quán bấm 1 nút duyệt Draft Cards và đăng hàng loạt trong `< 3 giây`.
2. **AI Feature 2 — Smart Food Recommendation & Semantic Search** *(Guardrail #7 — Allergen Hard Invariant)*:
   - **Layer 1 (SQL PostGIS Hard Filter)**: Bắt buộc lọc cứng tại SQL loại trừ 100% món chứa chất gây dị ứng trong `UserPreference.excluded_allergens` — **không lọc bằng Python hay phó thác cho AI**.
   - **Layer 2 (Multi-Factor Heuristic Scoring)**:
     $$\text{Score} = (0.40 \times \text{Proximity}) + (0.30 \times \text{Discount Depth \& Time Urgency}) + (0.30 \times \text{Taste Profile Match})$$
   - **Layer 3 (Gemini 2.5 Flash Justification)**: Sinh lời giải thích ngắn 20–30 từ cho Top 3 món đã lọc sạch dị ứng.
   - `POST /api/v1/dishes/search-semantic`: Bóc tách ý định tìm kiếm tự nhiên (ngân sách, loại món, ngữ cảnh) sang bộ lọc PostGIS + Allergen Hard Filter.
3. **Bổ sung Hồ sơ Dị ứng & Khẩu vị Người dùng (`UserPreference`)**:
   - Endpoints `GET /api/v1/users/me/preferences` & `PUT /api/v1/users/me/preferences` (dùng `schemas/user_preference.py` đã có) + trang cài đặt khẩu vị/dị ứng trên Frontend.

---

## 2. Bảng Giao việc Dự kiến Sprint 5 (1-1 Assignee Rule)

| Jira ID | Task / Story | Assignee | Reviewer | Pts | Dự kiến hoàn tất | Phạm vi & Deliverables |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **EC5-01** | `QuickPostService` (Gemini 2.5 Flash Native Audio + Menu Grounding + 2-Tier Allergen) | Huy | Phúc | 5 | `02/12` | `backend/app/services/quick_post_service.py`, `endpoints/ml.py` (`POST /ml/parse-dish-nlp`), unit test mock Gemini SDK (`< 3s` SLA). |
| **EC5-02** | `UserPreference` CRUD & Layer 1 SQL PostGIS Allergen Hard Filter | Phúc | Tony | 4 | `02/12` | `preference_repo.py`, `endpoints/users.py` (`/me/preferences`), SQL filter loại trừ `excluded_allergens` trong `recommendation_repo.py`. |
| **EC5-03** | Layer 2 Heuristic Scoring, Layer 3 Gemini Justification & Semantic Search | Huy | Phúc | 4 | `04/12` | `recommendation_service.py`, `endpoints/recommendations.py` (`GET /recommendations/personalized`, `POST /dishes/search-semantic`). |
| **EC5-04** | Frontend Voice Quick-Post UI & Draft Cards Editor (`/store/dishes`) | Thịnh | Huy | 4 | `05/12` | Component ghi âm/upload audio (`MediaRecorder`), hiển thị Draft Cards kèm badge cảnh báo dị ứng 2 tầng (`EXPLICIT`/`INFERRED`) và nút đăng hàng loạt `POST /dishes/batch`. |
| **EC5-05** | Frontend Smart Recommendations, Semantic Search & Allergen Profile (`/profile/preferences`) | Thịnh | Phúc | 4 | `06/12` | Thanh tìm kiếm ngữ nghĩa + Top 3 Gợi ý AI trên `/`; trang cấu hình dị ứng & khẩu vị cho Consumer. |
| **EC5-06** | Bộ Test An toàn Dị ứng (Allergen Invariant 100%) & Benchmark AI `< 3s` | Tony | Huy | 4 | `08/12` | `tests/integration/test_allergen_invariant.py`, `test_api_ml.py`, `test_api_recommendations.py`; kiểm chứng coverage toàn dự án `>= 80%`. |
| **EC5-07** | UAT Toàn hệ thống, Docker Packaging, Tài liệu Người dùng & Báo cáo PA5 + Video Go-Live | Cả nhóm *(Huy tổng hợp)* | Cả nhóm | 5 | `11/12` | Nghiệm thu full E2E trên Docker Compose, hoàn tất `docs/PA5.md` / `PA5.pdf` và Video Demo Release `1.0`. |
