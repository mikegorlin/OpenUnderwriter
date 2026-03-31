# Technology Stack: v12.0 Output Quality & Architectural Integrity

**Project:** D&O Underwriting Worksheet System
**Researched:** 2026-03-27
**Scope:** Stack additions for typed output contracts, canonical metrics, output sanitization, cross-section consistency, template type validation

## Recommendation: Zero New Dependencies

The existing stack already contains everything needed. The v12.0 features are **architectural patterns**, not library problems. Adding dependencies would increase surface area for no gain.

| Capability | Existing Tool | Why Sufficient |
|---|---|---|
| Typed output contracts | **Pydantic v2 (2.12.5)** `BaseModel` + `model_dump()` | Context builders already return `dict[str, Any]`; switching return type to `SectionContext.model_dump()` is a refactor, not a dependency |
| Template variable extraction | **Jinja2 (3.1.6)** `jinja2.meta.find_undeclared_variables()` | Built-in AST introspection; returns set of all variables a template expects from context |
| Output sanitization | **re (stdlib)** + existing `formatters_humanize.py` | `clean_narrative_text()`, `_strip_markdown()`, `_sanitize_narrative()` already exist; consolidation into single pass is the work |
| HTML parsing for QA | **BeautifulSoup4 (4.14.3)** already installed | `semantic_qa.py` and `health_check.py` already use it for post-render validation |
| Cross-section consistency | **Pydantic v2 validators** + canonical registry dict | `model_validator(mode='after')` on a `WorksheetContext` model enforces same-fact consistency at build time |
| Metrics formatting | **existing `formatters.py`** + `formatters_numeric.py` | `format_currency()`, `format_percentage()`, `safe_float()` already handle all display formatting |

## Architecture for Each Capability

### 1. Typed Output Contracts (Pydantic BaseModel per section)

**What exists now:** ~90 context builders return `dict[str, Any]`. Templates access keys with no compile-time or runtime validation. Typos in template variables silently render as empty string (Jinja2 `undefined` default).

**What to build (no new deps):**

```python
# Per-section Pydantic model replaces raw dict
class FinancialSectionContext(BaseModel):
    """Typed contract for financial section template variables."""
    model_config = ConfigDict(extra="forbid")  # Catch typos at build time

    revenue: str = "N/A"
    revenue_raw: float | None = None
    net_income: str = "N/A"
    gross_margin: str = "N/A"
    # ... every variable the template uses

# Context builder returns typed model
def build_financial_context(state: AnalysisState) -> FinancialSectionContext:
    return FinancialSectionContext(
        revenue=format_currency(state.extracted.financials...),
        ...
    )

# Assembly calls .model_dump() before passing to Jinja2
context["financial"] = build_financial_context(state).model_dump()
```

**Why Pydantic BaseModel, not TypedDict:**
- `extra="forbid"` catches accidental key additions at runtime
- `model_validator` enables cross-field consistency checks
- Already the project standard (Pydantic v2 everywhere)
- `model_dump()` produces the dict Jinja2 needs
- TypedDict only helps at type-check time (Pyright), not runtime

**Confidence:** HIGH -- Pydantic v2 `model_dump()` verified working, `ConfigDict(extra="forbid")` is documented behavior.

### 2. Canonical Metrics Registry (Single-source computed values)

**What exists now:** Revenue computed in `financials.py`, `key_stats_context.py`, `company.py`, and `dossier_revenue_card.py` -- potentially different values/formatting.

**What to build (no new deps):**

```python
class CanonicalMetrics(BaseModel):
    """Single computed value per metric. Frozen after creation."""
    model_config = ConfigDict(frozen=True)

    # Identity
    ticker: str
    company_name: str
    exchange: str = "N/A"
    ceo_name: str = "N/A"

    # Scale (raw + formatted)
    revenue_raw: float | None = None
    revenue_display: str = "N/A"
    revenue_period: str = ""  # "FY2025"
    market_cap_raw: float | None = None
    market_cap_display: str = "N/A"
    employees: int | None = None
    employees_display: str = "N/A"

    # Margins
    gross_margin_pct: float | None = None
    operating_margin_pct: float | None = None
    net_margin_pct: float | None = None

    # Litigation counts
    active_sca_count: int = 0
    active_derivative_count: int = 0
    sec_enforcement_count: int = 0

    # Score
    overall_score: float | None = None
    tier: str = "N/A"

def build_canonical_metrics(state: AnalysisState) -> CanonicalMetrics:
    """Single function, single source. Called once at render start."""
    ...
```

