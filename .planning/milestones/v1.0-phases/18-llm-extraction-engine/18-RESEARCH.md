# Phase 18: LLM Extraction Engine - Research

**Researched:** 2026-02-10
**Domain:** LLM-powered structured data extraction from SEC filings using instructor + Anthropic API
**Confidence:** HIGH

## Summary

Phase 18 replaces the current regex-based filing extraction with LLM-powered extraction that sends complete SEC filing documents to Claude Haiku 4.5 with Pydantic schemas and receives validated structured data back. The system uses the `instructor` library (v1.14.5) wrapping the Anthropic Python SDK (v0.79.0) with `from_provider("anthropic/claude-haiku-4-5")`, the same proven pattern already in `pricing_ingestion.py`.

Key technical findings: Haiku 4.5 has a 200k token context window which fits most SEC filings after boilerplate stripping. Pricing is $1/MTok input, $5/MTok output, keeping total cost well under $1.00/company. The Anthropic SDK provides a free `messages.count_tokens()` endpoint to pre-verify document fit before sending. Structured outputs via tool_use support nested Pydantic models but prohibit recursive schemas and some JSON Schema features.

**Primary recommendation:** Use instructor's `from_provider` + `chat.completions.create` with `response_model` exactly as in `pricing_ingestion.py`. Add `anthropic>=0.79.0` and `instructor>=1.14.0` as optional dependencies (`llm` extra). Use schema hash (from `model_json_schema()`) as the version key for cache invalidation.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `instructor` | >=1.14.0 | Pydantic-validated LLM extraction | Already used in `pricing_ingestion.py`. Wraps Anthropic tool_use, handles retries on validation failure, returns typed Pydantic objects. |
| `anthropic` | >=0.79.0 | Anthropic API client | Required by instructor's `from_provider("anthropic/...")`. Provides `messages.count_tokens()` for pre-flight token checks. |
| `pydantic` | >=2.10 (already dep) | Extraction schemas + validation | Already a core dependency. Used for `response_model` in instructor and for `model_json_schema()` to generate schema hashes. |
| `sqlite3` | stdlib | Extraction cache | Already used in `AnalysisCache`. New `extraction_cache` table in existing `analysis.db`. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `hashlib` | stdlib | Schema version hashing | Generate deterministic hash from `model_json_schema()` for cache invalidation |
| `json` | stdlib | JSON serialization for cache storage | Store extracted results and token counts |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| instructor | Raw Anthropic `tool_use` | More control but must handle validation, retries, schema conversion manually. instructor already proven in codebase. |
| instructor | Anthropic `messages.parse()` with `output_format` | New GA feature (structured outputs). Could bypass instructor entirely. But instructor provides retry logic and is already proven in the codebase. |
| Haiku 4.5 | Sonnet 4 | 3x more expensive ($3/$15 vs $1/$5 per MTok). Only needed if Haiku quality is insufficient. |
| SQLite raw | SQLAlchemy ORM | Overkill for a simple cache table. Raw sqlite3 matches existing `AnalysisCache` pattern. |

**Installation:**
```bash
uv add anthropic instructor
# Or as optional dependency group:
# [project.optional-dependencies]
# llm = ["anthropic>=0.79.0", "instructor>=1.14.0"]
```

## Architecture Patterns

### Recommended Project Structure

```
src/do_uw/stages/extract/
  llm/
    __init__.py              # LLMExtractor class (main entry point)
    schemas/
      __init__.py            # Schema registry, version hashing
      ten_k.py               # TenKExtraction Pydantic model
      def14a.py              # DEF14AExtraction Pydantic model
      eight_k.py             # EightKExtraction Pydantic model
      form4.py               # Form4Extraction Pydantic model
      ten_q.py               # TenQExtraction Pydantic model
      common.py              # Shared sub-models (PersonInfo, MoneyAmount, etc.)
    boilerplate.py           # strip_boilerplate() for oversized filings
    cache.py                 # ExtractionCache (sqlite3, same DB as AnalysisCache)
    cost_tracker.py          # Per-filing and per-company cost tracking
    prompts.py               # System prompts per filing type
```

