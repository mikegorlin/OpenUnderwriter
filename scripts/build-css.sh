#!/usr/bin/env bash
# Build compiled Tailwind CSS for D&O Underwriting Worksheet.
#
# Scans all .j2 template files via @source directive in input.css,
# outputs a single compiled.css with all used utility classes.
#
# Usage:
#   bash scripts/build-css.sh          # normal build
#   bash scripts/build-css.sh --embed  # base64-embed fonts for Playwright file:// URLs
set -euo pipefail
cd "$(dirname "$0")/.."

TEMPLATE_DIR="src/do_uw/templates/html"
INPUT_CSS="${TEMPLATE_DIR}/input.css"
OUTPUT_CSS="${TEMPLATE_DIR}/compiled.css"

echo "Building Tailwind CSS..."
echo "  Input:  ${INPUT_CSS}"
echo "  Output: ${OUTPUT_CSS}"

# Run Tailwind v4 CLI (content scanning configured via @source in input.css)
uv run tailwindcss \
  -i "${INPUT_CSS}" \
  -o "${OUTPUT_CSS}" \
  --minify

# If --embed flag passed, base64-encode font files into the CSS
# for Playwright file:// rendering compatibility.
if [[ "${1:-}" == "--embed" ]]; then
  echo "Embedding fonts as base64..."
  FONTS_DIR="${TEMPLATE_DIR}/fonts"

  for FONT_FILE in "${FONTS_DIR}"/*.woff2; do
    FONT_NAME=$(basename "$FONT_FILE")
    # Base64-encode the font file
    B64=$(base64 < "$FONT_FILE" | tr -d '\n')
    # Replace the relative URL with the base64 data URI
    sed -i '' "s|url(./fonts/${FONT_NAME})|url(data:font/woff2;base64,${B64})|g" "${OUTPUT_CSS}"
  done
  echo "Fonts embedded."
fi

# Verify output
SIZE=$(wc -c < "${OUTPUT_CSS}" | tr -d ' ')
echo "CSS compiled successfully. Output size: ${SIZE} bytes."
