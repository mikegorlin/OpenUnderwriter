# Phase 137: Canonical Metrics Registry - Research

**Researched:** 2026-03-27
**Domain:** Metric deduplication, source priority resolution, Pydantic compute-once patterns
**Confidence:** HIGH

## Summary

Phase 137 addresses a verified, pervasive problem: the same core metrics (revenue, market cap, employees, exchange, CEO name, stock price, net income, growth rates) are independently extracted from different state paths by multiple context builders, producing inconsistent values across worksheet sections. A direct audit of the 96 context builder files in `src/do_uw/stages/render/context_builders/` found 365 references to these metrics across 39 files. Revenue alone is extracted by at least 5 independent functions: `_extract_revenue()` in key_stats_context.py, `extract_xbrl_revenue()` in _beta_report_helpers.py, inline XBRL iteration in scorecard_context.py, `snap.revenue.value` in company_exec_summary.py, and `info.get("totalRevenue")` fallback in beta_report.py. Market cap has 6+ independent extraction paths. Each uses different source priority logic and different fallback chains, so the same company can show "$3.05B" in one section and "$2.98B" in another.

The solution is a `CanonicalMetrics` Pydantic model computed exactly once at the top of `build_html_context()` in `assembly_registry.py`. Each metric carries its raw value, pre-formatted display string, source attribution, confidence level, and as-of date. Context builders read from this registry for any metric that appears in 2+ sections. The registry uses the XBRL-first source priority chain already established in CLAUDE.md. No new dependencies are needed -- this is pure Pydantic v2 + existing formatters.

**Primary recommendation:** Create `stages/render/canonical_metrics.py` with a `CanonicalMetrics` Pydantic model and `build_canonical_metrics(state)` function. Wire it into `build_html_context()` as the first computation step. Store as `context["_canonical"]`. Then migrate the 5 highest-duplication builders (key_stats, beta_report, company_profile, scorecard, company_exec_summary) to read from the registry. Do NOT migrate all 39 files in this phase -- registry + 5 consumer migrations is the scope.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| METR-01 | CanonicalMetricsRegistry computes each metric exactly once with XBRL-first source priority | Audit confirms 5+ independent revenue extractions, 6+ market_cap extractions. Registry eliminates duplication. Source priority chain documented below. |
| METR-02 | Revenue, net income, market cap, stock price, employees, exchange, CEO name, and growth rates computed once, consumed by all sections | Specific files and functions identified for each metric. Migration path documented for top-5 consumers. |
| METR-03 | Every metric carries source, as-of date, and confidence level | `MetricValue` model designed with `source`, `as_of`, `confidence` fields matching existing `SourcedValue` pattern from `models/common.py`. |
| METR-04 | Context builders import from canonical registry instead of independently navigating state | Integration pattern: `canonical` parameter added to builder signature. Top-5 builders migrated in-phase; remainder tracked for future phases. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | >=2.10 (installed) | MetricValue and CanonicalMetrics models | Already the project's data model layer |
| formatters.py | existing | `safe_float()`, `format_currency()`, `format_percentage()` | Already used by all context builders |
| formatters_numeric.py | existing | `_compact_number()`, `format_currency_accounting()` | Extracted from formatters.py, already in use |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| state_paths.py | existing | Typed state accessors for raw data reads | Reading source data before registry transforms it |
| _key_stats_helpers.py | existing | `fmt_large_number()`, `size_tier()`, `spectrum_pct()` | Display formatting utilities |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic model | Plain dataclass | Pydantic gives validation, serialization, model_dump() -- dataclass would miss field validation |
| Pre-formatted strings | Raw values + Jinja2 filters | Pre-formatted is safer (no template-side formatting bugs) and matches existing pattern in beta_report helpers |

**Installation:** No new packages needed.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/stages/render/
  canonical_metrics.py         # NEW: MetricValue, CanonicalMetrics, build_canonical_metrics()
  context_builders/
    assembly_registry.py       # MODIFIED: call build_canonical_metrics() at top
    key_stats_context.py       # MODIFIED: read from canonical instead of _extract_revenue()
    beta_report.py             # MODIFIED: read from canonical for mc, rev, price, emp
    company_profile.py         # MODIFIED: read from canonical for exchange, emp, sic
    scorecard_context.py       # MODIFIED: read from canonical for market_cap, revenue
    company_exec_summary.py    # MODIFIED: read from canonical for exchange, market_cap, revenue
