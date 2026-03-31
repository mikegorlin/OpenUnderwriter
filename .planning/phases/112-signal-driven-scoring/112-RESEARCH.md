# Phase 112: Signal-Driven Scoring - Research

**Researched:** 2026-03-16
**Domain:** Scoring engine refactoring -- 10-factor scoring to signal-driven aggregation
**Confidence:** HIGH

## Summary

Phase 112 replaces the legacy `factor_data.py` data extraction (which reads `ExtractedData` directly) with signal-driven aggregation. Currently, the 10-factor scoring engine (`factor_data.py` + `factor_rules.py` + `factor_scoring.py`) bypasses the 562 YAML-defined signals entirely -- it hardcodes data extraction from Pydantic state models and applies JSON-defined rule matching. Meanwhile, the H/A/E multiplicative model already consumes signal results via `hae_scoring.py`. Phase 112 bridges this gap for the legacy 10-factor model.

The codebase is well-prepared: 425 of 562 signals already have `factors` field assignments mapping to F1-F10, the `SignalResultView` dataclass provides typed signal access, and the `_signal_consumer.py` / `_signal_fallback.py` infrastructure handles graceful degradation. The refactoring is primarily a rewiring job: replace ~10 `_get_fN_data()` functions with signal aggregation queries, add a `scoring` block to YAML signals (for weight/factor declarations), and implement a normalization formula.

**Primary recommendation:** Refactor `factor_data.py` to query signal results by factor tag; keep `factor_rules.py` as fallback for factors with <50% signal coverage; add `scoring` block to YAML schema and signals; produce shadow calibration comparing old vs new for RPM/HNGE/V.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Signals declare their factor in YAML (`scoring.factor` field, e.g., `F1_prior_litigation`) -- brain portability preserved, signals are fully self-describing
- A signal can contribute to multiple factors with per-factor weights (e.g., governance signal -> F9 at weight 1.0 + F10 at weight 0.5)
- `factor_data.py` queries signals by factor tag instead of reading ExtractedData directly
- DEFERRED and SKIPPED signals are excluded from factor score calculation but contribute to a per-factor "data completeness" metric -- low completeness lowers confidence, not the score itself
- Weighted severity sum, normalized to 0-10 scale: each TRIGGERED signal contributes severity x weight, sum normalized by total possible weight
- YAML declares default signal weight (`scoring.weight: 1.0`), scoring.json can override per-factor for calibration flexibility
- Phased migration: signal-driven aggregation is the primary score; if a factor has <50% signal coverage, fall back to old rule-based score for that factor. Remove fallback once coverage is high
- Composite score continues to use existing weighted average of factor scores -- only factor-level calculation changes, not composite formula
- Accept new signal-driven scores as truth -- if old scores were wrong due to missing data, the new score IS better
- Full change tracking: every run stores factor-level diff with signal attribution
- Shadow comparison report for 3 test tickers (RPM, HNGE, V)
- Top 3 contributing signals shown per factor + expandable full signal list
- Augment existing scoring section -- add "Signal Attribution" subsection below each factor
- Per-factor confidence bar visible to underwriters (e.g., "15/20 signals evaluated")
- Factor weights visible in the factor table

### Claude's Discretion
- Exact YAML schema for `scoring.factor` and `scoring.weight` fields
- Normalization formula for weighted severity sum
- Signal coverage threshold for rule-based fallback (suggested 50% but tunable)
- Calibration storage format and location (DuckDB vs JSON, gitignored)
- Layout details for signal attribution in worksheet

