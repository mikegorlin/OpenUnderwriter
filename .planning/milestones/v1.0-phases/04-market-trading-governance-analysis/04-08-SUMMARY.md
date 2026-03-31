---
phase: 4
plan: 8
subsystem: governance-extraction
tags: [board-governance, ownership, activist-risk, DEF-14A, 13D-13G]
depends_on:
  requires: [04-03]
  provides: [board-governance-extractor, ownership-extractor, governance-scoring]
  affects: [04-09, 04-10, 04-11]
tech_stack:
  added: []
  patterns: [config-driven-scoring, word-level-activist-matching]
key_files:
  created:
    - src/do_uw/stages/extract/board_governance.py
    - src/do_uw/stages/extract/ownership_structure.py
    - src/do_uw/config/governance_weights.json
    - src/do_uw/config/activist_investors.json
    - tests/test_board_ownership.py
  modified: []
metrics:
  duration: 11m 00s
  completed: 2026-02-08
  tests_added: 12
  tests_total: 469
---

# Phase 4 Plan 8: Board Governance & Ownership Extractors Summary

Board governance quality scoring (SECT5-03/07) and ownership structure (SECT5-08) extractors with config-driven weights and 12 tests.

## What Was Built

### Board Governance Extractor (board_governance.py, 475 lines)
- DEF 14A proxy statement parsing for director profiles
- Director name extraction with bio block splitting and fallback extraction
- Independence, tenure, committee membership, overboarding, prior litigation detection
- 7-dimension governance quality scoring: independence, CEO-chair duality, refreshment, overboarding, committee structure, say-on-pay, tenure
- Config-driven weights and thresholds from governance_weights.json
- Weighted total score normalized to 0-100 scale

### Ownership Structure Extractor (ownership_structure.py, 442 lines)
- Institutional/insider ownership percentages from yfinance info
- Top 10 institutional holder extraction from yfinance DataFrame data
- Activist investor matching against 23 known activists (word-level partial matching)
- SC 13D/13G filing extraction with filer name parsing
- 13G-to-13D conversion detection (passive to activist signal)
- Dual-class share structure detection from proxy text and info dict
- Activist risk assessment: HIGH/MEDIUM/LOW based on composite signals

### Config Files
- governance_weights.json: 7 scoring dimension weights summing to 1.0, 9 thresholds
- activist_investors.json: 23 known activist investor names for holder matching

### Tests (12 tests in test_board_ownership.py)
- Board: high score, low score, overboarding, config loading, missing proxy fallback
- Ownership: institutional holders, activist match, 13D filing, 13G-to-13D conversion, dual class, LOW risk, graceful missing data

## Decisions Made

1. **Public scoring/matching functions**: Made compute_governance_score, score_overboarding, check_for_activists, assess_activist_risk, extract_dual_class, extract_from_institutional_holders public (not underscore-prefixed) for direct testability following project pattern of only importing public functions in tests.

2. **Word-level activist matching**: Substring match alone misses "Elliott Management" vs "Elliott Investment Management LP". Added first-word matching (4+ char words) to handle name variations across SEC filings.

3. **Governance score scale**: Individual dimensions score 0-10, weighted sum multiplied by 10 for 0-100 total. Neutral default of 5.0 when data unavailable for a dimension.

4. **13G-to-13D conversion**: Detected by matching filer names across SC 13G and SC 13D filing documents. This is a strong activist risk signal (passive to active filing transition).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Activist matching logic**
- **Found during:** Task 2 test execution
- **Issue:** Substring matching failed for "Elliott Management" vs "Elliott Investment Management LP"
- **Fix:** Added word-level matching (_activist_matches helper) checking if first distinctive word (4+ chars) of activist name appears in holder name
- **Files modified:** ownership_structure.py
- **Commit:** 73cb12c

**2. [Rule 1 - Bug] Pyright strict mode compliance**
- **Found during:** Task 1 and 2 verification
- **Issue:** Unknown types from yfinance dicts, unnecessary casts on typed return values
- **Fix:** Added cast() for officer lists, removed unnecessary casts on get_filing_documents return values, cast list[Any] for yfinance DataFrame columns
- **Files modified:** board_governance.py, ownership_structure.py

## Next Phase Readiness

Board governance and ownership extractors are ready for integration into the ExtractStage orchestrator (plan 04-11). Both extractors follow the established pattern:
- Return tuple of (result_model, ExtractionReport)
- Use sourced.py helpers for state access
- Config files in src/do_uw/config/
- All files under 500 lines
