#!/usr/bin/env python3
"""Check CourtListener download progress."""

import json
from pathlib import Path


# Paths
output_dir = Path(__file__).parent.parent.parent / "data" / "sources" / "courtlistener_giuffre_maxwell"
metadata_file = output_dir / "download_metadata.json"

# Load metadata
if metadata_file.exists():
    with open(metadata_file) as f:
        metadata = json.load(f)

    downloaded = len(metadata.get("downloads", []))
    failed = len(metadata.get("failed", []))
    total = 371  # Expected total

    print("=" * 60)
    print("CourtListener Download Progress")
    print("=" * 60)
    print(f"Downloaded: {downloaded} / {total} ({downloaded/total*100:.1f}%)")
    print(f"Failed: {failed}")
    print(f"Remaining: {total - downloaded - failed}")
    print("=" * 60)

    if downloaded > 0:
        # Show last downloaded file
        last = metadata["downloads"][-1]
        print(f"\nLast downloaded: {last['filename']}")
        print(f"Size: {last['size_bytes'] / 1024:.1f} KB")

    if failed > 0:
        print(f"\n⚠️  {failed} failed downloads")

else:
    print("No metadata file found. Download may not have started.")

# Count actual files
pdf_files = list(output_dir.glob("*.pdf"))
print(f"\nActual PDF files in directory: {len(pdf_files)}")

# Calculate total size
total_size = sum(f.stat().st_size for f in pdf_files)
print(f"Total size: {total_size / (1024 * 1024):.2f} MB")
