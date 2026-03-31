# Signal Composition Model Research

## Purpose

Evaluate whether the current 400-signal to 10-factor aggregation approach is the right
composition model for D&O underwriting, and propose improvements based on code analysis
and industry practice.

---

## 1. Current Composition Model

### Architecture Overview

The system operates as a multi-layer pipeline with distinct composition stages:

```
Layer 0: ACQUIRE/EXTRACT -> raw data (SEC filings, stock, litigation, web)
Layer 1: CLASSIFY -> market_cap_tier + sector + IPO_recency -> base_filing_rate_pct
Layer 2: HAZARD PROFILE -> 39 dimensions (H1-H7) -> IES score + ies_multiplier
Layer 3: ANALYZE -> 400 signals evaluated -> TRIGGERED / CLEAR / SKIPPED / INFO
Layer 4: SCORE ->
  Step 1:  CRF gates (17 triggers) -> ceiling constraints
  Step 2:  10-factor scoring (F1-F10) -> base risk points
  Step 3:  19 pattern detections -> pattern modifiers to factors
  Step 4:  IES amplification of behavioral factors
  Step 5:  Composite score = 100 - total_risk_points
  Step 6:  CRF ceiling application -> quality_score
  Step 7:  Tier classification (WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH)
  Step 8:  Risk type archetype (7 types)
  Step 9:  Allegation theory mapping (5 theories: A-E)
  Step 10: Claim probability (base_rate x hazard_mult x signal_mult)
  Step 11: Severity (DDL-based settlement prediction or tier fallback)
  Step 12: Tower position recommendation
  Step 13: Red flag summary
  Step 14: 7-lens peril map + bear cases
```

### The 10-Factor Model

From `src/do_uw/brain/scoring.json`, the factors and their weights:

| Factor | Name | Max Points | Weight | Historical Lift | Confidence |
|--------|------|-----------|--------|-----------------|------------|
| F1 | Prior Litigation | 20 | 20% | 4.2x | VALIDATED |
| F2 | Stock Decline | 15 | 15% | 3.8x | VALIDATED |
| F3 | Restatement/Audit | 12 | 12% | 4.5x | VALIDATED |
| F4 | IPO/SPAC/M&A | 10 | 10% | 2.8x | VALIDATED |
| F5 | Guidance Misses | 10 | 10% | 2.8x (est) | VALIDATED |
| F6 | Short Interest | 8 | 8% | 2.1x | CORRELATED |
| F7 | Volatility | 9 | 9% | 1.9x | CORRELATED |
| F8 | Financial Distress | 8 | 8% | 2.0x | CORRELATED |
| F9 | Governance | 6 | 6% | 1.3x | HYPOTHESIS |
| F10 | Officer Stability | 2 | 2% | 1.2x | HYPOTHESIS |
| **Total** | | **100** | **100%** | | |

**Scoring formula**: `quality_score = 100 - risk_points` (after CRF ceiling)

**Tier boundaries**: WIN (86-100), WANT (71-85), WRITE (51-70), WATCH (31-50), WALK (11-30), NO_TOUCH (0-10)

### How 400 Signals Feed Into 10 Factors

The relationship between the signal layer and the factor layer is **indirect and
under-specified**. Here is the actual data flow:

1. **Signals (ANALYZE stage)** - Each of the ~400 signals has a `factors` field listing
   which F-factors it relates to (e.g., `FIN.FORENSIC.fis_composite` maps to `[F3]`).
   Signals evaluate to TRIGGERED/CLEAR/SKIPPED/INFO with evidence strings.

2. **Factor scoring (SCORE stage)** - Factors are scored by `factor_scoring.py` using
   `factor_data.py` which extracts data DIRECTLY from `ExtractedData` (not from signal
   results). Factor rules in `scoring.json` match against this extracted data.

3. **The gap**: Signal results from ANALYZE do NOT directly drive factor scores.
   Factor scoring re-extracts data from state independently. The signals exist primarily
   for:
   - Populating the worksheet with individual findings
   - Feeding the peril map (7-lens assessment)
   - Recording effectiveness data for the learning loop
   - Providing evidence trails

4. **Limited bridges**: Some signal results reach factor scoring through:
   - `analysis_results` dict passed to `score_all_factors()` (forensic composites,
     executive risk, NLP signals)
   - CRF gates that read signal results for Phase 26 gates (CRF-12 through CRF-17)
   - Pattern detection reads from `ExtractedData`, not signal results

### CRF Gates: The Override Layer

