---
phase: 116-d-o-commentary-layer
plan: 01
subsystem: brain
tags: [do_context, yaml, d&o-commentary, batch-generation, brain-signals]

requires:
  - phase: 115-do-context-infrastructure
    provides: do_context_engine.py template evaluation engine, SafeFormatDict, validate_do_context_template

provides:
  - do_context templates (TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR) for all 563 brain signals
  - batch generation script (scripts/batch_generate_do_context.py) for future re-generation
  - validation test suite (tests/brain/test_do_context_batch.py) with 5 test classes

affects: [116-02, 116-03, 116-04, 116-05, d-o-commentary-tables, scoring-detail, section-narratives]

tech-stack:
  added: [ruamel.yaml (round-trip YAML preservation)]
  patterns: [deterministic do_context generation from signal metadata, FACTOR_TO_THEORY mapping]

key-files:
  created:
    - scripts/batch_generate_do_context.py
    - tests/brain/test_do_context_batch.py
  modified:
    - src/do_uw/brain/signals/**/*.yaml (all 100 signal YAML files)

key-decisions:
  - "Deterministic template generation from signal metadata (factors, thresholds, epistemology) rather than LLM-only -- faster, reproducible, no API cost; LLM mode available via --use-llm flag"
  - "Fixed 11 pre-existing templates (Phase 115) to include {value}/{company} placeholders for consistency"
  - "FACTOR_TO_THEORY dict maps F1-F10 to specific D&O litigation theories referenced in every template"

patterns-established:
  - "do_context template format: 1-3 sentences with {value}, {company} placeholders referencing D&O litigation theory"
  - "Batch generation via scripts/batch_generate_do_context.py with --dry-run, --validate-only, --file, --use-llm modes"

requirements-completed: [COMMENT-01, COMMENT-03]

duration: 7min
completed: 2026-03-19
---

# Phase 116 Plan 01: D&O Commentary Batch Generation Summary

**Generated do_context templates (TRIGGERED_RED/YELLOW/CLEAR) for all 563 brain signals across 100 YAML files with D&O litigation theory references and company-specific placeholders**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-19T04:48:34Z
- **Completed:** 2026-03-19T04:55:34Z
- **Tasks:** 2
- **Files modified:** 102

## Accomplishments
- All 563 brain signals now have presentation.do_context with TRIGGERED_RED, TRIGGERED_YELLOW, and CLEAR templates
- 1688 templates pass validate_do_context_template() with zero errors
- Every template contains at least one placeholder variable ({value}, {company}, etc.)
- Zero generic boilerplate phrases (QUAL-04 compliant)
- Batch generation script supports deterministic mode (default) and LLM mode (--use-llm)
- FACTOR_TO_THEORY mapping ensures F1-F10 factors reference correct D&O litigation theories

## Task Commits

Each task was committed atomically:

1. **Task 1: Build batch do_context generation script and validate** - `7ff1f0ca` (feat)
2. **Task 2: Run batch generation and validate all 563 signals** - `49fae289` (feat)

## Files Created/Modified
- `scripts/batch_generate_do_context.py` - Batch generation script with deterministic + LLM modes, FACTOR_TO_THEORY mapping
- `tests/brain/test_do_context_batch.py` - 5 test classes: coverage, validation, placeholders, boilerplate, key validity
- `src/do_uw/brain/signals/**/*.yaml` - All 100 signal YAML files enriched with do_context templates

## Decisions Made
- Used deterministic template generation from signal metadata rather than LLM calls -- faster, reproducible, zero API cost. LLM mode preserved as --use-llm flag for future quality improvement
- Fixed 11 pre-existing Phase 115 templates (Altman Z-Score, Ohlson O-Score, Beneish M-Score) to include {value}/{company} placeholders for consistency with new templates
- Templates reference the specific D&O litigation theory via FACTOR_TO_THEORY mapping (F1=Litigation History, F2=Stock Decline, F3=Financial Irregularities, etc.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing do_context templates missing placeholders**
- **Found during:** Task 2 (batch generation validation)
- **Issue:** 11 templates from Phase 115 (accounting.yaml, forensic.yaml, forensic_xbrl.yaml) lacked {value}/{company} placeholders
- **Fix:** Rewrote Altman Z-Score, Ohlson O-Score, Beneish M-Score, and M-Score Composite templates with {company} and {value} variables
- **Files modified:** fin/accounting.yaml, fin/forensic.yaml, fin/forensic_xbrl.yaml
- **Verification:** test_templates_contain_placeholders passes for all 1688 templates
- **Committed in:** 49fae289 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential for test consistency. No scope creep.

## Issues Encountered
None - batch generation completed in under 2 minutes for all 558 signals.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 563 signals have do_context templates ready for consumption by section renderers (Plans 02-05)
- Migration targets (sect3-7 Python functions) can now replace hardcoded D&O commentary with signal do_context
- CI gate (Plan 05) can promote WARN to FAIL once all Python/Jinja2 migration complete

---
*Phase: 116-d-o-commentary-layer*
*Completed: 2026-03-19*
