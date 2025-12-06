#!/usr/bin/env python3
"""
Generate deterministic UUIDs for documents and create mapping file.

This script:
1. Generates UUID5 from source file paths (deterministic)
2. Maps existing document IDs (SHA256, Bates numbers) to UUIDs
3. Creates mapping file for cross-reference
4. Transforms documents to canonical schema

Usage:
    python scripts/transformations/generate_document_uuids.py [--limit N]
"""

import json
import uuid
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

# UUID namespace for documents (DNS namespace)
DOCUMENT_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

def generate_document_uuid(source_path: str) -> str:
    """
    Generate deterministic UUID5 from source file path.

    Args:
        source_path: Relative path to source file

    Returns:
        UUID string in canonical form

    Design Decision: UUID5 with DNS namespace ensures:
    - Deterministic: Same path always generates same UUID
    - Collision-resistant: Different paths generate different UUIDs
    - Standard: Uses official UUID5 specification (RFC 4122)
    """
    # Normalize path separators and remove leading slashes
    normalized_path = source_path.replace('\\', '/').lstrip('/')

    # Generate UUID5 from normalized path
    return str(uuid.uuid5(DOCUMENT_NAMESPACE, normalized_path))


def extract_title_from_document(doc: dict[str, Any]) -> str:
    """
    Extract human-readable title from document metadata.

    Priority:
    1. Email subject
    2. Cleaned filename
    3. Original filename

    Args:
        doc: Document dictionary

    Returns:
        Document title string
    """
    # Email: use subject
    if doc.get('type') == 'email' and doc.get('subject'):
        return doc['subject'][:200]  # Truncate long subjects

    # PDF: clean filename
    filename = doc.get('filename', 'Untitled Document')

    # Remove extension and common prefixes
    title = filename.replace('.pdf', '').replace('.json', '')
    title = title.replace('_metadata', '')

    # Replace underscores and hyphens with spaces
    title = title.replace('_', ' ').replace('-', ' ')

    # Capitalize words
    title = ' '.join(word.capitalize() for word in title.split())

    return title


def parse_document_date(doc: dict[str, Any]) -> dict[str, str | None]:
    """
    Parse document date into ISO format.

    Returns dict with:
    - date: ISO 8601 date (YYYY-MM-DD) or None
    - date_raw: Original date string

    Args:
        doc: Document dictionary

    Returns:
        Dict with parsed and raw dates
    """
    result: dict[str, str | None] = {
        'date': None,
        'date_raw': None
    }

    # Email documents
    if doc.get('type') == 'email':
        if 'date' in doc:
            result['date_raw'] = doc['date']

            # Try parsed date if available
            if doc.get('date_parsed'):
                result['date'] = doc['date_parsed']
                # Normalize to YYYY-MM-DD if needed
                if len(result['date']) == 7:  # YYYY-MM format
                    result['date'] = f"{result['date']}-01"

    # Check date_extracted field for PDFs
    elif doc.get('date_extracted'):
        result['date_raw'] = doc['date_extracted']
        # Would need date parsing logic here

    return result


def classify_document_type(doc: dict[str, Any]) -> tuple[str, float]:
    """
    Map existing classification to canonical document_type.

    Returns:
        Tuple of (document_type, confidence)
    """
    classification = doc.get('classification', 'other')
    confidence = doc.get('classification_confidence', 0.5)

    # Direct mappings
    type_mapping = {
        'email': 'email',
        'court_filing': 'court_record',
        'administrative': 'administrative',
        'contact_directory': 'contact_directory',
        'government_document': 'government_document',
        'media_article': 'media_article'
    }

    document_type = type_mapping.get(classification, 'other')

    return document_type, confidence


