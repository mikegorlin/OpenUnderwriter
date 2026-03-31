# Professional D&O Underwriting Worksheet: Presentation Model Research

## 1. Current Output Assessment

### What We Produce Today

The system generates a 26-template HTML worksheet (rendered to PDF via Playwright) organized into 9 sections plus 4 appendices:

**Section Order (from `worksheet.html.j2`):**
1. Identity (company header, basic stats)
2. Executive Summary (profile, risk classification, tier badge, key findings, claim probability, tower recommendation)
3. Red Flags (triggered signals table)
4. Financial Health (YoY comparison, key metrics, full statements, distress models, quarterly updates, tax risk, earnings quality, audit profile, peers)
5. Market & Trading (stock performance, charts, drops, short interest, earnings guidance, insider trading, ownership, capital markets activity)
6. Governance & Leadership (people risk, board composition, forensic profiles, structural governance, ownership structure, transparency/disclosure, activist risk)
7. Litigation & Regulatory (active matters, SEC enforcement, settlements, SOL analysis, derivative suits, contingent liabilities, defense strength, workforce/product/environmental, whistleblower indicators)
8. AI Risk Assessment (score, dimension breakdown, competitive position, forward indicators)
9. Scoring & Risk Assessment (tier classification, peril assessment, hazard profile, 10-factor scoring, pattern detection, risk type, allegation theory mapping, claim probability, severity scenarios, tower recommendation, radar chart, forensic composites, executive risk profile, temporal signals, NLP filing analysis, peril map, calibration notes)

**Appendices:**
- A: Meeting Preparation Questions
- B: Sources (numbered citation list)
- C: QA / Audit Trail (full check-level audit)
- D: Data Coverage & Quality

**Design System:**
- Bloomberg-style navy/gold color scheme
- Tailwind CSS v4 with self-hosted fonts (zero CDN dependencies)
- CapIQ-inspired two-column layout: sticky sidebar TOC + main content
- Sticky top bar with company identity, tier badge, and date
- Component macros: traffic_light badges, tier_badge (WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH), kv_table, data_table, data_grid (3-column CapIQ-style), spectrum_bar, density_indicator, section_narrative, evidence_chain
- Print-optimized with page-break controls

### Strengths

1. **Comprehensive Data Coverage**: 400 signals across 9 facets, with 8 D&O claim peril types evaluated through causal chain framework. This depth exceeds what any manual underwriting process could achieve.

2. **Professional Visual Quality**: Bloomberg-grade color scheme, tabular-nums typography, alternating row shading, navy headers with gold borders. Looks like a serious financial document.

3. **Density-Conditional Rendering**: Three-tier system (CLEAN/ELEVATED/CRITICAL) adapts section depth to risk level. Critical sections get deep dives with evidence chains; clean sections stay minimal.

4. **Traffic Light Risk Communication**: Consistent TRIGGERED/ELEVATED/CLEAR/INFO/SKIPPED status badges throughout. Underwriters can visually scan for red.

5. **Data Provenance**: Every check has source, confidence, and filing reference. The Sources appendix provides numbered citations. The QA Audit Trail shows every check executed.

6. **Interactive HTML Features**: Sticky sidebar TOC with IntersectionObserver tracking, collapsible hazard dimension details, embedded charts (stock performance, ownership, radar).

7. **Meeting Prep Integration**: Appendix A translates findings into broker discussion questions categorized by type (Credibility Test, Gap Filler, Forward Indicator, AI-Generated).

8. **Peril-Organized Scoring**: Maps check results to 8 D&O claim types via causal chains (triggers, amplifiers, mitigators). This is a genuinely novel analytical framework.

### Weaknesses

1. **No Clear Decision Framework on First Page**: The identity block and executive summary exist but the critical "write this risk?" decision is buried. An underwriter opening the document sees company name, ticker, and a CIK number before any risk assessment. The tier badge (WIN/WALK) is visible but the decision logic supporting it is scattered.

2. **Scoring Section is Overwhelming**: Section 9 attempts to present tier classification, peril assessment, hazard profile, 10-factor scoring, pattern detection, risk type classification, allegation theory mapping, claim probability, severity scenarios, tower recommendation, radar chart, forensic composites, executive risk, temporal signals, NLP analysis, peril map, AND calibration notes. This is 15+ subsections in one section -- far too dense for a human to process.

