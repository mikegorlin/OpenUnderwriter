# COMPANY Section Design

**Status:** Steps 1-3 complete — Questions, data points, and three-layer breakdown defined
**Date:** 2026-02-16
**Pattern:** This is the pilot section. All 7 sections follow SECTION-DESIGN-TEMPLATE.md.

## Section Purpose

The COMPANY section tells the **story of the company**. When an underwriter finishes reading it, they understand the entity completely — what it does, how it works, how it makes money, how it's built, where it operates, what's happening around it.

**Boundary rules:**
- COMPANY owns: entity identity, business model, operations, structure, geography, transactions, competitive position
- FINANCIAL owns: financial health, capital needs, earnings quality, distress indicators
- LITIGATION owns: lawsuit history, regulatory enforcement, which agencies regulate this entity
- GOVERNANCE owns: people (board, management, compensation, insider activity)
- FORWARD owns: future predictions, alternative data signals, upcoming catalysts

---

## Questions Moved to Other Sections

| Question | Destination | Rationale |
|---|---|---|
| Capital markets access (equity raise, debt refinance) | FINANCIAL | Financial condition question |
| Which agencies regulate this entity | LITIGATION.REGULATORY | Enforcement jurisdiction |
| Litigation history, recidivist pattern, outcomes | LITIGATION | Litigation data |
| Revenue growth rate evaluation | FINANCIAL | Financial performance metric |
| Debt maturity, cash runway, burn rate | FINANCIAL | Financial health |

## Questions Moved Here from Other Sections

| Question | Source | Rationale |
|---|---|---|
| Sector dynamics (performance, consolidation, disruption) | FORWARD.ENVIRONMENT | Describes current landscape, not future prediction |
| Industry-specific metric applicability | FINANCIAL (FIN.SECTOR.*) | Which metrics apply is an identity question; evaluation stays in FINANCIAL |
| Operating leverage, cost structure, capital intensity | Orphaned checks | Fundamental business model questions |
| Goodwill accumulation context | FINANCIAL.DISTRESS | Comes from M&A history; financial impairment eval stays in FINANCIAL |

---

## AREA 1: IDENTITY

*What is this company?*

---

### Q1.1: What industry is this company in and what's the base D&O exposure for this sector?

**Why:** Industry is the single biggest determinant of D&O exposure. Biotech = 7% annual SCA rate; utilities = 1.5%. Sets the starting premium.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| SIC code + description | SEC EDGAR | — | ✅ Have |
| NAICS code | SEC EDGAR | — | ✅ Have |
| Sector code (TECH, BIOT, etc.) | yfinance | SIC range mapping | ✅ Have (no SIC fallback) |
| Industry classification (human-readable) | yfinance | SIC description | ✅ Have |
| Base SCA filing rate by sector | brain/sectors.json | DEFAULT 3.5% | ✅ Have |
| Market cap filing multiplier | brain/sectors.json | 1.0x | ✅ Have |
| Industry allegation theories | config/industry_theories.json | — | ⚠️ Exists, unused |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Base filing rate computation | sector_rate × cap_multiplier | Numeric rate (e.g., 7.8%) |
| High-risk sector flag | base rate > 5% | RED / YELLOW / CLEAR |
| Industry theory lookup | SIC range → applicable D&O theories | Theory list |

**DISPLAY:**

> **Industry:** Technology — Consumer Electronics (SIC 3674, Semiconductors)
> **Sector D&O Base Rate:** 5.0% annual SCA filing probability
> **Size-Adjusted Rate:** 5.0% × 1.56 (mega-cap) = 7.8%
> **Industry-Specific D&O Theories:** Patent disclosure, guidance dependency, supply chain misrepresentation

---

### Q1.2: How big is this company?

**Why:** Size determines claim severity (settlement amounts scale with market cap), regulatory scrutiny level, and exposure scale.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Market capitalization | yfinance | — | ✅ Have |
| Revenue TTM | SEC financials | yfinance | ✅ Have (check field_key broken) |
| Employee count | yfinance | 10-K LLM extraction | ✅ Have |
| Filer category (LAF/AF/NAF/SRC) | SEC DEI | Derived from market cap | ✅ Have |
| Exchange (NYSE/NASDAQ/etc.) | yfinance | SEC EDGAR | ✅ Have |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Size tier | MICRO <$300M, SMALL <$2B, MID <$10B, LARGE <$50B, MEGA >$50B | Tier label |
| Severity multiplier | Tier → multiplier from sectors.json | Numeric (e.g., 1.56x) |
| Employment litigation flag | >10K employees = elevated employment class action exposure | Flag |

**DISPLAY:**

> **Size Tier:** MEGA CAP ($3.4T market cap)
> **Revenue:** $394B TTM | **Employees:** 164,000 | **Filer:** Large Accelerated
> **Exchange:** NASDAQ
> **Severity Multiplier:** 1.56x (mega-cap average settlement scaling)

---

### Q1.3: What risk archetype does this company fit?