**Rationale:** Schemas in their own subpackage because each filing type schema may be 50-100 lines. LLM extraction logic is cleanly separated from regex extractors. Everything under `stages/extract/llm/` keeps the 500-line-per-file rule.

### Pattern 1: LLMExtractor (Core Extraction Class)

**What:** Single class that takes a filing document and schema, calls the API, caches results, tracks costs.
**When to use:** Every filing extraction.
**Example:**

```python
# Source: Verified from pricing_ingestion.py + instructor docs
import instructor
from typing import TypeVar, cast
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class LLMExtractor:
    """LLM-powered filing extraction using instructor + Anthropic."""

    def __init__(
        self,
        model: str = "anthropic/claude-haiku-4-5",
        max_retries: int = 2,
        cache: ExtractionCache | None = None,
    ) -> None:
        self._model = model
        self._max_retries = max_retries
        self._cache = cache
        self._cost_tracker = CostTracker()

    def extract(
        self,
        filing_text: str,
        schema: type[T],
        accession: str,
        form_type: str,
        system_prompt: str,
    ) -> T:
        # Check cache first
        schema_version = schema_hash(schema)
        if self._cache:
            cached = self._cache.get(accession, form_type, schema_version)
            if cached is not None:
                return schema.model_validate_json(cached)

        # Create instructor client
        client = instructor.from_provider(self._model)

        result = cast(
            T,
            client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": filing_text},
                ],
                response_model=schema,
                max_tokens=8192,
                max_retries=self._max_retries,
            ),
        )

        # Cache result
        if self._cache:
            self._cache.set(
                accession, form_type, schema_version,
                result.model_dump_json(),
            )

        return result
```

### Pattern 2: Schema Versioning via JSON Schema Hash

**What:** Use `hashlib.sha256` on the canonical JSON schema of the Pydantic model to create a deterministic version string.
**When to use:** Cache key generation. When schema changes, hash changes, cache automatically invalidates.
**Example:**

```python
import hashlib
import json
from pydantic import BaseModel

def schema_hash(model: type[BaseModel]) -> str:
    """Generate a deterministic hash of a Pydantic model's JSON schema."""
    schema = model.model_json_schema()
    # Sort keys for deterministic serialization
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]
```

### Pattern 3: Boilerplate Stripping

**What:** Remove low-value content from oversized filings to fit within context limits.
**When to use:** When pre-flight token count exceeds 190,000 (leaving ~10k buffer for system prompt + schema + output).
**Example:**

```python
import re

def strip_boilerplate(text: str) -> str:
    """Remove SEC filing boilerplate that adds no extraction value."""
    # 1. Remove inline XBRL tags (ix:nonfraction, ix:nonnumeric, etc.)
    text = re.sub(r"<ix:[^>]+>", "", text)
    text = re.sub(r"</ix:[^>]+>", "", text)

    # 2. Remove exhibit index section
    text = re.sub(
        r"(?i)EXHIBIT\s+INDEX.*?(?=SIGNATURES|$)",
        "[EXHIBIT INDEX REMOVED]\n",
        text,
        flags=re.DOTALL,
    )

    # 3. Remove signature pages
    text = re.sub(
        r"(?i)SIGNATURES\s+Pursuant\s+to.*$",
        "[SIGNATURES REMOVED]",
        text,
        flags=re.DOTALL,
    )

    # 4. Remove SEC filing headers (CONFORMED SUBMISSION TYPE, etc.)
    text = re.sub(
        r"(?i)<SEC-HEADER>.*?</SEC-HEADER>",
        "",
        text,
        flags=re.DOTALL,
    )

    # 5. Remove officer certifications (Exhibits 31/32)
    text = re.sub(
        r"(?i)CERTIFICATION\s+PURSUANT\s+TO.*?(?=\n(?:EXHIBIT|ITEM|\Z))",
        "[CERTIFICATION REMOVED]\n",
        text,
        flags=re.DOTALL,
    )

    # 6. Normalize excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {3,}", " ", text)

    return text.strip()
```

