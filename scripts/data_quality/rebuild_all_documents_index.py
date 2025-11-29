#!/usr/bin/env python3
"""
Rebuild All Documents Index

Combines categorized PDFs from master_document_index_categorized.json
with emails to create a proper all_documents_index.json.
"""

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def rebuild_all_documents_index(
    master_categorized: str, old_all_documents: str, output_file: str, backup: bool = True
) -> dict:
    """
    Rebuild all_documents_index.json from categorized master and emails.

    Args:
        master_categorized: Path to master_document_index_categorized.json
        old_all_documents: Path to old all_documents_index.json (for emails)
        output_file: Path to save new all_documents_index.json
        backup: Whether to create backup

    Returns:
        Dict with rebuild statistics
    """
    logger.info(f"Loading categorized PDFs from {master_categorized}")
    with open(master_categorized) as f:
        master_data = json.load(f)

    logger.info(f"Loading emails from {old_all_documents}")
    with open(old_all_documents) as f:
        old_all_docs = json.load(f)

    # Create backup if requested
    if backup:
        backup_path = f"{old_all_documents}.rebuild_backup"
        with open(backup_path, "w") as f:
            json.dump(old_all_docs, f, indent=2)
        logger.info(f"Created backup at {backup_path}")

    # Extract emails from old index
    old_documents = old_all_docs.get("documents", [])
    emails = [doc for doc in old_documents if doc.get("type") == "email"]
    logger.info(f"Found {len(emails)} email documents")

    # Build new documents list from PDFs
    new_documents = []

    for pdf_doc in master_data.get("documents", []):
        # Convert master format to all_documents format
        new_doc = {
            "id": pdf_doc.get("hash", "unknown"),
            "type": "pdf",
            "source": pdf_doc.get("source", "unknown"),
            "path": pdf_doc.get("canonical_path", ""),
            "filename": (
                Path(pdf_doc.get("canonical_path", "")).name
                if pdf_doc.get("canonical_path")
                else ""
            ),
            "file_size": pdf_doc.get("size", 0),
            "date_extracted": None,
            "classification": pdf_doc.get("classification", "unknown"),
            "classification_confidence": pdf_doc.get("classification_confidence", 0.0),
            "entities_mentioned": [],
            "doc_type": pdf_doc.get("doc_type", "pdf"),
        }
        new_documents.append(new_doc)

    # Add emails
    logger.info(f"Adding {len(emails)} emails to index")
    for email in emails:
        # Ensure emails have proper classification
        if email.get("classification") != "email":
            email["classification"] = "email"
            email["classification_confidence"] = 0.99
        new_documents.append(email)

    logger.info(f"Total documents in new index: {len(new_documents)}")

    # Calculate statistics
    classification_counts = Counter()
    source_counts = Counter()
    type_counts = Counter()

    for doc in new_documents:
        classification = doc.get("classification", "unknown")
        source = doc.get("source", "unknown")
        doc_type = doc.get("type", "unknown")

        classification_counts[classification] += 1
        source_counts[source] += 1
        type_counts[doc_type] += 1

    # Build new all_documents_index
    new_index = {
        "generated": datetime.now().isoformat(),
        "version": "2.0",
        "sources": {
            "master_document_index": str(master_categorized),
            "email_documents": f"{len(emails)} emails from {old_all_documents}",
        },
        "total_documents": len(new_documents),
        "statistics": {
            "by_source": dict(source_counts),
            "by_type": dict(type_counts),
            "by_classification": dict(classification_counts),
        },
        "documents": new_documents,
    }

    # Save new index
    logger.info(f"Saving rebuilt index to {output_file}")
    with open(output_file, "w") as f:
        json.dump(new_index, f, indent=2)

    stats = {
        "total_documents": len(new_documents),
        "pdfs": len(new_documents) - len(emails),
        "emails": len(emails),
        "by_classification": dict(classification_counts),
        "by_source": dict(source_counts),
    }

    return stats


def print_rebuild_stats(stats: dict):
    """Print rebuild statistics."""

    print("\n" + "=" * 70)
    print("ALL DOCUMENTS INDEX REBUILT")
    print("=" * 70)

    print(f"\nTotal documents: {stats['total_documents']:,}")
    print(f"  PDF documents: {stats['pdfs']:,}")
    print(f"  Email documents: {stats['emails']:,}")

    print("\n" + "-" * 70)
    print("CLASSIFICATION BREAKDOWN")
    print("-" * 70)

    for classification, count in sorted(stats["by_classification"].items(), key=lambda x: -x[1]):
        percentage = (count / stats["total_documents"]) * 100
        bar_length = int(percentage / 2)
        bar = "█" * bar_length
        print(f"{classification:25} {count:>6,} ({percentage:>5.1f}%) {bar}")

    print("\n" + "-" * 70)
    print("SOURCE BREAKDOWN (Top 10)")
    print("-" * 70)

    for source, count in sorted(stats["by_source"].items(), key=lambda x: -x[1])[:10]:
        percentage = (count / stats["total_documents"]) * 100
        print(f"{source:35} {count:>6,} ({percentage:>5.1f}%)")

    print("\n" + "=" * 70)


def main():
    """Main execution function."""

    # File paths
    project_root = Path(__file__).parent.parent.parent

    master_categorized = (
        project_root / "data" / "metadata" / "master_document_index_categorized.json"
    )
    old_all_documents = project_root / "data" / "metadata" / "all_documents_index.json"
    output_file = old_all_documents  # Overwrite

    # Run rebuild
    stats = rebuild_all_documents_index(
        str(master_categorized), str(old_all_documents), str(output_file), backup=True
    )

    # Print results
    print_rebuild_stats(stats)

    print("\n✅ Rebuilt all_documents_index.json with proper categorizations")
    print("✅ Backup saved to all_documents_index.json.rebuild_backup")


if __name__ == "__main__":
    main()
