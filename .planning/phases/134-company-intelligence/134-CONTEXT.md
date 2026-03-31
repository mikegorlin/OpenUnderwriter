# Phase 134: Company Intelligence - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning
**Mode:** Auto-selected (all gray areas, recommended defaults)

<domain>
## Phase Boundary

Surfaces company-specific risk context that only deep 10-K analysis reveals. Adds 5 new analytical sub-sections to the Company section: risk factor review with YoY deltas, sector/competitive landscape with peer SCA contagion, customer/supply chain concentration assessment, regulatory environment map, and sector-specific D&O concerns table.

All data comes from existing pipeline outputs (10-K text, XBRL, litigation data, peer group) — the gap is extraction targeting and structured display, not new data acquisition.

</domain>

<decisions>
## Implementation Decisions

### Risk Factor Review (COMP-01, COMP-02)
- **D-01:** Extract risk factors from 10-K Item 1A raw text (already stored in `output/TICKER/sources/`). LLM classifies each factor as Standard (industry boilerplate), Novel (newly added this year), or Elevated (language stronger than prior year).
- **D-02:** YoY delta computed by comparing current year factor list vs prior year factor list. Show factors Added, Removed, and Language Changed with severity rating. Prior year text available from 2-year filing history.
- **D-03:** Severity rating per factor: LOW (standard boilerplate), MEDIUM (specific to company but stable), HIGH (new or escalated language). Severity drives sort order — underwriter sees highest-risk factors first.
- **D-04:** Risk factors display as a table: Factor Name | Classification | Severity | YoY Delta | D&O Implication. Expandable rows show the actual 10-K language.

### Sector & Competitive Landscape (COMP-03, COMP-04, COMP-05)
- **D-05:** Reuse existing peer group infrastructure (`peer_group.py`, `peer_scoring.py`) which already constructs 5-signal composite peer groups. Extend to include SCA filing history per peer.
- **D-06:** Peer SCA contagion: for each peer in the group, query Supabase SCA claims database (already integrated) for active cases. Show company name, case caption, filing date, deadline. If a peer in the same sector just got sued, that's a leading indicator.
- **D-07:** Sector-specific D&O concerns table: derive from brain signals with `sector_filter` field. Each row: Concern | Sector Relevance | Company Exposure | D&O Implication. Not hardcoded — driven by brain YAML signal `sector_filter` and `presentation.do_context`.
- **D-08:** Competitive landscape card: 4-6 peer profiles with MCap, Revenue, SCA History (count + most recent), and relative risk positioning. Reuse `dossier_competitive.py` context builder.

### Concentration Assessment (COMP-06, COMP-07)
- **D-09:** Four-dimension concentration assessment: Customer, Geographic, Product/Service, Channel. Each dimension: concentration level (HIGH/MEDIUM/LOW), key data point (e.g., "Top customer = 15% revenue"), D&O implication (e.g., "Customer loss triggers revenue miss SCA").
- **D-10:** Supply chain dependency table: extract from 10-K Item 1/1A language about key suppliers, single-source components, geographic manufacturing concentration. LLM extraction with structured output.
- **D-11:** Data sources: XBRL segment data (geographic/product), 10-K Item 1A (customer/supplier mentions), dossier enrichment (already has some concentration data). No new acquisition needed.

### Regulatory Environment (COMP-08)
- **D-12:** Reuse existing `regulatory_extract.py` which already extracts non-SEC regulatory proceedings from 10-K, 8-K, and web. Extend display to show per-regulator table: Agency | Jurisdiction | Exposure Level | Current Status | Risk Level.
- **D-13:** Regulatory environment context builder already exists (`company_environment.py`) — extend rather than replace.

### Claude's Discretion
- Template layout within existing beta_report structure — whether to use cards, tables, or mixed
- LLM extraction prompt design for risk factor classification
- Threshold calibration for concentration levels
- Order of sub-sections within the company section

