#!/bin/bash
# Internet Archive Downloader for Epstein Collections

BASE_DIR="/Users/masa/Projects/Epstein/data/sources/internet_archive"
LOG_FILE="/Users/masa/Projects/Epstein/logs/downloads/internet_archive.log"

mkdir -p "$BASE_DIR"

echo "[$(date)] Starting Internet Archive download" | tee -a "$LOG_FILE"

# Known high-value Internet Archive collections
COLLECTIONS=(
    "jeffrey-epstein-documents-collection_202502"
    "epstein-flight-logs"
    "epstein-black-book"
    "ghislaine-maxwell-documents"
)

for collection in "${COLLECTIONS[@]}"; do
    echo "[$(date)] Processing collection: $collection" | tee -a "$LOG_FILE"

    # Create collection directory
    col_dir="$BASE_DIR/$collection"
    mkdir -p "$col_dir"

    # Try to get collection metadata
    metadata_url="https://archive.org/metadata/$collection"
    echo "[$(date)] Fetching metadata from: $metadata_url" | tee -a "$LOG_FILE"

    if curl -s "$metadata_url" -o "$col_dir/metadata.json"; then
        echo "[$(date)] Metadata retrieved" | tee -a "$LOG_FILE"

        # Extract file URLs from metadata
        # Internet Archive files are at: https://archive.org/download/{collection}/{filename}
        files=$(cat "$col_dir/metadata.json" | grep -o '"name":"[^"]*\.pdf"' | sed 's/"name":"//;s/"$//' | head -20)

        if [ -n "$files" ]; then
            echo "[$(date)] Found PDF files in collection" | tee -a "$LOG_FILE"

            while IFS= read -r filename; do
                if [ -z "$filename" ]; then continue; fi

                file_url="https://archive.org/download/$collection/$filename"
                output_file="$col_dir/$filename"

                if [ -f "$output_file" ]; then
                    echo "[$(date)] File already exists: $filename" | tee -a "$LOG_FILE"
                    continue
                fi

                echo "[$(date)] Downloading: $filename" | tee -a "$LOG_FILE"

                if curl -L -f --retry 3 --retry-delay 5 -o "$output_file" "$file_url" 2>&1 | tee -a "$LOG_FILE"; then
                    size=$(ls -lh "$output_file" | awk '{print $5}')
                    echo "[$(date)] ✓ Downloaded: $filename ($size)" | tee -a "$LOG_FILE"
                else
                    echo "[$(date)] ✗ Failed: $filename" | tee -a "$LOG_FILE"
                    rm -f "$output_file"
                fi

                sleep 2
            done <<< "$files"
        else
            echo "[$(date)] No PDF files found in metadata" | tee -a "$LOG_FILE"
        fi
    else
        echo "[$(date)] ✗ Could not retrieve metadata for $collection" | tee -a "$LOG_FILE"
    fi

    echo "[$(date)] Completed collection: $collection" | tee -a "$LOG_FILE"
    echo "---" | tee -a "$LOG_FILE"
done

echo "[$(date)] Internet Archive download complete" | tee -a "$LOG_FILE"
echo "[$(date)] Files saved to: $BASE_DIR" | tee -a "$LOG_FILE"
du -sh "$BASE_DIR"/* 2>/dev/null | tee -a "$LOG_FILE"
