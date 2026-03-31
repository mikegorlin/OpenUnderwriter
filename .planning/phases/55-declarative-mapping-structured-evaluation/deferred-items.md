# Phase 55 Deferred Items

## Pre-existing Test Failures (Out of Scope)

1. **test_brain_enrich.py::test_management_display_have_report_section** - Expects 99, gets 98. Pre-existing count mismatch unrelated to Phase 55 changes.

2. **test_enriched_roundtrip.py::test_content_type_filter_counts** - Pre-existing count mismatch in knowledge roundtrip tests.

3. **test_regression_baseline.py::test_baseline_file_exists** - Missing baseline file from Phase 47 (47-baseline.json). Pre-existing infrastructure gap.

## Plan 55-02 Deferred Items

4. **signal_engine.py at 579 lines** - Exceeds 500-line limit from CLAUDE.md. Shadow evaluation added ~138 lines. Consider splitting _evaluate_v2_signal + _log_shadow_evaluation into a separate `shadow_evaluator.py` module in a future refactor plan.

5. **Pre-existing test failures in knowledge/ module** - test_enrichment.py, test_enriched_roundtrip.py, test_migrate.py all have stale count assertions (99 vs 98, 263 vs 270) from MANAGEMENT_DISPLAY content_type reclassification. Not caused by Phase 55.

6. **Pre-existing test failure in acquire/** - test_orchestrator_brain.py::test_brain_requirements_logged has assertion mismatch. Not caused by Phase 55.
