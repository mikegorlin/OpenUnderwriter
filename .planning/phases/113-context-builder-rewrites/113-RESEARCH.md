# Phase 113: Context Builder Rewrites -- ALL Builders - Research

**Researched:** 2026-03-16
**Domain:** Python context builder refactoring, signal-driven rendering architecture
**Confidence:** HIGH

## Summary

Phase 113 rewrites the 15 context builders that currently bypass the signal engine, making them consume signal results for all evaluative content. The codebase has a well-established pattern from Phase 104 (`_signal_consumer.py` + `_signal_fallback.py`) and three reference implementations already consuming signals (adversarial_context.py, pattern_context.py, severity_context.py). The core challenge is separating **tabular/display data** (stays as direct state reads) from **evaluative judgments** (must come from signal results) in each builder.

The traceability audit (2026-03-16) shows 15/18 context builders (83.3%) bypass signals entirely. All evaluative content in these builders reads directly from `state.extracted.*` or `state.analysis.*` instead of consuming the 562 signal results that the ANALYZE stage produces. This phase rewrites each builder to source evaluative content from signals while preserving tabular data extraction.

**Primary recommendation:** Rewrite each builder to accept `signal_results: dict[str, Any] | None` as a parameter, use `_signal_fallback.py` safe accessors for all evaluative content, keep tabular/display data as direct state reads, and split company.py (1,178 lines) into focused modules under 300 lines each.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BUILD-01 | `company.py` rewritten from scratch -- split into focused modules <300 lines each, all 6 v6.0 sub-builders consume signal results, old 1,178-line file deleted | company.py analysis shows 12 functions with natural split points at line ~175, ~305, ~641, ~768, ~871, ~1092; 6 sub-builders map to BIZ.*, ENVR.*, FWRD.* signal prefixes |
| BUILD-02 | `financials.py` rewritten -- all evaluative content from signals, tabular data direct | Evaluative content identified: distress zones (FIN.DISTRESS.*), earnings quality (FIN.EARNINGS.*), leverage (FIN.LEVERAGE.*), tax risk (FIN.TAX.*), liquidity (FIN.LIQUIDITY.*); tabular data (line items, sparklines, statements) stays direct |
| BUILD-03 | `market.py` rewritten -- all evaluative content from signals | Evaluative: volatility regime (STOCK.VOLATILITY.*), short interest assessment (STOCK.SHORT.*), insider assessment (STOCK.INSIDER.*), guidance track record (FWRD.GUIDANCE.*); display data (prices, transactions, valuation ratios) stays direct |
| BUILD-04 | `governance.py` rewritten -- all evaluative content from signals | Evaluative: board quality (GOV.BOARD.*), compensation flags (GOV.COMP.*), structural governance (GOV.STRUCTURE.*), narrative coherence (GOV.NARRATIVE.*); display data (directors list, holders, departures) stays direct |
| BUILD-05 | `litigation.py` rewritten -- all evaluative content from signals | Evaluative: defense strength (LIT.DEFENSE.*), SEC enforcement (LIT.SEC.*), SoL urgency (LIT.SOL.*), reserve adequacy (LIT.RESERVE.*); display data (case lists, settlements, provisions) stays direct |
| BUILD-06 | `scoring.py` and `analysis.py` rewritten if evaluative bypasses exist | scoring.py (482 lines) already partially signal-backed via Phase 112; analysis.py (551 lines) has 8 extract functions that read state.analysis/state.hazard_profile directly -- all evaluative |
| BUILD-07 | Every rewritten builder <300 lines, consumes `_signal_consumer.py`, returns typed context dict | Current sizes: company.py=1178, financials.py=626, narrative.py=580, analysis.py=551, market.py=496, litigation.py=495, scoring.py=482, governance.py=460. All over 300 lines need splitting |
| BUILD-08 | H/A/E radar chart rendered from rewritten context data | scoring.py or a new hae_context.py must extract H/A/E composite scores from signal results for radar chart rendering |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime | Project requirement |
| Pydantic | v2 | Data models | Project requirement (CLAUDE.md) |
| PyYAML | latest | Brain signal YAML loading | Already used throughout |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruff | latest | Linting/formatting | Every file change |
| pytest | 9.x | Testing | 790 render tests to maintain |

