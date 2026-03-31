# Phase 118: Revenue Model + Company Intelligence Dossier - Research

**Researched:** 2026-03-20
**Domain:** Revenue model extraction, business intelligence dossier, ASC 606 analysis, concentration assessment, emerging risk radar, LLM extraction from 10-K/S-1
**Confidence:** HIGH

## Summary

Phase 118 creates a Company Intelligence Dossier section in the worksheet -- Section 5 in the gold standard PDF (pages 4-12). The gold standard for HNGE shows 9 subsections: (5.1) What the Company Does, (5.2) How Money Flows, (5.3) Revenue Model Card, (5.4) Revenue Segment Breakdown + Concentration Assessment, (5.5) Unit Economics, (5.6) Revenue Waterfall, (5.7) Competitive Landscape + Moat Assessment [assigned to Phase 119 per STATE.md], (5.8) Emerging Risk Radar, (5.9) Revenue Recognition (ASC 606). Each subsection contains company-specific data with D&O risk implications in every row/assessment.

The existing codebase has substantial foundations: `CompanyProfile` already has `business_description`, `revenue_model_type`, `revenue_segments`, `geographic_footprint`, `customer_concentration`, `supplier_concentration`, `segment_lifecycle`, `segment_margins`, `disruption_risk`, and `key_person_risk`. The `TenKExtraction` LLM schema extracts `business_description`, `revenue_segments`, `geographic_regions`, `customer_concentration`, `revenue_model_type`, and `competitive_position`. Context builders `company_business_model.py` and `company_operations.py` already produce template-ready dicts for the existing Business Model Profile section. However, the DOSSIER requirements demand MUCH richer extraction (ASC 606 elements, unit economics, revenue waterfall, emerging risks, revenue quality, NDR, ARPU, contract duration, billings vs revenue gap) and every table needs a D&O Risk column that does not currently exist.

**Primary recommendation:** Implement in 6 waves following the Phase 117 pattern: (1) New Pydantic models for DossierData on AnalysisState, (2) LLM extraction enhancement for dossier-specific fields from 10-K + S-1, (3) BENCHMARK computation of concentration assessment + emerging risks + unit economics, (4) 7 context builders (one per subsection, excluding competitive landscape), (5) 7 Jinja2 templates, (6) pipeline wiring + manifest + integration tests. DOSSIER-07 (competitive landscape) is explicitly assigned to Phase 119 per ROADMAP.md.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DOSSIER-01 | "What the Company Does" subsection: plain English business description + "The core D&O exposure" paragraph identifying single most important risk vector | Existing `business_description` on CompanyProfile from 10-K Item 1; needs LLM enrichment to generate D&O exposure paragraph from scoring results + signal evaluations |
| DOSSIER-02 | "How Money Flows" subsection: revenue flow diagram showing business model visually | New LLM extraction generating text-based flow diagram from 10-K Item 1 + revenue recognition notes; rendered as pre-formatted text block (see gold standard page 5) |
| DOSSIER-03 | "Revenue Model Card" table: model type, pricing, revenue quality, recognition method, contract duration, NDR, retention, ARPU, rev-rec complexity, guidance miss risk, concentration risk, regulatory overlay -- each with D&O Risk column | Partially exists in `company_business_model.py` context builder; needs 8+ new extraction fields (pricing model, revenue quality tier, NDR, ARPU, contract duration, rev-rec complexity) + D&O Risk per row |
| DOSSIER-04 | "Revenue Segment Breakdown" with D&O Litigation Exposure per segment + multi-dimensional concentration assessment (customer, geographic, product, channel, payer) | Existing `revenue_segments`, `geographic_footprint`, `customer_concentration` on CompanyProfile; needs enrichment with D&O Litigation Exposure per segment + 6-dimension concentration matrix with risk levels |
| DOSSIER-05 | "Unit Economics" table: key business metrics with Value/Benchmark/Assessment + narrative identifying SINGLE MOST IMPORTANT METRIC | New LLM extraction for company-specific unit economics from 10-K + S-1; new Pydantic model; narrative generated in BENCHMARK using scoring context |
| DOSSIER-06 | "Revenue Waterfall (Growth Decomposition)": starting->new->expansion->churn->ending for key business metrics | New LLM extraction from 10-K MD&A for growth decomposition components; template renders waterfall table with D&O insight narrative |
| DOSSIER-07 | "Competitive Landscape & Moat Assessment" | **DEFERRED TO PHASE 119** per ROADMAP.md and STATE.md decision |
| DOSSIER-08 | "Emerging Risk Radar": risk/probability/impact/timeframe/D&O Factor/status for next 12-18 months | New LLM extraction from 10-K Risk Factors + 8-K + web search results; combined with existing forward-looking data; maps each risk to scoring factor |
| DOSSIER-09 | "Revenue Recognition (ASC 606)": element/approach/complexity/D&O Risk from 10-K footnotes + billings vs revenue gap | New LLM extraction from 10-K Note 2 (revenue recognition policy); structured into ASC 606 elements; billings vs revenue computation from financial statements |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.x (existing) | New DossierData model + sub-models for revenue card, unit economics, waterfall, emerging risks, ASC 606 | Project standard -- all state models are Pydantic v2 |
| anthropic + instructor | existing | Enhanced LLM extraction for dossier fields from 10-K/S-1 | Existing LLMExtractor pattern in `stages/extract/llm/` |
| jinja2 | existing | 7 new HTML templates for dossier subsections | Project standard for all HTML rendering |
| PyYAML | existing | Brain YAML signals for dossier-related evaluations | Project standard for brain signal loading |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | existing | Unit/integration tests for all new modules | Every new file gets companion tests |

