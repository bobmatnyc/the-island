#!/bin/bash
#
# Batch Entity Enrichment Pipeline
#
# This script automates the entity enrichment process using the content agent:
# 1. Enrich entities in batches of 10
# 2. Run QA validation after each batch
# 3. Generate progress reports
# 4. Handle errors and resume from checkpoint
#
# Usage:
#   ./batch_enrich.sh [--start N] [--count N] [--continue]
#
# Options:
#   --start N     Start from entity N (default: 0)
#   --count N     Enrich N entities (default: 10)
#   --continue    Continue from last checkpoint
#   --validate    Run validation only (no enrichment)
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/Users/masa/Projects/epstein"
DATA_DIR="$PROJECT_ROOT/data/metadata"
LOG_DIR="$PROJECT_ROOT/logs/enrichment"
CHECKPOINT_FILE="$DATA_DIR/.enrichment_checkpoint"

# Create log directory
mkdir -p "$LOG_DIR"

# Default options
START_INDEX=0
COUNT=10
CONTINUE=false
VALIDATE_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --start)
            START_INDEX="$2"
            shift 2
            ;;
        --count)
            COUNT="$2"
            shift 2
            ;;
        --continue)
            CONTINUE=true
            shift
            ;;
        --validate)
            VALIDATE_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Load checkpoint if continuing
if [ "$CONTINUE" = true ] && [ -f "$CHECKPOINT_FILE" ]; then
    START_INDEX=$(cat "$CHECKPOINT_FILE")
    echo "📍 Resuming from checkpoint: entity $START_INDEX"
fi

# Log file
LOG_FILE="$LOG_DIR/batch_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "="
log "BATCH ENTITY ENRICHMENT PIPELINE"
log "="
log ""
log "Configuration:"
log "  Start index: $START_INDEX"
log "  Count: $COUNT"
log "  Output: $DATA_DIR/enriched_entity_data.json"
log "  Log file: $LOG_FILE"
log ""

# Run validation only
if [ "$VALIDATE_ONLY" = true ]; then
    log "Running QA validation..."
    python3 "$SCRIPT_DIR/qa_validation.py" \
        --input "$DATA_DIR/enriched_entity_data.json" \
        --export "$DATA_DIR/qa_validation_report.json"
    exit $?
fi

# Main enrichment loop
log "Starting batch enrichment..."
BATCH_SIZE=10
CURRENT=$START_INDEX
END=$((START_INDEX + COUNT))

while [ $CURRENT -lt $END ]; do
    BATCH_COUNT=$((END - CURRENT))
    if [ $BATCH_COUNT -gt $BATCH_SIZE ]; then
        BATCH_COUNT=$BATCH_SIZE
    fi

    log ""
    log "Batch: entities $CURRENT to $((CURRENT + BATCH_COUNT - 1))"
    log "="

    # Run enrichment
    if python3 "$SCRIPT_DIR/automated_entity_enrichment.py" \
        --batch $BATCH_COUNT \
        --output "$DATA_DIR/enriched_entity_data.json" \
        2>&1 | tee -a "$LOG_FILE"; then

        log "✅ Batch enrichment successful"

        # Update checkpoint
        echo $((CURRENT + BATCH_COUNT)) > "$CHECKPOINT_FILE"

        # Run QA validation
        log "Running QA validation..."
        if python3 "$SCRIPT_DIR/qa_validation.py" \
            --input "$DATA_DIR/enriched_entity_data.json" \
            2>&1 | tee -a "$LOG_FILE"; then
            log "✅ QA validation passed"
        else
            log "⚠️  QA validation found issues (see report)"
        fi

        # Generate progress report
        log "Generating progress report..."
        python3 "$SCRIPT_DIR/automated_entity_enrichment.py" \
            --report \
            2>&1 | tee -a "$LOG_FILE"

        CURRENT=$((CURRENT + BATCH_COUNT))

        # Rate limiting between batches
        if [ $CURRENT -lt $END ]; then
            log "Waiting 30 seconds before next batch..."
            sleep 30
        fi

    else
        log "❌ Batch enrichment failed"
        log "Checkpoint saved at: $CURRENT"
        exit 1
    fi
done

log ""
log "="
log "BATCH ENRICHMENT COMPLETE"
log "="
log "Total entities enriched: $COUNT"
log "Final checkpoint: $CURRENT"
log "Log file: $LOG_FILE"
log ""

# Final validation and report
log "Running final QA validation..."
python3 "$SCRIPT_DIR/qa_validation.py" \
    --input "$DATA_DIR/enriched_entity_data.json" \
    --export "$DATA_DIR/qa_validation_final.json"

log ""
log "📊 Final Report:"
python3 "$SCRIPT_DIR/automated_entity_enrichment.py" --report

log ""
log "✅ Pipeline complete!"
log "   Results: $DATA_DIR/enriched_entity_data.json"
log "   QA Report: $DATA_DIR/qa_validation_final.json"
log "   Full log: $LOG_FILE"
