# Epstein Document Archive

**The Canonical Data Source of Epstein Files**

Organized, sourced, semantically and structurally indexed archive of Jeffrey Epstein-related documents from public sources.

## 📊 Current Status

- **Total Documents**: 67,144+ PDFs from House Oversight Nov 2025 release
- **Expected Emails**: ~2,330 (per DocETL/UC Berkeley analysis)
- **Entities Indexed**: 1,773 unique entities (people, organizations)
- **Entity Relationships**: 387 entities with 2,221 documented flight co-occurrences
- **Document Types**: 11 classification categories
- **OCR Progress**: 45% complete (15,100 / 33,572 files processed)

## 🎯 Project Goal

Create the canonical, searchable data source of publicly available Epstein files with complete source provenance, automatic deduplication, document classification, entity extraction, relationship network mapping, and semantic search capabilities.

## 🔍 Quick Start - Search Tools

### Search by Entity
```bash
python3 scripts/search/entity_search.py --entity "Clinton"
python3 scripts/search/entity_search.py --connections "Ghislaine"
python3 scripts/search/entity_search.py --multiple "Clinton" "Epstein"
```

### Search by Document Type
```bash
python3 scripts/search/entity_search.py --type "email"
```

## 📁 Directory Structure

```
data/
├── raw/              # Raw PDFs, CSVs, ZIPs
├── md/               # Markdown extractions & structured data
├── metadata/         # Indexes, databases, analysis reports
└── canonical/        # Deduplicated final documents
```

See `data/DATA_ORGANIZATION.md` for complete structure.

## 📚 Key Resources

- **Entity Network**: `data/metadata/entity_network.json` (387 entities, 2,221 connections)
- **Semantic Index**: `data/metadata/semantic_index.json` (entity → document mappings)
- **Classifications**: `data/metadata/document_classifications.json`
- **Entity Index**: `data/md/entities/ENTITIES_INDEX.json` (1,773 entities)

## 📈 Network Analysis Highlights

- **Ghislaine Maxwell**: 256 connections, 228 flights with Epstein
- **Sarah Kellen**: 110 connections, 146 flights with Epstein
- **33 Billionaires** in contact book (Leon Black, Glenn Dubin, Les Wexner, etc.)

See `data/metadata/entity_network_stats.txt` for full analysis.

## 🛠️ Available Tools

- **OCR Processing**: `scripts/extraction/ocr_house_oversight.py`
- **Classification**: `scripts/classification/classify_all_documents.py`
- **Entity Search**: `scripts/search/entity_search.py`
- **Network Analysis**: `scripts/analysis/rebuild_flight_network.py`

## 📖 Documentation

- `CLAUDE.md` - Project resumption guide
- `docs/COMPREHENSIVE_EPSTEIN_DOCUMENT_SOURCES.md` - All 30+ sources
- `data/DATA_ORGANIZATION.md` - Directory structure guide

---

**Last Updated**: 2025-11-16 | **OCR**: 45% complete
