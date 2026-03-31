# Phase 26: Check Reorganization & Analytical Engine Enhancement - Research

**Researched:** 2026-02-11
**Domain:** D&O Underwriting Check Architecture, Signal Classification, Analytical Engine Design
**Confidence:** HIGH (based on deep analysis of existing codebase + comprehensive unified framework document)

## Summary

Phase 26 implements Layer 3 of the five-layer analysis architecture defined in `24-UNIFIED-FRAMEWORK.md`. The core task is reorganizing 359 existing checks from their current flat, section-based organization into a multi-dimensional classification system (4 dimensions: worksheet section, plaintiff lens, signal type, check category), while simultaneously adding ~90 new checks for temporal change detection, financial forensics composites, executive forensics, and NLP signals.

The current system has a functional but simplistic analytical engine: checks.json defines 359 checks with section/pillar/tier metadata, the check_engine.py evaluates them against ExtractedData via check_mappers.py, and results feed into a 10-factor scoring model (factor_scoring.py). The critical gap is that checks have NO plaintiff lens mapping, NO signal type classification, NO distinction between "decision-driving" and "context/display", and 91 of 359 checks have empty factor mappings -- meaning they execute but don't influence scoring at all.

**Primary recommendation:** Execute in 4 waves: (1) Check reclassification and metadata enrichment in checks.json + knowledge store, (2) Temporal change detection engine + financial forensics composites, (3) Executive forensics pipeline as a new analytical dimension, (4) NLP signal implementation + factor restructuring to absorb new sub-factors.

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | Models for new check metadata, forensic scores, temporal results | Already used throughout; strict typing |
| SQLAlchemy 2.0 | 2.x | Knowledge store Check model extension | Already used for knowledge store |
| Alembic | 1.x | DB migration for new Check columns | Already used for schema migrations |
| httpx | 0.x | HTTP for any new data source (CourtListener, SEC SALI) | Already used; project standard |
| instructor | 1.x | LLM extraction for NLP signals | Already used for filing extraction |

### Supporting (New for Phase 26)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| textstat | 0.7.x | Readability metrics (Gunning Fog, Flesch) | NLP.MDA.readability_change check |
| None additional needed | -- | Temporal analysis, forensics, executive scoring all implementable with existing stack | -- |

**Installation:**
```bash
uv add textstat
```

## Architecture Patterns

### Current Architecture (What Exists)

```
src/do_uw/
  brain/
    checks.json          # 359 checks, flat structure, section-based
    scoring.json         # 10-factor model (F1-F10), rules, tiers
    patterns.json        # 17+ composite patterns
    red_flags.json       # 11 CRF gates
  stages/
    analyze/
      __init__.py        # AnalyzeStage - loads checks, executes, aggregates
      check_engine.py    # execute_checks(), evaluate_check() dispatcher
      check_mappers.py   # map_check_data() - routes by section (1-6)
      check_results.py   # CheckResult model, CheckStatus enum
    score/
      __init__.py        # ScoreStage - 16-step pipeline
      factor_scoring.py  # score_all_factors() - F1-F10
      factor_rules.py    # rule_matches() per factor
      factor_data.py     # get_factor_data() - data for each factor
      pattern_detection.py
      red_flag_gates.py
      severity_model.py
      tier_classification.py
      allegation_mapping.py
  knowledge/
    models.py            # SQLAlchemy Check model with lifecycle
```

### Target Architecture (What to Build)

```
src/do_uw/
  brain/
    checks.json          # ENHANCED: +4 new fields per check (category, lenses, signal_type, hazard_or_signal)
  config/
    check_classification.json  # NEW: master classification lookup
    forensic_models.json       # NEW: FIS, RQS thresholds and weights
    temporal_thresholds.json   # NEW: change detection thresholds
    executive_scoring.json     # NEW: individual risk score weights
  stages/
    analyze/
      __init__.py              # ENHANCED: wire temporal + forensic + executive
      check_engine.py          # ENHANCED: support new threshold types
      check_mappers.py         # ENHANCED: new section 7-8 mappers
      check_results.py         # ENHANCED: add category, lenses to CheckResult
      temporal_engine.py       # NEW: QoQ/YoY change detection
      temporal_metrics.py      # NEW: metric computation helpers (split)
      forensic_composites.py   # NEW: FIS, RQS, CFQS computation
      forensic_models.py       # NEW: Dechow F-Score, Montier C-Score
      executive_forensics.py   # NEW: individual risk scoring
      executive_data.py        # NEW: executive data acquisition bridge
      nlp_signals.py           # NEW: tone shift, readability, risk factor evolution
    score/
      factor_scoring.py        # ENHANCED: new sub-factors under F3, F5, F8, F9
      factor_rules.py          # ENHANCED: new rules for enhanced factors
      factor_data.py           # ENHANCED: new data sources for factors
  models/
    forensic.py                # NEW: FinancialIntegrityScore, RevenueQualityScore, etc.
    executive_risk.py          # NEW: IndividualRiskScore, BoardAggregateScore
    temporal.py                # NEW: TemporalSignal, TemporalClassification
```

