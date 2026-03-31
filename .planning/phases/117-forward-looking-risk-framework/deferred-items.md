# Deferred Items - Phase 117

## Pre-existing Test Failure

- **File:** `tests/brain/test_brain_contract.py::TestSignalAuditTrail::test_threshold_provenance_categorized`
- **Issue:** FIN.ACCT.ohlson_o_score threshold_provenance.source is 'academic' but test expects values from the set {'academic_research', 'calibrated', ...}
- **Scope:** Unrelated to Phase 117 changes. Pre-existing brain YAML data issue.
- **Action:** Fix the ohlson_o_score YAML to use 'academic_research' instead of 'academic', or update the test valid_sources set.

## Additional Pre-existing Test Failures (identified during 117-06)

- **test_contract_enforcement.py::test_real_manifest_template_agreement** - Orphaned templates: crf_banner, decision_record, scorecard, executive_brief, governance/*, scoring/factor_detail, litigation/*
- **test_template_facet_audit.py::test_no_orphaned_group_templates** - Same orphan set as above (worksheet-level includes not declared as manifest groups)
- **test_template_purity.py::test_company_templates_have_no_hardcoded_thresholds** - Hardcoded threshold in company template
- **test_peril_scoring_html.py::test_peril_scoring_key_present_with_brain_data** - SimpleNamespace mock missing signal_contributions attribute
- **test_inference_evaluator.py::TestSingleValueFallback** - Evidence string format changed ("Single signal present" vs "Single signal only")
