# ChromaDB Entity Search - Quick Start Guide

## Installation & Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Index entities (first time only, ~1-2 minutes)
python scripts/chromadb/index_entities.py --reset
```

## Basic Usage

### Search Entities
```bash
# Simple search
python scripts/chromadb/query_entities.py "financiers"

# With more results
python scripts/chromadb/query_entities.py "business associates" --limit 20
```

### Filter by Type
```bash
# Find locations
python scripts/chromadb/query_entities.py "islands and estates" --type location

# Find organizations
python scripts/chromadb/query_entities.py "financial institutions" --type organization

# Find persons
python scripts/chromadb/query_entities.py "lawyers" --type person
```

### Filter by Biography
```bash
# Only entities with detailed biographies
python scripts/chromadb/query_entities.py "accusers" --has-biography
```

### Filter by Prominence
```bash
# Entities mentioned in at least 10 documents
python scripts/chromadb/query_entities.py "key figures" --min-documents 10
```

### Filter by Classification
```bash
# Find specific classifications
python scripts/chromadb/query_entities.py "associates" --classification "Known Associates"
```

## Common Queries

### Find Associates
```bash
python scripts/chromadb/query_entities.py "business partners and associates"
```

### Find Victims/Accusers
```bash
python scripts/chromadb/query_entities.py "victims and accusers" --has-biography
```

### Find Properties
```bash
python scripts/chromadb/query_entities.py "private islands and mansions" --type location
```

### Find Legal Team
```bash
python scripts/chromadb/query_entities.py "lawyers and attorneys" --has-biography
```

### Find Financial Entities
```bash
python scripts/chromadb/query_entities.py "banks and investment firms" --type organization
```

## Advanced Usage

### Combine Multiple Filters
```bash
# Find prominent persons with biographies
python scripts/chromadb/query_entities.py "key figures" \
    --type person \
    --has-biography \
    --min-documents 5 \
    --limit 20
```

### Show Full Text
```bash
# See complete entity information
python scripts/chromadb/query_entities.py "Jeffrey Epstein" --full-text
```

### Collection Statistics
```bash
# View database statistics
python scripts/chromadb/query_entities.py --stats
```

## Understanding Results

Each result shows:
- **Canonical Name**: Official entity name
- **ID**: Unique UUID identifier
- **Similarity**: Relevance score (0-1, higher = more relevant)
- **Documents**: Number of documents mentioning this entity
- **Connections**: Number of documented relationships
- **Classifications**: Semantic categories (if available)
- **Preview**: First 200 characters of entity text

Example:
```
1. Alan Dershowitz (person)
   ID: 6431de2e-1123-59e4-a43e-26eedb4ef623
   Similarity: 0.843
   Documents: 42
   Connections: 15
   Classifications: Legal Team, Known Associates
   ✓ Has biography
   Preview: Prominent criminal defense attorney and Harvard Law School professor...
```

## Maintenance

### Reindex (if data updates)
```bash
python scripts/chromadb/index_entities.py --reset
```

### Test with Sample
```bash
python scripts/chromadb/index_entities.py --limit 10
```

## Tips

1. **Natural Language**: Use descriptive phrases ("financial associates" works better than "finance")
2. **Combine Filters**: Stack filters for precise results
3. **Check Stats**: Use `--stats` to understand the collection
4. **Biography Filter**: Use `--has-biography` for entities with rich context
5. **Document Count**: Use `--min-documents` to find prominent entities

## Troubleshooting

### Collection Not Found
```bash
# Run indexing first
python scripts/chromadb/index_entities.py
```

### No Results
- Try broader search terms
- Remove filters and see if results exist
- Check collection stats to verify data

### Slow Performance
- Reduce `--limit` value
- Collection size is only ~5MB, should be fast

## Data Coverage

- **Total Entities**: 2,939
  - Persons: 1,637
  - Locations: 423
  - Organizations: 879
- **With Biographies**: 125 (detailed context)
- **With Classifications**: 579 (categorized)

## Next Steps

After getting comfortable with entity search:
1. Explore document search: `scripts/chromadb/query_documents.py`
2. Combine entity and document queries
3. Export results for further analysis

## Help

```bash
# See all options
python scripts/chromadb/query_entities.py --help
```

For more details, see `scripts/chromadb/README.md`
