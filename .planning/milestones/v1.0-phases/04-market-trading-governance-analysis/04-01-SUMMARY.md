# Phase 4 Plan 1: ACQUIRE Extensions -- Full-Document-Once Architecture

Full-document-once SEC filing architecture with filing_fetcher.py, section parsing moved to EXTRACT stage, 5 new filing types, and yfinance earnings/analyst/upgrades data.

## Execution Summary

| Field | Value |
|-------|-------|
| Phase | 04 |
| Plan | 01 |
| Status | COMPLETE |
| Tasks | 2/2 |
| Tests Added | 36 (15 filing_fetcher + 21 acquire_extensions) |
| Tests Total | 356 (all passing) |
| Duration | 10m 29s |
| Completed | 2026-02-08 |

## What Was Built

### Task 1: Extended MarketDataClient (68dce96)
- Added `_safe_get_earnings_dates()` wrapping `yf_ticker.get_earnings_dates(limit=20)` with defensive try/except
- Added `_safe_get_analyst_targets()` with DataFrame primary and info dict fallback (targetMeanPrice, targetMedianPrice, etc.)
- Added `upgrades_downgrades` via existing `_safe_get_dataframe()` pattern
- market_client.py: 187 -> 252 lines

### Task 2: Full-Document-Once Architecture (9cb0433)

**NEW: `filing_fetcher.py` (336 lines)**
- `FilingDocument` TypedDict: accession, filing_date, form_type, full_text
- `fetch_filing_document()`: fetches single filing, strips HTML, caches by accession
- `fetch_all_filing_documents()`: fetches ALL filing types from metadata, groups by form type
- `fetch_exhibit_21()`: moved from filing_text.py with added cache support
- `strip_html()`: moved from filing_text.py, made public

**NEW: `filing_sections.py` (136 lines)**
- `SECTION_DEFS`, `extract_section()`, `extract_10k_sections()` moved from ACQUIRE to EXTRACT stage
- Clean ACQUIRE/EXTRACT boundary: ACQUIRE downloads, EXTRACT parses

**REFACTORED: `filing_text.py` (407 -> 180 lines)**
- Thin backward-compatible wrapper delegating to filing_fetcher and filing_sections
- Public API unchanged: `fetch_filing_texts()`, `fetch_filing_content()`

**UPDATED: `sec_client.py` (435 -> 463 lines)**
- New filing types: S-3, S-1, 424B, SC 13D, SC 13G with TTLs and lookbacks
- Calls `fetch_all_filing_documents()` after metadata acquisition
- Stores result as `filing_documents` in result dict
- Backward-compat: still calls `fetch_filing_content()` for Phase 3 extractors

**UPDATED: `sourced.py` (115 -> 164 lines)**
- `get_filing_documents(state)`: returns filing_documents dict keyed by form type
- `get_filing_document_text(state, form_type, index)`: convenience accessor for full text

**UPDATED: `state.py` AcquiredData model**
- New field: `filing_documents: dict[str, list[dict[str, str]]]`

## Key Files

### Created
- `src/do_uw/stages/acquire/clients/filing_fetcher.py` -- Pure document fetcher
- `src/do_uw/stages/extract/filing_sections.py` -- Section parsing (moved from ACQUIRE)
- `tests/test_filing_fetcher.py` -- 15 tests for filing_fetcher
- `tests/test_acquire_extensions.py` -- 21 tests for Phase 4 extensions

### Modified
- `src/do_uw/stages/acquire/clients/market_client.py` -- 3 new data categories
- `src/do_uw/stages/acquire/clients/filing_text.py` -- Refactored to thin wrapper
- `src/do_uw/stages/acquire/clients/sec_client.py` -- 5 new filing types + full-doc fetch
- `src/do_uw/stages/extract/sourced.py` -- 2 new helper functions
- `src/do_uw/models/state.py` -- filing_documents field on AcquiredData
- `tests/test_filing_text.py` -- Updated imports for refactored locations

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| TypedDict for FilingDocument | JSON serialization compatibility with Pydantic state, lighter than dataclass |
| Section parsing in EXTRACT not ACQUIRE | Clean stage boundary: ACQUIRE downloads raw docs, EXTRACT interprets them |
| Backward-compat wrapper in filing_text.py | Phase 3 extractors call get_filing_texts() which reads filing_texts key -- keep working |
| fetch_filing_content() kept alongside fetch_all | Phase 3 extractors depend on filing_texts dict structure; gradual migration |
| strip_html() made public in filing_fetcher | Used by both filing_fetcher and filing_text; public API is cleaner than private |
| Analyst targets fallback to info dict keys | yfinance.analyst_price_targets is unreliable; info dict has targetMeanPrice etc. |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated test_filing_text.py imports**
- **Found during:** Task 2
- **Issue:** Refactoring filing_text.py moved _strip_html, _extract_section, fetch_exhibit_21 to new modules. Existing test imports broke.
- **Fix:** Updated test imports to use new canonical locations (filing_fetcher.strip_html, filing_sections.extract_section, filing_fetcher.fetch_exhibit_21). Updated mock patch targets from filing_text to filing_fetcher for exhibit_21 tests.
- **Files modified:** tests/test_filing_text.py
- **Commit:** 9cb0433

**2. [Rule 3 - Blocking] Pyright strict compliance for filing_fetcher.py**
- **Found during:** Task 2
- **Issue:** Cache dict returns Unknown type values; iteration over filings_metadata values produces Unknown types.
- **Fix:** Added `cast()` for cached dict access and typed_filings iteration per established project pattern.
- **Files modified:** src/do_uw/stages/acquire/clients/filing_fetcher.py
- **Commit:** 9cb0433

## Verification Results

- `ruff check`: All checks passed
- `pyright`: 0 errors, 0 warnings, 0 informations
- `pytest`: 356 passed, 0 failed (92 new tests from Plans 01-03 combined)
- All files under 500 lines (max: sec_client.py at 463)

## Next Phase Readiness

This plan provides the data acquisition foundation for Phase 4's analysis plans:
- **Plan 04-04+**: Can use `get_filing_document_text(state, "DEF 14A")` for governance extraction
- **Plan 04-05+**: Can use `get_filing_document_text(state, "4")` for insider trading XML parsing
- **Plan 04-06+**: Can use `get_filing_document_text(state, "8-K")` for leadership change detection
- **Plan 04-07+**: Can use `state.acquired_data.market_data["earnings_dates"]` for market analysis
- **SC 13D/SC 13G**: Available for activist investor detection in later plans
