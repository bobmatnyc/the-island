# News Article Semantic Search

**Quick Summary**: Semantic search functionality for news articles in the Epstein Document Archive. .

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Keyword-based relevance scoring** (backend fallback)
- **MCP vector search integration** (frontend - future enhancement)
- **Advanced filtering** by publication, date, entities, and credibility
- Keyword-based relevance scoring
- Article filtering and ranking

---

Semantic search functionality for news articles in the Epstein Document Archive.

## Overview

The news semantic search system provides intelligent article discovery using:
- **Keyword-based relevance scoring** (backend fallback)
- **MCP vector search integration** (frontend - future enhancement)
- **Advanced filtering** by publication, date, entities, and credibility

## Architecture

### Backend API (Python/FastAPI)

**Service Layer**: `server/services/news_search_service.py`
- Keyword-based relevance scoring
- Article filtering and ranking
- No external dependencies (ChromaDB, sentence-transformers)

**API Routes**: `server/routes/news.py`
- `/api/news/search/semantic` - Semantic search endpoint
- `/api/news/search/similar/{article_id}` - Find similar articles
- `/api/news/search/stats` - Search statistics

### Search Method

**Current**: Keyword-based fallback
- TF-IDF-like scoring across title, excerpt, tags, and entities
- Fast (<50ms per query)
- No additional dependencies required
- Suitable for small-medium article databases (<10,000 articles)

**Future**: MCP Vector Search Integration
- True semantic search using sentence transformers
- Cross-document similarity (news + court documents)
- Requires ChromaDB and mcp-vector-search MCP server
- See "Future Enhancement" section below

## API Endpoints

### 1. Semantic Search

```bash
GET /api/news/search/semantic
```

**Parameters:**
- `query` (required) - Natural language search query
- `limit` (optional, default: 10, max: 50) - Maximum results
- `similarity_threshold` (optional, default: 0.3) - Minimum score (0.0-1.0)
- `publication` (optional) - Filter by publication name
- `start_date` (optional) - Filter from date (YYYY-MM-DD)
- `end_date` (optional) - Filter to date (YYYY-MM-DD)
- `min_credibility` (optional) - Minimum credibility score (0.0-1.0)
- `entities` (optional) - Comma-separated entity names

**Example Request:**
```bash
curl "http://localhost:8081/api/news/search/semantic?query=financial+fraud&limit=10&min_credibility=0.9"
```

**Example Response:**
```json
{
  "query": "financial fraud",
  "results": [
    {
      "article": {
        "id": "...",
        "title": "...",
        "publication": "...",
        "published_date": "2019-07-06",
        ...
      },
      "similarity_score": 0.87,
      "matched_excerpt": "...",
      "search_method": "keyword"
    }
  ],
  "total": 5,
  "filters_applied": {
    "similarity_threshold": 0.3,
    "min_credibility": 0.9,
    ...
  }
}
```

### 2. Find Similar Articles

```bash
GET /api/news/search/similar/{article_id}
```

**Parameters:**
- `article_id` (required, path) - Reference article UUID
- `limit` (optional, default: 5, max: 20) - Maximum similar articles
- `similarity_threshold` (optional, default: 0.5) - Minimum similarity

**Example Request:**
```bash
curl "http://localhost:8081/api/news/search/similar/1de6b30b-3c6e-49e3-935c-f2e848db1b76?limit=5"
```

**Example Response:**
```json
{
  "reference_article_id": "1de6b30b-3c6e-49e3-935c-f2e848db1b76",
  "similar_articles": [
    {
      "article": {...},
      "similarity_score": 0.78,
      "matched_excerpt": "..."
    }
  ],
  "total": 3
}
```

### 3. Search Statistics

```bash
GET /api/news/search/stats
```

**Example Response:**
```json
{
  "total_articles": 70,
  "indexed_articles": 70,
  "unindexed_articles": 0,
  "search_method": "keyword_fallback",
  "note": "True semantic search requires mcp-vector-search MCP integration",
  "recommendation": "Use /api/news/articles with filters for production keyword search"
}
```

## Keyword Search Algorithm

**Scoring Formula:**
```python
score = (matched_terms + title_bonus) / (total_query_terms + query_length)
```

