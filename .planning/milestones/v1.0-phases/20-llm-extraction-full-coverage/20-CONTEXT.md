# Phase 20: LLM Extraction — Full Coverage - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend LLM extraction to ALL remaining filing sections (Item 1, Item 7, Item 8 Footnotes, Item 9A, 8-K Events, DEF 14A Ownership, AI Risk). After this phase, every data point in the worksheet comes from XBRL, LLM, or structured API — zero reliance on regex for primary data. The pattern is established from Phase 19 (LLM-first with regex fallback). This phase applies it everywhere else.

</domain>

<decisions>
## Implementation Decisions

### Extraction scope & ordering
- ALL 7 section areas built in a single wave, all parallel — no prioritization, no phasing within the phase
- Every section matters equally for underwriting — there is no "nice to have"
- Extend existing TenKExtraction / DEF14AExtraction / EightKExtraction Pydantic schemas with new fields (not separate schemas)
- One LLM call per filing type, richer output — same call extracts more fields

### Converter module structure
- Group converters by filing type, NOT by domain area
  - `ten_k_converters.py` — Items 1, 7, 8 footnotes, 9A together
  - `eight_k_converter.py` — Executive departures, material agreements, acquisitions, restatements
  - `proxy_ownership_converter.py` — DEF 14A ownership tables, 5% holders
- Fewer files, grouped by source document — split at 500-line limit as needed

### LLM vs regex fallback
- Same pattern everywhere: LLM-first, regex fallback — consistent with Phase 19
- Regex extractors stay as fallback when LLM returns nothing
- --no-llm flag continues to work (debugging use — worksheet will have gaps)
- Claude decides per-section whether to merge LLM + regex for partial results or treat LLM as authoritative

### Data completeness
- Target: 100% field coverage or documented reason why a field is unavailable
- "Not Available" is acceptable only when the company genuinely doesn't disclose something
- XBRL always wins for financial numbers — LLM supplements with qualitative context but never overrides audited structured data
- FPI companies (20-F): FPI-aware schemas map FPI disclosures to domestic fields where possible, explicitly mark unavailable where not

### Ground truth expansion
- Significantly expand ground truth test cases to cover the new sections
- Add 20+ new ground truth fields covering Items 1/7/8/9A, 8-K events, ownership
- Hand-verify against actual filings for TSLA and AAPL at minimum

### Cost management
- Budget increased to $2.00/company (up from $1.00) to accommodate full-coverage extraction
- Batch API support deferred to Phase 21 (production hardening)
- Claude decides cost tracking granularity (per filing type vs per section)

### Claude's Discretion
- AI risk extraction approach (same LLM pattern vs multi-source special case)
- LLM + regex merging strategy per section (authoritative LLM vs merge)
- Large filing handling (chunking by section vs truncation)
- Cost tracking granularity level
- --no-llm degradation strategy (debugging-only vs usable)

</decisions>

<specifics>
## Specific Ideas

- Phase 19 proved the pattern works: LLM-first extraction with regex fallback for governance (DEF 14A) and litigation (10-K Items 3/8/1A)
- The user's core concern: the system must actually produce worksheets with complete information — every section, every field, sourced from real filing data. No gaps, no generic defaults, no garbage regex output
- "100% or explain why not" — the bar is that every field is populated with real data, or there's a documented reason the data doesn't exist for that company

</specifics>

<deferred>
## Deferred Ideas

- Batch API support for bulk runs (50% discount) — Phase 21
- Multi-ticker validation across 20+ companies — Phase 21
- Worksheet redesign for complete data — Phase 22

</deferred>

---

*Phase: 20-llm-extraction-full-coverage*
*Context gathered: 2026-02-10*
