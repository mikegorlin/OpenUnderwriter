# Deferred Items - Phase 56

## Pre-existing Test Failures (Out of Scope)

These test failures existed before Phase 56 changes and are unrelated to facet-driven rendering:

1. **test_brain_enrich.py::TestEnrichmentCompleteness::test_management_display_have_report_section** - Expects 99 MANAGEMENT_DISPLAY with report_section, gets 98
2. **test_enriched_roundtrip.py::test_content_type_filter_counts** - Expects 99 MANAGEMENT_DISPLAY, gets 98
3. **test_enriched_roundtrip.py::test_enriched_check_validates_against_definition** - SignalDefinition validation error on V2 presentation fields (extra_forbidden)
4. **test_regression_baseline.py::test_baseline_file_exists** - Missing 47-baseline.json file
