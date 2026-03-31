---
phase: 48-output-quality-hardening
plan: "01"
subsystem: brain-schema
tags: [brain, schema, display-spec, facet, tdd, wave-0]
dependency_graph:
  requires: []
  provides:
    - DisplaySpec Pydantic model in brain_check_schema.py
    - FacetSpec Pydantic model in brain_facet_schema.py
    - brain/facets/governance.yaml
    - brain/facets/red_flags.yaml
    - Wave 0 failing tests for QA-01, QA-02, QA-04
  affects:
    - brain_check_schema.py (additive only — no existing YAML breaks)
    - html_checks.py (facet loader wired, lazy load)
    - 5 brain YAML files with display: blocks
tech_stack:
  added: [brain_facet_schema.py, brain/facets/governance.yaml, brain/facets/red_flags.yaml]
  patterns:
    - DisplaySpec as optional sub-model on BrainCheckEntry (default=None, additive)
    - FacetSpec schema with validate_display_type() for fail-fast loading
    - Lazy facet loader via _get_facets() in html_checks.py
    - Wave 0 TDD pattern: write failing tests before implementation plans begin
key_files:
  created:
    - src/do_uw/brain/brain_facet_schema.py
    - src/do_uw/brain/facets/governance.yaml
    - src/do_uw/brain/facets/red_flags.yaml
    - tests/stages/render/test_qa_audit_source.py
    - tests/stages/render/test_red_flags_template.py
    - tests/stages/analyze/test_coerce_value_boolean.py
  modified:
    - src/do_uw/brain/brain_check_schema.py
    - src/do_uw/brain/checks/gov/board.yaml
    - src/do_uw/brain/checks/gov/effect.yaml
    - src/do_uw/brain/checks/lit/defense.yaml
    - src/do_uw/brain/checks/fin/forensic.yaml
    - src/do_uw/stages/render/html_checks.py
decisions:
  - "[48-01]: DisplaySpec placed above BrainCheckEntry in brain_check_schema.py — both classes use ConfigDict(extra='allow') so new display: blocks in YAML are accepted without schema migration"
  - "[48-01]: FacetSpec.validate_display_type() called explicitly (not via Pydantic validator) — keeps fail-fast behavior without triggering on model_construct()"
  - "[48-01]: _get_facets() uses global state pattern (not module-level eager load) — avoids import-time side effects in tests"
  - "[48-01]: LIT.PATTERN.peer_contagion lives in lit/defense.yaml (not lit/pattern.yaml); FIN.QUALITY checks live in fin/forensic.yaml (not fin/quality.yaml) — plan frontmatter had wrong file names, actual check IDs are correct"
  - "[48-01]: governance.yaml signals list uses actual check IDs (GOV.BOARD.ceo_chair not GOV.BOARD.ceo_chair_separation) to match real brain YAML entries"
metrics:
  duration: 525s
  completed: "2026-02-26"
  tasks: 3
  files: 12
---

# Phase 48 Plan 01: Signal Display Schema + Wave 0 Tests Summary

**One-liner:** DisplaySpec and FacetSpec Pydantic schemas established with two representative Facet YAMLs, 5 brain YAML display blocks, and Wave 0 RED baseline tests for QA-01/02/04.

## What Was Built

### Task 1: DisplaySpec model + representative brain YAML updates (511c730)

Added `DisplaySpec` Pydantic model to `brain_check_schema.py` with four locked fields:
- `value_format`: How to display result.value ("numeric_2dp", "boolean", "text", "pct_1dp")
- `source_type`: Filing type key for date lookup ("SEC_10K", "SEC_DEF14A", "WEB")
- `threshold_context`: Human-readable threshold criterion text
- `deprecation_note`: Non-empty = permanently unanswerable check

`BrainCheckEntry` gets optional `display: DisplaySpec | None = None` — all existing YAMLs load unchanged since no YAML without a `display:` block is affected.

Five brain YAML files updated with `display:` blocks:
- `gov/board.yaml`: `GOV.BOARD.ceo_chair` — `value_format: boolean, source_type: SEC_DEF14A`
- `gov/effect.yaml`: `GOV.EFFECT.iss_score` and `GOV.EFFECT.proxy_advisory` — both with deprecation_note (ISS/Glass Lewis API required)
- `lit/defense.yaml`: `LIT.PATTERN.peer_contagion` — `value_format: boolean, source_type: SEC_10K`
- `fin/forensic.yaml`: `FIN.QUALITY.q4_revenue_concentration` and `FIN.QUALITY.deferred_revenue_trend` — both `value_format: numeric_2dp, source_type: SEC_10K`

