---
phase: 45-codebase-cleanup-architecture-hardening
plan: "04"
subsystem: render
tags: [density, section-densities, render, cleanup, deprecated-fields]

# Dependency graph
requires:
  - phase: 45-01
    provides: BackwardCompatLoader renamed to BrainKnowledgeLoader in render files
  - phase: 45-02
    provides: brain_loader.py hardened
  - phase: 45-03
    provides: render sections clean after rename wave

provides:
  - "Render sections (sect3, sect4, sect5, sect6) read exclusively from section_densities"
  - "Deprecated boolean fields governance_clean, market_clean, financial_clean, litigation_clean removed from AnalysisResults"
  - "_is_market_clean(), _is_governance_clean(), _is_litigation_clean() deleted from render"
  - "_read_density_clean() helper added to sect4_market, sect5_governance, sect6_litigation"
  - "section_assessments.py no longer writes backward-compat booleans"

affects:
  - "Any test that sets analysis.*_clean directly needs to use section_densities instead"
  - "Phase 35 backward-compat layer fully removed"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_read_density_clean(state, section) module-local helper: reads section_densities, defaults False (full detail) not True (condensed)"
    - "Conservative degradation: unpopulated section_densities renders full detail, never suppresses content"

key-files:
  created: []
  modified:
    - "src/do_uw/stages/render/sections/sect4_market.py - removed _is_market_clean(), added _read_density_clean()"
    - "src/do_uw/stages/render/sections/sect5_governance.py - removed _is_governance_clean(), added _read_density_clean()"
    - "src/do_uw/stages/render/sections/sect3_financial.py - removed financial_clean fallback from _is_financial_density_clean()"
    - "src/do_uw/stages/render/sections/sect6_litigation.py - removed _is_litigation_clean(), added _read_density_clean()"
    - "src/do_uw/models/state.py - removed 4 deprecated boolean fields from AnalysisResults"
    - "src/do_uw/stages/analyze/section_assessments.py - removed backward-compat boolean writes"
    - "src/do_uw/stages/render/coverage.py - removed deprecated field exclusions"
    - "tests/stages/analyze/test_section_assessments.py - removed backward-compat boolean tests"
    - "tests/test_render_sections_3_4.py - removed deprecated field assignment"
    - "tests/test_render_sections_5_7.py - fixed density gating test to populate section_densities"

key-decisions:
  - "Default changed from True (condensed) to False (full detail) when section_densities unpopulated: conservative degradation prevents content suppression"
  - "sect6_litigation.py treated the same as sect4/sect5: _is_litigation_clean() deleted and replaced with _read_density_clean() helper (same pattern)"
  - "_read_density_clean() is module-local in each file — no shared utility to avoid cross-module dependency"
  - "Function parameters named market_clean in sect4_market_events.py are legitimate API — not deprecated state fields"

patterns-established:
  - "Density gating pattern: _read_density_clean(state, 'section') returns bool from section_densities; defaults False"
  - "No recompute in render: analytical logic that belongs in ANALYZE is deleted, not wrapped"

requirements-completed:
  - ARCH-03

# Metrics
duration: 20min
completed: 2026-02-25
---

# Phase 45 Plan 04: Remove Deprecated *_clean Fields Summary

**Eliminated dual-decision system in render: deleted _is_market_clean(), _is_governance_clean(), _is_litigation_clean(), backward-compat boolean fields, and all fallback recompute logic; render sections now read exclusively from state.analysis.section_densities**

## Performance

- **Duration:** 20 min
- **Started:** 2026-02-25T17:26:25Z
- **Completed:** 2026-02-25T17:46:45Z
- **Tasks:** 4
- **Files modified:** 10

## Accomplishments
- Deleted ~160 lines of recompute logic from render sections (market, governance, litigation)
- Removed 4 deprecated boolean fields from AnalysisResults model
- Eliminated backward-compat boolean writes from section_assessments.py
- All render sections now use a consistent `_read_density_clean(state, "section")` pattern
- Default changed from True (condensed) to False (full detail) — conservative, correct behavior
- 3,972 tests pass; 2 pre-existing coverage failures unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove _is_market_clean() and _is_governance_clean()** - `f90a280` (refactor)
2. **Task 2: Remove deprecated fields and financial fallback** - `a5200c8` (refactor)
3. **Task 3: Fix tests for removed fields** - `61b35f8` (fix)
4. **Task 4: AAPL pipeline verification** - no additional commit (no new files)

