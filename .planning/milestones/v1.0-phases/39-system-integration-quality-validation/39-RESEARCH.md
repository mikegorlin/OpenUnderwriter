# Phase 39: System Integration & Quality Validation - Research

**Researched:** 2026-02-21
**Domain:** End-to-end pipeline quality, check accuracy, knowledge loop validation, architectural cleanup, token tracking
**Confidence:** HIGH (all findings based on direct codebase investigation)

## Summary

Phase 39 is the system-level quality gate before the final polish phase. The codebase is 105K lines of Python across a 7-stage pipeline (RESOLVE through RENDER) with 384 checks in `brain/checks.json`, 4,157 tests, and three output formats (Word, PDF, Markdown). Research reveals several concrete issues that must be fixed:

1. **AAPL worksheet renders as "Unknown Company" with all sections showing "data not available"** despite the state.json containing complete data (Apple Inc., $3.8T market cap, 150K employees). This is a critical rendering/deserialization bug that represents exactly the deal-breaker quality issue the user identified.

2. **11 source files exceed 500 lines** (max: `enrichment_data.py` at 767, `calibrate.py` at 727), plus 33 test files over 500 lines. The `check_file_lengths.py` script already exists and catches these.

3. **`classify/` and `hazard/` directories physically remain** under `stages/` with their own import paths, despite Phase 29's conceptual absorption into the ANALYZE stage. The CONTEXT.md calls for moving them to `analyze/layers/`.

4. **LLM CostTracker exists** in `stages/extract/llm/cost_tracker.py` but is not surfaced to the pipeline level or worksheet footer. Token counts are tracked per-extraction but lost at the pipeline boundary.

5. **Knowledge feedback loop infrastructure is complete** (feedback CLI, calibration CLI, backtest system, proposal generation, DuckDB storage) but has never been validated end-to-end with real round-trip scenarios.

**Primary recommendation:** Fix the rendering deserialization bug first (it undermines trust in the entire system), then systematically audit every TRIGGERED and SKIPPED check across both AAPL and TSLA, wire token tracking to the worksheet footer, validate the knowledge loop end-to-end, and clean up architecture debt.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### False Trigger Triage
- **Zero tolerance** for false triggers -- every triggered check must be genuinely relevant to the data it evaluates
- **Full audit** of both AAPL and TSLA -- review every TRIGGERED check result for accuracy
- **Audit SKIPPED checks too** -- a skipped check that should have fired is equally bad; both undermine underwriter trust
- **Fix the check logic itself** -- improve field routing, threshold parsing, or mapper logic so checks evaluate against the correct data. No exclusion rules or workarounds.
- Discovery method: run full backtest on both tickers, audit every TRIGGERED and SKIPPED result

#### Worksheet Quality Bar
- **Single source of truth** -- completeness, accuracy, AND actionability all matter equally. An underwriter must be able to make decisions based solely on this worksheet.
- **Clarity and transparency are paramount** -- every data point sourced, every risk signal visible, every narrative tells a clear story
- **Deal-breakers (any of these = reject):**
  - Wrong company data (data integrity failures like TSLA showing Tim Cook)
  - Missing known public risk signals (active lawsuits, SEC investigations not appearing)
  - Unsourced claims presented as fact
  - Stale data presented as current
  - Misleading narrative that downplays real risks
- **Reusable quality checklist** -- create a standard per-section verification checklist that becomes part of the system for every run, not a one-time review
- **All 3 formats (Word, PDF, Markdown) must meet the same quality bar** -- underwriters may use any of them

#### Architecture Cleanup Scope
- **Broader sweep** beyond named items -- use this as an opportunity to clean up anything violating anti-context-rot rules
- Named items: classify/ and hazard/ directories to analyze/layers/, checks.json sync from DuckDB, calibrate.py split
- **Pragmatic 500-line enforcement** -- split files that are genuinely hard to navigate; well-organized cohesive files slightly over 500 lines are acceptable
- **Reusable dead code detection tool** -- build a script/command that can be re-run after any phase, not a one-time vulture scan
- **Full import cleanup** on directory moves -- update every import across the codebase, no backwards-compat shims or re-exports

