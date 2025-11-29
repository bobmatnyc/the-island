# News Articles RAG Integration - Quick Start Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- News articles populated in `/data/metadata/news_articles_index.json`
- ChromaDB installed (`pip3 install chromadb sentence-transformers`)
- Existing vector store initialized (`data/vector_store/chroma/`)

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- News articles populated in `/data/metadata/news_articles_index.json`
- ChromaDB installed (`pip3 install chromadb sentence-transformers`)
- Existing vector store initialized (`data/vector_store/chroma/`)

### 1. Embed News Articles (2 minutes)
```bash
cd /Users/masa/Projects/epstein

# Test with 20 articles
python3 scripts/rag/embed_news_articles.py --limit 20

# Embed all articles (when ready)
python3 scripts/rag/embed_news_articles.py
```

### 2. Verify Embeddings (30 seconds)
```bash
# Check status
python3 scripts/rag/batch_embed_helper.py status

# Expected output:
# 📊 Embedding Status:
#    Total articles: 150
#    Embedded: 150
#    Not embedded: 0
#    Embedding rate: 100.0%
```

### 3. Test Search (1 minute)
```bash
# Start server (if not running)
cd server && python3 app.py

# Test news search
curl "http://localhost:5003/api/rag/news-search?query=Jeffrey+Epstein"

# Test similar articles (use an article ID from search results)
curl "http://localhost:5003/api/rag/similar-news/uuid-1234"
```

---

## 📚 New API Endpoints

### 1. Search News Articles
```bash
GET /api/rag/news-search?query=<query>&publication=<pub>&min_credibility=<score>
```

**Example**:
```bash
curl "http://localhost:5003/api/rag/news-search?query=Epstein+arrest&publication=New+York+Times&min_credibility=0.8"
```

### 2. Find Similar Articles
```bash
GET /api/rag/similar-news/{article_id}?limit=5
```

**Example**:
```bash
curl "http://localhost:5003/api/rag/similar-news/uuid-1234?limit=10"
```

### 3. Entity Search with News
```bash
GET /api/rag/entity/{entity_name}?include_news=true
```

**Example**:
```bash
curl "http://localhost:5003/api/rag/entity/Jeffrey+Epstein?include_news=true"
```

---

## 🛠️ Common Operations

### Check Embedding Status
```bash
python3 scripts/rag/batch_embed_helper.py status
```

### Reindex All Articles
```bash
python3 scripts/rag/embed_news_articles.py --force-reindex
```

### Remove All News Embeddings
```bash
python3 scripts/rag/batch_embed_helper.py remove
```

### Get System Stats
```bash
curl "http://localhost:5003/api/rag/stats"
```

---

## 🔍 Search Examples

### Basic Semantic Search
```bash
# All documents (court + news)
curl "http://localhost:5003/api/rag/search?query=Epstein+arrest"

# Only news articles
curl "http://localhost:5003/api/rag/search?query=Epstein+arrest&doc_type=news_article"
```

### Advanced News Search
```bash
# By publication
curl "http://localhost:5003/api/rag/news-search?query=Epstein&publication=Miami+Herald"

# High credibility only
curl "http://localhost:5003/api/rag/news-search?query=Epstein&min_credibility=0.9"

# With entity filter
curl "http://localhost:5003/api/rag/news-search?query=trafficking&entity=Virginia+Giuffre"

# Combined filters
curl "http://localhost:5003/api/rag/news-search?query=Epstein&publication=New+York+Times&min_credibility=0.8&entity=Jeffrey+Epstein&limit=20"
```

### Entity-Based Search
```bash
# All documents mentioning entity
curl "http://localhost:5003/api/rag/entity/Bill+Clinton?include_news=true"

# Court documents only (original behavior)
curl "http://localhost:5003/api/rag/entity/Bill+Clinton?include_news=false"
```

### Similar Articles
```bash
# Find similar news articles
curl "http://localhost:5003/api/rag/similar-news/uuid-1234?limit=5"

# Find similar documents (any type)
curl "http://localhost:5003/api/rag/similar/DOJ-OGR-00000001"
```

---

## 📊 Response Formats

