#!/usr/bin/env python3
"""
Generate summary report of CourtListener download.

Analyzes downloaded PDFs and metadata to create comprehensive summary.
"""

import json
from collections import Counter
from pathlib import Path


def summarize_download(output_dir: Path):
    """Generate download summary report."""

    metadata_file = output_dir / "download_metadata.json"

    # Load metadata
    if not metadata_file.exists():
        print("❌ No metadata file found!")
        return

    with open(metadata_file) as f:
        metadata = json.load(f)

    downloads = metadata.get("downloads", [])
    failed = metadata.get("failed", [])

    # Count actual files
    pdf_files = list(output_dir.glob("giuffre_maxwell_*.pdf"))

    # Calculate statistics
    total_expected = 371
    total_size = sum(d["size_bytes"] for d in downloads)

    # Group by document number
    doc_numbers = set()
    attachments_by_doc = Counter()

    for download in downloads:
        doc_num = download.get("document_number", "")
        if "." in doc_num:
            main_doc, attach = doc_num.split(".", 1)
            doc_numbers.add(main_doc)
            if attach != "0":
                attachments_by_doc[main_doc] += 1

    # Print summary
    print("=" * 70)
    print("CourtListener Download Summary - Giuffre v. Maxwell")
    print("=" * 70)
    print("\n📊 Download Statistics:")
    print(f"  ✓ Successfully downloaded: {len(downloads)} / {total_expected}")
    print(f"  ✗ Failed downloads: {len(failed)}")
    print(f"  📁 Files in directory: {len(pdf_files)}")
    print(f"  💾 Total size: {total_size / (1024 * 1024):.2f} MB")
    print(f"  📄 Unique documents: {len(doc_numbers)}")
    print(f"  📎 Documents with attachments: {len(attachments_by_doc)}")

    # Size distribution
    sizes = [d["size_bytes"] for d in downloads]
    print("\n📏 Size Distribution:")
    print(f"  Smallest: {min(sizes) / 1024:.1f} KB")
    print(f"  Largest: {max(sizes) / (1024 * 1024):.2f} MB")
    print(f"  Average: {(sum(sizes) / len(sizes)) / 1024:.1f} KB")

    # Documents with most attachments
    if attachments_by_doc:
        print("\n📎 Documents with Most Attachments:")
        for doc_num, count in attachments_by_doc.most_common(5):
            print(f"  Document {doc_num}: {count} attachments")

    # Failed downloads
    if failed:
        print(f"\n⚠️  Failed Downloads ({len(failed)}):")
        for fail in failed[:10]:
            print(f"  - {fail['filename']}: {fail['reason']}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    # Completion status
    completion_pct = (len(downloads) / total_expected) * 100
    print(f"\n✅ Download Completion: {completion_pct:.1f}%")

    if completion_pct >= 99:
        print("🎉 Download complete!")
    elif completion_pct >= 90:
        print(f"⏳ Nearly complete ({total_expected - len(downloads)} remaining)")
    else:
        print(f"⏳ In progress ({total_expected - len(downloads)} remaining)")

    print("=" * 70)

    # Save summary to file
    summary_file = output_dir / "DOWNLOAD_SUMMARY.txt"
    with open(summary_file, "w") as f:
        f.write("CourtListener Download Summary - Giuffre v. Maxwell\n")
        f.write(f"{'=' * 70}\n\n")
        f.write(f"Download Date: {metadata.get('last_update', 'Unknown')}\n")
        f.write(f"Total PDFs: {len(downloads)} / {total_expected}\n")
        f.write(f"Failed: {len(failed)}\n")
        f.write(f"Total Size: {total_size / (1024 * 1024):.2f} MB\n")
        f.write(f"Unique Documents: {len(doc_numbers)}\n\n")

        f.write("Document Numbers:\n")
        for doc_num in sorted(doc_numbers, key=lambda x: int(x)):
            attach_count = attachments_by_doc.get(doc_num, 0)
            if attach_count > 0:
                f.write(f"  {doc_num} (+ {attach_count} attachments)\n")
            else:
                f.write(f"  {doc_num}\n")

    print(f"\n📝 Summary saved to: {summary_file}")


def main():
    output_dir = Path(__file__).parent.parent.parent / "data" / "sources" / "courtlistener_giuffre_maxwell"
    summarize_download(output_dir)


if __name__ == "__main__":
    main()
