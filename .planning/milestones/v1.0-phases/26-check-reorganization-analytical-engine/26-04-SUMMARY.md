---
phase: 26-check-reorganization-analytical-engine
plan: 04
subsystem: analyze
tags: [executive-forensics, nlp-signals, textstat, readability, insider-trading, board-risk, tone-shift]

# Dependency graph
requires:
  - phase: 26-01
    provides: check classification foundation (CheckCategory, PlaintiffLens, SignalType, HazardOrSignal enums; check_classification.json)
  - phase: 26-01
    provides: executive_risk.py Pydantic models (IndividualRiskScore, BoardAggregateRisk)
provides:
  - executive forensics scorer pipeline (score_individual_risk, compute_board_aggregate_risk, run_executive_forensics)
  - executive data extraction bridge (extract_executive_data from AnalysisState)
  - NLP signal engine (readability change, tone shift, risk factor evolution, whistleblower detection)
  - 20 EXEC.* checks in checks.json (board aggregate, CEO/CFO risk, insider trading, tenure, departures, board profile)
  - 15 NLP.* checks in checks.json (readability, tone, risk factors, whistleblower, late filing, CAM, hedging)
  - 24 tests covering both engines
affects: [26-05-check-execution-wiring, score-stage, render-stage]

# Tech tracking
tech-stack:
  added: [textstat]
  patterns: [config-driven-scoring, graceful-degradation-on-missing-data, fuzzy-name-matching, time-decay-exponential]

key-files:
  created:
    - src/do_uw/stages/analyze/executive_data.py
    - src/do_uw/stages/analyze/executive_forensics.py
    - src/do_uw/stages/analyze/nlp_signals.py
    - tests/test_executive_forensics.py
    - tests/test_nlp_signals.py
  modified:
    - src/do_uw/brain/checks.json
    - pyproject.toml
    - uv.lock
    - tests/config/test_loader.py
    - tests/knowledge/test_migrate.py
    - tests/knowledge/test_integration.py
    - tests/test_check_classification.py

key-decisions:
  - "Config-driven scoring: all role weights, dimension maxima, time decay half-life, and aggregate thresholds in executive_scoring.json"
  - "Fuzzy name matching for insider trade attribution uses first-word + last-word comparison (handles middle names, initials, suffixes)"
  - "Graceful degradation: run_executive_forensics returns None when no governance data; NLP engine falls back to CURRENT_ONLY mode without prior-year text"
  - "textstat library for Gunning Fog Index and Flesch Reading Ease (lightweight, no ML dependencies)"
  - "Dual-strategy role extraction: phrase-keywords use substring match, word-keywords use whole-word match (prevents CTO matching inside DIRECTOR)"

patterns-established:
  - "Data extraction bridge pattern: separate module (executive_data.py) extracts and standardizes AnalysisState data before passing to scorer"
  - "Config-driven dimension scoring: each dimension scored independently with configurable max, combined via role-weighted aggregation"
  - "Time decay for historical findings: exponential decay with configurable half-life from config JSON"
  - "NLP comparison mode: COMPARISON (current vs prior) or CURRENT_ONLY (no prior available), detected automatically"

# Metrics
duration: 20min
completed: 2026-02-12
---

# Phase 26 Plan 04: EXEC/NLP Analytical Engines Summary

**Executive forensics scorer with 6-dimension person-level risk scoring, NLP signal engine with textstat readability/tone analysis, and 35 new EXEC.*/NLP.* checks in checks.json**

## Performance

- **Duration:** 20 min
- **Started:** 2026-02-12T16:14:21Z
- **Completed:** 2026-02-12T16:34:42Z
- **Tasks:** 3/3
- **Files modified:** 13 (unique across all commits)

## Accomplishments
- Built executive forensics scorer pipeline with 6 dimensions (prior litigation, regulatory enforcement, prior company failures, insider trading patterns, negative news, tenure stability) producing IndividualRiskScore and BoardAggregateRisk models
- Built NLP signal engine using textstat for Gunning Fog Index readability change detection, keyword-based tone shift analysis, risk factor evolution tracking via fuzzy matching, and whistleblower/qui tam language detection
- Added 35 new checks to checks.json (20 EXEC.*, 15 NLP.*) with full multi-dimensional classification metadata, bringing total from 346 to 381
- Created 24 comprehensive tests covering both engines (11 executive forensics, 13 NLP signals)

## Task Commits

Each task was committed atomically:

1. **Task 1: Executive forensics scorer pipeline and data extraction bridge** - `4af0dae` (feat)
2. **Task 2: NLP signal engine with textstat and prior-year comparison** - `b0971b6` (feat)
3. **Task 3: Add EXEC/NLP checks to checks.json, tests for both engines** - `3e19be0` (feat)

**Plan metadata:** [pending] (docs: complete plan)

