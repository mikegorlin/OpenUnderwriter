---
phase: 15-scoring-calibration-validation
plan: 01
subsystem: scoring
tags: [calibration, audit, scoring, config, sectors, governance]
completed: 2026-02-10
duration: 8m
dependency_graph:
  requires: [06-scoring-engine, 09-knowledge-store, 12-actuarial-pricing]
  provides: [calibrated-scoring-config, audit-documentation]
  affects: [15-02-pipeline-validation]
tech_stack:
  added: []
  patterns: [config-audit-document, before-after-calibration]
key_files:
  created:
    - docs/scoring-calibration-audit.md
  modified:
    - src/do_uw/brain/sectors.json
    - src/do_uw/config/governance_weights.json
decisions:
  - "Claim base rates calibrated downward 0.4-1.0pp based on Cornerstone/NERA/Stanford SCAC data"
  - "Leverage distress thresholds differentiated from critical (~25-30% above) across 11 sectors"
  - "Small-cap filing multiplier increased from 0.90x to 0.95x"
  - "Governance weights rebalanced: say_on_pay 0.15->0.12, refreshment 0.10->0.13"
  - "scoring.json and red_flags.json left unchanged -- weights and gates are well-calibrated"
  - "Tier boundaries preserved (no changes to score ranges or probability bands)"
metrics:
  tests_before: 1845
  tests_after: 1845
  audit_doc_lines: 823
---

# Phase 15 Plan 01: Scoring Calibration Audit Summary

Comprehensive audit of all scoring configuration parameters against D&O industry research with calibrated claim base rates and differentiated leverage distress thresholds.

## What Was Done

### Task 1: Scoring Calibration Audit Document (4d831fe)

Created 823-line audit document at `docs/scoring-calibration-audit.md` covering:

1. **Factor Weight Audit (10 factors):** Each factor assessed against NERA, Cornerstone Research, Stanford SCAC, and academic literature. All 10 factor weights (F1-F10) found to be well-calibrated. Historical lift values validated. Decay curves, threshold bands, and pattern modifiers reviewed.

2. **Tier Boundary Audit (6 tiers):** WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH boundaries produce appropriate distribution. WRITE tier's 20-point span correctly creates the "fat middle." Probability ranges slightly conservative (appropriate for underwriting tool).

3. **Red Flag Gate Audit (11 CRFs):** All 11 gates found appropriately calibrated. CRF-01 (Active SCA) at WALK ceiling is correct for new-business context. No missing critical red flags identified (4 potential additions rated LOW/MEDIUM priority).

4. **Governance Weights Audit (7 dimensions):** Weights broadly appropriate. Found say_on_pay (0.15) slightly overweighted relative to its D&O litigation correlation.

5. **Sector Baselines Audit:** Short interest, volatility, and leverage baselines all well-calibrated. Two HIGH priority issues found: claim_base_rates needed calibration (marked "NEEDS CALIBRATION"), and leverage distress thresholds were identical to critical thresholds in 11 sectors.

6. **Calibration Recommendations:** 13 HIGH, 3 MEDIUM, 3 LOW priority recommendations produced.

### Task 2: Apply HIGH Priority Calibrations (d37a070)

Applied 13 HIGH priority changes:

- **Claim base rates (sectors.json):** Reduced 9 of 11 sector rates by 0.4-1.0 percentage points. Biotech: 8.0%->7.0%, Tech: 6.0%->5.0%, HLTH: 4.5%->4.0%, etc. Removed "NEEDS CALIBRATION" flag.
- **Leverage distress thresholds (sectors.json):** Set distress ~25-30% above critical for all 11 sectors where they were previously equal. Example: TECH distress 4.0x->6.0x.
- **Small-cap filing multiplier (sectors.json):** 0.90x->0.95x to reflect slightly elevated per-company risk.
- **Governance weights (governance_weights.json):** Rebalanced say_on_pay 0.15->0.12, refreshment 0.10->0.13.
- **No changes to:** scoring.json (factor weights, max_points, tier boundaries all appropriate), red_flags.json (all 11 CRF gates well-calibrated).

All 1845 tests pass after changes.

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Claim base rates reduced conservatively (0.4-1.0pp) | Move to center of defensible ranges without overcorrecting |
| Leverage distress set ~25-30% above critical | Distress = imminent covenant/default risk, needs meaningful separation |
| scoring.json left unchanged | Factor weights, max_points (total=100), and tier boundaries are all defensible |
| red_flags.json left unchanged | All 11 CRF gates at appropriate ceiling levels |
| say_on_pay reduced, refreshment increased | Refreshment has stronger oversight signal than advisory pay vote |

## Key Artifacts

- `docs/scoring-calibration-audit.md` -- 823-line comprehensive audit with industry research citations
- `src/do_uw/brain/sectors.json` -- Calibrated claim rates, distress thresholds, filing multipliers
- `src/do_uw/config/governance_weights.json` -- Rebalanced dimension weights

## Next Phase Readiness

Plan 15-02 (pipeline validation) can proceed. The calibration changes affect:
- Actuarial expected loss calculations (lower claim base rates)
- Financial distress scoring (more granular distress tier)
- Governance quality scoring (slight dimension rebalancing)
- No changes to factor weights, tier boundaries, or CRF gates