**Key design:** `frozen=True` prevents mutation after creation. Every context builder receives `CanonicalMetrics` as input and uses its values instead of re-deriving from state. Template variables like `{{ metrics.revenue_display }}` are always consistent.

**Confidence:** HIGH -- `ConfigDict(frozen=True)` is core Pydantic v2.

### 3. Template Variable Type Validation (CI gate)

**What exists now:** No validation that template `{{ foo.bar }}` matches context builder output keys.

**What to build (no new deps):**

```python
# CI test using jinja2.meta (built into Jinja2 3.1.6)
from jinja2 import Environment, meta

def test_template_variables_match_context_schema():
    env = Environment(...)
    # Register all custom filters as stubs so meta.parse works
    for name in CUSTOM_FILTERS:
        env.filters[name] = lambda x: x

    for template_path in TEMPLATE_DIR.rglob("*.html.j2"):
        ast = env.parse(template_path.read_text())
        undeclared = meta.find_undeclared_variables(ast)
        # Check each undeclared var exists in the section's Pydantic schema
        schema_fields = get_schema_for_template(template_path)
        missing = undeclared - schema_fields - GLOBAL_CONTEXT_VARS
        assert not missing, f"{template_path.name}: {missing} not in schema"
```

**Important limitation:** `jinja2.meta.find_undeclared_variables()` returns top-level names only (`company`, `revenue`), NOT dotted paths (`company.name`). For dotted path validation, a custom AST walker on `jinja2.nodes.Getattr` is needed -- still no new deps, just ~50 lines of visitor code.

**Verified:** Tested `jinja2.meta.find_undeclared_variables()` against Jinja2 3.1.6 -- works correctly but requires all custom filters to be registered (even as stubs) before `env.parse()` or it raises `TemplateAssertionError`.

**Confidence:** HIGH -- `jinja2.meta` tested and working with Jinja2 3.1.6.

### 4. Output Sanitization Layer (Consolidation, not new code)

**What exists now (scattered across 6+ locations):**
- `formatters_humanize.py`: `clean_narrative_text()` -- strips boilerplate phrases
- `html_narrative.py`: `_strip_markdown()` -- removes markdown artifacts from HTML
- `md_renderer.py`: `_sanitize_narrative()` -- cleans LLM output for markdown
- `assembly_html_extras.py`: ad-hoc sanitization in builder
- `assembly_registry.py`: `_strip_do_context_boilerplate()` -- recursive dict walk
- `health_check.py`: post-hoc detection of leaked LLM text, zero placeholders
- `self_review.py`: boilerplate pattern detection (60+ regex patterns)

**What to build (no new deps):**

```python
class OutputSanitizer:
    """Single-pass HTML sanitization. Runs on complete HTML before write."""

    def sanitize(self, html: str) -> SanitizationReport:
        """Strip markdown artifacts, debug strings, raw serialization,
        system jargon. Return cleaned HTML + report of changes."""
        ...
```

Consolidate the ~6 scattered sanitization functions into one module with one entry point. Use existing `re` (stdlib) and `BeautifulSoup4` (already installed). No new library needed.

**Why NOT nh3:** nh3 is for security sanitization (XSS prevention via allowlisting HTML tags/attributes). This system needs content sanitization (removing markdown `**bold**` artifacts, `[source](url)` links, debug strings like `signal_name=...`). Different problem entirely. nh3 would strip legitimate HTML structure that the templates intentionally produce.

**Confidence:** HIGH -- all building blocks already exist in codebase.

### 5. Cross-Section Consistency Checker

**What exists now:** `semantic_qa.py` validates a few values (revenue, board size, score) by parsing rendered HTML back and comparing to state. Manual, fragile, post-hoc.

**What to build (no new deps):**

```python
class ConsistencyReport(BaseModel):
    """Report of cross-section fact discrepancies."""
    discrepancies: list[Discrepancy] = []

class Discrepancy(BaseModel):
    fact: str            # "revenue"
    sections: list[str]  # where it appeared
    values: list[str]    # what values were found
    canonical: str       # what it should be

def check_cross_section_consistency(
    context: dict[str, Any],
    metrics: CanonicalMetrics,
) -> ConsistencyReport:
    """Pre-render check: walk context dict, find all instances of
    canonical facts, verify they match CanonicalMetrics values."""
    ...
```

