# Phase 13: AI Transformation Risk Factor - Research

**Researched:** 2026-02-10
**Domain:** AI business model disruption risk assessment
**Confidence:** MEDIUM

## Summary

Phase 13 implements a dedicated AI transformation risk assessment as a separate analytical dimension beyond the existing 10-factor scoring model. This research identifies that AI risk assessment requires industry-specific frameworks (what threatens a SaaS company differs fundamentally from biotech or financial services), peer-relative scoring (is the company ahead/behind competitors in AI adoption and defense), and fast-moving data acquisition (AI disclosures in SEC filings, earnings calls, patent activity, and hiring trends). The standard approach combines disclosure analysis from existing SEC filings (Item 1A risk factors, MD&A) with external signals (patent filings via USPTO, job postings, competitor AI announcements, industry analyst reports). The implementation follows the established pattern: new ACQUIRE clients for AI-specific data, new EXTRACT modules for disclosure parsing, industry-specific scoring models in the knowledge store, and a new worksheet section (Section 8) rendered via the existing rendering pipeline.

**Primary recommendation:** Follow the existing 7-stage pipeline architecture with AI risk as a parallel analytical track, reusing established infrastructure (knowledge store for industry models, ExtractStage sub-orchestrator pattern, section rendering dispatch) while adding AI-specific data clients and extractors.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.28+ | HTTP client for USPTO API, web fetching | Already in use, async capable, HTTP/2 support |
| pydantic | 2.10+ | AI risk assessment models | Project standard for all data models |
| sqlalchemy | 2.0+ | Knowledge store for industry AI impact models | Phase 9 knowledge store infrastructure |
| existing SEC client | N/A | SEC 10-K Item 1A, 8-K disclosures | Already fetches filings, extend to parse AI mentions |
| existing web search | N/A | Competitor AI announcements, analyst reports | Phase 2 blind spot discovery client |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yfinance | 1.1+ | Earnings call metadata (dates, links) | Already in use for market data, can identify AI-heavy calls |
| rapidfuzz | 3.14+ | Fuzzy matching for AI keyword extraction | Already in use, handles variant terminology (AI/ML/GenAI/LLM) |
| None (use stdlib re) | N/A | Pattern matching for disclosure sections | Regex sufficient for SEC filing structure |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| USPTO public API | Patent database libraries (e.g., `patentpy`) | USPTO public API is free and sufficient; specialized libraries add dependency for marginal benefit |
| Rule-based keyword extraction | spaCy/transformers NLP | Deep NLP is overkill for counting AI mentions in structured SEC filings; adds model download burden |
| Custom AI impact models | External AI risk APIs | No suitable free APIs exist; proprietary models align with project's public-data-only constraint |

**Installation:**
No new core dependencies required. All functionality builds on existing stack (httpx, pydantic, sqlalchemy, SEC client, web search).

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
├── stages/
│   ├── acquire/
│   │   └── clients/
│   │       ├── ai_disclosure_client.py    # Extract AI mentions from existing SEC filings
│   │       └── patent_client.py           # USPTO patent API for AI patent filings
│   ├── extract/
│   │   ├── ai_disclosure_extract.py       # Parse Item 1A AI risks, count mentions
│   │   ├── ai_competitive_extract.py      # Peer AI adoption comparison
│   │   └── extract_ai_risk.py             # Sub-orchestrator (follows extract_market pattern)
│   ├── score/
│   │   └── ai_risk_scoring.py             # Score 5 AI sub-dimensions
│   └── render/
│       └── sections/
│           └── sect8_ai_risk.py           # Section 8: AI Transformation Risk
├── models/
│   └── ai_risk.py                         # AIRiskAssessment, AISubDimension, AICompetitivePosition
├── knowledge/
│   └── ai_impact_models.py                # Industry-specific AI impact models
└── config/
    └── ai_risk_weights.json               # Scoring weights per industry
```

### Pattern 1: Reuse ExtractStage Sub-Orchestrator Pattern
**What:** AI risk extraction follows the same sub-orchestrator pattern as market/governance/litigation extractors.
**When to use:** When adding a new analytical dimension that requires multiple extractors with shared dependencies.
**Example:**
```python
# File: src/do_uw/stages/extract/extract_ai_risk.py
# Source: Mirrors extract_market.py, extract_governance.py, extract_litigation.py