### Search Response
```json
{
  "query": "Jeffrey Epstein arrest",
  "results": [
    {
      "id": "news:uuid-1234",
      "similarity": 0.92,
      "text_excerpt": "Jeffrey Epstein arrested on charges...",
      "metadata": {
        "doc_type": "news_article",
        "title": "Epstein Arrested on Federal Charges",
        "publication": "New York Times",
        "author": "John Doe",
        "published_date": "2019-07-06",
        "url": "https://example.com/article",
        "credibility_score": 0.95,
        "entity_mentions": "Jeffrey Epstein, FBI, New York",
        "tags": "arrest, federal, charges"
      }
    }
  ],
  "total_results": 15,
  "search_time_ms": 45.3
}
```

### Similar Articles Response
```json
{
  "source_article_id": "news:uuid-1234",
  "source_title": "Epstein Arrested on Federal Charges",
  "source_publication": "New York Times",
  "similar_articles": [
    {
      "id": "news:uuid-5678",
      "similarity": 0.89,
      "text_excerpt": "Federal prosecutors announced charges...",
      "metadata": {
        "title": "Federal Charges Announced",
        "publication": "Washington Post",
        "published_date": "2019-07-06"
      }
    }
  ],
  "total_results": 5
}
```

### Stats Response
```json
{
  "total_documents": 33762,
  "court_documents": 33562,
  "news_articles": 200,
  "total_entities": 450,
  "total_entity_mentions": 15234,
  "network_nodes": 450,
  "network_edges": 3421,
  "vector_store_path": "/path/to/chroma",
  "collection_name": "epstein_documents"
}
```

---

## 🐛 Troubleshooting

### Articles Not Showing in Search
```bash
# 1. Check if embedded
python3 scripts/rag/batch_embed_helper.py status

# 2. If not embedded, run:
python3 scripts/rag/embed_news_articles.py

# 3. Verify in ChromaDB
curl "http://localhost:5003/api/rag/stats"
```

### Embedding Script Fails
```bash
# Check dependencies
pip3 install chromadb sentence-transformers

# Check vector store exists
ls -la data/vector_store/chroma/

# Check news index exists
cat data/metadata/news_articles_index.json | jq '.metadata.total_articles'
```

### Search Returns No Results
```bash
# 1. Check if articles are embedded
python3 scripts/rag/batch_embed_helper.py status

# 2. Check if query is too specific
curl "http://localhost:5003/api/rag/news-search?query=Epstein"

# 3. Check ChromaDB collection
curl "http://localhost:5003/api/rag/stats"
```

### Slow Performance
```bash
# Reduce result limit
curl "http://localhost:5003/api/rag/news-search?query=Epstein&limit=5"

# Add more specific filters
curl "http://localhost:5003/api/rag/news-search?query=Epstein&publication=New+York+Times"
```

---

## 💡 Tips & Best Practices

### Embedding Strategy
- **Small batches** (1-10 articles): Use `NewsService.add_article_with_embedding()`
- **Large batches** (100+ articles): Use `scripts/rag/embed_news_articles.py`
- **Resume capability**: Script tracks progress, safe to restart

### Search Strategy
- **Broad search**: Use `/api/rag/search` (all documents)
- **News-specific**: Use `/api/rag/news-search` (article filters)
- **Entity-focused**: Use `/api/rag/entity/{name}` (relationship-based)
- **Related content**: Use `/api/rag/similar-news/{id}` (semantic similarity)

### Performance Optimization
- Use filters to reduce result set
- Limit results to what you need
- Cache frequently-used queries (future enhancement)

### Data Quality
- Higher `min_credibility` = more reliable sources
- Check `credibility_score` in metadata
- Use `source_tier` for reputation filtering

---

## 📖 Full Documentation

See `NEWS_RAG_INTEGRATION.md` for:
- Complete implementation details
- Architecture decisions
- All API endpoints documentation
- Maintenance procedures
- Future enhancements

---

## ✅ Quick Checklist

Before using in production:

- [ ] News articles populated in `news_articles_index.json`
- [ ] ChromaDB dependencies installed
- [ ] Existing vector store initialized
- [ ] News articles embedded successfully
- [ ] Embedding status shows 100%
- [ ] Search endpoints tested and working
- [ ] Similar articles feature tested
- [ ] Entity search includes news articles
- [ ] Stats endpoint shows correct counts
- [ ] No regressions in existing RAG features

---

**Last Updated**: 2025-11-20
**Status**: ✅ Ready for Testing
**Next Step**: Populate `news_articles_index.json` and run embedding script
