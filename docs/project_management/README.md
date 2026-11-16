# 🗂️ Trung tâm Quản lý Tiến độ & Giao việc Dự án EcoBite (`docs/project_management/`)

Đây là thư mục trung tâm quản lý toàn bộ vòng đời dự án **EcoBite Platform** qua 5 mốc đánh giá môn học (**PA1 – PA5**), bao gồm lộ trình tổng thể, bảng giao việc chuẩn **Jira 1-1 Assignee Rule**, nhật ký tiến độ hàng ngày, biên bản họp Scrum và tiêu chuẩn nghiệm thu Quality Gates.

## Cấu trúc Thư mục

```text
docs/project_management/
├── README.md                                  # Cổng điều phối quản lý dự án (tệp này)
├── 00_Overall_Roadmap_and_PA_Tracker.md       # Bảng tổng hợp tiến độ toàn dự án (PA1 -> PA5 & Features 1-8 + AI 1-2)
├── pa1_sprint1/
│   └── README.md                              # Tổng kết hoàn thành PA1 (04/10 – 17/10/2026)
├── pa2_sprint2/
│   └── README.md                              # Tổng kết hoàn thành PA2 (18/10 – 31/10/2026)
├── pa3_sprint3/
│   └── README.md                              # Tổng kết hoàn thành PA3 (01/11 – 14/11/2026)
├── pa4_sprint4/                               # ĐANG CHẠY (15/11 – 28/11/2026)
│   ├── README.md
│   ├── 01_PA4_Master_Execution_Plan.md        # Kế hoạch tổng thể PA4 (3 BE + 1 FE)
│   ├── 02_Week5_Detailed_Action_Plan.md       # Kế hoạch tác chiến từng ngày Tuần 5 (16/11 – 22/11)
│   ├── 03_Task_Assignment_Jira_Backlog.md     # Bảng giao việc 1-1 & Story Points Sprint 4
│   └── 04_Sprint4_Progress_Tracker.md         # Theo dõi tiến độ, Burn-down, Daily Scrum & Blocker Log
└── pa5_sprint5/                               # KẾ HOẠCH TIẾP THEO (29/11 – 12/12/2026, khởi động sớm AI từ 23/11)
    ├── 01_PA5_Plan_and_Backlog.md             # Kế hoạch & Bảng giao việc 1-1 cho AI Suite + UAT + Go-Live
    └── 02_Sprint5_Progress_Tracker.md         # Bảng theo dõi tiến độ & Quality Gates Sprint 5
```

## Tài liệu Nền tảng Liên quan
- Thỏa ước nhóm, công cụ Jira/GitHub & DoR/DoD: [`docs/05_Agile_Roadmap_and_Kanban.md`](../05_Agile_Roadmap_and_Kanban.md)
- Quy trình kỹ thuật & 8 Ranh giới Bất khả Xâm phạm: [`AGENTS.md`](../../AGENTS.md)
- Đặc tả API RESTful (`/api/v1`): [`docs/04_API_Specification.md`](../04_API_Specification.md)
- Tài liệu báo cáo chính thức đã xuất bản: [`docs/PA2.md`](../PA2.md), [`docs/PA3_Section_E_Functional_Group_Demo.md`](../PA3_Section_E_Functional_Group_Demo.md)
