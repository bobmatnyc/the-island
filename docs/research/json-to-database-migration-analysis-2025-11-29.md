# JSON to Database Migration Analysis
**Research Date**: 2025-11-29
**Ticket Context**: 1M-364 (Entity Classification Work)
**Researcher**: Claude Code Research Agent

## Executive Summary

**Recommendation**: **Stick with optimized JSON files for 12-18 months**, then migrate to **SQLite** when data exceeds 100K documents or query latency becomes problematic.

**Key Findings**:
- Current JSON approach is **well-architected** with service layer abstraction
- Data size (38K docs, 1.6K entities) is manageable in memory (~30-50MB RAM)
- Zero-setup deployment is **critical advantage** for archive/research projects
- Migration complexity is **moderate** (2-3 weeks) but provides **minimal immediate benefit**
- SQLite offers best balance: simplicity + SQL power without deployment overhead

**Critical Path**: Focus on query optimization and caching **before** considering database migration.

---

## 1. Current Architecture Analysis

### 1.1 Data Loading Patterns

**File**: `server/app.py` (4,924 lines)
**Pattern**: **Startup-time bulk load** with in-memory caching

```python
@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    load_data()  # Loads all JSON files into global dictionaries
```

**Data Loaded at Startup**:
| File | Size | Records | Memory Est. | Load Time Est. |
|------|------|---------|-------------|----------------|
| `master_document_index.json` | 16.3 MB | 38,177 docs | ~25-30 MB | ~0.5-1s |
| `entity_biographies.json` | 2.9 MB | 1,637 entities | ~5-8 MB | ~0.1-0.2s |
| `entity_statistics.json` | 3.1 MB | 1,637 entities | ~6-10 MB | ~0.1-0.2s |
| `entity_network.json` | Unknown | 255 nodes | ~2-4 MB | ~0.05s |
| `document_classifications.json` | 398 KB | Unknown | ~1-2 MB | ~0.05s |
| `semantic_index.json` | Unknown | Unknown | ~2-5 MB | ~0.1s |
| **TOTAL** | **~23 MB** | **~40K records** | **~40-60 MB** | **~1-2 seconds** |

**Additional Storage**:
- ChromaDB vector store: **619 MB** (for semantic search)
- Vector embeddings: Persistent on disk, lazy-loaded

### 1.2 Service Layer Architecture

**Abstraction Pattern**: Clean service layer separates data access from API routes

**Key Services**:
1. **`DocumentService`** (`server/services/document_service.py`, 260 lines)
   - In-memory filtering and search
   - No database dependencies
   - Loads `all_documents_index.json` into `self.documents` list

2. **`EntityService`** (`server/services/entity_service.py`, 1,129 lines)
   - Sophisticated entity management
   - **Reverse mappings** for O(1) lookups: `name_to_id`, `id_to_name`, `guid_to_id`
   - **Tiered classification**: LLM → NLP → Procedural fallback
   - Pydantic validation support (optional)

**Design Quality**: ✅ **Excellent** - Service layer makes database migration feasible without frontend changes

### 1.3 Current Query Patterns

**Evidence from Code Analysis**:

**Entity Queries** (from `entity_service.py`):
```python
# O(1) lookups via pre-built dictionaries
def get_entity_by_id(self, entity_id: str) -> Optional[dict]:
    return self.entity_stats.get(entity_id)  # O(1)

def get_entity_by_name(self, name: str) -> Optional[dict]:
    entity_id = self.name_to_id.get(name)  # O(1)
    return self.get_entity_by_id(entity_id)  # O(1)
```

**Document Queries** (from `document_service.py`):
```python
# O(n) filtering over full document list
def search_documents(self, q=None, entity=None, doc_type=None, ...):
    filtered_docs = self.documents.copy()  # O(n) copy

    # Sequential filters (each O(n))
    if q:
        filtered_docs = [d for d in filtered_docs if q_lower in d['filename'].lower()]
    if entity:
        filtered_docs = [d for d in filtered_docs if entity in d['entities_mentioned']]
    # ... more filters

    return paginate(filtered_docs, offset, limit)
```

**API Endpoint Evidence** (87 endpoints identified):
- `/api/entities` - List entities with filters
- `/api/entities/{entity_id}` - Get single entity (O(1))
- `/api/documents` - Search documents (O(n) filtering)
- `/api/documents/{doc_id}` - Get single document (O(n) lookup)
- `/api/entities/{entity_id}/connections` - Network traversal (O(E) edges)
- `/api/search` - Full-text search (uses ChromaDB for semantic, O(n) for text)

