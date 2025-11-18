# Epstein Document Archive - Documentation

**Complete documentation for the Epstein Document Archive project**

**Last Updated**: November 18, 2025
**Documentation Status**: ✅ Reorganized and consolidated

---

## Quick Navigation

### I'm a...

Choose your path based on what you want to do:

#### 👤 User (I want to explore the archive)
**Start here**: [User Guide](user/)

- [Getting Started](user/getting-started.md) - First-time user walkthrough
- [Searching Documents](user/searching.md) - Search by entity, type, connections
- [Understanding Entities](user/entities.md) - Entity database and network
- [Flight Data](user/flights.md) - Flight logs and passenger lists
- [Network Analysis](user/network-analysis.md) - Relationship graphs

**Quick start**:
```bash
# Start the server
python3 server/app.py

# Open browser
http://localhost:8000
```

---

#### 💻 Developer (I want to contribute code)
**Start here**: [Developer Guide](developer/)

**Core Documentation**:
- [Setup Environment](developer/setup.md) - Development environment setup
- [Architecture Overview](developer/architecture.md) - System architecture
- [API Reference](developer/api/) - Complete API documentation
- [UI Development](developer/ui/) - Frontend development guide
- [Testing Guide](developer/testing.md) - Testing procedures

**Quick start**:
```bash
# Set up development environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run development server
cd server
python app.py 8000
```

---

#### 📊 Data Analyst (I want to analyze the data)
**Start here**: [Content Guide](content/) & [Research Guide](research/)

**Data Documentation**:
- [Data Sources](content/data-sources.md) - All document sources
- [Entity Extraction](content/entity-extraction.md) - Entity identification
- [Data Quality](content/data-quality.md) - Quality assurance

**Quick exploration**:
```bash
# View entity statistics
cat data/metadata/entity_statistics.json

# Explore network data
cat data/metadata/entity_network.json
```

---

#### 🚀 Operator (I'm deploying/maintaining)
**Start here**: [Operations Guide](operations/)

- [Deployment Guide](deployment/deployment.md) - Deployment instructions
- [Server Quick Reference](operations/SERVER_QUICK_REFERENCE.md) - Server operations
- [Monitoring](operations/monitoring.md) - System monitoring
- [Troubleshooting](operations/DIAGNOSTIC_INSTRUCTIONS.md) - Common issues

**Quick deployment**:
```bash
# Start production server
./start_server.sh

# Check system status
curl http://localhost:8000/api/health
```

---

## Documentation by Category

### 🎯 Features

Complete feature documentation with implementation details, usage guides, and testing procedures.

**Core Features**:
- **[Timeline Feature](features/TIMELINE_FEATURE.md)** - Flight timeline with month-by-month navigation (49 months, 922 flights)
- **[Entity System](features/ENTITY_SYSTEM.md)** - Entity management with disambiguation (1,639 entities, 0 duplicates)
- **[Progressive Loading](features/PROGRESSIVE_LOADING.md)** - Network performance optimization (100-1,584 connections)

**Visualization Features**:
- **[Network Edge Styling](features/NETWORK_EDGE_STYLING_IMPLEMENTATION.md)** - Enhanced edge visualization
- **[RAG System](features/RAG_SYSTEM.md)** - Retrieval-Augmented Generation for entity Q&A

**Filter & Navigation**:
- **[Flight Filters](features/FLIGHT_FILTERS_STANDARDIZATION.md)** - Standardized flight filtering
- **[Mistral Integration](features/MISTRAL_INTEGRATION_SUMMARY.md)** - AI-powered entity disambiguation

---

### 👨‍💻 Developer Documentation

#### API Documentation ([developer/api/](developer/api/))

**Architecture**:
- [API Refactor Summary](developer/api/API_REFACTOR_SUMMARY.md) - API redesign overview
- [Architecture Diagram](developer/api/ARCHITECTURE_DIAGRAM.md) - System architecture

