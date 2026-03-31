---
phase: 09-knowledge-store-domain-intelligence
plan: 02
subsystem: database
tags: [knowledge-store, migration, fts5, backward-compat, query-api, sqlalchemy]

# Dependency graph
requires:
  - phase: 09-knowledge-store-domain-intelligence
    plan: 01
    provides: SQLAlchemy ORM models, lifecycle, Alembic migration
  - phase: 01-project-setup
    provides: brain/ JSON files, ConfigLoader, BrainConfig
provides:
  - KnowledgeStore query API with FTS5 full-text search
  - Migration of all 5 brain JSON files (359 checks, 19 patterns, 55 rules, 11 flags, sector baselines)
  - BackwardCompatLoader as drop-in ConfigLoader replacement
  - Raw JSON metadata storage for faithful backward reconstruction
affects: [09-03 (enrichment), 09-04 (playbooks), 09-05 (learning), 09-06 (ingestion)]

# Tech tracking
tech-stack:
  added: []
  patterns: [FTS5 rebuild-on-search, raw metadata for backward compat, module-level converter functions]

key-files:
  created:
    - src/do_uw/knowledge/store.py
    - src/do_uw/knowledge/store_converters.py
    - src/do_uw/knowledge/store_search.py
    - src/do_uw/knowledge/migrate.py
    - src/do_uw/knowledge/compat_loader.py
    - tests/knowledge/test_store.py
    - tests/knowledge/test_migrate.py
    - tests/knowledge/test_compat_loader.py
  modified:
    - src/do_uw/knowledge/__init__.py

key-decisions:
  - "Standalone FTS5 tables (not content-synced) with rebuild-on-search for reliable indexing"
  - "Split store.py into store.py (410L) + store_converters.py (110L) + store_search.py (124L) for 500-line compliance"
  - "Raw JSON metadata stored alongside structured data for backward-compat reconstruction"
  - "BackwardCompatLoader uses stored raw JSON (not reconstruction) for guaranteed ConfigLoader parity"
  - "Closure default_factory for MigrationResult.errors (pyright strict list[Unknown] fix)"
  - "cast(list[Any]) for iteration over JSON arrays from Mapped[Any] columns (pyright strict)"

patterns-established:
  - "store_converters: module-level ORM-to-dict converters for import from multiple modules"
  - "store_search: FTS5 and LIKE search implementations as standalone functions"
  - "metadata store pattern: __metadata__key notes for raw JSON reconstruction"
  - "migration pattern: _load_json + _migrate_X per file + MigrationResult dataclass"

# Metrics
duration: 14min
completed: 2026-02-09
---

# Phase 9 Plan 2: Data Migration and Query API Summary

**All 359 checks, 19 patterns, 55 scoring rules, 11 red flags, and sector baselines migrated from brain/ JSON to knowledge store with FTS5 search and verified backward-compatible loader**

## Performance

- **Duration:** 14 min
- **Started:** 2026-02-09T06:10:01Z
- **Completed:** 2026-02-09T06:23:38Z
- **Tasks:** 2
- **Files created:** 8
- **Files modified:** 1

## Accomplishments
- KnowledgeStore query API with multi-criteria filtering (section, status, factor, severity, pillar) and FTS5 full-text search with LIKE fallback
- Complete migration of all 5 brain JSON files: 359 checks, 19 patterns, 55 scoring rules, 11 red flags, sector baselines across 10 metric sections
- BackwardCompatLoader that produces identical BrainConfig as ConfigLoader (verified by 25 comparison tests)
- Raw JSON metadata stored alongside structured data ensuring faithful reconstruction of complex nested structures (scoring tiers, pattern modifiers, etc.)
- 91 new tests (39 store + 27 migration + 25 compat), all passing alongside 1134 existing tests (1225 total)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create KnowledgeStore query API with FTS5 search** - `150da4d` (feat)
2. **Task 2: Create migration and backward-compatible loader** - `12ae96c` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/store.py` (410 lines) - KnowledgeStore class with query API, bulk insert, metadata store
- `src/do_uw/knowledge/store_converters.py` (110 lines) - ORM-to-dict converter functions
- `src/do_uw/knowledge/store_search.py` (124 lines) - FTS5 and LIKE search implementations
- `src/do_uw/knowledge/migrate.py` (412 lines) - migrate_from_json with per-file migration functions
- `src/do_uw/knowledge/compat_loader.py` (156 lines) - BackwardCompatLoader wrapping KnowledgeStore
- `src/do_uw/knowledge/__init__.py` (58 lines) - Updated exports with KnowledgeStore, BackwardCompatLoader, migrate_from_json
- `tests/knowledge/test_store.py` - 39 tests for query API, search, playbooks, metadata
- `tests/knowledge/test_migrate.py` - 27 tests for migration counts, check details, scoring rules, patterns, red flags, sectors
- `tests/knowledge/test_compat_loader.py` - 25 tests verifying ConfigLoader/BackwardCompatLoader parity

## Decisions Made
- **Standalone FTS5 tables**: Not content-synced to avoid SQLAlchemy session management issues; rebuilt on each search call for reliability
- **3-way store.py split**: store.py (410L) + store_converters.py (110L) + store_search.py (124L) to stay under 500-line limit
- **Raw metadata approach**: Full original JSON stored as metadata notes, used by BackwardCompatLoader for guaranteed parity with ConfigLoader output
- **Closure default_factory**: `_empty_str_list()` for MigrationResult.errors (pyright strict compliance)
- **cast(list[Any])**: Required for iterating JSON arrays from Mapped[Any] columns in pyright strict mode

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed FTS5 external content table session issue**
- **Found during:** Task 1 (test_search_checks)
- **Issue:** FTS5 external content tables (`content=checks`) couldn't sync with SQLAlchemy-managed sessions; FTS search returned empty results
- **Fix:** Changed to standalone FTS5 tables with rebuild-on-search pattern
- **Files modified:** src/do_uw/knowledge/store.py, src/do_uw/knowledge/store_search.py
- **Committed in:** 150da4d

**2. [Rule 3 - Blocking] Split store.py for 500-line compliance**
- **Found during:** Task 1 (line count verification)
- **Issue:** store.py reached 730 lines with all converters, search, and query methods
- **Fix:** Extracted converters to store_converters.py (110L) and search to store_search.py (124L)
- **Files created:** src/do_uw/knowledge/store_converters.py, src/do_uw/knowledge/store_search.py
- **Committed in:** 150da4d

**3. [Rule 1 - Bug] Fixed pyright strict errors on JSON iteration**
- **Found during:** Task 1 and Task 2 (pyright check)
- **Issue:** Iterating over `Mapped[Any]` JSON columns and `dict[str, Any].get()` produces Unknown types in pyright strict
- **Fix:** Added cast(list[Any]) and cast(dict[str, Any]) patterns; closure default_factory for MigrationResult.errors
- **Files modified:** src/do_uw/knowledge/store.py, src/do_uw/knowledge/migrate.py
- **Committed in:** 150da4d, 12ae96c

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correct FTS5 operation, 500-line compliance, and pyright strict. No scope creep.

## Issues Encountered
None beyond the auto-fixed items above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- KnowledgeStore fully operational with 359 checks, 19 patterns, 55 rules, 11 flags, sector baselines
- Query API supports all specified filter criteria plus FTS5 search
- BackwardCompatLoader verified as drop-in ConfigLoader replacement
- Ready for 09-03 (enrichment) and 09-04 (industry playbooks)
- No blockers for subsequent plans

---
*Phase: 09-knowledge-store-domain-intelligence*
*Completed: 2026-02-09*
