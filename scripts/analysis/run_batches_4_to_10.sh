#!/bin/bash
# Auto-run biography generation batches 4-10
# Generated: 2025-11-25

set -e

PROJECT_ROOT="/Users/masa/Projects/epstein"
cd "$PROJECT_ROOT/scripts/analysis"

# API Key
export OPENROUTER_API_KEY=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

# Function to run a batch
run_batch() {
    local batch_num=$1
    local limit=$2
    local output_file="$PROJECT_ROOT/data/metadata/entity_biographies_batch${batch_num}.json"

    echo ""
    echo "=========================================="
    echo "BATCH $batch_num: Generating $limit biographies"
    echo "=========================================="
    echo "Start time: $(date)"

    python3 generate_entity_bios_grok.py \
        --tier all \
        --limit "$limit" \
        --output "$output_file" \
        --backup

    echo "Batch $batch_num complete: $(date)"
    echo ""
}

# Run batches sequentially
echo "Starting biography generation batches 4-10"
echo "Started at: $(date)"

# Check if Batch 4 is already running
if pgrep -f "entity_biographies_batch4" > /dev/null; then
    echo "⚠️  Batch 4 is already running. Waiting for completion..."
    while pgrep -f "entity_biographies_batch4" > /dev/null; do
        sleep 10
    done
    echo "✓ Batch 4 completed"
fi

# Run remaining batches
run_batch 5 100
run_batch 6 100
run_batch 7 100
run_batch 8 100
run_batch 9 100
run_batch 10 100

echo ""
echo "=========================================="
echo "ALL BATCHES COMPLETE"
echo "=========================================="
echo "Finished at: $(date)"
echo ""
echo "Files created:"
ls -lh "$PROJECT_ROOT/data/metadata/entity_biographies_batch"*.json
