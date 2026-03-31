---
phase: 35-display-presentation-clarity
plan: 06
subsystem: render
tags: [density, narratives, word-renderer, markdown-renderer, jinja2, pre-computed, out-03, data-14]

# Dependency graph
requires:
  - phase: 35-display-presentation-clarity
    provides: "DensityLevel enum, SectionDensity, PreComputedNarratives model (Plan 01); LLM narrative generation (Plan 03)"
provides:
  - "Word renderer density indicators (ELEVATED CONCERN amber, CRITICAL RISK red)"
  - "Word renderer pre-computed narrative paragraphs with [AI Assessment] prefix"
  - "Markdown template density_indicator() and section_narrative() Jinja2 macros"
  - "build_template_context() with narratives and densities context keys"
  - "Pre-computed LLM narratives override rule-based narratives in Markdown output"
affects: [35-07, render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_add_density_indicator() and _add_section_narrative() as document-level helpers in Word renderer"
    - "Jinja2 macros density_indicator() and section_narrative() for template-level rendering"
    - "Pre-computed narratives override rule-based narratives via OR-chain priority"

key-files:
  created:
    - tests/stages/render/test_word_density.py
  modified:
    - src/do_uw/stages/render/word_renderer.py
    - src/do_uw/stages/render/md_renderer.py
    - src/do_uw/templates/markdown/worksheet.md.j2

key-decisions:
  - "CLEAN density = no indicator (clean is the normal state, no visual noise)"
  - "ELEVATED = amber 'ELEVATED CONCERN', CRITICAL = red 'CRITICAL RISK' in both Word and Markdown"
  - "Section-to-density mapping covers 8 analytical sections; Calibration Notes and Meeting Prep skip indicators"
  - "Pre-computed narratives take priority over rule-based via OR-chain: narratives.get(id) or rule_based(state)"
  - "[AI Assessment] italic prefix on all LLM-generated narrative paragraphs per DATA-14"

patterns-established:
  - "_SECTION_DENSITY_MAP dict maps section display names to density/narrative field IDs"
  - "Jinja2 macros for density rendering: density_indicator(section_id) and section_narrative(section_id)"

requirements-completed: [OUT-01, OUT-03, DATA-12]

# Metrics
duration: 5min
completed: 2026-02-21
---

# Phase 35 Plan 06: Renderer Density Indicators and Pre-Computed Narratives Summary

**Word and Markdown renderers updated with three-tier density indicators (CLEAN/ELEVATED/CRITICAL) and pre-computed LLM narrative paragraphs with AI Assessment labeling**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T15:09:19Z
- **Completed:** 2026-02-21T15:14:06Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Word renderer now renders density-tier indicators (amber ELEVATED CONCERN, red CRITICAL RISK) and pre-computed narrative paragraphs with italic [AI Assessment] prefix before each section's content
- Markdown renderer build_template_context() now populates narratives and densities dicts; pre-computed LLM narratives override rule-based narratives when available
- Jinja2 template updated with density_indicator() and section_narrative() macros applied to all 6 analytical sections
- 19 new tests covering all density tiers, narrative rendering, fallback behavior, and edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1: Update Word renderer with density indicators and pre-computed narratives** - `a3c2838` (feat)
2. **Task 2: Update Markdown renderer and template for pre-computed narratives** - `e1ce613` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/word_renderer.py` - Added _add_density_indicator(), _add_section_narrative(), integrated into section render loop (407 lines)
- `src/do_uw/stages/render/md_renderer.py` - Added narratives/densities to build_template_context(), pre-computed narrative priority chain (331 lines)
- `src/do_uw/templates/markdown/worksheet.md.j2` - Added density_indicator() and section_narrative() Jinja2 macros, applied to 6 sections
- `tests/stages/render/test_word_density.py` - 19 tests across 6 test classes for density + narrative Word rendering

## Decisions Made
- CLEAN density renders no indicator -- clean is the normal state, adding text to clean sections would be noise
- _SECTION_DENSITY_MAP covers 8 analytical sections (executive_summary through ai_risk); non-analytical sections (Calibration Notes, Meeting Prep) are excluded
- Pre-computed narratives take priority over rule-based narratives via simple OR-chain pattern: `narratives.get("financial") or financial_narrative(state) or ...`
- Word narrative paragraphs use italic "[AI Assessment]" prefix (DATA-14) followed by normal-weight narrative body
- Density indicator colors match design system: amber (0xFF, 0xB8, 0x00) for ELEVATED, red (0xCC, 0x00, 0x00) for CRITICAL

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - all tests passed on first run.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Word and Markdown renderers are fully density-aware with pre-computed narrative support
- Plan 07 (HTML Bloomberg renderer) can follow the same density/narrative patterns
- All 112 render tests pass (93 existing + 19 new)

## Self-Check: PASSED

All 4 created/modified files verified on disk. Both task commits (a3c2838, e1ce613) verified in git log. 112 render tests pass (93 existing + 19 new).

---
*Phase: 35-display-presentation-clarity*
*Completed: 2026-02-21*