### Task 2: Wave 0 failing test scaffolds (c48484b)

Three test files created in RED state before any implementation:

- `tests/stages/render/test_qa_audit_source.py` — 6 tests for `_format_check_source()` function (ImportError RED: function doesn't exist yet)
- `tests/stages/render/test_red_flags_template.py` — 2 tests for `threshold_context` in `extract_scoring()` output (FAIL RED: key not in dict)
- `tests/stages/analyze/test_coerce_value_boolean.py` — 6 tests for bool coercion in `coerce_value()` (2 FAIL RED: True/False not stringified)

### Task 3: FacetSpec schema + Facet YAMLs + html_checks wiring (a55f06c)

New `brain_facet_schema.py` (75 lines) with:
- `FacetSpec` Pydantic model: id, name, display_type, signals, display_config
- `VALID_DISPLAY_TYPES` frozenset for fail-fast validation
- `load_facet()` and `load_all_facets()` utility functions

Two Facet YAML files:
- `brain/facets/governance.yaml`: 12 GOV.* signals, `display_type: scorecard_table`
- `brain/facets/red_flags.yaml`: empty signals list, `display_type: flag_list`; triggered flags sourced from scoring results at render time

`html_checks.py` wired with lazy `_get_facets()` loader — proves schema works without migrating rendering logic (full Facet-driven rendering is Phase 49's job).

## Verification Results

All plan verification checks pass:
1. `from do_uw.brain.brain_check_schema import DisplaySpec, BrainCheckEntry` — exits 0
2. `from do_uw.brain.brain_facet_schema import load_all_facets, FacetSpec` — exits 0
3. `load_all_facets(Path('src/do_uw/brain/facets'))` returns governance and red_flags facets — exits 0
4. `from do_uw.stages.render.html_checks import _get_facets` — exits 0
5. Full test suite (excluding Wave 0): **3967 passed, 2 pre-existing failures** — no regressions
6. Wave 0 tests confirm RED baseline (ImportError + AssertionError before implementation)
7. `brain_check_schema.py`: 153 lines (under 500). `brain_facet_schema.py`: 75 lines (under 100).

## Deviations from Plan

**1. [Rule 1 - Minor] Actual YAML file locations differ from plan frontmatter**
- **Found during:** Task 1 execution
- **Issue:** Plan frontmatter listed `src/do_uw/brain/checks/lit/pattern.yaml` and `src/do_uw/brain/checks/fin/quality.yaml` but these files don't exist. The check IDs `LIT.PATTERN.peer_contagion` and `FIN.QUALITY.*` actually live in `lit/defense.yaml` and `fin/forensic.yaml`.
- **Fix:** Updated the correct YAML files. Check IDs specified in the plan were correct; file paths were wrong.
- **Files modified:** `lit/defense.yaml`, `fin/forensic.yaml`
- **Commit:** 511c730

**2. [Rule 1 - Minor] governance.yaml uses actual check ID GOV.BOARD.ceo_chair**
- **Found during:** Task 3
- **Issue:** Plan specified `GOV.BOARD.ceo_chair_separation` in governance.yaml signals list but the actual check ID is `GOV.BOARD.ceo_chair` (verified in board.yaml).
- **Fix:** Used the real check ID. No behavior change — just correctness.
- **Commit:** a55f06c

## Self-Check: PASSED

- `src/do_uw/brain/brain_check_schema.py`: FOUND (153 lines)
- `src/do_uw/brain/brain_facet_schema.py`: FOUND (75 lines)
- `src/do_uw/brain/facets/governance.yaml`: FOUND
- `src/do_uw/brain/facets/red_flags.yaml`: FOUND
- `tests/stages/render/test_qa_audit_source.py`: FOUND (38 lines)
- `tests/stages/render/test_red_flags_template.py`: FOUND (44 lines)
- `tests/stages/analyze/test_coerce_value_boolean.py`: FOUND (38 lines)
- Commits 511c730, c48484b, a55f06c: FOUND in git log
