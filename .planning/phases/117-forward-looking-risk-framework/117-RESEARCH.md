# Phase 117: Forward-Looking Risk Framework - Research

**Researched:** 2026-03-19
**Domain:** Forward-looking statement extraction, management credibility scoring, monitoring triggers, underwriting posture recommendation, quick screen/trigger matrix
**Confidence:** HIGH

## Summary

Phase 117 introduces five major new rendering sections (Forward-Looking Statement Risk Map, Management Credibility, Monitoring Triggers, Suggested Underwriting Posture, Quick Screen / Trigger Matrix) plus three scoring enhancements (ZER-001 verification, Watch Items, Posture). This is the largest Phase 117 scope in v8.0, touching extraction (LLM + yfinance), analysis/benchmark (credibility scoring, miss risk, posture algorithm), brain YAML config (posture decision matrix, nuclear triggers), and rendering (5+ new context builders, 5+ new Jinja2 templates).

The existing codebase provides strong foundations: 79 FWRD signals in brain YAML, `EarningsGuidanceAnalysis` model with quarter-by-quarter records and beat rate, `earnings_guidance.py` extraction from yfinance, `tier_explanation.py` for algorithmic tier analysis, `_signal_consumer.py` for signal aggregation, `narrative_generator.py` for LLM narratives, and forward-looking template stubs in `templates/html/sections/forward_looking/`. The scoring.json tier definitions already contain `action`, `pricing_multiplier`, and `tower_position` per tier.

**Primary recommendation:** Implement in 6 waves: (1) Pydantic models + brain YAML config, (2) extraction/credibility engine, (3) analysis/posture algorithm, (4) context builders, (5) Jinja2 templates, (6) wiring + integration tests. Keep the posture decision matrix in brain YAML per CONTEXT.md decision. Reuse `tier_explanation.py` pattern for algorithmic posture generation.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **LLM extraction from 10-K + 8-K** for forward-looking statements: Extract from 10-K (risk factors, MD&A) and 8-K (earnings releases, guidance updates) using LLM in EXTRACT stage. Map each to: metric guided, current value, guidance/target, miss risk assessment, SCA theory if missed
- **Miss risk algorithm**: Compare current trajectory to guidance midpoint. >10% gap = HIGH, 5-10% = MEDIUM, <5% = LOW. Adjust by management credibility score (track record <50% beat -> +1 level, >80% beat -> -1 level)
- **SCA relevance mapping**: Deterministic mapping, not LLM-generated. HIGH miss risk + material metric -> "10b-5: misleading forward guidance". MED miss risk + financial metric -> "Potential earnings fraud theory"
- **yfinance earnings + LLM from 8-K** for management credibility: yfinance provides historical EPS estimates vs actuals. LLM extracts company-specific revenue/margin guidance from 8-K earnings releases. Track record: % of quarters where management beat their own guidance. Credibility score: HIGH (>80% beat), MEDIUM (50-80%), LOW (<50%)
- **Company-specific thresholds for monitoring triggers**: Stock below support level, insider selling pace >2x current quarterly rate, EPS miss >10%, CEO/C-suite departure, SCA filing (SCAC match), Peer SCA (same SIC code). All thresholds specific to THIS company.
- **Algorithmic from scoring tier for underwriting posture**: Decision matrix in brain YAML config mapping tier to posture (WIN->WANT->WRITE->WATCH->WALK->NO_TOUCH). Specific factor overrides: Active SCA (F.1>0) -> add litigation exclusion. Heavy insider selling (F.7>5) -> add insider monitoring. Restatement (F.3>0) -> add financial reporting exclusion.
- **Signal results aggregation for quick screen**: Scan all signal results for TRIGGERED status with red/yellow threshold_level. Group by section. Each flag links to section anchor in HTML worksheet.
- **5 nuclear triggers verified with positive evidence**: Active SCA (Stanford SCAC match), SEC investigation/enforcement (AAER match), Financial restatement (10-K disclosure), CEO/CFO departure under pressure (8-K Item 5.02), Going concern opinion (audit opinion). Display: "0/5 nuclear triggers fired"
- **Posture decision matrix lives in brain YAML config**, not hardcoded Python

### Claude's Discretion
- Exact LLM prompt design for forward statement extraction from 10-K/8-K
- How to handle companies that don't provide numeric guidance (qualitative-only)
- Prospective check data sources and assessment methodology
- Whether growth estimates table (FORWARD-05) uses yfinance consensus or extracted guidance
- Exact section placement in the HTML worksheet (new section or subsection of existing)
- Alternative forward-looking signals implementation (FORWARD-06: short interest trend, analyst sentiment, buyback support)

