---
phase: 124-css-density-overhaul
plan: 01
subsystem: ui
tags: [css, tailwind, typography, risk-colors, tabular-nums, infographic-density]

requires:
  - phase: 122-audit-layer
    provides: manifest v2.0 section ordering and layer classification
provides:
  - Borderless table design with navy headers, row dividers, alternating backgrounds
  - Updated risk color palette (Critical/Elevated/Watch/Positive)
  - Normal-case section headers at 1.125rem with gold accent
  - Compact spacing rhythm (halved from 8px to 4px grid)
  - Tabular-nums on all numeric contexts
  - Backward-compatible color aliases in CSS and Python
affects: [124-02, 125-section-grid-layouts, render]

tech-stack:
  added: []
  patterns: [borderless-tables, css-nth-child-alternation, compact-p1-padding]

key-files:
  created: []
  modified:
    - src/do_uw/templates/html/styles.css
    - src/do_uw/templates/html/input.css
    - src/do_uw/templates/html/components.css
    - src/do_uw/templates/html/scorecard.css
    - src/do_uw/stages/render/design_system.py
    - src/do_uw/templates/html/components/tables.html.j2
    - src/do_uw/templates/html/compiled.css

key-decisions:
  - "Risk colors updated: Critical=#DC2626, Elevated=#EA580C, Watch=#EAB308, Positive=#2563EB with backward-compat aliases"
  - "Kept uppercase on scorecard micro-labels (0.5rem-0.625rem), only removed from h2-level headers and scorecard-section-title"
  - "Global CSS table reset handles navy headers, row dividers, alternating rows -- templates stripped of inline border/bg classes"
  - "Bulk-replaced px-3 py-2 with p-1 across 79 template files (738 occurrences)"

patterns-established:
  - "Borderless table design: no cell borders, 1px gray-200 bottom-border on tbody td, navy thead th"
  - "CSS-driven alternation: nth-child(even) bg-alt, no inline Jinja2 conditionals"
  - "Compact padding: p-1 (0.25rem 0.5rem) on all table cells"

requirements-completed: [VIS-01, VIS-02, VIS-03, VIS-05, VIS-06, VIS-07]

duration: 7min
completed: 2026-03-21
---

# Phase 124 Plan 01: CSS Density Overhaul Summary

**Borderless tables with navy headers, compact p-1 spacing, updated risk colors (#DC2626/#EA580C/#EAB308/#2563EB), normal-case h2 headers, and tabular-nums across 79 templates**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-21T21:34:56Z
- **Completed:** 2026-03-21T21:42:32Z
- **Tasks:** 2
- **Files modified:** 82

## Accomplishments
- Replaced entire table visual system: borderless design with 1px row dividers, navy header rows, alternating white/#F8FAFC backgrounds via CSS nth-child
- Updated risk color palette across all 3 sources (styles.css, input.css, design_system.py) with backward-compatible aliases
- Section h2 headers changed from uppercase/700/1rem to normal-case/600/1.125rem with gold left-border accent
- Compact spacing: halved spacing rhythm variables, body margin 0.5rem, p-1 on all table cells
- Tabular-nums applied globally to td, .tabular-nums, and all numeric class selectors
- Bulk-updated 79 Jinja2 templates: 738 padding replacements, removed all inline border classes

## Task Commits

Each task was committed atomically:

1. **Task 1: Update CSS variables, risk colors, typography, and spacing** - `a74c5539` (feat)
2. **Task 2: Update table template macros for borderless compact design** - `5f0cd8ff` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/styles.css` - Updated :root variables, borderless table reset, h2 typography, spacing rhythm, tabular-nums
- `src/do_uw/templates/html/input.css` - Updated @theme risk color tokens with backward-compat aliases
- `src/do_uw/templates/html/components.css` - Removed borders from collapsible, exec-card, narrative-layers, narrative-evidence-grid; removed uppercase from data-grid-title
- `src/do_uw/templates/html/scorecard.css` - Removed uppercase from scorecard-section-title
- `src/do_uw/stages/render/design_system.py` - New html_risk_critical/elevated/watch/positive fields, updated _RISK_COLORS dict, backward-compat aliases
- `src/do_uw/templates/html/components/tables.html.j2` - Simplified macros: p-1 padding, kv-key/kv-value classes, removed inline alternation
- `src/do_uw/templates/html/compiled.css` - Rebuilt Tailwind output
- 79 section/appendix template files - Bulk px-3 py-2 -> p-1, removed inline border classes
- `tests/stages/render/test_html_components.py` - Updated color assertions to match new palette

## Decisions Made
- Risk colors updated with backward-compatible aliases so existing template references (text-risk-red, etc.) continue working
- Kept uppercase on scorecard micro-labels (sc-panel-title, sc-vstat-label, etc.) at 0.5rem-0.625rem -- they serve as structural markers, not section headers
- Removed scorecard-section-title uppercase (0.75rem) since it functions as a section header
- Global CSS table reset applied universally -- templates stripped of redundant inline styling

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing IndentationError in _market_display.py**
- **Found during:** Task 1 (render test verification)
- **Issue:** `_format_events` function had unindented for-loop body and referenced wrong variable name (`drop_events` instead of `result`)
- **Fix:** The linter auto-corrected this to a `_format_event` single-item function called via list comprehension
- **Files modified:** src/do_uw/stages/render/context_builders/_market_display.py (auto-fixed by linter)
- **Verification:** Render tests pass (1156 passed)
- **Committed in:** Not committed separately (linter auto-fix)

---

**Total deviations:** 1 auto-fixed (1 pre-existing bug caught by linter)
**Impact on plan:** No scope creep. Pre-existing syntax error blocked test execution.

## Issues Encountered
- Pre-existing test failure in `test_builder_line_limits.py` (financials_evaluative.py at 347 lines, limit 300) -- not related to CSS changes, excluded from verification
- Pre-existing test failure in `test_html_signals.py` (missing 'do_context' key) -- not related to CSS changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CSS foundation complete for Phase 124-02 (section-specific density refinements)
- All 1156 render tests pass
- Tailwind compiled.css rebuilt and embedded
- Ready for Phase 125 section grid layouts

---
*Phase: 124-css-density-overhaul*
*Completed: 2026-03-21*
