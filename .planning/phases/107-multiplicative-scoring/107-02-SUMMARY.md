---
phase: 107-multiplicative-scoring
plan: 02
subsystem: scoring
tags: [legacy-lens, shadow-calibration, pipeline-integration, calibration-report, hae-model, scoring-comparison]

# Dependency graph
requires:
  - phase: 107-multiplicative-scoring-01
    provides: "ScoringLens Protocol, HAEScoringLens, CRFVetoResult, evaluate_crf_discordance, HAETier"
  - phase: 106-model-research
    provides: "decision_framework.yaml tier definitions"
provides:
  - "LegacyScoringLens -- legacy 10-factor wrapped as ScoringLens producing ScoringLensResult"
  - "ScoreStage pipeline integration -- both H/A/E and legacy lenses run on every SCORE execution"
  - "Shadow calibration runner with 36 curated tickers across 10+ sectors"
  - "Interactive HTML calibration report with UW assessment inputs and JSON export"
  - "calibrate_from_pipeline() extracts real comparison data from completed pipeline runs"
  - "Graceful degradation -- H/A/E failure does not break existing scoring pipeline"
affects: [108-severity-patterns, 110-score-integration, 112-worksheet-restructure]

# Tech tracking
tech-stack:
  added: []
  patterns: [legacy-lens-adapter, dual-lens-pipeline, shadow-calibration, interactive-html-report]

key-files:
  created:
    - src/do_uw/stages/score/legacy_lens.py
    - src/do_uw/stages/score/shadow_calibration.py
    - src/do_uw/stages/score/_calibration_report.py
    - tests/stages/score/test_shadow_calibration.py
    - output/calibration_report.html
  modified:
    - src/do_uw/stages/score/__init__.py

key-decisions:
  - "Legacy lens is post-hoc adapter (takes ScoringResult in constructor) rather than matching ScoringLens Protocol exactly -- documented as intentional divergence"
  - "Shadow calibration stub mode generates synthetic data for report structure testing; real calibration requires full pipeline per ticker (20+ min each)"
  - "HTML report generation split into _calibration_report.py to manage file sizes"
  - "36 calibration tickers curated across 10+ sectors with 4 categories: known_good, known_bad, edge_cases, recent_actuals"

patterns-established:
  - "Dual-lens pipeline: ScoreStage runs both H/A/E and legacy, stores both results, H/A/E drives worksheet"
  - "Graceful degradation: H/A/E failure logged as warning, legacy scoring continues unaffected"
  - "Interactive HTML calibration: self-contained single-file reports with inline CSS/JS for UW feedback collection"

requirements-completed: [SCORE-05]

# Metrics
duration: ~20min
completed: 2026-03-15
---

# Phase 107 Plan 02: Legacy Lens + Shadow Calibration Summary

**Legacy 10-factor scoring wrapped as ScoringLens adapter, dual-lens pipeline integration in ScoreStage, and interactive shadow calibration report with 36 tickers for UW tier validation**

## Performance

- **Duration:** ~20 min (across checkpoint pause)
- **Started:** 2026-03-15T23:34:02Z
- **Completed:** 2026-03-15T23:49:00Z
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files modified:** 6

## Accomplishments
- LegacyScoringLens wraps existing 10-factor scoring output as ScoringLensResult with legacy tier mapped to HAETier (WIN->PREFERRED, WANT/WRITE->STANDARD, WATCH->ELEVATED, WALK->HIGH_RISK, NO_TOUCH->PROHIBITED)
- ScoreStage.run() now executes both H/A/E and legacy lenses -- H/A/E drives the worksheet, legacy is comparison only
- CRF discordance applied after H/A/E lens evaluation, with graceful degradation if H/A/E fails
- Shadow calibration runner with 36 curated tickers across tech, healthcare, financials, industrials, consumer, energy, materials, REIT, and utilities
- Interactive HTML report with sortable table, UW assessment dropdowns, follow-up rationale inputs, category filter tabs, and JSON export button
- calibrate_from_pipeline() extracts real comparison data from completed AnalysisState for live calibration
- 205 score stage tests passing (33 new for this plan + 172 existing)

## Task Commits

Each task was committed atomically (TDD: RED -> GREEN for Task 1):

1. **Task 1: Legacy lens adapter + pipeline integration** - `aeb88fd` (test), `6206ad2` (feat)
2. **Task 2: Shadow calibration runner + interactive HTML report** - `f413662` (feat)
3. **Task 3: Verify complete scoring system and calibration report** - checkpoint:human-verify (approved)

## Files Created/Modified
- `src/do_uw/stages/score/legacy_lens.py` (162 lines) - LegacyScoringLens adapter wrapping 10-factor output as ScoringLensResult
- `src/do_uw/stages/score/shadow_calibration.py` (592 lines) - Calibration runner with 36 curated tickers, CalibrationRow/Metrics models, stub and live calibration modes
- `src/do_uw/stages/score/_calibration_report.py` (357 lines) - HTML report generation extracted to stay under file size limits
- `src/do_uw/stages/score/__init__.py` (526 lines, modified) - H/A/E lens + CRF discordance integrated as Step 7.5 after legacy tier classification
- `tests/stages/score/test_shadow_calibration.py` (33 tests) - Legacy lens mapping, calibration ticker diversity, metrics computation, HTML structure, pipeline integration
- `output/calibration_report.html` - Generated interactive calibration report for UW review

## Decisions Made
- **Legacy lens as post-hoc adapter:** LegacyScoringLens takes ScoringResult in its constructor rather than matching the ScoringLens Protocol signature (which expects signal_results). This is intentional -- legacy scoring is already computed by the existing pipeline, the lens just wraps the result. Documented as adapter pattern.
- **Stub vs live calibration:** run_shadow_calibration() generates synthetic data for report structure testing. Full pipeline runs take 20+ minutes per ticker and require MCP tools. calibrate_from_pipeline() provides the real-data path for individual completed pipeline runs.
- **shadow_calibration.py at 592 lines:** Exceeds the 500-line soft limit. HTML generation was already split to _calibration_report.py (357 lines). The remaining 592 lines contain 36 ticker definitions + CalibrationRow/Metrics models + runner + pipeline extractor. Further splitting would fragment naturally cohesive calibration logic. Flagged for review but not blocking.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both scoring lenses (H/A/E and legacy) run in the pipeline -- ready for Phase 110 full score integration
- Calibration report infrastructure ready for real ticker runs as pipeline matures
- CRF discordance integrated and tested -- ready for severity model (Phase 108) to layer P x S computation
- shadow_calibration.py at 592 lines should be reviewed during Phase 110 integration for potential further split

## Self-Check: PASSED

All 5 created files exist. All 3 task commits verified in git log (aeb88fd, 6206ad2, f413662).

---
*Phase: 107-multiplicative-scoring*
*Completed: 2026-03-15*
