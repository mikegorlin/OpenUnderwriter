---
phase: 38-render-completeness-quarterly-data
plan: 05
subsystem: render
tags: [jinja2, markdown, html, governance-forensics, litigation, board-profiles, derivative-suits, contingent-liabilities]

# Dependency graph
requires:
  - phase: 38-render-completeness-quarterly-data
    provides: "Split MD templates into section includes (38-01)"
provides:
  - "Full board forensic profiles with interlocks, relationship flags, independence concerns in MD/HTML"
  - "Derivative suits with individual case detail in all three formats"
  - "Contingent liabilities (ASC 450) rendering with classification and amount ranges"
  - "Workforce/product/environmental matter rendering by category"
  - "Whistleblower indicator rendering with significance levels"
  - "Empty fields show 'None found' for underwriter trust"
affects: [38-06, 38-07]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Per-board-member forensic profile card pattern in MD/HTML", "Extract-then-render split for governance (separate file)"]

key-files:
  created:
    - src/do_uw/stages/render/md_renderer_helpers_governance.py
  modified:
    - src/do_uw/stages/render/md_renderer_helpers_ext.py
    - src/do_uw/templates/markdown/sections/governance.md.j2
    - src/do_uw/templates/markdown/sections/litigation.md.j2
    - src/do_uw/templates/html/sections/governance.html.j2
    - src/do_uw/templates/html/sections/litigation.html.j2
    - src/do_uw/stages/render/sections/sect6_defense.py

key-decisions:
  - "Split extract_governance() into md_renderer_helpers_governance.py (258 lines) to keep ext file under 500 lines"
  - "Board forensic profiles rendered as individual sub-sections per member with attribute table + bulleted lists for interlocks/flags/concerns"
  - "Empty forensic fields explicitly show 'None found' rather than being omitted, confirming the system checked"
  - "Workforce/product/environmental rendering added to sect6_defense.py (SECT6-04) alongside contingent liabilities and whistleblower (SECT6-08/09)"

patterns-established:
  - "Per-entity forensic card pattern: attribute table + conditional bulleted lists for findings, 'None found' for empty"
  - "Litigation matter type subsections: each type gets its own heading with explicit empty state message"

requirements-completed: [SC-4, SC-5]

# Metrics
duration: 7min
completed: 2026-02-21
---

# Phase 38 Plan 05: Governance Forensics & Complete Litigation Rendering Summary

**Full board forensic profiles (interlocks, relationship flags, independence concerns) and complete litigation rendering (derivative suits with case detail, contingent liabilities, workforce/product/environmental, whistleblower) in MD, Word, and HTML**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-21T20:33:26Z
- **Completed:** 2026-02-21T20:41:02Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Board forensic profiles now render full detail per member: committees, other boards, interlocks, relationship flags, independence concerns, overboarded status, prior litigation count
- Derivative suits render with individual case detail (case name, filing date, court, status, allegations, settlement) instead of just a count
- Contingent liabilities render with ASC 450 classification, amount ranges, and source notes
- Workforce, product, environmental, and cybersecurity matters render categorized by type
- Whistleblower indicators render with type, description, date, and significance
- All empty subsections explicitly show "None found" / "No derivative suits found" etc.
- Governance extraction split to dedicated file for 500-line compliance

## Task Commits

Each task was committed atomically:

1. **Task 1: Complete board forensics in MD + extend governance context extraction** - `bf4f84b` (feat)
2. **Task 2: Complete litigation rendering** - `3fc15c8` (feat -- changes absorbed into concurrent 38-04 summary commit)

## Files Created/Modified
- `src/do_uw/stages/render/md_renderer_helpers_governance.py` - New file: extract_governance() split out (258 lines)
- `src/do_uw/stages/render/md_renderer_helpers_ext.py` - Rewritten: litigation extraction with derivative/contingent/WPE/whistleblower helpers (420 lines)
- `src/do_uw/templates/markdown/sections/governance.md.j2` - Per-member forensic profile sections with attribute tables (98 lines)
- `src/do_uw/templates/markdown/sections/litigation.md.j2` - Full litigation subsections for all matter types (113 lines)
- `src/do_uw/templates/html/sections/governance.html.j2` - Board forensic profile cards with kv_table + conditional lists (214 lines)
- `src/do_uw/templates/html/sections/litigation.html.j2` - Derivative/contingent/WPE/whistleblower HTML sections (260 lines)
- `src/do_uw/stages/render/sections/sect6_defense.py` - Added workforce/product/environmental Word rendering (483 lines)

## Decisions Made
- **Governance extraction split**: extract_governance() moved to `md_renderer_helpers_governance.py` because adding forensic fields pushed `md_renderer_helpers_ext.py` to 503 lines. The ext file re-exports via `from ... import extract_governance as extract_governance` for backward compatibility.
- **Per-member forensic cards**: Each board member gets its own sub-section with an attribute table and conditional bulleted lists for interlocks, relationship flags, and independence concerns. "None found" shown for empty fields to confirm the system checked.
- **WPE in sect6_defense.py**: Workforce/product/environmental rendering placed in sect6_defense.py alongside contingent liabilities and whistleblower (all SECT6-04/05/08/09) rather than creating a new file, keeping the module at 483 lines.
- **Litigation matter subsections**: Each matter type (derivative suits, contingent liabilities, WPE, whistleblower) gets its own titled subsection with explicit empty-state messaging rather than being silently omitted.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Task 2 file changes (litigation.md.j2, litigation.html.j2, sect6_defense.py) were committed as part of a concurrent 38-04 summary commit (3fc15c8) rather than in a separate Task 2 commit. The changes are correct and complete; only the commit attribution differs from the standard per-task commit pattern.
- Two pre-existing test failures (PDF/WeasyPrint library loading) are unrelated to this plan and were not fixed (out of scope).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All governance forensic fields now render in all three formats (MD, Word, HTML)
- All litigation matter types now render with full detail in all three formats
- Templates ready for 38-06 (remaining render gaps) and 38-07 (final cleanup)

## Self-Check: PASSED

- All 7 modified/created files verified present on disk
- Commit bf4f84b verified in git history (Task 1)
- Commit 3fc15c8 verified in git history (Task 2 changes)
- All 17 Markdown renderer tests pass
- All files under 500 lines (max: 483 in sect6_defense.py)

---
*Phase: 38-render-completeness-quarterly-data*
*Completed: 2026-02-21*