**Authentication & Security**:
- [Authentication Changes](developer/api/AUTHENTICATION_CHANGES.md) - Auth system updates
- [Authentication Implementation](developer/api/AUTHENTICATION_IMPLEMENTATION.md) - Auth details
- [Audit Logging](operations/AUDIT_LOGGING_IMPLEMENTATION.md) - Audit trail system

**Entity APIs**:
- [Entity Aliases](developer/api/ENTITY_ALIASES.md) - Entity name mapping
- [Entity Biography Fix](developer/api/ENTITY_BIO_FIX.md) - Biography system
- [Entity Linking](developer/api/ENTITY_LINKING_IMPLEMENTATION.md) - Multi-entity linking

**Flight APIs**:
- [Flight Bugs Fix](developer/api/FLIGHT_BUGS_FIX_SUMMARY.md) - Bug fixes
- [Flight Fixes Verification](developer/api/FLIGHT_FIXES_VERIFICATION_REPORT.md) - Verification report

**More**: [View all API docs →](developer/api/)

#### UI Documentation ([developer/ui/](developer/ui/))

**UI Components**:
- [Page Template](developer/ui/PAGE_TEMPLATE.md) - Standard page structure
- [Component Mockups](developer/ui/COMPONENT_MOCKUPS.md) - UI component designs
- [Edge Tooltips](developer/ui/EDGE_TOOLTIPS_IMPLEMENTATION.md) - Network tooltips

**Page Implementations**:
- [Documents Page](developer/api/DOCUMENTS_PAGE_IMPLEMENTATION.md) - Document browser
- [Flights Implementation](developer/ui/FLIGHTS_IMPLEMENTATION.md) - Flight visualization
- [Flights Redesign](developer/ui/FLIGHTS_REDESIGN_SUMMARY.md) - UI redesign

**Styling & Standards**:
- [Standardization Summary](developer/ui/STANDARDIZATION_SUMMARY.md) - UI standards
- [Flights Styling Changes](developer/ui/FLIGHTS_STYLING_CHANGES.md) - Style updates

**More**: [View all UI docs →](developer/ui/)

---

### ⚙️ Operations

**Server Management**:
- [Server Quick Reference](operations/SERVER_QUICK_REFERENCE.md) - Common server operations
- [Diagnostic Instructions](operations/DIAGNOSTIC_INSTRUCTIONS.md) - Troubleshooting guide
- [Audit Logging Quickstart](operations/AUDIT_LOGGING_QUICKSTART.md) - Audit log usage

**Infrastructure**:
- [Ngrok Setup](operations/NGROK_SETUP.md) - Remote access configuration
- [Ngrok Status](operations/NGROK_STATUS.md) - Ngrok connection status

---

### 🔬 Research

**Schema & Architecture**:
- [Pydantic Schema Design](research/PYDANTIC_SCHEMA_DESIGN.md) - Data validation schemas
- [Pydantic Executive Summary](research/PYDANTIC_EXECUTIVE_SUMMARY.md) - Schema overview
- [Pydantic Migration Roadmap](research/PYDANTIC_MIGRATION_ROADMAP.md) - Migration plan
- [Pydantic Quick Start](research/PYDANTIC_QUICK_START.md) - Quick reference

**Data Quality**:
- [Entity Deduplication Research](research/ENTITY_DEDUPLICATION_RESEARCH_REPORT.md) - Duplicate entity analysis

---

### 📋 Project Management

**Project Documentation** (in main docs/):
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Project-wide quick reference
- [ROADMAP.md](ROADMAP.md) - Product roadmap
- [RELEASE_NOTES_v1.1.0.md](RELEASE_NOTES_v1.1.0.md) - Release notes

---

### 🗄️ Archive

Historical documentation preserved for reference.

**By Topic**:
- **[Timeline](archive/timeline/)** - 17 historical timeline implementation docs
- **[Entities](archive/entities/)** - 20 entity system development docs
- **[Progressive Loading](archive/progressive-loading/)** - 7 loading system docs
- **[Sessions](archive/sessions/)** - 4 session pause/resume notes
- **[Implementation](archive/implementation/)** - General implementation summaries
- **[Documentation Meta](archive/documentation-meta/)** - Documentation about documentation

