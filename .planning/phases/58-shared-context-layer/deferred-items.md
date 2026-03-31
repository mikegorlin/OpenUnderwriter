# Deferred Items - Phase 58

## Pre-existing Test Failures (Out of Scope)

These 19 test failures exist on the pre-change codebase and are NOT caused by Phase 58 changes.

### Brain Data Count Mismatches
- `tests/brain/test_brain_framework.py` - ModuleNotFoundError: No module named 'do_uw.brain.legacy'
- `tests/brain/test_brain_enrich.py::test_management_display_have_report_section` - Expected 99, got 98
- `tests/knowledge/test_enriched_roundtrip.py::test_content_type_filter_counts` - Expected 99, got 98
- `tests/knowledge/test_enriched_roundtrip.py::test_enriched_check_validates_against_definition`
- `tests/knowledge/test_enrichment.py::TestContentType::test_content_type_distribution`
- `tests/knowledge/test_enrichment.py::TestContentType::test_management_display_checks_mostly_no_factors`
- `tests/knowledge/test_enrichment.py::TestContentType::test_management_display_checks_mostly_context_display`
- `tests/knowledge/test_enrichment.py::TestFieldKey::test_field_key_coverage`
- `tests/knowledge/test_enrichment.py::TestFieldKey::test_field_key_checks_have_primary_source`
- `tests/knowledge/test_enrichment.py::TestExistingFieldsPreserved::test_existing_fields_preserved`
- `tests/knowledge/test_migrate.py::TestChecksMigration::test_check_sections`
- `tests/knowledge/test_migrate.py::TestChecksMigration::test_specific_check_lookup`

### Other Pre-existing Failures
- `tests/stages/acquire/test_orchestrator_brain.py::test_brain_requirements_logged`
- `tests/stages/analyze/test_regression_baseline.py::test_baseline_file_exists`
- `tests/test_forensic_composites.py::TestChecksJson::test_all_checks_have_classification`
- `tests/test_phase26_integration.py::TestBrainChecks::test_backward_compat_no_regression`
- `tests/test_render_coverage.py::TestMultiFormatCoverage::test_word_coverage_exceeds_90_percent`
- `tests/test_render_coverage.py::TestMultiFormatCoverage::test_html_coverage_exceeds_90_percent`
- `tests/test_signal_classification.py` (3 tests)
