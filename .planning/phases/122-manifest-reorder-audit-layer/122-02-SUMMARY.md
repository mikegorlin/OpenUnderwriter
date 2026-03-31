---
phase: 122-manifest-reorder-audit-layer
plan: 02
subsystem: rendering
tags: [jinja2, html-template, layer-rendering, audit-collapse, section-merge]

requires:
  - phase: 122-manifest-reorder-audit-layer
    provides: ManifestSection.layer field and narrative-ordered manifest v2.0
provides:
  - Layer-aware worksheet template (decision/analysis/audit zones)
  - Audit layer collapsed in <details> element
  - Merged company_operations template with dossier sub-templates
  - Layer rendering test suite (10 tests)
affects: [123-market-condensation, 124-css-density, 125-section-templates]

tech-stack:
  added: []
  patterns: [3-zone manifest rendering (decision/analysis/audit), audit collapse via HTML details element]

key-files:
  created:
    - tests/stages/render/test_layer_rendering.py
  modified:
    - src/do_uw/templates/html/worksheet.html.j2
    - src/do_uw/templates/html/sections/company.html.j2
    - tests/stages/render/test_html_layout.py

key-decisions:
  - "Zone 0-1 remain hardcoded (Key Stats, Scorecard, Brief, CRF, Trigger Matrix) -- these are decision layer but have dedicated templates"
  - "Zone 2 filters decision-layer manifest sections (catches Red Flags not hardcoded above)"
  - "Zone 3 renders analysis-layer sections in manifest order (the story)"
  - "Zone 4 wraps ALL audit sections in a single <details> collapse with system appendices"
  - "Section reorder confirmed in AAPL HTML output -- visual impact minimal until CSS/Market phases execute"

patterns-established:
  - "Layer-aware template rendering: filter manifest_sections by section.layer in Jinja2 for loop"
  - "Audit collapse pattern: single <details class='audit-layer'> wrapping all audit content"

requirements-completed: [STRUCT-01, STRUCT-04]

duration: 70min
completed: 2026-03-21
---

# Phase 122 Plan 02: Layer-Aware Template Rendering Summary

**Worksheet template renders 3-layer document structure (decision at top, analysis in story order, audit collapsed) with merged Company & Operations section including dossier content**

## Performance

- **Duration:** 70 min (includes fresh AAPL pipeline run for visual verification)
- **Started:** 2026-03-21T20:14:49Z
- **Completed:** 2026-03-21T21:24:49Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 4

## Accomplishments
- Rewrote worksheet.html.j2 from 3-zone to 5-zone structure with layer-aware manifest filtering
- Audit layer sections wrapped in collapsed `<details>` element -- not visible until user expands
- Company template merged to include 9 dossier sub-templates (what_company_does, money_flows, revenue_model_card, revenue_segments, unit_economics, revenue_waterfall, competitive_landscape, emerging_risk_radar, asc_606)
- Fresh AAPL pipeline confirmed correct section order: Decision -> Analysis (story flow) -> Audit (collapsed)
- 10 new layer rendering tests covering layer assignments, story order, dossier merge, deleted sections

## Task Commits

1. **Task 1: Layer-aware worksheet template with audit collapse** - `ad6caea4` (feat)
2. **Task 2: Merge company template + layer rendering tests** - `34ac4e30` (feat)
3. **Task 2b: Fix html layout tests for new section order** - `6f3d6aa7` (fix)

## Files Created/Modified
- `src/do_uw/templates/html/worksheet.html.j2` - 5-zone layer-aware rendering with audit collapse
- `src/do_uw/templates/html/sections/company.html.j2` - Merged company + dossier, renamed to "Company & Operations"
- `tests/stages/render/test_layer_rendering.py` - 10 tests for layer rendering structure
- `tests/stages/render/test_html_layout.py` - Updated section order, IDs, and collapsible section lists

## Decisions Made
- Zone 0-1 (Key Stats, Scorecard, Brief, CRF, Trigger Matrix) remain hardcoded at top -- they ARE the decision layer but have dedicated templates with fixed positions
- Red Flags caught by Zone 2 decision-layer manifest filter rather than hardcoding
- Single `<details>` element wraps all audit content (manifest audit sections + system appendices like signal_audit and render_audit)
- company-profile section ID renamed to company-operations for consistency with manifest

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated test_html_layout.py for new section order and IDs**
- **Found during:** Task 2 (post-commit test verification)
- **Issue:** 3 tests in test_html_layout.py failed: test_section_order expected old order (market before governance), test_collapsible_sections_present/open_by_default referenced deleted ai-risk section
- **Fix:** Updated section order to narrative flow (governance before market), removed ai-risk from collapsible lists, added company-operations, renamed company-profile to company-operations
- **Files modified:** tests/stages/render/test_html_layout.py
- **Verification:** All 16 html_layout tests pass
- **Committed in:** 6f3d6aa7

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Test update necessary for manifest v2.0 structure. No scope creep.

## Issues Encountered
- Word renderer warns that `company_operations` and `forward_looking` are not in `_SECTION_RENDERER_MAP` -- pre-existing gap, not caused by this plan. Word output still generates but may be missing these sections.
- Playwright PDF generation failed (Chromium not installed) -- fell back to WeasyPrint successfully. Pre-existing environment issue.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Layer-aware rendering is live -- Decision layer at top, Analysis in story order, Audit collapsed
- User confirmed: "Section reorder confirmed in HTML output. Visual impact minimal until CSS/Market phases execute."
- Phase 123 (market condensation) can proceed -- market section rendering is in place
- Phase 124 (CSS density) will have maximum visual impact on the new structure

---
*Phase: 122-manifest-reorder-audit-layer*
*Completed: 2026-03-21*

## Self-Check: PASSED
All 3 files verified on disk, all 3 commits verified in git log.