17 Critical Red Flag gates act as hard ceilings:
- CRF-01 to CRF-03: Active SCA, Wells Notice, DOJ -> ceiling at 30 (WALK)
- CRF-04 to CRF-11: Going concern, restatement, SPAC, short report, stock drops -> ceiling at 50 (WATCH)
- CRF-12 to CRF-17: DOJ criminal, Altman Z distress, Caremark, exec forensics, FIS critical, whistleblower -> ceiling at 20-30 (REFER)

This is the system's most powerful composition mechanism: binary gates that override
the additive model.

### Pattern Detection: The Interaction Layer

19 patterns detect multi-signal combinations (from `src/do_uw/brain/patterns.json`):
- `PATTERN.STOCK.EVENT_COLLAPSE`: single-day drop + company-specific trigger + peer stability
- `PATTERN.STOCK.DEATH_SPIRAL`: price + convertibles + shorts + delisting + cash
- `PATTERN.STOCK.INFORMED_TRADING`: insider selling + cluster + pre-announcement
- `PATTERN.FIN.EARNINGS_QUALITY_DETERIORATION`: accruals + Beneish + DSO trend
- `PATTERN.GOV.TURNOVER_STRESS`: leadership departures + stress timing
- etc.

Each detected pattern adds modifier points to specific factors (capped at max).

### Enhanced Frequency Model

The frequency model computes:
```
adjusted_probability = base_rate * hazard_mult * signal_mult
```
Where:
- `base_rate` comes from Layer 1 classification (sector + market cap)
- `hazard_mult` comes from Layer 2 IES profile (39 hazard dimensions)
- `signal_mult` = CRF_mult * pattern_mult * factor_elevation_mult (capped at 2.0x)

### Hazard Interactions: Named Profiles

From `src/do_uw/brain/config/hazard_interactions.json`, 5 named interaction profiles:
- **ROOKIE_ROCKET**: high growth + inexperienced management + recent IPO (1.3-1.5x)
- **BLACK_BOX**: complex model + weak earnings quality + non-GAAP reliance (1.2-1.4x)
- **IMPERIAL_FOUNDER**: founder CEO + dual-class + weak board (1.2-1.5x)
- **ACQUISITION_MACHINE**: serial acquirer + goodwill-heavy (1.15-1.35x)
- **CASH_BURN_CLIFF**: pre-revenue + IPO + rapid growth (1.25-1.45x)

These are the closest thing to a compounding interaction model in the current system.

---

## 2. Strengths and Weaknesses

### Strengths

**S1. Multi-layer architecture is fundamentally sound.**
The separation of classification (inherent exposure) from behavioral signals (company
actions) from catastrophic triggers (CRF gates) mirrors how experienced underwriters
think. Layer 1 says "what kind of company is this?" Layer 2 says "what inherent risks
does it carry?" Layers 3-4 say "what has it actually done?"

**S2. CRF gates correctly implement non-linear risk.**
An active SCA should not be "one of many factors" -- it should dominate the decision.
The ceiling mechanism is the right approach for binary risk events that fundamentally
change the risk picture.

**S3. Sector-relative baselines.**
Short interest, volatility, leverage, and guidance miss scoring all use sector-specific
baselines. A 5% short interest at a biotech (normal) means something different from 5%
at a utility (extreme). This is correct underwriting practice.

**S4. Pattern detection captures multi-factor interactions.**
The 19 patterns detect meaningful combinations (EVENT_COLLAPSE, DEATH_SPIRAL,
INFORMED_TRADING) that additive scoring alone would miss.

**S5. The frequency model uses multiplicative composition.**
`base_rate * hazard_mult * signal_mult` is multiplicative, not additive.
This correctly captures that high-hazard + high-signal companies face exponentially
higher risk than either alone.

### Weaknesses

**W1. The 400 signals are disconnected from factor scoring.**
This is the most significant structural problem. The ANALYZE stage evaluates 400 signals
but the SCORE stage largely ignores them, re-extracting data independently. The signals
exist as a parallel evaluation that feeds the worksheet and peril map but does not
systematically drive the score.

**Impact**: A signal like `FIN.FORENSIC.beneish_dechow_convergence` triggers (both
Beneish AND Dechow flag manipulation), but this information only reaches F3 through
the `analysis_results.forensic_composites` side channel, not through any systematic
signal-to-factor aggregation.

**W2. Factor weights are static and hand-tuned.**
F1 (Prior Litigation) always gets 20 points max regardless of context. But prior
litigation matters much more for a company with a recent stock drop (DDL is higher)
than for one with stable stock performance. The weights should be contextual.

