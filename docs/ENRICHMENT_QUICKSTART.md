# Entity Enrichment - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install Dependencies

```bash
cd /Users/masa/Projects/Epstein
source .venv/bin/activate
pip install httpx beautifulsoup4 html5lib
```

### 2. Run Test Suite

```bash
python3 server/test_enrichment.py
```

Expected output: All tests pass ✅

### 3. Start Server

```bash
python3 server/app.py
```

Server starts on `http://localhost:8000`

### 4. Test API Endpoints

```bash
# Enrich an entity
curl -u epstein:archive2025 \
  'http://localhost:8000/api/entities/Ghislaine%20Maxwell/enrich'

# Get cached enrichment
curl -u epstein:archive2025 \
  'http://localhost:8000/api/entities/Ghislaine%20Maxwell/enrichment'

# Get statistics
curl -u epstein:archive2025 \
  'http://localhost:8000/api/enrichment/stats'
```

## 📖 API Endpoints

| Endpoint | Method | Purpose | Speed |
|----------|--------|---------|-------|
| `/api/entities/{id}/enrich` | GET | Trigger enrichment | 2-5s (real), <100ms (mock) |
| `/api/entities/{id}/enrichment` | GET | Get cached data | <10ms |
| `/api/entities/enrich/batch` | POST | Batch enrich | Varies |
| `/api/enrichment/stats` | GET | Cache stats | <10ms |

## 🎯 Common Use Cases

### Use Case 1: Enrich Entity on Page Load

```javascript
async function loadEntityPage(entityId) {
    // Try cache first (fast)
    const cached = await fetch(`/api/entities/${entityId}/enrichment`);
    const data = await cached.json();

    if (data.status === 'not_enriched') {
        // Trigger enrichment in background
        fetch(`/api/entities/${entityId}/enrich`, { method: 'GET' });
        // Show loading state
    } else {
        // Display enrichment immediately
        displayEnrichment(data);
    }
}
```

### Use Case 2: Batch Enrich Top Entities

```bash
# Enrich top entities
curl -u epstein:archive2025 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '["Ghislaine Maxwell", "Jeffrey Epstein", "Bill Clinton"]' \
  'http://localhost:8000/api/entities/enrich/batch?max_concurrent=3'
```

### Use Case 3: Display Enrichment with Sources

```javascript
function displayEnrichment(enrichment) {
    const html = `
        <h2>${enrichment.entity_name}</h2>
        <p>${enrichment.summary}</p>

        ${enrichment.facts.map(fact => `
            <div class="fact">
                <h3>${fact.category}</h3>
                <p>${fact.text}</p>
                <div class="sources">
                    ${fact.sources.map(source => `
                        <a href="${source.url}" target="_blank">
                            ${source.title}
                            <span class="confidence">${(source.confidence * 100).toFixed(0)}% confidence</span>
                        </a>
                    `).join('')}
                </div>
            </div>
        `).join('')}

        <p class="disclaimer">${enrichment.disclaimer}</p>
    `;

    document.getElementById('enrichment').innerHTML = html;
}
```

## 🔧 Configuration

### Switch to Real Search (Production)

**File**: `/server/app.py`

```python
# Current (Mock for demo)
enrichment_service = EntityEnrichmentService(
    storage_path=ENRICHMENT_STORAGE,
    use_mock=True  # <-- Change to False
)

# Production (Real search)
enrichment_service = EntityEnrichmentService(
    storage_path=ENRICHMENT_STORAGE,
    use_mock=False  # Enable real DuckDuckGo search
)
```

**Note**: Real search may trigger anti-bot protections. For production, use Brave Search API:

1. Get free API key: https://brave.com/search/api
2. Add to `.env.local`: `BRAVE_SEARCH_API_KEY=your_key`
3. Implement `BraveSearchAPI` class in `entity_enrichment.py`

### Adjust Cache TTL

**File**: `/server/services/entity_enrichment.py`

```python
class EntityEnrichmentService:
    CACHE_TTL_DAYS = 30  # <-- Change to desired days
```

### Adjust Rate Limiting

**File**: `/server/services/entity_enrichment.py`

```python
self.rate_limiter = RateLimiter(
    max_requests=5,    # <-- Requests per time window
    time_window=60     # <-- Seconds
)
```

## 📊 Response Format

### Enrichment Response

```json
{
    "entity_id": "ghislaine_maxwell",
    "entity_name": "Ghislaine Maxwell",
    "summary": "Brief biography...",
    "facts": [
        {
            "category": "Biography",
            "text": "Ghislaine Noelle Marion Maxwell is...",
            "sources": [
                {
                    "title": "Ghislaine Maxwell - Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 0.90,
                    "snippet": "Original text snippet...",
                    "domain": "en.wikipedia.org"
                }
            ]
        },
        {
            "category": "Profession",
            "text": "Socialite",
            "sources": [...]
        },
        {
            "category": "Dates Mentioned",
            "text": "2021",
            "sources": [...]
        }
    ],
    "metadata": {
        "total_sources": 3,
        "average_confidence": 0.87,
        "last_updated": "2025-11-16T23:00:00Z",
        "search_queries": ['"Ghislaine Maxwell" Epstein documents']
    },
    "disclaimer": "Information sourced from public web search. Accuracy not guaranteed. See sources for verification."
}
```

