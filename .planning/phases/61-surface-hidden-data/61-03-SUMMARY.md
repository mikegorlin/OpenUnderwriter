---
phase: 61-surface-hidden-data
plan: 03
subsystem: render
tags: [jinja2, html, css, governance, scoring, hazard, forensic, source-attribution]

requires:
  - phase: 61-01
    provides: "Compensation analysis facet and source attribution patterns"
  - phase: 61-02
    provides: "NLP dashboard, hazard category cards, confidence dot CSS"
provides:
  - "Executive shade factor detail cards with source attribution"
  - "Board forensic profiles with independence concerns, relationship flags, interlocks"
  - "Full allegation theory detail with D&O claim types and factor sources"
  - "Hazard interaction display with named/dynamic distinction and multiplier badges"
affects: [65-narrative-depth, 66-final-qa]

tech-stack:
  added: []
  patterns:
    - "_governance_helpers.py extraction pattern for keeping context builders under 500 lines"
    - "Expandable forensic detail cards with confidence dots and source tooltips"
    - "Allegation bar visual overview with expandable theory cards"

key-files:
  created:
    - "src/do_uw/stages/render/context_builders/_governance_helpers.py"
  modified:
    - "src/do_uw/stages/render/context_builders/governance.py"
    - "src/do_uw/stages/render/context_builders/scoring.py"
    - "src/do_uw/stages/render/context_builders/analysis.py"
    - "src/do_uw/templates/html/sections/governance/people_risk.html.j2"
    - "src/do_uw/templates/html/sections/governance/board_forensics.html.j2"
    - "src/do_uw/templates/html/sections/scoring/allegation_mapping.html.j2"
    - "src/do_uw/templates/html/sections/scoring/hazard_profile.html.j2"
    - "src/do_uw/templates/html/components.css"

key-decisions:
  - "Extracted _governance_helpers.py to keep governance.py under 500 lines (same pattern as _nlp_helpers.py)"
  - "Kept backward-compat alias _build_compensation_analysis in governance.py for existing test imports"
  - "Named interactions displayed prominently with amber styling; dynamic in collapsible section"

patterns-established:
  - "Forensic detail: expandable cards per executive/director with source attribution via confidence dots"
  - "Allegation mapping: exposure summary bar + expandable theory cards with D&O claim type tags"

requirements-completed: [SURF-04, SURF-06, SURF-07, SURF-08]

duration: 16min
completed: 2026-03-03
---

# Phase 61 Plan 03: Surface Hidden Data Summary

**Executive shade factors, allegation D&O coverage mapping, and hazard interaction amplification detail surfaced with full source attribution**

## Performance

- **Duration:** 16 min
- **Started:** 2026-03-03T04:08:14Z
- **Completed:** 2026-03-03T04:24:41Z
- **Tasks:** 6
- **Files modified:** 9

## Accomplishments
- Executive profiles show shade_factors with individual detail cards, departure context, prior enforcement/restatements, and forensic flag counts
- Board forensic profiles show independence concerns, relationship flags, interlocks, and qualification tags per director with source attribution
- Allegation mapping shows full theory detail with D&O claim types (10b-5, Section 11, Caremark, etc.), all evidence findings, and factor source traceability
- Hazard interactions distinguish named patterns (prominent amber cards with multiplier badges) from dynamic detections (collapsible), with triggered dimension cross-references and combined interaction multiplier

## Task Commits

1. **Task 1: Enhance governance context with full shade factor detail** - `36e5360` (feat)
2. **Task 2: Enhance people_risk and board_forensics templates** - `cb20e81` (feat)
3. **Task 3: Enhance allegation mapping with full theory detail** - `ea64048` (feat)
4. **Task 4: Enhance hazard interaction display** - `93e1ebf` (feat)
5. **Task 5: Add CSS for new components** - `ead19bd` (feat)
6. **Task 6: Backward-compat fix for test imports** - `a9d2436` (fix)

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/_governance_helpers.py` - Compensation analysis builder + shared SourcedValue utilities (145 lines)
- `src/do_uw/stages/render/context_builders/governance.py` - Enhanced exec/board extraction with forensic detail (436 lines)
- `src/do_uw/stages/render/context_builders/scoring.py` - Theory names, claim types, full findings extraction (442 lines)
- `src/do_uw/stages/render/context_builders/analysis.py` - Named/dynamic interaction separation, interaction_multiplier (496 lines)
- `src/do_uw/templates/html/sections/governance/people_risk.html.j2` - Exec cards with forensic detail
- `src/do_uw/templates/html/sections/governance/board_forensics.html.j2` - Director detail with independence/flags
- `src/do_uw/templates/html/sections/scoring/allegation_mapping.html.j2` - Exposure bar + theory cards with D&O coverage
- `src/do_uw/templates/html/sections/scoring/hazard_profile.html.j2` - Named/dynamic interaction display
- `src/do_uw/templates/html/components.css` - CSS for exec-card, allegation-bar, interaction-card (441 lines)

## Decisions Made
- Extracted `_governance_helpers.py` to keep governance.py under 500 lines (matches `_nlp_helpers.py` pattern from 61-02)
- Added backward-compat alias `_build_compensation_analysis` in governance.py for existing test imports
- Named interactions displayed prominently with amber backgrounds and multiplier badges; dynamic interactions in collapsible section
- Compacted CSS section comments from multi-line banners to single-line to keep components.css under 500 lines

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed broken test import after function extraction**
- **Found during:** Task 6 (test verification)
- **Issue:** `tests/stages/render/test_compensation_peer_matrix.py` imports `_build_compensation_analysis` from governance.py, but it was moved to `_governance_helpers.py`
- **Fix:** Added backward-compat alias in governance.py: `_build_compensation_analysis = build_compensation_analysis`
- **Files modified:** `src/do_uw/stages/render/context_builders/governance.py`
- **Verification:** All 393 render tests pass
- **Committed in:** `a9d2436`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Single backward-compat alias, no scope creep.

## Issues Encountered
- Pre-existing test failures in `tests/brain/test_brain_framework.py` and `tests/brain/test_brain_enrich.py` (unrelated to this plan)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 61 (Surface Hidden Data) is now COMPLETE (all 3 plans done)
- All 8 SURF requirements verified: SURF-01 through SURF-08
- Ready for Wave 3/4 phases (63, 64, 65, 66)

---
*Phase: 61-surface-hidden-data*
*Completed: 2026-03-03*
