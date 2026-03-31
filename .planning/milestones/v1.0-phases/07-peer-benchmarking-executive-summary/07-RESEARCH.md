# Phase 7: Peer Benchmarking & Executive Summary - Research

**Researched:** 2026-02-08
**Domain:** BENCHMARK pipeline stage + Executive Summary synthesis (SECT1-01 through SECT1-07, CORE-02)
**Confidence:** HIGH (codebase analysis verified, domain data from published sources)

## Summary

Phase 7 builds two interconnected capabilities: (1) the BENCHMARK pipeline stage that positions every metric peer-relative, and (2) the Executive Summary (Section 1) that synthesizes all prior sections into an at-a-glance risk assessment. This phase completes the analytical pipeline -- after BENCHMARK, the state file contains everything needed for document rendering in Phase 8.

The codebase is well-prepared for this phase. The `BenchmarkResult` model already exists with `peer_rankings: dict[str, float]` for metric-to-percentile mappings. The `PeerGroup` with `PeerCompany` instances (ticker, name, market_cap, revenue, sic_code, industry) is constructed in EXTRACT (Phase 3). Several models already have peer_percentile fields (GovernanceQualityScore.peer_percentile, LeadershipStability.stability_peer_percentile, AdverseEventScore.peer_rank/peer_percentile). The SCORE stage produces all the data the Executive Summary needs: ScoringResult with factor_scores, red_flag_summary, claim_probability, severity_scenarios, tower_recommendation, risk_type, and allegation_mapping.

**Primary recommendation:** Split into 2 plans as roadmapped (07-01: BENCHMARK stage, 07-02: Executive Summary + state completeness). The BENCHMARK stage focuses on computing percentile ranks using peer financial data already available from EXTRACT, while the Executive Summary synthesizes data already in state into structured models. No new external data acquisition is needed -- this phase operates entirely on local state data.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | (existing) | Executive summary models, benchmark result expansion | Already the foundation of all models |
| Python statistics | stdlib | Percentile rank computation | `statistics.quantiles()` for percentile calculation -- no external dependency needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math | stdlib | Percentile interpolation | If `statistics` doesn't offer the exact percentile function needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| numpy/scipy for percentile | stdlib statistics | numpy would add heavyweight dependency for simple percentile rank; stdlib is sufficient for ranking N=5-10 peers |
| pandas for metric aggregation | Plain Python dicts | Peers are always <20 companies; pandas overhead not justified |

**Installation:** No new dependencies needed. All libraries are already in the project or stdlib.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
├── models/
│   ├── scoring.py              # BenchmarkResult expansion (existing)
│   ├── executive_summary.py    # NEW: SECT1-01 through SECT1-07 models
│   └── state.py                # Add executive_summary field to AnalysisState
├── stages/
│   ├── benchmark/
│   │   ├── __init__.py         # BenchmarkStage (replace stub)
│   │   ├── peer_metrics.py     # Metric extraction from peer PeerCompany data
│   │   ├── percentile_engine.py # Percentile rank computation
│   │   └── inherent_risk.py    # SECT1-02: filing probability + severity baseline
│   └── (no changes to other stages)
├── brain/
│   └── sectors.json            # EXTEND: Add claim_base_rates + severity_ranges per sector
└── config/
    └── (no new config files needed)
```

### Pattern 1: Percentile Rank Computation
**What:** Given a company metric and a list of peer values, compute the percentile rank (0-100) indicating where the company falls relative to peers.
**When to use:** Every metric that needs peer-relative positioning.
**Key design:**
```python
def percentile_rank(company_value: float, peer_values: list[float]) -> float:
    """Compute percentile rank of company_value within peer_values.

    Returns 0.0 (worst) to 100.0 (best).
    With 5 peers: ranks are 0, 20, 40, 60, 80, 100.
    If peer_values is empty, returns 50.0 (no comparison possible).
    """
    if not peer_values:
        return 50.0
    count_below = sum(1 for v in peer_values if v < company_value)
    count_equal = sum(1 for v in peer_values if v == company_value)
    n = len(peer_values)
    # Standard percentile rank formula
    return ((count_below + 0.5 * count_equal) / n) * 100.0
