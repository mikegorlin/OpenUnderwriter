# Phase 39: Professional PDF & Visual Polish - Research

**Researched:** 2026-02-21
**Domain:** HTML/CSS PDF rendering, print layout, professional financial document design
**Confidence:** HIGH (verified against actual codebase and live Playwright testing)

## Summary

Phase 39 transforms the existing HTML-to-PDF pipeline from a functional but unpolished prototype into a Bloomberg/S&P-quality professional document. The current AAPL PDF output (12 pages, reviewed in detail) reveals specific issues: the header shows "Unknown Company" (company_name not resolving in context), excessive whitespace on pages with sparse data, no charts rendering (chart_dir issue now fixed by Phase 37), Tailwind CDN works in Playwright but introduces a network dependency that will fail in offline/CI environments, and the document lacks the information density expected of a professional underwriting report.

The core technical challenge is replacing the Tailwind CSS CDN (JavaScript-based runtime compilation) with pre-compiled static CSS while preserving all existing utility classes used across 17+ template files. The Tailwind standalone CLI (`@tailwindcss/standalone`) can scan Jinja2 `.j2` templates and output a single static CSS file, eliminating the network dependency entirely. This is the recommended approach.

Secondary challenges include: proper page break management to prevent orphaned headers and blank half-pages, consistent number formatting and right-alignment in financial tables, and ensuring charts render inline in the PDF with proper sizing.

**Primary recommendation:** Replace Tailwind CDN with a build-time CSS compilation step using the Tailwind standalone CLI, then systematically fix layout issues (page breaks, whitespace, table formatting) and verify with visual regression tests against the AAPL PDF output.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Playwright | 1.58.0 (installed) | Headless Chromium PDF generation | Already in use, verified working |
| Jinja2 | (installed) | HTML template rendering | Already in use across all templates |
| WeasyPrint | 68.1 (installed) | Fallback PDF engine | Already installed as fallback |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@tailwindcss/standalone` | v4.x | Pre-compile Tailwind CSS to static file | Build step before PDF render |
| `pytailwindcss` | 0.3.0 | Python wrapper for Tailwind standalone CLI | Alternative to direct binary download |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tailwind standalone CLI | Hand-write all CSS (no Tailwind) | Would require rewriting all 17 template files; 200+ Tailwind utility classes in use |
| Tailwind standalone CLI | Inline all styles in templates | Unmaintainable, template bloat, defeats component reuse |
| Playwright PDF | WeasyPrint-only | WeasyPrint has worse CSS grid/flexbox support, no JS execution |
| Google Fonts CDN | Self-hosted font files | Eliminates network dependency for fonts too; recommended |

## Architecture Patterns

### Current Template Structure (Preserved)
```
src/do_uw/templates/html/
  base.html.j2              # Master layout: head, header, footer, content block
  worksheet.html.j2          # Entry point: extends base, includes all sections
  styles.css                 # Custom CSS (243 lines, supplements Tailwind)
  components/                # Reusable macros: badges, tables, callouts, charts, narratives
  sections/                  # Per-section templates (8 sections)
  appendices/                # Meeting prep, coverage appendix
```

### Pattern 1: Static CSS Build Step
**What:** Pre-compile Tailwind utilities by scanning all `.j2` template files, outputting a single `compiled.css` file that replaces the CDN `<script>` tag.
**When to use:** Always -- eliminates network dependency for every PDF render.
**How it works:**
1. A build script runs `tailwindcss -i input.css -o compiled.css --content 'templates/html/**/*.j2'`
2. The `base.html.j2` template references `compiled.css` via `{% include %}` instead of CDN script
3. Build step runs once during development or as part of CI, not on every PDF render
4. The compiled CSS file is committed to the repo (it's deterministic from templates)

### Pattern 2: CSS Variable Design Tokens
**What:** All colors, sizes, and spacing defined as CSS custom properties in `:root`, referenced throughout.
**When to use:** Already partially implemented in `styles.css` with `--do-*` variables.
**Why it matters:** Enables consistent theming between HTML/PDF and makes the color system auditable. The existing `DesignSystem` dataclass has `html_*` properties that should be the single source of truth.

### Pattern 3: Print-Specific CSS Layer
**What:** A dedicated `@media print` block plus `@page` rules that control PDF-specific behavior.
**When to use:** For page margins, headers/footers, page breaks, orphan/widow control.
**Key rules:**
```css
@page {
  size: letter;
  margin: 0.75in 0.65in;
}