**Note**: Archive files are kept for historical reference. Refer to consolidated feature docs for current information.

---

## Documentation Structure

```
docs/
├── README.md                      # This file - master index
├── QUICK_REFERENCE.md             # Project-wide quick reference
├── ROADMAP.md                     # Product roadmap
├── RELEASE_NOTES_v1.1.0.md        # Release notes
│
├── features/                      # Feature documentation
│   ├── TIMELINE_FEATURE.md        # Timeline feature (consolidated)
│   ├── ENTITY_SYSTEM.md           # Entity system (consolidated)
│   ├── PROGRESSIVE_LOADING.md     # Progressive loading (consolidated)
│   ├── NETWORK_EDGE_STYLING*.md   # Network visualization
│   ├── RAG_SYSTEM*.md             # RAG system
│   ├── MISTRAL*.md                # Mistral integration
│   └── FLIGHT_FILTERS*.md         # Flight filtering
│
├── developer/                     # Developer documentation
│   ├── README.md                  # Developer guide index
│   ├── architecture.md            # System architecture
│   ├── api/                       # API documentation
│   │   ├── API_REFACTOR_SUMMARY.md
│   │   ├── ARCHITECTURE_DIAGRAM.md
│   │   ├── AUTHENTICATION*.md
│   │   ├── ENTITY*.md
│   │   ├── FLIGHT*.md
│   │   └── ... (22 files total)
│   └── ui/                        # UI documentation
│       ├── PAGE_TEMPLATE.md
│       ├── COMPONENT_MOCKUPS.md
│       ├── FLIGHTS*.md
│       └── ... (17 files total)
│
├── operations/                    # Operations documentation
│   ├── README.md                  # Operations guide index
│   ├── SERVER_QUICK_REFERENCE.md
│   ├── DIAGNOSTIC_INSTRUCTIONS.md
│   ├── AUDIT_LOGGING*.md
│   └── NGROK*.md
│
├── research/                      # Research documentation
│   ├── PYDANTIC*.md               # Schema design research
│   └── ENTITY_DEDUPLICATION*.md   # Entity research
│
├── content/                       # Content documentation
│   ├── data-sources.md
│   ├── entity-extraction.md
│   └── ... (existing content docs)
│
├── user/                          # User documentation
│   ├── getting-started.md
│   ├── searching.md
│   └── ... (existing user docs)
│
├── deployment/                    # Deployment documentation
│   └── deployment.md
│
├── data/                          # Data documentation
│   └── ... (existing data docs)
│
├── guides/                        # General guides
│   └── ... (existing guides)
│
└── archive/                       # Historical documentation
    ├── README.md                  # Archive index
    ├── timeline/                  # 17 timeline docs
    ├── entities/                  # 20 entity docs
    ├── progressive-loading/       # 7 loading docs
    ├── sessions/                  # 4 session notes
    ├── implementation/            # Implementation summaries
    └── documentation-meta/        # Documentation meta files
```

---

## Documentation Standards

### File Organization

**Root Directory** (only essential files):
- `README.md` - Project README
- `CHANGELOG.md` - Change history
- `CONTRIBUTING.md` - Contribution guide
- `CLAUDE.md` - AI context file

**All other documentation** → `docs/` directory

### Naming Conventions

- **UPPERCASE_WITH_UNDERSCORES.md** - Documentation files
- **README.md** - Index files for each directory
- **lowercase-with-hyphens.md** - User-facing guides

### Documentation Types

1. **Feature Docs** (`docs/features/`) - Complete feature documentation
   - Overview, implementation, usage, testing, troubleshooting

2. **Developer Docs** (`docs/developer/`) - Code and API documentation
   - Architecture, API reference, implementation guides

3. **Operations Docs** (`docs/operations/`) - Deployment and maintenance
   - Server management, monitoring, troubleshooting

4. **Research Docs** (`docs/research/`) - Design decisions and analysis
   - Schema design, data analysis, architectural research

5. **Archive** (`docs/archive/`) - Historical documentation
   - Preserved for reference, not actively maintained