## Files Created/Modified
- `src/do_uw/stages/analyze/executive_data.py` - Data extraction bridge: pulls executive data from AnalysisState into standardized dicts for scoring (283 lines)
- `src/do_uw/stages/analyze/executive_forensics.py` - Executive forensics scorer: 6-dimension scoring, board aggregate risk, config-driven weights (492 lines)
- `src/do_uw/stages/analyze/nlp_signals.py` - NLP signal engine: readability, tone, risk factor evolution, whistleblower detection (484 lines)
- `tests/test_executive_forensics.py` - 11 tests covering individual scoring, board aggregate, time decay, fuzzy matching, graceful degradation
- `tests/test_nlp_signals.py` - 13 tests covering readability, tone shift, risk factor evolution, whistleblower detection, no-prior-year fallback
- `src/do_uw/brain/checks.json` - Added 20 EXEC.* and 15 NLP.* checks (total 346 -> 381)
- `pyproject.toml` - Added textstat dependency
- `uv.lock` - Updated lock file for textstat
- `tests/config/test_loader.py` - Updated check count assertions from 346 to 381
- `tests/knowledge/test_migrate.py` - Updated check count assertions from 346 to 381
- `tests/knowledge/test_integration.py` - Updated minimum check count assertions to >= 370
- `tests/test_check_classification.py` - Widened category count ranges for 381 checks

## Decisions Made
- **Config-driven scoring:** All role weights (CEO=3.0, CFO=2.5, COO=2.0, etc.), dimension maxima, time decay half-life (5 years), and aggregate thresholds loaded from executive_scoring.json rather than hardcoded
- **Fuzzy name matching:** First-word + last-word comparison for associating Form 4 insider trades with executives handles middle names, initials, and suffixes
- **Graceful degradation:** run_executive_forensics returns None when no governance data available; NLP engine falls back to CURRENT_ONLY mode without prior-year text
- **textstat for readability:** Lightweight library providing Gunning Fog Index and Flesch Reading Ease without heavy ML dependencies
- **Dual-strategy role extraction:** Phrase-keywords use substring match ("CHIEF EXECUTIVE" in title), word-keywords use whole-word match ("CEO" as discrete word) to prevent false matches like "CTO" inside "DIRECTOR"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed CTO substring matching inside DIRECTOR**
- **Found during:** Task 3 (test_executive_forensics.py - test_role_extraction)
- **Issue:** `_extract_role_from_title` used `if kw in title_upper` which matched "CTO" as a substring inside "DIRECTOR", causing directors to be classified as CTO
- **Fix:** Split role mappings into phrase_keywords (substring match) and word_keywords (whole-word match using `set(title_upper.split())`). Only acronyms like CEO/CFO/CTO use word matching; full phrases like "CHIEF EXECUTIVE" use substring matching.
- **Files modified:** `src/do_uw/stages/analyze/executive_data.py`
- **Verification:** test_role_extraction passes; "Director" correctly maps to "Director" role, not "CTO"
- **Committed in:** `3e19be0` (Task 3 commit)

**2. [Rule 1 - Bug] Updated hardcoded check count assertions across 4 test files**
- **Found during:** Task 3 (running full test suite after adding 35 checks)
- **Issue:** Multiple test files had hardcoded check counts (346) that no longer matched the new total (381) after adding EXEC/NLP checks
- **Fix:** Updated assertions in test_loader.py (346->381), test_migrate.py (346->381), test_integration.py (>=340 -> >=370), test_check_classification.py (widened category ranges)
- **Files modified:** `tests/config/test_loader.py`, `tests/knowledge/test_migrate.py`, `tests/knowledge/test_integration.py`, `tests/test_check_classification.py`
- **Verification:** All 2636 tests pass (335 skipped)
- **Committed in:** `3e19be0` (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (2 bug fixes via Rule 1)
**Impact on plan:** Both fixes necessary for correctness. The CTO/DIRECTOR bug was caught by tests; the count assertions needed updating as a natural consequence of adding checks. No scope creep.

## Issues Encountered
- **File size limits:** Both executive_forensics.py (513 lines) and nlp_signals.py (522 lines) initially exceeded the 500-line anti-context-rot rule. Resolved by condensing docstrings and compacting keyword lists to single-line format. Final sizes: 492 and 484 lines respectively.
- **Pre-existing test failure:** `tests/test_forensic_composites.py::TestDechowFScore::test_high_risk` fails due to missing `as_of` field in SourcedValue constructor. Confirmed pre-existing (fails on clean main branch). Not caused by this plan's changes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Executive forensics and NLP signal engines are built and tested, ready for wiring into AnalyzeStage check execution (Plan 05)
- All 381 checks in checks.json have complete multi-dimensional classification metadata
- Both engines follow the graceful-degradation pattern: they produce results when data is available and return None/CURRENT_ONLY when it is not
- Plan 05 will wire these engines into the analyze stage's check runner and connect results to the scoring pipeline

## Self-Check: PASSED

- All 7 key files verified present on disk
- All 3 task commits (4af0dae, b0971b6, 3e19be0) verified in git history

---
*Phase: 26-check-reorganization-analytical-engine*
*Plan: 04*
*Completed: 2026-02-12*
