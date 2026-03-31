# Phase 133: Stock and Market Intelligence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 133-stock-and-market-intelligence
**Areas discussed:** Drop attribution depth, Earnings reaction table, Analyst & volume display, Data source strategy

---

## Drop Attribution Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Full event card | Per-drop card: date, magnitude, COMPANY/MARKET/SECTOR % split, catalyst, recovery days, D&O litigation theory | ✓ |
| Attribution table only | Simple table: date, drop %, market %, sector %, company-specific %, catalyst | |
| You decide | Claude picks detail level based on data availability | |

**User's choice:** Full event card
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, group consecutive | Multi-day drops consolidated into single events with per-day breakdown | ✓ |
| Show each day separately | Every >10% day is its own card | |

**User's choice:** Yes, group consecutive
**Notes:** None

---

## Earnings Reaction Table

| Option | Description | Selected |
|--------|-------------|----------|
| Full reaction analysis | Per-quarter: EPS estimate vs actual, beat/miss, revenue, day-of/next-day/1-week returns, trust assessment | ✓ |
| Compact beat/miss only | Per-quarter: date, EPS beat/miss, stock reaction. No revenue, no multi-day windows | |
| You decide | Claude picks based on data availability | |

**User's choice:** Full reaction analysis
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Pattern narrative | Short paragraph analyzing beat/miss pattern + market reaction, connected to D&O theories | ✓ |
| Simple metrics only | Beat rate %, avg miss magnitude, consecutive miss streak. Numbers only | |
| You decide | Claude determines depth based on pattern interest | |

**User's choice:** Pattern narrative
**Notes:** None

---

## Analyst & Volume Display

| Option | Description | Selected |
|--------|-------------|----------|
| Revision trend table | Rating breakdown, price target range, 30d/90d EPS revision direction | ✓ |
| Current snapshot only | Just current consensus, target, analyst count | |
| You decide | Claude picks based on data availability | |

**User's choice:** Revision trend table
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Full event cross-reference | Volume >2x days cross-referenced with 8-K filings and news by date | ✓ |
| Volume table only | List anomalous volume days with multiple, no event cross-referencing | |
| You decide | Claude determines depth based on available data | |

**User's choice:** Full event cross-reference
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated metrics card | Correlation vs sector ETF, vs SPY, R-squared, idiosyncratic risk % as standalone card | ✓ |
| Inline in stock section | Weave correlation numbers into stock chart annotations | |
| You decide | Claude picks placement | |

**User's choice:** Dedicated metrics card
**Notes:** None

---

## Data Source Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Optimize existing first | Focus on yfinance + better extraction/presentation. New sources only if gaps found | ✓ |
| Add FMP API | Financial Modeling Prep for granular earnings/analyst data | |
| Add Alpha Vantage | Earnings surprises with multi-day reactions | |

**User's choice:** Optimize existing first
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Both: surface hidden + improve visible | Find unpopulated state fields AND improve current display | ✓ |
| Surface hidden data only | Wire up state fields not shown in worksheet | |
| Improve visible only | Make current data more useful without adding new displays | |

**User's choice:** Both: surface hidden + improve visible
**Notes:** User's original directive: "Ensure to optimize all info that is there"

---

## Claude's Discretion

- Exact layout/CSS for all new displays
- Multi-day consolidation algorithm specifics
- State field audit methodology
- Placement within existing market section

## Deferred Ideas

- "Executive Brief narrative boilerplate overhaul" todo -- not stock/market specific, deferred