3. **Section Numbering is Inconsistent**: Identity has no number; Executive Summary is "Section 1"; Company Profile is "Section 2" (but appears on the same page as identity). Red Flags has no section number. Financial is "Section 3". Market is "Section 4". Governance is "Section 5" (but subsections reference "5.1", "5.2" while comments in the template reference "4.1", "4.2"). Litigation is "Section 6". AI Risk is "Section 8". Scoring is "Section 7". The sidebar TOC and the section numbers do not agree.

4. **Redundant Information**: Claim probability appears in both Executive Summary and Scoring. Tower recommendation appears in both. The "Company Profile" section (Section 2) duplicates identity data already in the Executive Summary's Company Profile card. Risk classification data is partially in Executive Summary, partially in Scoring.

5. **Missing Underwriter Decision Support**: No premium indication ranges. No retention recommendation. No D&O policy structure recommendations (ABC coverage split). No benchmarking against comparable placements.

6. **Check Results Scattered Across Sections**: Each section has its own "Check Results" subsection (e.g., "Financial Checks", "Governance Checks", "Litigation Checks"). This fragments the check results across the document. An underwriter wanting to see all triggered checks must visit each section individually. The Red Flags section partially solves this but only shows CRF-level flags, not the 400 individual check results.

7. **Narrative Quality Varies**: AI-generated section narratives are labeled "AI Assessment" but the quality and utility of these varies. Some are genuinely insightful; others are boilerplate summaries of data already visible in the tables.

8. **Financial Statements Too Detailed for Decision-Making**: Full income statement, balance sheet, and cash flow statement with all line items are useful reference material but dominate the financial section. The D&O-relevant financial analysis (distress models, earnings quality, debt covenants) gets pushed to the end.

9. **No Peer Comparison Integration**: Peer group is listed but peer comparison data does not flow into the financial or market sections. There is no "vs. peers" column in financial metrics tables.

10. **AI Risk Section Feels Orphaned**: Section 8 covers AI risk assessment but does not clearly connect to the D&O claim framework. It reads more like a technology analyst report than an underwriting assessment.

11. **No Visual Summary Dashboard**: Despite having 400 signals and a 10-factor score, there is no single-page visual dashboard showing the risk profile at a glance.

---

## 2. Industry Standard D&O Worksheet Structure

### What Professional D&O Underwriting Referrals Contain

Based on industry research (PLUS education modules, D&O Diary, Woodruff Sawyer guides, Ames & Gough, InsuranceTrainingCenter), professional D&O underwriting analyses follow a standardized structure:

**Standard Professional D&O Referral Structure:**

1. **Cover Page / Header**
   - Company name, ticker, exchange
   - Proposed policy period
   - Expiring program summary (if renewal)
   - Broker name and contact
   - Underwriter assignment

2. **Executive Summary (1 page max)**
   - Recommendation: WRITE / DECLINE / REFER TO MANAGER
   - Risk tier classification
   - Proposed terms (limit, retention, premium range)
   - 3-5 key risk factors
   - 3-5 favorable factors
   - Any deal-breaking issues

3. **Company Overview (1-2 pages)**
   - Business description (2-3 sentences)
   - Size metrics (market cap, revenue, employees)
   - Industry classification and peer context
   - Geographic footprint
   - Recent M&A or structural changes
   - Years public / IPO history

4. **Financial Analysis (2-3 pages)**
   - D&O-relevant financial summary (NOT full statements)
   - Key ratios: current ratio, debt/equity, interest coverage
   - Distress indicators (Z-Score, going concern)
   - Earnings stability and guidance track record
   - Audit opinion and auditor profile
   - Material weaknesses / restatements
   - Comparison to peers on key metrics

5. **Governance Assessment (1-2 pages)**
   - Board composition and independence
   - CEO/Chair separation
   - Key executive profiles (character, litigation history, tenure)
   - Compensation structure and say-on-pay results
   - Anti-takeover provisions
   - Recent departures
   - Insider ownership and trading patterns

6. **Claims / Litigation History (2-3 pages)**
   - Active matters with coverage implications
   - Historical claims (10-year lookback)
   - SEC enforcement pipeline
   - Settlement history
   - Statute of limitations analysis
   - Derivative and books-and-records demands
   - Regulatory exposure

7. **Market Analysis (1-2 pages)**
   - Stock performance and volatility
   - Short interest
   - Analyst consensus
   - Capital markets activity (Section 11 exposure)
   - Significant stock drops with trigger analysis

8. **Risk Scoring / Assessment (1 page)**
   - Composite risk score
   - Frequency assessment (claim probability)
   - Severity assessment (expected loss range)
   - Key risk factors driving the score
   - Comparison to sector norms