**Why:** Companies of same size/industry still differ. A growth darling, a distressed company, and a stable mature company each need different treatment. Archetype adjusts the base rate.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Risk archetype classification | SCORE stage (allegation_mapping.py) | — | ⚠️ Computed but not stored in CompanyProfile |
| Classification evidence | SCORE stage | — | ⚠️ Same — disconnected |
| Growth rate | → FINANCIAL cross-reference | — | ✅ Available |
| Valuation multiples | → FINANCIAL / MARKET cross-ref | — | ✅ Available |
| Cash burn / pre-revenue flag | → FINANCIAL cross-reference | — | ✅ Available |
| Distress indicators | → FINANCIAL cross-reference | — | ⚠️ Partial |
| Pending regulatory decision | 10-K Item 1A | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Archetype assignment | Priority chain: DISTRESSED → BINARY_EVENT → GROWTH_DARLING → GUIDANCE_DEPENDENT → REGULATORY_SENSITIVE → TRANSFORMATION → STABLE_MATURE | Primary + secondary archetype |
| Evidence collection | Which signals triggered the classification | Evidence list |
| Archetype rate multiplier | Archetype → multiplier (e.g., GROWTH_DARLING = 1.3x, STABLE_MATURE = 0.7x) | Numeric |

**DISPLAY:**

> **Risk Archetype:** GROWTH_DARLING (primary), GUIDANCE_DEPENDENT (secondary)
> **Evidence:** Premium valuation (45x P/E), high analyst coverage, history of guidance-driven stock moves
> **Archetype-Adjusted Rate:** 7.8% × 1.3 = 10.1%

---

### Q1.4: How long has it been public, and is it a SPAC or de-SPAC?

**Why:** IPO <3yr = 4x claim rate. De-SPAC <24mo = critical risk. SPACs were #1 SCA source 2022-2024.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| IPO date | yfinance (firstTradeDateMilliseconds) | SEC EDGAR first filing | ✅ Have |
| Years public | Derived from IPO date | — | ✅ Have |
| SPAC/de-SPAC indicators | 8-K Item 1.01 + 10-K | — | ❌ Missing |
| De-SPAC merger date | 8-K | — | ❌ Missing |
| Original SPAC projections | S-4 / proxy | — | ❌ Missing |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| IPO risk period | <3yr = RED, 3-7yr = YELLOW, >7yr = CLEAR | Risk flag |
| SPAC detection | Keywords/patterns in 8-K, 10-K (blank check, SPAC, de-SPAC, business combination) | Boolean + age |
| De-SPAC projection comparison | Original projections vs actual results | Projection miss % |

**DISPLAY:**

> **Public Since:** 2012 (14 years) ✅ Past IPO danger zone
> **SPAC Status:** Not a SPAC/de-SPAC ✅

---

## AREA 2: BUSINESS MODEL & REVENUE

*How does this company make money?*

---

### Q2.1: What's the business model and revenue model?

**Why:** Revenue model determines which fraud patterns are possible. Subscription = churn manipulation. Project-based = completion percentage manipulation. Licensing = channel stuffing. The model defines the risk surface.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Business description | 10-K Item 1 LLM | yfinance longBusinessSummary | ✅ Have |
| Revenue model type | 10-K Item 1 LLM extraction | — | ❌ No extraction |
| Business model classification | Derived from description + financials | — | ❌ Not computed |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Revenue model classification | Categorize: subscription, transactional, project, licensing, advertising, marketplace, hardware+services, mixed | Model type |
| Fraud pattern tagging | Model type → applicable fraud patterns (subscription → churn manipulation, project → completion %, licensing → channel stuffing) | Applicable pattern list |
| Model risk tier | Project-based/percentage-of-completion = HIGH; subscription = LOW; mixed = MEDIUM | Risk tier |

**DISPLAY:**

> **Business Model:** Consumer electronics manufacturer + digital services platform
> **Revenue Model:** Hardware sales (product) + subscription services (services)
> **Applicable Fraud Patterns:** Revenue timing (hardware), subscriber count manipulation (services)
> **Model Risk:** MEDIUM (mixed model with recurring component)

---

### Q2.2: How is revenue broken down by segment?

**Why:** Segment concentration = fragility. >50% from one segment means one disruption is existential. Also identifies which business lines matter most for D&O exposure.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Revenue segments (name, amount, %) | 10-K LLM extraction | 10-K XPath tables | ⚠️ Partial (AAPL gets 0) |
| Segment growth rates | Multi-period 10-K comparison | — | ❌ Not computed |
| Segment profitability | 10-K segment disclosures | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Segment concentration | Top segment % of total: >70% = RED, >50% = YELLOW, <50% = CLEAR | Risk flag |
| Segment trend | Declining segment >10% of revenue = flag | Trend flag |
| Single-segment dependency | Only 1 reportable segment = inherent concentration | Flag |

**DISPLAY:**

> | Segment | Revenue | % of Total | Trend |
> |---|---|---|---|
> | iPhone | $205B | 52% | ⚠️ Declining |
> | Services | $96B | 24% | Growing |
> | Mac | $30B | 8% | Stable |
> | iPad | $29B | 7% | Stable |
> | Wearables | $34B | 9% | Declining |
>
> **Concentration:** ⚠️ YELLOW — iPhone represents 52% of revenue

---

### Q2.3: How is revenue broken down by geography?