```

**Note on directionality:** Some metrics are "higher is better" (operating margin, FCF yield, ROE) while others are "lower is better" (debt-to-equity, short interest %). The percentile computation should account for this: for "lower is better" metrics, flip the ranking so 100th percentile still means "best."

### Pattern 2: Key Findings Selection Algorithm
**What:** Multi-signal ranking to select top 5 negatives and top 5 positives from all findings across sections.
**When to use:** SECT1-03 (Key Negatives) and SECT1-04 (Key Positives).
**Design approach (from CONTEXT.md decisions):**
```python
def rank_finding(finding: FlaggedItem) -> float:
    """Score a finding for key negatives/positives ranking.

    Combines:
    - Scoring impact (how many points deducted/preserved) -- weight 40%
    - Recency (newer findings rank higher) -- weight 20%
    - Trajectory (WORSENING > NEW > STABLE > IMPROVING) -- weight 20%
    - Claim probability correlation (mapped from allegation theory) -- weight 20%
    """
    score = 0.0
    score += _scoring_impact_score(finding) * 0.40
    score += _recency_score(finding) * 0.20
    score += _trajectory_score(finding) * 0.20
    score += _claim_correlation_score(finding) * 0.20
    return score
```

### Pattern 3: Underwriting Thesis Templates
**What:** Rule-based templates per risk type (GROWTH_DARLING, DISTRESSED, etc.) filled with specific findings -- deterministic, no LLM call.
**When to use:** SECT1 thesis narrative generation.
**Template structure (from CONTEXT.md decisions):**
```python
THESIS_TEMPLATES: dict[RiskType, str] = {
    RiskType.GROWTH_DARLING: (
        "The company presents as a {tier.value} risk ({quality_score:.0f}/100) "
        "with {risk_descriptor} as a high-growth, high-multiple issuer. "
        "{top_factor_narrative}. The primary allegation exposure is "
        "{primary_theory}, driven by {theory_evidence}. "
        "Industry base rate: {base_rate:.1f}% | Company-adjusted: "
        "{adjusted_rate_low:.0f}-{adjusted_rate_high:.0f}%."
    ),
    RiskType.DISTRESSED: (
        "The company presents elevated fiduciary risk ({quality_score:.0f}/100, "
        "{tier.value}) driven by financial distress indicators. "
        "{top_factor_narrative}. Side A coverage value is {side_a_assessment} "
        "given indemnification capacity concerns. "
        "Industry base rate: {base_rate:.1f}% | Company-adjusted: "
        "{adjusted_rate_low:.0f}-{adjusted_rate_high:.0f}%."
    ),
    # ... templates for all 7 risk types
}
```

### Pattern 4: Inherent Risk Baseline (SECT1-02)
**What:** Market cap x industry matrix showing actuarial filing probability and severity range BEFORE company-specific adjustments.
**When to use:** Computed in BENCHMARK stage, consumed in Executive Summary.
**Design (from CONTEXT.md decisions -- multiplicative adjustment):**
```python
# Step 1: Look up base rate from sectors.json claim_base_rates
base_rate = sectors["claim_base_rates"][sector_code]  # e.g., 3.9% for all-company

# Step 2: Look up market cap adjustment factor
# (S&P 500 companies have 6.1% rate vs 3.9% all-company = 1.56x multiplier)
cap_multiplier = _market_cap_filing_multiplier(market_cap)

# Step 3: Company-specific adjustment from quality score
# Multiplicative: score_multiplier = f(quality_score)
# WIN (86-100): 0.3-0.5x
# WANT (71-85): 0.6-0.9x
# WRITE (51-70): 1.0-1.2x
# WATCH (31-50): 1.3-1.8x
# WALK (11-30): 2.0-3.0x
score_multiplier = _quality_score_multiplier(quality_score, tier)

