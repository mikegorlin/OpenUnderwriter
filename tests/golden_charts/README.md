# Golden Reference Gallery

Visual standards for every chart type in the D&O underwriting worksheet.
Each image represents the canonical "great" version of that chart type.

## Chart Types

### Stock Performance (stock_1y.png, stock_5y.png)
Bloomberg dark-theme area chart with company price line, sector ETF and
S&P 500 indexed overlays. Uses green/red conditional area fill.

### Drawdown (drawdown_1y.png, drawdown_5y.png)
Red area fill showing peak-to-trough drawdown with maximum drawdown
annotation. Light theme on white background.

### Volatility (volatility_1y.png, volatility_5y.png)
Rolling 30-day annualized volatility with color-coded zone boundaries
(green <20%, red >40%). Shows EWMA overlay.

### Drop Analysis (drop_analysis_1y.png)
Price line with drop event markers colored by trigger category.
Shows earnings miss and guidance cut events.

### Relative Performance (relative_1y.png)
All series indexed to 100 for direct comparison. Company vs sector ETF
with green/red fill for over/underperformance.

### Radar (radar.png)
10-factor risk profile polar chart with navy fill, gold outline.
Each spoke represents one scoring factor's risk fraction (0-100%).

### Ownership (ownership.png)
Donut chart showing institutional vs insider vs retail float.
Center text with top holder annotations.

### Timeline (timeline.png)
Horizontal timeline with litigation and corporate events color-coded
by type (filing=red, settlement=orange, regulatory=amber, etc).

### Sparklines (sparkline_up.svg, sparkline_down.svg, sparkline_flat.svg)
Inline SVG trend indicators. Green for up, red for down, gray for flat.
Area fill with 12% alpha. These are SVG, not PNG.

## Regenerating Golden References

When chart styling intentionally changes (e.g., chart_styles.yaml update):

```bash
uv run python tests/golden_charts/generate_golden_charts.py
```

Then verify visually and commit the new PNGs.

## Visual Consistency Testing

Tests in `tests/stages/render/test_chart_visual_consistency.py` compare
generated charts against these golden references using pixel-level
comparison with a configurable threshold (default: 5% RMSE tolerance).
