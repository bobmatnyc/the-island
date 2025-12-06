# ChromaDB Indexing System

Vector database system for semantic search and retrieval of Epstein documents and entities.

## Overview

This system provides two ChromaDB collections:

1. **Documents Collection** (`epstein_documents`): 38,482 documents with metadata
2. **Entities Collection** (`epstein_entities`): 2,939 entities (persons, locations, organizations)

Both collections use the `all-MiniLM-L6-v2` sentence transformer model for 384-dimensional embeddings.

## Components

### Configuration (`config.py`)
Centralized settings for ChromaDB paths, embedding models, and performance parameters.

---

## Document Indexing

### Indexing Script (`index_documents.py`)
Indexes all documents with metadata for filtering and search.

**Usage:**
```bash
# Index all documents (initial run or update)
python scripts/chromadb/index_documents.py

# Reset collection and reindex from scratch
python scripts/chromadb/index_documents.py --reset

# Index only first N documents (for testing)
python scripts/chromadb/index_documents.py --limit 100
```

**Performance:**
- Batch size: 100 documents per batch
- Full indexing: ~7 minutes for 38,482 documents
- Memory efficient: processes documents in batches

### Query Script (`query_documents.py`)
Search the indexed documents using natural language queries.

**Usage:**
```bash
# Basic search
python scripts/chromadb/query_documents.py "Jeffrey Epstein" --limit 10

# Filter by classification
python scripts/chromadb/query_documents.py "court filings" --classification court_record

# Filter by source
python scripts/chromadb/query_documents.py "FBI investigation" --source fbi_vault

# Combine query and filters
python scripts/chromadb/query_documents.py "government documents" \
    --classification government_document \
    --source house_oversight_nov2025 \
    --limit 20
```

## Data Sources

The indexing system pulls from three data files:

1. **Document Classifications** (`data/transformed/document_classifications.json`)
   - 38,482 documents with updated classifications
   - Classification confidence scores
   - Keywords matched during classification

2. **Document-Entity Mappings** (`data/transformed/document_to_entities.json`)
   - 31,111 documents with entity references
   - Links documents to mentioned entities

3. **All Documents Index** (`data/metadata/all_documents_index.json`)
   - Complete document metadata
   - File sizes, paths, types
   - Source information

## Document Schema

Each document in ChromaDB contains:

```python
{
    "id": "document_hash_id",
    "document": "text content for embedding",
    "metadata": {
        "filename": "document.pdf",
        "source": "fbi_vault",
        "classification": "fbi_report",
        "confidence": 0.90,
        "doc_type": "pdf",
        "file_size": 1234567,
        "entity_count": 15,
        "has_real_content": False,  # True if summary available
        "path": "data/sources/fbi_vault/document.pdf"
    }
}
```

## Text Content Strategy

Since most documents lack extracted text:

1. **Primary Strategy**: Use document summary if available (rare)
2. **Fallback Strategy**: Use filename + classification + source + keywords as pseudo-content
3. **Metadata Tracking**: `has_real_content` flag indicates which strategy was used

**Statistics from Full Index:**
- Total documents: 38,482
- With real content: 0 (summaries not yet extracted)
- With pseudo-content: 38,482 (filename-based embeddings)

## Filtering Options

Filter documents by metadata fields:

- **classification**: `court_record`, `fbi_report`, `government_document`, `court_filing`, etc.
- **source**: `fbi_vault`, `404media`, `house_oversight_nov2025`, etc.
- **has_real_content**: `True` (summaries) or `False` (filename-based)

## Storage

- **Location**: `data/chromadb/`
- **Size**: ~150MB for full index (38,482 documents)
- **Persistence**: Automatically persisted to disk
- **Collection Name**: `epstein_documents`

## Future Enhancements

1. **OCR Integration**: Extract text from PDFs and index actual content
2. **Summary Generation**: Use LLM to generate document summaries
3. **Entity-Aware Search**: Weight results by entity mentions
4. **Temporal Filtering**: Add date-based search capabilities
5. **Hybrid Search**: Combine vector search with keyword search

## Performance

- **Indexing Time**: ~7 minutes for full dataset
- **Query Time**: <100ms for most queries
- **Memory Usage**: ~2GB during indexing (batched processing)
- **Disk Usage**: ~150MB for embeddings + metadata

## Requirements