# Company-adjusted rate = base_rate * cap_multiplier * score_multiplier
adjusted_rate = base_rate * cap_multiplier * score_multiplier
```

The multiplicative approach is actuarially sound because risk factors compound rather than add: a distressed company (2x) in a high-risk sector (1.5x) should be 3x base, not 2.5x.

### Anti-Patterns to Avoid
- **Computing new analysis in BENCHMARK:** BENCHMARK positions existing metrics peer-relative. No new check execution, no new pattern detection. Just comparison.
- **Fetching new peer data in BENCHMARK:** The peer group and their basic financials are already in state from EXTRACT (Phase 3 peer_group.py). Use what's there. If a peer lacks a metric, note the sample size.
- **LLM calls for thesis generation:** Per CONTEXT.md decision, use rich rule-based templates. Deterministic, reproducible, no API cost.
- **Suppressing comparisons with few peers:** Per CONTEXT.md decision, compute percentile ranks even with 3/5 peers having data. Note sample size but don't suppress.
- **Mixing scoring impact into benchmarking:** The SCORE stage already computed all scores. BENCHMARK just adds the peer-relative context. Don't re-run scoring.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Percentile computation | Custom ranking algorithm | Standard percentile rank formula | Well-defined statistical method, handles ties correctly |
| Metric directionality | Per-metric if/else | Metric metadata with `higher_is_better: bool` | Avoids bugs from forgetting to flip direction |
| Severity data | Hardcoded settlement tables | Extend existing scoring.json `severity_ranges` | Config-driven per CLAUDE.md, not hardcoded |
| Filing probability rates | Inline constants | sectors.json `claim_base_rates` section | Config-driven, updateable without code changes |

**Key insight:** The BENCHMARK stage is computationally trivial -- it's just sorting and ranking. The hard part is data model design: defining which metrics get benchmarked, how they map to peer data, and how the executive summary models connect to all 7 sections. Get the models right, and the implementation is straightforward.

## Common Pitfalls

### Pitfall 1: BenchmarkResult Model Expansion
**What goes wrong:** The existing `BenchmarkResult` model has a flat `peer_rankings: dict[str, float]` which could become unwieldy with 30+ metrics.
**Why it happens:** Not planning the metric categories up front.
**How to avoid:** Group metrics by section: financial (operating_margin, debt_to_equity, etc.), governance (governance_score, independence_ratio), market (volatility, short_interest, decline_from_high). Use a nested structure or at least consistent key naming (e.g., `fin.operating_margin`, `gov.independence_ratio`).
**Warning signs:** More than 50 unique keys in peer_rankings with no grouping.

### Pitfall 2: Missing Peer Data Handling
**What goes wrong:** A peer company has market_cap and revenue but no operating_margin (not computed for peers -- they only have basic yfinance data from PeerCompany model).
**Why it happens:** PeerCompany stores: ticker, name, sic_code, industry, market_cap, revenue, peer_score, peer_tier. It does NOT store financial ratios, governance scores, or distress indicators.
**How to avoid:** Two categories of benchmarking: (1) metrics where peer data exists (market_cap, revenue -- from PeerCompany model), (2) metrics where we use the company's own ratio against sector baselines (operating_margin vs. sector median from sectors.json). For (2), use sector_baselines as the "peer" rather than individual company data. This is the pragmatic approach given that we're not running the full EXTRACT pipeline for each peer.
**Warning signs:** Trying to compute Altman Z-Score for peers without their financial data.

### Pitfall 3: Executive Summary Circular Dependencies
**What goes wrong:** SECT1-03/04 (key negatives/positives) need data from SECT7 scoring, but SECT1-02 (inherent risk baseline) feeds INTO the scoring narrative.
**Why it happens:** The executive summary both consumes and contextualizes scoring output.
**How to avoid:** Clear data flow: SCORE stage produces all scoring data -> BENCHMARK adds peer context + inherent risk baseline -> Executive Summary reads everything. The inherent risk baseline is computed in BENCHMARK (not SCORE), and the "Industry base rate: X% | Company-adjusted: Y%" comparison is a display element, not a scoring input.
**Warning signs:** BENCHMARK stage trying to modify ScoringResult.

### Pitfall 4: 500-Line Limit on Executive Summary
**What goes wrong:** The Executive Summary model + builder spans too many fields and templates.
**Why it happens:** SECT1-01 through SECT1-07 is 7 sub-requirements, each with structured output.
**How to avoid:** Split models early:
- `executive_summary.py` (~300L): SECT1-01 through SECT1-07 Pydantic models
- `summary_builder.py` (~400L): Logic to populate all 7 sub-sections from state
- `thesis_templates.py` (~200L): Risk type narrative templates and filling logic
- `key_findings.py` (~300L): Key negatives/positives selection and ranking algorithm
**Warning signs:** Any file approaching 400 lines.

### Pitfall 5: Not Updating Pipeline/CLI Tests
**What goes wrong:** Replacing the BenchmarkStage stub breaks existing pipeline tests.
**Why it happens:** Pipeline tests mock at stage level. The stub had no dependencies; the real implementation needs SCORE stage output.
**How to avoid:** Follow the same pattern as Phase 6: mock BenchmarkStage.run in pipeline/CLI tests (patch at `do_uw.stages.benchmark.BenchmarkStage.run` or patch the whole stage). The real BenchmarkStage tests live in dedicated test files.
**Warning signs:** Pipeline tests failing because BenchmarkStage tries to read state.scoring.

## Code Examples

Verified patterns from the existing codebase:

### Existing BenchmarkResult Model (to extend)
```python
# Source: src/do_uw/models/scoring.py lines 246-277
class BenchmarkResult(BaseModel):
    model_config = ConfigDict(frozen=False)
    peer_group_tickers: list[str] = Field(default_factory=lambda: [], ...)
    peer_rankings: dict[str, float] = Field(default_factory=dict, ...)
    peer_quality_scores: dict[str, float] = Field(default_factory=dict, ...)
    sector_average_score: float | None = Field(default=None, ...)
    relative_position: str | None = Field(default=None, ...)