9. **Underwriting Recommendation (1 page)**
   - Proposed tower position
   - Premium guidance
   - Retention recommendation
   - Coverage terms (Side A/B/C, exclusions)
   - Conditions / subjectivities
   - Special endorsements needed

10. **Appendices (as needed)**
    - Detailed financial statements
    - Full litigation case summaries
    - Board member bios
    - Organizational structure chart

### Key Structural Principles

- **Decision First**: The recommendation comes before the analysis. An underwriter should know the answer on page 1 and understand the "why" by page 3.
- **D&O Lens on Everything**: Financial analysis is not a credit analysis. It focuses on indicators that predict D&O claims (restatement risk, going concern, earnings volatility) rather than general creditworthiness.
- **Brevity Over Completeness**: Professional referrals are 15-25 pages total, not 50+. Detail goes in appendices.
- **Quantified Risk**: Every risk factor should have a magnitude estimate, not just "present/absent". "Short interest at 12% of float" is useful; "short interest detected" is not.
- **Peer Context**: Every metric should have context -- industry average, peer comparison, or historical trend.

---

## 3. Gap Analysis: Current Output vs. Industry Standard

### Critical Gaps

| Gap | Current State | Industry Standard | Impact |
|-----|--------------|-------------------|--------|
| **No decision-first layout** | Tier badge visible but recommendation logic scattered across Exec Summary and Scoring sections | Recommendation on page 1 with key rationale | Underwriter must read entire document to form opinion |
| **No pricing guidance** | None | Premium range, retention suggestion, rate-on-line benchmarks | Missing the core underwriting deliverable |
| **No policy structure recommendation** | Tower position only | Side A/B/C allocation, entity coverage, excess structure, retention | Incomplete underwriting guidance |
| **No expiring program context** | None | Expiring terms, carrier, premium, claims under policy | Missing for renewals |
| **Scoring section too large** | 15+ subsections, ~10 pages | 1-page risk score summary | Information overload |
| **No peer comparison in tables** | Peer group listed separately | Peer values as context column in financial/market tables | Raw numbers lack context |
| **Full financial statements in body** | Income/balance/cash flow with all line items inline | D&O-relevant summary inline; full statements in appendix | Dilutes focus on risk indicators |
| **Section numbering chaos** | Inconsistent numbers, TOC/body mismatch | Clean sequential numbering | Professional credibility |

### Presentation Gaps

| Gap | Current State | Industry Standard | Impact |
|-----|--------------|-------------------|--------|
| **No 1-page dashboard** | None | Visual risk profile summary with key metrics | No at-a-glance overview |
| **No heat map visualization** | Traffic lights on individual checks | Heat map showing risk concentration by category | Hard to see patterns |
| **Redundant data presentation** | Claim probability, tower recommendation appear 2x | Each data point appears exactly once | Wastes space, confuses readers |
| **Interpretation buried after tables** | Bullet points below each table | Interpretation woven into or adjacent to data | Underwriter must scroll past data to find meaning |
| **Check results fragmented** | Per-section check summary tables | Consolidated triggered check table (Red Flags section exists but is incomplete) | Hard to see full risk picture |

### Content Gaps

| Gap | Current State | Industry Standard |
|-----|--------------|-------------------|
| **M&A activity section** | Not present as standalone | Key D&O risk factor per PLUS modules |
| **Employment practices section** | Buried in litigation under "Workforce" | Separate D&O risk category |
| **Regulatory exposure summary** | Scattered across litigation and forward-looking | Consolidated regulatory risk assessment |
| **Insurance program history** | Not captured | Critical for renewals |
| **Loss development** | Not captured | Track claims across policy periods |
| **Benchmark data** | Limited sector filing rates | Industry settlement medians, sector claim frequency, peer placement terms |

---

## 4. Presentation Design Recommendations

### Recommendation 1: Decision-First Executive Summary

The first page after the cover header should contain EVERYTHING an underwriter needs to make a preliminary decision:

```
+--------------------------------------------------+
| COMPANY NAME (TICKER) - D&O UNDERWRITING REFERRAL |
+--------------------------------------------------+
|                                                    |
| [WIN badge]  Quality: 87.3  Composite: 82.1       |
|                                                    |
| RECOMMENDATION: Write at $25M xs $25M              |
| Premium Guidance: $180K-$220K                      |
| Retention: $1M                                     |
|                                                    |
| +---------------------+------------------------+  |
| | KEY RISK FACTORS     | FAVORABLE FACTORS      |  |
| | * Active SCA (high)  | * Clean audit (Big 4)  |  |
| | * CFO departed 3mo   | * Strong cash flow     |  |
| | * 35% off 52wk high  | * No prior settlements |  |
| +---------------------+------------------------+  |
|                                                    |
| CLAIM PROBABILITY: Elevated (8-12%)               |
| SEVERITY BAND: $10M-$30M                          |
| BINDING CEILING: None                             |
|                                                    |
| Size: Mid-cap ($4.2B) | Sector: Industrials      |
| Years Public: 28      | Employees: 14,500         |
+--------------------------------------------------+
```

