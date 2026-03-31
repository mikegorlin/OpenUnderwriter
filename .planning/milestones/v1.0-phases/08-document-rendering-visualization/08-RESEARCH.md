# Phase 8: Document Rendering & Visualization - Research

**Researched:** 2026-02-08
**Domain:** Document generation (Word/PDF/Markdown), data visualization, design systems
**Confidence:** HIGH (core libraries verified via official docs and PyPI)

## Summary

Phase 8 transforms the complete AnalysisState (populated by Phases 1-7) into three output formats: a professionally styled Word document (primary), PDF (secondary), and Markdown (secondary), plus a meeting prep companion document. The system has 15 Pydantic model files containing all data needed for rendering across 7 worksheet sections (SECT1-SECT7), with every data point wrapped in `SourcedValue[T]` carrying source attribution and confidence levels.

The standard stack is python-docx 1.2.0 for Word generation, WeasyPrint 68.x for PDF, Jinja2 for Markdown templates, and matplotlib 3.10.x for chart generation. Charts are rendered to in-memory PNG images via BytesIO and embedded in the Word document via `add_picture()`. The critical architectural challenge is the 500-line file limit: each of the 7 worksheet sections should be its own render module, with shared utilities (design system, chart helpers, table builders) extracted into common modules.

**Primary recommendation:** Build a design system module defining all colors, fonts, and formatting constants, then implement one render module per section (7 modules), a chart generator module per visualization type, and thin format-specific orchestrators (Word, PDF, Markdown) that compose these modules.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-docx | 1.2.0 | Word (.docx) generation | Only maintained Python library for docx creation. Supports paragraphs, tables, images, headers/footers, styles. Required by OUT-01. |
| WeasyPrint | 68.x | PDF generation from HTML/CSS | Renders HTML+CSS to PDF with modern CSS support (flexbox, grid). Required by OUT-02. Requires system deps (Pango, Cairo). |
| Jinja2 | 3.1.x | Markdown template rendering | Already a transitive dependency. Required by OUT-02 for Markdown output. Also used for HTML templates fed to WeasyPrint. |
| matplotlib | 3.10.x | Chart/visualization generation | Standard Python plotting. Generates stock charts (VIS-01), pie/bar charts (VIS-02), timeline viz (VIS-03). Saved as PNG to BytesIO for embedding. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| defusedxml | (already dep) | Safe XML parsing | Already in project. Not directly needed for render. |
| mplfinance | 0.12.x | Financial chart formatting | OPTIONAL: Provides candlestick charts, OHLC. Consider if VIS-01 needs candlestick style. Standard matplotlib line charts are likely sufficient. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| WeasyPrint | reportlab | ReportLab is more mature for PDF but requires learning a different API. WeasyPrint leverages HTML/CSS skills and shares templates with Markdown. WeasyPrint has system dependencies (Pango, Cairo) but is specified in requirements. |
| WeasyPrint | fpdf2 | fpdf2 is simpler but lacks CSS-based layout. WeasyPrint is better for matching Word doc layout quality. |
| matplotlib | plotly | Plotly produces interactive HTML charts but python-docx needs static images. Matplotlib is the standard for static chart generation. |
| python-docx | docxtpl | docxtpl adds Jinja2 templating on top of python-docx. Adds abstraction but the project needs fine-grained control over formatting, conditional coloring, and XML manipulation for cell shading. Direct python-docx is better here. |