### Pattern 4: Pre-flight Token Counting

**What:** Use the Anthropic SDK's `messages.count_tokens()` to verify a document fits before extraction.
**When to use:** Before every extraction call, especially for 10-K filings.
**Example:**

```python
import anthropic

def count_filing_tokens(
    text: str,
    system_prompt: str,
    model: str = "claude-haiku-4-5",
) -> int:
    """Count tokens for a filing extraction request."""
    client = anthropic.Anthropic()
    response = client.messages.count_tokens(
        model=model,
        system=system_prompt,
        messages=[{"role": "user", "content": text}],
    )
    return response.input_tokens
```

**Note:** Token counting is free but rate-limited (100-8000 RPM depending on tier). It adds a small latency per filing. For cost optimization, consider estimating tokens first (1 token ~= 4 chars) and only using the API for borderline cases.

### Pattern 5: Source Attribution in Schemas

**What:** Include a `source_passage` field alongside each extracted data point so the LLM cites where it found the data.
**When to use:** All extraction schemas.
**Example:**

```python
class ExtractedItem(BaseModel):
    """A single extracted data point with source attribution."""
    value: str | float | None = Field(description="The extracted value")
    source_passage: str = Field(
        description=(
            "The exact quote or passage from the filing where this "
            "value was found. Maximum 200 characters."
        )
    )
    confidence: str = Field(
        default="HIGH",
        description="HIGH if explicitly stated, MEDIUM if inferred, LOW if uncertain",
    )
```

### Pattern 6: Dual Extraction Path (LLM Primary, Regex Fallback)

**What:** Try LLM extraction first. If API call fails (network, rate limit, auth error), fall back to existing regex extractors.
**When to use:** In the ExtractStage orchestrator.
**Example:**

```python
def extract_with_fallback(
    filing_text: str,
    accession: str,
    form_type: str,
    llm_extractor: LLMExtractor | None,
) -> ExtractedData:
    """Try LLM extraction, fall back to regex on failure."""
    if llm_extractor is not None:
        try:
            return llm_extractor.extract(
                filing_text, TenKExtraction,
                accession, form_type, TEN_K_SYSTEM_PROMPT,
            )
        except Exception:
            logger.warning(
                "LLM extraction failed for %s, falling back to regex",
                accession,
            )
    # Existing regex extraction path
    return regex_extract(filing_text)
```

### Anti-Patterns to Avoid

- **Splitting filings into sections before LLM extraction:** The CONTEXT.md explicitly locks "complete document extraction." Send the whole document. Do NOT expand `filing_sections.py` for this purpose.
- **Multiple API calls per filing:** One call per document, not per section. The schema is comprehensive enough to extract everything in one pass.
- **Hardcoding model IDs:** Use a configurable model string, defaulting to `"anthropic/claude-haiku-4-5"`. This allows easy switching to Sonnet if needed.
- **Skipping cache lookup:** Every extraction MUST check cache first. Re-extraction of the same filing is pure waste.
- **Ignoring token limits:** Always pre-check token count. A 10-K that exceeds 200k tokens after boilerplate stripping should be logged as a warning, not crash the pipeline.
- **Mixing extraction with state mutation:** The `LLMExtractor` returns Pydantic models. The caller (ExtractStage) maps them into `AnalysisState`. Clean separation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema validation | Custom JSON validator | instructor + Pydantic `response_model` | Handles retries, type coercion, nested models automatically |
| Token counting | Character-based estimation | `anthropic.messages.count_tokens()` | Exact count including tool schema overhead, free API |
| Retry logic | Custom retry loops | instructor `max_retries` + tenacity | Automatic validation error feedback to LLM, exponential backoff |
| JSON schema generation | Manual schema dict | `model.model_json_schema()` | Pydantic generates it, instructor converts to tool schema |
| Schema versioning | Manual semver tracking | `hashlib.sha256(model_json_schema())` | Automatic, deterministic, no human maintenance |
| Cost calculation | Custom arithmetic | Token counts from API response `usage` | Anthropic returns exact input/output tokens in response |

