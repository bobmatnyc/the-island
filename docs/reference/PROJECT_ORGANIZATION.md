# Project Organization Standard

**Version**: 1.0
**Last Updated**: 2025-11-24
**Status**: Active

## Overview

This document defines the official file organization standards for the Epstein Documents Archive project. All contributors and AI assistants must follow these rules to maintain a clean, organized codebase.

## Philosophy

- **Minimal Root Directory**: Keep the project root clean and uncluttered
- **Logical Grouping**: Files are organized by purpose and type
- **Consistent Structure**: Predictable locations make navigation easier
- **Version Control Friendly**: Structure supports git history and collaboration

## Directory Structure

```
epstein/
├── README.md                    # Main project overview
├── CLAUDE.md                    # AI assistant instructions
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── SECURITY.md                  # Security policy
├── pyproject.toml               # Python project configuration
├── Makefile                     # Build automation
├── .gitignore                   # Git ignore rules
├── .env.example                 # Environment template
│
├── docs/                        # ALL documentation (except core 5)
│   ├── reference/               # Reference documentation
│   ├── implementation-summaries/# Feature implementation summaries
│   ├── qa-reports/              # QA and testing reports
│   ├── linear-tickets/          # Linear ticket updates
│   ├── archive/                 # Historical documentation
│   │   ├── txt-files/           # Archived text/log files
│   │   └── screenshots/         # Archived screenshots
│   ├── developer/               # Developer guides
│   └── frontend/                # Frontend documentation
│
├── tests/                       # ALL test files
│   ├── api/                     # API tests
│   ├── browser/                 # Browser/HTML tests
│   ├── qa/                      # QA-specific tests
│   ├── verification/            # Verification scripts
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
│
├── scripts/                     # ALL scripts
│   ├── analysis/                # Data analysis
│   ├── ingestion/               # Data ingestion
│   ├── rag/                     # RAG-related
│   ├── verification/            # Test/verification
│   ├── operations/              # Operational (start, restart)
│   └── cli/                     # CLI utilities
│
├── frontend/                    # React frontend application
│   ├── src/
│   ├── public/
│   └── package.json
│
├── server/                      # FastAPI backend
│   ├── app.py
│   └── ...
│
└── data/                        # Data files
    ├── metadata/
    └── ...
```

## File Organization Rules

### Core Documentation (Root Only)

Only these five documentation files belong in the project root:

1. **README.md** - Main project overview and quick start
2. **CLAUDE.md** - AI assistant instructions and project memory
3. **CHANGELOG.md** - Version history and release notes
4. **CONTRIBUTING.md** - Contribution guidelines and development workflow
5. **SECURITY.md** - Security policy and vulnerability reporting

**All other documentation** must go in `docs/` subdirectories.

### Documentation Files (`docs/`)

| File Type | Location | Examples |
|-----------|----------|----------|
| Implementation summaries | `docs/implementation-summaries/` | Feature completion reports, implementation details |
| QA reports | `docs/qa-reports/` | Test results, QA evidence, bug reports |
| Linear tickets | `docs/linear-tickets/` | Ticket resolutions, status updates |
| Reference docs | `docs/reference/` | API specs, architecture docs, standards |
| Historical docs | `docs/archive/` | Old docs, deprecated features |
| Developer guides | `docs/developer/` | Setup guides, tutorials |
| Frontend docs | `docs/frontend/` | React component docs, UI guides |

**Rules**:
- Use descriptive filenames with topic prefixes (e.g., `BIO_ENRICHMENT_COMPLETE_REPORT.md`)
- Archive old docs rather than deleting them
- Update index files when adding major documentation

### Test Files (`tests/`)

| File Type | Location | Examples |
|-----------|----------|----------|
| API tests (Python) | `tests/api/` | `test_entity_detection.py`, `test_guid_endpoint.py` |
| Browser tests (HTML) | `tests/browser/` | `test_biography_rendering.html`, `test_pdf_viewer.html` |
| QA tests | `tests/qa/` | Manual test scripts, QA validation |
| Verification scripts | `tests/verification/` | Python verification scripts |
| Unit tests | `tests/unit/` | Component unit tests |
| Integration tests | `tests/integration/` | End-to-end integration tests |

**Rules**:
- Python test files must start with `test_` or end with `_test.py`
- HTML test files should include `test` in filename
- Keep test data in `tests/fixtures/` or `tests/data/`
- Use descriptive names indicating what is being tested

### Scripts (`scripts/`)

| Script Type | Location | Examples |
|-------------|----------|----------|
| Data analysis | `scripts/analysis/` | `enrich_bios_from_documents.py` |
| Data ingestion | `scripts/ingestion/` | Import and ETL scripts |
| RAG operations | `scripts/rag/` | RAG system scripts |
| Verification | `scripts/verification/` | `verify-pdf-viewer.sh`, `test-entity-news-cards.sh` |
| Operations | `scripts/operations/` | `start_all.sh`, `restart-backend.sh` |
| CLI tools | `scripts/cli/` | `epstein-cli.py` |