### Pattern 1: Multi-Dimensional Check Classification
**What:** Each check carries 4 classification dimensions as metadata (not computed at runtime).
**When to use:** Every check in checks.json.
**Example:**
```json
{
  "id": "FIN.ACCT.beneish_m_score",
  "name": "Beneish M-Score Manipulation Indicator",
  "section": 3,
  "pillar": "P1_WHAT_WRONG",
  "category": "DECISION_DRIVING",
  "plaintiff_lenses": ["SHAREHOLDERS", "REGULATORS"],
  "signal_type": "FORENSIC",
  "hazard_or_signal": "SIGNAL",
  "factors": ["F3"],
  "tier": 1,
  "threshold": { "type": "tiered", "red": "> -1.78", "yellow": "> -2.22" }
}
```

### Pattern 2: Temporal Change Detection
**What:** A `TemporalAnalyzer` that takes multi-period data and produces IMPROVING/STABLE/DETERIORATING/CRITICAL classifications.
**When to use:** For the ~10 temporal checks (FIN.TEMPORAL.*) that detect QoQ and YoY changes.
**Example:**
```python
class TemporalSignal(BaseModel):
    metric_name: str
    periods: list[TemporalDataPoint]  # 4-8 quarters
    classification: TemporalClassification  # IMPROVING/STABLE/DETERIORATING/CRITICAL
    consecutive_adverse_periods: int
    magnitude_pct: float  # total change over period
    evidence: str

def analyze_temporal_metric(
    metric_name: str,
    values: list[float],
    periods: list[str],
    direction: Literal["higher_is_worse", "lower_is_worse"],
    threshold_consecutive: int = 3,
) -> TemporalSignal:
    """Detect directional trends in multi-period data."""
```

### Pattern 3: Composite Forensic Scores
**What:** Unified 0-100 scores that combine multiple sub-models into actionable composites.
**When to use:** Financial Integrity Score, Revenue Quality Score, Cash Flow Quality Score.
**Example:**
```python
class FinancialIntegrityScore(BaseModel):
    overall_score: float  # 0-100, higher = more integrity
    zone: Literal["HIGH_INTEGRITY", "ADEQUATE", "CONCERNING", "WEAK", "CRITICAL"]
    manipulation_detection: SubScore  # Beneish + Dechow + Montier
    accrual_quality: SubScore  # Enhanced Sloan + intensity + NI/CFO divergence
    revenue_quality: SubScore  # DSO + AR divergence + Q4 concentration + deferred rev
    cash_flow_quality: SubScore  # QoE + CCE + CFA
    audit_risk: SubScore  # MW + auditor changes + restatements + GC
```

### Pattern 4: Executive Forensics as Independent Dimension
**What:** Person-level risk scoring separate from governance factor, with weighted board aggregate.
**When to use:** EXEC.* checks, feeding into F9 as sub-factor.
**Example:**
```python
class IndividualRiskScore(BaseModel):
    person_name: str
    role: str
    role_weight: float  # CEO=3.0, CFO=2.5, etc.
    total_score: float  # 0-100
    prior_litigation: float  # 0-25
    regulatory_enforcement: float  # 0-25
    prior_company_failures: float  # 0-15
    insider_trading_patterns: float  # 0-10
    negative_news: float  # 0-10
    tenure_stability: float  # 0-5
    time_decay_applied: bool
    findings: list[str]
    sources: list[str]
```

### Anti-Patterns to Avoid
- **Scoring in ANALYZE stage:** Check evaluation determines TRIGGERED/CLEAR/SKIPPED. Factor scoring stays in SCORE stage. Do not mix.
- **New checks without data sources:** Per "Nothing Empty" principle (Section 1.6 of framework), every new check must have a real data path. Checks without implementable data go to FUTURE/RESEARCH.
- **Overengineering temporal analysis:** Simple consecutive-period counting is 80% of value. Do not build LSTM or complex time-series models.
- **Breaking the 500-line rule:** New modules must be split proactively. The temporal engine, forensic composites, and executive forensics each need 2+ files.

## Current Check Inventory: Complete Analysis

### Check Distribution by Section Prefix
| Prefix | Count | Section | Examples |
|--------|-------|---------|----------|
| BIZ.* | 58 | 1 (Company Profile) | Classification, size, model, competition, dependencies |
| STOCK.* | 35 | 2 (Market) | Price, short interest, insider trading, patterns, valuation |
| FIN.* | 32 | 3 (Financial) | Accounting, debt, guidance, liquidity, profitability |
| LIT.* | 56 | 4 (Litigation) | SCA, regulatory, other litigation |
| GOV.* | 90 | 5 (Governance) | Board, exec, pay, rights, activists, effectiveness |
| FWRD.* | 88 | 6 (Forward-Looking) | Events, warnings, narrative, disclosure, macro |
| **Total** | **359** | | |

### Check Execution Profile
| Metric | Count |
|--------|-------|
| AUTO execution mode | 351 |
| FALLBACK_ONLY | 3 |
| MANUAL_ONLY | 3 |
| SECTOR_CONDITIONAL | 2 |
| Checks with empty `factors` field | 91 (25%) |
| Checks with `tier=1` (highest) | 23 |
| Checks with `tier=2` | 336 |