**Why:** Geographic revenue concentration determines FX risk, jurisdictional litigation exposure, and vulnerability to country-specific disruptions (trade policy, sanctions, regulatory changes).

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Revenue by region/country | 10-K geographic segment disclosure | — | ⚠️ Partial |
| Geographic revenue percentages | Derived | — | ⚠️ Partial |
| Operating countries | Exhibit 21 subsidiary list | — | ⚠️ Fragile parsing |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Geographic concentration | >50% from single non-US market = RED; >30% = YELLOW | Risk flag |
| International mix | >50% international = elevated complexity flag | Flag |
| High-risk market exposure | Revenue from sanctioned/unstable markets | Flag |

**DISPLAY:**

> | Region | Revenue | % of Total |
> |---|---|---|
> | Americas | $170B | 43% |
> | Europe | $99B | 25% |
> | Greater China | $75B | 19% |
> | Japan | $24B | 6% |
> | Rest of Asia Pacific | $26B | 7% |
>
> **International Mix:** 57% non-Americas
> **Concentration:** No single non-US market >30% ✅
> **Note:** China exposure (19%) creates trade policy sensitivity

---

### Q2.4: How does revenue convert to earnings?

**Why:** Operating leverage determines how revenue misses amplify into earnings misses. High fixed costs mean a 10% revenue decline becomes a 30% earnings decline — directly amplifies SCA risk. Capital intensity affects impairment/writeoff exposure.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Cost structure (fixed vs variable) | 10-K LLM extraction | — | ❌ No extraction |
| Operating leverage assessment | 10-K + financials | — | ❌ No extraction |
| Gross margin | → FINANCIAL cross-reference | — | ✅ Available |
| Operating margin | → FINANCIAL cross-reference | — | ✅ Available |
| Capital intensity (CapEx/Revenue) | Derived from financials | — | ❌ Not computed |
| R&D intensity (R&D/Revenue) | Derived from financials | — | ❌ Not computed |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Operating leverage tier | >60% fixed costs = HIGH, 40-60% = MEDIUM, <40% = LOW | Tier |
| Earnings amplification factor | Estimated from operating leverage | "10% revenue miss → ~X% earnings decline" |
| Capital intensity flag | CapEx/Revenue >15% = capital-intensive flag | Flag |
| R&D intensity flag | R&D/Revenue >20% = high R&D flag (positive for innovation, risk for capitalization) | Flag |

**DISPLAY:**

> **Cost Structure:** ~60% fixed (manufacturing, R&D, retail stores) / 40% variable
> **Operating Leverage:** HIGH — a 10% revenue miss would result in ~25% earnings decline
> **Capital Intensity:** CapEx/Revenue 4% (LOW — asset-light relative to revenue)
> **R&D Intensity:** R&D/Revenue 8% ($30B annually)
> **Margin Profile:** 46% gross, 30% operating (→ see FINANCIAL for trend analysis)

---

### Q2.5: What are the key products or services driving the business?

**Why:** Product concentration creates event risk. A company dependent on one product (single drug, single platform) is vulnerable to a single adverse event. Product lifecycle stage matters — aging products without successors signal future revenue pressure.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Key products/services list | 10-K Item 1 LLM extraction | — | ❌ Not specifically extracted |
| Product revenue attribution | 10-K segment/product disclosure | — | ⚠️ Overlaps with Q2.2 segments |
| Product lifecycle stage | 10-K + news | — | ❌ Not extracted |
| Upcoming product transitions | 10-K + 8-K + news | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Product concentration | >50% revenue from single product = YELLOW, >70% = RED | Flag |
| Lifecycle risk | Aging product + no disclosed successor = YELLOW | Flag |
| Transition risk | Mid-major-transition = elevated event risk | Flag |

**DISPLAY:**

> **Key Products/Services:**
> 1. iPhone (52% of revenue) — mature product, annual refresh cycle
> 2. Services (24%) — growing, high-margin, subscription-based
> 3. Mac (8%) — mature, transitioning to Apple Silicon
> 4. Wearables (9%) — growth stage
>
> **Product Concentration:** ⚠️ iPhone >50% — single-product dependency
> **Lifecycle:** No major product sunset risk; Services growing as revenue diversifier

---

## AREA 3: OPERATIONS & DEPENDENCIES

*How does it work, and what can break?*

---

### Q3.1: What are the critical customer dependencies?

**Why:** >20% revenue from one customer = structural fragility. Customer loss → revenue cliff → stock drop → lawsuits.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Customer concentration disclosure | 10-K Item 1/7 regex + LLM | — | ✅ Have |
| Top customer % of revenue | 10-K | — | ✅ Have |
| Named customers (if disclosed) | 10-K | — | ⚠️ Sometimes extracted |
| Contract terms / renewal dates | 10-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Customer concentration | >20% from single customer = RED, >10% = YELLOW | Risk flag |
| Named customer risk | Named customer = assessable; unnamed = opaque | Flag |
| Contract renewal risk | Major customer contract expiring within 12mo = flag | Flag |

**DISPLAY:**

> **Customer Concentration:** No single customer >10% of revenue ✅
> **Distribution:** Broad consumer + enterprise base through retail and carrier channels
> **Contract Risk:** No disclosed material customer contract renewals pending