tests/
  test_canonical_metrics.py    # NEW: unit tests against real state.json
```

### Pattern 1: MetricValue with Provenance
**What:** Every canonical metric is a Pydantic model carrying value + display string + source attribution.
**When to use:** Any metric that appears in 2+ worksheet sections.
**Example:**
```python
# Source: existing SourcedValue pattern from models/common.py + new formatting layer
class MetricValue(BaseModel):
    """Single authoritative metric value with provenance."""
    model_config = ConfigDict(frozen=True)

    raw: float | int | str | None = None     # Raw numeric/string value
    formatted: str = "N/A"                    # Pre-formatted display: "$3.05B", "142,000"
    source: str = "unknown"                   # "xbrl:10-K:FY2025" | "yfinance:info" | "llm:10-K"
    confidence: str = "LOW"                   # HIGH | MEDIUM | LOW
    as_of: str = ""                           # "FY2025" | "2026-03-27" | "TTM"
```

### Pattern 2: Source Priority Chain (per metric type)
**What:** Each metric has an explicit, ordered fallback chain. First non-None source wins.
**When to use:** Every metric in the registry.
**Example:**
```python
def _resolve_revenue(state: AnalysisState) -> MetricValue:
    """Revenue: XBRL (audited) > LLM 10-K extraction > yfinance TTM."""
    # Priority 1: XBRL income statement
    xbrl_rev = _xbrl_line_item(state, "income_statement",
                                ("total_revenue", "revenue", "net_sales"))
    if xbrl_rev is not None:
        period = _xbrl_latest_period(state)
        return MetricValue(
            raw=xbrl_rev,
            formatted=fmt_large_number(xbrl_rev),
            source=f"xbrl:10-K:{period}",
            confidence="HIGH",
            as_of=period or "",
        )
    # Priority 2: yfinance totalRevenue (TTM, unaudited)
    info = _yfinance_info(state)
    yf_rev = info.get("totalRevenue") if info else None
    if yf_rev is not None:
        return MetricValue(
            raw=safe_float(yf_rev),
            formatted=fmt_large_number(safe_float(yf_rev)),
            source="yfinance:info",
            confidence="MEDIUM",
            as_of="TTM",
        )
    return MetricValue()  # All defaults (raw=None, formatted="N/A")
```

### Pattern 3: Registry as Context Builder Parameter
**What:** Pass `CanonicalMetrics` to builders that need cross-section metrics.
**When to use:** Migrating existing builders to use the registry.
**Example:**
```python
# In assembly_registry.py build_html_context():
from do_uw.stages.render.canonical_metrics import build_canonical_metrics

canonical = build_canonical_metrics(state)
context["_canonical"] = canonical.model_dump()  # for templates

# Builders receive canonical as parameter:
def build_key_stats_context(
    state: AnalysisState,
    canonical: CanonicalMetrics | None = None,
) -> dict[str, Any]:
    # If canonical available, use it; otherwise fall back to old extraction
    if canonical:
        revenue_display = canonical.revenue.formatted
    else:
        revenue_display = fmt_large_number(_extract_revenue(state.extracted))