### Deferred Ideas (OUT OF SCOPE)
- Rethink what factors feed pricing/actuarial models -- new milestone scope
- Supabase as centralized data store -- infrastructure milestone
- Multiplicative H/A/E scoring model (Phase 106 design) -- future milestone after signal-driven scoring proves stable
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FSCORE-01 | `factor_data.py` reads signal results (not ExtractedData) for all 10 factors -- each factor is a weighted aggregation of constituent signals | Signal-to-factor mapping via existing `factors` field (425/562 signals already tagged); new `scoring` block for weight/severity; `get_factor_data()` refactored to query signal results dict |
| FSCORE-02 | Composite score demonstrably changes when signals TRIGGER vs when they don't -- signals have measurable influence on score | Weighted severity sum formula ensures TRIGGERED signals contribute points; normalization ensures proportional impact; shadow comparison validates delta |
| FSCORE-03 | Factor breakdown shows which signals contributed to each factor score with weights | `FactorScore.sub_components` extended to include `signal_contributions` list; template augmented with signal attribution subsection |
| FSCORE-04 | Shadow calibration comparing old direct-data scoring vs new signal-driven scoring on 3 test tickers (RPM, HNGE, V) | `shadow_calibration.py` and `_calibration_report.py` already exist for H/A/E vs legacy; extend to include signal-driven 10-factor vs old 10-factor comparison |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | Schema for `scoring` block in BrainSignalEntry, FactorScore extensions | Project standard for all models |
| PyYAML | 6.x | Read/write YAML signal files with new `scoring` block | Already used throughout brain |
| Python dataclasses | stdlib | SignalResultView (frozen) already exists | Phase 104 pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| DuckDB | 1.x | Calibration history storage (run diffs) | Shadow comparison persistence |
| json (stdlib) | stdlib | Calibration report data export | Alternative to DuckDB for simplicity |

### No New Dependencies
This phase requires zero new libraries. All infrastructure exists.

## Architecture Patterns

### Current Data Flow (BEFORE)
```
ExtractedData -> factor_data._get_fN_data() -> dict -> factor_rules.rule_matches() -> FactorScore
                 (hardcoded extraction)         (rule-based matching)
```

### Target Data Flow (AFTER)
```
signal_results dict -> factor_data.get_factor_data_from_signals() -> weighted aggregation -> FactorScore
                       (query by factor tag)                         (severity * weight)

                       [fallback if <50% coverage]
                       ExtractedData -> _get_fN_data() -> factor_rules.rule_matches() -> FactorScore
```

### Recommended File Structure Changes
```
src/do_uw/stages/score/
  factor_data.py          # REFACTORED: signal-driven primary + fallback
  factor_data_market.py   # KEPT: F6/F7 market helpers (fallback path)
  factor_data_signals.py  # NEW: signal aggregation logic (<300 lines)
  factor_rules.py         # KEPT: becomes fallback path only
  factor_scoring.py       # MODIFIED: call signal path first, fallback second
  _calibration_report.py  # EXTENDED: signal-driven vs old comparison
  shadow_calibration.py   # EXTENDED: include signal-driven 10-factor lens
```

### Pattern 1: Signal-to-Factor Aggregation
**What:** Each factor score is computed as a weighted severity sum of its constituent signals.
**When to use:** Primary scoring path when factor has >= 50% signal coverage.
**Formula:**
```
factor_score = (sum(severity_i * weight_i for triggered_signals) / sum(weight_i for all_signals)) * max_points
```
Where:
- `severity_i`: mapped from threshold_level: red=1.0, yellow=0.5, clear=0.0
- `weight_i`: from signal's `scoring.weight` (default 1.0), overridable in scoring.json
- Normalization denominator = total possible weight (all signals for this factor)
- Multiplied by `max_points` from scoring.json to produce 0-N scale matching existing FactorScore

### Pattern 2: YAML Scoring Block Schema
**What:** New optional `scoring` block on BrainSignalEntry for factor weight declarations.
**Schema (recommended):**
```yaml
scoring:
  factor: F1_prior_litigation    # single factor (most signals)
  weight: 1.0                    # default weight
  severity_map:                  # optional: override default threshold_level -> severity
    red: 1.0
    yellow: 0.5
    clear: 0.0

# OR multi-factor:
scoring:
  factors:
    - factor: F9_governance
      weight: 1.0
    - factor: F10_officer_stability
      weight: 0.5
```

