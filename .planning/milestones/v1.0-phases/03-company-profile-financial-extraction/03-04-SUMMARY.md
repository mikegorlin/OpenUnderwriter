# Phase 3 Plan 4: Distress Models & Earnings Quality Summary

**One-liner:** Four academic distress models (Altman Z, Beneish M, Ohlson O, Piotroski F) with sector-routed variants, earnings quality forensics, and 20 tests verifying formulas against hand-calculated values.

## Metadata

- **Phase:** 03-company-profile-financial-extraction
- **Plan:** 04
- **Duration:** ~9m
- **Completed:** 2026-02-08
- **Tests added:** 20 (225 total, 0 regressions)

## What Was Built

### distress_models.py (492 lines) + distress_formulas.py (499 lines)

Main function: `compute_distress_indicators(statements, sector, market_cap)` returns `(DistressIndicators, list[ExtractionReport])`.

**Altman Z-Score** with 3 variants:
- Original 5-factor for manufacturing: `Z = 1.2*(WC/TA) + 1.4*(RE/TA) + 3.3*(EBIT/TA) + 0.6*(MktCap/TL) + 1.0*(Sales/TA)`
- Z''-Score for FINS/REIT/INSUR: `Z'' = 6.56*(WC/TA) + 3.26*(RE/TA) + 6.72*(EBIT/TA) + 1.05*(Equity/TL)`
- Early-stage for pre-revenue: cash runway, burn rate, cash-to-debt ratio

**Beneish M-Score** 8-variable: DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI with published coefficients. >-1.78 = manipulation likely.

**Ohlson O-Score** with logistic transformation to bankruptcy probability. GDP deflator constant ~130.

**Piotroski F-Score** 9 binary criteria across profitability (4), leverage (3), efficiency (2). Each criterion individually trackable.

**Trajectory support:** Altman Z computed across all available annual periods for trend visualization.

### earnings_quality.py (383 lines)

Main function: `compute_earnings_quality(statements)` returns `(SourcedValue[dict] | None, ExtractionReport)`.

Six forensic ratios:
1. Accruals ratio: (NI - OCF) / TA (flag >0.10)
2. OCF/NI ratio: healthy 0.8-1.5, poor <0.5
3. DSO trend: increasing DSO = possible channel stuffing
4. Asset quality: non-current asset growth vs revenue growth
5. Cash flow adequacy: OCF / (CapEx + Dividends) (flag <1.0)
6. Quality score summary: STRONG/ADEQUATE/WEAK/RED_FLAG

### test_distress_earnings.py (674 lines, 20 tests)

- 5 Altman Z tests: SAFE zone, DISTRESS zone, Z'' for financials, early-stage pre-revenue, div-by-zero
- 3 Beneish M tests: manipulation detection, clean company, partial inputs
- 2 Ohlson O tests: high probability, probability in [0,1] range
- 3 Piotroski F tests: all 9 criteria met (score=9), weak (score<=2), individual criteria tracking
- 1 trajectory test: multi-period trajectory generation
- 6 earnings quality tests: normal accruals, red flag accruals, healthy OCF/NI, DSO trend, missing inputs, quality score summary

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Split distress code into 2 files (models + formulas) | Single file was 1011 lines; split keeps both under 500 |
| Zone classifiers and safe_ratio public in distress_formulas.py | Reusable by distress_models.py and tests |
| GDP deflator constant (130.0) for Ohlson O-Score | Affects absolute score but not relative ranking; simplification documented |
| QualityScore as StrEnum with numeric mapping in dict | Dict values must be float|None; quality stored as 0.0-3.0 |
| >50% threshold for partial score computation | Below 50% inputs = score is None, above = compute with available |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] File too large for 500-line limit**
- **Found during:** Task 1
- **Issue:** Single distress_models.py was 1011 lines
- **Fix:** Split into distress_models.py (Altman Z + orchestration) and distress_formulas.py (Beneish/Ohlson/Piotroski + zone helpers)
- **Files created:** `distress_formulas.py` (not in original plan)
- **Commit:** 1201afa

**2. [Rule 1 - Bug] Ruff lint errors in earnings_quality.py**
- **Found during:** Task 2 verification
- **Issue:** `reversed(sorted(...))` flagged as C413; `assert` statements flagged as S101
- **Fix:** Used `sorted(..., reverse=True)` and explicit `if` narrowing instead of `assert`
- **Files modified:** `earnings_quality.py`
- **Commit:** 6dbf0d3

## Key Files

| File | Lines | Role |
|------|-------|------|
| `src/do_uw/stages/extract/distress_models.py` | 492 | Main entry point, Altman Z variants, trajectory, orchestration |
| `src/do_uw/stages/extract/distress_formulas.py` | 499 | Beneish M, Ohlson O, Piotroski F formulas and zone classifiers |
| `src/do_uw/stages/extract/earnings_quality.py` | 383 | Earnings quality forensic ratios |
| `tests/test_distress_earnings.py` | 674 | 20 tests covering all models + earnings quality |

## Commits

| Hash | Message |
|------|---------|
| 1201afa | feat(03-04): distress model computations with sector awareness |
| 6dbf0d3 | feat(03-04): earnings quality analysis and 20 tests for distress+earnings |