### Already Available (No Installation Needed)
All dependencies already installed via `uv sync`. No new packages needed for this phase.

## Architecture Patterns

### Current Context Builder Pattern (Pre-Rewrite)
```python
# CURRENT: direct state read (bypasses signals)
def extract_financials(state: AnalysisState) -> dict[str, Any]:
    fin = state.extracted.financials
    z = fin.distress.altman_z_score  # Direct state read for evaluative content
    result["z_zone"] = z.zone  # Evaluative judgment bypassing signals
```

### Target Context Builder Pattern (Post-Rewrite)
```python
# TARGET: signal-backed evaluative content
def extract_financials(
    state: AnalysisState,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fin = state.extracted.financials

    # TABULAR DATA: direct state read (correct -- this is display, not evaluation)
    result["revenue"] = format_currency(find_line_item_value(items, "total_revenue"))

    # EVALUATIVE CONTENT: from signal results
    z_result = safe_get_result(signal_results, "FIN.DISTRESS.altman_z")
    if z_result:
        result["z_zone"] = z_result.evidence  # Signal-backed
        result["z_level"] = signal_to_display_level(z_result.status, z_result.threshold_level)
    else:
        # Fallback to direct state for backward compat
        result["z_zone"] = z.zone if z else "N/A"
```

### Reference Implementation Pattern (Already Working)
Three builders already consume signals correctly. Follow their pattern:

```python
# From severity_context.py -- the cleanest reference
def build_severity_context(state: AnalysisState) -> dict[str, Any]:
    if state.scoring is None:
        return {"severity_available": False}
    severity_result = getattr(state.scoring, "severity_result", None)
    if severity_result is None:
        return {"severity_available": False}
    # ... extract from typed result objects, return template-ready dict
```

### Recommended Project Structure After Rewrite
```
context_builders/
├── __init__.py                    # Re-exports all public functions
├── _signal_consumer.py            # SignalResultView + typed extraction (192 lines, KEEP)
├── _signal_fallback.py            # Safe wrappers (104 lines, KEEP)
├── _governance_helpers.py         # Shared helpers (145 lines, KEEP)
├── _nlp_helpers.py                # NLP helpers (228 lines, KEEP)
├── _bull_bear.py                  # Bull/bear case builder (445 lines, KEEP)
├── company_profile.py             # extract_company() -- identity, segments, geo (NEW, <300)
├── company_exec_summary.py        # extract_exec_summary() (NEW, <300)
├── company_business_model.py      # extract_business_model() (NEW, <300)
├── company_environment.py         # _build_environment_assessment, _build_sector_risk (NEW, <300)
├── company_operations.py          # _build_operational_complexity, _build_structural_complexity (NEW, <300)
├── company_events.py              # _build_corporate_events, extract_ten_k_yoy (NEW, <300)
├── financials.py                  # Rewritten -- evaluative from signals (REWRITE, <300)
├── financials_balance.py          # Statement rows (138 lines, KEEP)
├── financials_forensic.py         # Forensic dashboard (250 lines, KEEP)
├── financials_peers.py            # Peer percentiles (179 lines, KEEP)
├── financials_quarterly.py        # Quarterly trends (225 lines, KEEP)
├── financials_evaluative.py       # Distress zones, earnings quality, leverage from signals (NEW, <300)
├── market.py                      # Display data (REWRITE, <300)
├── market_evaluative.py           # Volatility, short interest, insider assessment from signals (NEW, <300)
├── governance.py                  # Display data (REWRITE, <300)
├── governance_evaluative.py       # Board quality, comp flags from signals (NEW, <300)
├── litigation.py                  # Display data (REWRITE, <300)
├── litigation_evaluative.py       # Defense, SEC, SoL from signals (NEW, <300)
├── scoring.py                     # Already partially signal-backed (AUGMENT, <300)
├── analysis.py                    # Hazard, classification from state (REWRITE, <300)
├── analysis_evaluative.py         # Forensic composites, exec risk from signals (NEW, <300)
├── narrative.py                   # Already reads signal_results (580 lines, SPLIT)
├── adversarial_context.py         # Already signal-backed (122 lines, KEEP)
├── pattern_context.py             # Already signal-backed (113 lines, KEEP)
├── severity_context.py            # Already signal-backed (181 lines, KEEP)
├── audit.py                       # Audit trail (137 lines, KEEP)
├── calibration.py                 # Calibration notes (221 lines, KEEP)
├── chart_thresholds.py            # Chart thresholds (398 lines, KEEP)
├── render_audit.py                # Render audit (54 lines, KEEP)
└── hae_context.py                 # H/A/E radar chart data (NEW, <300)
```