#### Knowledge Loop Validation
- **Full round-trip testing** -- submit feedback, verify persistence in DuckDB, re-run calibration, confirm score actually changed, verify learning persists
- **Three feedback scenarios to test:**
  1. Score overrides -- "This company should be HIGH risk, not MEDIUM" -> verify future scoring adjusts
  2. False trigger reports -- "This check fired incorrectly" -> verify check gets suppressed or adjusted
  3. Data corrections -- "Revenue was wrong, here's the real number" -> verify correction persists
- **Real SEC filings** for document ingestion tests -- prove the pipeline works with real-world data, not synthetic test documents

#### LLM Token Tracking
- **Worksheet footer** -- include data freshness date and estimated API cost in the final worksheet output for transparency
- Per-stage token count and cost in pipeline logs

### Claude's Discretion
- Exact approach to backtest automation (script vs. test harness)
- Which dead code detection tool to use or build
- Organization of the reusable quality checklist (config file vs. code vs. test suite)
- Order of operations within the phase (cleanup first vs. fixes first vs. parallel)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| pydantic | >=2.10 | State models, check definitions | In use, stable |
| duckdb | >=1.4.4 | Brain DB, knowledge store, feedback persistence | In use, stable |
| jinja2 | >=3.1.0 | Template rendering for MD/HTML/PDF | In use, stable |
| python-docx | >=1.1.0 | Word document generation | In use, stable |
| playwright | >=1.58.0 | HTML-to-PDF rendering | In use, stable |
| typer+rich | >=0.15 | CLI with progress display | In use, stable |

### Supporting (To Add)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| vulture | >=2.13 | Dead code detection | Reusable dead code scan script |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| vulture | Custom grep-based script | Vulture has better false-positive handling via whitelist files, but custom scripts can be more targeted. Recommend vulture for comprehensive scanning plus a custom wrapper for CI integration. |
| pytest-based quality tests | Standalone script | pytest integration lets quality checks run with the test suite, making them harder to skip. Standalone script is simpler but requires separate invocation. Recommend pytest markers for quality assertions. |

**Installation:**
```bash
uv add --dev vulture
```

## Architecture Patterns

### Current File Structure (Phase 39 Cleanup Targets)
```
src/do_uw/
  stages/
    classify/          # TARGET: Move to analyze/layers/classify/
      __init__.py
      classification_engine.py
      severity_bands.py
    hazard/            # TARGET: Move to analyze/layers/hazard/
      __init__.py
      hazard_engine.py
      dimension_scoring.py
      dimension_h1_business.py through dimension_h7_emerging.py
      data_mapping.py, data_mapping_h2_h3.py, data_mapping_h4_h7.py
      interaction_effects.py
    analyze/
      __init__.py      # Imports from classify/ and hazard/ here
      check_engine.py  # 384 lines
      check_mappers.py # 489 lines (approaching limit)
      ...
  brain/
    checks.json        # 384 checks, source of truth alongside brain.duckdb
    brain_writer.py    # 561 lines -- OVER LIMIT
    enrichment_data.py # 767 lines -- OVER LIMIT
  knowledge/
    calibrate.py       # 727 lines -- OVER LIMIT
    ...
  cli_brain.py         # 633 lines -- OVER LIMIT
  cli_knowledge.py     # 505 lines -- OVER LIMIT
```

### Post-Cleanup Structure
```
src/do_uw/
  stages/
    analyze/
      layers/
        classify/      # Moved from stages/classify/
        hazard/        # Moved from stages/hazard/
      check_engine.py
      ...
  brain/
    brain_writer.py    # Split: brain_writer.py + brain_writer_export.py
    enrichment_data.py # Split: enrichment_data.py + enrichment_data_ext.py
  knowledge/
    calibrate.py       # Split: calibrate.py + calibrate_impact.py
```

