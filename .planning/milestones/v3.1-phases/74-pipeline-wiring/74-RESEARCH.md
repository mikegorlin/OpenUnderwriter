# Phase 74: Pipeline Wiring -- Quarterly XBRL + Ownership Concentration - Research

**Researched:** 2026-03-07
**Domain:** Pipeline integration (wiring existing tested modules into extract stage)
**Confidence:** HIGH

## Summary

Phase 74 is a gap closure phase. The v3.1 milestone audit (`v3.1-MILESTONE-AUDIT.md`) found that 5 functions built in Phases 68 and 71 were never wired into the pipeline extract stage. The modules are fully built, tested, and verified -- they just need to be called from the right places.

Two distinct integration points need wiring: (1) quarterly XBRL extraction + trend computation + reconciliation into the extract stage orchestrator (`stages/extract/__init__.py`), and (2) ownership concentration + trajectory analysis into `extract_insider_trading()` in `insider_trading.py`.

**Primary recommendation:** Add approximately 30-40 lines of pipeline wiring code across 2 files. No new modules, no new models, no new tests beyond integration verification. The existing unit tests for all 5 functions already pass.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QTRLY-01 | Extract 8 quarters from Company Facts API | `extract_quarterly_xbrl()` exists in `xbrl_quarterly.py`, needs call from `extract/__init__.py` |
| QTRLY-02 | YTD-to-quarterly disambiguation | Part of `extract_quarterly_xbrl()` -- wired once QTRLY-01 is wired |
| QTRLY-03 | Fiscal period alignment with dual labels | Part of `extract_quarterly_xbrl()` -- wired once QTRLY-01 is wired |
| QTRLY-04 | QoQ and YoY trend computation | `compute_all_trends()` in `xbrl_trends.py`, needs call after quarterly extraction |
| QTRLY-05 | Sequential pattern detection (acceleration/deceleration) | Part of `compute_all_trends()` -- wired once QTRLY-04 is wired |
| QTRLY-06 | XBRL/LLM reconciler runs and logs divergences | `reconcile_quarterly()` in `xbrl_llm_reconciler.py`, needs call after quarterly extraction |
| QTRLY-07 | yfinance cross-validation | `cross_validate_yfinance()` in `xbrl_llm_reconciler.py`, needs call after quarterly extraction |
| QTRLY-08 | SourcedValue provenance on all quarterly values | Already implemented in `extract_quarterly_xbrl()` -- flows once data flows |
| FORM4-01 | Post-transaction ownership tracking + concentration | `compute_ownership_concentration()` and `build_ownership_trajectories()` in `insider_trading_analysis.py`, need calls from `extract_insider_trading()` |
| RENDER-01 | 8-quarter trend table renders real XBRL data | `financials_quarterly.py` context builder already wired, will show data once `quarterly_xbrl` is populated |
</phase_requirements>

## Standard Stack

No new libraries needed. All existing modules are built and tested.

### Core Modules (Already Built)

| Module | Location | Function(s) | Phase Built |
|--------|----------|-------------|-------------|
| xbrl_quarterly.py | stages/extract/ | `extract_quarterly_xbrl()` | 68-01 |
| xbrl_trends.py | stages/extract/ | `compute_all_trends()` | 68-02 |
| xbrl_llm_reconciler.py | stages/extract/ | `reconcile_quarterly()`, `cross_validate_yfinance()` | 68-03 |
| insider_trading_analysis.py | stages/extract/ | `compute_ownership_concentration()`, `build_ownership_trajectories()` | 71-01 |
| financials_quarterly.py | stages/render/context_builders/ | `build_quarterly_trend_context()` | 73-01 |

### Existing Tests

| Test File | What It Tests |
|-----------|---------------|
| test_xbrl_quarterly.py | `extract_quarterly_xbrl()` unit tests |
| test_xbrl_trends.py | `compute_all_trends()` unit tests |
| test_xbrl_reconciler.py | Reconciler unit tests |
| test_quarterly_integration.py | Quarterly update aggregation |
| test_financials_quarterly_context.py | Context builder |
| render/test_quarterly_html.py | Template rendering |

## Architecture Patterns

### Wiring Point 1: Extract Stage Orchestrator

**File:** `src/do_uw/stages/extract/__init__.py` (392 lines, room for ~100 more)

The extract stage runs extractors in numbered phases. Quarterly XBRL should be wired as a new phase between Phase 8c (yfinance quarterly) and Phase 9 (financial narrative). This follows the existing pattern:

