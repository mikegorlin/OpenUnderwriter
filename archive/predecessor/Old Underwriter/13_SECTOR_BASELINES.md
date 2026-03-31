# SECTOR BASELINE REFERENCE TABLES
## For Contextual Scoring in 10_SCORING.md

This file contains sector-specific baseline data used by F.6, F.7, F.8, F.9 contextual scoring.

---

## MARKET CAP TIERS

| Tier | Market Cap | Code |
|------|------------|------|
| Mega | >$50B | MEGA |
| Large | $10-50B | LARGE |
| Mid | $2-10B | MID |
| Small | $500M-2B | SMALL |
| Micro | <$500M | MICRO |

---

## F.6: SHORT INTEREST SECTOR BASELINES

| Sector | Typical SI Range | Elevated Threshold | Sector ETF |
|--------|------------------|-------------------|------------|
| Utilities | 2-3% | >5% | XLU |
| Consumer Staples | 2-4% | >6% | XLP |
| Financials | 2-4% | >6% | XLF |
| Industrials | 2-4% | >6% | XLI |
| Technology | 3-5% | >8% | XLK |
| Healthcare | 3-5% | >8% | XLV |
| Consumer Discretionary | 4-7% | >10% | XLY |
| Energy | 3-6% | >10% | XLE |
| REITs | 3-5% | >8% | XLRE |
| Healthcare/Biotech | 5-10% | >15% | XBI |

**Sector Average Calculation**: Use ETF short interest as proxy, or pull peer group median.

**Source**: Yahoo Finance Statistics tab, FINRA bi-monthly data

---

## F.8: VOLATILITY SECTOR BASELINES (90-Day Std Dev)

| Sector | Typical 90-Day Vol | Elevated | High | Sector ETF |
|--------|-------------------|----------|------|------------|
| Utilities | 1.0-1.5% | >2% | >3% | XLU |
| Consumer Staples | 1.0-1.5% | >2% | >3% | XLP |
| Healthcare (Pharma) | 1.5-2.5% | >3% | >5% | XLV |
| Financials | 1.5-2.5% | >3% | >5% | XLF |
| Industrials | 2.0-3.0% | >4% | >6% | XLI |
| Technology | 2.0-3.0% | >4% | >6% | XLK |
| Consumer Discretionary | 2.0-3.0% | >4% | >6% | XLY |
| Energy | 2.5-4.0% | >5% | >8% | XLE |
| REITs | 2.0-3.0% | >4% | >6% | XLRE |
| Biotech | 4.0-6.0% | >8% | >12% | XBI |
| Cannabis/Speculative | 5.0-8.0% | >10% | >15% | N/A |

**Volatility Calculation Method**:
1. Download 90 trading days of closing prices
2. Calculate daily returns: (Today - Yesterday) / Yesterday
3. STDEV of 90 daily returns = 90-day volatility

**Source**: Yahoo Finance Historical Data

---

## F.9: LEVERAGE SECTOR BASELINES (Debt/EBITDA)

| Sector | Normal Range | Elevated | Critical |
|--------|--------------|----------|----------|
| Technology | 0-2x | 2-4x | >4x |
| Healthcare | 1-3x | 3-5x | >5x |
| Consumer Discretionary | 2-3x | 3-5x | >5x |
| Consumer Staples | 2-3x | 3-5x | >5x |
| Industrials | 2-3x | 3-5x | >5x |
| Energy | 2-3x | 3-5x | >5x |
| Telecom | 3-4x | 4-6x | >6x |
| Utilities | 4-6x | 6-8x | >8x |
| REITs | 5-7x | 7-9x | >9x |
| Financials | N/A (use Debt/Equity) | 10-15x D/E | >15x D/E |

**Why It Matters**: A utility at 7x Debt/EBITDA is normal; tech at 5x is critical.

**Source**: 10-Q/10-K Balance Sheet, Debt Footnotes

---

## SECTOR ETF REFERENCE TABLE

| Sector | Primary ETF | Alternative | Description |
|--------|-------------|-------------|-------------|
| Technology | XLK | QQQ, IGV | Broad tech, IGV for software |
| Healthcare | XLV | IBB, XBI | XBI for small-cap biotech |
| Financials | XLF | KRE | KRE for regional banks |
| Industrials | XLI | â€” | Broad industrials |
| Energy | XLE | XOP | XOP for E&P specifically |
| Consumer Disc | XLY | RTH | RTH for retail |
| Consumer Staples | XLP | â€” | Defensive consumer |
| Materials | XLB | â€” | Commodities/materials |
| Utilities | XLU | â€” | Regulated utilities |
| Real Estate | XLRE | VNQ | REITs |
| Communications | XLC | â€” | Media/telecom |

---

## PEER GROUP SELECTION GUIDANCE

When sector ETF isn't sufficient, use peer groups:

### Technology Sub-Sectors
| Sub-Sector | Peer Group | Notes |
|------------|------------|-------|
| Enterprise Software | CRM, NOW, WDAY | SaaS metrics differ |
| Semiconductors | NVDA, AMD, INTC | Cyclical |
| Cloud Infrastructure | AMZN (AWS), MSFT (Azure), GOOGL | Scale matters |

### Healthcare Sub-Sectors
| Sub-Sector | Peer Group | Notes |
|------------|------------|-------|
| Large Pharma | PFE, JNJ, MRK | Mature, dividend-paying |
| Biotech | Use XBI | High volatility normal |
| Medical Devices | MDT, ABT, SYK | Mix of growth/value |

### Financials Sub-Sectors
| Sub-Sector | Peer Group | Notes |
|------------|------------|-------|
| Large Banks | JPM, BAC, WFC | Systemically important |
| Regional Banks | Use KRE | More volatile |
| Insurance | MET, PRU, AIG | Longer tail risks |
| Asset Managers | BLK, BX, KKR | AUM-driven |

---

## DATA REFRESH SCHEDULE

| Metric | Refresh Frequency | Source |
|--------|-------------------|--------|
| Short Interest | Bi-monthly | FINRA, Yahoo Finance |
| Volatility | Daily (calculate as needed) | Yahoo Finance Historical |
| Leverage Baselines | Quarterly (with earnings) | 10-Q filings |
| Sector ETF Performance | As needed | Yahoo Finance |

---

## CHANGE LOG

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-17 | Initial baseline tables | Support v4.2 contextual scoring |
| 2025-12-17 | Consolidated from 13_CONTEXT_MODIFIERS.md | Scoring logic moved to 10_SCORING.md |