### Pattern 1: Backtest Audit Script
**What:** A script/test that runs backtest on AAPL and TSLA state files, collects all TRIGGERED and SKIPPED results, and produces a human-readable audit report.
**When to use:** After any change to check logic, field routing, or threshold definitions.
**Implementation approach:**
```python
# tests/test_backtest_audit.py or scripts/backtest_audit.py
from do_uw.knowledge.backtest import run_backtest
from pathlib import Path

def audit_backtest(ticker: str, state_path: Path) -> dict:
    """Run backtest and classify results for human review."""
    result = run_backtest(state_path, record=False)
    return {
        "triggered": {k: v for k, v in result.results_by_id.items() if v == "TRIGGERED"},
        "skipped": {k: v for k, v in result.results_by_id.items() if v == "SKIPPED"},
        "clear": {k: v for k, v in result.results_by_id.items() if v == "CLEAR"},
        "info": {k: v for k, v in result.results_by_id.items() if v == "INFO"},
    }
```

### Pattern 2: Quality Checklist as Pytest Assertions
**What:** Per-section quality assertions that validate worksheet output against known requirements.
**When to use:** On every re-render and as CI gate.
**Implementation approach:**
```python
# tests/test_worksheet_quality.py
import pytest

class TestWorksheetQuality:
    """Quality gate: reusable checklist for worksheet output validation."""

    def test_company_name_not_unknown(self, worksheet_md: str) -> None:
        assert "Unknown Company" not in worksheet_md

    def test_no_unsourced_claims(self, state: AnalysisState) -> None:
        # Verify every SourcedValue has a non-empty source
        ...

    def test_all_sections_have_content(self, worksheet_md: str) -> None:
        # No "data not available" in any section when state has data
        ...
```

### Pattern 3: Token Cost in Worksheet Footer
**What:** Surface CostTracker totals through pipeline to render stage.
**When to use:** Every pipeline run.
**Implementation approach:**
```python
# In pipeline.py or state model
# Option A: Store in AnalysisState metadata
state.pipeline_metadata = {
    "llm_tokens_input": cost_tracker.total_input_tokens,
    "llm_tokens_output": cost_tracker.total_output_tokens,
    "llm_cost_usd": cost_tracker.total_cost_usd,
    "data_freshness_date": "2026-02-21",
}
# Then render in worksheet footer template
```

### Anti-Patterns to Avoid
- **Workaround-based false trigger fixes:** Don't add exclusion lists or "skip this check for AAPL" rules. Fix the underlying field routing or threshold so the check evaluates correctly everywhere.
- **One-time cleanup scripts:** Phase 39 explicitly requires reusable tools (dead code detection, quality checklist). Don't create scripts that only run once.
- **Backwards-compat import shims:** When moving classify/hazard, update ALL imports directly. No `from do_uw.stages.classify import *` re-export from the old location.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dead code detection | Custom grep for unused functions | `vulture` (+ whitelist) | Vulture understands Python AST, handles dynamic dispatch, supports whitelisting known false positives |
| File length enforcement | Manual checking | Existing `scripts/check_file_lengths.py` | Already built, already used, just enforce it |
| Import cleanup after directory moves | Manual find-and-replace | `ruff` fixable imports + grep verification | ruff can fix simple import issues; grep catches what ruff misses |
| Cross-format rendering parity | Manual comparison | Existing `tests/test_cross_format_consistency.py` | Already has framework for testing MD/Word/HTML parity |

**Key insight:** Most infrastructure already exists. The CostTracker, backtest system, feedback loop, quality checklist framework, and cross-format tests are all built. Phase 39 is about wiring them together end-to-end and validating they actually work with real data.

## Common Pitfalls

### Pitfall 1: State Deserialization Regression
**What goes wrong:** The AAPL worksheet currently renders "Unknown Company" and "data not available" everywhere despite complete data in state.json. This suggests a Pydantic model change broke deserialization of older state files, or a render-only path skips state loading.
**Why it happens:** State model evolves across phases. Field additions, renames, or type changes can silently cause older state.json files to load with None/missing fields.
**How to avoid:** After any model change, load the existing AAPL and TSLA state.json files and verify all top-level fields are non-None. Add a regression test that loads known-good state files.
**Warning signs:** Sections rendering "not available" when `state.json` contains the data; "Unknown Company" in output.