**Key insight:** The instructor library + Pydantic v2 combination handles the entire extraction pipeline mechanics. The engineering effort should go into schema design (what to extract) and prompt engineering (how to instruct Claude), not plumbing.

## Common Pitfalls

### Pitfall 1: Schema Too Complex for Constrained Decoding

**What goes wrong:** A Pydantic model with recursive schemas, deeply nested structures, or many `anyOf` unions causes Anthropic's structured output engine to reject the schema with "Schema is too complex" or "Too many recursive definitions."
**Why it happens:** Structured outputs use compiled grammar artifacts. Complex schemas create exponential grammar expansion.
**How to avoid:**
- Keep schemas flat: 2-3 levels of nesting maximum.
- No recursive models (e.g., a `Section` that contains `list[Section]`).
- Use `list[SpecificSubModel]` not `list[dict[str, Any]]`.
- If a schema is rejected, break it into two sequential extractions (not preferred, but fallback).
**Warning signs:** 400 errors from the API mentioning schema complexity.

### Pitfall 2: Output Token Limit Truncation

**What goes wrong:** A comprehensive extraction schema with 50+ fields and source attributions generates more than 8192 output tokens, causing truncation (`stop_reason: "max_tokens"`).
**Why it happens:** Haiku 4.5 supports up to 64k output tokens, but `max_tokens` must be set explicitly. The instructor default may be lower.
**How to avoid:**
- Set `max_tokens=16384` for 10-K extractions (large schemas).
- Set `max_tokens=8192` for smaller filing types (8-K, Form 4).
- Check `stop_reason` in the response. If `"max_tokens"`, retry with higher limit.
- Consider the cost: output tokens are 5x input tokens ($5/MTok vs $1/MTok).
**Warning signs:** Incomplete extraction results, missing fields in the response.

### Pitfall 3: instructor Import Guarding

**What goes wrong:** Importing `instructor` at module level crashes the entire application if the package isn't installed (it's an optional dependency).
**Why it happens:** Not all users need LLM extraction. Some may only use regex mode.
**How to avoid:** Use the pattern from `pricing_ingestion.py`:
```python
try:
    import instructor as instructor
except ImportError:
    instructor = None  # type: ignore[assignment]
```
Check at runtime before use. Same pattern for `anthropic`.
**Warning signs:** `ImportError` on startup when `anthropic` or `instructor` not installed.

### Pitfall 4: Pyright Strict Mode Issues

**What goes wrong:** `instructor.from_provider()` returns a complex overloaded type that pyright resolves to `Coroutine` or `Unknown`.
**Why it happens:** instructor's type stubs may not cover all overloads cleanly.
**How to avoid:** Use `cast()` on the result, exactly as in `pricing_ingestion.py`:
```python
result = cast(
    TenKExtraction,
    client.chat.completions.create(
        messages=[...],
        response_model=TenKExtraction,
        max_tokens=16384,
    ),
)
```
Also: `import instructor as instructor` (the `as instructor` helps pyright in some cases).
**Warning signs:** pyright errors about `Unknown` type on extraction results.

### Pitfall 5: Oversized Filings Silently Failing

