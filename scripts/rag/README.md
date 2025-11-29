# RAG System Scripts
**Epstein Document Archive - Retrieval-Augmented Generation**

This directory contains all scripts for building, querying, and managing the RAG system.

---

## 📁 Files Overview

| Script | Purpose | Time to Run |
|--------|---------|-------------|
| `install_chromadb.sh` | Install all dependencies | 2 minutes |
| `build_vector_store.py` | Embed 33,562 documents | 5-6 hours |
| `link_entities_to_docs.py` | Create entity-document index | 30 minutes |
| `query_rag.py` | Command-line query interface | Instant |
| `kg_rag_integration.py` | Hybrid search (semantic + graph) | Instant |
| `test_rag_system.py` | Comprehensive test suite | 1 minute |

---

## 🚀 Quick Start

```bash
# 1. Install
bash install_chromadb.sh

# 2. Build vector store (5-6 hours)
python3 build_vector_store.py

# 3. Link entities (30 minutes)
python3 link_entities_to_docs.py

# 4. Test
python3 test_rag_system.py

# 5. Query
python3 query_rag.py --query "your search query"
```

See **[QUICKSTART.md](QUICKSTART.md)** for detailed instructions.

---

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[/docs/RAG_SYSTEM.md](../../docs/RAG_SYSTEM.md)** - Complete documentation

---

## 🔍 Common Commands

### Semantic Search
```bash
python3 query_rag.py --query "Who visited Little St. James?"
```

### Entity Search
```bash
python3 query_rag.py --entity "Clinton" --limit 20
```

### Multi-Entity Search
```bash
python3 query_rag.py --entities "Clinton" "Epstein" "Maxwell"
```

### Find Connections
```bash
python3 query_rag.py --connections "Ghislaine"
```

### Similar Documents
```bash
python3 query_rag.py --similar DOJ-OGR-00012345
```

---

## 🧠 Advanced Queries

### Hybrid Search
```bash
python3 kg_rag_integration.py --query "financial transactions" --entity "Wexner"
```

### Path Finding
```bash
python3 kg_rag_integration.py --path "Clinton" "Prince Andrew" --max-hops 3
```

### Temporal Query
```bash
python3 kg_rag_integration.py --temporal "Wexner" --date-range "1995" "2000"
```

---

## 🌐 API Integration

The RAG system is integrated into the FastAPI server at `/api/rag`.

**Endpoints:**
- `GET /api/rag/search` - Semantic search
- `GET /api/rag/entity/{entity_name}` - Entity documents
- `GET /api/rag/similar/{doc_id}` - Similar documents
- `GET /api/rag/connections/{entity_name}` - Entity connections
- `GET /api/rag/multi-entity` - Multi-entity search
- `GET /api/rag/stats` - System statistics

**Example:**
```bash
curl "http://localhost:8000/api/rag/search?query=Epstein&limit=5"
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Total Documents | 33,562 |
| Embedding Dimensions | 384 |
| Query Latency | <500ms |
| Storage Size | ~2GB |
| Build Time | 5-6 hours |

---

## 🛠️ Script Details

### build_vector_store.py

**Purpose:** Embed all documents into ChromaDB

**Options:**
- `--batch-size N` - Process N documents at a time (default: 100)
- `--no-resume` - Start from scratch

**Output:**
- ChromaDB collection: `epstein_documents`
- Progress file: `data/vector_store/embedding_progress.json`

**Features:**
- Automatic resume on interruption
- Entity mention detection
- Date extraction
- Metadata tagging

---

### link_entities_to_docs.py

**Purpose:** Build entity → document index

**Options:**
- `--min-mentions N` - Minimum mentions to link (default: 1)

**Output:**
- `data/metadata/entity_document_index.json`

**Contains:**
- Entity → document mappings
- Mention counts
- Document rankings

---

### query_rag.py

**Purpose:** Command-line query interface

**Modes:**
- `--query TEXT` - Semantic search
- `--entity NAME` - Entity-based search
- `--entities NAME1 NAME2 ...` - Multi-entity search
- `--connections NAME` - Find entity connections
- `--similar DOC_ID` - Find similar documents

**Options:**
- `--limit N` - Maximum results (default: 10)
- `--show-text` - Display document excerpts

---

### kg_rag_integration.py

**Purpose:** Hybrid search combining semantic + graph

**Modes:**
- `--query TEXT` - Semantic search
- `--connect ENTITY1 ENTITY2 ...` - Connect entities
- `--path ENTITY1 ENTITY2` - Find path between entities
- `--temporal ENTITY` - Temporal query

**Options:**
- `--entity NAME` - Filter by entity
- `--date-range START END` - Date range filter
- `--max-hops N` - Path length limit
- `--weight-threshold N` - Connection weight threshold

---

### test_rag_system.py

**Purpose:** Comprehensive test suite

**Tests:**
1. Vector store existence
2. Embedding generation
3. Semantic search (basic)
4. Semantic search (relevance)
5. Entity-document index
6. Entity search
7. Entity network
8. Multi-entity search
9. Metadata extraction
10. Performance benchmarks

**Options:**
- `--quick` - Run core tests only
- `--benchmark` - Performance tests only

---

## 🐛 Troubleshooting

### Error: Collection not found

```bash
# Solution: Build vector store first
python3 build_vector_store.py
```

### Error: Entity not found

```bash
# Solution: Check entity name in index
cat ../../data/md/entities/ENTITIES_INDEX.json | grep -i "clinton"
```

### Slow performance

```bash
# Solution: Reduce batch size or limit
python3 build_vector_store.py --batch-size 50
python3 query_rag.py --query "test" --limit 5
```

### Out of memory

```bash
# Solution: Reduce batch size
python3 build_vector_store.py --batch-size 30
```

---

## 📈 Performance Tuning

### Build Performance

```bash
# Faster (higher memory usage)
python3 build_vector_store.py --batch-size 200

# Slower (lower memory usage)
python3 build_vector_store.py --batch-size 50
```

### Query Performance

```bash
# Faster: Use entity search instead of semantic
python3 query_rag.py --entity "Clinton"

# Slower: Semantic search
python3 query_rag.py --query "Clinton"
```

---

## 🔄 Updates & Maintenance

### Rebuild Vector Store

```bash
# Full rebuild (loses progress)
python3 build_vector_store.py --no-resume
```

### Update Entity Index

```bash
# Re-link entities (if entity data changed)
python3 link_entities_to_docs.py
```

### Verify Integrity

```bash
# Run full test suite
python3 test_rag_system.py
```

---

## 📞 Support

- **Documentation**: [docs/RAG_SYSTEM.md](../../docs/RAG_SYSTEM.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **API Docs**: `http://localhost:8000/docs` (when server running)

---

**Last Updated**: 2025-11-17
**Version**: 1.0.0