```

### Anti-Patterns to Avoid
- **Removing old extraction code immediately:** Keep old functions during migration. Builders that haven't been migrated still need them. Delete only after all consumers are migrated.
- **Making CanonicalMetrics a required parameter:** Use `canonical: CanonicalMetrics | None = None` so unmigrated call sites don't break.
- **Computing derived metrics in the registry:** The registry holds raw facts. Derived values (EV/Revenue ratio, revenue per employee) belong in the consuming builder, not the registry.
- **Formatting in templates instead of pre-formatting:** Pre-format in the registry so templates get display-ready strings. This prevents the `safe_float()` / `format_currency()` bugs that happen at the template boundary.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Number formatting | Custom formatting in each builder | `fmt_large_number()` from `_key_stats_helpers.py` or `format_currency(compact=True)` from `formatters_numeric.py` | Already 2 implementations that differ slightly; standardize on one |
| Safe numeric conversion | Bare `float()` calls | `safe_float()` from `formatters.py` | Handles "N/A", "%", None, concatenated junk (383 existing call sites) |
| SourcedValue unwrapping | `getattr(x, "value", x)` everywhere | Centralized `_sv()` helper in canonical_metrics.py | Pattern appears 50+ times across builders |
| XBRL line item extraction | Inline iteration per builder | Extract shared `_xbrl_line_item()` into canonical_metrics.py | Already exists in 2 forms: key_stats `_extract_revenue()` and beta_report `extract_xbrl_revenue()` |

**Key insight:** The two `fmt_large_number()` functions (in `_key_stats_helpers.py` and `beta_report_infographics.py`) differ in edge cases: one returns "N/A" for None, the other returns an em dash. The registry must pick ONE and use it consistently. Recommend the em-dash variant for display, "N/A" for data cells.

## Common Pitfalls

### Pitfall 1: Breaking Existing Builder Signatures
**What goes wrong:** Adding `canonical` as a required positional parameter breaks all existing callers.
**Why it happens:** Builders are called from `md_renderer.py` (base context) AND `assembly_registry.py` (HTML extras), with different signatures.
**How to avoid:** Make `canonical` keyword-only with `None` default: `def build_key_stats_context(state: AnalysisState, *, canonical: CanonicalMetrics | None = None)`.
**Warning signs:** Import errors or TypeError at render time.

### Pitfall 2: Registry Computed Too Late in Pipeline
**What goes wrong:** If registry depends on data only available after SCORE, it can't be used by pre-SCORE builders.
**Why it happens:** Some metrics (overall_score, tier, filing_probability) come from the SCORE stage.
**How to avoid:** Split the registry into two categories: (1) data metrics (revenue, market_cap, etc.) computed from extracted data, available pre-SCORE; (2) scoring metrics added after SCORE. The registry is built at render time when all stages are complete, so this isn't actually a problem -- but document it clearly.
**Warning signs:** `None` values for scoring metrics when testing with partial state.

### Pitfall 3: Formatted Strings Don't Match Template Expectations
**What goes wrong:** Template expects `"$3.05B"` but registry produces `"$3,050,000,000"` or `"$3.1B"`.
**Why it happens:** Different formatters have different precision/style. `format_currency(compact=True)` vs `fmt_large_number()` produce different output for same input.
**How to avoid:** Audit each template's current expected format. Standardize on `fmt_large_number()` for large currency values. Write tests that compare registry output against known-good state.json rendering.
**Warning signs:** Visual regression in worksheet output.

### Pitfall 4: SourcedValue Wrapping Creates Extraction Bugs
**What goes wrong:** `state.company.market_cap` is `SourcedValue[float] | None`, but `info.get("marketCap")` is raw `float | None`. Mixing them without unwrapping causes `MetricValue(raw=SourcedValue(value=3.05e9, ...))` instead of `MetricValue(raw=3.05e9)`.
**Why it happens:** Half the state model uses `SourcedValue` wrappers, half uses raw values. yfinance acquired_data is always raw dicts.
**How to avoid:** Every resolver function in the registry MUST unwrap SourcedValue: `val = sv.value if isinstance(sv, SourcedValue) else sv`. Write a unit test that verifies `raw` is always a primitive type.
**Warning signs:** `MetricValue.raw` containing Pydantic model objects.

### Pitfall 5: Dual Formatting Functions
**What goes wrong:** `fmt_large_number()` exists in TWO files with different behavior for None/NaN. Using the wrong one causes inconsistent display.
**Why it happens:** `_key_stats_helpers.py` line 46 returns em dash for None; `beta_report_infographics.py` line 17 returns "N/A" for None.
**How to avoid:** The registry should use exactly one. Import from a single canonical location. Recommend adding a unified version to `formatters.py` or `formatters_numeric.py` (the project's designated formatting module) and having both existing locations delegate to it.

## Detailed Metric Audit: Sources of Duplication

### Revenue (5+ independent extractions)
| Location | Source Path | Priority | Returns |
|----------|-----------|----------|---------|
| `key_stats_context._extract_revenue()` | XBRL income_statement line_items | XBRL only | `float \| None` |
| `_beta_report_helpers.extract_xbrl_revenue()` | XBRL income_statement line_items | XBRL only | `float \| None` |
| `beta_report.py` line 143 | XBRL > yfinance totalRevenue | XBRL > yfinance | `float \| None` |
| `scorecard_context.py` line 812 | XBRL income_statement inline | XBRL only | formatted string |
| `company_exec_summary.py` line 234 | `snap.revenue.value` (executive_summary model) | Derived | formatted string |
| `dossier_money_flows._extract_revenue_streams()` | dossier segment data | LLM extraction | list[dict] |

### Market Cap (6+ independent extractions)
| Location | Source Path | Priority | Returns |
|----------|-----------|----------|---------|
| `key_stats_context.py` line 67 | `state.company.market_cap` (SourcedValue) | CompanyProfile | `float \| None` |
| `beta_report.py` line 150-154 | XBRL shares x price > yfinance marketCap | Computed > yfinance | `float \| None` |
| `scorecard_context.py` line 800-804 | CompanyProfile > market.stock.market_cap_yf | Profile > yfinance | `float \| None` |
| `_forward_scenarios._get_market_cap()` | market.stock > acquired_data marketCap | Extracted > yfinance | `float` |
| `company_exec_summary.py` line 233 | `snap.market_cap.value` | ExecSummary model | formatted string |
| `probability_decomposition.py` line 105-121 | scoring.metadata > market.stock | Scoring > extracted | `float \| None` |
| `dossier_money_flows.py` line 271 | `company.market_cap` | CompanyProfile | `float` |
| `_beta_report_findings.py` line 462 | yfinance info dict | yfinance only | `float` |

### Exchange (4 independent extractions)
| Location | Source Path |
|----------|-----------|
| `key_stats_context.py` line 165 | `identity.exchange` (SourcedValue) |
| `company_profile.py` line 94 | `identity.exchange` (SourcedValue, different unwrapping) |
| `beta_report_sections.py` line 2579 | `yf_info.get("exchange")` |
| `company_exec_summary.py` line 232 | `snap.exchange` |

### Employees (4+ independent extractions)
| Location | Source Path |
|----------|-----------|
| `key_stats_context.py` line 68 | `company.employee_count` (SourcedValue) |
| `company_profile.py` lines 233,300-304 | `prof.employee_count` > `stock.employee_count_yf` |
| `company_operations.py` lines 63-66 | `prof.employee_count` > workforce_distribution |
| `beta_report_sections.py` line 2165 | `info.get("fullTimeEmployees")` |
| `scorecard_context.py` line 821-825 | CompanyProfile employee_count |

### CEO Name (3 independent extractions)
| Location | Source Path |
|----------|-----------|
| `governance.py` line 107 | `ecd.get("ceo_name")` from governance extraction |
| `beta_report_sections.py` lines 1297, 2371-2383 | Scanning officers list for "CEO"/"Chief Executive" title |
| `key_stats_context.py` line 133-138 | `kpr.get("ceo_tenure_years")` (tenure, not name) |

### Stock Price (3+ independent extractions)
| Location | Source Path |
|----------|-----------|
| `key_stats_context.py` line 84 | `state.extracted.market.stock.current_price` |
| `beta_report.py` line 136 | `yf_info.get("currentPrice")` |
| `_market_display.py` / `_market_acquired_data.py` | Various yfinance info paths |

## Source Priority Chain (per CLAUDE.md)

The canonical source priority, per CLAUDE.md's "Data Source Priority -- XBRL First":

| Metric Type | Priority 1 (HIGH) | Priority 2 (MEDIUM) | Priority 3 (LOW) |
|------------|-------------------|---------------------|-------------------|
| Revenue | XBRL income_statement: total_revenue/revenue/net_sales | yfinance: info.totalRevenue | LLM 10-K extraction |
| Net Income | XBRL income_statement: net_income/net_income_loss | yfinance: info.netIncomeToCommon | -- |
| Market Cap | XBRL shares_outstanding x current_price | yfinance: info.marketCap | CompanyProfile.market_cap |
| Stock Price | extracted.market.stock.current_price | yfinance: info.currentPrice | -- |
| Employees | CompanyProfile.employee_count (10-K XBRL) | yfinance: info.fullTimeEmployees | LLM workforce extraction |
| Exchange | CompanyIdentity.exchange (SEC EDGAR) | yfinance: info.exchange | -- |
| CEO Name | governance extraction (proxy/10-K) | Officers list scan | -- |
| Growth Rates | Derived from XBRL multi-period revenue | yfinance revenue history | -- |
| Total Assets | XBRL balance_sheet | yfinance: info.totalAssets | -- |
| Total Debt | XBRL balance_sheet | yfinance: info.totalDebt | -- |

**Critical note on as-of dates:** XBRL data is fiscal-year (e.g., "FY2025"), yfinance is TTM or real-time. The registry MUST carry the period type so underwriters know if they're looking at audited annual or trailing estimates.

## Code Examples

### Complete CanonicalMetrics Model
```python
# Source: designed from audit of existing extraction patterns
from pydantic import BaseModel, ConfigDict

