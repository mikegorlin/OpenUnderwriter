---
created: 2026-02-27T18:30:18.871Z
title: Volume spike detection and event correlation
area: brain
files:
  - src/do_uw/brain/signals/stock/insider.yaml:200-235 (STOCK.TRADE.volume_patterns — currently display-only)
  - src/do_uw/brain/composites/stock_drop_analysis.yaml (model for new composite)
  - src/do_uw/brain/facets/market_activity.yaml:36-37 (volume_patterns facet ref)
  - src/do_uw/brain/framework/causal_chains.yaml:39 (volume_patterns as evidence in stock_drop_to_sca)
  - src/do_uw/models/market.py:73-76 (avg_daily_volume field)
  - src/do_uw/models/market.py:77-80 (single_day_events field)
---

## Problem

The brain currently treats volume as a display-only metric (`STOCK.TRADE.volume_patterns` has `work_type: extract`, `threshold: display`). It captures `avg_daily_volume` and `single_day_events` (>5% price moves) but never detects **abnormal volume spikes independent of price direction**.

Colleague insight: underwriters look at significant volume spikes to find events the market is reacting to — both positive and negative. A 5x volume day with no price drop might mean an M&A rumor, FDA approval, or contract win. These are just as important for D&O because they establish what the market believed at the time (which becomes the basis for "what should management have disclosed?").

Current gaps:
1. **No volume spike thresholds** — no red/yellow/clear evaluation on volume multiples
2. **No spike-to-news correlation** — when volume spikes, we don't search for the catalyst
3. **Drop-biased** — `single_day_events` only captures >5% price moves, misses high-volume days with small price changes (accumulation/distribution)
4. **No composite** — `stock_drop_analysis` groups drop signals but nothing groups volume anomaly signals

## Solution

### Signal changes
- Upgrade `STOCK.TRADE.volume_patterns` from `extract` to `evaluate` with tiered thresholds:
  - RED: any day with volume >5x 20-day average
  - YELLOW: any day with volume >3x 20-day average
  - CLEAR: no days exceeding 3x average
- Add new signal `STOCK.TRADE.volume_spike_events` (list of spike dates with magnitude and catalyst)

### New composite
- `COMP.STOCK.volume_spike_analysis` grouping:
  - `STOCK.TRADE.volume_patterns` (spike detection)
  - `STOCK.TRADE.volume_spike_events` (event attribution)
  - `STOCK.INSIDER.cluster_timing` (insider activity around spikes)
  - `STOCK.PRICE.single_day_events` (price moves on spike days)

### Acquisition enhancement
- For each detected volume spike: run targeted news search (Brave Search) within ±2 days of spike date
- Classify catalyst: earnings, litigation, regulatory, M&A, short report, insider activity, sector-wide, unknown
- Flag both positive and negative catalysts — positive ones establish market expectations

### Causal chain integration
- Volume spikes are already evidence in `stock_drop_to_sca` — enhance to also be evidence in other chains where market reaction matters
- Consider new chain: `volume_anomaly_to_investigation` (abnormal volume preceding material events can indicate information leakage → SEC investigation risk)

### Data model
- Add to MarketProfile: `volume_spike_events: list[SourcedValue[dict]]` with fields: date, volume, volume_multiple, price_change_pct, catalyst, catalyst_sentiment
