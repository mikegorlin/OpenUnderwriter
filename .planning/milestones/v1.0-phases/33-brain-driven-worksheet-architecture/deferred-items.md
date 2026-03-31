# Deferred Items — Phase 33

## brain.duckdb Out of Sync with checks.json

**Found during:** Plan 33-07, Task 2
**Severity:** Medium — causes 3 test failures in test_compat_loader.py
**Issue:** `src/do_uw/brain/brain.duckdb` was populated before Plan 33-03 added 12 new checks to checks.json. The BrainDBLoader filters to only active checks in brain.duckdb, so BackwardCompatLoader returns 388 checks instead of 396.

**Affected checks (12 missing from brain.duckdb):**
- BIZ.STRUCT.subsidiary_count, BIZ.STRUCT.vie_spe, BIZ.STRUCT.related_party
- LIT.DEFENSE.forum_selection, LIT.DEFENSE.contingent_liabilities, LIT.DEFENSE.pslra_safe_harbor
- LIT.PATTERN.peer_contagion, LIT.PATTERN.temporal_correlation, LIT.PATTERN.sol_windows
- LIT.SECTOR.industry_patterns, LIT.SECTOR.regulatory_databases

**Fix:** Rebuild brain.duckdb from checks.json (run brain migration script).

**Pre-existing test failures (3):**
- tests/knowledge/test_compat_loader.py::TestChecksEquality::test_checks_total
- tests/knowledge/test_compat_loader.py::TestChecksEquality::test_checks_count
- tests/knowledge/test_compat_loader.py::TestChecksEquality::test_checks_ids_match

## Playbook Checks Missing `pillar` Field

**Found during:** Plan 33-07, Task 2
**Severity:** Low — 4 playbook checks in brain.duckdb lack pillar field
**Issue:** Checks FWRD.EVENT.19-BIOT, 20-BIOT, 21-BIOT, 22-HLTH stored in brain.duckdb without `pillar` field. Causes CheckDefinition validation failure.
**Fix:** Update playbook data to include pillar field, then rebuild brain.duckdb.

## INFERENCE_PATTERN Checks Missing pattern_ref

**Found during:** Plan 33-07, Task 2
**Severity:** Low — 2 IP checks from Plan 33-03 lack pattern_ref
**Issue:** LIT.PATTERN.peer_contagion and LIT.PATTERN.temporal_correlation are typed as INFERENCE_PATTERN but have no pattern_ref value.
**Fix:** Add pattern_ref values to these checks in checks.json.