### Recommendation 2: Restructure into 6 Core Sections

Reduce from 9 sections + 4 appendices to 6 core sections + appendices:

1. **Executive Summary & Recommendation** (1 page) -- Decision, key factors, proposed terms
2. **Company Profile** (1-2 pages) -- Business, size, classification, risk factors
3. **Financial Health** (2-3 pages) -- D&O-relevant metrics, distress indicators, audit, earnings quality
4. **Governance & Leadership** (1-2 pages) -- Board, executives, compensation, ownership, activist risk
5. **Litigation & Claims** (2-3 pages) -- Active matters, history, SOL, SEC enforcement, defense
6. **Market & Trading** (1-2 pages) -- Stock performance, short interest, insider activity, capital markets

**Appendices:**
- A: Scoring Detail (10-factor breakdown, peril assessment, hazard profile, forensic composites -- all the current Scoring section detail)
- B: Financial Statements (full income/balance/cash flow)
- C: Meeting Preparation Questions
- D: QA / Audit Trail
- E: Sources
- F: Data Coverage

This moves from 9 sections (~30+ pages of body) to 6 sections (~12-15 pages of body) with detail in appendices.

### Recommendation 3: Paired-Column KV Tables

Replace single-column KV tables with paired 4-column layouts to increase information density:

```
+---------------------+--------+---------------------+--------+
| Market Cap           | $4.2B  | Revenue (TTM)       | $6.8B  |
| Employees           | 14,500 | Years Public         | 28     |
| State of Inc.       | DE     | FPI Status           | No     |
| SIC Code            | 3562   | GICS                 | 20106  |
+---------------------+--------+---------------------+--------+
```

This halves the vertical space consumed by identity/classification data.

### Recommendation 4: Side-by-Side Section Layouts

For sections with multiple data categories, use two-column layouts:

```
+------- Financial Metrics -------+------- Distress Models --------+
| Revenue         | $6.8B  | +12% | Altman Z-Score  | 3.42 | Safe |
| Net Income      | $890M  | +8%  | Ohlson O-Score  | 0.12 | Safe |
| Operating Margin| 13.1%  | -0.5 | Beneish M-Score | -2.8 | Clean|
| Debt/Equity     | 0.45   | +0.03| Piotroski F     | 7/9  | Good |
+---------------------------------+--------------------------------+
```

### Recommendation 5: Consolidated Risk Scorecard

Replace the scattered check results with a single consolidated risk scorecard appearing early in the document:

```
RISK SCORECARD
+-----------------+--------+-----------+-----+
| Dimension       | Score  | Risk      | # Triggered |
+-----------------+--------+-----------+-----+
| Financial       | 85/100 | LOW       | 2   |
| Governance      | 62/100 | MODERATE  | 5   |
| Litigation      | 38/100 | HIGH      | 8   |
| Market          | 71/100 | MODERATE  | 3   |
| Operational     | 78/100 | LOW       | 1   |
+-----------------+--------+-----------+-----+
| COMPOSITE       | 67/100 | ELEVATED  | 19  |
+-----------------+--------+-----------+-----+
```

### Recommendation 6: Remove Redundancy

- Claim probability: Show ONLY in Executive Summary
- Tower recommendation: Show ONLY in Executive Summary
- Risk classification: Show ONLY in Executive Summary
- Company Profile card: Consolidate identity block + company profile into one
- Check results: Remove per-section check tables from body; consolidate into Red Flags section and QA Audit appendix

---

## 5. Section-by-Section Template (Proposed Worksheet Structure)

### Page 1: Cover Header + Decision Summary

