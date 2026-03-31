---
phase: 114-worksheet-restructure
plan: 02
subsystem: render
tags: [jinja2, templates, scorecard, heatmap, executive-brief, crf-banner, hae-badges, css-grid]

requires:
  - phase: 114-worksheet-restructure
    provides: 5 context builders (scorecard, heatmap, crf_bar, epistemological_trace, decision)
provides:
  - 7 new Jinja2 templates (3 sections, 4 components) for scorecard-first worksheet layout
  - Restructured worksheet.html.j2 with 3 structural zones
  - Audience-oriented sidebar TOC (Overview, Analysis, Appendix)
  - scorecard.css with all component styling
  - 17 integration tests for template rendering
affects: [114-03-styling]

tech-stack:
  added: []
  patterns: [CSS Grid 60/40 scorecard layout, macro-based reusable components, structural zone includes before manifest loop]

key-files:
  created:
    - src/do_uw/templates/html/sections/scorecard.html.j2
    - src/do_uw/templates/html/sections/executive_brief.html.j2
    - src/do_uw/templates/html/sections/crf_banner.html.j2
    - src/do_uw/templates/html/components/heatmap.html.j2
    - src/do_uw/templates/html/components/hae_badge.html.j2
    - src/do_uw/templates/html/components/signal_drilldown.html.j2
    - src/do_uw/templates/html/components/confidence_badge.html.j2
    - src/do_uw/templates/html/scorecard.css
    - tests/stages/render/test_scorecard.py
    - tests/stages/render/test_executive_brief.py
    - tests/stages/render/test_hae_badges.py
  modified:
    - src/do_uw/templates/html/worksheet.html.j2
    - src/do_uw/templates/html/base.html.j2

key-decisions:
  - "Created scorecard.css as separate file to keep styles.css under 500-line limit (was at 954 lines)"
  - "Used ignore missing on placeholder includes (decision_record, epistemological_trace) for Plan 03 forward compatibility"
  - "PDF details expansion now excludes signal-drilldown class to keep drill-downs collapsed in print"

patterns-established:
  - "Structural zone pattern: includes before manifest_sections loop for fixed-position content"
  - "Audience-oriented sidebar: Overview/Analysis/Appendix groups with conditional links"
  - "Component macro pattern: hae_badge, confidence, signal_drill as importable macros"

requirements-completed: [WS-01, WS-02, WS-05, WS-08]

duration: 7min
completed: 2026-03-17
---

# Phase 114 Plan 02: Scorecard Templates and Worksheet Restructure Summary

**7 new Jinja2 templates (scorecard, executive brief, CRF banner, heatmap, H/A/E badges, signal drilldown, confidence badges) with CSS Grid layout and worksheet restructured into 3 structural zones**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-17T14:39:34Z
- **Completed:** 2026-03-17T14:46:30Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Created scorecard page template with CSS Grid 60/40 layout: factor bar charts, tier badge with Moody's-style coloring, H/A/E radar integration, key metrics strip, signal heatmap, top 8 concerns
- Created self-contained executive brief with enriched findings, confidence badges, and graceful fallbacks
- Restructured worksheet.html.j2 into 3 zones: scorecard/brief/CRF before manifest sections, appendix placeholders after
- 17 new integration tests covering template rendering, graceful degradation, and component macros; 844 total render tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Templates + components** - `ede02ac1` (feat)
2. **Task 2: Worksheet restructure + sidebar + CSS + tests** - `5500019b` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/sections/scorecard.html.j2` - Page 1 risk scorecard with CSS Grid layout (129 lines)
- `src/do_uw/templates/html/sections/executive_brief.html.j2` - Page 2 standalone executive brief (119 lines)
- `src/do_uw/templates/html/sections/crf_banner.html.j2` - CRF alert bar with linked severity pills (29 lines)
- `src/do_uw/templates/html/components/heatmap.html.j2` - Signal heatmap grid grouped by H/A/E (37 lines)
- `src/do_uw/templates/html/components/hae_badge.html.j2` - H/A/E dimension badge macro (16 lines)
- `src/do_uw/templates/html/components/signal_drilldown.html.j2` - Expandable signal provenance details (23 lines)
- `src/do_uw/templates/html/components/confidence_badge.html.j2` - HIGH/MEDIUM/LOW confidence micro-badges (14 lines)
- `src/do_uw/templates/html/scorecard.css` - All scorecard component styling with print rules (490 lines)
- `src/do_uw/templates/html/worksheet.html.j2` - Restructured with 3 structural zones
- `src/do_uw/templates/html/base.html.j2` - Audience-oriented sidebar TOC + hae_badge import + scorecard.css include
- `tests/stages/render/test_scorecard.py` - 5 tests for scorecard rendering
- `tests/stages/render/test_executive_brief.py` - 6 tests for executive brief
- `tests/stages/render/test_hae_badges.py` - 6 tests for H/A/E badge macros

## Decisions Made
- Created `scorecard.css` as a separate CSS file (490 lines) rather than appending to `styles.css` (already at 954 lines) to comply with the 500-line anti-context-rot rule
- Used `ignore missing` on placeholder template includes (decision_record.html.j2, epistemological_trace.html.j2) so worksheet renders cleanly before Plan 03 creates those templates
- PDF details expansion script modified to `details:not(.signal-drilldown)` so signal drill-down panels stay collapsed in PDF output (epistemological trace appendix serves the print provenance purpose)
- Sidebar TOC restructured into 3 audience groups (Overview, Analysis, Appendix) with CRF Alerts link conditionally shown only when alerts exist

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Template parse verification initially failed because `format_na` is a custom Jinja2 filter registered at runtime -- resolved by using filter stub in the verification script

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 7 component templates and scorecard.css are wired into worksheet.html.j2 and ready for production rendering
- Plan 03 (epistemological trace template + decision record template) can proceed -- placeholder includes already in worksheet.html.j2
- Context builders from Plan 01 feed directly into these templates via `context["scorecard"]`, `context["heatmap"]`, `context["crf_bar"]`

---
*Phase: 114-worksheet-restructure*
*Completed: 2026-03-17*
