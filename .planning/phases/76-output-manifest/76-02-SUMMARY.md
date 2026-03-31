---
phase: 76-output-manifest
plan: 02
subsystem: render
tags: [manifest, html, word, pdf, jinja2, section-ordering]

requires:
  - phase: 76-output-manifest
    provides: "OutputManifest schema, output_manifest.yaml, load_manifest()"
provides:
  - "Manifest-driven HTML section loop in worksheet.html.j2"
  - "Manifest-driven Word section dispatch in word_renderer.py"
  - "manifest_sections context variable for template rendering"
  - "PDF inherits manifest ordering automatically via HTML"
affects: [77-manifest-rendering, 78-template-authority, 79-facet-requires, 80-gap-remediation]

tech-stack:
  added: []
  patterns: ["Manifest loop replaces hardcoded includes in HTML", "Section renderer map for Word dispatch"]

key-files:
  created:
    - tests/stages/render/test_manifest_rendering.py
  modified:
    - src/do_uw/stages/render/section_renderer.py
    - src/do_uw/templates/html/worksheet.html.j2
    - src/do_uw/stages/render/word_renderer.py

key-decisions:
  - "HTML template uses simple manifest_sections loop instead of 13 hardcoded includes"
  - "Word renderer maps manifest section IDs to (module, function) tuples via _SECTION_RENDERER_MAP"
  - "Calibration Notes appended as system section outside manifest (not worksheet content)"
  - "HTML-only appendices (sources, qa_audit, coverage) skipped in Word via None mapping"

patterns-established:
  - "manifest_sections context variable: ordered list of dicts with id/name/template/render_mode/facets"
  - "_SECTION_RENDERER_MAP: manifest section ID to Word renderer module/function mapping"

requirements-completed: [MAN-02, MAN-03]

duration: 4min
completed: 2026-03-07
---

# Phase 76 Plan 02: Manifest-Driven Rendering Summary

**Replaced hardcoded section lists in HTML and Word renderers with manifest-driven loops so output_manifest.yaml controls section structure across all formats**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-07T18:20:19Z
- **Completed:** 2026-03-07T18:24:15Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Replaced 13 hardcoded `{% include %}` lines in worksheet.html.j2 with a 3-line manifest loop
- Updated build_section_context() to return manifest_sections list preserving manifest order
- Converted Word renderer from 10 hardcoded section entries to manifest-driven dispatch via _SECTION_RENDERER_MAP
- All 560 render tests pass with zero regressions, plus 10 new manifest rendering tests

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing manifest rendering tests** - `0979439` (test)
2. **Task 1 (GREEN): Manifest-driven HTML rendering** - `ce61a2f` (feat)
3. **Task 2: Manifest-driven Word rendering** - `612b566` (feat)

## Files Created/Modified
- `tests/stages/render/test_manifest_rendering.py` - 10 tests for manifest_sections ordering, shape, removal, determinism, HTML context wiring
- `src/do_uw/stages/render/section_renderer.py` - build_section_context now returns manifest_sections list alongside section_context dict
- `src/do_uw/templates/html/worksheet.html.j2` - Manifest loop replaces 13 hardcoded includes
- `src/do_uw/stages/render/word_renderer.py` - _get_section_renderers uses manifest for ordering via _SECTION_RENDERER_MAP

## Decisions Made
- HTML template uses `{% for section in manifest_sections %}{% include section.template %}{% endfor %}` -- simple, transparent, and the manifest controls what renders
- Word renderer keeps _SECTION_RENDERER_MAP as explicit mapping rather than auto-discovery -- safer for a format where not all HTML sections have Word equivalents
- Calibration Notes stays outside the manifest as a system section (not worksheet content)
- Backward compat maintained: section_context dict still returned for facet-level dispatch within sections

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three output formats (HTML, Word, PDF) now driven by output_manifest.yaml
- Adding/removing a section in the manifest changes the output accordingly
- Ready for Phase 77 (template authority) and Phase 78 (facet requires enforcement)

## Self-Check: PASSED

All files verified on disk. All commit hashes verified in git log.

---
*Phase: 76-output-manifest*
*Completed: 2026-03-07*
