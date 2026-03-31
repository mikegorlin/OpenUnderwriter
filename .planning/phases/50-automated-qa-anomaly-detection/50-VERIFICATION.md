---
phase: 50-automated-qa-anomaly-detection
verified: 2026-02-27T04:30:00Z
status: passed
score: 14/14 must-haves verified
re_verification: false
human_verification:
  - test: "Run `do-uw analyze AAPL` end-to-end and inspect post-pipeline output"
    expected: "After QA report prints, a Rich-formatted Signal Health Summary appears with TRIGGERED/CLEAR/SKIPPED/INFO counts, section breakdown, and any anomaly warnings. If 0 signals are TRIGGERED and active_cases is non-empty, a WARNING anomaly fires."
    why_human: "Cannot run full pipeline without MCP data acquisition. Verified hook wiring (cli.py lines 354-360) and health_summary.py logic programmatically, but Rich terminal output and real anomaly detection requires live state."
---

# Phase 50: Automated QA & Anomaly Detection — Verification Report

**Phase Goal:** Signal detail enrichment, composite evaluation engine, brain health/audit/delta CLI tooling
**Verified:** 2026-02-27T04:30:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SignalResult has a `details` field for composites to read | VERIFIED | `details` in `SignalResult.model_fields` confirmed via Python import; field at line 176 of signal_results.py |
| 2 | Post-evaluation enrichment populates details for 4 signal domains | VERIFIED | signal_details.py: `_enrich_stock_drop_events`, `_enrich_insider_trading`, `_enrich_litigation`, `_enrich_financial_distress` all substantive; wired into signal_engine.py line 129-131 |
| 3 | Health summary prints after every `do-uw analyze` run with counts and anomaly warnings | VERIFIED | cli.py lines 354-360 import and call `compute_health_summary` + `print_health_summary`; manual print test confirms Rich-formatted output with Evaluated/TRIGGERED/CLEAR/INFO/SKIPPED rows |
| 4 | Three anomaly rules: 0-TRIGGERED-with-litigation, high-SKIPPED (>45), all-section-SKIPPED | VERIFIED | health_summary.py: `_check_zero_triggered_with_litigation` (line 215), `_check_high_skipped` (line 285), `_check_section_all_skipped` (line 305); `MAX_SKIPPED_THRESHOLD=45` at line 27 |
| 5 | `do-uw brain health` shows coverage %, fire rate distribution, top signals, freshness | VERIFIED | CLI runs cleanly; shows 380 active (of 400), 100% facet coverage, 6-bucket fire rate histogram, always-fire/never-fire/high-skip tables, freshness, feedback queue |
| 6 | `do-uw brain audit` shows staleness, peril coverage NOT AVAILABLE, threshold conflicts, orphans | VERIFIED | CLI runs cleanly; shows 380 never-calibrated, "NOT AVAILABLE (0/380 signals have peril assignments)", "No threshold conflicts detected", "All active signals are assigned to facets" |
| 7 | `do-uw brain delta <TICKER>` shows signal status changes between two most recent runs | VERIFIED | `brain delta TEST` runs; shows old/new run metadata (run_id, date, signal count) and reports "No signal status changes between runs" with correct grouping logic |
| 8 | `do-uw brain delta NONEXISTENT` shows clear error when < 2 runs | VERIFIED | Exit code 1; message: "Need at least 2 runs for delta. Found 0 run(s) for NONEXISTENT. Run 'do-uw analyze NONEXISTENT' to create more runs." |
| 9 | `--list-runs` lists available runs with dates | VERIFIED | `brain delta TEST --list-runs` shows Rich table with run_id, date, signal count for 3 TEST runs |
| 10 | CompositeDefinition YAML + CompositeResult Pydantic model + evaluate_composites() engine | VERIFIED | `brain_composite_schema.py` has both models (114 lines); `brain_composite_engine.py` has `evaluate_composites()` with 4-function dispatch registry (513 lines) |
| 11 | 3 composites defined: COMP.STOCK.drop_analysis, short_analysis, insider_analysis | VERIFIED | All 3 YAML files in `src/do_uw/brain/composites/`; `load_all_composites()` returns all 3 with correct member counts |
| 12 | evaluate_composites() wired into AnalyzeStage.run() pipeline | VERIFIED | `_run_composites()` at analyze/__init__.py line 204; called at line 448 inside pipeline try/except block |
| 13 | Composite results stored in state.analysis.composite_results | VERIFIED | `state.py` line 246: `composite_results: dict[str, Any] = Field(default_factory=dict)`; _run_composites() writes to it |
| 14 | FacetSpec evolved with content list referencing composites; backward compatible | VERIFIED | `brain_facet_schema.py` line 24: `FacetContentRef` model; line 68: `content` field on `FacetSpec`; `market_activity.yaml` has `content:` referencing 3 COMP.STOCK.* composites and 23 standalone signals, plus preserved `signals:` list |

**Score:** 14/14 truths verified

### Required Artifacts

