# Deferred Items - Phase 52.1

## Pre-existing Test Failures (Not caused by 52.1 changes)

- `tests/brain/test_brain_enrich.py` - 3 failures in TestEnrichmentCompleteness (report_section, total_count, version_2). Likely stale enrichment expectations from Phase 50.1.
- `tests/brain/test_brain_framework.py::test_chains_reference_valid_signal_ids` - Chain YAML references signals not in active set. Pre-existing.
- `tests/brain/test_brain_loader.py::test_field_values_identical` - Round-trip compatibility drift. Pre-existing.

All verified by running against pre-52.1 commit (same failures without our changes).
