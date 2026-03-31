---
phase: 128-infrastructure-foundation
plan: 01
subsystem: infra
tags: [registry-pattern, context-assembly, audit-dedup, html-renderer]

# Dependency graph
requires:
  - phase: 114-worksheet-foundation
    provides: html_context_assembly.py monolithic context builder
provides:
  - Registry pattern for HTML context assembly (register_builder decorator)
  - Domain-grouped assembly modules (html_extras, signals, dossier)
  - Unified audit appendix with deduplication
affects: [128-02, 128-03, future worksheet section additions]

# Tech tracking
tech-stack:
  added: []
  patterns: [registry-pattern for context assembly, builder-function decoration]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/assembly_registry.py
    - src/do_uw/stages/render/context_builders/assembly_html_extras.py
    - src/do_uw/stages/render/context_builders/assembly_signals.py
    - src/do_uw/stages/render/context_builders/assembly_dossier.py
    - tests/render/test_assembly_registry.py
    - tests/render/test_audit_dedup.py
  modified:
    - src/do_uw/stages/render/html_context_assembly.py
    - src/do_uw/stages/render/context_builders/__init__.py
    - src/do_uw/stages/render/context_builders/audit.py

key-decisions:
  - "Registry pattern with @register_builder decorator for extensible context assembly"
  - "Keep html_context_assembly.py as thin re-export stub for backward compatibility"
  - "Unified audit merges disposition and render audit via signal_id-to-field-path prefix matching"

patterns-established:
  - "Registry pattern: new context builders register via @register_builder decorator"
  - "Builder function signature: (state, context, chart_dir) -> None (mutates context)"
  - "Import-triggered registration: assembly_registry imports domain modules at module load"

requirements-completed: [INFRA-01, INFRA-06]

# Metrics
duration: 7min
completed: 2026-03-22
---

# Phase 128 Plan 01: Assembly Split + Audit Dedup Summary

**Registry pattern splitting 712-line html_context_assembly.py into 4 domain modules (all under 320 lines), plus unified audit appendix with signal/field deduplication**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-22T21:32:52Z
- **Completed:** 2026-03-22T21:39:51Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Dissolved 712-line monolith into 4 focused modules via registry pattern (115, 186, 219, 313 lines)
- Backward-compatible: all existing imports continue working via thin re-export stub
- Audit appendix now merges disposition and render audit into unified summary with deduplication
- 14 new tests (8 registry + 6 audit dedup)

## Task Commits

Each task was committed atomically:

1. **Task 1: Split html_context_assembly.py into registry + domain modules** - `bc14dc02` (feat)
2. **Task 2: Deduplicate audit appendix context** - `e3d5884b` (feat)

_Note: Task 1 was already committed as part of a prior 128-02 session; tests confirmed all acceptance criteria met._

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/assembly_registry.py` - Registry pattern + build_html_context dispatcher
- `src/do_uw/stages/render/context_builders/assembly_html_extras.py` - HTML-specific context (densities, charts, logos, identity)
- `src/do_uw/stages/render/context_builders/assembly_signals.py` - Signal results, coverage, footnotes, chart thresholds
- `src/do_uw/stages/render/context_builders/assembly_dossier.py` - Dossier builders, forward risk, audit, worksheet builders
- `src/do_uw/stages/render/html_context_assembly.py` - Reduced to 8-line re-export stub
- `src/do_uw/stages/render/context_builders/__init__.py` - Added build_html_context export
- `src/do_uw/stages/render/context_builders/audit.py` - Added render_audit param + unified summary with dedup
- `tests/render/test_assembly_registry.py` - 8 tests for registry pattern
- `tests/render/test_audit_dedup.py` - 6 tests for audit deduplication

## Decisions Made
- Used registry pattern with decorator (@register_builder) rather than explicit function calls for extensibility
- Signal-to-field dedup uses prefix matching (e.g., FIN.revenue_growth -> fin.revenue) for reasonable overlap detection
- Kept html_context_assembly.py as stub rather than deleting for import backward compatibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure in tests/render/test_peril_scoring_html.py (ceiling_details AttributeError on SimpleNamespace mock) -- unrelated to this plan, excluded from verification.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Registry pattern established -- future phases can add context builders by registering a single function
- Audit appendix unified summary available for template consumption
- Ready for 128-02 (raw filing storage) and 128-03 (discrepancy warnings)

---
*Phase: 128-infrastructure-foundation*
*Completed: 2026-03-22*
