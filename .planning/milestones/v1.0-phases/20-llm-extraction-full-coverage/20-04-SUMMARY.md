---
phase: 20
plan: 04
subsystem: extract
tags: [llm, company-profile, audit-risk, ownership, file-split, LLM-first, regex-fallback]
depends_on:
  requires: [20-02, 20-03]
  provides: ["LLM-first Item 1 business extraction in company_profile.py", "LLM-first Item 9A controls extraction in audit_risk.py", "LLM-supplemented ownership from DEF 14A in ownership_structure.py"]
  affects: [20-06]
tech_stack:
  added: []
  patterns: ["type-widening cast for SourcedValue dict assignment", "LLM-fill-only-when-empty strategy for ownership"]
key_files:
  created:
    - src/do_uw/stages/extract/profile_item1_helpers.py
    - src/do_uw/stages/extract/audit_risk_helpers.py
    - tests/test_llm_company_profile_integration.py
    - tests/test_llm_audit_risk_integration.py
    - tests/test_llm_ownership_integration.py
  modified:
    - src/do_uw/stages/extract/company_profile.py
    - src/do_uw/stages/extract/audit_risk.py
    - src/do_uw/stages/extract/ownership_structure.py
decisions:
  - id: "20-04-D1"
    description: "LLM customer/supplier concentration mapped to dict[str, str|float] with 0.0 placeholder for numeric fields (converter returns SourcedValue[str] but model requires dict)"
  - id: "20-04-D2"
    description: "LLM material weakness detail only fills when regex found nothing (avoids duplicating regex findings with LLM)"
  - id: "20-04-D3"
    description: "LLM top holders use cast(dict[str, Any]) to widen from converter's dict[str, str] to model's dict[str, Any]"
  - id: "20-04-D4"
    description: "Ownership LLM enrichment runs before activist risk assessment so LLM holders are included in activist check"
metrics:
  duration: "10m 15s"
  completed: "2026-02-11"
  tests_added: 23
  tests_total: 2323
---

# Phase 20 Plan 04: Sub-Orchestrator LLM Integration (company_profile, audit_risk, ownership) Summary

**LLM-first/regex-fallback enrichment for 3 sub-orchestrators with proactive file splits keeping all files under 500 lines. 23 integration tests verify enrichment paths, fallback behavior, and override protection.**

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | LLM integration for company_profile.py with file split | e0ca2d2 | company_profile.py, profile_item1_helpers.py, test_llm_company_profile_integration.py |
| 2 | LLM integration for audit_risk.py and ownership_structure.py | d26d470 | audit_risk.py, audit_risk_helpers.py, ownership_structure.py, test_llm_audit_risk_integration.py, test_llm_ownership_integration.py |

## What Was Built

### company_profile.py -- LLM Item 1 Enrichment (357 lines, down from 483)

Split `_extract_revenue_segments`, `_extract_operational_complexity`, and `_extract_business_changes` to `profile_item1_helpers.py` (281 lines). Added `_enrich_from_llm()` with 6 enrichment paths:

1. **Business description**: LLM replaces regex when longer (richer content)
2. **Geographic footprint**: LLM fills only when Exhibit 21 is empty
3. **Customer concentration**: LLM supplements with SourcedValue[str] mapped to dict format
4. **Supplier concentration**: Same supplement pattern as customer
5. **Operational complexity**: LLM flags (dual-class, VIE) supplement existing regex flags
6. **Employee count**: LLM fills when yfinance is absent

### audit_risk.py -- LLM Item 9A Controls Enrichment (292 lines, down from 478)

Split all regex helpers (auditor name, tenure, opinion, going concern, material weakness, restatement, late filing, comment letters, CAMs) to `audit_risk_helpers.py` (280 lines). Added `_enrich_from_llm()` with strict override protection:

- **Going concern**: NEVER overridden by LLM (XBRL/regex authoritative)
- **Opinion type**: NEVER overridden by LLM (regex authoritative)
- **Material weakness detail**: LLM fills only when regex found nothing
- **Significant deficiencies**: LLM fills (new field, not available from regex)
- **Remediation status**: LLM fills (new field, not available from regex)
- **Auditor name/tenure**: LLM supplements only when regex/XBRL is empty

### ownership_structure.py -- LLM DEF 14A Ownership (496 lines, up from 442)

Added `_enrich_from_llm()` before activist risk assessment:

- **Top holders**: LLM fills when yfinance institutional_holders are empty
- **Insider pct**: LLM fills when yfinance/governance path left empty
- Note: Phase 19 governance path also supplements insider_pct; this path handles independent execution ordering

### Test Coverage (23 new tests)

- 10 tests for company_profile LLM integration (5 test classes)
- 7 tests for audit_risk LLM integration (4 test classes)
- 6 tests for ownership_structure LLM integration (3 test classes)
- Coverage: enrichment path, fallback path, override protection for each sub-orchestrator

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 20-04-D1 | LLM concentration mapped to dict with 0.0 placeholder | Converter returns SourcedValue[str] but CompanyProfile model requires dict[str, str\|float] |
| 20-04-D2 | LLM MW detail only fills when regex is empty | Avoids duplicating regex-found weaknesses with LLM versions |
| 20-04-D3 | Type widening via cast for ownership holders | Converter's dict[str, str] needs to widen to model's dict[str, Any] |
| 20-04-D4 | LLM enrichment before activist risk assessment | Ensures LLM-sourced holders are checked against activist list |

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

```
pyright: 0 errors, 0 warnings, 0 informations (all 5 modified/created source files)
ruff: All checks passed!
pytest: 2323 passed, 14 skipped, 3 xfailed, 1 xpassed
Line counts: company_profile.py 357, audit_risk.py 292, ownership_structure.py 496 (all under 500)
```

## Next Phase Readiness

All three sub-orchestrators now consume LLM converter output from Plans 02 and 03. Plan 05 (parallel) handles the remaining sub-orchestrators (debt_analysis, extract_market, extract_ai_risk). Plan 06 will expand ground truth validation to verify LLM data against actual TSLA/AAPL filings.
