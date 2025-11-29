# News Article Ingestion - Quick Start Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Embedding Pipeline**: 5.94 articles/second processing speed
- **Vector Search**: <100ms query latency, semantic search operational
- **Data Quality**: No duplicates, complete metadata, all validations passing
- **Article Count**: 4 high-quality tier-1 articles (avg 2,477 words, 16.5 entities)
- **Dead URLs**: 89% of seed CSV URLs return 404/401 errors (URLs from 2018-2021 are outdated)

---

**Status**: ⚠️ Partial Success (4/100 articles) - Infrastructure Ready, Data Source Needed

---

## Current State

### ✅ What's Working
- **Embedding Pipeline**: 5.94 articles/second processing speed
- **Vector Search**: <100ms query latency, semantic search operational
- **Data Quality**: No duplicates, complete metadata, all validations passing
- **Article Count**: 4 high-quality tier-1 articles (avg 2,477 words, 16.5 entities)

### ❌ Blocking Issue
- **Dead URLs**: 89% of seed CSV URLs return 404/401 errors (URLs from 2018-2021 are outdated)
- **Gap**: Need 96+ additional articles to reach 100+ target

---

## Quick Commands

### Check Current Article Count
```bash
source .venv/bin/activate
python3 -c "import json; data = json.load(open('data/metadata/news_articles_index.json')); print(f'Articles: {data[\"metadata\"][\"total_articles\"]}')"
```

### Ingest Articles from Seed CSV
```bash
source .venv/bin/activate
python3 scripts/ingestion/ingest_seed_articles.py --all --limit 100 --data-dir data --entity-index data/md/entities/ENTITIES_INDEX.json
```

### Generate Embeddings
```bash
source .venv/bin/activate
python3 scripts/rag/embed_news_articles.py
```

### Test Vector Search
```bash
source .venv/bin/activate
python3 -c "
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path='data/vector_store/chroma')
collection = client.get_collection('epstein_documents')
model = SentenceTransformer('all-MiniLM-L6-v2')

query = 'Ghislaine Maxwell arrest'
embedding = model.encode([query])[0]
results = collection.query(
    query_embeddings=[embedding.tolist()],
    n_results=3,
    where={'doc_type': 'news_article'}
)
print(f'Found {len(results[\"documents\"][0])} articles')
for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
    print(f'{i}. {meta[\"title\"]} ({meta[\"publication\"]})')
"
```

---

## Current Database Stats

| Metric | Value |
|--------|-------|
| **Total Articles** | 4 |
| **Embeddings** | 4 / 4 (100%) |
| **Vector Store Docs** | 33,333 (4 news + 33,329 court docs) |
| **Avg Word Count** | 2,477 words |
| **Date Range** | 2018-11-28 to 2020-07-02 |
| **Sources** | Miami Herald (2), NPR (1), Reuters (1) |
| **Query Performance** | <100ms |

---

## Why Only 4 Articles?

### Ingestion Attempt Results
- **Attempted**: 9 articles from seed CSV
- **Succeeded**: 1 article (11.1%)
- **Failed**: 8 articles (88.9%)
  - HTTP 404: 6 articles (dead links)
  - HTTP 401: 2 articles (access denied)

### Seed CSV Issues
- URLs from 2018-2021 are now dead (news site redesigns, paywall changes)
- Archive.org fallback failed (CDX API format mismatch)
- Only 20 total URLs in seed CSV (insufficient for 100+ target)

---

## Path to 100+ Articles

### Option 1: Fix Archive.org Integration (Quick - 2 hours)
```bash
# Fix link_verifier.py to handle 5-property CDX snapshots
# Re-run ingestion to recover 8 dead URLs
# Expected gain: +8 articles → 12 total
```

### Option 2: Expand Seed CSV with Working URLs (Medium - 4-6 hours)
```bash
# Manually curate 100+ working URLs from:
# - BBC News Epstein archive
# - The Guardian topic pages
# - ProPublica investigations
# Add to data/sources/news_articles_seed.csv
# Expected gain: +80-100 articles → 92-112 total
```

