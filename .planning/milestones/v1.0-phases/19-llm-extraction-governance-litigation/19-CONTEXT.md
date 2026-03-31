# Phase 19: LLM Extraction — Governance & Litigation (P0) - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the worst regex extractors with LLM extraction for the most critical D&O underwriting data sources — DEF 14A governance/compensation, 10-K Item 3 litigation/contingencies, and Item 1A risk factors. After this phase, Sections 5 and 6 transform from harmful/useless to genuinely valuable. The LLM extraction infrastructure (Phase 18) already exists — Phase 19 is about CONSUMING those results to populate domain models with HIGH confidence data.

External-source extractors (Stanford SCAC, SEC enforcement, yfinance) remain untouched for their primary data but are updated to merge cleanly with LLM results.

</domain>

<decisions>
## Implementation Decisions

### LLM vs Regex Strategy
- **LLM replaces regex entirely** when LLM extraction succeeds for a filing. If LLM produced a result for DEF 14A, skip regex governance extractors. Regex only runs when LLM returned None (API down, over budget, etc.)
- **Field-level fallback**: If LLM returned null for a specific field, run targeted regex extraction for just that field. LLM result is not all-or-nothing — missing individual fields trigger regex fallback for those fields only
- Source text attribution is **nice-to-have for key fields** — high-impact fields (legal proceedings, compensation totals, board independence) should include source passages, but not every minor field. This reduces token usage
- The Phase 18 `source_passage` fields on ExtractedDirector, ExtractedCompensation, ExtractedLegalProceeding already capture this for key items

### Extraction Scope
- Claude decides the exact split of what goes in Phase 19 vs Phase 20 based on complexity/dependency analysis during planning. All four P0 targets (governance, compensation, litigation, risk factors) are in scope but can be prioritized
- **Schema expansion**: Claude evaluates each field gap and expands Phase 18 schemas only where the field is critical for underwriting AND the LLM can reliably extract it from filing text
- **External source merge**: Phase 19 updates external-source extractors to merge cleanly with LLM results (e.g., LLM finds directors from DEF 14A, Stanford SCAC adds their prior litigation history). Not just filing-text extraction — complete integration
- Target: 100% accuracy AND coverage. Not a tradeoff between them

### Data Mapping
- Claude decides where conversion logic lives (new converter modules vs inline in extractors) based on code organization and 500-line constraints
- Claude decides deserialization strategy (on-demand vs pre-deserialized once) based on performance and simplicity
- **Confidence levels**: LLM-extracted data gets **HIGH confidence** (same as XBRL), since it reads actual SEC filing text. Regex-extracted data stays LOW/MEDIUM
- **Source citation**: Source becomes `'DEF 14A (LLM)'` or `'10-K (LLM)'` to distinguish from regex extraction. Helps debugging and audit trail

### Ground Truth & Validation
- Claude picks test companies based on which have the most interesting/challenging governance and litigation disclosures
- **Full field verification**: Every extracted field verified against the actual filing. No spot-checking — comprehensive validation
- **Live API for validation**: Run actual LLM extraction against real filings to validate quality. Tests the real pipeline
- **Explicit absence handling**: Fields should distinguish between 'not found' (extraction failure) and 'not disclosed' (company genuinely doesn't have this). The LLM should actively confirm absence, not just return null

### Claude's Discretion
- Whether to refactor existing extractors in-place or create new LLM consumer modules (based on file size constraints and code organization)
- Pre-deserialization strategy (once at orchestrator level vs on-demand per extractor)
- Which specific schema fields to expand (evaluate gap criticality vs extraction reliability)
- Test company selection for ground truth validation
- Plan splitting (how many plans, which extractors per plan)

</decisions>

<specifics>
## Specific Ideas

- The Phase 18 field mapping analysis revealed strong LLM coverage (80-100%) for board composition and compensation, moderate coverage for litigation proceedings, and weak coverage for SEC enforcement, contingent liability details, and workforce/product litigation
- Key schema gaps to evaluate for expansion: contingent liability amounts/ranges/ASC 450 classification, clawback policies, performance metrics, deal litigation type classification
- Some domain fields are ONLY available from external sources (Stanford SCAC for prior litigation, SEC EDGAR for comment letters, yfinance for ownership %). These extractors stay but need clean merge with LLM data
- DEF14AExtraction already has: directors, named_executive_officers, board composition, anti-takeover provisions, say-on-pay, shareholder proposals, ownership percentages, D&O insurance mentions
- TenKExtraction already has: legal_proceedings (Item 3), risk_factors (Item 1A), contingent_liabilities (text only), going_concern, material_weaknesses, debt instruments

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 19-llm-extraction-governance-litigation*
*Context gathered: 2026-02-10*