**W3. Additive factor composition misses compounding risk.**
`quality_score = 100 - sum(factor_points)` is purely additive. A company scoring
8/20 on F1 (prior litigation) and 12/15 on F2 (stock decline) gets 80 risk points.
But in reality, prior litigation + stock decline = enormously higher risk than either
alone, because the stock decline establishes damages (DDL) for the existing litigation.
The current system adds them; it should multiply them.

**W4. The IES amplification is too crude.**
`_apply_ies_amplification()` uses 3 fixed multipliers (1.50x, 1.25x, 0.85x) applied
uniformly to "behavioral" factors (F3, F5, F6, F7, F9, F10). But IES should modulate
different factors differently. High business model complexity (H1-02) should amplify
F3 (restatement risk) more than F6 (short interest).

**W5. 19 patterns are insufficient for the interaction space.**
With 8 signal prefix groups (FIN, GOV, LIT, STOCK, BIZ, EXEC, FWRD, NLP) and 10
factors, there are dozens of meaningful cross-domain interactions. Only 19 patterns
are defined, and they're hardcoded with specific field lookups in `pattern_fields.py`.
Adding a new interaction requires code changes, not configuration.

**W6. Governance signals are under-weighted.**
F9 (Governance) = 6 points, F10 (Officer Stability) = 2 points. Total = 8/100.
But governance quality is an enabler/suppressor of all other risks. A company with
strong governance can contain a restatement; one with weak governance will see it
escalate to litigation. Governance should modulate other factors, not just add points.

**W7. The tier system creates artificial boundaries.**
A score of 71 (WANT) and 70 (WRITE) represent nearly identical risk but receive
dramatically different treatment. The sharp tier boundaries create cliff effects
that a continuous risk model would not.

**W8. No temporal interaction model.**
The system evaluates current state but does not model how signal trajectories interact.
A company with deteriorating financials AND rising short interest AND declining governance
quality is on a much worse trajectory than any individual signal suggests. The temporal
engine runs but its output is consumed only by F8 sub-factors.

**W9. The allegation theory mapping is post-hoc, not integrated.**
Allegation mapping (5 theories: A-E) runs after scoring as a labeling exercise. But
allegation theory should drive how signals are weighted, because D&O claims are
structured around specific legal theories. A disclosure theory (10b-5) requires
different evidence than a governance theory (Caremark).

---

## 3. Industry Standard Approaches

### How D&O Underwriters Actually Work

Based on industry research (Woodruff Sawyer, WTW, Cornerstone Research, NERA):

**3.1 Two-phase assessment**: Experienced D&O underwriters use a two-phase approach:
1. **Classification** (inherent exposure): Sector, size, geography, business model,
   capital markets activity. This sets the base rate.
2. **Signal assessment** (behavioral indicators): What has the company actually done
   that elevates or reduces risk from baseline?

This maps well to the current Layer 1 (classification) + Layer 2 (hazard) architecture.

**3.2 Knockout gates first**: Every underwriter checks hard stops first:
- Active litigation? Stop.
- Going concern? Stop.
- Recent restatement? Stop.
- Stock price collapse? Stop.
This maps to CRF gates. Industry practice confirms this is correct.

**3.3 Risk story, not risk score**: Experienced underwriters do not think in "scores."
They think in narratives: "This is a high-growth tech company that just had its first
earnings miss, and the CFO left. The stock is down 40%. This looks like a classic
growth-darling-to-SCA pipeline." The score is a summary, not the analysis.

**3.4 Filing rates by sector and market cap** (Cornerstone Research 2024):
- Core litigation rate: 3.9% in 2024 (above 2010-2023 average of 3.6%)
- Technology + Healthcare accounted for >50% of filings
- Large-cap companies face 10.7x higher litigation probability
- DDL-to-market-cap ratios as low as 3% still trigger filings for large caps

**3.5 Factor interactions are standard**: The WTW research found that cyber risk
increases SCA probability from 5% to 68% -- a 13.6x multiplier, not an additive
adjustment. Industry models inherently treat certain combinations as multiplicative.

**3.6 Settlement prediction is DDL-driven**: NERA and Cornerstone models predict
settlement from Dollar Damages Loss (DDL), which is market-cap-drop during the class
period. This is already implemented in `settlement_prediction.py`.

### Academic and Analytical Approaches

**Kim and Skinner (2012)**: "Measuring Securities Litigation Risk" found that
industry-alone is a poor predictor, but firm characteristics (size, growth, volatility)
improve prediction considerably. Sudden stock price declines at information release
are the strongest predictor -- consistent with F2's highest weight after F1.

**Multi-factor copula models**: Academic literature uses copula structures to model
dependent risks in insurance. The key insight: factors are not independent. Loss
distributions must account for tail dependencies between correlated risks.

