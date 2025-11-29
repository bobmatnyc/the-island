#!/bin/bash

BASE_DIR="/Users/masa/Projects/Epstein/data/sources/giuffre_maxwell"
cd "$BASE_DIR"

echo "=== Giuffre v. Maxwell - Final Download Strategy ==="
echo "Using Internet Archive bulk download API"
echo "Started: $(date)"
echo ""

# Download each part as a ZIP of all PDFs
download_zip() {
    local collection_id=$1
    local part_name=$2
    local part_dir=$3
    
    echo "[$part_name] Downloading from $collection_id..."
    mkdir -p "$part_dir"
    cd "$part_dir"
    
    curl -L --progress-bar \
        "https://archive.org/compress/$collection_id/formats=PDF" \
        -o "${part_name}_pdfs.zip"
    
    if [ -f "${part_name}_pdfs.zip" ] && [ -s "${part_name}_pdfs.zip" ]; then
        echo "  Extracting..."
        unzip -q "${part_name}_pdfs.zip"
        rm "${part_name}_pdfs.zip"
        count=$(find . -name "*.pdf" | wc -l | tr -d ' ')
        size=$(du -sh . | awk '{print $1}')
        echo "  Complete: $count PDFs, $size total"
    else
        echo "  ERROR: Download failed or empty"
    fi
    
    cd "$BASE_DIR"
    echo ""
}

# Download all parts
download_zip "1_20210130_202101" "part1" "part1"
download_zip "attachment-26_202101" "part3" "part3"
download_zip "attachment-1" "part5" "part5"
download_zip "main-document" "part8" "part8"
download_zip "main-document-2" "part9" "part9"

echo "=== Download Summary ==="
echo "2024 Unsealed: Already downloaded (943 pages, 23MB)"
echo ""
find part* -name "*.pdf" -type f | wc -l | xargs echo "Total PDF files in parts 1,3,5,8,9:"
du -sh part* | awk '{sum+=$1} END {print "Total size of parts: varies"}'
du -sh . | awk '{print "Total collection size: "$1}'
echo ""
echo "Finished: $(date)"
