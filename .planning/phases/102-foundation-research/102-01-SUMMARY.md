---
phase: 102-foundation-research
plan: 01
subsystem: brain
tags: [yaml, taxonomy, risk-model, hae, rap, signal-classification]

# Dependency graph
requires:
  - phase: none
    provides: "Existing 514 brain signals in src/do_uw/brain/signals/**/*.yaml"
provides:
  - "H/A/E taxonomy definition (rap_taxonomy.yaml) with 3 categories, 20 subcategories"
  - "Complete signal-to-H/A/E mapping (rap_signal_mapping.yaml) for all 514 signals"
  - "Classification rules for edge cases and dual-aspect signals"
affects: [103-signal-hae-annotation, 104-scoring-redesign, 107-multiplicative-scoring]

# Tech tracking
tech-stack:
  added: []
  patterns: ["RAP H/A/E 3-dimensional risk decomposition (Host/Agent/Environment)"]

key-files:
  created:
    - src/do_uw/brain/framework/rap_taxonomy.yaml
    - src/do_uw/brain/framework/rap_signal_mapping.yaml
  modified: []

key-decisions:
  - "Agent (47%) is the largest category -- reflects D&O claim reality where management conduct drives most litigation"
  - "20 subcategories (7 Host, 7 Agent, 6 Environment) provide granular classification without over-fragmentation"
  - "BASE.* signals classified as host.data_foundation -- they describe analysis inputs, not risk"
  - "GOV.BOARD/GOV.EXEC/GOV.EFFECT split between Host (structural) and Agent (events/findings) based on whether signal describes architecture or behavior"
  - "EXEC.CEO/CFO.risk_score classified as Agent despite being composites, because computation is heavily weighted by behavioral signals"
  - "FWRD.MACRO.* classified as Environment (external conditions), while ENVR.* captures structural sensitivity to those conditions (Host)"
  - "Added agent.governance_events subcategory not in original plan -- needed for board departures, material weakness findings, auditor changes"

patterns-established:
  - "RAP taxonomy: Host=structural/slow-moving, Agent=behavioral/dynamic, Environment=external/contextual"
  - "Classification rules for split-domain signals (same prefix, different H/A/E based on signal nature)"
  - "Dual-aspect signals resolved by primary D&O relevance (which dimension matters most for claim theory)"

requirements-completed: [TAX-01, TAX-02]

# Metrics
duration: 6min
completed: 2026-03-15
---

# Phase 102 Plan 01: H/A/E Taxonomy Summary

**Derived 3-dimensional H/A/E risk taxonomy from 514 brain signals: Host 154 (30%), Agent 241 (47%), Environment 119 (23%) with 20 subcategories and validated MECE classification**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-15T02:39:36Z
- **Completed:** 2026-03-15T02:45:39Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments
- Created `rap_taxonomy.yaml` defining Host/Agent/Environment risk decomposition with 20 subcategories, each documented with D&O rationale and claim relevance
- Created `rap_signal_mapping.yaml` with complete mapping of all 514 signals to H/A/E categories -- zero orphans, MECE validated
- Documented classification rules for 8 edge-case signal domains where the same prefix splits across H/A/E categories
- Established dual-aspect signal resolution patterns for borderline classifications

## Task Commits

Each task was committed atomically:

1. **Task 1: Define H/A/E taxonomy with subcategories and classification rules** - `7a22ddf` (feat)
2. **Task 2: Map all 514 signals to H/A/E categories with validation** - `d913b13` (feat)

## Files Created/Modified
- `src/do_uw/brain/framework/rap_taxonomy.yaml` - H/A/E taxonomy definition with 3 categories, 20 subcategories, classification rules, and dual-aspect guidance (726 lines)
- `src/do_uw/brain/framework/rap_signal_mapping.yaml` - Complete signal-to-H/A/E mapping for all 514 signals with rationale (2064 lines)

## Decisions Made
- **Agent dominance (47%):** Intentional -- D&O claims are primarily triggered by management CONDUCT (restatements, insider trading, disclosure failures). The flat 10-factor model underweighted this dimension.
- **20 subcategories:** 7 Host, 7 Agent, 6 Environment. Added `agent.governance_events` (not in original plan) to properly capture board departures, material weakness findings, and auditor changes that are events rather than structure.
- **FWRD.MACRO as Environment, ENVR as Host:** Distinguished between the company's INHERENT sensitivity to macro factors (Host) and the current STATE of macro conditions (Environment). This preserves the clean H/A/E boundary.
- **BASE.* as host.data_foundation:** Data acquisition signals are structural attributes of the analysis, not risk evaluations. They affect underwriting confidence, not claim probability.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added agent.governance_events subcategory**
- **Found during:** Task 1 (taxonomy definition)
- **Issue:** Plan specified 6 Agent subcategories. GOV.BOARD.departures, GOV.EFFECT.material_weakness, GOV.EXEC.departure_context, and similar event/finding signals needed a proper home that was not `agent.executive_conduct` (which is specifically about insider trading and individual officer behavior).
- **Fix:** Added `agent.governance_events` as 7th Agent subcategory covering board departures, refresh activity, governance effectiveness findings (material weakness, late filing, auditor change), and executive turnover events.
- **Files modified:** src/do_uw/brain/framework/rap_taxonomy.yaml
- **Verification:** All GOV.BOARD/EXEC/EFFECT edge-case signals now have semantically correct subcategory assignments.
- **Committed in:** 7a22ddf (Task 1 commit)

**2. [Rule 1 - Bug] Corrected signal counts from plan**
- **Found during:** Task 2 (signal mapping)
- **Issue:** Plan specified approximate counts per domain prefix (e.g., FIN.FORENSIC: 35, LIT.REG: 18, FWRD.WARN: 30). Actual counts from YAML files differed (FIN.FORENSIC: 38, LIT.REG: 22, FWRD.WARN: 32). Counts in plan were from an earlier snapshot.
- **Fix:** Used actual signal IDs from YAML files as source of truth (per CLAUDE.md: "YAML files are the ONLY source of truth for brain signals"). All 514 signals accounted for.
- **Files modified:** src/do_uw/brain/framework/rap_signal_mapping.yaml
- **Verification:** Validation script confirms 514 mapped = 514 actual, zero missing, zero extra.
- **Committed in:** d913b13 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical subcategory, 1 count correction)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep -- taxonomy is cleaner with proper governance_events subcategory.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Taxonomy and mapping artifacts are machine-readable YAML, ready for Phase 103 (Signal H/A/E Annotation) to add `rap_class` field directly to each signal YAML file
- Distribution is well-balanced (no category below 23%) for multiplicative scoring model viability
- Classification rules documented for downstream phases to handle new signals consistently
- All 20 subcategories populated with sufficient signal counts for meaningful aggregation

---
*Phase: 102-foundation-research*
*Completed: 2026-03-15*
