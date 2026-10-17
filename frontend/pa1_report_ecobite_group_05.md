### VIETNAM NATIONAL UNIVERSITY HO CHI MINH CITY

### UNIVERSITY OF SCIENCE

### FACULTY OF INFORMATION TECHNOLOGY

### DEPARTMENT OF SOFTWARE ENGINEERING

## **PROJECT ASSIGNMENT 1 (PA1)**

# **PROJECT PROPOSAL & TEAM SETUP**

### **SUBJECT: CS300 - INTRODUCTION TO SOFTWARE ENGINEERING**

### **PROJECT NAME:**

# **ECOBITE - FOOD RESCUE PLATFORM**

*(Smart Mobile Application)*

Ho Chi Minh City, Academic Year 2025 - 2026

# TABLE OF CONTENTS

1. [SECTION A: GROUP REGISTRATION](#section-a-group-registration)

2. [SECTION B: PROJECT PROPOSAL (ECOBITE)](#section-b-project-proposal-ecobite)

   * [B.1 Introduction & Problem Statement](#b1-introduction--problem-statement)

   * [B.2 Target Users (Actors) & Environments](#b2-target-users-actors--environments)

   * [B.3 Core Functional Groups (Detailed Specifications)](#b3-core-functional-groups-detailed-specifications)

   * [B.4 Meaningful AI-Powered Capabilities](#b4-meaningful-ai-powered-capabilities)

   * [B.5 High-Level System Architecture](#b5-high-level-system-architecture)

3. [SECTION C: EXISTING APP SURVEY & COMPETITOR ANALYSIS](#section-c-existing-app-survey--competitor-analysis)

   * [C.1 Surveyed Product 1: Too Good To Go](#c1-surveyed-product-1-too-good-to-go)

   * [C.2 Surveyed Product 2: Yindii](#c2-surveyed-product-2-yindii)

   * [C.3 Feature Matrix & Cross-Comparison](#c3-feature-matrix--cross-comparison)

   * [C.4 Competitive Edge & Innovation of EcoBite](#c4-competitive-edge--innovation-of-ecobite)

   * [C.5 Adopted UI/UX Patterns](#c5-adopted-uiux-patterns)

4. [SECTION D: TEAM CONTRACT](#section-d-team-contract)

   * [D.1 Team Roles & Responsibilities](#d1-team-roles--responsibilities)

   * [D.2 Communication Plan & Meeting Cadence](#d2-communication-plan--meeting-cadence)

   * [D.3 Work Schedule, Sprints & Deadlines](#d3-work-schedule-sprints--deadlines)

   * [D.4 Code & Documentation Standards](#d4-code--documentation-standards)

   * [D.5 Accountability, Performance & Peer Evaluation](#d5-accountability-performance--peer-evaluation)

   * [D.6 Decision-Making Protocol](#d6-decision-making-protocol)

   * [D.7 Conflict Resolution Mechanism](#d7-conflict-resolution-mechanism)

   * [D.8 Review & Contract Revision Policy](#d8-review--contract-revision-policy)

5. [SECTION E: DEVELOPMENT TOOLS & PROCESS SETUP](#section-e-development-tools--process-setup)

   * [E.1 Agile/Scrum Workflow Integration](#e1-agilescrum-workflow-integration)

   * [E.2 Toolchain & Infrastructure Setup](#e2-toolchain--infrastructure-setup)

   * [E.3 Git Repository Structure & Conventions](#e3-git-repository-structure--conventions)

   * [E.4 Task Management (Jira Setup)](#e4-task-management-jira-setup)

   * [E.5 Spec Kit & AI Coding Tool Accounts](#e5-spec-kit--ai-coding-tool-accounts)

6. [APPENDIX & REFERENCES](#appendix--references)

# SECTION A: GROUP REGISTRATION

> **Task Assignment:**
>
> *Performed by:* Võ Ngọc Thịnh | *Reviewed by:* Đặng Trọng Phúc | *Edited by:* Phùng Quốc Huy, Đàng Thế Tony

### Team Profile: Group 05

* **Project Name:** EcoBite - Food Rescue Platform

* **Course:** CS300 / CSC13002 - Introduction to Software Engineering

* **Academic Term:** Semester 1 (2025 - 2026)

| No. | Student ID | Full Name | University Email Address | Role in Team | GitHub Username | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| 1 | **24127246** | **Võ Ngọc Thịnh** | vnthinh2418@clc.fitus.edu.vn | **Team Leader / Full-Stack** | `@thinh-vongoc` *(edit if needed)* | 
| 2 | **24127495** | **Đặng Trọng Phúc** | dtphuc2418@clc.fitus.edu.vn | **Member / Full-Stack** | `@phuc-dangtrong` | 
| 3 | **24127402** | **Phùng Quốc Huy** | pqhuy2425@clc.fitus.edu.vn | **Member / Full-Stack** | `@huy-phungquoc` | 
| 4 | **24127561** | **Đàng Thế Tony** | dttony2424@clc.fitus.edu.vn | **Member / Full-Stack** | `@tony-dangthe` | 

# SECTION B: PROJECT PROPOSAL (ECOBITE)

> **Task Assignment:**
>
> *Performed by:* Đặng Trọng Phúc, Võ Ngọc Thịnh | *Reviewed by:* Phùng Quốc Huy | *Edited by:* Đàng Thế Tony

## B.1 Introduction & Problem Statement

Every day, bakeries, cafes, buffet restaurants, and grocery supermarkets discard tons of edible, high-standard food items simply because they reach the end of their business hours or daily shelf life. Concurrently, millions of students and urban budget-conscious consumers face surging living and food costs.

**EcoBite** is designed as a localized, on-demand food rescue mobile ecosystem that bridges the gap between merchant food waste and consumer thriftiness. By enabling merchants to package end-of-day food into heavily discounted "Surprise Bags" (50%–70% off retail prices), EcoBite provides substantial cost savings to urban consumers while unlocking supplementary revenue streams for merchants. Furthermore, every rescued meal directly cuts down landfill methane emissions, establishing a tangible, measurable environmental contribution toward sustainable urban living.

## B.2 Target Users (Actors) & Environments

```
graph LR
    C[Consumer / Student] -- "Reserve & Pick up Bags" --> EcoBiteApp((EcoBite Mobile System))
    M[Store Partner / Merchant] -- "List Surplus Bags & Scan QR" --> EcoBiteApp
    A[System Administrator] -- "KYC Audit & Analytics" --> EcoBiteApp


```

### 1. Primary Actors

1. **Actor 1: Consumer (Students & Cost-Conscious Urban Eaters)**

   * *Characteristics:* University students, young professionals, and environmental advocates seeking affordable daily meals near their residence or campus.

   * *Primary Goal:* Browse nearby available food bags, order ahead with digital payment, and pick up fresh meals at specific closing windows.

2. **Actor 2: Store Partner (Bakeries, Cafes, Grocery Stores, Buffets)**

   * *Characteristics:* Store managers and kitchen staff with surplus inventory at late hours.

   * *Primary Goal:* Monetize potential waste, specify pickup slots, effortlessly publish surprise packs, and authenticate handovers via QR verification.

3. **Actor 3: System Administrator (Platform Operations & Quality Control)**

   * *Characteristics:* Platform managers responsible for business verification, partner KYC, food safety compliance, and dispute resolution.

### 2. Operating Environments

* **Consumer & Store Partner Client:** Cross-platform Mobile Application (iOS 15.0+ and Android 11.0+) built with React Native / Flutter to leverage device hardware (GPS Geolocation, Camera Scanner, Push Notifications).

* **Store & Admin Management Console:** Responsive Web Dashboard (Chromium/Safari latest) for store analytics and administrative KYC auditing.

* **Backend Infrastructure:** RESTful & WebSocket API server containerized via Docker, hosted on Cloud (AWS/GCP/Supabase), utilizing PostgreSQL with PostGIS extensions for spatial radius queries.

## B.3 Core Functional Groups (Detailed Specifications)

To adhere strictly to software engineering standards, the application is divided into **8 cohesive functional groups**. Each functional group encapsulates related use cases addressing a vital system objective:

### Functional Group 1: User Authentication & KYC Onboarding (Auth & Profile)

* **Description:** This module provides secure authentication mechanisms for both Consumers and Store Partners using JWT tokens, OAuth2 (Google/Apple), and email-based password recovery. Furthermore, it enforces a Know-Your-Customer (KYC) onboarding pipeline requiring Store Partners to upload business licenses and food safety credentials before listing items.

* **Value & Utility:** It establishes identity integrity, safeguards user data with modern encryption, and prevents fraudulent merchants from distributing unverified food to consumers.

### Functional Group 2: Surplus Inventory & Surprise Bag Management

* **Description:** This module allows Store Partners to rapidly create, publish, and schedule recurring or ad-hoc "Surprise Bags" with original prices, discounted prices (50%–70% off), quantity limits, and strict pickup windows (e.g., 20:30 - 21:30). It supports item status toggles (Active, Sold Out, Expired) and automated inventory deductions.

* **Value & Utility:** It minimizes operational friction for busy kitchen staff by eliminating the need to itemize individual dishes, turning surplus food cataloging into a 30-second workflow.

### Functional Group 3: Geolocation-Based Search & Dietary Filtering

* **Description:** This feature empowers Consumers to discover nearby available food packs via an interactive map view and dynamic radius sliders (1 km to 10 km). It integrates rich multi-criteria filters including dietary preferences (Halal, Vegetarian, Vegan, Bakery, Meals), price range, collection time, and store ratings.

* **Value & Utility:** It drastically reduces discovery time for hungry consumers, ensuring they only view actionable, currently available food bags within reasonable walking or transit distance.

### Functional Group 4: Order Reservation & Cryptographic QR Generation

* **Description:** This module manages the consumer checkout lifecycle, supporting integrated mobile payment gateways (MoMo, ZaloPay, VNPay, or Card) and temporary inventory locking to avoid over-ordering. Upon successful reservation, the system generates a digitally signed, dynamic QR Code containing unique cryptographic tokens tied to the order.

* **Value & Utility:** It ensures seamless, contactless transactions and guarantees that ordered food is reserved exclusively for the customer until the pickup window expires.

### Functional Group 5: Contactless Order Handover & Instant Redemption

* **Description:** This module equips Store Partners with an integrated camera scanner to scan the Consumer's presented QR Code upon arrival. The system validates the token signature in real time via WebSocket/REST, confirms pickup legitimacy, and transitions order status from "Pending Pickup" to "Completed".

* **Value & Utility:** It completely eliminates manual order reconciliation, stops duplicate pickups or fraud, and reduces handover duration to under 10 seconds per customer.

### Functional Group 6: Social Review, Trust Scoring & Food Quality Feedback

* **Description:** Following an order completion, the module prompts Consumers to submit 1-to-5 star ratings, structured feedback tags (e.g., "Generous Portions", "Great Taste", "Polite Staff"), and photo reviews. It computes aggregate store reputation scores and flags stores whose ratings plunge below predefined safety thresholds.

* **Value & Utility:** It fosters transparent community trust, holds food providers accountable for freshness, and drives customer loyalty toward high-performing partners.

### Functional Group 7: Smart Push Notifications & Real-Time Alert Dispatcher

* **Description:** This subsystem broadcasts automated background notifications via Firebase Cloud Messaging (FCM) when favorite stores publish new bags, when collection windows are 30 minutes away, or when reservation deadlines approach. Store Partners also receive auditory pings whenever a new reservation occurs.

* **Value & Utility:** It guarantees high pickup compliance rates, prevents consumers from missing their scheduled pickup windows, and keeps merchants constantly informed without manual screen refreshing.

### Functional Group 8: Environmental Impact & Financial Analytics Dashboard

* **Description:** This analytical engine calculates cumulative metrics for both actors: Consumers see total money saved alongside gamified environmental KPIs (kilograms of CO2 equivalent emissions avoided and equivalent tree seedlings saved). Store Partners access detailed financial breakdowns of recovered revenue and waste reduction percentages over time.

* **Value & Utility:** It reinforces emotional and behavioral engagement through gamification, while equipping business owners with clear return-on-investment (ROI) data.

## B.4 Meaningful AI-Powered Capabilities

EcoBite incorporates a dedicated **AI Intelligence Engine** delivering practical value beyond simple rule-based heuristics:

```
graph TD
    subgraph Data Inputs
        A1[Historical Sales & Residual Counts]
        A2[Real-Time Closing Clock Countdown]
        A3[Consumer Dietary History & Coordinates]
    end
    subgraph AI Engine
        B1[Dynamic Markdown Pricing Engine]
        B2[Smart Context-Aware Recommendation Model]
    end
    subgraph Concrete Outputs
        C1[Automated Optimal Discount Suggestion 50%-85%]
        C2[Personalized Home Feed & Timely Rescue Pushes]
    end
    A1 --> B1
    A2 --> B1
    A1 --> B2
    A3 --> B2
    B1 --> C1
    B2 --> C2


```

### 1. AI Dynamic Markdown Pricing Engine (For Store Partners)

* **Mechanism:** As closing time draws near, leftover food risk increases exponentially. The EcoBite dynamic pricing model uses regression analysis considering remaining item count, store closing countdown, day-of-week trends, and current local weather conditions.

* **Practical Value:** The AI calculates the optimal clearing discount (e.g., starting at 50% off 2 hours prior to close, stepping down intelligently to 75% off in the final 30 minutes). This maximizes food clearance rates for the merchant while offering hyper-attractive flash-sale prices to late-night students.

### 2. Context-Aware Smart Food Recommendation (For Consumers)

* **Mechanism:** Utilizing collaborative filtering combined with spatial-temporal embeddings, the recommendation engine predicts what items a user is most likely to purchase based on historical order timing, preferred dietary categories, current GPS location, and typical walking pace.

* **Practical Value:** Instead of forcing students to scroll through irrelevant listings, the app surfaces a customized "Picks for You Right Now" section, delivering tailored push notifications exactly when their favorite bakery drops an end-of-day surprise bag.

## B.5 High-Level System Architecture

```
classDiagram
    class User {
        +UUID id
        +String email
        +String fullName
        +String phone
        +Role role
        +register()
        +login()
    }
    class Consumer {
        +Float savedMoney
        +Float co2OffsetKg
        +browseBags()
        +reserveOrder()
    }
    class StorePartner {
        +String businessName
        +String address
        +Coordinates location
        +KYCStatus status
        +publishBag()
        +scanHandoverQR()
    }
    class SurpriseBag {
        +UUID bagId
        +String title
        +Float originalPrice
        +Float discountedPrice
        +Int quantityAvailable
        +Time pickupStart
        +Time pickupEnd
        +BagCategory category
    }
    class Order {
        +UUID orderId
        +OrderStatus status
        +String qrSignature
        +DateTime createdAt
        +generateQR()
        +verifyCompletion()
    }
    User <|-- Consumer
    User <|-- StorePartner
    StorePartner "1" --> "*" SurpriseBag : manages
    Consumer "1" --> "*" Order : places
    SurpriseBag "1" --> "*" Order : contains


```

# SECTION C: EXISTING APP SURVEY & COMPETITOR ANALYSIS

> **Task Assignment:**
>
> *Performed by:* Phùng Quốc Huy, Đàng Thế Tony | *Reviewed by:* Võ Ngọc Thịnh | *Edited by:* Đặng Trọng Phúc

To benchmark industry standards and identify opportunities for architectural and UX differentiation, the team surveyed two prominent production applications in the food rescue domain: **Too Good To Go** and **Yindii**.

## C.1 Surveyed Product 1: Too Good To Go

* **Platform:** Global Mobile App (iOS / Android)

* **Market:** Over 17 European countries and North America, with 85+ million registered users.

* **Core Philosophy:** Pioneered the concept of the "Magic Bag" (Surprise Bag), letting food businesses monetize surplus inventory.

```
+-----------------------------------------------------------------------+
|                       [SCREENSHOT PLACEHOLDER]                        |
|                                                                       |
|   Figure 1.1: Too Good To Go Home Screen & Interactive Map View       |
|   Caption: Shows location-based merchant discovery with real-time     |
|   distance indicators, pickup countdown timers, and "Sold Out" status.|
+-----------------------------------------------------------------------+


```

```
+-----------------------------------------------------------------------+
|                       [SCREENSHOT PLACEHOLDER]                        |
|                                                                       |
|   Figure 1.2: Too Good To Go Checkout & Swipe-to-Redeem Verification  |
|   Caption: Illustrates the purchase flow and the interactive swipe-up  |
|   gesture used by consumers in-store to validate food handover.       |
+-----------------------------------------------------------------------+


```

### Strengths & Weaknesses of Too Good To Go

* **Strengths:** Intuitive map/list toggle; exceptionally polished micro-animations; strong environmental messaging showing saved CO2 on the user profile.

* **Weaknesses:** Strictly fixed merchant pricing (no dynamic markdown as closing time approaches); lacking localized payment gateways suitable for Vietnamese consumers (relies mainly on international credit cards and Apple Pay); lacks social proof tags for dietary specifics.

## C.2 Surveyed Product 2: Yindii

* **Platform:** Mobile Application (iOS / Android)

* **Market:** Southeast Asia (Thailand, expanding to urban Vietnam).

* **Core Philosophy:** Targets premium bakeries, hotels, and organic grocery markets offering high-end surplus meals at 50%–70% discount.

```
+-----------------------------------------------------------------------+
|                       [SCREENSHOT PLACEHOLDER]                        |
|                                                                       |
|   Figure 2.1: Yindii Merchant Feed & Flash-Deal Badges               |
|   Caption: Displays visual flash deals with category tags (Bakery,    |
|   Hotels, Vegan) and countdown clocks showing remaining hours.       |
+-----------------------------------------------------------------------+


```

```
+-----------------------------------------------------------------------+
|                       [SCREENSHOT PLACEHOLDER]                        |
|                                                                       |
|   Figure 2.2: Yindii Order Details & In-Store Pickup Guide            |
|   Caption: Displays order receipt with store pickup guidelines,       |
|   operating hours, and in-app customer support hotline.               |
+-----------------------------------------------------------------------+


```

### Strengths & Weaknesses of Yindii

* **Strengths:** Tailored to Southeast Asian lifestyle and food culture; attractive food photography; incorporates delivery options alongside self-pickup.

* **Weaknesses:** Delivery fees frequently exceed food discount savings; app performance suffers from sluggish map rendering; no AI recommendation algorithm; manual order verification creates bottleneck queues during closing peak hours.

## C.3 Feature Matrix & Cross-Comparison

| Evaluation Dimension | Too Good To Go | Yindii | Proposed EcoBite Platform | 
| ----- | ----- | ----- | ----- | 
| **Primary Platforms** | iOS / Android | iOS / Android | iOS / Android (Mobile-First) + Admin Web | 
| **Surprise Bag Concept** | Yes (Core feature) | Yes (Mixed with itemized items) | Yes (Surprise Bag + Specific Tagging) | 
| **Pricing Model** | Fixed 67% markdown | Fixed 50%–70% discount | **AI Dynamic Markdown (Time-decay pricing)** | 
| **Order Handover Method** | In-app Swipe button | Manual receipt verification | **Cryptographic QR Code Scanning** | 
| **Recommendation Engine** | Basic distance sorting | Basic category filtering | **AI Context-Aware Recommendation System** | 
| **Payment Integration** | Stripe / Apple Pay / PayPal | Local Thai Cards / PromptPay | **MoMo, ZaloPay, VNPay, Card, Cash-reserve** | 
| **Gamification & Social** | Personal CO2 stats | Impact badges | **CO2 Leaderboards, Badges, Student Perks** | 
| **Target Localization** | Western European/US | Southeast Asia (Bangkok) | **Vietnam Campuses & Urban Retail Density** | 

## C.4 Competitive Edge & Innovation of EcoBite

1. **Dynamic Time-Decay Pricing (AI-Driven):** Unlike competitors who lock prices 24 hours in advance, EcoBite allows AI to dynamically slash prices deeper in the final 30 minutes of a store's operation, guaranteeing zero food waste.

2. **Cryptographic QR Verification:** Eliminates dispute risks and accidental double-swiping by requiring the merchant to scan a verifiable QR token.

3. **Hyper-Localized Student Ecosystem:** Integrated with popular Vietnamese campus nodes and domestic e-wallets (MoMo, ZaloPay) with micro-incentives for student community champions.

## C.5 Adopted UI/UX Patterns

From the competitor survey, EcoBite will adopt and adapt the following proven UI/UX paradigms:

* **Real-Time Pickup Countdown Pills:** High-contrast countdown indicators (e.g., `Pickup in: 00:45:12`) to reinforce urgency.

* **Unified Map & Bottom-Sheet List View:** Seamlessly toggle between map clustering and card feeds without page reloads.

* **High-Impact Green Carbon Badges:** Visually rewarding consumers post-pickup with celebratory milestone graphics.

# SECTION D: TEAM CONTRACT

> **Task Assignment:**
>
> *Performed by:* Đàng Thế Tony, Phùng Quốc Huy | *Reviewed by:* Đặng Trọng Phúc | *Edited by:* Võ Ngọc Thịnh

This Team Contract represents a binding commitment between all members of **Group 05** for the duration of the CS300 coursework.

## D.1 Team Roles & Responsibilities

In accordance with course regulations, all members operate as **Full-Stack Engineers** participating in coding, testing, and documentation. However, dedicated leadership responsibilities are distributed to ensure accountability:

* **Võ Ngọc Thịnh (Team Leader & Lead Architect):**

  * Facilitates Scrum ceremonies, manages Jira sprint backlogs, and oversees overall system architecture.

  * Leads backend core services, database schemas, and API gateway design.

* **Đặng Trọng Phúc (Lead Mobile Frontend Engineer):**

  * Manages UI component libraries, navigation architecture, and client-side state management.

  * Leads implementation of Geolocation mapping and QR Code presentation modules.

* **Phùng Quốc Huy (Lead QA & DevOps Engineer):**

  * Configures automated CI/CD pipelines, Git branch policies, and automated unit/integration testing suites.

  * Leads implementation of QR scanner validation, notification dispatchers, and test reporting.

* **Đàng Thế Tony (Lead AI & Data Engineer / UI/UX Co-Lead):**

  * Formulates and implements the AI Dynamic Pricing algorithms and recommendation heuristic logic.

  * Coordinates UX user research, wireframes, and design consistency across all screens.

## D.2 Communication Plan & Meeting Cadence

* **Primary Asynchronous Channel:** Private Discord Server (categorized into `#announcements`, `#dev-frontend`, `#dev-backend`, `#jira-git-feed`). Urgent matters are coordinated via an emergency Zalo group.

* **Meeting Schedule:**

  * **Sprint Planning Meeting:** Held on the first Monday of each Sprint (PA cycle) at 20:00 via Google Meet (60 mins).

  * **Weekly Scrum Standups:** Held twice a week (Wednesday & Saturday at 21:00) lasting 15 minutes.

  * **Sprint Review & Retrospective:** Held at the conclusion of each Sprint before assignment submission.

* **Response SLA (Service Level Agreement):**

  * Members must acknowledge routine messages on Discord within **4 hours** during daytime (08:00 - 22:00).

  * Urgent blockers (`@urgent`) must be responded to within **1 hour**.

## D.3 Work Schedule, Sprints & Deadlines

* Project progression is governed by the bi-weekly Sprint cycle mirroring each PA milestone.

* **Internal "Soft Deadline":** Set **48 hours prior** to the official Moodle submission deadline. This window is strictly reserved for integration testing, cross-reviewing Markdown reports, and converting documentation to PDF.

* Any member anticipating unavoidable delays must notify the group in Discord at least **24 hours in advance**.

## D.4 Code & Documentation Standards

* **Version Control Protocol:** Trunk-Based / Feature Branch workflow (`feature/<jira-ticket-id>-description`). Direct commits to `main` or `develop` are strictly prohibited and blocked by branch protection rules.

* **Code Reviews:** Every Pull Request (PR) requires a minimum of **one approving peer review** from another team member before merging. PRs must pass all automated linting checks (ESLint / Prettier).

* **Documentation:** All documentation must be written in strict **English Markdown format**, utilizing **Mermaid diagrams** for visual models as mandated by course guidelines.

* **Security Rule:** Never commit API keys, environment credentials, or secrets to Git.

## D.5 Accountability, Performance & Peer Evaluation

* **Definition of Done (DoD):** A task in Jira is marked `Done` only when code is written, unit-tested, documented, reviewed via PR, and merged into the development branch.

* **Peer Evaluation Rubric:** Team contributions will be tracked quantitatively via Git commit metrics, Jira resolution logs, and Sprint retrospective peer evaluations (scale 1.0 to 5.0).

* **Penalty Protocol for Non-Performance:**

  * *1st Occurrence:* Informal verbal warning during Scrum meeting.

  * *2nd Occurrence:* Formal written notification recorded in sprint minutes with reassignment of critical tasks.

  * *3rd Occurrence:* Formal escalation to course Instructors / Teaching Assistants for individual grade penalties.

## D.6 Decision-Making Protocol

1. **Consensus-Seeking:** Technical and design decisions are first debated openly to achieve unanimous consensus.

2. **Majority Voting:** If consensus cannot be reached within 20 minutes, a democratic vote is conducted (simple majority of 3/4).

3. **Leader Tie-Breaker:** In the event of a 2-2 tie, the Team Leader (**Võ Ngọc Thịnh**) exercises the decisive vote in alignment with project deadlines and architectural stability.

## D.7 Conflict Resolution Mechanism

* **Step 1 (Direct 1-on-1 Dialogue):** Conflicting parties engage in an objective discussion focused on software requirements rather than personal bias.

* **Step 2 (Internal Team Mediation):** The entire group convenes an extraordinary meeting moderated by the Team Leader to evaluate technical trade-offs.

* **Step 3 (Instructor Escalation):** If internal resolution fails within 48 hours, the team officially submits an advisory request to the Teaching Assistant or Course Lecturer.

## D.8 Review & Contract Revision Policy

This contract is reviewed at the conclusion of each Sprint Retrospective. Adjustments require unanimous agreement of all 4 team members and must be logged in the project repository.

# SECTION E: DEVELOPMENT TOOLS & PROCESS SETUP

> **Task Assignment:**
>
> *Performed by:* Võ Ngọc Thịnh, Phùng Quốc Huy | *Reviewed by:* Đàng Thế Tony | *Edited by:* Đặng Trọng Phúc

## E.1 Agile/Scrum Workflow Integration

Group 05 strictly adopts the **Agile/Scrum framework** across the semester:

* **Sprint Duration:** 2 to 3 weeks corresponding to each Project Assignment (PA1 through PA5).

* **Sprint Ceremonies:**

  * 1x Sprint Planning (Backlog grooming, story pointing, task assignment).

  * 2x Scrum Check-ins (Blocker removal, sprint velocity check).

  * 1x Sprint Review & Retrospective (Demoing working increments, identifying process enhancements).

## E.2 Toolchain & Infrastructure Setup

The team has established and verified the required course infrastructure:

| Category | Designated Tool | Group Workspace / URL | Purpose | 
| ----- | ----- | ----- | ----- | 
| **Course Submissions** | Moodle | HCMUS Courses Portal | Official deliverable submission | 
| **Class Discussion** | FB Group / Forum | Course Official Group | General announcements & Q&A | 
| **Team Communication** | Discord & Zalo | Group 05 Server | Daily collaboration & meetings | 
| **Task Management** | Jira Software | `ecobite-hcmus.atlassian.net` | Scrum sprint board & issue tracking | 
| **Version Control** | GitHub (Private) | `github.com/hcmus-cs300-g05/ecobite` | Source code & documentation repo | 
| **Spec-Driven Dev** | Spec Kit | Local CLI / Repository setup | Specification-to-code workflow | 
| **AI Coding Assistance** | GitHub Copilot / Cursor | Student Verified Accounts | AI-assisted development | 

## E.3 Git Repository Structure & Conventions

The private GitHub repository is organized according to the instructor-recommended layout:

```
ecobite-repository/
├── .github/
│   └── workflows/              # Automated CI/CD, linting, tests
├── /src                        # Application Source Code
│   ├── /mobile-client          # React Native / Flutter Consumer & Merchant App
│   ├── /server                 # Backend REST/GraphQL API & Database Schemas
│   └── /ai-engine              # Pricing regression & Recommendation modules
├── /docs                       # Central Text-Based Markdown Documentation
│   ├── /management             # Weekly reports, sprint reviews, team contract
│   ├── /requirements           # Vision document, use cases, actor specifications
│   ├── /analysis-and-design    # Architecture blueprints, diagrams, UI wireframes
│   └── /test                   # Test plans, automated test cases, QA logs
├── .gitignore
├── README.md
└── LICENSE


```

### Git Commit Conventions

The team strictly follows the **Conventional Commits** specification:

* `feat(scope): add new feature` (e.g., `feat(auth): implement jwt token generation`)

* `fix(scope): resolve bug` (e.g., `fix(qr): fix verification token expiration check`)

* `docs(scope): update documentation` (e.g., `docs(pa1): finalize section b proposal`)

* `test(scope): add automated tests` (e.g., `test(pricing): unit test time decay discount`)

## E.4 Task Management (Jira Setup)

The team has configured the Jira workspace with the following mandatory fields:

1. **1-to-1 Assignee Rule:** Every task is assigned to strictly one responsible member.

2. **Date Lifecycle:** Every issue contains `Created Date`, `Start Date`, and `Resolution Date`. Tasks are never backfilled post-completion.

3. **Scrum Issue Types:** Epics (representing Functional Groups) -> User Stories -> Subtasks & Bugs.

```
+-----------------------------------------------------------------------+
|                       [SCREENSHOT PLACEHOLDER]                        |
|                                                                       |
|   Figure E.1: Jira Scrum Board & Sprint Backlog Setup                 |
|   Caption: Overview of the Group 05 Jira board displaying PA1 tasks,   |
|   assigned members, story points, and sprint status columns.          |
+-----------------------------------------------------------------------+


```

## E.5 Spec Kit & AI Coding Tool Accounts

* **Spec Kit Preparation:** The repository is configured to receive Spec Kit specification templates starting from PA2.

* **AI Coding Verification:** All 4 team members have secured verified educational subscriptions for AI development environments:

  * **Võ Ngọc Thịnh:** GitHub Copilot Student Pack (Verified) & Cursor Pro.

  * **Đặng Trọng Phúc:** GitHub Copilot Student Pack (Verified).

  * **Phùng Quốc Huy:** GitHub Copilot Student Pack (Verified).

  * **Đàng Thế Tony:** GitHub Copilot Student Pack (Verified) & Cursor Pro.

```
+-----------------------------------------------------------------------+
|                       [SCREENSHOT PLACEHOLDER]                        |
|                                                                       |
|   Figure E.2: Team AI Account Verification Proofs                     |
|   Caption: Combined screenshot confirming GitHub Copilot / Cursor     |
|   active educational licenses for all 4 team members.                 |
+-----------------------------------------------------------------------+


```

# APPENDIX & REFERENCES

### Academic & Regulatory References

1. *CS300 Introduction to Software Engineering - Project Assignment 1 (PA1-2026) Guidelines*, Faculty of Information Technology, University of Science, VNU-HCM.

2. *Agile Software Engineering with Scrum*, Ken Schwaber & Mike Beedle.

3. *Sustainable Development Goal 12: Responsible Consumption and Production*, United Nations (Target 12.3: Halving per capita global food waste).

### Team Sign-off

By affixing digital consent below, all members of **Group 05** certify that they have reviewed, contributed to, and agreed with the contents of this report and the Team Contract:

* **Võ Ngọc Thịnh** *(Team Leader)* — *Signed*

* **Đặng Trọng Phúc** — *Signed*

* **Phùng Quốc Huy** — *Signed*

* **Đàng Thế Tony** — *Signed*