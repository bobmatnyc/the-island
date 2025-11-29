#!/bin/bash
# Download Status Checker

LOG_DIR="/Users/masa/Projects/Epstein/logs/downloads"
PID_FILE="$LOG_DIR/download_pids.txt"

echo "=== Download Status Check ==="
echo "Time: $(date)"
echo ""

if [ ! -f "$PID_FILE" ]; then
    echo "No downloads running (PID file not found)"
    exit 0
fi

echo "Process Status:"
echo "---------------"

while IFS=: read -r name pid; do
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "✓ $name (PID: $pid) - RUNNING"
    else
        echo "✗ $name (PID: $pid) - COMPLETED/STOPPED"
    fi
done < "$PID_FILE"

echo ""
echo "Recent Log Activity:"
echo "-------------------"

for log in fbi_vault internet_archive documentcloud_extra house_oversight_sept2024; do
    log_file="$LOG_DIR/${log}.log"
    if [ -f "$log_file" ]; then
        echo ""
        echo "[$log]"
        tail -3 "$log_file" 2>/dev/null | sed 's/^/  /'
    fi
done

echo ""
echo "Storage Usage:"
echo "--------------"
du -sh /Users/masa/Projects/Epstein/data/sources/* 2>/dev/null | sort -h

echo ""
echo "File Counts:"
echo "------------"
for dir in /Users/masa/Projects/Epstein/data/sources/*/; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
        echo "$(basename "$dir"): $count PDFs"
    fi
done
