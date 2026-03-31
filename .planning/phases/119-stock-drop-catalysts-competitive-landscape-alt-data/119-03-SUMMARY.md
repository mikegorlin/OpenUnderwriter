---
phase: 119-stock-drop-catalysts-competitive-landscape-alt-data
plan: 03
subsystem: extract
tags: [llm-extraction, competitive-landscape, alt-data, esg, ai-washing, tariff, peer-sca, 10-k]

requires:
  - phase: 119-01
    provides: "CompetitiveLandscape, AltDataAssessments, PeerRow, MoatDimension Pydantic models + AnalysisState fields"
provides:
  - "extract_competitive_landscape() -- LLM extraction of peers + moat dimensions from 10-K Item 1"
  - "extract_alt_data() -- ESG, AI-washing, tariff, peer SCA extraction from existing state"
affects: [119-04, 119-05, 119-06]

tech-stack:
  added: []
  patterns: ["LLM JSON extraction with QUAL-03 analytical context", "State-derived alt data signals with D&O relevance narratives"]

key-files:
  created:
    - src/do_uw/stages/extract/competitive_extraction.py
    - src/do_uw/stages/extract/alt_data_extraction.py
    - tests/stages/extract/test_competitive_extraction.py
    - tests/stages/extract/test_alt_data_extraction.py
  modified: []

key-decisions:
  - "competitive_extraction uses raw JSON LLM extraction (no Pydantic schema class) -- simpler than instructor-based approach for this use case"
  - "alt_data_extraction uses regex-based SCA keyword scanning on web_search_results rather than LLM -- deterministic, no cost"
  - "AI-washing scienter risk derived from opportunity-to-threat mention ratio (>10:1 = HIGH, >3:1 = MEDIUM)"
  - "Tariff exposure mapped directly from geopolitical_risk_score thresholds (>=3 HIGH, >=1 MEDIUM)"

patterns-established:
  - "State-derived extraction pattern: all alt data sourced from existing state, no new MCP/acquisition calls"
  - "D&O relevance narrative: every sub-assessment includes actionable D&O risk explanation"

requirements-completed: [DOSSIER-07, ALTDATA-01, ALTDATA-02, ALTDATA-03, ALTDATA-04]

duration: 4min
completed: 2026-03-20
---

# Phase 119 Plan 03: Competitive Landscape + Alt Data Extraction Summary

**LLM extraction of 4+ peers and 7 moat dimensions from 10-K Item 1, plus ESG/AI-washing/tariff/peer-SCA alt data signals derived from existing state data**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-20T16:57:03Z
- **Completed:** 2026-03-20T17:01:45Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Competitive landscape LLM extraction from 10-K with QUAL-03 analytical context, parsing 4+ peers and 7 moat dimensions
- Alt data extraction from existing state data: ESG risk (esg_gap_score thresholds), AI-washing (opportunity/threat ratio), tariff (geopolitical_risk_score), peer SCA (regex web search scan)
- D&O relevance narratives auto-generated for all sub-assessments
- 28 TDD tests across both modules, all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Competitive landscape LLM extraction from 10-K** - `bdde6a60` (feat)
2. **Task 2: Alt data extraction from existing state data** - `ac483aaa` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/competitive_extraction.py` - LLM extraction of peers + moat dimensions from 10-K Item 1
- `src/do_uw/stages/extract/alt_data_extraction.py` - ESG, AI-washing, tariff, peer SCA extraction from state
- `tests/stages/extract/test_competitive_extraction.py` - 8 tests for competitive extraction
- `tests/stages/extract/test_alt_data_extraction.py` - 20 tests for alt data extraction

## Decisions Made
- Used raw JSON LLM extraction for competitive landscape rather than instructor-based Pydantic schema -- simpler for this use case since we manually parse into PeerRow/MoatDimension models
- AI-washing scienter risk uses opportunity-to-threat mention ratio from existing AIRiskAssessment disclosure data (>10:1 = HIGH, >3:1 = MEDIUM)
- Peer SCA detection uses regex on web_search_results rather than LLM -- deterministic, zero cost, matches "securities class action", "securities fraud", "SCA", "10b-5" etc.
- Tariff exposure mapped directly from geopolitical_risk_score (>=3 sanctioned = HIGH, >=1 high-risk = MEDIUM)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Competitive extraction ready for pipeline wiring (119-06)
- Alt data extraction ready for scoring integration (119-04) and template rendering (119-05)
- Both modules export clean public APIs: extract_competitive_landscape(), extract_alt_data()

---
*Phase: 119-stock-drop-catalysts-competitive-landscape-alt-data*
*Completed: 2026-03-20*