### 1.4 Frontend Data Access Patterns

**Evidence from `frontend/src/pages/Entities.tsx`**:
```typescript
const loadEntities = async () => {
  const offset = (currentPage - 1) * PAGE_SIZE;  // 100 per page
  const response = await api.getEntities({
    limit: PAGE_SIZE,
    offset,
    search: debouncedSearch || undefined,
    entity_type: selectedType !== 'all' ? selectedType : undefined,
    has_biography: showOnlyWithBio  // Server-side filter
  });

  // Client-side category filter (OR logic)
  if (selectedCategories.length > 0) {
    filteredEntities = response.entities.filter(entity =>
      selectedCategories.some(selectedCat =>
        entity.bio?.relationship_categories?.some(cat => cat.type === selectedCat)
      )
    );
  }
}
```

**Pattern Analysis**:
- **Pagination**: Backend returns 100 entities per page (reasonable)
- **Hybrid filtering**: Server-side type/bio filters + client-side category filter
- **Debounced search**: 500ms delay prevents excessive requests
- **State management**: React hooks with local state (no Redux/global store)

**API Call Frequency**: Moderate
- Entities page: 1 request per filter change
- Document detail: 1-2 requests (document + summary)
- Network viz: 1 large request for full graph

---

## 2. Performance Characteristics

### 2.1 Current Bottlenecks

**Identified Issues**:

1. **Document Search is O(n) linear scan**
   - 38,177 documents scanned on EVERY search query
   - Multiple filters applied sequentially (each O(n))
   - **Impact**: Search latency increases linearly with document count
   - **Mitigation**: Client-side pagination hides latency (100 docs/page)

2. **Entity Type Classification Can Block Requests**
   - LLM classification via OpenRouter API (disabled in production: `ENABLE_LLM_CLASSIFICATION=false`)
   - NLP classification via spaCy (CPU-intensive for large batches)
   - **Impact**: Entity list endpoint can be slow if type filter enabled
   - **Mitigation**: Procedural fallback (keyword matching) is fast

3. **Network Graph Traversal is Unoptimized**
   - Full graph loaded into memory (255 nodes, ~1K+ edges)
   - Multi-hop traversal not implemented (TODO in code)
   - **Impact**: Limited to 1-hop queries currently
   - **Mitigation**: Small graph size makes this non-critical

4. **No Index on Document ID Lookup**
   ```python
   def get_document_by_id(self, doc_id: str) -> Optional[dict]:
       # O(n) linear search through all documents!
       document = next((doc for doc in self.documents if doc.get("id") == doc_id), None)
   ```
   - **Impact**: Individual document lookups are slow
   - **Mitigation**: Frontend caches document data after initial load

5. **Memory Usage Grows with Data**
   - Current: ~40-60 MB resident set size (RSS) at startup
   - Projected: ~200-300 MB if data grows to 100K documents
   - **Impact**: Not critical on modern servers, but limits horizontal scaling

### 2.2 Actual Performance Metrics

**Server Memory Usage** (from `ps aux` snapshot):
```
masa  77645  0.0  0.0  435288336  23584   ??  Ss  2:17PM  0:17.25
  Python uvicorn server (epstein backend)
  RSS: 23,584 KB = ~23 MB resident memory
```

**Analysis**: Very light memory footprint despite loading all JSON data. Python's memory efficiency + small dataset size = excellent performance.

**Startup Time**: ~1-2 seconds (estimated from file sizes)
- Faster than spinning up PostgreSQL container
- No connection pooling overhead
- Instant availability

### 2.3 Data Growth Trajectory

**Current State**:
- Documents: 38,177 (master_document_index.json)
- Entities: 1,637 (entity_biographies.json + entity_statistics.json)
- Network nodes: 255
- Vector embeddings: ~38K in ChromaDB (619 MB)

**Growth Analysis** (from git history):
- `entity_biographies.json` grew from 36 KB (Nov 17) to 2.9 MB (Nov 28)
  - **10 days = 80x growth** (due to batch biography generation)
- `master_document_index.json` relatively stable (archive dataset)
- **Key Insight**: Data is mostly static (historical archive), not live-ingestion system

**Projection**:
- **Pessimistic**: 100K documents, 5K entities by 2026 (if more archives ingested)
- **Realistic**: 50K documents, 2.5K entities by mid-2026 (slow organic growth)
- **Optimistic**: <50K documents (archive is mostly complete)

