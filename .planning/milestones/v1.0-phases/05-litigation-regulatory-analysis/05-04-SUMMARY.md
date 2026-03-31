---
phase: 05-litigation-regulatory-analysis
plan: 04
subsystem: extract
tags: [litigation, defense-assessment, pslra, forum-provisions, sol, contingent-liabilities, asc-450, industry-claims]

# Dependency graph
requires:
  - phase: 05-01
    provides: "Litigation models (DefenseAssessment, IndustryClaimPattern, SOLWindow, ContingentLiability), claim_types.json, industry_theories.json configs"
provides:
  - "Defense assessment extractor (forum provisions, PSLRA, prior dismissals, overall strength)"
  - "Industry claim pattern extractor (SIC-to-theory mapping, contagion risk)"
  - "SOL mapper (dual SOL+repose windows from config with trigger date resolution)"
  - "Contingent liability extractor (ASC 450 classification, accrued amounts, ranges, reserves)"
affects: [05-05, phase-6-scoring, phase-7-render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Trigger date resolution chain: SCA cases -> enforcement actions -> proxy 10-K date"
    - "ASC 450 regex classification with probability-based categorization"
    - "Config-driven claim type windows with dual expiry computation"

key-files:
  created:
    - src/do_uw/stages/extract/defense_assessment.py
    - src/do_uw/stages/extract/industry_claims.py
    - src/do_uw/stages/extract/sol_mapper.py
    - src/do_uw/stages/extract/contingent_liab.py
    - tests/test_defense_assessment.py
    - tests/test_industry_claims.py
    - tests/test_sol_mapper.py
    - tests/test_contingent_liab.py

key-decisions:
  - "CompanyIdentity.sic_code field (not .sic) used for SIC code access"
  - "PeerCompany has plain str fields (name, ticker) not SourcedValue -- enrichment uses direct string access"
  - "Contingent liability extractor returns 3-tuple (liabilities, reserve, report) per plan specification"
  - "SOL window requires both SOL and repose to be open for window_open=True"
  - "Item 3 matters default to reasonably_possible ASC 450 classification with LOW confidence"

patterns-established:
  - "Trigger date fallback chain: specific events -> proxy dates with confidence degradation"
  - "Dollar amount parsing with million/billion multipliers for financial text extraction"
  - "Deduplication by first-100-chars prefix matching for contingent liabilities"

# Metrics
duration: 9min
completed: 2026-02-08
---

# Phase 5 Plan 4: Defense/SOL/Contingent Extractors Summary

**Defense assessment parsing forum provisions + PSLRA safe harbor, industry claims mapping SIC to legal theories, SOL mapper computing dual windows, and contingent liabilities extracting ASC 450 classifications from 10-K footnotes**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-08T17:44:08Z
- **Completed:** 2026-02-08T17:53:08Z
- **Tasks:** 2
- **Files created:** 8

## Accomplishments
- Defense assessment parses federal/exclusive forum provisions from DEF 14A, classifies PSLRA safe harbor usage (STRONG/MODERATE/WEAK/NONE), evaluates truth-on-the-market viability, checks prior dismissals, and computes overall defense strength
- Industry claim patterns map company SIC code to legal theories from config with contagion risk detection and peer group enrichment
- SOL mapper computes dual windows (statute of limitations + statute of repose) for all claim types from config, with trigger date resolution from SCA cases, enforcement actions, or proxy 10-K dates
- Contingent liabilities extracted from full 10-K text with ASC 450 classification, accrued amounts, range disclosures, total litigation reserve, and Item 3 pending matter parsing
- 65 tests covering all extractors, 705 total tests passing, 0 lint/type errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Defense assessment + industry claim patterns** - `9317a9f` (feat)
2. **Task 2: SOL mapper + contingent liabilities** - `ab2a854` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/defense_assessment.py` - Forum provisions, PSLRA safe harbor, defense strength assessment (479 lines)
- `src/do_uw/stages/extract/industry_claims.py` - SIC-to-theory mapping with contagion risk (331 lines)
- `src/do_uw/stages/extract/sol_mapper.py` - Dual SOL/repose window computation from config (362 lines)
- `src/do_uw/stages/extract/contingent_liab.py` - ASC 450 contingency extraction from 10-K footnotes (485 lines)
- `tests/test_defense_assessment.py` - 18 tests for forum detection, PSLRA, dismissals, strength
- `tests/test_industry_claims.py` - 12 tests for SIC matching, theory loading, contagion risk
- `tests/test_sol_mapper.py` - 13 tests for window computation, trigger dates, sorting
- `tests/test_contingent_liab.py` - 22 tests for ASC 450, amounts, ranges, reserves, deduplication

## Decisions Made
- Used `CompanyIdentity.sic_code` field name (not `.sic`) per the actual model definition
- PeerCompany has plain `str` fields (name, ticker), not SourcedValue -- enrichment accesses them directly
- Contingent liability extractor returns 3-tuple per plan spec so sub-orchestrator can populate total_litigation_reserve separately
- SOL `window_open` requires BOTH SOL and repose to be open (conservative approach matching legal practice)
- Item 3 pending matters default to `reasonably_possible` ASC 450 classification with LOW confidence (most common treatment)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed CompanyIdentity.sic field name**
- **Found during:** Task 1 (industry_claims.py)
- **Issue:** Plan referenced `state.company.identity.sic` but actual model field is `sic_code`
- **Fix:** Used `sic_code` field name and removed unnecessary None check on `identity` (it is a required field on CompanyProfile)
- **Files modified:** src/do_uw/stages/extract/industry_claims.py
- **Committed in:** 9317a9f

**2. [Rule 1 - Bug] Fixed PeerCompany field access pattern**
- **Found during:** Task 1 (industry_claims.py)
- **Issue:** Plan implied SourcedValue fields on PeerCompany but they are plain str fields
- **Fix:** Access `peer.name` and `peer.ticker` directly without `.value`
- **Files modified:** src/do_uw/stages/extract/industry_claims.py
- **Committed in:** 9317a9f

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for pyright strict compliance and correct field access. No scope creep.

## Issues Encountered
- CompanyIdentity requires `ticker` as a required constructor argument -- test helper needed `CompanyIdentity(ticker="TEST")`

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 extractors (SECT6-09 through SECT6-12) complete with ExtractionReport validation
- Ready for 05-05 sub-orchestrator integration that will wire these into the extract pipeline
- Defense assessment, industry claims, SOL windows, and contingent liabilities populate LitigationLandscape fields

---
*Phase: 05-litigation-regulatory-analysis*
*Completed: 2026-02-08*