### Pitfall 2: False Trigger Fix Cascades
**What goes wrong:** Fixing one false trigger (e.g., routing BIZ.DEPEND.labor to `labor_risk_flag_count` instead of `employee_count`) can change which checks fire on all tickers, potentially introducing new false negatives.
**Why it happens:** Check field routing is a many-to-many mapping. Changing one mapping affects all checks that share the same mapper.
**How to avoid:** Always run backtest on both AAPL and TSLA before and after any field routing change. Compare results diff.
**Warning signs:** A field routing fix causes previously-CLEAR checks to become SKIPPED (data no longer found) or previously-INFO checks to become TRIGGERED.

### Pitfall 3: Directory Move Import Breakage
**What goes wrong:** Moving `stages/classify/` and `stages/hazard/` to `stages/analyze/layers/` breaks imports in 25+ files across src/ and tests/.
**Why it happens:** Internal imports within hazard/ reference each other (e.g., `from do_uw.stages.hazard.data_mapping import ...`), and external consumers in analyze/__init__.py, tests, and render use the old paths.
**How to avoid:** Use `grep -r "from do_uw.stages.classify\|from do_uw.stages.hazard"` to find ALL import sites. There are currently 25 import statements in src/ and 4 test files to update. Do the move atomically: move files, update all imports, run tests.
**Warning signs:** `ModuleNotFoundError` on any `do_uw.stages.classify` or `do_uw.stages.hazard` import.

### Pitfall 4: Knowledge Loop Silent Failures
**What goes wrong:** Feedback is recorded in DuckDB but calibration proposals never surface, or proposals are applied but have no effect on actual scoring.
**Why it happens:** The feedback -> proposal -> calibration -> scoring pipeline has multiple handoff points (DuckDB tables, JSON export, check engine loading). Any one link can break silently.
**How to avoid:** Test the full round-trip with assertions at each step: (1) feedback_id returned, (2) proposal created in brain_proposals, (3) calibration preview shows the change, (4) calibration apply modifies brain_checks_active, (5) re-run backtest shows changed result.
**Warning signs:** `pending_proposals: 0` after submitting feedback that should generate a proposal.

### Pitfall 5: Token Tracking Data Loss
**What goes wrong:** CostTracker records tokens during extraction, but the summary is never persisted. If the pipeline crashes or the ExtractStage object is garbage collected, token data is lost.
**Why it happens:** CostTracker is an in-memory object living inside LLMExtractor. Nothing persists it to state.json or passes it to the pipeline.
**How to avoid:** At ExtractStage completion, write the cost summary to `state.pipeline_metadata` or a dedicated field. This way it survives in the state file for the render stage to pick up.
**Warning signs:** `state.json` has no token/cost fields; worksheet footer shows no API cost.

## Code Examples

### Example 1: Current AAPL Backtest Results (from state.json investigation)
```
AAPL Check Results:
  Total: 391, TRIGGERED: 7, CLEAR: 51, SKIPPED: 97, INFO: 236

TRIGGERED (7):
  EXEC.INSIDER.ceo_net_selling:   val=100.0, red threshold 80.0
  EXEC.INSIDER.cfo_net_selling:   val=100.0, red threshold 80.0
  FIN.LIQ.efficiency:             val=0.217, yellow threshold 0.5
  FIN.LIQ.position:               val=0.8933, red threshold 6.0
  FIN.LIQ.working_capital:        val=0.8933, red threshold 1.0
  FIN.QUALITY.dso_ar_divergence:  val=11.86, yellow threshold 10.0
  NLP.RISK.regulatory_risk_factor_new: val=1.0, boolean True

SKIPPED (97): All have data_status=DATA_UNAVAILABLE
  Notable: BIZ.DEPEND.labor, EXEC.CEO.risk_score, EXEC.CFO.risk_score,
           EXEC.PROFILE.avg_tenure, FIN.ACCT.auditor_attestation_fail,
           FIN.QUALITY.deferred_revenue_trend, etc.
```

