#!/bin/bash
# Start OCR processing in the background
# This script will process all 33,572 House Oversight PDFs

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="/Users/masa/Projects/Epstein"
VENV_DIR="$PROJECT_ROOT/.venv"
LOG_FILE="$PROJECT_ROOT/logs/ocr_house_oversight.log"
PID_FILE="$PROJECT_ROOT/logs/ocr_process.pid"

# Activate virtual environment and run OCR
cd "$PROJECT_ROOT"
source "$VENV_DIR/bin/activate"

# Start OCR processing in background
nohup python "$SCRIPT_DIR/ocr_house_oversight.py" --workers 10 --batch-size 1000 --resume >> "$LOG_FILE" 2>&1 &

# Save PID
echo $! > "$PID_FILE"

echo "OCR processing started in background"
echo "Process ID: $(cat $PID_FILE)"
echo "Log file: $LOG_FILE"
echo ""
echo "To check status:"
echo "  python scripts/extraction/check_ocr_status.py"
echo ""
echo "To view live log:"
echo "  tail -f $LOG_FILE"
echo ""
echo "To stop processing:"
echo "  kill \$(cat $PID_FILE)"
