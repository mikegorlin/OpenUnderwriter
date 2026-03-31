# Phase 3: Company Profile & Financial Extraction - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Parse raw acquired data (SEC filings, market data from Phase 2) into structured facts covering the full company profile (Section 2: 11 requirements) and financial health analysis (Section 3: 13 requirements). This is the EXTRACT pipeline stage. All 24 requirements should be fully implemented — no stubbing or deferring of individual fields. When data sources are needed beyond what Phase 2 acquired, expand ACQUIRE within this phase.

</domain>

<decisions>
## Implementation Decisions

### XBRL Extraction Strategy
- XBRL is the primary extraction source for financial data
- Text-based fallback when XBRL fields are missing or non-standard (Claude decides approach per data type — regex vs. LLM-assisted)
- No need to handle filings prior to 2019 (all target companies have inline XBRL)
- Build a canonical mapping table of common XBRL elements (~50 US GAAP concepts) to standard field names, rather than relying solely on library normalization

### Peer Group Construction
- Multi-signal composite approach: combine SIC, NAICS, GICS, ETF holdings, and revenue segment similarity into a composite peer score (SIC alone is inadequate)
- Market cap band: 0.5x to 2x target company's market cap
- Research needed: identify best free/accessible sources for GICS codes and ETF holdings data
- CLI flag `--peers` to allow user override/supplement of auto-generated peer list (auto-peers fill remaining slots)

### Distress Score Edge Cases
- Use modified/sector-appropriate models for financial companies (banks, insurance, REITs) — e.g., Altman Z''-Score for non-manufacturing, bank-specific models
- Partial scores with flags when inputs are missing: compute what's possible, mark as 'partial', list missing inputs
- For early-stage/pre-revenue companies: substitute appropriate alternative metrics (cash runway, burn rate, etc.) rather than forcing standard models. Explain why the substitution was made.
- 4-quarter trajectory shows both numerical score values AND zone classifications (safe/gray/distress)

### Extraction Depth and Data Gaps
- Full extraction of all fields across all 24 requirements — no phased rollout or TODO markers
- When extraction needs a data source not acquired in Phase 2, expand ACQUIRE within Phase 3 (phase boundary is flexible for data acquisition)
- When exact data isn't available: derive estimate if possible (LOW confidence), otherwise mark Not Available with reason code ('not_disclosed', 'no_source', 'not_applicable')

### Extraction Validation (CRITICAL — Trust-Defining)
- **Known failure modes to prevent:**
  1. **Silent incompleteness** — extracting 3 of 12 income statement line items and presenting it as "the income statement." The system must know how many items it SHOULD have and verify it got them.
  2. **Silent imputation** — filling in a revenue segment or financial field that doesn't exist in the filing because the model "expected" it. If a company reports 2 segments, the output must show 2 segments, not 4.
- **Completeness validation:** Every extraction must compare what it found against what it expected to find. For financial statements: validate against the filing's own table of contents / line item count. For segments: validate against the company's actual segment disclosures. Log extraction coverage (e.g., "extracted 11/11 income statement line items" or "extracted 8/12 — missing: [list]").
- **Anti-imputation rule:** The system must NEVER generate data that isn't in the source. If a field isn't in the filing, it's "Not Available" — not a plausible-looking number. This applies to segments, subsidiaries, geographic breakdowns, and all other structured data.
- **Source traceability:** Every extracted value must trace back to a specific location in a specific filing (filing type, date, and ideally the XBRL element name or section heading). An underwriter should be able to verify any number by going to the cited source.
- **Extraction audit log:** Each extraction run should produce a validation summary: fields expected vs. fields found, confidence levels, any fallbacks used, and any gaps. This is internal (not in the final document) but essential for debugging and trust.

### Underwriter Trust (Cross-Cutting Principle)
- This system is the underwriter's PRIMARY analysis source — trust is non-negotiable
- The moment an underwriter can't trust ANY piece of data, the ENTIRE system loses credibility
- Every derived or estimated value must carry an inline confidence badge visible in output: 'ESTIMATED', 'DERIVED', or similar
- The underwriter must always know whether a number came from an audited source, was derived from related data, or is an estimate
- Existing CLAUDE.md rules apply: every data point has source + confidence + citation
- NEVER impute or estimate without making it immediately visible
- Prefer an honest gap ("Not Available") over a plausible-looking fabrication — every time

### Claude's Discretion
- Text fallback approach per data type (regex patterns vs. LLM-assisted extraction)
- Peer group caching strategy (cache with TTL vs. fresh each run)
- Specific alternative metrics for early-stage companies (Claude determines what's meaningful for D&O context)
- Internal implementation of composite peer scoring algorithm

</decisions>

<specifics>
## Specific Ideas

- "SIC code is notoriously a bad way to determine sector and peer group" — user wants genuinely comparable peers, not just same-SIC companies
- "The key in this system is that the underwriter needs to be able to trust it as its primary analysis source" — this principle should guide every extraction decision. When in doubt, flag uncertainty rather than presenting a best guess as fact.
- "If the metrics we're suggesting are the right ones, figure out what the right comparable metrics are" — for edge cases (financials, early-stage), don't force inappropriate models. Research and use the right tools for the job.
- "We've had multiple issues with extractions — extracting only very small parts or imputing segments." Prior extraction attempts produced output that looked complete but wasn't. This is the #1 risk to mitigate in Phase 3. The researcher and planner must prioritize validation mechanisms that catch these failures before they reach the underwriter.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-company-profile-financial-extraction*
*Context gathered: 2026-02-07*
