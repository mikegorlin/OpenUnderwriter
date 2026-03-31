---
phase: 03-company-profile-financial-extraction
plan: 05
subsystem: extract
tags: [debt-analysis, liquidity, leverage, refinancing, financial-ratios]
depends_on:
  requires: ["03-03"]
  provides: ["liquidity-ratios", "leverage-ratios", "debt-structure", "refinancing-risk"]
  affects: ["04", "05", "07"]
tech_stack:
  added: []
  patterns: ["ratio-computation-from-typed-statements", "text-based-filing-extraction", "cascading-debt-derivation"]
files:
  created:
    - src/do_uw/stages/extract/debt_analysis.py
    - src/do_uw/stages/extract/debt_text_parsing.py
    - tests/test_debt_analysis.py
  modified: []
decisions:
  - id: "03-05-01"
    decision: "Split debt_analysis.py into ratio module (469L) and text parsing module (392L) to stay under 500-line limit"
    rationale: "Combined module was 818 lines. Logical split: numeric ratios vs text-based extraction."
  - id: "03-05-02"
    decision: "Total debt fallback: LTD + STD when total_debt XBRL concept not available"
    rationale: "Many companies report long-term and short-term debt separately rather than a combined total_debt concept."
  - id: "03-05-03"
    decision: "Zero interest expense treated as 'No debt service' flag rather than division error"
    rationale: "Companies with no debt have zero interest expense. This is informative, not an error."
  - id: "03-05-04"
    decision: "Refinancing risk depends on debt_structure; returns None with reason when debt structure unavailable"
    rationale: "Cannot assess refinancing risk without maturity schedule data. Honest 'Not Available' with dependency reason."
metrics:
  duration: "6m 39s"
  completed: "2026-02-08"
  tests_added: 15
  tests_total: 205
  lines_added: 1377
---

# Phase 3 Plan 5: Debt Analysis Summary

Liquidity/leverage ratios from XBRL balance sheet + income statement, text-based debt structure parsing from 10-K Item 7, refinancing risk derivation from maturity schedule vs available resources.

## What Was Built

### 1. Liquidity Assessment (SECT3-08) -- `debt_analysis.py`
- Current Ratio = Current Assets / Current Liabilities
- Quick Ratio = (Current Assets - Inventory) / Current Liabilities
- Cash Ratio = Cash / Current Liabilities
- Working Capital = Current Assets - Current Liabilities
- Days Cash on Hand = Cash / (Operating Expenses / 365)
- Source: Derived from XBRL balance sheet, HIGH confidence

### 2. Leverage Assessment (SECT3-09) -- `debt_analysis.py`
- Debt-to-Equity = Total Debt / Stockholders' Equity
- Debt-to-EBITDA = Total Debt / (Operating Income + D&A)
- Interest Coverage = EBIT / Interest Expense
- Debt-to-Assets = Total Debt / Total Assets
- Net Debt = Total Debt - Cash
- Warning flags: D/EBITDA > 4.0, Interest Coverage < 2.0, D/E > 3.0
- Total debt fallback: long_term_debt + short_term_debt when composite concept missing

### 3. Debt Structure (SECT3-10) -- `debt_text_parsing.py`
- Maturity schedule: Regex extraction of "$X due/maturing YYYY" patterns
- Interest rates: Fixed rate percentages + floating rate references (SOFR/LIBOR)
- Covenants: Financial/debt covenant mention detection
- Credit facility: Revolving credit/credit agreement amount parsing
- Source: Text extraction from 10-K Item 7, MEDIUM confidence

### 4. Refinancing Risk (SECT3-11) -- `debt_text_parsing.py`
- Near-term maturities: Sum of debt maturing within 2 years
- Maturity wall: Largest single-year maturity
- Coverage ratio: Available resources / near-term maturities
- Risk classification: LOW / MEDIUM / HIGH / CRITICAL
- Dependency chain: requires debt_structure -> maturity_schedule

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] File split to comply with 500-line limit**
- **Found during:** Task 1 verification
- **Issue:** Combined debt_analysis.py was 818 lines, exceeding 500-line anti-context-rot rule
- **Fix:** Split into debt_analysis.py (469L, ratio computations) and debt_text_parsing.py (392L, text parsing + refinancing)
- **Files created:** `src/do_uw/stages/extract/debt_text_parsing.py`
- **Commits:** 52a4814

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 03-05-01 | Split into debt_analysis.py + debt_text_parsing.py | 500-line limit, logical separation of numeric vs text extraction |
| 03-05-02 | Total debt fallback: LTD + STD | Many companies lack composite total_debt XBRL concept |
| 03-05-03 | Zero interest = "No debt service" flag | Informative signal for debt-free companies |
| 03-05-04 | Refinancing risk None when debt_structure unavailable | Honest dependency declaration, never fabricate |

## Test Coverage

15 tests covering:
- Liquidity ratios: current (2.5), quick (2.0), cash (0.75), missing inputs
- Leverage ratios: D/E (0.75), D/EBITDA (2.5), interest coverage (3.33)
- Edge cases: zero interest expense, high leverage flags (D/EBITDA > 4.0)
- Refinancing: maturity-based HIGH risk, not-available when missing
- Coverage reporting: all ratios -> HIGH coverage
- No-imputation: missing data -> None values

## Next Phase Readiness

- Liquidity and leverage ratios feed into SCORE stage (Factor F1: Financial Health)
- Debt structure feeds into covenant violation risk analysis
- Refinancing risk feeds into distress probability assessment
- All metrics carry source traceability for audit trail
