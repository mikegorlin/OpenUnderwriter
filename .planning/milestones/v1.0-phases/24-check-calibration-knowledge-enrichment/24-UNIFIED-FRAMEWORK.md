# D&O Underwriting Knowledge Framework: Unified Architecture

**Date:** 2026-02-11
**Status:** USER-APPROVED final architecture — 5-layer analysis model + 3-layer system architecture + 7 research documents + hazard taxonomy
**Purpose:** Define the organizing principles, check architecture, five-layer analysis architecture, three-layer system architecture, and implementation roadmap for the Angry Dolphin Underwriting D&O knowledge system.

---

## 1. Executive Summary

### What This Framework Is

This document defines the unified knowledge architecture for the Angry Dolphin Underwriting D&O worksheet system. It reorganizes 359 existing checks and proposes ~100 new checks around six organizing principles derived from experienced underwriter feedback and seven research documents covering forensic accounting, executive forensics, non-SCA claims, recent settlement patterns, cutting-edge detection signals, NLP-based fraud detection, and game theory of D&O pricing and settlement dynamics.

### The Six Organizing Principles

**1. "Who's Suing" Lens.** Every liability exposure is organized by plaintiff type -- shareholders, regulators, customers, competitors, employees, creditors, and government-as-counterparty. A single check can map to multiple plaintiff lenses. Checks that map to more lenses are inherently more valuable. Checks that map to zero lenses are display-only or deprecation candidates.

**2. Four-Layer Architecture.** Every piece of information belongs to exactly one of four layers:
- **Customary** -- Standard data the underwriter expects. Always present. The reference layer.
- **Objective Risk** -- Quantifiable signals. Facts that exist or don't. Scored by the system.
- **Relative Risk** -- Peer-benchmarked. Direction of risk vs. comparables.
- **Subjective Modifiers** -- Where the underwriter adds judgment. System surfaces the right questions.

**3. Issue-Driven Analysis.** Silence means clean. Noise means investigate. The worksheet should be thin for clean companies and thick for problematic ones. Every forensic model runs silently. Only issues get surfaced. If financials are clean: "No financial integrity concerns identified." If flagged: full forensic breakdown.

**4. Three Check Categories.** Every check is classified:
- **Decision-driving** -- Changes the tier, triggers a red flag, materially affects the decision. Gets scored.
- **Context/display** -- Useful information the underwriter expects but doesn't drive the decision. Appears in customary layer.
- **Redundant/remove** -- Doesn't answer a meaningful question. Gets deprecated.

**5. Context Through Comparison.** No metric is presented in isolation. Every number answers "compared to what?" The system makes everything relative and contextual:
- Market cap is presented with rank among all US public companies AND rank within industry ("$80B = top 75 US public companies, top 10 in semiconductor industry")
- Revenue includes percentile within sector
- Settlement exposure contextualizes DDL with "if sued, this would be in the top X% of cases by DDL"
- Executive compensation shows percentile vs. named peers
- Stock drops include "this magnitude historically leads to X% filing probability"
- Financial ratios show percentile vs. named peers with directional arrows
- Filing frequency shows "companies with this profile have a X% annual SCA filing rate vs. Y% baseline"
The presentation layer must always answer "compared to what?"

**6. Nothing Empty -- Every Check Must Be Real.** The framework contains ZERO placeholder checks. Every active check has:
- A real data source (SEC EDGAR, web search, market data, or user-uploaded)
- A real acquisition path (which API, which filing section, which search query)
- A real computation (formula, threshold, or LLM extraction prompt)
- A real output (what appears in the worksheet when this fires)
Any proposed check that cannot be implemented with current data sources is explicitly moved to the Future/Research category (see Appendix E) and is NOT counted in the active check inventory.

### The Three-Layer System Architecture

The Angry Dolphin Underwriting system operates as three interconnected layers, each reinforcing the others:

**Layer 1: Market Intelligence (always running, company-independent)**
- Pricing database: every quote, binder, tower structure ingested over time
- Market analytics: hardening/softening by segment, capacity trends, rate-on-line benchmarks
- Settlement database: outcomes feeding severity models (Cornerstone regression calibration)
- Claims trends: what is being filed, settling, and emerging by sector and allegation type
- Industry baselines: self-calibrating from accumulated data -- filing rates, settlement percentages, defense costs
- Market cycle position: late soft / early hardening / hard / post-hard transition indicators

**Layer 2: Knowledge Engine (continuously improving)**
- Brain: checks, forensic models, signals, bear case templates, allegation pathway mappings
- Continuous learning: calibration runs comparing predicted vs. actual outcomes, scoring weight adjustments
- Document ingestion: short seller reports, claims studies, broker reports, industry white papers
- NLP improvement: extraction prompts refined from output review and underwriter feedback
- Feedback loop: underwriter corrections and annotations feed back into model calibration

**Layer 3: Company Analysis (per-ticker, on-demand)**
- Uses Layer 2 (Brain) for what to look for -- which checks, which models, which signals matter for this industry/profile
- Uses Layer 1 (Market Intelligence) for context and pricing -- peer benchmarks, settlement ranges, market cycle position
- Feeds results BACK into Layers 1 and 2 -- every analysis enriches the knowledge base
- Company #50 analyzed is better than Company #1 because the system has learned from 49 prior analyses
- Each analysis calibrates settlement prediction, refines industry baselines, and improves extraction quality

### The Five-Layer Analysis Architecture (USER-APPROVED)

While the Three-Layer System Architecture describes HOW the system operates (market intelligence, knowledge engine, company analysis), the Five-Layer Analysis Architecture describes HOW A SINGLE COMPANY ANALYSIS IS STRUCTURED. This was approved by the user as the final organizing framework for the knowledge system revamp.

```
Layer 1: CLASSIFICATION (Objective, Automated)
  ├── 3-4 variables ONLY: market cap tier, industry sector, IPO age, exchange/index
  ├── Produces: base filing rate, severity band, DDL range
  ├── Fully automated from public data — no judgment required
  └── Output: "This is a large-cap biotech, public 2 years, NASDAQ = 8-12% annual filing rate"

Layer 2: HAZARD PROFILE (Subjective Adjustments)
  ├── 7 hazard categories (47 dimensions): Business Model, People, Financial Structure,
  │   Governance, Public Company Maturity, External Environment, Emerging/Modern
  ├── Hazard interaction effects: "Rookie Rocket" (growth + inexperience + IPO = 3-5x),
  │   "Black Box" (complexity + weak earnings + non-GAAP = 2-4x), etc.
  ├── Produces: Adjusted Inherent Exposure Score (IES, 0-100)
  └── Output: "Classification says 8% base rate; hazard profile adjusts to 18% (IES=72)"

Layer 3: ANALYTICAL ENGINE (6 Workflows)
  ├── Stock & Market Analysis: drops, volatility, insider trading, short interest, DDL computation
  ├── Financial Analysis: distress models, forensic accounting, earnings quality, revenue quality
  ├── Litigation & Regulatory Analysis: SCA history, enforcement pipeline, defense assessment
  ├── Executive & Governance Analysis: shadiness score, board forensics, compensation analysis
  ├── NLP & Disclosure Analysis: tone shift, risk factor evolution, readability manipulation
  ├── Frequency & Severity Modeling: filing probability, settlement prediction, defense costs
  └── Each workflow consumes Layers 1-2 context and produces scored signals

Layer 4: PERIL MAPPING (Who Sues, How Bad)
  ├── 7 plaintiff lenses: shareholders, regulators, customers, competitors, employees,
  │   creditors, government-as-counterparty
  ├── Bear case construction: 7 allegation templates instantiated from actual analysis
  ├── Settlement prediction: DDL × case characteristics → expected loss
  └── Output: "Primary exposure: shareholder SCA (65% probability), regulatory (15%),
      estimated settlement range: $35-85M, defense costs: $8-12M"

Layer 5: PRESENTATION (Issue-Driven, Contextual)
  ├── 4-tier display: Customary → Objective → Relative → Subjective
  ├── Context-through-comparison: every metric answers "compared to what?"
  ├── Issue-driven density: thin for clean companies, thick for problematic ones
  ├── Underwriter education: What IS → What COULD BE → What to ASK
  └── Output: worksheet, meeting prep, dashboard — all driven by Layers 1-4
```

**Key design decisions (user-specified):**
- Layer 1 is ONLY 3-4 objective variables — no subjective judgment at the classification stage
- Hazard profile (Layer 2) is where subjective adjustments live — separated from objective classification
- The analytical engine (Layer 3) is NOT a conceptual layer — it's the actual computational workflows
- Stock/market analysis, financial analysis, charts — all live in Layer 3, not buried in other concepts
- Frequency/severity modeling cuts across all layers but its PRIMARY home is Layer 3

**Relationship to existing system:**
- Layer 1 maps to: RESOLVE stage + inherent risk baseline (Section 7.1)
- Layer 2 maps to: NEW hazard profiling engine (does not exist yet)
- Layer 3 maps to: EXTRACT + ANALYZE stages (exists, needs reorganization)
- Layer 4 maps to: SCORE stage + bear case framework (partially exists)
- Layer 5 maps to: RENDER stage + dashboard (exists, needs context-through-comparison)

**Full hazard taxonomy:** See `research/HAZARD_DIMENSIONS_RESEARCH.md` (7 categories, 47 dimensions, interaction effects, IES scoring 0-100)
**Industry validation:** See `research/HAZARD_MODEL_VALIDATION.md` (directionally sound, more structured than published industry practice)

### Underwriter Education Dimension

The system educates the underwriter, not just scores the risk. Three levels of insight:

**Level 1: What IS** -- Current state facts. The company's financials, governance, litigation history, market position. Pure data with context-through-comparison.

**Level 2: What COULD BE** -- Probabilistic scenario analysis. "Companies in this industry with this market cap and governance profile get sued at X% annual rate. Here's a recent case against [named peer]. Your company has similar characteristics because [specific shared traits] / differs because [specific differences]." Industry claims context is critical: "No claims" does NOT equal "no risk." If every peer has been sued, absence of a claim needs explanation, not celebration. The bear case framework (Section 9) provides the structure.

**Level 3: What to ASK** -- Meeting prep questions generated from the ACTUAL analysis, not generic templates. "Ask about the 15% DSO increase in Q3 and whether it reflects a change in collection terms or revenue recognition timing" -- not "ask about revenue recognition practices." Every elevated signal generates a targeted question. Every industry pattern generates a contextual question. The meeting prep section is the direct output of Levels 1 and 2, not a separate template.

### What Changes