**Database Threshold**: >50K documents OR >5K entities with complex relationships

---

## 3. Database Options Analysis

### 3.1 PostgreSQL

**Pros**:
- ✅ Full SQL power: joins, indexes, foreign keys, transactions
- ✅ JSONB support: Hybrid relational + document model
- ✅ Full-text search: `tsvector`, `tsquery` (better than linear scan)
- ✅ Scalability: Handles millions of rows easily
- ✅ Robust ecosystem: pgAdmin, PostGIS for geospatial, replication

**Cons**:
- ❌ **Deployment overhead**: Requires PostgreSQL server setup
- ❌ **Not available locally**: `psql not found` (would need Homebrew/Docker)
- ❌ **Connection pooling complexity**: Additional code for connection management
- ❌ **Backup complexity**: `pg_dump` + separate backup strategy
- ❌ **Overkill for 38K records**: PostgreSQL shines at 1M+ rows

**Use Cases**:
- Multi-tenant SaaS with 100K+ users
- Real-time analytics with complex aggregations
- Geospatial queries (PostGIS)
- Strong consistency requirements

**Verdict**: ❌ **Not Recommended** - Too heavy for this use case

---

### 3.2 SQLite

**Pros**:
- ✅ **Zero deployment overhead**: Single file database (`epstein.db`)
- ✅ **Built-in Python support**: `import sqlite3` (no dependencies)
- ✅ **Full SQL support**: CREATE INDEX, JOIN, transactions
- ✅ **Fast read performance**: Optimized for read-heavy workloads
- ✅ **Simple backups**: `cp epstein.db epstein.db.backup`
- ✅ **Portable**: Copy database file = instant migration
- ✅ **Full-text search**: FTS5 extension (better than grep)

**Cons**:
- ⚠️ **Single-writer limitation**: Only 1 write transaction at a time
  - **Mitigation**: This is a read-heavy archive, not a high-write app
- ⚠️ **No network access**: Local file only
  - **Mitigation**: Deploy with app on same server (current architecture)
- ⚠️ **Limited concurrency**: ~100 concurrent readers OK, >1K readers problematic
  - **Mitigation**: Current traffic is low (research archive, not Twitter)

**Use Cases**:
- **PERFECT**: Read-heavy archives (Epstein docs)
- Mobile apps (one user at a time)
- Desktop applications
- Embedded systems
- Prototyping before PostgreSQL

**Migration Path**:
```python
# Phase 1: SQLite for structured data
conn = sqlite3.connect('data/epstein.db')

# Phase 2: Hybrid approach
# - SQLite: entities, documents, relationships
# - ChromaDB: vector embeddings (unchanged)
# - JSON: configuration files only

# Phase 3: Full migration
# - All metadata in SQLite
# - JSON files as export/backup only
```

**Verdict**: ✅ **RECOMMENDED** - Best fit for this project

---

### 3.3 MongoDB

**Pros**:
- ✅ Flexible schema: JSON-native storage
- ✅ Horizontal scaling: Sharding for massive datasets
- ✅ Rich query language: $regex, $text, aggregation pipelines
- ✅ Change streams: Real-time notifications

**Cons**:
- ❌ **Deployment overhead**: Requires MongoDB server (Docker or cloud)
- ❌ **Not installed locally**: Would need setup
- ❌ **Memory hungry**: MongoDB loves RAM (default: 50% of system RAM)
- ❌ **Schema validation complexity**: Requires careful design
- ❌ **Overkill for structured data**: Current data is highly structured (entities have consistent schema)

**Use Cases**:
- User-generated content with unpredictable schema
- Real-time analytics pipelines
- IoT sensor data (high write volume)
- Social media applications

**Verdict**: ❌ **Not Recommended** - Wrong tool for this job

---

### 3.4 Keep JSON (Status Quo + Optimizations)

**Pros**:
- ✅ **Zero migration cost**: No code changes required
- ✅ **Zero deployment overhead**: No database server to manage
- ✅ **Version control friendly**: `git diff` shows changes in JSON
- ✅ **Human-readable**: Developers can inspect data easily
- ✅ **Fast prototyping**: Direct file editing for testing

**Optimizations Available**:
1. **Add entity ID index** (Quick win):
   ```python
   # Build index at startup
   self.doc_id_index = {doc['id']: doc for doc in self.documents}

   # O(1) lookup instead of O(n)
   def get_document_by_id(self, doc_id: str) -> Optional[dict]:
       return self.doc_id_index.get(doc_id)
   ```

