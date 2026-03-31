# Phase 135: Governance Intelligence - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning
**Mode:** Auto-selected (all gray areas, recommended defaults)

<domain>
## Phase Boundary

Governance analysis reaches investigative depth: per-officer background investigation with prior SCA/SEC exposure, serial defendant detection, complete shareholder rights inventory with anti-takeover assessment, and detailed per-insider trading activity with 10b5-1 plan classification. Five new or enhanced sub-sections in the governance section.

Builds on substantial existing infrastructure — 11 extraction modules, 3 context builders, 14 templates, and rich Pydantic models (BoardForensicProfile, LeadershipForensicProfile, GovernanceQualityScore, OwnershipAnalysis). The gap is deeper officer investigation (cross-referencing officers against Supabase SCA database), structured shareholder rights display, and per-insider activity detail.

</domain>

<decisions>
## Implementation Decisions

### Officer Background Investigation (GOV-01)
- **D-01:** For each named officer from DEF 14A extraction, show: prior companies (from bio text), SCA/SEC history at those prior companies (queried from Supabase + SEC EDGAR), personal litigation (from web search results already acquired), and suitability assessment (HIGH/MEDIUM/LOW confidence based on data completeness).
- **D-02:** Officer prior company extraction uses LLM extraction from DEF 14A biographical text — regex is insufficient for the variety of bio formats. Structured output: list of {company_name, role, years}.
- **D-03:** Suitability assessment confidence: HIGH = full bio + no issues found + cross-validated, MEDIUM = partial data + some gaps, LOW = minimal bio data. The assessment itself is not a judgment on the person — it's a data completeness indicator for the underwriter.

### Serial Defendant Detection (GOV-02)
- **D-04:** Cross-reference officer prior companies against Supabase SCA database. If an officer was at Company X during the class period of an SCA against Company X, flag as "serial defendant" with case caption, class period, and role at that company.
- **D-05:** Use batch Supabase query (same pattern as Phase 134 `query_peer_sca_filings`) — collect all prior company names, query in one batch, then match against officer tenure dates.
- **D-06:** Display: officer name with red "Serial Defendant" badge, linked case references, and a one-liner D&O implication ("Prior SCA exposure at [Company] during [period] increases personal risk assessment").

### Shareholder Rights Inventory (GOV-03, GOV-04)
- **D-07:** Extract from DEF 14A and governance data already in state. Cover all 8 provisions: board classification, poison pill, supermajority requirements, proxy access, cumulative voting, written consent, special meeting threshold, and forum selection.
- **D-08:** Display as a checklist-style table: Provision | Status (Yes/No/N/A) | Details | Defense Strength | D&O Implication. Green/red/gray color coding.
- **D-09:** Anti-takeover defense strength assessment: aggregate the 8 provisions into an overall defense posture (Strong/Moderate/Weak). Based on count of protective provisions vs shareholder-friendly provisions.

### Per-Insider Activity Detail (GOV-05)
- **D-10:** Reuse existing insider trading extraction (`insider_trading.py`, `insider_trading_analysis.py`) which already parses Form 4 XMLs with 10b5-1 detection. The gap is structured per-insider display rather than aggregate summary.
- **D-11:** Per-insider table: Name | Position | Total Sales ($) | Total Sales (%O/S) | Tx Count | 10b5-1 Plan Status | Activity Period. Sort by total sales descending.
- **D-12:** 10b5-1 plan status from existing `_detect_10b5_1()` function — already reads SEC XML `aff10b5One` and `rule10b5One` elements. Render as badge: "10b5-1" (green) or "Discretionary" (amber).

### Claude's Discretion
- Template layout within existing beta_report governance section
- LLM prompt design for officer bio extraction
- How to handle officers with no prior company data (show "No prior public company history found" vs omit)
- Sorting/grouping of rights inventory provisions

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data Models
- `src/do_uw/models/governance.py` — BoardProfile model
- `src/do_uw/models/governance_forensics.py` — BoardForensicProfile, LeadershipForensicProfile, GovernanceQualityScore, OwnershipAnalysis (dual-class), CompensationAnalysis
- `src/do_uw/models/executive_risk.py` — BoardAggregateRisk
- `src/do_uw/models/state.py` — AnalysisState governance paths

### Existing Extraction
- `src/do_uw/stages/extract/board_governance.py` — Board/officer extraction from DEF 14A
- `src/do_uw/stages/extract/insider_trading.py` — Form 4 parsing with 10b5-1 detection
- `src/do_uw/stages/extract/insider_trading_analysis.py` — Aggregate insider analysis
- `src/do_uw/stages/extract/llm_governance.py` — LLM-based governance extraction
- `src/do_uw/stages/acquire/clients/supabase_litigation.py` — Supabase SCA query (batch pattern from Phase 134)

### Context Builders
- `src/do_uw/stages/render/context_builders/governance.py` — Main governance context builder
- `src/do_uw/stages/render/context_builders/_governance_helpers.py` — Helper functions
- `src/do_uw/stages/render/context_builders/governance_evaluative.py` — Evaluative governance context

### Templates
- `src/do_uw/templates/html/sections/governance/` — 14 existing template fragments
- `src/do_uw/templates/html/sections/beta_report.html.j2` — Active rendering path

### Integration
- `memory/reference-supabase-claims-db.md` — Supabase SCA database (6,980 filings)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `insider_trading.py`: Full Form 4 XML parser with 10b5-1 detection (`_detect_10b5_1()`)
- `supabase_litigation.py`: Batch SCA query (`query_peer_sca_filings()`) — reuse for officer prior company lookup
- `board_governance.py`: DEF 14A board/officer extraction
- `llm_governance.py`: LLM-based governance extraction with structured output
- `board_forensics.html.j2`: Existing forensic profiles template
- `ownership_structure.html.j2`: Existing ownership display

### Established Patterns
- Phase 134 pattern: models in `company_intelligence.py` → extraction modules → context builder `_company_intelligence.py` → template fragments → beta_report wiring
- `safe_float()` for all numeric values from state
- Templates with `{% if data %}` guards, `tabular-nums`, severity color coding
- Beta report hardcoded includes — new templates MUST be added there

### Integration Points
- New context builders wire into `governance.py` extract_governance()
- New templates include in `beta_report.html.j2` governance section
- Officer prior company SCA lookup via Supabase batch query
- 10b5-1 status already extracted per-transaction in insider_trading.py

</code_context>

<specifics>
## Specific Ideas

- Serial defendant detection is the highest-value feature — if a CFO was at Enron during the class period, that's a red flag an underwriter MUST see
- Shareholder rights inventory answers "how protected is this company from activist/hostile action and how does that affect D&O exposure?"
- Per-insider detail moves beyond "aggregate net selling" to "who exactly is selling, how much, and is it planned?"
- CLAUDE.md requires governance MUST ALWAYS show: prior lawsuits, character issues, qualifications — this phase delivers all three

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 135-governance-intelligence*
*Context gathered: 2026-03-27 via auto mode*
