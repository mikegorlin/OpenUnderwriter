---
phase: 108-severity-model
plan: 02
subsystem: scoring
tags: [severity, pxs-matrix, chart, context-builder, calibration, cli, matplotlib, log-normal]

# Dependency graph
requires:
  - phase: 108-01
    provides: "Severity models, damages estimation, settlement regression, amplifiers, layer erosion, ScoreStage Step 15.5"
  - phase: 107-multiplicative-scoring
    provides: "ScoringLensResult with product_score (P) for P x S computation"
  - phase: 105-chart-library
    provides: "chart_styles.yaml, chart_registry.yaml, resolve_colors pattern"
provides:
  - "SeverityScoringLens: full orchestrator implementing SeverityLens Protocol"
  - "compute_p_x_s(P, S) and classify_zone(P, S) module-level functions"
  - "build_severity_result() combining primary + legacy lenses with HAE probability"
  - "P x S matrix chart with log-scale severity, 4 zone backgrounds, scenario dots + range bar"
  - "Severity context builder for worksheet template rendering"
  - "20-case calibration report comparing model to landmark settlements"
  - "CLI --attachment and --product parameters for Liberty layer quoting"
  - "pxs_matrix chart registered in chart_registry.yaml and chart_styles.yaml"
affects: [109, 110, 111, 112, 113]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SeverityScoringLens: standalone lens using company proxy instead of state for flexibility"
    - "Calibration data extracted to severity_calibration.py (anti-context-rot 500-line split)"
    - "Context builder provides dual data layers: main section (fired only) + appendix (all 11)"
    - "P x S chart uses matplotlib Rectangle patches for zone backgrounds on log-scale"

key-files:
  created:
    - src/do_uw/stages/score/severity_scoring.py
    - src/do_uw/stages/score/severity_calibration.py
    - src/do_uw/stages/render/charts/pxs_matrix_chart.py
    - src/do_uw/stages/render/context_builders/severity_context.py
    - tests/stages/score/test_pxs_computation.py
    - tests/stages/render/test_pxs_chart.py
  modified:
    - src/do_uw/stages/score/__init__.py
    - src/do_uw/cli.py
    - src/do_uw/pipeline.py
    - src/do_uw/brain/config/chart_registry.yaml
    - src/do_uw/brain/config/chart_styles.yaml
    - tests/test_chart_registry.py

key-decisions:
  - "SeverityScoringLens uses company proxy (not AnalysisState) for max flexibility in standalone quoting"
  - "Calibration report uses max(damages-based, regression-based) without amplifiers -- no signal data for historical cases"
  - "Chart zone backgrounds drawn as discrete Rectangle patches rather than contourf for precision on zone boundaries"
  - "Severity context provides dual data layers: amplifiers_fired (main section answers) + amplifiers_full (appendix show-your-work)"
  - "ScoreStage accepts liberty_attachment/product via constructor, passed from Pipeline config -> CLI"

patterns-established:
  - "SeverityScoringLens Protocol compliance: evaluate(signal_results, company, attachment, product, hae_result)"
  - "Module-level P x S helpers for direct import: compute_p_x_s(), classify_zone()"
  - "Context builder graceful degradation: severity_available=False when no data"
  - "Calibration data as module-level constants with _estimate_for_case() for per-case evaluation"

requirements-completed: [SEV-04, SEV-05]

# Metrics
duration: 30min
completed: 2026-03-16
---

# Phase 108 Plan 02: Severity Orchestrator + P x S Chart + CLI Summary

**SeverityScoringLens full pipeline, P x S risk matrix chart with 4-zone log-scale visualization, severity context builder, 20-case calibration report, and --attachment/--product CLI parameters**

## Performance

- **Duration:** 30 min
- **Started:** 2026-03-16T01:15:40Z
- **Completed:** 2026-03-16T01:45:42Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- SeverityScoringLens orchestrates full severity pipeline: allegation inference -> damages -> regression -> amplifiers -> defense costs -> layer erosion -> P x S zone classification
- P x S matrix chart renders with log-scale severity axis ($100K-$10B), 4 colored zone backgrounds (GREEN/YELLOW/ORANGE/RED), primary dot + scenario range bar, optional Liberty attachment line
- Severity context builder provides all template data for worksheet section + appendix with dual amplifier views
- 20 landmark settlement calibration report (Enron $7.2B through Activision $35M) with log-scale error metrics
- CLI --attachment and --product parameters pass through Pipeline -> ScoreStage for quoting accounts not in database
- 26 new severity-specific tests + 35 existing severity tests + 14 chart registry tests, zero regressions

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: SeverityScoringLens + P x S computation + CLI + calibration**
   - `3353bfa` (test: failing tests for P x S computation and severity scoring lens)
   - `46b8e59` (feat: SeverityScoringLens orchestrator, P x S computation, CLI --attachment, calibration)