**Plan metadata:** TBD (docs commit)

## Files Created/Modified
- `src/do_uw/stages/render/sections/sect4_market.py` - Deleted _is_market_clean() (~50 lines), added _read_density_clean(), updated 2 usages
- `src/do_uw/stages/render/sections/sect5_governance.py` - Deleted _is_governance_clean() (~55 lines), added _read_density_clean(), updated 1 usage
- `src/do_uw/stages/render/sections/sect3_financial.py` - Removed financial_clean fallback from _is_financial_density_clean(), changed default True->False
- `src/do_uw/stages/render/sections/sect6_litigation.py` - Deleted _is_litigation_clean() (~45 lines), added _read_density_clean(), updated 1 usage
- `src/do_uw/models/state.py` - Removed governance_clean, litigation_clean, financial_clean, market_clean fields
- `src/do_uw/stages/analyze/section_assessments.py` - Removed backward-compat boolean writes (4 lines), updated docstring
- `src/do_uw/stages/render/coverage.py` - Removed deprecated field string exclusions
- `tests/stages/analyze/test_section_assessments.py` - Removed 4 backward-compat test methods
- `tests/test_render_sections_3_4.py` - Removed deprecated field assignment
- `tests/test_render_sections_5_7.py` - Fixed density gating test to populate section_densities

## Decisions Made
- Default changed from `True` (condensed) to `False` (full detail): if ANALYZE hasn't populated section_densities, safer to show full detail than suppress content.
- `_read_density_clean()` is module-local (not shared) to keep render sections self-contained without new cross-module dependencies.
- `_is_litigation_clean()` was also cleaned up (not in original plan scope) since it used the same deprecated `litigation_clean` field pattern.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed _is_litigation_clean() from sect6_litigation.py**
- **Found during:** Task 2 (Remove deprecated fields from state.py)
- **Issue:** Plan said grep must return 0 results for deprecated field references. sect6_litigation.py still accessed state.analysis.litigation_clean and had _is_litigation_clean() recompute function.
- **Fix:** Added _read_density_clean() helper to sect6_litigation.py; deleted _is_litigation_clean(); replaced fallback pattern; added DensityLevel import; removed unused coverage.py exclusions; removed backward-compat writes from section_assessments.py.
- **Files modified:** sect6_litigation.py, section_assessments.py, coverage.py
- **Verification:** grep for deprecated field references returns only function parameter names (not state field accesses)
- **Committed in:** a5200c8 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed tests referencing deprecated state fields**
- **Found during:** Task 3 (Run full test suite)
- **Issue:** test_backward_compat_booleans and 3 other tests referenced fields that were just removed; test_no_sca_shows_helpful_message expected clean behavior but state had no section_densities populated.
- **Fix:** Removed backward-compat test methods; updated test to populate section_densities for clean density gating test.
- **Files modified:** test_section_assessments.py, test_render_sections_3_4.py, test_render_sections_5_7.py
- **Verification:** 3,972 tests pass with 0 new regressions
- **Committed in:** 61b35f8 (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (2 x Rule 1 - Bug)
**Impact on plan:** Both fixes necessary to achieve the plan's stated goal of zero deprecated field references. No scope creep.

## Issues Encountered
- Pre-existing coverage test failures (test_render_coverage.py: 2 tests at 89.1% and ~88% coverage, both below 90% threshold) — confirmed pre-existing by testing against prior commit. Logged to deferred-items.

## Next Phase Readiness
- Render sections use section_densities exclusively — ARCH-03 fully enforced
- No dual-decision system remains in render stage
- Plans 05, 06, 07, 08 in Phase 45 can proceed independently

---
*Phase: 45-codebase-cleanup-architecture-hardening*
*Completed: 2026-02-25*