### Function Signature Pattern
All rewritten builders add `signal_results` parameter with `None` default for backward compatibility:

```python
def extract_governance(
    state: AnalysisState,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
```

### Caller Update Pattern
The `md_renderer.py::build_template_context()` and `html_renderer.py::build_html_context()` must pass signal_results to each builder:

```python
signal_results = None
if state.analysis and state.analysis.signal_results:
    signal_results = state.analysis.signal_results

context["financials"] = extract_financials(state, signal_results)
context["market"] = extract_market(state, signal_results)
# etc.
```

### Evaluative vs Display Data Classification

**EVALUATIVE (must come from signals):**
- Risk assessments, zone classifications, threat levels
- Distress indicators (Altman zone, Beneish zone, Ohlson zone)
- Volatility regime, vol_regime_duration
- Short interest assessment
- Insider trading assessment (net buying/selling verdict)
- Board quality score, governance score interpretation
- Defense strength rating
- SEC enforcement stage assessment
- Reserve adequacy judgment
- Earnings quality assessment
- Tax risk flags
- Leverage risk assessment
- Any "is this good or bad" interpretation

**DISPLAY DATA (stays as direct state reads):**
- Raw financial numbers (revenue, net income, assets, etc.)
- Financial statement line items and tables
- Stock prices, ratios, valuation multiples
- Director names, titles, tenures
- Case names, filing dates, settlement amounts
- Transaction details (insider trades)
- Geographic footprint, revenue segments
- Company identity fields (SIC, CIK, exchange)
- Sparklines, charts from raw data
- Peer comparison tables (raw numbers)

### Anti-Patterns to Avoid
- **Hardcoded thresholds in builders:** Never `if z_score < 1.81: zone = "Distress"`. That logic belongs in signals.
- **Evaluative text generation in builders:** Never compose risk narratives from raw data. Use signal evidence/threshold_context.
- **Breaking backward compat:** All rewritten functions must accept the same positional args. `signal_results` is keyword-only with None default.
- **Over-splitting:** Don't create files with only 1-2 trivial functions. Group logically.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Signal result access | Raw dict[str, Any] indexing | `_signal_consumer.py` typed views | Type safety, brain metadata enrichment |
| Missing signal fallback | try/except blocks | `_signal_fallback.py` safe accessors | Consistent SignalUnavailable sentinel |
| Display level mapping | if/elif chains per builder | `signal_to_display_level()` | Single source of truth for status->display |
| Signal prefix grouping | Manual dict comprehension | `get_signals_by_prefix()` | Consistent, tested, returns typed views |

## Common Pitfalls

### Pitfall 1: Breaking Template Expectations
**What goes wrong:** Rewritten builder returns different dict keys or value formats than templates expect.
**Why it happens:** Template key names diverge during refactoring.
**How to avoid:** Document every key the current builder returns. Verify the rewritten builder returns the same keys. Run existing render tests (790 tests) after every change.
**Warning signs:** Jinja2 UndefinedError, empty sections in HTML output.

### Pitfall 2: Signal ID Mismatches
**What goes wrong:** Builder requests `FIN.DISTRESS.altman_z` but signal is actually `FIN.DISTRESS.altman_z_score`.
**Why it happens:** Signal IDs are not validated at compile time.
**How to avoid:** Grep `brain/signals/` for exact signal IDs before wiring. Use `get_signals_by_prefix()` for domain-level queries.
**Warning signs:** safe_get_result returns SignalUnavailable for signals that should exist.

