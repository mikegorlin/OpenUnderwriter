---
phase: 61-surface-hidden-data
plan: 02
subsystem: render
tags: [nlp, sentiment, hazard-profile, jinja2, css, trend-arrows, dashboard]

requires:
  - phase: 58-shared-context-layer
    provides: context_builders/analysis.py extract functions
  - phase: 61-01
    provides: SURF-08 source attribution pattern (_sources/_confidence dicts)
provides:
  - NLP/Sentiment Dashboard with full SentimentProfile and NarrativeCoherence rendering
  - Expandable H1-H7 hazard category cards showing all 55 dimensions
  - Trend arrow rendering pattern for directional NLP signals
  - L-M dictionary bar trend visualization
affects: [65-narrative-depth, 66-final-qa]

tech-stack:
  added: []
  patterns:
    - "_nlp_helpers.py extraction module to keep analysis.py under 500 lines"
    - "CSS-only mini bar charts for L-M dictionary trends"
    - "Unicode trend arrows with CSS color classes"
    - "Expandable <details> cards for category-grouped dimension display"

key-files:
  created:
    - src/do_uw/stages/render/context_builders/_nlp_helpers.py
    - src/do_uw/templates/html/sections/scoring/nlp_dashboard.html.j2
  modified:
    - src/do_uw/stages/render/context_builders/analysis.py
    - src/do_uw/templates/html/sections/scoring/hazard_profile.html.j2
    - src/do_uw/templates/html/sections/scoring/nlp_analysis.html.j2
    - src/do_uw/brain/sections/scoring.yaml
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/templates/html/components.css

key-decisions:
  - "Created _nlp_helpers.py to extract NLP/sentiment/coherence data, keeping analysis.py under 500 lines"
  - "Updated existing nlp_analysis facet in scoring.yaml to point to nlp_dashboard template (avoids duplicate rendering)"
  - "Kept nlp_analysis.html.j2 as deprecated backward-compat fallback"

patterns-established:
  - "Trend arrow pattern: _trend_arrow() returns {arrow, css, label} dict consumed by templates"
  - "Category card pattern: <details> with summary header + child dimension table"

requirements-completed: [SURF-03, SURF-05, SURF-08]

duration: 8min
completed: 2026-03-03
---

# Phase 61 Plan 02: NLP/Sentiment Dashboard and Hazard Category Cards Summary

**Full NLP/Sentiment Dashboard with trend arrows, L-M dictionary bars, multi-source sentiment, narrative coherence checks, and expandable H1-H7 hazard category cards showing all 55 dimensions**

## Performance

- **Duration:** 8 min (continuation -- Tasks 1-4 completed by prior executor)
- **Started:** 2026-03-03T03:40:01Z
- **Completed:** 2026-03-03T03:48:00Z
- **Tasks:** 5
- **Files modified:** 9

## Accomplishments
- NLP/Sentiment Dashboard renders all 15+ SentimentProfile fields with trend arrows, L-M dictionary bar trends, multi-source sentiment grid, and narrative coherence assessment
- All 55 hazard dimensions visible in expandable H1-H7 category cards with auto-open for elevated categories
- Source attribution (_sources/_confidence) on all new displays per SURF-08
- Zero test regressions (319 render tests pass, 34 NLP/hazard/scoring tests pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Enhance NLP signals context builder with full sentiment data** - `152ff54` (feat)
2. **Task 2: Create NLP/Sentiment Dashboard template** - `5e85b2d` (feat)
3. **Task 3: Enhance hazard profile with expandable category cards** - `042666b` (feat)
4. **Task 4: Add CSS for NLP trend arrows, L-M bars, and hazard cards** - `72aa87f` (feat)
5. **Task 5: Run tests and verify rendering** - verification only, no commit needed

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/_nlp_helpers.py` - New module: extracts SentimentProfile, NarrativeCoherence, trend arrows, L-M trends, multi-source sentiment
- `src/do_uw/stages/render/context_builders/analysis.py` - Enhanced extract_nlp_signals() and extract_hazard_profile() with categories_with_dimensions (484 lines)
- `src/do_uw/templates/html/sections/scoring/nlp_dashboard.html.j2` - New comprehensive NLP/Sentiment Dashboard (256 lines)
- `src/do_uw/templates/html/sections/scoring/hazard_profile.html.j2` - Expandable H1-H7 category cards with child dimension tables
- `src/do_uw/templates/html/sections/scoring/nlp_analysis.html.j2` - Marked deprecated, kept for backward compat
- `src/do_uw/brain/sections/scoring.yaml` - nlp_analysis facet now points to nlp_dashboard template
- `src/do_uw/templates/html/sections/scoring.html.j2` - Updated legacy fallback include
- `src/do_uw/templates/html/components.css` - Trend arrows, L-M bars, hazard cards, alignment indicators (445 lines)

## Decisions Made
- Created `_nlp_helpers.py` extraction module to keep analysis.py under the 500-line limit (was approaching 480 lines pre-change)
- Updated existing `nlp_analysis` facet ID in scoring.yaml to point to new `nlp_dashboard.html.j2` template rather than adding a new facet -- avoids duplicate rendering
- Kept `nlp_analysis.html.j2` with deprecation comment for backward compatibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-existing test failures in `tests/brain/` and `tests/knowledge/` (MANAGEMENT_DISPLAY count 98 vs expected 99) -- unrelated to this plan's changes, not addressed
- Pre-existing Word coverage test at 89.6% < 90% threshold -- unrelated to this plan

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- NLP/Sentiment Dashboard and hazard category cards ready for visual review
- Plan 61-03 can proceed (remaining surface-hidden-data work)
- Phase 65 (Narrative Depth) can consume the new NLP context data

---
*Phase: 61-surface-hidden-data*
*Completed: 2026-03-03*
