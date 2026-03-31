---
phase: 38-render-completeness-quarterly-data
plan: 01
subsystem: render
tags: [jinja2, markdown, templates, includes, data-flow]

# Dependency graph
requires:
  - phase: 35-display-presentation-clarity
    provides: "Markdown renderer with density indicators and pre-computed narratives"
provides:
  - "Split Markdown template into 8 section include files"
  - "Slim root template orchestrator (64 lines) with macros and includes"
  - "Defensive company name fallback chain with logging"
affects: [38-02, 38-03, 38-04, 38-05, 38-06, 38-07]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Jinja2 {% include %} for template section isolation", "Trim syntax {#- -#} for macro whitespace control"]

key-files:
  created:
    - src/do_uw/templates/markdown/sections/executive.md.j2
    - src/do_uw/templates/markdown/sections/company.md.j2
    - src/do_uw/templates/markdown/sections/financial.md.j2
    - src/do_uw/templates/markdown/sections/market.md.j2
    - src/do_uw/templates/markdown/sections/governance.md.j2
    - src/do_uw/templates/markdown/sections/litigation.md.j2
    - src/do_uw/templates/markdown/sections/scoring.md.j2
    - src/do_uw/templates/markdown/sections/appendix.md.j2
  modified:
    - src/do_uw/templates/markdown/worksheet.md.j2
    - src/do_uw/stages/render/md_renderer.py

key-decisions:
  - "Macros (triggered_block, density_indicator, section_narrative) remain in root template since Jinja2 includes inherit parent scope"
  - "Used {#- -#} trim syntax to eliminate spurious blank lines from macro definitions"
  - "Company name uses 3-tier fallback: legal_name.value -> ticker -> 'Unknown Company' with logging at each level"

patterns-established:
  - "Template section isolation: each section in its own file under sections/ for independent editing"
  - "Root template as orchestrator: macros + includes only, no section content"

requirements-completed: [SC-1, SC-7]

# Metrics
duration: 6min
completed: 2026-02-21
---

# Phase 38 Plan 01: Template Split & Data Flow Fix Summary

**Split 594-line Markdown template into 8 section includes with 64-line root orchestrator, added defensive company name fallback chain with logging**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-21T20:24:33Z
- **Completed:** 2026-02-21T20:30:47Z
- **Tasks:** 1
- **Files modified:** 10

## Accomplishments
- Split monolithic 594-line worksheet.md.j2 into 8 section include files (largest: 94 lines for financial)
- Root template reduced to 64-line orchestrator with macros and Jinja2 {% include %} directives
- Added 3-tier company name fallback chain with warning logs at each degradation level
- Eliminated spurious blank lines from macro definitions using {#- -#} trim syntax
- AAPL state.json round-trip verified: renders "Apple Inc." correctly from deserialized state
- All 6 existing Markdown renderer tests pass with identical behavior

## Task Commits

Each task was committed atomically:

1. **Task 1: Diagnose and fix AAPL data flow bug + split MD template into section includes** - `17f9d61` (feat)

**Plan metadata:** (see below)

## Files Created/Modified
- `src/do_uw/templates/markdown/sections/executive.md.j2` - Section 1: Executive Summary template (59 lines)
- `src/do_uw/templates/markdown/sections/company.md.j2` - Section 2: Company Profile template (55 lines)
- `src/do_uw/templates/markdown/sections/financial.md.j2` - Section 3: Financial Health template (94 lines)
- `src/do_uw/templates/markdown/sections/market.md.j2` - Section 4: Market & Trading template (61 lines)
- `src/do_uw/templates/markdown/sections/governance.md.j2` - Section 5: Governance template (76 lines)
- `src/do_uw/templates/markdown/sections/litigation.md.j2` - Section 6: Litigation template (49 lines)
- `src/do_uw/templates/markdown/sections/scoring.md.j2` - Section 7: Scoring template (67 lines)
- `src/do_uw/templates/markdown/sections/appendix.md.j2` - Section 8 + Coverage Gaps + Appendix template (76 lines)
- `src/do_uw/templates/markdown/worksheet.md.j2` - Root orchestrator with macros + includes (64 lines, was 594)
- `src/do_uw/stages/render/md_renderer.py` - Added defensive company name fallback with logging

## Decisions Made
- **Macros in root template**: Jinja2 macros (`triggered_block`, `density_indicator`, `section_narrative`) remain in root template because included templates inherit the parent template's scope. No separate macro import file needed.
- **Trim syntax for macros**: Used `{#- -#}` comment block syntax to prevent macro definitions from generating blank lines in rendered output. Eliminates 4 spurious blank lines at document start.
- **Company name fallback chain**: Instead of just "Unknown Company", the fallback now tries: (1) legal_name.value, (2) ticker symbol, (3) "Unknown Company" -- with a warning log at each degradation level. This makes debugging data flow issues trivial.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The AAPL "Unknown Company" bug was already fixed by the time this plan executed. Investigation confirmed that `Pipeline.load_state()` correctly deserializes state.json via `model_validate()`, and `build_template_context()` correctly extracts the company name. The existing AAPL_worksheet.md showing "Unknown Company" was an artifact from a previous render run. Added defensive logging to prevent silent degradation in future runs.
- Two pre-existing test failures (PDF/WeasyPrint library loading) are unrelated to this plan and were not fixed (out of scope).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Template split enables independent editing of section templates in subsequent plans (38-02 through 38-07)
- FileSystemLoader path in md_renderer.py already supports nested includes (verified)
- Root template macros are available to all included sections

## Self-Check: PASSED

- All 10 files verified present on disk
- Commit 17f9d61 verified in git history
- All 6 Markdown renderer tests pass
- AAPL state round-trip renders "Apple Inc." correctly

---
*Phase: 38-render-completeness-quarterly-data*
*Completed: 2026-02-21*