### Threshold Type Distribution
| Type | Count | Behavior |
|------|-------|----------|
| tiered | 309 | Red/yellow/clear comparison |
| info | 19 | Always INFO status (display only) |
| percentage | 10 | Numeric percentage comparison |
| pattern | 6 | INFO -- detection deferred to SCORE |
| classification | 5 | INFO -- report classification value |
| value | 4 | Simple numeric comparison |
| count | 2 | Count-based comparison |
| boolean | 2 | True/false evaluation |
| multi_period | 1 | INFO -- complex temporal |
| search | 1 | INFO -- search-based |

### Key Finding: 91 Checks Have No Factor Mapping
These 91 checks execute and produce TRIGGERED/CLEAR/SKIPPED results but have empty `factors: []` fields, meaning they do NOT feed into any of the 10 scoring factors. This is a significant architectural gap: these checks are "orphaned" from scoring. Many are BIZ.SIZE.*, BIZ.MODEL.*, and GOV.PAY.* checks that should be classified as CONTEXT_DISPLAY (not scored). Others like FWRD.WARN.* and FWRD.EVENT.* may need factor mapping to become decision-driving.

## Double-Counting Analysis: Hazard Dimensions vs. Checks

### What Phase 25 (Hazard Profile) Will Score
Phase 25 builds the hazard profile engine with 7 categories and 47 dimensions. These assess STRUCTURAL CONDITIONS:
- H1: Business Model (complexity, regulatory intensity, geographic risk, revenue model, growth speed, etc.)
- H2: People (management experience, industry expertise, scale mismatch, key person dependency)
- H3: Financial Structure (leverage profile, cash runway, capital structure, off-balance-sheet)
- H4: Governance Structure (board independence, committee quality, anti-takeover, compensation structure)
- H5: Public Company Maturity (IPO age, index membership, analyst coverage, FPI status)
- H6: External Environment (macro, geopolitical, technology disruption, regulatory change)
- H7: Emerging/Modern (AI exposure, cyber, ESG, SPAC-specific)

### Existing Checks That Overlap with Hazard Dimensions

**HIGH overlap (structural condition checks that should migrate to hazard profile or become CONTEXT_DISPLAY):**

| Current Check | Hazard Dimension | Disposition |
|--------------|-----------------|-------------|
| BIZ.CLASS.primary/secondary | H1-01 Industry Sector Risk Tier | -> Hazard profile (Layer 2). Check becomes CONTEXT_DISPLAY. |
| BIZ.SIZE.market_cap | Classification (Layer 1) | -> Classification engine. Check becomes CONTEXT_DISPLAY. |
| BIZ.SIZE.revenue_ttm, employees | H1 exposure parameters | -> CONTEXT_DISPLAY with comparison. |
| BIZ.MODEL.revenue_type | H1-05 Revenue Model Manipulation Surface | -> Hazard profile input. Check becomes CONTEXT_DISPLAY. |
| BIZ.MODEL.revenue_segment | H1-02 Business Model Complexity | -> Hazard profile. Check becomes CONTEXT_DISPLAY. |
| BIZ.DEPEND.customer_concentration (10 checks) | H1-06 Customer/Supplier Concentration | -> Hazard profile. Some duplication within these 10 checks (~8 consolidation candidates). |
| BIZ.COMP.* (12 checks) | Partial H1-02, H1-12, H1-13 | -> Mixed: some hazard, some CONTEXT_DISPLAY. |
| BIZ.UNI.* (10 checks) | H1-03 Regulatory Intensity, H1-04 Geographic, H7 | -> Hazard profile for structural; CONTEXT_DISPLAY for display. |
| GOV.BOARD.independence, ceo_chair, size | H4 Governance Structure | -> Hazard profile provides baseline; check remains for SIGNAL detection (change from baseline). |
| GOV.RIGHTS.dual_class, voting_rights | H4-specific, H1-10 Dual-Class | -> Hazard profile. Check becomes CONTEXT_DISPLAY. |
| GOV.EXEC.* (11 checks) | H2 People & Management | -> Hazard profile for experience/tenure; SIGNAL for departures/instability. |

**MODERATE overlap (behavioral signals that reference structural conditions):**

| Current Check | Hazard Dimension | Disposition |
|--------------|-----------------|-------------|
| FIN.LIQ.*, FIN.DEBT.* | H3 Financial Structure | -> Hazard profile scores the STRUCTURE (leverage level, cash runway). Checks score the BEHAVIOR (deteriorating trajectory, covenant breach). Both needed but must not double-count. |
| GOV.PAY.* (15 checks) | H4-specific compensation structure | -> Hazard scores compensation STRUCTURE. Checks flag BEHAVIORAL anomalies (extreme outliers, trend changes). |

**NO overlap (pure behavioral signals -- these are Layer 3):**

| Current Check Category | Why No Overlap |
|-----------------------|---------------|
| STOCK.PRICE.*, STOCK.PATTERN.* | Stock movements are SIGNALS, not structural conditions |
| STOCK.SHORT.*, STOCK.INSIDER.* | Market-derived behavioral evidence |
| FIN.ACCT.* (Beneish, restatements) | Financial manipulation detection = SIGNAL |
| FIN.GUIDE.* (earnings misses) | Guidance performance = SIGNAL |
| LIT.SCA.*, LIT.REG.*, LIT.OTHER.* | Litigation events = PERIL/SIGNAL |
| FWRD.WARN.*, FWRD.EVENT.* | Forward-looking warnings = SIGNAL |
| GOV.INSIDER.* (insider trading) | Trading behavior = SIGNAL |
| GOV.ACTIVIST.* (activist campaigns) | External pressure events = SIGNAL |