2. **Implement search indexes** (Medium complexity):
   ```python
   # Inverted index for full-text search
   self.entity_to_docs = defaultdict(list)  # entity -> [doc_ids]
   self.type_to_docs = defaultdict(list)    # doc_type -> [doc_ids]
   ```

3. **Lazy loading for large files** (Advanced):
   ```python
   # Load document index only (not full content)
   # Fetch document content on-demand from .md files
   ```

4. **Pre-compute aggregations** (Quick win):
   ```python
   # At startup, calculate:
   # - Total entities per type
   # - Total documents per source
   # - Connection count distributions
   ```

**Cons**:
- ⚠️ **O(n) queries remain**: Linear scans for complex filters
- ⚠️ **Memory scales linearly**: 100K docs = ~100-150 MB RAM
- ⚠️ **No transactions**: Concurrent writes could corrupt data
- ⚠️ **Limited query expressiveness**: Can't do JOINs or complex aggregations

**Verdict**: ✅ **RECOMMENDED for 12-18 months** - Optimize first, migrate later

---

## 4. Tradeoffs Matrix

| Criteria | JSON Files (Optimized) | SQLite | PostgreSQL | MongoDB |
|----------|------------------------|--------|------------|---------|
| **Read Performance** | 🟡 Good (O(1) with indexes) | 🟢 Excellent (indexed queries) | 🟢 Excellent (indexed queries) | 🟢 Excellent (indexed queries) |
| **Write Performance** | 🟢 Excellent (1-2ms file write) | 🟡 Good (single writer lock) | 🟢 Excellent (MVCC) | 🟢 Excellent (MVCC) |
| **Query Flexibility** | 🔴 Poor (manual filtering) | 🟢 Excellent (full SQL) | 🟢 Excellent (full SQL + JSONB) | 🟢 Excellent (rich query API) |
| **Deployment Complexity** | 🟢 **Trivial** (copy files) | 🟢 **Very Low** (single .db file) | 🔴 **High** (server setup) | 🔴 **High** (server setup) |
| **Development Speed** | 🟢 Fast (direct file editing) | 🟡 Medium (need schema design) | 🟡 Medium (need schema + migrations) | 🟡 Medium (schema validation) |
| **Scalability** | 🔴 Poor (<100K records) | 🟡 Medium (<10M records) | 🟢 Excellent (>1B records) | 🟢 Excellent (>1B records) |
| **Transaction Support** | 🔴 None (file locks only) | 🟢 Full ACID | 🟢 Full ACID + savepoints | 🟢 ACID (w/ WiredTiger) |
| **Backup/Recovery** | 🟢 **Trivial** (`git commit`) | 🟢 **Very Easy** (`cp .db`) | 🟡 Medium (`pg_dump`) | 🟡 Medium (mongodump) |
| **Full-Text Search** | 🔴 Poor (O(n) grep) | 🟢 Good (FTS5 extension) | 🟢 Excellent (`tsvector`) | 🟢 Good (text indexes) |
| **Vector Search** | 🟢 ChromaDB (separate) | 🟢 ChromaDB (hybrid) | 🟢 pgvector extension | 🔴 Poor (no native support) |
| **Memory Usage (38K docs)** | 🟢 Low (~50 MB) | 🟢 Low (~20 MB + cache) | 🟡 Medium (~100 MB) | 🔴 High (~200 MB base) |
| **Joins/Relationships** | 🔴 Manual (Python loops) | 🟢 SQL JOIN | 🟢 SQL JOIN + CTEs | 🟡 $lookup (slower) |
| **Schema Evolution** | 🟢 Easy (just update JSON) | 🟡 Medium (ALTER TABLE) | 🟡 Medium (migrations) | 🟢 Easy (flexible schema) |
| **Observability** | 🔴 None (log file reads) | 🟡 Medium (EXPLAIN QUERY PLAN) | 🟢 Excellent (pg_stat_*) | 🟢 Good (profiler) |
| **Cost** | 🟢 $0 | 🟢 $0 | 🟡 $0 (self-hosted) - $$$$ (managed) | 🟡 $0 (self-hosted) - $$$$ (managed) |
| **Learning Curve** | 🟢 None (Python dicts) | 🟡 Low (SQL basics) | 🟡 Medium (SQL + admin) | 🟡 Medium (query API) |

