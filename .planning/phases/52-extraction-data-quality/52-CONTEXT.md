# Phase 52: Extraction Data Quality - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix 4 high-severity data quality issues found in SNA validation audit: board director extraction from DEF 14A, guidance vs consensus mislabeling, litigation false positives from boilerplate 10-K language, and volume spike detection upgrade. All fixes are extraction/analysis layer changes — no new pipeline stages or rendering overhauls.

</domain>

<decisions>
## Implementation Decisions

### Board Director Extraction
- Extract core governance fields per director: name, independence status, committee memberships, tenure, age, qualifications summary
- Qualifications as structured tags (not free text): industry expertise, financial expert, legal/regulatory, technology, public company experience, prior C-suite — binary flags per director
- Populate existing BoardForensicProfile model (add missing fields) rather than creating a separate board_directors array — one source of truth per director
- Accept LLM extraction output, mark all as MEDIUM confidence — no cross-check against proxy header count
- Source: DEF 14A proxy statement parsing

### Guidance vs Consensus
- Determine if company provides forward guidance via 10-K/10-Q language check — search for "forward-looking statements", "guidance range", "we expect revenue of" etc.
- If no explicit guidance language found: provides_forward_guidance=False
- Non-guiding companies: display analyst estimates labeled as "Analyst Consensus (not company guidance)" — still show data but don't evaluate as company guidance
- For companies that DO provide guidance: extract actual guidance ranges from filings
- Extraction priority: 8-K earnings releases first, fall back to 10-Q outlook sections
- FIN.GUIDE.* checks only evaluate against company-issued numbers, not analyst consensus

### Litigation Filtering
- Minimum evidence for a real CaseDetail: named parties (plaintiff name or "class of shareholders") AND court/jurisdiction AND approximate filing date
- Boilerplate with zero specifics = rejected (not a CaseDetail)
- Defense in depth: tighten LLM extraction prompt to require specifics AND add post-extraction validation that drops records missing required fields
- Borderline cases (named parties but missing court/docket): keep as LOW confidence rather than dropping — better to over-flag than miss real litigation
- Add SNA regression test: verify 0 boilerplate-derived false SCAs after fix

### Volume Spike Detection
- Spike definition: volume > 2x the 20-trading-day moving average
- Lookback window: 1 year (252 trading days) — matches typical D&O policy period
- Event correlation: automated inline news search via Brave Search when spike detected — attach findings to the volume signal
- Upgrade STOCK.TRADE.volume_patterns from MANAGEMENT_DISPLAY to EVALUATIVE_CHECK
- Scoring thresholds: 0 spikes = clean, 1-2 = watch, 3+ = concern

### Claude's Discretion
- Exact LLM prompt wording for DEF 14A extraction and litigation filtering
- Internal data model field names and types
- Volume spike scoring weight relative to other STOCK.TRADE.* checks
- Post-extraction validation implementation details

</decisions>

<specifics>
## Specific Ideas

- SNA is the primary validation target — all 4 fixes should be verified against SNA output
- Board directors: SNA should show ~10 directors from DEF 14A
- Guidance: SNA is known not to provide forward guidance — should show FIN.GUIDE.current=No with analyst consensus labeled correctly
- Litigation: SNA should produce 0 false SCAs from boilerplate after fix
- Volume spikes: use existing yfinance stock data already acquired in pipeline

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 52-extraction-data-quality*
*Context gathered: 2026-02-28*
