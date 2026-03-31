---
phase: 44-brain-unification-yaml-knowledge-model-self-describing-checks-live-learning
plan: "02"
subsystem: brain
tags: [yaml, migration, knowledge-model, checks, brain, causal-chains, red-flags]

# Dependency graph
requires:
  - phase: 44-01
    provides: "SCHEMA.md — authoritative spec for unified 3-axis YAML check model"
provides:
  - "brain_migrate_yaml.py — 469-line idempotent migration script"
  - "36 domain YAML files under src/do_uw/brain/checks/ with all 400 checks"
  - "117 checks auto-populated with chain_roles from causal_chains.yaml"
  - "283 checks flagged unlinked: true with empty chain_roles: {}"
  - "11 checks flagged critical_red_flag: true from red_flags.json semantic mapping"
  - "All checks with provenance block: origin=migrated_from_json, confidence=inherited"
  - "Deprecated fields removed: pillar/category/signal_type/hazard_or_signal/content_type/section"
affects:
  - "44-03-PLAN.md — brain build pipeline reads these YAML files to populate DuckDB"
  - "44-04-PLAN.md — patterns/red_flags absorption validates against these files"
  - "44-05-PLAN.md — brain add CLI enforces provenance on files in this directory"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Custom PyYAML _CompactDumper: flow style for short lists (<=5 items) and _FlowMapping dicts reduces per-check line count from ~40 to ~28"
    - "clean_output_dir() for idempotent re-runs: deletes entire checks/ directory before writing"
    - "Semantic red flag mapping: CRF name → check IDs for cases where detection_logic lacks explicit check IDs"
    - "Two-tier splitting: sub-prefix routing + 3rd-level ID routing for domains with single sub-prefix (LIT.REG, LIT.SCA, FWRD.WARN)"

key-files:
  created:
    - "src/do_uw/brain/brain_migrate_yaml.py"
    - "src/do_uw/brain/checks/biz/competitive.yaml"
    - "src/do_uw/brain/checks/biz/core.yaml"
    - "src/do_uw/brain/checks/biz/dependencies.yaml"
    - "src/do_uw/brain/checks/biz/model.yaml"
    - "src/do_uw/brain/checks/exec/activity.yaml"
    - "src/do_uw/brain/checks/exec/profile.yaml"
    - "src/do_uw/brain/checks/fin/accounting.yaml"
    - "src/do_uw/brain/checks/fin/balance.yaml"
    - "src/do_uw/brain/checks/fin/forensic.yaml"
    - "src/do_uw/brain/checks/fin/income.yaml"
    - "src/do_uw/brain/checks/fin/temporal.yaml"
    - "src/do_uw/brain/checks/fwrd/guidance.yaml"
    - "src/do_uw/brain/checks/fwrd/ma.yaml"
    - "src/do_uw/brain/checks/fwrd/transform.yaml"
    - "src/do_uw/brain/checks/fwrd/warn_ops.yaml"
    - "src/do_uw/brain/checks/fwrd/warn_sentiment.yaml"
    - "src/do_uw/brain/checks/fwrd/warn_tech.yaml"
    - "src/do_uw/brain/checks/gov/activist.yaml"
    - "src/do_uw/brain/checks/gov/board.yaml"
    - "src/do_uw/brain/checks/gov/effect.yaml"
    - "src/do_uw/brain/checks/gov/exec_comp.yaml"
    - "src/do_uw/brain/checks/gov/insider.yaml"
    - "src/do_uw/brain/checks/gov/pay.yaml"
    - "src/do_uw/brain/checks/gov/rights.yaml"
    - "src/do_uw/brain/checks/lit/defense.yaml"
    - "src/do_uw/brain/checks/lit/other.yaml"
    - "src/do_uw/brain/checks/lit/reg_agency.yaml"
    - "src/do_uw/brain/checks/lit/reg_sec.yaml"
    - "src/do_uw/brain/checks/lit/sca.yaml"
    - "src/do_uw/brain/checks/lit/sca_history.yaml"
    - "src/do_uw/brain/checks/nlp/nlp.yaml"
    - "src/do_uw/brain/checks/stock/insider.yaml"
    - "src/do_uw/brain/checks/stock/ownership.yaml"
    - "src/do_uw/brain/checks/stock/pattern.yaml"
    - "src/do_uw/brain/checks/stock/price.yaml"
    - "src/do_uw/brain/checks/stock/short.yaml"
  modified: []

