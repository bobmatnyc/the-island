# Document Viewability Analysis

**Generated**: 2025-11-26
**Analyst**: Claude MPM

## Executive Summary

Out of **38,177 total documents** in the Epstein archive, only **33,333 documents (87.3%)** are indexed in ChromaDB and viewable through the web interface. This leaves **4,848 documents (12.7%)** that exist in the file system but are not searchable or viewable on the site.

## Key Findings

### Overall Statistics
- **Total Documents**: 38,177 unique documents
- **Indexed in ChromaDB**: 33,333 documents
- **Not Viewable**: 4,848 documents (12.7%)
- **Primary Issue**: Only documents from `house_oversight_nov2025` source are indexed

### Coverage by Source

| Source | Total Docs | Indexed | Missing | % Missing |
|--------|------------|---------|---------|-----------|
| house_oversight_nov2025 | 37,469 | 33,329 | 4,140 | 11.0% |
| courtlistener_giuffre_maxwell | 358 | 0 | 358 | 100.0% |
| 404media | 319 | 0 | 319 | 100.0% |
| fbi_vault | 21 | 0 | 21 | 100.0% |
| house_oversight_sept2024 | 4 | 0 | 4 | 100.0% |
| documentcloud | 3 | 0 | 3 | 100.0% |
| giuffre_maxwell | 1 | 0 | 1 | 100.0% |
| raw_entities | 1 | 0 | 1 | 100.0% |
| doj_official | 1 | 0 | 1 | 100.0% |

## Root Cause Analysis

### ChromaDB Indexing

The ChromaDB vector database at `data/vector_store/chroma` contains the "epstein_documents" collection with 33,333 indexed chunks. Analysis of the metadata reveals:

- **Source field**: Only contains "house_oversight_nov2025" (except 4 "unknown")
- **Doc_id field**: 33,333 unique document identifiers
- **Filename field**: 33,329 unique filenames

### Missing Documents

Two categories of missing documents:

1. **Partially Indexed Source (house_oversight_nov2025)**:
   - 4,140 documents missing from this source
   - Represents 11% of the 37,469 documents in this collection
   - Could be due to processing failures or intentional filtering

2. **Completely Unindexed Sources**:
   - 708 documents across 8 other sources
   - 100% of documents from these sources are not indexed
   - Indicates these sources were never processed for ChromaDB indexing

## Technical Details

### ChromaDB Metadata Structure

```json
{
  "date_extracted": "January",
  "doc_id": "DOJ-OGR-00000001",
  "entity_mentions": "Maxwell, Ghislaine",
  "file_size": "754",
  "filename": "DOJ-OGR-00000001.txt",
  "source": "house_oversight_nov2025"
}
```

### Document Identification Method

Documents are matched between the master index and ChromaDB using the **doc_id** field, which is extracted from the filename stem (filename without extension). This ensures consistent identification across systems.

## Sample Missing Documents

From `house_oversight_nov2025` source:
- `DOJ-OGR-00003657.pdf` (358 KB)
- `DOJ-OGR-00028114.pdf` (12 KB)
- `DOJ-OGR-00023544.pdf` (340 KB)
- `DOJ-OGR-00019451.pdf` (734 KB)
- `DOJ-OGR-00020588.pdf` (393 KB)

All missing documents from other sources (courtlistener, 404media, fbi_vault, etc.)

## Impact

### User Experience
- Users cannot search or view 12.7% of the document collection
- Entire source collections (courtlistener, 404media, FBI vault) are inaccessible
- RAG-based chat assistant has incomplete context

### Data Accessibility
- Court documents from Maxwell case are completely missing from search
- Investigative journalism pieces not searchable
- FBI vault documents not integrated

## Recommendations

### Immediate Actions

1. **Index Missing Sources**
   - Run document indexing pipeline for the 8 completely unindexed sources
   - Priority: courtlistener_giuffre_maxwell (358 docs), 404media (319 docs)

2. **Complete house_oversight_nov2025 Indexing**
   - Identify why 4,140 documents from this source weren't indexed
   - Re-process these documents through the indexing pipeline

### Long-term Improvements

1. **Monitoring**
   - Add automated checks to detect indexing gaps
   - Alert when new document sources are added but not indexed

2. **Documentation**
   - Document the expected indexing workflow
   - Create runbook for adding new document sources

3. **Validation**
   - Implement post-indexing validation to ensure all documents are searchable
   - Add master_index.json vs ChromaDB reconciliation to deployment pipeline

## Files Generated

- `data/metadata/documents_not_viewable_report.json` - Detailed analysis with sample missing documents
- This document - Executive summary and recommendations

## Next Steps

To make all documents viewable:
1. Run indexing pipeline for unindexed sources
2. Investigate and reprocess 4,140 missing house_oversight_nov2025 documents
3. Verify all documents are searchable in the web interface
4. Update monitoring to prevent future gaps

---

*This analysis was performed as part of the document accessibility audit to identify gaps in the ChromaDB vector search index.*
