#!/bin/bash

BASE_DIR="/Users/masa/Projects/Epstein/data/sources/giuffre_maxwell"
cd "$BASE_DIR"

echo "=== Giuffre v. Maxwell - Corrected Download Script ==="
echo "Started: $(date)"
echo ""

# Function to get metadata and find actual filenames
download_collection() {
    local collection_id=$1
    local part_name=$2
    local target_dir=$3
    
    echo "[$part_name] Downloading from $collection_id..."
    mkdir -p "$target_dir"
    
    # Get list of PDF files from metadata
    pdf_files=$(curl -s "https://archive.org/metadata/$collection_id" | \
        python3 -c "import sys,json; data=json.load(sys.stdin); print('\n'.join([f['name'] for f in data['files'] if f.get('name','').endswith('.pdf')]))")
    
    count=0
    total=$(echo "$pdf_files" | wc -l | tr -d ' ')
    
    for pdf_file in $pdf_files; do
        count=$((count + 1))
        echo -n "  [$count/$total] $pdf_file... "
        curl -s -o "$target_dir/$pdf_file" \
            "https://archive.org/download/$collection_id/$pdf_file"
        size=$(ls -lh "$target_dir/$pdf_file" | awk '{print $5}')
        echo "$size"
    done
    
    echo "  Complete: $count files downloaded"
    echo ""
}

# Download all parts
download_collection "1_20210130_202101" "Part 1" "part1"
download_collection "attachment-26_202101" "Part 3" "part3" 
download_collection "attachment-1" "Part 5" "part5"
download_collection "main-document" "Part 8" "part8"
download_collection "main-document-2" "Part 9" "part9"

echo "=== Download Complete ==="
echo "Finished: $(date)"
echo ""
echo "2024 Unsealed (943 pages): Already downloaded"
echo ""
echo "Summary:"
find part* -name "*.pdf" -type f | wc -l | xargs echo "  Total PDF files:"
du -sh part* 2024_unsealed | awk '{sum+=$1} END {print "  Total size: "sum}'