### Alternatives Considered
None -- this phase uses exclusively existing project dependencies. No new libraries needed.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  models/
    dossier.py                          # NEW: DossierData, RevenueModelCard, UnitEconomicMetric,
                                        #       RevenueWaterfall, EmergingRisk, ASC606Element,
                                        #       ConcentrationDimension, RevenueSegmentDossier
  stages/
    extract/
      dossier_extraction.py             # NEW: LLM extraction for dossier-specific fields
      llm/schemas/
        dossier.py                      # NEW: Pydantic schema for dossier LLM extraction
    benchmark/
      dossier_enrichment.py             # NEW: Concentration assessment, unit economics narrative,
                                        #       emerging risk scoring factor mapping, D&O Risk generation
  stages/render/
    context_builders/
      dossier_what_company_does.py      # NEW: "What the Company Does" context
      dossier_money_flows.py            # NEW: "How Money Flows" context
      dossier_revenue_card.py           # NEW: Revenue Model Card context
      dossier_segments.py               # NEW: Revenue Segments + Concentration context
      dossier_unit_economics.py         # NEW: Unit Economics context
      dossier_waterfall.py              # NEW: Revenue Waterfall context
      dossier_emerging_risks.py         # NEW: Emerging Risk Radar context
      dossier_asc606.py                 # NEW: ASC 606 Revenue Recognition context
templates/html/sections/
    dossier.html.j2                     # NEW: Section wrapper
    dossier/
      what_company_does.html.j2         # NEW
      money_flows.html.j2              # NEW
      revenue_model_card.html.j2       # NEW
      revenue_segments.html.j2         # NEW
      unit_economics.html.j2           # NEW
      revenue_waterfall.html.j2        # NEW
      emerging_risk_radar.html.j2      # NEW
      asc_606.html.j2                  # NEW
tests/
  models/test_dossier.py               # NEW
  stages/extract/test_dossier_extraction.py  # NEW
  stages/benchmark/test_dossier_enrichment.py  # NEW
  stages/render/test_dossier_context_builders.py  # NEW
  stages/render/test_dossier_templates.py  # NEW
  stages/render/test_dossier_integration.py  # NEW
