# Phase 21: Multi-Ticker Validation & Production Hardening - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate LLM extraction across 20+ diverse companies and harden the pipeline for production use. Every verification failure gets fixed. After this phase, any US public company (excluding financial institutions) produces underwriting-grade output with consistent quality, graceful error handling, and cost control within $2.00/company.

</domain>

<decisions>
## Implementation Decisions

### Ticker Selection & Diversity
- At least 2 tickers per industry playbook vertical (Tech, Biotech, Energy, Healthcare, CPG, Media, Industrials, REITs, Transportation) = 20+ base
- **No financial institutions** (banks, insurance, asset managers) — excluded from validation set
- Include 3-5 known-outcome companies (companies with known D&O claims history, e.g., SMCI accounting issues, SVB-adjacent, FTX-adjacent) to validate risk detection
- All runs are fresh — clear cache, re-acquire everything, true end-to-end validation
- Claude selects specific tickers at its discretion to maximize industry diversity coverage

### Quality Audit Methodology
- Automated ground truth comparison — expand ground truth fixtures to 8-10 companies (currently TSLA/AAPL/JPM)
- Programmatic comparison with tolerances (existing 10% relative tolerance pattern for financials)
- 90% overall accuracy threshold gates pass/fail (adjusted down from roadmap's 95% — LLM has inherent variance)
- **Fix everything that fails** — every verification failure gets a fix or explicit tolerance adjustment. Zero known failures at phase end.

### Error Handling & Retry
- Anthropic API failures: retry 3x with exponential backoff, then fall back to regex extraction. Pipeline continues with degraded confidence.
- SEC EDGAR: conservative 5 req/sec rate (half the allowed 10/sec), retry 5x with longer backoff. Slower but more resilient for bulk runs.
- Validation run is resumable — checkpoint after each ticker completes. On restart, skip already-completed tickers.
- Batch continues on individual company failures — run all 20+ tickers regardless, produce comprehensive report at end showing pass/fail per company with reasons.

### Cost & Performance Targets
- $2.00/company budget maintained — no increase for validation
- 10 minutes per company acceptable (relaxed from roadmap's 5 minutes)
- Build Batch API support as a CLI option (--batch flag) but validate using real-time API to test the production code path
- Detailed cost breakdown report: per company totals AND per filing type (10-K, DEF 14A, 8-K, etc.) to identify which filings are most expensive

### Claude's Discretion
- Specific ticker selection (within the industry coverage and known-outcome constraints)
- Retry backoff timing and strategy details
- Ground truth field selection for new companies (which 13 categories to verify)
- Checkpoint storage format and location
- Cost report format (CLI output, file, or both)

</decisions>

<specifics>
## Specific Ideas

- Known-outcome companies should include companies where D&O claims actually happened, not just companies with risk indicators. The system should produce high risk scores for these.
- Conservative SEC rate limiting (5 req/sec) is specifically for the bulk validation run scenario — 20+ companies back-to-back would stress a 10 req/sec limit.
- "Fix everything that fails" means this phase may produce converter/extraction fixes as a side effect of validation. That's expected and desired.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 21-multi-ticker-validation*
*Context gathered: 2026-02-11*
