# Section B: Project Proposal (Updated Architecture v2.1.0)
**Course**: CS300 - Software Engineering / Advanced Software Development
**Group**: Group 05
**Project**: EcoBite - Smart Surplus Food Rescue Platform

---

## B - Project Proposal (10 points)

### 1. Introduction
**EcoBite** is an Online-to-Offline (O2O) smart surplus food rescue platform engineered to bridge the gap between commercial food establishments—including restaurants, bakeries, cafes, and supermarkets—and local consumers seeking high-quality meals at deeply discounted prices (40% to 70% off).

Globally and particularly in urban Vietnam, millions of tons of freshly prepared, hygienic meals are discarded daily simply because they remain unsold at the end of business shifts. This systemic inefficiency causes direct financial loss for food and beverage (F&B) businesses and inflicts catastrophic environmental damage, as decomposing organic food waste in municipal landfills generates potent greenhouse gases ($\text{CH}_4$ and $\text{CO}_2$).

EcoBite addresses this crisis with a pragmatic, transparent, and technology-driven approach:
- **Transparent Dish-Level Rescuing (No Mystery/Surprise Bags)**: Unlike Western platforms (e.g., Too Good To Go) relying on randomized "surprise bags" that struggle in the Vietnamese market due to local dining habits and dietary sensitivities, EcoBite mandates transparent listings of **specific surplus dishes** with clear photos, standard ingredient disclosures, and verified allergen warnings.
- **Deterministic Rule-Based Time-Shift Discounting**: Prices are governed by transparent, rule-based time schedules (e.g., 40%–50% during standard rescue windows, transitioning automatically to 60%–70% in the final 30–45 minutes before closing), providing predictability for merchants and maximizing clearance rates.
- **Dual AI Intelligence Suite (Powered by Google Gemini 2.5 Flash)**: Integrates native multimodal audio/NLP to empower busy merchants to batch-post end-of-shift surplus dishes in under 3 seconds with two-tier allergen screening, alongside a hybrid context-aware recommendation engine delivering personalized meal rescue suggestions to consumers.

---

### 2. Target Users and Environments

#### 2.1. Target Users
1. **Consumers (Food Rescuers)**: University students, young professionals, office workers, budget-conscious individuals, and eco-minded citizens looking for delicious, hygienic meals at affordable rates while actively participating in reducing urban food waste.
2. **Store Partners (Merchants)**: Local bakeries, cafes, family-owned lunch eateries, noodle houses, and supermarkets seeking to recover ingredient and labor costs from unsold daily inventory, minimize waste disposal fees, and attract new local patrons.
3. **System Administrators**: The platform operations team responsible for reviewing merchant food safety certificates (ATVSTP) and business licenses, moderating menu listings, monitoring transactions, mitigating disputes, and tracking aggregate environmental metrics.

#### 2.2. Target Environments
- **Client Application**: Cross-platform, fully responsive Progressive Web Application (PWA) built with **Next.js 14 (App Router)** and **Tailwind CSS**, optimized for mobile browsers (Apple Safari on iOS, Google Chrome on Android) as well as modern desktop environments (Windows, macOS, Linux).
- **Backend Infrastructure**: Containerized micro-services powered by **FastAPI (Python 3.11)** with asynchronous I/O, **PostgreSQL 16 with PostGIS** for spatial geospatial queries, **Redis 7** for caching, rate limiting, and distributed atomic locking, and **Google GenAI SDK** for Gemini 2.5 Flash model invocation.

---

### 3. Key Features (Core Platform Operations)

#### Feature 1: Authentication & Merchant Onboarding (KYC & Food Safety Verification)
* **Function**: Secure authentication via Email/Password and Google OAuth2 with Role-Based Access Control (`CONSUMER`, `STORE_PARTNER`, `ADMIN`) utilizing short-lived JWT access tokens and HTTP-Only refresh cookies. Merchants must upload official Food Safety Certificates (Giấy chứng nhận ATVSTP) and business credentials, subject to mandatory administrator audit and approval before publishing rights are granted.
* **Value**: Establishes end-to-end community trust, ensuring that all discounted surplus food originates from legitimate, hygienic, and government-certified food establishments.

#### Feature 2: Base Menu Catalog & Surplus Dish Management
* **Function**: Merchants maintain a persistent **Base Menu Catalog (`menu_items`)** containing standardized high-resolution photos, original retail prices, and ingredient baselines. At the close of each shift, merchants instantiate active **Surplus Dishes (`dishes`)** specifying remaining quantities, pickup windows (`pickup_start` to `pickup_end`), and optional fixed clearance pricing.
* **Value**: Eliminates the burden of re-creating dishes from scratch, ensuring that surplus listings always feature appetizing, authentic photos and accurate baseline pricing.