**Components:**
1. **Term Matching**: Count overlapping words between query and article
2. **Title Bonus**: Double weight for matches in article title
3. **Normalization**: Score ranges from 0.0 to 1.0
4. **Threshold Filtering**: Only return articles above similarity_threshold

**Searchable Fields:**
- Article title (2x weight)
- Content excerpt
- Tags
- Entity mentions

## Usage Examples

### Basic Semantic Search

```bash
# Find articles about arrests and charges
curl "http://localhost:8081/api/news/search/semantic?query=arrest+trafficking&limit=5"
```

### Filtered Search

```bash
# Find NPR articles about Ghislaine Maxwell from 2020
curl "http://localhost:8081/api/news/search/semantic?query=Maxwell&publication=NPR&start_date=2020-01-01&end_date=2020-12-31"
```

### High-Quality Source Search

```bash
# Only tier-1 sources with credibility >= 0.9
curl "http://localhost:8081/api/news/search/semantic?query=trial+testimony&min_credibility=0.9"
```

### Entity-Focused Search

```bash
# Articles mentioning specific entities
curl "http://localhost:8081/api/news/search/semantic?query=court+documents&entities=Jeffrey+Epstein,Ghislaine+Maxwell"
```

### Similar Article Discovery

```bash
# Find articles similar to a specific article
curl "http://localhost:8081/api/news/search/similar/1de6b30b-3c6e-49e3-935c-f2e848db1b76?limit=5"
```

## Frontend Integration

### TypeScript API Client

Add to `frontend/src/services/newsApi.ts`:

```typescript
export const searchNewsSemanticParams = {
  query: string;
  limit?: number;
  similarity_threshold?: number;
  publication?: string;
  start_date?: string;
  end_date?: string;
  min_credibility?: number;
  entities?: string[];
};

export const searchNewsSemantic = async (
  params: searchNewsSemanticParams
): Promise<SemanticSearchResponse> => {
  const queryParams = new URLSearchParams();
  queryParams.append('query', params.query);
  if (params.limit) queryParams.append('limit', params.limit.toString());
  if (params.similarity_threshold) {
    queryParams.append('similarity_threshold', params.similarity_threshold.toString());
  }
  // ... add other params

  const response = await fetch(
    `${API_BASE_URL}/news/search/semantic?${queryParams}`
  );
  return response.json();
};

export const findSimilarArticles = async (
  articleId: string,
  limit: number = 5
): Promise<SimilarArticlesResponse> => {
  const response = await fetch(
    `${API_BASE_URL}/news/search/similar/${articleId}?limit=${limit}`
  );
  return response.json();
};
```

### React Component Example

```tsx
import { searchNewsSemantic } from '@/services/newsApi';

export const NewsSemanticSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const response = await searchNewsSemantic({
      query,
      limit: 10,
      similarity_threshold: 0.3
    });
    setResults(response.results);
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search articles..."
      />
      <button onClick={handleSearch}>Search</button>

      {results.map((result) => (
        <ArticleCard
          key={result.article.id}
          article={result.article}
          score={result.similarity_score}
        />
      ))}
    </div>
  );
};
```

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Query Latency | <50ms (keyword), <500ms (with filters) |
| Index Size | 70 articles (~140KB JSON) |
| Scalability | Suitable for <10,000 articles |
| Memory Footprint | ~1MB (cached index) |
| Concurrent Requests | Limited by FastAPI workers |

**Bottlenecks:**
- Linear scan (O(n) per query)
- In-memory filtering
- No caching (each query re-scores all articles)

**Optimization Opportunities:**
1. Add result caching (5-minute TTL)
2. Pre-compute article term vectors
3. Use inverted index for faster term matching
4. Migrate to Elasticsearch for >10K articles

## Future Enhancement: True Semantic Search

### Option 1: Direct ChromaDB Integration

**Requirements:**
```bash
pip install chromadb sentence-transformers
```

**Embedding Pipeline:**
```bash
# Embed articles into ChromaDB
python3 scripts/rag/embed_news_articles.py --batch-size 50
```

**Service Update:**
```python
# Uncomment ChromaDB imports in news_search_service.py
# Enable vector similarity search in semantic_search()
```

**Performance:**
- Query time: ~50-200ms
- Better relevance than keyword matching
- Requires ~440MB ChromaDB storage