**Rules**:
- Shell scripts use `.sh` extension
- Python scripts use `.py` extension
- Make scripts executable: `chmod +x script.sh`
- Include shebang line: `#!/bin/bash` or `#!/usr/bin/env python3`
- Add brief description comment at top of file

### Archive Files (`docs/archive/`)

| File Type | Location |
|-----------|----------|
| Text/log files | `docs/archive/txt-files/` |
| Screenshots | `docs/archive/screenshots/` |
| Old documentation | `docs/archive/` |
| Migration logs | `docs/archive/migration-logs/` |

**Rules**:
- Archive instead of delete when possible
- Use timestamps in filenames for logs
- Compress large archived files

## Configuration Files (Root Level)

The following configuration files belong in the project root:

- `.gitignore` - Git ignore patterns
- `.env.example` - Environment variable template
- `.env.local` - Local environment (not committed)
- `pyproject.toml` - Python project metadata
- `Makefile` - Build automation
- `.mcp.json` - MCP configuration
- `.ruff.toml` - Ruff linter config
- `ecosystem.config.js` - PM2 configuration
- `VERSION` - Version file

## Naming Conventions

### Documentation Files
- Use UPPERCASE for major docs: `BIO_ENRICHMENT_COMPLETE_REPORT.md`
- Use descriptive names: `ENTITY_GUID_MIGRATION.md`
- Include dates for time-sensitive docs: `QA_REPORT_GUID_HYDRATION.md`

### Test Files
- Python: `test_<feature>.py` or `<feature>_test.py`
- HTML: `test-<feature>.html`
- Scripts: `test-<feature>.sh` or `verify-<feature>.sh`

### Scripts
- Operations: `start_`, `stop_`, `restart_`
- Verification: `verify-`, `test-`, `check-`
- Data: `ingest_`, `analyze_`, `export_`

## Framework-Specific Rules

### Python (FastAPI Backend)
- Source code in `server/` directory
- Tests in `tests/api/` or `tests/unit/`
- Scripts in `scripts/` with appropriate subdirectory
- No Python files in project root (except config files)

### React (Frontend)
- Application code in `frontend/src/`
- Tests in `frontend/src/` (colocated) or `tests/browser/`
- Build outputs in `frontend/dist/` (gitignored)
- No frontend files in project root

## Migration History

### 2025-11-24: Initial Reorganization
- Moved 70+ files from root to proper directories
- Established official organization standard
- Updated CLAUDE.md with organization rules
- Created PROJECT_ORGANIZATION.md

**Files Moved**:
- 11 documentation files → `docs/implementation-summaries/`, `docs/qa-reports/`
- 18 test files → `tests/api/`, `tests/browser/`
- 31 scripts → `scripts/verification/`, `scripts/operations/`
- 12 text/log files → `docs/archive/txt-files/`

## Enforcement

### For Developers
1. Read this document before contributing
2. Follow the structure when creating new files
3. Move misplaced files to correct locations
4. Update this document if patterns evolve

### For AI Assistants
1. Always check PROJECT_ORGANIZATION.md before creating files
2. Suggest proper locations when users create files
3. Identify and flag organization violations
4. Reference this document when explaining file placement

### Validation Commands

Check for misplaced files:
```bash
# Check for .md files in root (except core 5)
find . -maxdepth 1 -name "*.md" | grep -v -E "(README|CLAUDE|CHANGELOG|CONTRIBUTING|SECURITY).md"

# Check for scripts in root
find . -maxdepth 1 -name "*.sh" -o -name "*.py" -type f

# Check for test files in root
find . -maxdepth 1 -name "test*.html" -o -name "test*.py" -o -name "verify*.sh"

# Check for text/log files in root
find . -maxdepth 1 -name "*.txt" -o -name "*.log"
```

## Updates and Versioning

This document follows semantic versioning:
- **Major version**: Fundamental reorganization
- **Minor version**: New subdirectories or categories
- **Patch version**: Clarifications and examples

**Change Log**:
- v1.0 (2025-11-24): Initial organization standard established

## Questions and Clarifications

If you're unsure where a file should go:
1. Check this document first
2. Look for similar existing files
3. Consider the file's purpose (docs, tests, scripts, config)
4. When in doubt, ask in the project discussion

## Future Considerations

Potential future organization improvements:
- Add `benchmarks/` directory for performance tests
- Create `tools/` for development utilities
- Establish `migrations/` for database migrations
- Add `fixtures/` at top level for shared test data

---

**Document Owner**: Project Maintainers
**Review Frequency**: Quarterly or when major reorganization occurs
**Last Review**: 2025-11-24
