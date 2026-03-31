# Phase 10: Market Intelligence & Pricing - Research

**Researched:** 2026-02-09
**Domain:** Insurance pricing data accumulation, market intelligence, tower structure modeling
**Confidence:** MEDIUM (domain well-understood; no CONTEXT.md decisions to constrain scope)

## Summary

Phase 10 builds a proprietary pricing database that accumulates live quote data, tower structures, and premium information over time. The system extends the existing knowledge store (SQLAlchemy 2.0 + SQLite) with new tables for quotes, tower layers, carriers, and market positioning analytics. The pricing intelligence answers "what has the market been pricing for similar risks?" with confidence intervals reflecting data volume.

The domain is well-understood from the existing codebase: the system already models tower positions (5 layers: PRIMARY through DECLINE), tier-to-tower mappings, severity scenarios, claim probability bands, and deal context placeholders (SECT1-07). Phase 10 makes these concepts concrete and data-driven by replacing static config heuristics with accumulated real-world pricing observations.

Key architectural decisions: extend the existing knowledge store SQLite database (not DuckDB, not a separate database), add new Alembic migration(s), create Pydantic models for pricing data, add CLI commands for quote input, and build query/analytics modules for market positioning.

**Primary recommendation:** Extend the knowledge store with 4 new SQLAlchemy tables (quotes, tower_layers, carriers, market_segments) via a new Alembic migration, then build the analytics engine on top using basic statistics (no scipy dependency needed -- numpy or pure Python for percentiles and confidence intervals at the data volumes expected).

## Standard Stack

### Core

The phase uses no new external dependencies. Everything builds on the existing stack:

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | >=2.0 | ORM for pricing tables | Already in knowledge store, Mapped[] pattern established |
| Alembic | >=1.18 | Schema migrations | Already configured for knowledge store |
| Pydantic v2 | >=2.10 | Pricing data models | AnalysisState pattern, SourcedValue pattern |
| Typer | >=0.15 | CLI sub-commands | cli_knowledge.py pattern for sub-app |
| Rich | >=13.0 | Table/display output | Existing CLI display pattern |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| statistics (stdlib) | 3.12+ | Mean, median, stdev, quantiles | Confidence interval computation |
| math (stdlib) | 3.12+ | sqrt for CI formulas | Small-sample t-distribution CIs |
| datetime (stdlib) | 3.12+ | Date math for trend analysis | Period-over-period comparisons |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLite (knowledge store) | DuckDB (.cache/analysis.duckdb) | DuckDB is the analytical cache per CLAUDE.md, but pricing data is persistent domain knowledge, not cache. Knowledge store is the right home. |
| scipy.stats.bootstrap | stdlib statistics | scipy adds a heavy dependency for a feature that won't have enough data points to justify bootstrap. Percentile + t-distribution CI from stdlib is sufficient. |
| Separate database | Extended knowledge.db | One database is simpler, one migration path, one session factory. No cross-database joins needed. |
| pandas for analytics | Pure Python + SQLAlchemy | Data volumes will be small (hundreds to low thousands of quotes). pandas adds overhead for no benefit. |

**Installation:**
```bash
# No new dependencies needed
uv sync  # Existing deps are sufficient
```

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  models/
    pricing.py          # Pydantic models: QuoteInput, TowerStructure, MarketPosition
  knowledge/
    models.py           # Extended with: Quote, TowerLayer, Carrier (SQLAlchemy ORM)
    migrations/
      versions/
        002_pricing_tables.py  # New Alembic migration
    pricing_store.py    # PricingStore: CRUD for quotes, towers, market queries
    pricing_analytics.py # MarketPositionEngine: peer lookup, CI, trends
  cli_pricing.py        # Typer sub-app: do-uw pricing add-quote, do-uw pricing market-position
  stages/
    benchmark/
      market_position.py # Integration: cross-reference analysis with market pricing
