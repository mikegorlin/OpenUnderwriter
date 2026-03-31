---
phase: 44-brain-unification-yaml-knowledge-model-self-describing-checks-live-learning
plan: "01"
subsystem: brain
tags: [yaml, schema, knowledge-model, brain, duckdb, documentation]

# Dependency graph
requires: []
provides:
  - "SCHEMA.md — authoritative spec for unified check format across 3 axes (work_type, risk_position, acquisition_tier)"
  - "Complete field inventory: 9 required fields, 19 optional fields with conditional inclusion rules"
  - "Provenance block spec enabling live learning audit trail"
  - "File layout rules with 500-line subdirectory plan for all 8 check domains"
  - "Deprecated field list (pillar, category, signal_type, hazard_or_signal, content_type, section)"
  - "8-step article-to-brain decomposition workflow"
  - "Section mapping table: int (1-7) to semantic strings"
affects:
  - "44-02-PLAN.md — migration script must produce YAML matching this spec"
  - "44-03-PLAN.md — brain build pipeline validates against this spec"
  - "44-04-PLAN.md — patterns/red_flags absorption follows this spec"
  - "44-05-PLAN.md — brain add CLI enforces provenance rules from this spec"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "3-axis check model: work_type (what) + risk_position (where) + acquisition_tier (how expensive)"
    - "Provenance-first: every check entry tracks origin, source_url, source_date — audit trail for live learning"
    - "DuckDB as pure cache: nothing enters DuckDB that is not first declared in YAML"
    - "Subdirectory structure for large domains: checks/gov/, checks/fwrd/, etc. (anti-context-rot 500-line rule)"

key-files:
  created:
    - "src/do_uw/brain/SCHEMA.md"
  modified: []

key-decisions:
  - "3-axis model is the canonical schema: work_type (extract/evaluate/infer) + layer (hazard/signal/peril_confirming) + acquisition_tier (L1-L4)"
  - "Provenance block is a required field on every check; migrated checks get origin=migrated_from_json with all other provenance fields null"
  - "brain add CLI must require --source and --date flags; brain validate rejects brain_add checks without source_url"
  - "File layout uses subdirectory structure for all domains with >20 checks (7 of 8 domains exceed 500-line limit)"
  - "Deprecated fields (pillar, category, signal_type, hazard_or_signal, content_type, section int) kept in DuckDB for backward compat; removed from YAML entirely"
  - "Section int-to-string mapping defined: section 1-7 maps to company_profile/governance/management/financial/litigation/stock_activity/forward_looking"

patterns-established:
  - "Schema-first development: define the contract before writing any code or YAML files"
  - "brain build is explicit-only (not auto-triggered); validate is a separate post-build sanity check"

requirements-completed: [ARCH-09]

# Metrics
duration: 3min
completed: "2026-02-25"
---

# Phase 44 Plan 01: Brain Check Schema Summary

**SCHEMA.md — authoritative 396-line spec defining the unified 3-axis YAML check model (work_type/risk_position/acquisition_tier), all required and optional fields, provenance block structure, 500-line-safe subdirectory layout for 8 check domains, and 8-step article-to-brain decomposition workflow**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-25T05:39:21Z
- **Completed:** 2026-02-25T05:42:46Z
- **Tasks:** 1 of 1
- **Files modified:** 1 (created)

## Accomplishments

- Formally defined the 3-axis model: work_type (extract/evaluate/infer), risk_position (layer + factors + peril_ids + chain_roles), and acquisition_tier (L1-L4)
- Documented all 9 required fields and 19 optional fields with types, valid values, and conditional inclusion rules
- Specified the provenance block structure that enables the live learning audit trail and distinguishes migrated vs. brain_add checks
- Defined subdirectory layout for all 8 check domains — all domains with >20 checks require subdirectory structure to stay within CLAUDE.md's 500-line anti-context-rot rule
- Listed all 6 deprecated checks.json fields (pillar, category, signal_type, hazard_or_signal, content_type, section int) with their replacements and backward compat notes
- Provided complete annotated GOV.BOARD.independence example with inline comments on every field
- Wrote 8-step article-to-brain decomposition workflow that future users follow when adding new knowledge
- Added section mapping table translating old int sections (1-7) to semantic strings (governance, financial, etc.)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write SCHEMA.md — unified check format spec** - `a73da46` (docs)

**Plan metadata:** (docs commit added at end of state updates)

## Files Created/Modified

- `src/do_uw/brain/SCHEMA.md` — 396-line authoritative spec for unified check schema; the contract that 44-02 through 44-05 implement

## Decisions Made

- **3-axis model finalized:** work_type (extract/evaluate/infer) + risk_position (layer/factors/peril_ids/chain_roles) + acquisition_tier (L1-L4). These axes are orthogonal — each independently classifies a different dimension of the check.
- **Provenance is a required field:** The `provenance` dict is required on every check. Migrated checks get `origin: migrated_from_json` with all other provenance fields null. The brain add CLI enforces `source_url` and `source_date` via `--source` and `--date` flags.
- **Subdirectory structure required for 7 of 8 domains:** All domains exceeding ~20 checks will exceed the 500-line YAML file limit (at ~25 lines/check). Only `nlp/` (~15 checks, ~375 lines) is safe as a single flat file.
- **Section int-to-string mapping codified:** Old section integers 1-7 map to: company_profile, governance, management, financial, litigation, stock_activity, forward_looking.
- **brain build is explicit-only:** No auto-trigger from loader. Clearer mental model; auto-trigger (mtime check) deferred to a follow-on enhancement.
- **Backward compat columns stay in DuckDB:** hazard_or_signal and content_type are kept as DuckDB columns (not in YAML) until all callers are updated. Plan 44-03 cleanup subtask removes them.

## Deviations from Plan

None — plan executed exactly as written. Task 1 was documentation-only with no code changes.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- SCHEMA.md is the contract that 44-02 (migration script) must produce. The migration script reads checks.json and writes 8 YAML domain files that validate against this spec.
- All locked decisions are now documented — 44-02 can begin without waiting for architectural choices.
- The subdirectory plan (Section 6 of SCHEMA.md) specifies exactly which subdirs each domain needs — migration script can use this directly.
- No blockers or concerns.

## Self-Check: PASSED

- FOUND: `src/do_uw/brain/SCHEMA.md`
- FOUND: commit `a73da46`

---
*Phase: 44-brain-unification-yaml-knowledge-model-self-describing-checks-live-learning*
*Completed: 2026-02-25*
