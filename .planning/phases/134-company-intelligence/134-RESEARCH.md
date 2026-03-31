# Phase 134: Company Intelligence - Research

**Researched:** 2026-03-26
**Domain:** 10-K risk factor analysis, peer SCA contagion, concentration assessment, regulatory environment mapping
**Confidence:** HIGH

## Summary

Phase 134 adds 5 analytical sub-sections to the Company section: (1) enhanced risk factor review with classification, (2) YoY risk factor delta, (3) sector/competitive landscape with peer SCA contagion, (4) multi-dimensional concentration assessment, and (5) regulatory environment map. The good news: most of the underlying infrastructure already exists. The 10-K YoY comparison engine (`ten_k_yoy.py`) already computes risk factor deltas with `RiskFactorChange` models. The peer group construction (`peer_group.py`) already builds composite-scored peer groups. The regulatory extraction (`regulatory_extract.py`) already pulls proceedings from 10-K, 8-K, and web. Existing templates in `sections/company/` already render risk factors, customer concentration, and supplier concentration.

The primary gap is: (a) enriching existing extraction outputs with the classification/severity fields COMP-01 requires (Standard/Novel/Elevated), (b) querying Supabase SCA for each peer ticker to build the contagion view, (c) building a multi-dimensional concentration context builder that goes beyond the current simple customer/supplier tables, and (d) extending the regulatory display from a flat list to a per-regulator table with jurisdiction and exposure level.

**Primary recommendation:** Extend existing context builders and models rather than building new extraction pipelines. Data is already in the pipeline. The work is structured display enrichment and one new Supabase peer-query function.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Extract risk factors from 10-K Item 1A raw text (already stored in `output/TICKER/sources/`). LLM classifies each factor as Standard (industry boilerplate), Novel (newly added this year), or Elevated (language stronger than prior year).
- **D-02:** YoY delta computed by comparing current year factor list vs prior year factor list. Show factors Added, Removed, and Language Changed with severity rating. Prior year text available from 2-year filing history.
- **D-03:** Severity rating per factor: LOW (standard boilerplate), MEDIUM (specific to company but stable), HIGH (new or escalated language). Severity drives sort order.
- **D-04:** Risk factors display as a table: Factor Name | Classification | Severity | YoY Delta | D&O Implication. Expandable rows show the actual 10-K language.
- **D-05:** Reuse existing peer group infrastructure (`peer_group.py`, `peer_scoring.py`).
- **D-06:** Peer SCA contagion: query Supabase SCA claims database for each peer. Show company name, case caption, filing date, deadline.
- **D-07:** Sector-specific D&O concerns table driven by brain YAML signal `sector_filter` and `presentation.do_context`.
- **D-08:** Competitive landscape card: 4-6 peer profiles with MCap, Revenue, SCA History, relative risk positioning. Reuse `dossier_competitive.py`.
- **D-09:** Four-dimension concentration assessment: Customer, Geographic, Product/Service, Channel. Each dimension: level, key data point, D&O implication.
- **D-10:** Supply chain dependency table: extract from 10-K Item 1/1A. LLM extraction with structured output.
- **D-11:** Data sources: XBRL segment data, 10-K Item 1A, dossier enrichment. No new acquisition needed.
- **D-12:** Reuse `regulatory_extract.py`. Extend display to per-regulator table.
- **D-13:** Extend `company_environment.py` rather than replace.

### Claude's Discretion
- Template layout within existing beta_report structure (cards, tables, or mixed)
- LLM extraction prompt design for risk factor classification
- Threshold calibration for concentration levels
- Order of sub-sections within the company section

