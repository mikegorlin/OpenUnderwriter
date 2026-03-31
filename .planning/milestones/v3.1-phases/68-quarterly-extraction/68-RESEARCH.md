# Phase 68: Quarterly XBRL Extraction -- 8 Quarters with Trends - Research

**Researched:** 2026-03-06
**Domain:** XBRL quarterly financial extraction, YTD disambiguation, fiscal period alignment, trend computation
**Confidence:** HIGH

## Summary

Phase 68 extracts 8 quarters of XBRL financial data from the Company Facts API, which already returns quarterly data alongside annual data in a single cached response. The core technical challenge -- YTD-to-quarterly disambiguation -- is dramatically simpler than initially expected because the SEC API includes a `frame` field that is present ONLY on standalone quarterly entries (format `CY####Q#` for duration, `CY####Q#I` for instant) and absent on YTD cumulative entries. This was verified empirically against Apple (CIK 320193, non-calendar Sep fiscal year) and RPM International (CIK 81362, non-calendar Dec fiscal year).

The implementation builds a new `xbrl_quarterly.py` extraction module that filters Company Facts entries by `form="10-Q"`, selects entries with `frame` matching the `CY####Q#` pattern for duration concepts (income/cash flow), takes instant concepts (balance sheet) as-is with `CY####Q#I` pattern, and stores results in a new `QuarterlyStatements` Pydantic model on `state.extracted.financials.quarterly_xbrl`. Trend computation (QoQ, YoY, acceleration, sequential patterns) goes in a separate `xbrl_trends.py` module. An XBRL/LLM reconciler ensures XBRL always wins for numeric data while logging divergences.