/* Section breaks */
section.page-break { break-before: page; }

/* Keep heading with content */
h2, h3 { break-after: avoid; }

/* Don't split tables */
table { break-inside: avoid; }
tr { break-inside: avoid; }
thead { display: table-header-group; }

/* Orphan/widow control */
p { orphans: 3; widows: 3; }
```

### Anti-Patterns to Avoid
- **CDN dependencies in PDF pipeline:** The Tailwind CDN `<script>` tag requires network access AND JavaScript execution. While it works in Playwright locally, it will fail in: (1) offline environments, (2) restricted CI, (3) slow networks where `wait_until='networkidle'` times out. Replace with static CSS.
- **Duplicate CSS logic:** The project currently has TWO CSS files (`templates/html/styles.css` at 243 lines AND `templates/pdf/styles.css` at 353 lines) plus the Tailwind CDN. The HTML renderer uses its own template chain; the WeasyPrint fallback uses different templates. Consolidate to ONE CSS system.
- **Tailwind classes for print-critical layout:** Classes like `grid-cols-3`, `gap-4`, `flex` work well on screen but can behave unpredictably in print. Use explicit CSS for any layout that MUST render correctly in PDF (tables, page breaks, margins).

## Existing Codebase Inventory (What Phase 39 Works With)

### Files That Will Be Modified
| File | Lines | Current State | Phase 39 Changes |
|------|-------|---------------|-----------------|
| `templates/html/base.html.j2` | 132 | Tailwind CDN script, Google Fonts CDN, inline styles.css | Replace CDN with compiled CSS, self-host fonts |
| `templates/html/styles.css` | 243 | Custom CSS variables, risk colors, print styles | Expand to full standalone CSS, merge with compiled Tailwind |
| `stages/render/html_renderer.py` | 374 | Playwright PDF generation with header/footer | Fix company_name resolution, improve wait strategy |
| `stages/render/pdf_renderer.py` | 173 | WeasyPrint fallback, separate template chain | Potentially unify with HTML renderer's templates |
| `stages/render/design_system.py` | 220 | DesignSystem dataclass with html_* colors | Generate CSS variables from design tokens |

### Template Files Using Tailwind Classes (All Must Work After CSS Change)
| Template | Tailwind Classes Used (sample) | Complexity |
|----------|-------------------------------|------------|
| `base.html.j2` | `bg-white`, `text-gray-900`, `px-8`, `py-5`, `flex`, `justify-between` | HIGH |
| `components/badges.html.j2` | `inline-flex`, `items-center`, `px-2`, `py-0.5`, `rounded`, `text-xs`, `font-semibold`, `bg-red-700` | HIGH |
| `components/tables.html.j2` | `w-full`, `border-collapse`, `bg-navy`, `text-white`, `grid`, `grid-cols-*` | HIGH |
| `sections/executive.html.j2` | `grid grid-cols-2`, `gap-4`, `border-l-3` | MEDIUM |
| `sections/scoring.html.j2` | `grid grid-cols-3`, `text-3xl`, `font-bold` | MEDIUM |
| `appendices/coverage.html.j2` | `grid grid-cols-4`, `text-2xl` | MEDIUM |

### Tailwind Class Inventory (Approximate)
From scanning all 17 template files, the project uses approximately:
- **Layout:** `flex`, `grid`, `grid-cols-2/3/4`, `gap-4`, `items-center`, `items-baseline`, `justify-between`, `space-y-*`
- **Spacing:** `px-*`, `py-*`, `p-*`, `m-0`, `mt-*`, `mb-*`, `ml-*`, `my-*`
- **Typography:** `text-xs`, `text-sm`, `text-lg`, `text-xl`, `text-2xl`, `text-3xl`, `font-semibold`, `font-bold`, `font-normal`, `uppercase`, `tracking-wide`, `tracking-wider`, `leading-relaxed`, `italic`, `not-italic`
- **Colors:** `bg-white`, `bg-red-*`, `bg-blue-*`, `bg-emerald-*`, `bg-amber-*`, `bg-gray-*`, `bg-slate-*`, `text-white`, `text-gray-*`, `text-red-*`, `text-blue-*`, `border-*`
- **Custom colors:** `bg-navy`, `text-navy`, `border-gold`, `bg-bg-alt`, `bg-gold-light`, `text-risk-red`, `text-risk-blue`, `text-risk-amber`
- **Sizing:** `w-full`, `max-w-none`, `min-w-0`, `max-w-[50%]`, `h-auto`, `w-[35%]`
- **Borders:** `border`, `border-b`, `border-b-2`, `border-l-3`, `border-l-4`, `border-gray-*`, `border-red-*`, `border-amber-*`, `rounded`, `rounded-r`, `rounded-md`
- **Effects:** `hover:bg-slate-100`, `transition-colors`, `shadow-sm`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSS compilation from utility classes | Manual CSS for each class | Tailwind standalone CLI | 200+ utility classes; manual CSS would be error-prone and unmaintainable |
| Font embedding | Download fonts manually, base64-encode | Google Fonts download + `@font-face` in CSS | Correct subsetting, WOFF2 format, cross-platform |
| Page break optimization | Manual `page-break-*` on every element | CSS `break-*` properties with `orphans`/`widows` | Modern CSS handles this well; Chromium respects these properties in PDF mode |
| Number formatting in tables | Custom Jinja filters for each format | `font-variant-numeric: tabular-nums` CSS property | Already partially implemented; ensures aligned decimal points without per-cell formatting |

**Key insight:** The Tailwind standalone CLI can scan `.j2` files for class names just like `.html` files. It treats any text matching Tailwind patterns as potential classes. No special Jinja2 parser needed -- it just reads the raw file content.

## Common Pitfalls

### Pitfall 1: Tailwind CDN Works Locally But Fails in Production
**What goes wrong:** The Tailwind CDN `<script src="https://cdn.tailwindcss.com">` requires: (1) network access, (2) JavaScript execution in Playwright, (3) time to download and compile. It works in development but fails in CI/offline/slow-network environments.
**Why it happens:** Playwright's `wait_until='networkidle'` waits for network to settle, but CDN compilation happens asynchronously. In constrained environments, the CDN script may not load or compile before PDF generation.
**How to avoid:** Replace CDN with pre-compiled static CSS. The compiled file is deterministic and has zero runtime dependencies.
**Warning signs:** PDF renders correctly sometimes but not others; classes don't apply in CI; `hover:` and `transition` classes compiled but useless in print.

### Pitfall 2: Page Breaks Creating Blank Half-Pages
**What goes wrong:** Every section template has `class="page-break"` which forces a page break before each section. When sections have little content (like empty litigation or AI risk), this creates nearly-blank pages.
**Why it happens:** `break-before: always` is unconditional. The PDF for AAPL has pages 6, 8, 10 that are mostly blank (only a callout or "chart not available" placeholder).
**How to avoid:** Use `break-before: page` only on major sections with substantial content. For sections with minimal content, remove forced page breaks and let content flow naturally. Consider a Jinja2 conditional: only add `page-break` class if the section has data.
**Warning signs:** 12-page PDF where 4+ pages are >70% whitespace.

### Pitfall 3: Playwright Header/Footer Template CSS Limitations
**What goes wrong:** Playwright's `header_template` and `footer_template` for `page.pdf()` operate in an isolated context. Page styles are NOT visible inside these templates. Only inline styles work.
**Why it happens:** Chromium renders headers/footers separately from the page content. They get their own minimal rendering context.
**How to avoid:** Use only inline `style=` attributes in header/footer templates. Keep them simple: company name, date, "Confidential", page numbers. The current implementation already does this correctly.
**Warning signs:** Header/footer text appears unstyled or with wrong fonts.

### Pitfall 4: Google Fonts Network Dependency
**What goes wrong:** The template loads Inter and JetBrains Mono from Google Fonts CDN. In offline or restricted environments, fonts fall back to system defaults, changing the document's appearance.
**Why it happens:** `<link href="https://fonts.googleapis.com/...">` requires network access.
**How to avoid:** Download font files (WOFF2), include them in the project's assets directory, reference via `@font-face` in CSS. The fonts are small (Inter Regular+Bold+Semibold: ~200KB, JetBrains Mono Regular: ~50KB).
**Warning signs:** Text renders in Times New Roman or Arial instead of Inter/Georgia.

### Pitfall 5: Company Name Showing "Unknown Company"
**What goes wrong:** The AAPL PDF header shows "Unknown Company (AAPL)" despite the pipeline having resolved AAPL's identity. This is visible in the screenshot.
**Why it happens:** The `company_name` variable in the template context comes from `build_template_context()` in `md_renderer.py`. If the company identity SourcedValue is not properly unwrapped (`.value` extraction), or if the AAPL state was generated before the company resolution was complete, the fallback "Unknown Company" appears.
**How to avoid:** Verify the `company_name` context variable is correctly extracted. Add a test that renders AAPL state and confirms company name appears.
**Warning signs:** Any raw `SourcedValue` objects or "Unknown Company" text in output.

### Pitfall 6: Two Separate PDF Template Systems
**What goes wrong:** The project has TWO PDF-generation paths with different templates:
1. `html_renderer.py` uses `templates/html/` (Tailwind-based, 17 files, component macros)
2. `pdf_renderer.py` uses `templates/pdf/` (WeasyPrint-specific, 3 files, plain HTML)
**Why it happens:** Historical evolution -- WeasyPrint was first, then Playwright was added with a richer template system.
**How to avoid:** The `templates/pdf/` system should be deprecated or unified. Playwright is the primary renderer; WeasyPrint is the fallback. Both should use the same HTML. The WeasyPrint fallback just needs the Tailwind CDN replaced with static CSS (which it couldn't process anyway).

## Observed Issues from AAPL PDF Review

Based on detailed review of the 12-page AAPL PDF output:

### Page 1 (Executive Summary)
- **"Unknown Company (AAPL)"** in header -- company_name not resolving
- **Sector shows "DEFAULT"** instead of "Technology" -- sector resolution issue
- **Company Snapshot shows all N/A** except Ticker -- data not flowing from state
- Grid layout (2-column) IS working (Tailwind CDN did compile)
- Page numbers and confidential header ARE working
- NO_TOUCH badge renders correctly with proper red background

### Page 2 (Executive Summary continued)
- **"VERY_HIGH"** shown raw -- needs `humanize_enum` or display formatting
- Excessive whitespace below Tower Recommendation table

### Page 3 (Company Profile)
- **All fields N/A** -- data not populating (this may be a data issue, not rendering)
- Table formatting is clean and professional
- Gap notice ("D&O Exposure Factors: Not yet extracted") renders well

### Page 4 (Financial Health)
- ELEVATED density indicator renders correctly (amber left border)
- Gap notice for Financial Statements renders well
- Distress model table has proper navy header and gold bottom border
- N/A badges in assessment column look good

### Page 5 (Market & Trading)
- **Chart placeholders** ("chart not available") -- chart_dir was None (fixed by Phase 37)
- Table formatting is consistent

### Page 6 (Market continued)
- **Mostly blank page** -- only a warning box, then whitespace. This is the page break problem.

### Page 7 (Governance)
- Subsection density indicators (5.1-5.4) all showing ELEVATED CONCERN -- visually repetitive
- Gap notices render well

### Page 8 (Litigation)
- **Almost entirely blank** -- just section header, one line, chart placeholder, then whitespace

### Page 9 (Scoring)
- 3-column grid (Quality Score / Composite / Tier) renders correctly
- AI Assessment narrative renders but shows raw `**NO_TOUCH**` markdown bold markers
- Radar chart placeholder

### Page 10 (AI Risk)
- **Almost entirely blank** -- just section header, then whitespace

### Page 11 (Meeting Prep)
- Gap badges render well (blue pills)
- Good use of space

### Page 12 (Coverage Appendix)
- 4-column grid renders correctly
- All zeros (expected for sparse state)

### Summary of Visual Issues to Fix
1. Company name / sector not resolving (data flow, not CSS)
2. Raw enum values (VERY_HIGH, **NO_TOUCH**) need display formatting
3. Forced page breaks creating blank pages (sections 6, 8, 10)
4. No charts rendering (Phase 37 fix should resolve)
5. Tailwind CDN should be replaced with static CSS for reliability
6. Google Fonts should be self-hosted for offline reliability
7. Tables need right-aligned numbers (currently left-aligned)
8. Need consistent number formatting (currency with commas, percentages with decimals)
9. Repetitive ELEVATED CONCERN indicators in governance (visual noise)
10. Raw markdown formatting leaking into narrative text

## Code Examples

### Example 1: Tailwind Standalone CSS Build
```bash
# Install pytailwindcss (wraps the standalone binary)
uv add --dev pytailwindcss