### Deferred Ideas (OUT OF SCOPE)
- Real-time monitoring dashboard (different product -- worksheet is point-in-time)
- Automated bind/decline decisions (system augments judgment, doesn't replace it)
- Earnings call transcript analysis (paid API, out of scope for public-data-only constraint)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FORWARD-01 | Forward-Looking Statement Risk Map: every publicly guided metric -> current value -> guidance/claim -> miss risk -> SCA relevance if missed | New LLM extraction schema for 10-K/8-K forward statements; new Pydantic model `ForwardStatementRiskMap`; miss risk algorithm using credibility-adjusted gap analysis; deterministic SCA theory mapping |
| FORWARD-02 | Management Credibility table: quarter-by-quarter guidance vs actual with beat/miss/magnitude, track record %, credibility score | Extends existing `EarningsGuidanceAnalysis` model and `earnings_guidance.py` extraction; adds LLM extraction from 8-K for company-specific guidance; computes credibility score from beat rate |
| FORWARD-03 | 2026 Catalysts table: event/timing/impact if negative/litigation risk | New LLM extraction from 10-K/8-K for upcoming catalysts; stored on forward-looking state model; rendered as traffic-light table |
| FORWARD-04 | Monitoring Triggers table: trigger/action/threshold for post-bind monitoring | New analysis module computing company-specific thresholds from existing state data (stock support, insider pace, EPS history); brain YAML for trigger definitions |
| FORWARD-05 | Growth Estimates table: current quarter, current year, next year EPS estimates with trend assessment | Uses yfinance analyst estimates (forward EPS) from existing market_data; new context builder to extract and format |
| FORWARD-06 | Alternative Forward-Looking Signals: short interest trend, analyst sentiment shifts, buyback support | Reuses existing `ShortInterestProfile`, `AnalystSentimentProfile` data; new context builder aggregating and formatting |
| SCORE-02 | ZER-001 Verifications: explicit verification of zero-scored factors (F.1=0, F.3=0, F.9=0) with positive evidence | New analysis function scanning factor_scores for zero-scored factors; extracts positive evidence from signal results; context builder + template |
| SCORE-03 | Suggested Underwriting Posture table: decision/retention/limit/pricing/exclusions/monitoring/re-evaluation with rationale | Brain YAML posture config + algorithmic derivation from tier + factor overrides; reuses tier_explanation.py pattern |
| SCORE-05 | Watch Items: specific items requiring ongoing attention with clear thresholds for re-evaluation | Derived from signal results near thresholds + forward-looking risk map; stored on analysis state |
| TRIGGER-01 | Trigger Matrix Summary: all RED/YELLOW flags with flag level, deep-dive section routing, routed checkmark | Uses `get_signals_by_prefix` and signal aggregation from `_signal_consumer.py`; maps threshold_level to section anchors |
| TRIGGER-02 | Prospective Checks: forward-looking checks with findings and traffic light status | New analysis computing prospective risk assessments from forward data + scoring; 5 check categories per CONTEXT.md |
| TRIGGER-03 | Nuclear triggers checked and reported (0 triggered = clean) | Deterministic checks against existing state data: SCAC match, AAER, restatement flag, Item 5.02 departure, going concern |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.x (existing) | New models for ForwardStatement, MonitoringTrigger, PostureRecommendation, QuickScreen | Project standard -- all state models are Pydantic v2 |
| anthropic + instructor | existing | LLM extraction of forward-looking statements from 10-K/8-K | Existing LLMExtractor pattern in `stages/extract/llm/` |
| yfinance | existing | Earnings history, analyst estimates, forward EPS | Already used for `EarningsGuidanceAnalysis` |
| jinja2 | existing | 5+ new HTML templates for forward-looking sections | Project standard for all HTML rendering |
| PyYAML | existing | Brain YAML config for posture decision matrix | Project standard for brain signal/config loading |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | existing | Unit/integration tests for all new modules | Every new file gets companion tests |

### Alternatives Considered
None -- this phase uses exclusively existing project dependencies. No new libraries needed.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  models/
    forward_looking.py           # NEW: ForwardStatement, CredibilityScore, MonitoringTrigger, PostureRecommendation, QuickScreenResult, NuclearTriggerCheck
  brain/
    config/
      underwriting_posture.yaml  # NEW: Tier->posture decision matrix + factor overrides
      monitoring_triggers.yaml   # NEW: Trigger definitions + default thresholds
      nuclear_triggers.yaml      # NEW: 5 nuclear trigger definitions + data sources
  stages/
    extract/
      forward_statements.py      # NEW: LLM extraction of forward-looking statements from 10-K/8-K
      llm/schemas/
        forward_looking.py       # NEW: Pydantic schema for LLM forward statement extraction
    analyze/
      credibility_engine.py      # NEW: Management credibility scoring from earnings data + LLM-extracted guidance
      miss_risk.py               # NEW: Miss risk computation + SCA relevance mapping
    benchmark/
      monitoring_triggers.py     # NEW: Company-specific threshold computation
      underwriting_posture.py    # NEW: Algorithmic posture derivation from tier + factor overrides
      quick_screen.py            # NEW: Signal aggregation for trigger matrix + nuclear checks
  stages/render/
    context_builders/
      forward_risk_map.py        # NEW: Forward-Looking Statement Risk Map context
      credibility_context.py     # NEW: Management Credibility context
      monitoring_context.py      # NEW: Monitoring Triggers context
      posture_context.py         # NEW: Suggested Underwriting Posture context
      quick_screen_context.py    # NEW: Quick Screen / Trigger Matrix context
  templates/html/sections/
    forward_looking/
      risk_map.html.j2           # NEW: Forward-Looking Statement Risk Map
      credibility.html.j2        # NEW: Management Credibility table
      catalysts.html.j2          # NEW: 2026 Catalysts table
      monitoring_triggers.html.j2 # NEW: Monitoring Triggers table
      growth_estimates.html.j2   # NEW: Growth Estimates table
      alt_signals.html.j2        # NEW: Alternative Forward-Looking Signals
    scoring/
      zero_verification.html.j2  # NEW: ZER-001 verifications
      underwriting_posture.html.j2 # NEW: Posture table
      watch_items.html.j2        # NEW: Watch Items
    trigger_matrix.html.j2       # NEW: Quick Screen / Trigger Matrix (possibly top-level)
tests/
  models/
    test_forward_looking.py      # NEW
  stages/
    extract/
      test_forward_statements.py # NEW
    analyze/
      test_credibility_engine.py # NEW
      test_miss_risk.py          # NEW
    benchmark/
      test_monitoring_triggers.py # NEW
      test_underwriting_posture.py # NEW
      test_quick_screen.py       # NEW
    render/
      test_forward_context_builders.py # NEW
      test_posture_context.py    # NEW
      test_quick_screen_template.py # NEW
```

### Pattern 1: Brain YAML Config for Posture Decision Matrix
**What:** Store the tier-to-posture mapping in brain YAML rather than Python code, following the "brain portability" principle from CONTEXT.md.
**When to use:** For all configuration that maps tiers to underwriting actions, factor overrides to exclusions, and monitoring frequencies.
**Example:**
```yaml
# brain/config/underwriting_posture.yaml
posture_matrix:
  WIN:
    decision: "Full terms"
    retention: "Standard"
    limit: "Full tower"
    pricing: "At-model"
    exclusions: "Standard"
    monitoring: "Annual review"
    re_evaluation: "At renewal"
  WANT:
    decision: "Full terms with monitoring"
    retention: "Standard"
    limit: "Full tower"
    pricing: "Slight adjustment"
    exclusions: "Standard"
    monitoring: "Semi-annual review"
    re_evaluation: "6 months"
  # ... WRITE, WATCH, WALK, NO_TOUCH

factor_overrides:
  - condition: "F1 > 0"  # Active SCA
    add_exclusion: "Litigation exclusion (pending/prior matters)"
    add_monitoring: "Quarterly litigation status check"
    rationale: "Active SCA creates direct loss exposure"
  - condition: "F7 > 5"  # Heavy insider selling
    add_monitoring: "Monthly insider trading report"
    rationale: "Heavy selling indicates potential scienter evidence"
  - condition: "F3 > 0"  # Restatement
    add_exclusion: "Financial reporting exclusion"
    rationale: "Restatement history increases restatement recurrence risk"
```

### Pattern 2: Algorithmic Posture Generation (reuses tier_explanation.py pattern)
**What:** Purely algorithmic (no LLM) generation of underwriting posture recommendation with company-specific rationale.
**When to use:** In BENCHMARK stage, after scoring is complete.
**Example:**
```python
def generate_posture(
    scoring_result: ScoringResult,
    posture_config: dict,
    state: AnalysisState,
) -> PostureRecommendation:
    """Derive posture from tier + apply factor overrides."""
    tier = scoring_result.tier.tier.value
    base = posture_config["posture_matrix"][tier]
    recommendation = PostureRecommendation(**base)

    # Apply factor overrides
    for override in posture_config["factor_overrides"]:
        factor_id = override["condition"].split()[0]  # e.g., "F1"
        threshold = float(override["condition"].split()[-1])
        factor_score = _get_factor_score(scoring_result, factor_id)
        if factor_score > threshold:
            recommendation.apply_override(override)

    return recommendation
```

### Pattern 3: Nuclear Trigger Verification (deterministic checks against state)
**What:** Five explicit checks against existing state data with positive evidence requirement.
**When to use:** During BENCHMARK stage quick screen computation.
**Example:**
```python
def check_nuclear_triggers(state: AnalysisState) -> list[NuclearTriggerCheck]:
    """Verify 5 nuclear triggers with positive evidence."""
    checks = []
    # 1. Active SCA: check litigation.active_scas
    scac_match = bool(state.extracted.litigation and
                      state.extracted.litigation.active_cases)
    checks.append(NuclearTriggerCheck(
        trigger_id="NUC-01",
        name="Active Securities Class Action",
        fired=scac_match,
        evidence="Stanford SCAC: [case names]" if scac_match else "Stanford SCAC clean",
        source="Stanford SCAC database",
    ))
    # ... 4 more checks
    return checks
```

### Pattern 4: Signal Aggregation for Trigger Matrix
**What:** Scan all signal results for TRIGGERED with red/yellow threshold_level, group by worksheet section, map each to section anchor for deep-dive routing.
**When to use:** Quick Screen context builder.
**Example:**
```python
from do_uw.stages.render.context_builders._signal_consumer import (
    get_signals_by_prefix,
    signal_to_display_level,
)

def build_trigger_matrix(signal_results: dict) -> list[TriggerMatrixRow]:
    """Aggregate all RED/YELLOW signals into trigger matrix."""
    rows = []
    for signal_id, result in signal_results.items():
        if result.get("status") == "TRIGGERED":
            level = result.get("threshold_level", "")
            if level in ("red", "yellow"):
                section = _signal_id_to_section(signal_id)
                rows.append(TriggerMatrixRow(
                    signal_id=signal_id,
                    flag_level="RED" if level == "red" else "YELLOW",
                    section_anchor=_section_to_anchor(section),
                    do_context=result.get("do_context", ""),
                ))
    return sorted(rows, key=lambda r: (0 if r.flag_level == "RED" else 1, r.signal_id))
```

### Anti-Patterns to Avoid
- **D&O commentary in Python or Jinja2:** All D&O commentary MUST come from brain YAML do_context blocks. Renderers display, they don't interpret. (Per Phase 115/116 decisions.)
- **Hardcoded posture thresholds in Python:** Decision matrix lives in brain YAML, not Python code. Python reads YAML, applies it algorithmically.
- **LLM at render time:** Forward statement extraction happens in EXTRACT stage. Posture derivation is algorithmic in BENCHMARK. Templates only format pre-computed data.
- **Monolithic context builder:** With 5 new rendering sections, each needs its own context builder file (<300 lines per BUILD-07). Do NOT create one giant forward_looking_context.py.
- **Scoring logic outside stages/score/:** The posture derivation consumes scoring results but does NOT modify them. It lives in BENCHMARK stage as a post-scoring computation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Earnings beat/miss history | Custom earnings parser | Existing `EarningsGuidanceAnalysis` + `earnings_guidance.py` | Already parses yfinance earnings_dates into quarter records with beat rate |
| Signal result aggregation | Custom signal scanner | `_signal_consumer.py` `get_signals_by_prefix()`, `signal_to_display_level()` | Established typed extraction layer with brain metadata enrichment |
| LLM extraction | Custom API calls | `LLMExtractor` class from `stages/extract/llm/extractor.py` | Handles caching, cost tracking, rate limiting, schema validation |
| Tier boundary analysis | Custom tier logic | `tier_explanation.py` `generate_tier_explanation()` pattern | Already computes counterfactuals, adjacency, boundary proximity |
| Brain YAML loading | Custom YAML parser | `brain_unified_loader.load_signals()` | Standard brain loading with caching |
| Template rendering | Custom HTML | Jinja2 templates in `templates/html/sections/` | Project standard, with design system CSS classes |

**Key insight:** This phase composes existing infrastructure (signals, scoring, extraction, rendering) into new analytical views. The heavy lifting is in the composition logic and brain YAML config, not in building new infrastructure.

## Common Pitfalls

### Pitfall 1: Forward Statements from Companies That Don't Guide
**What goes wrong:** ~30-40% of public companies provide no explicit numeric guidance. LLM extraction returns empty, and the Forward-Looking Statement Risk Map is blank.
**Why it happens:** Not all companies issue EPS/revenue guidance. Some provide only qualitative outlook statements.
**How to avoid:** Design the LLM extraction prompt to capture both quantitative guidance (EPS, revenue targets) AND qualitative forward statements ("We expect continued growth", "We anticipate headwinds"). For qualitative-only companies, populate the risk map with qualitative claims + risk assessment. The template should gracefully handle both modes.
**Warning signs:** Risk map is empty for a Fortune 500 company that definitely discusses outlook in MD&A.

### Pitfall 2: Credibility Score Based on Consensus vs Company Guidance
**What goes wrong:** The beat rate from yfinance compares EPS estimate (analyst consensus) vs actual. This is ANALYST consensus, not COMPANY guidance. A company might consistently beat analyst estimates while missing its own guidance.
**Why it happens:** yfinance `earnings_dates` provides `EPS Estimate` (consensus) not company guidance. Per user feedback: "EPS must be company guidance not analyst consensus."
**How to avoid:** Use yfinance consensus as a fallback/secondary signal. Primary credibility should come from LLM-extracted company-specific guidance from 8-K earnings releases (Item 2.02). If LLM extraction finds explicit guidance numbers, use those. If not, fall back to yfinance consensus with a MEDIUM confidence flag.
**Warning signs:** Companies with HIGH credibility that actually missed their own guidance repeatedly.

### Pitfall 3: Over-counting Signals in Trigger Matrix
**What goes wrong:** With 563 brain signals, the trigger matrix could show 50+ red/yellow flags, making it useless for quick screening.
**Why it happens:** Many signals are evaluative/display signals that fire at low thresholds.
**How to avoid:** Filter the trigger matrix to only include signals with `signal_class: evaluative` or `signal_class: inference` that have genuine red/yellow thresholds (not display-type thresholds). Group by section and show count + top 3 per section, not every individual signal. The nuclear triggers section provides the truly critical binary checks.
**Warning signs:** Matrix has 40+ rows for a clean company.

### Pitfall 4: Posture Overrides Conflicting
**What goes wrong:** Multiple factor overrides fire simultaneously, creating contradictory recommendations (e.g., "full terms" from tier but "decline consideration" from active SCA override).
**Why it happens:** Factor overrides are additive -- they modify the base posture but can stack.
**How to avoid:** Define override priority in brain YAML. Nuclear triggers (NUC-01 through NUC-05) should override everything -- if any nuclear trigger fires, the posture should include explicit escalation language. Factor overrides add conditions/exclusions but don't override the base decision unless a threshold is crossed (e.g., F.1 = 20/20 should force WALK/NO_TOUCH regardless of composite score, which is already handled by red flag ceilings).
**Warning signs:** Posture says "Full terms" but nuclear trigger section shows active SCA.

### Pitfall 5: State Model Bloat
**What goes wrong:** Adding 5-6 new model classes to a single models/ file pushes it over 500 lines.
**Why it happens:** Phase 117 introduces substantial new data structures.
**How to avoid:** Create a NEW file `models/forward_looking.py` for all forward-looking models. Add it to `ExtractedData` or `AnalysisResults` as appropriate. Keep under 500 lines by using focused, flat model classes.
**Warning signs:** Any single .py file exceeding 400 lines during implementation.

### Pitfall 6: Missing Source Attribution
**What goes wrong:** Forward statements and credibility data lack source/confidence fields, violating the data integrity non-negotiable.
**Why it happens:** LLM-extracted data needs explicit source attribution (filing type, date, accession number).
**How to avoid:** Every forward statement must carry: source_filing (10-K accession or 8-K accession), extraction_date, confidence (MEDIUM for LLM-extracted, HIGH for yfinance numeric). Use the existing `SourcedValue[T]` pattern from `models/common.py`.
**Warning signs:** Template shows forward statements without source footnotes.

## Code Examples

### Forward Statement Pydantic Model
```python
# models/forward_looking.py
from pydantic import BaseModel, Field
from do_uw.models.common import SourcedValue

class ForwardStatement(BaseModel):
    """Single forward-looking claim extracted from SEC filings."""
    metric_name: str = Field(description="Metric guided: revenue, EPS, margin, etc.")
    current_value: SourcedValue[str] | None = Field(default=None, description="Current/latest value")
    guidance_claim: str = Field(default="", description="The forward-looking claim or target")
    guidance_type: str = Field(default="QUANTITATIVE", description="QUANTITATIVE or QUALITATIVE")
    miss_risk: str = Field(default="LOW", description="HIGH, MEDIUM, LOW")
    miss_risk_rationale: str = Field(default="", description="Why this miss risk level")
    sca_relevance: str = Field(default="", description="SCA theory if missed")
    source_filing: str = Field(default="", description="10-K or 8-K accession")
    source_date: str = Field(default="", description="Filing date")

class CredibilityScore(BaseModel):
    """Management credibility assessment from guidance track record."""
    beat_rate_pct: float = Field(default=0.0, description="% of quarters beating own guidance")
    quarters_assessed: int = Field(default=0)
    credibility_level: str = Field(default="MEDIUM", description="HIGH/MEDIUM/LOW")
    source: str = Field(default="yfinance + 8-K LLM")

class MonitoringTrigger(BaseModel):
    """Single monitoring trigger for post-bind surveillance."""
    trigger_name: str = Field(description="What to monitor")
    action: str = Field(description="What to do when triggered")
    threshold: str = Field(description="Company-specific threshold value")
    current_value: str = Field(default="", description="Current state for reference")
    source: str = Field(default="")

class PostureElement(BaseModel):
    """Single element of the underwriting posture recommendation."""
    element: str = Field(description="decision, retention, limit, pricing, exclusions, monitoring, re_evaluation")
    recommendation: str = Field(description="The recommendation")
    rationale: str = Field(description="Company-specific reasoning")

class NuclearTriggerCheck(BaseModel):
    """Verification result for one nuclear trigger."""
    trigger_id: str = Field(description="NUC-01 through NUC-05")
    name: str = Field(description="Human-readable trigger name")
    fired: bool = Field(default=False)
    evidence: str = Field(default="", description="Positive evidence for status")
    source: str = Field(default="")
```

### LLM Forward Statement Extraction Schema
```python
# stages/extract/llm/schemas/forward_looking.py
from pydantic import BaseModel, Field

class ExtractedForwardStatement(BaseModel):
    """LLM extraction schema for forward-looking statements from 10-K/8-K."""
    metric: str = Field(default="", description="The metric being guided (revenue, EPS, margin, etc.)")
    target_value: str = Field(default="", description="Guided value or range (e.g., '$4.50-$4.70 EPS')")
    timeframe: str = Field(default="", description="When (FY2026, Q2 2026, etc.)")
    context: str = Field(default="", description="Surrounding context from filing (max 300 chars)")
    is_quantitative: bool = Field(default=False, description="True if specific numbers provided")

class ForwardLookingExtraction(BaseModel):
    """Complete forward-looking extraction from a single filing."""
    forward_statements: list[ExtractedForwardStatement] = Field(
        default_factory=list,
        description="All forward-looking claims found in filing",
    )
    guidance_changes: list[str] = Field(
        default_factory=list,
        description="Any guidance raises, cuts, or withdrawals noted",
    )
    catalyst_events: list[str] = Field(
        default_factory=list,
        description="Upcoming events mentioned (earnings, product launch, regulatory decision, etc.)",
    )
```

### Miss Risk Algorithm
```python
# stages/analyze/miss_risk.py
def compute_miss_risk(
    current_value: float | None,
    guidance_midpoint: float | None,
    credibility_level: str,
) -> str:
    """Compute miss risk level with credibility adjustment.

    Base: >10% gap = HIGH, 5-10% = MEDIUM, <5% = LOW
    Adjustment: credibility <50% -> +1 level, >80% -> -1 level
    """
    if current_value is None or guidance_midpoint is None:
        return "UNKNOWN"

    gap_pct = abs(current_value - guidance_midpoint) / abs(guidance_midpoint) * 100

    # Base risk level
    if gap_pct > 10:
        base = 2  # HIGH
    elif gap_pct > 5:
        base = 1  # MEDIUM
    else:
        base = 0  # LOW

    # Credibility adjustment
    if credibility_level == "LOW":  # <50% beat rate
        base = min(base + 1, 2)
    elif credibility_level == "HIGH":  # >80% beat rate
        base = max(base - 1, 0)

    return ["LOW", "MEDIUM", "HIGH"][base]
```

### Posture Brain YAML Config Loading
```python
# stages/benchmark/underwriting_posture.py
from pathlib import Path
import yaml

def load_posture_config() -> dict:
    """Load posture decision matrix from brain YAML."""
    config_path = Path(__file__).parent.parent.parent / "brain" / "config" / "underwriting_posture.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Generic risk summary | Company-specific forward-looking risk map | Phase 117 (new) | Every guided metric mapped to miss risk and SCA theory |
| Analyst consensus = credibility | Company guidance vs actual | Phase 117 (new) | Per user feedback: company guidance, not analyst consensus |
| Generic "monitor this" | Company-specific trigger thresholds | Phase 117 (new) | Triggers use actual company data (support level, insider pace) |
| Tier = recommendation | Algorithmic posture with factor overrides | Phase 117 (new) | Structured decision table with company-specific rationale |

**Deprecated/outdated:**
- The existing `EarningsGuidanceAnalysis.beat_rate` uses yfinance consensus -- this will be supplemented (not replaced) with LLM-extracted company guidance credibility.

## Open Questions

1. **Growth Estimates Data Source (FORWARD-05)**
   - What we know: yfinance provides `forwardEps`, `forwardPE`, earnings estimates via `analyst_info`
   - What's unclear: Whether yfinance analyst estimates are sufficiently detailed (current Q, current Y, next Y breakdown)
   - Recommendation: Use yfinance as primary source. If yfinance provides granular forward estimates, use those. If not, supplement with what's extractable from 8-K earnings releases. Flag as Claude's Discretion per CONTEXT.md.

2. **Quick Screen Section Placement**
   - What we know: CONTEXT.md says "possibly in Section 1 (Executive Summary) or standalone section near the top"
   - What's unclear: Whether it's a subsection of the executive summary or a new top-level section
   - Recommendation: Place as a new subsection within the executive summary section (Section 1), immediately after key findings. This is Claude's Discretion per CONTEXT.md. The nuclear trigger verification is the single most important piece -- it should be at the very top.

3. **Prospective Checks Data Sources (TRIGGER-02)**
   - What we know: 5 check categories (earnings expectations, major contract/deal, regulatory decision, competitive disruption, macro headwinds)
   - What's unclear: What data feeds each check. Some require web search results (competitive disruption, macro headwinds) that may not be structured in state.
   - Recommendation: Map each check to available state data: (1) earnings expectations = forward EPS from yfinance, (2) major contract = 10-K/8-K extraction, (3) regulatory = regulatory_data from ACQUIRE, (4) competitive disruption = sector risk from classification, (5) macro headwinds = web search blind spot results. Some will be UNKNOWN if data unavailable -- show honestly.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/models/test_forward_looking.py tests/stages/analyze/test_credibility_engine.py tests/stages/analyze/test_miss_risk.py tests/stages/benchmark/test_underwriting_posture.py tests/stages/benchmark/test_quick_screen.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FORWARD-01 | Forward statement risk map renders with metric/value/guidance/risk/SCA | unit + integration | `uv run pytest tests/stages/extract/test_forward_statements.py -x` | Wave 0 |
| FORWARD-02 | Management credibility table with beat/miss/magnitude/credibility score | unit | `uv run pytest tests/stages/analyze/test_credibility_engine.py -x` | Wave 0 |
| FORWARD-03 | 2026 Catalysts table renders from extracted data | unit | `uv run pytest tests/stages/render/test_forward_context_builders.py::test_catalysts -x` | Wave 0 |
| FORWARD-04 | Monitoring triggers with company-specific thresholds | unit | `uv run pytest tests/stages/benchmark/test_monitoring_triggers.py -x` | Wave 0 |
| FORWARD-05 | Growth estimates table from yfinance data | unit | `uv run pytest tests/stages/render/test_forward_context_builders.py::test_growth_estimates -x` | Wave 0 |
| FORWARD-06 | Alt signals (short interest, analyst sentiment, buyback) | unit | `uv run pytest tests/stages/render/test_forward_context_builders.py::test_alt_signals -x` | Wave 0 |
| SCORE-02 | ZER-001 verification for zero-scored factors | unit | `uv run pytest tests/stages/benchmark/test_underwriting_posture.py::test_zero_verification -x` | Wave 0 |
| SCORE-03 | Posture table with decision/retention/limit/pricing/exclusions/monitoring | unit | `uv run pytest tests/stages/benchmark/test_underwriting_posture.py::test_posture_generation -x` | Wave 0 |
| SCORE-05 | Watch items with thresholds for re-evaluation | unit | `uv run pytest tests/stages/benchmark/test_underwriting_posture.py::test_watch_items -x` | Wave 0 |
| TRIGGER-01 | Trigger matrix with RED/YELLOW flags + section routing | unit | `uv run pytest tests/stages/benchmark/test_quick_screen.py::test_trigger_matrix -x` | Wave 0 |
| TRIGGER-02 | Prospective checks with traffic light status | unit | `uv run pytest tests/stages/benchmark/test_quick_screen.py::test_prospective_checks -x` | Wave 0 |
| TRIGGER-03 | Nuclear triggers: 5 checks, 0/5 clean display | unit | `uv run pytest tests/stages/benchmark/test_quick_screen.py::test_nuclear_triggers -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x --timeout=30 -q` (quick, fail-fast)
- **Per wave merge:** `uv run pytest` (full suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/models/test_forward_looking.py` -- covers ForwardStatement, CredibilityScore, MonitoringTrigger, PostureElement, NuclearTriggerCheck model instantiation and validation
- [ ] `tests/stages/extract/test_forward_statements.py` -- covers LLM extraction schema and forward statement parsing
- [ ] `tests/stages/analyze/test_credibility_engine.py` -- covers credibility scoring from earnings data
- [ ] `tests/stages/analyze/test_miss_risk.py` -- covers miss risk computation with credibility adjustment
- [ ] `tests/stages/benchmark/test_monitoring_triggers.py` -- covers company-specific threshold computation
- [ ] `tests/stages/benchmark/test_underwriting_posture.py` -- covers posture generation from tier + factor overrides, ZER-001, watch items
- [ ] `tests/stages/benchmark/test_quick_screen.py` -- covers trigger matrix, prospective checks, nuclear triggers
- [ ] `tests/stages/render/test_forward_context_builders.py` -- covers all 5 forward-looking context builders
- [ ] `tests/stages/render/test_posture_context.py` -- covers posture and scoring context builders
- [ ] `tests/stages/render/test_quick_screen_template.py` -- covers trigger matrix template rendering

## Sources

### Primary (HIGH confidence)
- Existing codebase inspection: `models/scoring.py` (ScoringResult, Tier, TierClassification), `models/market_events.py` (EarningsGuidanceAnalysis, EarningsQuarterRecord), `stages/extract/earnings_guidance.py` (extraction patterns), `stages/analyze/do_context_engine.py` (template engine), `stages/render/context_builders/_signal_consumer.py` (signal consumer pattern), `stages/benchmark/narrative_generator.py` (LLM narrative pattern), `stages/render/context_builders/tier_explanation.py` (algorithmic tier analysis)
- Brain config: `brain/config/scoring.json` (tier definitions with action, pricing_multiplier, tower_position), `brain/signals/fwrd/*.yaml` (79 existing FWRD signals)
- Template infrastructure: `templates/html/sections/forward_looking/` (5 existing stub templates), `templates/html/sections/scoring/` (factor_detail, tier_classification patterns)
- Phase 117 CONTEXT.md (locked decisions, canonical references, existing code insights)

### Secondary (MEDIUM confidence)
- REQUIREMENTS.md definitions for FORWARD-01 through FORWARD-06, SCORE-02, SCORE-03, SCORE-05, TRIGGER-01 through TRIGGER-03
- STATE.md accumulated decisions from Phase 115-116 (do_context infrastructure, signal consumer patterns, CI gate baselines)

### Tertiary (LOW confidence)
- None -- all findings verified against existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries are existing project dependencies, no new additions
- Architecture: HIGH - follows established patterns from Phase 115/116 (context builders, brain YAML, signal consumers, LLM extraction)
- Pitfalls: HIGH - derived from deep codebase inspection and CONTEXT.md user feedback history
- Models: HIGH - extends existing Pydantic model patterns with clear field definitions
- Templates: HIGH - follows established Jinja2 section template pattern with design system CSS

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable -- internal project patterns, no external dependency changes)
