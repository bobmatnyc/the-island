#!/usr/bin/env python3
"""
Merge Categorizations Script

Merges improved categorizations from master_document_index_categorized.json
into all_documents_index.json (which includes both PDFs and emails).
"""

import json
import logging
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def merge_categorizations(
    master_categorized: str, all_documents: str, output_file: str, backup: bool = True
) -> dict:
    """
    Merge categorizations from master index into all documents index.

    Args:
        master_categorized: Path to master_document_index_categorized.json
        all_documents: Path to all_documents_index.json
        output_file: Path to save updated all_documents_index.json
        backup: Whether to create backup

    Returns:
        Dict with merge statistics
    """
    logger.info(f"Loading master categorized index from {master_categorized}")
    with open(master_categorized) as f:
        master_data = json.load(f)

    logger.info(f"Loading all documents index from {all_documents}")
    with open(all_documents) as f:
        all_docs_data = json.load(f)

    # Create backup if requested
    if backup:
        backup_path = f"{all_documents}.backup"
        with open(backup_path, "w") as f:
            json.dump(all_docs_data, f, indent=2)
        logger.info(f"Created backup at {backup_path}")

    # Build hash -> categorization mapping from master index
    hash_to_category = {}
    for doc in master_data.get("documents", []):
        doc_hash = doc.get("hash")
        if doc_hash:
            hash_to_category[doc_hash] = {
                "classification": doc.get("classification"),
                "classification_confidence": doc.get("classification_confidence"),
                "source": doc.get("source"),
                "doc_type": doc.get("doc_type"),
            }

    logger.info(f"Built categorization mapping for {len(hash_to_category)} documents")

    # Update documents in all_documents_index
    all_documents_list = all_docs_data.get("documents", [])
    updated_count = 0
    email_count = 0

    for doc in all_documents_list:
        # Check if this is an email (already properly categorized)
        if doc.get("type") == "email":
            email_count += 1
            # Ensure email classification is correct
            if doc.get("classification") != "email":
                doc["classification"] = "email"
                doc["classification_confidence"] = 0.99
                updated_count += 1
            continue

        # For PDFs, try to match by path or other identifier
        doc_path = doc.get("path", "")

        # Try to find matching categorization
        matched = False
        for master_doc in master_data.get("documents", []):
            master_path = master_doc.get("canonical_path", "")

            # Match by path
            if doc_path and master_path and doc_path == master_path:
                doc["classification"] = master_doc.get("classification")
                doc["classification_confidence"] = master_doc.get("classification_confidence")
                doc["source"] = master_doc.get("source")
                if "doc_type" not in doc or doc["doc_type"] == "unknown":
                    doc["doc_type"] = master_doc.get("doc_type", "pdf")
                updated_count += 1
                matched = True
                break

        # If not matched and is PDF, mark as administrative with low confidence
        if not matched and doc.get("type") == "pdf":
            if doc.get("classification") == "unknown" or not doc.get("classification"):
                doc["classification"] = "administrative"
                doc["classification_confidence"] = 0.3
                doc["source"] = "unknown"
                doc["doc_type"] = "pdf"
                updated_count += 1

    # Update statistics in all_documents_index
    if "statistics" not in all_docs_data:
        all_docs_data["statistics"] = {}

    # Recalculate statistics
    classification_counts = {}
    source_counts = {}
    type_counts = {}

    for doc in all_documents_list:
        classification = doc.get("classification", "unknown")
        source = doc.get("source", "unknown")
        doc_type = doc.get("type", "unknown")

        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    all_docs_data["statistics"]["by_classification"] = classification_counts
    all_docs_data["statistics"]["by_source"] = source_counts
    all_docs_data["statistics"]["by_type"] = type_counts

    # Save updated index
    logger.info(f"Saving updated index to {output_file}")
    with open(output_file, "w") as f:
        json.dump(all_docs_data, f, indent=2)

    stats = {
        "total_documents": len(all_documents_list),
        "updated": updated_count,
        "emails": email_count,
        "by_classification": classification_counts,
        "by_source": source_counts,
    }

    return stats


def print_merge_stats(stats: dict):
    """Print merge statistics."""

    print("\n" + "=" * 70)
    print("CATEGORIZATION MERGE COMPLETE")
    print("=" * 70)

    print(f"\nTotal documents: {stats['total_documents']:,}")
    print(f"Documents updated: {stats['updated']:,}")
    print(f"Email documents: {stats['emails']:,}")

    print("\n" + "-" * 70)
    print("CLASSIFICATION BREAKDOWN")
    print("-" * 70)

    for classification, count in sorted(stats["by_classification"].items(), key=lambda x: -x[1]):
        percentage = (count / stats["total_documents"]) * 100
        bar_length = int(percentage / 2)
        bar = "█" * bar_length
        print(f"{classification:25} {count:>6,} ({percentage:>5.1f}%) {bar}")

    print("\n" + "=" * 70)


def main():
    """Main execution function."""

    # File paths
    project_root = Path(__file__).parent.parent.parent

    master_categorized = (
        project_root / "data" / "metadata" / "master_document_index_categorized.json"
    )
    all_documents = project_root / "data" / "metadata" / "all_documents_index.json"
    output_file = all_documents  # Overwrite original

    # Run merge
    stats = merge_categorizations(
        str(master_categorized), str(all_documents), str(output_file), backup=True
    )

    # Print results
    print_merge_stats(stats)

    print("\n✅ Updated all_documents_index.json with improved categorizations")
    print("✅ Backup saved to all_documents_index.json.backup")


if __name__ == "__main__":
    main()
