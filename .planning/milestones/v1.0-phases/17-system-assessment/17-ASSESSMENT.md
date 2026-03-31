# Phase 17: System Assessment & Reorientation

## Where We Are — Honest State of the System

### What Works (Keep)

| Component | Quality | Why It Works |
|-----------|---------|-------------|
| **XBRL Financial Extraction** | HIGH (87%) | Structured API (Company Facts) → typed XBRL concepts → Pydantic models. No ambiguity. |
| **Stock/Market Data** | HIGH | yfinance API provides clean, typed data. 18 stock drop events correctly identified for TSLA. |
| **Distress Models** | HIGH | 4 models (Altman Z, Beneish M, Ohlson O, Piotroski F) computed correctly from XBRL inputs with trajectory tracking. |
| **Scoring Engine** | HIGH (math) | 10-factor scoring, red flag gates, allegation mapping, tier classification — config-driven and correct. |
| **Acquisition Infrastructure** | HIGH | SEC EDGAR, Company Facts, yfinance, EFTS search, blind spot sweeps, caching, rate limiting, fallback chains — all solid. |
| **Pipeline Architecture** | HIGH | Single Pydantic state, 7-stage pipeline, stage isolation, SourcedValue provenance — sound design. |
| **Knowledge Store** | HIGH | SQLAlchemy + SQLite FTS5, lifecycle management, playbooks, ingestion — working correctly. |
| **Dashboard** | MEDIUM-HIGH | FastAPI + htmx + Plotly.js — operational, reads state correctly. Quality limited by data quality. |
| **Actuarial Pricing** | MEDIUM-HIGH | ILF curves, credibility weighting, market calibration — math is correct, limited by scoring inputs. |

### What Does Not Work (Must Fix)

| Component | Quality | Root Cause |
|-----------|---------|------------|
| **Leadership/Executive Extraction** | GARBAGE | Regex extracts "Interim Award", "Performance Award", "Space Exploration" as person names. Generates 8 false red flags. |
| **Board Governance Extraction** | LOW | Independence unknown for 7/8 members. Tenure N/A for all. Committee data partial. |
| **Compensation Extraction** | LOW-MEDIUM | Some fields work (say-on-pay) but detailed comp tables not parsed. |
| **SCA/Litigation Cases** | GARBAGE | 18 cases found but 97% of fields empty. Zero case numbers, courts, dates, settlements, counsel. |
| **SEC Enforcement** | LOW | Keyword detection only. No structured enforcement release parsing. |
| **Sentiment Analysis** | NEARLY EMPTY | 1/13 fields populated. |
| **AI Risk Assessment** | GENERIC DEFAULTS | Tesla classified "General / Other Industries". All sub-scores = 5.0/10 baseline. |
| **Revenue Segments** | EMPTY | Defined on model, no extractor populates them. |
| **Geographic Footprint** | EMPTY | Same — defined but never populated. |
| **Filing Documents Fetch** | BROKEN | `filing_documents` dict is empty. Proxy statement text never reaches extractors. |

### Overall: 55% Field Coverage, With Significant Garbage in the 55%

The system runs end-to-end without crashing. That's not the same as producing useful output. An underwriter would look at the current worksheet and see:
- Correct financial data (Section 3) — this section is genuinely useful
- Correct stock performance data (Section 4 partial) — useful
- Garbage governance data with fake names flagged as red flags (Section 5) — harmful, worse than nothing
- Hollow litigation data with no case details (Section 6) — useless
- A scoring summary built on the above garbage (Section 7) — misleading

---

## Critical Bug: Filing Documents Not Being Fetched

The `fetch_all_filing_documents()` function exists and should download full text for DEF 14A, 8-K, etc. But for TSLA, the `filing_documents` field in `acquired_data` is completely empty. This single bug cascades into:
- No proxy statement text → governance extraction collapses
- No full 8-K text → event extraction limited to filing dates only
- No full DEF 14A → compensation tables, director bios, ownership tables unavailable

**This must be diagnosed and fixed before any LLM extraction work begins.**

---

## Why Regex Extraction Failed

The v1 approach assumed SEC filing text has predictable patterns. It doesn't:
- **Proxy statements**: Complex HTML tables, nested footnotes, non-standard formatting per company
- **Legal proceedings**: Varies from 201 characters (Tesla Item 3) to 10+ pages of dense legal prose
- **Compensation**: Embedded in HTML tables that lose structure when text-stripped
- **Board bios**: Mixed with nomination committee reports, voting results, qualification criteria

Every regex that works for Company A breaks for Company B. The fundamental insight is:
**SEC filings are natural language with structure, not structured data with natural language.**

This is exactly the problem LLMs were built to solve.

---

## Architecture Reorientation

### Three-Tier Extraction (New Strategy)

