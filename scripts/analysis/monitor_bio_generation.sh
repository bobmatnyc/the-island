#!/bin/bash
# Monitor biography generation progress

LOG_FILE="/tmp/generate_missing_bios.log"

echo "==================================================="
echo "Biography Generation Monitor"
echo "==================================================="
echo ""

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "Generation may not have started yet."
    exit 1
fi

# Extract progress information
echo "📊 Current Status:"
echo ""

# Get last processing line
last_entity=$(grep -E "^\[[0-9]+/[0-9]+\] Processing:" "$LOG_FILE" | tail -1)
if [ -n "$last_entity" ]; then
    echo "  $last_entity"
else
    echo "  Initializing..."
fi

echo ""
echo "📈 Progress Summary:"
echo ""

# Count successful generations
success_count=$(grep -c "✓ Generated" "$LOG_FILE")
echo "  ✓ Successful: $success_count"

# Count failures
fail_count=$(grep -c "✗ Failed" "$LOG_FILE")
echo "  ✗ Failed: $fail_count"

# Total processed
total_processed=$((success_count + fail_count))
echo "  📦 Total processed: $total_processed"

echo ""
echo "🎯 Quality Metrics:"
echo ""

# Average quality score (if available)
if grep -q "quality:" "$LOG_FILE"; then
    avg_quality=$(grep "quality:" "$LOG_FILE" | grep -oE "[0-9]+\.[0-9]+" | awk '{sum+=$1; count++} END {if(count>0) printf "%.2f", sum/count; else print "N/A"}')
    echo "  Average quality: $avg_quality"
fi

# Average word count
if grep -q "words," "$LOG_FILE"; then
    avg_words=$(grep "words," "$LOG_FILE" | grep -oE "[0-9]+ words" | grep -oE "[0-9]+" | awk '{sum+=$1; count++} END {if(count>0) printf "%.0f", sum/count; else print "N/A"}')
    echo "  Average words: $avg_words"
fi

echo ""
echo "⏱️  Recent Activity (last 10 lines):"
echo ""
tail -10 "$LOG_FILE" | sed 's/^/  /'

echo ""
echo "==================================================="
echo "Run this script again to see updated progress"
echo "or: watch -n 5 '$0'"
echo "==================================================="
