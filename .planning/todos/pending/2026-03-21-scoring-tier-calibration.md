---
created: 2026-03-21T13:15:42.142Z
title: Scoring tier calibration
area: score
files:
  - src/do_uw/stages/score/ten_factor.py
  - src/do_uw/stages/score/tier_assignment.py
  - src/do_uw/config/scoring_weights.json
---

## Problem

AAPL (mega-cap, Altman Z-Score 9.93, $3.6T market cap, strong financials) and ANGI (distressed micro-cap, Altman Z-Score 0.98, $0.3B market cap, 73.7% stock decline) both score WALK tier. The tier system is not differentiating healthy companies from distressed ones.

Scores: AAPL 88.0 WALK, ANGI 85.3 WALK, HNGE 85.9 WATCH — all compressed into a narrow band despite radically different risk profiles.

User flagged this during Phase 120 visual review: "AAPL is walk? ANGI is a walk? really miscalibrated"

## Solution

Recalibrate tier thresholds and/or scoring factor weights so that:
- Distressed companies (Altman < 1.8, >50% stock decline) cannot score above COMPETE
- Mega-cap clean companies with strong financials should score WIN or near-WIN
- The full WIN/WALK/WATCH/COMPETE/DECLINE spectrum should be used, not just WALK/WATCH

Possible approaches:
1. Widen tier breakpoints (currently too compressed)
2. Increase weight of financial health factors (Altman, D/E, going concern)
3. Add market-cap-relative scaling to DDL/settlement calculations
4. Red flag gates should enforce harder ceilings (CRF gates may not be biting)

Target: Next milestone (v9.0 or equivalent)
