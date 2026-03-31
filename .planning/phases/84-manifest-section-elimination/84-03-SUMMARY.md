---
phase: 84-manifest-section-elimination
plan: 03
subsystem: render
tags: [manifest, signal-groups, html-renderer, section-elimination, v3-architecture]

requires:
  - phase: 84-manifest-section-elimination
    provides: "ManifestGroup model, collect_signals_by_group, evolved manifest YAML"
provides:
  - "section_renderer.py uses manifest groups + signal self-selection (no section YAML)"
  - "html_signals.py uses manifest + signal.group for section mapping (no section YAML)"
  - "Prefix-based grouping preserved for template backward compat (BIZ, FIN, GOV etc.)"
  - "Cached facet metadata lookup for O(1) per-signal resolution"
affects: [84-04, render-pipeline, qa-audit, coverage-stats]

tech-stack:
  added: []
  patterns: ["Prefix-based grouping from signal IDs for template backward compat", "Cached manifest lookups with _reset_caches for test isolation"]

key-files:
  created:
    - tests/stages/render/test_html_signals.py
  modified:
    - src/do_uw/stages/render/section_renderer.py
    - src/do_uw/stages/render/html_signals.py
    - tests/stages/render/test_section_renderer.py
    - tests/stages/render/test_manifest_rendering.py

key-decisions:
  - "Keep prefix-based grouping (BIZ, FIN, GOV) in html_signals for template backward compat -- templates hardcode these keys"
  - "section_context.section field set to None (no SectionSpec needed with manifest groups)"
  - "build_section_context accepts **kwargs to absorb deprecated sections_dir param"

patterns-established:
  - "Manifest-driven rendering: section_context and manifest_sections both sourced from manifest groups"
  - "Signal prefix derived from signal ID (first dot-segment), mapped to section name via manifest"

requirements-completed: [MANIF-03, MANIF-04, SECT-01, SECT-02]

duration: 6min
completed: 2026-03-08
---

# Phase 84 Plan 03: High-Risk Renderer Consumer Migration Summary

**section_renderer.py and html_signals.py migrated from section YAML to manifest groups with signal self-selection; prefix-based template grouping preserved**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-08T07:49:26Z
- **Completed:** 2026-03-08T07:55:11Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- section_renderer.py fully migrated: build_section_context uses load_manifest + collect_signals_by_group instead of load_all_sections
- html_signals.py fully migrated: _build_signal_section_map derives prefix mapping from manifest + signal.group field
- All 573 render tests pass with zero section YAML imports in either migrated file
- Cached facet metadata for O(1) per-signal lookup in _lookup_facet_metadata

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate section_renderer.py to manifest groups** - `43e6616` (feat)
2. **Task 2: Migrate html_signals.py to manifest groups** - `d9f259d` (feat)
3. **Auto-fix: Update manifest rendering test for groups** - `2848b87` (fix)

## Files Created/Modified
- `src/do_uw/stages/render/section_renderer.py` - Replaced load_all_sections with manifest groups; section_context from ManifestGroup
- `src/do_uw/stages/render/html_signals.py` - Replaced _get_sections() with manifest + signal.group; added caching layer
- `tests/stages/render/test_section_renderer.py` - Rewritten: 29 tests for manifest-driven dispatch
- `tests/stages/render/test_html_signals.py` - New: 16 tests for signal grouping and coverage stats
- `tests/stages/render/test_manifest_rendering.py` - Updated data_type test to render_as (ManifestGroup field)

## Decisions Made
- Kept prefix-based grouping keys (BIZ, FIN, GOV, STOCK, LIT, FWRD, EXEC, NLP) because 15+ HTML templates hardcode these keys in `signal_results_by_section.get('FIN', [])` etc.
- section_context["section"] set to None rather than a SectionSpec object -- templates only access facets, not the section object
- build_section_context accepts **kwargs to absorb the deprecated sections_dir parameter from old callers

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated test_manifest_rendering.py data_type assertion**
- **Found during:** Task 2 verification (full render test suite)
- **Issue:** test_manifest_facets_have_data_type expected `data_type` key in manifest_sections facets, but ManifestGroup doesn't have data_type (was ManifestFacet-only)
- **Fix:** Replaced with test_manifest_facets_have_render_as checking the render_as field instead; removed unused ManifestFacet import
- **Files modified:** tests/stages/render/test_manifest_rendering.py
- **Verification:** All 573 render tests pass
- **Committed in:** 2848b87

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Test was asserting a deprecated field. Minimal change to match the new schema.

## Issues Encountered
- Signal IDs in tests used fake IDs like "BIZ.company_description" that don't exist; actual signals have nested prefixes like "BIZ.COMP.market_position" -- fixed in test creation.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both high-risk renderer consumers (section_renderer.py, html_signals.py) now fully migrated from section YAML
- Ready for Plan 04 (final section YAML deletion and cleanup)
- All 573 render tests pass; no section YAML imports remain in render/

---
*Phase: 84-manifest-section-elimination*
*Completed: 2026-03-08*