**Legend**:
- 🟢 Excellent / Very Low / Trivial
- 🟡 Good / Medium / Some Effort
- 🔴 Poor / High / Significant Effort

---

## 5. Recommendations

### 5.1 Short-Term (0-3 months) - **Optimize JSON**

**Priority**: 🔴 **HIGH** - Quick wins with minimal risk

**Actions**:
1. **Add document ID index** (1 day):
   ```python
   # In DocumentService.__init__()
   self.doc_id_index = {doc['id']: doc for doc in self.documents}
   ```

2. **Pre-compute entity type classifications** (2 days):
   ```python
   # Generate entity_types.json at build time
   # Avoid LLM/NLP calls at runtime for known entities
   ```

3. **Implement search result caching** (2 days):
   ```python
   # Cache popular search queries for 5 minutes
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def search_documents_cached(query_hash):
       return self.search_documents(...)
   ```

4. **Add server-side pagination for network graph** (1 day):
   ```python
   # Return only visible nodes within zoom level
   # Reduce initial payload from 255 nodes to ~50
   ```

**Expected Impact**:
- Document lookup: **10x faster** (O(n) → O(1))
- Search queries: **2-3x faster** (caching popular queries)
- Network viz load time: **5x faster** (smaller initial payload)
- Memory usage: **Unchanged** (~50 MB)

**Risk**: 🟢 **Very Low** - No schema changes, backward compatible

---

### 5.2 Medium-Term (3-12 months) - **Hybrid JSON + SQLite**

**Priority**: 🟡 **MEDIUM** - Evaluate when data exceeds 50K documents

**Trigger Conditions** (ANY of these):
- Document count exceeds **50,000**
- Entity count exceeds **5,000**
- Search query latency exceeds **500ms** (p95)
- Memory usage exceeds **200 MB** at startup
- User feedback: "Search is slow"

**Migration Strategy**:

**Phase 1: Dual-write mode** (1 week):
```python
# Write to both JSON and SQLite
def save_entity(entity_data):
    # Legacy path
    with open('entity_biographies.json', 'w') as f:
        json.dump(entities, f)

    # New path
    conn.execute("INSERT INTO entities (...) VALUES (...)", entity_data)
    conn.commit()
```

**Phase 2: SQLite schema design** (1 week):
```sql
-- entities table
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT,
    entity_type TEXT CHECK(entity_type IN ('person', 'organization', 'location')),
    total_documents INTEGER DEFAULT 0,
    connection_count INTEGER DEFAULT 0,
    sources JSON,  -- JSON for flexibility
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entity_name ON entities(name);
CREATE INDEX idx_entity_type ON entities(entity_type);
CREATE INDEX idx_entity_docs ON entities(total_documents DESC);

-- documents table
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    path TEXT,
    source TEXT,
    doc_type TEXT,
    classification TEXT,
    entities_mentioned JSON,  -- Array of entity IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_doc_source ON documents(source);
CREATE INDEX idx_doc_type ON documents(doc_type);
CREATE INDEX idx_doc_classification ON documents(classification);

-- Full-text search (FTS5)
CREATE VIRTUAL TABLE documents_fts USING fts5(
    filename, path, content,
    content=documents,
    content_rowid=rowid
);

-- entity_documents junction (many-to-many)
CREATE TABLE entity_documents (
    entity_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    PRIMARY KEY (entity_id, document_id),
    FOREIGN KEY (entity_id) REFERENCES entities(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE INDEX idx_ed_entity ON entity_documents(entity_id);
CREATE INDEX idx_ed_document ON entity_documents(document_id);
```

**Phase 3: Read from SQLite** (1 week):
```python
class DocumentService:
    def __init__(self, data_path: Path, use_sqlite: bool = True):
        if use_sqlite:
            self.conn = sqlite3.connect('data/epstein.db')
            self.conn.row_factory = sqlite3.Row  # Dict-like rows
        else:
            self.load_json_data()  # Fallback

    def search_documents(self, q=None, entity=None, ...):
        if self.conn:
            return self._search_sqlite(q, entity, ...)
        else:
            return self._search_json(q, entity, ...)
```

**Phase 4: Deprecate JSON reads** (1 week):
```python
# Keep JSON as export format only
# Generate JSON from SQLite for compatibility
def export_to_json():
    entities = conn.execute("SELECT * FROM entities").fetchall()
    with open('entity_biographies.json', 'w') as f:
        json.dump({"entities": entities}, f, indent=2)
```

