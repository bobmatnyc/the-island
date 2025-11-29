# RAG System Quick Start Guide
**Epstein Document Archive - Get Started in 5 Minutes**

---

## 🚀 Quick Setup (15 minutes)

### Step 1: Install Dependencies (2 minutes)

```bash
cd /Users/masa/Projects/Epstein
bash scripts/rag/install_chromadb.sh
```

**What it installs:**
- ChromaDB (vector database)
- sentence-transformers (embedding model)
- PyTorch (CPU version)
- FastAPI dependencies

---

### Step 2: Build Vector Store (5-6 hours)

```bash
python3 scripts/rag/build_vector_store.py
```

**This will:**
- Embed all 33,562 documents
- Generate 384-dimensional vectors
- Store in ChromaDB collection
- Extract entity mentions and dates
- Process ~5-10 docs/second

**Progress monitoring:**
```bash
# In another terminal, watch progress
python3 -c "
import json
from pathlib import Path
progress_file = Path('data/vector_store/embedding_progress.json')
if progress_file.exists():
    data = json.load(open(progress_file))
    print(f\"Processed: {data['total_processed']} documents\")
    print(f\"Last updated: {data['last_updated']}\")
"
```

**Resume after interruption:**
```bash
# Automatically resumes from last checkpoint
python3 scripts/rag/build_vector_store.py --resume
```

---

### Step 3: Link Entities (30 minutes)

```bash
python3 scripts/rag/link_entities_to_docs.py
```

**Creates:**
- Entity → document index
- Mention counts per document
- Output: `data/metadata/entity_document_index.json`

---

### Step 4: Test the System (1 minute)

```bash
python3 scripts/rag/test_rag_system.py
```

**Expected output:**
```
✅ PASS: Vector Store Existence
✅ PASS: Embedding Generation
✅ PASS: Semantic Search - Basic
✅ PASS: Entity-Document Index
...

Success rate: 100%
```

---

## 🔍 Quick Examples

### 1. Semantic Search

```bash
python3 scripts/rag/query_rag.py --query "Who visited Little St. James?"
```

### 2. Entity Search

```bash
python3 scripts/rag/query_rag.py --entity "Clinton"
```

### 3. Multi-Entity Search

```bash
python3 scripts/rag/query_rag.py --entities "Clinton" "Epstein" "Maxwell"
```

### 4. Find Connections

```bash
python3 scripts/rag/query_rag.py --connections "Ghislaine"
```

---

## 🌐 API Usage

### Start Server

```bash
cd server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Test Endpoints

```bash
# System stats
curl "http://localhost:8000/api/rag/stats"

# Semantic search
curl "http://localhost:8000/api/rag/search?query=Epstein&limit=5"

# Entity search
curl "http://localhost:8000/api/rag/entity/Clinton?limit=10"

# Multi-entity
curl "http://localhost:8000/api/rag/multi-entity?entities=Clinton,Epstein"
```

---

## 🧠 Advanced Queries

### Hybrid Search (Semantic + Graph)

```bash
python3 scripts/rag/kg_rag_integration.py \
  --query "financial transactions" \
  --entity "Wexner" \
  --limit 10
```

### Find Path Between Entities

```bash
python3 scripts/rag/kg_rag_integration.py \
  --path "Clinton" "Prince Andrew" \
  --max-hops 3
```

### Temporal Query

```bash
python3 scripts/rag/kg_rag_integration.py \
  --temporal "Wexner" \
  --date-range "1995" "2000"
```

---

## 📊 Performance Expectations

| Operation | Time |
|-----------|------|
| Vector store build | 5-6 hours |
| Entity linking | 30 minutes |
| Semantic search | <500ms |
| Entity search | <50ms |
| API cold start | ~5 seconds |

---

## 🐛 Troubleshooting

### Issue: Vector store not found

```bash
# Build it first
python3 scripts/rag/build_vector_store.py
```

### Issue: Out of memory

```bash
# Reduce batch size
python3 scripts/rag/build_vector_store.py --batch-size 50
```

### Issue: Slow queries

```bash
# Check system resources
# Reduce limit parameter
python3 scripts/rag/query_rag.py --query "test" --limit 5
```

---

## 📁 File Locations

| Component | Path |
|-----------|------|
| Vector store | `data/vector_store/chroma/` |
| Entity index | `data/metadata/entity_document_index.json` |
| Scripts | `scripts/rag/` |
| API routes | `server/routes/rag.py` |
| Documentation | `docs/RAG_SYSTEM.md` |

---

## 🎯 Next Steps

1. ✅ Build vector store (5-6 hours)
2. ✅ Link entities (30 minutes)
3. ✅ Test system (1 minute)
4. 🚀 Start querying!

**Full Documentation:** `docs/RAG_SYSTEM.md`

---

## 💡 Tips

- **Entity Names**: Use exact names from `data/md/entities/ENTITIES_INDEX.json`
- **Query Speed**: Entity search is 10x faster than semantic search
- **Multi-Entity**: Great for finding document connections
- **Graph Queries**: Use `kg_rag_integration.py` for relationship-aware search
- **API Integration**: Perfect for building web interfaces

---

**Last Updated**: 2025-11-17
**Total Documents**: 33,562
**Total Entities**: 1,641+
