---
phase: 144-pipeline-rendering-resilience
verified: 2026-03-28T17:30:00Z
status: passed
score: 8/8 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 5/8
  gaps_closed:
    - "Pipeline status table wired end-to-end: build_pipeline_status_context called in assembly_registry.py, pipeline_status.html.j2 template created, audit_trail.html.j2 includes it"
    - "Stage failure banners visible in rendered HTML: _stage_banner rendered in financial.html.j2, governance.html.j2, litigation.html.j2, stock_market.html.j2, scoring.html.j2; _propagate_banners_to_beta_report bridges top-level context into beta_report sub-dicts"
    - "Chart placeholder PNG wired: create_chart_placeholder called in render __init__.py for all 11 chart slots when buf is None"
  gaps_remaining: []
  regressions: []
---

# Phase 144: Pipeline Rendering Resilience Verification Report

**Phase Goal:** Underwriter always gets a worksheet -- pipeline completes all stages or fails clearly, rendering handles missing data gracefully, and partial results still produce useful output
**Verified:** 2026-03-28T17:30:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (Plan 03)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Pipeline continues through all 7 stages even when one fails | VERIFIED | pipeline.py: `continue # catch-and-continue` in both validation and execution blocks; 6 tests pass |
| 2 | CLI exits 0 with warnings when HTML produced despite stage failures | VERIFIED | cli.py: `failed_stages` list + exit-1 only when no HTML; 7 tests pass |
| 3 | state.json contains stage status/duration/error for every stage | VERIFIED | models/state.py: all 7 stages initialized PENDING at construction; pipeline records RUNNING/COMPLETED/FAILED with duration |
| 4 | Audit section of worksheet shows pipeline execution status table | VERIFIED | build_pipeline_status_context called at assembly_registry.py:144; pipeline_status.html.j2 renders status badges, duration, errors; audit_trail.html.j2:16 includes it; 4 wiring tests pass |
| 5 | Every chart builder returns None (not crash) when given None/missing data | VERIFIED | @null_safe_chart on all 10 chart modules; 10 null-safety tests pass |
| 6 | Sections affected by failed stages show amber Incomplete banner | VERIFIED | _stage_banner rendered in 5 section templates; _propagate_banners_to_beta_report in assembly_registry.py:165 bridges top-level into beta_report sub-dicts with 2-pass approach; 3 propagation tests pass |
| 7 | Risk card renders Supabase SCA data even when EXTRACT fails | VERIFIED | litigation.py: _hydrate_risk_card reads from state.acquired_data (ACQUIRE stage, independent of EXTRACT); 3 isolation tests pass |
| 8 | Chart placeholder PNG written to disk when a chart builder returns None | VERIFIED | create_chart_placeholder imported at render/__init__.py:333 and called for all 11 chart slots; 3 placeholder wiring tests pass |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/pipeline.py` | Catch-and-continue loop | VERIFIED | 2 `continue # catch-and-continue` lines |
| `src/do_uw/cli.py` | Exit-0-on-HTML logic | VERIFIED | `failed_stages` list + exit-1 only when no HTML |
| `src/do_uw/stages/render/__init__.py` | Pass-through validate_input + placeholder calls | VERIFIED | validate_input body is `pass`; create_chart_placeholder called 9 times (11 chart slots) |
| `src/do_uw/stages/render/context_builders/assembly_registry.py` | Pipeline status wired + banner propagation | VERIFIED | build_pipeline_status_context called at line 144; _propagate_banners_to_beta_report defined at line 165 and called at line 137 |
| `src/do_uw/stages/render/context_builders/pipeline_status.py` | Pipeline status context builder | VERIFIED | Produces correct 7-stage list; now called in production at assembly_registry:144 |
| `src/do_uw/stages/render/context_builders/stage_failure_banners.py` | STAGE_SECTION_MAP + inject_stage_failure_banners | VERIFIED | Correct map; wired in assembly_registry; propagation bridges to beta_report sub-dicts |
| `src/do_uw/stages/render/charts/chart_guards.py` | null_safe_chart + create_chart_placeholder | VERIFIED | Both functions exist; decorator on 10 chart modules; create_chart_placeholder called in production |
| `src/do_uw/templates/html/appendices/pipeline_status.html.j2` | Pipeline status table template | VERIFIED | Created; renders status badges (COMPLETED/FAILED/RUNNING/PENDING), duration, error column |
| `src/do_uw/templates/html/sections/report/audit_trail.html.j2` | Includes pipeline_status template | VERIFIED | Line 16: `{% include "appendices/pipeline_status.html.j2" ignore missing %}` |
| `src/do_uw/templates/html/sections/report/financial.html.j2` | _stage_banner conditional | VERIFIED | Lines 12-16: amber banner div rendered when fn._stage_banner is set |
| `src/do_uw/templates/html/sections/report/governance.html.j2` | _stage_banner conditional | VERIFIED | Lines 12-16: amber banner div rendered when gv._stage_banner is set |
| `src/do_uw/templates/html/sections/report/litigation.html.j2` | _stage_banner conditional | VERIFIED | Lines 17-21: amber banner div rendered when ld._stage_banner is set |
| `src/do_uw/templates/html/sections/report/stock_market.html.j2` | _stage_banner conditional | VERIFIED | Lines 10-14: amber banner div rendered when me._stage_banner is set |
| `src/do_uw/templates/html/sections/report/scoring.html.j2` | _stage_banner conditional | VERIFIED | Lines 16-20: amber banner div rendered when sd._stage_banner is set |
| `tests/test_pipeline_resilience.py` | 6 catch-and-continue tests | VERIFIED | 6 tests pass |
| `tests/test_cli_resilience.py` | 7 CLI exit-code tests | VERIFIED | 7 tests pass |
| `tests/stages/render/test_pipeline_status_context.py` | 3 status context tests | VERIFIED | 3 tests pass (no regression) |
| `tests/stages/render/test_chart_null_safety.py` | 10 null-safety tests | VERIFIED | 10 tests pass (no regression) |
| `tests/stages/render/test_stage_failure_banners.py` | 5 banner injection tests | VERIFIED | 5 tests pass (no regression) |
| `tests/stages/render/test_risk_card_isolation.py` | 3 risk card isolation tests | VERIFIED | 3 tests pass (no regression) |
| `tests/stages/render/test_pipeline_status_wiring.py` | 4 pipeline status wiring tests | VERIFIED | 4 new tests pass (gap closure) |
| `tests/stages/render/test_stage_banner_template.py` | 3 banner propagation tests | VERIFIED | 3 new tests pass (gap closure) |
| `tests/stages/render/test_chart_placeholder_wiring.py` | 3 placeholder wiring tests | VERIFIED | 3 new tests pass (gap closure) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `pipeline.py` | `models/common.py` | `state.mark_stage_failed()` | WIRED | Called at lines 173 and 187 |
| `cli.py` | `pipeline.py` | `state = pipeline.run(state)` | WIRED | Returns state; no PipelineError caught |
| `chart_guards.py` | `stock_charts.py` et al. | `@null_safe_chart` decorator | WIRED | Applied to all 10 chart modules |
| `stage_failure_banners.py` | `assembly_registry.py` | `inject_stage_failure_banners(state, context)` | WIRED | Called; _propagate_banners_to_beta_report follows |
| `stage_failure_banners.py` / `assembly_registry.py` | HTML section templates | `_stage_banner` in beta_report sub-dicts rendered | WIRED | 5 templates read and render _stage_banner |
| `pipeline_status.py` | `assembly_registry.py` | `build_pipeline_status_context(state)` | WIRED | Called at line 144; key "pipeline_status" in context |
| `pipeline_status.html.j2` | `audit_trail.html.j2` | `{% include ... %}` | WIRED | Line 16 of audit_trail.html.j2 |
| `chart_guards.py` | `render/__init__.py` | `create_chart_placeholder()` on None buf | WIRED | 9 call sites covering 11 chart slots |
| `litigation.py` | `state.acquired_data` | `_hydrate_risk_card` reads from acquired_data | WIRED | Line 374 confirmed |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `pipeline_status.html.j2` | `pipeline_status` list | `state.stages` via `build_pipeline_status_context` | Yes — reads live stage results | FLOWING — called in production, renders in audit trail |
| 5 section templates | `_stage_banner` in beta_report sub-dicts | `state.stages[name].status == FAILED` via two-pass propagation | Yes — reads live stage results | FLOWING — propagated into beta_report sub-dicts and rendered |
| `render/__init__.py` chart slots | Placeholder PNG bytes | `create_chart_placeholder()` → matplotlib gray figure | Yes — non-zero bytes, valid PNG | FLOWING — written to disk at chart_dir when buf is None |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Pipeline catches stage failure and continues | `uv run pytest tests/test_pipeline_resilience.py -x -q` | 6 passed | PASS |
| CLI exits 0 with failed stages when HTML exists | `uv run pytest tests/test_cli_resilience.py -x -q` | 7 passed | PASS |
| Pipeline status wired into build_html_context | `uv run pytest tests/stages/render/test_pipeline_status_wiring.py -x -q` | 4 passed | PASS |
| Banner propagation into beta_report sub-dicts | `uv run pytest tests/stages/render/test_stage_banner_template.py -x -q` | 3 passed | PASS |
| Chart placeholder written when builder returns None | `uv run pytest tests/stages/render/test_chart_placeholder_wiring.py -x -q` | 3 passed | PASS |
| All 34 original phase 144 tests unbroken | `uv run pytest tests/test_pipeline_resilience.py tests/test_cli_resilience.py tests/stages/render/test_pipeline_status_context.py tests/stages/render/test_chart_null_safety.py tests/stages/render/test_stage_failure_banners.py tests/stages/render/test_risk_card_isolation.py -x -q` | 34 passed | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| RES-01 | 144-01 | Pipeline completes all 7 stages or logs clear error; state.json includes stage status | SATISFIED | catch-and-continue in pipeline.py; state.stages dict with all 7 stages tracked from construction |
| RES-02 | 144-02 | Every chart builder guards against None — no AttributeError crashes; empty chart renders placeholder | SATISFIED | @null_safe_chart on all 10 chart modules; create_chart_placeholder called for all 11 chart slots in render/__init__.py |
| RES-03 | 144-02, 144-03 | Section templates guard against missing context — show "Incomplete" banner | SATISFIED | Amber banner rendered in 5 section templates; two-pass propagation ensures banners reach beta_report sub-dicts even when top-level context values are None |
| RES-04 | 144-02 | Risk card renders from acquired_data even when extraction incomplete | SATISFIED | _hydrate_risk_card reads from state.acquired_data (ACQUIRE stage, independent of EXTRACT); 3 isolation tests pass |
| RES-05 | 144-01 | CLI always produces HTML output — even on partial completion | SATISFIED | CLI exit-0 when HTML exists confirmed; 7 CLI exit-code tests pass |
| RES-06 | 144-01, 144-03 | Stage status tracked in state.json; visible in worksheet audit section | SATISFIED | models/state.py + pipeline.py track all 7 stages; pipeline_status.html.j2 renders execution table in audit trail |

