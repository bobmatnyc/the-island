#!/bin/bash
# House Oversight September 2024 Release Downloader

BASE_DIR="/Users/masa/Projects/Epstein/data/sources/house_oversight_sept2024"
LOG_FILE="/Users/masa/Projects/Epstein/logs/downloads/house_oversight_sept2024.log"

mkdir -p "$BASE_DIR"

echo "[$(date)] Starting House Oversight September 2024 download" | tee -a "$LOG_FILE"

# Google Drive folder ID: 1ZSVpXEhI7gKI0zatJdYe6QhKJ5pjUo4b
DRIVE_FOLDER_ID="1ZSVpXEhI7gKI0zatJdYe6QhKJ5pjUo4b"

echo "[$(date)] Checking for publicly accessible files in Google Drive folder" | tee -a "$LOG_FILE"
echo "[$(date)] Folder ID: $DRIVE_FOLDER_ID" | tee -a "$LOG_FILE"

# Try to access the folder listing via Google Drive API
# Note: This may require authentication or the folder may not be publicly accessible

# Alternative approach: Check if there's a direct download link pattern
# Google Drive direct download: https://drive.google.com/uc?export=download&id={FILE_ID}

# Try to get folder metadata
folder_url="https://drive.google.com/drive/folders/$DRIVE_FOLDER_ID"
echo "[$(date)] Folder URL: $folder_url" | tee -a "$LOG_FILE"

# Attempt to fetch the page and extract file IDs
echo "[$(date)] Attempting to access folder contents..." | tee -a "$LOG_FILE"

if curl -s -L "$folder_url" -o "$BASE_DIR/folder_page.html"; then
    echo "[$(date)] Folder page retrieved" | tee -a "$LOG_FILE"

    # Try to extract file IDs from the page
    # Google Drive file IDs are typically 33-44 characters
    file_ids=$(grep -oE '["\047]([a-zA-Z0-9_-]{33,44})["\047]' "$BASE_DIR/folder_page.html" | sort -u | head -20)

    if [ -n "$file_ids" ]; then
        echo "[$(date)] Found potential file IDs" | tee -a "$LOG_FILE"

        count=0
        while IFS= read -r file_id; do
            # Clean the ID
            clean_id=$(echo "$file_id" | tr -d '"\047')

            if [ ${#clean_id} -lt 25 ]; then
                continue
            fi

            ((count++))
            if [ $count -gt 10 ]; then
                break
            fi

            output_file="$BASE_DIR/document_${count}.pdf"

            if [ -f "$output_file" ]; then
                echo "[$(date)] File $count already exists, skipping" | tee -a "$LOG_FILE"
                continue
            fi

            echo "[$(date)] Attempting to download file $count (ID: ${clean_id:0:10}...)" | tee -a "$LOG_FILE"

            # Try direct download
            download_url="https://drive.google.com/uc?export=download&id=$clean_id"

            if curl -L -f --retry 2 --retry-delay 3 -o "$output_file" "$download_url" 2>&1 | tee -a "$LOG_FILE"; then
                # Check if it's actually a PDF
                if file "$output_file" | grep -q "PDF"; then
                    size=$(ls -lh "$output_file" | awk '{print $5}')
                    echo "[$(date)] ✓ Downloaded file $count ($size)" | tee -a "$LOG_FILE"
                else
                    echo "[$(date)] ✗ File $count is not a PDF, removing" | tee -a "$LOG_FILE"
                    rm -f "$output_file"
                fi
            else
                echo "[$(date)] ✗ Failed to download file $count" | tee -a "$LOG_FILE"
                rm -f "$output_file"
            fi

            sleep 2
        done <<< "$file_ids"
    else
        echo "[$(date)] No file IDs found - folder may require authentication" | tee -a "$LOG_FILE"
        echo "[$(date)] Manual intervention may be required for this source" | tee -a "$LOG_FILE"
    fi
else
    echo "[$(date)] ✗ Could not access Google Drive folder" | tee -a "$LOG_FILE"
    echo "[$(date)] This source may require manual download with authentication" | tee -a "$LOG_FILE"
fi

echo "[$(date)] House Oversight September 2024 download attempt complete" | tee -a "$LOG_FILE"
echo "[$(date)] Files saved to: $BASE_DIR" | tee -a "$LOG_FILE"
du -sh "$BASE_DIR" 2>/dev/null | tee -a "$LOG_FILE"
ls -lh "$BASE_DIR"/*.pdf 2>/dev/null | tee -a "$LOG_FILE"