This leverages the existing `factors: [F1, F9]` field for backward compat but adds explicit weights. The `factors` list field already exists on 425 signals. The new `scoring` block adds granularity.

**Implementation approach:**
1. For the 425 signals that already have `factors: [F1]` etc., these continue working -- the new code reads `factors` as the factor assignment
2. The new `scoring` block is OPTIONAL -- signals without it default to weight=1.0 and use their existing `factors` field
3. Only signals where multi-factor weighting or custom severity mapping is needed get the full `scoring` block

### Pattern 3: Phased Migration with Coverage Check
**What:** Each factor checks signal coverage before using signal-driven scoring.
**Logic:**
```python
def get_factor_data(factor_key, signal_results, extracted, ...):
    # Count signals assigned to this factor
    total = count_signals_for_factor(factor_key)
    evaluated = count_evaluated_signals_for_factor(factor_key, signal_results)
    coverage = evaluated / total if total > 0 else 0

    if coverage >= COVERAGE_THRESHOLD:  # 0.50 default
        return aggregate_from_signals(factor_key, signal_results)
    else:
        # Fallback to old path
        return _get_fN_data_legacy(factor_key, extracted, ...)
```

### Pattern 4: Signal Contribution Tracking
**What:** Each FactorScore records which signals contributed and how.
**Data structure:**
```python
signal_contributions: list[dict] = [
    {
        "signal_id": "LIT.SCA.search",
        "signal_name": "SCA Database Search",
        "status": "TRIGGERED",
        "threshold_level": "red",
        "severity": 1.0,
        "weight": 1.0,
        "contribution": 1.0,  # severity * weight
        "evidence": "1 active securities class action"
    },
    ...
]
```
Stored in `FactorScore.sub_components["signal_contributions"]`.

### Anti-Patterns to Avoid
- **Replacing both factor_data AND factor_rules simultaneously:** The user wants phased migration. Keep factor_rules.py as the fallback path. Only remove it when coverage is provably high across multiple tickers.
- **Modifying the composite formula:** CONTEXT.md explicitly states "Composite score continues to use existing weighted average of factor scores -- only factor-level calculation changes, not composite formula."
- **Hardcoding factor-to-signal mappings in Python:** The mapping MUST come from YAML (brain portability principle). Python code queries by tag, never maintains a hardcoded map.
- **Treating DEFERRED/SKIPPED as risk signals:** They affect data completeness confidence, not the score itself.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Signal result querying | Custom dict traversal | `_signal_consumer.py` functions: `get_signal_result()`, `get_signals_by_prefix()` | Already handles brain YAML lookup, RAP metadata, epistemology |
| Severity level mapping | Hardcoded if/elif chains | Config-driven severity_map from YAML or scoring.json | Calibration flexibility, brain portability |
| Calibration report HTML | Custom HTML generation | Extend `_calibration_report.py` / `shadow_calibration.py` | Already has sortable tables, tier badges, export |
| Signal loading/caching | Fresh YAML reads per factor | `load_signals()` from `brain_unified_loader` + module-level cache pattern | Established in Phase 104 |

## Common Pitfalls

### Pitfall 1: Factor Tag Inconsistency
**What goes wrong:** Existing `factors` field uses `F1`, `F10` etc., but scoring.json uses `F1_prior_litigation`, `F10_officer_stability`. Mismatch causes zero signals found for a factor.
**Why it happens:** Two naming conventions evolved independently. 425 signals use short form (`F1`), scoring.json uses long form (`F1_prior_litigation`).
**How to avoid:** Build a canonical mapping: `F1 -> F1_prior_litigation`, etc. Factor query code accepts both forms. Test with assertions that every factor finds >0 signals.
**Warning signs:** A factor returning 0 signals when you expect dozens.

