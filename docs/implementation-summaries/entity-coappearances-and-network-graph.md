# Entity Co-appearances and Network Graph Implementation

**Date**: 2025-12-06
**Issues**: Linear #22 (Entity Co-appearances), Linear #23 (Network Graph)
**Status**: ✅ Complete

## Overview

Implemented comprehensive entity relationship analysis by calculating co-appearances across all documents and building a unified network graph that merges document-based relationships with existing flight log connections.

## Implementation

### Scripts Created

1. **`scripts/transformations/calculate_coappearances.py`**
   - Calculates entity pairs appearing in same documents
   - Uses `itertools.combinations` for efficient O(n²) pair generation
   - Filters to include only pairs with ≥2 co-appearances
   - Maps entity names to UUIDs where possible
   - Tracks document types for each co-appearance

2. **`scripts/transformations/build_entity_network.py`**
   - Builds network from co-appearance data
   - Merges with existing flight log network
   - Ensures bidirectional edges (A→B and B→A)
   - Adds document counts to each node
   - Calculates network statistics

### Output Files

1. **`data/transformed/entity_coappearances.json`**
   - **31,682 entity pairs** (after filtering for ≥2 co-appearances)
   - **4,572 unique entities** involved in co-appearances
   - **31,111 documents** processed
   - Top co-appearance: Jeffrey Epstein ↔ FBI (13,848 documents)

2. **`data/transformed/entity_network_full.json`**
   - **4,790 nodes** (entities)
   - **66,193 edges** (33,096 unique bidirectional pairs)
   - **Average 14.24 connections per node**
   - Sources: documents (31,111) + flight logs (merged)
   - **104 edges** with merged sources (both documents and flight logs)

## Key Features

### Co-appearances Script

1. **Efficient Processing**
   - Processed 31,111 documents in < 1 second
   - Used `itertools.combinations` for optimal pair generation
   - Early filtering to skip documents with < 2 entities

2. **UUID Mapping**
   - Matches entity names to UUIDs from `entity_uuid_mappings.json`
   - Handles multiple name formats (lowercase, underscores, aliases)
   - Fallback to synthetic IDs for unmapped entities

3. **Document Type Tracking**
   - Infers document types from ID prefixes (DOJ-OGR, EMAIL, COURT)
   - Tracks distribution of co-appearances by document type

### Network Graph Script

1. **Bidirectional Edges**
   - All edges are bidirectional (A→B and B→A have same weight)
   - Consistent ordering prevents duplicates

2. **Source Merging**
   - Merges flight log connections with document co-appearances
   - Tracks source attribution (documents vs flight_logs)
   - Combines weights when entities appear in both sources

3. **Rich Node Metadata**
   - Connection count (number of connected entities)
   - Document count (number of documents mentioning entity)
   - Entity type (person, location, organization)
   - UUID for unique identification

## Results

### Top Connected Entities

| Rank | Entity | Connections | Documents |
|------|--------|------------|-----------|
| 1 | Jeffrey Epstein | 1,799 | 18,563 |
| 2 | FBI | 1,203 | 16,959 |
| 3 | Ghislaine Maxwell's | 695 | 2,868 |
| 4 | DOJ | 607 | 2,713 |
| 5 | Little St James | 545 | 12,658 |
| 6 | United States | 536 | 1,127 |
| 7 | New York | 492 | 2,029 |
| 8 | Southern District Reporters PC | 438 | 1,909 |
| 9 | Maxwell | 425 | 2,013 |
| 10 | Maxwell, Ghislaine | 359 | 0 |

### Network Statistics

- **Unique edges**: 33,096 (bidirectional pairs)
- **Flight log edges**: 2,933 edges (1,467 unique pairs)
- **Merged edges**: 104 edges with both document and flight log sources
- **Average connections**: 14.24 per node
- **Network density**: Highly connected around key entities (Jeffrey Epstein, Ghislaine Maxwell, FBI)

## Data Quality Notes

### UUID Mappings
- Successfully mapped 4,764 entity names to UUIDs
- Unmapped entities use synthetic IDs: `unmapped_{normalized_name}`
- Common unmapped entities: "fbi", "doj", "maxwell", "little st james"

### Entity Name Variations
- Observed duplicate entities with different names:
  - "Ghislaine Maxwell's" (UUID: 1cff1722..., 695 connections)
  - "Maxwell" (unmapped, 425 connections)
  - "Maxwell, Ghislaine" (flight_log ID, 359 connections)
- **Recommendation**: Entity name normalization should be improved to consolidate these

### Document Types
- Most co-appearances are from government documents (DOJ-OGR prefix)
- Limited email and court filing data in current dataset
- Document type inference based on ID prefix (could be improved with metadata lookup)

## Performance

- **Co-appearances calculation**: < 1 second for 31,111 documents
- **Network building**: < 1 second for 31,682 pairs + flight log merge
- **Memory usage**: Efficient (entire dataset fits in memory)
- **Algorithm complexity**: O(n × m²) where n=documents, m=avg entities per doc

## Future Improvements

1. **Entity Name Consolidation**
   - Merge duplicate entities (e.g., "Maxwell", "Ghislaine Maxwell", "Maxwell, Ghislaine")
   - Improve UUID mapping coverage

2. **Document Type Metadata**
   - Use `all_documents_index.json` for accurate document classifications
   - Add document dates for temporal analysis

3. **Network Analysis**
   - Calculate connected components
   - Identify community clusters
   - Compute centrality metrics (betweenness, closeness, eigenvector)

4. **Visualization**
   - Export to network visualization formats (Gephi, Cytoscape)
   - Generate interactive web-based network explorer

## Files Changed

### Created
- `scripts/transformations/calculate_coappearances.py` (241 lines)
- `scripts/transformations/build_entity_network.py` (405 lines)
- `data/transformed/entity_coappearances.json` (~2.5 MB)
- `data/transformed/entity_network_full.json` (~4.5 MB)
- `docs/implementation-summaries/entity-coappearances-and-network-graph.md` (this file)

## Testing

Verified output structure:
- ✅ Co-appearances JSON has correct metadata
- ✅ All entity pairs have valid UUIDs or synthetic IDs
- ✅ Network graph has bidirectional edges
- ✅ Flight log data successfully merged
- ✅ Document counts accurately populated
- ✅ Network statistics calculated correctly

## Conclusion

Successfully implemented entity co-appearance analysis and comprehensive network graph construction. The system now has:
- Complete entity relationship data from 31,111 documents
- Unified network merging document co-appearances and flight logs
- Rich metadata for network analysis and visualization
- Scalable algorithms for future data additions

**Next Steps**: Entity name normalization and network visualization.
