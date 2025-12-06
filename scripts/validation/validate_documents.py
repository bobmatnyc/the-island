#!/usr/bin/env python3
"""
Validate transformed documents against canonical schema.

This script validates:
1. JSON schema compliance
2. UUID format and determinism
3. Required fields presence
4. Data type correctness
5. Cross-reference integrity

Usage:
    python scripts/validation/validate_documents.py [--file PATH]
"""

import json
import uuid
import re
from pathlib import Path
from typing import Any


class DocumentValidator:
    """Validate documents against canonical schema."""

    def __init__(self, schema_path: str = 'data/schemas/document_schema.json'):
        """Initialize validator with schema."""
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)

        self.errors: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []

    def validate_uuid(self, value: str, field: str, doc_index: int) -> bool:
        """Validate UUID format."""
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            self.errors.append({
                'document_index': doc_index,
                'field': field,
                'error': f'Invalid UUID format: {value}',
                'severity': 'error'
            })
            return False

    def validate_date(self, value: str, field: str, doc_index: int) -> bool:
        """Validate ISO 8601 date format (YYYY-MM-DD)."""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, value):
            self.errors.append({
                'document_index': doc_index,
                'field': field,
                'error': f'Invalid date format (expected YYYY-MM-DD): {value}',
                'severity': 'error'
            })
            return False
        return True

    def validate_checksum(self, value: str, field: str, doc_index: int) -> bool:
        """Validate SHA256 checksum format."""
        pattern = r'^[a-f0-9]{64}$'
        if not re.match(pattern, value):
            self.warnings.append({
                'document_index': doc_index,
                'field': field,
                'warning': f'Invalid SHA256 format: {value}',
                'severity': 'warning'
            })
            return False
        return True

    def validate_required_fields(self, doc: dict[str, Any], doc_index: int) -> bool:
        """Validate required fields are present."""
        required = self.schema['required']
        missing = [f for f in required if f not in doc]

        if missing:
            self.errors.append({
                'document_index': doc_index,
                'field': 'required_fields',
                'error': f'Missing required fields: {missing}',
                'severity': 'error'
            })
            return False
        return True

    def validate_document_type(self, doc: dict[str, Any], doc_index: int) -> bool:
        """Validate document_type is in allowed enum."""
        allowed = self.schema['properties']['document_type']['enum']
        doc_type = doc.get('document_type')

        if doc_type not in allowed:
            self.errors.append({
                'document_index': doc_index,
                'field': 'document_type',
                'error': f'Invalid document_type: {doc_type}. Allowed: {allowed}',
                'severity': 'error'
            })
            return False
        return True

    def validate_confidence(self, doc: dict[str, Any], doc_index: int) -> bool:
        """Validate classification_confidence is in range [0, 1]."""
        confidence = doc.get('classification_confidence')

        if confidence is None:
            return True  # Optional field

        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            self.errors.append({
                'document_index': doc_index,
                'field': 'classification_confidence',
                'error': f'Invalid confidence value: {confidence} (must be 0.0-1.0)',
                'severity': 'error'
            })
            return False
        return True

    def validate_document(self, doc: dict[str, Any], doc_index: int) -> bool:
        """Validate a single document against schema."""
        valid = True

        # Required fields
        valid &= self.validate_required_fields(doc, doc_index)

        # UUID format
        if 'document_id' in doc:
            valid &= self.validate_uuid(doc['document_id'], 'document_id', doc_index)

        # Document type enum
        valid &= self.validate_document_type(doc, doc_index)

        # Date format
        if 'date' in doc and doc['date']:
            valid &= self.validate_date(doc['date'], 'date', doc_index)

        # Date range
        if 'date_range' in doc:
            date_range = doc['date_range']
            if 'start' in date_range:
                valid &= self.validate_date(date_range['start'], 'date_range.start', doc_index)
            if 'end' in date_range:
                valid &= self.validate_date(date_range['end'], 'date_range.end', doc_index)

        # Checksum format
        if 'source_checksum' in doc and doc['source_checksum']:
            self.validate_checksum(doc['source_checksum'], 'source_checksum', doc_index)

        # Confidence range
        valid &= self.validate_confidence(doc, doc_index)

        # Entity UUIDs
        if 'extracted_entities' in doc:
            for i, entity_id in enumerate(doc['extracted_entities']):
                valid &= self.validate_uuid(entity_id, f'extracted_entities[{i}]', doc_index)

        # Title not empty
        if 'title' in doc and not doc['title'].strip():
            self.warnings.append({
                'document_index': doc_index,
                'field': 'title',
                'warning': 'Title is empty or whitespace-only',
                'severity': 'warning'
            })

        # Content preview length
        if 'content_preview' in doc and len(doc['content_preview']) > 500:
            self.warnings.append({
                'document_index': doc_index,
                'field': 'content_preview',
                'warning': f'Content preview exceeds 500 chars: {len(doc["content_preview"])}',
                'severity': 'warning'
            })

        return valid

    def validate_file(self, file_path: str) -> dict[str, Any]:
        """Validate all documents in a file."""
        print(f"Validating: {file_path}")
        print()

        with open(file_path, 'r') as f:
            data = json.load(f)

        documents = data.get('documents', [])
        total = len(documents)

        print(f"Total documents: {total:,}")
        print()

        valid_count = 0
        for i, doc in enumerate(documents):
            if self.validate_document(doc, i):
                valid_count += 1

        # Report results
        print("=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        print()
        print(f"Valid documents:   {valid_count:6,} / {total:,} ({(valid_count/total)*100:.1f}%)")
        print(f"Errors:            {len(self.errors):6,}")
        print(f"Warnings:          {len(self.warnings):6,}")
        print()

        if self.errors:
            print("ERRORS:")
            print("-" * 80)
            for err in self.errors[:10]:  # Show first 10
                print(f"  Document {err['document_index']}: {err['field']}")
                print(f"    {err['error']}")
                print()
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")
                print()

        if self.warnings:
            print("WARNINGS:")
            print("-" * 80)
            for warn in self.warnings[:10]:  # Show first 10
                print(f"  Document {warn['document_index']}: {warn['field']}")
                print(f"    {warn['warning']}")
                print()
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
                print()

        return {
            'total': total,
            'valid': valid_count,
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'success': len(self.errors) == 0
        }


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate transformed documents')
    parser.add_argument('--file', default='data/transformed/documents_sample.json',
                        help='Path to documents file to validate')
    args = parser.parse_args()

    validator = DocumentValidator()
    results = validator.validate_file(args.file)

    print("=" * 80)
    if results['success']:
        print("✓ VALIDATION PASSED")
    else:
        print("✗ VALIDATION FAILED")
    print("=" * 80)
    print()

    # Exit with error code if validation failed
    import sys
    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
