---
phase: "03"
plan: "06"
subsystem: "extract"
tags: ["audit-risk", "tax-indicators", "peer-group", "XBRL", "financedatabase"]
dependency_graph:
  requires: ["03-01", "03-03"]
  provides: ["audit-profile-extraction", "tax-indicator-extraction", "peer-group-construction"]
  affects: ["03-07", "phase-4", "phase-5", "phase-7"]
tech_stack:
  added: []
  patterns: ["multi-signal-composite-scoring", "line-by-line-subsidiary-parsing", "file-splitting-for-500-line-limit"]
key_files:
  created:
    - "src/do_uw/stages/extract/audit_risk.py"
    - "src/do_uw/stages/extract/tax_indicators.py"
    - "src/do_uw/stages/extract/peer_group.py"
    - "src/do_uw/stages/extract/peer_scoring.py"
    - "tests/test_audit_tax_peers.py"
  modified: []
decisions:
  - id: "03-06-01"
    description: "Split peer_group.py into peer_group.py + peer_scoring.py to stay under 500 lines"
  - id: "03-06-02"
    description: "Tax haven counting per-line (not per-jurisdiction) to reflect multiple subsidiaries in same haven"
  - id: "03-06-03"
    description: "Opinion type parsing handles both 'present fairly' and 'presents fairly' variants"
  - id: "03-06-04"
    description: "Mock yfinance returns enriched format dict matching _enrich_candidate_yfinance output"
metrics:
  duration: "9m 28s"
  completed: "2026-02-08"
  tests_added: 28
  tests_total: 253
  lines_added: 2010
---

# Phase 3 Plan 6: Audit Risk, Tax Indicators, Peer Group Summary

Audit risk profile extraction from 10-K text/XBRL, tax indicator computation with ETR and haven cross-referencing, and multi-signal peer group construction using 5-signal composite scoring via financedatabase + yfinance.

## Tasks Completed

### Task 1: Audit risk and tax indicator extraction
**Commit:** e6d3134

**audit_risk.py** (478 lines): Extracts 10 audit fields from 10-K filing text and XBRL Company Facts DEI namespace. Big 4 auditor detection (Deloitte, EY, KPMG, PwC), auditor tenure from "served as auditor since" patterns, opinion type parsing (unqualified/qualified/adverse/disclaimer), going concern language detection, material weakness extraction from Item 9A, restatement classification (Big R vs little r), late filing check against SEC deadlines by filer category, comment letter counting from CORRESP filings, and Critical Audit Matter extraction from PCAOB reports.

**tax_indicators.py** (392 lines): Computes 6 tax indicator fields. Effective tax rate from XBRL IncomeTaxExpenseBenefit/pretax income with aggressive threshold flagging (<15% or >30%). ETR trend analysis across up to 3 periods. Deferred tax asset/liability extraction. Exhibit 21 subsidiary cross-referencing against tax_havens.json (32 jurisdictions across zero_tax, low_tax, preferential_regime categories). Unrecognized tax benefits from XBRL. Transfer pricing risk flag when international operations coincide with declining ETR.

### Task 2: Peer group construction and tests
**Commit:** ad8f526

**peer_scoring.py** (127 lines): Five scoring signal functions normalized to 0-100 scale: SIC match (4-digit=100, 3-digit=75, 2-digit=50), industry match (exact=100, sector=50), market cap proximity (linear 0.5x-2.0x band), revenue similarity (ratio-based), description overlap (Jaccard similarity with stop words). Composite weighted score: SIC 25%, industry 20%, market cap 25%, revenue 15%, description 15%.

**peer_group.py** (398 lines): Main `construct_peer_group()` using financedatabase for US equities candidate universe, yfinance for enrichment. Market cap band filter (0.5x-2x tight, 0.3x-3.0x expanded fallback). Override peers force-included first. Top 10 selected by composite score, minimum 5 guaranteed. Peer tiers: primary_sic, sector_etf, market_cap_cohort. Sector ETF lookup from brain/sectors.json.

**tests** (28 tests): 6 audit tests (Big 4, XBRL auditor, opinion types, going concern, material weakness, CAMs), 4 tax tests (ETR normal/aggressive, haven cross-reference, missing data), 11 scoring tests (composite high/partial, SIC 4/3/2-digit, market cap band, revenue similarity, description overlap, industry match), 3 peer group construction tests (minimum count, override inclusion, tier assignment), 4 infrastructure tests (load tax havens, extraction report).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Split peer_group.py into peer_group.py + peer_scoring.py**
- **Found during:** Task 2 initial implementation
- **Issue:** peer_group.py exceeded 500-line limit at 542 lines with scoring functions inline
- **Fix:** Extracted 5 scoring functions and composite score computation into peer_scoring.py (127 lines), leaving peer_group.py at 398 lines
- **Files created:** src/do_uw/stages/extract/peer_scoring.py

**2. [Rule 1 - Bug] Fixed opinion type to handle "present fairly" variant**
- **Found during:** Task 2 test execution
- **Issue:** `_extract_opinion_type` only matched "presents fairly" but SEC filings also use "present fairly" (without trailing 's')
- **Fix:** Added check for both "present fairly" and "presents fairly" in opinion detection
- **Files modified:** src/do_uw/stages/extract/audit_risk.py

**3. [Rule 1 - Bug] Fixed tax haven counting for multiple subsidiaries**
- **Found during:** Task 2 test execution
- **Issue:** `_cross_reference_tax_havens` counted each jurisdiction only once regardless of how many subsidiaries were in that haven
- **Fix:** Changed to line-by-line processing of Exhibit 21, counting each occurrence on separate lines
- **Files modified:** src/do_uw/stages/extract/tax_indicators.py

## Decisions Made

| ID | Decision | Rationale |
|---|---|---|
| 03-06-01 | Split scoring into peer_scoring.py | peer_group.py exceeded 500-line CLAUDE.md limit; clean separation of scoring logic from orchestration |
| 03-06-02 | Per-line tax haven counting | A company with 3 subsidiaries in Cayman Islands should count as 3, not 1, for exposure calculation |
| 03-06-03 | Both "present/presents fairly" accepted | SEC filings use both forms; rejecting valid unqualified opinions would create false negatives |
| 03-06-04 | Test mock returns enriched format | Mock bypasses _enrich_candidate_yfinance so must match its output key format (sic_code, market_cap) not raw yfinance format (sic, marketCap) |

## Verification Results

- `uv run pyright src/do_uw/stages/extract/` -- 0 errors
- `uv run ruff check src/do_uw/` -- 0 errors
- `uv run pytest tests/test_audit_tax_peers.py -v` -- 28 passed
- `uv run pytest tests/ -v` -- 253 passed, 0 failed
- All source files under 500 lines (max: 478 audit_risk.py)

## Next Phase Readiness

Plan 03-06 completes SECT2-09 (peer group), SECT3-05 (peer benchmarking foundation), SECT3-12 (audit risk), and SECT3-13 (tax indicators). With 03-04 (distress/earnings) and 03-05 (debt analysis) also complete, only 03-07 (extract orchestrator) remains in Phase 3.