class MetricValue(BaseModel):
    """Single authoritative metric value with provenance."""
    model_config = ConfigDict(frozen=True)

    raw: float | int | str | None = None
    formatted: str = "N/A"
    source: str = "unknown"
    confidence: str = "LOW"
    as_of: str = ""

class CanonicalMetrics(BaseModel):
    """All canonical metrics, computed once from state at render start."""
    model_config = ConfigDict(frozen=True)

    # Identity
    company_name: MetricValue = MetricValue()
    ticker: MetricValue = MetricValue()
    exchange: MetricValue = MetricValue()
    sic_code: MetricValue = MetricValue()
    sic_description: MetricValue = MetricValue()
    ceo_name: MetricValue = MetricValue()

    # Financial (XBRL-first)
    revenue: MetricValue = MetricValue()
    revenue_growth_yoy: MetricValue = MetricValue()
    net_income: MetricValue = MetricValue()
    total_assets: MetricValue = MetricValue()
    total_liabilities: MetricValue = MetricValue()
    total_debt: MetricValue = MetricValue()
    cash_and_equivalents: MetricValue = MetricValue()
    market_cap: MetricValue = MetricValue()
    shares_outstanding: MetricValue = MetricValue()
    employees: MetricValue = MetricValue()

    # Market
    stock_price: MetricValue = MetricValue()
    high_52w: MetricValue = MetricValue()
    low_52w: MetricValue = MetricValue()
    beta: MetricValue = MetricValue()

    # Scoring (populated from state.scoring)
    overall_score: MetricValue = MetricValue()
    tier: MetricValue = MetricValue()
