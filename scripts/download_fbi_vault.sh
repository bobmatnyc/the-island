#!/bin/bash
# FBI Vault Downloader for Jeffrey Epstein Files
# Based on known FBI Vault structure

BASE_DIR="/Users/masa/Projects/Epstein/data/sources/fbi_vault"
LOG_FILE="/Users/masa/Projects/Epstein/logs/downloads/fbi_vault.log"

mkdir -p "$BASE_DIR"

echo "[$(date)] Starting FBI Vault download" | tee -a "$LOG_FILE"

# FBI Vault typically has parts numbered sequentially
# Known pattern: https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%20XX%20of%20XX/view

# Based on public FBI Vault structure for Epstein (22+ parts confirmed)
PARTS=(
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2001%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2002%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2003%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2004%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2005%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2006%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2007%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2008%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2009%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2010%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2011%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2012%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2013%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2014%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2015%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2016%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2017%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2018%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2019%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2020%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2021%20of%2022/at_download/file"
    "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%2022%20of%2022/at_download/file"
)

count=0
success=0
failed=0

for i in "${!PARTS[@]}"; do
    part_num=$((i + 1))
    part_file=$(printf "%02d" $part_num)
    output_file="$BASE_DIR/epstein_part_${part_file}_of_22.pdf"

    if [ -f "$output_file" ]; then
        echo "[$(date)] Part $part_num already exists, skipping" | tee -a "$LOG_FILE"
        ((success++))
        continue
    fi

    echo "[$(date)] Downloading Part $part_num of 22..." | tee -a "$LOG_FILE"

    if curl -L -f --retry 3 --retry-delay 5 -o "$output_file" "${PARTS[$i]}" 2>&1 | tee -a "$LOG_FILE"; then
        size=$(ls -lh "$output_file" | awk '{print $5}')
        echo "[$(date)] ✓ Part $part_num downloaded successfully ($size)" | tee -a "$LOG_FILE"
        ((success++))
    else
        echo "[$(date)] ✗ Part $part_num failed to download" | tee -a "$LOG_FILE"
        rm -f "$output_file"
        ((failed++))
    fi

    ((count++))

    # Small delay to be respectful to FBI servers
    sleep 2
done

echo "[$(date)] FBI Vault download complete: $success successful, $failed failed" | tee -a "$LOG_FILE"
echo "[$(date)] Files saved to: $BASE_DIR" | tee -a "$LOG_FILE"
ls -lh "$BASE_DIR" | tee -a "$LOG_FILE"