### Resolution Strategy: Eliminating Double-Counting

1. **Structural condition checks** (BIZ.CLASS, BIZ.SIZE, BIZ.MODEL structural, GOV.RIGHTS structural) -> Reclassify as `CONTEXT_DISPLAY`. Their data feeds the hazard profile (Phase 25). They appear in the worksheet for display but do NOT feed into Factor scoring.

2. **Behavioral signal checks** (STOCK.*, FIN.ACCT, FIN.GUIDE, LIT.*, FWRD.WARN, GOV.INSIDER) -> Remain `DECISION_DRIVING`. These are the core of Layer 3.

3. **Mixed checks** (FIN.LIQ, FIN.DEBT, GOV.BOARD, GOV.PAY) -> Split: structural aspect feeds hazard profile, behavioral aspect (trajectory, change, anomaly) stays as scored check. Example: `FIN.DEBT.structure` = CONTEXT_DISPLAY (hazard profile scores this); `FIN.DEBT.coverage` deteriorating trajectory = DECISION_DRIVING.

4. **IES context:** After Phase 25, the Inherent Exposure Score (IES) provides the baseline. Phase 26 checks should assess "given the IES, what BEHAVIORAL evidence exists that modifies risk up or down?"

## Proposed Check Reclassification

### Category Assignments (Estimated)

| Category | Count (Current -> Proposed) | Description |
|----------|---------------------------|-------------|
| DECISION_DRIVING | 0 -> ~100 | Changes tier, triggers CRF, materially affects decision. Scored. |
| CONTEXT_DISPLAY | 0 -> ~195 | Useful information, always displayed, not scored. |
| DEPRECATED | 0 -> ~34 | Duplicate, COVID-specific, never-implementable. Remove. |
| FUTURE_RESEARCH | 0 -> ~11 | Valuable but blocked by data source constraints. |
| NEW (to build) | 0 -> ~90 | Temporal, forensic, executive, NLP, derivative, regulatory. |
| **Total Active** | **359 -> ~385** (after deprecation + new) | |

### Decision-Driving Checks by Factor (After Restructuring)

| Factor | Current Checks | Enhanced/New Sub-factors | Proposed Total |
|--------|---------------|--------------------------|----------------|
| F1 Prior Litigation (20 pts) | ~20 | DDL computation, settlement range, recidivist flag, "no claims but high risk" counterbalance | ~25 |
| F2 Stock Decline (15 pts) | ~10 | DDL as severity input, cap inflation, filing probability context | ~12 |
| F3 Restatement/Audit (12 pts) | ~6 | Dechow F-Score, Montier C-Score, MD&A tone shift, risk factor evolution, CAM changes, NT filing | ~18 |
| F4 IPO/SPAC/M&A (10 pts) | ~5 | No change needed | ~5 |
| F5 Guidance Misses (10 pts) | ~5 | Non-GAAP divergence, kitchen sink quarter, magnitude weighting | ~8 |
| F6 Short Interest (8 pts) | ~3 | Named short seller reports, report quality assessment | ~5 |
| F7 Volatility (9 pts) | ~6 | DDL exposure estimate | ~7 |
| F8 Financial Distress (8 pts) | ~10 | Temporal trajectory, Altman Z zone, zone of insolvency, creditor duty | ~15 |
| F9 Governance (6 pts) | ~15 | Executive forensics aggregate, Caremark mission-critical, derivative exposure | ~20 |
| F10 Officer Stability (2 pts) | ~5 | Departure-during-stress amplifier, CFO/CAO departure timing | ~6 |
| **Total Decision-Driving** | **~85** | | **~121** |

### New Check Categories (from Unified Framework Section 4.4)

| Category | New Checks | Priority | Key Items |
|----------|-----------|----------|-----------|
| EXEC.* (Executive Forensics) | ~20 | P1-P3 | Individual risk score, prior litigation, SEC enforcement, insider timing, board aggregate |
| FIN.FORENSIC.* | ~8 | P1-P2 | Dechow F-Score, Montier C-Score, enhanced Sloan, FIS composite |
| FIN.QUALITY.* | ~5 | P1-P2 | Revenue quality, cash flow quality, audit risk, non-GAAP divergence |
| FIN.TEMPORAL.* | ~10 | P1-P2 | Revenue deceleration, margin compression, DSO trajectory, CFO/NI divergence, working capital |
| FIN.INSOL.* | ~5 | P1-P2 | Altman Z zone, zone of insolvency, insider payments during distress |
| NLP.* | ~15 | P1-P3 | Tone shift, readability, risk factor evolution, whistleblower language, CAM changes, filing timing |
| DERIV.* | ~10 | P1-P3 | Caremark mission-critical, say-on-pay, shareholder proposals, 13D filings |
| REG.* | ~10 | P1-P2 | Recidivist enforcement, DOJ language, FCPA geographic, cyber governance |
| EMERGING.* | ~5 | P1-P2 | AI washing, short seller reports, ESG (context only) |
| FIN.DDL.* | ~2 | P2 | DDL exposure computation |
| **Total New** | **~90** | | |

