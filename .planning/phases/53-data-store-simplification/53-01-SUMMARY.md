---
phase: 53-data-store-simplification
plan: 01
subsystem: brain
tags: [yaml, json, pydantic, caching, config-consolidation, brain-loader]

# Dependency graph
requires:
  - phase: 52.1-integration-gap-closure
    provides: "Stable brain/ YAML signals and config JSON files"
provides:
  - "BrainLoader class with YAML signal loading (brain_unified_loader.py)"
  - "Module-level singleton functions: load_signals(), load_config(), load_all()"
  - "Backward-compat enrichment (content_type, hazard_or_signal, category, section)"
  - "28 config JSON files consolidated in brain/config/ as single canonical location"
  - "Framework data loaders: load_perils(), load_causal_chains(), load_taxonomy()"
affects: [53-02-PLAN, 53-03-PLAN, brain-loader-migration]

# Tech tracking
tech-stack:
  added: [PyYAML CSafeLoader]
  patterns: [module-level-singleton-caching, enrichment-helper-split]

key-files:
  created:
    - src/do_uw/brain/brain_unified_loader.py
    - src/do_uw/brain/brain_enrichment.py
    - tests/brain/test_brain_unified_loader.py
    - src/do_uw/brain/config/signal_classification.json
    - src/do_uw/brain/config/sic_naics_mapping.json
  modified:
    - src/do_uw/brain/brain_config_loader.py
    - src/do_uw/brain/brain_build_signals.py
    - src/do_uw/brain/brain_migrate.py
    - src/do_uw/config/loader.py
    - src/do_uw/stages/extract/company_profile_items.py
    - src/do_uw/stages/extract/peer_group.py
    - src/do_uw/stages/render/md_renderer_helpers_scoring.py
    - src/do_uw/calibration/impact_ranker.py
    - src/do_uw/cli_knowledge_governance.py

key-decisions:
  - "Split enrichment maps into brain_enrichment.py helper to keep brain_unified_loader.py under 500 lines"
  - "Restored original brain/ root JSON content over brain/config/ brain-build-export versions (brain build exported stripped versions missing critical_red_flag_ceilings, tower_positions, etc.)"
  - "Used post-Phase-49 signal naming convention for merged signal_classification.json (deprecated_signal_ids not deprecated_check_ids)"
  - "brain_config_loader.py default changed to brain/config/ to match canonical location"

patterns-established:
  - "Module-level singleton: load once on first call, _reset_cache() for testing"
  - "Brain/config/ is the single canonical location for all config JSON"
  - "Enrichment helper pattern: maps and logic in separate file from loader"

requirements-completed: [STORE-01, STORE-02]

# Metrics
duration: ~90min
completed: 2026-03-01
---

# Phase 53 Plan 01: BrainLoader + Config Consolidation Summary

**Unified BrainLoader reading 400 YAML signals in <1s with 28 config JSONs consolidated into brain/config/ as single canonical source**

## Performance

- **Duration:** ~90 min
- **Started:** 2026-02-28T23:00:00Z (approx)
- **Completed:** 2026-03-01T06:24:30Z
- **Tasks:** 2
- **Files modified:** 37+ (source + test + config)

## Accomplishments
- Created BrainLoader (brain_unified_loader.py, 430 lines) that loads 400 YAML signals in <1s via PyYAML CSafeLoader with module-level caching
- Created brain_enrichment.py helper with backward-compat enrichment maps (content_type, hazard_or_signal, category, section)
- Consolidated all 28 config JSON files into brain/config/ as single canonical location -- no JSON in brain/ root
- Merged signal_classification.json + check_classification.json using post-Phase-49 naming convention
- 47 tests covering integration, caching, enrichment, framework data, backward-compat API, and validation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create BrainLoader (TDD)**
   - `4f7a699` (test) - RED: 47 failing tests for BrainLoader
   - `7b0ee98` (feat) - GREEN: brain_unified_loader.py + brain_enrichment.py + moved 5 JSON files + updated 32 path references
2. **Task 2: Consolidate config files** - `9bd3bca` (chore) - Track 28 brain/config/ JSON files, restore full originals, merge classification, update defaults