**Expected Benefits**:
- Search: **10-100x faster** (indexed queries vs. O(n) scans)
- Complex filters: **5-50x faster** (SQL WHERE vs. Python loops)
- Joins: **Possible** (entity → documents → sources)
- Aggregations: **Easy** (COUNT, GROUP BY, etc.)

**Cost Estimate**: **2-3 weeks** (1 developer)

**Risk**: 🟡 **Medium** - Requires careful testing, schema design

---

### 5.3 Long-Term (12+ months) - **PostgreSQL (if needed)**

**Priority**: 🔴 **LOW** - Only if project becomes multi-tenant SaaS

**Trigger Conditions** (ALL of these):
- Document count exceeds **500,000**
- Multiple users editing data concurrently
- Need for complex analytics (aggregations, windowing)
- Revenue justifies managed database cost
- Team has PostgreSQL expertise

**Migration Path**:
1. SQLite → PostgreSQL dump (use `pgloader` tool)
2. Update connection strings (minimal code changes)
3. Add connection pooling (pgbouncer or SQLAlchemy pool)
4. Monitor query performance (pg_stat_statements)
5. Optimize indexes based on query patterns

**Cost Estimate**: **1-2 weeks** (easier than JSON → PostgreSQL)

**Risk**: 🟢 **Low** (if migrating FROM SQLite, SQLite validates schema first)

---

## 6. Migration Effort Estimate

### 6.1 JSON Optimizations (Recommended Now)

| Task | Effort | Impact | Risk |
|------|--------|--------|------|
| Add document ID index | 1 day | High | Very Low |
| Pre-compute entity types | 2 days | Medium | Low |
| Implement query caching | 2 days | High | Low |
| Optimize network pagination | 1 day | Medium | Very Low |
| **TOTAL** | **6 days** | **High** | **Low** |

**Cost**: <$5K (1 developer, 1 week)

---

### 6.2 Hybrid JSON + SQLite Migration

| Task | Effort | Dependencies | Risk |
|------|--------|--------------|------|
| Schema design + review | 3 days | Database expert review | Medium |
| Implement dual-write mode | 5 days | Schema design | Medium |
| Migration script (JSON → SQLite) | 3 days | Dual-write tested | Low |
| Update service layer (read from SQLite) | 5 days | Migration script | Medium |
| Integration testing | 3 days | Service layer changes | High |
| Performance benchmarking | 2 days | Integration tests pass | Low |
| Rollback plan + documentation | 2 days | - | Low |
| **TOTAL** | **23 days (~4.5 weeks)** | - | **Medium** |

**Cost**: $20-30K (1 developer, 1 month)

**Critical Path Items**:
1. ✅ Service layer already abstracts data access (migration-friendly!)
2. ⚠️ Frontend expects certain JSON structures (need backward compat)
3. ⚠️ ChromaDB integration must remain (vector search unchanged)
4. ✅ No authentication/user data (simpler than typical migrations)

---

### 6.3 Full PostgreSQL Migration (Not Recommended)

| Task | Effort | Dependencies | Risk |
|------|--------|--------------|------|
| PostgreSQL setup (Docker/managed) | 2 days | Infrastructure approval | Low |
| Schema design (normalized) | 5 days | Database expert | Medium |
| Connection pooling setup | 2 days | PostgreSQL running | Low |
| Migration script (JSON → PG) | 5 days | Schema finalized | Medium |
| Update service layer | 7 days | Migration tested | High |
| Performance tuning (indexes, EXPLAIN) | 5 days | Service layer done | High |
| Integration + load testing | 5 days | Performance tuned | High |
| Backup/restore procedures | 3 days | - | Medium |
| Monitoring setup (pg_stat_*) | 2 days | - | Low |
| **TOTAL** | **36 days (~7 weeks)** | - | **High** |

**Cost**: $40-60K (1 developer, 2 months)

**Why Not Recommended**:
- 3x more effort than SQLite
- Deployment complexity (Docker + networking + secrets)
- Overkill for 38K documents
- SQLite provides 90% of benefits at 30% of cost

---

## 7. Risks and Mitigation Strategies

### 7.1 JSON Optimization Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Index memory overhead | Low | Low | Indexes add <10 MB, acceptable |
| Cache invalidation bugs | Medium | Medium | Use TTL-based caching (5 min), simple logic |
| Backward compatibility | Low | Low | Optimizations are additive, no breaking changes |

