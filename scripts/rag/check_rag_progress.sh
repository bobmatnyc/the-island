#!/bin/bash
# RAG Vector Store Build Progress Monitor
# Usage: bash scripts/rag/check_rag_progress.sh

LOG_FILE="/tmp/rag_build.log"
PROGRESS_FILE="/Users/masa/Projects/Epstein/data/vector_store/embedding_progress.json"

echo "========================================"
echo "RAG Vector Store Build Progress"
echo "========================================"
echo ""

# Check if process is running
PID=$(ps aux | grep -v grep | grep build_vector_store.py | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "Status: RUNNING (PID: $PID)"
else
    echo "Status: NOT RUNNING"
fi
echo ""

# Show latest progress from log
echo "Latest Progress:"
tail -1 "$LOG_FILE" | grep -o "Embedding documents:.*" || echo "No progress data yet"
echo ""

# Show progress file stats if exists
if [ -f "$PROGRESS_FILE" ]; then
    echo "Progress File Stats:"
    python3 -c "
import json
with open('$PROGRESS_FILE', 'r') as f:
    data = json.load(f)
    print(f\"  Documents processed: {data.get('total_processed', 0):,}")
    print(f\"  Last updated: {data.get('last_updated', 'N/A')}\")
"
    echo ""
fi

# Estimate completion time
echo "Recent Log Activity (last 10 lines):"
tail -10 "$LOG_FILE" | grep "Embedding documents" | tail -5
echo ""

echo "Commands:"
echo "  View full log: tail -f /tmp/rag_build.log"
echo "  Check process: ps aux | grep build_vector_store"
echo "  Monitor progress: watch -n 10 'bash scripts/rag/check_rag_progress.sh'"
