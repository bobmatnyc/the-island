# Canonical Data Processing Scripts

**Last Updated**: 2025-11-19
**Purpose**: Define the OFFICIAL scripts for each data processing stage
**Status**: Phase 1 - Initial Documentation

---

## ⚠️ CRITICAL RULE

**ONE CANONICAL SCRIPT PER TRANSFORMATION**

- Do NOT create alternative implementations
- Do NOT create one-off fix scripts
- Do NOT modify core data outside canonical scripts
- DO use `scripts/lib/atomic_io.py` for all writes
- DO track changes with `scripts/lib/metadata_tracker.py`

---

## Data Processing Pipeline

### Stage 1: Document Ingestion

#### Download Scripts (Parallel, source-specific)

**House Oversight Documents**
- **Script**: `download_house_oversight_sept2024.sh`
- **Location**: `/Users/masa/Projects/epstein/scripts/`
- **Input**: DocumentCloud API
- **Output**: `data/sources/house_oversight_nov2025/epstein-pdf/*.pdf`
- **Status**: ✅ Production
- **Last Updated**: 2025-11-17

**FBI Vault Documents**
- **Script**: `download_fbi_vault.sh`
- **Location**: `/Users/masa/Projects/epstein/scripts/`
- **Input**: FBI Vault API
- **Output**: `data/sources/fbi_vault/*.pdf`
- **Status**: ✅ Production

**DocumentCloud**
- **Script**: `download_documentcloud.sh`
- **Location**: `/Users/masa/Projects/epstein/scripts/`
- **Input**: DocumentCloud API
- **Output**: `data/sources/documentcloud/*.pdf`
- **Status**: ✅ Production

**Alternative: Hugging Face Import**
- **Scripts**:
  - `import/import_huggingface_documents.py` - Import documents from HF dataset
  - `import/import_huggingface_emails.py` - Import emails from HF dataset
- **Input**: Hugging Face datasets (20K documents)
- **Output**: Same structure as download scripts
- **Status**: ✅ Production
- **Use Case**: Bulk import from existing datasets

---

### Stage 2: Text Extraction

#### OCR Processing
- **Script**: `extraction/ocr_house_oversight.py`
- **Input**: `data/sources/house_oversight_nov2025/epstein-pdf/*.pdf`
- **Output**:
  - `data/sources/house_oversight_nov2025/ocr_text/*.txt`
  - `data/sources/house_oversight_nov2025/ocr_progress.json` (state tracking)
- **Features**:
  - Parallel OCR with `pytesseract`
  - Email detection during OCR
  - Resume capability (tracks progress)
  - Quality scoring
- **Dependencies**: tesseract-ocr (system package)
- **Status**: ✅ Production, resume-capable
- **Last Updated**: 2025-11-16

#### Email Extraction
- **Script**: `extraction/extract_emails.py`
- **Input**: `data/sources/house_oversight_nov2025/ocr_text/*.txt`
- **Output**:
  - `data/emails/house_oversight_nov2025/YYYY-MM/*.txt` (organized by date)
  - `data/emails/house_oversight_nov2025/EMAIL_INDEX.json`
- **Features**:
  - Date-based directory organization
  - Metadata extraction (From, To, Date, Subject)
  - Full text and body-only files
- **Status**: ✅ Production
- **Last Updated**: 2025-11-16

---

### Stage 3: Entity Extraction & Normalization

⚠️ **CRITICAL**: This stage has **5 canonical scripts** that must run in order.

#### 3.1 Entity Network Building (Primary)
- **Script**: `analysis/entity_network.py`
- **Input**: Flight logs, documents (various sources)
- **Output**: `data/md/entities/ENTITIES_INDEX.json` (1,639 entities)
- **Purpose**: Extract entities from co-occurrence patterns in flight logs
- **Features**:
  - Flight log co-passenger analysis
  - Name variation detection
  - Relationship strength scoring
- **Status**: ✅ Production (but needs consolidation with other entity scripts)
- **Last Updated**: 2025-11-17
- **Note**: This is the PRIMARY entity source, others are cleanup/enrichment