### Not Enriched Response

```json
{
    "entity_id": "example_person",
    "entity_name": "Example Person",
    "status": "not_enriched",
    "message": "No enrichment data available. Use POST /api/entities/{entity_id}/enrich to generate.",
    "cache_ttl_days": 30
}
```

### Statistics Response

```json
{
    "total_enrichments": 150,
    "valid_enrichments": 120,
    "stale_enrichments": 30,
    "average_sources_per_entity": 8.5,
    "average_confidence": 0.72
}
```

## ⚠️ Error Handling

### 404 - Entity Not Found

```json
{
    "detail": "Entity 'Unknown Person' not found in archive. Only entities in existing documents can be enriched."
}
```

**Solution**: Only enrich entities that exist in `entity_stats`

### 429 - Rate Limit Exceeded

```json
{
    "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

**Solution**: Wait for rate limiter to reset. Use batch endpoint with lower `max_concurrent`.

### 500 - Search Service Error

```json
{
    "detail": "Error enriching entity: Connection timeout"
}
```

**Solution**: Check network connectivity. May need to retry.

## 🧪 Testing

### Unit Tests

```bash
python3 server/test_enrichment.py
```

### Manual API Tests

```bash
# Test single enrichment
curl -u epstein:archive2025 \
  'http://localhost:8000/api/entities/Ghislaine%20Maxwell/enrich'

# Test cache retrieval
curl -u epstein:archive2025 \
  'http://localhost:8000/api/entities/Ghislaine%20Maxwell/enrichment'

# Test batch (max 3 concurrent)
curl -u epstein:archive2025 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '["Ghislaine Maxwell", "Jeffrey Epstein"]' \
  'http://localhost:8000/api/entities/enrich/batch?max_concurrent=3'
```

### Check Cache File

```bash
cat /Users/masa/Projects/Epstein/data/metadata/entity_enrichments.json | jq
```

## 📈 Monitoring

### Cache Hit Rate

```bash
curl -u epstein:archive2025 \
  'http://localhost:8000/api/enrichment/stats' | \
  jq '{hit_rate: (.valid_enrichments / .total_enrichments * 100)}'
```

### Average Source Quality

```bash
curl -u epstein:archive2025 \
  'http://localhost:8000/api/enrichment/stats' | \
  jq '.average_confidence'
```

**Good**: > 0.7 (high-quality sources)
**Acceptable**: 0.5-0.7 (mixed sources)
**Poor**: < 0.5 (low-quality sources)

## 🔒 Security

### Authentication Required

All endpoints require basic auth:
- Username: `epstein` (or from `.credentials` file)
- Password: `archive2025` (or from `.credentials` file)

### Rate Limiting

- 5 searches per minute (global)
- Applied across all users
- Prevents abuse and overload

### Input Validation

- Entity IDs validated against existing entities
- No speculative searches allowed
- Search queries sanitized

## 📚 Full Documentation

- **Complete Guide**: `/docs/ENTITY_ENRICHMENT.md`
- **Implementation Summary**: `/ENTITY_ENRICHMENT_IMPLEMENTATION.md`
- **Source Code**: `/server/services/entity_enrichment.py`
- **API Docs**: `http://localhost:8000/docs` (when server running)

## 🆘 Troubleshooting

### No Results Returned

**Problem**: Enrichment returns 0 sources

**Causes**:
1. Entity name not in mock data
2. Real search being used (fragile)

**Solutions**:
1. Check `use_mock=True` in `app.py`
2. Add entity to `MockWebSearch.mock_results`
3. Switch to Brave Search API for production

### Cache Not Updating

**Problem**: Enrichment shows stale data

**Causes**:
1. Cache TTL not expired (30 days)
2. `force_refresh=false` (default)

**Solutions**:
1. Use `?force_refresh=true` query parameter
2. Delete cache file and re-enrich
3. Reduce `CACHE_TTL_DAYS` in service

### Rate Limit Blocking

**Problem**: Requests hang or timeout

**Causes**:
1. Too many concurrent requests
2. Rate limit saturated

**Solutions**:
1. Reduce `max_concurrent` in batch endpoint
2. Wait 60 seconds for rate limit reset
3. Increase rate limit (see Configuration)

---

**Quick Start Complete!** 🎉

For advanced usage, see `/docs/ENTITY_ENRICHMENT.md`
