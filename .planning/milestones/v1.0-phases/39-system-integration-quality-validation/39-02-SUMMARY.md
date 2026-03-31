---
phase: 39-system-integration-quality-validation
plan: 02
subsystem: infra
tags: [vulture, dead-code, file-splitting, anti-context-rot]

requires:
  - phase: 38-professional-pdf-visual-polish
    provides: codebase at 90K+ lines
provides:
  - Reusable dead code detection tool (scripts/dead_code_scan.py)
  - 4 large files split below 500-line limit
affects: [brain, knowledge, cli]

tech-stack:
  added: [vulture]
  patterns: [import-delegation for file splits]

key-files:
  created:
    - scripts/dead_code_scan.py
    - scripts/vulture_whitelist.py
    - src/do_uw/brain/enrichment_data_ext.py
    - src/do_uw/knowledge/calibrate_impact.py
    - src/do_uw/cli_brain_ext.py
    - src/do_uw/brain/brain_writer_export.py
  modified:
    - src/do_uw/brain/enrichment_data.py
    - src/do_uw/knowledge/calibrate.py
    - src/do_uw/cli_brain.py
    - src/do_uw/brain/brain_writer.py

key-decisions:
  - "Import delegation pattern: main file re-exports from ext so consumers don't change imports"
  - "Pragmatic 500-line enforcement: split the 4 largest files, not borderline 505-535 files"

patterns-established:
  - "File splitting via _ext.py suffix with re-exports from main module"

requirements-completed: []

duration: 30min
completed: 2026-02-21
---

# Plan 39-02: Dead Code Scanner + File Splitting Summary

**Vulture-based dead code tool + 4 files split below 500 lines via import delegation**

## Performance

- **Duration:** 30 min
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Added vulture as dev dependency with reusable scan script
- Split enrichment_data.py (767→464+328), calibrate.py (727→319+436), cli_brain.py (633→355+296), brain_writer.py (561→460+155)
- All public APIs preserved — zero consumer import changes needed

## Task Commits

1. **Task 1: Dead code detection tool** - `b172401` (feat)
2. **Task 2: Split 4 large files** - `5962990` (refactor)

## Deviations from Plan
None — plan executed as written.

## Issues Encountered
- Agent ran out of usage mid-execution; file splits completed manually
- checks.json was inadvertently modified by agent; reverted before commit

---
*Phase: 39-system-integration-quality-validation*
*Completed: 2026-02-21*
