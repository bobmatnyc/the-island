#!/bin/bash
# Master Parallel Downloader for Epstein Document Collections
# Runs multiple download scripts in background and tracks progress

SCRIPT_DIR="/Users/masa/Projects/Epstein/scripts"
LOG_DIR="/Users/masa/Projects/Epstein/logs/downloads"
PID_FILE="$LOG_DIR/download_pids.txt"
STATUS_FILE="$LOG_DIR/download_status.json"

mkdir -p "$LOG_DIR"

echo "=== Epstein Document Collections - Parallel Download Manager ===" | tee "$LOG_DIR/master.log"
echo "Started: $(date)" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

# Make all scripts executable
chmod +x "$SCRIPT_DIR"/download_*.sh

# Clear previous PID file
> "$PID_FILE"

# Initialize status file
cat > "$STATUS_FILE" << 'EOFSTATUS'
{
  "session": {
    "started": "",
    "status": "running",
    "downloads": []
  }
}
EOFSTATUS

# Update start time
sed -i.bak "s/\"started\": \"\"/\"started\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"/g" "$STATUS_FILE"

echo "Starting parallel downloads..." | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

# Priority 1: FBI Vault (highest value)
echo "[1/4] Starting FBI Vault download..." | tee -a "$LOG_DIR/master.log"
nohup bash "$SCRIPT_DIR/download_fbi_vault.sh" > "$LOG_DIR/fbi_vault_nohup.log" 2>&1 &
FBI_PID=$!
echo "fbi_vault:$FBI_PID" >> "$PID_FILE"
echo "  → FBI Vault PID: $FBI_PID" | tee -a "$LOG_DIR/master.log"
echo "  → Log: $LOG_DIR/fbi_vault.log" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

sleep 2

# Priority 2: Internet Archive collections
echo "[2/4] Starting Internet Archive download..." | tee -a "$LOG_DIR/master.log"
nohup bash "$SCRIPT_DIR/download_internet_archive.sh" > "$LOG_DIR/internet_archive_nohup.log" 2>&1 &
IA_PID=$!
echo "internet_archive:$IA_PID" >> "$PID_FILE"
echo "  → Internet Archive PID: $IA_PID" | tee -a "$LOG_DIR/master.log"
echo "  → Log: $LOG_DIR/internet_archive.log" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

sleep 2

# Priority 3: DocumentCloud additional collections
echo "[3/4] Starting DocumentCloud additional collections download..." | tee -a "$LOG_DIR/master.log"
nohup bash "$SCRIPT_DIR/download_documentcloud.sh" > "$LOG_DIR/documentcloud_extra_nohup.log" 2>&1 &
DC_PID=$!
echo "documentcloud_extra:$DC_PID" >> "$PID_FILE"
echo "  → DocumentCloud Extra PID: $DC_PID" | tee -a "$LOG_DIR/master.log"
echo "  → Log: $LOG_DIR/documentcloud_extra.log" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

sleep 2

# Priority 4: House Oversight September 2024
echo "[4/4] Starting House Oversight September 2024 download..." | tee -a "$LOG_DIR/master.log"
nohup bash "$SCRIPT_DIR/download_house_oversight_sept2024.sh" > "$LOG_DIR/house_oversight_sept2024_nohup.log" 2>&1 &
HO_PID=$!
echo "house_oversight_sept2024:$HO_PID" >> "$PID_FILE"
echo "  → House Oversight Sept 2024 PID: $HO_PID" | tee -a "$LOG_DIR/master.log"
echo "  → Log: $LOG_DIR/house_oversight_sept2024.log" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

# Summary
echo "======================================" | tee -a "$LOG_DIR/master.log"
echo "All downloads started in background!" | tee -a "$LOG_DIR/master.log"
echo "======================================" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

echo "Process IDs:" | tee -a "$LOG_DIR/master.log"
cat "$PID_FILE" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

echo "Monitor progress with:" | tee -a "$LOG_DIR/master.log"
echo "  ps -p $FBI_PID,$IA_PID,$DC_PID,$HO_PID" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

echo "View logs:" | tee -a "$LOG_DIR/master.log"
echo "  tail -f $LOG_DIR/fbi_vault.log" | tee -a "$LOG_DIR/master.log"
echo "  tail -f $LOG_DIR/internet_archive.log" | tee -a "$LOG_DIR/master.log"
echo "  tail -f $LOG_DIR/documentcloud_extra.log" | tee -a "$LOG_DIR/master.log"
echo "  tail -f $LOG_DIR/house_oversight_sept2024.log" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

echo "Check status:" | tee -a "$LOG_DIR/master.log"
echo "  bash $SCRIPT_DIR/check_download_status.sh" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

# Create a status checker script
cat > "$SCRIPT_DIR/check_download_status.sh" << 'EOFCHECKER'
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
EOFCHECKER

chmod +x "$SCRIPT_DIR/check_download_status.sh"

echo "Status checker script created at: $SCRIPT_DIR/check_download_status.sh" | tee -a "$LOG_DIR/master.log"
echo "" | tee -a "$LOG_DIR/master.log"

# Wait a few seconds and show initial status
sleep 5
echo "Initial Status Check:" | tee -a "$LOG_DIR/master.log"
echo "--------------------" | tee -a "$LOG_DIR/master.log"
bash "$SCRIPT_DIR/check_download_status.sh" | tee -a "$LOG_DIR/master.log"
