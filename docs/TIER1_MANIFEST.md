# Tier 1 Data Manifest

## Two-Tier Acquisition Model

Every piece of data in the D&O Underwriting system is traceable to one of two tiers:

**Tier 1 -- Foundational Batch:** A defined, documented manifest of data we always pull and compute for every company. Includes raw data (XBRL financials, SEC filings, stock prices, litigation searches, news sweeps) and standard derivations (financial ratios, Beneish components, trend computations, forensic metrics). Rationale: "An underwriter always needs this on the desk." The manifest is explicit and finite.

**Tier 2 -- Signal-Driven Acquisition:** When a brain signal needs data NOT already in the Tier 1 manifest, its `acquisition` block triggers additional pulls. If Tier 1 already staged the data, the signal just references it via `data_strategy.field_key`.

**The Rule:** Every piece of data is traceable to either "it's on the Tier 1 manifest" or "signal X requested it." No orphaned computation.

## Foundational Signal Traceability

Each Tier 1 data source has a corresponding foundational signal (`type: foundational`) in `brain/signals/base/`. These signals are NOT evaluated by the signal engine -- they serve as the explicit manifest for what the ACQUIRE stage always pulls.

### Filings (`brain/signals/base/filings.yaml`)

| Data Source | Signal ID | Fields | Description |
|---|---|---|---|
| 10-K Annual Report | `BASE.FILING.10K` | `acquired_data.filings.annual`, `extracted.financials`, `extracted.risk_factors`, `extracted.text_signals` | Most recent 10-K: XBRL financials, risk factors, MD&A, Item 3, auditor opinion |
| 10-Q Quarterly Report | `BASE.FILING.10Q` | `acquired_data.filings.quarterly`, `extracted.financials.quarterly_periods` | Recent 10-Q reports (up to 8 quarters) for quarterly XBRL and trends |
| DEF 14A Proxy Statement | `BASE.FILING.DEF14A` | `extracted.governance.board`, `extracted.governance.leadership`, `extracted.governance.compensation`, `extracted.governance.comp_analysis` | Board composition, executive compensation, say-on-pay, shareholder proposals |
| 8-K Current Report | `BASE.FILING.8K` | `acquired_data.filings.current_reports` | Material events: exec departures, auditor changes, restatements, M&A |

### Market Data (`brain/signals/base/market.yaml`)

| Data Source | Signal ID | Fields | Description |
|---|---|---|---|
| Stock Price & Trading | `BASE.MARKET.stock_price` | `extracted.market.stock`, `.current_price`, `.high_52w`, `.low_52w`, `.decline_from_high_pct`, `.pe_ratio`, `.beta` | Stock price, returns, volume, volatility from yfinance |
| Institutional Ownership | `BASE.MARKET.institutional` | `extracted.market.ownership.institutional_pct`, `.top_holders`, `extracted.market.short_interest` | Institutional ownership %, top holders, short interest |
| Insider Trading | `BASE.MARKET.insider_trading` | `extracted.market.insider_analysis.transactions`, `.cluster_events`, `.pct_10b5_1` | Form 4 insider buy/sell, cluster detection, 10b5-1 plan coverage |

### XBRL Financial Data (`brain/signals/base/xbrl.yaml`)

| Data Source | Signal ID | Fields | Description |
|---|---|---|---|
| Balance Sheet | `BASE.XBRL.balance_sheet` | `extracted.financials.statements.balance_sheet` | Annual XBRL balance sheet: assets, liabilities, equity |
| Income Statement | `BASE.XBRL.income_statement` | `extracted.financials.statements.income_statement` | Annual XBRL income statement: revenue, COGS, operating/net income, EPS |
| Cash Flow Statement | `BASE.XBRL.cash_flow` | `extracted.financials.statements.cash_flow` | Annual XBRL cash flow: operating, investing, financing |
| Quarterly Financials | `BASE.XBRL.quarterly` | `extracted.financials.quarterly_periods` | 8-quarter XBRL data for QoQ/YoY trends and seasonal patterns |
| Derived Metrics | `BASE.XBRL.derived` | `extracted.financials.liquidity`, `.leverage`, `.profitability`, `.distress`, `.earnings_quality` | Ratios, Altman Z, Beneish M-Score, Piotroski F-Score |

