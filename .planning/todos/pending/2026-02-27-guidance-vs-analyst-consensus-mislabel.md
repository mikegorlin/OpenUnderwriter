---
created: 2026-02-27T21:00:00Z
title: Earnings guidance signals conflate analyst consensus with company-issued guidance
area: extract, analyze
severity: high
files:
  - src/do_uw/stages/extract/earnings_guidance.py (or wherever yfinance earnings data is processed)
  - src/do_uw/models/market.py (EarningsGuidance model)
  - src/do_uw/brain/signals/fin/ (FIN.GUIDE.* signal definitions)
  - src/do_uw/stages/analyze/check_mappers.py (FIN.GUIDE field mapping)
---

## Problem

The pipeline treats yfinance analyst consensus estimates as company-issued earnings guidance. Confirmed on SNA (Snap-on), which does NOT provide forward earnings guidance:

- `FIN.GUIDE.current = Yes` — FALSE. Snap-on doesn't guide.
- `FIN.GUIDE.philosophy = CONSERVATIVE` — meaningless when there's no guidance.
- `FIN.GUIDE.track_record = 0.7917` — this is analyst estimate beat rate, not guidance accuracy.
- `FIN.GUIDE.earnings_reaction = 7.49` (TRIGGERED) — max earnings day stock move, unrelated to guidance.

Source: `yfinance earnings_dates` provides `guidance_eps_low/high` fields that are actually analyst consensus estimates, not company guidance. The field names in yfinance are misleading.

## Why This Matters for D&O

Company-issued guidance vs. analyst estimates have fundamentally different D&O risk profiles:
- **Company guides and misses**: High SCA risk (material misstatement theory). The company made a forward-looking statement that proved wrong.
- **Company doesn't guide, analysts miss**: Low SCA risk. Analysts got it wrong, but the company didn't make the statement.
- **Company guides conservatively and beats**: Low risk. Under-promise, over-deliver.

Conflating these overstates guidance risk for non-guiding companies and understates it for companies that actively guide.

## Solution

1. **Distinguish guidance from consensus**: Add a boolean field `provides_forward_guidance` to the model. Determine this from:
   - LLM extraction from 10-K MD&A / earnings call transcripts (does management provide specific EPS/revenue outlook?)
   - If no explicit guidance language found, set `provides_forward_guidance = False`

2. **Relabel existing data**: Rename `guidance_eps_low/high` from yfinance to `consensus_eps_low/high` in the data model to avoid confusion.

3. **Conditional signal evaluation**: FIN.GUIDE.* signals should check `provides_forward_guidance` first:
   - If False: FIN.GUIDE.current = "No", FIN.GUIDE.philosophy = "N/A", FIN.GUIDE.track_record = INFO (show beat rate as analyst consensus, not guidance)
   - If True: Current behavior (evaluate guidance accuracy, philosophy, track record)

4. **Display**: Worksheet should clearly label whether data is "Company Guidance" vs "Analyst Consensus Estimates"

### Validation
- SNA: FIN.GUIDE.current should be "No" or "N/A"
- Companies known to guide (e.g., AAPL provides revenue guidance): should show as guiding
- Track record table should label source correctly