### Example 2: Current TSLA Backtest Results
```
TSLA Check Results:
  Total: 391, TRIGGERED: 12, CLEAR: 41, SKIPPED: 43, INFO: 295

TRIGGERED (12):
  STOCK.PRICE.peer_relative:      val=17.31, yellow threshold 10.0
  STOCK.PRICE.single_day_events:  val=17.0, yellow threshold 10.0
  STOCK.PRICE.technical:          val=42.69, yellow threshold 35.0
  FIN.PROFIT.earnings:            val=3.89, red threshold 2.0
  FIN.ACCT.material_weakness:     val=2.0, boolean True
  GOV.INSIDER.net_selling:        val=11.135, red threshold 5.0
  EXEC.AGGREGATE.board_risk:      val=45.4, yellow threshold 35.0
  EXEC.PRIOR_LIT.any_officer:     val=75.0, boolean True
  EXEC.PRIOR_LIT.ceo_cfo:         val=75.0, boolean True
  EXEC.INSIDER.cfo_net_selling:   val=100.0, red threshold 80.0
  EXEC.INSIDER.cluster_selling:   val=1.0, boolean True
  EXEC.PROFILE.ceo_chair_duality: val=1.0, boolean True
```

### Example 3: Files Exceeding 500 Lines (Source Only)
```
FAIL: src/do_uw/brain/enrichment_data.py    767 lines
FAIL: src/do_uw/knowledge/calibrate.py      727 lines
FAIL: src/do_uw/cli_brain.py                633 lines
FAIL: src/do_uw/brain/brain_writer.py       561 lines
FAIL: src/do_uw/stages/extract/earnings_guidance.py      533 lines
FAIL: src/do_uw/stages/extract/regulatory_extract.py     521 lines
FAIL: src/do_uw/stages/extract/company_profile.py        518 lines
FAIL: src/do_uw/stages/acquire/clients/sec_client.py     511 lines
FAIL: src/do_uw/stages/analyze/financial_formulas.py     509 lines
FAIL: src/do_uw/stages/score/factor_data.py              506 lines
FAIL: src/do_uw/cli_knowledge.py                         505 lines
```

### Example 4: Import Sites for classify/hazard Move
```
Source files importing from stages/classify (4 internal, 2 external):
  stages/classify/__init__.py (self)
  stages/classify/classification_engine.py (internal)
  stages/analyze/__init__.py (consumer)

Source files importing from stages/hazard (12 internal, 2 external):
  stages/hazard/__init__.py (self)
  stages/hazard/hazard_engine.py (internal)
  stages/hazard/dimension_scoring.py (internal, 7 dimension imports)
  stages/hazard/data_mapping.py (internal)
  stages/hazard/data_mapping_h2_h3.py (internal)
  stages/hazard/data_mapping_h4_h7.py (internal)
  stages/hazard/interaction_effects.py (internal)
  stages/analyze/__init__.py (consumer)

Test files:
  tests/test_classification.py
  tests/test_classification_integration.py
  tests/test_hazard_engine.py
  tests/test_hazard_dimensions.py
```

