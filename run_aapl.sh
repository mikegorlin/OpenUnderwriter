#!/bin/bash
# Run AAPL analysis with logging

set -e

LOG_DIR="output/AAPL-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/analysis.log"

echo "Starting AAPL analysis at $(date)" | tee -a "$LOG_FILE"
echo "Logging to: $LOG_FILE" | tee -a "$LOG_FILE"

# Run the analysis with verbose output
uv run do-uw analyze AAPL --verbose 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo "Analysis completed with exit code: $EXIT_CODE at $(date)" | tee -a "$LOG_FILE"

# Check for output files
if [[ -f "output/AAPL-$(date +%Y%m%d)/worksheet.html" ]]; then
    echo "Worksheet generated: output/AAPL-$(date +%Y%m%d)/worksheet.html" | tee -a "$LOG_FILE"
else
    echo "Warning: Worksheet not found" | tee -a "$LOG_FILE"
fi