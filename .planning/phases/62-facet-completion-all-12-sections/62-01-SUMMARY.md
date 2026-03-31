---
phase: 62-facet-completion-all-12-sections
plan: 01
subsystem: render
tags: [facets, yaml, jinja2, html-templates, section-dispatch]

# Dependency graph
requires:
  - phase: 56-facet-driven-rendering
    provides: FacetSpec schema, section dispatch in section_renderer.py
provides:
  - forward_looking section with 5 facets and HTML templates
  - executive_risk section with 4 facets and HTML templates
  - All 12 brain sections now have facets (zero legacy-only sections)
affects: [62-02, render, html-output]

# Tech tracking
tech-stack:
  added: []
  patterns: [signal_results_by_section filtering in Jinja2 templates for signal-group facets]

key-files:
  created:
    - src/do_uw/templates/html/sections/forward_looking/early_warning.html.j2
    - src/do_uw/templates/html/sections/forward_looking/event_catalysts.html.j2
    - src/do_uw/templates/html/sections/forward_looking/macro_risks.html.j2
    - src/do_uw/templates/html/sections/forward_looking/disclosure_quality.html.j2
    - src/do_uw/templates/html/sections/forward_looking/narrative_coherence.html.j2
    - src/do_uw/templates/html/sections/executive_risk/executive_profiles.html.j2
    - src/do_uw/templates/html/sections/executive_risk/tenure_stability.html.j2
    - src/do_uw/templates/html/sections/executive_risk/insider_trading.html.j2
    - src/do_uw/templates/html/sections/executive_risk/prior_litigation.html.j2
  modified:
    - src/do_uw/brain/sections/forward_looking.yaml
    - src/do_uw/brain/sections/executive_risk.yaml
    - tests/brain/test_section_schema.py
    - tests/stages/render/test_section_renderer.py

key-decisions:
  - "Forward-looking templates filter FWRD.* signals from signal_results_by_section via prefix matching, avoiding need for new context builders"
  - "Executive risk templates combine signal_results_by_section with extract_executive_risk() analysis context for rich profile display"
  - "KV table format for disclosure_quality and narrative_coherence (fewer signals, key-value nature); metric_table for early_warning, event_catalysts, macro_risks (many signals, assessment + evidence columns)"

patterns-established:
  - "Signal-group facet templates: filter signals from signal_results_by_section by prefix, render as metric_table or kv_table"
  - "All 12 brain sections now have facets -- zero legacy-only rendering paths remain"

requirements-completed: [FACET-01, FACET-02, FACET-05]

# Metrics
duration: 7min
completed: 2026-03-03
---

# Phase 62 Plan 01: Forward-Looking + Executive Risk Facets Summary

**Added 5 forward_looking facets and 4 executive_risk facets with 9 HTML templates, enabling section dispatch for all 12 brain sections**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-03T02:55:32Z
- **Completed:** 2026-03-03T03:03:00Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- forward_looking.yaml now has 5 facets grouping 79 FWRD.* signals by prefix (WARN, EVENT, MACRO, DISC, NARRATIVE)
- executive_risk.yaml now has 4 facets grouping 20 EXEC.* signals by prefix (PROFILE, TENURE, INSIDER, PRIOR_LIT)
- 9 new HTML facet templates created with proper data access via signal_results_by_section
- All 12 brain sections now have facets -- zero legacy-only rendering paths remain
- 79 tests pass across test_section_schema.py and test_section_renderer.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Add facets to forward_looking.yaml and executive_risk.yaml** - `32ff005` (test: failing tests RED), `0f1db06` (feat: YAML facets GREEN)
2. **Task 2: Create HTML facet templates** - `559589f` (feat: 9 templates + test updates)

## Files Created/Modified
- `src/do_uw/brain/sections/forward_looking.yaml` - Added 5 facets with template paths and representative signals
- `src/do_uw/brain/sections/executive_risk.yaml` - Added 4 facets with template paths and representative signals
- `src/do_uw/templates/html/sections/forward_looking/early_warning.html.j2` - FWRD.WARN signals metric table
- `src/do_uw/templates/html/sections/forward_looking/event_catalysts.html.j2` - FWRD.EVENT signals metric table
- `src/do_uw/templates/html/sections/forward_looking/macro_risks.html.j2` - FWRD.MACRO signals metric table
- `src/do_uw/templates/html/sections/forward_looking/disclosure_quality.html.j2` - FWRD.DISC signals KV table
- `src/do_uw/templates/html/sections/forward_looking/narrative_coherence.html.j2` - FWRD.NARRATIVE signals KV table
- `src/do_uw/templates/html/sections/executive_risk/executive_profiles.html.j2` - EXEC profile + aggregate risk KV table
- `src/do_uw/templates/html/sections/executive_risk/tenure_stability.html.j2` - EXEC.TENURE + DEPARTURE metric table
- `src/do_uw/templates/html/sections/executive_risk/insider_trading.html.j2` - EXEC.INSIDER metric table with red highlighting
- `src/do_uw/templates/html/sections/executive_risk/prior_litigation.html.j2` - EXEC.PRIOR_LIT metric table
- `tests/brain/test_section_schema.py` - 10 new tests for facet validation
- `tests/stages/render/test_section_renderer.py` - Updated for 12 sections with facets, fixed stale assertions

## Decisions Made
- Forward-looking templates access data via `signal_results_by_section.get('FWRD', [])` with prefix filtering rather than requiring a new context builder -- this reuses the existing signal grouping infrastructure
- Executive risk templates combine signal data with `executive_risk` analysis context (from `extract_executive_risk()`) for richer profile display
- Used `kv_table` macro for disclosure quality and narrative coherence facets (KV nature of data), `metric_table` for others (tabular signal lists)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed stale test assertions in test_section_renderer.py**
- **Found during:** Task 2 (template creation)
- **Issue:** Pre-existing stale assertions: financial_health expected 11 facets (now 12 with peer_matrix), governance expected 9 facets (now 10 with compensation_analysis), scoring expected 18 templates on disk (19 with nlp_dashboard), filing_analysis/red_flags not in _SECTIONS_WITH_FACETS despite having facets
- **Fix:** Updated expected facet lists, counts, and _SECTIONS_WITH_FACETS to reflect actual section state (all 12 sections now have facets)
- **Files modified:** tests/stages/render/test_section_renderer.py
- **Verification:** All 79 tests pass
- **Committed in:** 559589f (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Test assertions were stale from previous phases' additions. No scope creep.

## Issues Encountered
None -- plan executed cleanly after fixing stale test data.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 12 sections now have facets and templates -- ready for 62-02 plan
- Section dispatch path fully operational for all sections
- No legacy-only rendering paths remain

## Self-Check: PASSED

All 13 key files verified on disk. All 3 commit hashes (32ff005, 0f1db06, 559589f) found in git log.

---
*Phase: 62-facet-completion-all-12-sections*
*Completed: 2026-03-03*