---

### Q3.2: What are the critical supply chain dependencies?

**Why:** Single-source suppliers are failure points. If the sole supplier of a critical component fails, the business stops. Supply chain geographic concentration (e.g., all suppliers in one country) amplifies geopolitical risk.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Supplier concentration | 10-K Item 1/7 regex + LLM | — | ✅ Have |
| Single-source suppliers | 10-K | — | ✅ Have |
| Key components + suppliers | 10-K Item 1 | — | ❌ Not extracted as structured list |
| Supply chain geography | 10-K + Exhibit 21 | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Single-source critical supplier | Sole supplier for critical component = RED | Risk flag |
| Multiple single-sources | >2 single-source dependencies = compound risk | Flag |
| Geographic supply chain concentration | >70% of suppliers in one country = YELLOW | Flag |

**DISPLAY:**

> **Key Supply Chain Dependencies:**
> 1. ⚠️ TSMC — sole fabricator for A-series and M-series chips (CRITICAL single-source)
> 2. ⚠️ Samsung Display — primary OLED supplier (limited alternatives)
> 3. Assembly concentrated in China/India (Foxconn, Pegatron)
>
> **Supply Chain Risk:** ⚠️ HIGH — critical semiconductor dependency on single source

---

### Q3.3: What are the technology and platform dependencies?

