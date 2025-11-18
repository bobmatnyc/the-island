# Epstein Document Archive

**The Canonical, Searchable Data Source of Publicly Available Epstein Files**

A comprehensive, organized archive of Jeffrey Epstein-related documents from public sources with complete source provenance, automatic deduplication, document classification, entity extraction, relationship network mapping, and semantic search capabilities.

---

## Quick Navigation

**New to this project?** → Start with [Getting Started](#-quick-start)
**Developers?** → See [Developer Setup](docs/developer/setup.md) and [API Documentation](docs/developer/api/)
**Searching documents?** → See [Search Guide](docs/user/searching.md)
**Deploying?** → See [Deployment Guide](docs/operations/deployment.md)
**Understanding the data?** → See [Data Sources](docs/content/data-sources.md) and [Research Methodology](docs/research/methodology.md)

---

## Current Status

| Metric | Count | Status |
|--------|-------|--------|
| **Total Documents** | 67,144+ PDFs | From House Oversight Nov 2025 release |
| **OCR Progress** | 45% (15,100/33,572) | Processing ~7-8 files/second |
| **Expected Emails** | ~2,330 | Per DocETL/UC Berkeley analysis |
| **Entities Indexed** | 1,773 unique | People, organizations |
| **Entity Network** | 387 entities | 2,221 documented connections |
| **Document Types** | 11 categories | Email, court filing, financial, etc. |
| **Billionaires** | 33 identified | In contact book |

**Last Updated**: 2025-11-17
**Code Quality**: ⭐⭐⭐⭐ (Good)
**Project Phase**: Active Development - OCR Processing

---

## Project Overview

### Goal

Create the **canonical, searchable data source** of publicly available Epstein files with:

- Complete source provenance tracking
- Automatic deduplication across sources
- Document classification (11 types)
- Entity extraction and indexing
- Relationship network mapping
- Semantic search by entity mentions
- Full-text search capabilities

### Key Features

- **Entity Database**: 1,773 unique entities with biographical information
- **Flight Logs**: 1,167 documented flights with passenger lists
- **Document Archive**: 67,144+ documents with OCR and classification
- **Network Analysis**: Entity relationship graph with 2,221 connections
- **Semantic Search**: Find documents by entity mentions
- **Entity Enrichment**: AI-powered biographical data extraction
- **Deduplication**: Content-based duplicate detection across sources
- **Source Tracking**: Full provenance for every document

---

## Quick Start

### For Users (Searching Documents)

```bash
# Search by entity name
python3 scripts/search/entity_search.py --entity "Clinton"

# See entity connections
python3 scripts/search/entity_search.py --connections "Ghislaine"

# Multi-entity search
python3 scripts/search/entity_search.py --multiple "Clinton" "Epstein" "Maxwell"

# Search by document type
python3 scripts/search/entity_search.py --type "email"
```

**Learn more**: [User Guide](docs/user/) | [Search Guide](docs/user/searching.md)

### For Developers (Contributing Code)

```bash
# Clone repository
git clone <repository-url>
cd Epstein

# Set up development environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the application
cd server
python app.py 8081

# Visit http://localhost:8081
```

**Learn more**: [Developer Setup](docs/developer/setup.md) | [Architecture](docs/developer/architecture.md) | [API Docs](docs/developer/api/)

### For Researchers (Understanding Data)

```bash
# View entity network statistics
cat data/metadata/entity_network_stats.txt

# Explore entity index
cat data/md/entities/ENTITIES_INDEX.json

# Check document classifications
cat data/metadata/document_classifications.json
```

**Learn more**: [Data Sources](docs/content/data-sources.md) | [Research Methodology](docs/research/methodology.md)

---

## Documentation

### Quick Links

- **Users**: [Getting Started](docs/user/getting-started.md) | [Searching](docs/user/searching.md) | [FAQ](docs/user/faq.md)
- **Developers**: [Setup](docs/developer/setup.md) | [API Reference](docs/developer/api/) | [Architecture](docs/developer/architecture.md) | [Testing](docs/developer/testing.md)
- **Content**: [Data Sources](docs/content/data-sources.md) | [Classification System](docs/content/classification.md) | [Entity Extraction](docs/content/entity-extraction.md)
- **Operations**: [Deployment](docs/operations/deployment.md) | [Monitoring](docs/operations/monitoring.md) | [Troubleshooting](docs/operations/troubleshooting.md)
- **Research**: [Methodology](docs/research/methodology.md) | [Ethics](docs/research/ethics.md) | [Source Evaluation](docs/research/sources.md)

### Core Documentation

| Document | Description |
|----------|-------------|
| [docs/README.md](docs/README.md) | Complete documentation index |
| [CLAUDE.md](CLAUDE.md) | Project resumption guide (for AI assistants) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [CHANGELOG.md](CHANGELOG.md) | Project changelog |

---

## Project Statistics

### Network Analysis Highlights

- **Most Connected**: Jeffrey Epstein (265 connections)
- **Top Relationship**: Epstein ↔ Maxwell (228 flights together)
- **Ghislaine Maxwell**: 520 flights total, 228 with Epstein
- **Sarah Kellen**: 291 flights with Epstein
- **33 Billionaires**: Leon Black, Glenn Dubin, Les Wexner, and others

See [data/metadata/entity_network_stats.txt](data/metadata/entity_network_stats.txt) for complete analysis.

### Document Classification

- **11 Categories**: email, court_filing, financial, flight_log, contact_book, investigative, legal_agreement, personal, media, administrative, unknown
- **67,144 Documents**: From House Oversight release
- **~2,330 Emails**: Expected after OCR completion
- **6 Documents Classified**: Entity documents (will expand to all 67,144)

See [docs/content/classification.md](docs/content/classification.md) for details.

---

## Data Structure

```
Epstein/
├── data/
│   ├── raw/              # Source PDFs, CSVs, ZIPs
│   ├── md/               # Markdown extractions
│   ├── metadata/         # Indexes, analysis, databases
│   └── canonical/        # Deduplicated final documents
├── server/               # Web application backend
├── scripts/              # Data processing scripts
│   ├── extraction/       # OCR and text extraction
│   ├── classification/   # Document classification
│   ├── analysis/         # Network and entity analysis
│   └── search/           # Search tools
├── docs/                 # All documentation
└── web-svelte/          # Frontend application
```

See [data/DATA_ORGANIZATION.md](data/DATA_ORGANIZATION.md) for complete structure.

---

## Key Resources

### Data Files

- **Entity Network**: [data/metadata/entity_network.json](data/metadata/entity_network.json) (387 entities, 2,221 connections)
- **Semantic Index**: [data/metadata/semantic_index.json](data/metadata/semantic_index.json) (entity → document mappings)
- **Entity Index**: [data/md/entities/ENTITIES_INDEX.json](data/md/entities/ENTITIES_INDEX.json) (1,773 entities)
- **Classifications**: [data/metadata/document_classifications.json](data/metadata/document_classifications.json)

### Analysis Reports

- **Network Statistics**: [data/metadata/entity_network_stats.txt](data/metadata/entity_network_stats.txt)
- **Classification Report**: [data/metadata/classification_report.txt](data/metadata/classification_report.txt)
- **Extraction Summary**: [data/md/entities/EXTRACTION_SUMMARY.md](data/md/entities/EXTRACTION_SUMMARY.md)

---

## Available Tools

| Tool | Purpose | Location |
|------|---------|----------|
| **OCR Processing** | Extract text from PDFs | `scripts/extraction/ocr_house_oversight.py` |
| **Document Classification** | Classify all documents | `scripts/classification/classify_all_documents.py` |
| **Entity Search** | Search by entity/type | `scripts/search/entity_search.py` |
| **Network Analysis** | Build relationship graph | `scripts/analysis/rebuild_flight_network.py` |
| **Entity Enrichment** | Add biographical data | `scripts/enrichment/enrich_entities.py` |

---

## Data Sources

This archive integrates 30+ public document sources:

- **House Oversight Committee** (67,144 PDFs - Nov 2025 release)
- **Giuffre v. Maxwell** court documents
- **FBI Vault** (22 parts)
- **DocumentCloud** collections
- **Court filings** from multiple cases
- **Flight logs** and contact books
- And many more...

**Complete list**: [docs/content/data-sources.md](docs/content/data-sources.md)

---

## Contributing

We welcome contributions! Please see:

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [docs/developer/setup.md](docs/developer/setup.md) - Development environment setup
- [docs/developer/testing.md](docs/developer/testing.md) - Testing guidelines
- [CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md) - Code quality standards

### Code Quality Standards

- **Line Length**: 100 characters
- **Type Hints**: Required for all functions
- **Docstrings**: Google style
- **Test Coverage**: ≥80% for new code
- **Linting**: Ruff, Black, isort, mypy

```bash
# Run quality checks before committing
./scripts/pre_release.sh
```

---

## License & Ethics

### Data Usage

All documents in this archive are from **public sources** with proper attribution. This project:

- Maintains complete source provenance
- Respects privacy of non-public figures
- Focuses on public interest journalism
- Provides transparent research methodology

See [docs/research/ethics.md](docs/research/ethics.md) for ethical guidelines.

### Project License

See [LICENSE](LICENSE) file for project license.

---

## Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Documentation**: See [docs/README.md](docs/README.md) for complete documentation
- **FAQ**: See [docs/user/faq.md](docs/user/faq.md) for common questions

---

## Acknowledgments

- **House Oversight Committee** for document release
- **UC Berkeley** for DocETL analysis
- **Internet Archive** for hosting and preservation
- **DocumentCloud** for document infrastructure
- All public interest journalists and researchers

---

**Built with transparency, organized for research, powered by open data.**
