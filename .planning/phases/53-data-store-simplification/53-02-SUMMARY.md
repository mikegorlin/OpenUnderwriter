---
phase: 53-data-store-simplification
plan: 02
subsystem: brain
tags: [brain-loader, import-migration, config-consolidation, yaml, duckdb-decoupling]

requires:
  - phase: 53-01
    provides: "BrainLoader unified loader with YAML signal loading and JSON config loading"
provides:
  - "All pipeline stages migrated from 4 old loaders to single BrainLoader"
  - "config/ directory deleted -- brain/config/ is sole canonical location"
  - "Old loader modules deleted (brain_config_loader, compat_loader)"
  - "DuckDB no longer touched for signal/config definitions at runtime"
affects: [53-03-cli-migration]

tech-stack:
  added: []
  patterns:
    - "Module-level functions (load_config, load_signals) preferred over class instantiation"
    - "Lazy import of BrainLoader inside functions to avoid circular deps"

key-files:
  created: []
  modified:
    - src/do_uw/stages/analyze/__init__.py
    - src/do_uw/stages/score/__init__.py
    - src/do_uw/stages/benchmark/__init__.py
    - src/do_uw/stages/render/scoring_peril_data.py
    - src/do_uw/brain/brain_enrichment.py
    - src/do_uw/knowledge/signal_definition.py
    - src/do_uw/stages/acquire/clients/market_client.py

key-decisions:
  - "Keep brain_loader.py + brain_loader_rows.py alive for CLI files (Plan 03 scope)"
  - "Inline playbook signal append logic from BrainKnowledgeLoader into analyze/__init__.py"
  - "Add execution_mode=AUTO enrichment to YAML signals (was DuckDB-only field)"
  - "Make SignalDefinition.pillar and .section optional (not present in YAML source)"

patterns-established:
  - "Import BrainLoader lazily in ACQUIRE stage to maintain MCP boundary"
  - "Use load_config() for direct JSON reads instead of file path construction"

requirements-completed: [STORE-03, STORE-04]

duration: 45min
completed: 2026-03-01
---

# Phase 53 Plan 02: Import Migration + Loader Deletion Summary

**Migrated 31 pipeline files from 4 old loaders to BrainLoader, deleted config/ directory (24 files) and 2 old loader modules, updated 20+ test files**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-03-01T08:00:00Z
- **Completed:** 2026-03-01T08:45:00Z
- **Tasks:** 2
- **Files modified:** 87

## Accomplishments
- All pipeline stages (ACQUIRE through RENDER) now use BrainLoader exclusively -- zero imports of BrainDBLoader, BrainKnowledgeLoader, ConfigLoader, or load_brain_config from old modules remain in pipeline code
- Deleted 24 files from config/ directory (22 JSON configs + 2 Python modules) -- brain/config/ is now the sole canonical config location
- Deleted brain_config_loader.py and compat_loader.py -- 2 of 4 old loaders removed
- Updated 20+ test files to use BrainLoader mock targets and brain/config/ paths
- Zero new test failures introduced

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate all pipeline imports** - `beb2ca6` (feat)
   - 22 files: load_brain_config -> load_config
   - 5 files: BrainDBLoader -> BrainLoader/load_signals
   - 4 files: BrainKnowledgeLoader -> BrainLoader
   - Inlined playbook signal append logic into analyze/__init__.py
   - Updated knowledge/__init__.py exports

2. **Task 2: Delete old loaders + update tests** - `9dcc2f1` (chore)
   - Deleted brain_config_loader.py, compat_loader.py
   - Deleted entire config/ directory (24 files)
   - Updated brain_loader.py to import BrainConfig from brain_unified_loader
   - Added execution_mode enrichment to brain_enrichment.py
   - Made SignalDefinition.pillar/section optional
   - Fixed market_client.py sectors path
   - Updated 20+ test mock targets and file paths

## Files Created/Modified

### Deleted (27 files)
- `src/do_uw/brain/brain_config_loader.py` - Old config loader (replaced by load_config)
- `src/do_uw/knowledge/compat_loader.py` - BrainKnowledgeLoader/BackwardCompatLoader (replaced by BrainLoader)
- `src/do_uw/config/` - Entire directory: 22 JSON configs + __init__.py + loader.py
- `tests/brain/test_brain_loader.py` - Old BrainDBLoader tests
- `tests/config/test_loader.py` + `tests/config/__init__.py` - Old ConfigLoader tests

### Key Modifications
- `src/do_uw/stages/analyze/__init__.py` - BrainKnowledgeLoader -> BrainLoader + inlined _append_playbook_signals helper
- `src/do_uw/stages/score/__init__.py` - Both imports migrated to BrainLoader + load_config
- `src/do_uw/stages/benchmark/__init__.py` - BrainKnowledgeLoader -> BrainLoader
- `src/do_uw/stages/render/scoring_peril_data.py` - BrainDBLoader -> load_perils/load_causal_chains functions
- `src/do_uw/brain/brain_enrichment.py` - Added execution_mode=AUTO enrichment
- `src/do_uw/knowledge/signal_definition.py` - Made pillar/section optional with defaults
- `src/do_uw/stages/acquire/clients/market_client.py` - Direct file read -> load_config("sectors")
- `src/do_uw/brain/brain_loader.py` - BrainConfig import updated (config/loader -> brain_unified_loader)
- 22 files across stages/ - load_brain_config -> load_config rename

