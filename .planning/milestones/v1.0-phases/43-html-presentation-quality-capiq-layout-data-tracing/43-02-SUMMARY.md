---
phase: 43-html-presentation-quality-capiq-layout-data-tracing
plan: 02
subsystem: render
tags: [jinja2, html, templates, risk-first, section-order, scoring]

# Dependency graph
requires:
  - phase: 43-01
    provides: sidebar TOC with section anchors (id="identity", id="red-flags")
provides:
  - sections/identity.html.j2 with id="identity" (company name, ticker, sector, metrics table)
  - sections/red_flags.html.j2 with id="red-flags" (priority-sorted TRIGGERED/ELEVATED flags table)
  - worksheet.html.j2 with new section order (identity → executive → red_flags → scoring → ...)
  - scoring.html.j2 trimmed to 484 lines (below 500-line rule) via 3 sub-splits
  - appendices/sources.html.j2 placeholder for Plan 43-04 footnote infrastructure
affects: [43-03, 43-04, future rendering phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Risk-first document flow: identity → executive summary → red flags → scoring (worst signals seen first)"
    - "500-line Jinja2 split: large scoring.html.j2 broken into scoring_perils, scoring_hazard, scoring_peril_map via {% include %}"
    - "Severity weight filtering in Jinja2: filter TRIGGERED/ELEVATED from all red flags without Python sorting"

key-files:
  created:
    - src/do_uw/templates/html/sections/identity.html.j2
    - src/do_uw/templates/html/sections/red_flags.html.j2
    - src/do_uw/templates/html/sections/scoring_perils.html.j2
    - src/do_uw/templates/html/sections/scoring_hazard.html.j2
    - src/do_uw/templates/html/sections/scoring_peril_map.html.j2
    - src/do_uw/templates/html/appendices/sources.html.j2
  modified:
    - src/do_uw/templates/html/worksheet.html.j2
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/templates/html/styles.css
    - tests/stages/render/test_html_renderer.py

key-decisions:
  - "company.html.j2 excluded from new section order — its content was redundant with financial/governance sections; identity.html.j2 replaces it as the document header"
  - "scoring.html.j2 split into 4 files (scoring + 3 includes): perils, hazard, peril_map each extracted as standalone includes to satisfy 500-line rule"
  - "Red flags section shows only TRIGGERED and ELEVATED status flags; CLEAR/INFO silently omitted"

patterns-established:
  - "Section ID convention: section id matches sidebar TOC href anchor (id='identity', id='red-flags', id='scoring')"
  - "Large template split pattern: move block to new file, replace with {% include 'sections/new_file.html.j2' %}"

requirements-completed: [VIS-05, OUT-03]

# Metrics
duration: 6min
completed: 2026-02-25
---

# Phase 43 Plan 02: Section Reorder & Red Flags Summary

**Risk-first document flow via identity.html.j2 + red_flags.html.j2, with scoring.html.j2 split from 742 to 484 lines across 4 files**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-25T03:03:54Z
- **Completed:** 2026-02-25T03:09:22Z
- **Tasks:** 2
- **Files modified:** 10 (6 created, 4 modified)

## Accomplishments

- Created `identity.html.j2` with `id="identity"` — company name, ticker, sector, exchange, description, and metrics table (market cap, revenue, employees, years public)
- Created `red_flags.html.j2` with `id="red-flags"` — priority-sorted table showing only TRIGGERED/ELEVATED flags (Severity | Flag | Finding | Source), appears immediately after executive summary
- Reordered `worksheet.html.j2` to risk-first flow: identity → executive → red_flags → scoring → financial → market → governance → litigation → ai_risk → appendices
- Split `scoring.html.j2` from 742 lines to 484 lines by extracting D&O Peril Assessment, Hazard Profile, and Peril Map into dedicated include files
- All 217 render tests pass

## Task Commits

1. **Task 1: Create identity.html.j2 and update worksheet.html.j2 section order** - `e416b97` (feat)
2. **Task 2: Create red_flags.html.j2 and split scoring.html.j2** - `f429c75` (feat)

**Plan metadata:** *(final commit follows)*

## Files Created/Modified

- `src/do_uw/templates/html/sections/identity.html.j2` - Company identity block with id="identity", name/ticker/sector/metrics
- `src/do_uw/templates/html/sections/red_flags.html.j2` - Dedicated Red Flags section, TRIGGERED/ELEVATED filtered sorted table
- `src/do_uw/templates/html/sections/scoring_perils.html.j2` - D&O Peril Assessment block (split from scoring.html.j2)
- `src/do_uw/templates/html/sections/scoring_hazard.html.j2` - Hazard Profile block (split from scoring.html.j2)
- `src/do_uw/templates/html/sections/scoring_peril_map.html.j2` - Peril Map block (split from scoring.html.j2)
- `src/do_uw/templates/html/appendices/sources.html.j2` - Placeholder for Plan 43-04 footnote infrastructure
- `src/do_uw/templates/html/worksheet.html.j2` - New include order: identity → executive → red_flags → scoring → ...
- `src/do_uw/templates/html/sections/scoring.html.j2` - Red flags block removed, 3 sub-blocks extracted to includes (742→484 lines)
- `src/do_uw/templates/html/styles.css` - Added identity block CSS (.identity-block, .kv-key, .kv-value, .kv-context)
- `tests/stages/render/test_html_renderer.py` - Updated section assertions to match new worksheet order

## Decisions Made

- `company.html.j2` was excluded from the new worksheet order — its content (company profile, classification) was already represented in financial/governance sections; `identity.html.j2` serves as the concise document header
- scoring.html.j2 required three separate splits (perils, hazard, peril_map) to reach under 500 lines, since removing the red_flags block alone only reduced it from 742 to 718 lines

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test assertion for new section order**
- **Found during:** Task 2 (verification run)
- **Issue:** `test_full_html_render` asserted `"Company Profile" in html` but company.html.j2 was removed from the worksheet's section include list per the plan
- **Fix:** Replaced `assert "Company Profile" in html` with `assert "Red Flags" in html` to match the new section order
- **Files modified:** `tests/stages/render/test_html_renderer.py`
- **Verification:** 217/217 render tests pass
- **Committed in:** `f429c75` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — test updated to match intentional section removal)
**Impact on plan:** Necessary correctness fix. company.html.j2 removal was by design.

## Issues Encountered

- scoring.html.j2 was 742 lines before any changes — required 3 extraction passes (perils 68 lines, hazard 137 lines, peril_map 48 lines) plus red_flags removal (24 lines) to reach 484 lines

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Sidebar TOC anchors (`id="identity"`, `id="red-flags"`) now exist, matching Plan 43-01's TOC links
- sources.html.j2 placeholder ready for Plan 43-04 (footnote infrastructure)
- scoring.html.j2 at 484 lines with clean include structure for future additions

---
*Phase: 43-html-presentation-quality-capiq-layout-data-tracing*
*Completed: 2026-02-25*