---

## Recent Changes

### Documentation Reorganization (2025-11-18)

**Major Cleanup**:
- ✅ Reduced root directory from **91 to 4 markdown files**
- ✅ Consolidated **17 timeline docs** → 1 comprehensive guide
- ✅ Consolidated **20 entity docs** → 1 comprehensive guide
- ✅ Consolidated **7 progressive loading docs** → 1 comprehensive guide
- ✅ Moved **22 server docs** → `docs/developer/api/`
- ✅ Moved **17 UI docs** → `docs/developer/ui/`
- ✅ Archived **48 historical docs** → `docs/archive/`

**New Structure**:
- Clear separation by audience (user/developer/operator/researcher)
- Consolidated feature documentation (no duplication)
- Organized API and UI documentation
- Preserved historical documentation in archive

**Benefits**:
- ✅ **Discoverability**: Easy to find relevant documentation
- ✅ **Maintainability**: Single source of truth for each feature
- ✅ **Scalability**: Clear structure for adding new docs
- ✅ **Professionalism**: Clean, organized project

---

## Finding What You Need

### By Task

| I want to... | Go to... |
|--------------|----------|
| Use the application | [User Guide](user/) |
| Search for an entity | [Searching Documents](user/searching.md) |
| Understand flight data | [Flight Data](user/flights.md) |
| Set up development environment | [Developer Setup](developer/setup.md) |
| Understand the API | [API Documentation](developer/api/) |
| Deploy the application | [Deployment Guide](deployment/deployment.md) |
| Troubleshoot issues | [Diagnostic Instructions](operations/DIAGNOSTIC_INSTRUCTIONS.md) |
| Understand the data structure | [Data Sources](content/data-sources.md) |
| Learn about a specific feature | [Features](features/) |

### By Component

| Component | Documentation |
|-----------|---------------|
| Timeline Slider | [Timeline Feature](features/TIMELINE_FEATURE.md) |
| Entity System | [Entity System](features/ENTITY_SYSTEM.md) |
| Network Visualization | [Progressive Loading](features/PROGRESSIVE_LOADING.md), [Network Edge Styling](features/NETWORK_EDGE_STYLING_IMPLEMENTATION.md) |
| RAG System | [RAG System](features/RAG_SYSTEM.md) |
| Flight Filters | [Flight Filters](features/FLIGHT_FILTERS_STANDARDIZATION.md) |
| Authentication | [Authentication Implementation](developer/api/AUTHENTICATION_IMPLEMENTATION.md) |
| Server | [Server Quick Reference](operations/SERVER_QUICK_REFERENCE.md) |

---

## Contributing to Documentation

### Adding New Documentation

1. **Choose the right location**:
   - Feature? → `docs/features/`
   - API/Backend? → `docs/developer/api/`
   - UI/Frontend? → `docs/developer/ui/`
   - Operations? → `docs/operations/`
   - Research? → `docs/research/`

2. **Follow naming conventions**:
   - Use `UPPERCASE_WITH_UNDERSCORES.md` for docs
   - Be descriptive (e.g., `AUTHENTICATION_IMPLEMENTATION.md`)

3. **Include standard sections**:
   - Overview
   - Implementation details
   - Usage examples
   - Testing procedures
   - Troubleshooting

4. **Update this README**:
   - Add link to your new doc in appropriate section
   - Update "By Task" or "By Component" tables if applicable

### Updating Existing Documentation

1. **Update the content**
2. **Update "Last Updated" date**
3. **Commit with descriptive message**:
   ```bash
   git commit -m "docs: Update FEATURE_NAME.md with new usage examples"
   ```

---

## Support

**Questions?**
1. Check this README for navigation
2. Review relevant feature documentation
3. Check troubleshooting guides
4. Review archived documentation for historical context

**Found an issue?**
- Update documentation and submit PR
- Follow contribution guidelines in [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Last Updated**: November 18, 2025
**Documentation Version**: 2.0.0
**Status**: ✅ Complete and Organized
**Maintainer**: Documentation Agent (Claude Code)