```

### Pattern 1: Quote Data as Knowledge Store Extension

**What:** Pricing data is stored in the same SQLite database as checks, patterns, and notes -- it's domain knowledge that accumulates over time, not ephemeral analysis cache.

**When to use:** Always. The knowledge store already has the infrastructure (SQLAlchemy, Alembic, session management, FTS5).

**Example:**
```python
# In knowledge/models.py (extended)
class Quote(Base):
    """Individual pricing quote for a D&O program."""
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)

    # Quote details
    effective_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    quote_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Coverage
    total_limit: Mapped[float] = mapped_column(Float, nullable=False)  # USD
    total_premium: Mapped[float] = mapped_column(Float, nullable=False)  # USD
    retention: Mapped[float | None] = mapped_column(Float, nullable=True)  # SIR/deductible

    # Classification
    market_cap_tier: Mapped[str] = mapped_column(String, nullable=False)  # MEGA/LARGE/MID/SMALL/MICRO
    sic_code: Mapped[str | None] = mapped_column(String, nullable=True)
    sector: Mapped[str | None] = mapped_column(String, nullable=True)

    # Metadata
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tier: Mapped[str | None] = mapped_column(String, nullable=True)  # WIN/WANT/etc.
    source: Mapped[str] = mapped_column(String, nullable=False)  # Who entered this
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(String, nullable=True)

    layers: Mapped[list[TowerLayer]] = relationship(
        "TowerLayer", back_populates="quote", cascade="all, delete-orphan"
    )
```

### Pattern 2: Tower Structure as Layered Hierarchy

**What:** Each quote has 1-N tower layers, each with a carrier, attachment point, limit, and premium.

**When to use:** Every time a quote is entered. Tower structure is the core data structure for D&O pricing.

**Example:**
```python
class TowerLayer(Base):
    """Individual layer in a D&O insurance tower."""
    __tablename__ = "tower_layers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotes.id"), nullable=False)

    # Layer position
    layer_position: Mapped[str] = mapped_column(String, nullable=False)  # PRIMARY, LOW_EXCESS, MID_EXCESS, HIGH_EXCESS
    layer_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-based within tower

    # Coverage
    attachment_point: Mapped[float] = mapped_column(Float, nullable=False)  # USD (0 for primary)
    limit: Mapped[float] = mapped_column(Float, nullable=False)  # USD per layer
    premium: Mapped[float] = mapped_column(Float, nullable=False)  # USD per layer

    # Carrier
    carrier_name: Mapped[str] = mapped_column(String, nullable=False)
    carrier_rating: Mapped[str | None] = mapped_column(String, nullable=True)  # AM Best

    # Derived metrics (computed on insert)
    rate_on_line: Mapped[float] = mapped_column(Float, nullable=False)  # premium / limit
    premium_per_million: Mapped[float] = mapped_column(Float, nullable=False)  # premium / (limit/1M)

    quote: Mapped[Quote] = relationship("Quote", back_populates="layers")
```

### Pattern 3: Market Positioning via Risk Profile Bucketing

**What:** To answer "what has the market been pricing for companies like this?", the engine buckets quotes by (market_cap_tier, sector, score_range) and computes summary statistics with confidence intervals.

**When to use:** After analysis, when comparing system risk assessment to actual market pricing.

**Example:**
```python
@dataclass
class MarketPosition:
    """Market positioning result for a risk profile."""
    peer_count: int  # How many quotes match this profile
    confidence_level: str  # HIGH (50+), MEDIUM (10-49), LOW (3-9), INSUFFICIENT (<3)
    median_rate_on_line: float | None
    mean_rate_on_line: float | None
    ci_low: float | None  # 95% CI lower bound
    ci_high: float | None  # 95% CI upper bound
    percentile_25: float | None
    percentile_75: float | None
    trend_direction: str  # HARDENING, SOFTENING, STABLE
    trend_magnitude_pct: float | None  # YoY change
    data_window: str  # e.g. "2024-01 to 2026-01"
```

### Pattern 4: CLI Sub-App for Quote Management

**What:** `do-uw pricing` sub-app mirrors the `do-uw knowledge` pattern. Commands: `add-quote`, `list-quotes`, `market-position`, `trends`.

**When to use:** All quote input and market intelligence queries go through the CLI.

**Example:**
```python
# cli_pricing.py
pricing_app = typer.Typer(name="pricing", help="Market pricing intelligence")