### Option 2: MCP Vector Search (Recommended)

**Advantages:**
- No Python dependencies
- Reuses existing mcp-vector-search infrastructure
- Works across all document types (news + court docs)

**Implementation:**
1. Index news articles in mcp-vector-search codebase
2. Use MCP tools from Claude interface
3. Frontend calls MCP directly (bypassing backend)

**MCP Tools Available:**
- `mcp__mcp-vector-search__search_code` - Semantic code/content search
- `mcp__mcp-vector-search__search_similar` - Find similar documents
- `mcp__mcp-vector-search__search_context` - Context-based discovery

**Example MCP Usage:**
```javascript
// Frontend calls MCP tools directly
const results = await mcpClient.callTool('mcp__mcp-vector-search__search_code', {
  query: 'financial fraud and corruption',
  file_extensions: ['.json'],  // Filter to news articles
  limit: 10
});
```

## Testing

### Backend API Tests

```bash
# Test semantic search
curl "http://localhost:8081/api/news/search/semantic?query=arrest&limit=5"

# Test similar articles
curl "http://localhost:8081/api/news/search/similar/1de6b30b-3c6e-49e3-935c-f2e848db1b76"

# Test search stats
curl "http://localhost:8081/api/news/search/stats"
```

### Test Queries

```bash
# Broad topical search
query="financial crimes corruption"

# Specific event search
query="arrest trafficking charges"

# Entity-focused search
query="Ghislaine Maxwell trial testimony"

# Publication-specific
query="investigation plea deal" publication="Miami Herald"
```

### Expected Results

- **Arrest/trafficking**: Should return arrest-related articles
- **Trial/testimony**: Should return court proceeding articles
- **Financial/fraud**: Should return investigation articles
- **Similarity threshold**: Higher = fewer, more relevant results

## Troubleshooting

### No Results Returned

**Issue**: `{"total": 0, "results": []}`

**Solutions:**
1. Lower `similarity_threshold` (try 0.1-0.2)
2. Simplify query (use fewer terms)
3. Check article index exists: `ls data/metadata/news_articles_index.json`
4. Verify articles loaded: `curl http://localhost:8081/api/news/stats`

### Low Relevance Scores

**Issue**: Results returned but scores <0.3

**Causes:**
- Query terms don't match article content
- Articles use different terminology
- Tags/entities don't align with query

**Solutions:**
1. Use broader query terms
2. Include entity names explicitly
3. Search by publication for known coverage
4. Try similar article search from known relevant article

### Import Errors

**Issue**: `ModuleNotFoundError: No module named 'chromadb'`

**Solution**: This is expected. The current implementation uses keyword fallback and doesn't require ChromaDB. If you want true semantic search, see "Future Enhancement" section.

## Success Criteria

- ✅ Semantic search endpoint returns relevant articles
- ✅ Similar article recommendations work
- ✅ Performance acceptable (<500ms per search)
- ✅ Integration with existing news API seamless
- ✅ No errors in backend logs
- ⚠️ True semantic search requires MCP or ChromaDB integration (future enhancement)

## Next Steps

1. **Frontend Integration** (Pending)
   - Add semantic search to News page
   - Create "Related Articles" component
   - Integrate with NewsFilters

2. **Performance Optimization** (Optional)
   - Add Redis caching for search results
   - Pre-compute article term vectors
   - Implement search analytics

3. **True Semantic Search** (Future)
   - Deploy ChromaDB integration OR
   - Implement MCP vector search in frontend

## Files Modified

- ✅ `/server/services/news_search_service.py` - Search logic
- ✅ `/server/routes/news.py` - API endpoints
- ⏳ `/frontend/src/services/newsApi.ts` - API client (pending)
- ⏳ `/frontend/src/components/news/NewsSemanticSearch.tsx` - UI (pending)

## Related Documentation

- [News Articles API](./docs/api/NEWS_API.md) - Full news API documentation
- [RAG System](./docs/rag/RAG_SYSTEM.md) - Vector search architecture
- [MCP Integration](./docs/mcp/MCP_TOOLS.md) - MCP tools reference

---

**Last Updated**: 2025-11-20
**Status**: Backend Complete, Frontend Pending
**Search Method**: Keyword Fallback (Semantic via MCP future enhancement)
