# Entity Enrichment System

**Author**: Python Engineer
**Date**: 2025-11-16
**Version**: 1.0.0

## Overview

The Entity Enrichment System augments entities in the Epstein Document Archive with biographical information from public web sources while maintaining strict provenance tracking and ethical guidelines.

### Key Features

- **Web Search Integration**: DuckDuckGo search (no API key required)
- **Provenance Tracking**: Every fact traceable to original source
- **Source Reliability Scoring**: Confidence scores based on domain reputation
- **Rate Limiting**: Respects search API limits (5 requests/minute)
- **Caching**: 30-day TTL to minimize redundant searches
- **Ethical Constraints**: Only enriches entities already in documents

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Endpoints                        │
│  /api/entities/{id}/enrich                                  │
│  /api/entities/{id}/enrichment                              │
│  /api/entities/enrich/batch                                 │
│  /api/enrichment/stats                                      │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              EntityEnrichmentService                        │
│  - Cache management (30-day TTL)                            │
│  - Rate limiting (5 req/min)                                │
│  - Batch processing with concurrency control                │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              DuckDuckGoSearch                               │
│  - HTML scraping (no API key)                               │
│  - Result parsing and extraction                            │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│         SourceReliabilityScorer                             │
│  - Domain-based confidence scoring                          │
│  - Wikipedia: 0.9, NYT: 0.85, Social Media: 0.3             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Request**: API receives entity enrichment request
2. **Cache Check**: Check if valid enrichment exists (< 30 days old)
3. **Rate Limit**: Acquire token from rate limiter (max 5/min)
4. **Search**: Perform DuckDuckGo search: `"{entity_name}" Epstein documents`
5. **Parsing**: Extract titles, URLs, snippets from HTML results
6. **Scoring**: Assign confidence scores based on source domain
7. **Extraction**: Extract biography, profession, dates from snippets
8. **Storage**: Cache enrichment with full provenance
9. **Response**: Return formatted data with sources

## Data Models

### EnrichmentSource

Provenance record for every piece of information:

```python
{
    "url": "https://nytimes.com/article/...",
    "title": "Article Title",
    "snippet": "Original text containing the information...",
    "retrieved_at": "2025-11-16T23:00:00Z",
    "confidence": 0.85,  # NYT = high confidence
    "search_query": "\"Ghislaine Maxwell\" Epstein documents",
    "domain": "nytimes.com"
}
```

### EntityEnrichment

Complete enrichment data with metadata:

```python
{
    "entity_id": "ghislaine_maxwell",
    "entity_name": "Ghislaine Maxwell",
    "biography": "British socialite and convicted sex offender...",
    "profession": "Socialite",
    "associations": ["Jeffrey Epstein", "Prince Andrew"],
    "known_dates": ["1991", "2002", "2019"],
    "sources": [
        // Array of EnrichmentSource objects
    ],
    "enriched_at": "2025-11-16T23:00:00Z",
    "last_updated": "2025-11-16T23:00:00Z",
    "search_queries_used": [
        "\"Ghislaine Maxwell\" Epstein documents"
    ],
    "total_sources": 10,
    "average_confidence": 0.72
}
```

## Source Reliability Scoring

### Confidence Score Levels

| Source Type | Confidence | Examples |
|------------|-----------|----------|
| **Court Documents** | 1.0 | courtlistener.com, pacer.gov |
| **Wikipedia/Academic** | 0.85-0.9 | wikipedia.org, .edu domains |
| **Major News** | 0.75-0.85 | NYT, WaPo, Guardian, Reuters |
| **Mid-Tier News** | 0.65-0.75 | CNN, Forbes, Bloomberg |
| **Archives** | 0.7-0.8 | archive.org, documentcloud.org |
| **Unknown Sources** | 0.5 | Default for unrecognized domains |
| **Social Media** | 0.3 | Twitter, Facebook, Reddit |
| **Blogs** | 0.2 | Medium, Blogspot, WordPress |

### Scoring Rationale

**Design Decision**: Domain-based heuristic scoring

**Alternatives Considered**:
1. Manual curation of source list (too labor-intensive)
2. ML-based article quality assessment (over-engineered)
3. Citation count analysis (unavailable from search results)

