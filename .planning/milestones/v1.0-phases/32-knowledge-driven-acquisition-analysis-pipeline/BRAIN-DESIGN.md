# D&O Underwriting Brain -- Architecture Design

**Date:** 2026-02-15
**Status:** DESIGN PROPOSAL (ready for implementation planning)
**Inputs:** 8 research documents, 12 user decisions (D1-D12), 594 old-system checks, 388 current checks
**Scope:** Complete architecture for a self-improving, knowledge-driven D&O underwriting brain

---

## Table of Contents

1. [Brain Conceptual Model](#1-brain-conceptual-model)
2. [Dual Organization (D5)](#2-dual-organization)
3. [Check Taxonomy](#3-check-taxonomy)
4. [DuckDB Schema (D11)](#4-duckdb-schema)
5. [Industry Model (D6)](#5-industry-model)
6. [Data Source Mapping](#6-data-source-mapping)
7. [Self-Improvement Architecture (D4)](#7-self-improvement-architecture)
8. [Migration Path](#8-migration-path)
9. [The 25 Underwriting Questions](#9-the-25-underwriting-questions)
10. [Readable Documentation (D9)](#10-readable-documentation)

---

## 1. Brain Conceptual Model

### How the Brain Thinks About D&O Risk

The brain models D&O risk as three interconnected layers, following the framework used by major D&O underwriters (AIG, Allianz, Aon, WTW) and validated by academic research (Baker & Griffith, University of Chicago Law Review).

```
                         ┌─────────────────────┐
                         │    FINAL SCORE       │
                         │  f(IR, HAZ, RC)      │
                         └──────────┬──────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                     │
    ┌──────────▼──────────┐  ┌─────▼──────────┐  ┌──────▼──────────────┐
    │   INHERENT RISK     │  │    HAZARDS     │  │ RISK CHARACTERISTICS │
    │   (Baseline)        │  │ (What COULD    │  │ (What AMPLIFIES or   │
    │                     │  │  happen)       │  │  MITIGATES)          │
    │ Industry sector     │  │ Securities SCA │  │ Financial health     │
    │ Market cap / size   │  │ Derivative     │  │ Governance quality   │
    │ Exchange listing    │  │ Regulatory     │  │ Insider activity     │
    │ Jurisdiction        │  │ Bankruptcy     │  │ Disclosure quality   │
    │ Lifecycle stage     │  │ Employment     │  │ Stock signals        │
    │ Business complexity │  │ Cyber/AI/ESG   │  │ Early warnings       │
    └─────────────────────┘  └────────────────┘  └──────────────────────┘
```

### Layer 1: Inherent Risk (Base Rate)

Inherent risk is the baseline D&O exposure a company carries simply by existing -- before any analysis of behavior, governance, or financials. It is determined by structural characteristics that cannot be changed in the short term.

**Six Inherent Risk Dimensions:**

| Dimension | What It Captures | Key Differentiators | Stability |
|---|---|---|---|
| **Industry Sector** | SCA filing rate by sector | Healthcare/Biotech = 44 SCAs in 2024 (highest); Tech = persistent high; FinServ = regulatory density | Changes only with redomiciliation or pivot |
| **Market Capitalization** | Size-driven exposure | Mid-cap ($2B-$10B) = worst risk-adjusted exposure (enough to attract litigation, too small for mature governance); Large-cap = higher frequency, bigger settlements | Changes with market moves |
| **Exchange Listing** | Securities law regime | NYSE/NASDAQ = full 10b-5/Section 11 exposure; OTC = fraud risk; Private = no securities SCA but derivative/employment | Rarely changes |
| **Jurisdiction** | Legal environment | Delaware = evolving Caremark; California = aggressive disclosure laws; Ninth Circuit now exceeds Second Circuit for SCA filings (69 vs 64 in 2024) | Changes only with reincorporation |
| **Lifecycle Stage** | Company maturity | IPO + 3 years = 13% lawsuit rate; de-SPACs = 17%; Distress = 40%+ of SCA filings despite <5% of companies | Dynamic -- companies age, enter distress |
| **Business Complexity** | Operational breadth | Diversified conglomerates > focused companies; international operations multiply regulatory exposure | Semi-stable |

**Key design principle:** Inherent risk varies by hazard. A biotech company has very high inherent risk for securities litigation (binary FDA outcomes) but low inherent risk for FCPA violations. The base rate is hazard-specific, not a single number.

**Scoring output:** The inherent risk layer produces a base risk profile (1-10 scale) for each applicable hazard category. This is a lookup, not a calculation.

### Layer 2: Hazards (What Could Go Wrong)

Hazards are the specific D&O loss scenarios -- the ways a D&O policy can be triggered. The brain maintains a complete taxonomy of hazard types. Not every hazard applies to every company; the inherent risk layer determines which hazards are relevant and at what base probability.

**Complete Hazard Taxonomy:**

| Code | Hazard | 2024-2025 Frequency | Typical Severity | Fastest-Growing? |
|---|---|---|---|---|
| **HAZ-SCA** | Securities Class Actions (10b-5) | 225 filings (2024), 14% above average | Median settlement $14M; total $4.75B (2024) | Stable frequency, record DDL |
| **HAZ-S11** | Section 11 Claims (IPO/offering) | Concentrated around offering events | Very high; strict liability | Stable |
| **HAZ-DER** | Shareholder Derivative Suits | ~2/3 of stock-drop suits get derivatives | $1.4B in settlements past 5 years; expanding via Caremark | Growing -- officers now subject |
| **HAZ-SEC** | SEC Enforcement | 313 actions FY2025 (27% drop); cyclical | Fines, disgorgement, bars; triggers follow-on litigation | Down cyclically, will rebound |
| **HAZ-DOJ** | DOJ Criminal Actions | Persistent priority for FCPA, fraud | Imprisonment, massive fines | Stable |
| **HAZ-REG** | Industry-Specific Regulatory | Highly industry-dependent | Varies widely | State AG enforcement increasing |
| **HAZ-BANK** | Bankruptcy/Insolvency Claims | Global insolvencies 24% above pre-pandemic; 17 mega-bankruptcies H1 2025 | Very high -- creditors are motivated | Growing sharply |
| **HAZ-EMPL** | Employment Claims | Most common for private/non-profit | High frequency, lower severity per claim | Rising (retaliation, whistleblower) |
| **HAZ-CYBER** | Cyber-Related D&O Claims | 13.6x SCA risk increase post-breach; 14 SCAs tracked since 2021 | Google $350M, Zoom $150M, Okta $60M (2024) | Growing |
| **HAZ-AI** | AI-Related Claims | 7 (2023) to 15 (2024) to 12 (H1 2025) | 30%+ stock drops triggering fraud claims | Fastest-growing category |
| **HAZ-ESG** | ESG/Greenwashing Claims | 27% report growing exposure | EU penalties up to 10% global turnover | Growing (but politically volatile) |
| **HAZ-SPAC** | SPAC/De-SPAC Claims | 17% litigation rate; past peak filing but severity increasing | Alta Mesa $126.3M, Grab $80M records | Severity growing, frequency past peak |
| **HAZ-ANTITRUST** | Antitrust/Competition | Persistent | Criminal imprisonment, treble damages | Stable |
| **HAZ-IP** | Intellectual Property | Industry-dependent | Variable | Stable |
| **HAZ-PRODUCT** | Product Liability Escalation | Triggers Caremark pattern (Boeing, Blue Bell) | Boeing: massive; PG&E: $90M derivative | Case-dependent |

**Key design principle:** Hazards are not checks. A hazard is a loss scenario. A check is an observable data point. Multiple checks map to one hazard. The brain maintains this distinction rigorously.

**Key insight -- Bankruptcy as Master Hazard:** Financial distress amplifies virtually every other D&O claim type simultaneously. Moody's EDF-X identifies 82% of eventual bankruptcies at least 3 months in advance. The brain treats financial distress as a meta-amplifier that modifies the entire risk profile, not just a single factor.

### Layer 3: Risk Characteristics (Amplifiers and Mitigators)

Risk characteristics are observable company traits that amplify or mitigate the hazards. They are the modification factors applied to the inherent risk base rate. Each characteristic is bidirectional -- the same dimension (e.g., governance) can amplify or mitigate depending on quality.

**Risk Characteristics by Strength:**

| Characteristic | Signal Strength | Direction | Primary Hazards Affected |
|---|---|---|---|
| **Financial distress** (negative cash flow, high leverage, Z < 1.81) | Very Strong | Amplifier | All (master hazard) |
| **Insider trading at suspicious times/amounts** | Very Strong | Amplifier | HAZ-SCA, HAZ-SEC, HAZ-DOJ |
| **Financial restatement** | Very Strong | Amplifier | HAZ-SCA, HAZ-SEC, HAZ-DER |
| **Material weakness in internal controls** | Very Strong | Amplifier | HAZ-SCA, HAZ-SEC, HAZ-REG |
| **Going concern opinion** | Very Strong | Amplifier | HAZ-BANK, HAZ-SCA, HAZ-DER |
| **Prior data breach** | Very Strong | Amplifier | HAZ-CYBER (13.6x SCA risk increase) |
| **Recent significant stock drop (>20%)** | Very Strong | Trigger | HAZ-SCA (litigation trigger threshold) |
| **Governance weakness** (low independence, combined CEO/Chair) | Moderate-Strong | Amplifier | HAZ-DER, HAZ-SEC, HAZ-EMPL |
| **Strong governance** (independent board, clawbacks, robust ERM) | Moderate-Strong | Mitigator | All (premium credits up to 15%) |
| **M&A activity** | Strong | Amplifier | HAZ-DER, HAZ-SCA, HAZ-ANTITRUST |
| **High stock volatility** | Strong | Amplifier | HAZ-SCA (larger potential damages) |
| **Short seller report** | Strong | Amplifier/Trigger | HAZ-SCA (stock drop catalyst) |
| **Aggressive earnings guidance** | Strong | Amplifier | HAZ-SCA (sets up litigation trigger) |
| **Hype-focused communications** | Strong | Amplifier | HAZ-SCA, HAZ-AI |
| **Auditor change** | Strong | Amplifier | HAZ-SCA (29% of Big R restatements follow within 1 year) |
| **Big 4 auditor with long tenure** | Moderate | Mitigator | HAZ-SCA, HAZ-SEC |

**Hazard-Characteristic Mapping Matrix:**

The brain maintains a matrix that specifies how strongly each risk characteristic affects each hazard. This enables hazard-specific risk modification rather than a single composite adjustment.

```
                     Securities  Derivative  Regulatory  Bankruptcy  Employment  Cyber    AI
                     SCA         Suit        Action
Financial distress   +++         ++          ++          +++         +           +        +
Insider trading      +++         ++          +++         +           -           -        -
Governance weakness  ++          +++         ++          ++          ++          ++       +
Restatement          +++         ++          +++         ++          -           -        -
Stock volatility     +++         +           +           +           -           -        -
Cyber incident       +++         ++          ++          -           -           +++      +
M&A activity         ++          +++         ++          ++          +           -        -
ESG misrepresent     ++          ++          +++         -           +           -        -
AI overclaiming      +++         +           +++         -           -           -        +++
Short seller report  +++         +           ++          +           -           -        ++

+++ = strong amplifier, ++ = moderate, + = weak, - = not applicable
```

### The Scoring Formula

```
Final Score = Base Rate(Inherent Risk, Hazard)
              x Product(Applicable Characteristic Modifications)
              , floored at 0, capped at 100
```

This follows the actuarial pricing model described by Moore Actuarial and the framework used by Moody's, Allianz, and WTW. Each modification factor has a direction (amplify/mitigate) and a strength (weak/moderate/strong/very strong) mapped to a numerical multiplier.

**Scoring tiers** (from Old System, validated by industry practice):

| Score Range | Tier | 18-Month Claim Probability | Underwriting Posture |
|---|---|---|---|
| 70-100 | EXTREME | >20% (1 in 5) | Decline or 2-3x rate |
| 50-69 | HIGH | 10-20% (1 in 5-10) | 1.5-2x rate, higher retention |
| 30-49 | AVERAGE | 5-10% (1 in 10-20) | Market rate |
| 15-29 | BELOW AVERAGE | 2-5% (1 in 20-50) | Discount available |
| 0-14 | MINIMAL | <2% (1 in 50+) | Best rates |

---

## 2. Dual Organization

### The Two Lenses (D5)

The brain supports two simultaneous views of the same underlying checks and data. This is not redundancy -- it is two different ways of reading the same information, each optimized for a different audience and purpose.

**Lens 1: Report Sections** -- How an underwriter reads the report. Organized by information type. "Show me all the financial data." "Show me all the governance data." This follows the conventional structure of a D&O submission.

**Lens 2: Risk Questions** -- What the brain is trying to answer. Organized by analytical purpose. "Will this company get sued?" "Can it survive a claim?" "Is management trustworthy?" This follows the underwriter's thought process.

### How the Two Lenses Map

```
REPORT SECTIONS (reading order)          RISK QUESTIONS (analytical order)
=====================================    ====================================
Section 1: Company Profile               Q1: What is this company inherently?
  - Business description                 Q2: How sustainable is the business model?
  - Industry classification              Q3: What is the competitive landscape?
  - Size and listing                     Q25: Any unique/emerging exposures?

Section 2: Financial Condition            Q6: Is the financial condition sound?
  - Liquidity ratios                     Q7: Are the financial statements reliable?
  - Leverage and debt                    Q8: Is management guidance credible?
  - Profitability trends
  - Cash flow analysis

Section 3: Governance & Management        Q9: Is the board providing adequate oversight?
  - Board composition                    Q10: Is the executive team trustworthy?
  - Executive profiles                   Q11: Are insiders trading in concerning patterns?
  - Compensation structure               Q12: Is compensation aligned with shareholders?
  - Shareholder rights                   Q13: Do shareholder rights protect investors?
  - Insider trading activity             Q14: Is there activist pressure?

Section 4: Litigation & Regulatory        Q4: Does the company have active/recent SCAs?
  - Securities class actions             Q5: What other litigation/regulatory exists?
  - Regulatory enforcement
  - Other litigation

Section 5: Market & Stock                 Q15: What does stock behavior tell us?
  - Stock price and patterns             Q16: What do short selling signals say?
  - Short interest                       Q17: What is the ownership structure?
  - Ownership structure                  Q18: What do valuation/analyst metrics suggest?
  - Analyst coverage

Section 6: Disclosure & NLP               Q19: What does disclosure language reveal?
  - Risk factor changes                  Q23: Is disclosure quality adequate?
  - MD&A tone shifts                     Q24: Are there narrative inconsistencies?
  - Filing timing

Section 7: Forward-Looking                Q20: What events could trigger claims during the policy?
  - Policy period events                 Q21: What early warning signals exist?
  - Macro headwinds                      Q22: What macro/industry headwinds exist?
  - Early warning signals
```

### Example: Same Check, Two Lenses

Consider the check `STOCK.SHORT.position` (Short Interest as % of Float):

**Report Section view:** This check appears in **Section 5: Market & Stock** under the "Short Interest" subsection. An underwriter scanning the stock section sees it alongside stock price, volatility, and ownership data.

**Risk Question view:** This check answers **Q16: What does short selling signal?** alongside short interest trend, short seller reports, and days to cover. It also contributes as evidence to **Q6: Is the financial condition sound?** (elevated short interest correlates with market skepticism about financial health).

**Implementation:** Each check carries both a `report_section` field (which section it renders in) and a `risk_questions` array (which questions it helps answer). A check can belong to exactly one report section but can contribute to multiple risk questions.

```
brain_checks.check_id = "STOCK.SHORT.position"
  report_section = "market_stock"        -- ONE section
  risk_questions = ["Q16", "Q6"]         -- MULTIPLE questions
  risk_framework = "risk_characteristic" -- ONE framework layer
  hazards = ["HAZ-SCA"]                  -- Hazards it amplifies
```

---

## 3. Check Taxonomy

### Check Identification Convention

Checks use a hierarchical dot-notation ID that encodes domain and specificity. The existing prefix convention (BIZ, FIN, GOV, LIT, STOCK, EXEC, NLP, FWRD) is retained for backward compatibility, with new metadata fields providing the risk-question and risk-framework organization.

**Format:** `PREFIX.SUBDOMAIN.specific_name`

**Examples:**
- `FIN.LIQ.position` -- Financial domain, Liquidity subdomain, Position check
- `LIT.SCA.active` -- Litigation domain, Securities Class Action subdomain, Active check
- `GOV.BOARD.independence` -- Governance domain, Board subdomain, Independence check

**Naming rules:**
- All lowercase with underscores for multi-word names
- 3-level hierarchy: PREFIX.SUBDOMAIN.name
- Maximum 40 characters per ID
- IDs are permanent -- retired checks keep their ID forever
- New checks that replace retired ones get new IDs (no reuse)

### Check Metadata Schema

Every check in the brain carries the following metadata. This schema is validated by a Pydantic model (`CheckDefinition`) that serves as the single source of truth.

```
CheckDefinition:
  # IDENTITY
  id: str                          # Unique, permanent (e.g., "FIN.LIQ.position")
  name: str                        # Human-readable name (e.g., "Liquidity Position")
  version: int                     # Incremented on any change (append-only history)

  # CLASSIFICATION (D2 -- display embeds in risk)
  content_type: ContentType        # EVALUATIVE_CHECK | MANAGEMENT_DISPLAY | INFERENCE_PATTERN
  lifecycle_state: LifecycleState  # BACKLOG | INVESTIGATION | MONITORING | SCORING | RETIRED
  depth: DepthLevel                # 1 (extract/display) | 2 (compute) | 3 (infer) | 4 (hunt)
  execution_mode: str              # AUTO | MANUAL

  # DUAL ORGANIZATION (D5)
  report_section: str              # Where it renders (company, financials, governance, litigation, market, disclosure, forward)
  risk_questions: list[str]        # Which questions it helps answer (Q1-Q25)
  risk_framework_layer: str        # inherent_risk | hazard | risk_characteristic

  # RISK MODEL (D7)
  factors: list[str]               # Scoring factors (F1-F10)
  hazards: list[str]               # Hazard codes it relates to (HAZ-SCA, HAZ-DER, etc.)
  characteristic_direction: str    # amplifier | mitigator | context | null
  characteristic_strength: str     # very_strong | strong | moderate | weak | null

  # EVALUATION
  threshold: ThresholdSpec         # Type + RED/YELLOW/CLEAR criteria
  pattern_ref: str | None          # For INFERENCE_PATTERN: reference to patterns.json

  # UNDERWRITER-READABLE (D9)
  question: str                    # Plain English: "Is the company financially distressed?"
  rationale: str                   # WHY this matters for D&O (with source reference)
  interpretation: str              # How to read the result

  # DATA REQUIREMENTS (D8)
  data_strategy: DataStrategy      # field_key, required_data, data_locations
  required_data: list[str]         # Source types needed (SEC_10K, MARKET_PRICE, etc.)
  data_locations: dict             # Source-to-section mapping
  acquisition_type: str            # structured | broad_search | composite

  # INDUSTRY (D6)
  industry_scope: str              # universal | sector_adjusted | supplement
  applicable_industries: list[str] # Empty = all; ["BIOT","HLTH"] = biotech/healthcare only

  # SELF-IMPROVEMENT (D4)
  expected_fire_rate: float | None # Expected % of companies that trigger this check
  last_calibrated: str | None      # Date of last calibration review
  calibration_notes: str | None    # Notes from last calibration

  # HISTORY (D3)
  created_date: str                # When this check was created
  created_by: str                  # Who created it
  retired_date: str | None         # When retired (null if active)
  retired_reason: str | None       # Why retired
```

### Lifecycle States (D1)

Every signal goes through a defined lifecycle. The brain never deletes anything -- retired checks remain in full history.

```
 BACKLOG ──► INVESTIGATION ──► MONITORING ──► SCORING ──► RETIRED
   │              │                │              │            │
   │   "We know   │  "We're       │  "We run it  │  "It       │  "It served
   │    this      │   figuring    │   every time  │   counts   │   its purpose
   │    could     │   out WHERE   │   and collect │   toward   │   but is no
   │    matter"   │   to get the  │   data, but   │   the      │   longer
   │              │   data"       │   it doesn't  │   final    │   relevant"
   │              │               │   score yet"  │   score"   │
   │              │               │               │            │
   ▼              ▼               ▼               ▼            ▼
 Tracked in    Data source     Appears in      Appears in    Full history
 brain_backlog  identified;    detail view;    risk score;   preserved;
 table with     may need new   fire rate       validated     never deleted
 priority and   acquisition    tracked;        by fire rate,
 rationale      capability     threshold       override, and
                               calibrated      event data
```

**State transitions and rules:**

| From | To | Trigger | Who Decides |
|---|---|---|---|
| BACKLOG | INVESTIGATION | Data source identified; implementation prioritized | Developer or automated gap analysis |
| INVESTIGATION | MONITORING | Data pipeline can populate the check; thresholds proposed | Developer after implementation |
| MONITORING | SCORING | Fire rate analysis confirms discrimination power; not always/never firing; calibration validated against outcomes | Self-improvement system or human review |
| SCORING | RETIRED | Check no longer relevant (hazard disappeared, regulation changed, better check exists) | Human review only; requires documented reason |
| MONITORING | RETIRED | Fire rate shows check is not useful; data source became unavailable | Self-improvement system flags; human approves |
| Any | BACKLOG | Check demoted (data source lost, threshold needs recalibration) | Human review |

**Current system mapping:**
- 198 checks with defined criteria = SCORING (they count toward scores today)
- 190 placeholder checks = mixture of BACKLOG (no data source) and INVESTIGATION (data source known but not implemented)
- 0 checks currently in MONITORING (this is a new state)
- 0 checks currently RETIRED (this is a new state; previously, checks were just deleted)

### Content Types

| Type | Count (Current) | What It Does | Evaluation Path |
|---|---|---|---|
| **EVALUATIVE_CHECK** | 305 | Compares data against RED/YELLOW/CLEAR thresholds; produces a risk signal | `evaluate_threshold()` -- numeric, boolean, percentage, temporal, or tiered comparison |
| **MANAGEMENT_DISPLAY** | 64 | Extracts and presents contextual data; no risk evaluation | `verify_presence()` -- confirms data is available; reports INFO status |
| **INFERENCE_PATTERN** | 19 | Detects multi-signal patterns by combining multiple check results | `detect_pattern()` -- evaluates trigger conditions across multiple data points |

### Display Embedded in Risk (D2)

There is no separate "display manifest." Each report section (Company, Financials, Governance, Litigation, Market, Disclosure, Forward) defines both what to DISPLAY and what to CHECK. The check's `content_type` determines its role:

- MANAGEMENT_DISPLAY checks define what data the section shows
- EVALUATIVE_CHECK checks define what the section evaluates
- INFERENCE_PATTERN checks define composite patterns the section detects

A single brain, a single configuration, a single truth.

---

## 4. DuckDB Schema

### Design Principles (D11)

The brain lives in a dedicated DuckDB database (`brain.duckdb`), separate from the pipeline cache (`analysis.duckdb`). Key properties:
- **Append-only version history** -- every edit is a new row; full audit trail
- **Continuous updates** -- add/modify checks without redeploying code
- **Queryable** -- SQL access for analytics, fire rate queries, coverage reports
- **Accessible** -- export to readable docs, generate reports
- **Pipeline integration** -- pipeline reads check definitions from DB at runtime

### Table Definitions

#### `brain_checks` -- Check Definitions (Append-Only)

The authoritative source of truth for all check definitions. Every modification creates a new row with an incremented version number. The current version is the row with the highest version for each check_id.

```sql
CREATE TABLE brain_checks (
    -- Identity
    check_id VARCHAR NOT NULL,              -- e.g., 'FIN.LIQ.position'
    version INTEGER NOT NULL,               -- monotonically increasing per check_id

    -- Classification
    name VARCHAR NOT NULL,                  -- human-readable name
    content_type VARCHAR NOT NULL,          -- EVALUATIVE_CHECK | MANAGEMENT_DISPLAY | INFERENCE_PATTERN
    lifecycle_state VARCHAR NOT NULL,       -- BACKLOG | INVESTIGATION | MONITORING | SCORING | RETIRED
    depth INTEGER NOT NULL DEFAULT 2,       -- 1=display, 2=compute, 3=infer, 4=hunt
    execution_mode VARCHAR NOT NULL DEFAULT 'AUTO',

    -- Dual Organization
    report_section VARCHAR NOT NULL,        -- company | financials | governance | litigation | market | disclosure | forward
    risk_questions VARCHAR[] NOT NULL,      -- ['Q6', 'Q7']
    risk_framework_layer VARCHAR NOT NULL,  -- inherent_risk | hazard | risk_characteristic

    -- Risk Model
    factors VARCHAR[],                      -- ['F1', 'F2']
    hazards VARCHAR[],                      -- ['HAZ-SCA', 'HAZ-DER']
    characteristic_direction VARCHAR,       -- amplifier | mitigator | context | NULL
    characteristic_strength VARCHAR,        -- very_strong | strong | moderate | weak | NULL

    -- Evaluation
    threshold_type VARCHAR NOT NULL,        -- tiered | boolean | percentage | temporal | pattern | etc.
    threshold_red VARCHAR,                  -- RED criterion text
    threshold_yellow VARCHAR,               -- YELLOW criterion text
    threshold_clear VARCHAR,                -- CLEAR criterion text
    pattern_ref VARCHAR,                    -- for INFERENCE_PATTERN checks

    -- Underwriter-Readable
    question VARCHAR NOT NULL,              -- "Is the company financially distressed?"
    rationale TEXT,                          -- WHY this matters for D&O
    interpretation TEXT,                     -- how to read the result

    -- Data Requirements
    field_key VARCHAR,                      -- state model field to evaluate
    required_data VARCHAR[],                -- ['SEC_10K', 'MARKET_PRICE']
    data_locations JSON,                    -- {"SEC_10K": ["item_8_financials"]}
    acquisition_type VARCHAR,               -- structured | broad_search | composite

    -- Industry
    industry_scope VARCHAR NOT NULL DEFAULT 'universal',  -- universal | sector_adjusted | supplement
    applicable_industries VARCHAR[],        -- NULL = all; ['BIOT','HLTH'] = specific
    industry_threshold_overrides JSON,      -- {"BIOT": {"red": "< 0.5"}, "TECH": {"red": "< 0.8"}}

    -- Self-Improvement
    expected_fire_rate FLOAT,
    last_calibrated DATE,
    calibration_notes TEXT,

    -- History
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    created_by VARCHAR NOT NULL DEFAULT 'system',
    change_description TEXT,                -- what changed in this version

    -- Retirement
    retired_at TIMESTAMP,
    retired_reason TEXT,

    PRIMARY KEY (check_id, version)
);

-- View for current (latest) version of each check
CREATE VIEW brain_checks_current AS
SELECT * FROM brain_checks
WHERE (check_id, version) IN (
    SELECT check_id, MAX(version)
    FROM brain_checks
    GROUP BY check_id
);

-- View for active (non-retired) checks only
CREATE VIEW brain_checks_active AS
SELECT * FROM brain_checks_current
WHERE lifecycle_state != 'RETIRED';
```

#### `brain_taxonomy` -- Risk Questions, Report Sections, Factors, Hazards

Stores the organizational structures that checks map into. Changes rarely.

```sql
CREATE TABLE brain_taxonomy (
    entity_type VARCHAR NOT NULL,           -- 'risk_question' | 'report_section' | 'factor' | 'hazard' | 'pillar'
    entity_id VARCHAR NOT NULL,             -- 'Q6' | 'financials' | 'F2' | 'HAZ-SCA' | 'P1_WHAT_WRONG'
    version INTEGER NOT NULL DEFAULT 1,

    name VARCHAR NOT NULL,                  -- "Is the financial condition sound?"
    description TEXT NOT NULL,              -- Extended description
    parent_id VARCHAR,                      -- Hierarchical: Q6 parent = P1_WHAT_WRONG
    weight FLOAT,                           -- For factors: F1 weight = 0.15

    -- For risk_questions
    domain VARCHAR,                         -- 'financial_condition', 'governance', etc.
    aggregation_method VARCHAR,             -- 'worst_of', 'weighted_average', 'count_red'

    -- For hazards
    frequency_trend VARCHAR,               -- 'growing', 'stable', 'declining'
    severity_range VARCHAR,                -- '$14M median settlement'

    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,

    PRIMARY KEY (entity_type, entity_id, version)
);

CREATE VIEW brain_taxonomy_current AS
SELECT * FROM brain_taxonomy
WHERE (entity_type, entity_id, version) IN (
    SELECT entity_type, entity_id, MAX(version)
    FROM brain_taxonomy
    GROUP BY entity_type, entity_id
);
```

#### `brain_backlog` -- Potential Checks Not Yet Implemented (D3)

The prioritized list of signals we COULD add. Nothing is ever removed from this -- items are either promoted (to brain_checks with state=BACKLOG) or deprioritized.

```sql
CREATE TABLE brain_backlog (
    backlog_id VARCHAR PRIMARY KEY,         -- 'BL-001'

    -- What
    title VARCHAR NOT NULL,                 -- "SPAC/De-SPAC Detection"
    description TEXT NOT NULL,              -- Detailed description of what this would check
    underwriting_question TEXT,             -- What question does this answer?
    risk_questions VARCHAR[],              -- Which Q1-Q25 does this relate to?
    hazards VARCHAR[],                     -- Which hazards does this address?

    -- Why
    rationale TEXT NOT NULL,                -- Why do we need this?
    source VARCHAR,                         -- Where did the idea come from?
    gap_reference VARCHAR,                  -- Reference to gap analysis (e.g., "G1" from OLD-SYSTEM-INSIGHTS)

    -- Priority
    priority VARCHAR NOT NULL DEFAULT 'MEDIUM',  -- CRITICAL | HIGH | MEDIUM | LOW
    priority_rationale TEXT,                -- Why this priority level?
    estimated_effort VARCHAR,               -- S | M | L | XL

    -- Data
    data_sources_needed TEXT,               -- What data would feed this check?
    data_available BOOLEAN DEFAULT FALSE,   -- Can we get the data today?
    data_gap_notes TEXT,                    -- What's blocking data acquisition?

    -- Status
    status VARCHAR NOT NULL DEFAULT 'OPEN', -- OPEN | IN_PROGRESS | PROMOTED | DEFERRED
    promoted_to_check_id VARCHAR,           -- If promoted, which check_id was created?

    -- History
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    created_by VARCHAR NOT NULL DEFAULT 'system',

    FOREIGN KEY (promoted_to_check_id) REFERENCES brain_checks(check_id)
);
```

#### `brain_changelog` -- Auto-Generated from Version Diffs (D3)

Auto-populated whenever a new version of a check is inserted. Records the diff between versions.

```sql
CREATE TABLE brain_changelog (
    changelog_id INTEGER PRIMARY KEY,       -- auto-increment

    check_id VARCHAR NOT NULL,
    old_version INTEGER,                    -- NULL for new checks
    new_version INTEGER NOT NULL,

    change_type VARCHAR NOT NULL,           -- CREATED | MODIFIED | RETIRED | PROMOTED | THRESHOLD_CHANGED
    change_description TEXT NOT NULL,       -- Human-readable description
    fields_changed VARCHAR[],              -- ['threshold_red', 'rationale']

    -- Context
    changed_by VARCHAR NOT NULL DEFAULT 'system',
    changed_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    change_reason TEXT,                     -- Why was this change made?
    triggered_by VARCHAR,                   -- 'fire_rate_analysis' | 'override_review' | 'manual'

    FOREIGN KEY (check_id, new_version) REFERENCES brain_checks(check_id, version)
);
```

#### `brain_effectiveness` -- Fire Rates, Override Tracking, Event Correlation (D4)

Stores per-check effectiveness metrics aggregated from pipeline runs.

```sql
CREATE TABLE brain_effectiveness (
    -- Identity
    check_id VARCHAR NOT NULL,
    measurement_period VARCHAR NOT NULL,    -- '2026-Q1', '2026-02', 'all_time'

    -- Fire Rate Metrics
    total_evaluations INTEGER NOT NULL DEFAULT 0,
    red_count INTEGER NOT NULL DEFAULT 0,
    yellow_count INTEGER NOT NULL DEFAULT 0,
    clear_count INTEGER NOT NULL DEFAULT 0,
    info_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    not_available_count INTEGER NOT NULL DEFAULT 0,

    fire_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN total_evaluations > 0
        THEN (red_count + yellow_count)::FLOAT / total_evaluations
        ELSE 0 END
    ) STORED,

    skip_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN total_evaluations > 0
        THEN skipped_count::FLOAT / total_evaluations
        ELSE 0 END
    ) STORED,

    discrimination_power FLOAT,             -- entropy of result distribution (0=no discrimination, 1=max)

    -- Override Tracking
    override_count INTEGER NOT NULL DEFAULT 0,
    override_direction VARCHAR[],           -- ['red_to_clear', 'yellow_to_red', ...]
    override_reasons TEXT[],

    -- Event Correlation (when claims data available)
    companies_with_claims INTEGER DEFAULT 0,
    companies_flagged_before_claim INTEGER DEFAULT 0,  -- sensitivity
    companies_cleared_before_claim INTEGER DEFAULT 0,  -- false negatives

    -- Status Flags
    flagged_always_fires BOOLEAN DEFAULT FALSE,
    flagged_never_fires BOOLEAN DEFAULT FALSE,
    flagged_high_skip BOOLEAN DEFAULT FALSE,
    flagged_low_discrimination BOOLEAN DEFAULT FALSE,

    -- Metadata
    computed_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    run_count INTEGER NOT NULL,             -- number of pipeline runs in this period

    PRIMARY KEY (check_id, measurement_period)
);
```

#### `brain_industry` -- Industry Supplements and Threshold Adjustments (D6)

Stores industry-specific threshold overrides and supplement check activation rules.

```sql
CREATE TABLE brain_industry (
    industry_code VARCHAR NOT NULL,         -- 'BIOT', 'TECH', 'FINS', 'ENGY', 'CDIS', etc.
    version INTEGER NOT NULL DEFAULT 1,

    -- Industry Profile
    name VARCHAR NOT NULL,                  -- 'Biotechnology / Life Sciences'
    sic_codes VARCHAR[],                    -- SIC codes that map to this industry
    naics_codes VARCHAR[],                 -- NAICS codes that map to this industry
    sector_etf VARCHAR,                     -- Primary benchmark ETF (e.g., 'XBI' for biotech)
    alternative_etf VARCHAR,               -- Secondary ETF

    -- Inherent Risk Profile
    base_sca_rate FLOAT,                   -- Annual SCA filing rate for this industry
    base_risk_level VARCHAR,               -- LOW | MODERATE | ELEVATED | HIGH | VERY_HIGH
    typical_claim_types VARCHAR[],         -- ['HAZ-SCA', 'HAZ-SEC', 'HAZ-REG']

    -- Threshold Adjustments (JSON: check_id -> override thresholds)
    threshold_overrides JSON,              -- {"FIN.LIQ.position": {"red": "< 0.5", "yellow": "0.5 - 1.0"}}

    -- Sector Baselines (from Old System MODULE 13)
    baseline_short_interest JSON,          -- {"typical": "2-5%", "elevated": ">8%", "critical": ">15%"}
    baseline_volatility JSON,              -- {"typical": "25-35%", "elevated": ">50%", "high": ">75%"}
    baseline_leverage JSON,                -- {"normal": "<3x", "elevated": "3-5x", "critical": ">5x"}

    -- Supplement Checks (check_ids activated for this industry)
    supplement_check_ids VARCHAR[],        -- ['FIN.SECTOR.biotech_pipeline', 'FIN.SECTOR.fda_status']

    -- Module Priority (from Old System industry-specific module emphasis)
    priority_modules VARCHAR[],            -- ['litigation', 'financial', 'alternative_data']

    -- Operating Metrics (industry-specific KPIs)
    operating_metrics JSON,                -- {"rule_of_40": {"formula": "rev_growth + ebitda_margin", "red": "<20%"}}

    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,

    PRIMARY KEY (industry_code, version)
);
```

#### `brain_check_runs` -- Per-Run Check Results (Extends Existing CheckRun)

This table already exists in the knowledge store (Phase 30). Extended with brain-specific fields.

```sql
CREATE TABLE brain_check_runs (
    run_id VARCHAR NOT NULL,               -- Pipeline run identifier
    check_id VARCHAR NOT NULL,
    check_version INTEGER NOT NULL,

    -- Result
    status VARCHAR NOT NULL,               -- RED | YELLOW | CLEAR | INFO | SKIPPED
    value VARCHAR,                         -- The actual value evaluated
    evidence TEXT,                         -- Evidence string

    -- Context
    ticker VARCHAR NOT NULL,
    run_date TIMESTAMP NOT NULL,
    is_backtest BOOLEAN DEFAULT FALSE,     -- TRUE for historical replays

    -- Industry Context
    industry_code VARCHAR,
    threshold_was_adjusted BOOLEAN DEFAULT FALSE,  -- TRUE if industry override applied

    PRIMARY KEY (run_id, check_id)
);
```

### Index Strategy

```sql
-- Fast lookup of current check definitions
CREATE INDEX idx_checks_current ON brain_checks(check_id, version DESC);

-- Query checks by lifecycle state
CREATE INDEX idx_checks_lifecycle ON brain_checks(lifecycle_state) WHERE version = (
    SELECT MAX(version) FROM brain_checks bc WHERE bc.check_id = brain_checks.check_id
);

-- Query checks by report section (for rendering)
CREATE INDEX idx_checks_section ON brain_checks(report_section);

-- Query checks by risk question (for analysis)
-- Note: DuckDB supports array contains via list_contains()

-- Effectiveness lookups
CREATE INDEX idx_effectiveness_check ON brain_effectiveness(check_id, measurement_period);
CREATE INDEX idx_effectiveness_flags ON brain_effectiveness(flagged_always_fires, flagged_never_fires, flagged_high_skip);

-- Check run history
CREATE INDEX idx_runs_ticker ON brain_check_runs(ticker, run_date);
CREATE INDEX idx_runs_check ON brain_check_runs(check_id, status);
```

---

## 5. Industry Model

### Three-Layer Industry Handling (D6)

The brain handles industry variation through three distinct mechanisms, applied in order:

```
Layer 1: CORE CHECKS (universal -- run for every company)
  │
  │  Apply industry-adjusted thresholds
  │
Layer 2: THRESHOLD ADJUSTMENTS (same check, different calibration by sector)
  │
  │  Activate industry supplements
  │
Layer 3: INDUSTRY SUPPLEMENTS (sector-specific checks that only run for that sector)
```

### Layer 1: Core Checks (Universal)

These checks run for every company regardless of industry. They represent universal D&O risk factors.

**388 current checks are almost entirely core.** The only industry-conditional checks today are `FIN.SECTOR.energy`, `FIN.SECTOR.retail`, and the orphaned `FWRD.EVENT.19-BIOT` through `FWRD.EVENT.22-HLTH`.

Core checks include:
- All financial ratio checks (FIN.LIQ, FIN.DEBT, FIN.PROFIT)
- All governance checks (GOV.BOARD, GOV.EXEC, GOV.PAY)
- All litigation checks (LIT.SCA, LIT.REG, LIT.OTHER)
- All stock market checks (STOCK.PRICE, STOCK.PATTERN, STOCK.SHORT)
- All NLP/disclosure checks (NLP.RISK, NLP.MDA, NLP.DISCLOSURE)
- All forward-looking event checks (FWRD.EVENT)
- Company identity and classification (BIZ.CLASS, BIZ.SIZE)

### Layer 2: Industry-Adjusted Thresholds

The same check runs for all companies, but what constitutes RED/YELLOW/CLEAR varies by sector. This is critical because financial "normal" differs dramatically by industry.

**Threshold adjustment examples from the Old System (MODULE 13: Sector Baselines):**

| Check | Universal Threshold | Biotech Override | Financial Services Override | Energy Override |
|---|---|---|---|---|
| `FIN.DEBT.structure` (Debt/EBITDA) | RED: > 5x | RED: N/A (pre-revenue) | RED: > 8x (higher leverage norm) | RED: > 4x (commodity risk) |
| `FIN.LIQ.cash_burn` (Cash Runway) | RED: < 12 months | RED: < 18 months (longer trials) | N/A (profitable) | RED: < 12 months |
| `STOCK.SHORT.position` (Short Interest) | RED: > 15% | RED: > 20% (biotech volatile) | RED: > 10% (lower norm) | RED: > 12% |
| `FIN.PROFIT.margins` (Margin Compression) | RED: > 500bps | RED: N/A (no margins) | RED: > 300bps (tighter) | RED: > 800bps (commodity cycles) |
| `STOCK.PRICE.recent_drop_alert` (Stock Decline) | RED: > 30% | RED: > 50% (binary events) | RED: > 25% | RED: > 35% |

**Storage:** Threshold overrides are stored in the `brain_industry.threshold_overrides` JSON column, keyed by check_id. At evaluation time, the engine checks if an override exists for the company's industry; if so, it uses the override thresholds instead of the check's default.

**Sector codes** (from Old System, 13 sectors):

| Code | Sector | Base Risk Level | Typical Claim Types |
|---|---|---|---|
| BIOT | Biotechnology/Life Sciences | VERY_HIGH | HAZ-SCA, HAZ-SEC, HAZ-REG |
| TECH | Technology | HIGH | HAZ-SCA, HAZ-AI, HAZ-CYBER |
| FINS | Financial Services | HIGH | HAZ-SEC, HAZ-REG, HAZ-DER |
| HLTH | Healthcare | HIGH | HAZ-SCA, HAZ-REG, HAZ-PRODUCT |
| ENGY | Energy | ELEVATED | HAZ-ESG, HAZ-REG, HAZ-SCA |
| CDIS | Consumer Discretionary | MODERATE | HAZ-SCA, HAZ-EMPL, HAZ-PRODUCT |
| STPL | Consumer Staples | MODERATE | HAZ-PRODUCT, HAZ-EMPL |
| INDU | Industrials | MODERATE | HAZ-SCA, HAZ-REG |
| REIT | Real Estate | MODERATE | HAZ-BANK, HAZ-SCA |
| COMM | Communications | MODERATE | HAZ-SCA, HAZ-AI |
| MATL | Materials | MODERATE | HAZ-REG, HAZ-ESG |
| UTIL | Utilities | LOW-MODERATE | HAZ-REG |
| SPEC | Special Situations (SPAC, crypto, cannabis) | VERY_HIGH | HAZ-SPAC, HAZ-SEC, HAZ-REG |

### Layer 3: Industry Supplements

Sector-specific checks that only activate when a company belongs to that sector. These capture risks that are irrelevant for other sectors.

**Biotech/Life Sciences Supplement (from Old System B.7.2, Module 6 Section 6):**

| Supplement Check | What It Checks | Data Source |
|---|---|---|
| `FIN.SECTOR.biotech_pipeline` | Drug pipeline stage analysis (phase, indication, PDUFA date) | ClinicalTrials.gov, 10-K |
| `FIN.SECTOR.biotech_cash_runway` | Cash runway to next catalyst (different from generic cash runway) | Cash flow + pipeline dates |
| `FIN.SECTOR.biotech_fda_status` | FDA status: pending decisions, CRLs, inspection status | FDA.gov |
| `FIN.SECTOR.biotech_patent_cliff` | Key patent expirations, revenue at risk | 10-K, patent filings |
| `FIN.SECTOR.biotech_pubpeer` | PubPeer comments on company-sponsored research | PubPeer.com |
| `FIN.SECTOR.biotech_retraction` | Retraction Watch for paper retractions | RetractionWatch.com |

**SaaS/Software Supplement (from Old System B.7.1):**

| Supplement Check | What It Checks | Data Source |
|---|---|---|
| `FIN.SECTOR.saas_rule_of_40` | Revenue growth + EBITDA margin > 40% | Financial statements |
| `FIN.SECTOR.saas_nrr` | Net Revenue Retention (NRR) -- <90% = CRITICAL | Earnings releases |
| `FIN.SECTOR.saas_cac_payback` | CAC Payback Period -- >36mo = CRITICAL | Financial statements |
| `FIN.SECTOR.saas_churn` | Gross churn rate | Company disclosures |

**Financial Services Supplement (from Old System B.7.3):**

| Supplement Check | What It Checks | Data Source |
|---|---|---|
| `FIN.SECTOR.finserv_capital` | CET1, Total Capital, Leverage vs minimums | Regulatory filings |
| `FIN.SECTOR.finserv_npl` | Non-performing loan ratio and trend | 10-Q |
| `FIN.SECTOR.finserv_nim` | Net interest margin trend (8 quarters) | 10-Q |
| `FIN.SECTOR.finserv_reserves` | Loan loss reserves / NPLs adequacy | 10-Q |

**Energy Supplement (from Old System C.5, energy_sector_litigation_patterns.md):**

| Supplement Check | What It Checks | Data Source |
|---|---|---|
| `FIN.SECTOR.energy_rrr` | Reserve replacement ratio | 10-K |
| `FIN.SECTOR.energy_hedging` | Hedging program assessment | 10-K derivatives footnote |
| `FIN.SECTOR.energy_commodity` | Output pricing exposure, % hedged | 10-K, MD&A |
| `FIN.SECTOR.energy_esg` | ESG/greenwashing specific risks (Exxon precedent) | Sustainability reports |

**Retail Supplement (from Old System B.7.4):**

| Supplement Check | What It Checks | Data Source |
|---|---|---|
| `FIN.SECTOR.retail_comps` | Comparable store sales trends | Earnings releases |
| `FIN.SECTOR.retail_stores` | Store count trends (opens, closes, net) | 10-K |
| `FIN.SECTOR.retail_inventory` | Inventory turn with retail-specific thresholds | Financial statements |
| `FIN.SECTOR.retail_ecommerce` | E-commerce penetration rate | Earnings releases |

**Supplement activation:** When `BIZ.CLASS.primary` classifies a company into a sector, the engine queries `brain_industry.supplement_check_ids` for that sector code and activates those additional checks.

---

## 6. Data Source Mapping

### Data Sources by Check Category

Each check category maps to specific data sources. The table below specifies whether the source is structured (API/filing) or unstructured (broad web search), and whether the current system supports it. This directly addresses D8 (broad web search as first-class).

#### Inherent Risk Checks (Q1-Q3, Q25)

| Check Category | Primary Source | Secondary Source | Structured/Unstructured | Current System? |
|---|---|---|---|---|
| Company identity (BIZ.CLASS) | SEC EDGAR (SIC codes, filing dates) | EdgarTools MCP | Structured | YES |
| Market cap / size (BIZ.SIZE) | yfinance (market cap, shares outstanding) | SEC 10-K (revenue, employees) | Structured | YES |
| Business model (BIZ.MODEL) | SEC 10-K (business description, revenue breakdown) | EdgarTools MCP | Structured | YES |
| Revenue concentration (BIZ.DEPEND) | SEC 10-K (customer/supplier disclosures) | 10-K Risk Factors | Structured | YES |
| Competitive position (BIZ.COMP) | SEC 10-K (industry description) | Web search (industry reports) | Composite | PARTIAL |
| AI/cyber exposure (BIZ.UNI) | SEC 10-K (risk factors) | **Broad web search** (AI claims, cyber incidents) | Composite | PARTIAL |
| **SPAC detection (NEW)** | SEC 8-K (merger filings), S-4 | **Broad web search** (SPAC litigation) | Composite | **NO** |

#### Securities Litigation Checks (Q4)

| Check Category | Primary Source | Secondary Source | Structured/Unstructured | Current System? |
|---|---|---|---|---|
| Active SCA search | Stanford SCAC (Playwright MCP) | **Broad web search** (`"[Company] securities class action"`) | Composite | YES |
| SCA details | Stanford SCAC, CourtListener API | PACER (federal court records) | Structured | YES |
| SCA history | Stanford SCAC database | SEC EFTS (10-K Item 3) | Structured | YES |
| Derivative suits | CourtListener, Delaware Chancery | **Broad web search** | Composite | PARTIAL |
| Pre-filing activity | **Broad web search** (law firm announcements) | News monitoring | **Unstructured** | YES (blind spot sweep) |

#### Other Litigation & Regulatory Checks (Q5)

| Check Category | Primary Source | Secondary Source | Structured/Unstructured | Current System? |
|---|---|---|---|---|
| SEC enforcement | SEC Litigation Releases, AAER | SEC EFTS, **Broad web search** | Composite | PARTIAL |
| DOJ investigation | **Broad web search** (`"[Company] DOJ investigation indictment"`) | DOJ press releases | **Unstructured** | **GAP** (missing DOJ-specific search terms) |
| State AG actions | **Broad web search** (`"[Company] attorney general investigation"`) | StateAG.org database | **Unstructured** | **GAP** (missing state AG search terms) |
| FTC enforcement | FTC Cases & Proceedings database | **Broad web search** | Composite | **NO** |
| EPA/environmental | EPA ECHO (800K+ facilities) | **Broad web search** | Structured | **NO** |
| OSHA/workplace | OSHA Establishment Search | **Broad web search** | Structured | PARTIAL (search only) |
| CFPB complaints | CFPB API (free, documented) | **Broad web search** | Structured | PARTIAL (search only) |
| FDA enforcement | FDA Warning Letters, 483 database | **Broad web search** | Structured | PARTIAL (search only) |

#### Financial Condition Checks (Q6-Q8)

| Check Category | Primary Source | Secondary Source | Structured/Unstructured | Current System? |
|---|---|---|---|---|
| Liquidity ratios | XBRL financial data (SEC API) | EdgarTools MCP (10-K/10-Q) | Structured | YES |
| Leverage/debt | XBRL financial data | 10-K debt footnotes | Structured | YES |
| Profitability | XBRL financial data | Income statement analysis | Structured | YES |
| Cash flow | XBRL financial data | Cash flow statement | Structured | YES |
| Temporal trends (FIN.TEMPORAL) | Multi-period XBRL data | Quarter-over-quarter comparison | Structured | YES |
| Forensic models (FIN.FORENSIC) | Computed from XBRL inputs | Academic model formulas | Structured | YES |
| Earnings quality (FIN.QUALITY) | XBRL + 10-K text analysis | Multi-field computation | Structured | YES |
| **Altman Z-Score (NEW)** | XBRL financial data | Computed formula | Structured | **NO** (inputs available) |
| **Going concern (NEW)** | 10-K auditor's report | 8-K Item 4.02 | Structured | **NO** |
| Guidance track record | 8-K earnings releases vs guidance | **Broad web search** (earnings miss reporting) | Composite | PARTIAL |

#### Governance & Management Checks (Q9-Q14)

| Check Category | Primary Source | Secondary Source | Structured/Unstructured | Current System? |
|---|---|---|---|---|
| Board composition | DEF 14A proxy statement | EdgarTools MCP | Structured | PARTIAL (parsing incomplete) |
| Executive profiles | DEF 14A, 10-K | **Broad web search** (executive background) | Composite | PARTIAL |
| Compensation | DEF 14A Summary Compensation Table | XBRL compensation data | Structured | PARTIAL (parsing incomplete) |
| Shareholder rights | DEF 14A, Charter, Bylaws | | Structured | PLACEHOLDER (10 checks) |
| Insider trading | Form 4 filings (SEC EDGAR) | OpenInsider, SECForm4.com | Structured | **CRITICAL GAP** |
| Executive departures | 8-K Item 5.02 | **Broad web search** (departure news) | Composite | PARTIAL (8-K not systematically parsed) |
| Auditor changes | 8-K Item 4.01 | PCAOB inspection reports | Structured | **GAP** (8-K not event-parsed) |
| Activist campaigns | Schedule 13D (SEC EDGAR) | **Broad web search** (activist investor news) | Composite | PARTIAL (config exists, data unclear) |
| **Say-on-pay results (NEW)** | 8-K annual meeting results | DEF 14A disclosure | Structured | **NO** |
| **Employee sentiment (NEW)** | **Broad web search** (Glassdoor, Indeed) | Playwright MCP (scraping) | **Unstructured** | **NO** |

#### Market & Stock Checks (Q15-Q18)

| Check Category | Primary Source | Secondary Source | Structured/Unstructured | Current System? |
|---|---|---|---|---|
| Stock price/returns | yfinance | Yahoo Finance API | Structured | YES |
| Stock patterns | Computed from price history | | Structured | YES |
| Short interest | yfinance (basic SI) | FINRA data (official, semi-monthly) | Structured | PARTIAL (yfinance may be stale) |
| Short seller reports | **Broad web search** (`"[Company] short seller report Hindenburg"`) | Breakout Point tracker | **Unstructured** | PARTIAL (blind spot sweep) |
| Ownership structure | yfinance (institutional holders) | SEC 13F filings | Structured | PARTIAL |
| Analyst coverage | yfinance (analyst data) | **Broad web search** (downgrades) | Composite | PARTIAL |
| **Options implied volatility (FUTURE)** | Options chain data | | Structured | **NO** |

#### Disclosure & NLP Checks (Q19, Q23-Q24)

| Check Category | Primary Source | Secondary Source | Structured/Unstructured | Current System? |
|---|---|---|---|---|
| Risk factor changes | 10-K Item 1A (year-over-year diff) | EdgarTools MCP | Structured | YES |
| MD&A tone analysis | 10-K Item 7 (NLP analysis) | | Structured | YES |
| Filing timing | SEC EDGAR filing dates | | Structured | YES |
| Whistleblower language | 10-K/10-Q text search | | Structured | YES |
| **Loughran-McDonald sentiment (FUTURE)** | 10-K/10-Q full text | Notre Dame SRAF dictionary | Structured | **NO** |
| **SEC comment letters (NEW)** | SEC EDGAR CORRESP filings | EdgarTools MCP | Structured | **NO** |
| **10-K risk factor diff (NEW)** | Year-over-year 10-K comparison | | Structured | **NO** |

#### Forward-Looking & Early Warning Checks (Q20-Q22)

| Check Category | Primary Source | Secondary Source | Structured/Unstructured | Current System? |
|---|---|---|---|---|
| Earnings calendar | yfinance, company IR | 8-K | Structured | YES |
| Debt maturities | 10-K debt footnote | XBRL | Structured | YES |
| Regulatory decisions | FDA.gov, regulatory calendars | **Broad web search** | Composite | PARTIAL |
| Macro headwinds | **Broad web search** (economic data, regulatory trackers) | | **Unstructured** | PLACEHOLDER |
| Employee early warnings | **Broad web search** (Glassdoor, LinkedIn, WARN Act) | WARNTracker.com, layoffdata.com | **Unstructured** | **NO** |
| Customer complaints | **Broad web search** (app reviews, BBB, CFPB) | CFPB API | Composite | **NO** |
| **Congressional investigations (FUTURE)** | **Broad web search** (`"[Company] congressional hearing subpoena"`) | GovInfo.gov | **Unstructured** | **NO** |

### Acquisition Priority Tiers

Based on impact and feasibility, data source development should follow this priority:

**Tier 1: High Impact, Achievable Now (Phase 32-33)**
1. 8-K Event Stream Monitoring (auditor changes, exec departures, non-reliance) -- fills F3, F4, F10 gaps
2. Form 4 Insider Transaction Analysis (cluster selling, timing) -- fills major F2 gap
3. Expanded Blind Spot Search Queries (DOJ, state AG, FTC, WARN Act) -- fills F1 + regulatory coverage
4. 10-K Risk Factor Diff Analysis (year-over-year comparison) -- signals emerging risks
5. SEC Comment Letter (CORRESP) Monitoring -- SEC review questions

**Tier 2: High Impact, Moderate Effort**
6. AAER / SEC Enforcement Database (SEED/NYU) -- critical for F1, F3
7. EPA ECHO + OSHA Integration -- industry-specific but powerful
8. CFPB API Integration -- complaint trends for financial services
9. Going Concern + Auditor Report Parsing -- critical for F3, F8
10. Glassdoor Employee Sentiment -- research-validated leading indicator

**Tier 3: Valuable, Longer-Term**
11. FINRA Direct Short Interest Data
12. PubPeer / Retraction Watch (biotech/pharma)
13. Loughran-McDonald Sentiment Analysis
14. Schedule 13D / Activist Investor Tracking
15. PCAOB Inspection Reports

**Tier 4: Nice-to-Have**
16-25. Social media sentiment, supply chain monitoring, patent/IP tracking, options IV, job posting analysis, BBB complaints, ISS/Glass Lewis scores, credit ratings, congressional investigations, dark web monitoring

---

## 7. Self-Improvement Architecture

### Design Philosophy (D4)

The brain is relentlessly self-questioning. It tracks five dimensions of its own performance and uses the results to improve continuously. User mandate: "Keep questioning why we need things and whether we can do better."

```
                    ┌──────────────────────┐
                    │  SELF-IMPROVEMENT     │
                    │  ENGINE               │
                    └──────────┬───────────┘
                               │
         ┌─────────┬───────────┼───────────┬──────────┐
         │         │           │           │          │
    ┌────▼───┐ ┌───▼────┐ ┌───▼───┐ ┌─────▼────┐ ┌───▼──────┐
    │ Fire   │ │Override│ │ Event │ │ Provided │ │ Self-    │
    │ Rate   │ │Tracking│ │Correl.│ │ Feedback │ │ Analysis │
    │Analysis│ │        │ │       │ │          │ │          │
    └────────┘ └────────┘ └───────┘ └──────────┘ └──────────┘
```

### Mechanism 1: Fire Rate Analysis

**What:** Track how often each check fires (produces RED or YELLOW) across all companies analyzed.

**Why:** A check that NEVER fires may have a threshold set too conservatively or may test for something that doesn't occur. A check that ALWAYS fires may have a threshold set too aggressively. The useful checks are those with intermediate fire rates that differentiate companies.

**Thresholds for action:**
| Condition | Action |
|---|---|
| Fire rate = 0% over 20+ runs | Investigate: threshold unreachable? Check still relevant? |
| Fire rate > 80% over 20+ runs | Investigate: threshold too sensitive? Universal condition? |
| Not-available rate > 50% | Data acquisition gap: check can't get what it needs |
| Low discrimination power (entropy < 0.3) | Check doesn't differentiate risk -- recalibrate or retire |

**Storage:** `brain_effectiveness` table, computed after each pipeline run. `measurement_period` tracks both per-quarter and all-time statistics.

**Implementation:** After each pipeline run, the pipeline writes check results to `brain_check_runs`. A post-run step aggregates results into `brain_effectiveness` for the current period. Flagging logic sets `flagged_always_fires`, `flagged_never_fires`, `flagged_high_skip`, and `flagged_low_discrimination`.

### Mechanism 2: Override Tracking

**What:** When a human underwriter disagrees with a check result, that disagreement is recorded as an override.

**Why:** Overrides are signal. If underwriters consistently override a check, the check is miscalibrated. If overrides cluster in one direction (e.g., always upgrading from RED to CLEAR), the threshold is too aggressive. If overrides are random, the check may be capturing real uncertainty.

**Data captured per override:**
- check_id, original_result (RED/YELLOW/CLEAR), overridden_to (RED/YELLOW/CLEAR)
- override_reason (free text)
- overrider_id (who overrode)
- timestamp

**Analysis triggers:**
- >3 overrides on same check in same direction within 90 days: flag for threshold review
- Override rate >25% for any check: automatic calibration review

### Mechanism 3: Event Correlation

**What:** Retrospective analysis when D&O claims are actually filed. Did the brain predict it? What did it miss?

**Why:** This is the ultimate validation. A RED flag that never leads to a claim is a false positive. A CLEAR assessment for a company that faces a major claim is a dangerous miss.

**Implementation approach:**
```
For each company that experiences a D&O event:
  1. Look up the most recent brain assessment before the event
  2. Record: which checks were RED, YELLOW, CLEAR, SKIPPED
  3. Compute: sensitivity (of flagged companies, what % had events?)
  4. Compute: specificity (of cleared companies, what % stayed clean?)
  5. Identify: which checks were the best predictors?
  6. Identify: which hazard categories were missed?
```

**Short-term proxies (before actual claims data):**
- Securities class action filing within 24 months (Stanford SCAC)
- Stock drop > 20% within 12 months
- SEC enforcement action within 24 months
- Restatement within 12 months

**Storage:** `brain_effectiveness.companies_with_claims`, `companies_flagged_before_claim`, `companies_cleared_before_claim`.

### Mechanism 4: Self-Analysis

**What:** The brain periodically questions its own structure and identifies gaps.

**Triggers for self-analysis:**
1. **New hazard type emerges** (e.g., AI claims doubled in 2024) -- does the brain have adequate checks?
2. **Coverage gap detected** -- a hazard category has zero or very few checks
3. **Backlog items accumulate** -- high-priority backlog items not being promoted
4. **Check distribution skew** -- too many checks in one area, too few in another
5. **Industry shift** -- new SEC filing trend (crypto, AI) without corresponding brain coverage

**Automated gap detection queries:**

```sql
-- Hazards without adequate check coverage
SELECT h.entity_id AS hazard_code, h.name AS hazard_name,
       COUNT(DISTINCT c.check_id) AS check_count
FROM brain_taxonomy_current h
LEFT JOIN brain_checks_active c ON list_contains(c.hazards, h.entity_id)
WHERE h.entity_type = 'hazard'
GROUP BY h.entity_id, h.name
HAVING check_count < 3
ORDER BY check_count ASC;

-- Risk questions without adequate check coverage
SELECT t.entity_id AS question_id, t.name AS question_text,
       COUNT(DISTINCT c.check_id) AS check_count,
       SUM(CASE WHEN c.lifecycle_state = 'SCORING' THEN 1 ELSE 0 END) AS scoring_checks
FROM brain_taxonomy_current t
LEFT JOIN brain_checks_active c ON list_contains(c.risk_questions, t.entity_id)
WHERE t.entity_type = 'risk_question'
GROUP BY t.entity_id, t.name
HAVING scoring_checks < 2
ORDER BY scoring_checks ASC;

-- Checks with no fire in 20+ evaluations (dead checks)
SELECT check_id, total_evaluations, fire_rate, skip_rate
FROM brain_effectiveness
WHERE measurement_period = 'all_time'
  AND total_evaluations >= 20
  AND fire_rate = 0.0
ORDER BY total_evaluations DESC;
```

### Mechanism 5: Backtesting

**What:** Run the current brain against historical company data and compare results to known outcomes.

**Implementation:**
```
For each historical company-year in the database:
  1. Load the state snapshot from that period
  2. Run all current checks against that snapshot
  3. Record results to brain_check_runs with is_backtest = TRUE
  4. Compare to known outcomes (claim filed, settlement, stock drop)

Metrics:
  - Sensitivity: of companies that had claims, what % did we flag?
  - Specificity: of companies that didn't have claims, what % did we clear?
  - Lift: how much better is the brain than random?
  - Factor-level: which F1-F10 factors are most predictive?
```

**Current data:** Historical state files exist for AAPL and TSLA (4-7MB each). Statistical significance requires 50+ company-years, so this infrastructure is built now for future use as the company corpus grows.

**A/B testing for rule changes:** When modifying a threshold, run both old and new versions against the same company set and compare:
- Which companies changed result?
- In what direction?
- Does the change improve alignment with known outcomes?

---

## 8. Migration Path

### Current State

| Metric | Value |
|---|---|
| Total checks in checks.json | 388 |
| Checks with defined criteria (can evaluate) | 198 (51%) |
| Placeholder checks (tiered, no criteria) | 190 (49%) |
| Content types | EVALUATIVE_CHECK: 305, MANAGEMENT_DISPLAY: 64, INFERENCE_PATTERN: 19 |
| Factor mappings | 324 checks have F1-F10; 64 without (all CONTEXT_DISPLAY -- correct) |
| Prefix categories | BIZ: 40, EXEC: 20, FIN: 58, FWRD: 83, GOV: 81, LIT: 56, NLP: 15, STOCK: 35 |
| Identified redundancies | ~14 clusters involving ~45 checks; consolidation saves ~20-25 |
| Identified gaps vs Old System | 30 gap items (G1-G30), ~40-50 new checks needed |
| Naming/description mismatches | ~15-20 checks need ID/description fixes |

### Migration Phases

**The migration is incremental. No big-bang rewrite. Each phase is independently deployable and testable.**

#### Phase A: Foundation (DuckDB Brain + Metadata Enrichment)
**What changes:** Create `brain.duckdb` and populate it from current `checks.json`. Add new metadata fields to CheckDefinition.
**What stays the same:** Pipeline continues reading from checks.json. No behavior changes.

Steps:
1. Create `brain.duckdb` with the schema defined in Section 4
2. Write a migration script that reads current `checks.json` and inserts all 388 checks as version 1
3. Add new metadata fields to each check: `report_section`, `risk_questions`, `risk_framework_layer`, `hazards`, `lifecycle_state`
4. Populate `brain_taxonomy` with the 25 risk questions (Q1-Q25), 10 factors (F1-F10), 15 hazard codes, and 7 report sections
5. Populate `brain_industry` with 13 sector codes and baseline data from Old System MODULE 13
6. Populate `brain_backlog` with the 30 gap items (G1-G30) from OLD-SYSTEM-INSIGHTS

**Validation:** All 388 checks have valid metadata. Every check maps to at least one risk question. Every evaluative check maps to at least one factor.

#### Phase B: Fix Known Issues
**What changes:** Fix naming mismatches, consolidate true redundancies. Brain DB updated; checks.json regenerated from DB.
**What stays the same:** Pipeline behavior unchanged (same checks fire, same results).

Steps:
1. Fix naming mismatches (R6, R14, O2 from CHECK-REORGANIZATION):
   - BIZ.DEPEND checks: align IDs with descriptions
   - BIZ.SIZE.growth_trajectory / BIZ.SIZE.public_tenure: fix swapped names
   - LIT.REG.doj_investigation, LIT.REG.industry_reg, LIT.REG.ftc_investigation: rename to match actual content
   - FWRD.EVENT.19-BIOT etc.: replace with descriptive names
2. Consolidate true redundancies (R1-R13):
   - Merge EXEC.PROFILE display checks into GOV.BOARD evaluative counterparts (keep GOV.BOARD, retire EXEC.PROFILE duplicates)
   - Consolidate SEC investigation lifecycle (R5) into single check with stages
   - Consolidate executive turnover checks (R8-R10) -- keep richest version, retire duplicates
   - Consolidate insider selling checks (R11-R12)
   - Consolidate material weakness checks (R13)
3. Reclassify 7 FWRD.WARN financial checks (zone_of_insolvency, goodwill_risk, etc.) as aliases to FIN checks
4. Generate new `checks.json` from `brain.duckdb` using the `brain_checks_active` view

**Validation:** All existing tests pass. Pipeline output unchanged. Retired checks have `lifecycle_state = 'RETIRED'` with documented reason.

#### Phase C: Add Critical Gap Checks
**What changes:** Add highest-priority new checks. They start in MONITORING state (run, collect data, but don't affect score).
**What stays the same:** Scoring unchanged. Existing check behavior unchanged.

Priority new checks (from OLD-SYSTEM-INSIGHTS G1-G7):
1. **SPAC/De-SPAC detection** (G1) -- 5 checks
2. **Going concern explicit flag** (G2) -- 1 check
3. **Altman Z-Score** (G3) -- 1 check (data already available in XBRL)
4. **Revenue fraud pattern taxonomy** (G5) -- 6-8 pattern-specific checks
5. **Derivative risk category assessment** (G6) -- 5 category checks
6. **AI-specific hazard checks** (G7) -- 7 hazard checks
7. **AGR Score** (G4) -- 1 check

All new checks enter as `lifecycle_state = 'MONITORING'`. They appear in the detailed report but do NOT influence risk scores until promoted.

#### Phase D: Pipeline Reads from Brain DB
**What changes:** Pipeline reads check definitions from `brain.duckdb` instead of `checks.json`. `checks.json` becomes a generated artifact.
**What stays the same:** All check evaluation logic. All mapper code. All renderer code.

Steps:
1. Create `BrainDBLoader` that reads from `brain_checks_active` view
2. Wire `BrainDBLoader` into `BackwardCompatLoader` as an alternative source
3. Pipeline configuration flag: `brain_source = "duckdb"` (default) or `brain_source = "json"` (fallback)
4. `checks.json` is now auto-generated from the DB on each brain update
5. `brain_changelog` is auto-populated on every check modification

**Validation:** Pipeline produces identical output whether reading from JSON or DuckDB.

#### Phase E: Effectiveness Tracking Live
**What changes:** After each pipeline run, effectiveness metrics are computed and stored.
**What stays the same:** Pipeline execution. Scoring.

Steps:
1. Post-run hook writes check results to `brain_check_runs`
2. Aggregation step computes `brain_effectiveness` metrics
3. CLI command `do-uw brain effectiveness` displays the report
4. CLI command `do-uw brain gaps` shows coverage gap analysis
5. CLI command `do-uw brain backtest` replays checks against historical state files

#### Phase F: Promote Monitoring Checks to Scoring (Ongoing)
**What changes:** Validated MONITORING checks are promoted to SCORING based on effectiveness data.
**Promotion criteria:**
- Fire rate between 5% and 80% (discriminates)
- Skip rate below 50% (data available)
- At least 10 evaluations
- Discrimination power > 0.3

This phase is ongoing -- it happens continuously as more companies are analyzed and more data accumulates.

### Integration Within do-uw (D12)

The brain database and all infrastructure lives within the current do-uw project. No external dependencies.

**File structure:**
```
src/do_uw/
  brain/
    brain.duckdb          -- The brain database (gitignored, generated)
    checks.json           -- Generated from brain DB (backward compat)
    patterns.json         -- Composite pattern definitions
    brain_schema.py       -- DuckDB schema DDL
    brain_loader.py       -- Load checks from DuckDB
    brain_writer.py       -- Write/update checks in DuckDB
    brain_migrate.py      -- Migration scripts (JSON -> DuckDB)
    brain_docs.py         -- Documentation generation from DB
  knowledge/
    effectiveness.py      -- Fire rate, calibration, gap detection
    backtest.py           -- Historical replay
    requirements.py       -- Acquisition manifest from check declarations
    gap_detector.py       -- Pipeline gap analysis
```

**CLI commands:**
```
do-uw brain status         -- Show brain summary (check counts, lifecycle distribution)
do-uw brain gaps           -- Run pipeline gap detection
do-uw brain effectiveness  -- Show check effectiveness metrics
do-uw brain backtest       -- Replay checks against historical states
do-uw brain export-docs    -- Generate readable documentation
do-uw brain changelog      -- Show recent brain changes
do-uw brain backlog        -- Show prioritized backlog
```

---

## 9. The 25 Underwriting Questions

### Organized by Report Section

These are the complete 25 underwriting questions, each with its check mappings, organized first by the report section they appear in, then cross-referenced to the risk framework layer.

---

#### Report Section: Company Profile

**Q1: What is this company and how risky is it inherently?**
*Risk framework: INHERENT RISK*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| What does this company do? | BIZ.MODEL.description, BIZ.COMP.market_position | Active |
| What D&O risk category? | BIZ.CLASS.primary, BIZ.CLASS.secondary | Active |
| How big is it? | BIZ.SIZE.market_cap, BIZ.SIZE.revenue_ttm, BIZ.SIZE.employees | Active |
| How long public? | BIZ.SIZE.public_tenure, BIZ.SIZE.growth_trajectory | Active (names swapped -- fix) |
| Prior SCA history? | BIZ.CLASS.litigation_history | Active |
| **Is this a SPAC/De-SPAC?** | **(NEW)** | **GAP (G1)** |

**Check count:** 12 existing + 5 new SPAC = 17

**Q2: How sustainable and diversified is the business model?**
*Risk framework: INHERENT RISK*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Revenue model? | BIZ.MODEL.revenue_type, revenue_segment, revenue_geo | Active |
| Cost structure risk? | BIZ.MODEL.cost_structure, leverage_ops | Active |
| Regulatory dependency? | BIZ.MODEL.regulatory_dep | Active |
| Customer/supplier concentration? | BIZ.DEPEND.customer_conc, supplier_conc | Active (names need fixing) |
| Key-person dependency? | BIZ.DEPEND.key_person | Active |

**Check count:** 17

**Q3: What is the competitive landscape and how does it affect risk?**
*Risk framework: INHERENT RISK*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Competitive position? | BIZ.COMP.threat_assessment, barriers_entry, moat | Active |
| Industry growing or contracting? | BIZ.COMP.industry_growth, headwinds | Active |
| Peer litigation frequency? | BIZ.COMP.peer_litigation | Active |

**Check count:** 8

**Q25: Does this company have unique/emerging risk exposures?**
*Risk framework: HAZARD*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| AI claims exposure? | BIZ.UNI.ai_claims | Active (display only) |
| Cybersecurity posture? | BIZ.UNI.cyber_posture, cyber_business | Active |
| **7 AI-specific hazard types?** | **(NEW)** | **GAP (G7)** |
| **ESG/greenwashing risk?** | **(NEW)** | **GAP (G10)** |

**Check count:** 3 existing + 11 new = 14

---

#### Report Section: Financial Condition

**Q6: Is the financial condition sound, or is there distress risk?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Short-term obligations? | FIN.LIQ.position, working_capital, efficiency, trend, cash_burn | Active |
| Debt sustainable? | FIN.DEBT.structure, coverage, maturity, credit_rating, covenants | Active |
| Profitable? | FIN.PROFIT.revenue, margins, earnings, segment | Active |
| Trends deteriorating? | FIN.TEMPORAL.* (10 checks) | Active |
| Industry-specific financial risks? | FIN.SECTOR.* | Placeholder |
| **Altman Z-Score?** | **(NEW)** | **GAP (G3)** |
| **Going concern?** | **(NEW)** | **GAP (G2)** |

**Check count:** 27 existing + 2 new = 29

**Q7: Are the financial statements reliable?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Restatement? | FIN.ACCT.restatement, magnitude, pattern, auditor_link, stock_window | Active |
| Internal controls? | FIN.ACCT.internal_controls, material_weakness | Active/Placeholder |
| Auditor reliable? | FIN.ACCT.auditor, auditor_disagreement | Active/Placeholder |
| Forensic models? | FIN.FORENSIC.* (6 checks) | Active |
| Earnings quality? | FIN.QUALITY.* (7 checks) | Active |
| **Revenue fraud patterns?** | **(NEW -- 8 patterns)** | **GAP (G5)** |
| **AGR Score?** | **(NEW)** | **GAP (G4)** |
| **Non-audit fee ratio?** | **(NEW)** | **GAP (G11)** |

**Check count:** 26 existing + 10 new = 36

**Q8: Is management guidance credible?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Guidance outstanding? | FIN.GUIDE.current, philosophy | Placeholder |
| Track record? | FIN.GUIDE.track_record | Active |
| Market reaction? | FIN.GUIDE.earnings_reaction | Placeholder |
| Analyst expectations? | FIN.GUIDE.analyst_consensus | Placeholder |

**Check count:** 5

---

#### Report Section: Governance & Management

**Q9: Is the board providing adequate oversight?**
*Risk framework: RISK CHARACTERISTIC (mitigator/amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Board composition? | GOV.BOARD.size, independence, ceo_chair, diversity | Active/Mixed |
| Board engaged? | GOV.BOARD.tenure, overboarding, attendance, expertise, meetings, committees | Placeholder |
| Governance controls? | GOV.EFFECT.* (10 checks) | Placeholder |
| Governance ratings? | GOV.EFFECT.iss_score, proxy_advisory | Placeholder |
| **Caremark duty assessment?** | **(NEW)** | **GAP (G6, partial)** |

**Check count:** 23 existing + partial from G6

**Q10: Is the executive team trustworthy and stable?**
*Risk framework: RISK CHARACTERISTIC (mitigator/amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Key executives? | GOV.EXEC.ceo_profile, cfo_profile, other_officers | Active |
| Leadership stable? | GOV.EXEC.stability, turnover_analysis, departure_context | Active |
| Succession plan? | GOV.EXEC.succession_status | Active |
| Prior litigation? | EXEC.PRIOR_LIT.any_officer, ceo_cfo | Active |
| Individual risk scores? | EXEC.CEO.risk_score, EXEC.CFO.risk_score | Active |

**Check count:** 31 (after consolidation of redundancies, ~26)

**Q11: Are insiders trading in concerning patterns?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Overall insider activity? | STOCK.INSIDER.summary, GOV.INSIDER.net_selling | Active/Placeholder |
| 10b5-1 plan concerns? | GOV.INSIDER.10b5_plans, plan_adoption | Placeholder |
| Cluster/unusual selling? | GOV.INSIDER.cluster_sales, EXEC.INSIDER.cluster_selling | Placeholder/Active |
| CEO/CFO selling? | EXEC.INSIDER.ceo_net_selling, cfo_net_selling | Active |
| **Share pledging?** | **(NEW)** | **GAP (G9, partial)** |

**Check count:** 15 (after consolidation, ~10)

**Q12: Is executive compensation aligned with shareholder interests?**
*Risk framework: RISK CHARACTERISTIC (mitigator/amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| CEO pay and structure? | GOV.PAY.ceo_total, ceo_structure | Placeholder |
| Peer comparison? | GOV.PAY.peer_comparison | Placeholder |
| Shareholder approval? | GOV.PAY.say_on_pay | Active |
| Clawback provisions? | GOV.PAY.clawback | Placeholder |
| Related-party transactions? | GOV.PAY.related_party | Placeholder |
| **Compensation manipulation?** | **(NEW -- spring-loading, backdating, pledging)** | **GAP (G9)** |

**Check count:** 15 existing + 3-4 new = 18-19

**Q13: Do shareholder rights protect or expose investors?**
*Risk framework: RISK CHARACTERISTIC (mitigator/amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Dual-class structure? | GOV.RIGHTS.dual_class, voting_rights | Placeholder |
| Anti-takeover provisions? | GOV.RIGHTS.takeover, classified | Placeholder |
| Proxy access? | GOV.RIGHTS.proxy_access | Placeholder |
| **Dual-class sunset?** | **(NEW)** | **GAP (G18)** |
| **Fee-shifting bylaws?** | **(NEW)** | **GAP (G19)** |

**Check count:** 10 existing + 2 new = 12

**Q14: Is there activist investor pressure?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| 13D filings? | GOV.ACTIVIST.13d_filings | Placeholder |
| Active campaigns? | GOV.ACTIVIST.campaigns, proxy_contests, demands | Placeholder |
| Short activism? | GOV.ACTIVIST.short_activism | Placeholder |

**Check count:** 15

---

#### Report Section: Litigation & Regulatory

**Q4: Does this company have active or recent securities litigation?**
*Risk framework: HAZARD*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Active SCA? | LIT.SCA.active, STOCK.LIT.existing_action | Active |
| SCA details? | LIT.SCA.filing_date, class_period, allegations, lead_plaintiff, case_status | Active |
| Monetary exposure? | LIT.SCA.exposure | Active |
| Settlement history? | LIT.SCA.prior_settle, settle_amount, settle_date | Active |
| Derivative suits? | LIT.SCA.derivative, demand | Active |
| Pre-filing activity? | LIT.SCA.prefiling | Active |

**Check count:** 21

**Q5: What other litigation exists and what regulatory actions are pending?**
*Risk framework: HAZARD*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| SEC enforcement? | LIT.REG.sec_investigation, sec_active, sec_severity | Active |
| DOJ/criminal? | LIT.REG.doj_investigation | Active (misnamed -- fix) |
| Other regulatory? | LIT.REG.* (16 additional placeholders) | Placeholder |
| Other litigation types? | LIT.OTHER.* (14 checks) | Placeholder |
| **Derivative risk category assessment?** | **(NEW -- 5 categories)** | **GAP (G6)** |

**Check count:** 36 existing + 5 new = 41

---

#### Report Section: Market & Stock

**Q15: What does stock price behavior tell us about risk?**
*Risk framework: RISK CHARACTERISTIC (amplifier/trigger)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Significant recent decline? | STOCK.PRICE.recent_drop_alert, position | Active |
| Peer comparison? | STOCK.PRICE.chart_comparison, peer_relative | Active |
| Single-day crashes? | STOCK.PRICE.single_day_events | Active |
| Decline patterns? | STOCK.PATTERN.* (6 checks) | Active |
| Delisting risk? | STOCK.PRICE.delisting_risk | Active |

**Check count:** 16

**Q16: What does short selling and options activity signal?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Short interest level? | STOCK.SHORT.position | Active |
| Trend? | STOCK.SHORT.trend | Placeholder |
| Short seller reports? | STOCK.SHORT.report | Placeholder |

**Check count:** 3

**Q17: What is the ownership structure and how does it affect risk?**
*Risk framework: RISK CHARACTERISTIC (context)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Ownership breakdown? | STOCK.OWN.structure | Active |
| Concentration? | STOCK.OWN.concentration | Placeholder |
| Activist presence? | STOCK.OWN.activist | Placeholder |

**Check count:** 3

**Q18: What do valuation metrics and analyst coverage suggest?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Analyst coverage? | STOCK.ANALYST.coverage, momentum | Active/Placeholder |
| Valuation multiples? | STOCK.VALUATION.* (4 checks) | Placeholder |
| Trading activity? | STOCK.TRADE.* (3 checks) | Placeholder |

**Check count:** 9

---

#### Report Section: Disclosure & NLP

**Q19: What does the company's own disclosure language reveal?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Risk factors changed? | NLP.RISK.* (4 checks) | Active |
| MD&A tone? | NLP.MDA.* (4 checks) | Active |
| Hedging language? | NLP.DISCLOSURE.* (2 checks) | Active |
| Filing timing? | NLP.FILING.* (2 checks) | Active |
| Whistleblower language? | NLP.WHISTLE.* (2 checks) | Active |

**Check count:** 15

**Q23: Is the company's disclosure quality adequate?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Risk factor evolution? | FWRD.DISC.risk_factor_evolution | Placeholder |
| MD&A depth? | FWRD.DISC.mda_depth | Placeholder |
| Non-GAAP reconciliation? | FWRD.DISC.non_gaap_reconciliation | Placeholder |
| Overall quality? | FWRD.DISC.disclosure_quality_composite | Placeholder |

**Check count:** 9

**Q24: Are there narrative inconsistencies or credibility gaps?**
*Risk framework: RISK CHARACTERISTIC (amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| 10-K vs earnings call? | FWRD.NARRATIVE.10k_vs_earnings | Placeholder |
| Investor vs SEC narrative? | FWRD.NARRATIVE.investor_vs_sec | Placeholder |
| Analyst skepticism? | FWRD.NARRATIVE.analyst_skepticism | Placeholder |
| Short thesis? | FWRD.NARRATIVE.short_thesis | Placeholder |

**Check count:** 6

---

#### Report Section: Forward-Looking

**Q20: What are the forward-looking events during the policy period?**
*Risk framework: HAZARD (policy-period triggers)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Earnings calendar? | FWRD.EVENT.earnings_calendar | Active |
| Guidance at risk? | FWRD.EVENT.guidance_risk | Active |
| Catalyst dates? | FWRD.EVENT.catalyst_dates | Active |
| Debt maturities? | FWRD.EVENT.debt_maturity, covenant_test | Active |
| Lock-up expirations? | FWRD.EVENT.lockup_expiry, warrant_expiry | Active |
| Pending M&A? | FWRD.EVENT.ma_closing, synergy | Active |

**Check count:** 21

**Q21: Are there early warning signals from alternative data?**
*Risk framework: RISK CHARACTERISTIC (forward-looking amplifier)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Employee sentiment? | FWRD.WARN.glassdoor_sentiment, indeed_reviews, blind_posts, linkedin_* | Placeholder |
| Customer signals? | FWRD.WARN.g2_reviews, trustpilot_trend, app_ratings, cfpb_complaints | Placeholder |
| Social/news signals? | FWRD.WARN.social_sentiment, journalism_activity | Placeholder |
| Whistleblower signals? | FWRD.WARN.whistleblower_exposure | Placeholder |
| Hiring anomalies? | FWRD.WARN.job_posting_patterns, compliance_hiring, legal_hiring | Placeholder |
| **Scientific community (biotech)?** | **(NEW)** | **GAP (G8)** |

**Check count:** 25 (after moving 7 financial warnings to Q6) + 5-6 new = 30-31

**Q22: What are the macro and industry headwinds?**
*Risk framework: RISK CHARACTERISTIC (context)*

| Sub-question | Key Checks | Current Status |
|---|---|---|
| Sector performance? | FWRD.MACRO.sector_performance, peer_issues | Placeholder |
| Macro factors? | FWRD.MACRO.interest_rate_sensitivity, inflation_impact, fx_exposure | Placeholder |
| Regulatory/political? | FWRD.MACRO.regulatory_changes, legislative_risk, trade_policy | Placeholder |
| Supply chain/climate? | FWRD.MACRO.supply_chain_disruption, climate_transition_risk | Placeholder |

**Check count:** 15

---

### Cross-Reference: Risk Framework View

| Risk Framework Layer | Questions | Check Count (Current) | Check Count (After Gaps Filled) |
|---|---|---|---|
| **Inherent Risk** | Q1, Q2, Q3 | 37 | 42 (+SPAC) |
| **Hazard** | Q4, Q5, Q20, Q25 | 81 | 103 (+SPAC, AI, ESG, derivative categories) |
| **Risk Characteristic** | Q6-Q19, Q21-Q24 | 270 | 285 (+Z-Score, going concern, fraud patterns, employee sentiment, etc.) |
| **Total** | Q1-Q25 | 388 | ~430 |

---

## 10. Readable Documentation

### Design Philosophy (D9)

The brain configuration IS the documentation. An underwriter should understand what's being checked without reading Python. Code must stay synced with the readable brain -- no discrepancies.

This is achieved through generated documentation: SQL views produce structured data that is formatted into human-readable markdown. The documentation is never hand-edited; it is always generated from the brain database.

### Generated Document Types

#### 1. Check Catalog (by Report Section)

What an underwriter sees when they ask "What does the Governance section check?"

```markdown
## Governance & Management

### Board Oversight (Q9)
**Why this matters:** Board quality directly determines derivative suit risk.
Studies show "deep governance" -- culture and character -- outweighs formal
structures (Baker & Griffith, U. Chicago Law Review).

| Check | Question | Criteria | Status |
|---|---|---|---|
| GOV.BOARD.independence | What % of directors are independent? | RED: <50% / YEL: 50-75% / CLR: >75% | SCORING |
| GOV.BOARD.ceo_chair | Is the CEO also the Board Chair? | RED: Combined + <50% independent / YEL: Combined | SCORING |
| GOV.BOARD.tenure | What is average director tenure? | RED: >15yr + no refresh / YEL: >12yr | MONITORING |
| GOV.BOARD.overboarding | Are any directors on 4+ boards? | RED: Any director 4+ boards | SCORING |
| ... | ... | ... | ... |
```

**SQL view that generates this:**

```sql
CREATE VIEW doc_check_catalog AS
SELECT
    c.report_section,
    t.name AS question_text,
    c.check_id,
    c.question,
    c.threshold_red,
    c.threshold_yellow,
    c.threshold_clear,
    c.lifecycle_state,
    c.rationale
FROM brain_checks_active c
LEFT JOIN brain_taxonomy_current t
    ON t.entity_type = 'risk_question'
    AND list_contains(c.risk_questions, t.entity_id)
ORDER BY c.report_section, t.entity_id, c.check_id;
```

#### 2. Risk Question Summary

What an underwriter sees when they ask "How do we answer 'Is this company financially distressed?'"

```markdown
## Q6: Is the Financial Condition Sound?

**Domain:** Financial Condition
**Scoring Factors:** F2 (Financial Condition), F8 (Financial Distress)
**Aggregation:** Worst-of (question is RED if any check is RED)
**Hazards Amplified:** All -- financial distress is the master amplifier

### Why This Question Matters
Financially distressed companies account for ~40% of securities class action
filings despite representing <5% of public companies. Distress creates perverse
incentives for earnings management, disclosure failures, and insider self-dealing.
Moody's EDF-X identifies 82% of eventual bankruptcies at least 3 months in advance.

### Checks Contributing to This Question

| Check | What It Measures | Strength | Status |
|---|---|---|---|
| FIN.LIQ.position | Current ratio liquidity | Strong | SCORING |
| FIN.DEBT.structure | Debt/EBITDA leverage | Very Strong | SCORING |
| FIN.TEMPORAL.cash_flow_deterioration | Cash flow trend | Strong | SCORING |
| FIN.DISTRESS.altman_z (NEW) | Altman Z-Score | Very Strong | MONITORING |
| FIN.DISTRESS.going_concern (NEW) | Auditor going concern | Very Strong | MONITORING |
| ... | ... | ... | ... |

### Data Sources
- **Primary:** SEC XBRL financial data (HIGH confidence)
- **Secondary:** 10-K auditor's report, 10-K MD&A
- **Gaps:** Going concern extraction not yet implemented; Altman Z not computed
```

**SQL view:**

```sql
CREATE VIEW doc_risk_questions AS
SELECT
    t.entity_id AS question_id,
    t.name AS question_text,
    t.description AS question_rationale,
    t.domain,
    t.aggregation_method,
    c.check_id,
    c.name AS check_name,
    c.question AS check_question,
    c.characteristic_strength,
    c.lifecycle_state,
    c.required_data,
    c.acquisition_type
FROM brain_taxonomy_current t
JOIN brain_checks_active c ON list_contains(c.risk_questions, t.entity_id)
WHERE t.entity_type = 'risk_question'
ORDER BY t.entity_id, c.lifecycle_state DESC, c.check_id;
```

#### 3. Hazard Coverage Report

Shows which hazards the brain covers and where gaps exist.

```markdown
## Hazard Coverage Report

| Hazard | Description | Checks (SCORING) | Checks (MONITORING) | Checks (BACKLOG) | Coverage |
|---|---|---|---|---|---|
| HAZ-SCA | Securities Class Actions | 21 | 0 | 0 | COMPREHENSIVE |
| HAZ-DER | Derivative Suits | 2 | 0 | 5 (G6) | WEAK -- only tracks existing, not risk factors |
| HAZ-SEC | SEC Enforcement | 6 | 0 | 3 | MODERATE |
| HAZ-AI | AI-Related Claims | 1 | 0 | 7 (G7) | MINIMAL -- fastest-growing hazard |
| HAZ-SPAC | SPAC/De-SPAC | 0 | 0 | 5 (G1) | NONE -- entire category missing |
| HAZ-ESG | ESG/Greenwashing | 0 | 0 | 4 (G10) | NONE |
| ... | ... | ... | ... | ... | ... |
```

**SQL view:**

```sql
CREATE VIEW doc_hazard_coverage AS
SELECT
    t.entity_id AS hazard_code,
    t.name AS hazard_name,
    t.frequency_trend,
    t.severity_range,
    COUNT(DISTINCT CASE WHEN c.lifecycle_state = 'SCORING' THEN c.check_id END) AS scoring_checks,
    COUNT(DISTINCT CASE WHEN c.lifecycle_state = 'MONITORING' THEN c.check_id END) AS monitoring_checks,
    COUNT(DISTINCT b.backlog_id) AS backlog_items,
    CASE
        WHEN COUNT(DISTINCT CASE WHEN c.lifecycle_state = 'SCORING' THEN c.check_id END) >= 5 THEN 'COMPREHENSIVE'
        WHEN COUNT(DISTINCT CASE WHEN c.lifecycle_state = 'SCORING' THEN c.check_id END) >= 3 THEN 'MODERATE'
        WHEN COUNT(DISTINCT CASE WHEN c.lifecycle_state = 'SCORING' THEN c.check_id END) >= 1 THEN 'WEAK'
        ELSE 'NONE'
    END AS coverage_level
FROM brain_taxonomy_current t
LEFT JOIN brain_checks_active c ON list_contains(c.hazards, t.entity_id)
LEFT JOIN brain_backlog b ON list_contains(b.hazards, t.entity_id) AND b.status = 'OPEN'
WHERE t.entity_type = 'hazard'
GROUP BY t.entity_id, t.name, t.frequency_trend, t.severity_range
ORDER BY scoring_checks ASC, t.entity_id;
```

#### 4. Effectiveness Dashboard

Shows how well the brain's checks are performing.

```markdown
## Check Effectiveness Report
Period: 2026-Q1 | Companies Analyzed: 15 | Confidence: LOW (N < 20)

### Flags Requiring Attention

| Check | Issue | Fire Rate | Skip Rate | Action Needed |
|---|---|---|---|---|
| FIN.ACCT.auditor | Never fires (0%) in 15 runs | 0.0% | 13.3% | Threshold too conservative? |
| GOV.BOARD.diversity | Always fires (100%) in 15 runs | 100% | 0% | Threshold too aggressive? |
| FIN.SECTOR.energy | High skip (80%) | N/A | 80% | Only runs for energy companies -- expected |
| FWRD.WARN.glassdoor_sentiment | High skip (100%) | N/A | 100% | Data not acquired -- needs INVESTIGATION |

### Factor-Level Discrimination Power

| Factor | Avg Fire Rate | Avg Discrimination | Most Predictive Check |
|---|---|---|---|
| F1: Prior Litigation | 8.2% | 0.71 | LIT.SCA.active |
| F2: Financial Condition | 33.1% | 0.84 | FIN.LIQ.cash_burn |
| ... | ... | ... | ... |
```

**SQL view:**

```sql
CREATE VIEW doc_effectiveness AS
SELECT
    e.check_id,
    c.name AS check_name,
    c.lifecycle_state,
    e.total_evaluations,
    e.fire_rate,
    e.skip_rate,
    e.discrimination_power,
    e.flagged_always_fires,
    e.flagged_never_fires,
    e.flagged_high_skip,
    e.flagged_low_discrimination,
    e.run_count,
    e.measurement_period
FROM brain_effectiveness e
JOIN brain_checks_current c ON c.check_id = e.check_id
WHERE e.measurement_period = 'all_time'
ORDER BY
    e.flagged_always_fires DESC,
    e.flagged_never_fires DESC,
    e.flagged_high_skip DESC,
    e.fire_rate ASC;
```

#### 5. Changelog

Shows what changed and why.

```markdown
## Brain Changelog (Last 30 Days)

| Date | Check | Change | Reason |
|---|---|---|---|
| 2026-02-15 | EXEC.PROFILE.board_size | RETIRED | Redundant with GOV.BOARD.size (R1) |
| 2026-02-15 | FIN.DISTRESS.altman_z | CREATED | Gap G3: Altman Z-Score missing |
| 2026-02-14 | FIN.LIQ.position | THRESHOLD_CHANGED | Fire rate analysis: 0% in 20 runs, red threshold unreachable for large-cap |
| 2026-02-14 | BIZ.DEPEND.supplier_conc | MODIFIED | Fixed description mismatch (was "Top 5 Customers", now "Supplier Concentration") |
```

**SQL view:**

```sql
CREATE VIEW doc_changelog AS
SELECT
    cl.changed_at,
    cl.check_id,
    cl.change_type,
    cl.change_description,
    cl.change_reason,
    cl.triggered_by,
    cl.changed_by,
    cl.fields_changed
FROM brain_changelog cl
ORDER BY cl.changed_at DESC;
```

### Documentation Generation Process

```
brain.duckdb (single source of truth)
    │
    ├─── SQL Views (5 views defined above)
    │       │
    │       └─── do-uw brain export-docs
    │               │
    │               ├─── docs/brain/check-catalog.md
    │               ├─── docs/brain/risk-questions.md
    │               ├─── docs/brain/hazard-coverage.md
    │               ├─── docs/brain/effectiveness.md
    │               └─── docs/brain/changelog.md
    │
    └─── checks.json (generated for backward compatibility)
```

**Generation is automated.** Running `do-uw brain export-docs` queries the views and formats the results as markdown. Documentation can never be stale because it is generated from the same database the pipeline reads.

**CI/CD integration:** A pre-commit hook or CI step can verify that generated docs match the database state. If someone edits the brain DB without regenerating docs, the build fails.

---

## Appendix A: Complete Check Count Summary

| Category | Current | After Fixes (Phase B) | After Gaps (Phase C) | Notes |
|---|---|---|---|---|
| Total unique checks | 388 | ~365 (-23 redundancies) | ~405 (+40 new) | Net: +17 |
| With defined criteria | 198 | 198 (unchanged) | 198 (new checks start as MONITORING) | Scoring unchanged until promoted |
| Placeholder | 190 | ~167 (-23 retired) | ~167 (no new placeholders) | Only create checks when data path is clear |
| In SCORING state | 198 | 198 | 198 | No scoring changes in first three phases |
| In MONITORING state | 0 | 0 | ~40 (new gap-fill checks) | Data collected, not scored |
| In INVESTIGATION state | ~100 | ~100 | ~67 (some promoted) | Data source being figured out |
| In BACKLOG state | ~90 | ~67 | ~100 (remaining gaps added) | Prioritized list of future work |
| RETIRED | 0 | ~23 (redundancies) | ~23 | Full history preserved |

## Appendix B: Old System Check Comparison

| Old System Module | Check Count | Current Coverage | Key Gaps |
|---|---|---|---|
| 00 Project Instructions | 36 rules | Covered by pipeline orchestrator | N/A -- workflow, not checks |
| 01 Quick Screen | 40 active + 28 rules | 80% covered | SPAC (QS-3,43), auto-decline layer (QS aggregate), AI/crypto (QS-41,42) |
| 03 Litigation/Regulatory | 37 | 85% covered | Going concern (A.6.1-2), SPAC (A.1.3), SEC comment letters (A.4.4) |
| 04 Financial Health | 112 | 60% covered | Industry KPIs (B.7: 24 checks), covenant analysis (B.2.9-13), guidance deep dive (B.8: 6 checks) |
| 05 Business Model | 74 | 50% covered | Commodity exposure (C.5: 6), operational execution (C.6: 10), growth strategy (C.7: 8) |
| 06 Governance | 78 | 40% covered | Executive assessment depth (D.1: 16), ownership deep dive (D.3: 14), compensation manipulation |
| 07 Market Dynamics | 68 | 35% covered | Short interest/trading depth (E.2: 20), analyst sentiment (E.4: 15), ownership structure (E.3: 15) |
| 08 Alternative Data | 97 | 15% covered | Employee signals (F.1: 15), customer signals (F.2: 12), regulatory databases (F.3: 20), PubPeer/Retraction Watch (F.4: 10) |
| 09 Prior Acts/Prospective | 85 | 40% covered | Stock drop attribution depth (G.1: 19), disclosure gap analysis (G.4: 12), insider deep dive (G.5: 12) |
| 10 Scoring | ~100 rules | Scoring implemented differently | Sector baselines (MODULE 13), contextual scoring (F6-F9) |
| **TOTAL** | **594 + 67 renewal** | **~45% covered** | Major gaps in alternative data, industry KPIs, governance depth |

## Appendix C: Color/Status System

The brain uses a 4-color system extending the Old System's approach:

| Status | Meaning | When Applied |
|---|---|---|
| **RED** | Concerning -- this check has triggered at the highest severity level | Evaluative checks exceeding RED threshold |
| **YELLOW** | Caution -- this check is in an elevated state that warrants attention | Evaluative checks in YELLOW range |
| **CLEAR** | Acceptable -- this check shows no concern at current thresholds | Evaluative checks within CLEAR range |
| **PURPLE** | Unknown -- data is not available to evaluate this check | Check cannot be evaluated because data was not acquired or extracted |
| **INFO** | Context -- this is display data with no risk evaluation | MANAGEMENT_DISPLAY content type |
| **SKIPPED** | Not evaluated -- check was not applicable or preconditions not met | Check execution skipped |

**Critical note on PURPLE:** The Old System explicitly uses PURPLE to prevent false "all clear" signals when data is simply unavailable. Missing data is NOT the same as CLEAR. The brain must distinguish between "we checked and it's fine" (CLEAR) and "we couldn't check" (PURPLE). In the current system, SKIPPED serves this role but should be made more prominent in reporting.

---

**END OF BRAIN DESIGN DOCUMENT**
