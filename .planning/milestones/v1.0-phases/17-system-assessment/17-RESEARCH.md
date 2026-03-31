# Phase 17 Research: LLM Extraction Architecture

## Key Architecture Decisions (from research)

### 1. Use Anthropic Native Structured Outputs (NOT Instructor)

Anthropic released **Structured Outputs** as GA for Haiku 4.5. This uses constrained decoding — the API compiles your JSON schema into a grammar and restricts token generation. The model literally cannot produce tokens that violate the schema.

```python
from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-haiku-4-5-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": f"Extract from: {text}"}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": transform_schema(MyPydanticModel),
        }
    }
)
```

**Why NOT Instructor**: Unnecessary dependency now that Anthropic has native schema-guaranteed output. Instructor's main value-add was validation retry loops, but constrained decoding makes format violations impossible.

**Critical caveat**: Structured outputs guarantee FORMAT, not ACCURACY. We still need cross-validation.

### 2. Haiku 4.5 for Extraction (NOT Sonnet/Opus)

- Haiku: $1/MTok input, $5/MTok output
- Sonnet: $3/MTok input, $15/MTok output (3x more expensive)
- Haiku is purpose-built for "extracting structured information" per Anthropic docs
- If a prompt works in Claude Code (Opus), it will generally work in Haiku with slightly more explicit instructions

### 3. Cost Per Company: ~$0.12 (Well Under $0.50 Target)

| Component | Input Tokens | Output Tokens | Cost |
|-----------|-------------|---------------|------|
| 10-K extraction (5 sections) | ~30K | ~5K | $0.055 |
| DEF 14A extraction | ~15K | ~3K | $0.030 |
| 8-K extraction (5-10 filings) | ~15K | ~3K | $0.030 |
| System prompts + schemas | ~5K | -- | $0.005 |
| **Total** | **~65K** | **~11K** | **~$0.12** |

With prompt caching: ~$0.07-0.08/company
With Batch API (50% discount): ~$0.06/company
5,000 companies at batch + caching: ~$300-400 total

### 4. Section-Targeted Extraction (NOT Full-Filing)

Extract per-section, not per-filing. Benefits:
- Targeted Pydantic schemas per section type
- Smaller input = cheaper + more accurate
- Source attribution maps directly to filing section
- Most 10-K sections fit easily in Haiku's 200K context

### 5. Source Attribution Pattern (from Google's LangExtract)

Every extracted field must include `source_passage: str` — the exact quote from the filing. This enables:
- Human verification in under 30 seconds
- Cross-validation against XBRL
- Audit trail for regulators

### 6. Two-Layer Caching

1. **Filing-level** (DuckDB): Key = `(cik, accession_number, section_id, schema_version)`. Never re-extract same filing.
2. **Prompt cache** (Anthropic): Cache filing text in system prompt, vary extraction instructions per section. Cache reads = 10% of input cost.

### 7. Validation Strategy

| Condition | Confidence |
|-----------|-----------|
| LLM matches XBRL value | HIGH |
| LLM from audited filing, no contradiction | HIGH |
| LLM matches 2+ other sources | MEDIUM |
| LLM single source, no validation | MEDIUM |
| LLM with low self-consistency | LOW |

### 8. What NOT to Do

- Do NOT send full filings to LLM (pre-parse into sections)
- Do NOT use Sonnet/Opus for extraction (Haiku sufficient, 3x cheaper)
- Do NOT build RAG (we have full text, not retrieval problem)
- Do NOT replace XBRL with LLM (XBRL is already perfect for financials)
- Do NOT use extended thinking for extraction (pattern-matching, not reasoning)

### 9. Claude Code Development Workflow

1. Read real filing section in Claude Code
2. Draft extraction prompt with Pydantic schema
3. Test extraction in Claude Code (simulates API, zero cost)
4. Iterate until accurate across 3-5 sample filings
5. Codify into pipeline for Haiku execution

### 10. Dependencies

```
anthropic >= 0.40.0     # Native structured outputs
sec-parser >= 0.58      # SEC filing section parsing (optional upgrade)
# No other new dependencies needed
```

## Batch API for Bulk Runs

50% discount, processes within 24 hours. Up to 100K requests per batch. Ideal for:
- Portfolio-level analysis (5,000 companies)
- Re-extraction when schemas change
- Evaluation runs

Batch + prompt caching discounts stack — up to 95% cost reduction.