**Trade-offs**:
- **Simplicity** vs. **Precision**: Domain patterns are easy to maintain but may misclassify individual articles
- **Transparency** vs. **Accuracy**: Clear rules vs. opaque ML predictions
- **Speed** vs. **Quality**: Instant scoring vs. time-consuming analysis

**Future Enhancements**:
- Article-level signals: Publication date, author credentials, citations
- User feedback on source quality
- Cross-reference verification across multiple sources

## Rate Limiting

### Token Bucket Algorithm

```python
class RateLimiter:
    max_requests = 5      # Maximum requests
    time_window = 60      # Per 60 seconds

    async def acquire():
        # Wait until token available
        # Add timestamp to bucket
        # Return when allowed
```

**Why 5 requests/minute?**
- DuckDuckGo informal limit to avoid blocking
- Respectful scraping practices
- Batch operations still complete quickly (3 concurrent = 15 entities/min)

**Enforcement**:
- Shared across all enrichment requests
- Blocks until token available (no request rejection)
- Automatic cleanup of expired timestamps

## Ethical Guidelines

### 1. Only Enrich Documented Entities

**Rule**: Only entities already mentioned in archive documents can be enriched.

**Rationale**: Prevents speculative searches for individuals not connected to existing documents.

**Enforcement**: API endpoints verify entity exists in `entity_stats` before enrichment.

### 2. Source Attribution

**Rule**: Every piece of information must include source URL, title, snippet, and confidence score.

**Rationale**: Transparency about data origin and quality. Users can verify information.

**Enforcement**: `EnrichmentSource` model requires all fields. UI displays sources with every fact.

### 3. Accuracy Disclaimers

**Rule**: All enrichment responses include disclaimer about accuracy.

**Rationale**: Web search results are not ground truth. Users must verify critical information.

**Enforcement**: `format_for_ui()` automatically adds disclaimer to every response.

**Disclaimer Text**:
```
"Information sourced from public web search. Accuracy not guaranteed.
See sources for verification."
```

### 4. Respect Copyright

**Rule**: Only snippets (150-500 chars) stored, never full article text.

**Rationale**: Fair use for search results. Avoid copyright infringement.

**Enforcement**: Snippet extraction limited to search result snippets provided by DuckDuckGo.

### 5. No PII Beyond Public Documents

**Rule**: Only extract information already in public web search results.

**Rationale**: Privacy protection. No aggregation of private data.

**Enforcement**: Search queries limited to `"{name}" Epstein documents"` (public context).

### 6. Rate Limit Respect

**Rule**: Maximum 5 searches per minute. Respect robots.txt.

**Rationale**: Avoid overloading search engines. Good netizen behavior.

**Enforcement**: `RateLimiter` class enforces limit. `httpx` client respects redirects and timeouts.

## API Reference

### GET /api/entities/{entity_id}/enrich

Trigger web search enrichment for an entity.

**Parameters**:
- `entity_id` (path): Entity identifier or name
- `force_refresh` (query, optional): Bypass cache (default: false)

**Response**:
```json
{
    "entity_id": "ghislaine_maxwell",
    "entity_name": "Ghislaine Maxwell",
    "summary": "British socialite and convicted sex offender...",
    "facts": [
        {
            "category": "Biography",
            "text": "Information extracted from sources...",
            "sources": [
                {
                    "title": "Source Title",
                    "url": "https://...",
                    "confidence": 0.85,
                    "snippet": "Original text...",
                    "domain": "nytimes.com"
                }
            ]
        }
    ],
    "metadata": {
        "total_sources": 10,
        "average_confidence": 0.72,
        "last_updated": "2025-11-16T23:00:00Z",
        "search_queries": [...]
    },
    "disclaimer": "Information sourced from public web search..."
}
```

**Errors**:
- `404`: Entity not found in archive
- `429`: Rate limit exceeded
- `500`: Search service error

### GET /api/entities/{entity_id}/enrichment

Get cached enrichment data (fast, no search).

**Parameters**:
- `entity_id` (path): Entity identifier or name

**Response** (if cached):
```json
{
    // Same format as /enrich endpoint
}
```