### Pitfall 3: Losing Data on Signal Fallback
**What goes wrong:** When signals are SKIPPED or missing, builder returns empty/N/A where direct state read would have provided data.
**Why it happens:** Signal-first approach without fallback to direct state.
**How to avoid:** Use dual-path: signal result if available, fall back to direct state read. The signal result is BETTER (has epistemology, threshold context), but direct state is ACCEPTABLE.
**Warning signs:** Sections that were previously populated showing "Unavailable".

### Pitfall 4: company.py Split Breaking Imports
**What goes wrong:** After splitting company.py, other modules that import from it break.
**Why it happens:** `from context_builders.company import _get_yfinance_sector` used in html_renderer.py and analysis.py.
**How to avoid:** Keep `company.py` as a re-export shim, or update `__init__.py` to export from new submodules. Search all imports before splitting.
**Warning signs:** ImportError at runtime.

### Pitfall 5: 300-Line Limit Creates Artificial Splits
**What goes wrong:** Functions are split mid-logic to hit line count, creating hard-to-follow code.
**Why it happens:** Mechanical line counting without considering logical boundaries.
**How to avoid:** Split on logical boundaries (exec_summary, business_model, company_profile, environment, operations, events). Each module should have a cohesive purpose.
**Warning signs:** Functions calling helpers in other files just to stay under 300 lines.

### Pitfall 6: Narrative Builder Already Uses signal_results
**What goes wrong:** narrative.py (580 lines) already reads `state.analysis.signal_results` directly (not via _signal_consumer). Rewriting it to use _signal_consumer changes behavior.
**Why it happens:** narrative.py was written before Phase 104 infrastructure.
**How to avoid:** Migrate narrative.py to use _signal_consumer/fallback functions but verify same output. This file also needs splitting (580 > 300 lines).

## Code Examples

### Example 1: Financials Evaluative Extraction (Signal-Backed)
```python
# Source: pattern derived from _signal_consumer.py + severity_context.py
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_value,
    safe_get_level,
)
from do_uw.stages.render.context_builders._signal_consumer import (
    signal_to_display_level,
)

def _extract_distress_signals(
    signal_results: dict[str, Any] | None,
    fin: Any,  # ExtractedFinancials
) -> dict[str, Any]:
    """Extract distress zone evaluations from signals with state fallback."""
    result: dict[str, Any] = {}

    # Altman Z-Score -- signal-backed
    z_signal = safe_get_result(signal_results, "FIN.DISTRESS.altman_z_score")
    if z_signal:
        result["z_score"] = str(z_signal.value) if z_signal.value else "N/A"
        result["z_zone"] = z_signal.evidence or "N/A"
        result["z_level"] = signal_to_display_level(z_signal.status, z_signal.threshold_level)
        result["z_epistemology"] = z_signal.epistemology_rule_origin
    else:
        # Fallback to direct state
        z = fin.distress.altman_z_score
        result["z_score"] = f"{z.score:.2f}" if z and z.score else "N/A"
        result["z_zone"] = z.zone if z else "N/A"
        result["z_level"] = "Unknown"

    return result
```

### Example 2: company.py Split -- Re-Export Shim
```python
# company.py becomes a thin re-export for backward compatibility
from do_uw.stages.render.context_builders.company_profile import (
    extract_company,
    _get_yfinance_sector,
    _lookup_gics_name,
)
from do_uw.stages.render.context_builders.company_exec_summary import (
    extract_exec_summary,
)
from do_uw.stages.render.context_builders.company_events import (
    extract_ten_k_yoy,
)
from do_uw.stages.render.context_builders.company_business_model import (
    extract_business_model,
)

__all__ = [
    "extract_company",
    "extract_exec_summary",
    "extract_ten_k_yoy",
    "extract_business_model",
    "_get_yfinance_sector",
    "_lookup_gics_name",
]
```