### Example 5: CostTracker Wiring Gap
```python
# CURRENT: CostTracker lives inside LLMExtractor, never surfaces
# src/do_uw/stages/extract/llm/extractor.py
class LLMExtractor:
    def __init__(self, ...):
        self._cost_tracker = CostTracker(budget_usd=budget_usd)

    def cost_summary(self) -> dict[str, Any]:
        return self._cost_tracker.summary()  # <-- Called nowhere by pipeline

# NEEDED: Wire through ExtractStage -> Pipeline -> State -> Render
# src/do_uw/stages/extract/__init__.py (ExtractStage.run)
#   -> at end: state.pipeline_metadata["llm_cost"] = extractor.cost_summary()
# src/do_uw/stages/render/ (worksheet footer)
#   -> read state.pipeline_metadata["llm_cost"] for footer display
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| classify/ and hazard/ as separate pipeline stages | Sub-steps of ANALYZE (conceptual) | Phase 29 | Import paths still use old locations -- physical move pending |
| No token tracking | CostTracker per extraction | Phase 29 | Tracks per-extraction but not surfaced to pipeline or output |
| Manual check audit | Backtest infrastructure | Phase 32 | Can replay checks against state files, records in DuckDB |
| No feedback mechanism | Full feedback + proposal + calibration CLI | Phase 34 | Infrastructure complete, never validated end-to-end |
| Single format (MD) | Three formats (MD, Word, PDF) | Phase 35-38 | Coverage >90% in all 3, but rendering quality varies |

**Current state:**
- 4,157 tests, all passing
- 44 files exceed 500 lines (11 source, 33 tests)
- Existing render coverage framework in `stages/render/coverage.py`
- Existing cross-format consistency tests in `tests/test_cross_format_consistency.py`
- Existing backtest infrastructure in `knowledge/backtest.py`
- Existing quality validation runner in `validation/runner.py`

## Codebase Findings

### Finding 1: AAPL Worksheet Rendering Bug (CRITICAL)
**Confidence:** HIGH (directly observed in output files)

The current `output/AAPL/AAPL_worksheet.md` (generated 2026-02-21 15:06) shows:
- Line 4: `**Company:** Unknown Company`
- Line 18: `| Company |  |` (empty)
- Lines 73, 85, 97, 109, 120: "*Company/Financial/Market/Governance/Litigation data not available.*"

But `output/AAPL/state.json` (saved 2026-02-21 10:29) contains:
- `identity.legal_name.value` = "Apple Inc."
- `company.market_cap.value` = 3888777003008.0
- `company.employee_count.value` = 150000
- Full extracted financial, market, governance, litigation data

Meanwhile, `output/AAPL_rerender/AAPL_worksheet.md` (from 2026-02-15) renders correctly with "Apple Inc.", "$3.8T", "150,000 employees".

**Root cause hypothesis:** A Pydantic model change between Feb 15 and Feb 21 broke deserialization. When loading the state file for re-render, fields silently become None because the model schema changed. The renderer correctly handles None by showing "not available" -- the bug is in data loading, not rendering.

**Action:** Investigate what model changes occurred after Feb 15. Add a regression test that loads both AAPL and TSLA state.json files and asserts all key fields are non-None.

### Finding 2: AAPL Score of 100/100 with NO_TOUCH Tier (Suspicious)
**Confidence:** HIGH

AAPL scores 100/100 quality score but gets classified as NO_TOUCH (decline). The AAPL_rerender (Feb 15) shows a more reasonable 88/100 WIN tier. A perfect 100 with a decline recommendation is contradictory and suggests the scoring is failing to deduct points because extracted data isn't loading properly.

### Finding 3: TSLA Prior Litigation Checks May Be Data Integrity Issue
**Confidence:** MEDIUM

TSLA triggers `EXEC.PRIOR_LIT.any_officer` and `EXEC.PRIOR_LIT.ceo_cfo` with value=75.0. The MEMORY.md notes "Kimbal Musk with 75 prior litigations" as an LLM hallucination. The executives list in the current state file is empty (`[]`), yet these checks still trigger with value 75.0, suggesting stale or incorrectly routed data.

### Finding 4: checks.json / DuckDB Dual Authority
**Confidence:** HIGH

`BrainDBLoader` (brain_loader.py) uses a dual-source approach:
- DuckDB (`brain_checks_active` view) determines which checks are active
- `checks.json` provides full execution details (thresholds, mappers, factors)
- Enrichment metadata from DuckDB is overlaid onto checks.json data

The CONTEXT.md mentions "checks.json sync from DuckDB" as cleanup needed. Currently `BrainWriter.export_to_json()` can write to checks.json, but the sync direction (DuckDB -> JSON vs JSON -> DuckDB) varies by operation.

### Finding 5: Token Tracking Infrastructure Gap
**Confidence:** HIGH

The `CostTracker` class in `stages/extract/llm/cost_tracker.py` is fully functional:
- Tracks input/output tokens per extraction
- Computes USD cost at Haiku 4.5 rates ($1/MTok in, $5/MTok out)
- Budget enforcement with per-company limit
- Thread-safe for parallel extraction

But it is not wired to the pipeline or state model:
- `LLMExtractor.cost_summary()` is never called by `ExtractStage`
- No field in `AnalysisState` stores pipeline-level metadata like cost
- No template in any renderer references cost information
- `validation/cost_report.py` exists but reads from ExtractionCache, not CostTracker

### Finding 6: Dead Code Detection Landscape
**Confidence:** HIGH

No dead code detection tool is currently installed. Options:
- **vulture**: Mature Python dead code detector, AST-based, supports whitelist files. Available via `pip install vulture`. Recommended.
- **pyflakes**: Already a ruff dependency, catches unused imports but not unused functions
- **ruff**: Already in use, catches unused imports (F401) but not unreachable code or unused functions
- Custom script: Could leverage `ast` module + import graph, but vulture already does this

Recommendation: Add vulture as dev dependency, create `scripts/dead_code_scan.py` wrapper that runs vulture with project-specific whitelist and outputs actionable report.

## Open Questions

1. **What model change broke AAPL rendering?**
   - What we know: The Feb 15 re-render works, the Feb 21 render doesn't, same state.json
   - What's unclear: Which model field changed between these dates
   - Recommendation: `git log --since=2026-02-15 -- src/do_uw/models/` to identify model changes, then validate deserialization of the AAPL state file against the current model

2. **Are TSLA EXEC.PRIOR_LIT triggers genuine or from hallucinated data?**
   - What we know: MEMORY.md reports "Kimbal Musk with 75 prior litigations" as hallucinated; current TSLA state shows empty executives list but val=75.0 in prior lit checks
   - What's unclear: Whether the 75.0 value comes from the current run's executive forensics or from cached/stale data
   - Recommendation: Trace the EXEC.PRIOR_LIT data path through check_mappers_phase26.py to determine what data source produces the 75.0 value

3. **Should the quality checklist be config-driven or code-driven?**
   - What we know: User wants it reusable and permanent, not a one-time document
   - Options: (a) JSON config listing expected fields per section, validated by a test; (b) pytest test class with per-section assertions; (c) a `config/quality_checklist.json` consumed by both tests and a CLI command
   - Recommendation: Pytest test class (option b) -- it runs automatically, fails loudly, and developers naturally maintain it. Add a `scripts/quality_check.py` CLI wrapper for ad-hoc use that imports from the same test module.

4. **How deep should the SKIPPED check audit go?**
   - What we know: AAPL has 97 SKIPPED checks (all DATA_UNAVAILABLE), TSLA has 43
   - What's unclear: How many of these are legitimately unavailable vs. field routing failures
   - Recommendation: Categorize SKIPPED checks into (a) data genuinely not extracted for this ticker, (b) data extracted but check can't find it due to routing, (c) data type mismatch. Fix category (b) and (c); document category (a) as extraction gaps for future phases.

## Sources

### Primary (HIGH confidence)
- Direct codebase investigation: every file path, line count, and data value was verified by reading source files and state.json
- `output/AAPL/state.json` and `output/AAPL/AAPL_worksheet.md` -- direct comparison showing the rendering bug
- `output/AAPL_rerender/AAPL_worksheet.md` -- working render from Feb 15 for comparison
- `output/TSLA/state.json` -- check result analysis
- `scripts/check_file_lengths.py` output -- 11 source files, 33 test files over 500 lines

### Secondary (MEDIUM confidence)
- MEMORY.md notes on TSLA exec list corruption -- reported but not independently verified in current run data
- Phase 29 SUMMARY.md on classify/hazard absorption -- conceptual change documented but physical move not completed

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools already in the project or are well-known Python utilities
- Architecture: HIGH -- based on direct reading of every relevant file in the codebase
- Pitfalls: HIGH -- identified from actual bugs found in current output files
- Knowledge loop: MEDIUM -- infrastructure exists but untested end-to-end; actual behavior may differ from design

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (stable codebase, no external dependencies changing)