### Option 3: Import Existing Dataset (Fast - 1-2 hours)
```bash
# Search Hugging Face for news datasets
# Filter by entity mentions: "Jeffrey Epstein"
# Import to news_articles_index.json
# Expected gain: +100-500 articles → 104-504 total
```

### Option 4: Build Discovery Pipeline (Long-term - 1-2 days)
```bash
# Automate article discovery via:
# - Google News API searches
# - RSS feed monitoring
# - Common Crawl news dataset
# Expected: Continuous growth
```

---

## Next Actions

### Immediate (Do Now)
1. **Review comprehensive report**: `NEWS_ARTICLE_INGESTION_REPORT.md`
2. **Choose expansion strategy**: Archive fix vs. CSV expansion vs. Dataset import
3. **Allocate time**: 2-8 hours depending on chosen path

### Short-term (This Week)
4. Fix Archive.org CDX API issue
5. Manually verify 20 BBC/Guardian URLs
6. Re-run ingestion pipeline

### Long-term (Next Sprint)
7. Build automated discovery pipeline
8. Add RSS feed monitoring
9. Implement continuous ingestion

---

## Key Files

| File | Description |
|------|-------------|
| `data/metadata/news_articles_index.json` | Article metadata storage |
| `data/sources/news_articles_seed.csv` | Seed URLs (⚠️ mostly dead) |
| `data/vector_store/chroma/` | Vector embeddings (ChromaDB) |
| `scripts/ingestion/ingest_seed_articles.py` | Ingestion script |
| `scripts/rag/embed_news_articles.py` | Embedding script |
| `NEWS_ARTICLE_INGESTION_REPORT.md` | Full ingestion report |

---

## Evidence of Success

### ✅ Ingestion Pipeline Working
```
Miami Herald: 1/3 articles successfully scraped
- Julie K. Brown investigation: 6,289 words, 58 entities
- Credibility score: 0.98 (Pulitzer finalist)
```

### ✅ Embeddings Operational
```
Processing Speed: 5.94 articles/second
Model: all-MiniLM-L6-v2 (384 dimensions)
Storage: ChromaDB persistent
```

### ✅ Vector Search Tested
```
Query: "Ghislaine Maxwell arrest and charges"
Top Result: Reuters Maxwell article (similarity: 0.175)
Latency: <100ms
```

### ✅ Data Quality Validated
```
Unique IDs: 4/4 ✓
Unique URLs: 4/4 ✓
Avg entities: 16.5 per article ✓
Credibility: 0.92-0.98 (tier-1 only) ✓
```

---

## Troubleshooting

### "Connection timeout" errors
- **Cause**: News sites rate limiting or network issues
- **Solution**: Already handled with retry logic (3 retries @ 10s)
- **Workaround**: Add `--skip-verification` flag to bypass link checks

### "Archive lookup failed" errors
- **Cause**: CDX API format mismatch (5 vs 7 properties)
- **Solution**: Fix `link_verifier.py` to handle variable formats
- **Status**: ⚠️ **Not yet fixed** (included in expansion plan)

### "Quality filter rejected" errors
- **Cause**: Article extraction failed (404/401/paywall)
- **Solution**: Use working URLs from BBC/Guardian/ProPublica
- **Status**: ⚠️ **Need new seed URLs**

---

## Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Articles | 100+ | 4 | ❌ 4% |
| Embeddings | 100% | 100% | ✅ |
| Vector Search | Working | Working | ✅ |
| Data Quality | No issues | No issues | ✅ |
| Query Speed | <100ms | <100ms | ✅ |

**Overall Status**: ⚠️ Infrastructure ready, data source expansion needed

---

**Last Updated**: 2025-11-20 12:15:00
**Next Review**: After implementing expansion strategy
