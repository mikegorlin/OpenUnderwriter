---
phase: 136-forward-looking-and-integration
plan: 01
subsystem: render
tags: [context-builders, forward-looking, scenarios, calendar, credibility, short-sellers]

requires:
  - phase: 131-scoring-visualization
    provides: scenario_generator.py with generate_scenarios()
  - phase: 117-forward-looking
    provides: CredibilityScore model and credibility_context.py

provides:
  - build_forward_scenarios() enhanced scenarios with probability/severity/catalyst
  - build_forward_calendar() key dates with urgency color coding
  - build_forward_credibility() pattern classification for management guidance
  - build_short_seller_alerts() named firm detection in web search results
  - derive_short_conviction() Rising/Stable/Declining from short interest trend

affects: [136-02-templates, beta-report-wiring]

tech-stack:
  added: []
  patterns: [context-builder-pattern, tdd-red-green, safe_float-everywhere]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/_forward_scenarios.py
    - src/do_uw/stages/render/context_builders/_forward_calendar.py
    - src/do_uw/stages/render/context_builders/_forward_credibility.py
    - src/do_uw/stages/render/context_builders/_forward_short_sellers.py
    - tests/render/test_forward_scenarios.py
    - tests/render/test_forward_calendar.py
    - tests/render/test_forward_credibility.py
    - tests/render/test_forward_short_sellers.py
  modified: []

key-decisions:
  - "Probability normalization maps VERY_HIGH->HIGH, ELEVATED->MEDIUM, MODERATE->MEDIUM to keep 3-level badges"
  - "Severity estimates use market cap percentile: HIGH=2%, MEDIUM=1%, LOW=0.5% of market cap"
  - "Credibility pattern evaluation order: Insufficient Data, Deteriorating, Unreliable, Sandbagging, Consistent Beater, Mixed"
  - "Short-seller detection requires firm name AND company ticker/name AND report keyword co-occurrence to prevent false positives"

patterns-established:
  - "Forward-looking builders follow Phase 134/135 pattern: pure data formatters returning template-ready dicts"
  - "Urgency color classification: within 30d=#DC2626, 30-90d=#D97706, >90d=#9CA3AF"

requirements-completed: [FWD-01, FWD-02, FWD-03, FWD-04, FWD-05]

duration: 5min
completed: 2026-03-27
---

# Phase 136 Plan 01: Forward-Looking Context Builders Summary

**Four context builders producing template-ready dicts for enhanced scenarios with probability/severity/catalyst, key dates calendar with urgency color coding, credibility pattern classification, and short-seller monitoring with conviction labels**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-27T12:54:53Z
- **Completed:** 2026-03-27T12:59:40Z
- **Tasks:** 2
- **Files created:** 8

## Accomplishments
- Forward scenarios builder enhances existing generate_scenarios() with probability badges (HIGH/MEDIUM/LOW), severity dollar estimates from market cap, and company-specific catalyst descriptions
- Key dates calendar collects from yfinance calendar, governance annual meeting, and IPO milestones with 30/90-day urgency color classification
- Credibility builder classifies management guidance patterns into 5 categories (Consistent Beater, Sandbagging, Unreliable, Deteriorating, Insufficient Data) with quarter-by-quarter table
- Short-seller monitoring scans web search results for 5 named firms with false-positive protection and derives conviction direction from short interest trend data
- 42 tests covering all output structures, edge cases, and classification thresholds

## Task Commits

Each task was committed atomically:

1. **Task 1: Forward scenarios builder + key dates calendar** - `ee968673` (feat)
2. **Task 2: Credibility patterns + short-seller monitoring** - `fd0f2ac9` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/_forward_scenarios.py` - Enhanced scenario builder with probability, severity, catalyst
- `src/do_uw/stages/render/context_builders/_forward_calendar.py` - Key dates calendar with urgency classification
- `src/do_uw/stages/render/context_builders/_forward_credibility.py` - Credibility pattern classification (5 patterns)
- `src/do_uw/stages/render/context_builders/_forward_short_sellers.py` - Short-seller report detection + conviction labels
- `tests/render/test_forward_scenarios.py` - 11 tests for scenario builder
- `tests/render/test_forward_calendar.py` - 10 tests for calendar builder
- `tests/render/test_forward_credibility.py` - 9 tests for credibility patterns
- `tests/render/test_forward_short_sellers.py` - 12 tests for short-seller monitoring

## Decisions Made
- Probability normalization: VERY_HIGH and CRITICAL map to HIGH; ELEVATED and MODERATE map to MEDIUM. Keeps 3-level badge system clean.
- Severity from market cap: HIGH=2% ($mcap*0.02), MEDIUM=1%, LOW=0.5% -- based on NERA settlement percentile data.
- Credibility evaluation order guards insufficient data first, then checks most-specific patterns before general ones.
- Short-seller detection requires triple co-occurrence (firm name + company name/ticker + report keyword) to prevent Hindenburg-the-disaster false positives.
- build_earnings_trust() function referenced in plan does not exist in codebase; credibility builder uses state.forward_looking.credibility directly instead.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] build_earnings_trust() not found in codebase**
- **Found during:** Task 2 (credibility patterns)
- **Issue:** Plan referenced `build_earnings_trust(state)` from `_market_acquired_data.py` but this function does not exist
- **Fix:** Used `state.forward_looking.credibility` directly (CredibilityScore model), which already contains beat_rate_pct, quarter_records, and all needed data
- **Files modified:** `_forward_credibility.py`
- **Verification:** All 9 credibility tests pass

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minimal -- the alternative data path provides equivalent functionality.

## Issues Encountered
None beyond the deviation noted above.

## Known Stubs
None -- all builders produce real data from existing state paths.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All four context builders ready for template consumption in 136-02
- Each returns `*_available: bool` flag for template conditional rendering
- Pattern follows established Phase 134/135 convention

---
*Phase: 136-forward-looking-and-integration*
*Completed: 2026-03-27*
