# PROJECT ASSIGNMENT 1 (PA1) REPORT

## EcoBite - Smart Food Rescue Platform
**Course**: Software Engineering (CS300) — University of Science, VNU-HCM (HCMUS)  
**Academic Year**: 2026 – 2027  

---

## A - Group Registration (0 points - administrative task)

> **Task Assignment (Section B)**  
> *Performed by*: Đặng Trọng Phúc | *Reviewed by*:  Đàng Thế Tony, Võ Ngọc Thịnh | *Edited by*: Phùng Quốc Huy

**Group name**: Group 5  
**Project name**: EcoBite - Food Rescue Platform  

| Student ID | Full name | Email |
| :--- | :--- | :--- |
| 24127402 | Phùng Quốc Huy | pqhuy2425@clc.fitus.edu.vn |
| 24127495 | Đặng Trọng Phúc | dtphuc2418@clc.fitus.edu.vn |
| 24127561 | Đàng Thế Tony | dttony2424@clc.fitus.edu.vn |
| 24127246 | Võ Ngọc Thịnh | vnthinh2418@clc.fitus.edu.vn |

---

## B - Project Proposal (10 points)

> **Task Assignment (Section B)**  
> *Performed by*: Đặng Trọng Phúc| *Reviewed by*:  Đàng Thế Tony, Võ ngọc thịnh| *Edited by*: Phùng Quốc Huy
### 1. Introduction

EcoBite is an intelligent Online-to-Offline (O2O) food rescue platform designed to connect commercial food businesses (such as restaurants, bakeries, cafes, and supermarkets) with local consumers seeking high-quality meals at deep discounts (40% to 70% off). Every day, commercial kitchens across urban areas discard massive amounts of wholesome, fresh, and hygienic food simply because it was not sold during their operational shift. This systemic inefficiency causes direct financial losses for store owners and severe environmental harm, as decomposing organic waste in municipal landfills emits potent greenhouse gases ($CH_4$ and $CO_2$).

EcoBite addresses this crisis through a transparent, practical, and tech-driven approach:

- **Dish-Level Transparent Food Rescue (No Mystery Bags)**: Unlike Western platforms (such as Too Good To Go) that rely on randomized "mystery bags"—which face strong friction in the Vietnamese market due to dietary habits, food safety awareness, and personal preferences—EcoBite mandates sealed, itemized listings of specific surplus dishes, accompanied by clear imagery, standardized ingredient lists, and verified allergen alerts.
- **Deterministic Rule-Based Time-Shift Discounting Engine**: Selling prices follow transparent, predictable time schedules (e.g., 40%–50% discount during standard rescue windows, automatically shifting to 60%–70% off during the final 30–45 minutes prior to kitchen closure), giving merchants pricing predictability while maximizing inventory clearance rates.
- **Dual AI Engine (Powered by Google Gemini 2.5 Flash)**: Leverages native multimodal audio ingestion and Natural Language Processing (NLP) to enable busy kitchen staff to batch-post surplus dishes in under 3 seconds with two-tier allergen screening, paired with a contextual AI recommendation engine delivering personalized meal rescue suggestions to consumers.

### 2. Target Users and Environments

#### 2.1. Target Users

- **Consumers (Food Rescuers)**: University students, office workers, and cost-conscious individuals seeking wholesome, hygienic meals at affordable prices, as well as eco-conscious citizens actively committed to curbing urban food waste.
- **Store Partners (Merchants)**: Bakeries, cafes, restaurants, local diners, and supermarkets seeking to monetize end-of-shift surplus, recover raw ingredient costs, reduce waste disposal fees, and acquire new local customers.
- **System Administrators**: Platform operations team responsible for verifying Food Hygiene and Safety (ATVSTP) certificates, vetting merchant business credentials, moderating dish listings, supervising transactions, resolving disputes, and monitoring aggregated environmental metrics.

#### 2.2. Target Environments