```

### Existing PeerCompany Model (available data per peer)
```python
# Source: src/do_uw/models/financials.py lines 186-213
class PeerCompany(BaseModel):
    ticker: str
    name: str
    sic_code: str | None = None
    industry: str | None = None
    market_cap: float | None = None  # Available for benchmarking
    revenue: float | None = None     # Available for benchmarking
    peer_score: float = 0.0
    peer_tier: str = ""
```

### Stage Implementation Pattern (from ScoreStage)
```python
# Source: src/do_uw/stages/score/__init__.py
class ScoreStage:
    @property
    def name(self) -> str:
        return "score"

    def validate_input(self, state: AnalysisState) -> None:
        analyze = state.stages.get("analyze")
        if analyze is None or analyze.status != StageStatus.COMPLETED:
            msg = "Analyze stage must be completed before score"
            raise ValueError(msg)

    def run(self, state: AnalysisState) -> None:
        state.mark_stage_running(self.name)
        # ... do work ...
        state.scoring = ScoringResult(...)
        state.mark_stage_completed(self.name)
```

### SourcedValue Pattern (for executive summary fields)
```python
# Source: src/do_uw/models/common.py
class SourcedValue[T](BaseModel):
    value: T
    source: str  # "Filing type + date + URL/CIK reference"
    confidence: Confidence  # HIGH/MEDIUM/LOW
    as_of: datetime
```

### FlaggedItem Pattern (for key findings extraction)
```python
# Source: src/do_uw/models/scoring_output.py lines 273-291
class FlaggedItem(BaseModel):
    description: str         # Human-readable
    source: str              # Data source
    severity: FlagSeverity   # CRITICAL/HIGH/MODERATE/LOW
    scoring_impact: str      # e.g. "F1: +20 points"
    allegation_theory: str   # Related theory (A-E)
    trajectory: str          # NEW/WORSENING/STABLE/IMPROVING
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No peer benchmarking | BenchmarkResult stub exists | Phase 1 | Model ready, implementation needed |
| claim_base_rates not in sectors.json | Need to add | Phase 7 | Required for SECT1-02 inherent risk |
| Flat peer_rankings dict | Should group by section | Phase 7 | Better organization for rendering |
| No executive summary model | Need to create | Phase 7 | SECT1-01 through SECT1-07 |

