# Epstein Document Archive - System Summary

**Created**: 2025-11-17  
**Status**: ✅ Production Ready  
**Public URL**: https://c61d9c1c764c.ngrok.app  
**Credentials**: epstein / archive2025

---

## 🎯 Project Mission

A comprehensive, publicly accessible archive of Epstein-related documents with:
- **Transparency**: All sources from public records
- **Provenance**: Complete source tracking
- **Accessibility**: Advanced search and AI assistance
- **Integrity**: No editorialization, only facts

---

## 📊 Current Archive Status

- **1,702 Entities** (71 duplicates merged via fuzzy matching)
- **387 Network Nodes** with centrality metrics
- **2,221 Connections** from flight passenger lists
- **6 Documents** classified (67K+ being processed via OCR)
- **1 Knowledge Graph** with NetworkX
- **OCR Progress**: ~60% complete (background processing)

---

## 🏗️ Architecture

### Three-Tier System

```
┌────────────────────────────────────────────────────────┐
│              Web Interface (D3.js + Vanilla JS)         │
│  - Network visualization                                │
│  - Entity search                                        │
│  - Chat assistant                                       │
│  - Ingestion progress dashboard                         │
└───────────────────────┬────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────┐
│          FastAPI Server (Python)                        │
│  - REST APIs                                            │
│  - Multi-vector search                                  │
│  - Qwen 2.5 Coder integration                          │
│  - Source suggestion system                             │
└───────────────────────┬────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────┐
│            Data Layer                                   │
│  ┌──────────────┬──────────────┬──────────────┐       │
│  │  JSON Files  │ NetworkX KG  │  (ChromaDB)  │       │
│  │  Metadata    │  Graph DB    │   Vectors    │       │
│  └──────────────┴──────────────┴──────────────┘       │
└────────────────────────────────────────────────────────┘
```

### Current Components

1. **Entity Extraction** (`scripts/extraction/extract_entities.py`)
   - SpaCy NER for person/organization detection
   - 1,702 entities extracted from documents

2. **Entity Disambiguation** (`scripts/analysis/entity_disambiguator.py`)
   - Fuzzy matching (SequenceMatcher + Jaccard)
   - 71 duplicate groups merged

3. **Knowledge Graph** (`data/metadata/knowledge_graph.json`)
   - NetworkX graph with 387 nodes
   - Degree/betweenness centrality calculated
   - Flight co-occurrence relationships

4. **Network Analysis** (`scripts/analysis/entity_network_builder.py`)
   - Co-occurrence analysis from flight logs
   - 2,221 weighted edges

5. **FastAPI Server** (`server/app.py`)
   - 10+ REST endpoints
   - HTTP Basic Authentication
   - Multi-vector search integration
   - Qwen chatbot with context

6. **Web Interface** (`server/web/`)
   - D3.js force-directed graph
   - Real-time OCR progress
   - Floating chat widget
   - Source suggestion form

---

## 🤖 AI Features

### Qwen 2.5 Coder Chatbot
- **Local inference** via Ollama
- **Multi-vector search**: entities + documents + semantic index
- **Project context**: Full archive statistics and structure
- **Security**: No personal/system info disclosure
- **Warning**: 30-60s response time (local LLM)

### Search Capabilities
Currently implemented:
- ✅ Entity name search (exact + fuzzy)
- ✅ Document path search
- ✅ Semantic index lookup

Planned (Hybrid RAG + KG):
- ⏳ Vector semantic search
- ⏳ Graph traversal queries
- ⏳ Multi-hop reasoning
- ⏳ Temporal analysis

---

## 🔐 Security Features

1. **Authentication**: HTTP Basic Auth on all endpoints
2. **Credentials**: Static file (`server/.credentials`)
3. **URL Validation**: Blocks localhost, private IPs
4. **Source Review**: Manual approval required
5. **HTTPS**: Via ngrok tunnel
6. **Privacy**: No personal data in LLM context

---

## 📁 Project Structure

```
Epstein/
├── data/
│   ├── raw/                    # Original PDFs
│   ├── md/                     # Extracted markdown + entities
│   ├── metadata/               # Analysis results
│   │   ├── entity_network.json
│   │   ├── entity_statistics.json
│   │   ├── knowledge_graph.json (NEW)
│   │   └── semantic_index.json
│   └── source_suggestions.jsonl
├── scripts/
│   ├── extraction/             # OCR, entity extraction
│   ├── analysis/               # Network, stats, KG
│   └── search/                 # Entity search tools
├── server/
│   ├── app.py                  # FastAPI server
│   ├── web/                    # Frontend
│   │   ├── index.html
│   │   └── app.js
│   ├── .credentials            # Auth
│   └── start.sh                # Launch script
├── docs/
│   └── HYBRID_RAG_KG_ARCHITECTURE.md
├── run.sh                      # Script wrapper
├── requirements.txt
├── ACCESS_INFO.md
└── SYSTEM_SUMMARY.md (this file)
```

