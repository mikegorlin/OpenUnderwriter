---
phase: 27-peril-mapping-bear-case-framework
plan: 07
subsystem: benchmark, render
tags: [mispricing, actuarial, ROL, market-intelligence, pricing-divergence]

# Dependency graph
requires:
  - phase: 27-05
    provides: "Peril map rendering and coverage gaps section in Section 7"
  - phase: 26-05
    provides: "Actuarial pricing builder with layer pricing and indicated ROL"
provides:
  - "check_model_vs_market_mispricing() comparing actuarial model ROL to market median"
  - "model_vs_market_alert field on MarketIntelligence model"
  - "Pricing Divergence Alert rendering in worksheet Section 7"
affects: [render, benchmark, executive-summary]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Model-vs-market comparison follows same pattern as existing check_mispricing()"
    - "Alert rendering aggregates both own-pricing and model-vs-market alerts"

key-files:
  created:
    - tests/stages/benchmark/test_mispricing_detection.py
  modified:
    - src/do_uw/stages/benchmark/market_position.py
    - src/do_uw/models/executive_summary.py
    - src/do_uw/stages/benchmark/__init__.py
    - src/do_uw/stages/render/sections/sect7_peril_map.py

key-decisions:
  - "Model-vs-market check placed in _enrich_actuarial_pricing() where both actuarial result and market intelligence are available"
  - "20% threshold for model-vs-market divergence (vs 15% for own-pricing mispricing)"
  - "Both mispricing alerts rendered together under single Pricing Divergence Alert heading"

patterns-established:
  - "Model-vs-market: actuarial indicated ROL compared to peer median with directional labeling"

# Metrics
duration: 2min
completed: 2026-02-12
---

# Phase 27 Plan 07: Mispricing Detection Summary

**Model-vs-market mispricing detection comparing actuarial indicated ROL to market median with 20% threshold and worksheet rendering**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-12T21:37:34Z
- **Completed:** 2026-02-12T21:39:51Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- check_model_vs_market_mispricing() detects when actuarial model pricing diverges >20% from market median
- Directional alerts: "UNDERPRICED BY MARKET" when model ROL exceeds market, "OVERPRICED BY MARKET" when market exceeds model
- model_vs_market_alert field on MarketIntelligence, wired into BenchmarkStage after actuarial pricing
- Pricing Divergence Alert subsection in Section 7 peril map renders both own-pricing and model-vs-market alerts
- 11 unit tests covering threshold boundaries, guards, CI formatting, directional context

## Task Commits

Each task was committed atomically:

1. **Task 1: Add model-vs-market mispricing detection and wire into BenchmarkStage** - `02a2407` (feat)
2. **Task 2: Render model-vs-market mispricing alert in worksheet Section 7** - `01e9560` (feat)

## Files Created/Modified
- `src/do_uw/stages/benchmark/market_position.py` - Added check_model_vs_market_mispricing() with 20% threshold
- `src/do_uw/models/executive_summary.py` - Added model_vs_market_alert field to MarketIntelligence
- `src/do_uw/stages/benchmark/__init__.py` - Wired model-vs-market check in _enrich_actuarial_pricing()
- `src/do_uw/stages/render/sections/sect7_peril_map.py` - Added Pricing Divergence Alert rendering
- `tests/stages/benchmark/test_mispricing_detection.py` - 11 tests for model-vs-market mispricing detection

## Decisions Made
- Placed model-vs-market check in _enrich_actuarial_pricing() (Option A from plan) since that is where both actuarial result and market intelligence are available
- Used 20% threshold (vs 15% for own-pricing check) since model-to-market comparison is inherently noisier
- Aggregated both mispricing alerts under a single "Pricing Divergence Alert" heading for readability

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added own-pricing mispricing_alert to rendering**
- **Found during:** Task 2
- **Issue:** Plan focused on model_vs_market_alert but existing mispricing_alert was also not rendered anywhere in the worksheet
- **Fix:** Rendered both alerts together under Pricing Divergence Alert heading
- **Files modified:** src/do_uw/stages/render/sections/sect7_peril_map.py
- **Verification:** grep confirms both alerts in rendering code
- **Committed in:** 01e9560 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for completeness -- own-pricing mispricing alert was computed but never rendered.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 27 verification gap #1 (mispricing detection) is now closed
- All 7 plans in Phase 27 complete
- Ready for Phase 28 (user-driven iteration)

## Self-Check: PASSED

All 6 files verified present. Both task commits (02a2407, 01e9560) found in git log.

---
*Phase: 27-peril-mapping-bear-case-framework*
*Completed: 2026-02-12*
