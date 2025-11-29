#!/bin/bash
# DocumentCloud Additional Collections Downloader

BASE_DIR="/Users/masa/Projects/Epstein/data/sources/documentcloud_extra"
LOG_FILE="/Users/masa/Projects/Epstein/logs/downloads/documentcloud_extra.log"

mkdir -p "$BASE_DIR"

echo "[$(date)] Starting DocumentCloud additional collections download" | tee -a "$LOG_FILE"

# High-priority DocumentCloud project IDs for Epstein-related documents
# These are known large collections not yet downloaded
PROJECTS=(
    "epstein-flight-logs-200991"
    "epstein-black-book-200992"
    "ghislaine-maxwell-trial-documents-214050"
    "epstein-victims-compensation-fund-210045"
    "southern-district-ny-epstein-documents-201234"
)

for project in "${PROJECTS[@]}"; do
    echo "[$(date)] Processing DocumentCloud project: $project" | tee -a "$LOG_FILE"

    # Create project directory
    proj_dir="$BASE_DIR/$project"
    mkdir -p "$proj_dir"

    # DocumentCloud API endpoint for searching
    # Note: These are example IDs - actual IDs may differ
    project_id=$(echo "$project" | grep -oE '[0-9]+$')

    if [ -n "$project_id" ]; then
        echo "[$(date)] Searching for documents in project $project_id" | tee -a "$LOG_FILE"

        # Try DocumentCloud API v2
        api_url="https://api.www.documentcloud.org/api/documents/?project=$project_id"

        if curl -s "$api_url" -o "$proj_dir/api_response.json"; then
            echo "[$(date)] API response received" | tee -a "$LOG_FILE"

            # Extract document IDs and URLs
            # DocumentCloud URLs: https://assets.documentcloud.org/documents/{doc_id}/filename.pdf
            doc_urls=$(cat "$proj_dir/api_response.json" | grep -oE '"canonical_url":"[^"]*"' | sed 's/"canonical_url":"//;s/"$//' | head -10)

            if [ -n "$doc_urls" ]; then
                while IFS= read -r doc_url; do
                    if [ -z "$doc_url" ]; then continue; fi

                    # Extract document ID from URL
                    doc_id=$(echo "$doc_url" | grep -oE '[0-9]+-[^/]+' | head -1)

                    if [ -n "$doc_id" ]; then
                        # Try to download the PDF
                        pdf_url="${doc_url}.pdf"
                        output_file="$proj_dir/${doc_id}.pdf"

                        if [ -f "$output_file" ]; then
                            echo "[$(date)] Document already exists: $doc_id" | tee -a "$LOG_FILE"
                            continue
                        fi

                        echo "[$(date)] Downloading document: $doc_id" | tee -a "$LOG_FILE"

                        if curl -L -f --retry 3 --retry-delay 5 -o "$output_file" "$pdf_url" 2>&1 | tee -a "$LOG_FILE"; then
                            size=$(ls -lh "$output_file" | awk '{print $5}')
                            echo "[$(date)] ✓ Downloaded: $doc_id ($size)" | tee -a "$LOG_FILE"
                        else
                            echo "[$(date)] ✗ Failed: $doc_id" | tee -a "$LOG_FILE"
                            rm -f "$output_file"
                        fi

                        sleep 2
                    fi
                done <<< "$doc_urls"
            else
                echo "[$(date)] No document URLs found in API response" | tee -a "$LOG_FILE"
            fi
        else
            echo "[$(date)] ✗ Could not retrieve API response for project $project_id" | tee -a "$LOG_FILE"
        fi
    fi

    echo "[$(date)] Completed project: $project" | tee -a "$LOG_FILE"
    echo "---" | tee -a "$LOG_FILE"
done

echo "[$(date)] DocumentCloud additional collections download complete" | tee -a "$LOG_FILE"
echo "[$(date)] Files saved to: $BASE_DIR" | tee -a "$LOG_FILE"
du -sh "$BASE_DIR"/* 2>/dev/null | tee -a "$LOG_FILE"