```
Tier 1: XBRL (Structured API)     → Financial statements, ratios
Tier 2: LLM  (Claude API)         → Governance, litigation, compensation, risk factors
Tier 3: API  (yfinance, Stanford)  → Market data, stock prices, SCA database
```

Regex is demoted to Tier 4 (emergency fallback only).

### LLM Extraction Architecture

**Pattern: Section-targeted extraction with Pydantic schema enforcement**

1. ACQUIRE downloads full filing text (already done, but filing_documents bug must be fixed)
2. Filing pre-parser splits into sections (Items 1-14 for 10-K, standard sections for DEF 14A)
3. For each section, send text + Pydantic schema to Claude API
4. Claude returns structured JSON matching the schema
5. Validate against Pydantic model, cross-check vs XBRL where possible
6. Cache by accession number (same filing never re-extracted)

**Key design decisions:**
- **Model**: Claude Haiku 4.5 for extraction (fast, cheap, sufficient for structured extraction)
- **Schema enforcement**: Use `tool_use` with the Pydantic schema as the tool definition — Claude returns validated JSON
- **Source attribution**: Prompt asks Claude to cite the specific paragraph for each extracted field
- **Cost**: ~$0.10-0.50 per company (10-K sections ≈ 50-100K tokens input, proxy ≈ 30-50K tokens)
- **Batch API**: 50% discount for bulk runs (5,000 companies ≈ $250-1,250 total)
- **Caching**: Cache by (accession_number, section_id, schema_version) — never re-extract same filing

### Development Approach: Claude Code First, API for Pipeline

- **Prompt design & testing**: Use Claude Code (this session) to iterate on extraction prompts against real filing text
- **Integration testing**: Use Claude Code to run extraction on sample filings and validate output
- **Pipeline execution**: Only the `LLMExtractor` class calls the Anthropic API programmatically
- **Cost control**: Haiku for extraction, Batch API for bulk, caching to avoid re-extraction

---

## What Needs to Be Redone

### Phase 21 → Comprehensive Worksheet Redesign (Not Just Section 8)

The original Phase 8 built all rendering on sparse regex data. Every section renderer was designed around "best effort with incomplete data" — lots of "N/A" fallbacks, simplified tables, generic narratives. With LLM extraction producing complete, high-quality data, **the entire worksheet needs to be rethought**:

- **Section narratives**: Replace template fill-in with LLM-grade analytical writing
- **Data tables**: Design for complete data, not empty-field-tolerant layouts
- **Visual design**: Design for rich data visualization, not sparse data with graceful degradation
- **Source attribution**: Every field links to specific filing passage
- **Meeting prep**: Generate from complete data, not sparse signals

---

## Revised v2 Milestone Plan

### Phase 17: System Assessment & Critical Bug Fixes
- Diagnose and fix filing_documents acquisition bug
- Remove garbage data extractors (broken leadership name regex)
- Establish ground truth test cases (3-5 companies with hand-verified data)
- Clean up dual model problem (Phase 3 vs Phase 4 models)
- Move Company Facts XBRL blob out of state.json (16MB → target <1MB)

### Phase 18: LLM Extraction Engine
- Build `LLMExtractor` class with Anthropic API integration
- Filing section pre-parser (all 15 10-K sections, DEF 14A sections)
- Pydantic schema → tool_use definition pipeline
- Extraction caching by accession number
- Cost tracking and token usage logging
- Integration with existing ExtractStage

### Phase 19: LLM Extraction — Governance & Litigation (P0)
- DEF 14A: Board composition, director bios, compensation tables, ownership
- Item 3 / Item 8 Contingencies: Legal proceedings, ASC 450 classification
- Item 1A: Risk factor categorization, D&O relevance scoring
- Replace all garbage regex extractors with LLM

### Phase 20: LLM Extraction — Full Coverage (P1)
- Item 1: Business description, segments, concentration
- Item 7 MD&A: Segment performance, guidance, non-GAAP
- Item 8 Footnotes: Debt detail, tax, stock comp
- Item 9A: Material weaknesses, controls
- 8-K Events: Departures, agreements, acquisitions
- AI risk: Company-specific extraction, patent data

### Phase 21: Multi-Ticker Validation & Production Hardening
- Run on 20+ tickers across industries
- >95% accuracy audit on 50 random fields
- Edge cases: FPI (20-F), REITs, pre-revenue biotech, recent IPOs
- Cost per company documented
- Performance: <5 min per company

### Phase 22: Comprehensive Worksheet Redesign
- All section renderers rebuilt for complete data
- Narrative quality: reads like an analyst wrote it
- Full source attribution throughout
- Visual design for rich data (charts, tables, formatting)
- Meeting prep from complete data
- Word/PDF/Markdown all updated
- AI risk section with real company-specific data