from do_uw.models.ai_risk import AIRiskAssessment
from do_uw.stages.extract.validation import ExtractionReport

def run_ai_risk_extractors(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> AIRiskAssessment:
    """Run all AI risk extractors in order.

    1. AI disclosure extraction (Item 1A, MD&A, earnings calls)
    2. Patent activity analysis (USPTO filings)
    3. Competitive positioning (peer comparison)
    4. Industry-specific impact assessment
    5. Narrative synthesis
    """
    # Extract AI disclosures from filings
    disclosure_data, disc_report = extract_ai_disclosures(state)
    reports.append(disc_report)

    # Analyze patent activity
    patent_data, patent_report = extract_patent_activity(state)
    reports.append(patent_report)

    # Competitive positioning
    competitive, comp_report = assess_competitive_position(state, disclosure_data)
    reports.append(comp_report)

    # Industry-specific scoring
    industry_score = score_industry_impact(state, disclosure_data, competitive)

    return AIRiskAssessment(
        disclosure_analysis=disclosure_data,
        patent_activity=patent_data,
        competitive_position=competitive,
        industry_score=industry_score,
    )
```

### Pattern 2: Industry-Specific AI Impact Models in Knowledge Store
**What:** Store per-industry AI impact models as JSON in knowledge store, loaded at runtime like industry playbooks.
**When to use:** When scoring logic varies significantly by industry vertical.
**Example:**
```python
# File: src/do_uw/knowledge/ai_impact_models.py
# Source: Mirrors playbooks.py pattern from Phase 9

AI_IMPACT_MODELS = [
    {
        "id": "saas_ai_impact",
        "industry": "Technology/SaaS",
        "sic_ranges": [(7370, 7379)],  # Computer programming, data processing
        "exposure_areas": {
            "revenue_displacement": {
                "weight": 0.35,
                "activities": ["customer support automation", "code generation", "documentation"],
                "threat_level": "HIGH",
            },
            "cost_structure": {
                "weight": 0.20,
                "activities": ["engineering labor reduction", "QA automation"],
                "threat_level": "MEDIUM",
            },
            "competitive_moat": {
                "weight": 0.25,
                "activities": ["feature commoditization", "AI-native competitors"],
                "threat_level": "HIGH",
            },
            "workforce_automation": {
                "weight": 0.15,
                "activities": ["sales automation", "CS deflection"],
                "threat_level": "MEDIUM",
            },
            "regulatory_ip": {
                "weight": 0.05,
                "activities": ["training data IP", "model regulation"],
                "threat_level": "LOW",
            },
        },
    },
    {
        "id": "biotech_ai_impact",
        "industry": "Biotech/Pharma",
        "sic_ranges": [(2834, 2836), (8731, 8734)],  # Pharma, biotech, clinical labs
        "exposure_areas": {
            "revenue_displacement": {
                "weight": 0.15,
                "activities": ["AI-discovered drugs", "virtual screening"],
                "threat_level": "MEDIUM",
            },
            "cost_structure": {
                "weight": 0.30,
                "activities": ["clinical trial design", "patient recruitment"],
                "threat_level": "HIGH",
            },
            "competitive_moat": {
                "weight": 0.20,
                "activities": ["accelerated drug discovery by competitors"],
                "threat_level": "MEDIUM",
            },
            "workforce_automation": {
                "weight": 0.10,
                "activities": ["lab automation", "data analysis"],
                "threat_level": "LOW",
            },
            "regulatory_ip": {
                "weight": 0.25,
                "activities": ["FDA AI validation", "AI-discovered IP disputes"],
                "threat_level": "HIGH",
            },
        },
    },
    # Financial Services, Energy, Healthcare models omitted for brevity
]
```

### Pattern 3: SEC AI Disclosure Parsing Without Custom NLP
**What:** Extract AI risk mentions from Item 1A using simple keyword matching and section extraction.
**When to use:** Structured SEC filings with predictable section headers.
**Example:**
```python
# File: src/do_uw/stages/extract/ai_disclosure_extract.py
# Source: Mirrors filing_sections.py pattern

import re
from do_uw.stages.extract.filing_sections import extract_section

def extract_ai_disclosures(state: AnalysisState) -> tuple[AIDisclosureData, ExtractionReport]:
    """Extract AI mentions from Item 1A risk factors and MD&A.

    Returns count of AI mentions, specific risk factors disclosed,
    sentiment (threat vs opportunity), and year-over-year trend.
    """
    # Get Item 1A text from most recent 10-K
    item_1a_text = extract_section(state, "Item 1A", "10-K", most_recent=True)

    # Simple keyword counting (case-insensitive)
    ai_keywords = [
        "artificial intelligence", "machine learning", "generative AI",
        "large language model", "AI model", "AI system", "AI technology",
        "automation", "algorithmic"
    ]

    mentions = 0
    risk_factors = []
    for keyword in ai_keywords:
        pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
        matches = pattern.findall(item_1a_text)
        mentions += len(matches)

        # Extract surrounding context for risk factors
        for match in matches:
            context = _extract_risk_factor_context(item_1a_text, match)
            if context:
                risk_factors.append(context)

    # Classify sentiment: does disclosure frame AI as threat or opportunity?
    sentiment = _classify_ai_sentiment(item_1a_text, ai_keywords)

    # Compare to prior year for trend
    prior_year_mentions = _get_prior_year_ai_mentions(state)
    trend = "increasing" if mentions > prior_year_mentions else "stable"

    return AIDisclosureData(
        mention_count=mentions,
        risk_factors=risk_factors,
        sentiment=sentiment,
        yoy_trend=trend,
    ), ExtractionReport(...)
```

### Anti-Patterns to Avoid
- **Reinventing peer comparison logic:** Reuse existing peer group from Phase 3 (construct_peer_group). Don't build a separate AI peer selection mechanism.
- **Creating a separate scoring scale:** AI risk should integrate with existing tier classification (WIN/WANT/WRITE/WATCH/WALK). Don't invent a parallel rating system.
- **Hardcoding industry AI impact in extractors:** Store industry models in knowledge store (ai_risk_weights.json), not in extractor code. Extractors should be industry-agnostic.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| USPTO patent search | Custom patent database scraper | USPTO public API (https://developer.uspto.gov/) | Free API with structured patent data, searching, and bulk download; scraping is fragile and violates TOS |
| AI keyword synonym expansion | Manual AI/ML/GenAI variant lists | `rapidfuzz` fuzzy matching with seed terms | Already in use; handles terminology variance without maintaining exhaustive synonym lists |
| Earnings call transcript acquisition | Custom call transcript scraper | Existing yfinance metadata + web search for transcript links | Transcripts are public but no free structured API; web search finds published transcripts; building scraper is brittle |
| Industry classification | Custom SIC/NAICS to industry mapper | Reuse Phase 1 sic_to_sector() + Phase 9 playbook activation | Already maps SIC to 5 industry verticals; don't duplicate classification logic |

**Key insight:** AI risk assessment data sources are mostly extensions of existing acquisition (SEC filings, web search, patent APIs) rather than net-new systems. The challenge is synthesis and industry-specific interpretation, not raw data access.

## Common Pitfalls

### Pitfall 1: AI Mention Counting as Proxy for Risk
**What goes wrong:** Counting "AI" mentions in 10-K as the sole risk metric produces false positives (company discusses AI as opportunity, not threat) and false negatives (company faces AI disruption but doesn't disclose extensively).
**Why it happens:** Quantitative metrics (mention counts) are easy to implement, qualitative assessment (threat vs opportunity) requires semantic analysis.
**How to avoid:** Combine mention counts with sentiment classification (threat/opportunity/neutral) and competitive positioning (peer comparison). A company with 50 AI mentions framed as opportunities while peers have 200 threat-framed mentions is BEHIND, not ahead.
**Warning signs:** AI risk score driven primarily by mention count, no distinction between proactive AI adoption vs defensive disclosure of AI threats.

### Pitfall 2: Static Industry AI Impact Models
**What goes wrong:** Industry AI exposure changes rapidly (coding went from "AI will assist" to "AI may replace" in 18 months). Static models in config files become stale quickly.
**Why it happens:** Config-driven approach (CLAUDE.md requirement) discourages frequent updates to JSON files.
**How to avoid:** Build model versioning into knowledge store (Phase 9 infrastructure supports versioning), add last_updated timestamp to AI impact models, log warnings when models are >6 months old. Consider quarterly review cadence for AI impact weights.
**Warning signs:** AI risk scores feel disconnected from current market reality, industry impact models unchanged for >6 months, no mechanism to update exposure weights.

### Pitfall 3: Peer AI Adoption Data Scarcity
**What goes wrong:** Peer comparison requires AI disclosure data for peer companies, but Phase 13 runs on a single ticker. Without pre-populated peer data, peer-relative scoring degrades to "not available."
**Why it happens:** Full analysis pipeline for each peer is expensive; caching peer AI data requires running pipeline on peers.
**How to avoid:** Start with lightweight peer signals (mention count only from cached 10-Ks, not full extraction) for initial comparison. Add --analyze-peers CLI flag to optionally run full AI extraction on peer group. Store peer AI mention counts in knowledge store for cross-analysis reuse.
**Warning signs:** "Peer comparison unavailable" in every AI risk assessment, no cached peer data accumulation over multiple analysis runs, slow analysis when peers ARE analyzed.

### Pitfall 4: Overreliance on SEC Disclosures for AI Threat Assessment
**What goes wrong:** Companies frame AI as opportunity in official filings even when existentially threatened. SEC disclosures are optimistic by nature.
**Why it happens:** Item 1A risk factors are legal disclosures, not strategic assessments. Companies minimize disclosed threats.
**How to avoid:** Cross-validate SEC disclosures with external signals: competitor AI announcements (web search), analyst reports flagging AI disruption, job posting trends (hiring AI roles = offense, cutting headcount = defense/retreat), patent activity (offense vs none = reactive).
**Warning signs:** High AI adoption scores for companies clearly disrupted by AI (e.g., legacy software displaced by AI-native startups), scoring driven solely by 10-K text without external validation.

## Code Examples

Verified patterns from existing codebase:

### ExtractStage Sub-Orchestrator Integration
```python
# File: src/do_uw/stages/extract/__init__.py (ExtractStage.run method)
# Source: Phase 4 integration pattern (lines 139-145)

# Phase 13: AI risk extractors (SECT8)
extracted.ai_risk = run_ai_risk_extractors(state, reports)
```

### Pydantic Model for AI Risk Assessment
```python
# File: src/do_uw/models/ai_risk.py
# Source: Mirrors governance_forensics.py, market_events.py patterns

from __future__ import annotations
from pydantic import BaseModel, Field
from do_uw.models.common import SourcedValue, Confidence

class AISubDimension(BaseModel):
    """Single AI risk sub-dimension (e.g., revenue displacement)."""
    dimension: str
    score: float  # 0-10 scale
    weight: float  # Industry-specific weight
    evidence: list[str]
    threat_level: str  # HIGH/MEDIUM/LOW

class AICompetitivePosition(BaseModel):
    """Peer-relative AI positioning."""
    company_ai_mentions: int
    peer_avg_mentions: float
    percentile_rank: float | None  # 0-100 where 100 = most AI-forward
    adoption_stance: str  # LEADING/INLINE/LAGGING/UNKNOWN

class AIRiskAssessment(BaseModel):
    """Complete AI transformation risk assessment (SECT8)."""
    overall_score: float  # 0-100 weighted composite
    sub_dimensions: list[AISubDimension]
    competitive_position: AICompetitivePosition
    industry_model_id: str  # References knowledge store AI impact model
    disclosure_trend: str  # INCREASING/STABLE/DECREASING
    narrative: SourcedValue[str]  # Industry-specific risk narrative
    peer_comparison_available: bool
    forward_indicators: list[str]  # Patent filings, hiring trends, etc.
```

### USPTO Patent API Client
```python
# File: src/do_uw/stages/acquire/clients/patent_client.py
# Source: Mirrors sec_client.py HTTP client pattern

import httpx
from do_uw.stages.acquire.rate_limiter import rate_limited_get

USPTO_PATENT_SEARCH_URL = "https://developer.uspto.gov/ibd-api/v1/patent/application"

class PatentClient:
    """USPTO patent API client for AI-related patent filings."""

    @property
    def name(self) -> str:
        return "uspto_patents"

    def acquire(
        self,
        state: AnalysisState,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any]:
        """Fetch AI-related patent applications for company.

        Searches USPTO by company name for patents with AI/ML keywords
        in abstract or claims. Returns count, filing dates, patent numbers.
        """
        company_name = state.company.identity.legal_name.value

        # Search for AI-related patents filed by company
        query = f'assignee:"{company_name}" AND (abstract:"artificial intelligence" OR abstract:"machine learning")'

        # Use rate-limited HTTP client (10 req/sec limit)
        response = rate_limited_get(
            USPTO_PATENT_SEARCH_URL,
            params={"query": query, "rows": 100},
        )

        patents = response.get("results", [])

        return {
            "patent_count": len(patents),
            "filings": [
                {
                    "patent_number": p.get("patentNumber"),
                    "filing_date": p.get("filingDate"),
                    "title": p.get("title"),
                }
                for p in patents
            ],
            "as_of": datetime.now(UTC),
        }
```

### Section 8 Renderer
```python
# File: src/do_uw/stages/render/sections/sect8_ai_risk.py
# Source: Mirrors sect5_governance.py, sect6_litigation.py patterns

from do_uw.models.state import AnalysisState
from do_uw.stages.render.docx_helpers import add_heading, add_paragraph

def render_sect8_ai_risk(doc: Any, state: AnalysisState) -> None:
    """Render Section 8: AI Transformation Risk."""
    if not state.extracted or not state.extracted.ai_risk:
        add_paragraph(doc, "AI risk assessment unavailable.")
        return

    ai_risk = state.extracted.ai_risk

    # Overall score and tier
    add_heading(doc, "AI Transformation Risk", level=1)
    add_paragraph(
        doc,
        f"Overall AI Risk Score: {ai_risk.overall_score:.1f}/100 "
        f"(Industry: {ai_risk.industry_model_id})"
    )

    # Sub-dimensions table
    add_heading(doc, "Risk Sub-Dimensions", level=2)
    _render_subdimensions_table(doc, ai_risk.sub_dimensions)

    # Competitive positioning
    add_heading(doc, "Peer Comparison", level=2)
    if ai_risk.peer_comparison_available:
        _render_competitive_position(doc, ai_risk.competitive_position)
    else:
        add_paragraph(doc, "Peer comparison unavailable (run with --analyze-peers).")

    # Industry-specific narrative
    add_heading(doc, "Industry-Specific Assessment", level=2)
    add_paragraph(doc, ai_risk.narrative.value)

    # Forward indicators
    if ai_risk.forward_indicators:
        add_heading(doc, "Forward Indicators", level=2)
        for indicator in ai_risk.forward_indicators:
            add_paragraph(doc, f"• {indicator}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| AI as general technology risk | AI as industry-specific disruption factor | 2025-2026 | Requires per-industry impact models, not one-size-fits-all |
| Manual AI risk assessment | Automated disclosure parsing + peer comparison | 2026 | Scalable to entire portfolio, not just ad-hoc deep dives |
| SEC 10-K as sole data source | Multi-signal (10-K + earnings calls + patents + web) | 2024-2026 | Cross-validation reduces disclosure gaming |
| Static risk taxonomy | Fast-updating exposure models | 2026 | AI landscape changes faster than traditional risk factors |

**Deprecated/outdated:**
- AI as a subset of "technology risk" or "operational risk" is outdated; AI warrants dedicated assessment as business model threat
- Relying solely on Item 1A risk factor disclosures is insufficient; companies downplay existential threats in official filings
- Treating all industries equally (uniform AI impact model) is obsolete; industry-specific exposure is critical

## Open Questions

Things that couldn't be fully resolved:

1. **Earnings call transcript acquisition**
   - What we know: Earnings call transcripts contain rich AI discussion but no free structured API exists. Motley Fool, Seeking Alpha, Yahoo Finance publish transcripts but structure varies.
   - What's unclear: Most reliable free source for call transcripts, whether web scraping violates TOS.
   - Recommendation: Start with yfinance metadata (call dates), use web search to find transcript URLs (treat as LOW confidence data source). Defer full transcript parsing to future enhancement; focus on 10-K Item 1A (HIGH confidence).

2. **Peer AI data accumulation strategy**
   - What we know: Peer-relative scoring requires AI data for peer companies, but running full pipeline on 5-10 peers per analysis is expensive.
   - What's unclear: Whether to pre-populate peer data (requires batch processing), cache lightweight peer metrics (mention counts only), or accept degraded peer comparison.
   - Recommendation: Implement lightweight peer AI mention count extraction (reuse cached 10-Ks, simple keyword count) for fast peer comparison. Add --deep-peer-analysis flag for optional full extraction. Store peer mention counts in knowledge store for cross-analysis reuse.

3. **AI impact model update cadence**
   - What we know: AI landscape changes faster than traditional risk factors (6-12 month half-life vs multi-year stability). Config files (ai_risk_weights.json) discourage frequent updates.
   - What's unclear: How to signal model staleness, who updates models, whether to automate model calibration.
   - Recommendation: Add last_updated timestamp to AI impact models, log warnings when >6 months old. Defer automated calibration to Phase 14 (knowledge governance). Manual quarterly review initially.

4. **Integration with existing tier classification (WIN/WANT/WRITE/WATCH/WALK)**
   - What we know: AI risk is a separate dimension but should influence tier classification. A company with high traditional score but existential AI threat should be downgraded.
   - What's unclear: Whether AI risk is a red flag gate (score ceiling), additive factor, or modifier to existing factors.
   - Recommendation: Implement as additive dimension initially (AI risk score + traditional 10-factor score = composite). Phase 15 calibration (multi-ticker validation) determines whether AI risk warrants red flag gate status.

## Sources

### Primary (HIGH confidence)
- White & Case: [Key considerations for 2026 annual reporting](https://www.whitecase.com/insight-alert/key-considerations-2026-annual-reporting-and-proxy-season-your-upcoming-form-10-k) - SEC AI disclosure requirements
- BLS: [Incorporating AI impacts in employment projections](https://www.bls.gov/opub/mlr/2025/article/incorporating-ai-impacts-in-bls-employment-projections.htm) - Occupational AI exposure data
- Allianz: [Risk Barometer 2026 - AI](https://commercial.allianz.com/news-and-insights/expert-risk-articles/allianz-risk-barometer-2026-ai.html) - AI business model impact framework
- USPTO Developer Hub: https://developer.uspto.gov/ - Patent API documentation (verified official source)

### Secondary (MEDIUM confidence)
- FactSet: [Highest number of S&P 500 earnings calls citing AI](https://insight.factset.com/highest-number-of-sp-500-earnings-calls-citing-ai-over-the-past-10-years-1) - Earnings call AI mention trends
- Greenberg Traurig: [AI Patent Outlook for 2026](https://www.gtlaw.com/en/insights/2026/01/ai-patent-outlook-for-2026) - Patent filing trends
- PwC: [2026 AI Business Predictions](https://www.pwc.com/us/en/tech-effect/ai-analytics/ai-predictions.html) - Industry AI adoption trends
- Bain & Company: [Uncovering AI Risks and Opportunities](https://www.bain.com/insights/new-diligence-challenge-uncovering-ai-risks-and-opportunities/) - AI diligence framework (verified with official Bain site)

### Tertiary (LOW confidence)
- WebSearch results on industry-specific AI exposure (SaaS, biotech, financial services) - Multiple sources but not independently verified with official documentation
- AI job displacement statistics from non-BLS sources - Claims require validation against official labor data
- Earnings call transcript analysis methodologies - Implementation details not verified with academic sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use, no new dependencies required
- Architecture: HIGH - Follows established ExtractStage sub-orchestrator pattern from Phases 4-5
- Pitfalls: MEDIUM - AI-specific pitfalls (static models, mention counting) verified via search results, general pitfalls (data scarcity) are extrapolations

**Research date:** 2026-02-10
**Valid until:** 2026-04-10 (60 days - AI landscape changes faster than typical research validity)