---

## 4. Proposed Model: Hierarchical Multiplicative Composition

### Core Principle

Replace the single additive formula (`100 - sum(points)`) with a hierarchical
multiplicative model that preserves interpretability while capturing interactions.

### Architecture: Three Tiers of Composition

```
Tier 1: RISK THEMES (5 themes, multiplicative composition)
  Disclosure Integrity  = f(F1, F3, F5, FIN signals, NLP signals)
  Market Signal         = f(F2, F6, F7, STOCK signals)
  Governance Quality    = f(F9, F10, GOV signals, EXEC signals)
  Financial Health      = f(F8, FIN balance signals)
  Event Exposure        = f(F4, FWRD signals, BIZ signals, LIT signals)

Tier 2: THEME INTERACTIONS (pairwise compounding)
  Disclosure * Market   = "Stock drop + accounting issues = SCA pipeline"
  Governance * anything = "Weak governance amplifies all other themes"
  Financial * Market    = "Distress + stock decline = death spiral"
  Event * Disclosure    = "M&A + earnings miss = Section 11 + 10(b) combo"

Tier 3: OVERRIDE GATES (CRF-style binary events)
  Active SCA, Wells Notice, DOJ, Going Concern, etc.
  These impose ceilings regardless of theme scores.
```

### Detailed Theme Scoring

Each theme produces a continuous score from 0 (no risk) to 1 (maximum risk):

```python
# Theme 1: Disclosure Integrity (currently F1 + F3 + F5)
disclosure_score = (
    weighted_average(
        signal_results["FIN.FORENSIC.*"],  # Beneish, Dechow, accruals
        signal_results["FIN.QUALITY.*"],   # Revenue quality, cash flow quality
        signal_results["NLP.*"],           # Tone shifts, readability
        factor_points["F3"],               # Restatement/audit
        factor_points["F5"],               # Guidance misses
    )
)

# Theme 2: Market Signal (currently F2 + F6 + F7)
market_score = (
    weighted_average(
        signal_results["STOCK.*"],         # Price patterns, insider trading
        factor_points["F2"],               # Stock decline
        factor_points["F6"],               # Short interest
        factor_points["F7"],               # Volatility
    )
)
```

### Pairwise Interaction Formula

Instead of additive composition, use:

```python
# For each pair of themes (A, B):
interaction_score = A * B * interaction_coefficient

# The overall risk score:
base_risk = max(theme_scores)  # Dominated by highest theme
interaction_risk = sum(pairwise_interactions)  # Compounding effects
total_risk = min(base_risk + interaction_risk, 1.0)

# Convert to quality score:
quality_score = 100 * (1 - total_risk)
```

### Why Multiplicative for Interactions

When a company has:
- F1 (Prior Litigation) = 80% of max -> disclosure_theme = 0.6
- F2 (Stock Decline) = 80% of max -> market_theme = 0.7

Additive: `0.6 + 0.7 = 1.3` (capped at 1.0) -- both contribute equally
Multiplicative: `0.6 * 0.7 * coefficient = 0.42 * coeff` -- interaction term

The multiplicative interaction captures: "stock decline BECAUSE OF disclosure issues
means DDL exists, which means the existing litigation has quantifiable damages."
This is qualitatively different from "stock decline from sector rotation" + "old
settled litigation."

### Governance as a Modulator

Governance should not be just another additive factor. It should multiply all other
themes:

```python
governance_multiplier = 1.0 + (governance_score * governance_amplification)
# Strong governance (score near 0): multiplier ~1.0 (neutral)
# Weak governance (score near 1): multiplier ~1.3 (amplifies all risks)

final_risk = total_risk * governance_multiplier
```

This reflects the reality that weak governance does not create risk independently --
it allows other risks to escalate unchecked.

---

## 5. Signal Interaction Map

### Cross-Domain Interactions That Should Exist

#### FIN x STOCK (Financial Signals x Stock Signals)
| Interaction | Mechanism | Current Coverage | Proposed |
|------------|-----------|------------------|----------|
| Earnings quality deterioration + stock drop | DDL exists for manipulation-based SCA | PATTERN.FIN.EARNINGS_QUALITY_DETERIORATION modifies F3 | Multiplicative: disclosure_theme * market_theme |
| Going concern + stock decline | Death spiral pipeline | PATTERN.STOCK.DEATH_SPIRAL (partial) | Automatic via theme interaction |
| Cash burn + stock drop | Existential risk + DDL | PATTERN.FIN.LIQUIDITY_STRESS (not linked to stock) | Cross-theme interaction |
| Revenue miss + stock drop | Classic 10b-5 pipeline | F5 + F2 additive only | disclosure_theme * market_theme interaction |