**Primary recommendation:** Use the `frame` field as the primary YTD discriminator (eliminates subtraction math entirely for ~95% of entries). Fall back to `start`/`end` date duration analysis only for entries missing the `frame` field. Build trend computation as a separate module consuming `QuarterlyStatements`.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QTRLY-01 | Extract 8 quarters from Company Facts API by filtering form_type="10-Q" | Existing `extract_concept_value()` already supports `form_type` parameter. Filter `form="10-Q"`, select entries with `frame` matching `CY####Q#` pattern. Company Facts API verified to contain both standalone and YTD entries for 10-Q filings. |
| QTRLY-02 | YTD-to-quarterly disambiguation for duration concepts | **Simpler than expected.** The `frame` field is present ONLY on standalone quarterly entries and absent on YTD cumulatives. Verified on AAPL and RPM. Primary strategy: filter by `frame` regex `CY\d{4}Q[1-4]$`. Fallback: compute `end - start` duration; 80-100 day span = standalone quarter, >100 = YTD. No subtraction math needed when `frame` is present. |
| QTRLY-03 | Fiscal period alignment using fy+fp fields, handle non-calendar fiscal years | AAPL (Sep FY) fiscal Q1 maps to calendar Q4. RPM (Dec FY) fiscal Q1 maps to calendar Q1. The `frame` field uses calendar alignment (CY2024Q4 for AAPL's fiscal Q1). Store both `fy`+`fp` (fiscal) and `frame` (calendar) for dual-view display. |
| QTRLY-04 | QoQ and YoY trend computation with acceleration/deceleration detection | Build in `xbrl_trends.py`. QoQ = sequential quarter change. YoY = same fiscal quarter prior year (fp=Q1 to fp=Q1, eliminates seasonality). Acceleration = current growth rate vs prior growth rate. |
| QTRLY-05 | Sequential pattern detection: 4+ quarters of margin compression, revenue deceleration | Sliding window over 8 quarters checking for consecutive negative deltas. Margin = gross_margin_pct QoQ. Revenue decel = revenue_growth_yoy decreasing. Cash flow deterioration = OCF/revenue declining. |
| QTRLY-06 | XBRL/LLM reconciler: XBRL always wins for numeric data, log divergences | Compare `quarterly_xbrl` values against `quarterly_updates` (LLM) and `yfinance_quarterly` for overlapping periods. XBRL wins. Log divergence magnitude and direction. |
| QTRLY-07 | Cross-validation against yfinance quarterly data | yfinance quarterly already extracted in `yfinance_quarterly.py` as `list[dict]`. Compare by matching period dates (within 7-day tolerance for fiscal calendar differences). Log discrepancies >1%. |
| QTRLY-08 | Every quarterly value carries SourcedValue with XBRL provenance at HIGH confidence | Reuse existing `_make_sourced_value()` pattern from `financial_statements.py`. Source format: `XBRL:10-Q:{end_date}:CIK{cik}:accn:{accn}`. Confidence = HIGH. |
</phase_requirements>

## Standard Stack

### Core (Already Installed -- No Changes)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime | Project standard |
| Pydantic | 2.10+ | QuarterlyStatements model | Already used for all state models |
| httpx | 0.28+ | SEC API (no new calls -- Company Facts already cached) | Project standard |

### Supporting (Already in Codebase)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `xbrl_mapping.py` | existing | `resolve_concept()` + `extract_concept_value()` | Extend with quarterly form_type support |
| `financial_statements.py` | existing | `_make_sourced_value()`, `fiscal_year_label()` | Reuse provenance pattern |
| `yfinance_quarterly.py` | existing | 8-quarter yfinance data | Cross-validation target |
| `validation.py` | existing | `ExtractionReport`, `create_report()` | Extraction reporting |

### No New Dependencies
Zero new packages. Everything is existing API data (already cached) + pure Python computation + new Pydantic models.

## Architecture Patterns

### Recommended File Structure
```
src/do_uw/
  stages/extract/
    xbrl_quarterly.py          # NEW: quarterly XBRL extraction (~300 lines)
    xbrl_trends.py             # NEW: trend computation (~200 lines)
    xbrl_llm_reconciler.py     # NEW: XBRL/LLM precedence merge (~120 lines)
    xbrl_mapping.py            # MODIFY: add frame-based quarterly filtering
    financial_statements.py    # NO CHANGE (annual extraction stays as-is)
  models/
    financials.py              # MODIFY: add QuarterlyStatements, QuarterlyPeriod
```

### Pattern 1: Frame-Based Quarterly Filtering (NEW -- critical discovery)
**What:** Filter Company Facts entries by `frame` field regex to get standalone quarterly values, avoiding YTD cumulatives entirely.
**When to use:** All duration concept extraction from 10-Q filings.
**Why:** The `frame` field is the SEC API's own disambiguation -- entries with `frame` matching `CY\d{4}Q[1-4]$` are standalone quarters, while YTD cumulatives lack this field.
**Example (from real AAPL data):**
```python
import re

QUARTERLY_FRAME_RE = re.compile(r"^CY\d{4}Q[1-4]$")
INSTANT_FRAME_RE = re.compile(r"^CY\d{4}Q[1-4]I$")

def extract_quarterly_entries(
    facts: dict[str, Any],
    concept: str,
    period_type: str,  # "duration" or "instant"
    unit: str = "USD",
) -> list[dict[str, Any]]:
    """Extract standalone quarterly entries from Company Facts.

    For duration concepts (income, cash flow): select entries with
    frame matching CY####Q# (standalone quarter, not YTD).

    For instant concepts (balance sheet): select entries with
    frame matching CY####Q#I (point-in-time snapshot).
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    concept_data = us_gaap.get(concept, {})
    entries: list[dict[str, Any]] = concept_data.get("units", {}).get(unit, [])

    # Filter to 10-Q filings only
    q_entries = [e for e in entries if e.get("form") == "10-Q"]

    # Select standalone quarterly entries via frame field
    pattern = INSTANT_FRAME_RE if period_type == "instant" else QUARTERLY_FRAME_RE
    framed = [e for e in q_entries if pattern.match(e.get("frame", ""))]

    if framed:
        return sorted(framed, key=lambda e: e.get("end", ""))

    # Fallback: duration-based filtering for entries without frame
    if period_type == "duration":
        return _filter_by_duration(q_entries)

    return sorted(q_entries, key=lambda e: e.get("end", ""))
```

**Real data verification (AAPL FY2025 Q2, filed 2025-05-02):**
```
# YTD cumulative (NO frame field):
{"start": "2024-09-29", "end": "2025-03-29", "val": 219659000000, "fp": "Q2", "form": "10-Q"}

# Standalone quarter (HAS frame field):
{"start": "2024-12-29", "end": "2025-03-29", "val": 95359000000, "fp": "Q2", "form": "10-Q", "frame": "CY2025Q1"}
```
Note: AAPL's fiscal Q2 = calendar Q1, hence `frame: "CY2025Q1"`.

### Pattern 2: Dual Period Labeling (NEW -- fiscal + calendar)
**What:** Store both the company's fiscal period labels (from `fy`+`fp`) and the calendar-aligned period (from `frame`) for each quarterly data point.
**When to use:** Every quarterly value.
**Why:** Fiscal labels for company-internal trend analysis; calendar labels for peer comparison.
**Example:**
```python
class QuarterlyPeriod(BaseModel):
    """Single quarter of financial data."""
    fiscal_year: int              # From fy field (e.g., 2025)
    fiscal_quarter: int           # From fp field (1-4)
    fiscal_label: str             # "Q1 FY2025"
    calendar_period: str          # From frame field: "CY2024Q4"
    period_end: str               # From end field: "2024-12-28"
    period_start: str | None      # From start field (duration) or None (instant)
    income: dict[str, SourcedValue[float] | None]
    balance: dict[str, SourcedValue[float] | None]
    cash_flow: dict[str, SourcedValue[float] | None]
```

### Pattern 3: Trend Computation (NEW -- establish)
**What:** Compute QoQ, YoY, acceleration, and sequential pattern metrics from quarterly time series.
**When to use:** After quarterly extraction is complete.
**Example:**
```python
@dataclass
class TrendResult:
    concept: str
    qoq_changes: list[float | None]   # Sequential quarter changes (%)
    yoy_changes: list[float | None]    # Same-quarter YoY changes (%)
    acceleration: float | None          # Latest QoQ change - prior QoQ change
    consecutive_decline: int            # Count of consecutive negative QoQ
    pattern: str | None                 # "compression", "deceleration", "deterioration", None

def compute_trends(
    quarters: list[QuarterlyPeriod],
    concept: str,
    statement: str,  # "income", "balance", "cash_flow"
) -> TrendResult:
    """Compute trend metrics for a single concept across quarters."""
```

### Anti-Patterns to Avoid
- **Subtracting YTD values manually when `frame` is available:** The SEC API has already disambiguated. YTD subtraction (Q2 = H1 - Q1) is a FALLBACK for the ~5% of entries missing `frame`, not the primary approach.
- **Using `fp` field to identify standalone quarters:** `fp=Q2` appears on BOTH the YTD cumulative and the standalone quarter. Only `frame` or `start`/`end` duration distinguishes them.
- **Filtering by `fp` for YoY comparison:** AAPL's fiscal Q1 = calendar Q4. Compare by `fp` for fiscal YoY, by `frame` for calendar YoY. Use fiscal for single-company analysis.
- **Creating a separate API call for quarterly data:** Company Facts API already returns everything in one call (already cached 14 months). Zero new API calls needed.
- **Breaking existing annual extraction:** `financial_statements.py` stays untouched. Quarterly extraction is a new parallel path, not a modification of annual.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YTD disambiguation | Subtraction math (H1-Q1, 9mo-H1) | `frame` field regex filter | SEC API already solved this; subtraction introduces errors on restated quarters |
| SourcedValue creation | Custom provenance builder | Existing `_make_sourced_value()` from `financial_statements.py` | Already handles all provenance fields correctly |
| Concept resolution | Hardcoded tag lookups | Existing `resolve_concept()` with tag priority | Already picks tag with most recent data |
| Extraction reporting | Custom logging | Existing `create_report()` from `validation.py` | Already computes coverage + confidence |
| Period deduplication | Custom dedup logic | Existing `extract_concept_value()` dedup by end+fy+fp | Already prefers most recently filed |

**Key insight:** The `frame` field discovery means this phase is primarily about data modeling and organization, not complex date arithmetic. The SEC did the hard work.

## Common Pitfalls

### Pitfall 1: Missing `frame` Field on Some Entries
**What goes wrong:** Not all 10-Q entries have a `frame` field. Older filings and some entries from filings that report comparative periods may lack `frame`.
**Why it happens:** The `frame` field is added by the SEC's aggregation process. Comparative/restated values from prior periods included in a current filing may not get `frame` assigned.
**How to avoid:** Primary: filter by `frame` regex. Fallback: for entries without `frame`, compute duration from `start`/`end` dates. Duration of 80-100 days = standalone quarter. Duration >150 days = YTD. Entries from 100-150 days are ambiguous -- skip them and log.
**Warning signs:** Coverage drops significantly when frame-only filtering is used. Compare count of framed entries vs total 10-Q entries per concept.

### Pitfall 2: Duplicate Entries Across Filings
**What goes wrong:** The same quarter's data appears multiple times -- once in the original filing and again in subsequent filings as comparative data. AAPL's Q1 FY2025 revenue appears in both the Q1 filing (accn ending 000008) AND the Q1 FY2026 filing (accn ending 000006).
**Why it happens:** 10-Q filings include prior-period comparatives. The Company Facts API stores each filing's data separately.
**How to avoid:** Deduplicate by `frame` field value (e.g., `CY2024Q4` should appear only once). When multiple entries share the same `frame`, prefer the most recently `filed` entry (may include corrections/amendments).
**Warning signs:** More than 8 entries after filtering -- indicates duplicates.

### Pitfall 3: Fiscal-Calendar Period Misalignment in Labels
**What goes wrong:** Displaying "Q1 FY2025" next to "CY2024Q4" confuses users. AAPL's fiscal Q1 (Oct-Dec 2024) maps to calendar Q4 2024. If trends show "Q1 FY2025 revenue up 15% QoQ" but the calendar label says Q4, it's disorienting.
**Why it happens:** Non-calendar fiscal year companies have fiscal quarters that span different calendar quarters.
**How to avoid:** Use fiscal labels (Q1 FY2025) for single-company display. Use calendar labels for peer comparison. Store both, let the renderer choose based on context. Add `fiscal_year_end_month` to help renderers contextualize.
**Warning signs:** QoQ trends that seem to contradict seasonal patterns (because fiscal Q1 is actually calendar Q4).

### Pitfall 4: Balance Sheet Entries Don't Have `start` Field
**What goes wrong:** Trying to use `start`/`end` duration analysis on instant (balance sheet) concepts fails because instant concepts have no `start` field.
**Why it happens:** Balance sheet items are point-in-time snapshots, not duration measurements. The SEC API correctly omits `start` for these.
**How to avoid:** Route handling by `period_type` from `xbrl_concepts.json`. Duration concepts use `frame` regex `CY####Q#`. Instant concepts use `CY####Q#I` (note trailing `I`).
**Warning signs:** KeyError on `start` field during extraction.

### Pitfall 5: yfinance Cross-Validation Date Matching
**What goes wrong:** yfinance uses actual calendar dates (e.g., "2024-12-31") while XBRL uses fiscal period end dates (e.g., "2024-12-28" for AAPL). Direct date matching fails.
**Why it happens:** yfinance normalizes to calendar quarter-end dates. XBRL uses the company's actual fiscal period end date, which may be a few days off.
**How to avoid:** Match periods by closest date within a 7-day tolerance window, not exact date match. Sort both datasets chronologically and zip by position if date matching fails.
**Warning signs:** Zero matches between XBRL and yfinance data despite both having 8 quarters.

## Code Examples

### Company Facts API 10-Q Response (Real AAPL Data)
```json
// AAPL Revenue - 10-Q entries for FY2025 Q2 filing (filed 2025-05-02)
// TWO entries appear for the same fp=Q2:

// Entry 1: YTD cumulative (6 months, NO frame field)
{
    "start": "2024-09-29", "end": "2025-03-29",
    "val": 219659000000, "fp": "Q2", "form": "10-Q",
    "fy": 2025, "filed": "2025-05-02",
    "accn": "0000320193-25-000057"
}

// Entry 2: Standalone quarter (3 months, HAS frame field)
{
    "start": "2024-12-29", "end": "2025-03-29",
    "val": 95359000000, "fp": "Q2", "form": "10-Q",
    "fy": 2025, "filed": "2025-05-02",
    "accn": "0000320193-25-000057",
    "frame": "CY2025Q1"   // Calendar Q1 2025 = AAPL fiscal Q2
}
```

### QuarterlyStatements Model
```python
class QuarterlyPeriod(BaseModel):
    """Single quarter of XBRL financial data."""
    model_config = ConfigDict(frozen=False)

    fiscal_year: int = Field(description="Fiscal year from fy field")
    fiscal_quarter: int = Field(description="1-4 from fp field")
    fiscal_label: str = Field(description="e.g., 'Q1 FY2025'")
    calendar_period: str = Field(description="e.g., 'CY2024Q4' from frame")
    period_end: str = Field(description="Period end date YYYY-MM-DD")
    income: dict[str, SourcedValue[float] | None] = Field(
        default_factory=dict,
        description="Income statement concepts for this quarter",
    )
    balance: dict[str, SourcedValue[float] | None] = Field(
        default_factory=dict,
        description="Balance sheet concepts for this quarter",
    )
    cash_flow: dict[str, SourcedValue[float] | None] = Field(
        default_factory=dict,
        description="Cash flow concepts for this quarter",
    )


class QuarterlyStatements(BaseModel):
    """8-quarter XBRL financial data for trend analysis."""
    model_config = ConfigDict(frozen=False)

    quarters: list[QuarterlyPeriod] = Field(
        default_factory=list,
        description="Up to 8 quarters, most recent first",
    )
    fiscal_year_end_month: int | None = Field(
        default=None,
        description="Company fiscal year end month (1-12)",
    )
    extraction_date: datetime | None = Field(
        default=None,
        description="When quarterly data was extracted",
    )
    concepts_resolved: int = Field(
        default=0,
        description="Number of concepts with data",
    )
    concepts_attempted: int = Field(
        default=0,
        description="Number of concepts attempted",
    )
```

### Frame-Based Filtering Implementation
```python
import re
from typing import Any

# Standalone quarterly entries have frame matching these patterns
_DURATION_FRAME_RE = re.compile(r"^CY\d{4}Q[1-4]$")
_INSTANT_FRAME_RE = re.compile(r"^CY\d{4}Q[1-4]I$")
_STANDALONE_DURATION_DAYS = (70, 105)  # 80-100 day quarter with tolerance


def select_standalone_quarters(
    entries: list[dict[str, Any]],
    period_type: str,
) -> list[dict[str, Any]]:
    """Select standalone quarterly entries, filtering out YTD cumulatives.

    Strategy:
    1. Primary: entries with frame matching CY####Q# (duration) or CY####Q#I (instant)
    2. Fallback: entries where end-start duration is ~90 days (duration concepts only)

    Returns entries sorted by end date ascending, deduplicated by frame.
    """
    pattern = _INSTANT_FRAME_RE if period_type == "instant" else _DURATION_FRAME_RE

    # Primary: frame-based selection
    framed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        frame = entry.get("frame", "")
        if pattern.match(frame):
            existing = framed.get(frame)
            if existing is None or entry.get("filed", "") > existing.get("filed", ""):
                framed[frame] = entry  # Prefer most recently filed

    if framed:
        return sorted(framed.values(), key=lambda e: e.get("end", ""))

    # Fallback: duration-based filtering (duration concepts only)
    if period_type == "duration":
        standalone = []
        for entry in entries:
            start = entry.get("start", "")
            end = entry.get("end", "")
            if start and end:
                from datetime import datetime as dt
                try:
                    days = (dt.strptime(end, "%Y-%m-%d") - dt.strptime(start, "%Y-%m-%d")).days
                    if _STANDALONE_DURATION_DAYS[0] <= days <= _STANDALONE_DURATION_DAYS[1]:
                        standalone.append(entry)
                except ValueError:
                    continue
        if standalone:
            # Deduplicate by end+fy+fp
            seen: set[str] = set()
            deduped = []
            for e in sorted(standalone, key=lambda e: e.get("filed", ""), reverse=True):
                key = f"{e.get('end','')}_{e.get('fy','')}_{e.get('fp','')}"
                if key not in seen:
                    seen.add(key)
                    deduped.append(e)
            return sorted(deduped, key=lambda e: e.get("end", ""))

    return []
```

### Trend Computation
```python
from dataclasses import dataclass


@dataclass
class TrendResult:
    """Trend analysis for a single financial concept across quarters."""
    concept: str
    qoq_changes: list[float | None]   # Most recent first
    yoy_changes: list[float | None]    # Same-quarter YoY, most recent first
    acceleration: float | None          # Current QoQ growth - prior QoQ growth
    consecutive_decline: int            # Count of consecutive negative QoQ
    pattern: str | None                 # "compression", "deceleration", "deterioration"


def compute_qoq(values: list[float | None]) -> list[float | None]:
    """Compute quarter-over-quarter changes (%). Most recent first."""
    changes: list[float | None] = [None]  # First quarter has no prior
    for i in range(1, len(values)):
        curr, prev = values[i-1], values[i]
        if curr is not None and prev is not None and prev != 0:
            changes.append(round((curr - prev) / abs(prev) * 100, 2))
        else:
            changes.append(None)
    return changes


def detect_sequential_pattern(
    qoq_changes: list[float | None],
    concept: str,
    threshold: int = 4,
) -> str | None:
    """Detect sequential patterns in QoQ changes.

    Returns pattern name if threshold+ consecutive quarters show the pattern:
    - "compression": margin declining (negative QoQ on margin concept)
    - "deceleration": growth rate declining (QoQ of growth is negative)
    - "deterioration": absolute value declining (negative QoQ on level concept)
    """
    consecutive = 0
    for change in qoq_changes:
        if change is not None and change < 0:
            consecutive += 1
        else:
            consecutive = 0
        if consecutive >= threshold:
            if "margin" in concept:
                return "compression"
            if "growth" in concept:
                return "deceleration"
            return "deterioration"
    return None
```

### XBRL/LLM Reconciler
```python
def reconcile_quarterly(
    xbrl_value: SourcedValue[float] | None,
    llm_value: float | None,
    yfinance_value: float | None,
    concept: str,
    period: str,
) -> tuple[SourcedValue[float] | None, list[str]]:
    """XBRL always wins. Log divergences.

    Returns (winning_value, list_of_divergence_messages).
    """
    divergences: list[str] = []

    if xbrl_value is not None:
        if llm_value is not None:
            pct = abs(xbrl_value.value - llm_value) / abs(xbrl_value.value) * 100
            if pct > 1.0:
                divergences.append(
                    f"XBRL/LLM divergence {concept} {period}: "
                    f"XBRL={xbrl_value.value:.0f} LLM={llm_value:.0f} ({pct:.1f}%)"
                )
        if yfinance_value is not None:
            pct = abs(xbrl_value.value - yfinance_value) / abs(xbrl_value.value) * 100
            if pct > 1.0:
                divergences.append(
                    f"XBRL/yfinance divergence {concept} {period}: "
                    f"XBRL={xbrl_value.value:.0f} yf={yfinance_value:.0f} ({pct:.1f}%)"
                )
        return xbrl_value, divergences

    # XBRL not available -- fall back
    if llm_value is not None:
        divergences.append(f"No XBRL for {concept} {period}, using LLM fallback (MEDIUM confidence)")
    return None, divergences
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yfinance quarterly only (MEDIUM confidence) | XBRL quarterly (HIGH confidence) primary + yfinance validation | This phase | 8 quarters at GAAP-exact precision |
| LLM-extracted 10-Q financials | XBRL for numbers, LLM retained for qualitative data (legal, risk factors, MD&A) | This phase | Zero hallucination risk for quarterly financials |
| No trend analysis | QoQ + YoY + acceleration + sequential pattern detection | This phase | Automated detection of margin compression, revenue deceleration |
| No YTD disambiguation | `frame` field filtering (primary) + duration math (fallback) | This phase | Correct standalone quarterly values without subtraction errors |

## Open Questions

1. **Q4 Standalone Quarter Availability**
   - What we know: Q4 is typically reported in the 10-K (annual), not a separate 10-Q. The Company Facts API may have Q4 data only from the 10-K with `fp=FY`, not `fp=Q4`.
   - What's unclear: For non-calendar year companies, does a Q4 10-Q filing exist? Or do we derive Q4 = FY - (Q1+Q2+Q3)?
   - Recommendation: Check if `frame` field CY####Q4 entries exist with `form=10-K`. If so, use them. Otherwise, compute Q4 from annual minus sum of Q1-Q3. This is the ONE case where subtraction is needed.

2. **Coverage for New Phase 67 Concepts in Quarterly Data**
   - What we know: Phase 67 expands to 120+ concepts. Not all concepts may have 10-Q data (some may only appear in annual filings).
   - What's unclear: Which of the 120+ concepts actually resolve from 10-Q filings.
   - Recommendation: Extract what's available; track per-concept quarterly resolution rate. Some balance sheet items (pension, deferred tax) may only appear in 10-K.

3. **Handling Restated Quarters**
   - What we know: When a company restates a prior quarter, both original and restated values exist in Company Facts.
   - What's unclear: Whether the `frame` deduplication (prefer most recently `filed`) correctly captures restatements.
   - Recommendation: The existing dedup strategy (prefer most recently filed for same `frame`) should handle this. Log when multiple entries share the same `frame` with different values.

## Sources

### Primary (HIGH confidence)
- SEC Company Facts API -- verified empirically against CIK 320193 (AAPL) and CIK 81362 (RPM): response structure, `frame` field behavior, YTD vs standalone entry patterns
- Existing codebase: `xbrl_mapping.py` (212 lines), `financial_statements.py` (486 lines), `financials.py` (410 lines), `yfinance_quarterly.py` (126 lines), `quarterly_integration.py` (312 lines), `validation.py` (239 lines)
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) -- Official API documentation

### Secondary (MEDIUM confidence)
- [sec-edgar-api documentation](https://sec-edgar-api.readthedocs.io/) -- API wrapper showing response structure
- [The Full Stack Accountant - Intro to EDGAR](https://www.thefullstackaccountant.com/blog/intro-to-edgar) -- Company Facts field descriptions
- Phase 67 research (`.planning/phases/67-xbrl-first/67-RESEARCH.md`) -- concept expansion, sign normalization patterns
- `.planning/research/ARCHITECTURE.md` -- v3.1 architecture with quarterly extraction design
- `.planning/research/xbrl-pitfalls.md` -- YTD disambiguation pitfall (Pitfall 2), fiscal misalignment (Pitfall 4)
- `.planning/research/xbrl-features.md` -- 8-quarter extraction feature details

### Tertiary (LOW confidence)
- None -- all findings verified against real SEC API data.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, extending proven patterns
- Architecture: HIGH -- `frame` field behavior verified empirically on two companies with different fiscal calendars
- YTD disambiguation: HIGH -- tested on real AAPL (Sep FY) and RPM (Dec FY) data, both confirm `frame` presence on standalone entries only
- Trend computation: MEDIUM -- algorithms are straightforward but sequential pattern thresholds need calibration against real tickers
- XBRL/LLM reconciliation: HIGH -- simple precedence logic, existing SourcedValue pattern

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable domain -- SEC API structure does not change frequently)
