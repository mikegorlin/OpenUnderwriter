---
phase: 102-foundation-research
plan: 03
subsystem: brain-framework
tags: [yaml, decision-framework, hae-taxonomy, underwriting, d-and-o, risk-tiers]

# Dependency graph
requires:
  - phase: 102-foundation-research (plan 01)
    provides: "H/A/E taxonomy with 20 subcategories and 514 signal mappings"
provides:
  - "6-tier underwriting decision framework (PREFERRED through PROHIBITED)"
  - "6 output dimensions per tier (pricing, layer, terms, monitoring, referral, communication)"
  - "Liberty excess-only calibration with ABC vs Side A product considerations"
  - "H/A/E multiplicative interaction model with CRF override mechanism"
  - "Worksheet integration spec for Phase 112 rendering"
affects: [107-scoring-implementation, 112-render-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Decision tier hierarchy with highest-applicable-wins logic"
    - "Non-compensatory CRF veto via ELECTRE discordance"
    - "Multiplicative H/A/E interaction model (P = H x A x E)"

key-files:
  created:
    - src/do_uw/brain/framework/decision_framework.yaml
  modified: []

key-decisions:
  - "6 tiers not 3-4: underwriting judgment has more nuance than traffic lights (PREFERRED, STANDARD, CAUTIOUS, ELEVATED, ADVERSE, PROHIBITED)"
  - "CRFs are non-compensatory: ELECTRE discordance veto overrides composite scores regardless of other dimensions"
  - "Liberty calibration uses attachment-dependent weighting: Host matters more at high attachment, Agent matters more for Side A"
  - "5 real-world underwriting patterns codified: follow-the-lead, market discipline, attachment point comfort, renewal vs new, broker relationship"

patterns-established:
  - "Decision framework YAML structure with tiers -> outputs -> calibration -> interactions -> worksheet spec"
  - "Tier entry criteria reference H/A/E composites from rap_taxonomy.yaml"
  - "peril_context and rap_composite keys link to perils.yaml and rap_taxonomy.yaml"

requirements-completed: [TAX-04, TAX-05]

# Metrics
duration: 3min
completed: 2026-03-15
---

# Phase 102 Plan 03: Decision Framework Summary

**6-tier D&O decision framework with pricing/layer/terms/monitoring/referral/communication outputs, calibrated for Liberty excess-only position with CRF non-compensatory override**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-15T02:48:31Z
- **Completed:** 2026-03-15T02:51:17Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Defined 6 decision tiers (PREFERRED through PROHIBITED) with signal-driven entry criteria mapped to H/A/E composite scores
- Created 6 output dimensions per tier providing actionable underwriting guidance (pricing, layer comfort, terms/conditions, monitoring triggers, referral criteria, communication patterns)
- Codified Liberty's excess-only position with product-specific considerations (ABC vs Side A) and attachment-dependent risk weighting
- Documented 6 H/A/E interaction scenarios with multiplicative amplification semantics and CRF non-compensatory override mechanism
- Defined worksheet integration spec for Phase 112 rendering including decision header, documentation fields, and signal-to-decision trace

## Task Commits

Each task was committed atomically:

1. **Task 1: Design decision tiers with multi-dimensional outputs** - `1943021` (feat)

## Files Created/Modified
- `src/do_uw/brain/framework/decision_framework.yaml` - Complete underwriting decision framework with 5 sections: tiers, outputs, Liberty calibration, interaction model, worksheet integration spec

## Decisions Made
- Used 6 tiers rather than 3-4 to capture the full spectrum of D&O underwriting judgment from "actively compete" to "non-negotiable decline"
- CRFs implemented as non-compensatory ELECTRE discordance vetoes -- no favorable score in another dimension can offset active fraud, SEC enforcement, or zone of insolvency
- Liberty calibration structured around attachment point and product type (ABC vs Side A), reflecting that Host risk dominates at high attachment while Agent risk dominates for Side A
- Codified 5 real-world underwriting patterns from practitioner experience (follow-the-lead, market discipline, attachment point comfort, renewal advantage, broker relationship)
- Worksheet integration spec includes both system recommendation and UW override capability with override_flag tracking

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Decision framework ready for Phase 107 scoring implementation (tier assignment from H/A/E composites)
- Worksheet integration spec ready for Phase 112 rendering
- Framework links to rap_taxonomy.yaml (composites) and perils.yaml (severity context) via documented key patterns

## Self-Check: PASSED

- FOUND: `src/do_uw/brain/framework/decision_framework.yaml`
- FOUND: commit `1943021`

---
*Phase: 102-foundation-research*
*Completed: 2026-03-15*
