# Presentation Map — How Each Manifest Item Should Be Displayed

Maps every golden manifest item to its ideal visual presentation.
Used by template builders to ensure consistent, optimal display.

## Presentation Types Available

| Type | When to Use | Visual |
|---|---|---|
| `metric_card` | Single KPI with trend | Big number + emoji + sparkline |
| `metric_strip` | Row of 3-6 KPIs | Grid of metric cards |
| `risk_card` | Risk finding with evidence | Colored border + badge + bullets |
| `alert_card` | Critical notification | Prominent colored box |
| `kv_card` | Structured key-value data | Bordered table with header |
| `comparison_card` | A vs B metrics | Side-by-side with winner highlighted |
| `timeline_card` | Chronological events | Vertical dots + descriptions |
| `table_card` | Tabular data | Compact table with sorting |
| `quarterly_trend` | 8Q time series | Table with YoY + beat/miss dots + 📈📉 |
| `financial_comparison` | YoY statement comparison | Current/Prior/Change with 🟢🔴 |
| `forensic_score` | Model score with components | Score + zone badge + component bar |
| `officer_card` | Executive profile | Avatar + name + badges + flags |
| `case_card` | Litigation case | Status badge + detail pairs + theories |
| `drop_card` | Stock drop event | Date + magnitude + attribution |
| `factor_card` | Scoring factor | ID circle + bar + evidence |
| `eight_k_card` | 8-K filing event | Date + item badges + severity |
| `peer_benchmark` | Percentile ranking | Value + bar + percentile |
| `comp_card` | Compensation breakdown | Stacked bar + components + ratios |
| `narrative_card` | Prose analysis | Accent border + text block |
| `badge_row` | Status flags | Row of colored pills |
| `sparkline` | Inline trend (5-8 data points) | SVG line in 120x24 |
| `composition_bar` | Parts of whole | Stacked horizontal bar |
| `gauge` | Score 0-100 | SVG semicircle gauge |
| `heatmap` | Multi-factor intensity | Color-coded grid cells |

---

## Section 1: Decision Dashboard

| Item | Presentation | Sparkline? |
|---|---|---|
| 1.2.1 Market cap | `metric_card` (purple) | No |
| 1.2.2 Revenue | `metric_card` (green) | Yes — 5yr revenue sparkline |
| 1.2.3 Stock price | `metric_card` (orange) | Yes — 1yr price sparkline |
| 1.2.4 Employees | `metric_card` (default) | No |
| 1.3 Score badge | `gauge` + tier badge | Score bar segments |
| 1.5.1 MCap & Valuation | `kv_card` (purple) + decile dots | EV/Revenue slider |
| 1.5.2 Stock & Range | `kv_card` (orange) + range slider | No |
| 1.5.3 Revenue & Growth | `metric_card` + sparkline | Yes — 5yr revenue |
| 1.5.4 Profitability | `metric_card` + sparkline + beat dots | Yes — EBITDA + FCF |
| 1.5.5 Balance Sheet | `kv_card` + composition bar | Cash/Debt bar |
| 1.5.6 Valuation | `kv_card` (blue) | No |
| 1.6 Litigation bar | `alert_card` with agency badges | No |
| 1.7 Combo chart | Full-width SVG chart | Price + DDL + volume |
| 1.8 Key findings | `risk_card` × 5-7 | Severity dots |
| 1.9 Exec summary | `narrative_card` + `kv_card` pairs | No |
| 1.10 Quick screen | `heatmap` grid | Pass/fail cells |

## Section 2: The Company