## Plaintiff Lens Coverage Analysis

### Current Coverage (from Unified Framework Section 2)

| Plaintiff Lens | Current Checks | Coverage Quality | Key Gaps |
|---------------|---------------|-----------------|----------|
| Shareholders | ~120 (STOCK, FIN, LIT.SCA, partial GOV) | STRONG for SCA | WEAK: derivative, ERISA stock-drop, Section 220 |
| Regulators | ~22 (LIT.REG.*) | ADEQUATE for SEC | WEAK: DOJ/FCPA, state AG, FTC/CFPB, bank regulatory |
| Customers | ~3 (BIZ.UNI.cyber*) | WEAK | ABSENT: product recall, data privacy, AI-washing, FCA |
| Competitors | ~2 (BIZ.COMP.*) | WEAK | ABSENT: antitrust, trade secret, patent |
| Employees | ~2 (partial whistleblower) | ABSENT | ABSENT: discrimination, ERISA, wage/hour, retaliation |
| Creditors | ~10 (FIN.LIQ.*, DEATH_SPIRAL) | GOOD for distress | WEAK: zone of insolvency, insider payments, duty expansion |
| Government | ~0 | ABSENT | ABSENT: FCA, procurement fraud, ITAR, sanctions |

### Target Coverage (After Phase 26)

| Plaintiff Lens | Proposed Checks | New Checks Needed |
|---------------|----------------|-------------------|
| Shareholders | ~140 | +20 (derivative, executive forensics, temporal, NLP) |
| Regulators | ~40 | +18 (recidivist, DOJ, FCPA, state AG, cyber) |
| Customers | ~10 | +7 (cyber governance, data privacy, AI-washing) |
| Competitors | ~5 | +3 (market dominance, antitrust, trade secret) |
| Employees | ~8 | +6 (whistleblower, ERISA, sentiment, retaliation) |
| Creditors | ~18 | +8 (zone of insolvency, insider payments, duty expansion) |
| Government | ~5 | +5 (FCA, procurement, FCPA geographic) |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Readability metrics (Fog, Flesch) | Custom word-counting | `textstat` library | Handles edge cases in syllable counting, validated implementations |
| Complex time-series analysis | LSTM/ARIMA models | Simple consecutive-period counting | 80% of value at 5% of complexity per framework guidance |
| Modified Jones Model | Cross-sectional peer regression | Dechow F-Score | Captures similar info without peer panel infrastructure |
| Social media sentiment | Custom scraper/analyzer | Ignore (framework Section 12: noise-to-signal too high) | Exception: Glassdoor deferred to Phase 30 |
| Graph neural network fraud | Custom ML model | Forensic model composites (Beneish + Dechow + Montier) | Opaque predictions an underwriter can't explain |
| Earnings call transcript analysis | Custom NLP pipeline | Defer to Phase 30+ (blocked by transcript acquisition) | No free/cheap transcript source available |

## Common Pitfalls

### Pitfall 1: Double-Counting Between Hazard Profile and Checks
**What goes wrong:** A structural condition (e.g., high leverage) is scored in both the hazard profile (IES) and a check (FIN.DEBT.structure), inflating risk artificially.
**Why it happens:** Phase 25 and Phase 26 both evaluate some of the same data fields.
**How to avoid:** Clear classification rule: if a check assesses a PERSISTENT STRUCTURAL CONDITION (what IS the company), it feeds the hazard profile only. If it assesses BEHAVIORAL EVIDENCE (what is the company DOING), it's a Layer 3 check. Example: leverage level = hazard. Leverage trajectory deteriorating = check.
**Warning signs:** Same data field appearing in both hazard dimension scorer and check mapper without a clear behavioral/structural distinction.

### Pitfall 2: Checks.json Becoming Unmanageable
**What goes wrong:** Adding 90 new checks + 4 new metadata fields per check to a 9215-line JSON file makes it impossible to review or maintain.
**Why it happens:** Organic growth without restructuring.
**How to avoid:** Consider splitting checks.json by check category prefix (BIZ, FIN, STOCK, etc.) or by category (DECISION_DRIVING, CONTEXT_DISPLAY). At minimum, add structured validation that new fields are present.
**Warning signs:** checks.json exceeds 12,000 lines; manual review becomes impractical.

### Pitfall 3: Factor Score Inflation from Sub-Factor Additions
**What goes wrong:** Adding Dechow F-Score, Montier C-Score, MD&A tone shift, etc. as sub-factors to F3 causes F3 to routinely hit its 12-point cap, making it less discriminating.
**Why it happens:** New sub-factors add points without adjusting the cap or weighting.
**How to avoid:** Sub-factors should be ALTERNATIVES or AMPLIFIERS, not purely additive. If Beneish already triggers 3 points, Dechow confirming should add only 1-2 (confirmation bonus), not a full additional 3. The framework specifies this: "Models run silently. Only ISSUES get surfaced."
**Warning signs:** F3 hitting cap on >50% of companies; loss of score discrimination.