- **Client Application**: Cross-platform, fully responsive Progressive Web Application (PWA) built with Next.js 14 (App Router) and Tailwind CSS, optimized for mobile browsers (Apple Safari on iOS, Google Chrome on Android) as well as modern desktop environments (Windows, macOS, Linux).
- **Backend Infrastructure**: Containerized microservices powered by FastAPI (Python 3.11) with asynchronous I/O, PostgreSQL 16 with PostGIS for high-performance geospatial queries, Redis 7 for caching and atomic distributed locking, and the official Google GenAI SDK for Gemini 2.5 Flash integration.

### 3. Key Features

- **Feature 1: Authentication & Merchant Onboarding (KYC & Food Safety Verification)**
  - *Function*: Users authenticate via Email/Password or Google OAuth2 with Role-Based Access Control (RBAC: `CONSUMER`, `STORE_PARTNER`, `ADMIN`) using dual JWT access/refresh tokens. Merchants must submit official Food Hygiene and Safety (ATVSTP) certificates and verified business credentials for mandatory administrator approval prior to publishing dishes.
  - *Value*: Establishes end-to-end community trust, ensuring that all discounted surplus meals originate from verified, certified, and sanitary establishments.

- **Feature 2: Base Menu Catalog & Surplus Dish Management**
  - *Function*: Merchants maintain a persistent Base Menu Catalog (`menu_items`) with standard high-resolution imagery, original retail prices, and basic ingredient metadata. At the end of each shift, merchants instantiate active Surplus Dishes (`dishes`) specifying remaining quantities, pickup windows, and clearance discount tiers.
  - *Value*: Eliminates the overhead of recreating dish listings from scratch daily, ensuring surplus items consistently present authentic presentation and verified baseline prices.

- **Feature 3: Rule-Based Time-Shift Discounting Engine**
  - *Function*: Enforces deterministic price decay schedules over time without volatile, black-box AI pricing. Dishes automatically transition through predefined tiers: standard rescue window (40%–50% off) and final rush clearance (up to 70% off in the last 30–45 minutes) accompanied by live countdown timers.
  - *Value*: Delivers clear pricing transparency for consumers while creating urgent incentives to clear 100% of perishable stock before kitchen closure.

- **Feature 4: Location-Based Search & PostGIS Radar Discovery**
  - *Function*: Leverages PostgreSQL PostGIS spatial indexes (`ST_DWithin`, `ST_Distance`) to compute real-time distances between consumers and nearby stores within a 1–5 km radius (expandable to 10 km). Features an interactive radar map with live map pins, cuisine filters (rice, noodles, bakery, vegetarian), price sliders, and pickup urgency indicators.
  - *Value*: Enables consumers to discover surplus meals within walking distance in seconds, minimizing commute time and ensuring food remains hot and fresh.

- **Feature 5: Inventory Anti-Overselling Lock & Order Management**
  - *Function*: Manages checkout concurrency with strict database-level ACID controls. Executes atomic SQL updates (`UPDATE dishes SET remaining_quantity = remaining_quantity - :qty WHERE remaining_quantity >= :qty`) backed by distributed Redis locks.
  - *Value*: Guarantees zero over-selling, eliminating race conditions when multiple concurrent users attempt to purchase the final available meal simultaneously.

- **Feature 6: Seamless Cashless Checkout (VNPay Payment Gateway)**
  - *Function*: Integrates the VNPay payment gateway supporting dynamic VNPAY-QR code scanning from mobile banking apps, domestic ATM cards, and e-wallets. Employs HMAC-SHA512 verified Instant Payment Notification (IPN) webhooks with idempotent deduplication processing.
  - *Value*: Provides smooth, secure cashless checkout familiar to tech-savvy urban users while protecting merchants against payment fraud.

- **Feature 7: Dynamic HMAC-SHA256 Single-Use QR Token & In-Store Web Scanner**
  - *Function*: Generates dynamic, cryptographically signed QR codes containing single-use HMAC-SHA256 tokens derived from order IDs, user identity, cryptographic nonces, and short expiration windows. Merchants scan the customer's QR code directly using an integrated in-browser camera scanner (`html5-qrcode`).
  - *Value*: Real-time signature verification instantly marks tokens as consumed upon scanning, preventing screenshot sharing, double-claiming, and replay attacks.

