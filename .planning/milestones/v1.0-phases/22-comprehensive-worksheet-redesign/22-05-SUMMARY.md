# Phase 22 Plan 05: Redesign Sections 6 & 7 (Litigation + Scoring) Summary

**One-liner:** Litigation section redesigned with defense split and full SCA details; scoring section redesigned with detail split, tier box, and red flag gates.

## Completed Tasks

| Task | Name | Commit | Duration |
|------|------|--------|----------|
| 1 | Redesign Section 6 Litigation with defense split | 67ce877 | ~5m |
| 2 | Redesign Section 7 Scoring with detail split | 3b2758b | ~4m |

## Changes Made

### Task 1: Section 6 Litigation Redesign

**sect6_litigation.py** (420 lines) - Main entry + narrative + SCA + enforcement:
- Added litigation_narrative() lead from md_narrative_sections
- SCA table expanded: court, class period (with date range formatter), lead counsel tier, source citation
- SEC enforcement pipeline with visual [confirmed]/(suspected) stage markers
- Industry sweep detection added
- Delegates to render_litigation_details() and render_defense_assessment()

**sect6_timeline.py** (256 lines) - Derivative + regulatory + patterns + SOL:
- Slimmed by moving defense, contingencies, whistleblower to sect6_defense
- Uses sv_val() from v2 formatters for consistent data access
- Retained: derivative suits, regulatory proceedings, industry claim patterns, SOL map

**sect6_defense.py** (301 lines) - NEW file: defense + contingencies + whistleblower:
- Defense strength assessment table: forum provisions (FFP/EFP with details), PSLRA safe harbor, judge track record, truth-on-market, prior dismissal success
- Contingent liabilities table with ASC 450 classification, accrued amounts, ranges
- Whistleblower indicators table with type, date, significance
- D&O context annotations for weak defense, probable contingencies, high-significance whistleblower

### Task 2: Section 7 Scoring Redesign

**sect7_scoring.py** (452 lines) - Main entry + narrative + tier + breakdown + radar + red flags:
- Added scoring_narrative() lead from md_narrative_sections
- Tier classification box: quality score, composite (pre-ceiling), tier, range, action, probability, pricing multiplier, binding ceiling
- Composite score breakdown: 10 factors with max pts, deducted, % used, top contributor
- Red flag gates: all CRF gates (triggered AND non-triggered) with evidence, ceiling, max tier
- Risk type classification, severity scenarios, calibration notes retained
- Delegates to render_scoring_detail()

**sect7_scoring_detail.py** (326 lines) - NEW file: factor detail + patterns + allegation + claim prob + tower:
- Per-factor detail tables: rules triggered, evidence, sub-component breakdowns
- Pattern detection results: triggers matched, score impact, D&O context for HIGH/SEVERE
- Allegation theory mapping: theory-to-evidence mapping with exposure levels
- Claim probability detail: band, range, industry base rate, adjustment rationale
- Tower position recommendation: recommended position, minimum attachment, per-layer assessments

### Test Updates

- Updated TestRenderSection6 assertion from "Defense Assessment" to "Defense Strength Assessment"
- Updated TestLitigationDetails to check derivative, regulatory, patterns, SOL (not contingencies)
- Added TestDefenseAssessment class (2 tests: with data, None litigation)
- Updated TestRenderSection7 assertions for new headings
- Added TestScoringDetail class (2 tests: with data, None scoring)
- Added ClaimProbability and TowerRecommendation to test fixtures

## Verification Results

- **Tests:** 14/14 sect6+sect7 tests passing (6 sect5 tests affected by parallel agent's changes to sect5_governance.py -- not in scope)
- **Pyright:** 0 errors, 0 warnings on all 5 files
- **Line counts:** 420, 256, 301, 452, 326 (all under 500)
- **Signatures:** render_section_6(doc, state, ds) and render_section_7(doc, state, ds) unchanged

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test assertion mismatch after heading rename**
- **Found during:** Task 1 verification
- **Issue:** Test checked for "Defense Assessment" but heading renamed to "Defense Strength Assessment"
- **Fix:** Updated test assertion
- **Files modified:** tests/test_render_sections_5_7.py
- **Commit:** 67ce877

**2. [Rule 1 - Bug] Test assertion mismatch after contingencies moved**
- **Found during:** Task 1 verification
- **Issue:** TestLitigationDetails expected "Contingent Liabilities" but that moved to sect6_defense
- **Fix:** Updated test to check derivative/regulatory/patterns/SOL, added TestDefenseAssessment
- **Files modified:** tests/test_render_sections_5_7.py
- **Commit:** 67ce877

**3. [Rule 3 - Blocking] sect6_defense.py stub existed from parallel agent**
- **Found during:** Task 1
- **Issue:** Another parallel agent created a stub file for sect6_defense.py to prevent import errors
- **Fix:** Replaced stub with full implementation
- **Files modified:** src/do_uw/stages/render/sections/sect6_defense.py
- **Commit:** 67ce877

## Key Files

### Created
- `src/do_uw/stages/render/sections/sect6_defense.py`
- `src/do_uw/stages/render/sections/sect7_scoring_detail.py`

### Modified
- `src/do_uw/stages/render/sections/sect6_litigation.py`
- `src/do_uw/stages/render/sections/sect6_timeline.py`
- `src/do_uw/stages/render/sections/sect7_scoring.py`
- `tests/test_render_sections_5_7.py`

## Metrics

- **Duration:** 9m 05s
- **Completed:** 2026-02-11
- **Tests added:** 4 (TestDefenseAssessment x2, TestScoringDetail x2)
- **Total tests in file:** 22 (was 16, now 22)