def transform_document(doc: dict[str, Any]) -> dict[str, Any]:
    """
    Transform document from legacy format to canonical schema.

    Args:
        doc: Legacy document dictionary

    Returns:
        Transformed document matching canonical schema
    """
    # Generate UUID from source path
    source_path = doc.get('path', '')
    document_id = generate_document_uuid(source_path)

    # Extract title
    title = extract_title_from_document(doc)

    # Parse dates
    dates = parse_document_date(doc)

    # Classify document
    document_type, classification_confidence = classify_document_type(doc)

    # Build canonical document
    canonical = {
        'document_id': document_id,
        'document_type': document_type,
        'title': title,
        'source_path': source_path,
        'source_checksum': doc.get('id', ''),  # Legacy SHA256 ID
        'classification_confidence': classification_confidence
    }

    # Add optional date field
    if dates['date']:
        canonical['date'] = dates['date']
    if dates['date_raw']:
        canonical['date_raw'] = dates['date_raw']

    # Add metadata based on document type
    metadata: dict[str, Any] = {
        'source_metadata': {
            'source_collection': doc.get('source', 'unknown'),
            'source_id': doc.get('id', ''),
            'original_filename': doc.get('filename', ''),
            'file_size': doc.get('file_size', 0)
        }
    }

    # Email-specific metadata
    if doc.get('type') == 'email':
        metadata['email'] = {
            'from': doc.get('from', ''),
            'to': doc.get('to', ''),
            'subject': doc.get('subject', ''),
            'sent_date': dates['date_raw'] or ''
        }

        # Add CC and BCC if available
        if doc.get('cc'):
            metadata['email']['cc'] = doc['cc']
        if doc.get('bcc'):
            metadata['email']['bcc'] = doc['bcc']

    canonical['metadata'] = metadata

    # Map legacy IDs for backward compatibility
    legacy_ids: dict[str, str] = {}

    if doc.get('id') and len(doc['id']) == 64:
        legacy_ids['sha256'] = doc['id']
    elif doc.get('id'):
        legacy_ids['source_id'] = doc['id']

    if legacy_ids:
        canonical['legacy_ids'] = legacy_ids

    # Add extracted entities if available
    if doc.get('entities_mentioned'):
        canonical['extracted_entities'] = doc['entities_mentioned']

    # Processing status
    canonical['processing_status'] = {
        'extracted': bool(doc.get('date_extracted') or doc.get('type') == 'email'),
        'classified': True,
        'entities_linked': bool(doc.get('entities_mentioned')),
        'indexed_chromadb': False,
        'last_updated': datetime.utcnow().isoformat() + 'Z'
    }

    return canonical


def create_uuid_mapping(doc: dict[str, Any], canonical: dict[str, Any]) -> dict[str, Any]:
    """
    Create mapping entry for old ID to new UUID.

    Args:
        doc: Legacy document
        canonical: Transformed document

    Returns:
        Mapping dictionary
    """
    return {
        'document_id': canonical['document_id'],
        'legacy_ids': canonical.get('legacy_ids', {}),
        'source_path': canonical['source_path'],
        'document_type': canonical['document_type'],
        'title': canonical['title']
    }


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate document UUIDs and mappings')
    parser.add_argument('--limit', type=int, help='Limit number of documents to process')
    parser.add_argument('--sample', action='store_true', help='Process sample (100 documents)')
    args = parser.parse_args()

    # Set limit
    limit = args.limit if args.limit else (100 if args.sample else None)

    print("=" * 80)
    print("Document UUID Generation and Transformation")
    print("=" * 80)
    print()

    # Load all_documents_index
    index_path = Path('data/metadata/all_documents_index.json')
    print(f"Loading: {index_path}")

    with open(index_path, 'r') as f:
        index_data = json.load(f)

    documents = index_data['documents']
    total_docs = len(documents)

    print(f"Total documents: {total_docs:,}")

    if limit:
        documents = documents[:limit]
        print(f"Processing: {len(documents):,} documents (limited)")
    else:
        print(f"Processing: ALL {len(documents):,} documents")

    print()

    # Transform documents
    transformed_docs = []
    uuid_mappings = []

    print("Transforming documents...")
    for i, doc in enumerate(documents):
        if i % 1000 == 0 and i > 0:
            print(f"  Processed {i:,} documents...")

        canonical = transform_document(doc)
        transformed_docs.append(canonical)

        mapping = create_uuid_mapping(doc, canonical)
        uuid_mappings.append(mapping)

    print(f"✓ Transformed {len(transformed_docs):,} documents")
    print()

    # Generate statistics
    type_counts: dict[str, int] = {}
    for doc in transformed_docs:
        doc_type = doc['document_type']
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    print("Document Type Distribution:")
    for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(transformed_docs)) * 100
        print(f"  {doc_type:20s}: {count:6,} ({pct:5.1f}%)")
    print()

    # Save outputs
    output_dir = Path('data/transformed')
    output_dir.mkdir(exist_ok=True)

    # Save transformed documents
    if limit and limit <= 100:
        docs_output = output_dir / 'documents_sample.json'
    else:
        docs_output = output_dir / 'documents_canonical.json'

    print(f"Saving: {docs_output}")
    with open(docs_output, 'w') as f:
        json.dump({
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'schema_version': '1.0',
            'total_documents': len(transformed_docs),
            'documents': transformed_docs
        }, f, indent=2)

    # Save UUID mappings
    mappings_output = output_dir / 'document_uuid_mappings.json'
    print(f"Saving: {mappings_output}")
    with open(mappings_output, 'w') as f:
        json.dump({
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'total_mappings': len(uuid_mappings),
            'mappings': uuid_mappings
        }, f, indent=2)

    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print()
    print(f"Transformed documents: {docs_output}")
    print(f"UUID mappings: {mappings_output}")
    print()
    print("Next steps:")
    print("1. Validate schema compliance: scripts/validation/validate_documents.py")
    print("2. Process remaining documents: run without --sample flag")
    print("3. Update entity references to use document UUIDs")
    print()


if __name__ == '__main__':
    main()