### Folded Todos
- **Earnings guidance signals conflate analyst consensus with company-issued guidance** (score: 0.6) — relevant to how company intelligence distinguishes between company-stated risks vs analyst opinions in risk factor review

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data Models
- `src/do_uw/models/state.py` — AnalysisState, the single source of truth
- `src/do_uw/models/financials.py` — PeerCompany, PeerGroup models
- `src/do_uw/models/litigation_details.py` — RegulatoryProceeding model

### Existing Extraction
- `src/do_uw/stages/extract/peer_group.py` — 5-signal peer group construction
- `src/do_uw/stages/extract/peer_scoring.py` — Composite scoring functions
- `src/do_uw/stages/extract/regulatory_extract.py` — Regulatory proceedings extraction from 10-K/8-K
- `src/do_uw/stages/extract/regulatory_extract_patterns.py` — Agency patterns and classification

### Existing Context Builders
- `src/do_uw/stages/render/context_builders/dossier_competitive.py` — Competitive landscape context
- `src/do_uw/stages/render/context_builders/company_environment.py` — Environment/regulatory signals
- `src/do_uw/stages/render/context_builders/company_operations.py` — Company operations context
- `src/do_uw/stages/render/context_builders/company_business_model.py` — Business model context

### Templates
- `src/do_uw/templates/html/sections/company.html.j2` — Company section parent template
- `src/do_uw/templates/html/sections/beta_report.html.j2` — Active rendering path (hardcoded includes)
- `src/do_uw/brain/output_manifest.yaml` — Manifest for facet-driven rendering

### Brain Signals
- `brain/signals/*.yaml` — 600+ signal definitions, check for `sector_filter` field
- `brain/framework/*.yaml` — Analytical frameworks

### Integration Reference
- `memory/reference-supabase-claims-db.md` — Supabase SCA claims database (6,980 filings)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `peer_group.py` + `peer_scoring.py`: Full peer construction with 5-signal composite scoring
- `regulatory_extract.py`: Extracts DOJ/FTC/FDA/EPA/CFPB/OCC/OSHA/EEOC/state AG/FCPA/NHTSA/FERC proceedings
- `dossier_competitive.py`: Competitive landscape context builder (moat, peers)
- `company_environment.py`: Environment signals (regulatory intensity, geopolitical, ESG, cyber)
- `dossier_emerging_risks.py`: Emerging risk extraction and display
- Supabase SCA integration already works — queried in acquire stage

### Established Patterns
- Context builders in `_market_*.py` pattern: function per sub-section, returns dict, merged via `result.update()`
- Templates in `sections/market/*.html.j2` pattern: fragment templates included by parent
- **Beta report hardcoded includes** — new templates MUST be added to `beta_report.html.j2` (not just manifest)
- `safe_float()` for all state data values
- `{% if data %}` guards on every template section

### Integration Points
- New context builders wire into `company.py` extract_company() or a new company intelligence builder
- New templates include in `beta_report.html.j2` company section (around line 926)
- Peer SCA data from Supabase via existing `acquire` stage client
- 10-K raw text from `output/TICKER/sources/` (stored by Phase 128)

</code_context>

<specifics>
## Specific Ideas

- Risk factor review should feel like a diff view — underwriter instantly sees what's new/changed/removed
- Peer SCA contagion is a leading indicator — if your competitor just got sued for the same thing, you're next
- Concentration assessment answers "where does the revenue come from and how fragile is it?"
- All of this already has data in the pipeline — the gap is structured extraction + display

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
- **Litigation extraction misclassifies boilerplate 10-K legal reserves as active cases** (score: 0.6) — Phase 129 scope (bug fixes), not Phase 134
- **Executive Brief narrative boilerplate overhaul** (score: 0.6) — Phase 136 (integration/forward-looking), not Phase 134
- **Volume spike detection and event correlation** (score: 0.4) — Phase 133 already shipped this
- **Board directors extraction empty** (score: 0.2) — Phase 135 (governance), not Phase 134
- **Scoring tier calibration** (score: 0.2) — Phase 131 scope, not Phase 134

</deferred>

---

*Phase: 134-company-intelligence*
*Context gathered: 2026-03-27 via auto mode*
