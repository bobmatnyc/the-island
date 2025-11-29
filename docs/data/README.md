# Data Documentation

**Quick Summary**: Documentation for data structures, classification systems, and knowledge graphs in the Epstein Document Archive. .

**Category**: Index
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- [Classification System](./CLASSIFICATION.md) - Email and document classification system
- [Relationship System](./RELATIONSHIPS.md) - Entity relationship and network analysis
- [Chatbot Knowledge Index](./CHATBOT_INDEX.md) - Knowledge graph and chatbot index
- Document classification and categorization
- Entity extraction and enrichment

---

Documentation for data structures, classification systems, and knowledge graphs in the Epstein Document Archive.

## Quick Links

- [Classification System](./CLASSIFICATION.md) - Email and document classification system
- [Relationship System](./RELATIONSHIPS.md) - Entity relationship and network analysis
- [Chatbot Knowledge Index](./CHATBOT_INDEX.md) - Knowledge graph and chatbot index

## Overview

This directory contains documentation about the data infrastructure, including:
- Document classification and categorization
- Entity extraction and enrichment
- Relationship mapping and network analysis
- Knowledge graph structure
- Semantic search and indexing

## Key Documents

### Classification & Categorization
- **CLASSIFICATION.md**: Complete documentation of the email and document classification system
  - 11 document type categories
  - Classification algorithms and confidence scoring
  - Email extraction from OCR results
  - Classification statistics and reports

### Relationships & Networks
- **RELATIONSHIPS.md**: Entity relationship system and network analysis
  - Co-occurrence network (387 entities, 2,221 connections)
  - Flight log analysis (1,167 flights parsed)
  - Relationship enrichment from multiple sources
  - Network statistics and top connections

### Knowledge Integration
- **CHATBOT_INDEX.md**: Knowledge graph structure and chatbot integration
  - Semantic index (entity → document mappings)
  - 2,667 entity mentions across documents
  - Cross-referencing across contact books and flight logs
  - Search and query capabilities

## Data Architecture

### Entity System
```
1,773 unique entities indexed from:
- Black Book (1,740 contacts)
- Flight Logs (3,721 records, 1,167 flights)
- Birthday Book
- Additional sources
```

### Classification System
```
11 Document Categories:
- Email
- Court Filing
- Financial
- Flight Log
- Contact Book
- Investigative
- Legal Agreement
- Personal
- Media
- Administrative
- Unknown
```

### Relationship Network
```
Network Metrics:
- 387 connected entities
- 2,221 documented relationships
- 33 billionaires identified
- Top connection: Epstein ↔ Maxwell (228 flights)
```

## Data Quality

### Current Status
- **Total Documents**: 67,144 PDFs downloaded
- **OCR Progress**: Processing in progress
- **Classified Documents**: 6 (expanding to 67,144 post-OCR)
- **Entity Coverage**: 1,773 unique entities

### Quality Metrics
- High confidence classifications (>0.8): 16.7%
- Medium confidence (0.5-0.8): varies by type
- Low confidence (<0.5): 83.3% (improving with OCR)

## Data Locations

### Primary Data Directories
```
/Users/masa/Projects/Epstein/data/
├── raw/                    # Source files (PDFs, CSVs)
│   ├── entities/          # Contact books, flight logs
│   └── house_oversight_nov2025/
├── md/                     # Markdown extractions
│   ├── entities/          # Entity data
│   └── house_oversight_nov2025/
├── metadata/               # Indexes and analysis
│   ├── entity_network.json
│   ├── semantic_index.json
│   └── document_classifications.json
└── canonical/              # Deduplicated documents
```

## Search & Query

### Entity Search
```bash
# Search by entity name
python3 scripts/search/entity_search.py --entity "Clinton"

# Find entity connections
python3 scripts/search/entity_search.py --connections "Maxwell"

# Multi-entity search
python3 scripts/search/entity_search.py --multiple "Clinton" "Epstein"

# Search by document type
python3 scripts/search/entity_search.py --type "email"
```

## Data Processing Pipeline

### 1. Ingestion
- Download from multiple sources
- Track provenance and metadata
- Store raw files with source attribution

### 2. Extraction
- OCR processing (Tesseract)
- Entity extraction from structured data
- Text extraction from PDFs

### 3. Classification
- Keyword-based pattern matching
- Confidence scoring
- Secondary classification support

### 4. Enrichment
- Entity normalization
- Relationship extraction
- Network construction

### 5. Indexing
- Semantic index creation
- Cross-referencing
- Search index building

## Related Documentation

- [Developer Documentation](../developer/README.md) - Developer guides and API docs
- [Deployment Documentation](../deployment/README.md) - Deployment and access guides
- [Main Documentation Index](../README.md) - Complete documentation index
- [Project Guide](../../CLAUDE.md) - Project resumption guide

## Data Analysis Scripts

### Classification
- `scripts/classification/document_classifier.py` - Main classifier
- `scripts/classification/classify_all_documents.py` - Batch classification

### Network Analysis
- `scripts/analysis/entity_network.py` - Network builder
- `scripts/analysis/rebuild_flight_network.py` - Flight network reconstruction

### Search
- `scripts/search/entity_search.py` - Entity and document search

### Extraction
- `scripts/extraction/ocr_house_oversight.py` - OCR processing
- `scripts/extraction/check_ocr_status.py` - Status checker

## Contributing

When adding new data documentation:
1. Place files in this directory
2. Update this README with links and descriptions
3. Include data schemas and examples
4. Document data quality metrics
5. Cross-reference related documentation

---

**Last Updated**: 2025-11-17
**Maintained By**: Data Engineering Team
