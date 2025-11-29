#!/bin/bash
# Giuffre v. Maxwell - Comprehensive Download Script

BASE_DIR="/Users/masa/Projects/Epstein/data/sources/giuffre_maxwell"
cd "$BASE_DIR"

echo "=== Downloading Giuffre v. Maxwell Court Documents ==="
echo "Started: $(date)"
echo ""

# Part 1 - Individual page files (103 pages)
echo "[1/6] Downloading Part 1 (July 2020 - 103 pages)..."
mkdir -p part1
cd part1
for i in $(seq 1 103); do
    printf "Page %3d/103\r" $i
    curl -s -o "page_$(printf '%03d' $i).pdf" \
        "https://archive.org/download/1_20210130_202101/$(printf '%d' $i).pdf" 2>/dev/null
done
echo -e "\nPart 1 complete."
cd "$BASE_DIR"

# Part 3 - Main doc + 19 attachments
echo -e "\n[2/6] Downloading Part 3 (July 2020 - 20 files)..."
mkdir -p part3
cd part3
curl -s -o "main_document.pdf" \
    "https://archive.org/download/attachment-26_202101/Main%20Document.pdf"
for i in $(seq 1 19); do
    printf "Attachment %2d/19\r" $i
    curl -s -o "attachment_$(printf '%02d' $i).pdf" \
        "https://archive.org/download/attachment-26_202101/Attachment%20$i.pdf" 2>/dev/null
done
echo -e "\nPart 3 complete."
cd "$BASE_DIR"

# Part 5 - Main doc + 27 attachments  
echo -e "\n[3/6] Downloading Part 5 (Jan 2021 - 28 files)..."
mkdir -p part5
cd part5
curl -s -o "main_document.pdf" \
    "https://archive.org/download/attachment-1/Main%20document.pdf"
for i in $(seq 1 27); do
    printf "Attachment %2d/27\r" $i
    curl -s -o "attachment_$(printf '%02d' $i).pdf" \
        "https://archive.org/download/attachment-1/Attachment%20$i.pdf" 2>/dev/null
done
echo -e "\nPart 5 complete."
cd "$BASE_DIR"

# Part 8
echo -e "\n[4/6] Downloading Part 8 (Jan 2021)..."
mkdir -p part8
curl -s -o "part8/main_document.pdf" \
    "https://archive.org/download/main-document/Main%20Document.pdf"
echo "Part 8 complete."

# Part 9
echo -e "\n[5/6] Downloading Part 9 (Jan 2021)..."
mkdir -p part9
curl -s -o "part9/main_document.pdf" \
    "https://archive.org/download/main-document-2/Main%20Document.pdf"
echo "Part 9 complete."

# 2024 Unsealed (already downloading in background)
echo -e "\n[6/6] 2024 Unsealed documents (943 pages) downloading in background..."

echo ""
echo "=== Download Complete ==="
echo "Finished: $(date)"