**Response** (if not cached):
```json
{
    "entity_id": "example",
    "entity_name": "Example Person",
    "status": "not_enriched",
    "message": "No enrichment data available. Use /enrich to generate.",
    "cache_ttl_days": 30
}
```

### POST /api/entities/enrich/batch

Enrich multiple entities concurrently.

**Request Body**:
```json
["entity_id_1", "entity_id_2", "entity_id_3"]
```

**Parameters**:
- `max_concurrent` (query, optional): Concurrent requests (1-5, default: 3)

**Response**:
```json
{
    "total": 3,
    "enrichments": [
        // Array of enrichment objects
    ]
}
```

**Limits**:
- Maximum 20 entities per batch
- Rate limiting applied across concurrent requests

### GET /api/enrichment/stats

Get enrichment cache statistics.

**Response**:
```json
{
    "total_enrichments": 150,
    "valid_enrichments": 120,
    "stale_enrichments": 30,
    "average_sources_per_entity": 8.5,
    "average_confidence": 0.72
}
```

## Usage Examples

### Command Line (curl)

```bash
# Enrich single entity
curl -u epstein:archive2025 \
  'http://localhost:8000/api/entities/Ghislaine%20Maxwell/enrich'

# Get cached enrichment
curl -u epstein:archive2025 \
  'http://localhost:8000/api/entities/Ghislaine%20Maxwell/enrichment'

# Force refresh (bypass cache)
curl -u epstein:archive2025 \
  'http://localhost:8000/api/entities/Ghislaine%20Maxwell/enrich?force_refresh=true'

# Batch enrichment
curl -u epstein:archive2025 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '["Bill Clinton", "Donald Trump", "Prince Andrew"]' \
  'http://localhost:8000/api/entities/enrich/batch?max_concurrent=3'

# Get statistics
curl -u epstein:archive2025 \
  'http://localhost:8000/api/enrichment/stats'
```

### Python Client

```python
import httpx
import asyncio

async def enrich_entity(entity_name: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/entities/{entity_name}/enrich",
            auth=("epstein", "archive2025")
        )
        return response.json()

# Usage
result = asyncio.run(enrich_entity("Ghislaine Maxwell"))
print(f"Found {len(result['facts'])} facts")
for fact in result['facts']:
    print(f"{fact['category']}: {fact['text'][:100]}...")
```

### JavaScript Frontend

```javascript
async function enrichEntity(entityId) {
    const response = await fetch(
        `/api/entities/${encodeURIComponent(entityId)}/enrich`,
        {
            credentials: 'include'  // Include auth cookies
        }
    );

    const data = await response.json();

    // Display facts with sources
    data.facts.forEach(fact => {
        console.log(`${fact.category}: ${fact.text}`);
        fact.sources.forEach(source => {
            console.log(`  - ${source.title} (${source.confidence})`);
            console.log(`    ${source.url}`);
        });
    });

    // Show disclaimer
    console.log(`\nDisclaimer: ${data.disclaimer}`);
}
```

## Testing

### Run Test Suite

```bash
# Install dependencies
pip install -r requirements.txt

# Run test script
python3 server/test_enrichment.py
```

### Expected Output

```
================================================================================
ENTITY ENRICHMENT SERVICE - TEST SUITE
================================================================================

TEST 1: Enriching entity 'Ghislaine Maxwell'
--------------------------------------------------------------------------------
✓ Enrichment completed
  - Entity: Ghislaine Maxwell
  - Sources found: 10
  - Average confidence: 0.72
  - Profession: Socialite
  ...

TEST 2: Retrieving cached enrichment
--------------------------------------------------------------------------------
✓ Cache hit!
  - Last updated: 2025-11-16T23:00:00
  - Sources cached: 10

...

ALL TESTS PASSED ✓
```

## Performance

### Metrics

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Cache hit | < 10ms | N/A |
| Single enrichment | 2-5s | 1/2-5s |
| Batch (3 entities, concurrent) | 3-8s | ~1/s |
| Rate limit wait | 0-60s | 5/min |

### Optimization Strategies

**Caching**: 30-day TTL dramatically reduces search load
- First enrichment: ~3s (web search)
- Cached retrieval: ~10ms (1000x faster)

**Batch Processing**: Concurrent searches with rate limiting
- Sequential: 3 entities × 3s = 9s
- Concurrent (3 workers): ~3-4s (2-3x faster)