```
LAYOUT: Full-width single page

COVER HEADER BAR (existing):
  Left: Company Name (Ticker)
  Center: [TIER BADGE] Quality Score | Composite Score
  Right: Angry Dolphin | D&O Worksheet | Date

RECOMMENDATION BLOCK (NEW):
  Background: Subtle tier-colored border (green=WIN, red=WALK)
  Contents:
    - Underwriting Recommendation: [WRITE/DECLINE/REFER]
    - Proposed Position: $XM xs $XM
    - Premium Guidance: $XXK-$XXK
    - Retention: $X.XM
    - Binding Ceiling: [None / Score ceiling description]

SPLIT COLUMNS:
  Left Column (55%): KEY NEGATIVES (3-5 bulleted, bold title + explanation)
  Right Column (45%): KEY POSITIVES (3-5 bulleted, bold title + explanation)

AT-A-GLANCE METRICS (horizontal strip):
  | Claim Prob: Elevated (8-12%) | Severity Band: $10M-$30M |
  | Active Matters: 2           | Red Flags: 5              |

COMPANY SNAPSHOT (paired KV table, 4 columns):
  | Market Cap | $4.2B | Revenue | $6.8B |
  | Employees  | 14.5K | Yrs Public | 28 |
  | Sector     | Industrials | Exchange | NYSE |
  | SIC        | 3562 - Pumps | GICS | 20106 |

AI THESIS (section_narrative):
  2-4 sentence AI-generated summary of the risk profile
```

### Pages 2-3: Financial Health

```
LAYOUT: Main content

SECTION HEADER: "Financial Health" with density_indicator

AI NARRATIVE: Pre-computed financial assessment

D&O-RELEVANT FINANCIAL SUMMARY (table):
  Metric | Current | Prior | YoY | D&O Significance
  Revenue | $6.8B | $6.1B | +11.5% | --
  Net Income | $890M | $820M | +8.5% | --
  Operating Margin | 13.1% | 13.6% | -0.5pp | Margin compression
  Debt/Equity | 0.45 | 0.42 | +0.03 | Increased leverage
  Current Ratio | 2.1 | 2.3 | -0.2 | Still adequate
  Interest Coverage | 8.4x | 9.1x | -0.7x | Comfortable

DISTRESS MODELS (compact table with traffic lights):
  | Model | Score | Zone | D&O Impact |
  | Z-Score | 3.42 | SAFE | No concern |
  | O-Score | 0.12 | SAFE | No concern |
  | Beneish | -2.8 | CLEAN | Low restatement risk |
  | Piotroski | 7/9 | GOOD | Strong fundamentals |

AUDIT PROFILE (paired KV, 1 row):
  | Auditor: KPMG (Big 4) | Tenure: 12 years |
  | Material Weaknesses: 0 | Going Concern: No |

EARNINGS QUALITY (compact KV):
  | Quality Score | 78/100 |
  | OCF/NI | 1.2x |
  | Accruals Ratio | -0.03 |

QUARTERLY UPDATE (if material change):
  Only show if quarter represents material departure from annual trend

EARNINGS GUIDANCE TRACK RECORD (if notable):
  Beat rate, consecutive misses, withdrawal history

TAX RISK (if elevated):
  Haven count, ETR trend, transfer pricing
```

### Pages 4-5: Governance & Leadership

```
LAYOUT: Main content

SECTION HEADER: "Governance & Leadership" with density_indicator

AI NARRATIVE

BOARD OVERVIEW (paired KV):
  | Board Size: 11 | Independence: 82% |
  | CEO/Chair: Separated | Avg Tenure: 6.2 yrs |
  | Gender Diversity: 36% | Governance Score: B+ |

LEADERSHIP TABLE (existing format -- this is good):
  Name | Title | Tenure | Prior Lit. | Character/Flags

BOARD FORENSIC PROFILES (existing format):
  Name | Tenure | Indep. | Qualifications | Other Boards | Flags

COMPENSATION HIGHLIGHTS (paired KV):
  | CEO Total: $12.5M | Pay Ratio: 185:1 |
  | Say-on-Pay: 94% | Clawback: Yes (broad) |

OWNERSHIP (compact):
  | Institutional: 85% | Insider: 3.2% |
  Top 5 holders, activist investors if any

RECENT DEPARTURES (only if any)
ANTI-TAKEOVER PROVISIONS (only if notable)
RELATED-PARTY TRANSACTIONS (only if any)
```

### Pages 5-7: Litigation & Claims

```
LAYOUT: Main content

SECTION HEADER: "Litigation & Claims" with density_indicator

AI NARRATIVE

ACTIVE MATTERS TABLE (existing format -- this is effective):
  Case | Coverage | Status | Class Period | Lead Counsel | Settlement

SEC ENFORCEMENT PIPELINE (compact KV):
  | Highest Stage: None | Wells Notice: No |
  | Comment Letters: 2 | Investigation: None |

SETTLEMENT HISTORY (if any):
  Case | Amount | Year | Type

SOL ANALYSIS (split actual vs theoretical -- existing approach is good)

DERIVATIVE SUITS (if any)

CONTINGENT LIABILITIES (ASC 450):
  Description | Classification | Amount Range

DEFENSE STRENGTH (compact KV):
  | Overall: Moderate | Federal Forum: Yes |
  | PSLRA Safe Harbor: Strong | Prior Dismissal: Yes |

WORKFORCE/PRODUCT/ENVIRONMENTAL (if notable)
```

