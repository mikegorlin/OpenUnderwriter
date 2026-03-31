---
phase: 43-html-presentation-quality-capiq-layout-data-tracing
plan: "05"
subsystem: testing
tags: [html, layout, pytest, capiq, jinja2, footnote-registry, sidebar, two-column]

requires:
  - phase: 43-01
    provides: two-column CapIQ layout shell, worksheet-layout + sidebar-toc CSS classes
  - phase: 43-02
    provides: red-flags dedicated section, section order reorg
  - phase: 43-03
    provides: 3-column data grid (dr-label/dr-value/dr-context), market anchor rename
  - phase: 43-04
    provides: FootnoteRegistry, sources appendix, footnote deduplication

provides:
  - "10 automated layout structure tests covering all Phase 43 HTML requirements"
  - "Regression shield for Plans 01-04 layout changes"
  - "AAPL HTML worksheet rendered and human-approved as institutionally credible"

affects: [future HTML rendering changes, Phase 43 QA gate, render regression suite]

tech-stack:
  added: []
  patterns:
    - "Test extracts topbar nav element specifically to avoid false positives from CSS class names in <style> blocks"
    - "_render_html_string helper renders HTML to string without disk I/O for fast unit tests"
    - "FootnoteRegistry tested as a standalone unit (no HTML rendering required)"

key-files:
  created:
    - tests/stages/render/test_html_layout.py
  modified: []

key-decisions:
  - "test_topbar_identity_only extracts the <nav class='sticky-topbar'> element rather than checking the full HTML string, because CSS class definitions in <style> tags would cause false positives"
  - "Test 8 (sources appendix) requires AcquiredData.filing_documents to be populated so FootnoteRegistry creates at least one entry — empty state produces no sources section"

patterns-established:
  - "Use html.find('<section id=...') + positional ordering to verify section order without parsing HTML"
  - "Import AcquiredData from do_uw.models.state (not do_uw.models.acquired)"

requirements-completed:
  - VIS-05
  - OUT-04
  - OUT-03

duration: 6min
completed: "2026-02-25"
---

# Phase 43 Plan 05: Layout Test Suite + AAPL Render Summary

**10 automated HTML layout tests validating Phase 43's two-column CapIQ layout, section order, sidebar TOC, red flags section, footnote registry, and sources appendix — all passing, plus AAPL worksheet rendered for human checkpoint review.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-24T01:04:40Z
- **Completed:** 2026-02-24T01:08:22Z
- **Tasks:** 2 complete (Task 1 + Task 2 human-verify checkpoint approved)
- **Files modified:** 1

## Accomplishments

- Created `tests/stages/render/test_html_layout.py` with 10 tests covering all Phase 43 layout requirements
- All 10 new tests pass; full render suite at 227/227 (no regressions)
- AAPL HTML worksheet generated at `output/AAPL/AAPL-2026-02-24/AAPL_worksheet.html` (2.7 MB) for human visual review

## Task Commits

1. **Task 1: Create test_html_layout.py** - `4079fd1` (test)
2. **Task 2: Human visual review of AAPL HTML worksheet** - approved 2026-02-25 (checkpoint:human-verify)

## Files Created/Modified

- `tests/stages/render/test_html_layout.py` — 10 automated layout structure tests:
  - `test_two_column_layout` — worksheet-layout + sidebar-toc classes present
  - `test_sidebar_toc_links` — all 9 section anchor hrefs in sidebar
  - `test_topbar_identity_only` — topbar nav contains company class, not tier/metric classes
  - `test_section_order` — 8 main sections in correct document order
  - `test_red_flags_section_standalone` — red-flags appears before scoring
  - `test_red_flags_empty_state` — renders with "No triggered" text when empty
  - `test_footnote_registry_deduplication` — FootnoteRegistry deduplication + numbering
  - `test_sources_appendix_renders` — sources section + fn- anchors with filing docs
  - `test_sidebar_print_css` — @media print hides sidebar-toc in sidebar.css
  - `test_data_row_macro_in_render` — dr-label/dr-value/dr-context in rendered HTML

## Decisions Made

- Checked topbar element specifically (not full HTML) to avoid false positives from CSS class name definitions in `<style>` blocks. CSS defines `sticky-topbar-tier` and `sticky-topbar-metric` as class names for legacy completeness, but the `<nav>` element itself must not instantiate them.
- `AcquiredData` is imported from `do_uw.models.state` (not a separate `models.acquired` module).
- Test 8 populates `filing_documents` to ensure the sources appendix renders — the Jinja2 template wraps the section in `{% if all_sources %}`, so an empty FootnoteRegistry produces no sources section.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_topbar_identity_only CSS false positive**
- **Found during:** Task 1 (initial test run)
- **Issue:** `assert "sticky-topbar-tier" not in html` failed because the CSS `<style>` block in the rendered HTML defines those class names, even though the topbar element does not use them
- **Fix:** Changed test to extract the `<nav class="sticky-topbar">` element substring and check within that — CSS class definitions in `<style>` tags are excluded
- **Files modified:** tests/stages/render/test_html_layout.py
- **Verification:** Test passes with the narrowed scope
- **Committed in:** 4079fd1 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed wrong module import for AcquiredData**
- **Found during:** Task 1 (test_sources_appendix_renders run)
- **Issue:** Test imported `from do_uw.models.acquired import AcquiredData` but that module does not exist — `AcquiredData` is defined in `do_uw.models.state`
- **Fix:** Changed import to `from do_uw.models.state import AcquiredData`
- **Files modified:** tests/stages/render/test_html_layout.py
- **Verification:** Test passes with correct import
- **Committed in:** 4079fd1 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs caught during initial test run)
**Impact on plan:** Both fixes were discovered and resolved during the same task iteration. No scope creep.

## Issues Encountered

None beyond the two auto-fixed bugs above.

## Checkpoint Outcome

Task 2 was a `checkpoint:human-verify` gate. The AAPL HTML worksheet was reviewed at:

```
output/AAPL/AAPL-2026-02-24/AAPL_worksheet.html
```

**Human reviewer response: "approved"** — AAPL HTML worksheet meets institutional quality standards.

## Next Phase Readiness

- All 10 layout tests are a permanent regression shield for Phase 43 changes
- Human checkpoint approved — Phase 43 is complete
- Phase 43 closes with all 5 plans complete

---
*Phase: 43-html-presentation-quality-capiq-layout-data-tracing*
*Completed: 2026-02-24*
