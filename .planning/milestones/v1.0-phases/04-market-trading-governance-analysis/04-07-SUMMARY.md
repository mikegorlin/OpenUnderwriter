---
phase: "04"
plan: "07"
subsystem: "extract"
tags: ["governance", "leadership", "compensation", "proxy", "8-K", "SECT5"]
dependency-graph:
  requires: ["04-03"]
  provides: ["leadership_profiles_extractor", "compensation_analysis_extractor"]
  affects: ["04-09", "04-10", "04-11"]
tech-stack:
  added: []
  patterns: ["split-module", "red-flag-scoring", "filing-document-parsing"]
key-files:
  created:
    - "src/do_uw/stages/extract/leadership_profiles.py"
    - "src/do_uw/stages/extract/leadership_parsing.py"
    - "src/do_uw/stages/extract/compensation_analysis.py"
    - "tests/test_leadership_comp.py"
  modified: []
decisions:
  - id: "04-07-01"
    description: "Split leadership_profiles into profiles + parsing for 500-line compliance"
  - id: "04-07-02"
    description: "Name regex uses mandatory space before last name: [A-Z][a-z]+\\s+(?:[A-Z]\\.?\\s+)?[A-Z][a-z]+"
  - id: "04-07-03"
    description: "Red flag score deductions via list[int] mutable reference pattern for clean function composition"
  - id: "04-07-04"
    description: "Pay ratio regex extended to 150-char window between CEO and ratio for real-world proxy text"
metrics:
  duration: "9m 29s"
  completed: "2026-02-08"
  tests-added: 12
  tests-total: 457
---

# Phase 4 Plan 07: Leadership Profiles & Compensation Analysis Summary

Leadership forensic profiles (SECT5-01/02/06) and compensation risk analysis (SECT5-05) extractors with 12 tests, all passing ruff/pyright/pytest.

## What Was Built

### leadership_profiles.py (346 lines) + leadership_parsing.py (288 lines)

Main extractor: `extract_leadership_profiles(state) -> (LeadershipStability, ExtractionReport)`

- Parses DEF 14A proxy for C-suite executives via regex title patterns (CEO, CFO, COO, CLO, CAO, CTO, CIO, President)
- Extracts departures from 8-K Item 5.02 filings, classifying PLANNED vs UNPLANNED
- Stability scoring starts at 100, deducts for 6 red flag categories:
  - Sudden CFO departure (-25)
  - CAO departure after filing season Jan-Mar (-20)
  - 3+ departures in tracking period (-30)
  - CFO + another C-suite departure (-35)
  - General Counsel/CLO departure (-25)
  - Interim officers serving (-15 to -20)
- Prior litigation search across litigation_data, web_search_results, blind_spot_results

### compensation_analysis.py (454 lines)

Main extractor: `extract_compensation(state) -> (CompensationAnalysis, ExtractionReport)`

- CEO compensation from Summary Compensation Table regex parsing
- Compensation mix percentage breakdown
- CEO pay ratio extraction (X:1 pattern)
- Say-on-pay vote percentage
- Clawback policy detection with scope (DODD_FRANK_MINIMUM vs BROADER)
- Related-party transaction extraction
- Notable perquisites detection (aircraft, gross-ups, etc.)
- Fallback to yfinance info dict for total comp if proxy parsing fails

## Tests Added (12)

Leadership (7): executive extraction from proxy, departure from 8-K, stability score full team, red flag CFO departure, red flag multiple departures, prior litigation search, no proxy text graceful

Compensation (5): say-on-pay extracted, pay ratio extracted, clawback detected, comp mix calculation, missing data graceful

## Decisions Made

1. **Split leadership module** (04-07-01): leadership_profiles.py (stability assessment + orchestration) and leadership_parsing.py (proxy/8-K text parsing helpers) to stay under 500 lines.

2. **Name regex fix** (04-07-02): Original pattern `[A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+` failed on "Robert Chen" because optional middle initial consumed the space+C. Fixed to `[A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+` with mandatory space before last name.

3. **Score mutation pattern** (04-07-03): Red flag check functions take `score: list[int]` (mutable container) to avoid returning tuples from each check. Walrus operator assigns fresh list for each check call.

4. **Pay ratio window** (04-07-04): Extended CEO-to-ratio regex window from 30 to 150 chars because real proxy text has "CEO's annual total compensation to the median..." between the keywords.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Name regex failed on common name patterns**
- Found during: Task 1 test execution
- Issue: Optional middle initial `(?:\s+[A-Z]\.?\s*)?` greedily consumed first letter of last name
- Fix: Changed to `\s+(?:[A-Z]\.?\s+)?` with mandatory spaces
- Files: leadership_parsing.py

**2. [Rule 1 - Bug] Pay ratio regex too restrictive**
- Found during: Task 2 test execution
- Issue: `ceo.{0,30}ratio` too short for real proxy text between CEO mention and ratio value
- Fix: Extended to `.{0,150}` and added `(?:approximately|was)` pattern
- Files: compensation_analysis.py

**3. [Rule 3 - Blocking] Files exceeded 500-line limit**
- Found during: Task verification
- Issue: leadership_profiles.py was 671 lines, compensation_analysis.py was 522 lines
- Fix: Split leadership into two modules; trimmed compensation docstrings
- Files: leadership_profiles.py, leadership_parsing.py, compensation_analysis.py

## Next Phase Readiness

Extractors ready for wiring into ExtractStage orchestrator when 04-09+ plans integrate Phase 4 extractors. Both return standard `(Model, ExtractionReport)` tuples compatible with existing extract pipeline pattern.