```

### Builder Migration Example
```python
# Source: existing key_stats_context.py pattern, modified for canonical
def build_key_stats_context(
    state: AnalysisState,
    *,
    canonical: CanonicalMetrics | None = None,
) -> dict[str, Any]:
    # Use canonical if available, else fall back to old extraction
    if canonical:
        market_cap_raw = canonical.market_cap.raw
        revenue_raw = canonical.revenue.raw
        employees_raw = canonical.employees.raw
        exchange_val = canonical.exchange.formatted
    else:
        # Legacy path (still works for md_renderer callers)
        c = state.company
        market_cap_raw = sv(c.market_cap) if c else None
        revenue_raw = _extract_revenue(state.extracted)
        employees_raw = sv(c.employee_count) if c else None
        exchange_val = sv(c.identity.exchange) if c and c.identity else "N/A"
```

### Wiring into Assembly Registry
```python
# In assembly_registry.py build_html_context():
def build_html_context(
    state: AnalysisState,
    chart_dir: Path | None = None,
) -> dict[str, Any]:
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics
    from do_uw.stages.render.md_renderer import build_template_context

    # Step 1: Compute canonical metrics ONCE
    canonical = build_canonical_metrics(state)

    # Step 2: Build base context (md_renderer path -- not yet migrated)
    context = build_template_context(state, chart_dir)

    # Step 3: Store canonical for templates and builders
    context["_canonical"] = canonical.model_dump()

    # Step 4: Run registered builders (they receive canonical via context)
    for builder in _BUILDERS:
        try:
            builder(state, context, chart_dir)
        except Exception:
            logger.warning("Assembly builder %s failed", ...)

    return context
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Each builder extracts from state independently | Registry computes once, builders consume | This phase | Eliminates cross-section contradictions |
| `SourcedValue` unwrapping scattered across builders | Centralized unwrapping in registry resolvers | This phase | Eliminates SourcedValue leak-through |
| Two `fmt_large_number()` implementations | Single canonical formatter | This phase | Consistent display format |

