# Deferred Items - Phase 91

## Pre-existing Test Failure

**File:** tests/brain/test_brain_contract.py::TestSignalAuditTrail::test_threshold_provenance_categorized
**Issue:** STOCK.PRICE.drawdown_duration has threshold_provenance.source='sca_settlement_data' which is not in the valid sources set {'calibrated', 'standard', 'unattributed'}. This existed before Phase 91 changes.
**Fix:** Either add 'sca_settlement_data' to valid_sources in the test, or reclassify the provenance source.
