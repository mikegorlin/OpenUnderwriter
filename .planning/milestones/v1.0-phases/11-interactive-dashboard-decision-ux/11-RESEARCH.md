# Phase 11: Interactive Dashboard & Decision UX - Research

**Researched:** 2026-02-09
**Domain:** Python web dashboard (FastAPI + htmx + Plotly.js)
**Confidence:** HIGH

## Summary

Phase 11 adds an interactive web dashboard as an alternative presentation layer for the same AnalysisState data that the Word/PDF/Markdown renderers already consume. The dashboard does not perform analysis -- it reads a completed `state.json` and presents it interactively with drill-down navigation, peer comparison, risk heatmaps, and interactive visualizations.

The standard approach for a Python-only team building an internal dashboard in 2026 is **FastAPI + Jinja2 + htmx + Plotly.js + DaisyUI/Tailwind CSS**. This stack requires no JavaScript framework (React/Vue/Angular), no Node.js build toolchain, and no async patterns -- it fits cleanly into the existing sync Python codebase. FastAPI already uses Pydantic (which the project uses for all models), Jinja2 is already a dependency (used for Markdown/PDF rendering), and httpx is already in the project (used for TestClient). The key insight is that htmx returns HTML fragments from server endpoints, making the entire application server-rendered Python with no client-side state management.

The existing `build_template_context()` function in `md_renderer.py` already extracts AnalysisState into simple dicts suitable for template rendering. The dashboard API layer follows this exact pattern: load state.json, extract sections into template-ready dicts, render HTML fragments via Jinja2, and let htmx swap them into the DOM.

**Primary recommendation:** Use FastAPI + htmx + Plotly.js + DaisyUI CDN. Zero JavaScript framework code. Plotly figures built server-side in Python, serialized to JSON, rendered client-side by Plotly.js. All styling via Tailwind/DaisyUI CDN (no Node.js build step). New `do-uw serve` CLI command starts the dashboard.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.128 | Web framework, API endpoints, template rendering | Already uses Pydantic; async-optional (sync defs auto-offloaded to threadpool); built-in Jinja2 support; TestClient uses httpx (already a project dep) |
| uvicorn | >=0.40 | ASGI server for FastAPI | Standard FastAPI server; programmatic `uvicorn.run()` for CLI integration |
| jinja2 | >=3.1 (already dep) | HTML templates | Already in project for Markdown/PDF rendering; reuse template patterns |
| plotly | >=6.5 | Interactive charts (radar, heatmap, scatter, bar) | Python API generates JSON specs; Plotly.js renders client-side with zoom/pan/hover; replaces static matplotlib for dashboard |
| htmx | 2.0.8 (CDN) | Server-driven interactivity | 16KB; no build step; HTML attributes drive AJAX; returns HTML fragments, not JSON |
| DaisyUI | 5 (CDN) | UI component library (cards, tabs, badges, modals) | 42KB CDN; pre-built components; Tailwind v4 based; no Node.js; Liberty Mutual branding via CSS variables |
| Tailwind CSS | 4 (CDN via @tailwindcss/browser) | Utility-first CSS | CDN-only, no build step; DaisyUI 5 requires it |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | >=0.0.7 | Form data parsing | Only if adding file upload (e.g., state.json upload) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI + htmx | Plotly Dash | Dash is higher-level but opinionated; uses React under the hood; harder to customize visuals; doesn't fit Typer CLI integration; would be a separate app rather than integrated CLI command |
| FastAPI + htmx | Streamlit | Great for prototyping but limited layout control; no drill-down navigation; server-only rerenders; doesn't suit underwriting document UX |
| FastAPI + htmx | NiceGUI | Interesting (Vue.js + FastAPI under hood) but immature ecosystem; less control over HTML structure; overkill for read-only dashboard |
| DaisyUI CDN | Manual Tailwind build | Requires Node.js/npm; adds build step complexity; CDN is sufficient for internal tool |
| Plotly.js | Chart.js / D3.js | Chart.js simpler but less interactive (no built-in zoom/pan/hover); D3.js too low-level; Plotly provides best Python API + client-side interactivity combination |

