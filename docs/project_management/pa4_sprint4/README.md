# 📁 Quản lý Sprint 4 & Dự án PA4 (`docs/project_management/pa4_sprint4/`)

> ⬅️ Quay về [Bảng Tổng hợp Toàn Dự án PA1–PA5](../00_Overall_Roadmap_and_PA_Tracker.md) | [Trung tâm Quản lý Dự án](../README.md)

Thư mục này là trung tâm điều phối công việc, phân công 1-1 và theo dõi tiến độ cho **Project Assignment 4 (Sprint 4: `16/11/2026 – 28/11/2026`)** của nhóm **Group 05 — EcoBite Platform**.

## Danh mục Tài liệu

| File | Mục đích | Đối tượng / Tần suất cập nhật |
| :--- | :--- | :--- |
| [`01_PA4_Master_Execution_Plan.md`](./01_PA4_Master_Execution_Plan.md) | Lộ trình tổng thể 2 tuần PA4 (3 Backend xong Core Tuần 5; Frontend xong Core trong 2 tuần; Tuần 6 QA + Báo cáo PA4 + Khởi động sớm AI). | Cả nhóm / Chốt đầu Sprint 4 |
| [`02_Week5_Detailed_Action_Plan.md`](./02_Week5_Detailed_Action_Plan.md) | Kế hoạch tác chiến chi tiết từng ngày cho **Tuần 5 (`16/11 – 22/11/2026`)**. | Cả nhóm / Theo dõi hàng ngày |
| [`03_Task_Assignment_Jira_Backlog.md`](./03_Task_Assignment_Jira_Backlog.md) | Bảng giao việc chi tiết chuẩn **Jira 1-1 Assignee Rule** (Epic → Task ID, Assignee, Story Points, File mục tiêu, Tiêu chí nghiệm thu DoD). | PM & Domain Leads / Cập nhật khi phát sinh task |
| [`04_Sprint4_Progress_Tracker.md`](./04_Sprint4_Progress_Tracker.md) | Bảng theo dõi tiến độ theo tính năng, Burn-down Story Points, Daily Scrum & Blocker Log, biên bản họp Sprint và Quality Gate Checklist (dùng trích xuất sang `docs/PA4.md`). | Cả nhóm / Cập nhật mỗi ngày & sau PR merge |
| [`05_Week5_Remaining_Tasks_and_Fix_Plan.md`](./05_Week5_Remaining_Tasks_and_Fix_Plan.md) | Danh sách đối chiếu các đầu việc và lỗi còn sót của Tuần 5 (`EC4-01` → `EC4-12`) tại thời điểm kiểm kê `23/11`. | Cả nhóm / Tham chiếu |
| [`06_Week6_Detailed_Action_Plan.md`](./06_Week6_Detailed_Action_Plan.md) | Kế hoạch tác chiến **Tuần 6 (`25/11 – 29/11/2026`)**: 2 cụm song song (**Thịnh + Tony** đóng 100% FE & QA PA4 → chuẩn bị PA5; **Huy + Phúc** dựng Baseline chạy được + nghiên cứu & khung đánh giá cho AI-1 & AI-2). | Cả nhóm / Theo dõi hàng ngày |

## Quy ước Làm việc Nhanh (theo `AGENTS.md` & `05_Agile_Roadmap_and_Kanban.md`)

1. **Quy tắc Gán 1-1**: Mỗi task có duy nhất 1 người chịu trách nhiệm chính và 1 người peer-review trước khi merge vào `dev`.
2. **Hạn chót nội bộ**:
   - Chốt Backend Core 100%: **22:00 Chủ Nhật, `22/11/2026`**.
   - Code Freeze Release 0.3: **23:59 Thứ Tư, `25/11/2026`**.
   - Internal Deadline PA4 (xong code + test + `docs/PA4.md` + Video Demo): **23:59 Thứ Sáu, `27/11/2026`** (đệm 1 ngày trước hạn Moodle `28/11/2026`).
3. **Chuẩn Commit & Nhánh**:
   - Nhánh PA4 làm việc trên feature branches tách từ `dev` (`feat/be-vnpay`, `feat/be-qr-reviews`, `feat/be-gamification`, `feat/fe-portals-vnpay`, `feat/fe-gamification-reviews`).
   - Từ `23/11`, các đầu việc AI cho PA5 phát triển trên nhánh riêng `feat/ai-*`, không merge vào nhánh Release 0.3 của PA4.
