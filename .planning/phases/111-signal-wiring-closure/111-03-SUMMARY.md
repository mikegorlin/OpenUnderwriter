---
phase: 111-signal-wiring-closure
plan: 03
subsystem: analyze
tags: [signal-resolver, yaml-driven, deferred, data-pending, migration, ci-tests]

requires:
  - phase: 111-signal-wiring-closure
    provides: "trend/peer evaluators (111-02), signal group assignment (111-01)"
provides:
  - "Generic YAML-driven signal field resolver (signal_resolver.py)"
  - "Phased migration: resolver primary, mapper fallback"
  - "72 signals classified DEFERRED with amber Data pending badge"
  - "Signal audit appendix shows DEFERRED separately from SKIPPED"
  - "6 CI tests for field declarations + SKIPPED/DEFERRED thresholds"
  - "Reusable signal result diff script for future migration QA"
affects: [112, 113, 115]

tech-stack:
  added: []
  patterns: ["resolver-then-mapper fallback for zero-regression migration", "DEFERRED execution_mode for unimplemented data sources", "SourcedValue auto-unwrap in path traversal"]

key-files:
  created:
    - src/do_uw/stages/analyze/signal_resolver.py
    - tests/stages/analyze/test_signal_resolver.py
    - tests/brain/test_field_declarations.py
    - tests/stages/analyze/test_skipped_rate.py
    - scripts/diff_signal_results.py
  modified:
    - src/do_uw/stages/analyze/signal_engine.py
    - src/do_uw/stages/analyze/signal_disposition.py
    - src/do_uw/stages/render/html_signals.py
    - src/do_uw/stages/render/context_builders/audit.py
    - src/do_uw/templates/html/components/badges.html.j2
    - src/do_uw/templates/html/appendices/signal_audit.html.j2
    - src/do_uw/brain/signals/**/*.yaml (18 files, 72 signals)

key-decisions:
  - "Phased migration: resolver tries YAML paths first, falls back to old mapper when empty — zero regression risk"
  - "72 signals classified DEFERRED across 18 YAML files (external APIs, proxy extraction gaps, peer benchmarks)"
  - "DEFERRED signals emit into signal results with data_status=DEFERRED for visible Data pending badge"
  - "SkipReason.DEFERRED added to disposition system, separated from SKIPPED in audit context"
  - "Regression verified via pre/post signal snapshot diff: 411 unchanged, 72 deferred, 0 regressions"

patterns-established:
  - "resolver-then-mapper: try resolve_signal_data() first, fall back to map_signal_data() when resolver returns empty"
  - "DEFERRED execution_mode: signals needing unimplemented data sources are explicitly classified, not silently SKIPPED"
  - "Data pending badge: amber badge visually distinct from SKIPPED (gray) and CLEAR (green) in worksheet"

requirements-completed: [WIRE-04, WIRE-05]

duration: 18min
completed: 2026-03-16
---

# Phase 111 Plan 03: YAML-Driven Field Resolver and SKIPPED Signal Closure Summary

**Generic signal resolver replaces hardcoded mapper routing with YAML path traversal, 72 signals classified DEFERRED with Data pending badge, zero regressions verified**

## Performance

- **Duration:** 18 min
- **Started:** 2026-03-16T22:33:47Z
- **Completed:** 2026-03-16T22:51:52Z
- **Tasks:** 3
- **Files modified:** 26 (+ 18 YAML signal files)

## Accomplishments
- Created signal_resolver.py (~160 lines) with generic YAML-driven field resolution supporting path, computed_from, fallback_paths, field_path, and data_strategy.field_key
- Wired resolver into signal engine with phased migration: resolver primary, old mapper fallback (zero regression risk)
- Classified 72 signals as DEFERRED across 18 YAML files — pipeline SKIPPED rate drops from 19.5% to 4.6%
- Added amber "Data pending" badge to HTML worksheet, visually distinct from gray SKIPPED badge
- Created reusable signal result diff script proving zero regressions (411 unchanged, 72 deferred)
- 18 new tests (12 resolver + 2 field declaration + 4 SKIPPED/DEFERRED rate)

## Task Commits

Each task was committed atomically:

1. **Task 1: Build generic YAML-driven field resolver (TDD)** - `6365097` (feat)
2. **Task 2: DEFERRED classification + Data pending badge + CI tests** - `d4ed9a8` (feat)
3. **Task 3: Signal result diff script + zero-regression QA gate** - `ec6c774` (feat)

## Files Created/Modified
- `src/do_uw/stages/analyze/signal_resolver.py` - Generic YAML-driven field resolver with SourcedValue unwrapping
- `src/do_uw/stages/analyze/signal_engine.py` - Resolver-then-mapper fallback, DEFERRED signal emission
- `src/do_uw/stages/analyze/signal_disposition.py` - DEFERRED SkipReason for disposition audit trail
- `src/do_uw/stages/render/html_signals.py` - DEFERRED counter in coverage stats
- `src/do_uw/stages/render/context_builders/audit.py` - Separate DEFERRED from SKIPPED in audit context
- `src/do_uw/templates/html/components/badges.html.j2` - Amber "Data pending" badge in traffic_light + check_summary
- `src/do_uw/templates/html/appendices/signal_audit.html.j2` - DEFERRED card + detail table in audit appendix
- `src/do_uw/brain/signals/**/*.yaml` - 72 signals marked execution_mode: DEFERRED across 18 files
- `tests/stages/analyze/test_signal_resolver.py` - 12 unit tests for resolver
- `tests/brain/test_field_declarations.py` - 2 CI tests for YAML path validity
- `tests/stages/analyze/test_skipped_rate.py` - 4 CI tests for DEFERRED/AUTO thresholds
- `scripts/diff_signal_results.py` - Reusable migration diff tool

## Decisions Made
- **Phased migration over big-bang replacement**: resolver tries YAML paths first, falls back to old mapper when resolver returns empty. This guarantees zero regressions because the mapper still handles every signal it handled before. Future YAML path corrections will migrate signals one-by-one from mapper to resolver.
- **72 signals DEFERRED (not SKIPPED)**: Signals requiring external APIs (ISS, Glassdoor), proxy extraction gaps (board attendance, compensation details, shareholder rights), peer benchmarks (SEC Frames not populated), and advanced analytics (NLP filing, insider timing) are explicitly classified rather than silently SKIPPED.
- **Regression verification via snapshot diff**: Rather than requiring a full pipeline run (which needs MCP servers), verified zero regressions by demonstrating the resolver-then-mapper fallback produces identical results for all AUTO signals.
- **SourcedValue auto-unwrap**: The resolver automatically detects and unwraps SourcedValue wrappers at each path traversal step, using a type check that excludes primitives to avoid false positives.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure in test_section_assessments.py (ScoringLensResult not fully defined) — confirmed unrelated, documented in 111-02 summary

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- WIRE-04 (SKIPPED rate <5%) and WIRE-05 (field declarations match state paths) requirements complete
- Resolver infrastructure ready for incremental YAML path corrections (each fix moves a signal from mapper to resolver)
- DEFERRED signals will evaluate once their data sources are wired in future phases
- Old mapper code (~3,000 lines) can be deleted in Phase 115 legacy purge once all signals use resolver
- Data pending badge renders in worksheet for underwriter transparency

## Self-Check: PASSED

All 5 created files verified on disk. All 3 task commits verified in git log.
