---
phase: 46-brain-driven-gap-search
plan: "01"
subsystem: brain
tags: [brain, yaml, gap-detection, classification, knowledge-store]

# Dependency graph
requires: []
provides:
  - "gap_bucket and gap_keywords fields on 68 SKIPPED checks in brain YAML files"
  - "66 intentionally-unmapped (L1) checks classified and documented"
  - "2 routing-gap (L3) checks with web-search keywords ready for Plan 03 gap searcher"
affects:
  - "46-02 (AcquiredData model + state field)"
  - "46-03 (gap searcher reads gap_bucket and gap_keywords)"
  - "46-04 (QA audit visibility)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "gap_bucket/gap_keywords fields added directly to brain YAML check entries (not a separate config file)"
    - "Gap classification sourced from actual pipeline SKIPPED state.json, not from static gap_detector.py logic"

key-files:
  created: []
  modified:
    - src/do_uw/brain/checks/biz/core.yaml
    - src/do_uw/brain/checks/biz/dependencies.yaml
    - src/do_uw/brain/checks/exec/profile.yaml
    - src/do_uw/brain/checks/fin/accounting.yaml
    - src/do_uw/brain/checks/fin/forensic.yaml
    - src/do_uw/brain/checks/fwrd/guidance.yaml
    - src/do_uw/brain/checks/fwrd/warn_ops.yaml
    - src/do_uw/brain/checks/fwrd/warn_sentiment.yaml
    - src/do_uw/brain/checks/gov/board.yaml
    - src/do_uw/brain/checks/gov/effect.yaml
    - src/do_uw/brain/checks/gov/insider.yaml
    - src/do_uw/brain/checks/gov/pay.yaml
    - src/do_uw/brain/checks/gov/rights.yaml
    - src/do_uw/brain/checks/lit/defense.yaml
    - src/do_uw/brain/checks/lit/reg_sec.yaml
    - src/do_uw/brain/checks/nlp/nlp.yaml

key-decisions:
  - "Gap population sourced from actual AAPL pipeline run (state.json) rather than gap_detector.py static logic: Phase 45 added declarative routing to all checks, so gap_detector now returns 0, but 68 checks still SKIP at runtime"
  - "66 L1 checks classified as intentionally-unmapped (structured-source-only, ineligible for web search per GAP-03)"
  - "2 L3 checks classified as routing-gap with keywords: FIN.ACCT.restatement_stock_window and LIT.PATTERN.peer_contagion"
  - "No aspirational bucket used: all L3 SKIPPED checks are routing-gap (data could be found via web search)"
  - "gap_keywords: [] for intentionally-unmapped checks (Plan 03 code-level gate enforces ineligibility)"

patterns-established:
  - "Gap classification fields (gap_bucket, gap_keywords) live in check's brain YAML entry, after provenance block"
  - "BrainCheckEntry model_config extra=allow passes new fields through schema validation without code changes"

requirements-completed: [GAP-01]

# Metrics
duration: 5min
completed: 2026-02-25
---

# Phase 46 Plan 01: Gap Classification in Brain YAML Files Summary

**68 SKIPPED checks classified into gap buckets (66 intentionally-unmapped L1, 2 routing-gap L3) with gap_bucket and gap_keywords fields added directly to 16 brain YAML check files**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-25T22:58:04Z
- **Completed:** 2026-02-25T23:02:50Z
- **Tasks:** 2 (analysis + YAML edits)
- **Files modified:** 16 brain YAML files

## Accomplishments
- Identified the exact 68 SKIPPED checks from the AAPL pipeline run (state.json) and classified each
- Added `gap_bucket: intentionally-unmapped` to 66 L1 checks (no keywords needed — ineligible for web search)
- Added `gap_bucket: routing-gap` with keywords to 2 L3 checks eligible for web gap search
- Brain DB rebuilt successfully; BrainCheckEntry `model_config = {"extra": "allow"}` passes new fields through schema validation
- All 16 modified YAML files parse without error

## Task Commits

1. **Tasks 1+2: Gap classification + YAML edits + brain rebuild** - `9cbfa5a` (feat)

