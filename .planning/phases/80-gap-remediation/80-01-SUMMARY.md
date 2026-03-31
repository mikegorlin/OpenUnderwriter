---
phase: 80-gap-remediation
plan: 01
subsystem: brain
tags: [manifest, signals, yaml, wiring, contract-validation]

# Dependency graph
requires:
  - phase: 79-contract-enforcement
    provides: Contract validator and manifest schema
  - phase: 76-manifest-structure
    provides: Output manifest with 14 sections, 100 facets
provides:
  - Fully-wired output_manifest.yaml with zero broken signal references
  - 173 unique brain signals mapped to facets
  - 20 data-display-only facets documented with inline comments
affects: [80-gap-remediation-plan-02, rendering, brain-chain-health]

# Tech tracking
tech-stack:
  added: []
  patterns: [signal-id-mapping-from-old-format-to-yaml-hierarchy]

key-files:
  created: []
  modified:
    - src/do_uw/brain/output_manifest.yaml

key-decisions:
  - "Mapped 136 phantom signal IDs to actual brain YAML IDs using domain/prefix/semantic matching"
  - "Wired 37 empty facets with 1-5 signals each based on plan interface mapping"
  - "Documented 20 data-display-only facets (checks, density alerts, charts, statements, calibration) with inline YAML comments"

patterns-established:
  - "Signal references in manifest must use hierarchical brain YAML IDs (e.g. BIZ.DEPEND.customer_conc not BIZ.customer_concentration)"

requirements-completed: [GAP-01, GAP-02]

# Metrics
duration: 3min
completed: 2026-03-07
---

# Phase 80 Plan 01: Signal Reference Rewrite Summary

**Rewired 136 phantom signal references and 37 empty facets in output_manifest.yaml to actual brain YAML signal IDs with zero broken references**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-07T23:34:48Z
- **Completed:** 2026-03-07T23:38:24Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Replaced all 136 phantom signal references (old-format IDs like `BIZ.customer_concentration`) with verified brain YAML signal IDs (like `BIZ.DEPEND.customer_conc`)
- Wired 37 previously-empty facets with appropriate signals (1-5 per facet) based on domain matching
- Documented 20 data-display-only facets with `# data-display-only` comments explaining why they have empty signal lists
- Contract validator confirms 0 broken signal references across all 100 facets
- 173 unique signals now referenced, 218 total signal-to-facet mappings

## Task Commits

Each task was committed atomically:

1. **Task 1: Build signal ID mapping and rewrite manifest** - `16595b0` (feat)

**Plan metadata:** pending

## Files Created/Modified
- `src/do_uw/brain/output_manifest.yaml` - Complete signal reference rewrite (102 insertions, 99 deletions)

## Decisions Made
- Used the plan's interface mapping as primary source for old-to-new signal ID translation
- For facets with multiple possible signals (e.g. `FIN.annual_total_assets`), chose the most semantically appropriate YAML signal rather than creating new ones
- `FIN.auditor_tenure` mapped to same signal as `FIN.auditor_name` (`FIN.ACCT.auditor`) since one signal covers both
- `EXEC.succession_plan` mapped to `EXEC.AGGREGATE.board_risk` since no direct succession signal exists

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Manifest is fully wired -- Plan 02 can now audit which of the 476 brain signals are not referenced by any facet and mark them INACTIVE
- Contract validator baseline is clean for signal references
- 5 orphaned template violations exist (pre-existing legacy templates) -- not in scope for this plan

---
*Phase: 80-gap-remediation*
*Completed: 2026-03-07*
