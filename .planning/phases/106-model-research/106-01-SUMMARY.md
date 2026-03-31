---
phase: 106-model-research
plan: 01
subsystem: brain-framework
tags: [scoring-model, severity-model, multiplicative, hae, damages, settlement, amplifiers, yaml-design]

requires:
  - phase: 102-rap-taxonomy
    provides: "H/A/E taxonomy with 20 subcategories, 514 signals"
  - phase: 103-schema-foundation
    provides: "SeverityAmplifier, PatternDefinition Pydantic schemas, epistemology, evaluation.mechanism"
provides:
  - "Multiplicative scoring model design (P = H x A x E) with composite computation, weights, CRF discordance, tier mapping, shadow calibration"
  - "Severity estimation model design with damages formula, settlement regression, 11 amplifiers, P x S matrix, Liberty adjustments"
affects: [107-scoring-implementation, 108-severity-implementation, 112-worksheet-render]

tech-stack:
  added: []
  patterns:
    - "YAML design artifact pattern: comprehensive algorithm spec as YAML, not code"
    - "Research-cited weighting: every weight has a weight_source field with citation"
    - "calibration_required flag: marks values needing empirical validation"

key-files:
  created:
    - src/do_uw/brain/framework/scoring_model_design.yaml
    - src/do_uw/brain/framework/severity_model_design.yaml
  modified: []

key-decisions:
  - "Multiplicative P = H x A x E with 0.05 floor per composite to prevent single-dimension domination"
  - "Dual-path tier assignment: both composite P score AND individual dimension criteria, most restrictive wins"
  - "6 CRF veto categories with ELECTRE III discordance mechanism (CRF-FRAUD=PROHIBITED, CRF-RESTATEMENT=ELEVATED, etc.)"
  - "Liberty calibration: attachment-dependent weight multipliers (host +30% at high attachment) and product-dependent (agent +25% for Side A)"
  - "Settlement regression: 12 features with log-linear model, fallback to Cornerstone lookup table if <50 training cases"
  - "11 severity amplifiers conforming to SeverityAmplifier Pydantic schema with multipliers 1.2x-2.0x"
  - "P x S matrix with 4 color-coded zones (GREEN/YELLOW/ORANGE/RED) and log-scale severity axis"
  - "Liberty excess-only severity via layer erosion probability (log-normal settlement distribution model)"

patterns-established:
  - "Design artifact convention: YAML files in brain/framework/ serve as implementation blueprints with status: design_artifact and implementation_phase: NNN"
  - "Research citation pattern: weight_source and epistemology.rule_origin cite real sources (SCAC, Cornerstone, NERA, ISS, Beneish, Altman)"

requirements-completed: [SCORE-01-design, SCORE-02-design, SCORE-03-design, SCORE-04-design, SCORE-05-design, SEV-01-design, SEV-02-design, SEV-03-design, SEV-04-design, SEV-05-design]

duration: 7min
completed: 2026-03-15
---

# Phase 106 Plan 01: Scoring + Severity Model Design Summary

**Multiplicative scoring model (P = H x A x E) with 20 weighted subcategories and severity model with damages estimation, 12-feature settlement regression, 11 amplifiers, and P x S expected loss matrix**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-15T04:44:14Z
- **Completed:** 2026-03-15T04:57:45Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments
- Scoring model with H/A/E composite computation, research-cited subcategory weights, multiplicative interaction with floor adjustment, CRF ELECTRE discordance, dual-path tier mapping, Liberty calibration, and shadow calibration spec
- Severity model with damages estimation (market_cap x class_period_return x turnover_rate), 6 allegation type modifiers, 12-feature settlement regression, 11 severity amplifiers with epistemology, P x S matrix with zone definitions, and Liberty excess-only adjustments

## Task Commits

1. **Task 1: Multiplicative scoring model design** - `09b0d7e` (feat)
2. **Task 2: Severity estimation model design** - `bc87d32` (feat)

## Files Created/Modified
- `src/do_uw/brain/framework/scoring_model_design.yaml` - 803-line design: composites, weights, P=HxAxE, CRF discordance, tier mapping, shadow calibration
- `src/do_uw/brain/framework/severity_model_design.yaml` - 789-line design: damages formula, regression features, amplifier catalog, P x S matrix, Liberty adjustments

## Decisions Made
- See key-decisions in frontmatter above

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed YAML parsing errors in severity_model_design.yaml**
- **Found during:** Task 2 (Severity model design)
- **Issue:** List items mixed with mapping keys at same indentation level caused YAML parser error
- **Fix:** Wrapped zone entries and attachment tier examples in nested `entries` keys
- **Files modified:** src/do_uw/brain/framework/severity_model_design.yaml
- **Verification:** YAML loads successfully after fix
- **Committed in:** bc87d32 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Structural YAML fix, no content change. No scope creep.

## Issues Encountered
None beyond the YAML structure fix noted above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both design documents are complete implementation blueprints for Phase 107 (scoring) and Phase 108 (severity)
- All research citations are real and verifiable
- calibration_required flags mark values needing empirical validation in implementation phases

---
*Phase: 106-model-research*
*Completed: 2026-03-15*