**Installation:**
```bash
uv add fastapi uvicorn plotly
```
Note: jinja2 and httpx are already project dependencies. htmx, Tailwind, DaisyUI, and Plotly.js are loaded from CDN in HTML templates -- no Python package needed for frontend.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  dashboard/              # NEW: Dashboard module
    __init__.py           # FastAPI app factory
    app.py                # FastAPI application, routes, middleware (~200L)
    state_api.py          # AnalysisState -> API response helpers (~300L)
    charts.py             # Plotly figure builders (radar, heatmap, etc.) (~400L)
    charts_financial.py   # Financial-specific Plotly charts (~300L)
    design.py             # Dashboard design tokens (CSS vars, colors) (~100L)
  templates/
    dashboard/            # NEW: Jinja2 HTML templates
      base.html           # Base layout (nav, CDN links, htmx setup)
      index.html          # Dashboard overview / executive summary
      section.html        # Generic section detail template
      partials/           # htmx fragment templates
        _summary_card.html
        _risk_gauge.html
        _factor_detail.html
        _peer_comparison.html
        _finding_detail.html
        _chart_container.html
  static/                 # NEW: Static assets
    css/
      dashboard.css       # Custom CSS (brand overrides, risk colors)
    js/
      dashboard.js        # Minimal JS: Plotly render helper (~50 lines)
```

### Pattern 1: State-to-Dashboard Data Flow
**What:** Load state.json once, extract sections on demand via htmx
**When to use:** Every dashboard page/fragment
**Example:**
```python
# Source: Existing pattern from md_renderer.py build_template_context()
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from do_uw.models.state import AnalysisState
from do_uw.pipeline import Pipeline

app = FastAPI(title="D&O Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/dashboard")

# State loaded once at startup, stored in app.state
_current_state: AnalysisState | None = None

def load_state(state_path: Path) -> AnalysisState:
    """Load AnalysisState from state.json."""
    return Pipeline.load_state(state_path)

@app.get("/", response_class=HTMLResponse)
def dashboard_index(request: Request) -> HTMLResponse:
    """Main dashboard page."""
    if _current_state is None:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"error": "No analysis loaded"},
        )
    context = build_dashboard_context(_current_state)
    return templates.TemplateResponse(
        request=request, name="index.html", context=context,
    )
```

### Pattern 2: htmx Fragment Endpoints
**What:** Return HTML fragments for drill-down navigation
**When to use:** Every interactive element (click-to-expand, tab switching)
**Example:**
```python
# Source: htmx docs pattern -- hx-get returns HTML fragment
@app.get("/api/section/{section_id}", response_class=HTMLResponse)
def get_section_detail(request: Request, section_id: str) -> HTMLResponse:
    """Return HTML fragment for a section drill-down."""
    section_data = extract_section(_current_state, section_id)
    return templates.TemplateResponse(
        request=request,
        name=f"partials/_section_{section_id}.html",
        context={"section": section_data},
    )
```

Corresponding HTML:
```html
<!-- hx-get triggers AJAX, hx-target swaps result into #detail-panel -->
<div class="card cursor-pointer"
     hx-get="/api/section/financials"
     hx-target="#detail-panel"
     hx-swap="innerHTML">
  <h3>Financial Health</h3>
  <p>Z-Score: {{ financials.z_score }}</p>
</div>
<div id="detail-panel"><!-- fragments load here --></div>
```

### Pattern 3: Plotly Figures via JSON API
**What:** Build Plotly figures in Python, serialize to JSON, render client-side
**When to use:** All interactive charts (radar, heatmap, peer comparison)
**Example:**
```python
import plotly.graph_objects as go  # type: ignore[import-untyped]
from fastapi.responses import JSONResponse

