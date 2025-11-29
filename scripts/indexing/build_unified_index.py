#!/usr/bin/env python3
"""
Build unified document index combining all document sources:
- 38,177 PDFs from master_document_index.json
- 305 classified emails from email_classifications.json
- Entity documents (flight logs, black book, etc.)

Outputs comprehensive index with document type, classification, and metadata.
"""

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
MASTER_DOC_INDEX = METADATA_DIR / "master_document_index.json"
EMAIL_CLASSIFICATIONS = METADATA_DIR / "email_classifications.json"
DOC_CLASSIFICATIONS = METADATA_DIR / "document_classifications.json"
SEMANTIC_INDEX = METADATA_DIR / "semantic_index.json"
OUTPUT_FILE = METADATA_DIR / "all_documents_index.json"


def load_json_file(filepath: Path) -> dict:
    """Load JSON file with progress indicator."""
    print(f"Loading {filepath.name}...")
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def build_unified_index() -> dict[str, Any]:
    """Build comprehensive document index from all sources."""
    print("\n" + "=" * 80)
    print("BUILDING UNIFIED DOCUMENT INDEX")
    print("=" * 80 + "\n")

    # Load all data sources
    master_index = load_json_file(MASTER_DOC_INDEX)
    email_classifications = load_json_file(EMAIL_CLASSIFICATIONS)
    doc_classifications = load_json_file(DOC_CLASSIFICATIONS)

    # Load semantic index if exists
    semantic_index = {}
    if SEMANTIC_INDEX.exists():
        semantic_index = load_json_file(SEMANTIC_INDEX)

    print(f"✓ Loaded {len(master_index.get('documents', []))} PDFs from master index")
    print(f"✓ Loaded {email_classifications.get('total', 0)} classified emails")
    print(f"✓ Loaded {len(doc_classifications.get('results', {}))} document classifications")
    print()

    # Initialize unified index
    unified_index = {
        "generated": datetime.now().isoformat(),
        "version": "1.0",
        "sources": {
            "master_document_index": str(MASTER_DOC_INDEX),
            "email_classifications": str(EMAIL_CLASSIFICATIONS),
            "document_classifications": str(DOC_CLASSIFICATIONS),
            "semantic_index": str(SEMANTIC_INDEX) if SEMANTIC_INDEX.exists() else None,
        },
        "total_documents": 0,
        "statistics": {
            "by_source": Counter(),
            "by_type": Counter(),
            "by_classification": Counter(),
            "by_date": Counter(),
        },
        "documents": [],
    }

    # Process PDFs from master index
    print("Processing PDF documents...")
    pdf_count = 0
    for doc in master_index.get("documents", []):
        doc_id = doc.get("document_id", "unknown")

        # Get classification if exists
        doc_path = doc.get("file_path", "")
        classification_info = None
        for path, class_data in doc_classifications.get("results", {}).items():
            if doc_id in path or doc_path in path:
                classification_info = class_data
                break

        # Build unified document entry
        unified_doc = {
            "id": doc_id,
            "type": "pdf",
            "source": doc.get("source", "unknown"),
            "path": doc_path,
            "filename": doc.get("filename", ""),
            "file_size": doc.get("file_size", 0),
            "date_extracted": doc.get("date_extracted"),
            "classification": classification_info.get("type") if classification_info else None,
            "classification_confidence": (
                classification_info.get("confidence") if classification_info else None
            ),
            "entities_mentioned": [],
        }

        # Add to index
        unified_index["documents"].append(unified_doc)
        unified_index["statistics"]["by_source"][unified_doc["source"]] += 1
        unified_index["statistics"]["by_type"]["pdf"] += 1
        if unified_doc["classification"]:
            unified_index["statistics"]["by_classification"][unified_doc["classification"]] += 1

        pdf_count += 1
        if pdf_count % 5000 == 0:
            print(f"  Processed {pdf_count} PDFs...")

    print(f"✓ Processed {pdf_count} PDF documents")

    # Process emails
    print("\nProcessing email documents...")
    email_count = 0
    for email_path, email_data in email_classifications.get("classifications", {}).items():
        doc_id = email_data.get("document_id", f"email_{email_count}")

        # Extract date from email metadata
        email_meta = email_data.get("email_metadata", {})
        email_date = email_meta.get("date", "")

        # Parse year-month from date if possible
        date_key = None
        if email_date:
            # Try to extract year-month (e.g., "2019-08")
            import re

            date_match = re.search(r"(\d{4})-(\d{2})", email_date)
            if date_match:
                date_key = f"{date_match.group(1)}-{date_match.group(2)}"
            else:
                # Try other formats
                date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", email_date)
                if date_match:
                    year = date_match.group(3)
                    month = date_match.group(1).zfill(2)
                    date_key = f"{year}-{month}"

        # Build unified document entry
        unified_doc = {
            "id": doc_id,
            "type": "email",
            "source": email_data.get("source", "house_oversight_nov2025"),
            "path": email_path,
            "filename": Path(email_path).name,
            "date": email_date,
            "date_parsed": date_key,
            "from": email_meta.get("from"),
            "to": email_meta.get("to"),
            "subject": email_meta.get("subject"),
            "classification": email_data.get("type"),
            "classification_confidence": email_data.get("confidence"),
            "secondary_classifications": email_data.get("secondary_types", []),
            "keywords": email_data.get("keywords", []),
            "entities_mentioned": [],
        }

        # Add to index
        unified_index["documents"].append(unified_doc)
        unified_index["statistics"]["by_source"][unified_doc["source"]] += 1
        unified_index["statistics"]["by_type"]["email"] += 1
        unified_index["statistics"]["by_classification"][unified_doc["classification"]] += 1
        if date_key:
            unified_index["statistics"]["by_date"][date_key] += 1

        email_count += 1

    print(f"✓ Processed {email_count} email documents")

    # Add entity mentions from semantic index
    if semantic_index and "entity_mentions" in semantic_index:
        print("\nAdding entity mentions...")
        entity_mentions = semantic_index["entity_mentions"]
        entity_count = 0

        for doc in unified_index["documents"]:
            doc_path = doc.get("path", "")
            # Check if document has entity mentions
            for entity, mentions in entity_mentions.items():
                for mention in mentions:
                    if mention.get("document") in doc_path or doc_path in mention.get(
                        "document", ""
                    ):
                        if entity not in doc["entities_mentioned"]:
                            doc["entities_mentioned"].append(entity)
                            entity_count += 1

        print(f"✓ Added {entity_count} entity mentions")

    # Update total count
    unified_index["total_documents"] = len(unified_index["documents"])

    # Convert Counters to dicts for JSON serialization
    unified_index["statistics"]["by_source"] = dict(unified_index["statistics"]["by_source"])
    unified_index["statistics"]["by_type"] = dict(unified_index["statistics"]["by_type"])
    unified_index["statistics"]["by_classification"] = dict(
        unified_index["statistics"]["by_classification"]
    )
    unified_index["statistics"]["by_date"] = dict(
        sorted(unified_index["statistics"]["by_date"].items())
    )

    return unified_index


