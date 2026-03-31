---
phase: 27-peril-mapping-bear-case-framework
plan: 05
subsystem: render
tags: [docx, peril-map, heat-map, bear-case, coverage-gaps, settlement-prediction, tower-risk]

# Dependency graph
requires:
  - phase: 27-02
    provides: "PerilMap model, PlaintiffAssessment, BearCase, EvidenceItem, 7-lens peril mapping engine"
  - phase: 27-03
    provides: "DDL settlement prediction, SeverityScenarios, tower risk characterization"
provides:
  - "Peril map heat map renderer (sect7_peril_map.py) with 7x2 color-coded grid"
  - "Bear case narrative renderer with committee summary + evidence chain"
  - "DDL-based settlement prediction table with 4 percentile scenarios"
  - "Tower risk characterization table showing per-layer expected loss share"
  - "Coverage gaps section (sect7_coverage_gaps.py) for DATA_UNAVAILABLE disclosure"
  - "Integration wiring into Section 7 of the worksheet"
affects: [render, scoring, output-quality]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Color-coded cell shading for heat map bands", "Tiered audience rendering (committee summary + detail drill-down)"]

key-files:
  created:
    - "src/do_uw/stages/render/sections/sect7_peril_map.py"
    - "src/do_uw/stages/render/sections/sect7_coverage_gaps.py"
    - "tests/stages/render/test_sect7_peril_map.py"
  modified:
    - "src/do_uw/stages/render/sections/sect7_scoring.py"
    - "src/do_uw/stages/render/sections/__init__.py"

key-decisions:
  - "Peril map heat map uses cell-level background shading (not conditional formatting) for maximum Word compatibility"
  - "Settlement prediction renders Phase 27 DDL-based data first, falls back to legacy severity scenarios"
  - "Coverage gaps section always renders last in Section 7 as disclosure"
  - "Render functions called from sect7_scoring.py (not as separate section entries) to keep Section 7 cohesive"

patterns-established:
  - "Band-to-color mapping: dict[str, str] for cell shading hex values"
  - "Coverage gaps rendering: grouped by section, with coverage percentage footer"

# Metrics
duration: 7min
completed: 2026-02-12
---

# Phase 27 Plan 05: Peril Map & Coverage Gaps Rendering Summary

**7-lens heat map with color-coded probability/severity bands, bear case narratives, DDL settlement tables, tower risk layers, and DATA_UNAVAILABLE coverage gaps disclosure**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-12T21:06:40Z
- **Completed:** 2026-02-12T21:13:55Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- 7x2 plaintiff heat map with per-cell color-coded probability and severity bands, plus summary notes for elevated lenses
- Bear case rendering with tiered audience: bold committee summary up front, evidence chain as numbered drill-down, defense assessment in italics
- DDL-based settlement prediction table showing 4 scenarios (Favorable/Median/Adverse/Catastrophic) with DDL, settlement, defense costs, total exposure
- Tower risk characterization showing per-layer expected loss share percentages
- Coverage Gaps section that explicitly lists all DATA_UNAVAILABLE checks with reasons, grouped by worksheet section, with coverage percentage footer
- NOT_APPLICABLE checks listed separately in brief format
- All new rendering wired into Section 7 via sect7_scoring.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Render peril map heat map and bear cases** - `cac4600` (feat)
2. **Task 2: Render coverage gaps section and wire into document assembly** - `58e379b` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/sections/sect7_peril_map.py` - Peril map heat map, bear cases, settlement prediction, tower risk rendering (439 lines)
- `src/do_uw/stages/render/sections/sect7_coverage_gaps.py` - Coverage gaps section for DATA_UNAVAILABLE disclosure (151 lines)
- `src/do_uw/stages/render/sections/sect7_scoring.py` - Added imports and calls to peril map + coverage gaps renderers (460 lines)
- `src/do_uw/stages/render/sections/__init__.py` - Exported render_peril_map and render_coverage_gaps
- `tests/stages/render/test_sect7_peril_map.py` - 18 tests covering heat map, bear cases, settlement, tower, edge cases

## Decisions Made
- Peril map heat map uses direct cell-level background shading (OxmlElement w:shd) for maximum compatibility across Word versions
- Settlement rendering checks Phase 27 DDL-based prediction first, falls back to legacy severity scenarios for backward compatibility
- Coverage gaps section always renders last in Section 7 -- disclosure should be the final thing an underwriter sees before Section 8
- New renderers are called from within sect7_scoring.py's render_section_7 rather than as separate entries in word_renderer.py, keeping Section 7 as a single cohesive unit

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] File exceeded 500-line limit**
- **Found during:** Task 1
- **Issue:** Initial sect7_peril_map.py was 519 lines, exceeding the 500-line anti-context-rot rule
- **Fix:** Condensed docstrings and removed decorative section header comments, brought to 439 lines
- **Files modified:** src/do_uw/stages/render/sections/sect7_peril_map.py
- **Verification:** `wc -l` confirms 439 lines; all 18 tests still pass
- **Committed in:** cac4600 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor formatting change to comply with line-length rule. No scope impact.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Phase 27 analytical rendering is now in the worksheet
- Phase 27 Plan 04 (bear case construction engine) is the remaining prerequisite
- After Plan 04, the full pipeline RESOLVE -> ACQUIRE -> EXTRACT -> ANALYZE -> SCORE -> BENCHMARK -> RENDER will produce peril maps, bear cases, settlement predictions, tower characterization, and coverage gaps in the final Word document

---
*Phase: 27-peril-mapping-bear-case-framework*
*Completed: 2026-02-12*
