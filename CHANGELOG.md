# Changelog

All notable changes to the Epstein Document Archive will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Roadmap documentation with 6 development phases
- Comprehensive changelog tracking
- Version file for automated version management
- Dark/light theme toggle with localStorage persistence
- Source suggestion submission system in web UI
- OpenRouter GPT-4.5 integration for AI chatbot
- Collapsible chat sidebar for better UX
- Hierarchical roadmap tracking system
- Roadmap tab in web interface navigation

### Changed
- Enhanced web interface navigation structure
- Improved theme switching performance
- Updated documentation structure

### Planned
- GitHub repository initialization (public)
- FBI Vault download automation (22 parts)
- Complete OCR processing of remaining 18,472 files
- Extract ~2,330 emails from OCR results
- Full document classification (67,144 documents)
- Timeline generation from dated documents
- Admin dashboard for source review

## [0.1.0] - 2025-11-16

### Added - Initial Release

#### Infrastructure
- Git repository initialization with 66,915 files
- Directory structure organization (`/data/raw`, `/data/md`, `/data/metadata`, `/data/canonical`)
- Python virtual environment setup
- FastAPI REST API server
- Data reorganization script (`scripts/reorganize_data.py`)

#### Document Processing
- OCR processing pipeline with Tesseract integration
- Parallel OCR processing with 10 workers
- Checkpoint/resume capability for long-running OCR jobs
- Progress tracking script (`scripts/extraction/check_ocr_status.py`)
- Email detection patterns (From:, To:, Subject:)
- Email candidates tracking (`email_candidates.jsonl`)
- Deduplication system with SQLite database
- Quality-based document version selection

#### Entity Extraction
- Black Book CSV parsing (1,740 contacts)
- Flight log PDF OCR extraction (3,721 records)
- Birthday Book PDF processing
- Entity normalization for name variations
- Billionaire identification (33 billionaires marked)
- Master entity index creation (`ENTITIES_INDEX.json` - 1,773 unique entities)
- Cross-source entity linking
- Entity metadata aggregation

#### Network Analysis
- Flight log parsing into 1,167 unique flights
- Entity relationship network building (387 nodes, 2,221 edges)
- Co-occurrence analysis from flight passenger lists
- Network centrality metrics
- Top relationship identified: Epstein ↔ Maxwell (228 flights together)
- Network statistics report (`entity_network_stats.txt`)

#### Document Classification
- 11-category classification framework:
  - email, court_filing, financial, flight_log, contact_book
  - investigative, legal_agreement, personal, media, administrative, unknown
- Keyword-based pattern matching
- Confidence scoring system (0.0-1.0)
- Secondary classification support
- Classification report generation

#### Search & Discovery
- Entity search tool (`scripts/search/entity_search.py`)
  - Search by entity name (`--entity "Clinton"`)
  - Connection lookup (`--connections "Ghislaine"`)
  - Multi-entity search (`--multiple`)
  - Document type filtering (`--type "email"`)
- Semantic index linking entities to documents
- Cross-reference search across contact books and flight logs

#### Web Interface
- HTML/CSS/JavaScript frontend with responsive design
- D3.js force-directed network graph visualization
- Interactive node exploration with click events
- Entity details panel with connection count, document mentions, billionaire status, centrality scores
- Network visualization controls (adjustable link distance, charge strength)
- Tab-based navigation: Overview, Entities, Network Graph, Ingestion Status
- Dark/light theme toggle with system preference detection
- Theme persistence via localStorage
- Real-time statistics in header (entities, connections, documents)

#### AI Features
- Archive Assistant chatbot powered by Qwen 2.5 Coder (via OpenRouter)
- Collapsible chat sidebar (380px width)
- Message history with user/assistant/system messages
- Loading indicator with animated dots
- Context-aware entity and document queries
- Source suggestion submission modal

#### Data Sources
- House Oversight Committee Nov 2025 release (67,144 PDFs)
- Black Book contact list (CSV)
- Flight logs (PDF)
- Birthday Book (PDF)
- Download automation scripts for multiple sources

#### Documentation
- README.md, CLAUDE.md, SESSION_RESUME.md, SYSTEM_SUMMARY.md
- ORGANIZATION_SUMMARY.md, ACCESS_INFO.md, DOWNLOAD_MANIFEST.md
- Data organization guide, comprehensive source list
- Extraction summaries and network analysis reports

#### Scripts & Tools
- Extraction: OCR processing, progress monitoring
- Classification: Document classifier, batch processing
- Analysis: Network building, flight network reconstruction
- Search: Command-line entity search tool
- Utilities: Data reorganization, download verification

#### Metadata & Indexes
- Entity network graph, semantic index, document classifications
- Network statistics, classification reports, source provenance tracking
- Structured flight data, deduplication database

### Fixed
- Birthday Book OCR quality issues (noted for manual review)
- Flight log name variation inconsistencies
- Directory structure for multi-source document organization

### Security
- Public archive contains only publicly available documents
- No personal identifying information beyond public records

---

## Version History Summary

| Version | Release Date | Key Highlights |
|---------|--------------|----------------|
| 0.1.0   | 2025-11-16   | Initial release with 67,144 documents, entity extraction, network visualization, AI chatbot |

---

## Versioning Policy

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes or major architectural changes
- **MINOR** version (0.X.0): New features in a backwards-compatible manner
- **PATCH** version (0.0.X): Backwards-compatible bug fixes

---

**Changelog Maintained By**: Archive Project Team
**Last Updated**: 2025-11-16 23:55 EST
