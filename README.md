# Epstein Document Archive

**The Canonical Data Source of Epstein Files**

Organized, sourced, semantically and structurally indexed archive of Jeffrey Epstein-related documents from public sources.

## 📊 Current Status

- **Total Documents**: 67,144+ PDFs from House Oversight Nov 2025 release
- **Expected Emails**: ~2,330 (per DocETL/UC Berkeley analysis)
- **Entities Indexed**: 1,773 unique entities (people, organizations)
- **Entity Relationships**: 287 entities with 1,648 documented flight co-occurrences
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

- **Entity Network**: `data/metadata/entity_network.json` (287 entities, 1,648 connections)
- **Semantic Index**: `data/metadata/semantic_index.json` (entity → document mappings)
- **Classifications**: `data/metadata/document_classifications.json`
- **Entity Index**: `data/md/entities/ENTITIES_INDEX.json` (1,773 entities)
- **Entity Filtering**: `data/metadata/entity_filter_list.json` (30 generic terms excluded)

## 📈 Network Analysis Highlights

- **Jeffrey Epstein**: 265 connections (most connected entity)
- **Ghislaine Maxwell**: 190 connections, 478 flights with Epstein
- **Sarah Kellen**: 138 connections, 291 flights with Epstein
- **33 Billionaires** in contact book (Leon Black, Glenn Dubin, Les Wexner, etc.)
- **Network cleaned**: Generic entities (Male, Female, etc.) excluded from visualization

See `data/metadata/entity_network_stats.txt` for full analysis.

## 🛠️ Available Tools

- **OCR Processing**: `scripts/extraction/ocr_house_oversight.py`
- **Classification**: `scripts/classification/classify_all_documents.py`
- **Entity Search**: `scripts/search/entity_search.py`
- **Network Analysis**: `scripts/analysis/rebuild_flight_network.py`

## 🧪 Development & Code Quality

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/epstein-document-archive.git
cd epstein-document-archive

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev tools (linting, testing)
pip install ruff black isort mypy pytest pytest-cov
```

### Pre-Release Quality Checks

Before committing code, run quality checks:

```bash
# Check code quality (linting, formatting, type checking)
./scripts/pre_release.sh

# Auto-fix linting and formatting issues
./scripts/pre_release.sh --fix

# Fast check (skip tests)
./scripts/pre_release.sh --fast
```

### Linting Tools

- **Ruff**: Fast Python linter (replaces flake8, isort)
- **Black**: Opinionated code formatter
- **isort**: Import sorting
- **mypy**: Static type checking

**Configuration**: See `.ruff.toml` and `pyproject.toml`

### Code Quality Standards

- **Line Length**: 100 characters
- **Type Hints**: Required for all functions
- **Docstrings**: Google style
- **Test Coverage**: ≥80% for new code
- **No Global State**: Use dependency injection
- **Explicit Error Handling**: No bare except clauses

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines and [CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md) for code quality analysis.

## 📖 Documentation

- `CLAUDE.md` - Project resumption guide
- `CONTRIBUTING.md` - Development guidelines and code standards
- `CODE_REVIEW_REPORT.md` - Comprehensive code quality analysis
- `docs/COMPREHENSIVE_EPSTEIN_DOCUMENT_SOURCES.md` - All 30+ sources
- `data/DATA_ORGANIZATION.md` - Directory structure guide

---

**Last Updated**: 2025-11-17 | **OCR**: 45% complete | **Code Quality**: ⭐⭐⭐⭐ (Good)
