# Epstein Document Archive - Project Guide

**Last Updated**: 2025-11-16 23:55 EST

## Quick Status

- **OCR Progress**: 45% complete (15,100 / 33,572 files) - ETA ~2 hours
- **Total Documents**: 67,144 PDFs downloaded
- **Entities Indexed**: 1,773 unique entities
- **Entity Network**: 387 entities with 2,221 flight co-occurrences
- **Documents Classified**: 6 (will expand to 67,144 after OCR completes)

## Project Goal

Create the **canonical, searchable data source** of publicly available Epstein files with:
- Complete source provenance tracking
- Automatic deduplication across sources
- Document classification (11 types)
- Entity extraction and indexing
- Relationship network mapping
- Semantic search by entity mentions

## Current Session Accomplishments

### ✅ Data Reorganization
- Created `/raw` directory for all source files (PDFs, CSVs)
- Created `/md` directory for markdown extractions
- Organized by source: entities, house_oversight_nov2025, giuffre_maxwell, etc.
- Script: `scripts/reorganize_data.py`

### ✅ Document Classification System
- Built 11-category classifier (email, court_filing, financial, flight_log, etc.)
- Keyword-based pattern matching with confidence scoring
- Secondary classification support
- Script: `scripts/classification/document_classifier.py`

### ✅ Semantic Entity Index
- Links 2,667 entity mentions to 6 documents (will expand after OCR)
- Cross-references entities across contact books and flight logs
- Tracks entity mentions per document
- Output: `data/metadata/semantic_index.json`

### ✅ Entity Relationship Network
- Parsed 1,167 unique flights from flight logs
- Built co-occurrence network (387 entities, 2,221 connections)
- Top relationship: Epstein ↔ Maxwell (228 flights together)
- Network graph: `data/metadata/entity_network.json`
- Script: `scripts/analysis/rebuild_flight_network.py`

### ✅ Entity Search Tool
- Search by entity name: `--entity "Clinton"`
- Find connections: `--connections "Ghislaine"`
- Multi-entity search: `--multiple "Clinton" "Epstein"`
- Search by type: `--type "email"`
- Script: `scripts/search/entity_search.py`

## Directory Structure

```
/Users/masa/Projects/Epstein/
├── data/
│   ├── raw/                    # Raw source files
│   │   ├── entities/          # Contact books, flight logs PDFs
│   │   ├── house_oversight_nov2025/ (67,144 PDFs in sources/)
│   │   └── ...
│   ├── md/                     # Markdown extractions
│   │   ├── entities/          # Entity extractions
│   │   │   ├── ENTITIES_INDEX.json (1,773 entities)
│   │   │   ├── black_book.md (1,740 contacts)
│   │   │   ├── flight_logs.md (3,721 records)
│   │   │   └── flight_logs_by_flight.json (1,167 flights)
│   │   └── house_oversight_nov2025/ (OCR output - in progress)
│   ├── metadata/               # Indexes & analysis
│   │   ├── entity_network.json (387 nodes, 2,221 edges)
│   │   ├── semantic_index.json (entity → docs)
│   │   ├── document_classifications.json
│   │   ├── entity_network_stats.txt
│   │   ├── classification_report.txt
│   │   └── source_index.json
│   └── canonical/              # Deduplicated final docs
├── scripts/
│   ├── extraction/
│   │   ├── ocr_house_oversight.py (RUNNING - PID 29722)
│   │   └── check_ocr_status.py
│   ├── classification/
│   │   ├── document_classifier.py
│   │   └── classify_all_documents.py
│   ├── analysis/
│   │   ├── entity_network.py
│   │   └── rebuild_flight_network.py
│   └── search/
│       └── entity_search.py
├── README.md
└── CLAUDE.md (this file)
```

## Next Steps (Priority Order)

### 1. Complete OCR Processing (In Progress)
- **Status**: 45% complete (15,100 / 33,572 files)
- **Process**: Running in background (PID 29722)
- **ETA**: ~2 hours (processing 7-8 files/second)
- **Check status**: `python3 scripts/extraction/check_ocr_status.py`

### 2. Extract Emails from OCR Results
- Expected: ~2,330 emails (per DocETL analysis)
- Email candidates tracked in: `email_candidates.jsonl`
- Will move to: `data/md/house_oversight_nov2025/emails/`

### 3. Classify All 67,144 Documents
- Run: `python3 scripts/classification/classify_all_documents.py`
- Will update semantic index with 67,144 documents
- Will classify into 11 types

### 4. Build Timeline
- Extract dates from classified documents
- Create chronological view of events
- Link timeline to entity network

### 5. Download Additional Sources
- FBI Vault (22 parts) - requires manual download
- JPMorgan lawsuit documents
- Additional DocumentCloud collections

## Search Examples

### Find Documents Mentioning an Entity
```bash
python3 scripts/search/entity_search.py --entity "Clinton"
# Returns: 4 documents (flight_logs.md, black_book.md, etc.)
```

