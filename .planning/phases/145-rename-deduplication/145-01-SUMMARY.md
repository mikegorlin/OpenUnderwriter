---
phase: 145-rename-deduplication
plan: 01
subsystem: render
tags: [refactor, rename, context-builders, templates, jinja2]

# Dependency graph
requires: []
provides:
  - "Canonical 'uw_analysis' naming for report context builder module"
  - "Zero 'beta_report' references in active codebase (src/tests/scripts)"
affects: [145-02, render, context-builders]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "uw_analysis is the canonical name for the main report context builder"

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/context_builders/uw_analysis.py
    - src/do_uw/stages/render/context_builders/assembly_uw_analysis.py
    - src/do_uw/stages/render/context_builders/_uw_analysis_helpers.py
    - src/do_uw/stages/render/context_builders/_uw_analysis_investigative.py
    - src/do_uw/stages/render/context_builders/_uw_analysis_findings.py
    - src/do_uw/stages/render/context_builders/_uw_analysis_uw_metrics.py
    - src/do_uw/stages/render/context_builders/uw_analysis_sections.py
    - src/do_uw/stages/render/context_builders/uw_analysis_charts.py
    - src/do_uw/stages/render/context_builders/uw_analysis_infographics.py
    - src/do_uw/stages/render/context_builders/assembly_registry.py
    - src/do_uw/templates/html/sections/uw_analysis.html.j2
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/worksheet.html.j2
    - scripts/qa_uw_analysis.py
    - scripts/qa_underwriter.py
    - tests/stages/render/test_stage_banner_template.py
    - tests/stages/render/test_pipeline_status_wiring.py
    - tests/stages/render/test_reading_paths.py
    - tests/brain/test_contract_enforcement.py
    - tests/brain/test_template_facet_audit.py
    - tests/test_canonical_metrics.py
    - src/do_uw/stages/render/context_builders/_stock_chart_mpl.py

key-decisions:
  - "Clean break rename: zero backward compat shims, all references updated atomically"
  - "3 pre-existing test failures (orphaned template checks) unrelated to rename, left as-is"

patterns-established:
  - "uw_analysis: canonical module name for underwriting analysis context builder"

requirements-completed: [NAME-01, NAME-02]

# Metrics
duration: 6min
completed: 2026-03-28
---

# Phase 145 Plan 01: Rename beta_report to uw_analysis Summary

**Complete rename of beta_report to uw_analysis: 11 files git-mv'd, 22 files updated, zero beta_report references remain in src/tests/scripts**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-28T17:59:06Z
- **Completed:** 2026-03-28T18:05:18Z
- **Tasks:** 1
- **Files modified:** 22

## Accomplishments
- Renamed 11 files via git mv (9 Python context builders + 1 Jinja2 template + 1 QA script)
- Updated all internal cross-imports across 9 renamed Python modules
- Updated assembly_registry.py: import path, function names, context dict key, docstrings
- Updated 3 Jinja2 templates: base.html.j2, worksheet.html.j2, uw_analysis.html.j2
- Updated 6 test files: mock patch paths, context key refs, template allowlists
- Verified zero beta_report/beta-report matches in src/, tests/, scripts/
- 297 tests pass (3 pre-existing failures on orphaned template checks, unrelated)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rename files and update all imports/references** - `da227c1c` (refactor)

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/uw_analysis.py` - Main context builder (renamed from beta_report.py)
- `src/do_uw/stages/render/context_builders/assembly_uw_analysis.py` - Assembly module (renamed from assembly_beta_report.py)
- `src/do_uw/stages/render/context_builders/_uw_analysis_helpers.py` - Helper module (renamed)
- `src/do_uw/stages/render/context_builders/_uw_analysis_investigative.py` - Investigative module (renamed)
- `src/do_uw/stages/render/context_builders/_uw_analysis_findings.py` - Findings module (renamed)
- `src/do_uw/stages/render/context_builders/_uw_analysis_uw_metrics.py` - UW metrics module (renamed)
- `src/do_uw/stages/render/context_builders/uw_analysis_sections.py` - Sections module (renamed)
- `src/do_uw/stages/render/context_builders/uw_analysis_charts.py` - Charts module (renamed)
- `src/do_uw/stages/render/context_builders/uw_analysis_infographics.py` - Infographics module (renamed)
- `src/do_uw/stages/render/context_builders/assembly_registry.py` - Updated import, function name, context key
- `src/do_uw/templates/html/sections/uw_analysis.html.j2` - Template renamed, set b = uw_analysis
- `src/do_uw/templates/html/base.html.j2` - if uw_analysis condition
- `src/do_uw/templates/html/worksheet.html.j2` - include uw_analysis.html.j2
- `scripts/qa_uw_analysis.py` - QA script renamed + internal refs updated
- `scripts/qa_underwriter.py` - Comment reference updated
- 6 test files - Patch paths, context keys, template allowlists updated

## Decisions Made
- Clean break rename with zero backward compatibility shims -- all 22 files updated atomically in a single commit
- 3 pre-existing test failures on orphaned template checks left untouched (out of scope for this rename plan)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Fixed additional beta_report references in comments/docstrings**
- **Found during:** Task 1 (post-rename verification)
- **Issue:** Plan specified file renames and import paths but _stock_chart_mpl.py docstring and uw_analysis.py docstring still contained "Beta Report" / "beta-report"
- **Fix:** Updated remaining docstring/comment references in _stock_chart_mpl.py, uw_analysis.py, base.html.j2, test_reading_paths.py
- **Files modified:** 4 additional files beyond plan spec
- **Verification:** grep -r "beta_report\|beta-report" returns 0 matches
- **Committed in:** da227c1c (part of task commit)

---

**Total deviations:** 1 auto-fixed (missing critical -- stale references in comments)
**Impact on plan:** Minor scope expansion to catch all string variants. No architectural changes.

## Issues Encountered
- Stale .pyc cache files for old beta_report modules needed deletion to avoid import confusion
- 3 pre-existing test failures (orphaned template checks) confirmed via git stash verification -- not caused by rename

## Known Stubs
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Codebase exclusively uses "uw_analysis" naming
- Ready for 145-02 deduplication work on clean naming foundation
- 3 pre-existing orphaned template test failures should be addressed in a future plan

---
*Phase: 145-rename-deduplication*
*Completed: 2026-03-28*