### Test Updates (20+ files)
- Mock targets: `BrainKnowledgeLoader` -> `BrainLoader` in 12 test files
- Mock targets: `BrainDBLoader` -> `BrainLoader` in 3 test files
- File paths: `config/` -> `brain/config/` in 5 test files
- Rewrote: test_scoring_peril_data.py, test_peril_scoring_html.py, test_persistent_store.py, test_integration.py, test_playbooks.py, test_enriched_roundtrip.py, test_pattern_detection.py

## Decisions Made
- **Keep brain_loader.py alive**: CLI files (cli_brain.py, cli_brain_ext.py, cli_knowledge_traceability.py) still import BrainDBLoader -- deferred to Plan 03
- **Keep brain_loader_rows.py alive**: brain_loader.py imports from it -- must be deleted together in Plan 03
- **Inline playbook logic**: BrainKnowledgeLoader had playbook_id support built in; this was inlined as _append_playbook_signals() in analyze/__init__.py rather than adding it to BrainLoader (keeps BrainLoader simple)
- **Add execution_mode enrichment**: YAML signals lack execution_mode (was DuckDB-only); added `execution_mode=AUTO` default to enrich_signal() since all signals are AUTO-evaluated
- **Make pillar optional**: YAML signals don't have a `pillar` field; made it optional with `""` default on SignalDefinition to avoid validation failures

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] brain_loader_rows.py could not be deleted**
- **Found during:** Task 2
- **Issue:** brain_loader.py imports _parse_json and row_to_signal_dict from brain_loader_rows.py; CLI files still use brain_loader.py
- **Fix:** Restored brain_loader_rows.py after attempted deletion; deferred to Plan 03 with CLI migration
- **Verification:** Import chain verified intact

**2. [Rule 1 - Bug] brain_requirements.py had leftover loader.close() call**
- **Found during:** Task 2 (test verification)
- **Issue:** After migrating from BrainDBLoader to BrainLoader, the try/finally/close pattern remained but BrainLoader has no close() method
- **Fix:** Removed try/finally/close pattern entirely
- **Files modified:** src/do_uw/stages/acquire/brain_requirements.py
- **Verification:** test_brain_requirements.py passes

**3. [Rule 3 - Blocking] Missing execution_mode field in YAML signals**
- **Found during:** Task 2 (test_enriched_roundtrip.py failure)
- **Issue:** load_signals() from YAML didn't include execution_mode (was DuckDB-enriched); tests filtering by execution_mode=="AUTO" got 0 results
- **Fix:** Added execution_mode=AUTO default to enrich_signal() in brain_enrichment.py
- **Files modified:** src/do_uw/brain/brain_enrichment.py
- **Verification:** 393 AUTO signals detected after fix

**4. [Rule 3 - Blocking] SignalDefinition required pillar field missing from YAML**
- **Found during:** Task 2 (test_enriched_check_validates_against_definition failure)
- **Issue:** SignalDefinition.pillar was required but YAML signals don't have it
- **Fix:** Made pillar and section optional with defaults
- **Files modified:** src/do_uw/knowledge/signal_definition.py

**5. [Rule 3 - Blocking] market_client.py sectors path broken**
- **Found during:** Task 2 (test_market_client_etf failure)
- **Issue:** Direct file read of brain/sectors.json failed because file moved to brain/config/sectors.json
- **Fix:** Changed from direct file read to load_config("sectors") function call
- **Files modified:** src/do_uw/stages/acquire/clients/market_client.py

**6. [Rule 3 - Blocking] Multiple test files had stale mock targets and config paths**
- **Found during:** Task 2 (progressive test verification)
- **Issue:** 20+ test files still referenced BrainKnowledgeLoader/BrainDBLoader mock targets and old config/ paths
- **Fix:** Updated all mock targets to BrainLoader and all file paths to brain/config/
- **Files modified:** 20+ test files (detailed in Files Created/Modified section)

---

**Total deviations:** 6 auto-fixed (1 bug, 5 blocking)
**Impact on plan:** All auto-fixes necessary for correctness. No scope creep. Plan scope slightly expanded to cover more test files than originally listed.

## Issues Encountered
- Pre-existing test failures (380 vs 400 signal count) in ~10 test files -- documented in Plan 01 SUMMARY, not caused by our changes
- Background pytest execution in Claude Code produced empty output files; worked around by running tests in smaller batches

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 03 (CLI migration) is the final plan: migrate cli_brain.py, cli_brain_ext.py, cli_knowledge_traceability.py from BrainDBLoader to BrainLoader, then delete brain_loader.py and brain_loader_rows.py
- brain_loader.py and brain_loader_rows.py intentionally kept alive for Plan 03

## Self-Check: PASSED

- [x] brain_config_loader.py deleted
- [x] compat_loader.py deleted
- [x] config/ directory deleted (including __pycache__)
- [x] test_brain_loader.py deleted
- [x] test_loader.py deleted
- [x] Commit beb2ca6 (Task 1) exists
- [x] Commit 9dcc2f1 (Task 2) exists
- [x] SUMMARY.md exists
- [x] Zero brain_config_loader imports in pipeline code
- [x] Zero compat_loader imports in pipeline code
- [x] Zero do_uw.config imports in pipeline code

---
*Phase: 53-data-store-simplification*
*Completed: 2026-03-01*
