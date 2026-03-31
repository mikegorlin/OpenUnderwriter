# Phase 32 Deferred Items

## Pre-existing Test Failures (Discovered During 32-05)

These test failures existed BEFORE Plan 05 execution and are NOT caused by Plan 05 changes.

### 1. test_brain_enrich.py (6 failures)
- `TestEnrichmentCompleteness::test_report_section_distribution`
- `TestSpotChecks::test_fin_liq_position`
- `TestSpotChecks::test_lit_sca_active`
- `TestSpotChecks::test_gov_board_independence`
- `TestSpotChecks::test_biz_class_primary`
- `TestSpotChecks::test_fwrd_event_earnings_calendar`
- **Cause:** 32-04 commit (efa95aa) remapped enrichment_data.py to v6 taxonomy but test expectations were not updated to match the new v6 section names/question IDs.
- **Fix:** Update test_brain_enrich.py to expect v6 taxonomy values.

### 2. test_ground_truth_coverage.py (1 failure)
- `test_item9a_material_weakness[TSLA]` -- expects False, got True
- **Cause:** TSLA ground truth data mismatch (pre-existing).

### 3. test_ground_truth_validation.py (1 failure)
- `test_identity_sector[TSLA]` -- sector assertion mismatch
- **Cause:** TSLA ground truth data mismatch (pre-existing).

### 4. test_llm_litigation_integration.py (1 failure)
- `test_total_reserve_computed` -- LLM litigation integration test
- **Cause:** Pre-existing, unrelated to Plan 05.

### 5. test_render_outputs.py (1 failure)
- `test_render_pdf_returns_none_without_weasyprint`
- **Cause:** Pre-existing, unrelated to Plan 05.
