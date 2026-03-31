---
phase: 03-company-profile-financial-extraction
plan: 01
subsystem: models, extract, acquire
tags: [pydantic, xbrl, sec-edgar, extraction-validation, company-facts, peer-group]

# Dependency graph
requires:
  - phase: 01-project-scaffolding
    provides: Pydantic models (SourcedValue, CompanyProfile, FinancialStatements, DistressIndicators)
  - phase: 02-company-resolution-data-acquisition
    provides: SECFilingClient, rate_limiter, sec_get
provides:
  - Typed financial statement models (FinancialLineItem, FinancialStatement)
  - DistressResult with zone classification and trajectory
  - PeerCompany/PeerGroup models for multi-signal peer construction
  - XBRL concept mapping config (50 concepts)
  - Tax havens config (32 jurisdictions)
  - ExtractionReport validation framework
  - XBRL concept resolver with fallback tags
  - Company Facts API acquisition
  - CompanyProfile expanded with all SECT2 fields
  - ExtractedFinancials expanded with SECT3 analysis fields
affects: [03-02, 03-03, 03-04, 03-05, 04-analysis, 05-scoring]

# Tech tracking
tech-stack:
  added: [financedatabase, edgartools]
  patterns: [ExtractionReport validation, XBRL tag fallback resolution, Company Facts API]

key-files:
  created:
    - src/do_uw/config/xbrl_concepts.json
    - src/do_uw/config/tax_havens.json
    - src/do_uw/stages/extract/validation.py
    - src/do_uw/stages/extract/xbrl_mapping.py
    - tests/test_extract_foundation.py
  modified:
    - pyproject.toml
    - src/do_uw/models/company.py
    - src/do_uw/models/financials.py
    - src/do_uw/models/__init__.py
    - src/do_uw/stages/acquire/clients/sec_client.py

key-decisions:
  - "lambda: [] for dataclass default_factory (pyright strict list[Unknown] fix)"
  - "ExtractionReport as @dataclass not Pydantic (simpler, no DB persistence needed)"
  - "XBRLConcept as TypedDict (lightweight schema for JSON config entries)"
  - "Company Facts integrated into SECFilingClient.acquire() via company_facts key"
  - "Coverage thresholds: >=80% HIGH, 50-79% MEDIUM, <50% LOW"

patterns-established:
  - "ExtractionReport: every extraction must produce a validation report comparing found vs expected"
  - "XBRL tag fallback: try tags in priority order, log which tag matched"
  - "Deduplication by end+fy+fp: prefer most recently filed entry per period"
  - "Company Facts as ACQUIRE expansion: one API call per company for all XBRL data"

# Metrics
duration: 8min
completed: 2026-02-08
---

# Phase 3 Plan 1: Extraction Foundation Summary

**Typed financial models, XBRL concept mapping (50 tags), extraction validation framework, and Company Facts API acquisition**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-08T05:19:17Z
- **Completed:** 2026-02-08T05:27:09Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Expanded CompanyProfile with 9 SECT2 fields (industry, business model, concentration, complexity, changes, D&O exposure, events, summary)
- Replaced dict[str, Any] financial models with typed FinancialLineItem/FinancialStatement/DistressResult/PeerCompany/PeerGroup models
- Built XBRL concept mapping config with 50 US GAAP concepts and 3-5 fallback tags each
- Created extraction validation framework (ExtractionReport) that prevents silent incompleteness and imputation
- Added Company Facts API acquisition to SECFilingClient for bulk XBRL data retrieval
- 21 new tests, all 126 tests passing, 0 pyright errors, 0 ruff errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand Pydantic models, add dependencies, create config files** - `8470b53` (feat)
2. **Task 2: Extraction validation framework, XBRL resolver, Company Facts acquisition, and tests** - `c38bc42` (feat)

## Files Created/Modified
- `pyproject.toml` - Added financedatabase and edgartools dependencies
- `src/do_uw/models/company.py` - Expanded CompanyProfile with 9 SECT2 fields
- `src/do_uw/models/financials.py` - Typed FinancialLineItem, FinancialStatement, DistressZone, DistressResult, PeerCompany, PeerGroup, and SECT3 fields on ExtractedFinancials
- `src/do_uw/models/__init__.py` - Updated exports for 6 new model classes
- `src/do_uw/config/xbrl_concepts.json` - 50 US GAAP concept mappings with fallback XBRL tags
- `src/do_uw/config/tax_havens.json` - 32 tax haven jurisdictions in 3 categories
- `src/do_uw/stages/extract/validation.py` - ExtractionReport, create_report, validate_no_imputation, merge_reports, log_report
- `src/do_uw/stages/extract/xbrl_mapping.py` - load_xbrl_mapping, resolve_concept, extract_concept_value, get_latest_value, get_period_values
- `src/do_uw/stages/acquire/clients/sec_client.py` - acquire_company_facts method + Company Facts URL
- `tests/test_extract_foundation.py` - 21 tests for validation, XBRL resolver, Company Facts

## Decisions Made
- **ExtractionReport as @dataclass:** Simpler than Pydantic for internal validation reports that do not need DB persistence or serialization
- **XBRLConcept as TypedDict:** Lightweight schema matching the JSON config structure without overhead of a full model class
- **Company Facts in acquire():** Integrated into the existing SECFilingClient.acquire() method, stored as `result["company_facts"]`
- **Coverage thresholds:** >=80% HIGH, 50-79% MEDIUM, <50% LOW -- aligned with reasonable extraction expectations
- **lambda: [] for dataclass defaults:** Same pyright strict fix used throughout the project for list default_factory

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pyright strict `list[Unknown]` in dataclass defaults**
- **Found during:** Task 2 (validation.py)
- **Issue:** `field(default_factory=list)` produces `list[Unknown]` under pyright strict mode
- **Fix:** Changed to `field(default_factory=lambda: [])` (same pattern used across project)
- **Files modified:** src/do_uw/stages/extract/validation.py
- **Verification:** pyright passes with 0 errors
- **Committed in:** c38bc42

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Known pyright strict pattern, consistent with prior decisions. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Phase 3 foundation models, configs, and utilities are in place
- Next plans can build individual extractors (financial statements, company profile, distress models) on top of this foundation
- XBRL concept resolver tested and ready for financial statement extraction
- Company Facts data will be available in acquired_data.filings["company_facts"]
- ExtractionReport pattern ready for all subsequent extractors to use

---
*Phase: 03-company-profile-financial-extraction*
*Completed: 2026-02-08*