## Actuarial Data for Inherent Risk Baseline (SECT1-02)

### Filing Probability by Market Cap / Company Type
**Source:** Cornerstone Research / Stanford SCAC 2024-2025 reports (MEDIUM confidence -- published research)

| Population | Annual Filing Rate | Source Year |
|------------|-------------------|-------------|
| All US exchange-listed | 3.9% | 2024 (Cornerstone) |
| S&P 500 | 6.1% | 2024 (Cornerstone) |
| All (historical average) | ~3.5% | 1997-2023 avg |

**Market cap adjustment multipliers (derived):**
| Market Cap Tier | Filing Rate | Multiplier vs Base |
|----------------|-------------|-------------------|
| Mega (>$50B, S&P 500) | ~6.1% | 1.56x |
| Large ($10-50B) | ~5.0% | 1.28x |
| Mid ($2-10B) | ~3.9% | 1.00x (base) |
| Small ($500M-2B) | ~3.5% | 0.90x |
| Micro (<$500M) | ~3.0% | 0.77x |

*Note: Large, Small, and Micro are interpolated. Only All-listed (3.9%) and S&P 500 (6.1%) are directly sourced. Mark as NEEDS CALIBRATION.*

### Filing Rate by Industry Sector
**Source:** D&O Diary / NERA / Cornerstone 2024 data (MEDIUM confidence)

| Sector | % of 2024 Filings | Est. Filing Rate | Rationale |
|--------|-------------------|-----------------|-----------|
| BIOT/Pharma | 21.1% of filings | ~8-10% | 47 of 222 filings; smaller population of listed cos |
| TECH/Software | 16.2% of filings | ~5-7% | 36 filings; large listed population |
| HLTH (non-biotech) | ~5% of filings | ~4% | Healthcare excluding pure pharma/biotech |
| FINS | ~8% of filings | ~4% | Financial services |
| CONS | ~7% of filings | ~4% | Consumer discretionary |
| ENGY | ~3% of filings | ~3% | Energy |
| INDU | ~5% of filings | ~3% | Industrials |
| DEFAULT | -- | 3.9% | All-company base rate |

*These are estimates derived from filing count proportions, not direct probability calculations. Mark as LOW confidence, NEEDS CALIBRATION.*

### Settlement Severity by Market Cap
**Source:** NERA 2024/2025 reports, Cornerstone Research (MEDIUM confidence)

| Market Cap Tier | Median Settlement | Mean Settlement | Source |
|----------------|------------------|-----------------|--------|
| All cases 2025 | $17M | ~$37M | NERA 2025 Full-Year |
| All cases 2024 | $14M | $42.4M | Cornerstone 2024 |
| Accounting cases 2024 | $12M | -- | Cornerstone 2024 |

The existing `severity_ranges` in scoring.json already captures settlement ranges by market cap (MEGA: $25-150M, LARGE: $15-75M, MID: $8-40M, SMALL: $4-20M, MICRO: $2-10M). These align reasonably with published data and should be referenced for SECT1-02.

### Recommendation for sectors.json Extension
Add `claim_base_rates` section to sectors.json using research-based estimates:
```json
{
  "claim_base_rates": {
    "description": "Annual SCA filing probability by sector. NEEDS CALIBRATION.",
    "source": "Derived from Cornerstone/NERA 2024-2025 reports",
    "BIOT": 8.0,
    "TECH": 6.0,
    "HLTH": 4.5,
    "FINS": 4.0,
    "CONS": 4.0,
    "ENGY": 3.0,
    "INDU": 3.0,
    "STPL": 2.5,
    "UTIL": 2.0,
    "REIT": 3.5,
    "DEFAULT": 3.9
  }
}
```

