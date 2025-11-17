#!/usr/bin/env python3
"""
Rebuild comprehensive document statistics across all sources.

Counts:
- All PDF documents by source
- All extracted emails by source
- All entity documents
- Creates unified document index
- Updates classification statistics
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


# Base paths
PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
SOURCES_DIR = DATA_DIR / "sources"
EMAILS_DIR = DATA_DIR / "emails"
METADATA_DIR = DATA_DIR / "metadata"
MD_DIR = DATA_DIR / "md"

def count_pdfs_by_source() -> Dict[str, int]:
    """Count PDF files in each source directory."""
    print("Counting PDFs by source...")

    pdf_counts = {}

    if not SOURCES_DIR.exists():
        print(f"Warning: Sources directory not found: {SOURCES_DIR}")
        return pdf_counts

    for source_dir in SOURCES_DIR.iterdir():
        if source_dir.is_dir():
            source_name = source_dir.name
            pdf_files = list(source_dir.rglob("*.pdf"))
            pdf_count = len(pdf_files)

            if pdf_count > 0:
                pdf_counts[source_name] = pdf_count
                print(f"  {source_name}: {pdf_count:,} PDFs")

    total = sum(pdf_counts.values())
    print(f"\nTotal PDFs: {total:,}")

    return pdf_counts

def count_emails_by_source() -> Dict[str, Dict[str, Any]]:
    """Count extracted emails by source."""
    print("\nCounting emails by source...")

    email_counts = {}

    if not EMAILS_DIR.exists():
        print(f"Warning: Emails directory not found: {EMAILS_DIR}")
        return email_counts

    for source_dir in EMAILS_DIR.iterdir():
        if source_dir.is_dir():
            source_name = source_dir.name

            # Count JSON metadata files (each represents one email)
            json_files = list(source_dir.rglob("*_metadata.json"))
            # Also count txt files
            txt_files = list(source_dir.rglob("*_full.txt"))
            body_files = list(source_dir.rglob("*_body.txt"))

            # Use metadata count as authoritative
            email_count = len(json_files)

            if email_count > 0:
                email_counts[source_name] = {
                    "count": email_count,
                    "metadata_files": len(json_files),
                    "full_text_files": len(txt_files),
                    "body_files": len(body_files)
                }
                print(f"  {source_name}: {email_count:,} emails")

    total = sum(c["count"] for c in email_counts.values())
    print(f"\nTotal emails: {total:,}")

    return email_counts

def count_entity_documents() -> Dict[str, Any]:
    """Count entity-related documents."""
    print("\nCounting entity documents...")

    entity_dir = MD_DIR / "entities"
    entity_counts = {
        "markdown_files": 0,
        "documents": []
    }

    if not entity_dir.exists():
        print(f"Warning: Entity directory not found: {entity_dir}")
        return entity_counts

    for md_file in entity_dir.glob("*.md"):
        entity_counts["markdown_files"] += 1
        entity_counts["documents"].append({
            "filename": md_file.name,
            "path": str(md_file),
            "size": md_file.stat().st_size
        })
        print(f"  {md_file.name}")

    # Also count JSON files
    json_files = list(entity_dir.glob("*.json"))
    entity_counts["json_files"] = len(json_files)

    print(f"\nTotal entity documents: {entity_counts['markdown_files']} MD, {entity_counts['json_files']} JSON")

    return entity_counts

def count_other_documents() -> Dict[str, int]:
    """Count other document types (OCR results, etc.)."""
    print("\nCounting other document types...")

    other_counts = {}

    # Count markdown files from OCR
    md_sources = MD_DIR / "house_oversight_nov2025"
    if md_sources.exists():
        ocr_md_files = list(md_sources.rglob("*.md"))
        other_counts["ocr_markdown"] = len(ocr_md_files)
        print(f"  OCR markdown files: {len(ocr_md_files):,}")

    return other_counts

def load_classifications() -> Dict[str, Any]:
    """Load existing document classifications."""
    classifications_file = METADATA_DIR / "document_classifications.json"

    if not classifications_file.exists():
        return {
            "total_documents": 0,
            "results": {}
        }

    with open(classifications_file) as f:
        return json.load(f)

def build_comprehensive_stats() -> Dict[str, Any]:
    """Build comprehensive document statistics."""
    print("\n" + "="*80)
    print("BUILDING COMPREHENSIVE DOCUMENT STATISTICS")
    print("="*80 + "\n")

    # Count all document types
    pdf_counts = count_pdfs_by_source()
    email_counts = count_emails_by_source()
    entity_counts = count_entity_documents()
    other_counts = count_other_documents()

    # Load classifications
    classifications = load_classifications()

    # Calculate totals
    total_pdfs = sum(pdf_counts.values())
    total_emails = sum(c["count"] for c in email_counts.values())
    total_entities = entity_counts.get("markdown_files", 0)
    total_ocr = other_counts.get("ocr_markdown", 0)

    # Grand total (unique documents - PDFs are primary)
    grand_total = total_pdfs + total_emails + total_entities

    # Build comprehensive stats
    stats = {
        "generated": datetime.now().isoformat(),
        "summary": {
            "total_documents": grand_total,
            "total_pdfs": total_pdfs,
            "total_emails": total_emails,
            "total_entity_documents": total_entities,
            "total_ocr_markdown": total_ocr,
            "total_classified": classifications.get("total_documents", 0)
        },
        "by_source": {
            "pdfs": pdf_counts,
            "emails": email_counts
        },
        "entity_documents": entity_counts,
        "other_documents": other_counts,
        "classifications": {
            "total": classifications.get("total_documents", 0),
            "by_type": count_by_classification_type(classifications)
        }
    }

    return stats

def count_by_classification_type(classifications: Dict[str, Any]) -> Dict[str, int]:
    """Count documents by classification type."""
    type_counts = defaultdict(int)

    for doc_data in classifications.get("results", {}).values():
        doc_type = doc_data.get("type", "unknown")
        type_counts[doc_type] += 1

    return dict(type_counts)

def save_stats(stats: Dict[str, Any]) -> None:
    """Save statistics to metadata directory."""
    output_file = METADATA_DIR / "comprehensive_document_stats.json"

    with open(output_file, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n✅ Statistics saved to: {output_file}")

    # Also create a human-readable report
    report_file = METADATA_DIR / "comprehensive_document_stats.txt"

    with open(report_file, "w") as f:
        f.write("="*80 + "\n")
        f.write("COMPREHENSIVE DOCUMENT STATISTICS\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {stats['generated']}\n\n")

        f.write("SUMMARY\n")
        f.write("-"*80 + "\n")
        summary = stats["summary"]
        f.write(f"Total Documents: {summary['total_documents']:,}\n")
        f.write(f"  - PDFs: {summary['total_pdfs']:,}\n")
        f.write(f"  - Emails: {summary['total_emails']:,}\n")
        f.write(f"  - Entity Documents: {summary['total_entity_documents']:,}\n")
        f.write(f"  - OCR Markdown: {summary['total_ocr_markdown']:,}\n")
        f.write(f"  - Classified: {summary['total_classified']:,}\n\n")

        f.write("PDFs BY SOURCE\n")
        f.write("-"*80 + "\n")
        for source, count in sorted(stats["by_source"]["pdfs"].items(),
                                    key=lambda x: x[1], reverse=True):
            f.write(f"  {source}: {count:,}\n")

        f.write("\nEMAILS BY SOURCE\n")
        f.write("-"*80 + "\n")
        for source, data in sorted(stats["by_source"]["emails"].items(),
                                   key=lambda x: x[1]["count"], reverse=True):
            f.write(f"  {source}: {data['count']:,}\n")

        f.write("\nCLASSIFICATIONS BY TYPE\n")
        f.write("-"*80 + "\n")
        for doc_type, count in sorted(stats["classifications"]["by_type"].items(),
                                      key=lambda x: x[1], reverse=True):
            f.write(f"  {doc_type}: {count:,}\n")

    print(f"✅ Report saved to: {report_file}")

def print_summary(stats: Dict[str, Any]) -> None:
    """Print summary to console."""
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80 + "\n")

    summary = stats["summary"]
    print(f"📊 Total Documents: {summary['total_documents']:,}")
    print(f"   📄 PDFs: {summary['total_pdfs']:,}")
    print(f"   📧 Emails: {summary['total_emails']:,}")
    print(f"   👥 Entity Documents: {summary['total_entity_documents']:,}")
    print(f"   📝 OCR Markdown: {summary['total_ocr_markdown']:,}")
    print(f"   🏷️  Classified: {summary['total_classified']:,}")

    print("\n🎯 Top Sources:")
    pdf_sources = sorted(stats["by_source"]["pdfs"].items(),
                        key=lambda x: x[1], reverse=True)[:5]
    for source, count in pdf_sources:
        print(f"   {source}: {count:,} PDFs")

def main():
    """Main execution."""
    try:
        # Ensure metadata directory exists
        METADATA_DIR.mkdir(exist_ok=True)

        # Build stats
        stats = build_comprehensive_stats()

        # Save results
        save_stats(stats)

        # Print summary
        print_summary(stats)

        print("\n✅ Document statistics rebuild complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