- **Feature 8: Verified Reviews, Green Points & Environmental Impact Tracker**
  - *Function*: Only users with verified in-store QR pickup transactions can submit 1-to-5 star ratings and reviews. Concurrently, the platform converts rescued meals into verified ecological metrics (~2.5 kg $CO_2e$ avoided per 1 kg rescued food) and awards Green Points to user accounts, redeemable for reward vouchers on a public Green Leaderboard.
  - *Value*: Gamifies sustainable consumer habits and provides verifiable ESG/environmental reporting metrics for participating merchants.

### 4. AI Features (AI Intelligence Suite - Powered by Google Gemini 2.5 Flash)

- **AI Feature 1: Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard**
  - *Function*: Solves the critical operational bottleneck where busy kitchen staff lack time to fill out complex forms during end-of-shift closing. The merchant simply records a short voice memo — for example: *"Remaining 5 broken rice with pork chops, 3 grilled pork vermicelli, clear until 3 PM"*:
    1. *Native Multimodal Audio Ingestion*: Streams raw audio directly to Gemini 2.5 Flash without intermediary speech-to-text (STT) services, accurately understanding Vietnamese regional accents, colloquial terms (*"bốn lăm cành"*, *"bì chả"*), and culinary nuances.
    2. *Menu-Catalog Grounding*: Gemini aligns extracted dish names against the merchant's Base Menu Catalog in the prompt context to assign `matched_menu_id`, automatically inheriting verified dish imagery, original pricing, and triggering rule-based discount schedules.
    3. *Two-Tier Allergen Guard (14 EU FIC Standards)*:
       - **Explicit Detection**: Detects allergens explicitly mentioned in speech (e.g., *"contains crushed peanuts"*).
       - **Inferred Culinary Knowledge**: Automatically infers hidden allergens based on traditional Vietnamese culinary recipes: e.g., broken rice with pork chop contains Egg (in steamed egg meatloaf) and Fish (in fish sauce); grilled pork vermicelli contains Peanuts and Fish sauce; banh mi contains Gluten.
       - **Local Dietary Notes**: Flags culturally essential dietary attributes (`dietary_notes`): scallion oil garnish (*Có mỡ hành*), chili spice level, pickled vegetables, and vegetarian suitability.
    4. *Batch Extraction & Server-Time Grounding*: Concurrently extracts multiple surplus items (`List[SurplusDishItem]`) and resolves relative time expressions (*"until 3 PM"*) into absolute ISO 8601 timestamps using provided server clock context (`current_server_time`).
  - *Value*: Reduces listing time from 3 minutes per item to under 3 seconds for entire batches, while preventing life-threatening allergic reactions through standardized medical warnings.

- **AI Feature 2: Smart Food Recommendation & Natural Language Semantic Search**
  - *Function*: Delivers personalized, context-aware surplus meal discovery through a robust 3-layer hybrid architecture:
    1. *Layer 1 - Hard Safety Invariant (SQL & PostGIS)*: Queries dishes within a 1–3 km radius and strictly excludes 100% of items matching the user's declared medical allergens (`excluded_allergens` in `user_preferences`). Medical safety is enforced at the database query layer and never delegated to probabilistic LLM text generation.
    2. *Layer 2 - Multi-Factor Heuristic Scoring*: Ranks candidate dishes using an objective composite weighted formula:
       $$\text{Score} = (0.40 \times \text{Proximity}) + (0.30 \times \text{Discount Depth \& Time Urgency}) + (0.30 \times \text{Taste Profile Match})$$
       Prioritizes urgent rescue deals entering the final 30 minutes of 70% clearance to prevent food expiration.
    3. *Layer 3 - Generative AI Personalization*: Top 3 ranked candidate dishes and user taste profiles are fed into Gemini 2.5 Flash to synthesize concise, emotionally compelling explanations (20–30 words) displayed on UI recommendation cards (e.g., *"Recommended for you: You frequently enjoy warm noodle soups for lunch. Pho Bac (350m away) is clearing 2 remaining bowls at 67% off (only 18,000 VND) until 13&#58;30 (1&#58;30 PM) — verified 100% peanut-free according to your profile!"*).
    4. *Conversational Semantic Search*: Allows consumers to query using natural language (e.g., *"Find me a comforting warm soup under 30k nearby"*), with Gemini extracting intent, budget, and dietary constraints to query PostGIS.
  - *Value*: Maximizes conversion rates, eliminates search fatigue for hungry users, and clears perishable stock before closing without compromising health.