| Item | Presentation | Sparkline? |
|---|---|---|
| 2.1.1 Business desc | `narrative_card` (navy) | No |
| 2.1.2 What company does | `narrative_card` (blue) | No |
| 2.1.3 Risk signature | `risk_card` (amber) with bullets | No |
| 2.1.4 Exchange | `badge_row` | No |
| 2.1.5 State of incorp | `badge_row` (flag Delaware) | No |
| 2.1.8 Years public | `metric_card` | No |
| 2.2.1 How money flows | Pre-formatted diagram | No |
| 2.2.2 Revenue model | `kv_card` with model type badge | No |
| 2.3.1-2 Revenue segments | `table_card` with segment bars | Yes — per-segment mini bars |
| 2.3.3 Revenue waterfall | `financial_comparison` style | Growth decomposition arrows |
| 2.3.4 Unit economics | `kv_card` (2 columns) | No |
| 2.4.1 Geographic | `table_card` + region bars | Stacked bar by region |
| 2.4.2 Customer conc | `risk_card` if concentrated | No |
| 2.4.3 Supplier conc | `risk_card` if concentrated | No |
| 2.5.1 Peer group | `table_card` | No |
| 2.5.3 Emerging risks | `table_card` with severity badges | No |
| 2.6.1 Regulatory map | `badge_row` + `kv_card` per agency | No |
| 2.7.1 Risk factors | `table_card` with severity | No |
| 2.7.2 10-K YoY delta | `timeline_card` (new/removed/changed) | No |
| 2.8.1 Subsidiaries | `metric_card` + jurisdiction breakdown | No |
| 2.8.2 Workforce | `metric_strip` (3 cards: total/domestic/intl) | No |
| 2.8.5 Key person risk | `risk_card` | No |
| 2.10.1 M&A history | `timeline_card` with deal values | No |
| 2.10.5 Event timeline | `timeline_card` (color by type) | No |

## Section 3: Stock & Market

| Item | Presentation | Sparkline? |
|---|---|---|
| 3.1.1 Stock perf | `metric_strip` (price, returns, drawdown) | No |
| 3.1.2-5 Charts | Full-width embedded SVG/PNG | Yes — full charts |
| 3.3.1-3 Stock drops | `drop_card` × N | Attribution bars |
| 3.4.1 Short interest | `metric_card` + trend direction | Yes — SI% sparkline |
| 3.5.1 Earnings track | `quarterly_trend` (8Q) | Beat/miss dots |
| 3.5.2 Analyst consensus | `comparison_card` (buy vs sell) + `kv_card` targets | No |
| 3.5.3 Quarterly detail | `quarterly_trend` (revenue + EPS) | 📈📉 per quarter |
| 3.6.1 Valuation multiples | `kv_card` (blue, 2 cols) | No |
| 3.7.1 Insider trading | `risk_card` + summary badges | No |
| 3.7.2 Insider txn table | `table_card` with type badges | No |
| 3.8.1 IPO analysis | `kv_card` + `alert_card` if recent | No |
| 3.8.2 Offerings | `timeline_card` + `alert_card` if near catalyst | No |
| 3.8.6 Dividends | `kv_card` (green) | Yes — yield sparkline |
| 3.8.7 Buybacks | `metric_card` + history bars | Yes — annual bars |
| 3.9.1-3 Sentiment/NLP | `forensic_score` style with component bars | No |
| 3.11 8-K events | `eight_k_card` × N | Severity badges |

## Section 4: Financials

| Item | Presentation | Sparkline? |
|---|---|---|
| 4.1.1 Annual comparison | `financial_comparison` (3-year) | YoY 🟢🔴 per row |
| 4.1.2 Key metrics | `kv_card` (2 cols: profitability + balance) | Yes — margin sparklines |
| 4.1.3 Quarterly trends | `quarterly_trend` (8Q, tabbed: income/balance/cash) | Per-metric trends |
| 4.2.1 Balance sheet | `financial_comparison` | YoY arrows |
| 4.3.1 Cash flow | `financial_comparison` | YoY arrows |
| 4.3.3 Capital allocation | `composition_bar` (FCF → dividends + buybacks + capex) | Stacked bar |
| 4.4.1 Debt summary | `metric_strip` (4 cards: total/ST/LT/net) | No |
| 4.4.2 Debt instruments | `table_card` (name/rate/maturity) 📋 | No |
| 4.4.3 Maturity schedule | Bar chart ($ by year) | Year bars |
| 4.4.7 Covenants | `narrative_card` or `alert_card` | No |
| 4.5 Liquidity | `metric_strip` (5 cards, risk-colored) | No |
| 4.6.1 Distress models | `forensic_score` × 4 (Altman/Beneish/Piotroski/Ohlson) | Component bars |
| 4.6.3 Earnings quality | `kv_card` with risk coloring | No |
| 4.7.1 Tax profile | `kv_card` + jurisdiction bars | Stacked bar (fed/state/foreign) |
| 4.7.3 UTB | `metric_card` (amber if large) | No |
| 4.8.1 Audit profile | `kv_card` with auditor badge | No |
| 4.8.7 Restatements | `alert_card` (red) if detected | No |
| 4.8.8 Auditor change | `alert_card` (red) if detected | No |
| 4.9 Peer benchmarks | `peer_benchmark` × N metrics | Percentile bars |

