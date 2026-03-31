---
phase: 13-ai-transformation-risk-factor
plan: 02
subsystem: extract
tags: [ai-risk, sec-filings, item-1a, uspto-api, keyword-nlp, peer-comparison]

# Dependency graph
requires:
  - phase: 13-01
    provides: AIRiskAssessment model, ai_risk field on ExtractedData
provides:
  - AI disclosure extractor parsing Item 1A for AI keywords and sentiment
  - Patent activity extractor via USPTO API with graceful degradation
  - Competitive position extractor comparing to peer group
  - Sub-orchestrator wiring all 3 extractors into ExtractStage
affects: [13-03-render-score-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AI keyword regex matching with word-boundary patterns"
    - "USPTO API integration with httpx and try/except graceful degradation"
    - "Sub-orchestrator pattern for SECT8 (mirrors SECT4/5/6)"
    - "Module-level import for patchable sub-orchestrator wiring"

key-files:
  created:
    - src/do_uw/stages/extract/ai_disclosure_extract.py
    - src/do_uw/stages/extract/ai_patent_extract.py
    - src/do_uw/stages/extract/ai_competitive_extract.py
    - src/do_uw/stages/extract/extract_ai_risk.py
    - tests/test_ai_risk_extract.py
  modified:
    - src/do_uw/stages/extract/__init__.py

key-decisions:
  - "Module-level import for run_ai_risk_extractors (enables standard patch pattern at do_uw.stages.extract.run_ai_risk_extractors)"
  - "Try/except wrapper in ExtractStage for AI risk (new feature that should not break existing pipeline)"
  - "cast(dict[str, Any]) for USPTO JSON response (pyright strict compliance)"
  - "Sentiment classification: THREAT if threat > 2*opportunity, OPPORTUNITY if reverse, BALANCED otherwise, UNKNOWN if < 3 total mentions"
  - "Competitive position returns UNKNOWN by default (normal for single-ticker analysis without peer filings)"

patterns-established:
  - "SECT8 sub-orchestrator follows exact same pattern as SECT4/5/6: try/except per extractor, default on failure"
  - "AI keyword matching: core terms (full weight) + broader automation terms (weighted lower)"

# Metrics
duration: 9min
completed: 2026-02-10
---

# Phase 13 Plan 02: AI Risk Extraction Pipeline Summary

**3 AI extractors (disclosure, patent, competitive) with sub-orchestrator wired into ExtractStage via module-level import**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-10T06:30:52Z
- **Completed:** 2026-02-10T06:40:22Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- AI disclosure extractor parses Item 1A for 17 AI keywords, classifies sentiment (THREAT/OPPORTUNITY/BALANCED/UNKNOWN), extracts contextual risk factor snippets, computes YoY trend
- Patent extractor queries USPTO API for AI-related patents with httpx, graceful degradation to defaults on any error
- Competitive position extractor compares company AI mentions to peer group, defaults to UNKNOWN when peer data unavailable
- Sub-orchestrator (run_ai_risk_extractors) calls all 3 extractors with try/except isolation per extractor
- ExtractStage.run() populates state.extracted.ai_risk after litigation extraction
- 19 tests covering keyword counting, sentiment classification, API mocking, failure isolation, and ExtractStage integration

## Task Commits

Each task was committed atomically:

1. **Task 1: AI disclosure and patent extractors** - `113b14b` (feat)
2. **Task 2: Competitive extractor, sub-orchestrator, ExtractStage wiring** - `f51df2d` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/ai_disclosure_extract.py` (331L) - Parse Item 1A for AI keywords, sentiment, risk factors, YoY trend
- `src/do_uw/stages/extract/ai_patent_extract.py` (267L) - Query USPTO API for AI patents with graceful degradation
- `src/do_uw/stages/extract/ai_competitive_extract.py` (205L) - Peer-relative AI positioning assessment
- `src/do_uw/stages/extract/extract_ai_risk.py` (150L) - Sub-orchestrator running all 3 extractors
- `src/do_uw/stages/extract/__init__.py` (397L) - ExtractStage wiring with module-level import
- `tests/test_ai_risk_extract.py` (580L) - 19 tests for all extractors and integration

## Decisions Made
- Module-level import for run_ai_risk_extractors enables standard patch pattern (do_uw.stages.extract.run_ai_risk_extractors)
- Try/except wrapper in ExtractStage for AI risk extraction (new feature isolation)
- cast(dict[str, Any]) for USPTO JSON response parsing (pyright strict)
- Sentiment thresholds: THREAT if threat > 2*opportunity, OPPORTUNITY if reverse, BALANCED otherwise
- Competitive position defaults to UNKNOWN (normal for single-ticker analysis)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- AI risk extraction pipeline complete and integrated into ExtractStage
- Ready for 13-03-PLAN.md (render, score integration, and pipeline wiring)
- 1766 tests passing, 0 lint/type errors

---
*Phase: 13-ai-transformation-risk-factor*
*Completed: 2026-02-10*