@pricing_app.command("add-quote")
def add_quote(
    ticker: str = typer.Argument(help="Stock ticker"),
    premium: float = typer.Option(..., help="Total premium USD"),
    limit: float = typer.Option(..., help="Total limit USD"),
    effective_date: str = typer.Option(..., help="Policy effective date YYYY-MM-DD"),
    # ... more options
) -> None: ...
```

### Anti-Patterns to Avoid

- **Storing pricing data in DuckDB cache:** DuckDB is for ephemeral analytical cache (7-day TTL). Pricing data is persistent domain knowledge.
- **Embedding pricing in AnalysisState:** The state model is per-analysis. Pricing is cross-analysis accumulated data.
- **Building a separate database:** The knowledge store already has SQLAlchemy, Alembic, session management. One database keeps it simple.
- **Over-engineering analytics for small data:** Early on, there will be few quotes. Don't build ML models or complex statistical engines. Basic percentiles and t-distribution CIs are appropriate.
- **Mixing quote input with analysis pipeline stages:** Quote input is a standalone operation, not part of RESOLVE-ACQUIRE-EXTRACT flow. The pipeline reads pricing data during BENCHMARK/RENDER but doesn't write it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Percentile computation | Custom sort-and-index | `statistics.quantiles()` (Python 3.10+) | Edge cases with interpolation, empty data |
| Confidence intervals | Manual formula | `statistics.stdev()` + t-distribution from math | Standard error formula is well-known but has edge cases with n<3 |
| Date math / period grouping | Manual date arithmetic | `datetime` + `calendar` stdlib | Leap years, month boundaries, fiscal years |
| Rate-on-line calculation | Inline division | Computed column on TowerLayer model | Ensures consistency, avoids division-by-zero |
| Market cap tier classification | New logic | Reuse existing `market_cap_multipliers.tiers` from scoring.json | Already defines MEGA/LARGE/MID/SMALL/MICRO boundaries |
| Tower position classification | New enum | Reuse existing `TowerPosition` from scoring_output.py | PRIMARY, LOW_EXCESS, MID_EXCESS, HIGH_EXCESS already defined |

**Key insight:** The system already defines many of the classification structures needed for pricing intelligence (market cap tiers, tower positions, tier classifications, sector codes). Phase 10 should reuse these, not create parallel taxonomies.

## Common Pitfalls

### Pitfall 1: Premature Statistical Sophistication

**What goes wrong:** Building complex statistical models (bootstrap, Bayesian, kernel density) when the pricing database has 5-20 data points per segment.
**Why it happens:** Desire for "real" statistics before sufficient data exists.
**How to avoid:** Start with simple descriptive statistics (median, IQR, min/max). Add confidence intervals using t-distribution for small samples. Only consider advanced methods when n>50 per segment. Always report sample size alongside any statistic.
**Warning signs:** Importing scipy, numpy, or sklearn for this phase.

### Pitfall 2: Conflating Quote Data with Binding Terms

**What goes wrong:** Treating a quote indication as the actual placement terms. Quotes may not bind; terms change during negotiation.
**Why it happens:** Underwriters enter quotes at different stages of the placement process.
**How to avoid:** Add a `status` field: INDICATION, QUOTED, BOUND, EXPIRED. Filter analytics by status (default: QUOTED + BOUND). Always show data source in output.
**Warning signs:** No status field on the quote model; mixing indications with bound premiums in analytics.

### Pitfall 3: Stale Data Without Time Windowing

**What goes wrong:** Including 5-year-old quotes in "current market" analytics when the market has cycled through hard and soft phases.
**Why it happens:** Queries don't default to recent data windows.
**How to avoid:** Default analytics window to trailing 24 months. Allow override. Always display the data window in results. Weight recent data higher in trend analysis.
**Warning signs:** No date filtering in market position queries.

### Pitfall 4: Ignoring Layer-Specific Pricing Dynamics

**What goes wrong:** Comparing total program premiums without accounting for tower structure. A $500K primary premium is not comparable to a $500K high-excess premium.
**Why it happens:** Quote-level aggregation ignores layer positions.
**How to avoid:** Analyze pricing per layer position. Rate-on-line comparisons must be within same tower position. Provide both program-level and layer-level analytics.
**Warning signs:** Only total_premium in analytics; no layer_position filtering.

### Pitfall 5: Overloading the Knowledge Store File

**What goes wrong:** Adding 200+ lines of Quote/TowerLayer/Carrier models to models.py (already 281 lines), pushing it over the 500-line limit.
**Why it happens:** Natural extension of existing models file.
**How to avoid:** Create pricing-specific model file (knowledge/pricing_models.py) that imports Base from models.py. Keep ORM models separate from store/analytics logic.
**Warning signs:** models.py growing past 400 lines after additions.

### Pitfall 6: Not Handling Zero-Data Segments Gracefully

**What goes wrong:** Errors or misleading results when a market position query returns 0 matching quotes.
**Why it happens:** No data exists yet for a particular market_cap_tier + sector + score_range combination.
**How to avoid:** Return explicit "INSUFFICIENT DATA" with available adjacent segments. Suggest broadening criteria. Never return NaN or error -- return None with explanatory message.
**Warning signs:** Division by zero in analytics; empty result sets cause exceptions.

## Code Examples

### Quote Entry via CLI

```python
# cli_pricing.py
from datetime import datetime, UTC