key-decisions:
  - "36 YAML files instead of planned 17: YAML verbosity was ~28 lines/check (not the planned ~25), requiring more aggressive splitting to stay under 500-line limit. All domains use subdirectory structure."
  - "Two-level routing for LIT.REG/LIT.SCA/FWRD.WARN: these domains have all checks under a single sub-prefix, so routing uses the 3rd ID segment (check name) for split decisions."
  - "Semantic red flag mapping: red_flags.json source_check fields are free text (not check IDs), so 12 CRF-to-check mappings added by name. Only 2 CRFs had detection_logic with explicit check IDs."
  - "_FlowMapping and _CompactDumper: provenance and chain_roles rendered in flow style (1 line each) to compact per-check YAML from ~40 to ~28 lines."
  - "clean_output_dir() added: makes re-runs idempotent; previous run left stale flat files that corrupted verify_output count."
  - "FIN.ACCT.altman_z_score not in checks.json: listed in red_flags.json detection_logic but is a backlog gap item (BL-G3), not yet implemented. Only NLP.WHISTLE.language_detected resolved from detection_logic."

patterns-established:
  - "Flow-style provenance block: use _FlowMapping for YAML fields that are always compact (provenance, empty chain_roles) to reduce line count"
  - "Verify-before-write: verify_output() checks count match and 490-line warning after every run"
  - "Idempotent migration: clean_output_dir() + write ensures no stale files from prior runs accumulate"

requirements-completed: [ARCH-09]

# Metrics
duration: 10min
completed: "2026-02-25"
---

# Phase 44 Plan 02: Brain YAML Migration Summary

**400 checks from checks.json migrated to 36 domain YAML files in unified 3-axis schema: 117 with chain_roles from causal_chains.yaml, 283 unlinked, 11 critical_red_flag, all under 500 lines, deprecated fields removed**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-25T05:46:37Z
- **Completed:** 2026-02-25T05:56:36Z
- **Tasks:** 2 of 2
- **Files modified:** 38 (1 script + 37 YAML files)

## Accomplishments

- Wrote `brain_migrate_yaml.py` (469 lines, under 500) — idempotent migration script reading 4 source files and producing domain YAML via unified 3-axis transformation
- Migrated all 400 checks from checks.json with count verified; deprecated fields (pillar, category, signal_type, hazard_or_signal, content_type, section int) removed
- Auto-populated chain_roles for all 117 checks that appear in causal_chains.yaml; 283 correctly marked unlinked: true
- Flagged 11 checks critical_red_flag: true from red_flags.json semantic mapping (>= 10 required)
- All 36 YAML files under 500-line limit (max: 494 lines, lit/other.yaml)
- gov/ has 7 subdomain files; fwrd/ has 6 subdomain files (plan required 5+ and 3+ respectively)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write brain_migrate_yaml.py — migration script** - `c17dfa2` (feat)
2. **Task 2: Run migration — produce all domain YAML files** - `50f4349` (feat)

**Plan metadata:** (docs commit added at end of state updates)

## Files Created/Modified

- `src/do_uw/brain/brain_migrate_yaml.py` — 469-line migration script: loads 4 sources, builds chain_roles and red_flag indexes, migrates checks, routes to 36 domain files, verifies count
- `src/do_uw/brain/checks/biz/` — 4 files: core.yaml (11 checks), model.yaml (8), competitive.yaml (11), dependencies.yaml (13)
- `src/do_uw/brain/checks/exec/` — 2 files: profile.yaml (12 checks), activity.yaml (8)
- `src/do_uw/brain/checks/fin/` — 5 files: accounting.yaml (13), balance.yaml (12), forensic.yaml (13), income.yaml (10), temporal.yaml (10)
- `src/do_uw/brain/checks/fwrd/` — 6 files: guidance.yaml (15), ma.yaml (17), transform.yaml (15), warn_ops.yaml (17), warn_sentiment.yaml (11), warn_tech.yaml (4)
- `src/do_uw/brain/checks/gov/` — 7 files: activist.yaml (14), board.yaml (16), effect.yaml (10), exec_comp.yaml (12), insider.yaml (8), pay.yaml (15), rights.yaml (10)
- `src/do_uw/brain/checks/lit/` — 6 files: defense.yaml (9), other.yaml (14), reg_agency.yaml (12), reg_sec.yaml (10), sca.yaml (11), sca_history.yaml (9)
- `src/do_uw/brain/checks/nlp/nlp.yaml` — 15 checks
- `src/do_uw/brain/checks/stock/` — 5 files: insider.yaml (6), ownership.yaml (7), pattern.yaml (6), price.yaml (10), short.yaml (6)

## Decisions Made