### Example 3: Governance Signal Wiring
```python
def _extract_governance_signals(
    signal_results: dict[str, Any] | None,
) -> dict[str, Any]:
    """Extract governance evaluations from signals."""
    result: dict[str, Any] = {}

    # Board quality signals
    board_signals = safe_get_signals_by_prefix(signal_results, "GOV.BOARD")
    triggered_board = [s for s in board_signals if s.status == "TRIGGERED"]
    result["board_flags"] = [
        {
            "signal_id": s.signal_id,
            "display_level": signal_to_display_level(s.status, s.threshold_level),
            "evidence": s.evidence,
            "threshold_context": s.threshold_context,
        }
        for s in triggered_board
    ]

    # Compensation signals
    comp_signals = safe_get_signals_by_prefix(signal_results, "GOV.COMP")
    result["comp_flags"] = [
        {
            "signal_id": s.signal_id,
            "display_level": signal_to_display_level(s.status, s.threshold_level),
            "evidence": s.evidence,
        }
        for s in comp_signals if s.status == "TRIGGERED"
    ]

    return result
```

## Signal ID Prefix Map (Which Builders Consume Which Signals)

| Builder | Signal Prefixes | Count | Content Type |
|---------|----------------|-------|--------------|
| company_profile | BIZ.*, ENVR.* | 62+5 | Business model, environment |
| company_business_model | BIZ.MODEL.*, BIZ.CONCENTRATION.* | ~20 | Revenue model, concentration |
| company_environment | ENVR.*, FWRD.* | 5+80 | Sector risk, forward indicators |
| company_operations | BIZ.OPS.*, BIZ.STRUCTURE.* | ~15 | Operational complexity |
| company_events | BIZ.EVENT.*, EXEC.* | ~20 | Corporate events, departures |
| financials | FIN.* | 101 | Distress, earnings, leverage, tax, liquidity |
| market | STOCK.* | 40 | Volatility, short, insider, returns |
| governance | GOV.* | 90 | Board, comp, structure, narrative |
| litigation | LIT.* | 65 | Defense, SEC, SoL, reserve |
| scoring | (already signal-backed via Phase 112) | -- | Factor attribution |
| analysis | NLP.*, DISC.* | 15+6 | Forensics, NLP, classification |
| hae_context | (computed from H/A/E scoring result) | -- | Radar chart data |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct state reads for all content | Signal-backed evaluative, direct display | Phase 104 (infra), Phase 113 (migration) | Full traceability chain |
| Single 1,178-line company.py | Split into 6 focused modules | Phase 113 | Anti-context-rot compliance |
| 83% context builders bypass signals | 100% consume signals | Phase 113 target | Traceability metric from 16.7% to 100% |

## Key File Inventory (What Needs Changing)

### Files to Rewrite/Split (HIGH Priority)
| File | Lines | Action | Signal Prefixes |
|------|-------|--------|----------------|
| company.py | 1,178 | Split into 6 modules | BIZ.*, ENVR.*, FWRD.* |
| financials.py | 626 | Extract evaluative to new module | FIN.* |
| analysis.py | 551 | Extract evaluative to new module | NLP.*, DISC.* |
| market.py | 496 | Extract evaluative to new module | STOCK.* |
| litigation.py | 495 | Extract evaluative to new module | LIT.* |
| scoring.py | 482 | Augment remaining bypasses | (mostly done) |
| governance.py | 460 | Extract evaluative to new module | GOV.* |
| narrative.py | 580 | Split (already reads signals) | All prefixes |

### Files to Update (Callers)
| File | Change Needed |
|------|--------------|
| `md_renderer.py` | Pass signal_results to all builder calls |
| `html_renderer.py` | Pass signal_results to all builder calls |
| `__init__.py` | Update imports for split modules |

### Files to Keep Unchanged
| File | Lines | Reason |
|------|-------|--------|
| _signal_consumer.py | 192 | Infrastructure, already correct |
| _signal_fallback.py | 104 | Infrastructure, already correct |
| adversarial_context.py | 122 | Already signal-backed |
| pattern_context.py | 113 | Already signal-backed |
| severity_context.py | 181 | Already signal-backed |
| financials_balance.py | 138 | Pure display data |
| financials_forensic.py | 250 | Pure display data |
| financials_peers.py | 179 | Pure display data |
| financials_quarterly.py | 225 | Pure display data |
| audit.py | 137 | Audit trail |
| render_audit.py | 54 | Render audit |
| calibration.py | 221 | Calibration notes |