@pricing_app.command("add-quote")
def add_quote(
    ticker: str = typer.Argument(help="Stock ticker"),
    premium: float = typer.Option(..., "--premium", "-p", help="Total premium USD"),
    limit: float = typer.Option(..., "--limit", "-l", help="Total limit USD"),
    effective_date: str = typer.Option(..., "--effective", "-e", help="Effective date YYYY-MM-DD"),
    source: str = typer.Option("manual", "--source", "-s", help="Data source"),
) -> None:
    """Record a pricing quote for market intelligence."""
    from do_uw.knowledge.pricing_store import PricingStore

    store = PricingStore()
    eff = datetime.strptime(effective_date, "%Y-%m-%d").replace(tzinfo=UTC)
    quote_id = store.add_quote(
        ticker=ticker.upper(),
        total_premium=premium,
        total_limit=limit,
        effective_date=eff,
        source=source,
    )
    console.print(f"[green]Quote {quote_id} recorded for {ticker.upper()}[/green]")
```

### Market Position Computation

```python
# knowledge/pricing_analytics.py
from statistics import mean, median, stdev, quantiles
from math import sqrt

_T_VALUES_95 = {  # t-distribution critical values for 95% CI
    2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    10: 2.228, 15: 2.131, 20: 2.086, 30: 2.042,
    50: 2.009, 100: 1.984,
}

def _t_value(n: int) -> float:
    """Lookup t-value for 95% CI given sample size."""
    if n < 2:
        return 0.0
    for threshold in sorted(_T_VALUES_95.keys()):
        if n <= threshold:
            return _T_VALUES_95[threshold]
    return 1.96  # Normal approximation for large n

def compute_market_position(
    rates: list[float],
    dates: list[datetime] | None = None,
) -> MarketPosition:
    """Compute market positioning from a list of rate-on-line values."""
    n = len(rates)
    if n < 3:
        return MarketPosition(
            peer_count=n,
            confidence_level="INSUFFICIENT",
            # ... all None
        )

    med = median(rates)
    avg = mean(rates)
    sd = stdev(rates) if n > 1 else 0.0
    t = _t_value(n)
    margin = t * sd / sqrt(n) if n > 1 else 0.0

    q = quantiles(rates, n=4)  # [Q1, Q2, Q3]

    confidence = "HIGH" if n >= 50 else "MEDIUM" if n >= 10 else "LOW"

    return MarketPosition(
        peer_count=n,
        confidence_level=confidence,
        median_rate_on_line=med,
        mean_rate_on_line=avg,
        ci_low=avg - margin,
        ci_high=avg + margin,
        percentile_25=q[0],
        percentile_75=q[2],
        trend_direction=_compute_trend(rates, dates),
        trend_magnitude_pct=_compute_trend_magnitude(rates, dates),
        data_window=_format_window(dates),
    )
