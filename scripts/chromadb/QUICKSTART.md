# ChromaDB Quick Start Guide

## Installation

ChromaDB is already installed in the project virtual environment:

```bash
# Verify installation
./.venv/bin/python3 -c "import chromadb; print(f'ChromaDB {chromadb.__version__}')"
```

## Initial Setup

**First time setup** - Index all documents:

```bash
# Index all 38,482 documents (~7 minutes)
./.venv/bin/python3 scripts/chromadb/index_documents.py --reset
```

**Expected output:**
```
Total documents processed: 38482
Successfully indexed: 38482
  - With real content: 0
  - With pseudo-content: 38482
Errors: 0

Collection size: 38482 documents
ChromaDB location: /Users/masa/Projects/epstein/data/chromadb
```

## Basic Usage

### Search Documents

```bash
# Search by topic
./.venv/bin/python3 scripts/chromadb/query_documents.py "Jeffrey Epstein"

# Search with more results
./.venv/bin/python3 scripts/chromadb/query_documents.py "FBI investigation" --limit 20

# Filter by classification
./.venv/bin/python3 scripts/chromadb/query_documents.py "court proceedings" \
    --classification court_record

# Filter by source
./.venv/bin/python3 scripts/chromadb/query_documents.py "government documents" \
    --source house_oversight_nov2025

# Combine filters
./.venv/bin/python3 scripts/chromadb/query_documents.py "federal investigation" \
    --classification fbi_report \
    --source fbi_vault \
    --limit 10
```

### Update Index

If data files change, reindex:

```bash
# Update existing index (upserts)
./.venv/bin/python3 scripts/chromadb/index_documents.py

# Or reset and rebuild from scratch
./.venv/bin/python3 scripts/chromadb/index_documents.py --reset
```

### Test with Small Dataset

```bash
# Test with first 100 documents
./.venv/bin/python3 scripts/chromadb/index_documents.py --limit 100 --reset

# Query the test dataset
./.venv/bin/python3 scripts/chromadb/query_documents.py "test query" --limit 5
```

## Python API Usage

Use ChromaDB directly in Python scripts:

```python
import chromadb
from chromadb.config import Settings

# Connect to database
client = chromadb.PersistentClient(
    path="data/chromadb",
    settings=Settings(anonymized_telemetry=False)
)

# Get collection
collection = client.get_collection("epstein_documents")

# Search
results = collection.query(
    query_texts=["your search query"],
    n_results=10,
    where={"classification": "court_record"},  # Optional filter
    include=["documents", "metadatas", "distances"]
)

# Process results
for doc_id, metadata, distance in zip(
    results["ids"][0],
    results["metadatas"][0],
    results["distances"][0]
):
    print(f"Document: {metadata['filename']}")
    print(f"Classification: {metadata['classification']}")
    print(f"Distance: {distance:.4f}")
    print()
```

## Available Filters

### Classification Types
- `court_record` - Court records and proceedings
- `fbi_report` - FBI investigation reports
- `government_document` - Government agency documents
- `court_filing` - Court filings and motions
- `media_article` - News articles and media
- `email` - Email communications
- `contact_directory` - Contact lists

### Document Sources
- `fbi_vault` - FBI vault releases
- `404media` - 404 Media documents
- `house_oversight_nov2025` - House Oversight Committee (Nov 2025)
- `house_oversight_sept2024` - House Oversight Committee (Sept 2024)
- `courtlistener_giuffre_maxwell` - CourtListener cases
- `documentcloud` - DocumentCloud archives
- `doj_official` - DOJ official releases

## Troubleshooting

### "Collection does not exist"
Index the documents first:
```bash
./.venv/bin/python3 scripts/chromadb/index_documents.py
```

### "No results found"
Try:
1. Broader search terms
2. Remove filters
3. Increase result limit (--limit 50)

### Slow queries
- Typical query time: <100ms
- If slower, check system resources
- Consider reducing result limit

### Memory issues during indexing
- Current batch size: 100 documents
- Reduce in `scripts/chromadb/config.py` if needed
- Close other memory-intensive applications

## File Locations

- **Configuration**: `scripts/chromadb/config.py`
- **Indexing Script**: `scripts/chromadb/index_documents.py`
- **Query Script**: `scripts/chromadb/query_documents.py`
- **Database Storage**: `data/chromadb/`
- **Documentation**: `scripts/chromadb/README.md`

## Quick Commands

```bash
# Status check
./.venv/bin/python3 -c "import chromadb; c = chromadb.PersistentClient(path='data/chromadb'); print(f'Documents: {c.get_collection(\"epstein_documents\").count()}')"

# Delete database (careful!)
rm -rf data/chromadb/

# Rebuild from scratch
./.venv/bin/python3 scripts/chromadb/index_documents.py --reset
```

## Next Steps

1. **Add OCR**: Extract text from PDFs for better search
2. **Generate Summaries**: Use LLM to create document summaries
3. **Web Integration**: Connect to FastAPI backend for web search
4. **Advanced Filtering**: Add date-based search

## Support

For issues or questions:
- Review full documentation: `scripts/chromadb/README.md`
- Check implementation details: `docs/implementation-summaries/chromadb-indexing-implementation.md`
- Linear ticket: #25