### Pages 7-8: Market & Trading

```
LAYOUT: Main content

SECTION HEADER: "Market & Trading" with density_indicator

AI NARRATIVE

STOCK PERFORMANCE (data_grid -- existing 3-column format):
  Current Price | 52-Week Range | % Off High
  1Y Return | Max Drawdown | 90D Volatility | Beta

STOCK CHARTS: 1-year and 5-year (existing embed_chart)

SIGNIFICANT DROPS (if any):
  Date | Drop % | Type | Trigger | Company-Specific | Recovery

SHORT INTEREST (compact KV):
  | Short % Float: 3.2% | Days to Cover: 2.1 |

INSIDER TRADING (compact):
  | Net Activity: Net seller | 10b5-1 Coverage: High |
  Cluster events if any

CAPITAL MARKETS (if active S11 windows):
  Recent offerings, shelf registrations
```

### Pages 8-9: Risk Scoring Summary (NEW -- condensed from current Section 9)

```
LAYOUT: Main content, single page target

RISK SCORECARD (consolidated):
  Dimension | Score | Risk | # Triggered
  (5-6 rows max)

10-FACTOR TABLE (existing, but compact):
  Factor | Score/Max | % | Risk Level
  (collapsed evidence rows -- expand only for >50% factors)

PERIL SUMMARY TABLE (existing, but top-line only):
  Peril | Risk Level | Active Chains | Key Evidence

SEVERITY SCENARIOS (existing):
  Scenario | Settlement | Defense | Total

RADAR CHART (existing)

All other scoring detail (hazard profile, forensic composites,
allegation theory, pattern detection, executive risk, temporal signals,
NLP analysis, peril map, calibration notes) moves to Appendix A.
```

### Appendices

```
APPENDIX A: Scoring & Risk Detail
  - Full hazard profile with all dimensions
  - Forensic composite scores
  - Executive risk profile
  - Allegation theory mapping
  - Pattern detection
  - Temporal signals
  - NLP filing analysis
  - Full peril map with bear cases
  - Calibration notes
  - AI Risk Assessment (current Section 8)

APPENDIX B: Financial Statements
  - Full income statement (all line items)
  - Full balance sheet (all line items)
  - Full cash flow statement (all line items)

APPENDIX C: Meeting Preparation Questions
  (existing)

APPENDIX D: QA / Audit Trail
  (existing)

APPENDIX E: Sources
  (existing)

APPENDIX F: Data Coverage & Quality
  (existing)
```

---

## 6. Risk Communication Framework

### Tier System (Current -- Keep)

The WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH tier system is effective and industry-appropriate. Keep it but enhance with more actionable language:

| Tier | Score Range | Action | Premium Guidance |
|------|-----------|--------|-----------------|
| WIN | 85-100 | Aggressively pursue; primary position | Below market rate |
| WANT | 70-84 | Pursue; primary or low excess | Market rate |
| WRITE | 55-69 | Write with conditions; mid-excess | Market to +15% |
| WATCH | 40-54 | Cautious; high excess only | +15% to +30% |
| WALK | 25-39 | Decline or refer to manager | +30%+ if written |
| NO_TOUCH | 0-24 | Decline outright | Do not quote |

### Traffic Light System (Current -- Refine)

Current five-state system (TRIGGERED/ELEVATED/CLEAR/INFO/SKIPPED) is too granular. Simplify to three states for display:

- **RED** (TRIGGERED): Requires underwriter attention. Active risk factor with evidence.
- **YELLOW** (ELEVATED): Notable but not deal-breaking. Monitor during policy period.
- **GREEN** (CLEAR): Favorable factor. No action needed.

Reserve INFO and SKIPPED for the QA Audit appendix only.

### Frequency-Severity Matrix

Present risk factors on a 2D grid rather than a single-dimensional list:

```
                    LOW FREQUENCY     HIGH FREQUENCY
HIGH SEVERITY   |   WATCH            WALK/NO_TOUCH
LOW SEVERITY    |   WRITE            WATCH
```

Each peril should be placed on this grid with its supporting evidence.