#### 3.2 Entity Name Normalization
- **Script**: `data_quality/normalize_entity_names.py`
- **Input**: `ENTITIES_INDEX.json`
- **Output**: `ENTITIES_INDEX.json` (updated with normalized names)
- **Purpose**: Standardize name formats to "Last, First" convention
- **Features**:
  - Handles multiple name formats
  - Preserves name variations
  - Logs all transformations
- **Dependencies**: Must run after `entity_network.py`
- **Status**: ✅ Production
- **Last Updated**: 2025-11-18

#### 3.3 Duplicate Entity Merging
- **Script**: `data_quality/merge_epstein_duplicates.py`
- **Input**: `ENTITIES_INDEX.json`
- **Output**: `ENTITIES_INDEX.json` (deduplicated)
- **Purpose**: Merge duplicate "Epstein, Jeffrey" variants
- **Features**:
  - Merges name variations ("Jeffrey Epstein", "Epstein Jeffrey", etc.)
  - Preserves all metadata and relationships
  - Creates backup before merging
- **Dependencies**: Must run after `normalize_entity_names.py`
- **Status**: ✅ Production
- **Last Updated**: 2025-11-19

#### 3.4 Biography Restoration
- **Script**: `data_quality/restore_entity_bios.py`
- **Input**:
  - `ENTITIES_INDEX.json`
  - `data/metadata/entity_biographies.json`
- **Output**: `ENTITIES_INDEX.json` (with restored biographies)
- **Purpose**: Restore biographies lost during normalization
- **Features**:
  - Smart name matching (handles format changes)
  - Preserves all biography data
  - Reports unmatched entities
- **Dependencies**: Must run after `merge_epstein_duplicates.py`
- **Status**: ✅ Production
- **Last Updated**: 2025-11-19

#### 3.5 Final Entity Cleanup
- **Script**: `analysis/final_entity_cleanup_complete.py`
- **Input**: `ENTITIES_INDEX.json`
- **Output**: `ENTITIES_INDEX.json` (cleaned)
- **Purpose**: Final validation and cleanup of entity data
- **Features**:
  - Removes invalid/malformed entities
  - Validates entity structure
  - Fixes edge cases
- **Dependencies**: Must run after `restore_entity_bios.py`
- **Status**: ✅ Production
- **Last Updated**: 2025-11-18

#### Entity Processing Order (REQUIRED)
```bash
# Run in this exact order:
python3 scripts/analysis/entity_network.py              # 1. Build initial entities
python3 scripts/data_quality/normalize_entity_names.py  # 2. Normalize names
python3 scripts/data_quality/merge_epstein_duplicates.py # 3. Merge duplicates
python3 scripts/data_quality/restore_entity_bios.py     # 4. Restore biographies
python3 scripts/analysis/final_entity_cleanup_complete.py # 5. Final cleanup
```

---

### Stage 4: Entity Enrichment (Optional)

#### Entity Research & Enrichment
- **Script**: `research/enrich_entity_data.py`
- **Input**: `ENTITIES_INDEX.json`
- **Output**: `ENTITIES_INDEX.json` (enriched with Wikipedia data)
- **Purpose**: Add biographical information from Wikipedia
- **Features**:
  - Wikipedia API integration
  - Caches results to avoid re-fetching
  - Adds descriptions, occupations, birth/death dates
- **Status**: ✅ Production (optional enrichment)
- **Last Updated**: 2025-11-17

#### WHOIS Entity Research (Experimental)
- **Script**: `research/basic_entity_whois.py`
- **Input**: `ENTITIES_INDEX.json`
- **Output**: `ENTITIES_INDEX.json` (enriched with WHOIS data)
- **Purpose**: Research entities using Perplexity AI WHOIS-style queries
- **Features**:
  - Perplexity API integration
  - Structured biographical research
  - Rate-limited and cached
- **Status**: 🧪 Experimental (not production-ready)
- **Last Updated**: 2025-11-19

---

### Stage 5: Network & Relationship Building

#### Entity Network Graph
- **Script**: `analysis/rebuild_flight_network.py`
- **Input**: `ENTITIES_INDEX.json`
- **Output**: `data/metadata/entity_network.json` (387 entities, 2,221 edges)
- **Purpose**: Build entity relationship graph from flight log co-occurrences
- **Features**:
  - Co-passenger analysis
  - Relationship strength scoring
  - Network statistics
- **Dependencies**: Must run after Stage 3 (all entity processing)
- **Status**: ✅ Production
- **Last Updated**: 2025-11-17

