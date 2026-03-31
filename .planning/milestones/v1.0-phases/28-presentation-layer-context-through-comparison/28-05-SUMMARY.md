---
phase: 28-presentation-layer-context-through-comparison
plan: 05
subsystem: render
tags: [meeting-prep, bear-case, peril-map, tier-helpers, four-tier-display, underwriter-education, docx]

# Dependency graph
requires:
  - phase: 28-03
    provides: "_is_financial_health_clean(), _is_market_clean() density gating for NOT-clean path"
  - phase: 28-04
    provides: "_is_governance_clean(), _is_litigation_clean() density gating; sect5_governance_board.py; sect6_defense.py"
provides:
  - "Bear case, peril map, and mispricing meeting prep question generators (SC5)"
  - "Four-tier visual helpers: render_objective_signal, render_scenario_context, add_meeting_prep_ref, render_customary_block (SC3)"
  - "Level 2 scenario context with industry claim rates on elevated signals (SC4)"
  - "Meeting prep cross-references in Sections 3-6 pointing to relevant questions (SC4 Level 3)"
  - "Enhanced credibility tests with specific Beneish M-Score/Altman Z-Score values"
  - "meeting_questions_analysis.py for analysis-driven question generators"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Four-tier rendering: customary (DOBody), objective (shaded callout), relative (DOCaption scenario), subjective (accent-color meeting ref)"
    - "Analysis-to-question pipeline: PerilMap deserialize -> filter by probability band -> generate typed MeetingQuestion"
    - "Tier helper replacement: existing inline D&O context blocks replaced with render_objective_signal + render_scenario_context calls"

key-files:
  created:
    - src/do_uw/stages/render/tier_helpers.py
    - src/do_uw/stages/render/sections/meeting_questions_analysis.py
  modified:
    - src/do_uw/stages/render/sections/meeting_questions.py
    - src/do_uw/stages/render/sections/meeting_questions_gap.py
    - src/do_uw/stages/render/sections/meeting_prep.py
    - src/do_uw/stages/render/sections/sect3_financial.py
    - src/do_uw/stages/render/sections/sect4_market.py
    - src/do_uw/stages/render/sections/sect5_governance.py
    - src/do_uw/stages/render/sections/sect6_litigation.py

key-decisions:
  - "Extracted bear case/peril map/mispricing generators to meeting_questions_analysis.py (not meeting_questions.py which would exceed 500 lines)"
  - "Used descriptive meeting prep refs (e.g., 'See Meeting Prep: Earnings Quality') not Q numbers to avoid cross-module numbering dependency"
  - "Replaced existing inline D&O context blocks with tier helper calls rather than adding alongside (avoids line count bloat)"
  - "Peril map deserialization uses same pattern as sect7_peril_map.py (PerilMap.model_validate from state.analysis.peril_map dict)"

patterns-established:
  - "render_objective_signal() for any elevated finding: shaded background + bold risk tag + evidence"
  - "render_scenario_context() for educational context: DOCaption style, indented, italic, with industry claim rates"
  - "add_meeting_prep_ref() for question cross-refs: accent-color italic pointing to topic area"
  - "generate_bear_case_questions() filters on MODERATE/HIGH probability_band, generates FORWARD_INDICATOR category"
  - "generate_peril_map_questions() filters on ELEVATED/HIGH, generates CREDIBILITY_TEST category"

# Metrics
duration: 9min
completed: 2026-02-13
---

# Phase 28 Plan 05: Meeting Prep + Four-Tier Display + Underwriter Education Summary

