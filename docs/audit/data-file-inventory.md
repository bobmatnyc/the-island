# Data File Inventory Audit

**Date:** 2025-12-06
**Project:** Epstein Document Archive
**Purpose:** Milestone 1 (M1) Audit & Discovery for "Fix Data Relationships" project
**Linear Issue:** [Issue #11 - Audit: Inventory all JSON data files](https://linear.app/1m-hyperdev/issue/13ddc89e7271-11)

---

## Executive Summary

The Epstein project contains **~125,000 data files** totaling **~33.9 GB** of data across multiple formats:

- **67,978 PDF files** (32 GB) - Source documents (immutable)
- **57,014 JSON files** (317 MB + indices) - Extracted and processed data
- **620 MB** - ChromaDB vector store (semantic search layer)
- **57,213 text files** - OCR extractions and processing logs

The data architecture follows a three-layer design:
1. **Source Layer** (32 GB): Immutable original documents
2. **Extraction Layer** (317 MB): JSON files with structured metadata
3. **Semantic Layer** (620 MB): ChromaDB for vector search (partial implementation)

---

## Overall Statistics

### File Counts by Type

| File Type | Count | Total Size | Purpose |
|-----------|-------|------------|---------|
| PDF | 67,978 | ~32 GB | Source documents (court filings, emails, reports) |
| JSON | 57,014 | ~317 MB | Extracted metadata, entities, relationships |
| Text | 57,213 | ~59 MB | OCR extractions, logs |
| Markdown | 81 | ~10 MB | Canonical documents, documentation |
| CSV | 1 | 4 KB | News article seed data |
| YAML | 3 | 56 KB | Entity configuration |
| SQLite DB | 6 | ~560 MB | ChromaDB + empty entity DBs |

### Directory Sizes (Top-Level)

| Directory | Size | Primary Content |
|-----------|------|-----------------|
| `sources/` | 32 GB | **SOURCE LAYER**: Original PDF documents |
| `vector_store/` | 620 MB | **SEMANTIC LAYER**: ChromaDB embeddings |
| `metadata/` | 317 MB | **EXTRACTION LAYER**: JSON indices and entity data |
| `raw/` | 59 MB | Raw extractions and processing artifacts |
| `emails/` | 10 MB | Structured email data |
| `md/` | 10 MB | Markdown extractions |
| `backups/` | 8.9 MB | Data migration backups |
| `migration/` | 820 KB | ID migration mappings |
| `canonical/` | 60 KB | Canonicalized documents (minimal) |
| `logs/` | 48 KB | Processing logs |

---

## Layer 1: Source Documents (Immutable)

**Location:** `/data/sources/`
**Size:** 32 GB
**Files:** 67,976 PDFs
**Architecture Constraint:** Must remain bytecode-identical to originals

### Source Collections

| Collection | Size | File Count | Description |
|------------|------|------------|-------------|
| `house_oversight_nov2025/` | 30 GB | ~60,000 | House Oversight Committee docs (Nov 2025) |
| `documentcloud/` | 427 MB | ~500 | DocumentCloud archive |
| `documentcloud_6250471/` | 427 MB | ~500 | Specific DocumentCloud collection |
| `404media/` | 193 MB | ~300 | 404 Media sourced documents |
| `courtlistener_giuffre_maxwell/` | 191 MB | ~350 | Giuffre v Maxwell case filings |
| `giuffre_maxwell/` | 108 MB | ~200 | Additional Giuffre v Maxwell docs |
| `house_oversight_sept2024/` | 90 MB | ~150 | House Oversight (Sept 2024) |
| `raw_entities/` | 58 MB | ~100 | Raw entity extraction data |
| `fbi_vault/` | 39 MB | ~50 | FBI Vault documents |
| `doj_official/` | 140 KB | ~5 | DOJ official releases |
| `internet_archive/` | 20 KB | ~3 | Internet Archive sources |

**Key Files:**
- `news_articles_seed.csv` (4 KB) - News article seed data
- `news_articles_seed_errors.json` (822 B) - Import error log

### Integrity Verification

**Status:** ✅ Source documents properly isolated
**Recommendation:** Implement SHA-256 checksums for all source PDFs to verify immutability

---

## Layer 2: Extracted Data (Primary JSON Files)

**Location:** `/data/metadata/`
**Size:** 317 MB
**Files:** 56 active JSON files + 78 backups

### Core Entity Files (18.2 MB total)

These files should eventually move to ChromaDB:

| File | Size | Records | Schema | Purpose |
|------|------|---------|--------|---------|
| `entity_biographies.json` | 2.9 MB | 1,637 | `{metadata, entities, [name]}` | Person biographies |
| `entity_locations.json` | 6.4 MB | 429 | `{metadata, entities}` | Location entities + mentions |
| `entity_organizations.json` | 6.3 MB | 888 | `{metadata, entities}` | Organization entities + mentions |
| `entity_document_index.json` | 1.7 MB | 157 | `{entity_to_documents, statistics}` | Entity→Document mappings |
| `entity_network.json` | 266 KB | N/A | Object | Network relationships |
| `entity_statistics.json` | 3.1 MB | N/A | Object | Statistical analysis |
| `entity_relationships_enhanced.json` | 936 KB | N/A | Object | Enhanced relationship data |

**Schema Example (entity_biographies.json):**
```json
{
  "metadata": {
    "total_entities": 1637,
    "last_updated": "2025-12-06",
    "batches_merged": [...],
    "average_quality_score": 0.85,
    "average_word_count": 250
  },
  "entities": {
    "ghislaine_maxwell": {
      "name": "Ghislaine Maxwell",
      "entity_type": "person",
      "summary": "...",
      "metadata": {...}
    }
  }
}
```

### Document Index Files (30 MB total)

| File | Size | Records | Purpose |
|------|------|---------|---------|
| `all_documents_index.json` | 18 MB | 6 root keys | Master document registry |
| `document_entities_full.json` | 7.0 MB | 2 keys | Full entity extraction data |
| `document_entity_index.json` | 3.7 MB | 2 keys | Document→Entity mappings |
| `news_articles_index.json` | 390 KB | Articles array | News article metadata |
| `timeline_events.json` | 64 KB | Events array | Timeline event data |

### Supporting Metadata Files

| File | Size | Purpose |
|------|------|---------|
| `entity_name_mappings.json` | 60 KB | Name normalization mappings |
| `entity_tags.json` | 13 KB | Entity tagging taxonomy |
| `entity_filter_list.json` | 1.5 KB | Entity filtering rules |
| `entity_classifications.json` | 2 KB | Entity classification schema |
| `entity_relationship_ontology.json` | 3.8 KB | Relationship type definitions |
| `entity_guid_migration_report.json` | 2.7 KB | GUID migration log |
| `entity_embedding_progress.json` | 158 B | Embedding generation status |

### Classification & Analysis Files

| File | Size | Purpose |
|------|------|---------|
| `document_classifications.json` | 398 KB | Document type classifications |
| `email_classifications.json` | 333 KB | Email categorizations |
| `enriched_entity_data.json` | 39 KB | Enriched entity metadata |
| `cases_index.json` | 22 KB | Legal case index |
| `chatbot_knowledge_index.json` | 27 KB | Chatbot knowledge base |

### Archive & Backups (8.9 MB)

**Backup Files:** 78 timestamped backups in `/data/metadata/`
- Entity biography backups: 60+ files (Nov 26 - Dec 6)
- Entity organization backups: 2 files (Dec 6)
- Entity location backups: 1 file (Dec 6)

**Archive Directory:** `/data/metadata/archive/`
- `batch_biographies/2025-11-26/`: 15 batch files (entity biography batches)

**Recommendation:** Move backups to `/data/backups/metadata/` to reduce clutter

---

## Layer 3: Semantic Search (ChromaDB)

**Location:** `/data/vector_store/`
**Size:** 620 MB

### ChromaDB Structure

| Component | Size | Purpose |
|-----------|------|---------|
| `chroma/chroma.sqlite3` | 551 MB | ChromaDB main database |
| `chroma/ff855d08-d06a-4172-a938-f3f3d21fb500/` | 59 MB | Collection embeddings |
| `embedding_progress.json` | 788 KB | Document embedding progress |
| `news_embedding_progress.json` | 10 KB | News article embedding progress |

**Status:** ✅ Partially implemented
**Coverage:** ~60% of documents embedded

**Recommendation:** Complete ChromaDB migration for all entities and relationships

---

## Other Data Directories

### Canonical Data (`/data/canonical/` - 60 KB)

Minimal canonicalized documents:
- `emails/`: 7 files (email index, statistics, 3 canonical emails)
- `court_filings/`: 1 example file
- `address_books/`, `fbi_reports/`, `financial/`, `flight_logs/`, `other/`: Empty

**Status:** ⚠️ Underutilized - Most documents not canonicalized

### Raw Extractions (`/data/raw/` - 59 MB)

Processing artifacts organized by source:
- `documentcloud_6250471/`, `documentcloud_6506732/`, `fbi_vault/`
- `giuffre_maxwell/`, `house_oversight_nov2025/`, `other_sources/`
- `entities/`: Empty (no JSON files)

### Emails (`/data/emails/` - 10 MB)

| File | Size | Purpose |
|------|------|---------|
| `epstein-emails-complete.pdf` | 6.4 MB | Complete email archive (PDF) |
| `epstein-emails-structured.json` | 115 KB | Structured email data |
| `house_oversight_nov2025/` | ~3 MB | Email PDFs from House Oversight |
| `pages/`, `markdown/`: Email page extractions |

### Markdown Extractions (`/data/md/` - 10 MB)

Markdown conversions organized by source:
- `documentcloud_6250471/`, `fbi_vault/`, `giuffre_maxwell/`
- `entities/`: 24 entity markdown files

### Migration Data (`/data/migration/` - 820 KB)

| File | Size | Purpose |
|------|------|---------|
| `entity_id_mappings.json` | 799 KB | Entity ID migration mappings |
| `entity_network_aliases_analysis.json` | 4.7 KB | Network alias analysis |
| `entity_network_aliases.json` | 2.7 KB | Network aliases |
| `id_generation_stats.json` | 4.5 KB | ID generation statistics |

### Backups (`/data/backups/` - 8.9 MB)

Historical cleanup and merge backups:
- `cleanup_20251117_154221/`, `cleanup_20251117_154454/`, `cleanup_20251117_154655/`
- `nested_fix_20251117_154752/`, `name_fix_20251117_183207/`
- `epstein_merge_20251119_160747/`

### Empty/Minimal Files

| File | Size | Status |
|------|------|--------|
| `entities.db` | 0 B | Empty SQLite database |
| `epstein.db` | 0 B | Empty SQLite database |
| `entities.yaml` | 53 KB | Entity configuration (active) |
| `temp/` | 0 B | Empty directory |
| `temp_import_nov25_dec6_errors.json` | 532 B | Recent import errors |

---

## Data Organization Issues

### 1. Backup File Proliferation

**Problem:** 78 backup files scattered in `/data/metadata/`
**Impact:** Directory clutter, difficult to identify active files
**Recommendation:**
- Move all `*backup*.json` files to `/data/backups/metadata/{YYYY-MM-DD}/`
- Keep only latest backup per file in metadata directory
- Implement retention policy (e.g., keep last 7 days, then weekly for 90 days)

### 2. Empty Database Files

**Problem:** `entities.db` and `epstein.db` are 0 bytes
**Impact:** Confusion about data storage strategy
**Recommendation:**
- Delete empty `.db` files if not in use
- Document intended use case if planned for future

### 3. Canonical Directory Underutilization

**Problem:** Only 8 files in canonical directory out of 67,976 source docs
**Impact:** Canonicalization goal not being met
**Recommendation:**
- Clarify canonicalization strategy
- If not needed, remove directory; if needed, implement pipeline

### 4. Duplicate Organizational Structures

**Problem:** Similar directory structures in `/data/raw/`, `/data/md/`, `/data/sources/`
**Impact:** Confusion about which is "source of truth"
**Recommendation:**
- Document hierarchy: `sources/` (original) → `raw/` (first extraction) → `metadata/` (structured)
- Consider consolidating or clearly documenting purpose of each layer

---

## ChromaDB Migration Candidates

Files that should be migrated from JSON to ChromaDB:

### Priority 1: Entity Data (18.2 MB)
- ✅ `entity_biographies.json` (2.9 MB) - Person entities with biographies
- ✅ `entity_locations.json` (6.4 MB) - Location entities
- ✅ `entity_organizations.json` (6.3 MB) - Organization entities
- ✅ `entity_network.json` (266 KB) - Network relationships
- ✅ `entity_relationships_enhanced.json` (936 KB) - Enhanced relationships

**Benefit:** Enable semantic search across entities, improve query performance

### Priority 2: Document Relationships (10.7 MB)
- ⚠️ `document_entities_full.json` (7.0 MB) - Full entity extraction
- ⚠️ `document_entity_index.json` (3.7 MB) - Document-entity mappings

**Benefit:** Fast lookup of entities mentioned in documents

### Priority 3: Supporting Indices
- `entity_document_index.json` (1.7 MB) - Entity-to-document reverse index
- `enriched_entity_data.json` (39 KB) - Additional entity metadata

**Benefit:** Bidirectional search (entity→doc, doc→entity)

### Retain as JSON (Master Indices)
- ✅ `all_documents_index.json` (18 MB) - Master document registry
- ✅ `news_articles_index.json` (390 KB) - News metadata
- ✅ `timeline_events.json` (64 KB) - Timeline data

**Reason:** These serve as master registries and are frequently updated

---

## Recommendations

### Immediate Actions (M1 Completion)

1. **Backup Consolidation**
   - Move 78 backup files to `/data/backups/metadata/{YYYY-MM-DD}/`
   - Implement backup retention policy

2. **File Cleanup**
   - Delete empty `entities.db` and `epstein.db` files
   - Archive or delete `temp_import_nov25_dec6_errors.json` after review

3. **Documentation**
   - Document purpose of each top-level directory in `/data/README.md`
   - Add schema documentation for all primary JSON files

### Short-Term (M2-M3)

4. **ChromaDB Migration**
   - Migrate Priority 1 entity files to ChromaDB
   - Implement entity relationship queries in ChromaDB
   - Verify embeddings cover all documents

5. **Index Consolidation**
   - Merge `document_entity_index.json` and `document_entities_full.json`
   - Create unified entity-document relationship table in ChromaDB

6. **Canonical Directory Strategy**
   - Define canonicalization goals and scope
   - Implement pipeline or remove unused directory

### Long-Term (M4+)

7. **Data Deduplication**
   - Identify duplicate or near-duplicate documents in sources
   - Implement deduplication tracking without modifying source files

8. **Relationship Ontology**
   - Expand `entity_relationship_ontology.json` with formal definitions
   - Implement relationship validation pipeline

9. **Automated Integrity Checks**
   - Implement SHA-256 checksums for all source documents
   - Add daily validation job to ensure source immutability

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SOURCE LAYER (32 GB)                     │
│                  /data/sources/ - Immutable                 │
│                    67,976 PDF Documents                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼ OCR & Extraction
┌─────────────────────────────────────────────────────────────┐
│                  EXTRACTION LAYER (317 MB)                  │
│                     /data/metadata/                         │
│    • all_documents_index.json (18 MB) - Master registry    │
│    • document_entities_full.json (7 MB) - Entity mentions  │
│    • entity_biographies.json (2.9 MB) - Person entities    │
│    • entity_locations.json (6.4 MB) - Location entities    │
│    • entity_organizations.json (6.3 MB) - Org entities     │
│    • 50+ supporting index and mapping files                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼ Embedding Generation
┌─────────────────────────────────────────────────────────────┐
│                   SEMANTIC LAYER (620 MB)                   │
│                   /data/vector_store/                       │
│              ChromaDB - Vector Embeddings                   │
│         • Document embeddings (60% complete)                │
│         • Entity embeddings (planned)                       │
│         • Relationship embeddings (planned)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## File Categories Summary

| Category | Files | Size | Status | Next Action |
|----------|-------|------|--------|-------------|
| **Source Documents** | 67,978 | 32 GB | ✅ Stable | Add checksums |
| **Active Metadata** | 56 | ~60 MB | ✅ Active | Migrate to ChromaDB |
| **Backup Files** | 78 | ~257 MB | ⚠️ Cluttered | Consolidate to backups/ |
| **Vector Store** | ~5 | 620 MB | 🔄 In Progress | Complete embeddings |
| **Canonical** | 8 | 60 KB | ⚠️ Minimal | Define strategy |
| **Raw Extractions** | ~5,000 | 59 MB | ✅ Stable | Archive old extractions |
| **Email Data** | ~100 | 10 MB | ✅ Stable | Maintain |
| **Migration Files** | 4 | 820 KB | ✅ Historical | Archive |

**Legend:**
- ✅ Stable: Working as intended
- ⚠️ Needs Attention: Issues identified
- 🔄 In Progress: Active development

---

## Appendix A: Complete File Listing

### Top 20 Largest Files (Metadata)

1. `all_documents_index.json` - 18 MB
2. `document_entities_full.json` - 7.0 MB
3. `entity_locations.json` - 6.4 MB
4. `entity_organizations.json` - 6.3 MB
5. `document_entity_index.json` - 3.7 MB
6. `entity_statistics.json` - 3.1 MB
7. `entity_biographies.json` - 2.9 MB
8. `entity_document_index.json` - 1.7 MB
9. `entity_relationships_enhanced.json` - 936 KB
10. `all_documents_index.json.backup` - 11 MB (backup)
11. `all_documents_index.json.rebuild_backup` - 11 MB (backup)
12. `document_classifications.json` - 398 KB
13. `email_classifications.json` - 333 KB
14. `entity_network.json` - 266 KB
15. `entity_biographies_tier4.json` - 82 KB
16. `entity_name_mappings.json` - 60 KB
17. `enriched_entity_data.json` - 39 KB
18. `cases_index.json` - 22 KB
19. `entity_tags.json` - 13 KB
20. `timeline_events.json` - 64 KB

### Key Entity Files by Type

**People Entities:**
- `entity_biographies.json` (2.9 MB, 1,637 entities)
- `entity_biographies_tier4.json` (82 KB, subset)
- `entity_biographies_grok.json` (2.3 KB, Grok-generated subset)

**Location Entities:**
- `entity_locations.json` (6.4 MB, 429 entities)

**Organization Entities:**
- `entity_organizations.json` (6.3 MB, 888 entities)

**Relationship Files:**
- `entity_network.json` (266 KB)
- `entity_relationships_enhanced.json` (936 KB)
- `entity_relationship_ontology.json` (3.8 KB, schema)

---

## Appendix B: Empty or Near-Empty Directories

| Directory | Files | Size | Recommendation |
|-----------|-------|------|----------------|
| `/data/temp/` | 0 | 0 B | Keep for processing |
| `/data/canonical/address_books/` | 0 | 0 | Remove or populate |
| `/data/canonical/fbi_reports/` | 0 | 0 | Remove or populate |
| `/data/canonical/financial/` | 0 | 0 | Remove or populate |
| `/data/canonical/flight_logs/` | 0 | 0 | Remove or populate |
| `/data/canonical/other/` | 0 | 0 | Remove or populate |
| `/data/raw/entities/` | 0 | 0 | Remove or document purpose |
| `/data/sources/courtlistener/` | 0 | 0 | Remove or populate |
| `/data/sources/house_oversight_sept2025/` | 0 | 0 | Remove or populate |

---

## Audit Completion

**Audit Completed:** 2025-12-06
**Files Inventoried:** 125,287 files
**Total Data Audited:** 33.9 GB
**Active JSON Files:** 56
**Backup JSON Files:** 78
**Source Documents:** 67,978 PDFs

**Next Steps:**
1. Review recommendations with project stakeholders
2. Implement backup consolidation (M1)
3. Plan ChromaDB migration strategy (M2)
4. Execute data layer reorganization (M3-M4)

**Related Linear Issues:**
- [Issue #11 - Audit: Inventory all JSON data files](https://linear.app/1m-hyperdev/issue/13ddc89e7271-11) (This audit)
- M2: ChromaDB migration planning
- M3: Index consolidation
- M4: Data relationship fixes

---

*End of Audit Report*