**Installation:**
```bash
uv add python-docx weasyprint matplotlib
# WeasyPrint system dependencies on macOS:
brew install pango cairo gdk-pixbuf libffi
```

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/stages/render/
    __init__.py           # RenderStage orchestrator (~200 lines)
    design_system.py      # Colors, fonts, spacing constants (~200 lines)
    docx_helpers.py       # Shared table/cell/shading helpers (~300 lines)
    chart_helpers.py      # Matplotlib figure creation utilities (~300 lines)
    word_renderer.py      # Word doc assembly orchestrator (~400 lines)
    sect1_executive.py    # Section 1: Executive Summary render (~400 lines)
    sect2_company.py      # Section 2: Company Profile render (~400 lines)
    sect3_financial.py    # Section 3: Financial Health render (~400 lines)
    sect4_market.py       # Section 4: Market & Trading render (~400 lines)
    sect5_governance.py   # Section 5: Governance render (~400 lines)
    sect6_litigation.py   # Section 6: Litigation render (~400 lines)
    sect7_scoring.py      # Section 7: Risk Scoring render (~400 lines)
    charts/
        stock_charts.py   # VIS-01: Stock price + event markers (~400 lines)
        ownership_chart.py# VIS-02: Ownership breakdown (~200 lines)
        timeline_chart.py # VIS-03: Litigation timeline (~300 lines)
    pdf_renderer.py       # PDF output via WeasyPrint (~300 lines)
    md_renderer.py        # Markdown output via Jinja2 (~300 lines)
    meeting_prep.py       # OUT-06: Meeting prep companion (~400 lines)
templates/
    markdown/
        worksheet.md.j2   # Main Markdown template
        section.md.j2     # Per-section Markdown template
    pdf/
        worksheet.html.j2 # HTML template for PDF
        styles.css        # CSS for PDF rendering
```

### Pattern 1: Section Renderer Protocol
**What:** Each section renderer is a module-level function that takes AnalysisState and a Document, appends its content, and returns nothing.
**When to use:** Every section renderer follows this pattern.
**Example:**
```python
# Source: project pattern from BenchmarkStage
from docx import Document
from do_uw.models.state import AnalysisState
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import add_styled_table, add_risk_indicator

def render_section_1(
    doc: Document,
    state: AnalysisState,
    ds: DesignSystem,
) -> None:
    """Render Executive Summary section into the Word document."""
    doc.add_heading("Section 1: Executive Summary", level=1)

    # Summary paragraph (OUT-03)
    if state.executive_summary and state.executive_summary.thesis:
        doc.add_paragraph(
            state.executive_summary.thesis.narrative,
            style="BodyText",
        )
    # ... render subsections
```

### Pattern 2: Design System as Dataclass
**What:** A frozen dataclass or module of constants defining all visual properties.
**When to use:** Every render module imports it for consistent styling.
**Example:**
```python
from dataclasses import dataclass
from docx.shared import Pt, Inches, RGBColor

@dataclass(frozen=True)
class DesignSystem:
    """Visual design constants for the D&O worksheet."""
    # Typography
    font_body: str = "Calibri"
    font_heading: str = "Calibri"
    font_mono: str = "Consolas"
    size_body: Pt = Pt(10)
    size_heading1: Pt = Pt(18)
    size_heading2: Pt = Pt(14)
    size_heading3: Pt = Pt(12)
    size_small: Pt = Pt(8)
    size_caption: Pt = Pt(9)

    # Color palette -- professional blue/navy scheme
    color_primary: RGBColor = RGBColor(0x1B, 0x3A, 0x5C)      # Dark navy
    color_secondary: RGBColor = RGBColor(0x2E, 0x75, 0xB6)     # Medium blue
    color_accent: RGBColor = RGBColor(0x4A, 0x90, 0xD9)        # Light blue
    color_text: RGBColor = RGBColor(0x33, 0x33, 0x33)          # Near-black
    color_text_light: RGBColor = RGBColor(0x66, 0x66, 0x66)    # Gray

    # Risk indicator colors
    color_risk_critical: str = "CC0000"  # Red (hex for XML)
    color_risk_high: str = "E67300"      # Orange
    color_risk_moderate: str = "FFB800"  # Amber
    color_risk_low: str = "339933"       # Green
    color_risk_neutral: str = "999999"   # Gray

    # Table colors (hex strings for XML shading)
    color_header_bg: str = "1B3A5C"      # Navy header
    color_header_text: str = "FFFFFF"    # White header text
    color_row_alt: str = "F2F6FA"        # Light blue-gray alt rows
    color_highlight_good: str = "E6F4EA" # Light green
    color_highlight_bad: str = "FCE8E6"  # Light red
    color_highlight_warn: str = "FFF3CD" # Light amber

    # Layout
    page_margin: Inches = Inches(0.75)
    chart_width: Inches = Inches(6.5)
    chart_dpi: int = 200