**Bear case/peril map meeting prep generators, four-tier visual helpers with scenario context on elevated signals, and meeting prep cross-references in Sections 3-6**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-13T13:45:08Z
- **Completed:** 2026-02-13T13:54:38Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Meeting prep now generates questions from 7 sources (was 4): clarification, forward indicator, gap filler, credibility test, bear case, peril map, mispricing
- Bear case scenarios generate FORWARD_INDICATOR questions with committee summary and probability/severity context
- Peril map plaintiff assessments with ELEVATED+ probability generate CREDIBILITY_TEST questions referencing specific findings
- Credibility tests now include specific forensic model values (Beneish M-Score of -1.42, Altman Z-Score in grey zone, insider cluster patterns)
- Four-tier visual distinction: customary (DOBody), objective (shaded callout), relative (caption scenario context), subjective (accent meeting ref)
- Elevated signals in Sections 3-6 show highlighted objective signals with industry claim rate scenario context
- Meeting prep cross-references in sections point to relevant question topics (Financial Distress, Earnings Quality, Short Interest, Governance Structure, Active Litigation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire bear cases, peril map, mispricing to meeting prep** - `43d0073` (feat)
2. **Task 2: Four-tier visual helpers + underwriter education + cross-refs** - `0278a43` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/sections/meeting_questions_analysis.py` - New file: bear case, peril map, mispricing question generators (238 lines)
- `src/do_uw/stages/render/tier_helpers.py` - New file: four-tier rendering helpers (170 lines)
- `src/do_uw/stages/render/sections/meeting_questions.py` - Updated docstring, removed unused imports (401 lines)
- `src/do_uw/stages/render/sections/meeting_questions_gap.py` - Enhanced credibility tests with forensic model specifics (448 lines)
- `src/do_uw/stages/render/sections/meeting_prep.py` - Wired 7 question generators (was 4) (304 lines)
- `src/do_uw/stages/render/sections/sect3_financial.py` - Distress zone/manipulation objective signals + scenario context (498 lines)
- `src/do_uw/stages/render/sections/sect4_market.py` - Short interest and earnings miss signals + scenario context (496 lines)
- `src/do_uw/stages/render/sections/sect5_governance.py` - CEO/Chair duality and overboarding signals (448 lines)
- `src/do_uw/stages/render/sections/sect6_litigation.py` - Active SCA objective signal + PSLRA scenario context (475 lines)

## Decisions Made
- Created meeting_questions_analysis.py rather than adding to meeting_questions.py (would have exceeded 500 lines at 615)
- Used descriptive meeting prep references ("See Meeting Prep: Earnings Quality") instead of Q numbers to avoid cross-module numbering dependency
- Replaced existing inline D&O context blocks with tier helper calls (net-neutral or fewer lines) rather than adding alongside
- Peril map deserialized from state.analysis.peril_map (not state.scored.peril_map as plan suggested -- plan had wrong path)
- Market intelligence accessed from state.executive_summary.deal_context.market_intelligence (not state.benchmarked as plan suggested)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Extracted meeting_questions_analysis.py for 500-line compliance**
- **Found during:** Task 1 (adding bear case/peril map/mispricing generators)
- **Issue:** meeting_questions.py hit 615 lines after adding all new generators
- **Fix:** Extracted bear case, peril map, and mispricing generators to new meeting_questions_analysis.py (238 lines), reducing meeting_questions.py to 401 lines
- **Files modified:** meeting_questions.py, meeting_questions_analysis.py, meeting_prep.py
- **Verification:** All 2928 tests pass, all files under 500 lines
- **Committed in:** 43d0073

**2. [Rule 1 - Bug] Corrected peril map and market intelligence access paths**
- **Found during:** Task 1 (wiring generators)
- **Issue:** Plan referenced state.scored.peril_map and state.benchmarked.market_intelligence which don't exist on AnalysisState
- **Fix:** Used state.analysis.peril_map (dict requiring PerilMap deserialization) and state.executive_summary.deal_context.market_intelligence (correct paths)
- **Files modified:** meeting_questions_analysis.py
- **Verification:** Import succeeds, generators handle None paths gracefully
- **Committed in:** 43d0073

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** 500-line split was mechanical. Path corrections were necessary for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 6 Phase 28 success criteria addressed across plans 01-05:
  - SC1 (context through comparison): Plans 02-04 added peer percentile context to all sections
  - SC2 (issue-driven density): Plans 03-04 added clean/problematic density gating
  - SC3 (four-tier display): Plan 05 added visual distinction helpers
  - SC4 (underwriter education): Plan 05 added Level 2 scenario context on elevated signals
  - SC5 (meeting prep from analysis): Plan 05 wired bear cases and peril map to meeting questions
  - SC6 (all sections enriched): Plans 01-05 touched all 7 main sections
- Phase 28 complete. Ready for Phase 29 or user-driven iteration.
- All 2928 tests pass with 0 regressions

## Self-Check: PASSED

- All 9 files exist on disk (2 created, 7 modified)
- Both commit hashes (43d0073, 0278a43) found in git log
- All files under 500 lines (max: 498 in sect3_financial.py)
- tier_helpers.py at 170 lines (min_lines: 60 requirement met)
- tier_helpers.py exports render_objective_signal, render_scenario_context, add_meeting_prep_ref (all 3 required exports present)
- 2928 tests pass

---
*Phase: 28-presentation-layer-context-through-comparison*
*Completed: 2026-02-13*
