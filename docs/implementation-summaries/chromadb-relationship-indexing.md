# ChromaDB Relationship Indexing Implementation

**Date**: 2025-12-06
**Issue**: #27 - Create ChromaDB indexing for entity relationships
**Milestone**: M4 - Vector Database (Fix Data Relationships)

## Summary

Implemented semantic search capabilities for entity relationships using ChromaDB vector database. This enables natural language queries like "Who was connected to Jeffrey Epstein through legal documents?" or "Find relationships involving flight logs".

## Implementation

### 1. Index Script (`scripts/chromadb/index_relationships.py`)

**Features**:
- Indexes 32,316 unique bidirectional relationships (66,193 edges deduplicated)
- Creates semantic descriptions for vector embedding
- Filters relationships by minimum weight (default: 2)
- Uses same embedding model as document collection (`all-MiniLM-L6-v2`)

**Relationship Schema**:
```python
{
    "id": "source_uuid__target_uuid",  # Lexicographically sorted IDs
    "document": "semantic relationship description",  # e.g., "Jeffrey Epstein (person) connected to FBI (organization) through 13,848 document co-appearances"
    "metadata": {
        "source_id": "uuid_a",
        "source_name": "Jeffrey Epstein",
        "source_type": "person",
        "target_id": "uuid_b",
        "target_name": "FBI",
        "target_type": "organization",
        "weight": 13848,
        "document_count": 13848,
        "flight_log_count": 0,
        "connection_types": "documents",
        "primary_doc_type": "government_document",
        "primary_doc_type_count": 13848
    }
}
```

**Text Content Strategy**:
- Includes entity names and types for context
- Mentions connection strength (weight)
- Specifies document vs. flight log sources
- Example: "Jeffrey Epstein (person) connected to FBI (organization) through 13,848 document co-appearances (primarily in government_document documents)"

### 2. Query Script (`scripts/chromadb/query_relationships.py`)

**Features**:
- Semantic search with natural language queries
- Filtering by entity type (person, organization, location)
- Filtering by connection type (documents, flight_logs)
- Filtering by minimum weight
- Entity name search (case-insensitive substring match)

**ChromaDB Limitations**:
- Only supports operators: `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`
- No `$contains` or complex `$or` operators
- Solution: Post-filter results in Python for entity name and connection type

**Usage Examples**:
```bash
# Find FBI connections
python scripts/chromadb/query_relationships.py "FBI connections" --limit 5

# Find flight log relationships
python scripts/chromadb/query_relationships.py "flight logs" --connection-type flight_logs

# Find Jeffrey Epstein's organizational connections
python scripts/chromadb/query_relationships.py "organizations" --entity "Epstein" --target-type organization

# Find strong connections (weight >= 100)
python scripts/chromadb/query_relationships.py "Jeffrey Epstein" --min-weight 100
```

## Statistics

- **Total edges in network**: 66,193
- **Filtered edges (weight >= 2)**: 32,316 unique relationships
- **Skipped bidirectional duplicates**: 32,316 (A→B and B→A counted once)
- **Successfully indexed**: 32,316 relationships
- **Indexing time**: ~6 minutes (324 batches of 100)
- **Collection size**: 32,316 documents in ChromaDB

## Test Results

### Query: "Jeffrey Epstein FBI connections"
**Top Result**:
- Jeffrey Epstein (person) ↔ FBI (unknown)
- Weight: 13,848
- Documents: 13,848
- Connection Types: documents
- Distance: 0.3920 (high relevance)

### Query: "flight logs" (--connection-type flight_logs)
**Top Result**:
- Kevin Spacey (person) ↔ Laura Wasserman (person)
- Weight: 9
- Flight Logs: 9
- Distance: 0.7648

### Query: "legal connections" (--entity "Epstein" --min-weight 100)
**Top Result**:
- UNITED STATES DISTRICT COURT (organization) ↔ Jeffrey Epstein (person)
- Weight: 136
- Documents: 136
- Distance: 1.3743

## Technical Details

### Deduplication Strategy
- Create unique edge ID using lexicographic ordering: `sorted([source_id, target_id])`
- Ensures A→B and B→A resolve to same edge ID
- Reduces storage by 50% (66,193 → 32,316 edges)

### Bidirectional Search Support
- Despite deduplication, searches work in both directions
- Metadata includes both source_name and target_name
- Semantic description mentions both entities

### Performance
- Batch size: 100 relationships per batch
- Progress reporting: Every 500 relationships
- Average processing: ~1 second per batch (~60 relationships/minute including embedding)

## Files Created

1. `/Users/masa/Projects/epstein/scripts/chromadb/index_relationships.py` - Indexing script (320 lines)
2. `/Users/masa/Projects/epstein/scripts/chromadb/query_relationships.py` - Query script (210 lines)
3. `/Users/masa/Projects/epstein/data/chromadb/` - ChromaDB storage (collection: `epstein_relationships`)

## Use Cases Enabled

1. **Semantic Relationship Search**: "Who was connected to Jeffrey Epstein through legal documents?"
2. **Connection Type Filtering**: "Find all flight log relationships"
3. **Entity Type Queries**: "Which organizations were connected to Jeffrey Epstein?"
4. **Strength-Based Filtering**: "Find Jeffrey Epstein's strongest connections (weight >= 1000)"
5. **Cross-Domain Discovery**: "Find relationships between people and locations in flight logs"

## Future Enhancements

1. **Relationship Types**: Add explicit relationship types (e.g., "co-defendant", "business partner", "passenger")
2. **Temporal Queries**: Add date range filtering for relationships
3. **Multi-Hop Search**: Find indirect connections (A→B→C)
4. **Relationship Clustering**: Group similar relationships
5. **API Integration**: Expose relationship search via FastAPI endpoints

## Integration with Existing System

- Uses same ChromaDB instance as document collection
- Shares embedding model configuration (`scripts/chromadb/config.py`)
- Complements entity network visualization (frontend)
- Can be used for relationship-aware document retrieval

## Notes

- Minimum weight threshold (2) filters out weak/spurious connections
- Relationship descriptions optimized for semantic search (mention entity types, connection strength)
- ChromaDB's limited operator support requires Python-side post-filtering for some queries
- Bidirectional deduplication reduces index size without losing search functionality