#### GOV x LIT (Governance x Litigation)
| Interaction | Mechanism | Current Coverage | Proposed |
|------------|-----------|------------------|----------|
| Weak governance + active SCA | Board cannot defend, settlement likely | None (CRF-01 overrides) | governance_multiplier amplifies all |
| Board turnover + SEC investigation | "Rats leaving ship" pattern | PATTERN.GOV.TURNOVER_STRESS (partial) | governance_multiplier on event_exposure |
| CEO chair duality + accounting issues | No independent oversight over financials | F9 + F3 additive | governance_multiplier on disclosure |
| Related party transactions + restatement | Self-dealing + manipulation | Not connected | disclosure * governance interaction |

#### STOCK x LIT (Stock x Litigation)
| Interaction | Mechanism | Current Coverage | Proposed |
|------------|-----------|------------------|----------|
| Stock drop + existing litigation | DDL quantifies damages for active case | F1 + F2 additive | Automatically multiplicative via themes |
| Insider selling + stock drop | Scienter element for 10b-5 | PATTERN.STOCK.INFORMED_TRADING (multiplier on F2) | Keep -- this is well-modeled |
| Short attack + filing | Plaintiff attorneys track short reports | PATTERN.STOCK.SHORT_ATTACK | Keep + add to event_exposure theme |
| Peer divergence + litigation history | Company-specific causation established | PATTERN.STOCK.PEER_DIVERGENCE (partial) | market_theme strength indicator |

#### BIZ x FWRD (Business x Forward-Looking)
| Interaction | Mechanism | Current Coverage | Proposed |
|------------|-----------|------------------|----------|
| Growth deceleration + high P/E | Growth darling to SCA | PATTERN.BIZ.GROWTH_TRAJECTORY | event_exposure theme |
| AI claims + SEC scrutiny | AI washing enforcement | PATTERN.BIZ.AI_WASHING_RISK | event_exposure theme |
| Concentration risk + catalyst event | Binary outcome in policy period | PATTERN.BIZ.CONCENTRATION + PATTERN.FWRD.CATALYST_RISK (separate) | Should interact via themes |
| Regulatory change + industry exposure | Sector-wide litigation wave | Not connected | External environment in hazard_profile |

#### EXEC x GOV (Executive x Governance)
| Interaction | Mechanism | Current Coverage | Proposed |
|------------|-----------|------------------|----------|
| Exec forensics risk + weak board | No oversight of problematic individuals | CRF-15 (exec aggregate > 50) | governance_multiplier on exec signals |
| CFO departure during stress + restatement | Timing correlation = scienter | F10 departure timing sub-factor (Phase 26) | disclosure * governance interaction |
| Prior personal litigation + current role | Pattern of behavior at new company | GOV.BOARD.* board forensics (partially wired) | Part of governance_theme |

### Interactions That Are MISSING and DANGEROUS

1. **Restatement + stock drop + insider selling**: This triple combination is the
   highest-probability SCA trigger, but it is currently scored as F3 + F2 + F2_insider_amp.
   The compounding effect (3 elements of a 10b-5 claim: misstatement + loss causation +
   scienter) should produce a SEVERE escalation, not just additive points.

2. **Deteriorating temporal trends + forward catalyst**: If multiple financial metrics
   are deteriorating AND a binary event is coming (e.g., drug trial, M&A close), the
   risk of a policy-period claim is much higher. Currently these are independent.

3. **NLP tone shift + guidance miss**: Management changing disclosure language while
   simultaneously missing guidance suggests they knew about problems before the market.
   This is scienter evidence. Currently NLP signals feed into F3 sub-factors but not
   into the guidance miss (F5) interaction.

---

## 6. Calibration Strategy

### Current State

The scoring system explicitly acknowledges lack of calibration:
- `needs_calibration=True` appears on claim probability, severity, allegation mapping,
  and tower recommendation
- `calibration_notes: "SECT7-11: All scoring parameters require calibration against
  historical cases"`
- Historical lift values on factors (1.2x to 4.5x) are noted but not verified against
  actual loss data

### Proposed Calibration Framework

#### Phase 1: Historical Backtesting

Use the learning loop (brain.duckdb `brain_signal_runs` table with 20K+ records):

1. **Collect outcomes**: For companies analyzed, track which ones actually had SCA
   filings within 12 months. Cross-reference against Stanford SCAC database.