def build_risk_radar(state: AnalysisState) -> go.Figure:
    """Build interactive risk radar chart."""
    if state.scoring is None:
        return go.Figure()
    factors = state.scoring.factor_scores
    names = [f.factor_name for f in factors]
    fractions = [f.points_deducted / f.max_points for f in factors]
    fig = go.Figure(data=go.Scatterpolar(
        r=fractions, theta=names, fill="toself",
        marker=dict(color="#1A1446"),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
    )
    return fig

@app.get("/api/chart/risk-radar")
def chart_risk_radar() -> JSONResponse:
    """Return Plotly JSON for risk radar chart."""
    fig = build_risk_radar(_current_state)
    return JSONResponse(content=fig.to_dict())
```

Client-side (minimal JS, ~10 lines):
```javascript
// dashboard.js -- Plotly render helper
function loadChart(elementId, apiUrl) {
  fetch(apiUrl)
    .then(r => r.json())
    .then(spec => Plotly.newPlot(elementId, spec.data, spec.layout, {responsive: true}));
}
```

### Pattern 4: CLI Integration via `do-uw serve`
**What:** New Typer command starts the dashboard server
**When to use:** Single entry point for the dashboard
**Example:**
```python
# In cli.py or cli_dashboard.py
@app.command("serve")
def serve(
    ticker: str = typer.Argument(help="Ticker to serve dashboard for"),
    port: int = typer.Option(8000, "--port", "-p", help="Port number"),
    output: Path = typer.Option(Path("output"), "--output", "-o"),
) -> None:
    """Launch interactive dashboard for an analysis."""
    state_path = output / ticker.upper() / "state.json"
    if not state_path.exists():
        console.print(f"[red]No analysis found for {ticker}. Run 'do-uw analyze {ticker}' first.[/red]")
        raise typer.Exit(code=1)
    console.print(f"[bold]Starting dashboard for {ticker.upper()}[/bold]")
    console.print(f"[dim]Open http://localhost:{port} in your browser[/dim]")
    import uvicorn  # type: ignore[import-untyped]
    from do_uw.dashboard.app import create_app
    dashboard_app = create_app(state_path)
    uvicorn.run(dashboard_app, host="127.0.0.1", port=port, log_level="warning")
```

### Pattern 5: Liberty Mutual Brand as CSS Custom Properties
**What:** Translate DesignSystem colors to CSS variables for DaisyUI theming
**When to use:** base.html template setup
**Example:**
```html
<style>
  :root {
    /* Liberty Mutual brand -- mirrors design_system.py */
    --lm-navy: #1A1446;
    --lm-gold: #FFD000;
    --lm-text: #333333;
    --lm-text-light: #666666;

    /* Risk spectrum (NO green) */
    --risk-critical: #CC0000;
    --risk-high: #E67300;
    --risk-elevated: #FFB800;
    --risk-moderate: #4A90D9;
    --risk-neutral: #999999;

    /* Conditional formatting */
    --fmt-deteriorating: #FCE8E6;
    --fmt-caution: #FFF3CD;
    --fmt-improving: #DCEEF8;
  }
</style>
```

### Anti-Patterns to Avoid
- **Building a SPA with React/Vue:** Adds enormous complexity (build toolchain, state management, TypeScript) for an internal tool. htmx does 95% of what's needed with zero JS framework code.
- **Duplicating data extraction logic:** Reuse `build_template_context()` from md_renderer.py and existing formatters. Do not re-extract AnalysisState data in a separate way.
- **Async endpoints when unnecessary:** The codebase is sync. Use regular `def` endpoints (FastAPI auto-offloads to threadpool). No need for `async def` unless doing I/O.
- **Serving the dashboard as a separate process/service:** It should be `do-uw serve TICKER` -- integrated into the existing CLI, using the existing state.json.
- **CDN in production without fallback:** For an internal tool, CDN is fine. But bundle Plotly.js and htmx as static files if offline usage is needed later.
- **Putting dashboard code in stages/render/:** The dashboard is a new top-level module (`dashboard/`), not an extension of the RENDER stage. The RENDER stage produces documents; the dashboard is a web server.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Risk gauge / dial visualization | Custom SVG or canvas gauge | Plotly `go.Indicator` with gauge mode | Built-in gauge chart type with segments, thresholds, colors |
| Heatmap of risk factors vs. categories | HTML table with colored cells | Plotly `go.Heatmap` | Interactive hover, zoom, proper color scaling |
| Radar chart for 10-factor scoring | Custom SVG polygon | Plotly `go.Scatterpolar` | Hover tooltips, multiple traces for peer overlay |
| Tab navigation between sections | Custom JS tab switching | htmx `hx-get` + DaisyUI tabs | Zero custom JS; tabs trigger server fragment loads |
| Collapsible detail sections | Custom accordion JS | DaisyUI `collapse` component + htmx lazy loading | Pre-built accessible component |
| Data table with sorting | Custom sort implementation | HTML table + htmx sort endpoints | Server-side sorting keeps logic in Python |
| Risk badge styling | Custom CSS per risk level | DaisyUI `badge` with Tailwind color utilities | `badge badge-error`, `badge badge-warning`, `badge badge-info` |
| Form for peer selection | Custom JS multiselect | DaisyUI `select` + htmx `hx-get` on change | Submit triggers server-side recompute and fragment swap |
| Loading indicators | Custom spinner CSS | htmx `hx-indicator` attribute + DaisyUI `loading` | Built-in loading indicator support |
| Toast notifications / alerts | Custom notification system | DaisyUI `alert` component | Pre-built with status variants |

**Key insight:** htmx + DaisyUI eliminate the need for custom JavaScript in almost every UI interaction pattern. The only custom JS needed is the Plotly render helper (~10 lines).

## Common Pitfalls

### Pitfall 1: Over-Engineering the Data API
**What goes wrong:** Building a full REST API with CRUD operations, versioning, and JSON Schema when the dashboard only reads a static state.json.
**Why it happens:** Developers default to API-first thinking. But this is a read-only presentation layer for pre-computed data.
**How to avoid:** The API serves HTML fragments (htmx pattern) and Plotly JSON specs. No JSON API for data entities. The state is loaded once at startup.
**Warning signs:** If you're writing serialization logic that duplicates Pydantic's `model_dump()`, or building endpoints that look like a CRUD API.

### Pitfall 2: State Synchronization Issues
**What goes wrong:** Dashboard shows stale data because state.json was updated by a new pipeline run but the server still holds the old state in memory.
**Why it happens:** State loaded once at startup isn't refreshed.
**How to avoid:** Check file modification time on each request (cheap stat() call). Reload state if mtime changed. This is an internal tool with one user -- no caching complexity needed.
**Warning signs:** Dashboard shows different data than the Word document.

### Pitfall 3: File Size Bloat from Plotly.js
**What goes wrong:** Plotly.js is ~3.5MB (minified). Loading it on every page makes the dashboard feel slow.
**How to avoid:** Use Plotly.js CDN with the `plotly-basic` bundle (~1MB) for the chart types we need (scatter, bar, heatmap, scatterpolar, indicator). Only load the full bundle if treemaps are needed.
**Warning signs:** Dashboard takes >2s to load on first visit.

### Pitfall 4: Template File Explosion
**What goes wrong:** Creating a separate template for every piece of data results in 30+ template files that are hard to maintain.
**Why it happens:** Over-granular componentization.
**How to avoid:** Use Jinja2 macros for reusable components (risk badge, source citation, metric card). Keep templates to: 1 base, 1 index, 1 section detail, ~8-10 partials.
**Warning signs:** Template directory has more files than the Python source.

### Pitfall 5: Pyright Strict Compliance with Untyped Libraries
**What goes wrong:** FastAPI, uvicorn, and plotly are not fully typed. Pyright strict will flag many issues.
**Why it happens:** These libraries use dynamic patterns (decorators, middleware) that resist static typing.
**How to avoid:** Use `# type: ignore[import-untyped]` for plotly (same pattern as matplotlib). FastAPI is well-typed (uses Pydantic). Uvicorn needs `# type: ignore[import-untyped]`. Use `Any` typing for template response objects (same pattern as python-docx in word_renderer.py).
**Warning signs:** Spending hours trying to satisfy pyright on FastAPI middleware or Plotly figure objects.

### Pitfall 6: 500-Line File Limit
**What goes wrong:** Dashboard app.py grows beyond 500 lines as routes accumulate.
**Why it happens:** All routes in one file.
**How to avoid:** Split from the start: `app.py` (app factory + middleware), `state_api.py` (state extraction helpers), `charts.py` (Plotly figure builders), `charts_financial.py` (financial chart builders). Each under 500 lines. Use FastAPI `APIRouter` for route grouping if needed.
**Warning signs:** Any file approaching 400 lines.

### Pitfall 7: Mixing Dashboard Logic with Pipeline Logic
**What goes wrong:** Dashboard code imports from stages/ or modifies AnalysisState.
**Why it happens:** Temptation to add "just one more analysis" to the dashboard.
**How to avoid:** Dashboard is read-only. It imports from `models/` and `stages/render/formatters.py` only. Never imports from `stages/acquire/`, `stages/analyze/`, etc. Never writes to state.
**Warning signs:** Import paths going into `stages/` other than `stages/render/formatters.py` or `stages/render/design_system.py`.

## Code Examples

Verified patterns from official sources:

### FastAPI App Factory Pattern
```python
# Source: FastAPI docs -- application factory for testability
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

def create_app(state_path: Path) -> FastAPI:
    """Create dashboard FastAPI app with state loaded."""
    from do_uw.pipeline import Pipeline

    app = FastAPI(title="D&O Underwriting Dashboard")
    state = Pipeline.load_state(state_path)
    app.state.analysis_state = state  # type: ignore[attr-defined]
    app.state.state_path = state_path  # type: ignore[attr-defined]

    # Templates and static files
    template_dir = Path(__file__).parent.parent / "templates" / "dashboard"
    static_dir = Path(__file__).parent.parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    templates = Jinja2Templates(directory=str(template_dir))
    app.state.templates = templates  # type: ignore[attr-defined]

    # Register routes
    from do_uw.dashboard.routes import register_routes
    register_routes(app)

    return app
```

### Reusing Existing Formatters
```python
# Source: Existing md_renderer.py pattern
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
    na_if_none,
)
from do_uw.stages.render.md_renderer import build_template_context

def build_dashboard_context(state: AnalysisState) -> dict[str, Any]:
    """Extend the existing template context for dashboard use."""
    # Reuse the proven extraction logic
    base_context = build_template_context(state)
    # Add dashboard-specific keys
    base_context["sections"] = _build_section_nav(state)
    base_context["risk_level_class"] = _tier_to_css_class(state)
    return base_context
```

### htmx Drill-Down with Jinja2
```html
{# Source: htmx.org + DaisyUI docs #}
{% macro risk_card(title, level, score, section_id) %}
<div class="card bg-base-100 shadow-md hover:shadow-lg cursor-pointer"
     hx-get="/api/section/{{ section_id }}"
     hx-target="#detail-panel"
     hx-swap="innerHTML"
     hx-indicator="#loading-spinner">
  <div class="card-body p-4">
    <h3 class="card-title text-sm" style="color: var(--lm-navy);">{{ title }}</h3>
    <div class="badge {{ 'badge-error' if level == 'CRITICAL' else 'badge-warning' if level in ('HIGH', 'ELEVATED') else 'badge-info' }}">
      {{ level }}
    </div>
    <p class="text-2xl font-bold">{{ score }}</p>
  </div>
</div>
{% endmacro %}
```

### Plotly Heatmap for Risk Factor Matrix
```python
import plotly.graph_objects as go  # type: ignore[import-untyped]

def build_risk_heatmap(state: AnalysisState) -> go.Figure:
    """Build interactive risk factor heatmap."""
    if state.scoring is None:
        return go.Figure()
    factors = state.scoring.factor_scores
    names = [f.factor_name for f in factors]
    scores = [f.points_deducted for f in factors]
    max_pts = [f.max_points for f in factors]
    fractions = [s / m if m > 0 else 0 for s, m in zip(scores, max_pts)]

    fig = go.Figure(data=go.Heatmap(
        z=[fractions],
        x=names,
        y=["Risk Level"],
        colorscale=[
            [0.0, "#4A90D9"],     # Moderate (blue)
            [0.5, "#FFB800"],     # Elevated (amber)
            [0.75, "#E67300"],    # High (orange)
            [1.0, "#CC0000"],     # Critical (red)
        ],
        hovertemplate="%{x}: %{z:.0%}<extra></extra>",
    ))
    fig.update_layout(
        height=120, margin=dict(l=0, r=0, t=0, b=40),
    )
    return fig
```

### TestClient Testing (sync, no async)
```python
# Source: FastAPI docs -- TestClient for testing
from fastapi.testclient import TestClient
from do_uw.dashboard.app import create_app

def test_dashboard_index(tmp_path: Path) -> None:
    """Dashboard index loads with valid state."""
    state_path = _write_test_state(tmp_path)
    app = create_app(state_path)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "D&O Underwriting" in response.text

def test_section_drill_down(tmp_path: Path) -> None:
    """Section drill-down returns HTML fragment."""
    state_path = _write_test_state(tmp_path)
    app = create_app(state_path)
    client = TestClient(app)
    response = client.get("/api/section/financials")
    assert response.status_code == 200
    assert "Financial Health" in response.text

def test_chart_api_returns_plotly_json(tmp_path: Path) -> None:
    """Chart endpoint returns valid Plotly figure spec."""
    state_path = _write_test_state(tmp_path)
    app = create_app(state_path)
    client = TestClient(app)
    response = client.get("/api/chart/risk-radar")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "layout" in data
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Plotly Dash for Python dashboards | FastAPI + htmx for server-rendered dashboards | 2024-2025 | No React dependency, simpler architecture, fits CLI integration |
| Custom JavaScript for interactivity | htmx 2.0 HTML attributes | 2024 (htmx 2.0 released) | 67% less code vs React implementations |
| Tailwind CSS via Node.js/npm | Tailwind CSS v4 CDN (`@tailwindcss/browser`) | 2025 (v4 release) | No build step needed for development |
| DaisyUI v3 (Tailwind v3) | DaisyUI v5 (Tailwind v4, CSS-only config) | 2025-2026 | Smaller (34KB compressed), no JS required, CSS variable theming |
| matplotlib for static charts | Plotly.js for interactive web charts | Plotly 6.x (2025) | Zoom, pan, hover, drill-down impossible with static images |
| Full REST API for dashboards | Hypermedia-driven (return HTML, not JSON) | 2024-2025 (htmx movement) | Eliminates client-side state management |

**Deprecated/outdated:**
- Plotly Dash callbacks: Still works but adds React complexity. FastAPI + htmx is simpler for internal tools.
- Streamlit: Good for prototypes but limited for structured navigation UX like underwriting workflows.
- Flask for new projects: FastAPI superseded Flask for Python web projects requiring Pydantic integration.

## Open Questions

Things that couldn't be fully resolved:

1. **Plotly.js bundle size vs. chart types needed**
   - What we know: Full bundle is 3.5MB. Basic bundle (~1MB) covers scatter, bar, heatmap, scatterpolar.
   - What's unclear: Whether `go.Indicator` (gauge) is in the basic bundle or requires full.
   - Recommendation: Start with basic bundle. If gauge charts fail, switch to full bundle. For internal tool, load time is acceptable either way.

2. **Plotly.js pyright typing**
   - What we know: Plotly Python is `import-untyped` under pyright strict (same as matplotlib).
   - What's unclear: Whether plotly 6.5+ has improved type stubs.
   - Recommendation: Use `# type: ignore[import-untyped]` and `cast()` patterns, same as existing matplotlib usage. Type plotly figure objects as `Any`.

3. **DaisyUI theme customization for Liberty Mutual branding**
   - What we know: DaisyUI v5 supports CSS variable theming and custom themes via `@plugin`.
   - What's unclear: Exact override mechanism when using CDN-only (no build step).
   - Recommendation: Use CSS custom properties (`:root` variables) to override DaisyUI defaults. If insufficient, define a custom DaisyUI theme in a small CSS file. The brand colors (#1A1446, #FFD000) should map to DaisyUI's `--p` (primary) and `--a` (accent) variables.

4. **State file size for large analyses**
   - What we know: Empty state is 1.1KB. Real analysis (AAPL) state.json is ~2KB (stub data). Full analysis with all sections could be much larger.
   - What's unclear: State size after complete AAPL analysis with all extractors.
   - Recommendation: Load state.json into memory at startup (likely <5MB even for large analyses). This is an internal tool for one company at a time.

## Sources

### Primary (HIGH confidence)
- FastAPI official docs (https://fastapi.tiangolo.com/advanced/templates/) - Template setup, static files, TestClient
- FastAPI PyPI (https://pypi.org/project/fastapi/) - Version 0.128.6, Python >=3.9
- htmx.org (https://htmx.org) - Version 2.0.8, 16KB, feature list
- Plotly PyPI (https://pypi.org/project/plotly/) - Version 6.5.2, Python >=3.8
- DaisyUI official docs (https://daisyui.com/docs/cdn/) - CDN setup, v5, 42KB
- Uvicorn PyPI (https://pypi.org/project/uvicorn/) - Version 0.40.0
- pytailwindcss PyPI (https://pypi.org/project/pytailwindcss/) - Version 0.3.0, no Node.js
- Existing codebase: `md_renderer.py` build_template_context(), `design_system.py` colors, `formatters.py` utilities, `word_renderer.py` section dispatch

### Secondary (MEDIUM confidence)
- FastAPI + htmx + DaisyUI guide (https://sunscrapers.com/blog/modern-web-dev-fastapi-htmx-daisyui/) - Architecture patterns
- TestDriven.io FastAPI + htmx tutorial (https://testdriven.io/blog/fastapi-htmx/) - Fragment return pattern, HX-Request header
- Plotly radar chart docs (https://plotly.com/python/radar-chart/) - go.Scatterpolar usage
- Plotly heatmap docs (https://plotly.com/python/heatmaps/) - go.Heatmap usage

### Tertiary (LOW confidence)
- Medium articles on FastAPI + htmx dashboards - General patterns confirmed with official sources
- htmx post-mortem (https://dev.to/kike/speeding-up-saas-shipping-htmx-in-production-a-post-mortem-5bb9) - 70% code reduction claim (unverified with our codebase)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via official PyPI/docs; version numbers confirmed; compatibility with Python 3.12+ confirmed; FastAPI already uses Pydantic (project's model framework)
- Architecture: HIGH - Patterns verified against official docs and existing codebase (build_template_context pattern); htmx fragment pattern confirmed in official docs
- Pitfalls: MEDIUM - Based on common patterns from multiple sources and project-specific constraints (500-line limit, pyright strict, sync codebase); some pitfalls extrapolated from similar projects

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (30 days -- stable technology stack, no rapid changes expected)