```python
# Phase 8d: XBRL quarterly extraction (8 quarters)
# After annual statements (Phase 2) and yfinance quarterly (Phase 8c)
from do_uw.stages.extract.xbrl_quarterly import extract_quarterly_xbrl

facts = state.acquired_data.filings.get("company_facts") if state.acquired_data else None
cik = str(state.company.identity.cik.value) if state.company and state.company.identity.cik else ""

if facts and cik:
    quarterly = extract_quarterly_xbrl(facts, cik)
    extracted.financials.quarterly_xbrl = quarterly

    # Phase 8e: Trend computation
    if quarterly.quarters and len(quarterly.quarters) >= 2:
        from do_uw.stages.extract.xbrl_trends import compute_all_trends
        trends = compute_all_trends(quarterly)
        # Store trends in pipeline_metadata for signal access
        state.pipeline_metadata["quarterly_trends"] = {
            k: {"pattern": v.pattern, "consecutive_decline": v.consecutive_decline}
            for k, v in trends.items()
        }

    # Phase 8f: XBRL/LLM reconciliation
    from do_uw.stages.extract.xbrl_llm_reconciler import (
        reconcile_quarterly,
        cross_validate_yfinance,
    )
    recon_report = reconcile_quarterly(quarterly, extracted.financials.quarterly_updates)
    logger.info(
        "XBRL/LLM reconciliation: %d comparisons, %d divergences, %d XBRL wins",
        recon_report.total_comparisons,
        recon_report.divergences,
        recon_report.xbrl_wins,
    )

    # Phase 8g: yfinance cross-validation
    yf_report = cross_validate_yfinance(quarterly, extracted.financials.yfinance_quarterly)
    logger.info(
        "yfinance cross-validation: %d comparisons, %d divergences",
        yf_report.total_comparisons,
        yf_report.divergences,
    )
```

**Key dependencies:** `company_facts` is rehydrated in Phase 0 (`rehydrate_company_facts`). CIK is available after Phase 1 (company profile extraction). Annual statements are extracted in Phase 2. LLM quarterly_updates are extracted in Phase 8b. yfinance_quarterly is extracted in Phase 8c. So the quarterly XBRL extraction should go after Phase 8c.

### Wiring Point 2: Insider Trading Extractor

**File:** `src/do_uw/stages/extract/insider_trading.py` (489 lines, at limit -- careful with additions)

Add 2 calls to `extract_insider_trading()` after exercise-sell and timing analysis:

```python
# Phase 71-01: Ownership concentration
from do_uw.stages.extract.insider_trading_analysis import (
    compute_ownership_concentration,
    build_ownership_trajectories,
)

ownership_alerts = compute_ownership_concentration(transactions, clusters)
analysis.ownership_alerts = ownership_alerts
if ownership_alerts:
    red_flags = [a for a in ownership_alerts if a.severity == "RED_FLAG"]
    warnings.append(
        f"Ownership concentration alerts: {len(ownership_alerts)} "
        f"({len(red_flags)} RED_FLAG)"
    )

# Phase 71-01: Ownership trajectories
trajectories = build_ownership_trajectories(transactions)
analysis.ownership_trajectories = trajectories
```

**Line count concern:** `insider_trading.py` is at 489 lines. Adding ~15 lines for ownership wiring brings it to ~504. This exceeds the 500-line rule. Options:
1. Move the new code into existing `insider_trading_analysis.py` (currently 259 lines) as a wrapper function
2. Accept the minor overage since it is pipeline-critical wiring
3. Extract a small helper or consolidate existing code

**Recommendation:** Option 1 -- create a `run_ownership_analysis()` wrapper in `insider_trading_analysis.py` that takes transactions + clusters and returns (alerts, trajectories). Then `extract_insider_trading()` calls it in a single line.

### Anti-Patterns to Avoid

- **Don't create new modules** -- this is wiring, not building
- **Don't modify function signatures** -- all functions already have the correct interfaces
- **Don't add error handling that swallows failures silently** -- quarterly extraction failure should log but not crash the pipeline (use try/except with warning, matching existing pattern)
- **Don't store trends on a new model field** -- store in pipeline_metadata or let signals read directly from quarterly_xbrl (as signal_mappers_analytical.py already does)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Quarterly extraction | New extractor | `extract_quarterly_xbrl()` | Already built & tested |
| Trend computation | New trend module | `compute_all_trends()` | Already built & tested |
| XBRL/LLM reconciliation | New reconciler | `reconcile_quarterly()` | Already built & tested |
| Ownership analysis | New analysis | `compute_ownership_concentration()` | Already built & tested |
| yfinance cross-validation | New validator | `cross_validate_yfinance()` | Already built & tested |

## Common Pitfalls

### Pitfall 1: company_facts Not Available
**What goes wrong:** `state.acquired_data.filings["company_facts"]` may be None/empty for companies without XBRL filings.
**Why it happens:** Foreign private issuers, recently-IPO'd companies, or data acquisition failures.
**How to avoid:** Guard with `if facts and cik:` before calling `extract_quarterly_xbrl()`. The function itself handles empty data gracefully (returns empty QuarterlyStatements).
**Warning signs:** No quarterly data for test tickers that should have it.