**Why:** Cloud provider lock-in, GPU access constraints, data center dependencies. For AI companies, compute access is existential. Platform dependencies can also create competitive risk (building on a competitor's platform).

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Cloud provider dependencies | 10-K Item 1A risk factors | — | ❌ Not extracted |
| Key technology platforms | 10-K Item 1 | — | ❌ Not extracted |
| GPU/compute dependencies | 10-K | — | ❌ Not extracted |
| Data center arrangements | 10-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Single cloud provider dependency | >80% on one provider = RED | Flag |
| Hyperscaler dependency | AI company without own compute = YELLOW | Flag |
| Platform risk | Building core business on competitor's platform = flag | Flag |

**DISPLAY:**

> **Technology Dependencies:** Own infrastructure (proprietary chips, own data centers, own cloud services) ✅
> **Platform Risk:** LOW — vertically integrated technology stack
> **Note:** Apple is a platform provider, not platform-dependent

---

### Q3.4: What are the key person dependencies?

**Why:** Founder-led companies with no succession plan have key person risk. A key individual's departure can trigger stock drops. Also matters for companies where a single visionary drives strategy.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| CEO/founder status | DEF14A + public information | — | ⚠️ Have exec list |
| Key person risk disclosures | 10-K Item 1A | — | ❌ Not extracted |
| Succession planning disclosure | DEF14A / 10-K | — | ❌ Not extracted |
| Management bench depth | DEF14A executive list | — | ⚠️ Have list, no assessment |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Founder-led flag | Current CEO = founder | Flag |
| Key person risk | Founder-led + no disclosed succession = RED; Founder-led + succession plan = YELLOW; Professional management = CLEAR | Risk level |
| → Cross-reference | GOVERNANCE.MANAGEMENT for full executive profiles | Link |

**DISPLAY:**

> **Key Person Risk:** LOW — Tim Cook (CEO since 2011) is professional management, not founder
> **Succession:** Deep management bench (SVPs of each major product line)
> **→ See GOVERNANCE.MANAGEMENT for full executive assessment**

---

### Q3.5: What are the regulatory and licensing dependencies?

**Why:** A business that requires specific licenses, approvals, or permits to operate faces existential risk from regulatory decisions. FDA approval, banking charter, spectrum license — loss of any means the business stops. Different from enforcement risk (LITIGATION) — this is about what the business needs to exist.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Required licenses/approvals | 10-K Item 1 / Item 1A LLM | — | ❌ Not extracted |
| Pending regulatory decisions | 10-K / 8-K | — | ❌ Not extracted |
| License renewal schedule | 10-K | — | ❌ Not extracted |
| Industry regulatory intensity | config/industry_theories.json | — | ⚠️ Partial |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Single regulatory gate | Business depends on one approval = HIGH (pharma FDA, telecom FCC) | Risk level |
| Pending decision flag | Major decision pending = event risk | Flag |
| Regulatory intensity | Industry requires multiple ongoing licenses = complexity flag | Flag |
| → Cross-reference | LITIGATION.REGULATORY for enforcement risk | Link |

**DISPLAY:**

> **Regulatory Dependencies:** App Store faces antitrust scrutiny (Epic Games, EU DMA)
> **Pending Decisions:** EU Digital Markets Act compliance deadline
> **Industry Regulation:** MODERATE — consumer electronics, not FDA/FDIC-regulated
> **→ See LITIGATION.REGULATORY for enforcement actions**

---

## AREA 4: CORPORATE STRUCTURE & COMPLEXITY

*How is it organized?*

---

### Q4.1: How complex is the legal entity structure?

**Why:** More subsidiaries across more jurisdictions = more places to hide things = higher fraud risk. Also increases litigation surface area and regulatory compliance burden.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Subsidiary count | Exhibit 21 | 10-K disclosure | ✅ Have |
| Subsidiary jurisdictions | Exhibit 21 parsing | — | ⚠️ Fragile parsing |
| Jurisdiction count | Derived from Exhibit 21 | — | ⚠️ Partial |
| Holding company layers | 10-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Entity complexity tier | >200 subs = HIGH, >50 = MEDIUM, <50 = LOW | Tier |
| Jurisdictional spread | >20 countries = HIGH, >10 = MEDIUM | Flag |
| Tax haven presence | Cross-ref with config/tax_havens.json | Flag |

**DISPLAY:**

> **Subsidiaries:** 398 entities across 28 jurisdictions
> **Complexity Tier:** HIGH (>200 subsidiaries, >20 jurisdictions)
> **Tax Haven Presence:** Ireland (operations hub), Jersey, Luxembourg (holding entities)
> **Holding Structure:** Apple Inc. (parent) → regional holding companies → operating entities

---

### Q4.2: Are there special structural features that add risk?

**Why:** VIEs, SPEs, off-balance-sheet arrangements add opacity. Each creates a surface area where financial manipulation or undisclosed risk can hide.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| VIE disclosures | 10-K | — | ⚠️ Flag extraction exists |
| SPE/SPV disclosures | 10-K | — | ❌ Not extracted |
| Off-balance-sheet arrangements | 10-K | — | ❌ Not extracted |
| Joint ventures | 10-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| VIE flag | VIE present = opacity flag | Flag |
| Off-balance-sheet flag | OBS arrangements present = flag | Flag |
| Structural risk count | Number of special structures present | Count + tier |

**DISPLAY:**

> **Special Structures:** No VIEs, no SPEs, no significant off-balance-sheet arrangements ✅
> **Joint Ventures:** None material
> **Structural Risk:** LOW — clean corporate structure

---

### Q4.3: What's the share structure?

**Why:** Dual-class shares insulate management from shareholder accountability. Voting control concentrated in few hands creates governance risk. Structural features here affect shareholder rights and litigation dynamics.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Dual-class structure | DEF14A + 10-K | — | ✅ Have |
| Voting control arrangement | DEF14A | — | ⚠️ Partial |
| Tracking stocks | 10-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Dual-class flag | Dual-class = governance risk flag | Flag |
| Voting concentration | >50% voting control in <3 people = RED | Flag |
| → Cross-reference | GOVERNANCE.RIGHTS for full shareholder rights analysis | Link |

**DISPLAY:**

> **Share Structure:** Single class common stock ✅
> **Voting:** One share, one vote
> **→ See GOVERNANCE.RIGHTS for full shareholder rights analysis**

---

### Q4.4: How complex are the intercompany arrangements?

**Why:** Related-party transactions between entities, transfer pricing, management fees — complexity here is a fraud risk indicator and creates disclosure obligations. Self-dealing is a major derivative suit trigger.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Related-party transactions | DEF14A / 10-K | — | ⚠️ Partial |
| Transfer pricing disclosures | 10-K | — | ❌ Not extracted |
| Management fee structures | 10-K / DEF14A | — | ❌ Not extracted |
| Intercompany loan arrangements | 10-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Related party flag | Significant related-party transactions = flag | Flag |
| Intercompany complexity | Multiple intercompany arrangements = opacity indicator | Flag |
| → Cross-reference | GOVERNANCE.COMPENSATION for related party detail | Link |

**DISPLAY:**

> **Related Party Transactions:** None material disclosed ✅
> **Intercompany:** Standard transfer pricing for multinational operations
> **→ See GOVERNANCE.COMPENSATION for executive-related party transactions**

---

## AREA 5: GEOGRAPHIC FOOTPRINT

*Where does it operate?*

---

### Q5.1: Where does the company have physical operations?

**Why:** Physical presence determines jurisdictional litigation exposure and operational risk. Each country with offices, factories, or employees is a jurisdiction where lawsuits can be filed.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Operating countries | Exhibit 21 subsidiary list | 10-K Item 2 | ⚠️ Fragile parsing |
| Major facilities | 10-K Item 2 (Properties) | — | ❌ Not extracted |
| Employee distribution by country | 10-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Jurisdictional count | >20 = HIGH exposure, >10 = MEDIUM | Tier |
| Operations in high-risk countries | Cross-ref with CPI / risk indices | Flag |

**DISPLAY:**

> **Physical Operations:** 28 countries
> **Major Facilities:** US (HQ Cupertino, data centers), China (manufacturing partners), India (manufacturing), Ireland (European HQ)
> **Jurisdictional Exposure:** HIGH (>20 countries)

---

### Q5.2: Which jurisdictions create elevated legal exposure?

**Why:** Operations in certain jurisdictions create specific legal obligations: FCPA (anti-corruption), GDPR (data privacy), sanctions compliance. Presence = obligation.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Operations in high-corruption countries | Exhibit 21 × CPI index | — | ❌ No CPI data |
| EU operations (GDPR trigger) | Exhibit 21 | — | ⚠️ Can derive from subsidiary list |
| Sanctions-proximate operations | Exhibit 21 × sanctions list | — | ❌ No sanctions list |
| Tax haven subsidiaries | Exhibit 21 × config/tax_havens.json | — | ⚠️ Tax haven list exists |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| FCPA exposure | Operations in countries with CPI <50 | HIGH / MEDIUM / LOW |
| GDPR exposure | EU operations + consumer data handling | Flag |
| Sanctions proximity | Operations in/near sanctioned regions | Flag |
| Tax haven flag | Subsidiaries in tax haven jurisdictions | Flag |

**DISPLAY:**

> **FCPA Exposure:** MEDIUM — operations in China, India, Brazil (mid-range CPI)
> **GDPR Exposure:** HIGH — European operations, consumer data, App Store
> **Sanctions Risk:** LOW — no operations in sanctioned countries
> **Tax Havens:** Ireland, Jersey, Luxembourg (holding entities — industry standard for tech)

---

### Q5.3: How much of the business is international vs domestic?

**Why:** International operations >50% = elevated complexity, FX risk, multi-jurisdictional litigation exposure. Also determines how many regulatory regimes the company navigates simultaneously.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| International revenue % | 10-K geographic segments | — | ⚠️ Partial |
| International operations % | Exhibit 21 country count | — | ⚠️ Partial |
| FX exposure disclosure | 10-K Item 7A | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| International mix | >50% international = elevated complexity flag | Flag |
| FX risk | Material FX exposure disclosed = flag | Flag |
| Regulatory complexity | International mix × jurisdiction count = complexity score | Score |

**DISPLAY:**

> **International/Domestic:** 57% international / 43% Americas
> **FX Exposure:** Material — revenue in EUR, GBP, CNY, JPY
> **Regulatory Complexity:** HIGH — operates under 20+ national regulatory frameworks simultaneously

---

## AREA 6: M&A & CORPORATE TRANSACTIONS

*What deals has it done, and what's pending?*

---

### Q6.1: Is there a pending M&A transaction?

**Why:** Active M&A = near-certain merger objection lawsuits. Companies in the process of acquiring or being acquired have elevated D&O exposure during the deal period. Deal terms, regulatory approvals, and competing bids all create claim triggers.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Active M&A announcements | 8-K Item 1.01 | NEWS | ⚠️ 8-K converter exists |
| Merger agreements | 8-K | — | ⚠️ 8-K converter exists |
| Expected close date | 8-K / news | — | ❌ Not extracted |
| Required regulatory approvals | 8-K / 10-K | — | ❌ Not extracted |
| Deal size | 8-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Active deal flag | Any pending M&A = flag | RED (acquiring) / RED (being acquired) |
| Deal materiality | Deal size > 10% of market cap = transformative | Materiality tier |
| Regulatory risk | Pending regulatory approval = deal uncertainty | Flag |
| Merger objection probability | Public M&A = ~100% merger objection filing | Near-certain |

**DISPLAY:**

> **Pending Transactions:** None ✅
> **M&A Status:** No active acquisition or sale process disclosed

---

### Q6.2: What's the 2-3 year acquisition history?

**Why:** A company's acquisition track record reveals integration capability, strategic direction, and accumulated risk. Rapid acquirers accumulate goodwill, integration complexity, and potential liability from pre-acquisition conduct of targets.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Completed acquisitions (2-3yr) | 8-K Item 2.01 + 10-K | NEWS | ⚠️ 8-K converter exists, not structured |
| Deal sizes | 8-K / 10-K | — | ❌ Not specifically extracted |
| Target names | 8-K / 10-K | — | ⚠️ Partial from 8-K |
| Strategic rationale | 10-K / 8-K | — | ❌ Not extracted |
| Integration status | 10-K MD&A | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Acquisition velocity | >3 deals in 2yr = HIGH integration complexity | Velocity tier |
| Deal magnitude | Sum of deal values / market cap = acquisition intensity | Intensity score |
| Integration burden | Multiple recent acquisitions still integrating = elevated operational risk | Flag |

**DISPLAY:**

> **Acquisition History (2023-2025):**
>
> | Date | Target | Size | Rationale | Integration Status |
> |---|---|---|---|---|
> | 2024 Q2 | [Example] | $500M | AI technology | Integrated |
> | 2023 Q4 | [Example] | $200M | Content library | Integrated |
>
> **Acquisition Velocity:** LOW — small tuck-in acquisitions
> **Integration Risk:** LOW — no major pending integrations

---

### Q6.3: How much goodwill has accumulated and is there impairment risk?

**Why:** Goodwill from acquisitions that exceeds 30% of total assets creates material impairment risk. A goodwill writedown triggers stock drops and potential SCA ("they knew the acquisition was overvalued"). Cross-references FINANCIAL for impairment testing.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Goodwill balance | Balance sheet | → FINANCIAL cross-ref | ⚠️ In financial data, not flagged |
| Total assets | Balance sheet | → FINANCIAL cross-ref | ✅ Have |
| Goodwill / total assets % | Derived | — | ❌ Not computed |
| Impairment testing history | 10-K | — | ❌ Not extracted |
| Recent impairment charges | 10-K / 8-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Goodwill concentration | >50% of assets = RED, >30% = YELLOW, <30% = CLEAR | Risk flag |
| Impairment risk assessment | High goodwill + declining business unit = elevated risk | Flag |
| → Cross-reference | FINANCIAL.DISTRESS for impairment evaluation | Link |

**DISPLAY:**

> **Goodwill:** $0 (Apple carries no goodwill) ✅
> **Impairment Risk:** None — no acquisition-driven goodwill
> **→ See FINANCIAL for full asset quality analysis**

---

### Q6.4: Has the company done any divestitures, spin-offs, or restructuring?

**Why:** Divestitures can be strategic simplification (positive) or distress response (concerning). Spin-offs create new public entities = new D&O exposure. Restructuring charges signal operational stress. Multiple restructurings in 3 years = chronic problems.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Divestitures | 8-K Item 2.01 + 10-K | — | ⚠️ Partial detection |
| Spin-offs | 8-K / 10-K | — | ❌ Not extracted |
| Restructuring charges | 10-K | — | ⚠️ Text pattern detection exists |
| Cost reduction programs | 10-K / 8-K | — | ❌ Not extracted |
| Layoffs / workforce reduction | 8-K Item 2.05 + news | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Divestiture assessment | Strategic repositioning vs distress signal | Assessment |
| Spin-off flag | New public entity = new D&O policy needed | Flag |
| Restructuring frequency | >1 restructuring in 3yr = chronic operational issues = RED | Flag |
| Layoff flag | Major layoff = employment litigation risk | Flag |

**DISPLAY:**

> **Divestitures:** None in past 3 years ✅
> **Spin-offs:** None
> **Restructuring:** No material restructuring charges
> **Workforce Actions:** None disclosed

---

### Q6.5: Is there activist-driven transaction pressure?

**Why:** Activists pushing for sale, breakup, or strategic alternatives create board-level conflict and transaction litigation risk. "Strategic alternatives" language in filings often precedes transformative transactions.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| 13D filings | SEC EDGAR | — | ✅ Have (governance data) |
| Activist campaigns | 13D + news | — | ⚠️ Partial |
| "Strategic alternatives" language | 10-K / 8-K text search | — | ❌ Not extracted |
| Board response to activists | DEF14A / 8-K | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Activist transaction pressure | Active activist pushing for sale/breakup = YELLOW | Flag |
| Strategic alternatives flag | "Evaluating strategic alternatives" in filings = elevated transaction probability | Flag |
| → Cross-reference | GOVERNANCE.ACTIVIST for full activist analysis | Link |

**DISPLAY:**

> **Activist Pressure:** No activist-driven transaction pressure ✅
> **Strategic Alternatives:** No "strategic alternatives" language in filings
> **→ See GOVERNANCE.ACTIVIST for ownership and activist activity detail**

---

## AREA 7: COMPETITIVE POSITION & INDUSTRY DYNAMICS

*Where does it sit in the market and what's happening around it?*

---

### Q7.1: What's the company's market position?

**Why:** Market leaders face antitrust risk. Declining positions face earnings pressure. Companies losing share may make aggressive claims about competitive response. A monopoly/oligopoly faces different D&O risk than a challenger.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Market position / share | 10-K Item 1 LLM extraction | NEWS | ❌ No extraction |
| Competitive moat assessment | 10-K Item 1 LLM | — | ❌ No extraction |
| Barriers to entry | 10-K Item 1 LLM | — | ❌ No extraction |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Dominant position flag | >40% market share in any market = antitrust risk flag | Flag |
| Declining position flag | Losing market share YoY = earnings pressure signal | Flag |
| Moat strength | Strong (ecosystem/network effects) / Moderate (brand/scale) / Weak (commodity) | Assessment |

**DISPLAY:**

> **Market Position:** #1 global smartphone by revenue, #1 consumer electronics ecosystem
> **Competitive Moat:** STRONG — ecosystem lock-in (hardware + services + App Store)
> **Barriers to Entry:** HIGH — brand, ecosystem, semiconductor design, retail network
> **Antitrust Note:** Dominant App Store position facing antitrust challenges in US and EU

---

### Q7.2: What's the industry growth trajectory?

**Why:** Declining industries create earnings pressure across all participants. Companies in declining industries must grow by taking share or making acquisitions — both create aggressive behavior that increases D&O risk. Growing industries are more forgiving.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Industry growth rate | 10-K / news / sector data | — | ❌ Not extracted |
| Industry lifecycle stage | Derived | — | ❌ Not computed |
| Peer revenue growth comparison | → FINANCIAL cross-reference | — | ⚠️ Partial (peer data exists) |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Industry growth assessment | Declining = RED, Flat = YELLOW, Growing = CLEAR | Assessment |
| Growth vs peers | Company growing faster/slower than industry | Relative position |

**DISPLAY:**

> **Industry Growth:** Consumer electronics STABLE; services/digital content GROWING
> **AI/Semiconductor Demand:** ACCELERATING
> **Assessment:** Mixed — mature hardware markets offset by growing services and AI demand

---

### Q7.3: What competitive pressures or disruptions are happening?

**Why:** Disruption creates uncertainty. Management may make aggressive claims about competitive response. Pricing pressure compresses margins. Platform shifts can make entire product categories obsolete.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Competitive dynamics | 10-K Item 1 / Item 1A LLM extraction | NEWS | ❌ Not extracted |
| New entrants / disruptors | 10-K / news | — | ❌ Not extracted |
| Technology disruption signals | 10-K Item 1A | — | ❌ Not extracted |
| Pricing pressure indicators | 10-K / earnings calls | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Active disruption flag | Material competitive disruption underway = YELLOW | Flag |
| Pricing pressure flag | Margin compression from competition = flag | Flag |
| Platform shift risk | Technology transition threatening core business = RED | Flag |

**DISPLAY:**

> **Competitive Pressures:** Android ecosystem (Samsung, Google Pixel); AI assistant competition
> **Disruption Risk:** LOW — Apple is generally the disruptor, not the disrupted
> **Pricing Pressure:** MODERATE — premium positioning under pressure in developing markets

---

### Q7.4: Are peers in this industry being sued?

**Why:** Sector contagion. If 3+ industry peers have active SCAs, there's likely a systemic issue (accounting practice, regulatory change, industry-wide fraud) that could affect this company too.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Peer SCA count | SCAC database | — | ✅ Have |
| Peer active SCA count | SCAC | — | ✅ Have |
| Sector SCA filing rate | SCAC | — | ✅ Have |
| Peer group list | SEC + yfinance | — | ✅ Have |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Sector contagion | 3+ peers with active SCAs = RED, 1-2 = YELLOW, 0 = CLEAR | Risk flag |
| Sector filing rate trend | Increasing = YELLOW | Trend |
| Common allegation patterns | Cluster of similar allegations across peers = systemic flag | Pattern flag |

**DISPLAY:**

> **Peer Litigation:**
>
> | Peer | Active SCAs | Most Recent |
> |---|---|---|
> | MSFT | 0 | 2019 |
> | GOOG | 1 | 2024 |
> | AMZN | 0 | 2021 |
> | META | 1 | 2023 |
> | NVDA | 0 | — |
>
> **Sector Contagion:** ⚠️ YELLOW — 2 of 5 major peers have recent/active SCAs
> **Common Patterns:** Privacy/antitrust allegations across Big Tech

---

### Q7.5: What are the industry headwinds and tailwinds?

**Why:** Industry-wide headwinds (regulation, trade policy, macro shifts) affect all companies in a sector regardless of individual performance. Tailwinds can mask company-specific problems. Consolidation creates M&A waves = transaction litigation. These were previously in FORWARD.ENVIRONMENT but describe the current landscape.

**ACQUIRE:**

| Data Point | Source | Fallback | Status |
|---|---|---|---|
| Industry headwinds | 10-K Item 1A LLM extraction | NEWS | ❌ Not extracted |
| Tailwinds | 10-K Item 1 LLM | NEWS | ❌ Not extracted |
| Consolidation activity | 10-K / news | — | ❌ Not extracted |
| Regulatory changes affecting sector | 10-K Item 1A | — | ❌ Not extracted |
| Macro factors (rates, FX, trade) | 10-K Item 7A | — | ❌ Not extracted |

**ANALYZE:**

| Evaluation | Logic | Output |
|---|---|---|
| Headwind severity | Material headwinds present = YELLOW; existential headwinds = RED | Assessment |
| Consolidation flag | Active M&A wave in sector = transaction litigation risk | Flag |
| Regulatory change flag | New regulation affecting sector = compliance transition risk | Flag |

**DISPLAY:**

> **Headwinds:**
> - EU Digital Markets Act (antitrust, App Store changes)
> - US-China trade tensions (manufacturing, market access)
> - Global smartphone market saturation
>
> **Tailwinds:**
> - AI integration driving services growth
> - India manufacturing expansion
> - Services revenue diversification
>
> **Consolidation:** LOW — Big Tech not actively consolidating
> **Regulatory Change:** ⚠️ SIGNIFICANT — DMA, antitrust investigations, AI regulation proposals

---

## Summary: Status Across All Areas

| Area | Questions | Data ✅ | Data ⚠️ | Data ❌ | Priority Fix |
|---|---|---|---|---|---|
| **1. Identity** | 4 | Q1.1, Q1.2 mostly | Q1.3, Q1.4 partial | SPAC detection, archetype wiring | Wire risk archetype, add SPAC |
| **2. Business Model** | 5 | Q2.2, Q2.3 partial | Q2.1 partial | Revenue model, cost structure, key products | LLM extraction for business model |
| **3. Operations** | 5 | Q3.1, Q3.2 | Q3.4 partial | Q3.3, Q3.5 entirely | Structured dependency extraction |
| **4. Structure** | 4 | Q4.1, Q4.3 mostly | Q4.2 VIE only | SPEs, OBS, intercompany | Structural feature extraction |
| **5. Geography** | 3 | — | Q5.1, Q5.3 partial | CPI data, GDPR flags, sanctions | Add reference data (CPI, sanctions) |
| **6. M&A** | 5 | Q6.5 partial | Q6.1, Q6.2, Q6.4 partial | Deal details, goodwill %, integration | Structured M&A history extraction |
| **7. Competitive** | 5 | Q7.4 fully | — | Q7.1-Q7.3, Q7.5 entirely | Industry context LLM extraction |