---

## C - Existing App Survey

> **Task Assignment (Section C)**  
> *Performed by*: Đàng Thế Tony | *Reviewed by*: Phùng Quốc Huy, Đặng Trọng Phúc | *Edited by*: Võ Ngọc Thịnh

### 1. Yindii

![Yindii Web Platform](media/image4.png)

**Operating Model**:
- Users select from 2 fulfillment streams:
  - *Dry goods*: Shelf-stable packaged groceries delivered to homes.
  - *Surplus meals*: Fresh discounted surplus meals for pickup.
- **EcoBite Strategy**: Exclusively focuses on same-day fresh surplus meal rescue for in-store pickup (*Only pickup surplus meals*).

![Yindii Mobile App](media/image6.png)


- **Food Recommendation**: Yindii suggests random food items across meal categories.
- **EcoBite Strategy**: Delivers individualized recommendations personalized for each user via an AI recommendation engine factoring in taste profiles, distance, and discount urgency.

#### Key Functions of Yindii

![Yindii - Browse Deals](media/image2.png)

*Users discover food bags from nearby stores, checking food categories, original retail value, and designated pickup windows.*

![Yindii - Mystery Bag Details](media/image14.png)

*Each bag lists food category descriptions and estimated retail values; specific contents vary depending on daily kitchen surplus.*

![Yindii - Cart & Checkout](media/image5.png)

*Users reserve surplus food bags and complete cashless payment within the mobile application.*

![Yindii - In-Store Pickup](media/image9.png)

*Users arrive at the store within the scheduled pickup window, present digital receipts on their smartphone, and confirm meal collection.*

---

### 2. Too Good To Go

![Too Good To Go - Overview](media/image8.png)


**Platform Name**: Too Good To Go  
Too Good To Go connects consumers with restaurants, bakeries, cafes, and grocery stores that have unsold surplus food. Users discover nearby offerings, reserve and pay online, and collect their meals during designated time slots.

![Too Good To Go - Search & Map Filter](media/image10.png)

*Displays available surplus food portions from nearby partner merchants. Users explore via list or interactive map views, applying filters and sorting by preference.*

![Too Good To Go - Item Details](media/image11.png)

*Users inspect food bag details, pricing, ratings, and pickup timeframes prior to reserving.*

![Too Good To Go - Order Confirmation](media/image16.png)

*Users confirm selections, reserve surplus bags, and complete in-app payment through supported mobile checkout channels.*

![Too Good To Go - Environmental Impact Profile](media/image12.png)

*Profile page displays order history and aggregated environmental impact metrics, highlighting avoided carbon emissions ($CO_2e$) and monetary savings.*

#### Evaluation of Too Good To Go & Lessons for EcoBite

**Strengths of Too Good To Go**:
- Intuitive and straightforward user journey from discovery to in-store pickup.
- Clear brand proposition centered on reducing food waste at deep discounts.
- Comprehensive location-based search with interactive maps, category filters, and clear pickup windows.
- Strong eco-friendly branding that motivates community engagement in food rescue.

**Development Opportunities for EcoBite**:
- **Localized Experience**: Fully localized Vietnamese interface with transparent VNĐ pricing and domestic VNPay payment integration.
- **Dish-Level Transparency (No Mystery Bags)**: Provide explicit dish names, real photos, and full ingredient lists to accommodate Vietnamese consumer eating habits and allergy safety.
- **AI-Powered Fast Merchant Posting**: Enable busy kitchen owners to post remaining stock in under 3 seconds via voice input with Gemini 2.5 Flash.
- **Security & Integrity**: 2-tier medical allergen guard and dynamic single-use HMAC-SHA256 QR codes to eliminate screenshot sharing and pickup fraud.

---

## D - Team Contract (5 points)

> **Task Assignment (Section D)**  
> *Performed by*: Phùng Quốc Huy | *Reviewed by*:  Đàng Thế Tony, Võ Ngọc Thịnh | *Edited by*: Đặng Trọng Phúc

### 1. Team Roles and Responsibilities