### Pitfall 2: SKIPPED/DEFERRED Signal Inflation
**What goes wrong:** 72 DEFERRED + ~26 SKIPPED signals (4.6% rate) could make coverage calculation misleadingly low if counted in denominator.
**Why it happens:** DEFERRED signals exist in YAML (have factor assignments) but never produce evaluation results.
**How to avoid:** Coverage denominator = only AUTO-mode signals with evaluated results (TRIGGERED + CLEAR + INFO). Exclude DEFERRED/SKIPPED/MANUAL_ONLY from denominator. Track them separately in completeness metric.
**Warning signs:** Factor coverage dropping below 50% when plenty of signals are tagged.

### Pitfall 3: Score Scale Mismatch
**What goes wrong:** New signal-driven score produces values on wrong scale, causing composite score to jump dramatically.
**Why it happens:** Old factor scores are 0 to max_points (e.g., F1 max = 20). New aggregation must produce same scale or composite breaks.
**How to avoid:** Normalization formula must output 0 to max_points for each factor. Test: `0 <= factor_score <= factor.max_points` for all factors on test tickers.
**Warning signs:** Composite quality_score going negative or exceeding 100.

### Pitfall 4: Losing F2 Modifiers (Insider Amplifier, Market Cap, Drop Contribution)
**What goes wrong:** F2 (Stock Decline) has complex post-scoring modifiers: insider amplifier (1.0-1.5x), market cap multiplier, drop contribution decay. These are applied AFTER base rule matching in `factor_scoring.py`. A naive signal aggregation replaces these with a flat weighted sum.
**Why it happens:** F2 scoring logic is 6+ steps in `factor_scoring.py`. Signal aggregation replaces step 1 (base rule) but must preserve steps 2-6.
**How to avoid:** Signal-driven path produces base score only. Existing modifiers in `factor_scoring.py` continue to apply on top. Or: model F2 modifiers as separate signals (STOCK.INSIDER_CLUSTER, STOCK.DROP_DECAY) that contribute via the signal framework.
**Warning signs:** F2 scores being consistently lower for known-bad tickers (missing amplifiers).

### Pitfall 5: INFO Signals Shouldn't Score
**What goes wrong:** 80+ INFO-status signals (MANAGEMENT_DISPLAY, informational thresholds) get included in factor scoring, inflating denominators or contributing zero-severity noise.
**Why it happens:** `content_type=MANAGEMENT_DISPLAY` and `signal_class=foundational` signals are informational, not evaluative.
**How to avoid:** Filter to `signal_class=evaluative` AND `content_type=EVALUATIVE_CHECK` when aggregating for scoring. Foundational and inference signals participate differently (or not at all in factor scoring).
**Warning signs:** Factor denominators being 2-3x larger than expected.

### Pitfall 6: Breaking Existing 5,000+ Tests
**What goes wrong:** Changing `get_factor_data()` signature breaks every test that calls it with (factor_key, extracted, company, sectors, analysis_results).
**Why it happens:** The current function signature doesn't accept signal_results. Adding it as a parameter changes the contract.
**How to avoid:** Add `signal_results` as an optional parameter with default `None`. When `None`, use legacy path. This preserves all existing tests while enabling new path. New tests pass signal_results.
**Warning signs:** Mass test failures on import.

## Code Examples

### Current factor_data.py signature (preserve backward compat)
```python
# Source: src/do_uw/stages/score/factor_data.py
def get_factor_data(
    factor_key: str,
    extracted: ExtractedData,
    company: CompanyProfile | None,
    sectors: dict[str, Any],
    analysis_results: dict[str, Any] | None = None,
    signal_results: dict[str, Any] | None = None,  # NEW: Phase 112
) -> dict[str, Any]:
```