The current system is organized by *worksheet section* (BIZ, STOCK, FIN, LIT, GOV, FWRD). This remains as Dimension 1 (display). The redesign adds three parallel dimensions: Dimension 2 (who's suing), Dimension 3 (signal type), and Dimension 4 (check category). The 10-factor scoring model is preserved but enhanced with game theory insights: settlement prediction from DDL and case characteristics, tower positioning intelligence, mispricing signals, and plaintiff attorney economics. Executive forensics is elevated from a governance sub-topic to a primary analytical dimension. Financial forensics shifts from point-in-time snapshots to issue-driven composite scoring with temporal change detection. The F1 (Prior Litigation) weighting is counterbalanced with a "no claims but high risk" assessment that prevents clean history from masking inherent exposure.

---

## 2. The "Who's Suing" Liability Map

### Overview

The D&O underwriter's fundamental question is: "Who might sue this company's directors and officers, for what, and how bad would it be?" The 7 plaintiff types below cover the full spectrum of D&O liability exposure. Each check in the system maps to one or more of these lenses.

### 2.1 Shareholders

**What they sue for:**
- Securities class actions (10b-5 disclosure fraud, Section 11 registration statements)
- Derivative suits (Caremark oversight failure, corporate waste, self-dealing)
- Appraisal actions (Delaware fair value proceedings)
- Proxy fight / proxy fraud claims
- ERISA stock-drop cases (401(k) plan fiduciary breach)
- Books and records demands (Section 220)

**Leading indicators detectable from public data:**
- Stock price decline >20% on company-specific news (necessary condition for SCA)
- Short seller reports (21% of 2024 core SCA filings referenced short reports)
- Beneish M-Score > -1.78 or Dechow F-Score > 1.0 (earnings manipulation signals)
- Insider selling clusters before bad news
- Revenue deceleration + guidance misses (3+ in 8 quarters)
- DSO increasing 3+ quarters (revenue recognition red flag)
- MD&A tone shift -- increasing negative/uncertain language YoY
- Risk factors removed or weakened before risk materializes
- Non-GAAP positive while GAAP negative
- Low say-on-pay vote (<70%), ISS/GL "Against" recommendations

**Confirming signals:**
- SCA filing on Stanford SCAC
- Derivative suit filing in Delaware Chancery
- Section 220 demand received
- Restatement or delayed filing (NT 10-K/10-Q)
- Auditor resignation (not dismissal)
- Wells Notice disclosed in 8-K

**Current check coverage:** ~120 checks (STOCK.*, FIN.*, LIT.SCA.*, partial GOV.*)
**Coverage quality:** STRONG for SCA detection; WEAK for derivative exposure (only ~8 checks); ABSENT for ERISA stock-drop and Section 220 demand risk

**What's missing:**
- Derivative exposure scoring (Caremark "mission critical" compliance assessment)
- Say-on-pay result tracking and trend
- ISS/GL recommendation monitoring
- Board meeting frequency anomalies (>30% YoY increase = firefighting)
- Shareholder proposal / activist campaign tracking
- ERISA stock-drop vulnerability (company stock in 401(k))
- Settlement range estimation based on DDL and case type

**Settlement prediction context (from game theory research):** Securities class actions almost never go to trial. ~50% are dismissed at motion to dismiss (PSLRA heightened pleading standard). Cases surviving MTD settle 85-90% of the time. Settlement amounts are driven primarily by DDL (Disclosure Dollar Loss), with case characteristics as multipliers. The Cornerstone regression model explains >75% of variance. Settlements gravitate toward available insurance limits (Baker & Griffith). Plaintiff attorney economics determine filing viability: expected value = DDL x P(survive MTD) x P(settlement) x settlement% x fee% - litigation costs. Cases with DDL below ~$50M are less attractive to top-tier plaintiff firms. The identity of the plaintiff firm matters: Bernstein Litowitz appointments signal 2.5x higher expected settlement than Robbins Geller because of institutional lead plaintiff concentration (98.5% vs. 78.8%).

**Regulatory intensity modifier:** Not directly applicable. Shareholder claims are universal across industries, but severity scales with market cap (see Section 5).

### 2.2 Regulators

**Who sues:**
- SEC (enforcement actions, Wells Notices, AAERs, cease-and-desist orders, D&O bars)
- DOJ (criminal investigations, FCPA, antitrust, healthcare fraud)
- State AGs (consumer protection, data privacy, environmental, antitrust -- filling federal enforcement voids, especially 2025+)
- FTC (antitrust, consumer protection, deceptive practices -- increasingly naming individual officers)
- CFPB (UDAAP enforcement -- naming "related persons" including officers/directors with managerial responsibility)
- Sector regulators (OCC/FDIC for banks, FDA for pharma, EPA for industrials, FERC for energy, state insurance departments)

**Leading indicators:**
- SEC comment letters (EDGAR CORRESP filings) -- especially accounting-focused, multi-round
- Prior enforcement actions at this company (recidivist pattern: SMCI had 2020 settlement, hit again 2024)
- Industry-wide enforcement sweeps (opioids, PFAS, AI, overdraft fees)
- "Cooperating with government investigation" language in 10-K/10-Q
- Whistleblower disclosures in filings
- Operations in high-corruption-risk countries (TI CPI < 40) for FCPA
- Consumer complaint volume trends (CFPB complaint database is public)
- State AG settlement history in company's industry

**Confirming signals:**
- Wells Notice disclosure
- DOJ subpoena or grand jury subpoena disclosed
- Formal Order of Investigation
- Consent order or settlement announced
- Individual officer/director named in enforcement action
- D&O bar or prohibition order

**Current check coverage:** ~22 checks (LIT.REG.*)
**Coverage quality:** ADEQUATE for SEC; WEAK for DOJ/FCPA, state AG, FTC/CFPB; ABSENT for bank regulatory (OCC/FDIC individual actions)

**What's missing:**
- SEC comment letter analysis (topic, escalation rounds, response readability)
- Prior enforcement history check (recidivist flag across all regulators)
- FCPA geographic risk mapping (country operations vs. TI CPI scores)
- State AG enforcement trend monitoring by industry
- CFPB consumer complaint volume tracking
- DOJ investigation disclosure language detection
- Bank regulatory enforcement action monitoring (OCC/FDIC)
- Regulatory intensity score by industry (see Section 2.8)

**Regulatory intensity modifier:**

| Industry | Regulator Count | Primary Regulators | Intensity Level |
|----------|----------------|-------------------|----------------|
| Banking/Financial Services | 5-6 | OCC, FDIC, Fed, SEC, state banking, CFPB | VERY HIGH |
| Healthcare/Pharma | 4-5 | FDA, CMS, OIG, DOJ, state AG | VERY HIGH |
| Energy/Utilities | 3-4 | FERC, EPA, NRC, state PUC | HIGH |
| Insurance | 3-4 | State insurance, SEC, NAIC, DOJ | HIGH |
| Telecom | 3 | FCC, FTC, state AG | MODERATE-HIGH |
| Defense/Aerospace | 3 | DOD, DCAA, CFIUS | MODERATE-HIGH |
| Technology (ad-tech/social) | 2-3 | FTC, state AG, EU regulators | MODERATE |
| Manufacturing | 2 | EPA, OSHA | MODERATE |
| Retail/Consumer | 1-2 | FTC, state AG | MODERATE-LOW |
| SaaS/Enterprise Software | 1 | SEC (public company rules only) | LOW |

### 2.3 Customers

**What they sue for:**
- Product liability (defective products causing harm)
- Consumer protection violations (deceptive practices, dark patterns, subscription traps)
- Data breach / privacy violations (CCPA, state privacy laws, GDPR)
- Contract disputes (breach of warranty, failure to deliver)
- False advertising / misleading claims (including "AI-washing")
- Medicare/Medicaid fraud (False Claims Act -- healthcare)

**Leading indicators:**
- Product recall history (FDA, CPSC databases)
- Customer complaint trends (CFPB, BBB, industry-specific databases)
- Data breach history (prior incidents)
- Inadequate Item 1C cybersecurity governance disclosure
- Privacy policy deficiencies vs. operations (data-intensive business with weak privacy governance)
- AI capability claims vs. actual AI-derived revenue ("AI-washing" gap)
- Subscription/cancellation practice design (dark patterns flagged by FTC)

**Confirming signals:**
- Product recall announcement
- Data breach disclosure (8-K)
- FTC or state AG consumer protection action
- Class action filing for consumer harm
- False Claims Act qui tam action

**Current check coverage:** ~3 checks (BIZ.UNI.cyber_posture, cyber_business)
**Coverage quality:** WEAK

**What's missing:**
- Cybersecurity governance quality score (board committee, Item 1C disclosure quality, breach history)
- Data privacy regulatory exposure score (number of applicable state privacy laws)
- AI-washing indicator (AI claims vs. AI-derived revenue)
- Product recall / safety history
- Customer complaint trend monitoring
- False Claims Act exposure for healthcare companies

### 2.4 Competitors

**What they sue for:**
- Antitrust violations (price-fixing, market allocation, monopoly maintenance)
- Trade secret misappropriation
- Patent infringement
- Unfair competition / tortious interference
- Employee non-compete / non-solicitation violations

**Leading indicators:**
- Market share exceeding 40% in any product/geographic market
- Industry under active antitrust investigation (DOJ Second Request)
- Non-compete or no-hire agreements with competitors (potential antitrust violation under 2025 DOJ/FTC Guidelines)
- Trade secret litigation disclosed in 10-K Item 3
- Senior executive departures to direct competitors
- Patent portfolio size and quality vs. R&D narrative

**Confirming signals:**
- DOJ/FTC antitrust investigation announced
- Competitor antitrust lawsuit filed
- Trade secret injunction sought
- Patent litigation verdict or injunction

**Current check coverage:** ~2 checks (BIZ.COMP.consolidation, competitive_position)
**Coverage quality:** WEAK

**What's missing:**
- Market share dominance / concentration risk indicator
- Industry antitrust investigation monitoring
- Non-compete/non-solicitation agreement exposure
- Trade secret litigation history tracking
- Patent filing pattern analysis (R&D claims vs. actual patent output)

### 2.5 Employees

**What they sue for:**
- Whistleblower retaliation (Dodd-Frank, SOX -- contributing factor vs. but-for causation)
- Employment discrimination class actions (Title VII, ADA, ADEA)
- ERISA fiduciary breach (stock-drop cases under Dudenhoeffer)
- Wage and hour class actions
- Workplace harassment / hostile environment (derivative exposure via Caremark)
- Non-compete enforcement actions (antitrust angle)

**Leading indicators:**
- Whistleblower disclosure language in 10-K Items 1A, 3
- Internal investigation disclosures
- Sudden executive departures ("personal reasons" -- potential constructive discharge or unreported harassment)
- EEOC complaints or charges
- Employee satisfaction declining (Glassdoor business outlook rating)
- Industry known for culture risk (entertainment, tech, finance, media)
- Retaliation as most frequently cited EEOC issue (~50% of all 2024 filings)
- CEO/executive departure for undisclosed reasons during period of compliance issues

**Confirming signals:**
- SEC whistleblower award announcement
- EEOC investigation or consent decree
- Employment discrimination class action filed
- Whistleblower retaliation lawsuit filed
- State civil rights commission action

**Current check coverage:** ~2 checks (partial whistleblower language detection)
**Coverage quality:** ABSENT for most categories

**What's missing:**
- Whistleblower disclosure language detection in filings
- Internal investigation disclosure tracking
- Sudden executive departure pattern detection (8-K Item 5.02)
- ERISA stock-drop vulnerability assessment (company stock in 401(k))
- Employee sentiment tracking (Glassdoor/Indeed, where available)
- Workplace culture risk assessment

### 2.6 Creditors

**What they sue for:**
- Deepening insolvency (continued operations beyond the point of insolvency increasing losses)
- Fraudulent transfer / preferential payment clawbacks (insider bonuses/severance within 1 year of filing)
- Zone of insolvency duty-shifting (fiduciary duties expand to include creditor interests)
- Breach of fiduciary duty in bankruptcy
- Chapter 7 trustee suits against former D&Os (can persist years after filing)

**Leading indicators:**
- Altman Z-Score entering distress zone (<1.81)
- Going concern opinion or substantial doubt language
- Covenant breaches or waiver negotiations
- Cash runway <12 months based on current burn rate
- Credit rating downgrade to CCC or below
- Debt-funded acquisitions or expansion while operating cash flow declining
- Dividends or share buybacks during period of cash flow decline
- Insider compensation payments (bonuses, severance) during financial distress
- New borrowing at significantly above-market rates

**Confirming signals:**
- Missed interest or principal payment
- Delisting warning
- Chapter 11 or Chapter 7 filing
- Auditor change during financial distress

**Current check coverage:** ~10 checks (FIN.LIQ.*, FIN.DEBT.*, DEATH_SPIRAL pattern)
**Coverage quality:** GOOD for financial distress detection; WEAK for specific D&O claim triggers in insolvency

**What's missing:**
- Altman Z-Score computation with zone classification (current system may use basic version)
- Zone of insolvency creditor duty assessment
- Insider payment tracking during distress periods (bonuses, severance clawback risk)
- Dividend/buyback-during-distress detection
- Above-market-rate borrowing detection
- Side A adequacy assessment (qualitative flag for underwriter)

**Post-Purdue Pharma impact:** Directors can no longer rely on bankruptcy plan releases to shield them from personal liability. This makes Zone of Insolvency signals more important than ever.

### 2.7 Government (as Counterparty)

**What they sue for:**
- False Claims Act / qui tam (healthcare Medicare/Medicaid fraud, defense procurement fraud)
- Procurement fraud (inflated costs, defective products, kickbacks)
- ITAR/EAR export control violations
- Government contract compliance failures
- CFIUS-related national security concerns
- Sanctions evasion (OFAC violations)

**Leading indicators:**
- Government revenue as percentage of total (high = higher exposure)
- Debarment/exclusion check on SAM.gov
- Prior government contract modifications, cancellations, or disputes
- Operations in defense, healthcare, or government IT sectors
- Export-controlled products or technology
- Geographic exposure to sanctioned countries
- Lobbying spend trajectory (sudden increases may signal defensive positioning)

**Confirming signals:**
- False Claims Act qui tam action filed or disclosed
- SAM.gov debarment or exclusion listing
- Government contract termination for cause
- CFIUS review initiated
- OFAC sanction enforcement action

**Current check coverage:** ~0 dedicated checks
**Coverage quality:** ABSENT

**What's missing:**
- Government revenue concentration assessment
- SAM.gov debarment/exclusion check
- Government contract trend monitoring (FPDS.gov)
- FCPA/export control geographic risk assessment
- False Claims Act exposure scoring for healthcare/defense companies
- Lobbying spend change detection (OpenSecrets.org)

### 2.8 Regulatory Intensity Dimension

The user identified that regulatory intensity is a multiplier on D&O exposure. A bank CEO operates under 5-6 regulators who can personally bar them from the industry. A SaaS CEO operates under basically one (SEC, as a public company). This dimension modifies the interpretation of all other signals.

**Regulatory Intensity Score (1-10):**

| Score | Level | Example Industries | Impact |
|-------|-------|-------------------|--------|
| 9-10 | Maximum | Banking, Nuclear Energy | Multiple regulators with individual liability powers; personal bar/prohibition possible |
| 7-8 | Very High | Healthcare/Pharma, Insurance, Defense | Sector regulators + federal + state; significant individual exposure |
| 5-6 | High | Energy/Utilities, Telecom, Financial Services (non-bank) | Multiple regulatory bodies; moderate individual exposure |
| 3-4 | Moderate | Technology (consumer-facing), Manufacturing, Retail | FTC + state AG; limited sector-specific regulation |
| 1-2 | Low | SaaS/Enterprise B2B, Professional Services | Primarily SEC as public company; minimal sector regulation |

**How it modifies checks:**
- Regulatory intensity multiplies the weight of governance checks (higher intensity = board oversight more critical)
- High-intensity industries trigger additional "mission critical" compliance checks (Caremark exposure)
- Regulatory intensity feeds into the inherent risk model (Section 5)

---

## 3. The Four-Layer Architecture

### 3.1 Layer 1: Customary

**What belongs here:** Standard data the underwriter expects to see on every worksheet. Always present regardless of risk level. This is the reference layer -- it provides context but does not drive the decision.

**How it's presented:** Always displayed. Forms the backbone of the worksheet. Clean, organized sections matching standard D&O underwriting practice.

**Examples (with context-through-comparison):**
- Company name, ticker, CIK, SIC/NAICS codes, state of incorporation
- Business description and primary products/services
- Market cap: "$80B -- ranks #72 among US public companies, #8 in semiconductor industry" (not just "$80B")
- Revenue: "$15.2B -- 85th percentile in semiconductor sector" (not just "$15.2B")
- Employee count: "28,000 -- median for this industry/size tier is 22,000"
- Geographic footprint with jurisdiction count and FCPA-risk country exposure
- Stock price chart (12-month), 52-week high/low, with peer index overlay
- Board of directors list with bios, committee memberships, tenure
- Named executive officers with titles and compensation summary: "CEO total comp $24M -- 78th percentile vs. named peers [PEER1, PEER2, PEER3]"
- Prior SCA history (listed, not scored) -- but if NO prior claims and peers HAVE claims, flag with context: "No prior SCA filings. Note: 4 of 6 identified peers have been subject to SCA in the past 5 years."
- D&O risk classification (growth darling, regulatory sensitive, etc.)
- Industry sector and primary competitors
- SCA filing rate context: "Companies with this profile (large-cap tech, public 8 years, no prior SCA) have a ~6-9% annual filing rate"

**Current check mapping (~85 checks):**
All BIZ.CLASS.*, BIZ.SIZE.* (12), most BIZ.MODEL.* (11), most BIZ.COMP.* (12), GOV.BOARD.* (13 -- basic board composition facts), GOV.EXEC.* (11 -- executive list), GOV.PAY.* (15 -- compensation display), STOCK.PRICE.position, STOCK.OWN.* (3)

**Key principle:** These checks populate the worksheet but do NOT feed into scoring. They are *parameters*, not *findings*.

### 3.2 Layer 2: Objective Risk

**What belongs here:** Quantifiable signals. Facts that exist or don't. Results of forensic models, litigation records, regulatory actions, insider trading patterns. Scored by the system.

**How it's presented:** Issue-driven. Run all models silently. If everything is clean: "No [category] concerns identified." If flagged: full breakdown with source, confidence, and significance.

**Examples:**
- Beneish M-Score = -1.42 (LIKELY MANIPULATOR zone) -- detail the 8 component variables and which ones are driving the score
- Prior SEC enforcement action at this company (2020 settlement) -- recidivist flag
- Insider selling: CFO sold $2.3M in shares 45 days before earnings miss -- scienter indicator
- DSO increased 13.3% YoY without business explanation -- revenue quality concern
- Short interest at 3.2x sector average, with Hindenburg report published Aug 2024
- Auditor resigned (not dismissed) in October 2024 -- critical governance event
- Going concern opinion issued by auditor -- financial distress confirmed
- Material weakness in internal controls over financial reporting

**Current check mapping (~180 checks):**
STOCK.SHORT.* (3), STOCK.INSIDER.* (3), STOCK.PATTERN.* (6), STOCK.TRADE.* (3), FIN.ACCT.* (6), FIN.DEBT.* (5), FIN.LIQ.* (5), FIN.PROFIT.* (5), FIN.GUIDE.* (5), LIT.SCA.* (20), LIT.REG.* (22), LIT.OTHER.* (14), GOV.INSIDER.* (8), FWRD.WARN.* (32), FWRD.EVENT.* (21)

**Key principle:** These checks feed into scoring. Each has a clear question it answers and maps to at least one "who's suing" lens.

### 3.3 Layer 3: Relative Risk

**What belongs here:** Peer-benchmarked data. "This company vs. its peers." Direction of risk. Answers the underwriter's question: "Is this normal for this type of company, or is this an outlier?"

**How it's presented:** Comparison tables and directional indicators. Show where the company falls relative to named peers on key dimensions.

**Examples (context-through-comparison in action):**
- Stock performance: -23% vs. peer median -5% (12M) -- "significant underperformance; a drop of this magnitude historically leads to 18% filing probability within 12 months"
- Valuation: P/E 45x vs. peer median 28x -- "premium of 1.6x; if this multiple compresses to peer median, estimated DDL = $12B"
- Short interest: 8.2% of float vs. peer median 3.1% -- "elevated; 21% of 2024 core SCA filings referenced short reports"
- Leverage: Debt/EBITDA 4.2x vs. peer median 2.8x -- "above peer group; 92nd percentile"
- Insider selling rate: 2.1% of holdings vs. peer median 0.8% -- "elevated; top decile for this sector"
- Revenue growth: 19% vs. peer median 12% -- "above peer, but DSO rising faster than any peer -- channel stuffing signal"
- Governance quality: Board independence 62% vs. peer median 78% -- "25th percentile; below ISS recommended threshold"
- Settlement exposure: "If sued, estimated DDL of $4.2B would place this in the top 5% of cases by DDL; estimated settlement range $35-85M based on case characteristics"
- Market cap cost ratio: "D&O premium per $M of market cap = $18 vs. peer median $25 -- potentially underpriced relative to exposure"

**Current check mapping (~35 checks):**
STOCK.VALUATION.* (4), FIN.SECTOR.* (6), GOV.SECTOR.* (9), BIZ.DEPEND.* (10 -- partial), FWRD.MACRO.* (15 -- partial)

**Coverage quality:** MODERATE. System has sector baselines but does not systematically benchmark against named peers. The underwriter's first question for any tech company is "how does this compare to its closest 5 peers?"

**What's missing:**
- Named peer identification algorithm (SIC + market cap + business similarity)
- Structured peer comparison on 10 dimensions
- Peer Relative Risk Score (is this company an outlier within its peer group?)

### 3.4 Layer 4: Subjective Modifiers

**What belongs here:** Where the underwriter adds judgment. The system surfaces the right questions, not the answers. The underwriter decides what the signals mean in combination.

**How it's presented:** Targeted questions specific to the company's risk profile. Not generic industry questions -- specific to what the system found.

**Examples:**
- "If this company's stock dropped 40% tomorrow, what would be the cause?" (bear case prompt)
- "The CFO sold $2.3M before the earnings miss and DSO is rising 13.3%. Is this pattern consistent with channel stuffing?" (forensic synthesis)
- "This company has 3 independent short seller reports. What are they seeing that the market isn't?" (short seller convergence)
- "CEO compensation is 2.8x the peer median. Is the board captured?" (governance judgment)
- "The company operates in 4 high-corruption-risk countries with third-party sales agents. FCPA compliance?" (regulatory judgment)
- "Management's MD&A tone shifted significantly negative YoY. What changed?" (disclosure quality)

**Current check mapping (~25 checks):**
FWRD.NARRATIVE.* (10), FWRD.DISC.* (10), GOV.EFFECT.* (10 -- partial)

**Coverage quality:** WEAK. The playbook meeting_questions partially address this but are generic by industry rather than specific to the company's risk profile.

**What needs to change:**
- Questions MUST be generated dynamically from the ACTUAL analysis, not from generic industry templates
- The bear case framework (Section 9) provides the structure for scenario-based questions
- Every elevated objective risk signal generates a corresponding subjective question: "The DSO increased 15% in Q3 while revenue grew only 4%. Is this a change in payment terms, a shift in customer mix, or a recognition timing issue?"
- Industry claims context generates comparative questions: "Four of your six identified peers have faced SCA filings in the past 5 years. What distinguishes this company's disclosure practices?"
- Game theory context generates pricing questions: "This company's D&O premium per $M of market cap is 30% below peer median. Is the broker leveraging competitive quotes, or does the underwriter have information the market doesn't?"
- The meeting prep section is the DIRECT OUTPUT of the analysis, not a separate template library
- Level 3 (What to ASK) is the most valuable part of the worksheet for an experienced underwriter

### 3.5 Check-to-Layer Mapping Summary

| Layer | Check Count (Current) | Estimated After Redesign | Purpose |
|-------|----------------------|--------------------------|---------|
| Customary | ~85 | ~95 (with context-through-comparison enrichment) | Always displayed with comparative context, not scored |
| Objective Risk | ~180 | ~260 (includes forensic models, settlement prediction, mispricing) | Scored, decision-driving |
| Relative Risk | ~35 | ~65 (includes peer benchmarks, market intelligence) | Peer-benchmarked, directional, "compared to what?" |
| Subjective Modifiers | ~25 | ~45 (company-specific question generators, Level 3 education) | Underwriter judgment prompts from actual analysis |
| Deprecated | ~34 | 0 (removed) | No longer in system |
| Future/Research | 0 | ~11 (see Appendix E) | Tracked, not active; promoted when data source available |
| **Total Active** | **359** | **~453** | |

---

## 4. Check Classification Framework

### 4.1 Decision-Driving Checks

These checks change the tier, trigger red flags, or materially affect the underwriting decision. They are scored. Each maps to at least one "who's suing" lens.

**Multi-Lens Mapping Principle:** Checks that connect to multiple plaintiff lenses are inherently more valuable. A check that connects to 4 lenses is more important than one that connects to 1.

**Example multi-lens checks:**

| Check | Lenses | Why Multi-Lens |
|-------|--------|----------------|
| Insider selling cluster before bad news | Shareholders (scienter in SCA), Regulators (SEC insider trading), Creditors (preferential transfer if distressed) | 3 lenses -- insider trading is the nexus of multiple claim types |
| Auditor resignation | Shareholders (SCA trigger), Regulators (SEC attention), Creditors (distress signal) | 3 lenses -- auditor resignation affects every stakeholder |
| Material weakness in ICFR | Shareholders (10b-5), Regulators (SOX enforcement), Employees (ERISA stock-drop if stock falls) | 3 lenses |
| Restatement | Shareholders (SCA), Regulators (AAER), Creditors (covenant breach), Employees (ERISA) | 4 lenses -- the most multi-dimensional signal |
| Whistleblower disclosure | Shareholders (derivative Caremark), Regulators (SEC investigation trigger), Employees (retaliation claim) | 3 lenses |
| FCPA geographic risk | Shareholders (stock drop on investigation), Regulators (DOJ/SEC), Government (debarment) | 3 lenses |
| Cybersecurity breach | Shareholders (SCA, derivative Caremark), Regulators (SEC disclosure rules), Customers (privacy class action) | 3 lenses |
| Beneish M-Score > -1.78 | Shareholders (SCA), Regulators (SEC AAER) | 2 lenses -- direct fraud indicator |
| Going concern opinion | Shareholders (stock drop), Creditors (zone of insolvency), Employees (ERISA) | 3 lenses |

**Current decision-driving checks by factor:**

| Factor | Current Weight | Check Count | Key Checks |
|--------|---------------|-------------|------------|
| F1 Prior Litigation | 20 pts (see F1 weighting note below) | ~20 | LIT.SCA.*, LIT.OTHER.*, + "no claims but high risk" counterbalance |
| F2 Stock Decline | 15 pts | ~10 | STOCK.PRICE.*, STOCK.PATTERN.* |
| F3 Restatement/Audit | 12 pts | ~6 | FIN.ACCT.*, restatement, material weakness |
| F4 IPO/SPAC/M&A | 10 pts | ~5 | BIZ.CLASS.ipo_age, spac_origin |
| F5 Guidance Misses | 10 pts | ~5 | FIN.GUIDE.* |
| F6 Short Interest | 8 pts | ~3 | STOCK.SHORT.* |
| F7 Volatility | 9 pts | ~6 | STOCK.PATTERN.*, STOCK.TRADE.* |
| F8 Financial Distress | 8 pts | ~10 | FIN.LIQ.*, FIN.DEBT.* |
| F9 Governance | 6 pts | ~15 | GOV.BOARD.*, GOV.RIGHTS.*, GOV.EFFECT.* |
| F10 Officer Stability | 2 pts | ~5 | GOV.EXEC.* |

**F1 Weighting Note -- Prior Claims Overvaluation Risk:**

F1 (Prior Litigation, 20 points) is the highest-weighted factor. While prior litigation is a legitimate predictor (4.2x lift for companies with prior SCA history), this weighting risks overvaluing claims history at the expense of inherent risk. A company with no prior claims but strong risk indicators (high-volatility tech with aggressive revenue recognition, recent IPO, concentrated insider ownership, declining financial integrity) may be MORE dangerous than a mature company that settled a modest SCA five years ago.

The system counterbalances F1 with a mandatory "No Claims But High Risk" assessment:
- If F1 scores LOW (no or minimal prior claims), the system explicitly checks whether the company's inherent risk profile (market cap tier, industry filing rate, governance quality, financial integrity, executive forensics) suggests claims SHOULD be expected
- If the inherent risk model (Section 5) produces an effective filing rate above 10% but F1 is near zero, the worksheet flags: "No prior litigation history. However, companies with this profile ([specific characteristics]) experience SCA filings at [X]% annual rate. [Y] of [Z] identified peers have been subject to SCA in the past 5 years."
- The bear case framework (Section 9) explicitly addresses the "no claims but high risk" scenario with bear case templates that construct the plaintiff's case from current signals
- Industry claims context: if the company operates in a sector where peer litigation is common, absence of claims needs explanation, not celebration

This ensures that a clean litigation history provides appropriate credit (lower F1 score) without creating a false sense of security when other indicators are elevated.

### 4.2 Context/Display Checks

These checks provide useful information the underwriter expects but do not drive the scoring decision. They populate the customary layer.

**Characteristics:**
- Answer: "What does this company look like?" not "What could go wrong?"
- Always present regardless of risk level
- Provide the baseline parameters for interpreting objective risk signals

**Examples of context/display checks (all with context-through-comparison):**
- BIZ.SIZE.market_cap -- market cap tier + rank among US public companies + rank within industry (not just "$80B" but "$80B, rank #72 US, #8 in sector")
- BIZ.SIZE.revenue -- revenue level + percentile within sector ("$15.2B, 85th percentile in semiconductor sector")
- BIZ.SIZE.employee_count -- employee count + comparison to sector median ("28,000, median for tier is 22,000")
- BIZ.MODEL.revenue_type -- revenue model classification (context for revenue quality interpretation)
- BIZ.COMP.peer_group -- identified peer companies (context for relative risk, foundation for all "compared to what?" analysis)
- GOV.BOARD.independence_pct -- board independence percentage + percentile vs. peers (context unless extreme outlier, e.g., "62%, 25th percentile vs. peers" becomes decision-driving)
- GOV.BOARD.board_size -- number of directors + comparison to peer median
- GOV.PAY.ceo_total_comp -- CEO total compensation + percentile vs. named peers ("$24M, 78th percentile vs. [PEER1, PEER2, PEER3]"; context unless extreme outlier >2.5x peer median, then decision-driving)
- STOCK.PRICE.current -- current stock price + implied DDL exposure at various drop scenarios
- STOCK.OWN.institutional_pct -- institutional ownership % + context ("higher institutional = more likely institutional lead plaintiff = 2.5x median settlement if sued")

**Key distinction from decision-driving:** These checks become decision-driving ONLY when they are extreme outliers. Board independence of 78% is context. Board independence of 33% is a decision-driving signal (derivative suit risk). The threshold at which a context check becomes decision-driving is defined in the check configuration.

### 4.3 Proposed Deprecation Candidates

These checks do not answer a meaningful underwriting question or are redundant with other checks. After careful analysis of *why each exists* (the 359 checks are a distillation of extensive research), the following categories are candidates for deprecation or consolidation:

**Deprecation rationale categories:**

| Category | Example Checks | Count | Reason |
|----------|---------------|-------|--------|
| Duplicate with different granularity | Multiple BIZ.DEPEND.* checks that measure the same concentration risk at different thresholds | ~8 | Consolidate into single check with graduated thresholds |
| COVID-specific | Any checks specifically targeting COVID-era claims patterns | ~3 | COVID filings effectively dead (3 in 2025, none after July) |
| Pure cosmetic display | Checks that only compute a label with no threshold or action | ~5 | Convert to display fields, not checks |
| Overlapping patterns | Pattern triggers that duplicate check logic | ~8 | Consolidate into the pattern system |
| Never-implementable signals | Checks requiring data that cannot be acquired (private arbitration results, sealed records) | ~5 | Remove or convert to manual underwriter prompts |
| ESG overweight (per user) | ESG/climate-specific checks beyond a reasonable minimum | ~5 | Downgrade from scored to context/display |

**Estimated deprecation count:** ~34 checks (from 359 to ~325 before new checks are added)

**IMPORTANT:** Before deprecating any check, ask: "What question was this check trying to answer?" If the question is still relevant, the check should be restructured, not removed.

### 4.4 New Checks to Build

Consolidated from all 6 research documents, deduplicated, and organized by the "who's suing" lens.

**Executive Forensics (NEW DIMENSION -- ~20 checks)**

| Check ID | Name | Source Doc | Lenses | Category | Priority |
|----------|------|-----------|--------|----------|----------|
| EXEC.LIT.sec_enforcement_personal | Individual SEC enforcement action history | Executive Forensics | Shareholders, Regulators | Decision-driving | P1 |
| EXEC.LIT.prior_sca_defendant | Named defendant in prior SCA at any company | Executive Forensics | Shareholders | Decision-driving | P1 |
| EXEC.LIT.prior_company_failures | Served at company that went bankrupt/restated | Executive Forensics | Shareholders, Creditors | Decision-driving | P1 |
| EXEC.LIT.finra_disclosures | FINRA BrokerCheck disclosure history | Executive Forensics | Regulators | Decision-driving | P2 |
| EXEC.LIT.court_record_search | Federal court case involvement (CourtListener/PACER) | Executive Forensics | Shareholders, Regulators | Decision-driving | P2 |
| EXEC.LIT.negative_news | Negative press coverage (fraud, investigation, lawsuit) | Executive Forensics | All | Decision-driving | P1 |
| EXEC.TRADE.suspicious_timing | Insider sales timed before bad news (pre-announcement) | Executive Forensics, Cutting Edge | Shareholders, Regulators | Decision-driving | P1 |
| EXEC.TRADE.10b5_1_modifications | 10b5-1 plan modifications within 6 months of bad news | Executive Forensics | Shareholders, Regulators | Decision-driving | P2 |
| EXEC.BOARD.overboarding | Directors exceeding ISS overboarding thresholds | Executive Forensics | Shareholders (derivative) | Decision-driving | P2 |
| EXEC.BOARD.interlocks | Board members sharing another company's board | Executive Forensics, Cutting Edge | Shareholders (derivative) | Context/display | P3 |
| EXEC.BOARD.interlock_fraud_contagion | Interlock with company that had fraud/enforcement | Cutting Edge | Shareholders, Regulators | Decision-driving | P3 |
| EXEC.BOARD.tenure_stale | Average director tenure >10 years, no refreshment | Executive Forensics | Shareholders (derivative) | Context/display | P3 |
| EXEC.PAY.ceo_vs_peer_extreme | CEO compensation >2.5x peer median | Executive Forensics | Shareholders (derivative, waste) | Decision-driving | P2 |
| EXEC.PAY.golden_parachute | Golden parachute >3x base salary | Executive Forensics | Shareholders (derivative) | Context/display | P3 |
| EXEC.REL.related_party_volume | Dollar volume of related party transactions | Non-SCA Claims | Shareholders (derivative, self-dealing) | Decision-driving | P2 |
| EXEC.REL.related_party_trend | Year-over-year change in related party transactions | Non-SCA Claims | Shareholders (derivative) | Decision-driving | P2 |
| EXEC.REL.related_party_types | Types of related party transactions (family, director entities) | Non-SCA Claims | Shareholders (derivative) | Context/display | P2 |
| EXEC.SCORE.individual_risk | Individual Executive Risk Score (0-100) per person | Executive Forensics | All | Decision-driving | P1 |
| EXEC.SCORE.board_aggregate | Board/Management Aggregate Risk Score | Executive Forensics | All | Decision-driving | P1 |
| EXEC.STABILITY.cfo_departure_stress | CFO/CAO departure during financial stress period | Cutting Edge | Shareholders, Regulators | Decision-driving | P1 |

**Financial Forensics (NEW + ENHANCED -- ~25 checks)**

| Check ID | Name | Source Doc | Lenses | Category | Priority |
|----------|------|-----------|--------|----------|----------|
| FIN.FORENSIC.beneish_m_score | Beneish M-Score (8-variable, already implemented) | Forensic Accounting | Shareholders, Regulators | Decision-driving | DONE |
| FIN.FORENSIC.dechow_f_score | Dechow F-Score (trained on SEC AAERs) | Forensic Accounting | Shareholders, Regulators | Decision-driving | P1 |
| FIN.FORENSIC.montier_c_score | Montier C-Score (6 binary cooking-the-books signals) | Forensic Accounting | Shareholders, Regulators | Decision-driving | P1 |
| FIN.FORENSIC.sloan_enhanced | Enhanced Sloan Accrual Ratio (graduated zones) | Forensic Accounting | Shareholders | Decision-driving | P1 |
| FIN.FORENSIC.integrity_score | Financial Integrity Score (composite 0-100) | Forensic Accounting | Shareholders, Regulators, Creditors | Decision-driving | P2 |
| FIN.FORENSIC.benford_analysis | Benford's Law digit distribution analysis | Forensic Accounting, Cutting Edge | Regulators | Decision-driving | P3 |
| FIN.QUALITY.revenue_quality_score | Revenue Quality Score (DSO trend, AR divergence, Q4 concentration) | Forensic Accounting | Shareholders, Regulators | Decision-driving | P2 |
| FIN.QUALITY.cash_flow_quality_score | Cash Flow Quality Score (QoE, CCE, AI, CFA, multi-period) | Forensic Accounting | Shareholders, Creditors | Decision-driving | P2 |
| FIN.QUALITY.audit_risk_score | Audit Risk Score (MW, auditor changes, CAMs, restatements) | Forensic Accounting | Shareholders, Regulators | Decision-driving | P2 |
| FIN.QUALITY.nongaap_divergence | Non-GAAP/GAAP divergence magnitude and trend | Knowledge Audit | Shareholders | Decision-driving | P1 |
| FIN.QUALITY.nongaap_positive_gaap_negative | Non-GAAP positive while GAAP negative | Knowledge Audit | Shareholders, Regulators | Decision-driving | P1 |
| FIN.TEMPORAL.revenue_deceleration | Revenue growth deceleration 3+ consecutive periods | Knowledge Audit | Shareholders | Decision-driving | P1 |
| FIN.TEMPORAL.margin_compression | Gross/operating margin decline 3+ quarters | Knowledge Audit | Shareholders | Decision-driving | P1 |
| FIN.TEMPORAL.dso_trajectory | DSO increasing 3+ quarters | Knowledge Audit, Forensic Accounting | Shareholders, Regulators | Decision-driving | P1 |
| FIN.TEMPORAL.cashflow_earnings_divergence | CFO/NI divergence widening over 3+ periods | Knowledge Audit | Shareholders | Decision-driving | P1 |
| FIN.TEMPORAL.working_capital_deterioration | Working capital deterioration 3+ quarters | Knowledge Audit | Creditors | Decision-driving | P2 |
| FIN.TEMPORAL.inventory_buildup | Inventory days increasing (manufacturing/retail) | Knowledge Audit, Forensic Accounting | Shareholders, Regulators | Decision-driving | P2 |
| FIN.TEMPORAL.employee_count_vs_growth | Employee count declining while growth narrative maintained | Knowledge Audit | Shareholders | Decision-driving | P2 |
| FIN.TEMPORAL.capex_vs_revenue | CapEx increasing while revenue flat/declining | Knowledge Audit | Shareholders | Context/display | P3 |
| FIN.INSOL.altman_z_zone | Altman Z-Score zone classification (distress/gray/safe) | Non-SCA Claims | Creditors, Shareholders | Decision-driving | P1 |
| FIN.INSOL.zone_of_insolvency | Zone of insolvency assessment (creditor duty trigger) | Non-SCA Claims | Creditors | Decision-driving | P1 |
| FIN.INSOL.insider_payments_distress | Insider compensation during financial distress | Non-SCA Claims | Creditors | Decision-driving | P2 |
| FIN.INSOL.dividends_during_distress | Dividends/buybacks while cash flow declining | Non-SCA Claims | Creditors | Decision-driving | P2 |
| FIN.INSOL.debt_funded_decline | Debt-funded expansion during operating decline | Non-SCA Claims | Creditors | Decision-driving | P2 |
| FIN.DDL.exposure_calculation | Disclosure Dollar Loss computation on stock drop events | Knowledge Audit, Recent Claims | Shareholders | Decision-driving | P2 |

**NLP/Forensic Signals (NEW -- ~15 checks)**

| Check ID | Name | Source Doc | Lenses | Category | Priority |
|----------|------|-----------|--------|----------|----------|
| NLP.MDA.tone_shift | MD&A sentiment shift YoY (negative/uncertain word frequency) | Knowledge Audit, Cutting Edge | Shareholders, Regulators | Decision-driving | P1 |
| NLP.MDA.specificity_erosion | Forward-looking statement specificity declining | Cutting Edge | Shareholders | Decision-driving | P2 |
| NLP.MDA.readability_change | Gunning Fog / Flesch readability change YoY | Cutting Edge | Shareholders, Regulators | Decision-driving | P2 |
| NLP.MDA.forward_backward_ratio | Forward-looking vs. backward-looking language balance shift | Cutting Edge | Shareholders | Context/display | P3 |
| NLP.RISK.factor_evolution | Risk factors added/removed/changed vs. prior year | Knowledge Audit | Shareholders, Regulators | Decision-driving | P1 |
| NLP.RISK.boilerplate_staleness | Risk factors unchanged despite material events | Cutting Edge | Shareholders, Regulators | Decision-driving | P2 |
| NLP.AUDIT.cam_changes | Critical Audit Matters added/removed/expanded | Knowledge Audit | Shareholders, Regulators | Decision-driving | P2 |
| NLP.AUDIT.going_concern_trajectory | Going concern language evolution across auditor reports | Knowledge Audit | Creditors, Shareholders | Decision-driving | P2 |
| NLP.DISC.whistleblower_language | Whistleblower/qui tam language in Items 1A, 3, legal footnotes | Knowledge Audit, Non-SCA Claims | Regulators, Employees | Decision-driving | P1 |
| NLP.DISC.revenue_recognition_changes | ASC 606 methodology changes vs. prior year | Knowledge Audit | Shareholders, Regulators | Decision-driving | P2 |
| NLP.DISC.related_party_language | Related party transaction disclosure analysis | Knowledge Audit | Shareholders (derivative) | Decision-driving | P2 |
| NLP.DISC.kitchen_sink_quarter | Quarter with multiple large write-downs + guidance reset | Knowledge Audit | Shareholders | Decision-driving | P2 |
| NLP.COMMENT.sec_comment_letters | SEC comment letter count, topic, and escalation | Knowledge Audit, Cutting Edge | Regulators, Shareholders | Decision-driving | P2 |
| NLP.FILING.timing_anomaly | Filing time deviation from company's own pattern | Cutting Edge | All | Decision-driving | P2 |
| NLP.FILING.nt_filing | Non-timely filing (NT 10-K, NT 10-Q) | Cutting Edge | Shareholders, Regulators | Decision-driving | P1 |

**Derivative/Governance Enhancement (NEW -- ~15 checks)**

| Check ID | Name | Source Doc | Lenses | Category | Priority |
|----------|------|-----------|--------|----------|----------|
| DERIV.CAREMARK.mission_critical | Mission-critical compliance area + board committee assessment | Non-SCA Claims | Shareholders (derivative) | Decision-driving | P1 |
| DERIV.CAREMARK.regulatory_pattern | Pattern of regulatory actions in same compliance area | Non-SCA Claims | Shareholders (derivative), Regulators | Decision-driving | P1 |
| DERIV.CAREMARK.cyber_oversight | Board-level cybersecurity oversight committee/framework | Non-SCA Claims, Recent Claims | Shareholders (derivative), Customers | Decision-driving | P2 |
| DERIV.CAREMARK.ai_governance | AI governance committee/policy/oversight framework | Non-SCA Claims | Shareholders (derivative) | Decision-driving | P2 |
| DERIV.SAY_ON_PAY.result | Say-on-pay vote result (flag <70% approval) | Non-SCA Claims | Shareholders (derivative) | Decision-driving | P2 |
| DERIV.SAY_ON_PAY.trend | Say-on-pay vote trend over 3 years | Non-SCA Claims | Shareholders (derivative) | Decision-driving | P3 |
| DERIV.ACTIVISM.shareholder_proposals | Active shareholder proposals (governance-related) | Non-SCA Claims | Shareholders | Decision-driving | P2 |
| DERIV.ACTIVISM.13d_filings | New 13D filings (activist intent) or 13G-to-13D conversions | Cutting Edge | Shareholders | Decision-driving | P2 |
| GOV.INCORP.state | State of incorporation risk modifier (Delaware vs. Nevada/Texas) | Recent Claims | Shareholders (derivative) | Context/display | P3 |
| GOV.INCORP.reincorporation_proposal | Pending reincorporation proposal | Recent Claims | Shareholders (derivative) | Context/display | P3 |

**Regulatory/Emerging (NEW -- ~15 checks)**

| Check ID | Name | Source Doc | Lenses | Category | Priority |
|----------|------|-----------|--------|----------|----------|
| REG.RECIDIVIST.prior_enforcement | Prior SEC/DOJ/regulatory enforcement action at this company | Recent Claims | Regulators, Shareholders | Decision-driving | P1 |
| REG.DOJ.investigation_language | DOJ subpoena/investigation/cooperation language in filings | Non-SCA Claims | Regulators | Decision-driving | P1 |
| REG.FCPA.geographic_risk | Revenue/operations in high-corruption countries (TI CPI < 40) | Non-SCA Claims | Regulators, Government | Decision-driving | P2 |
| REG.STATE_AG.enforcement_trend | Industry-specific state AG enforcement activity | Non-SCA Claims, Recent Claims | Regulators, Customers | Decision-driving | P2 |
| REG.CFPB.complaint_trend | CFPB consumer complaint volume trajectory | Non-SCA Claims | Regulators, Customers | Context/display | P3 |
| REG.PRIVACY.state_law_exposure | Number of applicable state privacy laws based on operations | Non-SCA Claims | Regulators, Customers | Decision-driving | P2 |
| REG.CYBER.governance_score | SEC cybersecurity disclosure rules compliance + board oversight | Recent Claims | Regulators, Customers, Shareholders | Decision-driving | P2 |
| REG.CYBER.breach_history | Prior data breach incidents | Recent Claims | Customers, Regulators | Decision-driving | P1 |
| EMERGING.AI.washing_indicator | AI revenue claims vs. actual AI-derived revenue | Recent Claims | Shareholders, Regulators | Decision-driving | P1 |
| EMERGING.AI.risk_factor_quality | AI risk factor disclosure quality (boilerplate vs. substantive) | Non-SCA Claims | Shareholders (derivative) | Context/display | P2 |
| EMERGING.SHORT.report_count | Count of independent short seller reports targeting company | Recent Claims | Shareholders | Decision-driving | P1 |
| EMERGING.SHORT.report_quality | Short seller report allegation type (fraud vs. valuation) | Recent Claims | Shareholders | Decision-driving | P2 |
| BIZ.COMPLEX.subsidiary_count | Number of subsidiaries (10-K Exhibit 21) | Non-SCA Claims | All | Context/display | P2 |
| BIZ.COMPLEX.jurisdiction_count | Number of countries with material operations | Non-SCA Claims | Regulators, Government | Context/display | P2 |
| BIZ.COMPLEX.rev_rec_complexity | Revenue recognition policy complexity score | Non-SCA Claims, Forensic Accounting | Shareholders, Regulators | Decision-driving | P2 |

**Estimated total new checks: ~90**
**Estimated total after reorganization: ~415 active checks + ~25 deprecated**

---

## 5. Baseline Characteristics & Inherent Risk Model

### 5.1 What Feeds the Inherent Risk Calculation

Baseline characteristics are INPUTS to the inherent risk model. They are parameters, not findings. They are always displayed (customary layer) but not scored as good or bad on their own. They determine the *starting point* from which all other signals are interpreted.

**The baseline parameters:**

| Parameter | Source | How It Modifies Risk Interpretation |
|-----------|--------|-------------------------------------|
| Market cap | Market data | Larger cap = larger DDL = larger settlements = more plaintiff interest |
| Revenue | 10-K | Business scale context |
| Employee count | 10-K Part I | Operating complexity proxy |
| Industry / SIC-NAICS | 10-K | Sector-specific baseline filing rates, regulatory intensity |
| Geography (HQ + operations) | 10-K | Jurisdictional exposure, FCPA risk |
| Public company age | SEC filing history | IPO recency (first 3 years = 2.8x filing probability) |
| Analyst coverage count | Market data | More coverage = more scrutiny = higher filing probability |
| Institutional ownership % | 13F filings | Higher institutional = more likely institutional lead plaintiff |
| State of incorporation | 10-K | Delaware = higher derivative risk; Nevada/Texas = lower but untested |
| Regulatory intensity score | Derived from industry | Multiplier on governance and regulatory checks |
| Prior SCA count (5 years) | Stanford SCAC / EDGAR | 4.2x lift for companies with prior SCA history |

### 5.2 Market Cap x Industry Matrix (Updated for Cap Inflation)

The user identified a critical point: market caps are 3-4x what they were a decade ago. The same percentage stock drop produces a 3-4x larger DDL, which drives 3-4x larger settlements. Historical settlement averages in nominal dollars systematically underestimate future severity.

**Market Cap Tier Definitions (2026-adjusted):**

| Tier | Market Cap Range | Annual SCA Filing Rate | Avg Settlement (if not dismissed) | DDL Multiplier |
|------|-----------------|----------------------|----------------------------------|----------------|
| Mega-cap | > $200B | ~6-8% | $150-500M+ | 4.0x |
| Large-cap | $10-200B | ~4-6% | $40-150M | 2.5x |
| Mid-cap | $2-10B | ~3-4% | $15-40M | 1.5x |
| Small-cap | $300M-2B | ~2-3% | $5-15M | 1.0x |
| Micro-cap | < $300M | ~1-2% | $2-5M | 0.5x |

**Industry Filing Rate Modifiers (2024-2025 data):**

| Industry | Share of Core Filings | Modifier |
|----------|----------------------|----------|
| Technology (AI/Cloud) | ~26% | 1.5x |
| Healthcare/Biotech | ~31% (largest single sector in 2025) | 1.6x |
| Financial Services | ~10% (rising with private credit) | 1.2x |
| Consumer Non-Cyclical | ~8% (up 16% in 2025) | 1.1x |
| Energy | ~5% | 0.9x |
| Industrial/Manufacturing | ~5% | 0.8x |
| All others | ~15% | 1.0x |

### 5.3 DDL Exposure Computation and Settlement Prediction

**Disclosure Dollar Loss (DDL)** is the single best predictor of whether a case will settle and for how much. Cases with DDL > $500M settle 85%+ of the time. The Cornerstone Research regression model explains >75% of variance in settlement amounts using DDL as the primary variable.

**Formula:**
```
DDL = Stock Price Drop on Corrective Disclosure Date x Shares Outstanding
Maximum Dollar Loss (MDL) = (Class Period High - Post-Disclosure Low) x Shares Outstanding
```

**Settlement Prediction Model (5-step framework from game theory research):**
```
Step 1: Compute DDL
  DDL = Market Cap Change on corrective disclosure dates
  For prospective analysis: estimate DDL from historical volatility and risk factors
  Base case: 10-20% stock drop on single disclosure event
  Stress case: 40-60% drop (accounting fraud, executive misconduct)
  Extreme case: 80%+ drop (Enron/FTX-level collapse)

Step 2: Apply settlement percentage by DDL tier
  | DDL Tier        | Median Settlement as % of DDL |
  |-----------------|-------------------------------|
  | < $25M          | 28.2% (highest ratio)         |
  | $25M - $150M    | ~10-15%                       |
  | $150M - $500M   | ~5-8%                         |
  | $500M - $1B     | ~3-5%                         |
  | > $1B           | ~2-4%                         |
  | Overall median  | 7.3% (2024 Cornerstone data)  |

Step 3: Adjust for case characteristics (multipliers)
  Financial restatement: 1.3-1.8x
  SEC enforcement action: 1.5-2.0x
  Institutional lead plaintiff: 1.5-2.5x (Bernstein Litowitz = high end)
  Accounting co-defendant: 1.2-1.5x
  Section 11 claim (vs. pure 10b-5): 1.2-1.4x
  Criminal charges: 2.0-3.0x
  Corresponding derivative action: 1.1-1.3x

Step 4: Cap at available insurance (Baker & Griffith finding)
  "The vast majority of securities claims settle within or just above
   the limits of the defendant corporation's D&O liability insurance coverage."
  If estimated_settlement > total_tower_limits:
    settlement likely = total_tower_limits
  The limits you write partially DETERMINE the settlement amount.

Step 5: Apply probability weighting for expected loss
  P(filing) = f(industry, market_cap, financial_distress, governance)
  P(survive_MTD) = ~50% (PSLRA heightened pleading standard)
  P(settlement | survive) = ~85%
  Expected_loss = settlement_estimate x P(filing) x P(survive_MTD) x P(settlement)
```

**Defense Cost Estimation (Stanford Securities Litigation Analytics):**

| Litigation Stage | Cumulative Defense Costs | Average Settlement |
|-----------------|------------------------|--------------------|
| Through MTD filing | ~$1.5M | N/A (dismissed or early settle) |
| Through discovery | ~$10M | $42M |
| Through summary judgment | ~$12-15M | $63M |
| Post-SJ denial | ~$15-20M | $120M |
| Trial preparation | ~$20-30M | Rare |

Defense cost drivers: number of individual defendants (each retains separate counsel), document volume, deposition count, jurisdiction (SDNY/N.D. Cal. most expensive), class period duration. Defense costs have nearly doubled for large D&O claims in the past six years (Allianz Commercial). Legal fee inflation: 8.3% in 2024 vs. 4.3% average.

**Plaintiff Attorney Filing Economics:**

A plaintiff attorney's decision to file is an expected value calculation:
```
EV = DDL x P(survive MTD) x P(settlement | survive) x Settlement% x Fee% - Litigation Costs

Worked example: Company with $500M DDL
  EV = $500M x 0.50 x 0.85 x 0.073 x 0.30 - $2M = $13.5M expected fee
```
This explains why cases with DDL below ~$50M are less attractive to top-tier firms. The system should flag when a company's potential DDL exceeds the $50M threshold where top-tier plaintiff firms become interested. The identity of the appointed plaintiff firm signals severity: Bernstein Litowitz cases average $120.3M settlement vs. Robbins Geller at $47.5M.

**Context-through-comparison presentation:**
- "This company's current DDL exposure (stress case) is $4.2B, placing it in the top 5% of potential cases by DDL"
- "If sued, estimated settlement range: $35-85M (base case), with 65% probability of filing given current risk profile"
- "At this DDL level, top-tier plaintiff firms (Bernstein Litowitz, Kessler Topaz) would find this case attractive"

**2025 DDL context:** Total DDL reached $694B (ALL-TIME RECORD, 62% increase over 2024). This is driven by mega-cap filings. The system must weight mega-cap companies' DDL exposure more heavily. A filing against a $500B+ market cap company has outsized DDL impact.

### 5.4 How Baseline Modifies Interpretation

The inherent risk model produces a **Starting Tier** for every company based solely on baseline characteristics, before any objective risk signals are considered:

```
Starting Tier = f(Market Cap Tier, Industry Modifier, Public Company Age, Prior SCA History, Regulatory Intensity)

Example 1: Clean mid-risk
  $50B tech company, public 8 years, no prior SCA, moderate regulatory intensity
  = Large-cap (4-6% base rate) x Tech (1.5x) x Mature (1.0x) x Clean (1.0x) x Moderate Reg (1.0x)
  = Effective filing rate: ~6-9%
  = Starting Tier: BENCHMARK (standard pricing)
  = DDL exposure (base case, 15% drop): $7.5B
  = Settlement range (if sued): $55-130M (Cornerstone regression)
  = Plaintiff attorney interest: HIGH (DDL well above $50M threshold)

Example 2: High-risk profile
  $5B healthcare company, public 2 years (IPO), prior SCA settlement
  = Mid-cap (3-4% base rate) x Healthcare (1.6x) x IPO (2.8x) x Prior SCA (4.2x) x High Reg (1.3x)
  = Effective filing rate: ~28-77% (effectively certain claim)
  = Starting Tier: CHALLENGE or REFER
  = DDL exposure (base case, 20% drop): $1B
  = Settlement range (if sued): $15-40M, with 1.3-1.8x multiplier if IPO-related Section 11 claim
  = Prior SCA counterbalance: N/A (prior claims present)

Example 3: No claims but high risk (F1 counterbalance scenario)
  $20B biotech company, public 5 years, NO prior SCA, high regulatory intensity
  = Mid-to-Large-cap (4-5% base rate) x Healthcare/Biotech (1.6x) x Post-IPO (1.5x) x Clean (1.0x) x High Reg (1.3x)
  = Effective filing rate: ~12-16%
  = Starting Tier: WATCH
  = BUT: 5 of 7 identified peers have been subject to SCA. Absence of claims needs explanation.
  = System flags: "Despite clean litigation history, inherent risk profile suggests 12-16% annual
    filing probability. Peer litigation is common in this sector. Bear case analysis recommended."
```

**Market Pricing Context (when premium data available):**

The Starting Tier feeds directly into the mispricing signal detection (Section 10.2). A company priced as BENCHMARK but with an effective filing rate suggesting CHALLENGE is a mispricing candidate. The system surfaces this as: "Risk profile suggests [CHALLENGE] tier but market pricing reflects [BENCHMARK]. Premium per $M of market cap ($18) is below peer median ($25)."

---

## 6. Executive Forensics Dimension

### 6.1 The Shadiness Score Framework

Executive forensics is the user's TOP PRIORITY -- more important than governance structure metrics. The fundamental questions are:
1. What lawsuits have these people been involved in at OTHER companies?
2. What does their personal background look like? (the "shadiness score")

**Individual Executive Risk Score (0-100):**

| Category | Max Points | Signals | Primary Source |
|----------|-----------|---------|----------------|
| Prior Securities Litigation | 25 | Named defendant in SCA at ANY company; settlement size matters | Stanford SCAC, CourtListener, PACER |
| SEC/Regulatory Enforcement | 25 | Personal enforcement action, FINRA sanction, OCC/FDIC action | SEC SALI, FINRA BrokerCheck, NYU SEED |
| Prior Company Failures | 15 | Officer/director at company that went bankrupt, restated, or faced SEC investigation | S&P Capital IQ + PACER + SEC EFTS |
| Insider Trading Patterns | 10 | Suspicious timing/volume; trading during blackout periods | SEC Form 4 analysis |
| Personal Financial Issues | 10 | Personal bankruptcy, tax liens, large judgments | PACER, BrokerCheck |
| Negative News / Reputation | 10 | Negative coverage in mainstream financial press | Brave Search |
| Tenure/Stability Red Flags | 5 | Forced departures, serial short-term roles, unexplained gaps | S&P Capital IQ, proxy bios |

**Time decay:** Reduce score by 20% for each 5-year period since the event. A 2-year-old SEC action is far more relevant than a 15-year-old dismissed lawsuit.

**Board/Management Aggregate Risk Score:**
```
Aggregate = Sum(Individual_Score_i x Role_Weight_i) / Sum(Role_Weight_i)

Role Weights:
  CEO: 3.0x | CFO: 2.5x | Board Chair: 2.5x | COO/President: 2.0x
  General Counsel: 2.0x | Audit Committee Chair: 2.0x
  Other NEOs: 1.5x | Independent Directors: 1.0x
```

**Risk Tiers:**

| Score | Tier | Underwriting Action |
|-------|------|-------------------|
| 0-10 | LOW | Standard underwriting |
| 11-25 | MODERATE | Enhanced review, document findings |
| 26-50 | HIGH | Senior underwriter review required |
| 51-75 | VERY HIGH | Potential declination or significant surcharge |
| 76-100 | EXTREME | Declination recommended |

### 6.2 Data Sources and Acquisition Strategy

**Free sources (SEC + public records + web):**

| Priority | Source | API? | What It Provides |
|----------|--------|------|-----------------|
| 1 | SEC Action Lookup (SALI) | NO (Playwright) | SEC enforcement actions as defendant |
| 2 | NYU SEED Database | NO (Playwright) | SEC enforcement vs. individuals |
| 3 | SEC EDGAR Full-Text Search (EFTS) | YES (REST) | Name mentions in any SEC filing |
| 4 | CourtListener | YES (REST, 5000 req/hr) | Federal court cases by party name |
| 5 | PACER Case Locator | YES (REST, $0.10/page) | All federal cases nationwide |
| 6 | judyrecords | YES (REST) | 760M+ state + federal cases |
| 7 | FINRA BrokerCheck | NO (Playwright) | Broker/advisor disclosures, sanctions |
| 8 | Stanford SCAC | NO (Playwright) | SCAs by company ticker (search prior companies) |
| 9 | Brave Search | YES (MCP) | News coverage of legal issues |
| 10 | OCC/FDIC Enforcement | NO (Playwright) | Bank officer/director actions |

**Paid (user has access):**
- S&P Capital IQ: Career history, board memberships, compensation data. THE most important source for cross-referencing an executive's full board history.

**Estimated cost per company:** $0.50-$3.00 (primarily PACER fees if used). Within $2.00 budget if PACER is limited to high-priority cases where free sources suggest something to find.

### 6.3 Integration with the Check System

Executive forensics generates checks at two levels:

**Individual level:** Each executive/director gets an Individual Executive Risk Score. If the score exceeds threshold (>25), individual findings are displayed in the worksheet.

**Aggregate level:** The Board/Management Aggregate Risk Score feeds into the scoring model. Proposed integration:

| Score Range | Factor Impact | Worksheet Treatment |
|------------|---------------|-------------------|
| 0-10 | No impact | "No executive background concerns identified" |
| 11-25 | +2 points to F9 (Governance) | Brief summary of moderate findings |
| 26-50 | +4 points; triggers REFER consideration | Detailed findings section; individual profiles |
| 51-75 | +6 points; triggers CRF-15 (REFER) | Full executive forensics section; red flag |
| 76-100 | +8 points; triggers CRF-16 (DECLINE consideration) | Full section; prominent red flag |

### 6.4 How It Maps to "Who's Suing" Lenses

Executive forensics data connects to EVERY plaintiff lens:
- **Shareholders:** Prior SCA involvement = elevated recurrence probability; insider trading patterns = scienter evidence
- **Regulators:** Prior SEC/FINRA/OCC enforcement = heightened regulatory scrutiny
- **Employees:** Harassment/discrimination history = workplace culture risk
- **Creditors:** Prior company bankruptcies = distress management capability
- **Customers/Competitors/Government:** Prior fraud convictions or debarments = integrity signal

This makes executive forensics the single most multi-lens connected dimension in the system.

---

## 7. Financial Integrity Dimension

### 7.1 Forensic Accounting Models

The system implements a battery of validated forensic models. All run silently. Only issues get surfaced.

**Tier 1 Models (Proven, XBRL-computable, implement first):**

| Model | What It Detects | Threshold | Status |
|-------|----------------|-----------|--------|
| Beneish M-Score (8-var) | Earnings manipulation | > -1.78 = likely manipulator | IMPLEMENTED |
| Dechow F-Score (Model 1) | Material accounting misstatements (trained on SEC AAERs) | > 1.0 = above-normal risk | TO BUILD |
| Montier C-Score (6 binary) | Book cooking signals | 4-6 = high risk | TO BUILD |
| Sloan Accrual Ratio (enhanced) | Earnings quality deterioration | > +25% = danger zone | PARTIAL (needs graduated zones) |
| Cash Flow Quality Score | Earnings-cash divergence | Composite 0-100, <40 = critical | PARTIAL (needs CCE, AI, multi-period) |
| Revenue Quality Score | Revenue manipulation | Composite 0-100, <40 = critical | PARTIAL (DSO exists, needs rest) |

**Tier 2 Models (Validated, requires NLP on filing text):**

| Model | What It Detects | Status |
|-------|----------------|--------|
| Audit Risk Score | Reporting problems (MW, CAMs, GC, restatements, auditor changes) | TO BUILD |
| Lev-Thiagarajan (12 signals, 8 XBRL + 4 text) | Earnings sustainability | TO BUILD |
| Benford's Law | Digit distribution anomalies in financial data | TO BUILD |

**Tier 3 Models (Advanced/Future):**

| Model | Status | Reason for Deferral |
|-------|--------|-------------------|
| Modified Jones Model | SKIP | Requires peer panel regression -- Dechow F-Score captures similar info |
| FinBERT topic-driven sentiment | EVALUATE | Requires ML infrastructure; LLM extraction may suffice |
| Graph neural network fraud detection | FUTURE | Research project, not near-term |

### 7.2 Financial Integrity Score (Composite 0-100)

**Architecture:**
```
FINANCIAL INTEGRITY SCORE (0-100, higher = more integrity)
|
+-- Manipulation Detection (30%)
|     Beneish M-Score (normalized): 40%
|     Dechow F-Score (normalized):  35%
|     Montier C-Score (normalized): 25%
|
+-- Accrual Quality (20%)
|     Enhanced Sloan Ratio: 50%
|     Accruals Intensity: 30%
|     Multi-period NI vs CFO divergence: 20%
|
+-- Revenue Quality (20%)
|     DSO trend: 30%
|     Revenue-Receivable divergence: 30%
|     Deferred revenue analysis: 20%
|     Q4 revenue concentration: 20%
|
+-- Cash Flow Quality (15%)
|     QoE Ratio (CFO/NI): 40%
|     Cash Conversion Efficiency: 30%
|     Cash Flow Adequacy: 30%
|
+-- Audit Risk (15%)
      Material weakness: 30%
      Auditor changes: 20%
      Restatement history: 25%
      Going concern: 25%
```

**Zone Classification:**

| Score | Zone | Worksheet Treatment |
|-------|------|-------------------|
| 80-100 | HIGH INTEGRITY | "No financial integrity concerns identified" |
| 60-79 | ADEQUATE | Brief note on any declining trajectory |
| 40-59 | CONCERNING | Detailed breakdown of flagged components |
| 20-39 | WEAK | Full forensic analysis section with all model outputs |
| 0-19 | CRITICAL | Prominent red flag; full forensic breakdown; pricing/declination trigger |

### 7.3 Issue-Driven Presentation

The user was clear: "I need to know if they can pay their debt. I need to know if they're fudging accounting. I don't need their actual margins unless it's an issue relative to competition."

**Presentation rules:**
1. If Financial Integrity Score >= 80: One line: "Financial Integrity Score: 87/100. No financial integrity concerns identified."
2. If Financial Integrity Score 60-79: Brief section listing any declining trajectory or borderline signals.
3. If Financial Integrity Score 40-59: Detailed section showing which sub-scores are flagged. Break down the specific model outputs that are driving the concern. Show the specific financial statement lines that triggered the models.
4. If Financial Integrity Score < 40: Full forensic analysis section. Show every model output. Show the component variables. Show the trend over 3 years. Show peer comparison. This is where the worksheet gets THICK.

### 7.4 Temporal Change Detection Engine

The strongest predictors are CHANGES over time, not point-in-time values. The system needs a `TemporalAnalyzer` that computes QoQ and YoY changes for:

| Metric | Trend Direction | Signal Strength |
|--------|----------------|-----------------|
| Revenue growth rate | Decelerating 3+ periods | HIGH -- classic growth darling trigger |
| Gross margin | Declining 3+ quarters | HIGH -- pricing power loss |
| DSO | Increasing 3+ quarters | HIGH -- revenue recognition red flag |
| CFO/NI divergence | Widening 3+ periods | HIGH -- earnings quality deterioration |
| Working capital | Deteriorating 3+ quarters | MEDIUM -- liquidity stress |
| SG&A as % of revenue | Increasing | MEDIUM -- operating leverage shift |
| CapEx as % of revenue | Increasing while revenue flat | MEDIUM -- capital allocation concern |
| Employee count | Declining while growth narrative maintained | HIGH -- narrative inconsistency |
| Debt/EBITDA | Deteriorating trajectory | MEDIUM -- financial distress path |
| Inventory days | Increasing (manufacturing/retail) | HIGH for applicable sectors |

**Each temporal signal produces a classification:** IMPROVING / STABLE / DETERIORATING / CRITICAL

**Integration:** Feed temporal classifications into existing checks as an additional data dimension. A check that fires on a point-in-time value fires STRONGER when the temporal trajectory is deteriorating.

---

## 8. NLP/Forensic Signal Dimension

### 8.1 Priority-Ranked Signals

Ranked by predictive value and implementation feasibility:

| Rank | Signal | Predictive Value | Feasibility | Data Source | Priority |
|------|--------|-----------------|-------------|-------------|----------|
| 1 | MD&A tone shift (negative/uncertain word frequency change YoY) | HIGH (Lift ~2x) | 4/5 | 10-K Item 7 | P1 |
| 2 | Risk factor evolution (added/removed/changed vs. prior year) | HIGH | 5/5 | 10-K Item 1A | P1 |
| 3 | NT filing detection | HIGH | 5/5 | EDGAR metadata | P1 |
| 4 | Filing timing anomaly | HIGH | 5/5 | EDGAR timestamp | P1 |
| 5 | Auditor change detection (8-K Item 4.01, resignation vs. dismissal) | HIGH | 5/5 | 8-K | P1 |
| 6 | Whistleblower/qui tam language detection | HIGH (when present) | 5/5 | 10-K Items 1A, 3, footnotes | P1 |
| 7 | Revenue recognition methodology changes | HIGH | 4/5 | 10-K Note 2 | P2 |
| 8 | Non-GAAP/GAAP divergence tracking | HIGH | 4/5 | 8-K earnings releases | P2 |
| 9 | "Kitchen sink" quarter detection | MEDIUM | 4/5 | 8-K earnings releases | P2 |
| 10 | SEC comment letter analysis (topic, escalation, response quality) | MEDIUM-HIGH | 4/5 | EDGAR CORRESP | P2 |
| 11 | Auditor CAM changes | MEDIUM-HIGH | 4/5 | 10-K auditor report | P2 |
| 12 | Readability manipulation (Fog Index change) | MEDIUM-HIGH | 5/5 | 10-K text | P2 |
| 13 | Boilerplate/stickiness detection (risk factors unchanged despite events) | MEDIUM | 5/5 | 10-K Item 1A consecutive years | P2 |
| 14 | Related party transaction language analysis | MEDIUM-HIGH | 4/5 | 10-K footnotes, proxy | P2 |
| 15 | Specificity erosion (quantitative targets replaced by vague language) | MEDIUM | 4/5 | MD&A, earnings calls | P3 |
| 16 | Footnote complexity / obfuscation detection | MEDIUM | 5/5 | 10-K footnotes | P3 |
| 17 | Going concern language trajectory | MEDIUM | 4/5 | 10-K auditor opinion | P2 |
| 18 | Deception detection in earnings calls (Larcker-Zakolyukina model) | HIGH | 4/5 | Earnings call transcripts | P3 (blocked by transcript acquisition) |
| 19 | Sentiment divergence (CEO vs. CFO tone, prepared vs. Q&A) | HIGH | 4/5 | Earnings call transcripts | P3 (blocked by transcript acquisition) |
| 20 | 8-K filing pattern analysis (frequency, timing, item types) | MEDIUM-HIGH | 5/5 | EDGAR 8-K filings | P2 |

### 8.2 What's Implementable with Current LLM Extraction

The system already sends full 10-K/10-Q filings to Claude Haiku for structured extraction. The following signals can be added as extraction prompts:

**P1 -- Add to existing extraction pipeline:**
- MD&A tone metrics (negative word count, uncertain word count, forward-looking specificity rating, key narrative themes)
- Risk factor headings + key language (for evolution tracking against prior year)
- Whistleblower/internal investigation language detection
- Going concern language in auditor opinion
- Revenue recognition methodology description

**P2 -- Add as new extraction targets:**
- CAM headings and descriptions from auditor report
- Related party transaction details from proxy/10-K
- Revenue recognition policy changes
- Non-GAAP metrics from 8-K earnings releases

### 8.3 Data Availability Constraints

| Signal | Data Available? | Constraint |
|--------|----------------|------------|
| All 10-K-based NLP signals | YES | 10-K filings already acquired |
| Risk factor evolution | YES (needs current + prior year 10-K) | Prior year filing must be acquired |
| SEC comment letters | YES (EDGAR CORRESP, 60-day delay) | Delayed publication |
| Earnings call transcripts | NO (not currently acquired) | Seeking Alpha transcripts are free but need acquisition pipeline |
| 8-K pattern analysis | YES (EDGAR filing metadata) | Already available |
| NT filing detection | YES (EDGAR NT filing search) | Trivial to implement |

### 8.4 Integration Approach

NLP signals integrate as sub-factors under existing factors:

| Signal | Parent Factor | Weight |
|--------|--------------|--------|
| MD&A tone shift | F3 (Restatement/Audit) | +1-3 points based on magnitude |
| Risk factor evolution | F3 | +1-2 points for material removals |
| Non-GAAP divergence | F5 (Guidance Misses) | +1-2 points if divergence widening |
| Revenue recognition changes | F3 | +1-2 points for methodology changes |
| SEC comment letters | F3 | +1 point if accounting-focused, multi-round |
| Auditor CAM changes | F3 | +1-2 points for new/expanded CAMs |
| Whistleblower language | New CRF-17 | Trigger REFER if detected |
| NT filing | F3 | +3-5 points (strong signal) |
| Kitchen sink quarter | F5 | +2-3 points |

---

## 9. The Bear Case Framework

### 9.1 Allegation Templates by Plaintiff Type

The bear case framework constructs the plaintiff's complaint for every company. This transforms the worksheet from a checklist to an underwriting tool.

**Template 1: Earnings Guidance Fraud (Shareholders, ~40% of SCA filings)**
```
IF: Company provides guidance + misses by >15% + stock drops >15% + insider selling during guidance period
THEN: "Plaintiff would allege management knew guidance was unattainable when given,
       citing [insider trading data], [revenue recognition changes], and [internal forecasts
       that showed declining pipeline]."
```

**Template 2: Accounting Misstatement (Shareholders + Regulators, ~25% of SCA filings)**
```
IF: Beneish M-Score > -1.78 OR auditor change/resignation OR material weakness OR restatement
THEN: "Plaintiff would allege company knowingly filed materially false financial statements,
       citing [specific model outputs], [auditor events], and [temporal deterioration in
       earnings quality metrics]."
```

**Template 3: Product/Operational Fraud (Shareholders + Customers, ~20% of SCA filings)**
```
IF: Product safety issue OR operational metric restatement OR clinical trial failure + prior claims
THEN: "Plaintiff would allege company misrepresented [product efficacy/safety/operational metrics],
       citing [specific disclosure vs. reality gap]."
```

**Template 4: Regulatory Failure (Shareholders + Regulators + Employees)**
```
IF: Regulatory investigation OR consent order in mission-critical area OR whistleblower disclosure
THEN: "Plaintiff would allege board failed to oversee [mission-critical compliance area],
       citing [pattern of regulatory actions], [whistleblower disclosures], and
       [inadequate board committee structure] under Caremark."
```

**Template 5: AI-Washing (Shareholders, fastest growing category)**
```
IF: Company positions as "AI company" + AI risk factors are boilerplate + revenue from non-AI sources
THEN: "Plaintiff would allege company materially overstated AI capabilities to inflate valuation,
       citing [AI revenue gap], [short seller reports], and [specific misleading statements]."
```

**Template 6: No Claims But High Risk (Counterbalance to F1)**
```
IF: No prior SCA history + inherent risk model produces effective filing rate > 10%
    + multiple peer companies have been sued + elevated objective risk signals
THEN: "Despite clean litigation history, this company exhibits [N] characteristics
       historically associated with SCA filings in this industry:
       - [Specific signals: e.g., DSO trajectory, guidance miss pattern, insider selling]
       - [Peer comparison: e.g., 4 of 6 peers have faced SCA in past 5 years]
       - [Industry context: e.g., biotech sector SCA filing rate is 1.6x baseline]
       The absence of prior claims does NOT reduce inherent exposure. A plaintiff
       constructing a case today would focus on [top 2-3 bear case elements]."
```

This template is critical. The bear case framework must explicitly address the "no claims but high risk" scenario. The system should never allow clean history to mask current exposure. Every company, regardless of claims history, gets a bear case analysis. The question is not IF a case could be constructed, but HOW STRONG the case would be.

**Template 7: Settlement Scenario (Game Theory Integration)**
```
FOR EVERY COMPANY:
  "If this company were sued today:
   - Estimated DDL (base case): $[X]B based on [Y]% stock drop
   - Settlement range: $[low]-$[high]M (Cornerstone regression, adjusted for case characteristics)
   - Defense costs (estimated): $[X]M through [likely litigation stage]
   - Plaintiff attorney economics: DDL of $[X]B makes this case [attractive/marginal/unattractive]
     to top-tier plaintiff firms
   - Filing probability: [X]% based on [industry, market cap, governance, financial integrity]
   - Expected loss (probability-weighted): $[X]M"
```

### 9.2 Company-Specific Bear Case Generator

For each company, the system synthesizes all signals into five questions:

```
BEAR CASE: [COMPANY NAME]

1. WHAT WAS THE MISREPRESENTATION?
   [Automated: Map elevated checks to specific statements in 10-K, guidance, or 8-K
    that could be characterized as false or misleading]

2. WHAT DID MANAGEMENT KNOW? (Scienter)
   [Automated: Insider trading timing, 10b5-1 modifications, analyst Q&A deflections,
    executive forensics findings, MD&A tone shift]

3. WHEN DID/WOULD THE TRUTH EMERGE? (Corrective Disclosure)
   [Automated: Identify most likely trigger -- earnings miss, short seller report,
    regulatory action, restatement, product failure]

4. HOW MUCH WOULD SHAREHOLDERS LOSE? (DDL / Damages)
   [Automated: Compute hypothetical DDL based on market cap and severity scenario.
    Estimate settlement range from Cornerstone regression.]

5. IS THIS CASE VIABLE? (Pleading Standards)
   [Automated: Assess MTD survival probability based on allegation type and
    sector-adjusted dismissal rates. 57-66% of filed cases are dismissed.]
```

### 9.3 How Checks Feed into Bear Case Construction

Every decision-driving check maps to one or more bear case template slots:

| Check | Bear Case Slot | Contribution |
|-------|----------------|-------------|
| FIN.FORENSIC.beneish_m_score > -1.78 | #1 (Misrepresentation), #5 (Viability) | Accounting fraud allegation type; strengthens pleading |
| EXEC.TRADE.suspicious_timing | #2 (Scienter) | Pre-announcement selling = scienter evidence |
| NLP.MDA.tone_shift | #2 (Scienter) | Management language shift suggests awareness |
| FIN.TEMPORAL.dso_trajectory | #1 (Misrepresentation) | Revenue quality concern supports disclosure fraud |
| EMERGING.SHORT.report_count >= 2 | #3 (Corrective Disclosure), #5 (Viability) | Short reports as disclosure trigger; multiple = stronger case |
| FIN.DDL.exposure_calculation | #4 (Damages) | Quantifies settlement range |
| REG.RECIDIVIST.prior_enforcement | #5 (Viability) | Prior enforcement strengthens pleading |

---

## 10. Proposed Check Architecture

### 10.1 Multi-Dimensional Organization

Every check is classified along four dimensions:

```
DIMENSION 1: Worksheet Section (for display)
  BIZ.*     -> Section 1: Company Profile
  STOCK.*   -> Section 2: Market Analysis
  FIN.*     -> Section 3: Financial Analysis
  LIT.*     -> Section 4: Litigation & Regulatory
  GOV.*     -> Section 5: Governance
  FWRD.*    -> Section 6: Forward-Looking
  EXEC.*    -> Section 7: Executive Forensics (NEW)
  DERIV.*   -> Section 4 subsection (derivative exposure)
  NLP.*     -> Distributed across sections based on content
  REG.*     -> Section 4 subsection (regulatory exposure)
  EMERGING.* -> Section 6 subsection (emerging risks)

DIMENSION 2: "Who's Suing" Lens (for analysis)
  SHAREHOLDERS  -- SCA, derivative, appraisal, ERISA
  REGULATORS    -- SEC, DOJ, state AG, FTC, CFPB, sector regulators
  CUSTOMERS     -- Product liability, data privacy, consumer protection
  COMPETITORS   -- Antitrust, trade secret, patent
  EMPLOYEES     -- Whistleblower, discrimination, ERISA, wage/hour
  CREDITORS     -- Deepening insolvency, fraudulent transfer, zone of insolvency
  GOVERNMENT    -- FCA, procurement fraud, ITAR, sanctions

DIMENSION 3: Signal Type (for methodology)
  LEVEL      -- Point-in-time value (current ratio, stock price, SI level)
  DELTA      -- Change over time (margin compression, SI trend, DSO trajectory)
  PATTERN    -- Multi-signal composite (DEATH_SPIRAL, INFORMED_TRADING)
  FORENSIC   -- Quantitative model output (Beneish, Dechow, Montier)
  NLP        -- Linguistic/textual signal (tone shift, risk factor evolution)
  BENCHMARK  -- Peer-relative comparison (valuation premium, growth vs peers)
  EVENT      -- Binary catalyst (FDA decision, contract renewal, debt maturity)
  JUDGMENT   -- Subjective underwriter assessment (bear case, management quality)

DIMENSION 4: Check Category (for presentation)
  DECISION_DRIVING -- Scored, affects tier, may trigger red flag
  CONTEXT_DISPLAY  -- Always shown, not scored (customary layer)
  DEPRECATED       -- Marked for removal (do not present or score)
```

### 10.2 Mispricing and Market Intelligence Checks (NEW)

Game theory research reveals systematic pricing inefficiencies that the system should detect and surface:

**Pricing Benchmark Signals:**

| Check ID | Name | Data Source | Computation | Output |
|----------|------|-------------|-------------|--------|
| MKT.PRICE.cost_per_mcap | Cost per $M of Market Cap | User-input premium + market data | Annual Premium / (Market Cap / $1M) | Compare to peer group; flag >1.5x or <0.5x peer median |
| MKT.PRICE.premium_to_ddl | Premium-to-DDL Ratio | User-input premium + DDL computation | Premium / (DDL_est x Settlement% x P(filing)) | If ratio < 1.0, premium doesn't cover expected loss |
| MKT.PRICE.rate_per_million | Rate per $M of Limit | User-input premium + program structure | Premium / (Limit / $1M) by layer | Compare across tower; normally decreasing with attachment |
| MKT.CYCLE.position | Market Cycle Position | Layer 1 market intelligence | Rate trends, capacity, loss development patterns | Late soft / Early hardening / Hard / Post-hard |
| MKT.CYCLE.adverse_dev | Adverse Development Indicator | Layer 1 market intelligence | Calendar year vs. ultimate loss ratio gap | Flag when current CY loss ratio mirrors pre-2020 soft years |

**Risk Profile Mismatch Signals:**

| Check ID | Name | Data Source | Computation | Output |
|----------|------|-------------|-------------|--------|
| MKT.MISMATCH.governance_price | Governance-Price Disconnect | Governance score + peer premium data | Governance score tier vs. premium tier | "Governance risk = ELEVATED but pricing reflects STANDARD" |
| MKT.MISMATCH.distress_price | Financial Distress Mismatch | Financial integrity + premium data | Distress indicators vs. pricing adjustment | Distressed companies = 3-5x filing frequency |
| MKT.MISMATCH.sector_shift | Industry Sector Shift | Business mix vs. SIC code | Current revenue by segment vs. classification | Business mix shifted; pricing may reflect old profile |

**Tower Structure Signals:**

| Check ID | Name | Data Source | Computation | Output |
|----------|------|-------------|-------------|--------|
| MKT.TOWER.defense_erosion | Defense Cost Erosion Alert | Defense cost estimate + primary limits | Est. defense costs / primary limits | Flag if defense costs > 30% of primary limits |
| MKT.TOWER.position_rec | Tower Positioning Intelligence | Risk profile + tower economics | Game theory optimal position analysis | Write primary / low excess / mid excess / avoid |
| MKT.TOWER.side_a_adequacy | Side A Adequacy Assessment | Distress indicators + Side A limit | Qualitative flag for personal director exposure | Flag if distressed + Side A may be insufficient |

These checks require user-input premium/program data (not publicly available). When premium data is provided, the system activates the full market intelligence module. When not provided, these checks are suppressed and the system notes "Market pricing analysis available when premium data is provided."

### 10.3 Factor Restructuring Proposals

**Current 10-factor model (preserved with enhancements):**

| Factor | Current Weight | Proposed Enhancement |
|--------|---------------|---------------------|
| F1 Prior Litigation | 20 pts | Add DDL computation; add settlement range estimate; add recidivist flag; add "no claims but high risk" counterbalance (see F1 Weighting Note in Section 4.1) |
| F2 Stock Decline | 15 pts | Add DDL as severity input (not just % decline); incorporate cap inflation; add "this magnitude historically leads to X% filing probability" context |
| F3 Restatement/Audit | 12 pts | Add Beneish M-Score, Dechow F-Score, MD&A tone shift, risk factor evolution, CAM changes, NT filing as sub-factors. Restatement multiplier on settlement: 1.3-1.8x (game theory) |
| F4 IPO/SPAC/M&A | 10 pts | No change needed; SPAC decay curve validated. IPO companies in first 3 years = 2.8x filing probability |
| F5 Guidance Misses | 10 pts | Add magnitude-weighted miss tracking; add Non-GAAP divergence; add kitchen sink quarter |
| F6 Short Interest | 8 pts | Add named short seller report count and quality assessment. 21% of 2024 core SCA filings referenced short reports |
| F7 Volatility | 9 pts | Rename to "Market Risk Indicators"; add DDL exposure estimate as severity context; volatility feeds directly into DDL scenario analysis |
| F8 Financial Distress | 8 pts | Add temporal trajectory scoring (improving vs. deteriorating); add Altman Z zone classification. Distressed companies = 3-5x filing frequency (game theory). Zone of insolvency triggers duty expansion to creditors |
| F9 Governance | 6 pts | Absorb derivative exposure scoring; add Caremark mission-critical assessment; add executive forensics aggregate score. Institutional LP cases = 2.5x median settlement (game theory); governance quality affects LP appointment probability |
| F10 Officer Stability | 2 pts | Add departure-during-stress amplifier; add CFO/CAO departure timing. Executive turnover is a leading indicator of undisclosed issues (game theory) |

**New sub-factors within existing factors:**

| Sub-Factor | Parent | Points | Source |
|-----------|--------|--------|--------|
| Beneish M-Score > -1.78 | F3 | +2-3 pts | XBRL financial data |
| Dechow F-Score > 1.0 | F3 | +2-3 pts | XBRL financial data |
| Montier C-Score >= 4 | F3 | +1-2 pts | XBRL financial data |
| MD&A tone shift > 20% negative | F3 | +1-3 pts | LLM extraction |
| Risk factor material removal | F3 | +1-2 pts | LLM extraction |
| NT filing | F3 | +3-5 pts | EDGAR metadata |
| Non-GAAP/GAAP divergence widening | F5 | +1-2 pts | 8-K earnings releases |
| Kitchen sink quarter | F5 | +2-3 pts | 8-K earnings releases |
| Named short seller reports >= 2 | F6 | +2-3 pts | Web search |
| Peer valuation premium > 2x | F2 | +1-2 pts | Market + financial data |
| SEC comment letters (accounting, multi-round) | F3 | +1 pt | EDGAR CORRESP |
| Auditor CAM additions | F3 | +1-2 pts | 10-K auditor report |
| Executive Forensics aggregate > 25 | F9 | +2-6 pts | Executive forensics pipeline |
| Caremark mission-critical non-compliance | F9 | +2-4 pts | Proxy + 10-K + regulatory data |
| Temporal financial deterioration (3+ metrics) | F8 | +2-4 pts | Temporal analysis engine |
| DDL exposure > $500M | F1/F2 | Amplifier on settlement estimate | Market data + stock drop computation |

**New Critical Red Flag Gates:**

| CRF | Condition | Ceiling | Rationale |
|-----|-----------|---------|-----------|
| CRF-12 | Active DOJ criminal investigation disclosed | REFER | Fundamental change in D&O exposure |
| CRF-13 | Altman Z-Score < 1.81 (distress zone) | REFER | Zone of insolvency changes fiduciary duty framework |
| CRF-14 | Caremark claim survived dismissal | REFER | Court found colorable oversight failure evidence |
| CRF-15 | Executive Forensics aggregate > 50 | REFER | Very high people risk |
| CRF-16 | Financial Integrity Score < 20 | REFER | Critical financial reporting concerns |
| CRF-17 | Whistleblower/qui tam disclosure in current filings | REFER | Strong leading indicator of larger problems |

### 10.4 Estimated Total Check Count After Reorganization

| Category | Current | Deprecated | Enhanced | New | Proposed Total |
|----------|---------|-----------|----------|-----|---------------|
| BIZ.* (Business) | 58 | -5 | 0 | +5 (complexity) | 58 |
| STOCK.* (Market) | 35 | -2 | +3 (short seller reports) | +2 (options signals) | 38 |
| FIN.* (Financial) | 32 | -3 | +5 (temporal, enhanced models) | +20 (forensic, insolvency) | 54 |
| LIT.* (Litigation) | 56 | -3 | +5 (derivative, regulatory) | +10 (regulatory, emerging) | 68 |
| GOV.* (Governance) | 80 | -8 | +3 (Caremark, say-on-pay) | +5 (derivative exposure) | 80 |
| FWRD.* (Forward) | 88 | -8 | +5 (NLP signals) | +10 (bear case, emerging) | 95 |
| EXEC.* (Executive Forensics) | 0 | 0 | 0 | +20 | 20 |
| NLP.* (Linguistic/Filing) | 0 | 0 | 0 | +15 | 15 |
| REG.* (Regulatory) | 0 | 0 | 0 | +10 | 10 |
| EMERGING.* (Emerging) | 0 | 0 | 0 | +5 | 5 |
| DERIV.* (Derivative) | 0 | 0 | 0 | +10 | 10 |
| MKT.* (Market Intelligence) | 0 | 0 | 0 | +11 (mispricing, tower, cycle) | 11 |
| **Total** | **349** (+ 10 deprecated already) | **-29** | **+21** | **+123** | **~464** |

*Note: 11 checks moved to Future/Research (see Appendix E) due to data source constraints. Active check count reflects only implementable checks.*

---

## 11. Implementation Roadmap (Revised — Five-Layer Architecture)

The previous priority-based roadmap (P1-P4) is superseded by a layer-aligned phase structure that implements the five-layer analysis architecture in order. Each phase in the main ROADMAP.md maps to one or more layers.

### Phase 25: Classification Engine & Hazard Profile (Layers 1-2)

**What gets built:**
- Classification engine: market cap tier, industry sector, IPO age, exchange → base filing rate
- Hazard profile: 7 categories × key dimensions → Inherent Exposure Score (IES 0-100)
- Hazard interaction effects: named combinations with multipliers
- Config-driven: all thresholds, weights, and tiers in JSON config
- Integration: feeds into SCORE stage as pre-step

**Key items from original P1/P2 that land here:**
- 1g: DDL exposure computation (Classification feeds DDL)
- 1i: "No claims but high risk" counterbalance (Hazard profile enables this)
- P2h-j: Executive forensics foundation (People hazard dimension)

### Phase 26: Check Reorganization & Analytical Engine (Layer 3)

**What gets built:**
- Reclassify all 359+ checks: decision-driving vs context/display vs deprecated
- Map every check to plaintiff lenses (Dimension 2: who's suing)
- Map every check to signal type (Dimension 3: hazard vs signal vs peril)
- Temporal change detection engine (most SCA triggers are CHANGES, not levels)
- Financial forensics composites: Financial Integrity Score, Revenue Quality Score
- Executive forensics elevation to primary analytical dimension
- NLP signals: MD&A tone shift, risk factor evolution, readability

**Key items from original P1/P2 that land here:**
- 1a: Temporal change detection engine
- 1b: Montier C-Score, enhanced Sloan
- 1c-f: NT filing, recidivist, short seller, non-GAAP
- 2a-g: MD&A tone, risk factor evolution, Dechow F-Score, FIS, revenue quality, CAM, whistleblower
- 2h-j: Executive forensics pipeline

### Phase 27: Peril Mapping & Bear Case Framework (Layer 4)

**What gets built:**
- 7 plaintiff lens assessment (probability + severity per lens per company)
- Bear case construction from 7 templates using actual analysis
- Settlement prediction model (5-step framework from game theory research)
- Frequency/severity modeling: filing probability × expected loss
- Tower positioning intelligence
- Mispricing signal detection
- Plaintiff firm intelligence

**Key items from original P1/P2/P3 that land here:**
- 1g: Settlement prediction (5-step framework)
- 2k-m: Mispricing, tower positioning, plaintiff firm
- 3a: Bear case narrative generator
- 3l: Defense cost erosion modeling

### Phase 28: Presentation Layer & Context-Through-Comparison (Layer 5)

**What gets built:**
- Context-through-comparison engine: every metric answers "compared to what?"
- Issue-driven density: thin worksheet for clean, thick for problematic
- 4-tier display: Customary → Objective → Relative → Subjective
- Underwriter education levels: What IS → What COULD BE → What to ASK
- Meeting prep from actual analysis (not templates)
- Structured peer comparison framework

**Key items from original P1/P2/P3 that land here:**
- 1h: Context-through-comparison engine
- 2n: Underwriter education Level 2
- 3b: Structured peer comparison
- 3m: Company-specific meeting prep generator

### Existing Phases (Renumbered)

- **Phase 29** (was 25): Pricing Model Calibration & Benchmark Ingestion
- **Phase 30** (was 26): Intelligence Augmentation & Feedback Loops

### Priority 4 items deferred to Phase 30+

All Priority 4 items from the original roadmap remain in the Future/Evaluate category. See Appendix E for the full list.

### Priority 2: Next Tier (Weeks 5-10)

| # | Item | Effort | Value | Dependency |
|---|------|--------|-------|------------|
| 2a | **MD&A tone shift analysis** | 3-5 days | HIGH -- single highest-value NLP signal | LLM extraction enhancement; prior year filing |
| 2b | **Risk factor evolution tracking** | 3-5 days | HIGH -- directly maps to plaintiff discovery | LLM extraction; prior year Item 1A |
| 2c | **Dechow F-Score (Model 1)** | 2-3 days | VERY HIGH -- trained on SEC enforcement data | XBRL financial data |
| 2d | **Financial Integrity Score (composite)** | 3-4 days | HIGH -- unified financial forensics metric | Models from P1 and P2 |
| 2e | **Revenue Quality Score** | 3-4 days | HIGH -- revenue manipulation most common fraud type | XBRL financial data |
| 2f | **Auditor CAM change detection** | 2-3 days | MEDIUM-HIGH -- new CAMs signal auditor concerns | LLM extraction from 10-K auditor report |
| 2g | **Whistleblower/qui tam language detection** | 1-2 days | HIGH (when present) -- strong leading indicator | Keyword extraction from Items 1A, 3, footnotes |
| 2h | **Executive forensics: person extraction** | 3-5 days | CRITICAL -- foundation for shadiness score | EdgarTools DEF 14A / 10-K parsing |
| 2i | **Executive forensics: SEC SALI + EFTS search** | 3-5 days | CRITICAL -- highest-value executive signal | Playwright + REST API |
| 2j | **Executive forensics: Individual Risk Score** | 2-3 days | CRITICAL -- the underwriter's top priority | Scoring framework on extracted data |
| 2k | **Mispricing signal detection** | 3-5 days | HIGH -- cost per $M of market cap, premium-to-DDL ratio, governance-price disconnect | User-input premium data + risk score |
| 2l | **Tower positioning intelligence** | 2-3 days | HIGH -- game theory optimal position by risk profile | Risk profile + tower economics model |
| 2m | **Plaintiff firm intelligence** | 1-2 days | MEDIUM -- track appointed lead counsel; calibrate severity by firm | Stanford SCAC + web search |
| 2n | **Underwriter education: Level 2 (What COULD BE)** | 3-5 days | HIGH -- peer case studies, industry claims context, "no claims" explanation | Peer SCA data + Layer 2 knowledge |

**Total Priority 2 effort: ~35-55 days**

### Priority 3: Later (Weeks 11-16)

| # | Item | Effort | Value | Dependency |
|---|------|--------|-------|------------|
| 3a | **Bear case narrative generator** | 5-8 days | HIGH -- transforms worksheet from checklist to tool | All P1/P2 signals as inputs |
| 3b | **Structured peer comparison framework** | 5-8 days | MEDIUM -- answers underwriter's first question | Peer identification algorithm + market data |
| 3c | **SEC comment letter analysis** | 3-5 days | MEDIUM-HIGH -- topic, escalation, response quality | EDGAR CORRESP filings |
| 3d | **Caremark mission-critical compliance assessment** | 3-4 days | HIGH for regulated industries | Proxy + 10-K + regulatory history |
| 3e | **Executive forensics: CourtListener + SCAC search** | 3-5 days | HIGH -- federal court + SCA at prior companies | REST API + Playwright |
| 3f | **Executive forensics: Board aggregate score** | 1-2 days | HIGH -- weighted aggregate of individual scores | Individual scores from P2 |
| 3g | **Readability manipulation / Fog Index change** | 2-3 days | MEDIUM-HIGH -- straightforward text metrics | 10-K text analysis |
| 3h | **8-K filing pattern analysis** | 2-3 days | MEDIUM-HIGH -- frequency, timing, item types | EDGAR 8-K metadata |
| 3i | **Altman Z-Score zone + insolvency D&O exposure** | 2-3 days | MEDIUM -- enhances existing distress checks | Existing financial data + zone classification |
| 3j | **Boilerplate/stickiness detection** | 2-3 days | MEDIUM -- risk factors unchanged despite events | Consecutive 10-K comparison |
| 3k | **Market cycle awareness module** | 3-5 days | MEDIUM -- late soft / early hardening / hard / post-hard indicators | Layer 1 market intelligence data |
| 3l | **Defense cost erosion modeling** | 2-3 days | MEDIUM -- estimated defense costs vs. primary limits; excess attachment probability adjustment | Defense cost model + tower structure |
| 3m | **Company-specific meeting prep generator** | 3-5 days | HIGH -- Level 3 (What to ASK) questions from actual analysis, not templates | All P1/P2 signals + bear case output |
| 3n | **Settlement scenario heat map** | 2-3 days | MEDIUM -- visual DDL scenarios with settlement ranges by case type | DDL computation + settlement model |

**Total Priority 3 effort: ~40-60 days**

### Priority 4: Future / Evaluate (Months 4+)

| # | Item | Effort | Notes |
|---|------|--------|-------|
| 4a | Earnings call transcript acquisition + deception analysis | 8-10 days | Blocked by transcript data source |
| 4b | FinBERT topic-driven sentiment analysis | 5-8 days | Evaluate whether LLM extraction suffices |
| 4c | Board interlock network + fraud contagion detection | 8-12 days | Requires graph database infrastructure |
| 4d | Benford's Law analysis | 3-4 days | Screening tool; lower priority than models |
| 4e | Lev-Thiagarajan 12 fundamental signals | 3-5 days | Signals 9-12 need text extraction |
| 4f | Executive forensics: FINRA BrokerCheck, PACER, judyrecords | 5-8 days | Additional sources beyond core |
| 4g | Employee sentiment tracking (Glassdoor) | 5-8 days | Requires scraping infrastructure |
| 4h | Patent filing pattern analysis vs. R&D narrative | 3-5 days | USPTO API; relevant for tech/pharma |
| 4i | Lobbying spend change detection | 2-3 days | OpenSecrets.org API; niche signal |
| 4j | Government contract monitoring (FPDS.gov) | 3-5 days | Relevant for defense/healthcare |
| 4k | Supply chain cross-verification (customer SEC filing cross-reference) | 5-8 days | High value but labor-intensive |
| 4l | EDGAR download pattern analysis | 10+ days | Terabytes of log data; marginal value |
| 4m | Allegation pathway restructuring (map all checks to claim types) | 10-15 days | Full architectural change |
| 4n | Layer 1 pricing database (quote/binder ingestion) | 15-20 days | Foundation for market intelligence; requires data partnership or manual entry |
| 4o | Layer 1 settlement outcome database | 10-15 days | Feed Cornerstone regression calibration; track predicted vs. actual |
| 4p | Layer 2 continuous calibration engine | 10-15 days | Compare predicted outcomes to actual; auto-adjust scoring weights |
| 4q | Third-party litigation funding detection | 3-5 days | TPLF involvement signals more aggressive plaintiff strategy; 10% CAGR growth |
| 4r | Adverse selection detection (tower buying behavior) | 5-8 days | Companies buying tall towers may have risk profiles that justify them |
| 4s | Reinsurance market signal tracking | 3-5 days | Reinsurer pricing is a leading indicator of primary market adequacy |

---

## 12. What NOT to Build

### Things That Sound Good But Aren't Worth It

**1. Point probability litigation prediction model.**
Attempting to predict the exact probability of a lawsuit is overfit to historical data. The system should identify conditions that make a lawsuit more likely and quantify their severity. The current tier framework (WIN through NO_TOUCH with probability ranges) is the right level of precision. A model that says "37.2% probability of SCA filing" is false precision.

**2. Social media sentiment scoring.**
The noise-to-signal ratio is too high. Social media occasionally contains early signals (e.g., Reddit posts about product quality) but the cost of systematically monitoring and filtering social media exceeds the value. Web search for news coverage is sufficient. Exception: Glassdoor employee reviews (structured, targeted, proven predictive value) may be worth building later (Priority 4).

**3. Full Modified Jones Model with peer regression.**
The Modified Jones Model is the academic gold standard for discretionary accruals, but it requires cross-sectional regression across industry peers. The Dechow F-Score captures similar information without requiring the peer panel infrastructure. The Jones Model is an academic tool, not a production tool.

**4. Real-time monitoring dashboard (for now).**
Extending from one-time analysis to continuous monitoring is valuable but is a different product. The current sprint should focus on making the one-time analysis excellent. Real-time monitoring is a future phase.

**5. EDGAR download log analysis.**
The data exists (terabytes of log files showing who downloaded what filings) but the infrastructure cost is massive and the IP anonymization limits usefulness. The signal (someone is investigating this company) is interesting but not actionable enough to justify the investment.

**6. Automated underwriting recommendations.**
The system should never output "write this risk" or "decline this risk." It provides risk assessment to support human underwriting decisions. The underwriter's judgment, informed by the system's analysis, is the decision. Game theory insights (tower positioning, mispricing signals, market cycle) are presented as intelligence, not directives. The system says "this risk profile historically performs best in low excess position" -- not "write low excess."

**7. Credit default swap (CDS) spread monitoring.**
CDS data is mostly behind paid terminals (Bloomberg, ICE). Company-specific CDS data has limited free availability. The credit signal is interesting but not accessible within the $2.00/company budget.

**8. Satellite imagery verification.**
Hindenburg uses this to verify facilities exist. It's powerful but requires image analysis infrastructure and is relevant only for a small subset of companies (those claiming physical assets in remote locations). Not worth building into the automated system.

### Data Sources That Are Too Expensive or Unreliable

| Source | Why Not Worth It |
|--------|-----------------|
| LexisNexis/Westlaw | Enterprise pricing; duplicates what CourtListener/PACER provide for federal cases |
| Bloomberg Terminal | $$$$ per month; duplicates S&P Capital IQ which user already has |
| ISS/Glass Lewis data feed | $$$ enterprise; proxy bios provide most of the same board data |
| UniCourt (comprehensive state courts) | Marginal improvement over judyrecords for most executives |
| Thinknum Alternative Data (job postings) | Expensive; Glassdoor reviews are free and more directly predictive |

### Models That Overfit or Aren't Actionable

| Model | Issue |
|-------|-------|
| Graph Neural Network fraud detection (FraudGCN) | Requires massive training data, custom ML infrastructure, and produces opaque predictions an underwriter can't explain |
| LSTM temporal models | Academic frontier; the temporal change detection engine (simple YoY/QoQ deltas) captures 80% of the value at 5% of the complexity |
| Hybrid Bayesian-LightGBM | Overengineered for the use case; ensemble models require retraining and produce predictions the underwriter can't interrogate |

---

## Appendix A: Check-to-Lens Mapping Density

The following table shows how many "who's suing" lenses each major check category maps to. Higher density = higher value checks.

| Check Category | SH | REG | CUST | COMP | EMPL | CRED | GOV | Lens Count | Value |
|---------------|----|----|------|------|------|------|-----|------------|-------|
| Restatement/audit issues | X | X | | | X | X | | 4 | HIGHEST |
| Executive forensics | X | X | | | X | X | X | 5 | HIGHEST |
| Insider trading patterns | X | X | | | | X | | 3 | VERY HIGH |
| Whistleblower disclosures | X | X | | | X | | | 3 | VERY HIGH |
| Cybersecurity breach/governance | X | X | X | | | | | 3 | VERY HIGH |
| Financial distress signals | X | | | | | X | | 2 | HIGH |
| Revenue quality forensics | X | X | | | | | | 2 | HIGH |
| Short seller activity | X | | | | | | | 1 | HIGH (strong predictor) |
| Guidance misses | X | | | | | | | 1 | HIGH (strong predictor) |
| FCPA geographic risk | X | X | | | | | X | 3 | HIGH |
| Caremark oversight failure | X | X | | | | | | 2 | HIGH |
| Board composition (basic) | X | | | | | | | 1 | MODERATE |
| ESG/climate commitments | X | X | X | | | | | 3 | LOW-MODERATE (declining) |
| Board meeting frequency | X | | | | | | | 1 | LOW |
| Settlement prediction / DDL | X | | | | | X | | 2 | VERY HIGH (game theory) |
| Mispricing signals | X | | | | | | | 1 | HIGH (pricing intelligence) |
| Tower positioning | X | | | | | X | | 2 | HIGH (game theory) |
| Company description | | | | | | | | 0 | DISPLAY ONLY |
| Market cap / revenue / employees | | | | | | | | 0 | BASELINE PARAMETER (but with context-through-comparison) |

SH = Shareholders, REG = Regulators, CUST = Customers, COMP = Competitors, EMPL = Employees, CRED = Creditors, GOV = Government

---

## Appendix B: ESG/Climate Disposition

Per user feedback, ESG/Climate litigation (originally Pathway 8 in the knowledge audit) should be downgraded. The data supports this:

- Global greenwashing cases down 12% YoY (first decline in 6 years)
- Banking/financial services greenwashing down 20% YoY
- Companies are "greenhushing" (reducing ESG communications to avoid litigation)
- SEC climate disclosure rule suspended and defense abandoned
- Anti-ESG backlash is now the larger risk vector (red state AG lawsuits)

**Disposition:**
- Maintain ~3 ESG checks as CONTEXT/DISPLAY (not scored):
  - EMERGING.ESG.dated_targets: Specific dated emissions targets without disclosed progress
  - EMERGING.ESG.supply_chain_due_diligence: Conflict mineral / forced labor exposure
  - EMERGING.ESG.anti_esg_backlash: Risk from BOTH sides (over-claim and anti-ESG)
- Remove ESG from decision-driving scoring
- If a company has specific, dated ESG commitments approaching their deadline with no progress, flag as a bear case element (but not a scored risk factor)

---

## Appendix C: Market Cap Inflation Impact on Settlement Estimates

The user identified that historical settlement averages in nominal dollars underestimate future severity because market caps have inflated 3-4x.

**Evidence:**
- 2025 total DDL: $694B (ALL-TIME RECORD, 62% increase over 2024)
- Average DDL per filing nearly doubled vs. 1997-2023 historical average
- Settlement/DDL ratio remains stable at ~1.1%
- Therefore: same filing rate + same allegation quality + 3-4x larger DDL = 3-4x larger settlements

**System implication:**
- Settlement estimation models must use CURRENT market cap, not historical averages
- The DDL computation (stock drop x shares outstanding) automatically adjusts for cap inflation
- Historical settlement ranges (e.g., "$5-15M for small-cap") should be indexed to current market cap tiers
- The inherent risk model's market cap tier definitions (Section 5.2) are calibrated to 2026 levels

---

## Appendix D: Source Document Index

| Document | Lines | Primary Contribution |
|----------|-------|---------------------|
| 24-KNOWLEDGE-AUDIT.md | 928 | 8 liability pathways, 5 structural gaps, 10 NLP signals, bear case templates, check architecture proposal |
| NON_SCA_CLAIMS_RESEARCH.md | ~700 | Derivative suits (Caremark trends, Boeing $237.5M), regulatory enforcement, bankruptcy D&O, employment claims, business complexity, emerging trends |
| EXECUTIVE_FORENSICS_RESEARCH.md | 771 | Data sources (15+ searchable databases), shadiness score framework, board composition risk, implementation plan |
| RECENT_CLAIMS_ANALYSIS.md | 654 | 2022-2026 filing/settlement trends, DDL records, case studies (SMCI, CrowdStrike, Blue Owl, Tempus AI, AppLovin), rising/declining claim types |
| CUTTING_EDGE_SIGNALS.md | 1,267 | 35 novel signals: deception detection, readability manipulation, sentiment divergence, filing patterns, Benford's Law, short seller playbook, Hindenburg methodology |
| FORENSIC_ACCOUNTING_MODELS.md | 1,245 | 10 quantitative models (Beneish, Dechow, Montier, Sloan, Jones, Lev-Thiagarajan, Benford, Cash Flow Quality, Revenue Quality, Audit Risk), Financial Integrity Score design |
| GAME_THEORY_PRICING.md | ~844 | Settlement game theory (Baker & Griffith), plaintiff attorney economics, insurance tower dynamics (free rider problem, defense cost erosion), pricing inefficiencies (9 types), mispricing signals, settlement prediction framework (Cornerstone regression), defense cost estimation, market cycle analysis, tower positioning intelligence, decision framework |

---

## Appendix E: Future/Research Checks (Not Yet Implementable)

Per the "Nothing Empty" principle, the following proposed checks have been moved out of the active check inventory because they lack a concrete, implementable data source, acquisition path, or computation today. They remain valuable and should be promoted to active status when their data source becomes available.

| Check ID | Name | Blocking Issue | Promotion Condition |
|----------|------|---------------|-------------------|
| EXEC.BOARD.interlock_fraud_contagion | Board interlock with company that had fraud | Requires graph database infrastructure to map board networks across all public companies | Build graph DB from DEF 14A parsing; estimated P4 effort |
| NLP.MDA.forward_backward_ratio | Forward vs. backward-looking language balance | Requires validated NLP model for forward/backward classification; LLM extraction may suffice but unvalidated | Validate LLM extraction accuracy on labeled corpus |
| NLP.DISC.kitchen_sink_quarter | Quarter with multiple large write-downs + guidance reset | Definition of "kitchen sink" is subjective; needs threshold calibration from historical examples | Calibrate thresholds against 50+ historical examples |
| EMERGING.AI.washing_indicator | AI revenue claims vs. actual AI-derived revenue | "AI-derived revenue" has no standard definition; companies do not consistently disclose this | SEC mandates AI revenue disclosure OR develop heuristic from segment data |
| REG.CFPB.complaint_trend | CFPB consumer complaint volume trajectory | CFPB complaint database API exists but bulk download/trend computation requires infrastructure not yet built | Build CFPB API integration |
| BIZ.COMPLEX.rev_rec_complexity | Revenue recognition policy complexity score | "Complexity" scoring requires NLP evaluation of ASC 606 disclosures; no validated metric exists | Develop and validate complexity rubric against auditor assessments |
| REG.PRIVACY.state_law_exposure | Number of applicable state privacy laws | Mapping company operations to specific state privacy law applicability requires detailed operational geography | Build state privacy law applicability matrix + map to 10-K operations disclosure |
| GOV.INCORP.reincorporation_proposal | Pending reincorporation proposal | Low-frequency event; no systematic data source for pending proposals beyond 8-K/proxy monitoring | Add to 8-K/proxy extraction pipeline |
| MKT.PRICE.cost_per_mcap | Cost per $M of Market Cap | Requires user-input premium data; not publicly available | Activate when user provides premium data |
| MKT.PRICE.premium_to_ddl | Premium-to-DDL Ratio | Requires user-input premium data | Activate when user provides premium data |
| MKT.PRICE.rate_per_million | Rate per $M of Limit | Requires user-input premium + program structure data | Activate when user provides program data |

**Total checks in Future/Research: 11**
**Active check inventory: ~453 (464 proposed - 11 deferred)**

These checks are tracked separately and reviewed quarterly for promotion. When a data source becomes available or the blocking infrastructure is built, the check moves to the active inventory with a concrete implementation plan.

---

## Appendix F: Game Theory Integration Map

This appendix shows where game theory concepts from the GAME_THEORY_PRICING.md research are integrated throughout the framework.

| Game Theory Concept | Framework Section | How It's Used |
|--------------------|--------------------|---------------|
| Settlement prediction model (5-step) | Section 5.3 | DDL computation, settlement range estimation, probability-weighted expected loss |
| Plaintiff attorney economics (EV calculation) | Section 5.3 | Filing viability threshold ($50M DDL), plaintiff firm identity as severity signal |
| Baker & Griffith policy limits phenomenon | Section 5.3 (Step 4), Section 9 (Template 7) | Settlements gravitate to insurance limits; limits partially determine settlement |
| Insurance tower dynamics (free rider, defense erosion) | Section 10.2 (MKT.TOWER checks), Section 11 | Defense cost erosion modeling, tower positioning intelligence |
| Pricing inefficiencies (9 types) | Section 10.2 (MKT.PRICE/MISMATCH checks) | Mispricing signal detection: anchoring, soft market, market cap lag, etc. |
| Market cycle analysis | Section 10.2 (MKT.CYCLE checks), Section 11 | Market cycle position indicator, adverse development trap awareness |
| Case characteristics multipliers | Section 5.3 (Step 3), Section 9 | Settlement adjustment for restatement (1.3-1.8x), SEC action (1.5-2.0x), etc. |
| Defense cost estimation by stage | Section 5.3 | Defense cost estimates from Stanford data ($1.5M through MTD to $20-30M trial) |
| Adverse selection in tower construction | Section 12 (What NOT to Build, item 4r) | Companies buying tall towers may signal higher risk |
| Third-party litigation funding | Section 11 (Priority 4q) | TPLF involvement signals more aggressive strategy; 10% CAGR |
| Social inflation / nuclear verdicts | Section 9 (bear case templates), Section 12 | Consumer-facing, large employee base, politically sensitive industries |
| Plaintiff firm concentration | Section 5.3 | Bernstein Litowitz ($120.3M avg) vs. Robbins Geller ($47.5M avg) |
| PSLRA impact on filing economics | Section 5.3 | ~50% MTD dismissal rate shapes entire settlement dynamic |
| F1 counterbalance | Section 4.1 (F1 Weighting Note), Section 9 (Template 6) | "No claims but high risk" scenario prevents clean history from masking exposure |
| Mediation dynamics | Section 5.3 | Specialist mediators calibrate to available insurance; anchor effect |

---

## Appendix G: Three-Layer Architecture Detail

### Layer 1: Market Intelligence (Company-Independent, Always Running)

This layer accumulates market-wide intelligence that informs every company analysis. It is company-independent and runs continuously.

**Data Feeds:**

| Feed | Source | Update Frequency | What It Provides |
|------|--------|-----------------|-----------------|
| Pricing database | User-input quotes, binders, tower structures | Per-transaction | Peer premium benchmarks, rate-on-line by layer, cost per $M of market cap |
| SCA filing tracker | Stanford SCAC + EDGAR | Weekly | Filing frequency by sector, DDL trends, allegation type distribution |
| Settlement outcomes | Cornerstone Research annual + interim reports | Quarterly | Settlement percentages by DDL tier, case characteristics multipliers |
| Defense cost benchmarks | Stanford Securities Litigation Analytics | Annually | Defense costs by litigation stage, jurisdiction, case complexity |
| Market cycle indicators | TransRe, Woodruff Sawyer, AM Best, Fitch | Quarterly | Rate change trends, capacity dynamics, loss ratio development |
| Plaintiff firm activity | Stanford SCAC, ISS SCAS | Quarterly | Which firms are filing, lead counsel appointments, average settlement by firm |
| Regulatory enforcement trends | SEC SALI, DOJ press releases, state AG databases | Monthly | Enforcement volume by agency, industry targets, individual actions |
| Industry baseline filing rates | Stanford SCAC + NAIC | Annually (recalibrated) | Sector-specific filing frequency, severity, and allegation type baselines |

**Self-Calibration:** Layer 1 data feeds self-calibrate. As more pricing data is ingested, peer benchmarks become more accurate. As more settlement outcomes are tracked, the Cornerstone regression parameters are refined. Industry baselines update as new filing data accumulates.

### Layer 2: Knowledge Engine (Continuously Improving)

This layer contains the system's intelligence -- what to look for, how to score it, and how to present it. It improves with every analysis.

**Components:**

| Component | Content | How It Improves |
|-----------|---------|-----------------|
| Check library | ~453 active checks with thresholds, data sources, computations | Thresholds calibrated from outcome tracking; new checks added from research |
| Forensic models | Beneish, Dechow, Montier, Sloan, Financial Integrity Score | Model weights calibrated against actual fraud/restatement outcomes |
| Bear case templates | 7 allegation templates + company-specific generator | Templates refined from actual SCA complaint analysis |
| Industry playbooks | 10 verticals with sector-specific checks and thresholds | Playbooks enriched from sector-specific loss experience |
| NLP extraction prompts | ~20 extraction targets for 10-K, 10-Q, proxy, 8-K | Prompts refined from extraction quality review |
| Executive forensics pipeline | 10 data sources, individual risk score, aggregate score | Source coverage expanded; scoring calibrated from actual enforcement data |
| Scoring model | 10-factor model with sub-factors and CRF gates | Weights adjusted from predicted-vs-actual outcome comparison |

**Feedback Loop:** Every underwriter correction, annotation, or override feeds back into Layer 2. If an underwriter consistently overrides a check's output, the check's threshold or weight is flagged for recalibration.

### Layer 3: Company Analysis (Per-Ticker, On-Demand)

This layer is the per-company analysis pipeline. It uses Layers 1 and 2 to produce the worksheet.

**Pipeline:**
```
RESOLVE → ACQUIRE → EXTRACT → ANALYZE → SCORE → BENCHMARK → RENDER
   |                                                              |
   +--- Uses Layer 2 for what to look for --------+              |
   +--- Uses Layer 1 for context and pricing ------+              |
   |                                                              |
   +--- Results feed BACK into Layers 1 and 2 <---+--------------+
```

**Continuous Learning Effect:**
- Company #1 uses only pre-loaded Layer 1 data (industry baselines, historical averages)
- Company #10 benefits from 9 prior analyses refining extraction quality and check calibration
- Company #50 has significantly better peer benchmarks, more accurate settlement predictions, and refined NLP extraction prompts
- Company #100+ operates with a self-calibrated knowledge base that improves with every run

This is the system's competitive moat: it gets smarter with use.