- **Phùng Quốc Huy -- AI and Data Lead / Full-Stack Engineer**
  - *Primary Responsibilities*: Leads data engineering pipelines and builds AI/ML models to predict optimal dynamic pricing for surplus food items.
  - *General Responsibilities*: Participates in full-stack development tasks and issue tracking.

- **Đặng Trọng Phúc -- Backend Lead & AI Engineer / Full-Stack Engineer**
  - *Primary Responsibilities*: Leads backend system architecture and database management, while assisting with AI model integration into the backend service.
  - *General Responsibilities*: Participates in full-stack development tasks and issue tracking.

- **Đàng Thế Tony -- QA/Tester Lead & Backend Engineer / Full-Stack Engineer**
  - *Primary Responsibilities*: Leads quality assurance (QA), authors test plans and test cases, conducts software testing, and assists with backend business logic implementation.
  - *General Responsibilities*: Participates in full-stack development tasks and issue tracking.

- **Võ Ngọc Thịnh -- Frontend Lead / Full-Stack Engineer**
  - *Primary Responsibilities*: Leads frontend development, implements responsive UI/UX designs, and integrates client-side web applications with backend APIs.
  - *General Responsibilities*: Participates in full-stack development tasks and issue tracking.

### 2. Communication Plan

- **Communication Tools**:
  - *Zalo*: Daily announcements, rapid technical discussions, urgent alerts, and sharing task links.
  - *Google Meet*: Weekly team meetings, Sprint planning, Scrum standups, code reviews, and pair-programming sessions.