### Signal aggregation function (new)
```python
# Source: new file factor_data_signals.py
def aggregate_factor_from_signals(
    factor_key: str,
    signal_results: dict[str, Any],
    brain_signals: list[dict[str, Any]],
    max_points: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Aggregate signal results for a single factor.

    Returns:
        Tuple of (factor_data_dict, signal_contributions_list)
    """
    canonical = _factor_canonical_name(factor_key)  # F1 -> F1_prior_litigation

    # Find all evaluative signals tagged with this factor
    tagged_signals = [
        s for s in brain_signals
        if canonical_factor_match(s.get("factors", []), canonical)
        and s.get("signal_class") == "evaluative"
        and s.get("execution_mode") == "AUTO"
    ]

    total_weight = 0.0
    weighted_severity = 0.0
    contributions = []
    evaluated_count = 0

    for sig in tagged_signals:
        sig_id = sig["id"]
        weight = _get_signal_weight(sig, factor_key)  # from scoring block or default 1.0
        total_weight += weight

        result = signal_results.get(sig_id)
        if result is None or not isinstance(result, dict):
            continue

        status = result.get("status", "SKIPPED")
        if status in ("SKIPPED", "DEFERRED"):
            continue

        evaluated_count += 1
        severity = _threshold_to_severity(result.get("threshold_level", ""))
        contribution = severity * weight
        weighted_severity += contribution

        if status == "TRIGGERED":
            contributions.append({
                "signal_id": sig_id,
                "signal_name": sig.get("name", sig_id),
                "status": status,
                "threshold_level": result.get("threshold_level", ""),
                "severity": severity,
                "weight": weight,
                "contribution": contribution,
                "evidence": result.get("evidence", ""),
            })

    # Normalize to 0-max_points scale
    if total_weight > 0:
        normalized = (weighted_severity / total_weight) * max_points
    else:
        normalized = 0.0

    coverage = evaluated_count / len(tagged_signals) if tagged_signals else 0.0

    data = {
        "signal_score": min(normalized, max_points),
        "signal_coverage": coverage,
        "evaluated_count": evaluated_count,
        "total_signals": len(tagged_signals),
        "use_signal_path": coverage >= COVERAGE_THRESHOLD,
    }

    # Sort contributions by contribution value descending
    contributions.sort(key=lambda c: c["contribution"], reverse=True)
    return data, contributions
```

### FactorScore extension for signal attribution
```python
# Source: extend FactorScore in models/scoring.py
class FactorScore(BaseModel):
    # ... existing fields ...
    signal_contributions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Signals that contributed to this factor score with weights",
    )
    signal_coverage: float = Field(
        default=0.0,
        description="Fraction of factor signals that were evaluated (0.0-1.0)",
    )
    scoring_method: str = Field(
        default="rule_based",
        description="How this factor was scored: 'signal_driven' or 'rule_based'",
    )
```