**Overall Risk**: 🟢 **Very Low**

---

### 7.2 SQLite Migration Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Data corruption during migration | Low | High | Test on copy, validate row counts, checksums |
| Performance regression | Medium | Medium | Benchmark before/after, rollback plan |
| Schema design mistakes | Medium | High | Expert review, start with minimal schema |
| Write contention (single writer) | Low | Low | Current app is read-heavy, acceptable |
| Disk space issues (index overhead) | Low | Low | SQLite DB ~2x JSON size, still <100 MB |

**Overall Risk**: 🟡 **Medium** (manageable with testing)

---

### 7.3 PostgreSQL Migration Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Deployment complexity | High | High | Use managed service (RDS, Heroku Postgres) |
| Connection pool exhaustion | Medium | High | Configure pgbouncer, monitor connections |
| Cost overruns (managed DB) | Medium | Medium | Budget $50-200/month for managed PostgreSQL |
| Over-engineering for scale | High | Low | Acknowledge PostgreSQL is overkill now |

**Overall Risk**: 🔴 **High** (not worth it for this use case)

---

## 8. Appendix: Code Examples

### 8.1 Current JSON Loading (app.py:349)

```python
def load_data():
    """Load all JSON data into memory with error handling"""
    global entity_stats, entity_bios, network_data, semantic_index, classifications, timeline_data
    global name_to_id, id_to_name, guid_to_id

    print("Loading data...")

    # Load entity statistics
    stats_path = DATA_DIR / "metadata/entity_statistics.json"
    if stats_path.exists():
        try:
            with open(stats_path) as f:
                data = json.load(f)
                entity_stats = data.get("statistics", {})
                print(f"  ✓ Loaded {len(entity_stats)} entities")
        except Exception as e:
            print(f"  ✗ Failed to load entity_statistics.json: {e}")
```

### 8.2 Current Document Search (document_service.py:64)

```python
def search_documents(
    self,
    q: Optional[str] = None,
    entity: Optional[str] = None,
    doc_type: Optional[str] = None,
    source: Optional[str] = None,
    classification: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search documents with multiple filters"""
    filtered_docs = self.documents.copy()  # O(n) copy

    # Full-text search in filename and path
    if q:
        q_lower = q.lower()
        filtered_docs = [
            doc for doc in filtered_docs
            if q_lower in doc.get("filename", "").lower()
            or q_lower in doc.get("path", "").lower()
        ]  # O(n) scan

    # Filter by entity mention
    if entity:
        entity_lower = entity.lower()
        filtered_docs = [
            doc for doc in filtered_docs
            if any(entity_lower in e.lower() for e in doc.get("entities_mentioned", []))
        ]  # O(n) scan

    # ... more filters (each O(n)) ...

    # Paginate
    total = len(filtered_docs)
    docs_page = filtered_docs[offset : offset + limit]

    return {"documents": docs_page, "total": total, ...}
```

**Problem**: Multiple sequential O(n) scans over 38K documents

---

### 8.3 Optimized Document Search (Proposed)

```python
class DocumentService:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.documents = []

        # NEW: Pre-built indexes
        self.doc_id_index = {}  # id -> doc (O(1) lookup)
        self.entity_to_docs = defaultdict(set)  # entity -> {doc_ids}
        self.type_to_docs = defaultdict(set)  # doc_type -> {doc_ids}
        self.source_to_docs = defaultdict(set)  # source -> {doc_ids}

        self.load_data()
        self._build_indexes()

    def _build_indexes(self):
        """Build inverted indexes for O(1) lookups"""
        for doc in self.documents:
            doc_id = doc['id']

            # ID index
            self.doc_id_index[doc_id] = doc

            # Entity index
            for entity in doc.get('entities_mentioned', []):
                self.entity_to_docs[entity.lower()].add(doc_id)

            # Type index
            if doc_type := doc.get('type'):
                self.type_to_docs[doc_type.lower()].add(doc_id)

            # Source index
            if source := doc.get('source'):
                self.source_to_docs[source.lower()].add(doc_id)

    def search_documents(self, q=None, entity=None, doc_type=None, ...):
        """Optimized search using indexes"""
        # Start with all doc IDs
        result_ids = set(self.doc_id_index.keys())

        # Intersect filters (O(1) for each lookup)
        if entity:
            result_ids &= self.entity_to_docs.get(entity.lower(), set())

        if doc_type:
            result_ids &= self.type_to_docs.get(doc_type.lower(), set())

        if source:
            result_ids &= self.source_to_docs.get(source.lower(), set())

        # Full-text search (still O(n), but only on result set)
        if q:
            q_lower = q.lower()
            result_ids = {
                doc_id for doc_id in result_ids
                if q_lower in self.doc_id_index[doc_id]['filename'].lower()
            }

        # Convert IDs to documents (O(k) where k = result count)
        filtered_docs = [self.doc_id_index[doc_id] for doc_id in result_ids]

        # Paginate
        total = len(filtered_docs)
        docs_page = filtered_docs[offset : offset + limit]

        return {"documents": docs_page, "total": total, ...}
```