### Confidence Communication

Current approach: (est.) for MEDIUM, (web) for LOW, silent for HIGH. This is appropriate. Do not add visual noise for HIGH confidence data.

For section-level confidence:
- If >80% of checks evaluated at HIGH confidence: "Analysis based on audited filings"
- If >20% of checks at LOW confidence: "Limited data — web-sourced findings require verification"

### "Areas of Concern" vs "Favorable Indicators"

Current approach (Key Negatives / Key Positives with enriched narratives) is good. Enhance by:
1. Ordering by materiality (largest D&O claim impact first)
2. Adding quantified impact where possible ("CEO departure within 18 months of SCA filing increases settlement by 2.3x")
3. Cross-referencing to specific sections ("See Section 3: Financial Health for detail")

---

## 7. Facet-to-Section Mapping

### Current Facets (9 YAML files in `brain/facets/`)

| Facet | Signal Count | Display Type | Current Section |
|-------|-------------|-------------|----------------|
| business_profile | 43 | metric_table | Company Profile (Sect 2) |
| financial_health | 58 | metric_table | Financial Health (Sect 3) |
| governance | 85 | scorecard_table | Governance (Sect 5) |
| litigation | 65 | flag_list | Litigation (Sect 6) |
| market_activity | 35 | metric_table | Market & Trading (Sect 4) |
| executive_risk | 20 | metric_table | Scoring (Sect 9) |
| red_flags | 0 (dynamic) | flag_list | Red Flags (after Exec Summary) |
| forward_looking | 79 | metric_table | Scoring (Sect 9) |
| filing_analysis | 15 | metric_table | Scoring (Sect 9) |

### Proposed Facet-to-Section Mapping

| Facet | Proposed Section | Layout Type |
|-------|-----------------|-------------|
| business_profile | Company Profile | Paired KV tables + risk factor cards |
| financial_health | Financial Health | Summary table + distress models + data_grid |
| governance | Governance & Leadership | Leadership table + board profiles + paired KV |
| litigation | Litigation & Claims | Active matters table + SOL table + KV summary |
| market_activity | Market & Trading | data_grid + charts + drop events table |
| executive_risk | Governance & Leadership (merge) | Integrated into leadership table |
| red_flags | Executive Summary (Red Flags strip) | Compact flagged-item table |
| forward_looking | Appendix A: Scoring Detail | metric_table (detail level) |
| filing_analysis | Appendix A: Scoring Detail | metric_table (detail level) |

### Key Mapping Decisions

1. **executive_risk merges into governance**: The 20 executive risk signals (CEO risk score, CFO departure timing, insider selling clusters) belong with the governance section where leadership profiles live. Currently they are orphaned in Scoring section 9.

2. **forward_looking and filing_analysis move to appendix**: These 94 signals are important analytical depth but do not drive the primary underwriting decision. They belong in Scoring Detail appendix, not body.

3. **red_flags becomes a strip in Executive Summary**: Instead of a full section between Exec Summary and Financial, red flags should be a compact table within the Exec Summary -- immediately visible to the underwriter.

4. **market_activity composites**: The facet already defines `content` with render_as directives (narrative_with_table, metric_with_alerts, detail_table). This is the v2.0 rendering model -- composites drive section layout, standalone signals fill gaps.

---

## 8. Implementation Priorities

### Quick Wins (Template-Only Changes, No Pipeline Impact)

1. **Fix section numbering** -- Make TOC and section headers consistent. Remove redundant "Section N:" prefix in favor of clean numbered headers.
   - Effort: 1 hour
   - Impact: Professional credibility

2. **Remove redundant Claim Probability and Tower Recommendation from Scoring section** -- Already shown in Executive Summary.
   - Effort: 30 minutes
   - Impact: Eliminates 2 redundant subsections

3. **Move full financial statements to appendix** -- Keep D&O-relevant summary in body, move all-line-item tables to Appendix B.
   - Effort: 2 hours
   - Impact: Reduces Financial section from ~8 pages to ~3 pages

4. **Add paired KV tables** -- Convert single-column KV tables to 4-column paired format for identity, classification, audit, and compensation data.
   - Effort: 3 hours (new macro + template updates)
   - Impact: Major density improvement, closer to CapIQ target

5. **Consolidate Red Flags into Executive Summary** -- Move Red Flags section content into the Executive Summary as a compact strip, eliminating the standalone section.
   - Effort: 2 hours
   - Impact: Key risk information on first page

### Structural Changes (Template + Context Changes)

