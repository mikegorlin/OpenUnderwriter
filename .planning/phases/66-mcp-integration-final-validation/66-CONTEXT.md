# Phase 66: MCP Integration & Final Validation - Context

**Gathered:** 2026-03-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrate 3 new MCP data sources (CourtListener, Financial Modeling Prep, Exa) into the ACQUIRE stage as supplementary sources, then validate the entire v3.0 milestone across 4 tickers with automated quality checks, visual regression framework, performance budget enforcement, and documentation updates.

</domain>

<decisions>
## Implementation Decisions

### MCP Integration Strategy
- All 3 MCPs are **graceful fallback** — pipeline completes with existing data if any MCP is unavailable, logs what was missed
- MCPs are supplementary enrichment, NOT replacements for existing data sources
- All MCP usage in ACQUIRE stage only (subagents cannot access MCP tools)

### CourtListener (MCP-01)
- Integrate as a new acquire client for federal case search
- Must be free tier (no paid API)
- Fills the gap: Stanford SCAC covers securities class actions only, CourtListener adds broader federal litigation (employment, regulatory, environmental)
- Falls through to existing pipeline (SCAC + Item 3 + web search) if unavailable

### Financial Modeling Prep (MCP-02)
- **Enrich only** — supplementary to yfinance + SEC, not a replacement
- Use FMP's free tier (250 req/day) for: institutional ownership detail, analyst estimates where yfinance gaps exist
- Do NOT migrate existing financial data acquisition to FMP

### Exa Semantic Search (MCP-03)
- Add Exa as second-pass search AFTER Brave Search in blind spot discovery
- Semantic search is materially better than keyword search for hidden risks (e.g., "accounting irregularities at {company}")
- Free tier usage
- Complements Brave, does not replace it

### Cross-Ticker Validation (QA-01)
- Validate AAPL, SNA, RPM, WWD — keep the existing 4 tickers
- **Full quality audit**: no Python exceptions + all sections have real data + human reviews outputs for quality/accuracy
- Validate **HTML + PDF** outputs (Word is secondary adapter — if shared context is correct, Word formatting is just formatting)
- Automated checks catch regressions; user does final human review for quality/accuracy

### Visual Regression Framework (QA-02)
- Golden screenshots approach — capture "approved" baseline screenshots
- **Per-section screenshots** — 12 sections individually per ticker, easier to pinpoint regressions
- **Structural diff threshold (5-10%)** — allow data value changes, catch layout shifts, missing sections, broken CSS
- Golden screenshots **committed to git** in a tests/golden/ directory (versioned, reviewable)
- Playwright captures screenshots (already a dependency)

### Performance Budget (QA-03)
- Pipeline <25min, HTML render <10s, PDF render <30s
- **Both**: CLI reports timing at end of every run + pytest assertions enforce budgets automatically
- Timing assertions as pytest markers so regressions are caught

### Test Health (QA-04)
- 4,921 tests already exceeds the 4,200 target — **don't pad the count**
- Fix the collection error in test_brain_framework.py
- Ensure all existing tests pass cleanly
- Add tests only for new MCP integrations (functional tests for new clients)

### Documentation (QA-05)
- Update CLAUDE.md, PROJECT.md, ROADMAP.md to reflect v3.0 completion
- **Create or update README.md** with setup instructions, usage examples, output screenshots
- Mark v3.0 milestone as shipped

### Ship Criteria
- **Quality bar, not checkbox** — requirements are a guide, user judgment is the gate
- Run all 4 tickers, user reviews outputs, confirms institutional-quality feel
- MUSTs must be met; SHOULDs are best-effort but expected

### Claude's Discretion
- MCP client module structure and error handling patterns
- Exa query construction for D&O-relevant semantic searches
- Screenshot comparison library choice (pixelmatch, PIL, etc.)
- Performance timing measurement approach
- README structure and content organization

</decisions>

<specifics>
## Specific Ideas

- CourtListener must be free tier only
- FMP is supplementary enrichment, NOT a replacement for yfinance
- Visual regression uses per-section granularity (~12 screenshots per ticker) to pinpoint regressions precisely
- Performance budget enforced both as CLI output AND pytest assertions

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `stages/acquire/clients/` — Clean client module pattern (litigation_client.py, market_client.py, news_client.py, etc.). New MCP clients follow this pattern.
- `stages/acquire/orchestrator.py` — Acquisition orchestration. New MCP calls integrate here.
- `stages/acquire/gap_searcher.py` — Existing blind spot discovery. Exa semantic search would augment this.
- `models/litigation.py` — Already references CourtListener in the model structure.
- Playwright is already a dependency (PDF rendering) — reuse for screenshot capture.

### Established Patterns
- Acquire clients return structured data with source + confidence fields
- All acquisition uses httpx (not requests)
- Graceful fallback chains documented in CLAUDE.md
- Tests alongside code, mirror src/ structure

### Integration Points
- New MCP clients → `stages/acquire/clients/` (new files)
- MCP orchestration → `stages/acquire/orchestrator.py` (add calls)
- Exa blind spot → `stages/acquire/gap_searcher.py` (augment)
- Visual regression → `tests/` (new test module + golden dir)
- Performance budget → `cli.py` timing + `tests/` assertions

</code_context>

<deferred>
## Deferred Ideas

- **NotebookLM MCP** — Curated D&O knowledge oracle. Upload case law, industry reports, settlement data. Query during ACQUIRE for grounded, citation-backed institutional knowledge. Builds over time. — Future milestone (v3.1+)
- **FRED macro data MCP** — Federal Reserve economic indicators (interest rates, sector indices, credit spreads). Macro conditions correlate with D&O claim frequency for forward-looking risk. — Future milestone (v3.1+)
- **BrainWriter YAML write-back fix** — BrainWriter still writes signal definitions to DuckDB only (bypassing YAML source of truth) in feedback.py, calibrate.py, discovery.py, cli_ingest.py, cli_brain_ext.py. Should use the `calibrate_apply.py` pattern (write YAML, rebuild DuckDB). — Technical debt, future phase.

</deferred>

---

*Phase: 66-mcp-integration-final-validation*
*Context gathered: 2026-03-03*
