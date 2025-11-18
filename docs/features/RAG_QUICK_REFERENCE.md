# RAG System Quick Reference

**Epstein Document Archive - Vector Search System**

---

## ✅ System Status

### Current State

```
📊 Documents Embedded:    33,329 / 33,561 (99.3%)
🔄 Entity Linking:        In Progress (~30-45 min)
✅ Semantic Search:       Operational
✅ Vector Store:          Ready
📍 Collection:            epstein_documents
💾 Storage:               440 MB
```

---

## 🚀 Quick Start Commands

### 1. Semantic Search

Search for documents by meaning:

```bash
cd /Users/masa/Projects/epstein
.venv/bin/python3 scripts/rag/query_rag.py --query "Jeffrey Epstein flight logs" --limit 10
```

### 2. Entity Search (After Index Completion)

Find all documents mentioning a specific person:

```bash
.venv/bin/python3 scripts/rag/query_rag.py --entity "Clinton" --limit 20
```

### 3. Multi-Entity Search

Find documents mentioning multiple people:

```bash
.venv/bin/python3 scripts/rag/query_rag.py --entities "Clinton" "Epstein" "Maxwell"
```

### 4. Similar Documents

Find documents similar to a specific document:

```bash
.venv/bin/python3 scripts/rag/query_rag.py --similar DOJ-OGR-00013382 --limit 10
```

### 5. Find Entity Connections

Discover documents linking entities:

```bash
.venv/bin/python3 scripts/rag/query_rag.py --connections "Ghislaine Maxwell" --limit 15
```

---

## 🌐 API Usage

### Start the Server

```bash
cd /Users/masa/Projects/epstein
.venv/bin/python3 server/app.py
```

Then access at: `http://localhost:8000`

### API Endpoints

**Semantic Search**:
```bash
curl "http://localhost:8000/api/rag/search?query=Epstein&limit=5"
```

**Entity Documents** (after index completion):
```bash
curl "http://localhost:8000/api/rag/entity/Clinton?limit=10"
```

**Similar Documents**:
```bash
curl "http://localhost:8000/api/rag/similar/DOJ-OGR-00013382?limit=5"
```

**System Stats**:
```bash
curl "http://localhost:8000/api/rag/stats"
```

---

## 🧪 Testing

### Run Full Test Suite

```bash
.venv/bin/python3 scripts/rag/test_rag_system.py
```

### Quick Test (Core Features Only)

```bash
.venv/bin/python3 scripts/rag/test_rag_system.py --quick
```

### Check System Status

```bash
.venv/bin/python3 << 'EOF'
import chromadb
client = chromadb.PersistentClient(path='data/vector_store/chroma')
collection = client.get_collection('epstein_documents')
print(f"Documents in ChromaDB: {collection.count():,}")
EOF
```

---

## 📁 Important File Locations

### Vector Store

```
data/vector_store/chroma/              # ChromaDB database
data/vector_store/embedding_progress.json  # Processing progress
```

### Entity Data

```
data/md/entities/ENTITIES_INDEX.json       # 1,639 entities
data/metadata/entity_document_index.json   # Entity→Document index (🔄 creating)
data/metadata/entity_network.json          # Entity relationships
```

### Scripts

```
scripts/rag/query_rag.py              # Command-line query tool
scripts/rag/build_vector_store.py     # Rebuild embeddings
scripts/rag/link_entities_to_docs.py  # Rebuild entity index
scripts/rag/test_rag_system.py        # Test suite
```

### Documentation

```
docs/RAG_SYSTEM.md                    # Complete documentation
scripts/rag/README.md                 # Scripts overview
scripts/rag/QUICKSTART.md             # Quick start guide
```

---

## 🔧 Maintenance Commands

### Rebuild Vector Store (Complete)

```bash
# Full rebuild (warning: takes 5-6 hours!)
.venv/bin/python3 scripts/rag/build_vector_store.py --no-resume
```

### Rebuild Entity Index

```bash
# Rebuild entity-document links
.venv/bin/python3 scripts/rag/link_entities_to_docs.py
```

### Check Progress

```bash
# Monitor embedding progress
bash scripts/rag/check_rag_progress.sh
```

### View Progress File

```bash
# See processing stats
cat data/vector_store/embedding_progress.json | python3 -m json.tool | head -20
```

---

## 💡 Usage Examples

### Example 1: Find Documents About Specific Topic

```bash
.venv/bin/python3 scripts/rag/query_rag.py \
  --query "financial transactions and wire transfers" \
  --limit 20 \
  --show-text
```

### Example 2: Find All Documents Mentioning Someone

```bash
# After entity index is complete
.venv/bin/python3 scripts/rag/query_rag.py \
  --entity "Prince Andrew" \
  --limit 50
```

### Example 3: Find Documents Mentioning Multiple People