```

### Tower Visualization Data

```python
# knowledge/pricing_store.py
def get_tower_comparison(
    self,
    ticker: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Get historical tower structures for a company.

    Returns most recent tower structures with layer details
    for side-by-side comparison.
    """
    with self._session() as session:
        stmt = (
            select(Quote)
            .where(Quote.ticker == ticker)
            .order_by(Quote.effective_date.desc())
            .limit(limit)
        )
        quotes = list(session.execute(stmt).scalars().all())
        return [
            {
                "quote_id": q.id,
                "effective_date": q.effective_date.isoformat(),
                "total_premium": q.total_premium,
                "total_limit": q.total_limit,
                "layers": [
                    {
                        "position": l.layer_position,
                        "carrier": l.carrier_name,
                        "attachment": l.attachment_point,
                        "limit": l.limit,
                        "premium": l.premium,
                        "rate_on_line": l.rate_on_line,
                    }
                    for l in sorted(q.layers, key=lambda x: x.layer_number)
                ],
            }
            for q in quotes
        ]
```

### Mispricing Alert

```python
# stages/benchmark/market_position.py
def check_mispricing(
    quality_score: float,
    market_position: MarketPosition,
    current_premium: float | None,
    current_limit: float | None,
) -> str | None:
    """Check if market pricing diverges from analytical assessment.

    Returns alert string if mispricing detected, None otherwise.
    """
    if current_premium is None or current_limit is None:
        return None
    if market_position.confidence_level == "INSUFFICIENT":
        return None

    current_rol = current_premium / current_limit if current_limit > 0 else 0.0
    median_rol = market_position.median_rate_on_line
    if median_rol is None or median_rol == 0:
        return None

    deviation_pct = ((current_rol - median_rol) / median_rol) * 100

    if abs(deviation_pct) < 15:
        return None  # Within normal range

    if deviation_pct > 0:
        return (
            f"OVERPRICED vs market: current ROL {current_rol:.4f} is "
            f"{deviation_pct:.0f}% above median {median_rol:.4f} "
            f"(n={market_position.peer_count}, "
            f"CI: {market_position.ci_low:.4f}-{market_position.ci_high:.4f})"
        )
    return (
        f"UNDERPRICED vs market: current ROL {current_rol:.4f} is "
        f"{abs(deviation_pct):.0f}% below median {median_rol:.4f} "
        f"(n={market_position.peer_count}, "
        f"CI: {market_position.ci_low:.4f}-{market_position.ci_high:.4f})"
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static pricing_multiplier in scoring.json tiers | Data-driven market positioning from accumulated quotes | Phase 10 | Enables "is the market agreeing with our assessment?" |
| DealContext as placeholder text fields | Structured quote data with carrier, layer, premium breakdown | Phase 10 | Machine-readable deal context for analytics |
| Tower position as tier-derived recommendation only | Actual tower visualization from historical placement data | Phase 10 | Underwriters see what carriers are actually doing |
| No market trend visibility | Period-over-period rate-on-line comparisons by segment | Phase 10 | Hardening/softening detection by market segment |

**Note:** The existing system already has the conceptual framework (tower positions, tier-to-pricing mappings, severity ranges by market cap). Phase 10 replaces heuristic guidance with empirical data.

## Integration Points with Existing System

### 1. AnalysisState Does NOT Get Pricing Fields

Pricing data is cross-analysis, accumulated over time. It does NOT belong on the per-analysis AnalysisState model. The pipeline reads from the pricing store during BENCHMARK but does not write pricing data to state.

### 2. Knowledge Store Extension (Not Replacement)

New tables are added alongside existing checks/patterns/notes tables. The KnowledgeStore class may be extended with pricing methods, or a separate PricingStore class can use the same underlying database and session factory.

**Recommendation:** Separate PricingStore class that shares the same SQLite database but has its own API surface. This avoids bloating KnowledgeStore (already 442 lines) and follows the separation pattern of store.py + store_search.py + store_converters.py.

### 3. CLI Registration Pattern

Follow the cli_knowledge.py pattern:
```python
# cli.py
from do_uw.cli_pricing import pricing_app
app.add_typer(pricing_app, name="pricing")
```

### 4. BENCHMARK Stage Integration

The BenchmarkStage can optionally query the pricing store for market positioning data. This is a non-breaking addition -- if no pricing data exists, the system behaves exactly as before.

### 5. RENDER Stage: Tower Visualization

If tower comparison data exists for the company, the Word renderer can include a tower structure comparison chart (new chart in stages/render/charts/). This is additive, not modifying existing section renderers.

### 6. Reuse of Existing Enums and Constants

- `TowerPosition` (scoring_output.py): PRIMARY, LOW_EXCESS, MID_EXCESS, HIGH_EXCESS, DECLINE
- `Tier` (scoring.py): WIN, WANT, WRITE, WATCH, WALK, NO_TOUCH
- Market cap tiers from scoring.json: MEGA, LARGE, MID, SMALL, MICRO
- Sector codes from CompanyIdentity.sector

## Data Model Design Considerations

### Quote Status Lifecycle

```
INDICATION -> QUOTED -> BOUND -> EXPIRED
                |         |
                +-> DECLINED (by carrier or insured)
```

Only QUOTED and BOUND should be used for market analytics by default. INDICATION is too preliminary; EXPIRED is historical.

### Market Segmentation Keys

For "what has the market been pricing for companies like this?" the segmentation keys are:

1. **market_cap_tier** (MEGA/LARGE/MID/SMALL/MICRO) -- primary driver of D&O pricing
2. **sector** (TECH/HLTH/FINS/etc.) -- secondary driver via industry claim rates
3. **score_range** (e.g., 80-100, 60-79, 40-59, 20-39, 0-19) -- quality score bucketed
4. **tower_position** (PRIMARY/LOW_EXCESS/MID_EXCESS/HIGH_EXCESS) -- for layer-specific comparison
5. **time_window** (trailing 24 months default) -- avoids market cycle distortion

### Minimum Data for Meaningful Analytics

| Metric | Min N | Confidence |
|--------|-------|-----------|
| Median rate-on-line | 3 | LOW |
| Mean + CI | 10 | MEDIUM |
| Trend direction | 20+ across 2+ periods | MEDIUM |
| Percentile distribution | 50+ | HIGH |
| Full market positioning | 100+ | HIGH |

Below n=3, report "INSUFFICIENT DATA" with no statistics.

### Rate-on-Line (ROL) as Primary Metric

ROL = premium / limit. This is the standard D&O pricing comparison metric because it normalizes for limit size. Layer-level ROL is more meaningful than program-level ROL because it accounts for attachment point risk.

ILF (Increased Limit Factor) curves show how pricing scales with limit. The ILF for a $10M layer is lower than for a $5M layer because higher attachment points have lower loss probability. This is captured implicitly by layer-level ROL comparisons.

### Carrier Intelligence

Carrier data enables competitive intelligence:
- Which carriers are active in which layers?
- Which carriers are expanding/contracting capacity?
- Market share by layer position
- Carrier pricing relative to market average

Simple carrier tracking (name + AM Best rating) is sufficient for v1.

## Proposed Table Schema Summary

### quotes
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| ticker | STRING | Company ticker |
| company_name | STRING | Company legal name |
| effective_date | DATETIME | Policy effective date |
| expiration_date | DATETIME | Policy expiration (nullable) |
| quote_date | DATETIME | When quote was issued |
| status | STRING | INDICATION/QUOTED/BOUND/EXPIRED/DECLINED |
| total_limit | FLOAT | Total program limit USD |
| total_premium | FLOAT | Total program premium USD |
| retention | FLOAT | SIR/deductible USD (nullable) |
| market_cap_tier | STRING | MEGA/LARGE/MID/SMALL/MICRO |
| sic_code | STRING | Company SIC code (nullable) |
| sector | STRING | Sector code (nullable) |
| quality_score | FLOAT | System quality score at quote time (nullable) |
| tier | STRING | System tier at quote time (nullable) |
| program_rate_on_line | FLOAT | Computed: total_premium / total_limit |
| source | STRING | Who entered this data |
| notes | STRING | Free-text notes (nullable) |
| created_at | DATETIME | Record creation timestamp |
| metadata_json | STRING | Extensible JSON metadata (nullable) |

### tower_layers
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| quote_id | INTEGER FK | References quotes.id |
| layer_position | STRING | PRIMARY/LOW_EXCESS/MID_EXCESS/HIGH_EXCESS |
| layer_number | INTEGER | 1-based position in tower |
| attachment_point | FLOAT | Attachment point USD (0 for primary) |
| limit | FLOAT | Layer limit USD |
| premium | FLOAT | Layer premium USD |
| carrier_name | STRING | Carrier name |
| carrier_rating | STRING | AM Best rating (nullable) |
| rate_on_line | FLOAT | Computed: premium / limit |
| premium_per_million | FLOAT | Computed: premium / (limit / 1e6) |
| is_lead | BOOLEAN | Whether carrier is lead on this layer |
| share_pct | FLOAT | Carrier's share if quota share (nullable) |

### Indexes
- ix_quotes_ticker (quotes.ticker)
- ix_quotes_effective_date (quotes.effective_date)
- ix_quotes_market_cap_tier (quotes.market_cap_tier)
- ix_quotes_sector (quotes.sector)
- ix_quotes_status (quotes.status)
- ix_tower_layers_quote_id (tower_layers.quote_id)
- ix_tower_layers_carrier_name (tower_layers.carrier_name)

## Open Questions

1. **Should tower layer input be required or optional?**
   - What we know: Some underwriters will have full tower data; others will only have program-level premium/limit.
   - What's unclear: How common is layer-level data availability in practice?
   - Recommendation: Make tower layers optional. Quote-level analytics work with just total premium/limit. Layer-level analytics are a bonus when data is available.

2. **Should quotes auto-link to analysis runs?**
   - What we know: Phase 9 stores analysis runs as notes with 'analysis_run' tag. A quote for AAPL could be linked to the latest AAPL analysis run.
   - What's unclear: Whether this linkage adds value or complexity.
   - Recommendation: Store quality_score and tier on the quote at entry time (from most recent analysis), but don't create a foreign key to analysis runs. Keep it simple.

3. **Should market positioning be displayed in the main worksheet or only via CLI?**
   - What we know: The RENDER stage produces Word/PDF/Markdown. Adding a "Market Intelligence" section would require a new section renderer.
   - What's unclear: Whether this should be in the main worksheet or a separate report.
   - Recommendation: Add to the main worksheet as an optional section (rendered only when pricing data exists). Keep the CLI for interactive queries. Defer the section rendering to Plan 10-03.

4. **Should the system import bulk pricing data from external sources?**
   - What we know: Some market reports publish aggregate pricing data. A bulk import capability would bootstrap the database faster.
   - What's unclear: Format standardization of external pricing data.
   - Recommendation: Build a `do-uw pricing import-csv` command for CSV/Excel ingestion. Define a standard column mapping. This enables bootstrapping from broker submission data.

5. **Trend analysis: linear regression or period-over-period?**
   - What we know: Market trends (hardening/softening) are typically reported as YoY or QoQ changes.
   - What's unclear: Whether more sophisticated trend detection is needed.
   - Recommendation: Start with period-over-period median comparison (H1 vs H2, or trailing 12m vs prior 12m). Linear regression can be added later when data volume supports it.

## Sources

### Primary (HIGH confidence)
- Existing codebase: knowledge/models.py, knowledge/store.py, models/scoring_output.py, models/executive_summary.py, brain/scoring.json -- all directly examined for integration points
- Python 3.12 stdlib documentation: statistics.quantiles(), statistics.stdev() -- standard library capabilities verified

### Secondary (MEDIUM confidence)
- [D&O in 2026: Abundant capacity, but sharper scrutiny directs renewals](https://www.insurancebusinessmag.com/us/news/professional-liability/dando-in-2026-abundant-capacity-but-sharper-scrutiny-directs-renewals-562802.aspx) -- current market conditions and pricing dynamics
- [D&O Insurance Pricing: 2024 in Review, 2025 Outlook](https://foundershield.com/blog/do-insurance-pricing-2024-review-2025-outlook/) -- pricing trend methodology
- [Excess Layers of D&O Insurance: Peeling the Onion](https://baileycav.com/wp-content/uploads/2023/02/excess_layers_of_d_o_insurance-_peeling_the_oniion.pdf) -- tower structure and attachment/exhaustion provisions
- [SciPy bootstrap documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) -- confirmed for reference, not recommended as dependency
- [ACORD Data Standards](https://www.acord.org/standards-architecture/acord-data-standards) -- industry standard data model concepts

### Tertiary (LOW confidence)
- [D&O Reinsurance Pricing - A Financial Market Approach (CAS)](https://www.casact.org/sites/default/files/database/forum_05wforum_05wf001.pdf) -- ILF and actuarial pricing methodology
- [Introduction to Increased Limits Ratemaking (CAS)](https://www.casact.org/library/studynotes/palmer.pdf) -- ILF curve theory
- General D&O insurance industry knowledge from training data -- used for domain terminology, verified against industry sources where possible

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies; all existing libraries are sufficient
- Architecture: HIGH - Follows established knowledge store patterns (SQLAlchemy, Alembic, Typer sub-app)
- Data model: MEDIUM - Schema design based on domain research and existing system structures, but no CONTEXT.md user decisions to validate against
- Analytics: MEDIUM - Statistical approach is sound but confidence interval methodology for small samples needs careful implementation
- Pitfalls: HIGH - Based on direct analysis of existing codebase patterns and anti-patterns documented in CLAUDE.md

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (stable domain, no fast-moving dependencies)
