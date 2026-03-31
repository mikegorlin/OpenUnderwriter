---
phase: 71-form4-enhancement
plan: 01
subsystem: insider-trading-extraction
tags: [form4, insider-trading, ownership, dedup, brain-signal]
dependency_graph:
  requires: []
  provides: [InsiderTransaction-v2, OwnershipConcentrationAlert, dedup-logic, ownership-trajectory]
  affects: [insider_trading.py, market_events.py, signal_field_routing.py, governance-facet]
tech_stack:
  added: []
  patterns: [file-split-for-500-line-compliance, tiered-severity-alerts, dedup-prefer-amendment]
key_files:
  created:
    - src/do_uw/stages/extract/insider_trading_analysis.py
    - src/do_uw/stages/extract/insider_trading_yfinance.py
    - tests/test_insider_form4_enhancements.py
  modified:
    - src/do_uw/models/market_events.py
    - src/do_uw/stages/extract/insider_trading.py
    - src/do_uw/stages/acquire/clients/sec_client_filing.py
    - src/do_uw/brain/signals/gov/insider.yaml
    - src/do_uw/brain/sections/governance.yaml
    - src/do_uw/brain/enrichment_data.py
    - src/do_uw/stages/analyze/signal_field_routing.py
decisions:
  - Split yfinance fallback to insider_trading_yfinance.py for 500-line compliance
  - Split dedup + concentration analysis to insider_trading_analysis.py
  - market_events.py at 556 lines (acceptable -- purely declarative Pydantic models)
  - C-suite pattern detection via regex on title field
metrics:
  duration_seconds: 572
  completed: "2026-03-06T21:53:29Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 25
  tests_total: 48
  files_created: 3
  files_modified: 8
---

# Phase 71 Plan 01: Form 4 Parser Enhancement Summary

Extended Form 4 parser with post-transaction ownership tracking, relationship flags, 4/A amendment dedup, gift/estate filtering, and tiered ownership concentration alerts wired to brain signal GOV.INSIDER.ownership_concentration.

## Tasks Completed

| Task | Name | Commit | Key Changes |
|------|------|--------|-------------|
| 1 | Extend InsiderTransaction model + parser with new fields, dedup, and gift filtering | 30d0922 | 9 new model fields, XML extraction, dedup logic, G/W/A/F filtering, 4/A variant |
| 2 | Ownership concentration analysis with tiered alerts and brain signal | ba2b0a9 + 29dd465 | compute_ownership_concentration, OwnershipConcentrationAlert model, brain signal + facet wiring |

## What Was Built

### Model Extensions (market_events.py)
- **InsiderTransaction**: 9 new fields -- shares_owned_following, is_director, is_officer, is_ten_pct_owner, ownership_nature, indirect_ownership_explanation, accession_number, is_amendment, is_superseded
- **OwnershipConcentrationAlert**: Tiered alert model with severity (RED_FLAG/WARNING/INFORMATIONAL/POSITIVE), personal_pct_sold, is_c_suite, compounds_with_cluster
- **OwnershipTrajectoryPoint**: Timeline point for ownership trajectory tracking
- **InsiderTradingAnalysis**: New fields -- ownership_alerts, ownership_trajectories, insider_purchases

### Parser Enhancement (insider_trading.py)
- parse_form4_xml now accepts accession_number and is_amendment parameters
- Extracts postTransactionAmounts/sharesOwnedFollowingTransaction for both derivative and non-derivative
- Extracts reportingOwnerRelationship flags (isDirector, isOfficer, isTenPercentOwner) at document level
- Extracts ownershipNature (D/I) and indirect explanation

### Deduplication (insider_trading_analysis.py)
- _deduplicate_transactions groups by (insider_name, date, code) tuple
- 4/A amendments preferred; originals marked is_superseded=True but retained

### Aggregation Filtering (insider_trading.py)
- EXCLUDED_CODES {G, W}: gifts/estate excluded from buy/sell totals
- COMPENSATION_CODES {A, F}: RSU vesting + tax withholding excluded entirely

### Ownership Concentration (insider_trading_analysis.py)
- C-suite >50% sold in 6mo = RED_FLAG; >25% = WARNING
- 10b5-1 plan reduces severity by one level
- Directors/10% holders capped at INFORMATIONAL
- Cluster overlap compounds severity upward
- Open-market purchases tracked as POSITIVE signal

### Acquisition (sec_client_filing.py)
- Added "4": ["4", "4/A"] to _FORM_TYPE_VARIANTS

### Brain Signal
- GOV.INSIDER.ownership_concentration: tiered signal wired to governance facet
- Signal routing: ownership_concentration_severity field_key
- Subsection mapping: 2.8 (insider trading)
- Peril mapping: HAZ-SCA, HAZ-SEC

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] File split for 500-line compliance**
- **Found during:** Task 1
- **Issue:** insider_trading.py was at 498 lines before changes; adding new code pushed it over 500
- **Fix:** Split yfinance fallback to insider_trading_yfinance.py (131 lines), analysis functions to insider_trading_analysis.py (258 lines). Main file now 464 lines.
- **Files created:** insider_trading_yfinance.py, insider_trading_analysis.py

**2. [Rule 1 - Bug] Brain contract test failure -- signal not in facet**
- **Found during:** Task 2 verification
- **Issue:** New signal GOV.INSIDER.ownership_concentration not registered in governance.yaml facet or enrichment_data.py
- **Fix:** Added signal to governance.yaml section list and both enrichment_data.py mappings (subsection + peril)
- **Commit:** 29dd465

## Verification

- 25 new tests + 23 existing insider tests = 48 passing
- Full test suite: 594 passed, 1 pre-existing failure (test_enriched_roundtrip -- unrelated SignalDefinition schema issue)
- All modified files under 500 lines (except market_events.py at 556 -- declarative models only)

## Self-Check: PASSED
