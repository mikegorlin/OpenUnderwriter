---
phase: 4
plan: 5
subsystem: extract
tags: [insider-trading, short-interest, form4, xml-parsing, cluster-detection]
depends_on: [04-01, 04-02]
provides: [insider_trading_extractor, short_interest_extractor]
affects: [04-09, 05-score]
tech_stack:
  added: [defusedxml]
  patterns: [sliding-window-cluster-detection, multi-source-fallback]
key_files:
  created:
    - src/do_uw/stages/extract/insider_trading.py
    - src/do_uw/stages/extract/short_interest.py
    - tests/test_insider_short.py
metrics:
  duration: 11m 43s
  tests_added: 23
  completed: 2026-02-08
---

# Phase 4 Plan 5: Insider Trading & Short Interest Extractors Summary

Insider trading extractor (SECT4-04) parsing Form 4 XML with defusedxml, cluster selling detection via 30-day sliding window, 10b5-1 plan classification, yfinance fallback; short interest extractor (SECT4-05) with trend detection, peer comparison ratio, and 10 known short seller report identification.

## Tasks Completed

### Task 1: insider_trading.py extractor (498 lines)

- `parse_form4_xml()`: Parses SEC Form 4 XML using defusedxml (secure XML parsing). Extracts owner name/title, transaction date/code/shares/price, 10b5-1 plan indicator from AFF10B5ONE element.
- `detect_cluster_selling()`: Sliding window algorithm (configurable: 30 days, 3+ insiders). Deduplicates overlapping windows, computes per-cluster total value and insider list.
- `compute_aggregates()`: Total sold/bought value, NET_SELLING/NET_BUYING/NEUTRAL classification (1.5x threshold), 10b5-1 percentage of sales.
- `_extract_from_form4s()`: Iterates Form 4 filing documents, filters to 18-month lookback, sorts descending by date.
- `_extract_from_yfinance()`: Fallback with MEDIUM confidence when no Form 4 XML available. Handles multiple yfinance column name formats.
- TX_CODE_MAP: 13 SEC transaction codes mapped to human-readable types (P=BUY, S=SELL, A=GRANT, etc.)

### Task 2: short_interest.py extractor (444 lines) + tests (534 lines)

- `extract_current_short_interest()`: Extracts shortPercentOfFloat (converted from decimal to %), shortRatio (days to cover), trend from sharesShort vs sharesShortPriorMonth (+/-10% thresholds for RISING/DECLINING/STABLE).
- `compare_vs_peers()`: Ratio of company SI to peer average (>1.0 = shorted more than peers).
- `identify_short_seller_reports()`: Scans web search results for 10 known activists (Hindenburg, Muddy Waters, Citron, Spruce Point, Kerrisdale, Iceberg, Grizzly, Blue Orca, Gotham City, Bonitas).
- 23 tests: 8 insider (XML sale, 10b5-1, purchase, cluster 3+, below threshold, aggregates, yfinance fallback, missing data) + 4 short interest (SI extraction, trend rising, seller report detection, missing data) + 11 utility tests.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| defusedxml for Form 4 XML parsing | Ruff S314 security rule; SEC EDGAR is trusted but defusedxml is available and correct practice |
| Public helper functions (no underscore) | Pyright strict reportPrivateUsage rule prevents importing _-prefixed functions in tests |
| 1.5x threshold for NET_SELLING/NET_BUYING | Distinguishes clear directional bias from neutral; avoids false signals from minor imbalances |
| 10% threshold for SI trend classification | Aligns with typical short interest reporting period noise; filters out month-to-month fluctuations |
| Empty short_seller_reports still marked "found" | No reports found is a valid extraction result (searched but nothing detected), not missing data |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed duplicate XML transaction parsing**
- Found during: Task 1 test execution
- Issue: XPath `.//nonDerivativeTransaction` recursively matched elements already found by `.//nonDerivativeTable/nonDerivativeTransaction`, causing each transaction to be parsed twice
- Fix: Removed redundant table-qualified search; `.//` already matches all descendants
- Commit: facb9a8

**2. [Rule 3 - Blocking] Fixed CompanyIdentity field name**
- Found during: Task 2 pyright check
- Issue: Used `company_name` field which doesn't exist on CompanyIdentity; correct field is `legal_name`
- Fix: Changed `_get_company_name()` to use `state.company.identity.legal_name`

## Verification

- ruff check: All checks passed (0 errors)
- pyright strict: 0 errors, 0 warnings, 0 informations
- pytest: 23 passed in 0.10s
- Line counts: insider_trading.py (498), short_interest.py (444), test_insider_short.py (534)