#### Feature 3: Rule-Based Time-Shift Discounting Engine
* **Function**: Executes deterministic, time-decay pricing rules without unpredictable black-box AI price speculation. Dishes automatically transition through predefined tiers:
  1. *Standard Rescue Window*: 40% to 50% discount off retail price.
  2. *Final Rush Clearance (Last 30–45 minutes)*: Deep clearance discount (up to 70% off) accompanied by a live visual countdown timer.
  3. *Merchant Fixed Price Override*: Supports manual flat-rate pricing (e.g., "Clearance at 20,000 VND") when specified.
* **Value**: Delivers clear price transparency for consumers and drives urgency to clear 100% of perishable inventory before kitchen shutdown.

#### Feature 4: Location-Based Search & PostGIS Radar Discovery
* **Function**: Leverages PostgreSQL PostGIS spatial functions (`ST_DWithin`, `ST_Distance`) and GIST spatial indexing to calculate real-time distances between consumers and nearby stores within a 1–5 km radius (expandable to 10 km). Features an interactive Leaflet/Mapbox radar map with live map pins, cuisine filters (rice, noodles, bakery, vegan), price sliders, and pickup urgency indicators.
* **Value**: Enables consumers to discover walking-distance food rescue opportunities within seconds, minimizing travel time and ensuring hot meals.

#### Feature 5: Inventory Anti-Overselling Lock & Order Management
* **Function**: Manages the complete consumer checkout lifecycle with strict database-level concurrency control. Employs atomic SQL updates (`UPDATE dishes SET remaining_quantity = remaining_quantity - :qty WHERE remaining_quantity >= :qty`) backed by Redis distributed locking.
* **Value**: Guarantees zero over-selling, eliminating race conditions when multiple consumers attempt to purchase the final available meal simultaneously.

#### Feature 6: Seamless Cashless Checkout (VNPay Payment Gateway)
* **Function**: Integrates the VNPay payment gateway supporting dynamic VNPAY-QR scanning from mobile banking apps, domestic ATM cards, and e-wallets. Employs cryptographically verified HMAC-SHA512 Instant Payment Notification (IPN) callbacks with idempotent webhook processing.
* **Value**: Facilitates frictionless, cashless transactions suited for young consumers while protecting merchants against payment fraud.

#### Feature 7: Dynamic HMAC-SHA256 Single-Use QR Token & In-Store Web Scanner
* **Function**: Upon order confirmation, the platform generates a dynamic, cryptographically signed QR code containing an HMAC-SHA256 token derived from order identifiers, user identity, a cryptographic nonce, and expiration timestamps. Merchants scan customer QR codes via an integrated web camera scanner (`html5-qrcode`).
* **Value**: The system validates signatures in real time, marks the nonce as used immediately, and prevents screenshot sharing or replay attacks (double-claiming).

#### Feature 8: Verified Reviews, Green Points & Environmental Impact Tracker
* **Function**: Only consumers with verified in-store QR pickups can submit 1-to-5 star ratings and reviews. Concurrently, the platform converts rescued meals into verified ecological metrics ($\approx 2.5\text{ kg } \text{CO}_2\text{e}$ mitigated per 1 kg of rescued food) and credits Green Points to user accounts for voucher redemption on a public Green Leaderboard.
* **Value**: Gamifies sustainable consumer behavior and provides tangible social proof and environmental reporting for participating merchants.

---

### 4. AI Features (AI Intelligence Suite - Powered by Google Gemini 2.5 Flash)