## Section 5: People & Governance

| Item | Presentation | Sparkline? |
|---|---|---|
| 5.1.1 Executives | `officer_card` × 5 | Risk badges |
| 5.1.2 People risk | `metric_card` (stability score) | No |
| 5.2.1 Board composition | `metric_strip` (size/independence/tenure/diversity) | No |
| 5.2.2 Board forensics | `officer_card` × N (director variant) | Qualification pills |
| 5.2.5 Skills matrix | Grid heatmap (directors × skills) | Filled dots |
| 5.3.1 Compensation | `comp_card` (stacked bar + components) | No |
| 5.3.4-6 ECD data | `comparison_card` (total vs actually paid) + TSR comparison | No |
| 5.4.1 Insider activity | `risk_card` with badges | No |
| 5.4.2 Insider txns | `table_card` with type badges | No |
| 5.5.1 Ownership | `table_card` (top 10 holders) + pie composition | Pie chart |
| 5.5.2 Activist risk | `alert_card` if active | No |
| 5.6.1 Governance struct | `badge_row` (pass/fail per provision) | No |

## Section 6: Litigation & Regulatory

| Item | Presentation | Sparkline? |
|---|---|---|
| 6.1.1 Active matters | `case_card` × N | Status badges |
| 6.2.1 Derivative suits | `case_card` × N (blue variant) | No |
| 6.3.1 SEC enforcement | `kv_card` + `alert_card` if active | No |
| 6.4.1 Settlement history | `table_card` with amounts | No |
| 6.4.4 SOL windows | `timeline_card` (horizontal, claim types) | Exposure bars |
| 6.5.1 Defense strength | `kv_card` with provision badges | No |
| 6.5.2 Allegation mapping | `table_card` with theory pills | No |
| 6.7.1 Litigation timeline | `timeline_card` (visual) | Colored dots |

## Section 7: Sector & Industry

| Item | Presentation | Sparkline? |
|---|---|---|
| 7.1 Sector claim profile | `metric_strip` (filing rate/dismissal/settlement) | No |
| 7.2 Competitive position | `kv_card` + `narrative_card` | No |
| 7.4.A Pipeline risk map | `table_card` (program × phase × catalyst) 🧬 | Phase progress dots |
| 7.4.A FDA calendar | `timeline_card` (PDUFA dates) | No |
| 7.4.A Cash vs catalyst | `comparison_card` (runway vs next catalyst) | Overlap visual |

## Section 8: Scoring & Underwriting

| Item | Presentation | Sparkline? |
|---|---|---|
| 8.1.1 Tier | `metric_card` (large) + gauge | Score bar |
| 8.2.1 10-Factor | `factor_card` × 10 + waterfall SVG | Factor bars |
| 8.3.1 Probability | `kv_card` with component decomposition | Component bars |
| 8.3.2 Scenarios | Tornado SVG + `table_card` | Impact bars |
| 8.3.3 Tower | `table_card` (5 layers) with pricing | Layer bars |
| 8.5 Forward scenarios | `risk_card` × N | No |
| 8.6.1 Posture | `narrative_card` (navy) | No |

## Section 9: Meeting Preparation

| Item | Presentation | Sparkline? |
|---|---|---|
| 9.1 Priority questions | Numbered cards with priority + topic badges | 🔴🟡🔵 |
| 9.2 Follow-up questions | Grouped by topic | Topic pills |

## Section 10: Audit Trail

| Item | Presentation | Sparkline? |
|---|---|---|
| All | Collapsed `<details>` sections | Standard tables |