### Deferred Ideas (OUT OF SCOPE)
- Litigation extraction boilerplate misclassification (Phase 129 scope)
- Executive Brief narrative overhaul (Phase 136)
- Volume spike detection (Phase 133 already shipped)
- Board directors extraction (Phase 135)
- Scoring tier calibration (Phase 131)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COMP-01 | 10-K risk factor review: each factor classified as Standard/Novel/Elevated with severity | Existing `RiskFactorProfile` model has `severity` and `is_new_this_year`. Needs `classification` field (Standard/Novel/Elevated). LLM extraction already runs on Item 1A text. Extend prompt to add classification. |
| COMP-02 | 10-K risk factor YoY delta: factors appeared/disappeared/changed language | Already implemented in `ten_k_yoy.py` with `RiskFactorChange` model (NEW/REMOVED/ESCALATED/DE_ESCALATED/REORGANIZED). Existing `ten_k_yoy.html.j2` template renders this. Needs UI polish for COMP-01 classification integration. |
| COMP-03 | Sector/competitive landscape with 4+ competitor profiles | Existing `dossier_competitive.py` + `PeerRow` model + `CompetitiveLandscape` model. Existing peer group from `peer_group.py`. Need to merge financial peer data with competitive landscape display. |
| COMP-04 | Peer SCA contagion tracking | Supabase `query_sca_filings()` queries by ticker. New function needed to batch-query each peer ticker. No sector-level query exists in Supabase schema. |
| COMP-05 | Sector-specific D&O concerns table | No brain signals currently have `sector_filter` field (verified: 0 matches). Signal engine supports it in code but no YAML uses it. Need to create sector-specific signals or use a config-driven approach. |
| COMP-06 | Multi-dimensional concentration assessment | Existing `customer_concentration` and `supplier_concentration` on CompanyProfile. Geographic data in `geographic_footprint`. Product data in `revenue_segments`. Need unified 4-dimension context builder. |
| COMP-07 | Supply chain dependency table | Current `supplier_concentration` is a simple name+percentage list. Need LLM extraction for dependency type, switching cost, D&O exposure. Uses 10-K Item 1/1A text already accessible via `filing_sections.py`. |
| COMP-08 | Regulatory environment map | Existing `regulatory_extract.py` extracts proceedings with agency classification. Existing `company_environment.py` builds environment assessment. Need per-regulator table format with jurisdiction and exposure level. |
</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | Data models for new fields | Project standard, all models use it |
| Jinja2 | 3.x | Template rendering | Project standard for all HTML output |
| httpx | 0.27+ | Supabase API calls for peer SCA | Project standard (not requests) |
| difflib | stdlib | Risk factor title matching | Already used in `ten_k_yoy.py` |

### No New Dependencies
This phase requires zero new packages. All work extends existing infrastructure:
- LLM extraction via existing `stages/extract/llm/` patterns
- Supabase via existing `supabase_litigation.py` client
- Templates via existing `sections/company/` fragment pattern
- Context builders via existing `company_*.py` module pattern

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  stages/
    extract/
      risk_factor_classify.py      # NEW: LLM classification of Item 1A factors
      supply_chain_extract.py      # NEW: LLM extraction of supply chain deps
    render/
      context_builders/
        _company_intelligence.py   # NEW: Peer SCA contagion + concentration + regulatory
      templates/html/sections/company/
        risk_factor_review.html.j2       # NEW or ENHANCED: replaces risk_factors.html.j2
        peer_sca_contagion.html.j2       # NEW: peer SCA tracking
        sector_concerns.html.j2          # NEW: sector-specific D&O concerns
        concentration_assessment.html.j2 # NEW: 4-dimension concentration
        supply_chain.html.j2             # NEW: supply chain dependencies
        regulatory_map.html.j2           # NEW or ENHANCED: per-regulator table
  models/
    state.py                       # EXTEND: RiskFactorProfile.classification field
    company_intelligence.py        # NEW: ConcentrationDimension, SupplyChainDependency, PeerSCARecord models
```

### Pattern 1: Context Builder Module (Follow Phase 133 `_market_*.py` Pattern)
**What:** Each sub-section gets a dedicated builder function in `_company_intelligence.py`. Functions return `dict[str, Any]` merged via `result.update()`. Parent `extract_company()` calls all builders.
**When to use:** All 5 new sub-sections.
**Example:**
```python
# Source: existing _market_volume.py pattern
def build_peer_sca_contagion(state: AnalysisState) -> dict[str, Any]:
    """Build peer SCA contagion table from peer group + Supabase."""
    if not state.extracted or not state.extracted.financials:
        return {}
    peer_group = state.extracted.financials.peer_group
    if not peer_group or not peer_group.peers:
        return {}
    # Query each peer's SCA history
    sca_records = []
    for peer in peer_group.peers[:6]:
        cases = query_sca_filings(peer.ticker)
        for case in cases:
            sca_records.append({...})
    return {"peer_sca_contagion": sca_records, "has_peer_sca": bool(sca_records)}