- **Response Time Expectations**:
  - *Regular Messages (Zalo)*: Members are expected to reply within 2 to 4 hours during standard working hours (08&#58;00 – 22&#58;00).
  - *Urgent Messages / Blockers*: When tagged with `@all` on Zalo, members must acknowledge and respond within 1 hour.

- **Meeting Protocols**:
  - Meeting minutes and key decision logs must be summarized and published in the group channel immediately following each session.

### 3. Work Schedule and Deadlines

- **Fixed Meeting Schedule**: Monday evening at 20&#58;30 (8&#58;30 PM).
- **Internal Deadline Policy**:
  - All assigned tasks, code submissions, and report sections must be completed at least 1 day prior to the official deadline set by the course instructors.
  - This 1-day buffer is strictly reserved for cross-member review and quality assurance prior to official submission.
- **Contingency & Emergency Protocol**:
  - *Early Notification*: If a team member encounters unforeseen personal circumstances preventing timely completion, they must notify the group on Zalo as early as possible.
  - *Peer Support*: Upon notification, remaining team members will step in to reallocate tasks and support the affected member to ensure all deliverables are completed on schedule without quality degradation.

### 4. Code and Documentation Standards

- **Coding and Tools**: PEP 8 (Python), Prettier/ESLint (JS/TS), Feature branching (`feature/*`) on Git.
- **Review and Test**: At least 1 PR approval required before merging; run unit tests locally prior to pushing.
- **Documentation**: All docs maintained in English Markdown (`.md`) under `/docs`, architecture diagrams rendered via Mermaid, with mandatory author tags on section headers.

### 5. Accountability and Performance

- **Performance Metrics**: Evaluated by Jira task completion rates, code and documentation quality, meeting attendance, and adherence to internal deadlines.
- **Underperformance Process**:
  - *Private Warning*: Direct message on Zalo immediately following a missed deadline or unexcused absence.
  - *Team Meeting*: Formal discussion during the Monday meeting to reallocate tasks and establish a strict recovery plan.
  - *Consequences*: Deduction in peer assessment scores, reallocation of task ownership, and direct escalation to the course instructor or TA for persistent non-responsiveness.

### 6. Decision-Making Process

- **Consensus & Majority Vote**: Technical and architectural decisions are first discussed openly via Google Meet or Zalo to reach team consensus. If consensus cannot be achieved, decisions are settled by a simple majority vote (>50%).
- **Tie-Breaking & Final Say**: In case of a tie or deadlock, the responsible domain Lead (e.g., AI Lead for ML/AI models, Backend Lead for system architecture, Frontend Lead for UI/UX) holds the tie-breaking vote and final decision.

### 7. Conflict Resolution

- **Internal Mediation**: Interpersonal or technical disputes must first be addressed directly between involved members through objective, fact-based discussion on Zalo or Google Meet.
- **Team Intervention**: If unresolved within 24 hours, the issue is escalated to a team meeting where the relevant domain Lead or PM mediates a fair compromise.
- **Instructor Escalation**: If a conflict remains unresolved after 48 hours or directly jeopardizes project deadlines, the team will formally escalate the matter to the TA or course instructor for guidance.

### 8. Review and Update Process

- **Scheduled Reviews**: The team contract is formally reviewed at the inception of each Sprint (PA phase) during Sprint Planning to adapt to evolving project needs.
- **Amendment Process**: Any member may propose contract modifications during weekly Monday meetings. Amendments require team consensus or a majority vote for ratification.
- **Version Control**: Approved changes are committed to the official project repository under `/docs/management/` with clear Git commit logs tracking amendment dates and rationale.

---

## E - Development Tools and Process Setup (5 points)

> **Task Assignment (Section E)**  
> *Performed by*: Võ Ngọc Thịnh | *Reviewed by*: Đàng Thế Tony, Đặng Trọng Phúc | *Edited by*: Phùng Quốc Huy

### E.1 Agile/Scrum Workflow Integration

Group 05 strictly adopts the **Agile/Scrum framework** across the semester:

- **Sprint Duration**: 2 to 3 weeks corresponding to each Project Assignment (PA1 through PA5).
- **Sprint Ceremonies**:
  - 1x Sprint Planning (Backlog grooming, story pointing, task assignment).
  - 2x Scrum Check-ins (Blocker removal, sprint velocity check).
  - 1x Sprint Review & Retrospective (Demoing working increments, identifying process enhancements).

### E.2 Toolchain & Infrastructure Setup

The team has established and verified the required course infrastructure:

| Category | Designated Tool | Group Workspace / URL | Purpose |
| :--- | :--- | :--- | :--- |
| **Course Submissions** | Moodle | HCMUS Courses Portal | Official deliverable submission |
| **Class Discussion** | FB Group / Forum | Course Official Group | General announcements & Q&A |
| **Team Communication** | Google Meet & Zalo | Group 05 Server | Daily collaboration & meetings |
| **Task Management** | Jira Software | ecobite-hcmus.atlassian.net | Scrum sprint board & issue tracking |
| **Version Control** | GitHub (Private) | github.com/hcmus-cs300-g05/ecobite | Source code & documentation repo |
| **Spec-Driven Dev** | Spec Kit | Local CLI / Repository setup | Specification-to-code workflow |
| **AI Coding Assistance** | GitHub Copilot / Cursor | Student Verified Accounts | AI-assisted development |

### E.3 Git Repository Structure & Conventions

The private GitHub repository is organized according to the instructor-recommended layout:

```text
EcoBite-Platform/
├── .gitignore                        # Ignore sensitive files, caches, and large weights
├── .env.example                      # Standard environment variables template
├── .env                              # Local active environment variables
├── .pre-commit-config.yaml           # Automated Git hook quality gates (Ruff, Secrets, File size)
├── AGENTS.md                         # Mandatory AI development rules & TDD cycle
├── docker-compose.yml                # Docker configuration for PostGIS 16 and Redis 7
├── README.md                         # Project overview documentation
├── docs/                             # Detailed project management & technical documentation
│   ├── 01_PRD_and_User_Stories.md    # Product requirements & 8 user stories
│   ├── 02_System_Architecture.md     # System architecture, sequence diagrams & lifespan
│   ├── 03_Database_Schema_ERD.md    # PostgreSQL/PostGIS schema & Mermaid ERD
│   ├── 04_API_Specification.md       # RESTful API v1 endpoint specifications
│   ├── 05_Agile_Roadmap_and_Kanban.md# 6-Sprint plan, DoR, DoD & risk management
│   ├── 06_Environment_and_ML_Setup_Guide.md # Comprehensive A-to-Z setup guide
│   └── 07_AI_Development_Workflow_and_Quality_Gates.md # TDD workflow & quality gates
├── ml/                               # Independent Machine Learning workspace
│   ├── README.md                     # Model weight naming conventions & backend IPC
│   ├── requirements.txt              # ML dependencies (Ultralytics, Scikit-learn, Jupyter)
│   ├── notebooks/                    # Research & model training notebooks
│   ├── datasets/                     # Food image datasets & annotations (gitignored)
│   └── weights/                      # Model weight checkpoint files (.pt)
├── backend/                          # Backend Web API application (FastAPI)
│   ├── requirements.txt              # API & inference runtime dependencies
│   ├── alembic.ini                   # Database migration configuration
│   ├── alembic/                      # Database migration revision scripts
│   ├── app/                          # Core application source code
│   │   ├── core/                     # Security, configuration & database session
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   ├── schemas/                  # Pydantic DTOs & schemas
│   │   ├── services/                 # Business logic & service helpers
│   │   └── api/v1/endpoints/         # API route controllers
│   └── tests/                        # Backend test suite
│       ├── unit/                     # Independent business logic unit tests
│       └── integration/              # Database & API integration tests
└── frontend/                         # Next.js 14 App Router web client
    ├── package.json                  # Dependencies (Leaflet, QR, TanStack Query)
    ├── .npmrc                        # Strict engine configuration
    ├── public/                       # Static assets (icons, illustrations)
    ├── src/                          
    │   ├── web/                      
    │   │   ├── (consumer)/           # Consumer web interface
    │   │   ├── (store-partner)/      # Store partner interface & QR scanner
    │   │   └── (admin)/              # Administrator dashboard
    │   ├── components/               # Reusable UI components
    │   └── lib/                      # Axios client, map helpers, QR utilities
    └── __tests__/                    # Frontend automated test suite
        ├── components/               # UI component tests
        └── hooks/                    # Custom hooks & query tests
```

#### Git Commit Conventions

The team strictly follows the **Conventional Commits** specification:

- `feat(scope)`: add new feature (e.g., `feat(auth): implement jwt token generation`)
- `fix(scope)`: resolve bug (e.g., `fix(qr): fix verification token expiration check`)
- `docs(scope)`: update documentation (e.g., `docs(pa1): finalize section b proposal`)
- `test(scope)`: add automated tests (e.g., `test(pricing): unit test time decay discount`)

---

### E.4 Task Management (Jira Setup)

The team has configured the Jira workspace with the following mandatory fields:

1. **1-to-1 Assignee Rule**: Every task is assigned to strictly one responsible member.
2. **Date Lifecycle**: Every issue contains Created Date, Start Date, and Resolution Date. Tasks are never backfilled post-completion.
3. **Scrum Issue Types**: Epics (representing Functional Groups) -> User Stories -> Subtasks & Bugs.

![Figure E.1: Jira Scrum Board & Sprint Backlog Setup](media/image15.png)  

*Figure E.1: Group 05 Jira Scrum Board & Sprint Backlog setup showing all 4 members and initial sprint tasks.*

---

### E.5 Spec Kit & AI Coding Tool Accounts

- **Spec Kit Preparation**: The repository is configured to receive Spec Kit specification templates starting from PA2.
- **AI Coding Verification**: All 4 team members have secured verified educational subscriptions for AI development environments:
  - **Võ Ngọc Thịnh**: GitHub Copilot Student Pack (Verified) & Gemini Pro.
  - **Đặng Trọng Phúc**: GitHub Copilot Student Pack (Verified).
  - **Phùng Quốc Huy**: GitHub Copilot Student Pack (Verified) & Gemini Pro.
  - **Đàng Thế Tony**: GitHub Copilot Student Pack (Verified).

#### Team AI Account Verification Proofs (Figure E.2)

**1. Google AI Pro Account - Phùng Quốc Huy**  
![Google AI Pro Account - Phùng Quốc Huy](media/image7.png)


**2. Google AI Pro Account - Võ Ngọc Thịnh**  
![Google AI Pro Account - Võ Ngọc Thịnh](media/image3.png)


**3. Google AI Pro Account - Đặng Trọng Phúc**  
![Google AI Pro Account - Đặng Trọng Phúc](media/image1.png)


**4. Google AI Pro Account - Đàng Thế Tony**  
![Google AI Pro Account - Đàng Thế Tony](media/image13.png)