| Artifact | Plan | Status | Details |
|----------|------|--------|---------|
| `src/do_uw/stages/analyze/signal_results.py` | 50-01 | VERIFIED | 10,554 bytes; `details: dict[str, Any]` field at line 176 |
| `src/do_uw/stages/analyze/signal_details.py` | 50-01 | VERIFIED | 8,382 bytes / 251 lines; 4 domain enrichment functions + dispatch |
| `src/do_uw/validation/health_summary.py` | 50-01 | VERIFIED | 15,258 bytes / 461 lines; compute + print functions + 3 anomaly rules |
| `src/do_uw/brain/brain_health.py` | 50-02 | VERIFIED | 7,580 bytes / 218 lines; `BrainHealthReport` + `compute_brain_health()` |
| `src/do_uw/brain/brain_audit.py` | 50-02 | VERIFIED | 16,343 bytes / 475 lines; `AuditFinding` + `BrainAuditReport` + `compute_brain_audit()` |
| `src/do_uw/cli_brain_health.py` | 50-02/03 | VERIFIED | 18,995 bytes / 596 lines; health, audit, delta CLI commands all registered |
| `src/do_uw/brain/brain_delta.py` | 50-03 | VERIFIED | 7,855 bytes / 256 lines; `DeltaReport`, `SignalChange`, `RunInfo`, `compute_delta()`, `list_runs()` |
| `tests/brain/test_brain_delta.py` | 50-03 | VERIFIED | 8,528 bytes; 9 tests — all pass |
| `src/do_uw/brain/brain_composite_schema.py` | 50-04 | VERIFIED | 3,959 bytes / 114 lines; `CompositeDefinition`, `CompositeResult`, `load_all_composites()` |
| `src/do_uw/brain/brain_composite_engine.py` | 50-04 | VERIFIED | 17,223 bytes / 513 lines; `evaluate_composites()` + 4 evaluators |
| `src/do_uw/brain/composites/stock_drop_analysis.yaml` | 50-04 | VERIFIED | 965 bytes; 6 member signals, evaluator=stock_drop_analysis |
| `src/do_uw/brain/composites/stock_short_analysis.yaml` | 50-04 | VERIFIED | 770 bytes; 4 member signals, evaluator=stock_short_analysis |
| `src/do_uw/brain/composites/stock_insider_analysis.yaml` | 50-04 | VERIFIED | 713 bytes; 3 member signals, evaluator=stock_insider_analysis |
| `tests/brain/test_brain_composites.py` | 50-04 | VERIFIED | 8,455 bytes; 9 tests — all pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `validation/health_summary.py` | `models/analysis_models.py (AnalysisState)` | `_get_signal_results_from_state()` reads `signal_results` and legacy `check_results` | WIRED | Lines 70-101 in health_summary.py |
| `cli.py (post-pipeline hook)` | `validation/health_summary.py` | `compute_health_summary` + `print_health_summary` called after `print_qa_report` | WIRED | cli.py lines 354-360 |
| `stages/analyze/signal_engine.py` | `stages/analyze/signal_details.py` | `enrich_signal_details(results, extracted)` called post-evaluation | WIRED | signal_engine.py lines 129-131 |
| `brain/brain_health.py` | `brain/brain_effectiveness.py` | `compute_effectiveness(conn)` called for fire rate data | WIRED | brain_health.py lines 19, 129 |
| `brain/brain_health.py` | `brain/brain_facet_schema.py` | `load_all_facets()` for coverage % computation | WIRED | brain_health.py lines 20, 114 |
| `cli_brain_health.py` | `cli_brain.py` | `import do_uw.cli_brain_health as _cli_brain_health` registers commands | WIRED | cli_brain.py lines 429-431 |
| `brain/brain_delta.py` | `brain_signal_runs table` | SQL queries: run enumeration + FULL OUTER JOIN for status diff | WIRED | brain_delta.py lines 82-107, 185-218 |
| `cli_brain_health.py (delta cmd)` | `brain/brain_delta.py` | `compute_delta()` and `list_runs()` called from CLI command | WIRED | cli_brain_health.py lines 241, 257, 287 |
| `brain/brain_composite_engine.py` | `models/analysis_models.py (SignalResult.details)` | `_get_details(result)` reads `details` key from signal result dict | WIRED | brain_composite_engine.py lines 85-88 |
| `brain/composites/*.yaml` | `brain/signals/**/*.yaml` | `test_all_composite_member_signals_exist` validates all member_signal IDs exist | WIRED | test_brain_composites.py; 9 tests all pass |
| `brain/facets/market_activity.yaml` | `brain/composites/*.yaml` | `content:` list references COMP.STOCK.drop_analysis, short_analysis, insider_analysis | WIRED | market_activity.yaml lines 13-21 |
| `stages/analyze/__init__.py` | `brain/brain_composite_engine.py` | `_run_composites()` calls `evaluate_composites()` at pipeline line 448 | WIRED | analyze/__init__.py lines 204-238, 448 |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| QA-01 | 50-01 | Every `do-uw analyze` run ends with automated health summary -- evaluated/TRIGGERED/SKIPPED counts, anomaly warnings | SATISFIED | `compute_health_summary` + `print_health_summary` wired in cli.py post-pipeline hook; 3 anomaly rules implemented |
| QA-02 | 50-02, 50-04 | User can view unified system health with `do-uw brain health` -- coverage %, fire rate distribution, top signals, freshness, feedback queue | SATISFIED | CLI verified: shows 380 active, 100% coverage, 6-bucket fire rate histogram, top always/never/high-skip, pipeline runs, tickers |
| QA-04 | 50-03 | User can detect cross-run changes with `do-uw brain delta <TICKER>` | SATISFIED | CLI verified: TEST ticker shows run metadata + "No changes"; NONEXISTENT shows clear error; --list-runs and --run1/--run2 work |
| QA-05 | 50-02 | User can audit brain health with `do-uw brain audit` -- staleness, coverage imbalance, threshold conflicts, orphaned checks | SATISFIED | CLI verified: 380 never-calibrated, "NOT AVAILABLE" peril coverage, no threshold conflicts, no orphaned signals |
| QA-03 | (Phase 49) | CI tests enforce brain contract | NOT SCOPED | Correctly attributed to Phase 49, not Phase 50 |

