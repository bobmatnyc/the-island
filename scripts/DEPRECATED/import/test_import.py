#!/usr/bin/env python3
"""
Test script to verify Hugging Face document import.

This script demonstrates how to access the imported documents.
"""

import json
from pathlib import Path


def main():
    """Test imported document access."""
    print("=" * 60)
    print("HUGGING FACE DOCUMENT IMPORT TEST")
    print("=" * 60)

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    import_dir = (
        project_root
        / "data"
        / "sources"
        / "house_oversight_nov2025"
        / "documents"
        / "huggingface_imported"
    )

    # Load metadata
    print("\n1. Loading import metadata...")
    metadata_path = import_dir / "import_metadata.json"
    if not metadata_path.exists():
        print(f"❌ Error: Metadata file not found at {metadata_path}")
        print("Have you run the import script yet?")
        return

    with open(metadata_path) as f:
        metadata = json.load(f)

    print(f"✓ Import Date: {metadata['import_date']}")
    print(f"✓ Total Imported: {metadata['statistics']['successful_imports']:,}")
    print(f"✓ Total Characters: {metadata['statistics']['total_characters']:,}")
    print(f"✓ Avg Document Length: {metadata['statistics']['avg_document_length']:,} chars")

    # Load document index
    print("\n2. Loading document index...")
    index_path = import_dir / "document_index.json"
    with open(index_path) as f:
        documents = json.load(f)

    print(f"✓ Index loaded: {len(documents):,} documents")

    # Show document breakdown by prefix
    print("\n3. Documents by prefix:")
    by_prefix = metadata["statistics"]["documents_by_prefix"]
    for prefix, count in sorted(by_prefix.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  • {prefix}: {count:,} documents")

    # Load and display sample documents
    print("\n4. Sample Documents:")
    sample_docs = documents[:3]  # First 3 documents

    for i, doc_entry in enumerate(sample_docs, 1):
        doc_path = import_dir / doc_entry["json_file"]
        with open(doc_path) as f:
            doc = json.load(f)

        print(f"\n  Document {i}:")
        print(f"  • ID: {doc['document_id']}")
        print(f"  • Filename: {doc['filename']}")
        print(f"  • Words: {doc['metadata']['word_count']:,}")
        print(f"  • Characters: {doc['metadata']['character_count']:,}")
        print(f"  • Preview: {doc['text'][:150]}...")

    # Statistics
    print("\n5. Document Statistics:")
    word_counts = [d["word_count"] for d in documents]
    print(f"  • Total documents: {len(documents):,}")
    print(f"  • Min words: {min(word_counts):,}")
    print(f"  • Max words: {max(word_counts):,}")
    print(f"  • Avg words: {sum(word_counts) // len(word_counts):,}")

    # Large documents
    large_docs = [d for d in documents if d["word_count"] > 1000]
    print(f"\n  • Documents > 1,000 words: {len(large_docs):,}")

    # Prefixes
    prefixes = set(d["filename"].split("-")[0] for d in documents if "-" in d["filename"])
    print(f"  • Unique prefixes: {len(prefixes)}")

    print("\n" + "=" * 60)
    print("✓ All tests passed! Import successful.")
    print("=" * 60)
    print(f"\nData location: {import_dir}")
    print(f"Index file: {index_path}")
    print(f"Metadata file: {metadata_path}")
    print("\nYou can now use these documents for analysis!")


if __name__ == "__main__":
    main()