2. **Compute empirical factor weights**: For each factor, compute the lift
   (probability of SCA given factor=HIGH vs factor=LOW). Use these empirical lifts
   to validate or replace hand-tuned weights.

3. **Validate interaction effects**: For each pair of themes, compute the joint
   probability and compare to the product of marginals. If joint >> product, there
   is a compounding effect that the model should capture.

4. **Calibrate tier boundaries**: Map quality scores to observed filing rates. If
   WRITE-tier companies actually file at 8% (not 5-10%), adjust boundaries.

#### Phase 2: External Benchmark Integration

Integrate public data from NERA and Cornerstone Research:

| Parameter | Current Value | 2024 Empirical | Action |
|-----------|--------------|----------------|--------|
| Overall filing rate | 4.0% default | 3.9% (NERA 2024) | Close enough |
| Tech sector rate | 5.0% | ~6.5% (>50% of filings, ~12% of listings) | INCREASE |
| Biotech rate | 7.0% | Higher than 7% per H1 2025 data | INCREASE |
| Large-cap multiplier | 1.28x | ~10.7x higher than micro-cap (but compare apples to apples) | VALIDATE |
| Stock drop threshold for filing | 15% (F2 rules) | DDL/MCap < 3% triggers for large caps | Need DDL model |

#### Phase 3: Continuous Learning

The brain.duckdb feedback tables already support this:

1. Each pipeline run records signal status (TRIGGERED/CLEAR/SKIPPED)
2. `brain_effectiveness` tracks fire rates per signal
3. Proposed: add `outcome_12mo` field (SCA filed? Settlement? Dismissal?)
4. Weekly recalibration of factor weights based on accumulating outcome data

### Weight Calibration Mathematics

For each factor `i`, the empirical weight should be:

```
weight_i = log(P(SCA | factor_i = HIGH) / P(SCA | factor_i = LOW))
```

This is the log-odds ratio, which naturally produces a logistic regression model.
The current additive model with hand-tuned weights is a simplified version of this.

For interaction terms:

```
interaction_ij = log(P(SCA | factor_i=HIGH, factor_j=HIGH)) -
                 log(P(SCA | factor_i=HIGH)) -
                 log(P(SCA | factor_j=HIGH)) +
                 log(P(SCA))
```

If `interaction_ij > 0`, the combination is super-additive (compounding risk).
If `interaction_ij < 0`, one factor subsumes the other.

---

## 7. Signal-to-Story Framework

### The Underwriter's Mental Model

An underwriter does not think: "F1=18, F2=12, F3=5, total=35, quality=65, tier=WRITE."

They think: "This company has an active lawsuit, the stock just crashed, and their
auditor found material weaknesses. This is a toxic risk."

The system needs an intermediate layer between individual signals and the final score
that tells this story.

### Proposed: Risk Narrative Themes

Five narrative themes, each telling a piece of the underwriting story:

#### Theme 1: "Are they telling the truth?" (Disclosure Integrity)
- Signals: FIN.FORENSIC.*, FIN.QUALITY.*, NLP.*, restatement, audit issues
- Story: Financial reporting quality and management transparency
- Key question: Is there evidence of manipulation or aggressive accounting?
- Allegation theories served: A (Disclosure), B (Guidance)

#### Theme 2: "What is the market saying?" (Market Signal)
- Signals: STOCK.*, short interest, volatility, peer divergence, insider trading
- Story: Market perception and trading-based risk indicators
- Key question: Is the market pricing in risk that fundamentals don't show?
- Allegation theories served: A (Disclosure -- via DDL), D (Governance -- via insider)

#### Theme 3: "Who is running the ship?" (Governance Quality)
- Signals: GOV.*, EXEC.*, board forensics, compensation, shareholder rights
- Story: Quality of oversight and management integrity
- Key question: Can this board and management team navigate trouble?
- Allegation theories served: D (Governance), C (Product/Ops -- via oversight duty)

#### Theme 4: "Can they survive?" (Financial Health)
- Signals: FIN.BALANCE.*, FIN.INCOME.*, distress indicators, leverage, liquidity
- Story: Financial resilience and ability to weather adversity
- Key question: If something goes wrong, does the company have the resources to manage?
- Allegation theories served: A (Disclosure -- if concealing distress)

#### Theme 5: "What's coming next?" (Event Exposure)
- Signals: FWRD.*, BIZ.*, LIT.*, M&A, IPO lifecycle, regulatory catalysts
- Story: Forward-looking exposure during the policy period
- Key question: What material events could trigger a claim during the next 12 months?
- Allegation theories served: E (M&A), C (Product/Ops), B (Guidance)

### How Themes Compose Into the Story