### Forensic Analysis (`brain/signals/base/forensics.yaml`)

| Data Source | Signal ID | Fields | Description |
|---|---|---|---|
| Balance Sheet Forensics | `BASE.FORENSIC.balance_sheet` | `analysis.xbrl_forensics.balance_sheet.*` | Goodwill impairment, intangible concentration, off-balance-sheet, CCC, WC volatility |
| Revenue Quality | `BASE.FORENSIC.revenue` | `analysis.xbrl_forensics.revenue.*` | Deferred revenue divergence, channel stuffing, margin compression, OCF ratio |
| Capital Allocation | `BASE.FORENSIC.capital_alloc` | `analysis.xbrl_forensics.capital_allocation.*` | ROIC trend, acquisition effectiveness, buyback timing, dividend sustainability |
| Debt & Tax | `BASE.FORENSIC.debt_tax` | `analysis.xbrl_forensics.debt_tax.*` | Interest coverage trend, debt maturity, ETR anomaly, deferred tax, pension |
| Beneish M-Score | `BASE.FORENSIC.beneish` | `analysis.xbrl_forensics.beneish.*` | 8 individual M-Score components (DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI) + composite |
| Earnings Quality | `BASE.FORENSIC.earnings` | `analysis.xbrl_forensics.earnings_quality.*` | Sloan accruals, cash flow manipulation, SBC dilution, non-GAAP gap |
| M&A Forensics | `BASE.FORENSIC.ma` | `analysis.xbrl_forensics.ma_forensics.*` | Serial acquirer flag, goodwill growth rate, acquisition-to-revenue ratio |

### Litigation (`brain/signals/base/litigation.yaml`)

| Data Source | Signal ID | Fields | Description |
|---|---|---|---|
| Stanford SCAC | `BASE.LIT.scac` | `extracted.litigation.securities_class_actions`, `.sca_summary` | Securities class action search (active + historical) |
| 10-K Item 3 | `BASE.LIT.10k_item3` | `extracted.litigation.other_legal_matters`, `.contingent_liabilities` | Legal proceedings from 10-K filings, LLM-extracted |
| CourtListener | `BASE.LIT.courtlistener` | `extracted.litigation.federal_dockets` | RECAP docket search for federal court cases |

### News & Sentiment (`brain/signals/base/news.yaml`)

| Data Source | Signal ID | Fields | Description |
|---|---|---|---|
| Pre-Acquisition Blind Spot | `BASE.NEWS.blind_spot_pre` | `acquired_data.news.blind_spot_pre` | Risk term searches at START of ACQUIRE: short seller reports, AG actions, employee lawsuits |
| Post-Acquisition Blind Spot | `BASE.NEWS.blind_spot_post` | `acquired_data.news.blind_spot_post` | Exploratory search targeting gaps found after structured acquisition |
| Company News | `BASE.NEWS.company_news` | `extracted.sentiment`, `acquired_data.news.general` | General company news and sentiment via Brave Search |

### Peer Benchmarking (`brain/signals/base/peer.yaml`)

| Data Source | Signal ID | Fields | Description |
|---|---|---|---|
| SEC Frames API | `BASE.PEER.frames` | `analyzed.benchmarks.frames_percentiles`, `.sector_percentiles` | Cross-filer percentile ranking via SEC Frames API for 10+ key metrics |

## Summary

| Category | File | Signal Count |
|---|---|---|
| Filings | `base/filings.yaml` | 4 |
| Market | `base/market.yaml` | 3 |
| XBRL | `base/xbrl.yaml` | 5 |
| Forensics | `base/forensics.yaml` | 7 |
| Litigation | `base/litigation.yaml` | 3 |
| News | `base/news.yaml` | 3 |
| Peer | `base/peer.yaml` | 1 |
| **Total** | **7 files** | **26** |