## Open Questions

1. **Should `build_template_context()` in md_renderer.py also use the registry?**
   - What we know: `build_template_context()` is the base context used by both MD and HTML renderers. It calls `extract_company()`, `extract_financials()`, etc.
   - What's unclear: Whether to pass `canonical` through `build_template_context()` or only through the HTML assembly path.
   - Recommendation: Phase 137 wires registry into `build_html_context()` only (HTML is the primary output). MD renderer migration can follow in a later phase. This limits blast radius.

2. **How to handle the scoring metrics that come from state.scoring?**
   - What we know: `overall_score` and `tier` are set by the SCORE stage, which runs before RENDER.
   - What's unclear: Whether score/tier should be in the same registry or a separate one.
   - Recommendation: Include in CanonicalMetrics since they're available at render time and appear in multiple sections. The registry is computed once at render start when all stages are complete.

3. **Should the registry produce multiple format variants per metric?**
   - What we know: Revenue appears as "$3.05B" (compact), "$3,050,000,000" (full), and "3050.0" (raw for charts).
   - What's unclear: Whether `formatted` should be a single string or a dict of variants.
   - Recommendation: Single `formatted` string (compact) plus `raw` value. Builders needing other formats can derive from `raw`. Keep the registry simple.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/test_canonical_metrics.py -x` |
| Full suite command | `uv run pytest tests/ -x --timeout=30` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| METR-01 | Registry computes each metric once with XBRL-first priority | unit | `uv run pytest tests/test_canonical_metrics.py::test_source_priority -x` | Wave 0 |
| METR-02 | All 8 metric types computed and non-None for valid state | integration | `uv run pytest tests/test_canonical_metrics.py::test_all_metrics_populated -x` | Wave 0 |
| METR-03 | Every MetricValue carries source, as_of, confidence | unit | `uv run pytest tests/test_canonical_metrics.py::test_provenance_fields -x` | Wave 0 |
| METR-04 | Migrated builders read from canonical, not state | unit | `uv run pytest tests/test_canonical_metrics.py::test_builder_reads_canonical -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_canonical_metrics.py -x`
- **Per wave merge:** `uv run pytest tests/ -x --timeout=60 -k "canonical or key_stats or beta_report or company_profile or scorecard"`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_canonical_metrics.py` -- covers METR-01 through METR-04 (unit + integration against real state.json)
- [ ] Test fixture: load `output/AAPL/state.json` (exists, verified) for real-state integration tests
- [ ] Regression: compare registry output against current builder output to verify no value changes

## Sources

### Primary (HIGH confidence)
- Direct codebase audit: 96 context builder files in `src/do_uw/stages/render/context_builders/`, 365 metric references across 39 files
- `assembly_registry.py`: confirmed `BuilderFn = Callable[[AnalysisState, dict[str, Any], Path | None], None]` type and `build_html_context()` entry point
- `state_paths.py`: confirmed typed accessor pattern (21 tests in `test_state_path_smoke.py`)
- `models/common.py`: `SourcedValue[T]` with `value`, `source`, `confidence`, `as_of` fields
- `models/company.py`: `CompanyProfile` with `market_cap: SourcedValue[float] | None`, `employee_count: SourcedValue[int] | None`
- `models/market.py`: `StockPerformance` with `current_price`, `high_52w`, `low_52w`, `beta` as SourcedValue
- `formatters.py` / `formatters_numeric.py`: `safe_float()`, `format_currency()`, `format_percentage()` implementations
- Two `fmt_large_number()` implementations: `_key_stats_helpers.py:46` and `beta_report_infographics.py:17`
- `pyproject.toml`: pydantic>=2.10, jinja2>=3.1.0 confirmed

### Secondary (MEDIUM confidence)
- v12.0 research ARCHITECTURE.md: Component design for CanonicalMetricsRegistry (cross-validated against codebase audit)
- v12.0 research SUMMARY.md: Root cause analysis confirming metric duplication as one of 5 root causes

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - zero new dependencies, all patterns verified in existing codebase
- Architecture: HIGH - registry pattern directly addresses verified duplication (365 references, 39 files)
- Pitfalls: HIGH - sourced from direct code analysis (SourcedValue wrapping, dual formatters, builder signatures)

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable -- no external dependency changes expected)
