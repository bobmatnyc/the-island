# ChromaDB Hybrid Search - Quick Start Guide

Unified search interface across all Epstein archive collections.

## Overview

The hybrid search system queries three ChromaDB collections simultaneously:
- **Documents** (38,482 items): Court records, FBI reports, emails, photos
- **Entities** (2,939 items): People, locations, organizations
- **Relationships** (32,316 items): Entity connections and co-appearances

## Quick Start

### Basic Usage

```bash
# Search everything
python scripts/chromadb/hybrid_search.py "Jeffrey Epstein"

# Limit results
python scripts/chromadb/hybrid_search.py "flight logs" --limit 30

# JSON output
python scripts/chromadb/hybrid_search.py "lawyers" --json
```

### Filter by Type

```bash
# Only documents
python scripts/chromadb/hybrid_search.py "court documents" --type document

# Only entities
python scripts/chromadb/hybrid_search.py "associates" --type entity

# Only relationships
python scripts/chromadb/hybrid_search.py "connections" --type relationship

# Documents and entities (no relationships)
python scripts/chromadb/hybrid_search.py "FBI investigation" --type document,entity
```

### Advanced Filtering

```bash
# Filter entities by type
python scripts/chromadb/hybrid_search.py "islands" --type entity --entity-type location

# Filter documents by classification
python scripts/chromadb/hybrid_search.py "legal" --document-classification court_filing

# Custom limits per collection
python scripts/chromadb/hybrid_search.py "Ghislaine Maxwell" \
  --doc-limit 10 --entity-limit 5 --rel-limit 5
```

## Result Format

### CLI Output

```
================================================================================
Query: Jeffrey Epstein
Total results: 9
================================================================================

Results by type:
  • document: 3
  • entity: 3
  • relationship: 3

Entity types:
  • person: 2
  • organization: 1

Document classifications:
  • fbi_report: 3

--------------------------------------------------------------------------------
Top Results:
--------------------------------------------------------------------------------

1. [ENTITY] Mark Epstein (person)
   Score: 0.779
   Preview: Mark Epstein (person). Also known as: mark_epstein
   Type: person
   Documents: 0
   Connections: 0

2. [DOCUMENT] jeffrey_epstein_part_07.pdf
   Score: 0.642
   Preview: Document: jeffrey_epstein_part_07.pdf. Classification: fbi_report...
   Classification: fbi_report
   Source: fbi_vault

3. [RELATIONSHIP] Jeffrey Epstein ↔ Drescher
   Score: 0.718
   Preview: Jeffrey Epstein (person) connected to Drescher (unknown)...
   Weight: 17
   Documents: 17
   Connection Types: documents
```

### JSON Output

```json
{
  "query": "Jeffrey Epstein",
  "total_results": 9,
  "results": [
    {
      "type": "entity",
      "id": "uuid",
      "name": "Mark Epstein (person)",
      "score": 0.779,
      "preview": "Mark Epstein (person). Also known as: mark_epstein",
      "metadata": {
        "entity_type": "person",
        "document_count": 0,
        "connection_count": 0,
        ...
      }
    }
  ],
  "facets": {
    "by_type": {
      "document": 3,
      "entity": 3,
      "relationship": 3
    },
    "by_entity_type": {
      "person": 2,
      "organization": 1
    },
    "by_document_classification": {
      "fbi_report": 3
    }
  }
}
```

## Use Cases

### Investigating a Person

```bash
# Find all evidence about Ghislaine Maxwell
python scripts/chromadb/hybrid_search.py "Ghislaine Maxwell" --limit 50

# Focus on her connections
python scripts/chromadb/hybrid_search.py "Ghislaine Maxwell" \
  --type entity,relationship --limit 30
```

### Exploring Locations

```bash
# Find island-related evidence
python scripts/chromadb/hybrid_search.py "private islands" \
  --type entity --entity-type location

# Little St. James references
python scripts/chromadb/hybrid_search.py "Little St James" --limit 40
```

### Legal Research

```bash
# Court documents only
python scripts/chromadb/hybrid_search.py "depositions" \
  --type document --document-classification court_filing

# Legal entities (law firms, courts)
python scripts/chromadb/hybrid_search.py "law firms" \
  --type entity --entity-type organization
```

### Flight Log Analysis

```bash
# Flight log documents and passengers
python scripts/chromadb/hybrid_search.py "flight logs" \
  --type document,entity --limit 40

# Specific route or destination
python scripts/chromadb/hybrid_search.py "Teterboro Airport" --limit 20
```

## Command Reference