```bash
.venv/bin/python3 scripts/rag/query_rag.py \
  --entities "Clinton" "Epstein" "Wexner" \
  --limit 30
```

### Example 4: Discover Related Documents

```bash
# Find documents similar to DOJ-OGR-00013382
.venv/bin/python3 scripts/rag/query_rag.py \
  --similar DOJ-OGR-00013382 \
  --limit 15 \
  --show-text
```

---

## 📊 System Statistics

### Current Metrics

```python
# Get detailed stats
.venv/bin/python3 << 'EOF'
import chromadb
import json
from pathlib import Path

client = chromadb.PersistentClient(path='data/vector_store/chroma')
collection = client.get_collection('epstein_documents')

# Load entity index
with open('data/md/entities/ENTITIES_INDEX.json') as f:
    entities = json.load(f)

print(f"Documents Embedded: {collection.count():,}")
print(f"Total Entities: {len(entities.get('entities', []))} ")
print(f"Collection: {collection.name}")
print(f"Embedding Model: all-MiniLM-L6-v2 (384 dimensions)")
EOF
```

---

## 🛠️ Troubleshooting

### Problem: "Collection not found"

```bash
# Solution: Rebuild vector store
.venv/bin/python3 scripts/rag/build_vector_store.py
```

### Problem: "Entity index not found"

```bash
# Solution: Create entity index
.venv/bin/python3 scripts/rag/link_entities_to_docs.py
```

### Problem: Slow query performance

```bash
# Solution: Use entity search instead of semantic search
.venv/bin/python3 scripts/rag/query_rag.py --entity "Clinton"  # Fast
# Instead of:
.venv/bin/python3 scripts/rag/query_rag.py --query "Clinton"  # Slower
```

### Problem: Out of memory

```bash
# Solution: Reduce batch size
.venv/bin/python3 scripts/rag/build_vector_store.py --batch-size 50
```

---

## 📖 Advanced Usage

### Hybrid Search (Semantic + Graph)

```bash
.venv/bin/python3 scripts/rag/kg_rag_integration.py \
  --query "financial transactions" \
  --entity "Wexner" \
  --limit 20
```

### Path Finding Between Entities

```bash
.venv/bin/python3 scripts/rag/kg_rag_integration.py \
  --path "Clinton" "Prince Andrew" \
  --max-hops 3
```

### Temporal Queries

```bash
.venv/bin/python3 scripts/rag/kg_rag_integration.py \
  --temporal "Wexner" \
  --date-range "1995" "2000"
```

---

## 🎯 Best Practices

### 1. Use Entity Search When Possible

Entity search is **10x faster** than semantic search:

```bash
# ✅ Fast (uses index)
.venv/bin/python3 scripts/rag/query_rag.py --entity "Clinton"

# ⚠️ Slower (uses embeddings)
.venv/bin/python3 scripts/rag/query_rag.py --query "Clinton"
```

### 2. Limit Results for Performance

Always specify `--limit` to avoid processing too many results:

```bash
# ✅ Good
.venv/bin/python3 scripts/rag/query_rag.py --query "Epstein" --limit 20

# ⚠️ Can be slow
.venv/bin/python3 scripts/rag/query_rag.py --query "Epstein"  # Returns many results
```

### 3. Use Multi-Entity Search for Precision

Combine multiple entities to narrow results:

```bash
.venv/bin/python3 scripts/rag/query_rag.py \
  --entities "Clinton" "Epstein" "Maxwell" \
  --limit 10
```

---

## 🔗 Quick Links

- **Full Documentation**: [docs/RAG_SYSTEM.md](docs/RAG_SYSTEM.md)
- **API Documentation**: `http://localhost:8000/docs` (when server running)
- **Quick Start**: [scripts/rag/QUICKSTART.md](scripts/rag/QUICKSTART.md)
- **Scripts README**: [scripts/rag/README.md](scripts/rag/README.md)

---

## 📋 Checklist for New Users

- [ ] Verify vector store exists: `ls -lh data/vector_store/chroma/chroma.sqlite3`
- [ ] Check document count: `python3 -c "import chromadb; print(chromadb.PersistentClient(path='data/vector_store/chroma').get_collection('epstein_documents').count())"`
- [ ] Wait for entity index completion: `ls -lh data/metadata/entity_document_index.json`
- [ ] Run quick tests: `.venv/bin/python3 scripts/rag/test_rag_system.py --quick`
- [ ] Try semantic search: `.venv/bin/python3 scripts/rag/query_rag.py --query "Epstein" --limit 5`
- [ ] Try entity search: `.venv/bin/python3 scripts/rag/query_rag.py --entity "Clinton" --limit 5`
- [ ] Start API server: `.venv/bin/python3 server/app.py`
- [ ] Test API: `curl "http://localhost:8000/api/rag/stats"`

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
**Status**: ✅ Operational (Entity index in progress)