### Anti-Patterns Found

| File | Lines | Pattern | Severity | Impact |
|------|-------|---------|----------|--------|
| `src/do_uw/brain/brain_composite_engine.py` | 513 | File exceeds 500-line limit (CLAUDE.md rule) | Warning | Non-blocking; file is well-structured with 4 evaluator functions. No context-rot risk. |
| `src/do_uw/cli_brain_health.py` | 596 | File exceeds 500-line limit (CLAUDE.md rule) | Warning | Non-blocking; houses 3 commands (health, delta, audit). Could be split into 3 files in a future phase. |
| `src/do_uw/brain/brain_delta.py` | multiple | `_placeholder_run = RunInfo(run_id="", run_date="", signal_count=0)` | Info | Intentional design (SUMMARY documents this decision): empty-placeholder RunInfo on error keeps model consistent. Not a stub. |
| `src/do_uw/validation/health_summary.py` | 80, 91, 101 | `return {}` in `_get_signal_results_from_state()` | Info | Legitimate early-exit fallbacks when state.analysis is None or no signal_results key is found. Not stubs. |

### Human Verification Required

#### 1. Live end-to-end health summary with anomaly detection

**Test:** Run `uv run do-uw analyze AAPL` with full data (MCP acquisition) and observe post-pipeline terminal output.
**Expected:** After the QA report, a Rich panel titled "Signal Health Summary" appears with a counts table (Evaluated, TRIGGERED, CLEAR, INFO, SKIPPED) and section breakdown (BIZ, FIN, GOV, etc.). If 0 signals TRIGGERED and `active_cases` is non-empty, a WARNING anomaly fires.
**Why human:** MCP-dependent acquisition required for real state data. Programmatic wiring verified; Rich terminal rendering and real-data anomaly detection require live run.

## Test Results

| Test Suite | Result | Count |
|-----------|--------|-------|
| `tests/brain/test_brain_delta.py` | PASS | 9/9 |
| `tests/brain/test_brain_composites.py` | PASS | 9/9 |
| `tests/brain/` (all) | PASS | 334/334 |
| `uv run do-uw brain health` | PASS | CLI runs cleanly |
| `uv run do-uw brain audit` | PASS | CLI runs cleanly |
| `uv run do-uw brain delta TEST` | PASS | Compares two most recent runs |
| `uv run do-uw brain delta NONEXISTENT` | PASS | Clear error + exit code 1 |
| `uv run do-uw brain delta TEST --list-runs` | PASS | Rich table of 3 runs |
| `evaluate_composites({})` graceful | PASS | 3 results, all CLEAR, no crash |

## Architecture Verification

The three-layer separation declared in the PLAN frontmatter is correctly implemented:

- **Signals** (atomic evaluation): Unchanged. SignalResult gains `details` dict as additive field.
- **Composites** (brain analysis): `brain/composites/*.yaml` + `brain_composite_engine.py`. Pure analysis — no display logic.
- **Facets** (display presentation): `brain/facets/market_activity.yaml` gains `content:` list referencing composites via `ref: COMP.*`. No analysis logic.

## Gaps Summary

No gaps. All 14 must-haves verified, all 4 phase requirements (QA-01, QA-02, QA-04, QA-05) satisfied, all key links wired, all CI tests pass.

Two files slightly exceed the 500-line limit (brain_composite_engine.py at 513 lines, cli_brain_health.py at 596 lines). These are warnings under CLAUDE.md Anti-Context-Rot rules but do not block the phase goal. Both files are structurally clean with no mixed concerns.

---

_Verified: 2026-02-27T04:30:00Z_
_Verifier: Claude (gsd-verifier)_