### Required Arguments

```
query                 Search query text
```

### Optional Arguments

```
--limit N            Total result limit (default: 20)
--type TYPE          Filter by types: document,entity,relationship
--doc-limit N        Override limit for documents
--entity-limit N     Override limit for entities
--rel-limit N        Override limit for relationships
--entity-type TYPE   Filter entities: person, location, organization
--document-classification CLASS
                     Filter documents by classification
--json               Output as JSON (for API integration)
--verbose            Show full metadata for each result
```

## Score Interpretation

Search results are ranked by **score** (0.0-1.0, higher is better):

| Score Range | Interpretation |
|-------------|----------------|
| 0.7 - 1.0 | Strong match - highly relevant |
| 0.5 - 0.7 | Good match - likely relevant |
| 0.3 - 0.5 | Moderate match - potentially relevant |
| 0.0 - 0.3 | Weak match - loosely related |

## Facets

Facets show result distribution for filtering:

### by_type
Count of results per collection:
```
by_type: {"document": 12, "entity": 8, "relationship": 5}
```

### by_entity_type
Count per entity category (when entities in results):
```
by_entity_type: {"person": 10, "location": 3, "organization": 2}
```

### by_document_classification
Count per document type (when documents in results):
```
by_document_classification: {
  "court_filing": 8,
  "fbi_report": 3,
  "email": 1
}
```

## Tips & Best Practices

### Query Construction

✅ **Good Queries**:
- Specific names: "Jeffrey Epstein", "Ghislaine Maxwell"
- Locations: "Little St James", "Manhattan apartment"
- Topics: "flight logs", "court depositions", "FBI investigation"
- Organizations: "JPMorgan", "Victoria's Secret"

❌ **Poor Queries**:
- Single generic words: "documents", "person", "place"
- Very long queries (>10 words): Semantic search works best with concise queries
- Boolean operators: ChromaDB doesn't support AND/OR/NOT

### Result Limits

- **Default (20)**: Good for initial exploration
- **30-50**: Deep dive into specific topics
- **10-15**: Quick sanity checks

### Type Filtering

- Start broad (all types), then narrow:
  ```bash
  # First: See what types are relevant
  python scripts/chromadb/hybrid_search.py "Prince Andrew"

  # Then: Focus on documents
  python scripts/chromadb/hybrid_search.py "Prince Andrew" --type document
  ```

### JSON Mode

Use `--json` for:
- API integration
- Programmatic processing
- Exporting search results
- Building custom UIs

## Performance

- **Query time**: ~60-120ms (parallel querying)
- **Collections**: 3 queried simultaneously
- **Total items**: 73,737 searchable items
- **Scalability**: O(log N) search (HNSW index)

## Python API

For programmatic use:

```python
from scripts.chromadb.hybrid_search import HybridSearchClient

# Initialize
client = HybridSearchClient()

# Search
results = client.search(
    query="Jeffrey Epstein",
    limit=20,
    result_types=["entity", "document"]
)

# Process results
for result in results["results"]:
    print(f"{result['name']}: {result['score']:.3f}")
```

## Troubleshooting

### No Results Found

1. Check query spelling
2. Try broader terms (e.g., "flight" instead of "flight manifest")
3. Remove type filters (search all collections)
4. Try synonyms (e.g., "airplane" vs "aircraft")

### Low Scores

- Scores < 0.3 indicate weak semantic matches
- Try more specific queries
- Consider the query matches concepts, not exact text

### Collection Not Found

```
⚠ Collection 'epstein_entities' not found
```

Run indexing scripts first:
```bash
python scripts/chromadb/index_documents.py
python scripts/chromadb/index_entities.py
python scripts/chromadb/index_relationships.py
```

## Next Steps

- **Backend Integration**: Add to FastAPI API (`/api/search` endpoint)
- **Frontend UI**: Connect to search interface
- **Caching**: Implement query caching for common searches
- **Pagination**: Add offset/limit pagination for large result sets

## Related Documentation

- [ChromaDB Implementation Summary](implementation-summaries/chromadb-hybrid-search-implementation.md)
- [Vector Database Design](reference/VECTOR_DATABASE_DESIGN.md)
- [Entity Indexing](implementation-summaries/chromadb-entity-indexing.md)
- [Relationship Indexing](implementation-summaries/chromadb-relationship-indexing.md)

---

**Quick Links**:
- [Main README](../README.md)
- [API Documentation](API.md)
- [Linear Project](https://linear.app/1m-hyperdev/project/epstein-island-13ddc89e7271/issues)
