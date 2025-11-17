#!/usr/bin/env python3
"""
Build unified document index linking all documents across sources.

Creates a single source of truth for all documents with:
- Document ID
- File path
- Document type (classification)
- Source
- Metadata (dates, entities, etc.)
- Links between emails and source PDFs
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# Paths
PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
SOURCES_DIR = DATA_DIR / "sources"
EMAILS_DIR = DATA_DIR / "emails"
METADATA_DIR = DATA_DIR / "metadata"
MD_DIR = DATA_DIR / "md"

def extract_doc_id_from_filename(filename: str) -> Optional[str]:
    """Extract DOJ-OGR document ID from filename."""
    # Pattern: DOJ-OGR-XXXXXXXX
    match = re.search(r"(DOJ-OGR-\d{8})", filename)
    if match:
        return match.group(1)
    return None

def extract_doc_id_from_content(text: str) -> Optional[str]:
    """Extract DOJ-OGR document ID from text content."""
    match = re.search(r"(DOJ-OGR-\d{8})", text)
    if match:
        return match.group(1)
    return None

def build_pdf_index() -> Dict[str, Dict[str, Any]]:
    """Index all PDF files."""
    print("Indexing PDF files...")

    pdf_index = {}

    for source_dir in SOURCES_DIR.iterdir():
        if not source_dir.is_dir():
            continue

        source_name = source_dir.name
        pdf_files = list(source_dir.rglob("*.pdf"))

        for pdf_file in pdf_files:
            # Create document ID
            relative_path = pdf_file.relative_to(SOURCES_DIR)
            doc_id = f"pdf_{source_name}_{pdf_file.stem}"

            # Check for DOJ-OGR ID in filename
            doj_id = extract_doc_id_from_filename(pdf_file.name)

            pdf_index[doc_id] = {
                "document_id": doc_id,
                "doj_id": doj_id,
                "source": source_name,
                "type": "pdf",
                "path": str(pdf_file),
                "relative_path": str(relative_path),
                "filename": pdf_file.name,
                "size": pdf_file.stat().st_size,
                "indexed_at": datetime.now().isoformat()
            }

    print(f"  Indexed {len(pdf_index):,} PDFs")
    return pdf_index

def build_email_index() -> Dict[str, Dict[str, Any]]:
    """Index all email files."""
    print("Indexing email files...")

    email_index = {}

    # Load email classifications
    email_classifications_file = METADATA_DIR / "email_classifications.json"
    classifications = {}
    if email_classifications_file.exists():
        with open(email_classifications_file) as f:
            data = json.load(f)
            classifications = data.get("classifications", {})

    for source_dir in EMAILS_DIR.iterdir():
        if not source_dir.is_dir():
            continue

        source_name = source_dir.name
        metadata_files = list(source_dir.rglob("*_metadata.json"))

        for metadata_file in metadata_files:
            # Load metadata
            with open(metadata_file) as f:
                metadata = json.load(f)

            # Get classification if available
            classification = classifications.get(str(metadata_file), {})

            # Extract DOJ-OGR ID
            doj_id = metadata.get("document_id")
            if not doj_id:
                # Try to extract from full text
                full_text_file = metadata_file.with_name(
                    metadata_file.name.replace("_metadata.json", "_full.txt")
                )
                if full_text_file.exists():
                    with open(full_text_file) as f:
                        text = f.read()
                        doj_id = extract_doc_id_from_content(text)

            # Create composite ID
            email_id = f"email_{source_name}_{metadata.get('email_index', 'unknown')}"

            email_index[email_id] = {
                "document_id": email_id,
                "doj_id": doj_id,
                "source": source_name,
                "type": "email",
                "classification": classification.get("type", "unknown"),
                "confidence": classification.get("confidence", 0.0),
                "path": str(metadata_file),
                "metadata": {
                    "from": metadata.get("from_address"),
                    "to": metadata.get("to_address"),
                    "subject": metadata.get("subject"),
                    "date": metadata.get("date"),
                    "email_addresses": metadata.get("email_addresses", [])
                },
                "indexed_at": datetime.now().isoformat()
            }

    print(f"  Indexed {len(email_index):,} emails")
    return email_index

def build_entity_index() -> Dict[str, Dict[str, Any]]:
    """Index entity documents."""
    print("Indexing entity documents...")

    entity_index = {}

    entity_dir = MD_DIR / "entities"
    if not entity_dir.exists():
        return entity_index

    for md_file in entity_dir.glob("*.md"):
        doc_id = f"entity_{md_file.stem}"

        entity_index[doc_id] = {
            "document_id": doc_id,
            "source": "entities",
            "type": "entity_document",
            "path": str(md_file),
            "filename": md_file.name,
            "size": md_file.stat().st_size,
            "indexed_at": datetime.now().isoformat()
        }

    print(f"  Indexed {len(entity_index):,} entity documents")
    return entity_index

def link_emails_to_pdfs(
    email_index: Dict[str, Dict[str, Any]],
    pdf_index: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Link emails to their source PDFs using DOJ-OGR IDs."""
    print("Linking emails to source PDFs...")

    linked_count = 0

    for email_id, email_data in email_index.items():
        doj_id = email_data.get("doj_id")
        if not doj_id:
            continue

        # Find matching PDF
        for pdf_id, pdf_data in pdf_index.items():
            if pdf_data.get("doj_id") == doj_id:
                email_data["source_pdf"] = pdf_id
                email_data["source_pdf_path"] = pdf_data["path"]
                linked_count += 1
                break

    print(f"  Linked {linked_count:,} emails to source PDFs")
    return email_index