## Files Created/Modified
- `src/do_uw/brain/checks/biz/core.yaml` - BIZ.STRUCT.vie_spe: intentionally-unmapped
- `src/do_uw/brain/checks/biz/dependencies.yaml` - BIZ.DEPEND.labor: intentionally-unmapped
- `src/do_uw/brain/checks/exec/profile.yaml` - 6 EXEC checks: intentionally-unmapped
- `src/do_uw/brain/checks/fin/accounting.yaml` - 3 FIN.ACCT L1 checks: intentionally-unmapped; FIN.ACCT.restatement_stock_window (L3): routing-gap with keywords [restatement, stock drop, disclosure]
- `src/do_uw/brain/checks/fin/forensic.yaml` - 2 FIN.QUALITY checks: intentionally-unmapped
- `src/do_uw/brain/checks/fwrd/guidance.yaml` - 3 FWRD.DISC/NARRATIVE checks: intentionally-unmapped
- `src/do_uw/brain/checks/fwrd/warn_ops.yaml` - 3 FWRD.WARN ops checks: intentionally-unmapped
- `src/do_uw/brain/checks/fwrd/warn_sentiment.yaml` - 10 FWRD.WARN sentiment checks: intentionally-unmapped
- `src/do_uw/brain/checks/gov/board.yaml` - 9 GOV.BOARD checks: intentionally-unmapped
- `src/do_uw/brain/checks/gov/effect.yaml` - 6 GOV.EFFECT checks: intentionally-unmapped
- `src/do_uw/brain/checks/gov/insider.yaml` - 2 GOV.INSIDER checks: intentionally-unmapped
- `src/do_uw/brain/checks/gov/pay.yaml` - 7 GOV.PAY checks: intentionally-unmapped
- `src/do_uw/brain/checks/gov/rights.yaml` - 8 GOV.RIGHTS checks: intentionally-unmapped
- `src/do_uw/brain/checks/lit/defense.yaml` - LIT.DEFENSE.forum_selection + LIT.SECTOR.regulatory_databases: intentionally-unmapped; LIT.PATTERN.peer_contagion (L3): routing-gap with keywords [peer lawsuit, contagion, class action, securities fraud]
- `src/do_uw/brain/checks/lit/reg_sec.yaml` - LIT.REG.comment_letters: intentionally-unmapped
- `src/do_uw/brain/checks/nlp/nlp.yaml` - 2 NLP.FILING checks: intentionally-unmapped

## Decisions Made
- **Gap population from state.json not gap_detector.py**: Phase 45 added declarative `data_strategy.field_key` routing to all checks, making `gap_detector.py` return 0 no-routing checks. The canonical 68 SKIPPED checks were sourced from the actual AAPL pipeline run at `output/AAPL-2026-02-25/state.json`, which is the ground truth per the plan context ("68 SKIPPED checks from v1.0").
- **No aspirational bucket**: All L3 checks in the SKIPPED population have required_data that could plausibly be found via web search (restatement timing correlation, peer litigation data). Pure aspirational checks (social media, personal conduct) are classified L1 in the brain and thus fall under intentionally-unmapped.
- **Keywords only on L3 routing-gap checks**: Plan requirement confirmed — intentionally-unmapped checks get `gap_keywords: []` because Plan 03's code-level gate (`acquisition_tier != L1`) enforces ineligibility; keywords would never be used.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Gap detection script adaptation for Phase 45 routing changes**
- **Found during:** Task 1 (identification of 68 SKIPPED checks)
- **Issue:** The plan's detection script (`not has_field_key and not has_legacy and not has_p26`) returns 0 checks because Phase 45 added declarative `data_strategy.field_key` to all BIZ/GOV/LIT/STOCK/FIN checks. The plan was written assuming the pre-Phase45 state.
- **Fix:** Sourced the 68-check population from `output/AAPL-2026-02-25/state.json` (actual pipeline run), which gives the ground truth SKIPPED set. This is more accurate than the static detection script because it reflects actual runtime behavior including Phase26 mappers that return `{}` for some checks.
- **Files modified:** None (analysis only - YAML edits used the correct population)
- **Verification:** 68 checks with gap_bucket confirmed via `load_checks_from_yaml()` after YAML edits
- **Impact:** No scope change — same 68 checks, different identification method

---

**Total deviations:** 1 auto-fixed (detection script adaptation)
**Impact on plan:** The auto-fix identified the correct population more accurately than the original script would have. No scope creep.

## Issues Encountered

The plan's verification script (`gap_detector.detect_gaps()` returning ~68 checks with NO_FIELD_ROUTING) returns 0 because Phase 45 completed full declarative routing coverage. The automated verification check in the plan cannot pass as written. The actual success criteria (68 checks have gap_bucket fields, brain build passes, routing-gap checks have keywords) are all met.

## Next Phase Readiness
- Plan 02: AcquiredData.brain_targeted_search field can be added — no blocker
- Plan 03: gap_searcher.py can read `gap_bucket` and `gap_keywords` from YAML via `load_checks_from_yaml()` — all 68 entries ready
- The 2 routing-gap checks (FIN.ACCT.restatement_stock_window, LIT.PATTERN.peer_contagion) are the only candidates for actual web gap searches — Plan 03 budget gating will handle this naturally

---
*Phase: 46-brain-driven-gap-search*
*Completed: 2026-02-25*
