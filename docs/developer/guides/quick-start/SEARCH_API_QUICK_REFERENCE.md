# Search API Quick Reference

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- `query` (required): Search query with optional boolean operators
- `limit` (optional, default: 20): Maximum results (1-100)
- `offset` (optional, default: 0): Pagination offset
- `fields` (optional, default: "all"): Comma-separated fields (entities, documents, news)
- `fuzzy` (optional, default: true): Enable fuzzy matching

---

**Last Updated:** 2025-11-20

---

## API Endpoints

### 1. Unified Search
```bash
GET /api/search/unified
```

**Parameters:**
- `query` (required): Search query with optional boolean operators
- `limit` (optional, default: 20): Maximum results (1-100)
- `offset` (optional, default: 0): Pagination offset
- `fields` (optional, default: "all"): Comma-separated fields (entities, documents, news)
- `fuzzy` (optional, default: true): Enable fuzzy matching
- `min_similarity` (optional, default: 0.5): Minimum similarity score (0.0-1.0)
- `doc_type` (optional): Filter by document type
- `source` (optional): Filter by source
- `date_start` (optional): Start date (YYYY-MM-DD)
- `date_end` (optional): End date (YYYY-MM-DD)

**Example:**
```bash
curl "http://localhost:8000/api/search/unified?query=Epstein&limit=10"
```

**Response:**
```json
{
  "query": "Epstein",
  "total_results": 5,
  "search_time_ms": 67.2,
  "results": [...],
  "facets": {...},
  "suggestions": [...]
}
```

---

### 2. Autocomplete Suggestions
```bash
GET /api/search/suggestions
```

**Parameters:**
- `query` (required, min 2 chars): Partial search query
- `limit` (optional, default: 10): Maximum suggestions (1-50)

**Example:**
```bash
curl "http://localhost:8000/api/search/suggestions?query=Eps&limit=5"
```

**Response:**
```json
[
  {
    "text": "Jeffrey Epstein",
    "type": "entity",
    "score": 0.95,
    "metadata": {"categories": ["person"]}
  },
  {
    "text": "Epstein Island",
    "type": "entity_alias",
    "score": 0.90,
    "metadata": {"canonical_name": "Little Saint James"}
  }
]
```

---

### 3. Search Analytics
```bash
GET /api/search/analytics
```

**Example:**
```bash
curl "http://localhost:8000/api/search/analytics"
```

**Response:**
```json
{
  "total_searches": 127,
  "top_queries": [
    {"query": "Epstein", "count": 45},
    {"query": "Maxwell", "count": 23}
  ],
  "recent_searches": [...],
  "last_updated": "2025-11-20T12:56:13.123Z"
}
```

---

### 4. Clear Search History
```bash
DELETE /api/search/analytics/history
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/search/analytics/history"
```

**Response:**
```json
{
  "status": "success",
  "message": "Search history cleared"
}
```

---

## Boolean Operators

### AND (Both terms must be present)
```bash
curl "http://localhost:8000/api/search/unified?query=Epstein%20AND%20Maxwell"
```

### OR (Either term must be present)
```bash
curl "http://localhost:8000/api/search/unified?query=Epstein%20OR%20Clinton"
```

### NOT (First present, second absent)
```bash
curl "http://localhost:8000/api/search/unified?query=Epstein%20NOT%20Maxwell"
```

### Complex (Nested logic)
```bash
curl "http://localhost:8000/api/search/unified?query=(Epstein%20OR%20Clinton)%20AND%20NOT%20Maxwell"
```

---

## Fuzzy Matching

**Automatically corrects typos:**

| Typo | Corrected To |
|------|--------------|
| Ghisline | Ghislaine |
| Maxwel | Maxwell |
| Jeffry | Jeffrey |
| Epstien | Epstein |

**Example:**
```bash
curl "http://localhost:8000/api/search/unified?query=Ghisline&fuzzy=true"
# Returns results for "Ghislaine"
```

**Disable fuzzy matching:**
```bash
curl "http://localhost:8000/api/search/unified?query=exact%20match&fuzzy=false"
```

---

## Filtering

### By Date Range
```bash
curl "http://localhost:8000/api/search/unified?query=flight&date_start=2019-01-01&date_end=2019-12-31"
```

### By Document Type
```bash
curl "http://localhost:8000/api/search/unified?query=deposition&doc_type=legal_document"
```

### By Source
```bash
curl "http://localhost:8000/api/search/unified?query=email&source=fbi_vault"
```

### By Fields (Search Scope)
```bash
# Search only entities
curl "http://localhost:8000/api/search/unified?query=Maxwell&fields=entities"

# Search entities and documents
curl "http://localhost:8000/api/search/unified?query=Maxwell&fields=entities,documents"

# Search all fields (default)
curl "http://localhost:8000/api/search/unified?query=Maxwell&fields=all"
```

---

## Pagination

```bash
# First page (results 0-19)
curl "http://localhost:8000/api/search/unified?query=Epstein&limit=20&offset=0"

# Second page (results 20-39)
curl "http://localhost:8000/api/search/unified?query=Epstein&limit=20&offset=20"

# Third page (results 40-59)
curl "http://localhost:8000/api/search/unified?query=Epstein&limit=20&offset=40"
```

