---
phase: 21-multi-ticker-validation
plan: 03
subsystem: ground-truth
tags: [testing, ground-truth, validation, multi-ticker]
depends_on:
  requires: [20-06]
  provides: [ground-truth-10-companies, multi-ticker-coverage]
  affects: [21-04, 21-05, 21-06]
tech-stack:
  added: []
  patterns: [parametrized-ground-truth, known-outcome-companies]
key-files:
  created:
    - tests/ground_truth/nvda.py
    - tests/ground_truth/mrna.py
    - tests/ground_truth/xom.py
    - tests/ground_truth/pg.py
    - tests/ground_truth/dis.py
    - tests/ground_truth/smci.py
    - tests/ground_truth/coin.py
  modified:
    - tests/ground_truth/__init__.py
    - tests/test_ground_truth_validation.py
    - tests/test_ground_truth_coverage.py
decisions:
  - Sector codes verified against actual sic_to_sector() mapping (ENGY not ENRG, UTIL not TELE)
  - MRNA altman_z_zone set to GREY (net losses despite cash reserves)
  - SMCI auditor set to BDO (EY resigned Oct 2024)
  - Known-outcome companies given higher employee_count_tolerance (0.25)
metrics:
  duration: 4m 28s
  completed: 2026-02-11
---

# Phase 21 Plan 03: Ground Truth Expansion Summary

Expanded ground truth fixtures from 3 companies (TSLA, AAPL, JPM) to 10 companies covering 5 industry verticals plus 2 known-outcome companies, with all tests parametrized across the full set.

## Task Results

### Task 1: Create 7 new ground truth files
**Commit:** `4df4285`

Created 7 ground truth files (766 lines total), each with 13 categories following the exact tsla.py format:

| Ticker | Company | SIC | Sector | Notable |
|--------|---------|-----|--------|---------|
| NVDA | NVIDIA | 3674 | TECH | MEGA cap, Jensen Huang, PwC auditor |
| MRNA | Moderna | 2836 | HLTH | Post-COVID revenue decline, GREY distress |
| XOM | Exxon Mobil | 1311 | ENGY | MEGA cap, climate litigation, PwC auditor |
| PG | Procter & Gamble | 2840 | HLTH | MEGA cap, Walmart concentration, Deloitte |
| DIS | Walt Disney | 4841 | UTIL | Bob Iger CEO, fiscal year ends Sep |
| SMCI | Super Micro | 3571 | TECH | Known-outcome: material weakness, BDO auditor |
| COIN | Coinbase | 6199 | FINS | Known-outcome: SEC enforcement, dual-class |

### Task 2: Update registry and parametrize tests
**Commit:** `739a35a`

- `__init__.py`: Registry expanded to 10 entries with all imports
- `test_ground_truth_validation.py`: `TICKERS = list(ALL_GROUND_TRUTH.keys())` -- 140 tests (was 42)
- `test_ground_truth_coverage.py`: `COVERAGE_TICKERS = [t for t in ALL_GROUND_TRUTH if t != "JPM"]` -- 135 tests (was 30)

## Verification Results

- **Full test suite:** 2373 passed, 217 skipped, 11 xfailed, 0 failures
- **Pyright:** 0 errors, 0 warnings
- **Ruff:** All checks passed
- **All files under 500 lines**

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected sector codes to match actual codebase mapping**
- **Issue:** Plan specified ENRG and TELE sector codes, but actual `sic_to_sector()` in `sec_identity.py` uses ENGY (SIC 10-14) and UTIL (SIC 48-49)
- **Fix:** Used correct sector codes: XOM -> ENGY, DIS -> UTIL
- **Files:** tests/ground_truth/xom.py, tests/ground_truth/dis.py

## Next Phase Readiness

Ground truth is ready for validation runs. Plans 21-04 through 21-06 can now validate extraction accuracy across all 10 companies.