### Factor tag canonical mapping
```python
FACTOR_CANONICAL: dict[str, str] = {
    "F1": "F1_prior_litigation",
    "F2": "F2_stock_decline",
    "F3": "F3_restatement_audit",
    "F4": "F4_ipo_spac_ma",
    "F5": "F5_guidance_misses",
    "F6": "F6_short_interest",
    "F7": "F7_volatility",
    "F8": "F8_financial_distress",
    "F9": "F9_governance",
    "F10": "F10_officer_stability",
}

# Reverse: for YAML signals that use short form
FACTOR_SHORT_TO_LONG = {
    "F1": "F1_prior_litigation", "F2": "F2_stock_decline",
    "F3": "F3_restatement_audit", "F4": "F4_ipo_spac_ma",
    "F5": "F5_guidance_misses", "F6": "F6_short_interest",
    "F7": "F7_volatility", "F8": "F8_financial_distress",
    "F9": "F9_governance", "F10": "F10_officer_stability",
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct ExtractedData reads per factor | Signal results as intermediary | Phase 112 (now) | Traceability: every score point traceable to a signal |
| Hardcoded rule matching in Python | YAML-declared thresholds evaluated by signal engine | Phase 111 | Brain portability: scoring logic in YAML, not code |
| Single-path scoring | Signal-driven primary + rule-based fallback | Phase 112 (now) | Phased migration: no cliff edge |

## Key Findings

### Factor Distribution Analysis (from codebase scan)
- **562 total signals**, 425 have factor assignments (75.6%)
- **137 signals without factors** -- mostly absence (20), conjunction (8), contextual (20), foundational (28), business/sector descriptive
- **Factor coverage by signal count:**
  - F1 (Prior Litigation): 78 signals -- excellent coverage
  - F10 (Officer Stability): 122 signals -- excellent coverage (includes many governance signals)
  - F3 (Restatement/Audit): 102 signals -- excellent coverage
  - F9 (Governance): 46 signals -- good coverage
  - F5 (Guidance Misses): 33 signals -- moderate coverage
  - F2 (Stock Decline): 32 signals -- moderate coverage
  - F7 (Volatility): 32 signals -- moderate coverage
  - F6 (Short Interest): 23 signals -- moderate coverage
  - F4 (IPO/SPAC/M&A): 17 signals -- lower coverage (fewer event types)
  - F8 (Financial Distress): 14 signals -- lowest coverage (may need fallback)

### Signal Class Relevance for Scoring
- **458 evaluative** signals -- primary scoring candidates
- **76 inference** signals (conjunction/absence/contextual) -- may contribute to factors but are meta-signals
- **28 foundational** signals -- data collection only, NEVER score

### Execution Mode Impact
- **483 AUTO** -- will produce results for aggregation
- **72 DEFERRED** -- exist but no data; exclude from scoring denominator
- **2 FALLBACK_ONLY, 3 MANUAL_ONLY, 2 SECTOR_CONDITIONAL** -- edge cases, handle gracefully

### Existing Scoring Infrastructure
- `scoring.json` defines F1-F10 with weights that sum to 100%
- `FactorScore` Pydantic model already has `sub_components` dict -- natural place for signal contributions
- `factor_scoring.py` already has modifier pipeline (insider amplifier, market cap, drop contribution) -- must be preserved
- `shadow_calibration.py` already handles H/A/E vs legacy comparison -- extendable for signal-driven comparison
- `_signal_consumer.py` SignalResultView has `factors` tuple field -- signals already carry factor tags into results

### Severity Mapping Recommendation
Based on existing threshold_level values in the codebase:
```
red -> severity 1.0 (full weight)
yellow -> severity 0.5 (half weight)
clear -> severity 0.0 (no contribution)
"" (empty) -> severity 0.0 (INFO/display signals)
```
This is the simplest mapping that produces meaningful differentiation. The CONTEXT.md allows custom severity_map in YAML for signals that need non-standard mapping.

## YAML Schema Decision: `scoring` Block

**Recommended schema** (Claude's discretion area):

```yaml
# Option A: Simple (use for most signals)
# No new block needed -- existing factors field + default weight 1.0
factors:
  - F1

# Option B: Weighted (when signal needs non-default weight)
scoring:
  weight: 2.0  # default is 1.0

# Option C: Multi-factor with per-factor weights
scoring:
  contributions:
    - factor: F9_governance
      weight: 1.0
    - factor: F10_officer_stability
      weight: 0.5