- **36 YAML files instead of planned 17:** YAML verbosity at ~28 lines/check (not the assumed ~25) required more aggressive subdirectory splitting. All 8 domains now use subdirectory structure.
- **Two-level routing for LIT.REG/LIT.SCA/FWRD.WARN:** These domains use all-same sub-prefix, so the 3rd ID segment (check name) determines the split file (e.g., LIT.SCA.historical → sca_history.yaml vs LIT.SCA.active → sca.yaml).
- **Semantic CRF mapping:** red_flags.json `source_check` fields are free-text data source descriptions, not check IDs. Added explicit 12-entry CRF-name-to-check-ID mapping in `build_red_flag_index()` to achieve >= 10 critical_red_flag checks.
- **_FlowMapping for compact YAML:** PyYAML block-style provenance = 9 lines per check. Flow style reduces it to 1 line, cutting ~8 lines per check across all 400 checks.
- **clean_output_dir() for idempotency:** First run left old flat files (biz.yaml, fin.yaml) in the checks/ directory. verify_output() counted all files including old ones, producing a false 636-vs-400 mismatch. Added directory cleanup before write.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed regex capture group returning prefix only, not full check ID**
- **Found during:** Task 2 (verifying critical_red_flag count = 0)
- **Issue:** `re.compile(r"\b(BIZ|FIN|...)\.[A-Z]+\.[a-z_]+\b")` with a capturing group returns only the matched group text (the prefix), not the full match. `findall()` on `"FIN.ACCT.altman_z_score"` returned `["FIN"]`.
- **Fix:** Changed to non-capturing group: `r"\b(?:BIZ|FIN|...)\.[A-Z]+\.[a-z_]+\b"`
- **Files modified:** `src/do_uw/brain/brain_migrate_yaml.py`
- **Committed in:** `50f4349` (part of Task 2 commit)

**2. [Rule 1 - Bug] Added clean_output_dir() to prevent stale file accumulation**
- **Found during:** Task 2 (verify_output showed 636 vs 400 checks)
- **Issue:** Running migration twice left both old flat files and new subdirectory files; verify_output counted both.
- **Fix:** Added `clean_output_dir()` that deletes and recreates the checks/ directory before writing.
- **Files modified:** `src/do_uw/brain/brain_migrate_yaml.py`
- **Committed in:** `50f4349` (part of Task 2 commit)

**3. [Rule 2 - Missing Critical] Added semantic CRF → check ID mapping**
- **Found during:** Task 2 (critical_red_flag count was 1, expected >= 10)
- **Issue:** Most red_flags.json entries lack detection_logic with check IDs; source_check is free-text. Without semantic mapping, only 1 check (NLP.WHISTLE.language_detected) got flagged.
- **Fix:** Added `crf_to_checks` dict in `build_red_flag_index()` mapping CRF names to known check IDs.
- **Files modified:** `src/do_uw/brain/brain_migrate_yaml.py`
- **Committed in:** `50f4349` (part of Task 2 commit)

**4. [Rule 2 - Missing Critical] Added _FlowMapping + _CompactDumper to stay under 500-line limit**
- **Found during:** Task 2 (initial migration produced 15 files over 490 lines)
- **Issue:** YAML verbosity was ~40 lines/check (not ~25 as planned), making even small domain groups exceed 500 lines.
- **Fix:** Custom YAML dumper using flow style for short lists and a _FlowMapping class that triggers flow style for specific dicts (provenance, chain_roles), reducing per-check output from ~40 to ~28 lines.
- **Files modified:** `src/do_uw/brain/brain_migrate_yaml.py`
- **Committed in:** `50f4349` (part of Task 2 commit)

---

**Total deviations:** 4 auto-fixed (2 bugs, 2 missing critical functionality)
**Impact on plan:** All auto-fixes necessary for correctness (regex bug) and completeness (line limit, red flags). No scope creep.

## Issues Encountered

- `FIN.ACCT.altman_z_score` referenced in red_flags.json detection_logic but is not in checks.json — it is backlog item BL-G3, not yet implemented. The check ID resolves correctly via the regex fix but does not match any check in checks.json.
- Plan specified 17 target YAML files matching the plan frontmatter `files_modified` list. Actual output is 36 files. The file layout evolved to meet the 500-line constraint, which is the more important requirement.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All 36 YAML files are valid, count-verified, and ready for `brain build` pipeline (44-03)
- The chain_roles keys reference actual causal_chains.yaml chain IDs — cross-validation in brain build will pass
- peril_ids is `[]` for all migrated checks — 44-04 populates these via causal chain traversal
- The checks/ glob pattern `**/*.yaml` is already subdirectory-transparent per the SCHEMA.md spec
- No blockers.

## Self-Check: PASSED

- FOUND: `src/do_uw/brain/brain_migrate_yaml.py` (469 lines, under 500)
- FOUND: commit `c17dfa2` (Task 1)
- FOUND: commit `50f4349` (Task 2)
- FOUND: 36 YAML files in src/do_uw/brain/checks/
- VERIFIED: 400 checks in YAML == 400 checks in checks.json
- VERIFIED: 117 chain_roles populated, 283 unlinked: true
- VERIFIED: 11 critical_red_flag: true
- VERIFIED: max file size 494 lines (under 500)

---
*Phase: 44-brain-unification-yaml-knowledge-model-self-describing-checks-live-learning*
*Completed: 2026-02-25*
