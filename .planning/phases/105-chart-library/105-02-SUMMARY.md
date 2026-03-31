---
phase: 105-chart-library
plan: 02
subsystem: render
tags: [matplotlib, pillow, numpy, visual-regression, golden-reference, chart-testing]

requires:
  - phase: 105-chart-library
    provides: chart_styles.yaml, chart_style_registry.py, resolve_colors pattern, all 9 renderers refactored
provides:
  - 14 golden reference images (11 PNG + 3 SVG) for all chart type families
  - generate_golden_charts.py deterministic regeneration script
  - test_chart_visual_consistency.py with 17 tests (pixel RMSE + SVG match + canary + registry completeness)
  - golden_reference field on ChartEntry dataclass linking registry to golden PNGs
affects: [render-pipeline, chart-styling-changes, ci-visual-regression]

tech-stack:
  added: []
  patterns: [golden-reference-gallery, pixel-rmse-visual-regression, deterministic-synthetic-data]

key-files:
  created:
    - tests/golden_charts/generate_golden_charts.py
    - tests/golden_charts/README.md
    - tests/golden_charts/stock_1y.png
    - tests/golden_charts/stock_5y.png
    - tests/golden_charts/drawdown_1y.png
    - tests/golden_charts/drawdown_5y.png
    - tests/golden_charts/volatility_1y.png
    - tests/golden_charts/volatility_5y.png
    - tests/golden_charts/radar.png
    - tests/golden_charts/ownership.png
    - tests/golden_charts/drop_analysis_1y.png
    - tests/golden_charts/relative_1y.png
    - tests/golden_charts/timeline.png
    - tests/golden_charts/sparkline_up.svg
    - tests/golden_charts/sparkline_down.svg
    - tests/golden_charts/sparkline_flat.svg
    - tests/stages/render/test_chart_visual_consistency.py
  modified:
    - src/do_uw/stages/render/chart_registry.py
    - src/do_uw/brain/config/chart_registry.yaml

key-decisions:
  - "Golden references generated from deterministic synthetic data (seed=42, fixed dates) -- no external API calls"
  - "Visual comparison uses RMSE on 0-100 scale with 5% default threshold for cross-platform tolerance"
  - "Sparklines tested via SVG string equality (not pixel diff) since they are SVG output"
  - "golden_reference field added to ChartEntry dataclass -- optional, None for charts without golden refs"

patterns-established:
  - "Golden reference pattern: deterministic synthetic data + pixel RMSE comparison for visual regression"
  - "SKIP_VISUAL_TESTS=1 env var to disable visual tests in CI without display"

requirements-completed: [CHART-03, CHART-04]

duration: 6min
completed: 2026-03-15
---

# Phase 105 Plan 02: Golden Reference Gallery + Visual Consistency Tests Summary

**14 golden reference images from deterministic synthetic data with 17-test visual consistency suite using pixel RMSE comparison**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-15T04:56:00Z
- **Completed:** 2026-03-15T05:02:04Z
- **Tasks:** 2
- **Files modified:** 20

## Accomplishments
- Generated 14 golden reference images (11 PNG at 200 DPI + 3 SVG sparklines) from deterministic synthetic data
- Created generate_golden_charts.py with fixed seed (42) and fixed dates for reproducible output across runs
- Built 17-test visual consistency suite: 11 per-chart PNG pixel RMSE tests, 3 SVG exact-match tests, canary corruption detection test, registry completeness test, graceful skip test
- Added golden_reference field to ChartEntry dataclass with paths in chart_registry.yaml
- All 208 chart tests pass (existing + new), visual tests complete in under 2 seconds

## Task Commits

1. **Task 1: Golden reference generation script + gallery** - `f9db444` (feat)
2. **Task 2: Visual consistency test suite** - `df05506` (test, TDD)

## Files Created/Modified
- `tests/golden_charts/generate_golden_charts.py` - Deterministic golden chart generation from synthetic data
- `tests/golden_charts/README.md` - Gallery documentation for all chart types
- `tests/golden_charts/*.png` - 11 golden reference PNG images (stock, drawdown, volatility, radar, ownership, drop_analysis, relative, timeline)
- `tests/golden_charts/*.svg` - 3 sparkline SVG golden references (up, down, flat)
- `tests/stages/render/test_chart_visual_consistency.py` - 17 visual consistency tests with pixel RMSE
- `src/do_uw/stages/render/chart_registry.py` - Added golden_reference field to ChartEntry
- `src/do_uw/brain/config/chart_registry.yaml` - golden_reference paths on 11 chart entries

## Decisions Made
- Golden references use deterministic synthetic data (seed=42, fixed dates) rather than real tickers for reproducibility
- RMSE threshold set at 5% (0-100 scale) to account for anti-aliasing and font rendering differences across platforms
- Sparklines tested via SVG string equality since they produce SVG output (not PNG)
- golden_reference field on ChartEntry is optional (None) -- only set for charts with generated golden PNGs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 105 (Chart Library) COMPLETE -- both plans shipped
- Chart style registry + golden reference gallery ready for downstream phases
- Visual regression test catches unintended styling changes automatically
- Any chart_styles.yaml change requires regenerating golden refs with `uv run python tests/golden_charts/generate_golden_charts.py`

## Self-Check: PASSED

All 18 files verified present. Both commits (f9db444, df05506) verified in git log.

---
*Phase: 105-chart-library*
*Completed: 2026-03-15*
