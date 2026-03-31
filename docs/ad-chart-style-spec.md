# AD Chart Style Specification

Portable reference for reproducing the Angry Dolphin chart style in any rendering system (Python, JS, React, etc.).

## Overview

Time-series price chart with mountain fill, annotation badges, reference lines, and damage/highlight period shading. Designed for financial underwriting worksheets — dense, professional, CIQ-quality.

## Canvas & Layout

```
viewBox: "0 0 900 200"   (4.5:1 aspect ratio for full-width)
preserveAspectRatio: default (xMidYMid meet) — NEVER "none"
CSS: display: block; width: 100%;

Chart area (inside axes):
  Left margin:   35px  (Y-axis labels)
  Right margin:  30px  (breathing room)
  Top margin:    10px
  Bottom margin: 30px  (X-axis labels)
  → Plot area: x=[35, 870], y=[10, 170]
```

## Color Palette

```
Navy (primary):     #0B1D3A   — price line, text
Green (positive):   #059669   — peak markers, positive badges
Red (negative):     #B91C1C   — current/low markers, drop badges, damage shading
Background:         #f8fafc   — chart background
Grid lines:         #e2e8f0   — dashed, subtle
Axis lines:         #cbd5e1   — solid, slightly stronger
Axis labels:        #9ca3af   — gray, small
Damage period fill: #fef2f2   — very light red, semi-transparent
Mountain fill:      #0B1D3A @ 6% opacity
```

## Elements (in rendering order)

### 1. Background
```svg
<rect width="900" height="200" fill="#f8fafc" rx="4"/>
```

### 2. Highlight/Damage Period
Shaded rectangle covering the period of interest (e.g., class period, drawdown).
```svg
<rect x="{period_start_x}" y="10" width="{period_width}" height="160"
      fill="#fef2f2" rx="2"/>
```

### 3. Grid Lines (Y-axis)
5 horizontal levels (0%, 25%, 50%, 75%, 100% of price range). Dashed.
```svg
<line x1="35" y1="{y}" x2="870" y2="{y}"
      stroke="#e2e8f0" stroke-width="0.5" stroke-dasharray="2,4"/>
```

### 4. Y-Axis (Price)
Solid vertical line with tick marks and dollar labels.
```svg
<!-- Axis line -->
<line x1="35" y1="10" x2="35" y2="170" stroke="#cbd5e1" stroke-width="1"/>
<!-- Tick + label for each level -->
<line x1="32" y1="{y}" x2="35" y2="{y}" stroke="#cbd5e1" stroke-width="1"/>
<text x="30" y="{y+3}" font-size="7" fill="#9ca3af" text-anchor="end"
      font-family="system-ui, sans-serif">${price}</text>
```

### 5. X-Axis (Time)
Solid horizontal line with quarterly tick marks and YYYY-MM labels.
```svg
<!-- Axis line -->
<line x1="35" y1="170" x2="870" y2="170" stroke="#cbd5e1" stroke-width="1"/>
<!-- Quarterly ticks (~63 trading days apart) -->
<line x1="{x}" y1="170" x2="{x}" y2="173" stroke="#cbd5e1" stroke-width="1"/>
<text x="{x}" y="182" font-size="7" fill="#9ca3af" text-anchor="middle"
      font-family="system-ui, sans-serif">2024-06</text>
```

### 6. Mountain Fill (area under price line)
Polygon from first point along the price line to last point, then down to baseline.
```svg
<polygon fill="#0B1D3A" opacity="0.06"
  points="{all price points} {last_x},170 {first_x},170"/>
```

### 7. Price Line
Main data line — navy, rounded joins.
```svg
<polyline fill="none" stroke="#0B1D3A" stroke-width="1.8" stroke-linejoin="round"
  points="{x1},{y1} {x2},{y2} ..."/>
```

### 8. Reference Line (from peak)
Dashed horizontal line from peak to right edge — shows "where price was."
```svg
<line x1="{peak_x}" y1="{peak_y}" x2="870" y2="{peak_y}"
      stroke="#059669" stroke-width="0.75" stroke-dasharray="4,3" opacity="0.35"/>
```

