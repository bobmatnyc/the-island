#!/bin/bash
# Epstein Documents - Quick Start Download Script
# Downloads the top 3 priority collections immediately
# Total size: ~2-3 GB, Est. time: 1-2 hours

set -e  # Exit on error

echo "=================================================="
echo "Epstein Documents - Quick Start Download"
echo "=================================================="
echo ""
echo "This script will download the top 3 priority collections:"
echo "  1. Internet Archive Comprehensive (1.5 GB)"
echo "  2. Giuffre v. Maxwell Complete (4,553 pages)"
echo "  3. DocumentCloud Large Collection (2,024 pages)"
echo ""
echo "Total estimated size: 2-3 GB"
echo "Total estimated time: 1-2 hours"
echo ""
read -p "Press ENTER to continue or Ctrl+C to cancel..."

# Create download directory
DOWNLOAD_DIR="/Users/masa/Projects/Epstein/downloads"
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

echo ""
echo "=================================================="
echo "STEP 1: Installing Internet Archive CLI"
echo "=================================================="
if ! command -v ia &> /dev/null; then
    echo "Installing 'internetarchive' Python package..."
    pip3 install internetarchive
    echo "✅ Installed"
else
    echo "✅ Already installed"
fi

echo ""
echo "=================================================="
echo "STEP 2: Configure Internet Archive (optional)"
echo "=================================================="
echo "You can configure with your account for faster downloads."
echo "This is optional - you can skip this step."
read -p "Configure now? (y/N): " configure
if [[ "$configure" =~ ^[Yy]$ ]]; then
    ia configure
fi

echo ""
echo "=================================================="
echo "STEP 3: Downloading Internet Archive Collections"
echo "=================================================="

# Collection 1: Main comprehensive collection
echo ""
echo "Downloading: Internet Archive Comprehensive Collection (1.5 GB)"
echo "URL: https://archive.org/details/jeffrey-epstein-documents-collection_202502"
mkdir -p "$DOWNLOAD_DIR/ia-comprehensive"
cd "$DOWNLOAD_DIR/ia-comprehensive"
ia download jeffrey-epstein-documents-collection_202502
echo "✅ Downloaded to: $DOWNLOAD_DIR/ia-comprehensive/"

# Collection 2: Giuffre v. Maxwell
echo ""
echo "Downloading: Giuffre v. Maxwell Complete (4,553 pages)"
echo "URL: https://archive.org/details/final-epstein-documents"
mkdir -p "$DOWNLOAD_DIR/giuffre-maxwell"
cd "$DOWNLOAD_DIR/giuffre-maxwell"
ia download final-epstein-documents
echo "✅ Downloaded to: $DOWNLOAD_DIR/giuffre-maxwell/"

echo ""
echo "=================================================="
echo "STEP 4: Downloading DocumentCloud Collection"
echo "=================================================="

# Collection 3: DocumentCloud large collection
echo ""
echo "Downloading: DocumentCloud 6250471 (2,024 pages)"
echo "URL: https://www.documentcloud.org/documents/6250471-Epstein-Docs/"
mkdir -p "$DOWNLOAD_DIR/documentcloud"
cd "$DOWNLOAD_DIR/documentcloud"

# Try PDF download
echo "Attempting PDF download..."
if curl -L -o "6250471-Epstein-Docs.pdf" "https://www.documentcloud.org/documents/6250471.pdf"; then
    echo "✅ Downloaded: 6250471-Epstein-Docs.pdf"
else
    echo "⚠️  PDF download failed. Trying text version..."
    curl -L -o "6250471-Epstein-Docs.txt" "https://www.documentcloud.org/documents/6250471.txt"
    echo "✅ Downloaded: 6250471-Epstein-Docs.txt"
fi

echo ""
echo "=================================================="
echo "DOWNLOAD COMPLETE!"
echo "=================================================="
echo ""
echo "Downloaded collections:"
echo "  1. ✅ Internet Archive Comprehensive: $DOWNLOAD_DIR/ia-comprehensive/"
echo "  2. ✅ Giuffre v. Maxwell: $DOWNLOAD_DIR/giuffre-maxwell/"
echo "  3. ✅ DocumentCloud 6250471: $DOWNLOAD_DIR/documentcloud/"
echo ""
echo "Next steps:"
echo "  1. Review downloaded files in: $DOWNLOAD_DIR"
echo "  2. Run extraction scripts to process PDFs"
echo "  3. Build master index across all collections"
echo ""
echo "Additional collections available:"
echo "  - FBI Vault (22+ parts): https://vault.fbi.gov/jeffrey-epstein"
echo "  - House Oversight (20,000 pages): https://couriernewsroom.com/"
echo "  - See COMPREHENSIVE_EPSTEIN_DOCUMENT_SOURCES.md for full list"
echo ""
echo "=================================================="

# Generate summary file
SUMMARY_FILE="$DOWNLOAD_DIR/DOWNLOAD_SUMMARY.txt"
cat > "$SUMMARY_FILE" << EOF
Epstein Documents - Download Summary
=====================================

Date: $(date)
Download Directory: $DOWNLOAD_DIR

Collections Downloaded:
-----------------------

1. Internet Archive Comprehensive Collection
   - ID: jeffrey-epstein-documents-collection_202502
   - Size: ~1.5 GB
   - Location: $DOWNLOAD_DIR/ia-comprehensive/
   - URL: https://archive.org/details/jeffrey-epstein-documents-collection_202502

2. Giuffre v. Maxwell Complete (4,553 pages)
   - ID: final-epstein-documents
   - Size: ~4,553 pages (8 batches)
   - Location: $DOWNLOAD_DIR/giuffre-maxwell/
   - URL: https://archive.org/details/final-epstein-documents

3. DocumentCloud Collection (2,024 pages)
   - ID: 6250471-Epstein-Docs
   - Size: 2,024 pages
   - Location: $DOWNLOAD_DIR/documentcloud/
   - URL: https://www.documentcloud.org/documents/6250471-Epstein-Docs/

File Counts:
------------
EOF

echo "Internet Archive Comprehensive:" >> "$SUMMARY_FILE"
find "$DOWNLOAD_DIR/ia-comprehensive" -type f | wc -l | xargs echo "  Files:" >> "$SUMMARY_FILE"

echo "Giuffre v. Maxwell:" >> "$SUMMARY_FILE"
find "$DOWNLOAD_DIR/giuffre-maxwell" -type f | wc -l | xargs echo "  Files:" >> "$SUMMARY_FILE"

echo "DocumentCloud:" >> "$SUMMARY_FILE"
find "$DOWNLOAD_DIR/documentcloud" -type f | wc -l | xargs echo "  Files:" >> "$SUMMARY_FILE"

cat >> "$SUMMARY_FILE" << EOF

Total Disk Usage:
-----------------
EOF
du -sh "$DOWNLOAD_DIR" >> "$SUMMARY_FILE"

echo ""
echo "📄 Summary saved to: $SUMMARY_FILE"
echo ""