**What goes wrong:** A 10-K with exhibits, XBRL, and extensive footnotes exceeds 200k tokens. The API returns an error or truncates input.
**Why it happens:** Some companies (e.g., large banks, conglomerates) have 10-Ks exceeding 300 pages.
**How to avoid:**
1. Always run `strip_boilerplate()` first.
2. Pre-count tokens with `messages.count_tokens()`.
3. If still over limit after stripping, log a warning and fall back to regex extraction.
4. Do NOT try to split the document and make multiple calls (per CONTEXT.md decision).
**Warning signs:** API 400/413 errors, unusually long extraction times.

### Pitfall 6: Cache Key Collisions

**What goes wrong:** Two different schema versions produce the same cache key, returning stale extraction results.
**Why it happens:** Using only accession number without schema version in the key.
**How to avoid:** Cache key MUST be `(accession_number, form_type, schema_version_hash)`. The schema hash changes whenever any field is added, removed, or renamed.
**Warning signs:** Extraction results that don't match the current schema structure.

### Pitfall 7: Cost Budget Exceeded

**What goes wrong:** Processing a company with many filings (20+ across all types) blows past the $1.00 budget.
**Why it happens:** Each 10-K costs ~$0.07-0.15 at Haiku rates. 20 filings could cost $1.40-3.00.
**How to avoid:**
- Track cumulative cost per company via CostTracker.
- Prioritize filing types: 10-K > DEF 14A > 10-Q > 8-K > others.
- When approaching budget, skip lower-priority filings and fall back to regex.
- Budget check before each extraction call, not after.
**Warning signs:** Cost tracking showing >$0.80 with filings remaining.

## Code Examples

### Complete LLM Extraction Flow

```python
# Source: Adapted from pricing_ingestion.py + Anthropic docs + instructor docs

import os
import logging
from typing import cast

from pydantic import BaseModel, Field

try:
    import anthropic
    import instructor as instructor
except ImportError:
    anthropic = None  # type: ignore[assignment]
    instructor = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class RiskFactor(BaseModel):
    """A single risk factor extracted from 10-K Item 1A."""
    title: str = Field(description="Risk factor heading/title")
    category: str = Field(
        description="Category: LITIGATION, REGULATORY, FINANCIAL, OPERATIONAL, CYBER, OTHER"
    )
    severity: str = Field(description="HIGH, MEDIUM, or LOW")
    source_passage: str = Field(
        description="Exact quote from filing (max 200 chars)"
    )


class TenKExtraction(BaseModel):
    """Complete extraction from a 10-K annual report."""

    # Business description (Item 1)
    business_description: str | None = Field(
        default=None,
        description="1-2 sentence summary of the company's business"
    )
    revenue_segments: list[str] = Field(
        default_factory=lambda: [],
        description="Major revenue segments or product lines"
    )
    employee_count: int | None = Field(
        default=None,
        description="Total number of employees"
    )

    # Risk factors (Item 1A)
    risk_factors: list[RiskFactor] = Field(
        default_factory=lambda: [],
        description="Key risk factors, max 20 most significant"
    )

    # Legal proceedings (Item 3)
    legal_proceedings: list[str] = Field(
        default_factory=lambda: [],
        description="Active legal proceedings described in Item 3"
    )

    # MD&A highlights (Item 7)
    revenue_trend: str | None = Field(
        default=None,
        description="Revenue trend description (growing/declining/stable)"
    )
    key_financial_concerns: list[str] = Field(
        default_factory=lambda: [],
        description="Financial concerns highlighted in MD&A"
    )

    # Controls (Item 9A)
    material_weaknesses: list[str] = Field(
        default_factory=lambda: [],
        description="Material weaknesses in internal controls"
    )
    going_concern: bool = Field(
        default=False,
        description="Whether going concern doubt is mentioned"
    )


def extract_10k(filing_text: str, accession: str) -> TenKExtraction | None:
    """Extract structured data from a complete 10-K filing."""
    if instructor is None or anthropic is None:
        logger.warning("instructor/anthropic not installed; skipping LLM extraction")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set; skipping LLM extraction")
        return None

    system_prompt = (
        "You are a D&O liability underwriting analyst extracting structured data "
        "from SEC 10-K annual reports. Extract all requested fields accurately. "
        "For each field, only extract what is explicitly stated in the filing. "
        "If a field is not found in the document, leave it as null or empty list. "
        "Never fabricate or infer data that is not in the source document."
    )

    client = instructor.from_provider("anthropic/claude-haiku-4-5")
    result = cast(
        TenKExtraction,
        client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": filing_text},
            ],
            response_model=TenKExtraction,
            max_tokens=16384,
            max_retries=2,
        ),
    )
    return result
```