### Pitfall 4: Executive Forensics Data Acquisition Boundary
**What goes wrong:** Executive forensics checks (SEC SALI, CourtListener, BrokerCheck) require data acquisition, but data acquisition is supposed to happen in ACQUIRE stage, not ANALYZE.
**Why it happens:** The MCP boundary rule: "MCP tools are used ONLY in ACQUIRE stage."
**How to avoid:** Executive forensics data acquisition must be added to the ACQUIRE stage as a new sub-step. The ANALYZE stage only evaluates data that's already in state. The executive forensics pipeline in Phase 26 should: (1) define what data to acquire, (2) add acquisition to ACQUIRE stage, (3) add evaluation to ANALYZE stage.
**Warning signs:** Import of MCP tools or httpx in analyze/ directory files.

### Pitfall 5: NLP Signals Requiring Prior-Year Filing
**What goes wrong:** NLP checks like "MD&A tone shift YoY" and "risk factor evolution" require comparison between current and prior year filings. If prior year filing is not acquired, these checks always SKIP.
**Why it happens:** Current acquisition pipeline fetches only the most recent filing of each type.
**How to avoid:** Add prior-year 10-K acquisition to the ACQUIRE stage. Store both current and prior year. NLP checks compare the two. If prior year unavailable, gracefully degrade to INFO status with note "prior year filing not available for comparison."
**Warning signs:** NLP temporal checks showing >80% SKIPPED rate across companies.

### Pitfall 6: Breaking Existing Tests
**What goes wrong:** Modifying CheckResult model, check_mappers.py, or factor_scoring.py breaks the extensive existing test suite.
**Why it happens:** 2526+ tests exist across the project; many mock check execution and scoring.
**How to avoid:** New fields on CheckResult and checks.json should be OPTIONAL with defaults. New check categories should be additive, not replacing existing behavior. Run `pytest` after every change. New modules should have their own test files alongside the code.
**Warning signs:** Test failures in phases 6, 15, 17, 21, 23 test files.

## Code Examples

### Check Metadata Enhancement (checks.json)
```json
{
  "id": "FIN.LIQ.position",
  "name": "Liquidity Position",
  "section": 3,
  "pillar": "P1_WHAT_WRONG",
  "category": "DECISION_DRIVING",
  "plaintiff_lenses": ["CREDITORS", "SHAREHOLDERS"],
  "signal_type": "LEVEL",
  "hazard_or_signal": "SIGNAL",
  "factors": ["F8"],
  "tier": 1,
  "claims_correlation": 0.85,
  "execution_mode": "AUTO",
  "required_data": ["SEC_10K", "SEC_10Q"],
  "data_locations": { "SEC_10K": ["item_8_financials"] },
  "threshold": {
    "type": "tiered",
    "red": "<6 months runway OR revolver >80% utilized",
    "yellow": "<12 months runway OR revolver >50% utilized"
  }
}
```

### Temporal Change Detection Engine
```python
# Source: Phase 26 design based on unified framework Section 7.4
from enum import StrEnum
from pydantic import BaseModel

class TemporalClassification(StrEnum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DETERIORATING = "DETERIORATING"
    CRITICAL = "CRITICAL"

class TemporalSignal(BaseModel):
    metric_name: str
    classification: TemporalClassification
    consecutive_adverse: int
    total_change_pct: float
    evidence: str
    source_periods: list[str]

def classify_temporal_trend(
    values: list[float],
    direction: str,  # "higher_is_worse" or "lower_is_worse"
    consecutive_threshold: int = 3,
) -> TemporalClassification:
    """Classify a multi-period trend."""
    if len(values) < 2:
        return TemporalClassification.STABLE

    # Count consecutive adverse moves
    adverse_count = 0
    for i in range(1, len(values)):
        if direction == "higher_is_worse":
            if values[i] > values[i - 1]:
                adverse_count += 1
            else:
                adverse_count = 0
        else:
            if values[i] < values[i - 1]:
                adverse_count += 1
            else:
                adverse_count = 0

    if adverse_count >= consecutive_threshold + 1:
        return TemporalClassification.CRITICAL
    if adverse_count >= consecutive_threshold:
        return TemporalClassification.DETERIORATING
    # ... symmetric for improving
    return TemporalClassification.STABLE
```

### Financial Integrity Score Computation
```python
# Source: Unified framework Section 7.2
class FinancialIntegrityScore(BaseModel):
    overall_score: float  # 0-100
    zone: str  # HIGH_INTEGRITY/ADEQUATE/CONCERNING/WEAK/CRITICAL
    manipulation_detection: float  # 0-100 (30% weight)
    accrual_quality: float  # 0-100 (20% weight)
    revenue_quality: float  # 0-100 (20% weight)
    cash_flow_quality: float  # 0-100 (15% weight)
    audit_risk: float  # 0-100 (15% weight)
    sub_scores: dict[str, float]  # individual model outputs

def compute_fis(extracted: ExtractedData) -> FinancialIntegrityScore:
    """Compute Financial Integrity Score from extracted financial data."""
    manipulation = _score_manipulation(extracted)  # Beneish + Dechow + Montier
    accruals = _score_accruals(extracted)  # Enhanced Sloan + intensity
    revenue = _score_revenue_quality(extracted)  # DSO + AR + Q4 + deferred
    cashflow = _score_cashflow_quality(extracted)  # QoE + CCE + CFA
    audit = _score_audit_risk(extracted)  # MW + auditor + restatement + GC

    overall = (
        manipulation * 0.30
        + accruals * 0.20
        + revenue * 0.20
        + cashflow * 0.15
        + audit * 0.15
    )
    # Zone classification
    zone = _classify_fis_zone(overall)
    return FinancialIntegrityScore(
        overall_score=overall, zone=zone, ...
    )
```