**Rate Limiting**: Prevents blocking by search engine
- Respectful scraping (5 req/min)
- Burst support with token bucket
- Graceful backoff (waits instead of fails)

## Monitoring

### Cache Statistics

Check enrichment health:

```bash
curl -u epstein:archive2025 \
  'http://localhost:8000/api/enrichment/stats'
```

**Key Metrics**:
- `valid_enrichments`: Enrichments within TTL
- `stale_enrichments`: Need refresh
- `average_confidence`: Overall source quality

**Alerts**:
- Average confidence < 0.5 → Improve source quality
- Stale enrichments > 50% → Increase batch refresh
- Total enrichments = 0 → Service not working

### Search Quality

Monitor search result quality:

```bash
# Check enrichment for known entity
curl -u epstein:archive2025 \
  'http://localhost:8000/api/entities/Jeffrey%20Epstein/enrich' | \
  jq '.metadata.average_confidence'
```

**Quality Thresholds**:
- High quality: confidence > 0.7
- Medium quality: confidence 0.5-0.7
- Low quality: confidence < 0.5

## Troubleshooting

### No Search Results

**Symptom**: Entity enrichment returns 0 sources

**Causes**:
1. Entity name too generic or misspelled
2. DuckDuckGo blocking (rate limit exceeded)
3. Network connectivity issues

**Solutions**:
1. Verify entity name spelling
2. Check rate limiter (5 req/min limit)
3. Test network: `curl https://duckduckgo.com`

### Low Confidence Scores

**Symptom**: `average_confidence < 0.5`

**Causes**:
1. Search results from low-quality sources
2. Entity name returns irrelevant results
3. Limited high-quality sources available

**Solutions**:
1. Refine search query (add context)
2. Verify entity relevance to archive
3. Manual source curation for critical entities

### Rate Limit Errors

**Symptom**: Enrichment hangs or times out

**Causes**:
1. Too many concurrent requests
2. Batch size too large
3. Rate limiter bottleneck

**Solutions**:
1. Reduce `max_concurrent` parameter
2. Split large batches (< 20 entities)
3. Wait 60s for rate limit reset

## Future Enhancements

### Planned Features

1. **Multi-Search Engine Support**
   - Add Brave Search API (requires key)
   - Add SearxNG self-hosted instance
   - Aggregate results across engines

2. **Advanced Source Scoring**
   - Article publication date (recency)
   - Author credentials verification
   - Cross-reference validation

3. **Entity Relationship Extraction**
   - Extract associations from snippets
   - Build connection graph from enrichment
   - Validate against flight logs/documents

4. **User Feedback Loop**
   - Rate source quality (thumbs up/down)
   - Flag incorrect information
   - Improve confidence scores over time

5. **Semantic Enrichment**
   - Extract structured data (dates, locations, roles)
   - Build knowledge graph from sources
   - Link to existing archive documents

## Security Considerations

### Input Validation

- Entity IDs validated against existing archive entities
- Search queries sanitized (no code injection)
- Rate limiting prevents abuse

### Source Validation

- URLs validated (HTTP/HTTPS only)
- No execution of JavaScript from search results
- Timeouts prevent hanging requests

### Data Privacy

- No PII collection beyond public search results
- Search queries logged for debugging only
- Cache stored locally (no third-party storage)

## Compliance

### Robots.txt

DuckDuckGo allows search scraping for non-commercial research purposes.

### Terms of Service

This system:
- ✅ Non-commercial research use
- ✅ Respectful rate limiting (5 req/min)
- ✅ Attribution to original sources
- ❌ No automated commercial scraping
- ❌ No circumvention of access controls

### Copyright

Fair use provisions:
- Search result snippets (150-500 chars)
- Attribution with URL to original
- Non-commercial educational purpose

## Support

### Documentation

- This file: `/docs/ENTITY_ENRICHMENT.md`
- API docs: `http://localhost:8000/docs` (when server running)
- Source code: `/server/services/entity_enrichment.py`

### Contact

- GitHub Issues: Project repository
- Questions: See README.md for contribution guidelines

---

**Last Updated**: 2025-11-16
**Version**: 1.0.0
**Author**: Python Engineer
