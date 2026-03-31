---
phase: 84-manifest-section-elimination
plan: 02
subsystem: brain
tags: [manifest, section-yaml, migration, brain-health, brain-audit, brain-trace]

requires:
  - phase: 84-01
    provides: "ManifestGroup schema, collect_signals_by_group, load_manifest"
provides:
  - "brain_health.py computes facet_coverage using signal.group field"
  - "brain_audit.py has no import of brain_section_schema"
  - "cli_brain_trace.py uses manifest groups for all group name lookups and render audit"
affects: [84-03, 84-04]

tech-stack:
  added: []
  patterns: ["signal.group self-selection replaces section YAML facet lists for coverage"]

key-files:
  created: []
  modified:
    - src/do_uw/brain/brain_health.py
    - src/do_uw/brain/brain_audit.py
    - src/do_uw/cli_brain_trace.py

key-decisions:
  - "brain_health facet coverage counts signals with non-empty group field (simpler than manifest cross-ref)"
  - "cli_brain_trace render-audit iterates manifest groups with collect_signals_by_group for declared signal lookup"

patterns-established:
  - "_get_group_name_map(): lazy-cached manifest group name lookup pattern for CLI display"

requirements-completed: [SECT-03, SECT-04]

duration: 3min
completed: 2026-03-08
---

# Phase 84 Plan 02: Low-Risk Consumer Migration Summary

**Migrated brain_health, brain_audit, and cli_brain_trace from section YAML to manifest groups with signal self-selection**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-08T07:48:43Z
- **Completed:** 2026-03-08T07:51:31Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- brain_health.py facet coverage now computed from signal.group field instead of section YAML signal lists
- brain_audit.py unused load_all_sections import removed (was dead code)
- cli_brain_trace.py all 3 usage sites migrated: lazy group name cache, trace blueprint/live tables, render-audit
- Zero remaining imports from brain_section_schema in all 3 files

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate brain_health and brain_audit** - `766fed8` (feat)
2. **Task 2: Migrate cli_brain_trace** - `8b5eb93` (feat)

## Files Created/Modified
- `src/do_uw/brain/brain_health.py` - Replaced section YAML facet coverage with signal.group counting; removed Path import
- `src/do_uw/brain/brain_audit.py` - Removed unused load_all_sections import
- `src/do_uw/cli_brain_trace.py` - Replaced _get_trace_sections with _get_group_name_map; render-audit now iterates manifest groups

## Decisions Made
- brain_health facet coverage uses simple `sum(1 for s in active_signals if s.get("group", ""))` -- equivalent to section YAML intersection since all grouped signals have valid group IDs
- cli_brain_trace render-audit uses collect_signals_by_group to map signal IDs to manifest groups, replacing section.signals list

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- test_cli_brain_trace.py has pre-existing failures (command registration issue with "trace-chain" subcommand) -- verified same failure exists on pre-change code. Not a regression, out of scope.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 3 of 5 section YAML consumers migrated (brain_health, brain_audit, cli_brain_trace)
- Remaining consumers: section_renderer.py (84-03, already completed in parallel), html_renderer.py (84-04)
- Ready for 84-04 final consumer migration and section YAML deletion

---
*Phase: 84-manifest-section-elimination*
*Completed: 2026-03-08*