6. **Add Recommendation Block to Executive Summary** -- New block at top of Exec Summary with proposed position, premium guidance, retention, and binding ceiling. Requires adding premium guidance data to scoring or executive summary context.
   - Effort: 4 hours (template + context builder)
   - Impact: Transforms document from analysis report to underwriting tool

7. **Merge executive_risk into Governance section** -- Move executive risk profile from Scoring to Governance template. Update context builder.
   - Effort: 3 hours
   - Impact: Better organization, all people-risk in one place

8. **Create Scoring Summary page** -- Condense current 15-subsection Scoring into a 1-page summary with risk scorecard, 10-factor table, peril summary, and severity scenarios. Move everything else to Appendix A.
   - Effort: 6 hours (new template + appendix template)
   - Impact: Dramatic reduction in cognitive load

9. **Add peer comparison columns to financial metrics** -- Extend data_grid/data_row to show peer average as context_text for key financial metrics.
   - Effort: 4 hours (template + context enrichment)
   - Impact: Every metric gains context

10. **Integrate AI Risk into Scoring appendix** -- Remove standalone AI Risk section; fold meaningful content into business profile (competitive position) and scoring detail (AI risk dimensions).
    - Effort: 3 hours
    - Impact: Eliminates orphaned section

### Architectural Changes (Phase 56+ Vision)

11. **Facet-driven rendering** -- Replace hardcoded section templates with facet-driven rendering where each facet's display_config drives layout. Composites define section structure; standalone signals fill gaps.
    - Effort: 20+ hours
    - Impact: Enables dynamic worksheet adaptation

12. **Dashboard page** -- SVG/CSS-only visual dashboard with heat map, risk gauge, and key metrics. First page before Executive Summary in PDF; interactive in HTML.
    - Effort: 15+ hours
    - Impact: At-a-glance risk overview

13. **Benchmarking integration** -- Historical placement database for peer comparison of premiums, retentions, and tower structures.
    - Effort: 40+ hours (data collection + storage + rendering)
    - Impact: True underwriting decision support

14. **Policy structure recommendation engine** -- Algorithmic Side A/B/C allocation, excess structure, and retention recommendation based on risk profile.
    - Effort: 30+ hours
    - Impact: Full underwriting automation

---

## Sources

- [PLUS Module 9: Public / Financial D&O Liability Insurance](https://plusweb.org/education/module-9-public-financial-do-liability-insurance-2/)
- [Underwriting Considerations for D&O Insurance (LaPorte)](https://www.laporte-insurance.com/wp-content/uploads/2014/03/LaPorte_Underwriting_v2.pdf)
- [What Do D&O Insurers Look For? (D&O Diary)](https://www.dandodiary.com/2008/05/articles/d-o-insurance/what-do-do-insurers-look-for/)
- [D&O Insurance Underwriting: What To Know (Vouch)](https://www.vouch.us/insurance101/directors-and-officers-insurance-underwriting)
- [Underwriting Consideration for D&O Insurance (Ames & Gough)](https://amesgough.com/underwriting-consideration-for-do-insurance/)
- [5 Ways Financial Statements Deliver D&O Risk Insights](https://insurancetrainingcenter.com/resource/5-ways-financial-statements-deliver-do-risk-insights/)
- [2026 D&O Looking Ahead Guide (Woodruff Sawyer)](https://woodruffsawyer.com/insights/do-looking-ahead-guide)
- [NERA: Recent Trends in Securities Class Action Litigation, 2025 Full-Year Review](https://www.nera.com/insights/publications/2026/recent-trends-in-securities-class-action-litigation--2025-full-y.html)
- [NERA: Securities Class Action Lawsuit Filings Declined in 2025 (D&O Diary)](https://www.dandodiary.com/2026/01/articles/securities-litigation/nera-securities-class-action-lawsuit-filings-declined-in-2025/)
- [D&O Insurance for Public Companies (Janover)](https://janoverinsurance.com/guides/d-o-insurance-for-public-companies)
- [S&P Capital IQ Pro Platform](https://www.spglobal.com/market-intelligence/en/solutions/products/sp-capital-iq-pro)
- [AIG Directors & Officers Liability Insurance](https://www.aig.com/home/risk-solutions/business/management-and-professional-liability/directors-and-officers-liability)
- [Travelers Directors & Officers Liability](https://www.travelers.com/business-insurance/professional-liability-insurance/apps-forms/directors-officers)
- [Chubb ForeFront Portfolio 3.0 D&O](https://www.chubb.com/us-en/business-insurance/forefront-portfolio-3-0-directors-officers-entity-liability-insurance.html)