#### Entity Relationship Enrichment
- **Script**: `analysis/enrich_entity_relationships.py`
- **Input**:
  - `ENTITIES_INDEX.json`
  - `entity_network.json`
  - Web search results
- **Output**: `entity_network.json` (enriched with web-sourced relationships)
- **Purpose**: Add relationship context from web sources
- **Features**:
  - Web search integration
  - Relationship type classification
  - Confidence scoring
- **Status**: ✅ Production (optional enrichment)
- **Last Updated**: 2025-11-17

---

### Stage 6: Document Indexing

⚠️ **ISSUE**: Currently 3 competing document indexes exist. Needs consolidation in Phase 2.

#### Primary Document Index (RECOMMENDED)
- **Script**: `data_quality/rebuild_all_documents_index.py`
- **Input**:
  - `data/sources/house_oversight_nov2025/ocr_text/*.txt`
  - `data/md/` (markdown files)
- **Output**: `data/metadata/all_documents_index.json` (18.9 MB)
- **Purpose**: Master index of all documents across all sources
- **Features**:
  - Document metadata (source, date, type, pages)
  - Full-text excerpts
  - File path tracking
- **Status**: ✅ Production (recommended)
- **Last Updated**: 2025-11-18

#### Unified Semantic Index
- **Script**: `indexing/build_unified_index.py`
- **Input**: Same as above
- **Output**: `data/metadata/unified_document_index.json` (38 MB)
- **Purpose**: Extended index with semantic analysis
- **Features**:
  - Document embeddings
  - Topic clustering
  - Similarity scores
- **Status**: ✅ Production (alternative)
- **Last Updated**: 2025-11-17
- **Note**: Larger than primary index, use for semantic search features

#### Categorized Document Index
- **Script**: `data_quality/categorize_documents.py`
- **Input**: `all_documents_index.json`
- **Output**: `data/metadata/master_document_index_categorized.json` (23 MB)
- **Purpose**: Documents with category tags (legal, financial, correspondence, etc.)
- **Features**:
  - ML-based categorization
  - Confidence scores
  - Multi-label support
- **Status**: ✅ Production (derived from primary)
- **Last Updated**: 2025-11-18

---

### Stage 7: RAG & Semantic Search

#### Vector Store Building
- **Script**: `rag/build_vector_store.py`
- **Input**: `data/sources/house_oversight_nov2025/ocr_text/*.txt`
- **Output**: `data/vector_store/chroma/` (ChromaDB, ~2 GB)
- **Purpose**: Build semantic search vector database
- **Features**:
  - ChromaDB with sentence-transformers (all-MiniLM-L6-v2)
  - Batch processing (1000 docs/batch)
  - Resume capability
  - Entity detection during indexing
- **Dependencies**: ChromaDB, sentence-transformers
- **Status**: ✅ Production, resume-capable
- **Last Updated**: 2025-11-17

#### Entity-Document Linking
- **Script**: `rag/link_entities_to_docs.py`
- **Input**:
  - `data/sources/house_oversight_nov2025/ocr_text/*.txt`
  - `ENTITIES_INDEX.json`
- **Output**: `data/metadata/entity_document_index.json`
- **Purpose**: Map entities to document mentions
- **Features**:
  - Entity mention counting
  - Name variation matching
  - Document relevance scoring per entity
- **Dependencies**: Must run after Stage 3 (entity processing)
- **Status**: ✅ Production
- **Last Updated**: 2025-11-17

#### Hybrid RAG Query System
- **Script**: `rag/kg_rag_integration.py`
- **Input**:
  - ChromaDB vector store
  - `entity_network.json`
  - `knowledge_graph.json`
- **Output**: Query results (hybrid semantic + graph)
- **Purpose**: Combine semantic search with knowledge graph traversal
- **Features**:
  - Vector similarity search
  - Graph-based relationship expansion
  - Hybrid ranking
- **Status**: ✅ Production
- **Last Updated**: 2025-11-17

---

### Stage 8: Derived Artifacts

#### Timeline Building
- **Script**: `analysis/timeline_builder.py`
- **Input**: Markdown files in `data/md/`
- **Output**: `data/metadata/timeline.json` (66 KB)
- **Purpose**: Extract chronological events from documents
- **Features**:
  - Date extraction and normalization
  - Event categorization
  - Timeline visualization data