### Pitfall 2: Line Count Overflow
**What goes wrong:** `insider_trading.py` at 489 lines, adding 15+ lines crosses the 500-line rule.
**How to avoid:** Use a wrapper function in `insider_trading_analysis.py` to keep the wiring call to 1-2 lines in the main file.

### Pitfall 3: Ordering Dependencies
**What goes wrong:** Calling quarterly extraction before `company_facts` rehydration or before company profile extraction (which provides CIK).
**How to avoid:** Place quarterly XBRL extraction after Phase 8c (yfinance quarterly), which is after all prerequisites.

### Pitfall 4: ReconciliationReport Not Stored
**What goes wrong:** Reconciliation runs but results are lost -- no audit trail.
**How to avoid:** Log the report summary (INFO level) and optionally store key metrics in `state.pipeline_metadata` for debugging.

### Pitfall 5: Trend Data Not Accessible to Signals
**What goes wrong:** `compute_all_trends()` runs but signals can't find the trend results.
**How to avoid:** The signal mapper `signal_mappers_analytical.py` already reads directly from `fin.quarterly_xbrl.quarters` (line 352-354). It does NOT read trend results -- it computes its own. So trend storage is informational only. The key thing is populating `quarterly_xbrl`.

## Code Examples

### Extract Stage Wiring (Verified Pattern from __init__.py)

The existing Phase 8b/8c pattern to follow:
```python
# Phase 8b: Quarterly updates (post-annual 10-Q aggregation)
from do_uw.stages.extract.quarterly_integration import (
    aggregate_quarterly_updates,
)
extracted.financials.quarterly_updates = (
    aggregate_quarterly_updates(state)
)

# Phase 8c: yfinance 8-quarter trending data
from do_uw.stages.extract.yfinance_quarterly import (
    extract_yfinance_quarterly,
)
extracted.financials.yfinance_quarterly = (
    extract_yfinance_quarterly(state)
)
```

### Insider Trading Wiring (Verified Pattern from insider_trading.py)

The existing Phase 71-02 pattern to follow:
```python
# Phase 71-02: Exercise-sell patterns
exercise_sell_events = detect_exercise_sell_patterns(transactions)
analysis.exercise_sell_events = exercise_sell_events
if exercise_sell_events:
    warnings.append(
        f"Exercise-sell patterns detected: {len(exercise_sell_events)} event(s)"
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yfinance-only quarterly | XBRL primary, yfinance fallback | Phase 68 (built) / Phase 74 (wired) | HIGH confidence quarterly data |
| No ownership analysis | Concentration alerts + trajectories | Phase 71 (built) / Phase 74 (wired) | Insider risk detection |
| LLM quarterly values | XBRL/LLM reconciler validates | Phase 68 (built) / Phase 74 (wired) | Anti-hallucination guarantee |

## Open Questions

1. **Trend storage location**
   - What we know: Signal mappers read directly from `quarterly_xbrl.quarters`, NOT from pre-computed trends
   - What's unclear: Should `compute_all_trends()` results be stored on the model or just logged?
   - Recommendation: Log key patterns at INFO level, store summary in `pipeline_metadata`. Don't add a new model field -- it would be unused by existing consumers.

2. **Reconciliation report persistence**
   - What we know: The reconciliation report is a dataclass, not a Pydantic model. It can't be stored directly on state.
   - What's unclear: Should we store the summary in pipeline_metadata?
   - Recommendation: Log the summary, store key counts (divergences, xbrl_wins) in `pipeline_metadata["xbrl_reconciliation"]` for downstream debugging.

## Sources

### Primary (HIGH confidence)
- `v3.1-MILESTONE-AUDIT.md` -- definitive gap identification with root cause analysis
- `src/do_uw/stages/extract/__init__.py` -- extract stage orchestrator (verified structure)
- `src/do_uw/stages/extract/insider_trading.py` -- insider trading extractor (verified call site)
- `src/do_uw/stages/extract/xbrl_quarterly.py` -- quarterly extraction function (verified interface)
- `src/do_uw/stages/extract/xbrl_trends.py` -- trend computation (verified interface)
- `src/do_uw/stages/extract/xbrl_llm_reconciler.py` -- reconciler (verified interface)
- `src/do_uw/stages/extract/insider_trading_analysis.py` -- ownership analysis (verified interface)

### Secondary (HIGH confidence)
- Phase 68 summaries (68-01/02/03-SUMMARY.md) -- original implementation details
- Phase 71 summaries (71-01/02-SUMMARY.md) -- Form 4 enhancement details
- `src/do_uw/stages/analyze/signal_mappers_analytical.py` -- confirms signals read from `quarterly_xbrl` directly

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all modules already built and tested
- Architecture: HIGH -- wiring pattern clearly established in existing code
- Pitfalls: HIGH -- root cause analysis in milestone audit is definitive

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable -- no external dependencies)
