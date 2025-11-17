# Changelog

All notable changes to the Epstein Document Archive will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- GitHub repository initialization (public)
- FBI Vault download automation (22 parts)
- Complete OCR processing of remaining 18,472 files
- Extract ~2,330 emails from OCR results
- Full document classification (67,144 documents)
- Admin dashboard for source review

## [1.1.0] - 2025-11-17

### Added - Major Feature Release

#### New Pages
- **Timeline page**: Interactive timeline with 103 historical events (1989-2024)
  - Event type filtering (legal, social, death, arrest, investigation, lawsuit, media)
  - Entity linking from timeline events to entity pages
  - Chronological visualization of Epstein case history
- **Login page**: User authentication interface
  - Terms of Service display and acceptance
  - Audit logging for login attempts
  - Session management preparation
- **Documents page**: Full-text document search and browsing
  - Search across 38,177 indexed documents
  - Entity mention highlighting in search results
  - Document type filtering (11 categories)
  - Direct links to entity pages from document mentions
- **Flights map page**: Geographic visualization of flight routes
  - Leaflet.js integration for interactive maps
  - Flight route polylines with origin/destination markers
  - Passenger list display per flight
  - Date and tail number filtering

#### Entity Enhancements
- **Biographical details**: Added detailed biographies for 30+ key figures
  - Jeffrey Epstein, Ghislaine Maxwell, Prince Andrew, Bill Clinton
  - Alan Dershowitz, Les Wexner, Jean-Luc Brunel, and 23 others
  - Structured data with roles, organizations, dates, locations
- **Entity normalization**: Improved name consistency
  - Consolidated duplicate entries (e.g., "Je Epstein" → "Jeffrey Epstein")
  - Reduced network from 387 to 287 nodes
  - Filtered out 100 generic terms (Mr, Ms, Dr, etc.)
- **Entity network filtering**: Cleaner graph visualization
  - Removed staff titles and generic terms
  - Improved relationship accuracy

#### Developer Experience
- **Hot-reload capability**: Server-Sent Events (SSE) for live updates
  - Automatic page refresh on file changes
  - SSE endpoint at `/api/events`
  - Development mode optimization
- **Comprehensive linting system**: Code quality automation
  - Ruff for fast Python linting
  - Black for code formatting
  - isort for import sorting
  - mypy for type checking
  - Makefile targets: `make lint`, `make format`, `make quality`
- **Icon system**: Lucide icons integration
  - Consistent iconography across UI
  - Lightweight SVG-based icons

#### Updates Feed
- **Git commit tracking**: Real-time project updates on homepage
  - Last 10 commits displayed with timestamps
  - Author attribution and commit messages
  - Direct links to changed files (when applicable)

### Fixed
- **Entity name duplication**: Resolved duplicate "Je Epstein" entries in network graph
- **Unclosed HTML tags**: Fixed malformed anchor tags in entity network
- **Document count accuracy**: Corrected display from 6 to 38,177 documents
- **Entity disambiguation**: Improved name matching and consolidation

### Changed
- **Entity network optimization**: Reduced node count by 26% (387→287)
- **Flights page styling**: Enhanced visual presentation and navigation
- **Entity cards**: Added dual linking (entity page + documents mentioning entity)
- **Web interface navigation**: Added Timeline, Documents, Login, Flights pages

### Technical Improvements
- Enhanced entity data structure with biographical fields
- Improved search index with document content
- Added geolocation data for flight visualization
- Implemented event typing system for timeline categorization

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
| 1.1.0   | 2025-11-17   | Timeline page (103 events), Documents search (38,177 docs), Flights map, Login page, Entity biographies, Hot-reload, Linting system |
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