```bash
pip install chromadb sentence-transformers
```

**Installed versions:**
- ChromaDB: 1.3.5
- Sentence Transformers: 5.1.2

---

## Entity Indexing

### Indexing Script (`index_entities.py`)
Indexes all 2,939 entities (persons, locations, organizations) with rich metadata and semantic content.

**Usage:**
```bash
# Index all entities (initial run or update)
python scripts/chromadb/index_entities.py

# Reset collection and reindex from scratch
python scripts/chromadb/index_entities.py --reset

# Index only first N entities (for testing)
python scripts/chromadb/index_entities.py --limit 100
```

**Performance:**
- Batch size: 100 entities per batch
- Full indexing: ~1-2 minutes for 2,939 entities
- Upsert support: Safe re-indexing without duplicates

### Query Script (`query_entities.py`)
Search entities using natural language queries.

**Usage:**
```bash
# Basic semantic search
python scripts/chromadb/query_entities.py "financiers and business associates"

# Filter by entity type
python scripts/chromadb/query_entities.py "private islands" --type location

# Find entities with biographies
python scripts/chromadb/query_entities.py "lawyers" --has-biography

# Filter by minimum document count
python scripts/chromadb/query_entities.py "key figures" --min-documents 10

# Filter by classification
python scripts/chromadb/query_entities.py "associates" --classification "Known Associates"

# Combine filters
python scripts/chromadb/query_entities.py "accusers and victims" \
    --type person \
    --has-biography \
    --limit 20

# Show collection statistics
python scripts/chromadb/query_entities.py --stats
```

## Entity Data Sources

The entity indexing system pulls from four data files:

1. **Persons** (`data/transformed/entities_persons.json`)
   - 1,637 persons with biographies and metadata

2. **Locations** (`data/transformed/entities_locations.json`)
   - 423 locations (islands, estates, addresses)

3. **Organizations** (`data/transformed/entities_organizations.json`)
   - 879 organizations (companies, institutions)

4. **Classifications** (`data/transformed/entity_classifications_derived.json`)
   - Semantic classifications for 579 entities
   - Confidence scores and evidence

## Entity Schema

Each entity in ChromaDB contains:

```python
{
    "id": "entity_uuid",
    "document": "rich text for embedding",  # name + biography + aliases + classifications
    "metadata": {
        "entity_type": "person|location|organization",
        "canonical_name": "Jeffrey Epstein",
        "normalized_name": "jeffrey epstein",
        "document_count": 42,
        "connection_count": 15,
        "has_biography": True,
        "classifications": "Primary Subject,Known Associates",
        "classification_confidence": 0.95,
        "alias_count": 3
    }
}
```

## Entity Text Content Strategy

Build rich semantic text for embeddings by combining:

1. **Entity type and canonical name**: "Jeffrey Epstein (person)"
2. **Biography** (if available, truncated to 500 chars)
3. **Aliases**: "Also known as: Jeff Epstein"
4. **Classifications**: "Classifications: Primary Subject, Known Associates"

**Example:**
```
Alan Dershowitz (person). Prominent criminal defense attorney and Harvard Law
School professor emeritus. Represented Jeffrey Epstein in 2008 plea deal
negotiations. Accused by Virginia Giuffre of sexual abuse... Also known as:
Alan Morton Dershowitz. Classifications: Legal Team, Known Associates
```

**Statistics from Full Index:**
- Total entities: 2,939
- Persons: 1,637
- Locations: 423
- Organizations: 879
- With biographies: 125
- With classifications: 579

## Entity Filtering Options

Filter entities by metadata fields:

- **entity_type**: `person`, `location`, `organization`
- **has_biography**: `True` (entities with biographical text)
- **min_document_count**: Minimum mentions in documents
- **classification**: Partial match on classification labels

## Storage

### Documents Collection
- **Location**: `data/chromadb/`
- **Size**: ~150MB for full index (38,482 documents)
- **Collection Name**: `epstein_documents`

### Entities Collection
- **Location**: `data/chromadb/`
- **Size**: ~5MB for full index (2,939 entities)
- **Collection Name**: `epstein_entities`

Both collections are automatically persisted to disk.

## Related Issues

- Linear Ticket #25: Create ChromaDB indexing for all documents
- Linear Ticket #26: Create ChromaDB indexing for all entities
- Project: Fix Data Relationships (M4: Vector Database)