## Metrics for Peer Benchmarking

### Category 1: Metrics with Peer Data Available (from PeerCompany)
These can be benchmarked directly because PeerCompany stores the data:
- Market capitalization (ranking within peer group)
- Revenue (ranking within peer group)

### Category 2: Financial Ratios (company vs sector baselines)
These are computed for the subject company but NOT for individual peers. Benchmark against sector baselines in sectors.json:
- Operating margin (company vs sector typical)
- Debt-to-equity / Debt-to-EBITDA (company vs sector `leverage_debt_ebitda` baselines)
- Current ratio (company vs general thresholds)
- Short interest % of float (company vs sector `short_interest` baselines)
- Volatility 90d (company vs sector `volatility_90d` baselines)

### Category 3: Risk Scores (company-specific, use sector baselines for context)
- Quality score vs sector average (BenchmarkResult.sector_average_score)
- Governance quality score vs peer percentile (GovernanceQualityScore.peer_percentile)
- Leadership stability vs peer percentile (LeadershipStability.stability_peer_percentile)
- Adverse event score vs peer rank (AdverseEventScore.peer_rank)
- Distress indicators (Altman Z vs zone thresholds -- already categorized)

### Recommendation: Metric Registry
Create a metric registry mapping metric names to:
1. Where the company value lives in state
2. Where the peer/baseline value comes from
3. Whether higher_is_better or lower_is_better
4. The section this metric belongs to (SECT2-SECT7)

This avoids hardcoding metric-by-metric logic and enables the RENDER stage to iterate metrics systematically.

## Executive Summary Model Design

### SECT1-01: Company Snapshot
```python
class CompanySnapshot(BaseModel):
    """Key metrics header block pulled from Section 2."""
    ticker: str
    company_name: str
    market_cap: SourcedValue[float] | None
    revenue: SourcedValue[float] | None
    employee_count: SourcedValue[int] | None
    industry: str
    sic_code: str
    exchange: str
```
Simple extraction from existing CompanyProfile fields.

### SECT1-02: InherentRiskBaseline
```python
class InherentRiskBaseline(BaseModel):
    """Actuarial filing probability BEFORE company-specific adjustments."""
    sector_base_rate_pct: float          # From sectors.json claim_base_rates
    market_cap_adjusted_rate_pct: float  # Base * cap_multiplier
    company_adjusted_rate_pct: float     # Final rate after score adjustment
    severity_range_25th: float           # Settlement at 25th percentile
    severity_range_50th: float           # Settlement at 50th percentile
    severity_range_75th: float           # Settlement at 75th percentile
    severity_range_95th: float           # Settlement at 95th percentile
    sector_name: str
    market_cap_tier: str
    methodology_note: str = "NEEDS CALIBRATION"
```

### SECT1-03/04: Key Findings
```python
class KeyFinding(BaseModel):
    """Single key negative or positive finding."""
    evidence_narrative: str       # What was found and why it matters
    section_origin: str           # Which section surfaced this (SECT2-SECT7)
    scoring_impact: str           # Points deducted/preserved and factor
    theory_mapping: str           # Allegation theory (neg) or defense theory (pos)

class KeyFindings(BaseModel):
    """Top 5 negatives and top 5 positives."""
    negatives: list[KeyFinding]   # Exactly 5 (or fewer if insufficient findings)
    positives: list[KeyFinding]   # Exactly 5 (or fewer)
```

### SECT1-05/06: Already in ScoringResult
- ClaimProbability (SECT1-05): Already in state.scoring.claim_probability
- TowerRecommendation (SECT1-06): Already in state.scoring.tower_recommendation
These are REFERENCED, not re-computed.

### SECT1-07: Deal Context
```python
class DealContext(BaseModel):
    """Deal-specific fields -- placeholders in ticker-only mode."""
    layer_quoted: str = ""
    premium: str = ""
    carrier_lineup: str = ""
    tower_structure: str = ""
    additional_notes: str = ""
    is_placeholder: bool = True  # True when running ticker-only
```