```

### Pattern 2: Template Fragment Include (Follow `sections/company/*.html.j2`)
**What:** Each new sub-section is a separate `.html.j2` file included from `beta_report.html.j2`.
**When to use:** All new display sections.
**Key constraint:** Templates MUST be added as `{% include %}` in `beta_report.html.j2` (around line 926-968 area). Manifest-only inclusion does not work for beta report.

### Pattern 3: Pydantic Model Extension
**What:** New fields added to existing models with defaults, backward-compatible.
**Example:**
```python
# Extend RiskFactorProfile
class RiskFactorProfile(BaseModel):
    title: str = ""
    category: str = "OTHER"
    severity: str = "MEDIUM"
    classification: str = "STANDARD"  # NEW: STANDARD/NOVEL/ELEVATED
    is_new_this_year: bool = False
    yoy_delta: str = ""  # NEW: "ADDED"/"REMOVED"/"ESCALATED"/"UNCHANGED"
    do_implication: str = ""  # NEW: D&O litigation theory
    do_relevance: str = "MEDIUM"
    source_passage: str = ""
    source: str = ""
```

### Anti-Patterns to Avoid
- **Creating new acquisition pipeline:** All data already exists. Do NOT add new MCP calls or web fetches in ACQUIRE stage.
- **Hardcoding sector-specific logic in Python:** COMP-05 sector concerns should be config-driven (brain YAML or JSON config), not `if sector == "Technology":` branches.
- **Querying Supabase at render time:** Peer SCA contagion data should be fetched during EXTRACT stage and stored in state, not queried during rendering. Context builders must be pure data formatters.
- **Modifying existing `ten_k_yoy.py` output:** The existing YoY comparison works correctly. Extend its output with classification, don't rewrite its comparison logic.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Risk factor title matching | Custom string comparison | `difflib.SequenceMatcher` | Already proven in `ten_k_yoy.py` with `_TITLE_MATCH_THRESHOLD = 0.6` |
| Peer group construction | Manual SIC-based peer lookup | `peer_group.py` + `peer_scoring.py` | 5-signal composite scoring already handles SIC, industry, MCap, revenue, description overlap |
| Regulatory agency detection | Regex pattern library | `regulatory_extract_patterns.py` | Already covers DOJ/FTC/FDA/EPA/CFPB/OCC/OSHA/EEOC/state AG/FCPA/NHTSA/FERC |
| SCA history lookup | Web scraping | `supabase_litigation.py` `query_sca_filings()` | Already integrated, MEDIUM confidence, 6,980 filings |
| Item 1A text extraction | Custom 10-K parser | `filing_sections.py` SECTION_DEFS + `regulatory_extract._get_item1a_text()` | Proven regex patterns for SEC filing section boundaries |

## Common Pitfalls

### Pitfall 1: Supabase Rate Limiting on Peer SCA Queries
**What goes wrong:** Querying Supabase for 10 peers = 10 HTTP requests. With the free tier, this could hit rate limits or add significant latency.
**Why it happens:** Current `query_sca_filings()` makes 1-2 requests per ticker (ticker match + company name match).
**How to avoid:** Batch queries using Supabase's `or` filter syntax: `?ticker=in.(AAPL,MSFT,GOOG)`. Limit to top 6 peers. Cache results in state.
**Warning signs:** Timeouts during EXTRACT stage; Supabase 429 responses.

### Pitfall 2: LLM Classification Inconsistency
**What goes wrong:** LLM classifies the same risk factor differently across runs. "Standard" vs "Novel" is subjective without strong anchoring.
**Why it happens:** Classification requires comparison context (what's "standard" for this sector?).
**How to avoid:** Provide clear examples in the prompt. Use the existing `is_new_this_year` boolean as a hard signal for "Novel". "Elevated" should map to existing `severity == "HIGH"` combined with YoY escalation. Cache classifications in state for deterministic re-rendering.
**Warning signs:** Same company producing different classifications on re-run without `--fresh`.

### Pitfall 3: Empty Peer SCA Data Looks Broken
**What goes wrong:** Many companies' peers have zero SCA history in Supabase. The contagion table renders empty, looking like a bug.
**Why it happens:** Supabase has 6,980 filings — good coverage for large-cap but gaps for smaller companies.
**How to avoid:** Template must have a meaningful "no contagion detected" state. Show "0 active SCAs among X peers analyzed" as a positive finding, not a gap.
**Warning signs:** Empty contagion sections for mid-cap or small-cap companies.

### Pitfall 4: Concentration Assessment Over-Classifying as HIGH
**What goes wrong:** Every company gets flagged HIGH on at least one concentration dimension because thresholds are too sensitive.
**Why it happens:** Default thresholds not calibrated to actual distributions.
**How to avoid:** Use conservative thresholds: Customer HIGH = top customer >15% revenue; Geographic HIGH = single region >80%; Product HIGH = single segment >60%. These are D&O underwriting standards, not generic risk levels.
**Warning signs:** All test companies (AAPL, RPM, etc.) showing HIGH on every dimension.

### Pitfall 5: Sector-Specific D&O Concerns Without Brain Signal Data
**What goes wrong:** COMP-05 requires a sector-specific concerns table but zero brain signals currently have `sector_filter` populated.
**Why it happens:** The `sector_filter` schema field exists in the signal engine but was never populated in YAML.
**How to avoid:** For Phase 134, use a config-driven approach (JSON mapping of SIC ranges to D&O concerns) rather than waiting for brain YAML population. This is Claude's discretion area.
**Warning signs:** Empty sector concerns table for all companies.

### Pitfall 6: Supabase Key Not Available
**What goes wrong:** Peer SCA contagion silently returns empty results because `SUPABASE_KEY` environment variable is missing.
**Why it happens:** The `query_sca_filings()` function returns `[]` silently when no key is set.
**How to avoid:** Log a visible warning when peer contagion is attempted without Supabase key. Template should show "SCA data source unavailable" rather than empty table.
**Warning signs:** Contagion section always empty during development.

## Code Examples

### Existing Risk Factor Model (state.py:138-151)
```python
# Source: src/do_uw/models/state.py
class RiskFactorProfile(BaseModel):
    title: str = ""
    category: str = "OTHER"  # LITIGATION, REGULATORY, FINANCIAL, CYBER, ESG, AI, OTHER
    severity: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    is_new_this_year: bool = False
    do_relevance: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    source_passage: str = ""
    source: str = ""
```

### Existing YoY Change Types (ten_k_comparison.py:13-23)
```python
# Source: src/do_uw/models/ten_k_comparison.py
class RiskFactorChange(BaseModel):
    title: str
    category: str  # LITIGATION, REGULATORY, FINANCIAL, OPERATIONAL, CYBER, ESG, AI, OTHER
    change_type: str  # NEW, REMOVED, ESCALATED, DE_ESCALATED, UNCHANGED, REORGANIZED, CONSOLIDATED_INTO
    current_severity: str  # HIGH, MEDIUM, LOW
    prior_severity: str | None = None
    summary: str
    prior_title: str | None = None
    new_title: str | None = None
```

### Existing Supabase Query Pattern (supabase_litigation.py:26-78)
```python
# Source: src/do_uw/stages/acquire/clients/supabase_litigation.py
def query_sca_filings(ticker: str, company_name: str | None = None) -> list[dict[str, Any]]:
    # Queries by exact ticker match, then by company name ILIKE
    # Returns: company_name, ticker, filing_date, case_status, settlement_amount_m, ...
```

### Context Builder Pattern (follow _market_volume.py)
```python
# Source: src/do_uw/stages/render/context_builders/_market_volume.py
def build_volume_anomalies(state: AnalysisState) -> dict[str, Any]:
    """Pure data formatter — no evaluative logic."""
    if not state.extracted or not state.extracted.market:
        return {}
    # Extract data from state, format for template, return dict
    return {"volume_anomalies": rows, "has_volume_anomalies": bool(rows)}
```

### Competitive Landscape Context Builder Pattern (dossier_competitive.py)
```python
# Source: src/do_uw/stages/render/context_builders/dossier_competitive.py
def build_competitive_landscape_context(state: AnalysisState, *, signal_results=None) -> dict[str, Any]:
    cl = state.dossier.competitive_landscape
    result = {"comp_peers": [], "comp_moats": [], ...}
    for peer in cl.peers:
        result["comp_peers"].append({...})
    return result
```

### Template Include in beta_report.html.j2 (lines 948-968)
```jinja2
{# Source: src/do_uw/templates/html/sections/beta_report.html.j2 #}
{% include "sections/company/business_model.html.j2" %}
{% include "sections/company/revenue_segments.html.j2" %}
{% include "sections/company/customer_concentration.html.j2" %}
{% include "sections/company/supplier_concentration.html.j2" %}
{% include "sections/company/risk_factors.html.j2" %}
{% include "sections/company/ten_k_yoy.html.j2" %}
{# NEW Phase 134 includes would go here #}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat risk factor list (severity only) | RiskFactorProfile with category, severity, D&O relevance | Phase 132 | Already has structure, needs classification |
| No peer SCA tracking | Supabase SCA integration for target company only | Phase ~118 | Need to extend to peer tickers |
| Simple customer/supplier tables | Two separate concentration tables | Phase ~56 | Need unified 4-dimension assessment |
| Flat regulatory proceedings list | Agency-classified RegulatoryProceeding model | Phase ~118 | Need per-regulator table display |
| No YoY risk factor tracking | Full `ten_k_yoy.py` with 7 change types | Phase 132 | Core exists, needs classification overlay |

## Existing Assets Inventory

### Already Working (Reuse Directly)
| Asset | Location | What It Does | Gap for Phase 134 |
|-------|----------|--------------|-------------------|
| `RiskFactorProfile` model | `models/state.py:138` | Structured risk factor with severity, category, D&O relevance | Missing `classification` (Standard/Novel/Elevated) and `do_implication` |
| `ten_k_yoy.py` | `stages/extract/ten_k_yoy.py` | YoY comparison with 7 change types | Works as-is for COMP-02. Needs classification from COMP-01 merged in |
| `risk_factors.html.j2` | `templates/html/sections/company/` | Renders risk factors grouped by D&O relevance | Needs Classification column, YoY Delta column, D&O Implication column |
| `ten_k_yoy.html.j2` | `templates/html/sections/company/` | Renders YoY changes with priority/routine split | Works as-is, enhance with classification badges |
| `peer_group.py` | `stages/extract/peer_group.py` | 5-signal composite peer group (10 peers) | Provides peer tickers for Supabase query |
| `query_sca_filings()` | `stages/acquire/clients/supabase_litigation.py` | SCA lookup by ticker | Need batch query for multiple peers |
| `dossier_competitive.py` | context builders | Competitive landscape context | Provides peer display data, needs SCA enrichment |
| `regulatory_extract.py` | `stages/extract/regulatory_extract.py` | Extracts DOJ/FTC/FDA/etc proceedings | Provides data for COMP-08 table |
| `company_environment.py` | context builders | Environment/regulatory assessment | Provides regulatory intensity scores |
| `customer_concentration.html.j2` | templates | Simple customer table | Needs upgrade to 4-dimension assessment |
| `supplier_concentration.html.j2` | templates | Simple supplier table | Needs upgrade with dep type, switching cost |
| `filing_sections.py` | `stages/extract/` | Item 1, 1A, 3, 7 extraction from 10-K | Provides raw text for LLM classification |

### Needs Building
| Component | Why It's Needed | Complexity |
|-----------|----------------|------------|
| Risk factor LLM classification prompt | COMP-01: Standard/Novel/Elevated classification | MEDIUM (prompt design + caching) |
| Batch Supabase peer query | COMP-04: Query SCA for 6 peers efficiently | LOW (extend existing client) |
| `_company_intelligence.py` context builder | COMP-03/04/06/08: Unified builder for new sub-sections | MEDIUM (follows established pattern) |
| Concentration dimension models | COMP-06: 4-dimension assessment Pydantic models | LOW |
| Supply chain LLM extraction | COMP-07: Structured extraction from Item 1/1A | MEDIUM (prompt design) |
| Sector D&O concerns config | COMP-05: Config-driven sector-to-concerns mapping | MEDIUM (no brain signals have sector_filter yet) |
| 5 new template fragments | All: HTML templates for new sub-sections | LOW-MEDIUM (follows established patterns) |

## Open Questions

1. **Sector-Specific D&O Concerns Source (COMP-05)**
   - What we know: The signal engine supports `sector_filter` but zero YAML signals use it. The `sector_classification` text signal provides hazard tier and claim patterns.
   - What's unclear: Should we create brain YAML signals with `sector_filter` (proper but time-consuming) or use a simpler JSON config mapping (pragmatic for Phase 134)?
   - Recommendation: Use JSON config mapping for Phase 134 (Claude's discretion area). A `config/sector_do_concerns.json` file mapping SIC ranges to concern rows. Brain signal population deferred to SECT-02 (future requirement).

2. **Risk Factor Classification Timing**
   - What we know: Current risk factor extraction happens during EXTRACT stage via LLM. Adding classification is natural.
   - What's unclear: Should classification be a separate LLM call or extend the existing extraction prompt?
   - Recommendation: Extend the existing 10-K LLM extraction schema to include `classification` field. Single call, not additional. Cache invalidation via schema version bump.

3. **Peer SCA Contagion Data Freshness**
   - What we know: Supabase has 6,980 filings. We don't know the update frequency.
   - What's unclear: How current is the Supabase data? Could show stale "active" cases that are actually resolved.
   - Recommendation: Display filing_date prominently. Add disclaimer: "SCA data as of [date]. Verify current status for active cases."

## Project Constraints (from CLAUDE.md)

Key directives that constrain Phase 134 implementation:

- **Brain portability**: New sector concerns MUST be config-driven (brain YAML or JSON), not hardcoded Python logic
- **Narrative quality**: Every sentence must contain company-specific data. No boilerplate in D&O implications
- **Data integrity**: Every data point needs source + confidence. Peer SCA data is MEDIUM confidence (Supabase)
- **safe_float()**: Required for all state data values in context builders
- **No bare float()**: Use `safe_float()` from formatters
- **No file over 500 lines**: New `_company_intelligence.py` must stay under limit; split if needed
- **Visual quality**: New templates must match existing CIQ-style density. No degradation.
- **No truncation**: Never `| truncate()` on analytical content
- **Preserve before improve**: Existing risk_factors.html.j2 and ten_k_yoy.html.j2 must not lose any current functionality
- **Additive only**: New sub-sections alongside existing ones, never replacements
- **Anti-context-rot**: Single state file, no scoring logic outside score/, no acquisition outside acquire/
- **Self-verification**: Re-render and check output before claiming done

## Sources

### Primary (HIGH confidence)
- Direct code inspection of all referenced files in the codebase
- `src/do_uw/models/state.py` — RiskFactorProfile model (lines 138-151)
- `src/do_uw/models/ten_k_comparison.py` — RiskFactorChange model
- `src/do_uw/models/competitive_landscape.py` — PeerRow, CompetitiveLandscape models
- `src/do_uw/stages/extract/ten_k_yoy.py` — YoY comparison engine
- `src/do_uw/stages/extract/regulatory_extract.py` — Regulatory proceedings extraction
- `src/do_uw/stages/extract/peer_group.py` — Peer group construction
- `src/do_uw/stages/acquire/clients/supabase_litigation.py` — SCA filings client
- `src/do_uw/stages/render/context_builders/` — All company_*.py and _market_*.py patterns
- `src/do_uw/templates/html/sections/company/` — All existing company templates
- `src/do_uw/templates/html/sections/beta_report.html.j2` — Include structure (lines 926-968)
- `src/do_uw/stages/analyze/signal_engine.py` — sector_filter support (lines 506-518)
- `src/do_uw/brain/signals/` — Verified 0 signals with sector_filter

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions on data sources and reuse strategy

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, all patterns verified in codebase
- Architecture: HIGH - follows established Phase 133 patterns exactly
- Pitfalls: HIGH - based on direct inspection of Supabase client limitations, signal engine gaps, and existing model structure
- Existing assets: HIGH - every file path verified, every model field confirmed

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable codebase, no external dependency changes expected)