```
Risk Story = {
    headline: "Growth Tech Company with Earnings Quality Concerns",
    severity: "ELEVATED",
    themes: {
        disclosure_integrity: {
            score: 0.65,
            narrative: "Beneish M-Score flags potential manipulation.
                       Non-GAAP earnings diverge 2.1x from GAAP.
                       DSO trend rising while revenue decelerates.",
            key_signals: ["FIN.FORENSIC.fis_composite: RED",
                         "FIN.QUALITY.non_gaap_divergence: RED"],
        },
        market_signal: {
            score: 0.40,
            narrative: "Stock down 25% from high. Short interest elevated
                       at 2.3x sector average. No catastrophic single-day
                       drop yet.",
            key_signals: ["STOCK.PRICE.decline_52wk: YELLOW",
                         "STOCK.SHORT.pct_float: YELLOW"],
        },
        interaction: {
            disclosure_x_market: 0.26,
            narrative: "Accounting red flags + stock decline creates
                       SCA pipeline risk. If stock drops further on
                       earnings revelation, DDL-based settlement applies.",
        },
    },
    decision: "WRITE tier. Monitor for earnings event that could
              trigger disclosure_x_market escalation.",
}
```

### Facets as the Rendering Layer

The existing facet system (`facet` field on each signal YAML) already groups signals
into narrative clusters:
- `financial_health`, `governance_quality`, `litigation_exposure`,
  `market_dynamics`, `business_risk`, etc.

Facets should map directly to narrative themes:

| Facet | Theme |
|-------|-------|
| financial_health | Disclosure Integrity + Financial Health |
| governance_quality | Governance Quality |
| litigation_exposure | Event Exposure |
| market_dynamics | Market Signal |
| business_risk | Event Exposure |
| executive_profile | Governance Quality |
| forward_risk | Event Exposure |

---

## 8. Implementation Recommendations

### Phase A: Wire Signals to Factor Scoring (v2.0 compatible)

**Goal**: Close the gap between 400 signal evaluations and 10-factor scoring.

**Changes**:
1. In `factor_scoring.py`, add a step that aggregates signal results by factor:
   ```python
   def _aggregate_signal_evidence(factor_id, signal_results):
       """Count triggered signals for this factor."""
       relevant = [r for r in signal_results.values()
                   if factor_id in r.get("factors", [])]
       triggered = [r for r in relevant if r["status"] == "TRIGGERED"]
       return len(triggered), len(relevant)
   ```

2. Use signal trigger counts as an additional input to factor scoring, alongside
   direct data extraction. This creates a "confirmation bonus" -- if both the direct
   data check AND the signals agree, confidence is higher.

3. **File**: `src/do_uw/stages/score/factor_scoring.py` -- modify `score_all_factors()`
   to accept `signal_results` dict and pass to `_score_factor()`.

**Effort**: Small. No model change, just wiring.

### Phase B: Implement Risk Themes (requires new module)

**Goal**: Add the 5-theme intermediate layer between signals and final score.

**Changes**:
1. New module: `src/do_uw/stages/score/theme_scoring.py`
   - `compute_theme_scores(signal_results, factor_scores, extracted) -> ThemeScores`
   - Each theme aggregates its signals using weighted averaging
   - Theme scores are continuous [0, 1]

2. New module: `src/do_uw/stages/score/theme_interactions.py`
   - `compute_interactions(theme_scores) -> InteractionScores`
   - Pairwise interaction terms with configurable coefficients
   - Governance acts as a universal multiplier

3. New config: `src/do_uw/brain/config/theme_config.json`
   - Signal-to-theme mappings
   - Interaction coefficients
   - Governance amplification curve

4. Modify `src/do_uw/stages/score/__init__.py` to incorporate theme scores
   between Step 5 (composite) and Step 6 (CRF ceilings).

**Effort**: Medium. New modules but compatible with existing architecture.

### Phase C: Multiplicative Composition (model change)

**Goal**: Replace `quality_score = 100 - sum(points)` with multiplicative composition.

**Changes**:
1. Each theme produces a risk score [0, 1]
2. Theme interactions use: `interaction = theme_a * theme_b * coefficient`
3. Governance multiplier: `gov_mult = 1.0 + (gov_score * 0.3)`
4. Total risk = `base_theme_risk * gov_mult + interaction_terms`
5. Quality score = `100 * (1 - total_risk)`

**Calibration needed**: The coefficients must be set so that the output range
matches the current tier boundaries. Run against existing analyzed companies
(WWD, ANGI, RPM, AAPL) to verify tier assignments are consistent.

