# Phase 18: LLM Extraction Engine — Context

## Decisions

These are LOCKED decisions from user discussion. Plans MUST implement these exactly.

### 1. Complete Document Extraction (NOT Section-Based)

**Decision**: Send COMPLETE filing documents to the LLM — entire 10-K, entire DEF 14A, entire 8-K. No pre-splitting into sections or items. Claude's 200k context handles full documents.

**Rationale**: Previous section-parsing approach (extracting Item 1, Item 1A, etc. separately) caused data loss and fragile regex-based splitting. The system has repeatedly failed because of attempts to be clever about chunking. Send the whole document. Extract everything in one pass.

**What this means for implementation**:
- The `LLMExtractor` sends raw filing `full_text` directly to the API
- No `filing_sections.py` expansion needed — existing section parsing stays as-is for regex fallback only
- One API call per filing document, not per section
- For oversized 10-Ks: strip exhibits, signatures, certifications, XBRL tags (boilerplate) to fit context. Keep ALL substantive Items.

### 2. ALL Acquired Filing Types

**Decision**: Phase 18 handles extraction for ALL filing types that ACQUIRE already fetches: 10-K, 10-Q, DEF 14A, 8-K, Form 4, S-3, 13D/13G, proxy amendments — everything.

**What this means**: One Pydantic extraction schema per filing type. Every filing that reaches `acquired.filing_documents` gets LLM extraction.

### 3. One Schema Per Filing Type

**Decision**: Single comprehensive Pydantic model per filing type (e.g., `TenKExtraction`, `DEF14AExtraction`, `EightKExtraction`). One call extracts ALL structured data from a document.

**What this means**: Schemas may be large (10-K schema covers business, risk factors, legal proceedings, financials, MD&A, controls — everything in one model). The LLM gets the complete document + complete schema and returns everything at once.

### 4. instructor + Anthropic API

**Decision**: Use the `instructor` library wrapping Anthropic API, exactly as done in `pricing_ingestion.py`. Pydantic `response_model` validation. Tool_use under the hood.

**What this means**: Reuse the proven pattern. Add `anthropic` and `instructor` to pyproject.toml dependencies.

### 5. Haiku 4.5 Default Model

**Decision**: Claude Haiku 4.5 as the default extraction model. Fast, cheap, good at structured extraction.

**What this means**: ~$0.01-0.05 per filing extraction. Target cost <$1.00/company total across all filings.

### 6. SQLite Cache Table

**Decision**: New table in existing `analysis.db`. Cache key: `(accession_number, filing_type, schema_version)`. Stores extracted JSON + token counts + cost. Never re-extract same filing.

**What this means**: Extend `AnalysisCache` or add a new `ExtractionCache` table. Schema version in the key ensures re-extraction when schemas change.

### 7. LLM Primary, Regex Fallback

**Decision**: LLM extraction is the primary path. Existing regex extractors remain as fallback when API is unavailable, rate-limited, or erroring.

**What this means**: Dual extraction path. Try LLM first. If it fails, fall back to regex. Don't remove any regex code yet. Phase 19-20 may eventually deprecate regex.

### 8. Cost Budget: $1.00/company Maximum

**Decision**: Maximum $1.00 per company across all filing extractions. Generous budget — focus on quality first, optimize later.

**What this means**: With Haiku at ~$0.01-0.05/filing, this allows 20-100 filing extractions per company. More than enough for all filing types.

### 9. Truncate Boilerplate for Oversized Documents

**Decision**: When a filing exceeds context limits, strip known low-value content: exhibit index, signatures, officer certifications, XBRL inline tags, SEC filing headers. Keep all substantive Items.

**What this means**: Implement a `strip_boilerplate(text)` function that removes known patterns. Most 10-Ks fit after stripping. No need to escalate to Sonnet or split into multiple passes.

## Claude's Discretion

These areas are implementation choices Claude can make during planning.

- **ExtractionCache table schema** — exact column definitions, indexes, migration approach
- **Schema version strategy** — how to version extraction schemas (hash, semver, etc.)
- **instructor configuration** — retry logic, max_tokens, temperature settings
- **Boilerplate stripping patterns** — which regex patterns to use for exhibit/signature removal
- **Error handling strategy** — retry count, backoff, fallback triggers
- **Cost tracking granularity** — per-filing vs per-company cost rollup
- **Token counting approach** — pre-count tokens to check fit, or just try and handle overflow
- **Source attribution format** — how to store the specific passage each extracted field came from
- **Filing type schema priority** — order of implementation if phased within Phase 18
- **Integration with existing extractors** — how LLM results feed into the existing Pydantic state models

## Deferred Ideas

These are OUT OF SCOPE for Phase 18. Do NOT include in plans.

- Batch API integration (mentioned in roadmap strategy but not a Phase 18 requirement)
- Replacing regex extractors entirely (Phase 19-20 scope)
- Multi-model routing (use Haiku for everything in Phase 18)
- Real-time extraction during ACQUIRE (extract after all filings acquired)
- Cross-filing correlation (e.g., comparing 10-K risk factors across years)
- Human-in-the-loop review workflow for extracted data