### Import Dependencies to Track
```
html_renderer.py → company._get_yfinance_sector (line 268)
analysis.py → company._get_yfinance_sector (line 69)
__init__.py → company.extract_company, extract_exec_summary, extract_ten_k_yoy
md_renderer.py → all extract_* functions via __init__.py
```

## Open Questions

1. **narrative.py (580 lines) -- in scope or separate?**
   - What we know: Already reads signal_results directly, needs splitting for <300 line target
   - What's unclear: Whether it should be rewritten to use _signal_consumer.py or just split
   - Recommendation: Split only (it already consumes signals, just not via typed consumer). Typed consumer migration is a nice-to-have, not required for BUILD-01 through BUILD-08.

2. **_bull_bear.py (445 lines) -- in scope?**
   - What we know: 445 lines, over 300 limit, generates bull/bear cases from state
   - What's unclear: Whether it contains evaluative content that should be signal-backed
   - Recommendation: Out of scope for this phase unless it contains evaluative bypasses. It's a case builder, not a section context builder.

3. **chart_thresholds.py (398 lines) -- in scope?**
   - What we know: 398 lines, over 300 limit, reads signal YAML for chart annotations
   - What's unclear: Whether this counts as "evaluative bypass"
   - Recommendation: Out of scope. It reads signal definitions (not results) for chart rendering.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/stages/render/ -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUILD-01 | company.py split into <300 line modules | unit | `uv run pytest tests/stages/render/ -x -q -k "company"` | Partial (existing render tests) |
| BUILD-02 | financials evaluative from signals | unit | `uv run pytest tests/stages/render/ -x -q -k "financial"` | Partial |
| BUILD-03 | market evaluative from signals | unit | `uv run pytest tests/stages/render/ -x -q -k "market"` | Partial |
| BUILD-04 | governance evaluative from signals | unit | `uv run pytest tests/stages/render/ -x -q -k "governance"` | Partial |
| BUILD-05 | litigation evaluative from signals | unit | `uv run pytest tests/stages/render/ -x -q -k "litigation"` | Partial |
| BUILD-06 | scoring/analysis evaluative from signals | unit | `uv run pytest tests/stages/render/ -x -q -k "scoring or analysis"` | Partial |
| BUILD-07 | Every builder <300 lines | smoke | `wc -l src/do_uw/stages/render/context_builders/*.py` | Wave 0 |
| BUILD-08 | H/A/E radar chart from signal data | unit | `uv run pytest tests/stages/render/ -x -q -k "hae"` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/render/ -x -q` (790 tests, ~10s)
- **Per wave merge:** `uv run pytest -x -q` (5,000+ tests)
- **Phase gate:** Full suite green + `wc -l` verification on all builder files

### Wave 0 Gaps
- [ ] `tests/stages/render/test_builder_line_limits.py` -- verify all builders <300 lines (BUILD-07)
- [ ] `tests/stages/render/test_signal_consumption.py` -- verify each builder consumes signals for evaluative content
- [ ] `tests/stages/render/test_hae_context.py` -- H/A/E radar chart context (BUILD-08)
- [ ] Existing 790 render tests provide regression coverage -- no additional framework needed

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis of all 25 context builder files
- `_signal_consumer.py` (192 lines) -- typed extraction API
- `_signal_fallback.py` (104 lines) -- safe fallback API
- `.planning/TRACEABILITY-AUDIT.md` -- 83.3% bypass metric baseline
- Phase 112 scoring context builder -- signal attribution pattern
- Phase 104 infrastructure -- consumer/fallback design

### Secondary (MEDIUM confidence)
- Signal prefix distribution from `brain/signals/` YAML (562 signals)
- Import dependency analysis via grep

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, all patterns exist in codebase
- Architecture: HIGH - three reference implementations already working (adversarial, pattern, severity)
- Pitfalls: HIGH - direct observation of import dependencies and template key contracts
- Signal mapping: MEDIUM - signal IDs verified by prefix counts but individual wiring needs per-builder grep

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable internal architecture)