### Extraction Cache Table

```python
# Source: Modeled on existing AnalysisCache in sqlite_cache.py

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class ExtractionCache:
    """SQLite-backed cache for LLM extraction results."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._initialize()

    def _initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS extraction_cache (
                accession_number TEXT NOT NULL,
                form_type TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                extracted_json TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd REAL NOT NULL DEFAULT 0.0,
                model_id TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                PRIMARY KEY (accession_number, form_type, schema_version)
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_extraction_form
            ON extraction_cache (form_type)
        """)
        self._conn.commit()

    def get(
        self, accession: str, form_type: str, schema_version: str
    ) -> str | None:
        """Get cached extraction result, or None if not cached."""
        if self._conn is None:
            return None
        cursor = self._conn.execute(
            "SELECT extracted_json FROM extraction_cache "
            "WHERE accession_number = ? AND form_type = ? AND schema_version = ?",
            (accession, form_type, schema_version),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def set(
        self,
        accession: str,
        form_type: str,
        schema_version: str,
        extracted_json: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        model_id: str = "",
    ) -> None:
        """Store extraction result in cache."""
        if self._conn is None:
            return
        self._conn.execute(
            "INSERT OR REPLACE INTO extraction_cache VALUES (?,?,?,?,?,?,?,?,?)",
            (accession, form_type, schema_version, extracted_json,
             input_tokens, output_tokens, cost_usd, model_id, time.time()),
        )
        self._conn.commit()

    def get_company_cost(self, accessions: list[str]) -> float:
        """Get total extraction cost for a set of accession numbers."""
        if self._conn is None or not accessions:
            return 0.0
        placeholders = ",".join("?" * len(accessions))
        cursor = self._conn.execute(
            f"SELECT SUM(estimated_cost_usd) FROM extraction_cache "  # noqa: S608
            f"WHERE accession_number IN ({placeholders})",
            accessions,
        )
        row = cursor.fetchone()
        return float(row[0]) if row and row[0] else 0.0
```

### Token Counting + Cost Estimation