2. **Task 2: P x S matrix chart + severity context builder + chart registry**
   - `3bdb611` (test: failing tests for P x S chart and severity context builder)
   - `4c6592f` (feat: P x S matrix chart, severity context builder, chart registry)

## Files Created/Modified

- `src/do_uw/stages/score/severity_scoring.py` - SeverityScoringLens implementing SeverityLens Protocol, compute_p_x_s, classify_zone, build_severity_result (432 lines)
- `src/do_uw/stages/score/severity_calibration.py` - 20 known settlements + generate_severity_calibration_report() HTML output (280 lines)
- `src/do_uw/stages/render/charts/pxs_matrix_chart.py` - P x S matrix chart with matplotlib: 4 zone backgrounds, primary dot, range bar, annotations (371 lines)
- `src/do_uw/stages/render/context_builders/severity_context.py` - build_severity_context() providing all template data for severity section (181 lines)
- `src/do_uw/stages/score/__init__.py` - ScoreStage constructor with liberty_attachment/product, passed to run_severity_model
- `src/do_uw/cli.py` - Added --attachment and --product parameters to analyze command
- `src/do_uw/pipeline.py` - Passes liberty_attachment/product from config to ScoreStage constructor
- `src/do_uw/brain/config/chart_registry.yaml` - Added pxs_matrix entry (section: risk_summary, position: 1)
- `src/do_uw/brain/config/chart_styles.yaml` - Added pxs_matrix theme with zone colors and styling
- `tests/stages/score/test_pxs_computation.py` - 16 tests: P x S, zones, lens evaluation, calibration report (294 lines)
- `tests/stages/render/test_pxs_chart.py` - 10 tests: chart rendering, context builder, amplifier split (314 lines)
- `tests/test_chart_registry.py` - Updated counts for 16 chart entries (was 15)

## Decisions Made

- **SeverityScoringLens uses company proxy**: Accepts `company` parameter rather than full AnalysisState, allowing standalone quoting for accounts not yet in the pipeline
- **Calibration without amplifiers**: Historical settlement cases lack signal data, so calibration uses max(damages, regression) without amplifier multiplication -- amplifiers tested separately in unit tests
- **Zone backgrounds as Rectangle patches**: More precise zone boundary rendering on log-scale than matplotlib contourf, and matches the discrete nature of the zone criteria
- **Dual amplifier views in context**: Main section shows "answers" (fired only), appendix shows "show your work" (all 11 with status) -- follows worksheet-as-decision-record philosophy
- **Pipeline threading via constructor**: liberty_attachment and liberty_product flow CLI -> pipeline_config -> ScoreStage constructor -> run_severity_model, avoiding state model changes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] severity_scoring.py exceeded 500-line limit**
- **Found during:** Task 1 (SeverityScoringLens implementation)
- **Issue:** severity_scoring.py reached 682 lines with calibration data and report generation included
- **Fix:** Extracted calibration data and report to severity_calibration.py (280 lines), re-exported from severity_scoring.py for backward compatibility
- **Files modified:** src/do_uw/stages/score/severity_scoring.py, src/do_uw/stages/score/severity_calibration.py
- **Verification:** severity_scoring.py now 432 lines, severity_calibration.py 280 lines, all tests pass

**2. [Rule 1 - Bug] Chart registry test expected 15 entries, now 16**
- **Found during:** Task 2 (full test suite verification)
- **Issue:** test_chart_registry.py hardcoded `len(entries) == 15` and `len(entries) == 15` for format filtering
- **Fix:** Updated test counts to 16 to reflect new pxs_matrix chart entry
- **Files modified:** tests/test_chart_registry.py
- **Verification:** All 14 chart registry tests pass

---

**Total deviations:** 2 auto-fixed (1 Rule 3 blocking, 1 Rule 1 bug)
**Impact on plan:** Both fixes necessary for correctness and anti-context-rot compliance. No scope creep.

## Issues Encountered

None beyond the auto-fixed deviations.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- SeverityResult fully populated on state.scoring.severity_result with P, S, EL, zone, scenarios, amplifiers, erosion
- P x S chart available as base64 PNG via build_severity_context() for worksheet rendering
- CLI --attachment and --product parameters ready for standalone quoting
- Calibration report validates model against 20 known settlements
- Phase 109 (Pattern Engines) can proceed independently
- Phase 110 (Worksheet Integration) will consume severity context builder output
- All existing scoring infrastructure preserved with zero regressions

---
*Phase: 108-severity-model*
*Completed: 2026-03-16*