### 9. Annotation Badges
All badges use the same pattern: rounded rect + centered white text.

**Peak badge (green):**
```svg
<circle cx="{x}" cy="{y}" r="4" fill="#059669" stroke="#fff" stroke-width="1.5"/>
<rect x="{x+6}" y="{y-14}" width="58" height="16" rx="3" fill="#059669"/>
<text x="{x+35}" y="{y-3}" font-size="9" fill="#fff" font-weight="700"
      text-anchor="middle" font-family="system-ui, sans-serif">$137.05</text>
```

**Current price badge (red):**
```svg
<circle cx="{x}" cy="{y}" r="4" fill="#B91C1C" stroke="#fff" stroke-width="1.5"/>
<rect x="{x-62}" y="{y-8}" width="56" height="16" rx="3" fill="#B91C1C"/>
<text x="{x-34}" y="{y+4}" font-size="9" fill="#fff" font-weight="700"
      text-anchor="middle" font-family="system-ui, sans-serif">$101.54</text>
```

**Drop percentage badge (red, centered on arrow):**
```svg
<rect x="{mid_x-24}" y="{mid_y-9}" width="48" height="18" rx="3" fill="#B91C1C"/>
<text x="{mid_x}" y="{mid_y+4}" font-size="10" fill="#fff" font-weight="800"
      text-anchor="middle" font-family="system-ui, sans-serif">-25.9%</text>
```

### 10. Drop Arrow
Dashed line with arrowhead from peak area to current price area.
```svg
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
          markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#B91C1C"/>
  </marker>
</defs>
<line x1="{peak_x+15}" y1="{peak_y+10}"
      x2="{current_x-10}" y2="{current_y-10}"
      stroke="#B91C1C" stroke-width="1.5" stroke-dasharray="5,3"
      marker-end="url(#arrow)"/>
```

## Coordinate Mapping

```python
def price_to_y(price, price_min, price_max, cy_min=10, cy_max=170):
    """Convert price to SVG Y coordinate (inverted — higher price = lower Y)."""
    price_range = price_max - price_min
    return cy_max - (price - price_min) / price_range * (cy_max - cy_min)

def index_to_x(idx, total_points, cx_min=35, cx_max=870):
    """Convert data index to SVG X coordinate."""
    return idx / total_points * (cx_max - cx_min) + cx_min
```

## Price Range Padding

```python
price_min = min(closes) * 0.95   # 5% padding below
price_max = max(closes) * 1.05   # 5% padding above
```

## Badge Positioning Rules

1. Peak badge: **right of dot** (+6px), above the line (-14px)
2. Current badge: **left of dot** (-62px), vertically centered on dot
3. Drop badge: centered on the midpoint of the drop arrow
4. Never overlap with axis labels — offset if needed
5. Keep labels concise — "$137.05" not "$137.05 peak" (context is obvious)

## Typography

```
Font family: system-ui, sans-serif (or Inter if available)
Axis labels: font-size 7, fill #9ca3af
Badge text:  font-size 9, fill #fff, font-weight 700
Drop badge:  font-size 10, font-weight 800
All numeric: font-variant-numeric: tabular-nums (CSS on container)
```

## Adapting to Different Contexts

| Context | viewBox | Aspect |
|---------|---------|--------|
| Full page width | 900 x 200 | 4.5:1 |
| Half page (side-by-side) | 520 x 150 | 3.5:1 |
| Compact/thumbnail | 300 x 80 | 3.75:1 |

Scale all coordinates proportionally. Keep font sizes absolute (7-10px range).

## Implementation Notes

- SVG renders inline in HTML — no external dependencies
- Works in print (add `print-color-adjust: exact` for backgrounds)
- All elements are standard SVG — compatible with any renderer (browser, Playwright, wkhtmltopdf, WeasyPrint, ReportLab)
- For React/D3: use the same coordinate system, just generate elements programmatically instead of templating