### See Entity Connections
```bash
python3 scripts/search/entity_search.py --connections "Ghislaine"
# Shows: 256 connections, top: Je Epstein (228 flights together)
```

### Multi-Entity Search
```bash
python3 scripts/search/entity_search.py --multiple "Clinton" "Epstein" "Maxwell"
# Returns: Documents mentioning ALL three entities
```

### Search by Document Type
```bash
python3 scripts/search/entity_search.py --type "email"
# Returns: All classified email documents
```

## Key Metrics

### Entity Network
- **Total Entities**: 1,773 in index
- **Connected Entities**: 387 (with flight co-occurrences)
- **Total Connections**: 2,221 documented relationships
- **Billionaires**: 33 identified
- **Top Flyer**: Ghislaine Maxwell (520 flights in logs)

### Document Classification
- **Total Documents**: 67,144 (from House Oversight)
- **Classified So Far**: 6 entity documents
- **After OCR Complete**: Will classify all 67,144
- **Expected Emails**: ~2,330
- **11 Categories**: email, court_filing, financial, flight_log, contact_book, investigative, legal_agreement, personal, media, administrative, unknown

### Data Quality
- **High Confidence (>0.8)**: 16.7% of current classifications
- **Low Confidence (<0.5)**: 83.3% (will improve with OCR completion)
- **OCR Quality Issues**: Birthday Book (noted for manual review)
- **Name Variations**: Flight logs (being normalized)

## Background Processes

### OCR Processing (PID 29722)
- **Command**: `python3 scripts/extraction/ocr_house_oversight.py --workers 10`
- **Status**: Running since 8:49 PM
- **Progress**: 45% (15,100 / 33,572 files)
- **Rate**: 7-8 files/second
- **Log**: `/Users/masa/Projects/Epstein/logs/ocr_house_oversight.log`
- **Check**: `python3 scripts/extraction/check_ocr_status.py`

## Important Files

### Documentation
- `README.md` - Public-facing documentation
- `CLAUDE.md` - This file (resumption guide)
- `data/DATA_ORGANIZATION.md` - Directory structure explained
- `docs/COMPREHENSIVE_EPSTEIN_DOCUMENT_SOURCES.md` - All 30+ sources

### Analysis Reports
- `data/metadata/entity_network_stats.txt` - Network analysis
- `data/metadata/classification_report.txt` - Classification statistics
- `data/md/entities/EXTRACTION_SUMMARY.md` - Entity extraction summary

### Indexes
- `data/md/entities/ENTITIES_INDEX.json` - Master entity index
- `data/metadata/entity_network.json` - Relationship graph
- `data/metadata/semantic_index.json` - Entity → Document mappings
- `data/metadata/document_classifications.json` - All classifications

## Resuming Work

1. **Check OCR Status**:
   ```bash
   python3 scripts/extraction/check_ocr_status.py
   ```

2. **If OCR Complete**:
   - Extract emails from results
   - Run full classification on all 67,144 documents
   - Rebuild semantic index with complete dataset

3. **Search & Analysis**:
   - Use `scripts/search/entity_search.py` for queries
   - Check `data/metadata/` for analysis results

4. **Next Priorities**:
   - Build timeline from dated documents
   - Download additional source collections
   - Create web visualization of entity network
   - Generate comprehensive final report

## Technical Notes

### OCR System
- **Engine**: Tesseract OCR
- **Parallelization**: 10 workers
- **Email Detection**: Keyword-based (From:, To:, Subject:)
- **Resume Capability**: Automatic checkpoint/resume
- **Performance**: 7-8 files/second (~1 hour per 10,000 files)

### Classification System
- **Method**: Keyword pattern matching with confidence scoring
- **Categories**: 11 document types
- **Thresholds**: Minimum 2-4 keyword matches per type
- **Output**: Primary + secondary classifications with confidence

### Entity Extraction
- **Sources**: Black Book CSV, Flight Logs PDF, Birthday Book PDF
- **Normalization**: Name variations handled (Clinton, Bill Clinton, etc.)
- **Cross-referencing**: Entities linked across all sources
- **Network**: Co-occurrence from flight passenger lists

### Deduplication
- **Method**: Content hash + file hash + partial overlap detection
- **Database**: SQLite (deduplication.db)
- **Version Selection**: Quality-based (OCR 40%, redactions 25%, completeness 20%)

## Resources

- **DocETL Analysis**: https://www.docetl.org/showcase/epstein-email-explorer
- **House Oversight Release**: https://archive.org/details/epstein-pdf
- **UC Berkeley Confirmation**: 2,322 emails in 20,000+ page release

---

**Project Status**: Active - OCR processing 45% complete
**Next Milestone**: Complete OCR → Extract 2,330 emails → Full classification
**Contact**: See README.md for contribution guidelines