The platform integrates **Google Gemini 2.5 Flash** (leveraging Google AI Studio / Pro Free Tier with 15 RPM and 1,000,000 TPM) through the official `google-genai` SDK, operating under strict Pydantic Structured Outputs.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   ECOBITE AI INTELLIGENCE SUITE                        │
├───────────────────────────────────┬────────────────────────────────────┤
│   AI FEATURE 1: MERCHANT SIDE     │    AI FEATURE 2: CONSUMER SIDE     │
│   Batch Quick-Post & Allergen     │    Smart Recommendation Engine     │
│                                   │                                    │
│ - Native Multimodal Audio Input   │ - Layer 1: PostGIS & SQL Allergen  │
│ - Menu-Catalog Grounding (Photos) │            Hard Filter (Safe)      │
│ - 2-Tier Allergen (14 EU FIC)     │ - Layer 2: Heuristic Multi-Factor  │
│   (Explicit vs. Inferred)         │            Ranking & Urgent Deals  │
│ - Batch Extraction (Multiple items│ - Layer 3: Gemini 2.5 Flash        │
│ - Relative Server-Time Resolution │            Personalized Reasoning  │
│ - 1-Tap Batch Publishing          │ - Natural Language Semantic Search │
└───────────────────────────────────┴────────────────────────────────────┘
```

#### AI Feature 1: Batch Quick-Post Multimodal Assistant & 2-Tier Allergen Guard
* **Function**: Solves the critical operational bottleneck where exhausted kitchen staff lack time to manually type forms at the end of shifts. Merchants simply record a brief conversational voice clip (e.g., *"Hôm nay còn 5 cơm sườn chả, 3 bún thịt nướng xả từ giờ đến 3h chiều nhé"*):
  1. **Native Multimodal Audio Ingestion**: Sends raw audio files directly to Gemini 2.5 Flash without intermediary phone STT, accurately interpreting Vietnamese regional dialects, slang (*"bốn lăm cành"*, *"bì chả"*), and culinary nuances.
  2. **Menu-Catalog Grounding**: Gemini compares extracted dish names against the merchant's Base Menu Catalog (`menu_items`) in the prompt context to assign `matched_menu_id`, automatically inheriting verified dish photos, standard retail prices, and activating rule-based discounts.
  3. **Two-Tier Allergen Guard (14 EU FIC Standards)**:
     - *Explicit Detection*: Captures allergens directly voiced by the merchant (e.g., "contains crushed peanuts").
     - *Inferred Culinary Knowledge*: Autonomously infers hidden allergens based on traditional Vietnamese recipes: e.g., *Cơm sườn chả* contains **Eggs** (in steamed meatloaf) and **Fish** (in fish sauce dip); *Bún thịt nướng* contains **Peanuts** and **Fish** sauce; *Bánh mì* contains **Gluten**.
     - *Local Dietary Notes*: Flags culturally critical preferences (`dietary_notes`): Scallion/Allium presence (*Có mỡ hành*), spicy level, sour pickles, and vegetarian status.
  4. **Batch Extraction & Server-Time Grounding**: Extracts multiple surplus items simultaneously (`List[SurplusDishItem]`) and resolves relative time expressions (*"from now until 3 PM"*) into absolute ISO 8601 timestamps using injected `current_server_time`.
* **Value**: Reduces listing time from 3 minutes per item to under 3 seconds for an entire menu batch, while preventing life-threatening allergic reactions through standardized medical warnings.

#### AI Feature 2: Smart Food Recommendation & Natural Language Semantic Search
* **Function**: Delivers context-aware, personalized surplus meal discovery through a robust 3-layer hybrid architecture:
  1. **Layer 1 - Hard Safety Invariant (SQL & PostGIS)**: Filters available meals within a 1–3 km radius and **strictly excludes 100% of dishes matching the consumer's medical allergy profile** (`excluded_allergens` in `user_preferences`). Medical safety is strictly guaranteed at the database query level and never delegated to probabilistic AI text generation.
  2. **Layer 2 - Multi-Factor Heuristic Scoring**: Ranks candidate meals using an objective weighted composite:
     $$\text{Score} = (0.40 \times \text{Proximity}) + (0.30 \times \text{Discount Depth \& Time Urgency}) + (0.30 \times \text{Taste Profile Match})$$
     Prioritizes **Urgent Rescue Deals** entering the final 30 minutes of 70% clearance to prevent food expiration.
  3. **Layer 3 - Generative AI Personalization**: Top 3 ranked candidate dishes and user taste profiles are submitted to Gemini 2.5 Flash to synthesize a concise, emotionally persuasive justification (20–30 words) displayed on the UI card:
     > *"💡 Recommended for you: You frequently enjoy hot noodle soups for lunch. Quán Phở Bắc (350m away) is currently offering a 67% clearance deal at 18,000 VND with 2 servings left until 13:30—guaranteed 100% peanut-free according to your preferences!"*
  4. **Conversational Semantic Search**: Enables consumers to query using natural language (e.g., *"Find me a comforting warm soup under 30k nearby"*), where Gemini extracts intent, budget, and dietary constraints to filter the PostGIS database.
* **Value**: Maximizes conversion rates, eliminates browsing fatigue for hungry consumers, and rapidly clears perishable items before kitchen closure without compromising consumer health.