---

## Performance Tips

### 1. Warm Up the API (First Request)
```bash
# Send warmup query before production use
curl "http://localhost:8000/api/search/unified?query=warmup&limit=1" > /dev/null
```

**Why:** First query loads embedding model (~1.4s), subsequent queries are fast (~67ms)

### 2. Use Field Filtering for Faster Searches
```bash
# Slower (searches all fields)
curl "http://localhost:8000/api/search/unified?query=Maxwell"

# Faster (searches only entities)
curl "http://localhost:8000/api/search/unified?query=Maxwell&fields=entities"
```

**Speed Comparison:**
- Entity-only: ~12ms
- All fields: ~67ms

### 3. Adjust Similarity Threshold
```bash
# More results (lower quality)
curl "http://localhost:8000/api/search/unified?query=Epstein&min_similarity=0.3"

# Fewer results (higher quality)
curl "http://localhost:8000/api/search/unified?query=Epstein&min_similarity=0.8"
```

**Default:** 0.5 (balanced quality/quantity)

---

## Response Format

### Search Result Object
```json
{
  "id": "entity:Jeffrey Epstein",
  "type": "entity",
  "title": "Jeffrey Epstein",
  "description": "American financier and convicted sex offender...",
  "similarity": 0.95,
  "metadata": {
    "aliases": ["JE", "J. Epstein"],
    "categories": ["person", "financier"],
    "sources": ["fbi_vault", "court_documents"]
  },
  "highlights": ["Jeffrey Epstein", "JE"]
}
```

### Result Types
- `entity`: Person, organization, location
- `document`: PDF, email, court filing
- `news`: News article

---

## Error Handling

### 200 OK - Success
```json
{
  "query": "test",
  "total_results": 5,
  "results": [...]
}
```

### 422 Unprocessable Entity - Validation Error
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "query"],
      "msg": "Field required"
    }
  ]
}
```

### 500 Internal Server Error - Server Error
```json
{
  "detail": "Vector store not initialized. Run build_vector_store.py first."
}
```

---

## Common Use Cases

### 1. Simple Entity Search
```bash
curl "http://localhost:8000/api/search/unified?query=Ghislaine%20Maxwell"
```

### 2. Find Documents by Date Range
```bash
curl "http://localhost:8000/api/search/unified?query=deposition&date_start=2015-01-01&date_end=2020-12-31"
```

### 3. Autocomplete for Search Bar
```bash
# User types "Eps"
curl "http://localhost:8000/api/search/suggestions?query=Eps&limit=5"
```

### 4. Get Popular Searches
```bash
curl "http://localhost:8000/api/search/analytics" | jq '.top_queries'
```

### 5. Search with Typo Tolerance
```bash
curl "http://localhost:8000/api/search/unified?query=Jeffry%20Epstien&fuzzy=true"
# Automatically finds "Jeffrey Epstein"
```

### 6. Find Related Entities
```bash
curl "http://localhost:8000/api/search/unified?query=Epstein%20AND%20Maxwell"
```

---

## Testing Commands

### Quick Smoke Test
```bash
# Test unified search
curl -s "http://localhost:8000/api/search/unified?query=test&limit=1" | jq '.'

# Test autocomplete
curl -s "http://localhost:8000/api/search/suggestions?query=Eps" | jq '.'

# Test analytics
curl -s "http://localhost:8000/api/search/analytics" | jq '.total_searches'
```

### Run Comprehensive Tests
```bash
python3 test_search_api_comprehensive.py
```

### Performance Benchmark
```bash
# Warmup first
curl -s "http://localhost:8000/api/search/unified?query=warmup&limit=1" > /dev/null

# Then benchmark
time curl -s "http://localhost:8000/api/search/unified?query=Epstein&limit=10" > /dev/null
```

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Median Latency** | 67ms | After warmup |
| **p95 Latency** | 279ms | After warmup |
| **Autocomplete** | 0.8ms | Sub-millisecond! |
| **Cold Start** | 1,400ms | First query only |
| **Fuzzy Accuracy** | 100% | Tested with 4 typos |

---

## Troubleshooting

### Q: First query is slow (>1s)
**A:** This is expected (cold start). Send a warmup query on server startup.

### Q: Getting 422 validation errors
**A:** Check that `query` parameter is provided and is a string.

### Q: Getting 500 "Vector store not initialized"
**A:** Run `python scripts/build_vector_store.py` first.

### Q: Fuzzy matching not working
**A:** Ensure `fuzzy=true` parameter is set (it's enabled by default).

### Q: No results for valid query
**A:** Try lowering `min_similarity` to 0.3 or check if data exists.

---

## API Changelog

### 2025-11-20
- ✅ Fixed async/await bugs in search.py
- ✅ All endpoints now return 200 OK
- ✅ Verified performance metrics
- ✅ 100% test pass rate

---

**Need Help?**
- API Documentation: `/docs` (Swagger UI)
- Test Results: `SEARCH_API_QA_REPORT.md`
- Performance Analysis: `SEARCH_API_PERFORMANCE_SUMMARY.md`