---

## 🚀 Quick Start

### Start Server
```bash
cd server
./start.sh 8081
```

### Start ngrok
```bash
ngrok http 8081
```

### Run Scripts
```bash
./run.sh disambiguate
./run.sh entity-stats
./run.sh network
```

---

## 🔮 Next Phase: Hybrid RAG + KG

### Planned Architecture
```
User Query
    ↓
Query Router (classify intent)
    ↓
┌───────────┬────────────┬───────────┐
│  Vector   │   Graph    │  Hybrid   │
│   RAG     │  Traversal │  Search   │
└─────┬─────┴──────┬─────┴─────┬─────┘
      │            │           │
  ChromaDB      NetworkX    Combined
  (Vectors)     (Graph)     Context
      │            │           │
      └────────────┴───────────┘
                   ↓
            Context Fusion
                   ↓
              Qwen LLM
                   ↓
              Response
```

### Implementation Steps
1. ✅ Build NetworkX knowledge graph
2. ⏳ Set up ChromaDB for vectors
3. ⏳ Generate embeddings (nomic-embed-text)
4. ⏳ Implement query router
5. ⏳ Build hybrid search pipeline
6. ⏳ Integrate with chatbot

### Benefits
- **Semantic search**: "Who flew with Epstein?" finds related entities
- **Graph queries**: "Shortest path between X and Y"
- **Multi-hop reasoning**: "Who connects Trump and Clinton?"
- **Document context**: Relevant text chunks, not just metadata
- **Scalability**: Handle 67K+ documents efficiently

---

## 📊 Key Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Entities | 1,702 | 5,000+ |
| Documents OCR'd | 20,100 | 67,144 |
| OCR Progress | 60% | 100% |
| Network Nodes | 387 | 500+ |
| Connections | 2,221 | 5,000+ |
| Sources | 4 | 10+ |
| Vector Embeddings | 0 | 67K+ |
| Graph Depth | 1-hop | 3-hop |

---

## 🤝 Community Contributions

Users can submit new sources via:
1. Chat widget → "Suggest a Source" button
2. Provide: URL, description, source name
3. Security validation (blocks private IPs)
4. Manual review before ingestion

Stored in: `data/source_suggestions.jsonl`

---

## 📝 Documentation

- **Architecture**: `docs/HYBRID_RAG_KG_ARCHITECTURE.md`
- **Access Info**: `ACCESS_INFO.md`
- **Web Interface**: `server/web/README.md`
- **API Docs**: http://localhost:8081/docs

---

## ⚡ Performance

- **Server**: FastAPI (async, high-performance)
- **Network Viz**: D3.js force simulation (optimized)
- **Search**: O(n) linear scan → O(log n) vector search (planned)
- **Graph**: NetworkX (in-memory, fast for <1K nodes)
- **LLM**: Local Ollama (30-60s, no API costs)

---

## 🎓 Technical Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla JS, D3.js |
| Backend | FastAPI, Python 3.11+ |
| Graph | NetworkX (→ Neo4j optional) |
| Vectors | (ChromaDB planned) |
| Embeddings | (nomic-embed-text planned) |
| LLM | Qwen 2.5 Coder 7B (Ollama) |
| OCR | Tesseract |
| NER | SpaCy |
| Server | Uvicorn |
| Tunnel | ngrok |

---

## ✅ Completed Milestones

- [x] Entity extraction from documents
- [x] Entity disambiguation (fuzzy matching)
- [x] Network graph generation
- [x] Knowledge graph with centrality metrics
- [x] FastAPI REST API
- [x] D3.js network visualization
- [x] Real-time ingestion dashboard
- [x] Qwen chatbot with multi-vector search
- [x] Source suggestion system
- [x] Password protection
- [x] ngrok public access
- [x] Home page with mission statement

## ⏳ In Progress

- [ ] OCR processing (60% complete)
- [ ] ChromaDB vector store
- [ ] Hybrid RAG + KG search
- [ ] Query router implementation

## 🔮 Future Enhancements

- [ ] Timeline visualization
- [ ] Document viewer with highlighting
- [ ] Advanced graph queries
- [ ] Export functionality
- [ ] Mobile-responsive design
- [ ] Multi-language support
- [ ] Neo4j migration (if scale requires)
- [ ] Real-time collaboration

---

**Last Updated**: 2025-11-17 02:55 EDT  
**Version**: 1.0.0  
**Maintainer**: masa