**Improvement**: O(k) instead of O(n), where k = result set size (usually << n)

---

### 8.4 SQLite Schema Example

```sql
-- entities table (normalized)
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT,
    entity_type TEXT CHECK(entity_type IN ('person', 'organization', 'location')),
    total_documents INTEGER DEFAULT 0,
    connection_count INTEGER DEFAULT 0,
    is_billionaire BOOLEAN DEFAULT 0,
    sources JSON,  -- Keep flexibility for array data
    aliases JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entity_name ON entities(name);
CREATE INDEX idx_entity_type ON entities(entity_type);
CREATE INDEX idx_entity_docs_desc ON entities(total_documents DESC);

-- entity_biographies (1:1 with entities)
CREATE TABLE entity_biographies (
    entity_id TEXT PRIMARY KEY,
    biography TEXT,
    key_facts JSON,
    timeline JSON,
    relationships JSON,
    relationship_categories JSON,
    last_updated TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- documents table
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    path TEXT,
    source TEXT,
    doc_type TEXT,
    classification TEXT,
    content TEXT,  -- Full markdown content
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_doc_source ON documents(source);
CREATE INDEX idx_doc_type ON documents(doc_type);
CREATE INDEX idx_doc_classification ON documents(classification);

-- Full-text search (FTS5 virtual table)
CREATE VIRTUAL TABLE documents_fts USING fts5(
    filename, path, content,
    content=documents,
    content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, filename, path, content)
    VALUES (new.rowid, new.filename, new.path, new.content);
END;

CREATE TRIGGER documents_ad AFTER DELETE ON documents BEGIN
    DELETE FROM documents_fts WHERE rowid = old.rowid;
END;

-- entity_documents junction (many-to-many)
CREATE TABLE entity_documents (
    entity_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    PRIMARY KEY (entity_id, document_id),
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_ed_entity ON entity_documents(entity_id);
CREATE INDEX idx_ed_document ON entity_documents(document_id);

-- Example queries
-- Get all documents mentioning an entity (O(log n) with indexes)
SELECT d.* FROM documents d
JOIN entity_documents ed ON d.id = ed.document_id
WHERE ed.entity_id = 'jeffrey_epstein'
ORDER BY d.created_at DESC
LIMIT 20;

-- Full-text search with entity filter
SELECT d.* FROM documents_fts fts
JOIN documents d ON fts.rowid = d.rowid
JOIN entity_documents ed ON d.id = ed.document_id
WHERE fts MATCH 'flight logs' AND ed.entity_id = 'ghislaine_maxwell';

-- Entity statistics (aggregations)
SELECT entity_type, COUNT(*) as count, AVG(total_documents) as avg_docs
FROM entities
GROUP BY entity_type;
```

---

## 9. Conclusion

**Current State**: Well-architected JSON-based system with clean service layer abstraction.

**Recommendation**: **Optimize JSON in short-term, migrate to SQLite when data exceeds 50K documents.**

**Key Insight**: The service layer abstraction (`DocumentService`, `EntityService`) makes database migration **low-risk** and **non-breaking** for the frontend. This is excellent architectural design that provides flexibility.

**Action Plan**:
1. **Now (Week 1)**: Implement JSON optimizations (6 days, high impact)
2. **Q1 2026**: Re-evaluate if data growth triggers SQLite migration
3. **Q2-Q3 2026**: Execute SQLite migration if needed (3-4 weeks)
4. **Beyond 2026**: PostgreSQL only if project becomes multi-tenant SaaS

**Critical Success Factor**: Focus on **query optimization** and **caching** before considering database migration. The current architecture can scale to 100K documents with proper indexing.

---

**Research Completed**: 2025-11-29
**Next Steps**: Present findings to team, prioritize JSON optimizations for sprint planning.