```

### Pattern 1: Phase 117 Decomposition Pattern (FOLLOW EXACTLY)
**What:** Each feature follows the same 6-layer decomposition: Pydantic models -> LLM extraction -> BENCHMARK enrichment -> context builders -> Jinja2 templates -> pipeline wiring
**When to use:** Every new worksheet section
**Why:** Established by Phases 115-117, this is the project's proven architecture. Models define schema, extraction populates from filings, BENCHMARK enriches with D&O intelligence, context builders format for templates, templates render dumb HTML, pipeline wiring connects everything.

### Pattern 2: Top-Level State Field for Cross-Stage Data
**What:** Like `ForwardLookingData`, `DossierData` should be a top-level field on `AnalysisState` because dossier data spans EXTRACT (LLM extraction from filings) through BENCHMARK (D&O enrichment, concentration scoring) to RENDER.
**Example:**
```python
# In models/state.py
from do_uw.models.dossier import DossierData

class AnalysisState(BaseModel):
    # ...existing fields...
    dossier: DossierData = Field(
        default_factory=DossierData,
        description="Company intelligence dossier: revenue model, unit economics, emerging risks",
    )
```

### Pattern 3: Context Builder Pure Formatting (No Business Logic)
**What:** Context builders are pure data formatters. No evaluative logic, no D&O commentary generation. They read pre-computed data from state and format for templates.
**Source:** Established in Phase 117 context builders (forward_risk_map.py, posture_context.py, etc.)
**Example:**
```python
def extract_revenue_model_card(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format revenue model card for template. No evaluative logic."""
    dossier = state.dossier
    if not dossier or not dossier.revenue_card:
        return {"revenue_card_available": False}
    card = dossier.revenue_card
    rows = []
    for attr in card:
        rows.append({
            "attribute": attr.label,
            "value": attr.value or "N/A",
            "do_risk": attr.do_risk or "",
            "row_class": _RISK_CSS.get(attr.risk_level, ""),
        })
    return {"revenue_card_available": True, "rows": rows}
```

### Pattern 4: D&O Risk Column from BENCHMARK Enrichment
**What:** D&O Risk commentary for each table row is generated in BENCHMARK stage using signal results + scoring context, stored on the Pydantic model, then rendered as-is by templates. This follows the do_context pattern where all D&O commentary originates from brain YAML or BENCHMARK computation, never from templates or context builders.
**Why:** Brain Portability Principle -- renderers are dumb consumers.

### Pattern 5: LLM Extraction Schema Extension
**What:** Add a new `DossierExtraction` Pydantic schema in `stages/extract/llm/schemas/dossier.py` for structured extraction of dossier-specific fields. Run as a second LLM pass on the 10-K (focused on Items 1, 7, and Note 2) since TenKExtraction already extracts basic fields.
**Why:** The existing `TenKExtraction` schema has `business_description`, `revenue_segments`, `revenue_model_type`, but lacks: pricing model details, NDR, ARPU, contract duration, ASC 606 elements, revenue waterfall components, emerging risks, and unit economics.

### Anti-Patterns to Avoid
- **Hand-rolling D&O commentary in templates:** Every D&O Risk cell must come from BENCHMARK enrichment or brain signal do_context, never from Jinja2 conditionals
- **Overloading CompanyProfile:** DossierData gets its own top-level model; do NOT add 20+ new fields to CompanyProfile
- **Giant extraction prompts:** Split dossier extraction into focused prompts per subsection (revenue model, ASC 606, unit economics, emerging risks) rather than one massive prompt
- **Assuming all companies have SaaS metrics:** Unit economics must gracefully degrade -- NDR, ARPU, engagement rate are SaaS/subscription metrics. Manufacturing companies have different unit economics (cost per unit, capacity utilization, etc.). The LLM extraction must be industry-aware.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Revenue model classification | Custom regex/rules for model type | LLM extraction + existing `revenue_model_type` field | Too many edge cases (HYBRID models, transition periods) |
| Concentration risk scoring | Custom multi-dimensional scoring algorithm | Extend existing `company_business_model.py` concentration logic | Already handles segment, customer, geographic dimensions |
| ASC 606 element identification | Manual parsing of revenue recognition footnotes | LLM extraction with structured schema | Revenue recognition notes are free-text, highly variable |
| Emerging risk identification | Pattern matching on risk factor text | LLM extraction from 10-K Risk Factors | Risk factor language is too varied for regex |
| Billings vs revenue gap | Manual computation from financial statements | LLM extraction + XBRL deferred revenue delta | Requires understanding of company-specific billing terminology |

## Common Pitfalls

### Pitfall 1: Empty Dossier for Non-SaaS Companies
**What goes wrong:** Unit economics (NDR, ARPU, churn, engagement rate) are SaaS metrics. Manufacturing, financial services, or retail companies have completely different KPIs.
**Why it happens:** LLM extraction prompt assumes subscription business model.
**How to avoid:** LLM prompt must be revenue-model-aware. First classify the revenue model (RECURRING, PROJECT, TRANSACTION, HYBRID), then extract model-appropriate unit economics. For TRANSACTION models: volume, ASP, take rate. For PROJECT: backlog, win rate, avg contract value. For RECURRING: NDR, ARPU, churn. Template must handle all variants.
**Warning signs:** "N/A" in every unit economics row for non-SaaS companies.

### Pitfall 2: Revenue Segments Mismatch Between Existing and New Extraction
**What goes wrong:** CompanyProfile already has `revenue_segments` from XBRL/text extraction. New dossier extraction produces different segment names or percentages.
**Why it happens:** Two extraction paths for the same data.
**How to avoid:** DossierData should CONSUME existing `state.company.revenue_segments` as the authoritative source and ENRICH with D&O Litigation Exposure and growth rates, not re-extract. New extraction only adds fields not in the existing data (growth rate per segment, D&O exposure narrative, rev-rec method per segment).
**Warning signs:** Segment names or percentages differ between Section 2 (Company Profile) and Section 5 (Dossier).

### Pitfall 3: Revenue Flow Diagram Rendering
**What goes wrong:** The "How Money Flows" diagram in the gold standard (page 5) is a pre-formatted text block using monospace alignment. HTML rendering of LLM-generated ASCII art breaks easily.
**Why it happens:** Variable-width fonts, HTML whitespace collapsing, LLM formatting inconsistency.
**How to avoid:** Use `<pre>` tag with monospace font in template. Alternatively, generate a structured data model (nodes + edges) and render with CSS, not ASCII art. The gold standard uses fixed-width text with arrows -- simplest approach is `<pre class="revenue-flow">` with the LLM output.
**Warning signs:** Misaligned arrows, broken ASCII art in rendered HTML.

### Pitfall 4: D&O Risk Column Becomes Generic
**What goes wrong:** D&O Risk commentary reads like boilerplate ("This represents D&O risk exposure") instead of company-specific analysis.
**Why it happens:** LLM prompt lacks analytical context (scoring results, signal evaluations, company specifics).
**How to avoid:** QUAL-03 requires every LLM extraction prompt include full analytical context. Pass scoring factors, signal results, financial data to the D&O Risk generation prompt. Each D&O Risk cell must reference THIS company's specific situation.
**Warning signs:** D&O Risk column text could apply to any company by changing the name.

### Pitfall 5: Overloading the LLM Extraction Token Budget
**What goes wrong:** Trying to extract all dossier fields in one massive prompt exceeds context window or produces low-quality extraction.
**Why it happens:** 10-K filings are 50-100+ pages. Dossier needs data from Items 1, 1A, 7, 8 (Note 2), and Risk Factors.
**How to avoid:** Split extraction into 3-4 focused prompts: (1) Revenue model + segments + concentration from Items 1/7, (2) ASC 606 elements from Note 2, (3) Emerging risks from Item 1A, (4) Unit economics from MD&A. Each prompt targets specific filing sections.
**Warning signs:** Extraction quality degrades, fields return null when data is clearly in the filing.

## Code Examples

### DossierData Model Structure
```python
# models/dossier.py
from pydantic import BaseModel, ConfigDict, Field

class RevenueModelCardRow(BaseModel):
    model_config = ConfigDict(frozen=False)
    attribute: str = Field(default="", description="Row label: Model Type, Pricing, etc.")
    value: str = Field(default="", description="Company-specific value")
    do_risk: str = Field(default="", description="D&O Risk assessment for this attribute")
    risk_level: str = Field(default="LOW", description="HIGH/MEDIUM/LOW for CSS styling")

class ConcentrationDimension(BaseModel):
    model_config = ConfigDict(frozen=False)
    dimension: str = Field(default="", description="Customer, Geographic, Product, Channel, Payer")
    metric: str = Field(default="", description="e.g. '17.5% of revenue'")
    risk_level: str = Field(default="LOW", description="HIGH/MEDIUM/LOW")
    do_implication: str = Field(default="", description="D&O Implication narrative")

class EmergingRisk(BaseModel):
    model_config = ConfigDict(frozen=False)
    risk: str = Field(default="", description="Risk description")
    probability: str = Field(default="", description="High/Medium/Low")
    impact: str = Field(default="", description="Very High/High/Medium/Low")
    timeframe: str = Field(default="", description="e.g. '6-18 months', 'Quarterly'")
    do_factor: str = Field(default="", description="Scoring factor reference: F.1 catalyst, F.5 narrative break")
    status: str = Field(default="", description="Current status: Monitoring, Inquiry open, etc.")

class DossierData(BaseModel):
    model_config = ConfigDict(frozen=False)
    # 5.1 What the Company Does
    business_description_plain: str = Field(default="", description="Plain English description")
    core_do_exposure: str = Field(default="", description="The core D&O exposure paragraph")
    # 5.2 How Money Flows
    revenue_flow_diagram: str = Field(default="", description="Text-based revenue flow diagram")
    revenue_flow_narrative: str = Field(default="", description="Key insights about revenue flow")
    # 5.3 Revenue Model Card
    revenue_card: list[RevenueModelCardRow] = Field(default_factory=list)
    # 5.4 Revenue Segments + Concentration
    # (segments consumed from state.company.revenue_segments, enriched here)
    segment_do_exposures: list[dict] = Field(default_factory=list)
    concentration_dimensions: list[ConcentrationDimension] = Field(default_factory=list)
    # 5.5 Unit Economics
    unit_economics: list[dict] = Field(default_factory=list)
    unit_economics_narrative: str = Field(default="")
    # 5.6 Revenue Waterfall
    waterfall_rows: list[dict] = Field(default_factory=list)
    waterfall_narrative: str = Field(default="")
    # 5.8 Emerging Risk Radar
    emerging_risks: list[EmergingRisk] = Field(default_factory=list)
    # 5.9 ASC 606
    asc_606_elements: list[dict] = Field(default_factory=list)
    billings_vs_revenue_narrative: str = Field(default="")
    # Metadata
    source_filings: list[str] = Field(default_factory=list)
    extraction_confidence: str = Field(default="MEDIUM")
```

### Manifest Entry Pattern (from gold standard)
```yaml
# In brain/output_manifest.yaml, new top-level section
- id: intelligence_dossier
  name: "Company & Business -- Intelligence Dossier"
  template: sections/dossier.html.j2
  render_mode: required
  groups:
  - id: dossier_what_company_does
    name: What the Company Does
    template: sections/dossier/what_company_does.html.j2
    render_as: narrative
    display_only: true
  - id: dossier_money_flows
    name: How Money Flows
    template: sections/dossier/money_flows.html.j2
    render_as: preformatted
    display_only: true
  - id: dossier_revenue_model_card
    name: Revenue Model Card
    template: sections/dossier/revenue_model_card.html.j2
    render_as: data_table
    display_only: true
  # ... etc for each subsection
```

### LLM Extraction Prompt Pattern (Revenue Model)
```python
_REVENUE_MODEL_PROMPT = """Extract the revenue model details from this SEC filing.

Company: {company_name} ({ticker})
Sector: {sector}
Revenue Model Type: {revenue_model_type}
Current Revenue: {revenue}
Scoring Context: {scoring_summary}

Extract for each attribute:
1. Model Type: How the company sells (B2B, B2C, B2B2C, marketplace, etc.)
2. Pricing: How they charge (subscription, per-unit, PMPM, usage-based, etc.)
3. Revenue Quality: Tier 1 (contractual recurring), Tier 2 (habitual recurring),
   Tier 3 (one-time/project)
4. Recognition: How revenue is recognized per ASC 606
5. Contract Duration: Average contract length and termination provisions
6. Net Dollar Retention: If disclosed or calculable
7. Gross Retention: If disclosed
8. ARPU: Revenue per user/customer/unit if calculable
9. Rev-Rec Complexity: LOW/MEDIUM/HIGH based on ASC 606 judgment areas
10. Concentration Risk: Based on customer/geographic/product concentration
11. Regulatory Overlay: Key regulatory bodies and compliance requirements

For EACH attribute, also provide a D&O Risk assessment explaining why this
specific value matters for D&O underwriting of THIS company.
"""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Basic business_description from 10-K Item 1 | Full intelligence dossier with D&O risk per data point | Phase 118 (this phase) | Transforms company section from data display to risk intelligence |
| Revenue segments as simple name/percentage pairs | Enriched segments with growth, rev-rec method, D&O litigation exposure per segment | Phase 118 | Underwriter sees where D&O risk concentrates by revenue stream |
| No ASC 606 analysis | Structured ASC 606 element extraction with complexity + D&O risk | Phase 118 | Revenue recognition risk is a top SCA allegation category |
| No emerging risk radar | Forward-looking risk table with probability/impact/timeframe/D&O factor | Phase 118 | Proactive risk identification for next 12-18 months |

## Key Design Decisions

### 1. DossierData as Separate Top-Level Model (Not Extending CompanyProfile)
CompanyProfile already has 30+ fields. Adding 20+ dossier fields would violate the anti-context-rot rule. DossierData lives as `state.dossier` (top-level on AnalysisState), same pattern as `state.forward_looking`.

### 2. Consume Existing Data, Don't Re-Extract
Dossier enrichment CONSUMES existing CompanyProfile fields (`revenue_segments`, `customer_concentration`, `geographic_footprint`, `revenue_model_type`, `business_description`) and ADDS D&O analysis. No duplicate extraction.

### 3. Dossier Extraction as Separate LLM Pass
The existing `TenKExtraction` schema handles basic company profile data. Dossier needs deeper extraction (ASC 606 elements, unit economics, revenue flow, emerging risks) that would bloat the existing schema. New focused extraction prompts target specific filing sections.

### 4. DOSSIER-07 Deferred to Phase 119
Per ROADMAP.md and STATE.md: "DOSSIER-07 (competitive landscape) assigned to Phase 119 (needs peer data + 10-K Item 1 extraction)". Phase 118 renders 8 of 9 dossier subsections.

### 5. Section Placement in HTML Worksheet
The gold standard shows the dossier as Section 5 ("COMPANY & BUSINESS -- Intelligence Dossier"). In the current worksheet, the Business Profile section (`business_profile` in manifest) renders company data. The dossier should either REPLACE or FOLLOW the existing Business Profile section. Recommendation: add as a new top-level manifest section `intelligence_dossier` positioned AFTER `business_profile`, keeping existing business profile for backward compatibility. The dossier subsections are NEW content, not replacements.

### 6. Revenue Flow Diagram Approach
The gold standard uses a text-based flow diagram with arrows (page 5). Two options:
- **Option A (recommended):** LLM generates structured JSON nodes/edges, template renders as styled HTML table/div with CSS arrows. More reliable than ASCII art.
- **Option B:** LLM generates pre-formatted text, rendered in `<pre>` block. Simpler but fragile.

Recommend Option A for reliability. The context builder transforms structured data into template-ready node lists.

## Open Questions

1. **Section ordering in manifest**
   - What we know: Gold standard has dossier as Section 5, after Deal Context (Section 4)
   - What's unclear: Whether to insert before or after existing Business Profile section
   - Recommendation: Add after business_profile as new section; existing section preserved

2. **Unit economics for non-SaaS companies**
   - What we know: Gold standard is for a SaaS-like company (HNGE) with subscription metrics
   - What's unclear: What unit economics look like for manufacturing (RPM), financial services (V), etc.
   - Recommendation: LLM prompt classifies revenue model first, then extracts model-appropriate metrics. Template uses flexible row rendering, not hardcoded SaaS labels.

3. **Emerging risk data sources**
   - What we know: 10-K Risk Factors + 8-K events + forward-looking data from Phase 117
   - What's unclear: Whether web search results should also feed emerging risk radar
   - Recommendation: Start with 10-K + existing forward_looking data. Web search enrichment can be added later.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x (existing) |
| Config file | pyproject.toml (existing) |
| Quick run command | `uv run pytest tests/models/test_dossier.py tests/stages/extract/test_dossier_extraction.py tests/stages/benchmark/test_dossier_enrichment.py tests/stages/render/test_dossier_context_builders.py tests/stages/render/test_dossier_templates.py -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DOSSIER-01 | Business description + core D&O exposure renders | unit + integration | `uv run pytest tests/stages/render/test_dossier_templates.py::test_what_company_does -x` | Wave 0 |
| DOSSIER-02 | Revenue flow diagram renders | unit | `uv run pytest tests/stages/render/test_dossier_templates.py::test_money_flows -x` | Wave 0 |
| DOSSIER-03 | Revenue model card table renders with D&O Risk column | unit + integration | `uv run pytest tests/stages/render/test_dossier_templates.py::test_revenue_model_card -x` | Wave 0 |
| DOSSIER-04 | Revenue segments + concentration assessment renders | unit + integration | `uv run pytest tests/stages/render/test_dossier_templates.py::test_revenue_segments -x` | Wave 0 |
| DOSSIER-05 | Unit economics table + narrative renders | unit | `uv run pytest tests/stages/render/test_dossier_templates.py::test_unit_economics -x` | Wave 0 |
| DOSSIER-06 | Revenue waterfall table + insight narrative renders | unit | `uv run pytest tests/stages/render/test_dossier_templates.py::test_revenue_waterfall -x` | Wave 0 |
| DOSSIER-07 | Competitive landscape + moat assessment | N/A | **DEFERRED TO PHASE 119** | N/A |
| DOSSIER-08 | Emerging risk radar table renders | unit + integration | `uv run pytest tests/stages/render/test_dossier_templates.py::test_emerging_risk_radar -x` | Wave 0 |
| DOSSIER-09 | ASC 606 table + billings vs revenue gap renders | unit | `uv run pytest tests/stages/render/test_dossier_templates.py::test_asc_606 -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** Quick run command (dossier tests only)
- **Per wave merge:** Full suite `uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/models/test_dossier.py` -- model instantiation, serialization, defaults
- [ ] `tests/stages/extract/test_dossier_extraction.py` -- LLM extraction schema validation
- [ ] `tests/stages/benchmark/test_dossier_enrichment.py` -- concentration scoring, D&O risk generation
- [ ] `tests/stages/render/test_dossier_context_builders.py` -- context builder output shapes
- [ ] `tests/stages/render/test_dossier_templates.py` -- template rendering with fixture data
- [ ] `tests/stages/render/test_dossier_integration.py` -- end-to-end from state to rendered HTML

## Sources

### Primary (HIGH confidence)
- Gold standard reference PDF: `Feedme/HNGE - D&O Analysis - 2026-03-18.pdf` (pages 4-12) -- definitive section structure, table schemas, narrative patterns
- Existing codebase: `src/do_uw/models/company.py` -- current CompanyProfile model fields
- Existing codebase: `src/do_uw/stages/extract/llm/schemas/ten_k.py` -- current TenKExtraction LLM schema
- Existing codebase: `src/do_uw/stages/render/context_builders/company_business_model.py` -- current business model context builder
- Existing codebase: `src/do_uw/stages/render/context_builders/forward_risk_map.py` -- Phase 117 context builder pattern
- Existing codebase: `src/do_uw/stages/benchmark/__init__.py` -- benchmark stage orchestration pattern
- Existing codebase: `src/do_uw/brain/output_manifest.yaml` -- manifest section structure

### Secondary (MEDIUM confidence)
- ROADMAP.md: DOSSIER-07 deferred to Phase 119
- STATE.md: Phase ordering and accumulated decisions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - exclusively existing project dependencies, no new libraries
- Architecture: HIGH - follows established Phase 115-117 patterns exactly
- Pitfalls: HIGH - based on direct codebase analysis and gold standard review
- Extraction approach: MEDIUM - LLM extraction quality for ASC 606 and unit economics depends on filing content variability

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable -- internal project patterns, no external dependency changes)