def build_unified_index() -> Dict[str, Any]:
    """Build comprehensive unified index."""
    print("\n" + "="*80)
    print("BUILDING UNIFIED DOCUMENT INDEX")
    print("="*80 + "\n")

    # Build indexes
    pdf_index = build_pdf_index()
    email_index = build_email_index()
    entity_index = build_entity_index()

    # Link emails to PDFs
    email_index = link_emails_to_pdfs(email_index, pdf_index)

    # Merge all indexes
    unified = {}
    unified.update(pdf_index)
    unified.update(email_index)
    unified.update(entity_index)

    # Build statistics
    stats = {
        "total_documents": len(unified),
        "by_type": {
            "pdf": len(pdf_index),
            "email": len(email_index),
            "entity_document": len(entity_index)
        },
        "by_source": {},
        "linked_emails": sum(1 for e in email_index.values() if "source_pdf" in e)
    }

    # Count by source
    for doc in unified.values():
        source = doc["source"]
        stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

    return {
        "generated": datetime.now().isoformat(),
        "statistics": stats,
        "documents": unified
    }

def save_unified_index(index: Dict[str, Any]) -> None:
    """Save unified index."""
    output_file = METADATA_DIR / "unified_document_index.json"

    with open(output_file, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\n✅ Unified index saved to: {output_file}")

    # Also create a compact version (statistics only)
    compact_file = METADATA_DIR / "unified_document_stats.json"

    compact = {
        "generated": index["generated"],
        "statistics": index["statistics"]
    }

    with open(compact_file, "w") as f:
        json.dump(compact, f, indent=2)

    print(f"✅ Compact stats saved to: {compact_file}")

def print_summary(index: Dict[str, Any]) -> None:
    """Print summary."""
    print("\n" + "="*80)
    print("UNIFIED INDEX SUMMARY")
    print("="*80 + "\n")

    stats = index["statistics"]
    print(f"Total Documents: {stats['total_documents']:,}")
    print("\nBy Type:")
    for doc_type, count in stats["by_type"].items():
        print(f"  {doc_type}: {count:,}")

    print("\nBy Source (Top 10):")
    top_sources = sorted(stats["by_source"].items(),
                        key=lambda x: x[1], reverse=True)[:10]
    for source, count in top_sources:
        print(f"  {source}: {count:,}")

    print(f"\nLinked Emails: {stats['linked_emails']:,} of {stats['by_type']['email']:,}")

def main():
    """Main execution."""
    try:
        # Build unified index
        index = build_unified_index()

        # Save
        save_unified_index(index)

        # Print summary
        print_summary(index)

        print("\n✅ Unified index build complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