## Open Questions

Things that couldn't be fully resolved:

1. **Peer financial ratio data availability**
   - What we know: PeerCompany stores only market_cap and revenue. No operating_margin, no debt_to_equity, no distress scores.
   - What's unclear: Should we fetch additional financial data for peers in BENCHMARK (requires yfinance calls), or benchmark against sector baselines?
   - Recommendation: Use sector baselines for financial ratios. Per CLAUDE.md, "No data acquisition outside stages/acquire/." BENCHMARK should not make network calls. The sector baselines in sectors.json provide sufficient context. If the user wants richer peer comparison, that's a Phase 9+ enhancement. Note this as a limitation.

2. **Exact filing probability rates by sector**
   - What we know: All-company 3.9%, S&P 500 6.1% (both Cornerstone 2024). Filing counts by SIC group available.
   - What's unclear: Population-adjusted per-sector rates require knowing how many companies are listed per SIC group, which varies year to year.
   - Recommendation: Use the research-based estimates in the table above, clearly labeled NEEDS CALIBRATION. The delta (company vs industry) is more valuable than the absolute number -- and the delta is reliable even with approximate base rates.

3. **Key positives selection when company has few positive signals**
   - What we know: The FlaggedItem model tracks negatives well (severity, scoring impact). Positives are less explicitly tracked -- they're the absence of negatives (e.g., "no active SCA" is positive).
   - What's unclear: How to generate positive KeyFindings from the scoring data.
   - Recommendation: Define a catalog of positive indicators mapped to checks that pass: no active litigation, clean audit opinion, stable leadership, strong governance score, low short interest, etc. Each positive is paired with the check IDs that support it and the defense theory it strengthens.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: All source files read directly from `/Users/gorlin/projects/research/src/do_uw/`
- scoring.json: Severity ranges, tier multipliers, tower positions verified from brain/scoring.json
- sectors.json: Sector baselines for short interest, volatility, leverage verified
- Existing models: BenchmarkResult, ScoringResult, PeerGroup, PeerCompany verified

### Secondary (MEDIUM confidence)
- [Cornerstone Research 2024 Year in Review](https://www.cornerstone.com/insights/press-releases/securities-class-action-filings-increase-for-second-consecutive-year-in-2024/): 3.9% all-company rate, 6.1% S&P 500 rate, 225 total filings
- [NERA 2025 Full-Year Review](https://www.nera.com/insights/publications/2026/recent-trends-in-securities-class-action-litigation--2025-full-y.html): $17M median settlement, $2.9B aggregate, 234 resolutions
- [D&O Diary 2024 Filing Analysis](https://www.dandodiary.com/2025/01/articles/securities-litigation/federal-court-securities-class-action-lawsuit-filings-increased-in-2024/): SIC code filing breakdown, sector percentages
- [NERA 2024 Full-Year Review](https://www.nera.com/insights/publications/2025/recent-trends-in-securities-class-action-litigation--2024-full-y.html): $3.8B aggregate settlements, settlement-to-losses ratios

### Tertiary (LOW confidence)
- Per-sector filing probability estimates: Derived from filing counts divided by estimated sector population. Not directly published by any authoritative source. NEEDS CALIBRATION.
- Market cap tier multipliers: Only two data points (all-company 3.9%, S&P 500 6.1%). Intermediate tiers are interpolated. NEEDS CALIBRATION.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all patterns from existing codebase
- Architecture: HIGH -- BenchmarkResult model exists, data flow is clear, stage pattern well-established
- Peer benchmarking metrics: HIGH -- metrics identified from existing models, sector baselines available
- Executive summary models: HIGH -- requirements are specific (SECT1-01 through SECT1-07), data sources identified
- Actuarial data: MEDIUM -- filing rates and settlement data from published sources, but sector-level rates are estimates
- Pitfalls: HIGH -- identified from codebase analysis and prior phase patterns

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (stable domain, no fast-moving library dependencies)
