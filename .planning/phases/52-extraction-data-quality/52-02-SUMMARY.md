---
phase: 52-extraction-data-quality
plan: 02
subsystem: extraction
tags: [earnings-guidance, forward-guidance, regex-detection, signal-gating, pydantic]

# Dependency graph
requires:
  - phase: 49-signal-system
    provides: Signal mapper infrastructure and compute_guidance_fields
provides:
  - provides_forward_guidance field on EarningsGuidanceAnalysis
  - detect_forward_guidance() regex detection function
  - FIN.GUIDE signal gating on forward guidance status
  - Caller wiring from extract_market.py through TenKExtraction.guidance_language
affects: [render, score, analyze]

# Tech tracking
tech-stack:
  added: []
  patterns: [regex-based filing text classification, signal gating on extraction metadata]

key-files:
  created:
    - tests/test_guidance_detection.py
  modified:
    - src/do_uw/models/market_events.py
    - src/do_uw/stages/extract/earnings_guidance.py
    - src/do_uw/stages/extract/extract_market.py
    - src/do_uw/stages/analyze/signal_mappers_ext.py

key-decisions:
  - "Single compiled alternation regex instead of list of patterns (500-line compliance)"
  - "getattr() fallback for provides_forward_guidance in mapper (backward compat with pre-existing state.json)"
  - "analyst_beat_rate stored under separate key for display when company does not guide"

patterns-established:
  - "Signal gating pattern: gate mapper output fields on extraction metadata booleans"
  - "Filing text classification: regex patterns against LLM-extracted guidance_language field"

requirements-completed: [DQ-02]

# Metrics
duration: 4min
completed: 2026-02-28
---

# Phase 52 Plan 02: Earnings Guidance Detection Summary

**Forward guidance detection via 10-K/10-Q regex patterns with FIN.GUIDE signal gating for non-guiding companies**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-28T17:57:16Z
- **Completed:** 2026-02-28T18:01:23Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added `provides_forward_guidance` bool field to `EarningsGuidanceAnalysis` model, defaulting to False
- Created `detect_forward_guidance()` function with 8 regex patterns that match explicit guidance language but not SEC boilerplate disclaimers
- Wired `extract_market.py` to pass `TenKExtraction.guidance_language` through to the earnings guidance extractor
- Gated `compute_guidance_fields()` so non-guiding companies show `guidance_provided="No"` instead of "Yes"
- Preserved analyst beat/miss data under `analyst_beat_rate` key for display even when company does not guide
- Post-earnings drift and consensus divergence remain active for all companies regardless of guidance status
- 27 tests covering positive detection, negative detection, boilerplate exclusion, and mapper gating

## Task Commits

Each task was committed atomically:

1. **Task 1: Add provides_forward_guidance field, detection function, and caller wiring** - `acd757a` (feat)
2. **Task 2: Gate FIN.GUIDE signals on provides_forward_guidance and add tests** - `7af7d33` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `src/do_uw/models/market_events.py` - Added provides_forward_guidance field to EarningsGuidanceAnalysis
- `src/do_uw/stages/extract/earnings_guidance.py` - Added detect_forward_guidance() with compiled regex, wired into extract_earnings_guidance()
- `src/do_uw/stages/extract/extract_market.py` - Passes guidance_language from get_llm_ten_k(state) to earnings extractor
- `src/do_uw/stages/analyze/signal_mappers_ext.py` - Gates guidance_provided/beat_rate/philosophy on provides_forward_guidance
- `tests/test_guidance_detection.py` - 27 tests for detection and mapper gating

## Decisions Made
- Used single compiled alternation regex instead of a list of separate Pattern objects to keep earnings_guidance.py at exactly 500 lines (anti-context-rot compliance)
- Used `getattr(eg, "provides_forward_guidance", False)` in mapper for backward compatibility with any pre-existing serialized state that lacks the field
- Stored analyst consensus beat rate under `analyst_beat_rate` key (separate from `beat_rate`) so non-guiding companies still show analyst data in the worksheet per CONTEXT.md requirement

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Compacted guidance patterns to meet 500-line limit**
- **Found during:** Task 1 (adding detect_forward_guidance)
- **Issue:** Adding 8 separate `re.compile()` calls plus function docstring pushed earnings_guidance.py to 519 lines, exceeding the 500-line limit
- **Fix:** Consolidated 8 patterns into a single compiled alternation regex and trimmed docstrings
- **Files modified:** src/do_uw/stages/extract/earnings_guidance.py
- **Verification:** `wc -l` shows exactly 500 lines
- **Committed in:** acd757a (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary compaction for anti-context-rot rule. Same functionality, more compact representation.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Forward guidance detection is wired end-to-end from 10-K extraction through signal evaluation
- SNA and similar non-guiding companies will now correctly show "No" for FIN.GUIDE.current
- Ready for Plan 03 (litigation false positives) and Plan 04 (board directors extraction)

## Self-Check: PASSED

All 5 files verified present. Both task commits (acd757a, 7af7d33) verified in git log.

---
*Phase: 52-extraction-data-quality*
*Completed: 2026-02-28*