**Key insight:** Do this PRE-render (on the context dict), not POST-render (on HTML). Prevents the problem instead of detecting it. The `CanonicalMetrics` frozen model is the single source; context builders that deviate are the bug.

**Confidence:** HIGH -- pure application logic, no library dependency.

## What NOT to Add

| Library | Why NOT |
|---|---|
| **typed-prompt** | Designed for LLM prompt templates, not HTML rendering. Wrong abstraction. |
| **typedtemplate** | Thin wrapper; Pydantic `model_dump()` is simpler and already in the stack. |
| **pyjinhx** | HTMX-focused; irrelevant for document generation. |
| **nh3** | Security sanitizer (XSS). This system needs content sanitization (markdown artifacts, debug strings). Wrong tool. |
| **marshmallow** | Pydantic v2 is already the project standard. Adding a second serialization library is complexity for no benefit. |
| **cattrs/attrs** | Same -- Pydantic v2 handles everything needed. |
| **jinja2-stubs** | Pyright strict mode already enabled. The real gap is runtime validation of template variables against context schemas, not static typing of Jinja2 API calls. |

## Existing Dependencies to Leverage More

| Already Installed | Current Version | New Use |
|---|---|---|
| **Pydantic v2** | 2.12.5 | `BaseModel` for section contexts, `ConfigDict(extra="forbid", frozen=True)`, `model_validator` for cross-field checks |
| **Jinja2** | 3.1.6 | `jinja2.meta.find_undeclared_variables()` for CI template validation, `jinja2.nodes.Getattr` AST walking for dotted-path validation |
| **BeautifulSoup4** | 4.14.3 | Consolidate into single `OutputSanitizer` class using existing BS4 parsing |
| **re (stdlib)** | -- | Consolidate scattered regex patterns into single sanitization registry |
| **pytest** | 9.0.2 | New CI test: `test_template_contract.py` validates template vars against Pydantic schemas |

## Migration Strategy

The typed output contract is a **per-context-builder migration**, not a big bang:

1. **Phase 1:** Create `CanonicalMetrics` model + `build_canonical_metrics()`. Thread through assembly. All builders read from it instead of re-deriving values.
2. **Phase 2:** Create Pydantic `SectionContext` models for highest-risk sections first (financials, key stats, scoring -- where contradictions actually happen).
3. **Phase 3:** CI gate -- `test_template_contract.py` using `jinja2.meta` validates every template's variables exist in its section schema.
4. **Phase 4:** Consolidate sanitization into `OutputSanitizer`. Single pass on complete HTML.
5. **Phase 5:** Cross-section consistency checker runs pre-render, fails pipeline on discrepancy.

Each phase is independently valuable. No phase requires the others to ship.

## Integration Points with Existing Code

| Existing Module | Integration |
|---|---|
| `context_builders/assembly_registry.py` | `build_html_context()` calls `build_canonical_metrics()` first, passes to all builders |
| `context_builders/*.py` (90 files) | Incrementally migrate from `-> dict[str, Any]` to `-> SectionContext` |
| `state_paths.py` | Continue using for state reads; `CanonicalMetrics` builder calls state_paths functions |
| `html_renderer.py` | Add `OutputSanitizer.sanitize()` call before `write()` |
| `semantic_qa.py` | Replace post-hoc HTML parsing with pre-render `ConsistencyReport` |
| `health_check.py` | Merge LLM leak detection into `OutputSanitizer` |
| `self_review.py` | Merge boilerplate patterns into `OutputSanitizer` |

## Sources

- Jinja2 API docs (meta module): https://jinja.palletsprojects.com/en/stable/api/
- Pydantic v2 model configuration: https://docs.pydantic.dev/latest/concepts/config/
- nh3 PyPI (evaluated and rejected): https://pypi.org/project/nh3/
- Jinja2 undeclared variables: https://dnmtechs.com/retrieving-all-variables-in-jinja-2-templates-in-python-3/
- Pydantic frozen models: https://docs.pydantic.dev/latest/concepts/models/
- typed-prompt (evaluated and rejected): https://pypi.org/project/typed-prompt/
- typedtemplate (evaluated and rejected): https://github.com/Shakakai/typedtemplate