**Effort**: Medium-large. Model change requires revalidation.

### Phase D: Dynamic Interaction Detection (brain-driven)

**Goal**: Replace hardcoded 19 patterns with data-driven interaction detection.

**Changes**:
1. Define interaction schemas in YAML (like signal definitions)
2. Each interaction specifies: theme_a, theme_b, threshold_a, threshold_b, coefficient
3. New module: `src/do_uw/stages/score/interaction_engine.py`
   - Reads interaction definitions from brain/interactions/*.yaml
   - Evaluates all defined interactions against theme scores
   - Returns detected interactions with evidence

4. Keep the 19 existing patterns as a compatibility layer that maps to interactions.

**Effort**: Large. New subsystem, but aligns with v2.0 brain-driven architecture.

### Phase E: Calibration Loop (learning integration)

**Goal**: Use outcome data to calibrate weights.

**Changes**:
1. Add `outcome_tracking` table to brain.duckdb
2. After each pipeline run, record the predicted tier and probability
3. Periodically (manual or automated), input actual outcomes (SCA filed? Y/N)
4. Compute empirical lifts and interaction coefficients
5. Update `theme_config.json` weights based on empirical data

**Effort**: Large. Requires outcome data collection infrastructure.

### Implementation Priority

```
Phase A (Wire signals) -> immediate, low risk, high value
Phase B (Risk themes) -> next, creates the narrative layer
Phase C (Multiplicative) -> after B, requires calibration
Phase D (Dynamic interactions) -> v2.0 aligned
Phase E (Calibration loop) -> ongoing, value grows with data
```

### Migration Path

The theme model can be implemented as a **shadow system** alongside the existing
10-factor model:

1. Both models run on every pipeline execution
2. Both scores are recorded in brain.duckdb
3. Compare outputs for discrepancies
4. When theme model produces equivalent or better differentiation (measured by
   outcome correlation), switch primary output
5. Keep 10-factor model as a "second opinion" / audit trail

This matches the Phase 55 shadow evaluation strategy already planned for V2 signals.

---

## 9. Summary

The current 10-factor additive model is a reasonable starting point that captures
the most important D&O risk signals. Its CRF gate system, sector-relative baselines,
and pattern detection are genuine strengths.

However, the model has three structural limitations that prevent it from matching
expert underwriter judgment:

1. **Disconnection**: 400 signals feed the worksheet but not the score
2. **Additivity**: Compounding risks are added, not multiplied
3. **Static weights**: Factor importance does not vary with context

The proposed hierarchical multiplicative model addresses all three while preserving
interpretability through the risk theme narrative layer. Implementation can be
incremental, with each phase delivering value independently.

The single highest-ROI change is **Phase A**: wiring signal results into factor
scoring. This requires minimal code change but closes the largest gap in the current
architecture.

---

## References

- [NERA: Recent Trends in Securities Class Action Litigation: 2024 Full-Year Review](https://www.nera.com/insights/publications/2025/recent-trends-in-securities-class-action-litigation--2024-full-y.html)
- [Cornerstone Research: Securities Suit Filings Increased in 2024](https://www.dandodiary.com/2025/01/articles/securities-litigation/cornerstone-research-securities-suit-filings-increased-in-2024/)
- [Cornerstone Research: Securities Class Action Filings Remain Steady While Size Increased H1 2025](https://www.cornerstone.com/insights/press-releases/securities-class-action-filings-remain-steady-while-size-of-filings-increased-substantially-in-first-half-of-2025/)
- [Woodruff Sawyer: 2026 D&O Looking Ahead Guide](https://woodruffsawyer.com/insights/do-looking-ahead-guide)
- [WTW: Directors and Officers Liability - A Look Ahead to 2025](https://www.wtwco.com/en-us/insights/2025/01/directors-and-officers-d-and-o-liability-a-look-ahead-to-2025)
- [D&O Diary: Assessing Securities Class Action Risk with Event Analysis](https://www.dandodiary.com/2020/01/articles/securities-litigation/assessing-securities-class-action-risk-with-event-analysis/)
- [ScienceDirect: Measuring Securities Litigation Risk (Kim & Skinner)](https://www.sciencedirect.com/science/article/abs/pii/S0165410111000681)
- [Moody's: D&O Evolving Risks - A New Era of D&O Liability](https://www.moodys.com/web/en/us/insights/insurance/d-o-series-evolving-risks-in-the-boardroom-a-new-era-of-d-o-liability-part-2.html)
- [TransRe: U.S. Public D&O 2025 Insurance Market Update](https://www.transre.com/u-s-public-do-2025-insurance-market-update/)
