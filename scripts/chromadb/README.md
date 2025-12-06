# ChromaDB Document Indexing

Vector database system for semantic search and retrieval of Epstein documents.

## Overview

This system indexes all 38,482 documents from the Epstein archive into ChromaDB for fast semantic search and filtering. Documents are embedded using the `all-MiniLM-L6-v2` sentence transformer model (384-dimensional embeddings).

## Components

### Configuration (`config.py`)
Centralized settings for ChromaDB paths, embedding models, and performance parameters.

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

## Related Issues

- Linear Ticket #25: Create ChromaDB indexing for all documents
- Project: Fix Data Relationships (M4: Vector Database)