### Anti-Patterns Found

None — all three previously orphaned implementations are now wired end-to-end. No stubs, no dead code in the gap closure paths.

### Human Verification Required

None — all checks are deterministic and verified programmatically.

### Re-verification Summary

All three gaps from the initial verification are now closed:

**Gap 1 closed: Pipeline status table in audit trail.** `build_pipeline_status_context(state)` is now called in `assembly_registry.py` at line 144 and the result stored under `context["pipeline_status"]`. The new `pipeline_status.html.j2` template renders a formatted table with status badges, duration, and error messages. `audit_trail.html.j2` includes the template at line 16.

**Gap 2 closed: Stage failure banners visible in rendered sections.** The critical architecture problem — `inject_stage_failure_banners()` injected into top-level context keys while report templates read from `beta_report` sub-dicts — is solved by `_propagate_banners_to_beta_report()`. The function uses a two-pass approach: first copying from top-level dict keys, then reading `state.stages` directly for the case where top-level context values are None (common when EXTRACT fails). All 5 section templates (financial, governance, litigation, stock_market, scoring) now render the amber banner when `_stage_banner` is present.

**Gap 3 closed: Chart placeholder written on None return.** `create_chart_placeholder()` is imported and called in `render/__init__.py` at 9 call sites covering all 11 chart slots (stock periods, radar, ownership, timeline, drawdown, volatility, relative performance, drop analysis, drop scatter). When a chart builder returns None, a gray PNG with centered label text is written to disk instead of being silently omitted.

The phase goal — "underwriter always gets a worksheet; rendering handles missing data gracefully" — is now fully achieved. All 8 observable truths verified, all 6 requirements satisfied, 44 tests passing (34 original + 10 new gap closure tests).

---

_Verified: 2026-03-28T17:30:00Z_
_Verifier: Claude (gsd-verifier)_
