# Transformed Documents - Canonical Schema

This directory contains documents transformed to the canonical schema defined in `data/schemas/document_schema.json`.

## Files

### `documents_sample.json`
- **Purpose**: Sample of 100 documents transformed to canonical schema
- **Use Case**: Testing, validation, schema development
- **Size**: ~100 documents
- **Status**: ✓ 100% schema compliant

### `documents_canonical.json` (Future)
- **Purpose**: All 38,482 documents in canonical schema
- **Use Case**: Production data, ChromaDB ingestion
- **Size**: ~38,482 documents
- **Status**: Not yet generated (run `generate_document_uuids.py` without `--sample`)

### `document_uuid_mappings.json`
- **Purpose**: Cross-reference from legacy IDs to new UUIDs
- **Use Case**: Backward compatibility, debugging, migration
- **Structure**:
  ```json
  {
    "mappings": [
      {
        "document_id": "e1569467-6b0c-5153-8b70-d351a2e05e31",
        "legacy_ids": {
          "sha256": "674c8534bc4b8b4cd05baa9f..."
        },
        "source_path": "data/sources/documentcloud/file.pdf",
        "document_type": "administrative",
        "title": "Document Title"
      }
    ]
  }
  ```

## Schema Version

**Current**: 1.0
**Schema**: `data/schemas/document_schema.json`
**Format**: JSON Schema Draft 7

## UUID Generation

Documents use **UUID5** (deterministic) generated from source file paths:
- **Namespace**: DNS namespace (`6ba7b810-9dad-11d1-80b4-00c04fd430c8`)
- **Input**: Normalized source path (e.g., `data/sources/fbi_vault/file.pdf`)
- **Output**: Deterministic UUID (same path → same UUID always)

### Example
```python
from scripts.transformations.generate_document_uuids import generate_document_uuid

uuid = generate_document_uuid("data/sources/fbi_vault/file.pdf")
# Always returns: "a3c5d8e1-4f7b-5a2c-9d6e-1b3f8c2a7e4d"
```

## Document Types

12 canonical document types:
- `email` - Email correspondence
- `court_record` - Court filings, dockets, transcripts
- `flight_log` - Aircraft flight records
- `fbi_report` - FBI documents and reports
- `deposition` - Deposition transcripts
- `correspondence` - Letters and memos
- `financial` - Financial records and statements
- `administrative` - Administrative documents
- `contact_directory` - Contact lists and address books
- `government_document` - Government documents (generic)
- `media_article` - News articles and media reports
- `other` - Uncategorized documents

## Usage

### Generate Transformed Documents

**Sample (100 docs)**:
```bash
python scripts/transformations/generate_document_uuids.py --sample
```

**Full dataset (38,482 docs)**:
```bash
python scripts/transformations/generate_document_uuids.py
```

### Validate Documents

```bash
python scripts/validation/validate_documents.py
python scripts/validation/validate_documents.py --file data/transformed/documents_canonical.json
```

### Query Documents

**Load documents**:
```python
import json

with open('data/transformed/documents_sample.json') as f:
    data = json.load(f)
    documents = data['documents']
```

**Find by UUID**:
```python
target_uuid = "e1569467-6b0c-5153-8b70-d351a2e05e31"
doc = next(d for d in documents if d['document_id'] == target_uuid)
print(doc['title'])
```

**Find by legacy ID**:
```python
with open('data/transformed/document_uuid_mappings.json') as f:
    mappings = json.load(f)['mappings']

legacy_sha256 = "674c8534bc4b8b4cd05baa9f..."
mapping = next(m for m in mappings if m['legacy_ids'].get('sha256') == legacy_sha256)
print(f"UUID: {mapping['document_id']}")
```

**Filter by type**:
```python
emails = [d for d in documents if d['document_type'] == 'email']
court_records = [d for d in documents if d['document_type'] == 'court_record']
```

**Filter by date**:
```python
from datetime import datetime

docs_2001 = [d for d in documents if d.get('date', '').startswith('2001')]
```

## Field Reference

### Required Fields
- `document_id` - UUID5 from source path
- `document_type` - One of 12 canonical types
- `title` - Human-readable title
- `source_path` - Relative path to source file
- `source_checksum` - SHA256 hash

### Optional Fields
- `date` - ISO 8601 date (YYYY-MM-DD)
- `date_raw` - Original unparsed date string
- `date_range` - For multi-date documents (flight logs)
- `content_preview` - First 500 chars of content
- `content_path` - Path to extracted text
- `extracted_entities` - Array of entity UUIDs
- `classification_confidence` - Float [0.0, 1.0]
- `metadata` - Type-specific metadata
- `legacy_ids` - Old ID system cross-reference
- `processing_status` - Pipeline processing flags

### Metadata Structure

**All Documents**:
```json
{
  "metadata": {
    "source_metadata": {
      "source_collection": "house_oversight_nov2025",
      "source_id": "DOJ-OGR-00015682",
      "original_filename": "file.pdf",
      "file_size": 56561399
    }
  }
}
```

**Emails**:
```json
{
  "metadata": {
    "email": {
      "from": "sender@example.com",
      "to": "recipient@example.com",
      "cc": "cc@example.com",
      "subject": "Email subject"
    }
  }
}
```

**Court Records**:
```json
{
  "metadata": {
    "court_record": {
      "case_number": "1:15-cv-07433-RWS",
      "court": "Southern District of New York",
      "filing_date": "2015-09-21"
    }
  }
}
```

## Statistics (Sample Data)

**Total Documents**: 100

**Type Distribution**:
| Type | Count | % |
|------|-------|---|
| court_record | 64 | 64.0% |
| government_document | 28 | 28.0% |
| media_article | 5 | 5.0% |
| administrative | 2 | 2.0% |
| contact_directory | 1 | 1.0% |

**Validation**: ✓ 100% pass (0 errors, 0 warnings)

## Migration Status

- ✅ **Phase 1**: Sample data (100 documents)
- ⏳ **Phase 2**: Full dataset (38,482 documents) - Run generator without `--sample`
- ⏳ **Phase 3**: Entity integration - Link entities to document UUIDs
- ⏳ **Phase 4**: ChromaDB ingestion - Semantic search layer

## See Also

- **Schema Spec**: `data/schemas/document_schema.json`
- **Generator**: `scripts/transformations/generate_document_uuids.py`
- **Validator**: `scripts/validation/validate_documents.py`
- **Implementation Guide**: `docs/implementation-summaries/document-schema-implementation.md`
- **Issue**: Linear #16 - Documents: Define canonical schema