```python
# Source: Anthropic docs (https://platform.claude.com/docs/en/build-with-claude/token-counting)

# Haiku 4.5 pricing (as of Feb 2026)
HAIKU_INPUT_COST_PER_TOKEN = 1.0 / 1_000_000   # $1.00 per MTok
HAIKU_OUTPUT_COST_PER_TOKEN = 5.0 / 1_000_000   # $5.00 per MTok


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a Haiku 4.5 extraction."""
    return (
        input_tokens * HAIKU_INPUT_COST_PER_TOKEN
        + output_tokens * HAIKU_OUTPUT_COST_PER_TOKEN
    )


# Example cost calculations:
# 10-K (80k tokens input, 4k output) = $0.08 + $0.02 = $0.10
# DEF 14A (40k tokens input, 3k output) = $0.04 + $0.015 = $0.055
# 8-K (5k tokens input, 1k output) = $0.005 + $0.005 = $0.01
# Form 4 (2k tokens input, 0.5k output) = $0.002 + $0.0025 = $0.0045
# Total for typical company (~15 filings) = ~$0.50-$0.80
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Regex section parsing | LLM whole-document extraction | Phase 18 (now) | Eliminates fragile regex, handles arbitrary filing formats |
| instructor `from_provider` with `chat.completions.create` | Same, but Anthropic also offers `messages.parse()` with native structured outputs | Nov 2025 (structured outputs GA) | Could potentially bypass instructor, but instructor provides retry logic and is proven in codebase |
| Separate token counting libraries | `anthropic.messages.count_tokens()` official endpoint | 2025 | Free, exact, includes tool schema overhead |
| No caching of LLM results | Schema-versioned cache with cost tracking | Phase 18 (now) | Prevents costly re-extraction, enables cost monitoring |

**Deprecated/outdated:**
- `output_format` parameter: Deprecated in favor of `output_config.format`. Still works temporarily.
- The old beta header `structured-outputs-2025-11-13` is no longer needed for structured outputs.

## Codebase Integration Points

### Filing Documents Available in State

The `AcquiredData.filing_documents` field (from Phase 17) provides full filing text:
```python
# state.acquired_data.filing_documents structure:
# Dict[str, List[Dict[str, str]]]
# Key: form_type (e.g., "10-K", "DEF 14A")
# Value: List of FilingDocument dicts, each with:
#   - accession: str (accession number)
#   - filing_date: str (ISO date)
#   - form_type: str
#   - full_text: str (complete filing plain text, HTML already stripped)
```

HTML is already stripped by `filing_fetcher.py:strip_html()`. The LLM extractor receives clean text.

### Existing Extractor Integration

The `ExtractStage` orchestrator in `stages/extract/__init__.py` calls extractors in dependency order. LLM extraction should be integrated as a pre-step before the existing regex extractors, providing data that regex extractors can supplement or validate.

### Filing Types Acquired

From `sec_client.py`, domestic filings: `10-K, 10-Q, DEF 14A, 8-K, 4, S-3, S-1, 424B, SC 13D, SC 13G`. FPI filings: `20-F, 6-K, DEF 14A, 4`. Each type needs a Pydantic extraction schema.

### Priority Order for Schema Implementation

Based on D&O underwriting value:
1. **10-K** (highest value: business, risk factors, legal, financials, controls)
2. **DEF 14A** (governance, compensation, ownership)
3. **10-Q** (quarterly financials, recent developments)
4. **8-K** (material events, leadership changes)
5. **Form 4** (insider transactions, already XML-parsed)
6. **SC 13D/13G** (activist/institutional ownership)
7. **S-3/S-1/424B** (capital raises, dilution)
8. **20-F/6-K** (FPI equivalents of 10-K/10-Q)

## Open Questions

### 1. instructor vs Native Anthropic Structured Outputs

**What we know:** Anthropic now has GA structured outputs via `output_config.format` and `messages.parse()` in the Python SDK. This provides constrained decoding (grammar-level guarantees), which is stronger than instructor's tool_use approach (which relies on LLM compliance + validation retries).

**What's unclear:** Whether instructor v1.14.5 uses Anthropic's structured outputs internally, or still uses the older tool_use approach. If instructor doesn't leverage constrained decoding, native structured outputs might produce more reliable results.

**Recommendation:** Start with instructor (proven pattern in codebase). If extraction quality issues arise, evaluate switching to native `client.messages.parse()`. The migration path is straightforward since both use Pydantic models.

### 2. Exact Token Overhead of Tool Schemas

**What we know:** Tool use adds 313-346 tokens of system prompt overhead. The extraction schema itself (as a JSON schema in the tool definition) also consumes input tokens. For a 50-field schema with descriptions, this could be 500-1000 additional tokens.

**What's unclear:** The exact token cost of a large extraction schema (e.g., TenKExtraction with 50+ fields and nested models). This affects the effective context available for the filing text.

**Recommendation:** Use `messages.count_tokens()` with the actual tool definition to measure exact overhead during development. Budget 2000-3000 tokens for schema overhead in capacity planning.

### 3. Source Attribution Quality with Haiku

**What we know:** The prompt can ask Haiku to include `source_passage` fields. Claude models generally comply with citation requests.

**What's unclear:** Whether Haiku 4.5 produces accurate, useful source citations for 50+ fields from a 100k token document. The citations might be approximate or hallucinated.

**Recommendation:** Include `source_passage` fields in schemas but treat them as MEDIUM confidence. Do not rely on them for anti-imputation validation. Cross-validate critical extractions against regex results.

### 4. Form 4 XML vs Text Extraction

**What we know:** Form 4 filings are XML documents (`filing_fetcher.py` preserves XML for Form 4). The existing `insider_trading.py` extractor parses this XML.

**What's unclear:** Whether sending raw XML to an LLM for extraction is better or worse than the existing XML parser.

**Recommendation:** Keep the existing XML parser for Form 4. LLM extraction adds cost without clear benefit for structured XML data. Skip Form 4 in Phase 18 or make it very low priority.

## Sources

### Primary (HIGH confidence)
- [Anthropic Pricing Docs](https://platform.claude.com/docs/en/about-claude/pricing) - Haiku 4.5: $1/$5 per MTok, 200k context, 64k max output
- [Anthropic Token Counting Docs](https://platform.claude.com/docs/en/build-with-claude/token-counting) - Free `messages.count_tokens()` API, rate limits by tier
- [Anthropic Structured Outputs Docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) - Schema constraints, supported/unsupported features, error handling
- [Instructor Anthropic Integration](https://python.useinstructor.com/integrations/anthropic/) - `from_provider`, `response_model`, async support
- [Instructor Retry Docs](https://python.useinstructor.com/concepts/retrying/) - `max_retries`, tenacity integration, validation error feedback
- [Instructor Patching Docs](https://python.useinstructor.com/concepts/patching/) - Mode.TOOLS, schema generation, `from_provider` internals
- Existing codebase: `pricing_ingestion.py` (proven instructor + Anthropic pattern)
- Existing codebase: `sqlite_cache.py` (cache table pattern)
- Existing codebase: `filing_fetcher.py` (FilingDocument structure, HTML stripping)
- Existing codebase: `sec_client.py` (filing types, lookback counts, cache TTLs)
- Existing codebase: `stages/extract/__init__.py` (ExtractStage orchestrator)

### Secondary (MEDIUM confidence)
- [instructor PyPI](https://pypi.org/project/instructor/) - v1.14.5 (2026-01-29), Python >=3.9
- [anthropic PyPI](https://pypi.org/project/anthropic/) - v0.79.0 (2026-02-07), Python >=3.9
- [LlamaIndex 10-K Token Analysis](https://www.llamaindex.ai/blog/testing-anthropic-claudes-100k-token-window-on-sec-10-k-filings-473310c20dba) - Apple 10-K ~70k tokens (80 pages)

### Tertiary (LOW confidence)
- Web search results on SEC boilerplate patterns - Regex patterns for exhibit index, signatures, XBRL tags need validation against real filings
- Web search results on schema complexity limits - "Schema is too complex" error exists but exact thresholds unknown

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - instructor and anthropic SDK are verified, pricing confirmed from official docs, existing codebase pattern proven
- Architecture: HIGH - Modeled directly on existing `pricing_ingestion.py` pattern and `sqlite_cache.py` pattern in the codebase
- Schema design: MEDIUM - Schema complexity limits need empirical validation with real extraction schemas
- Boilerplate stripping: MEDIUM - Regex patterns based on known SEC filing structure, but need testing against real filings
- Cost estimates: HIGH - Based on official Anthropic pricing, validated with concrete token count examples
- Pitfalls: HIGH - Based on official documentation constraints (no recursive schemas, schema complexity limits)

**Research date:** 2026-02-10
**Valid until:** 2026-03-10 (stable -- instructor and Anthropic SDK are mature)