```

**Rationale:** Option A requires zero YAML changes for 425 existing signals. Option B is minimal addition for weight tuning. Option C is for the minority of signals contributing to multiple factors with different weights. The `scoring` block is validated via Pydantic (add to BrainSignalEntry as optional).

## Calibration Storage Decision

**Recommended: JSON files in .cache/ (gitignored)**

Rationale:
- DuckDB adds query complexity for a simple key-value comparison
- JSON is human-readable, diffable, and trivially loadable
- Storage location: `.cache/calibration/` (gitignored per existing .cache/ pattern)
- Format: `{ticker}_{timestamp}_factor_calibration.json`
- Contains: per-factor old_score, new_score, delta, signal_contributions, coverage

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/stages/score/ -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FSCORE-01 | factor_data reads signal results for all 10 factors | unit | `uv run pytest tests/stages/score/test_factor_data_signals.py -x` | Wave 0 |
| FSCORE-01 | weighted aggregation produces correct scores | unit | `uv run pytest tests/stages/score/test_factor_data_signals.py::test_weighted_aggregation -x` | Wave 0 |
| FSCORE-02 | score changes when signals trigger | integration | `uv run pytest tests/stages/score/test_signal_scoring_influence.py -x` | Wave 0 |
| FSCORE-03 | factor breakdown shows signal contributions | unit | `uv run pytest tests/stages/score/test_factor_score_contributions.py -x` | Wave 0 |
| FSCORE-04 | shadow calibration old vs new for 3 tickers | integration | `uv run pytest tests/stages/score/test_shadow_signal_calibration.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/score/ -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/score/test_factor_data_signals.py` -- covers FSCORE-01
- [ ] `tests/stages/score/test_signal_scoring_influence.py` -- covers FSCORE-02
- [ ] `tests/stages/score/test_factor_score_contributions.py` -- covers FSCORE-03
- [ ] `tests/stages/score/test_shadow_signal_calibration.py` -- covers FSCORE-04

## Open Questions

1. **F2 Modifier Preservation Strategy**
   - What we know: F2 has 3 post-base-score modifiers (insider amplifier, market cap multiplier, drop contribution decay) that cannot be expressed as simple signal aggregation
   - What's unclear: Should these modifiers apply on top of signal-driven base score, or should they be modeled as separate signals?
   - Recommendation: Apply existing modifiers on top of signal-driven base score for Phase 112. Future milestone can refactor modifiers into signals if desired. This minimizes risk.

2. **Inference Signal Scoring Participation**
   - What we know: 76 inference signals (conjunction, absence, contextual) have factor assignments but evaluate meta-patterns rather than direct data
   - What's unclear: Should these participate in factor scoring at same weight as evaluative signals?
   - Recommendation: Include inference signals in factor scoring with weight 0.5 (half default). They represent synthesized risk that should influence scores but not dominate.

3. **Signal Weight Calibration**
   - What we know: All 425 signals will start with weight 1.0. Some signals (e.g., active SCA = F1-001 worth 20pts) are much more impactful than others.
   - What's unclear: How to calibrate initial weights so signal-driven scores approximate existing rule-based scores.
   - Recommendation: Start with uniform weights, run shadow calibration on 3 tickers, then adjust weights for top-5 signals per factor to bring scores within 10% of old scores. Document adjustments in scoring.json.

## Sources

### Primary (HIGH confidence)
- `src/do_uw/stages/score/factor_data.py` -- 442-line file, full review of all 10 factor extraction functions
- `src/do_uw/stages/score/factor_scoring.py` -- 554-line file, full scoring pipeline with modifiers
- `src/do_uw/stages/score/factor_rules.py` -- 286-line file, all per-factor rule matchers
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` -- SignalResultView and typed extraction API
- `src/do_uw/brain/brain_signal_schema.py` -- Pydantic schema for BrainSignalEntry (554 lines)
- `src/do_uw/stages/analyze/signal_results.py` -- SignalResult model with factors field
- `src/do_uw/brain/config/scoring.json` -- Factor definitions, weights, rules
- Brain signal YAML files -- 562 signals across 14 directories, 425 with factor assignments

### Secondary (MEDIUM confidence)
- `src/do_uw/stages/score/shadow_calibration.py` -- Existing calibration infrastructure, extendable
- `src/do_uw/stages/score/hae_scoring.py` -- H/A/E lens pattern for signal consumption
- `.planning/phases/112-signal-driven-scoring/112-CONTEXT.md` -- User decisions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all patterns exist in codebase
- Architecture: HIGH -- clear refactoring path, existing infrastructure supports all requirements
- Pitfalls: HIGH -- identified from direct code review, not speculation

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable domain, internal refactoring)