# Create input CSS with Tailwind directives
# src/do_uw/templates/html/input.css:
# @import "tailwindcss";
# @theme { --color-navy: #0B1D3A; ... }

# Build step (scans all .j2 files, outputs compiled CSS)
tailwindcss \
  -i src/do_uw/templates/html/input.css \
  -o src/do_uw/templates/html/compiled.css \
  --content 'src/do_uw/templates/html/**/*.j2' \
  --minify
```
Source: [Tailwind CLI docs](https://tailwindcss.com/docs/installation/tailwind-cli), [pytailwindcss PyPI](https://pypi.org/project/pytailwindcss/)

### Example 2: Self-Hosted Fonts via @font-face
```css
/* In compiled.css or styles.css */
@font-face {
  font-family: 'Inter';
  src: url('data:font/woff2;base64,...') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Inter';
  src: url('data:font/woff2;base64,...') format('woff2');
  font-weight: 600;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'Inter';
  src: url('data:font/woff2;base64,...') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
```
Note: For Playwright file:// rendering, fonts should be base64-embedded in the CSS or loaded from absolute paths. Relative paths from temp files won't resolve.

### Example 3: Conditional Page Breaks in Jinja2
```html
{# Only force page break if section has substantial content #}
<section id="litigation"
  {% if litigation and (litigation.cases or litigation.historical_cases) %}
    class="page-break"
  {% endif %}
>
```

### Example 4: Right-Aligned Numbers in Tables
```css
/* Financial table cells: tabular numerals + right alignment */
.tabular-nums {
  font-variant-numeric: tabular-nums;
}
.text-right {
  text-align: right;
}

/* Automatic right-alignment for cells with numeric content */
td[data-type="number"],
td[data-type="currency"],
td[data-type="percentage"] {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
```

### Example 5: Playwright PDF with Proper Wait Strategy
```python
# Current: wait_until='networkidle' -- depends on CDN
# Better: wait_until='load' with static CSS, or explicit wait for content
page.goto(f"file://{html_path}", wait_until="load")
# Optional: wait for specific element to confirm rendering
page.wait_for_selector("section#executive-summary", timeout=5000)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind CDN v4 `<script>` | Tailwind CLI standalone binary | Available now | Zero-runtime CSS, offline-compatible |
| WeasyPrint for PDF | Playwright headless Chromium | Phase 35 | Better CSS support (grid, flexbox, modern properties) |
| Google Fonts CDN | Self-hosted WOFF2 with `@font-face` | Standard practice | Offline rendering, consistent typography |
| `page-break-before: always` | `break-before: page` (modern) | CSS Fragmentation L3 | Better browser support, same effect |
| Separate PDF/HTML templates | Unified HTML templates for both renderers | This phase | Single template set, consistent output |

**Deprecated/outdated:**
- `templates/pdf/` directory (WeasyPrint-specific templates): Should be unified with `templates/html/` since Playwright is now primary
- `page-break-*` CSS properties: Replaced by `break-*` properties in modern CSS. Chromium supports both, but `break-*` is the standard.
- Tailwind CDN `<script>` approach: Works but introduces fragile network dependency

## Open Questions

1. **Should pytailwindcss be a dev dependency or runtime dependency?**
   - What we know: The CSS needs to be compiled once, then the compiled file is used at runtime. The compilation could happen during development only (committed CSS file) or at install time.
   - What's unclear: Whether the user wants to edit templates and have CSS auto-recompile, or treat compiled CSS as a build artifact.
   - Recommendation: Dev dependency only. Compiled CSS committed to repo. A `scripts/build-css.sh` for when templates change.

2. **Should the WeasyPrint fallback path be preserved?**
   - What we know: WeasyPrint is installed (v68.1), has its own template set, and serves as fallback when Playwright is unavailable. With static CSS, WeasyPrint could use the same HTML templates as Playwright.
   - What's unclear: Whether anyone actually uses the WeasyPrint path in practice.
   - Recommendation: Preserve as fallback, but unify templates. WeasyPrint can render the same static HTML/CSS that Playwright uses.

3. **How to handle the "Unknown Company" / N/A data issue?**
   - What we know: The AAPL PDF shows "Unknown Company" and many N/A values. This could be a state loading issue (stale state.json) rather than a rendering issue.
   - What's unclear: Whether Phase 38 (all data rendering) will have fixed these data flow issues before Phase 39.
   - Recommendation: Phase 39 should add defensive rendering (display whatever data exists gracefully) but not try to fix data acquisition. The company_name context variable extraction should be verified.

4. **Font licensing for self-hosting?**
   - What we know: Inter is SIL Open Font License (free for all use). JetBrains Mono is SIL Open Font License (free). Georgia is a system font (no hosting needed).
   - Recommendation: Self-host Inter and JetBrains Mono. Georgia is already available on all systems.

## Sources

### Primary (HIGH confidence)
- Codebase inspection: All files in `src/do_uw/stages/render/` and `src/do_uw/templates/html/` read and analyzed
- Live Playwright testing: Verified Tailwind CDN compiles in headless Chromium, verified PDF generation with headers/footers
- AAPL PDF output: Reviewed all 12 pages visually, cataloged specific issues
- [Tailwind CLI installation docs](https://tailwindcss.com/docs/installation/tailwind-cli) - verified standalone binary approach
- [Playwright page.pdf() docs](https://playwright.dev/docs/api/class-page) - header/footer template limitations confirmed

### Secondary (MEDIUM confidence)
- [pytailwindcss PyPI](https://pypi.org/project/pytailwindcss/) - Python wrapper for standalone CLI, verified package exists
- [Tailwind Jinja2 setup guide](https://waylonwalker.com/tailwind-and-jinja/) - confirmed CLI can scan non-HTML template files
- [Playwright PDF generation guide (BrowserStack)](https://www.browserstack.com/guide/playwright-pdf-html-generation) - page break and print CSS guidance
- [CSS page break best practices](https://www.clevago.com/blog/page-break-perfection-adding-avoiding-breaks-in-html-pdfs/) - orphan/widow handling

### Tertiary (LOW confidence)
- [Bloomberg Terminal UX design article](https://www.bloomberg.com/company/stories/how-bloomberg-terminal-ux-designers-concealed-complexity/) - design inspiration (general, not implementation-specific)
- [Bloomberg font by Matthew Carter](https://www.quora.com/What-font-is-used-in-Bloomberg-Terminal) - typography reference

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already installed and verified working
- Architecture: HIGH - Based on direct codebase analysis and working code, not theoretical patterns
- Pitfalls: HIGH - Most pitfalls observed directly in AAPL PDF output or verified via testing
- CSS compilation approach: HIGH - Tailwind CLI scanning .j2 files confirmed by official docs and community usage

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (stable domain, 30-day window appropriate)