## Files Created/Modified
- `src/do_uw/brain/brain_unified_loader.py` - Unified loader: YAML signals + JSON configs + framework data + backward-compat API (430 lines)
- `src/do_uw/brain/brain_enrichment.py` - Enrichment maps and logic extracted from loader (85 lines)
- `tests/brain/test_brain_unified_loader.py` - 47 tests covering all loader functionality (534 lines)
- `src/do_uw/brain/config/*.json` - 28 canonical config files (scoring, patterns, signals, sectors, red_flags, actuarial, etc.)
- `src/do_uw/brain/config/signal_classification.json` - Merged from check_classification.json with signal naming
- `src/do_uw/brain/config/sic_naics_mapping.json` - Moved from config/ (was only location)
- 16 source files updated with brain/config/ paths (brain_build_signals, brain_migrate, config/loader, calibration, cli, stages)
- 16 test files updated with brain/config/ paths

## Decisions Made
1. **Split enrichment into helper file** - brain_unified_loader.py was 536 lines; extracted enrichment maps and _enrich_signal() into brain_enrichment.py (85 lines), bringing loader to 430 lines. Plan anticipated this: "if approaching limit, split enrichment logic into a helper file."
2. **Restored original JSON content** - The brain/config/ versions from brain-build-export were stripped (missing critical_red_flag_ceilings, tower_positions, severity_ranges from scoring.json). Restored from the original brain/ root files to preserve all runtime data.
3. **Post-Phase-49 naming** - Merged signal_classification.json uses `deprecated_signal_ids` (not `deprecated_check_ids`) to match Phase 49 rename convention.
4. **brain_config_loader default updated** - Changed `_DEFAULT_CONFIG_DIR` from `config/` to `brain/config/` so all existing `load_brain_config()` callers automatically use the canonical location.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Moved 5 JSON files from brain/ root to brain/config/ during Task 1**
- **Found during:** Task 1 (GREEN phase - tests expected configs in brain/config/)
- **Issue:** Tests for BrainLoader needed scoring.json, patterns.json etc. in brain/config/, but those files were still in brain/ root (Task 2 was supposed to move them)
- **Fix:** Performed `git mv` of 5 JSON files and updated 32+ path references across source and test files as part of Task 1 instead of Task 2
- **Files modified:** All files listed in Task 1 commit
- **Verification:** All 47 BrainLoader tests pass
- **Committed in:** 7b0ee98 (Task 1 GREEN commit)

**2. [Rule 1 - Bug] Restored full JSON content over stripped brain-build-export versions**
- **Found during:** Task 2 (verification - scoring tests failed)
- **Issue:** brain/config/ already had scoring.json, patterns.json, red_flags.json, sectors.json from brain-build-export but they were stripped versions missing keys like critical_red_flag_ceilings, tower_positions, severity_ranges
- **Fix:** Restored original content from the brain/ root versions (preserved in git history) for all 4 affected files
- **Files modified:** brain/config/scoring.json, patterns.json, red_flags.json, sectors.json
- **Verification:** 255 tests pass including scoring validation, severity tower, tier differentiation
- **Committed in:** 9bd3bca (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Task ordering adjusted (JSON moves done in Task 1 instead of Task 2). Content restoration was necessary for correctness. No scope creep.

## Issues Encountered
- **DuckDB lock contention** during parallel test runs -- killed background pytest processes before continuing
- **Pre-existing test failures** (verified via git stash/pop, not caused by our changes): test_brain_enrich (380 vs 400 count), test_brain_loader (amplifier string vs bool), test_brain_migrate (380 vs 400), test_enriched_roundtrip (content type counts), test_config_loader (380 vs 400), test_signal_classification (missing signal_type on YAML signals), test_forensic_composites (amplifier "true" vs True)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BrainLoader exists and tested -- ready for Plan 02 to migrate all import sites from 4 old loaders to BrainLoader
- brain/config/ is the single canonical location -- Plan 02 can safely delete config/ directory files after migrating imports
- Old loaders (brain_loader.py, brain_config_loader.py, config/loader.py, knowledge/compat_loader.py) still exist and work -- Plan 02 handles their deletion
- Pre-existing test failures documented -- should be resolved in Plan 02/03 when old loaders are deleted and signal count tests updated

## Self-Check: PASSED

All files verified present. All commit hashes verified in git log.

---
*Phase: 53-data-store-simplification*
*Completed: 2026-03-01*