```

### Pattern 3: Chart to BytesIO Pipeline
**What:** Generate matplotlib charts, save to BytesIO, embed in Word doc.
**When to use:** All VIS-01 through VIS-05 chart generation.
**Example:**
```python
import io
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches

def create_stock_chart(
    dates: list,
    prices: list,
    events: list[dict],
    title: str,
) -> io.BytesIO:
    """Create stock price chart with event markers, return as BytesIO."""
    fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
    ax.plot(dates, prices, linewidth=1.5, color="#2E75B6")

    for event in events:
        ax.axvline(event["date"], color="red", alpha=0.3)
        ax.annotate(
            event["label"],
            xy=(event["date"], event["price"]),
            fontsize=7,
            rotation=45,
        )

    ax.set_title(title, fontsize=12)
    ax.set_ylabel("Price ($)")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)  # CRITICAL: prevent memory leak
    buf.seek(0)
    return buf

# Usage in section renderer:
buf = create_stock_chart(dates, prices, events, "AAPL - 1 Year")
doc.add_picture(buf, width=Inches(6.5))
```

### Pattern 4: Conditional Table Cell Shading
**What:** Apply background colors to table cells based on data values using XML manipulation.
**When to use:** VIS-04 financial tables with red/green conditional formatting.
**Example:**
```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_shading(cell, hex_color: str) -> None:
    """Set background shading color on a table cell.

    Args:
        cell: python-docx table cell object
        hex_color: 6-character hex color string (e.g., "FF0000")
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)
```

### Pattern 5: SourcedValue Citation Extraction
**What:** Extract source citations from SourcedValue fields for OUT-04 compliance.
**When to use:** Every rendered data point needs a citation.
**Example:**
```python
from do_uw.models.common import SourcedValue

def format_citation(sv: SourcedValue) -> str:
    """Format a SourcedValue's provenance as a citation string.

    Returns e.g.: "[10-K, 2025-09-28, HIGH]"
    """
    date_str = sv.as_of.strftime("%Y-%m-%d")
    return f"[{sv.source}, {date_str}, {sv.confidence.value}]"

def render_sourced_value(
    paragraph,
    sv: SourcedValue,
    ds: DesignSystem,
) -> None:
    """Render a SourcedValue with its value and superscript citation."""
    paragraph.add_run(str(sv.value))
    citation_run = paragraph.add_run(f" {format_citation(sv)}")
    citation_run.font.size = ds.size_small
    citation_run.font.color.rgb = ds.color_text_light
```

### Anti-Patterns to Avoid
- **Monolithic renderer:** Do NOT put all 7 sections in one file. Each section is 300-500 lines of render logic. Split by section.
- **Format-specific analysis:** Do NOT compute anything in render modules. All data comes from AnalysisState. The render stage is read-only on state data.
- **Hardcoded styles inline:** Do NOT scatter font sizes, colors, and spacing throughout section renderers. Use the design system module.
- **Reusing OxmlElement instances:** Each table cell needs its OWN shading element. Do not create one shading element and append it to multiple cells -- only the last cell gets it.
- **Forgetting plt.close():** Every matplotlib figure MUST be closed after saving to BytesIO. Failing to close leaks memory.
- **Mixing rendering with data extraction:** The render stage should never import from stages/acquire/ or stages/extract/. It reads from AnalysisState only.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cell background color | Custom XML string assembly | Helper function wrapping OxmlElement with proper namespace | XML namespace errors are subtle; helper ensures consistent qn() usage |
| Page numbers in footer | Static text | OxmlElement field codes (fldChar + instrText with PAGE instruction) | python-docx has no built-in page number support; the XML field approach triggers Word's auto-numbering |
| Chart image embedding | Save to temp file, embed, delete | BytesIO in-memory pipeline | No temp files to manage, no cleanup needed, faster |
| Table of contents | Manual list of sections | OxmlElement TOC field code (Word regenerates on open) | Cannot compute page numbers from python-docx; Word handles TOC on document open |
| Financial number formatting | String formatting per-call | Shared formatter functions (currency, percentage, compact notation) | Consistency across 7 sections; handles None/missing gracefully |
| Conditional formatting logic | Per-cell if/else in each section | Data-driven formatter that maps value + threshold to color | Reusable across financial tables, scoring tables, benchmark tables |
| PDF layout | Separate PDF construction logic | Shared Jinja2 HTML templates rendered by WeasyPrint | Single template source, CSS handles print styling |

**Key insight:** python-docx lacks many features you'd expect (cell shading, page numbers, TOC, borders). All of these require XML-level workarounds using OxmlElement. Centralizing these in docx_helpers.py prevents each section from reimplementing the same XML patterns.

## Common Pitfalls

### Pitfall 1: Style Must Exist in Template
**What goes wrong:** Applying a custom style name that doesn't exist in the document's style definitions produces no error but no formatting either. Word silently ignores undefined styles.
**Why it happens:** python-docx styles must be defined in the starting document or created programmatically before use.
**How to avoid:** Either (a) create a template.docx with all custom styles pre-defined and pass it to `Document("template.docx")`, or (b) create styles programmatically via `doc.styles.add_style()` before applying them. Option (b) is better for this project since the template is version-controlled as code.
**Warning signs:** Document opens but text lacks expected formatting.

### Pitfall 2: OxmlElement Reuse Across Cells
**What goes wrong:** Creating one shading element and appending it to multiple cells results in only the LAST cell being shaded.
**Why it happens:** XML elements can only have one parent. Appending moves the element, not copies it.
**How to avoid:** Create a NEW OxmlElement for each cell that needs shading. The `set_cell_shading()` helper creates a fresh element each time.
**Warning signs:** Only the last cell in a conditionally-formatted table has color.

### Pitfall 3: matplotlib Memory Leaks
**What goes wrong:** Generating 10+ charts without closing figures consumes hundreds of MB of memory.
**Why it happens:** matplotlib keeps Figure objects alive until explicitly closed. The garbage collector doesn't reliably clean them up.
**How to avoid:** Always call `plt.close(fig)` after saving to BytesIO. Use a context manager or try/finally pattern.
**Warning signs:** Process memory grows steadily during rendering; OOM on large analyses.

### Pitfall 4: WeasyPrint System Dependencies
**What goes wrong:** `uv add weasyprint` succeeds but import fails with missing library errors (Pango, Cairo, GDK-PixBuf).
**Why it happens:** WeasyPrint requires C libraries (Pango, Cairo, GDK-PixBuf) that cannot be installed via pip/uv. They must be installed via system package manager.
**How to avoid:** Document the brew install step. Consider making WeasyPrint an optional dependency (`uv add weasyprint --optional pdf`) so the system works without PDF support if deps are missing. Import WeasyPrint lazily with a clear error message.
**Warning signs:** ImportError mentioning cffi, pango, or cairo.

### Pitfall 5: Word Document File Size
**What goes wrong:** Embedding 10+ high-DPI charts produces a 50MB+ Word document.
**Why it happens:** Each 300 DPI chart at 8x4 inches is ~1MB as PNG. 15 charts = 15MB+ just in images.
**How to avoid:** Use 200 DPI (not 300) for charts embedded in Word documents -- sufficient for screen and print quality. Set figure size to match the actual display width (6.5 inches for full-width in a letter-size doc with 0.75" margins). Use tight bbox to eliminate whitespace.
**Warning signs:** Output .docx file over 10MB.

### Pitfall 6: 500-Line Limit Violations
**What goes wrong:** A section renderer grows past 500 lines as more subsections and tables are added.
**Why it happens:** Each section has multiple subsections (e.g., SECT3 has financial statements, distress scores, debt analysis, audit profile, peer group). The rendering logic for tables, conditional formatting, and narrative text adds up.
**How to avoid:** Plan splits early. The SECT3 renderer might need `sect3_financial.py` (statements + ratios) and `sect3_analysis.py` (distress + debt + audit). The design system, table helpers, and chart helpers are already factored out. If a section renderer approaches 400 lines, plan the split.
**Warning signs:** Any render module passing 350 lines.

### Pitfall 7: None/Missing Data Handling
**What goes wrong:** AnalysisState fields are Optional (e.g., `state.extracted` can be None). Rendering code crashes on None access.
**Why it happens:** Not all pipeline stages produce data for all fields. Missing data is expected.
**How to avoid:** Every section renderer must handle None gracefully. Use "Not Available" text for missing data (per CLAUDE.md: "NEVER generate, guess, or hallucinate financial data -- use 'Not Available' instead"). Pattern: `sv.value if sv is not None else "N/A"`.
**Warning signs:** AttributeError or TypeError during rendering.

### Pitfall 8: TOC Page Numbers
**What goes wrong:** TOC is added but shows no page numbers in the generated document.
**Why it happens:** python-docx cannot compute page numbers -- that requires Word's layout engine. The TOC field code tells Word to regenerate the TOC on open.
**How to avoid:** Insert a TOC field code via OxmlElement. When the document is first opened in Word, the user will be prompted to update the TOC. This is standard behavior for programmatically generated documents.
**Warning signs:** TOC shows "Error! Bookmark not defined" -- fixed when user presses "Update Table" in Word.

## Code Examples

Verified patterns from official sources:

### Creating a Document with Custom Styles
```python
# Source: python-docx 1.2.0 docs (styles-using.html)
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.style import WD_STYLE_TYPE

doc = Document()

# Create custom heading style
style = doc.styles.add_style("DOHeading1", WD_STYLE_TYPE.PARAGRAPH)
style.font.name = "Calibri"
style.font.size = Pt(18)
style.font.bold = True
style.font.color.rgb = RGBColor(0x1B, 0x3A, 0x5C)
style.paragraph_format.space_before = Pt(18)
style.paragraph_format.space_after = Pt(6)

# Use the style
doc.add_paragraph("Executive Summary", style="DOHeading1")
```

### Adding a Table with Header Shading
```python
# Source: python-docx 1.2.0 docs + GitHub issues #146, #434
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_shading(cell, hex_color: str) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

doc = Document()
table = doc.add_table(rows=3, cols=4)
table.style = "Table Grid"

# Style header row
for cell in table.rows[0].cells:
    set_cell_shading(cell, "1B3A5C")
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.bold = True
```

### Page Number in Footer via XML Field
```python
# Source: GitHub issues #498, #1297 (community workaround)
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def add_page_number(paragraph) -> None:
    """Add auto-updating page number field to a paragraph."""
    run = paragraph.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    run._element.append(fld_char_begin)

    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    run._element.append(instr_text)

    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    run._element.append(fld_char_end)

doc = Document()
section = doc.sections[0]
footer = section.footer
footer.is_linked_to_previous = False
p = footer.paragraphs[0]
p.text = "D&O Underwriting Worksheet | "
add_page_number(p)
```

### matplotlib Chart to Word Document (BytesIO)
```python
# Source: matplotlib 3.10.x docs + python-docx docs
import io
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/CLI
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches

def create_chart() -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=200)
    ax.plot([1, 2, 3, 4], [10, 20, 25, 30])
    ax.set_title("Sample Chart")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf

doc = Document()
doc.add_heading("Chart Section", level=2)
buf = create_chart()
doc.add_picture(buf, width=Inches(6.5))
doc.save("output.docx")
```

### WeasyPrint PDF from Jinja2 Template
```python
# Source: WeasyPrint 68.x docs + Jinja2 docs
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML  # type: ignore[import-untyped]

env = Environment(loader=FileSystemLoader("templates/pdf"))
template = env.get_template("worksheet.html.j2")

html_content = template.render(
    company_name="Apple Inc.",
    ticker="AAPL",
    sections=section_data,
)

HTML(string=html_content).write_pdf("output.pdf")
```

### Markdown via Jinja2
```python
# Source: Jinja2 docs
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader("templates/markdown"),
    trim_blocks=True,
    lstrip_blocks=True,
)
template = env.get_template("worksheet.md.j2")

md_content = template.render(
    state=analysis_state,
    format_currency=format_currency,
    format_pct=format_pct,
)

Path("output.md").write_text(md_content, encoding="utf-8")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-docx < 1.0 (pre-2023) | python-docx 1.2.0 | 2024 | Stable API, better type hints, maintained |
| WeasyPrint < 60 (GTK deps) | WeasyPrint 68.x (Pango/Cairo only) | 2023 | Lighter dependency chain, better CSS support |
| matplotlib.finance | mplfinance (separate pkg) | 2020 (mpl 3.0) | Candlestick/OHLC in separate package; standard line charts still in core matplotlib |
| Low-DPI charts (72/96 dpi) | 200 DPI for embedded Word charts | Current best practice | Balance of quality and file size for professional documents |

**Deprecated/outdated:**
- `matplotlib.finance` module: Removed in matplotlib 3.0, replaced by `mplfinance` package
- `python-docx` version 0.x: Superseded by 1.x with improved API
- WeasyPrint versions requiring GTK: Modern versions only need Pango/Cairo/GDK-PixBuf

## Data Model to Section Mapping

This is critical for the planner -- each section renderer needs to know which state fields to access:

| Section | State Path | Key Models |
|---------|-----------|------------|
| SECT1: Executive Summary | `state.executive_summary.*`, `state.scoring.*` | ExecutiveSummary, CompanySnapshot, InherentRiskBaseline, KeyFindings, UnderwritingThesis, ClaimProbability, TowerRecommendation |
| SECT2: Company Profile | `state.company.*` | CompanyProfile, CompanyIdentity |
| SECT3: Financial Health | `state.extracted.financials.*` | ExtractedFinancials, FinancialStatements, DistressIndicators, AuditProfile, PeerGroup |
| SECT4: Market & Trading | `state.extracted.market.*` | MarketSignals, StockPerformance, InsiderTradingProfile, ShortInterestProfile, StockDropAnalysis, EarningsGuidanceAnalysis |
| SECT5: Governance | `state.extracted.governance.*` | GovernanceData, LeadershipStability, BoardForensicProfile, CompensationAnalysis, OwnershipAnalysis, SentimentProfile |
| SECT6: Litigation | `state.extracted.litigation.*` | LitigationLandscape, CaseDetail, SECEnforcementPipeline, DefenseAssessment, IndustryClaimPattern |
| SECT7: Scoring | `state.scoring.*`, `state.analysis.*`, `state.benchmark.*` | ScoringResult, FactorScore, TierClassification, PatternMatch, RedFlagSummary, BenchmarkResult, MetricBenchmark |

### Visualizations to State Data Mapping

| Chart | State Data Source | Chart Type |
|-------|------------------|------------|
| VIS-01: Stock Price 1Y/5Y | `state.extracted.market.stock` (prices from acquired_data.market_data) | Line chart with event marker overlays |
| VIS-02: Ownership Breakdown | `state.extracted.governance.ownership` | Pie/donut chart |
| VIS-03: Litigation Timeline | `state.extracted.litigation.litigation_timeline_events` | Horizontal timeline with event markers |
| VIS-04: Financial Tables | `state.extracted.financials.statements` | Tables with conditional cell shading (not a chart) |

## Meeting Prep Companion (OUT-06)

The meeting prep document is a separate Word doc generated alongside the main worksheet. It needs:

1. **CLARIFICATION questions** -- generated from LOW confidence SourcedValue fields and missing data
2. **FORWARD_INDICATOR questions** -- generated from upcoming events (refinancing risk, SOL windows, earnings dates)
3. **GAP_FILLER questions** -- generated from None fields in the state model
4. **CREDIBILITY_TEST questions** -- generated from narrative coherence analysis, mismatches between management statements and data

Each question category maps to specific state model fields. The meeting prep generator should walk the state model and programmatically identify gaps, low-confidence items, and discrepancies.

## Testing Strategy

### Unit Tests for Render Modules
- Each section renderer gets a test file with a minimal AnalysisState fixture
- Test that the function produces a Document with expected headings, tables, and paragraphs
- Test None/missing data handling (state.extracted is None, specific fields are None)
- Do NOT test visual appearance -- test structural correctness (heading count, table dimensions, paragraph content)

### Integration Test
- Create a full AnalysisState with representative data
- Run RenderStage.run() and verify:
  - Word file is created and valid (can be opened by python-docx)
  - PDF file is created (if WeasyPrint available -- skip gracefully if not)
  - Markdown file is created and contains expected section headers
  - Meeting prep document is created

### Chart Tests
- Test chart functions return valid BytesIO objects
- Test with empty data (no events, no prices)
- Test that plt.close() is called (no open figures after chart generation)

## File Size Budget

Estimated line counts per file, enforcing the 500-line limit:

| File | Est. Lines | Risk of Overrun |
|------|-----------|-----------------|
| `__init__.py` (RenderStage) | ~150 | Low |
| `design_system.py` | ~200 | Low |
| `docx_helpers.py` | ~350 | Medium -- may need split if many XML helpers |
| `chart_helpers.py` | ~250 | Low |
| `word_renderer.py` | ~350 | Medium -- orchestrates 7 sections |
| `sect1_executive.py` | ~400 | Medium -- many subsections |
| `sect2_company.py` | ~350 | Low |
| `sect3_financial.py` | ~450 | HIGH -- financial tables + distress + audit |
| `sect4_market.py` | ~400 | Medium -- stock drops + insider + guidance |
| `sect5_governance.py` | ~400 | Medium -- leadership + board + comp |
| `sect6_litigation.py` | ~400 | Medium -- SCA + enforcement + defense |
| `sect7_scoring.py` | ~400 | Medium -- factors + patterns + tier |
| `stock_charts.py` | ~350 | Low |
| `ownership_chart.py` | ~150 | Low |
| `timeline_chart.py` | ~250 | Low |
| `pdf_renderer.py` | ~250 | Low |
| `md_renderer.py` | ~200 | Low |
| `meeting_prep.py` | ~350 | Low |

**High-risk splits:** sect3_financial.py may need to become sect3_statements.py + sect3_analysis.py if financial table rendering is complex.

## Open Questions

Things that could not be fully resolved:

1. **Stock price history data for charts**
   - What we know: VIS-01 requires 1-year and 5-year stock price charts with event markers. The ACQUIRE stage fetches stock data via yfinance and stores it in `state.acquired_data.market_data`.
   - What's unclear: The exact format of the stored price history data (daily closes, OHLC, date format). The render stage will need to parse whatever format is stored.
   - Recommendation: Read the stock acquisition client code during planning to understand the data format. If daily price history is not cached in state, the render stage may need to note this as a gap.

2. **WeasyPrint optional vs required**
   - What we know: WeasyPrint requires system dependencies (Pango, Cairo) that cannot be pip-installed. This could break CI/CD or developer setup.
   - What's unclear: Whether to make PDF output optional (graceful degradation if WeasyPrint not available) or required.
   - Recommendation: Make WeasyPrint an optional dependency. Import lazily with try/except. If unavailable, log a warning and skip PDF generation. Word and Markdown are always available.

3. **Template .docx vs programmatic styles**
   - What we know: python-docx can either start from a template.docx with pre-defined styles or create styles programmatically.
   - What's unclear: Which approach is more maintainable long-term.
   - Recommendation: Use programmatic style creation in a `setup_styles(doc)` function within design_system.py. This keeps everything in version-controlled Python code. A template.docx would be a binary file that's hard to diff and review.

4. **VIS-05 scope**
   - What we know: VIS-05 says "DETAILED VISUAL TREATMENT TO BE DETERMINED" -- it's a placeholder for a comprehensive visual design system.
   - What's unclear: Exactly which additional chart types (radar, heatmaps, waterfall) are needed.
   - Recommendation: Implement the design system (color palette, typography, conditional formatting) as part of 08-01. Defer advanced chart types (radar, heatmap) to 08-04 when the visual quality review pass happens. The 08-04 plan is explicitly for comparing against best-in-class financial reports and iterating.

5. **Markdown image embedding**
   - What we know: Markdown supports images via `![alt](path)` syntax. Charts would need to be saved as files.
   - What's unclear: Whether Markdown output should include charts or just text/tables.
   - Recommendation: Save chart images to an `images/` subdirectory alongside the Markdown file. Reference them with relative paths. This keeps Markdown self-contained.

## Sources

### Primary (HIGH confidence)
- [python-docx 1.2.0 official docs](https://python-docx.readthedocs.io/en/latest/) - Quickstart, styles, headers/footers, tables, API reference
- [python-docx PyPI](https://pypi.org/project/python-docx/) - Version 1.2.0 confirmed
- [WeasyPrint 68.x docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) - Installation, usage, system deps
- [WeasyPrint PyPI](https://pypi.org/project/weasyprint/) - Version 68.1, released 2026-02-06
- [matplotlib 3.10.x docs](https://matplotlib.org/stable/index.html) - savefig, DPI, figure sizing
- [matplotlib PyPI](https://pypi.org/project/matplotlib/) - Version 3.10.8

### Secondary (MEDIUM confidence)
- [python-docx GitHub issues #146, #434](https://github.com/python-openxml/python-docx/issues/146) - Cell shading workaround pattern
- [python-docx GitHub issues #498, #1297](https://github.com/python-openxml/python-docx/issues/498) - Page number field workaround
- [python-docx GitHub issue #36](https://github.com/python-openxml/python-docx/issues/36) - TOC field code approach
- [Office Open XML spec](http://officeopenxml.com/WPtableShading.php) - XML element reference for table shading
- [WeasyPrint + Jinja2 pattern](https://medium.com/@engineering_holistic_ai/using-weasyprint-and-jinja2-to-create-pdfs-from-html-and-css-267127454dbd) - Template-based PDF generation

### Tertiary (LOW confidence)
- [Consulting report design practices](https://www.contentbeta.com/blog/consulting-presentation/) - Design inspiration only
- [Financial typography best practices](https://www.gate39media.com/blog/design-spotlight-fonts-in-financial-services) - Font selection guidance
- [Financial consulting color palettes](https://produkto.io/color-palettes/financial-consulting) - Color scheme inspiration

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified on PyPI with current versions and official docs
- Architecture: HIGH - Patterns derived from existing project architecture (BenchmarkStage pattern, 500-line compliance, Pydantic models) and verified python-docx API
- Pitfalls: HIGH - Cell shading reuse and style existence issues confirmed via GitHub issues; WeasyPrint deps confirmed via official docs; matplotlib memory leaks well-documented
- Code examples: MEDIUM - Most patterns verified against official docs; some XML workarounds come from community patterns on GitHub issues (not official API)

**Research date:** 2026-02-08
**Valid until:** 2026-03-10 (libraries are stable; 30-day validity)