### CheckResult Model Enhancement
```python
# Enhanced CheckResult with new fields (backward-compatible defaults)
class CheckResult(BaseModel):
    check_id: str
    check_name: str
    status: CheckStatus
    value: str | float | None = None
    threshold_level: str = ""
    evidence: str = ""
    source: str = ""
    factors: list[str] = Field(default_factory=list)
    section: int = 0
    needs_calibration: bool = False
    # NEW Phase 26 fields (all optional for backward compat)
    category: str = ""  # DECISION_DRIVING, CONTEXT_DISPLAY, DEPRECATED
    plaintiff_lenses: list[str] = Field(default_factory=list)
    signal_type: str = ""  # LEVEL, DELTA, PATTERN, FORENSIC, NLP, etc.
    temporal_classification: str = ""  # IMPROVING/STABLE/DETERIORATING/CRITICAL
```

### Knowledge Store Migration (Alembic)
```python
# New columns on checks table
def upgrade() -> None:
    op.add_column("checks", sa.Column("category", sa.String(), nullable=True))
    op.add_column("checks", sa.Column("plaintiff_lenses", sa.JSON(), nullable=True))
    op.add_column("checks", sa.Column("signal_type", sa.String(), nullable=True))
    op.add_column("checks", sa.Column("hazard_or_signal", sa.String(), nullable=True))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat section-based check organization | Multi-dimensional classification (section + lens + signal + category) | Phase 26 | Enables "who's suing" analysis, eliminates orphaned checks |
| Single-period financial analysis | Temporal change detection (3+ period trends) | Phase 26 | Catches the CHANGES that trigger SCAs, not just levels |
| Beneish M-Score alone | Financial Integrity Score (4 models + composite) | Phase 26 | Multiple perspectives reduce false positives/negatives |
| Governance as check subcategory | Executive forensics as primary analytical dimension | Phase 26 | Person-level risk scoring -- the underwriter's top priority |
| No NLP signals | MD&A tone, readability, risk factor evolution | Phase 26 | Strongest academic predictors of fraud not yet implemented |
| 91 checks with no factor mapping | Every check mapped to category + factors | Phase 26 | Eliminates 25% of checks being "orphaned" from scoring |

## Behavioral vs. Structural: The Organizing Principle

The key intellectual distinction driving Phase 26 (from HAZARD_DIMENSIONS_RESEARCH.md):

| Concept | Layer | What It Answers | Phase |
|---------|-------|----------------|-------|
| Classification | Layer 1 | "What IS this company?" (market cap, industry, age) | Phase 25 |
| Hazard Profile | Layer 2 | "What ABOUT this company creates inherent exposure?" (47 structural dimensions) | Phase 25 |
| Analytical Engine | Layer 3 | "What is this company DOING that suggests a problem?" (behavioral signals) | **Phase 26** |
| Peril Mapping | Layer 4 | "WHO sues and HOW BAD?" (plaintiff lens assessment) | Phase 27 |
| Presentation | Layer 5 | "How do we communicate this?" (issue-driven, contextual) | Phase 28 |

**Phase 26's core question:** Given the structural baseline from Layers 1-2, what BEHAVIORAL EVIDENCE modifies risk assessment up or down?

## Integration with Phase 25 (IES)

Phase 25 produces an Inherent Exposure Score (IES, 0-100). Phase 26 checks should consume IES context:

1. **IES-aware check evaluation:** Checks can reference IES to contextualize findings. A Beneish M-Score of -1.5 is more alarming for a company with IES=30 (low inherent exposure = this is unexpected) than IES=85 (high inherent exposure = consistent with profile).

2. **"No claims but high risk" counterbalance:** When F1 scores LOW (no litigation) but IES is HIGH (>60), the system flags: "No prior litigation despite elevated inherent exposure." This check requires IES from Phase 25.

3. **Scoring flow:** Classification (Layer 1) -> Hazard Profile/IES (Layer 2) -> Check Execution (Layer 3, Phase 26) -> Factor Scoring (consumes both IES and check results).

## New Critical Red Flag Gates (CRF-12 through CRF-17)

From unified framework Section 10.3:

| CRF | Condition | Ceiling | Rationale |
|-----|-----------|---------|-----------|
| CRF-12 | Active DOJ criminal investigation | REFER | Fundamental D&O exposure change |
| CRF-13 | Altman Z-Score < 1.81 (distress zone) | REFER | Zone of insolvency changes fiduciary duties |
| CRF-14 | Caremark claim survived dismissal | REFER | Court found colorable oversight failure |
| CRF-15 | Executive Forensics aggregate > 50 | REFER | Very high people risk |
| CRF-16 | Financial Integrity Score < 20 | REFER | Critical financial reporting concerns |
| CRF-17 | Whistleblower/qui tam disclosure | REFER | Strong leading indicator |

## Open Questions

1. **checks.json restructuring approach**
   - What we know: Current file is 9215 lines with 359 checks. Adding 90 new + 4 new fields per check will push to ~14,000 lines.
   - What's unclear: Should we split checks.json by prefix (BIZ.json, FIN.json, etc.) or keep as one file? The BackwardCompatLoader and knowledge store migration both read from a single file.
   - Recommendation: Keep single file for Phase 26 (breaking it up is a separate refactor). Add a JSON schema validator to ensure new metadata fields are populated on all checks.

2. **Executive forensics data acquisition timing**
   - What we know: Executive forensics needs data from SEC SALI, CourtListener, and web search. These require ACQUIRE stage additions.
   - What's unclear: Should ACQUIRE stage changes be part of Phase 26 or a prerequisite?
   - Recommendation: Include minimal ACQUIRE stage additions in Phase 26 (executive name extraction + web search for prior litigation). Deep data source integration (CourtListener API, FINRA BrokerCheck) deferred to Phase 27 or 30.

3. **Temporal data availability**
   - What we know: Temporal change detection needs multi-quarter data. Current XBRL extraction provides FY Prior, FY Latest, and YTD.
   - What's unclear: Do we have enough quarterly data points for meaningful temporal analysis?
   - Recommendation: Start with YoY change (FY Prior vs. FY Latest) which is available. QoQ analysis requires quarterly XBRL extraction enhancement (potentially deferred).

4. **Factor weight rebalancing**
   - What we know: Adding sub-factors changes the effective weight of each factor even if max_points stays the same.
   - What's unclear: Should factor max_points be adjusted when sub-factors are added?
   - Recommendation: Keep current max_points for Phase 26. Factor weight rebalancing is a Phase 27-29 calibration task that requires multi-ticker validation.

5. **Prior-year filing acquisition**
   - What we know: NLP signals (tone shift, risk factor evolution) require comparison between current and prior year 10-K.
   - What's unclear: Does current ACQUIRE stage fetch only the latest filing, or can it fetch prior year?
   - Recommendation: Add prior-year 10-K acquisition to ACQUIRE as part of Phase 26. This is a prerequisite for NLP signals. EdgarTools supports fetching historical filings.

## Sources

### Primary (HIGH confidence)
- `/Users/gorlin/projects/research/.planning/phases/24-check-calibration-knowledge-enrichment/24-UNIFIED-FRAMEWORK.md` - Comprehensive 1800-line architecture document (USER-APPROVED)
- `/Users/gorlin/projects/research/.planning/phases/24-check-calibration-knowledge-enrichment/research/HAZARD_DIMENSIONS_RESEARCH.md` - 7-category, 47-dimension hazard taxonomy
- `/Users/gorlin/projects/research/.planning/phases/24-check-calibration-knowledge-enrichment/research/HAZARD_MODEL_VALIDATION.md` - Industry validation of hazard model
- `/Users/gorlin/projects/research/src/do_uw/brain/checks.json` - Current 359-check registry (analyzed programmatically)
- `/Users/gorlin/projects/research/src/do_uw/stages/analyze/__init__.py` - Current AnalyzeStage implementation
- `/Users/gorlin/projects/research/src/do_uw/stages/analyze/check_engine.py` - Current check execution engine
- `/Users/gorlin/projects/research/src/do_uw/stages/analyze/check_mappers.py` - Current data mapping (493 lines)
- `/Users/gorlin/projects/research/src/do_uw/stages/score/__init__.py` - Current ScoreStage (16-step pipeline)
- `/Users/gorlin/projects/research/src/do_uw/stages/score/factor_scoring.py` - Current 10-factor scoring
- `/Users/gorlin/projects/research/src/do_uw/stages/score/factor_rules.py` - Current per-factor rule matching
- `/Users/gorlin/projects/research/src/do_uw/knowledge/models.py` - Knowledge store Check model

### Secondary (MEDIUM confidence)
- `/Users/gorlin/projects/research/.planning/ROADMAP.md` - Phase 26 description and dependencies
- `/Users/gorlin/projects/research/src/do_uw/stages/analyze/check_results.py` - CheckResult/CheckStatus models
- `/Users/gorlin/projects/research/src/do_uw/brain/scoring.json` - 10-factor scoring configuration

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - existing project stack, minimal new dependencies
- Architecture: HIGH - clear unified framework document with detailed specifications
- Check reclassification: HIGH - programmatic analysis of all 359 checks + framework guidance
- Double-counting resolution: HIGH - clear hazard vs. signal distinction from research
- New check specifications: MEDIUM - specifications from framework but implementation details need fleshing out
- NLP signal implementation: MEDIUM - requires prior-year filing acquisition (untested)
- Executive forensics: MEDIUM - data acquisition boundary needs resolution
- Pitfalls: HIGH - based on deep codebase familiarity

**Research date:** 2026-02-11
**Valid until:** 60 days (architecture is stable; implementation details may shift as Phase 25 is built first)