def save_index(index: dict[str, Any]) -> None:
    """Save unified index to file."""
    print(f"\nSaving unified index to {OUTPUT_FILE}...")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print(f"✅ Saved {len(index['documents'])} documents to {OUTPUT_FILE}")


def print_summary(index: dict[str, Any]) -> None:
    """Print index summary."""
    print("\n" + "=" * 80)
    print("UNIFIED DOCUMENT INDEX SUMMARY")
    print("=" * 80 + "\n")

    print(f"Total Documents: {index['total_documents']:,}")
    print(f"Generated: {index['generated']}")
    print()

    print("Documents by Type:")
    for doc_type, count in sorted(
        index["statistics"]["by_type"].items(), key=lambda x: x[1], reverse=True
    ):
        pct = (count / index["total_documents"] * 100) if index["total_documents"] > 0 else 0
        print(f"  {doc_type:20s}: {count:7,d} ({pct:5.1f}%)")

    print("\nDocuments by Source:")
    for source, count in sorted(
        index["statistics"]["by_source"].items(), key=lambda x: x[1], reverse=True
    ):
        pct = (count / index["total_documents"] * 100) if index["total_documents"] > 0 else 0
        print(f"  {source:30s}: {count:7,d} ({pct:5.1f}%)")

    print("\nDocuments by Classification:")
    classified_count = sum(
        count
        for class_type, count in index["statistics"]["by_classification"].items()
        if class_type
    )
    print(
        f"  Total Classified: {classified_count:,} ({(classified_count/index['total_documents']*100):.1f}%)"
    )
    print()
    for class_type, count in sorted(
        index["statistics"]["by_classification"].items(), key=lambda x: x[1], reverse=True
    )[
        :10
    ]:  # Top 10
        pct = (count / classified_count * 100) if classified_count > 0 else 0
        print(f"    {class_type:20s}: {count:6,d} ({pct:5.1f}%)")

    if index["statistics"]["by_date"]:
        print("\nDocuments by Date (Top 10):")
        for date, count in sorted(
            index["statistics"]["by_date"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  {date}: {count:,}")

    print("\n" + "=" * 80)


def main():
    """Main execution."""
    try:
        # Build unified index
        unified_index = build_unified_index()

        # Save index
        save_index(unified_index)

        # Print summary
        print_summary(unified_index)

        print("\n✅ Unified document index built successfully!")
        print(f"\n📄 Output: {OUTPUT_FILE}")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