- **Status**: ✅ Production
- **Last Updated**: 2025-11-17

#### Knowledge Graph
- **Script**: `analysis/build_knowledge_graph.py`
- **Input**:
  - `ENTITIES_INDEX.json`
  - `entity_network.json`
  - `timeline.json`
- **Output**: `data/metadata/knowledge_graph.json` (569 KB)
- **Purpose**: Build unified knowledge graph combining entities, relationships, and events
- **Features**:
  - RDF-style triple store
  - Entity-event linking
  - Relationship typing
- **Status**: ✅ Production
- **Last Updated**: 2025-11-17

#### Chatbot Knowledge Index
- **Script**: `metadata/build_chatbot_knowledge_index.py`
- **Input**:
  - `ENTITIES_INDEX.json`
  - `entity_network.json`
  - `knowledge_graph.json`
  - Vector store
- **Output**: `data/metadata/chatbot_knowledge_index.json`
- **Purpose**: Optimized index for chatbot queries
- **Features**:
  - Pre-computed common queries
  - Entity context windows
  - Relationship summaries
- **Status**: ✅ Production
- **Last Updated**: 2025-11-17

---

## Supporting Utilities

### Core Libraries
- **`core/database.py`** - Database connection and query utilities
- **`core/deduplicator.py`** - Generic deduplication logic
- **`core/hasher.py`** - Content hashing for change detection
- **`core/ocr_quality.py`** - OCR quality scoring

### Utilities
- **`utils/entity_normalization.py`** - Entity name normalization helpers
- **`utils/entity_filtering.py`** - Entity filtering logic
- **`utils/build_entity_mappings.py`** - Entity alias mapping

---

## Data Quality & Validation

### Validation Scripts
- **`validation/validate_entity_names.py`** - Entity name format validation
- **`validation/run_pydantic_audit.py`** - Schema validation with Pydantic
- **`verification/verify_all_fixes.py`** - Comprehensive data quality checks
- **`verification/verify_task_completion.py`** - Pipeline stage completion checks

### Data Quality Scripts
- **`data_quality/verify_normalization.py`** - Verify entity normalization worked
- **`data_quality/generate_entity_mappings.py`** - Generate entity alias mappings
- **`data_quality/merge_categorizations.py`** - Merge document categorizations
- **`data_quality/validate_categorization.py`** - Validate document categories

---

## Deprecated & One-Off Scripts

See `DEPRECATED/README.md` for 16 scripts moved out of production pipeline.

**DO NOT CREATE**:
- Additional `fix_*` scripts (use canonical entity processing)
- Additional entity disambiguation scripts (use canonical pipeline)
- One-off cleanup scripts (add to validation suite instead)

---

## Creating New Canonical Scripts

If you need to add a new processing stage:

1. **Check if existing stage can be extended** (prefer extension over new script)
2. **Document purpose and dependencies** in this file FIRST
3. **Use atomic write patterns** (`scripts/lib/atomic_io.py`)
4. **Add metadata tracking** (`scripts/lib/metadata_tracker.py`)
5. **Add resume capability** for long-running operations
6. **Include validation** in script output
7. **Update dependency graph** in this document
8. **Add to integration tests**

---

## Pipeline Orchestration (Coming in Phase 2)

Currently, scripts must be run manually in correct order. Phase 2 will add:

- `orchestration/pipeline.py` - Automatic dependency-based execution
- `orchestration/dag.py` - Dependency graph definition
- `cli/run.py` - Single command to run full pipeline

---

## Questions & Issues

- **Data corruption?** Check if atomic writes being used (`lib/atomic_io.py`)
- **Duplicate entities?** Run Stage 3 scripts in order
- **Missing canonical script?** Check `DEPRECATED/` first, may need to create new one
- **Script fails mid-run?** Check if resume capability exists, check `.pipeline_metadata.json`

**See also**:
- `DATA_PIPELINE_AUDIT_REPORT.md` - Full pipeline analysis
- `scripts/MIGRATION_GUIDE.md` - Migration instructions
- `scripts/DEPRECATED/README.md` - Deprecated scripts

---

**Last Verified**: 2025-11-19
**Maintainer**: @masa
