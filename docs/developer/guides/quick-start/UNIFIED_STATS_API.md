# Unified Statistics API

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- ✅ **Single Request**: All statistics in one API call
- ✅ **Smart Caching**: 60-second in-memory cache (configurable)
- ✅ **Graceful Degradation**: Returns partial data if some sources fail
- ✅ **Section Filtering**: Request only specific data sections
- ✅ **Performance**: < 50ms cached, < 500ms fresh

---

Comprehensive statistics endpoint for the Epstein Archive backend.

## Overview

The unified statistics API (`/api/v2/stats`) provides a single endpoint to retrieve all system statistics in one request, with intelligent caching and graceful error handling.

### Key Features

- ✅ **Single Request**: All statistics in one API call
- ✅ **Smart Caching**: 60-second in-memory cache (configurable)
- ✅ **Graceful Degradation**: Returns partial data if some sources fail
- ✅ **Section Filtering**: Request only specific data sections
- ✅ **Performance**: < 50ms cached, < 500ms fresh
- ✅ **Backward Compatible**: Existing endpoints unchanged

## Endpoint

```
GET /api/v2/stats
```

## Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_cache` | boolean | `true` | Use cached data (60s TTL) |
| `detailed` | boolean | `false` | Include detailed breakdowns (future) |
| `sections` | string | `null` | Comma-separated sections to include |

## Response Format

```json
{
  "status": "success",
  "timestamp": "2025-11-20T16:45:00Z",
  "data": {
    "documents": {
      "total": 33329,
      "court_documents": 33329,
      "sources": 5
    },
    "timeline": {
      "total_events": 103,
      "date_range": {
        "earliest": "1992-01-01",
        "latest": "2025-11-20"
      }
    },
    "entities": {
      "total": 284,
      "with_biographies": 145,
      "types": {
        "person": 250,
        "organization": 34
      }
    },
    "flights": {
      "total": 1205,
      "date_range": {
        "earliest": "1997-11-03",
        "latest": "2005-11-03"
      },
      "unique_passengers": 284
    },
    "news": {
      "total_articles": 3,
      "sources": 3,
      "date_range": {
        "earliest": "2018-11-30",
        "latest": "2020-07-02"
      }
    },
    "network": {
      "nodes": 284,
      "edges": 1624,
      "avg_degree": 5.7
    },
    "vector_store": {
      "total_documents": 33332,
      "court_documents": 33329,
      "news_articles": 3,
      "collection": "epstein_documents"
    }
  },
  "cache": {
    "hit": false,
    "ttl": 60
  }
}
```

## Status Codes

| Status | Description |
|--------|-------------|
| `"success"` | All data sources returned successfully |
| `"partial"` | Some data sources failed (see `errors` field) |
| `"error"` | All data sources failed |

## Error Response

When status is `"partial"` or `"error"`, an `errors` array is included:

```json
{
  "status": "partial",
  "data": {
    "documents": {...},
    "timeline": null,
    "entities": {...}
  },
  "errors": [
    {
      "source": "timeline",
      "message": "Failed to load timeline statistics"
    }
  ]
}
```

## Usage Examples

### 1. Basic Request (with cache)

```bash
curl http://localhost:8000/api/v2/stats
```

**Use case**: Dashboard loading, frontend initialization

### 2. Fresh Data (bypass cache)

```bash
curl http://localhost:8000/api/v2/stats?use_cache=false
```

**Use case**: Admin panels, after data updates

### 3. Request Specific Sections

```bash
curl http://localhost:8000/api/v2/stats?sections=documents,news,timeline
```

**Use case**: Partial updates, targeted refreshes

### 4. Multiple Sections

```bash
curl http://localhost:8000/api/v2/stats?sections=documents,entities,flights
```

## Data Sources

### Documents
- **Source**: `data/metadata/all_documents_index.json` (primary)
- **Fallback**: `data/metadata/master_document_index.json`
- **Fields**: `total`, `court_documents`, `sources`

### Timeline
- **Source**: `data/metadata/timeline.json`
- **Fields**: `total_events`, `date_range`

### Entities
- **Source**: `data/metadata/entity_statistics.json`
- **Fields**: `total`, `with_biographies`, `types`

### Flights
- **Source**: `data/md/entities/flight_logs_by_flight.json`
- **Fields**: `total`, `date_range`, `unique_passengers`

### News
- **Source**: `data/metadata/news_articles_index.json`
- **Fields**: `total_articles`, `sources`, `date_range`

### Network
- **Source**: `data/metadata/entity_network.json`
- **Fields**: `nodes`, `edges`, `avg_degree`

### Vector Store
- **Source**: ChromaDB at `data/vector_store/chroma`
- **Fields**: `total_documents`, `court_documents`, `news_articles`, `collection`

## Performance

### Benchmarks

| Scenario | Target | Typical |
|----------|--------|---------|
| Cached request | < 50ms | ~10ms |
| Fresh data | < 500ms | ~200ms |
| Concurrent requests | 100+ req/s | N/A |

### Caching Strategy

- **TTL**: 60 seconds (configurable in code)
- **Storage**: In-memory (server process)
- **Invalidation**: Automatic expiration, manual clear endpoint
- **Concurrency**: Thread-safe read-only operations

### Cache Management

Clear cache manually:

```bash
curl -X POST http://localhost:8000/api/v2/stats/cache/clear
```

**Returns**:
```json
{
  "status": "success",
  "message": "Statistics cache cleared",
  "cache_cleared_at": "2025-11-20T16:45:00Z"
}
```

## Graceful Degradation

If a data source fails:

1. **Returns `null` for that section**
2. **Continues processing other sections**
3. **Status changes to `"partial"`**
4. **Includes error details in `errors` array**

Example partial failure:

```json
{
  "status": "partial",
  "data": {
    "documents": {...},
    "timeline": null,
    "vector_store": null
  },
  "errors": [
    {
      "source": "timeline",
      "message": "Failed to load timeline statistics"
    },
    {
      "source": "vector_store",
      "message": "Vector store not available"
    }
  ]
}
```

## Integration Examples

### JavaScript/TypeScript

```typescript
// Fetch all stats with caching
async function getStats() {
  const response = await fetch('/api/v2/stats');
  const data = await response.json();

  if (data.status === 'success') {
    console.log('All data loaded:', data.data);
  } else if (data.status === 'partial') {
    console.warn('Partial data:', data.errors);
    // Use available data, handle missing sections
  }

  return data;
}

// Fetch specific sections only
async function getStatsForDashboard() {
  const sections = ['documents', 'entities', 'timeline'];
  const response = await fetch(
    `/api/v2/stats?sections=${sections.join(',')}`
  );
  return response.json();
}

// Force fresh data after update
async function refreshStats() {
  const response = await fetch('/api/v2/stats?use_cache=false');
  return response.json();
}
```

### Python

```python
import requests

# Basic request
response = requests.get('http://localhost:8000/api/v2/stats')
data = response.json()

if data['status'] == 'success':
    print(f"Total documents: {data['data']['documents']['total']}")
    print(f"Total entities: {data['data']['entities']['total']}")

# Request specific sections
response = requests.get(
    'http://localhost:8000/api/v2/stats',
    params={'sections': 'documents,news'}
)
```

### React Hook

```typescript
import { useQuery } from '@tanstack/react-query';

interface StatsResponse {
  status: 'success' | 'partial' | 'error';
  timestamp: string;
  data: {
    documents?: { total: number; court_documents: number; sources: number };
    entities?: { total: number; with_biographies: number };
    // ... other sections
  };
  cache: { hit: boolean; ttl: number };
  errors?: Array<{ source: string; message: string }>;
}

export function useStats(sections?: string[]) {
  return useQuery<StatsResponse>({
    queryKey: ['stats', sections],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (sections) {
        params.set('sections', sections.join(','));
      }

      const response = await fetch(`/api/v2/stats?${params}`);
      if (!response.ok) throw new Error('Failed to fetch stats');
      return response.json();
    },
    staleTime: 60 * 1000, // 1 minute (matches server cache)
    refetchOnWindowFocus: false
  });
}

// Usage in component
function Dashboard() {
  const { data, isLoading, error } = useStats(['documents', 'entities', 'flights']);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading stats</div>;

  return (
    <div>
      <h1>Documents: {data?.data.documents?.total}</h1>
      <h2>Entities: {data?.data.entities?.total}</h2>
      {data?.status === 'partial' && (
        <div className="warning">
          Some data unavailable: {data.errors?.map(e => e.source).join(', ')}
        </div>
      )}
    </div>
  );
}
```

## Testing

Run the comprehensive test suite:

```bash
# Start server
cd server && python3 app.py

# In another terminal
python3 test_unified_stats.py
```

Test suite covers:
1. ✅ Basic request functionality
2. ✅ Cache hit/miss behavior
3. ✅ Fresh data fetching
4. ✅ Section filtering
5. ✅ Data completeness
6. ✅ Performance benchmarks
7. ✅ Cache clearing

## Migration Guide

### Before (multiple endpoints)

```typescript
// Old approach: Multiple requests
const [documents, entities, flights, news] = await Promise.all([
  fetch('/api/stats'),
  fetch('/api/entities'),
  fetch('/api/flights/all'),
  fetch('/api/news/stats')
]);

const documentsData = await documents.json();
const entitiesData = await entities.json();
const flightsData = await flights.json();
const newsData = await news.json();
```

### After (single endpoint)

```typescript
// New approach: Single request
const response = await fetch('/api/v2/stats');
const data = await response.json();

const { documents, entities, flights, news } = data.data;
```

### Benefits

- **85% fewer requests**: 1 request vs 6-7 separate calls
- **Faster loading**: ~50ms vs ~300-500ms (parallel requests)
- **Simpler code**: Single fetch, single error handler
- **Better caching**: Unified cache strategy

## Backward Compatibility

All existing endpoints remain functional:

- ✅ `/api/stats` - Original stats endpoint (unchanged)
- ✅ `/api/rag/stats` - RAG/vector store stats
- ✅ `/api/news/stats` - News article stats
- ✅ `/api/flights/all` - Flight data with stats
- ✅ `/api/entities` - Entity listings

**No breaking changes** - this is an additional endpoint.

## Future Enhancements

### Planned Features

1. **Detailed Mode** (`detailed=true`)
   - Breakdown by source for documents
   - Classification distribution
   - Entity type breakdowns
   - Top passengers by flight count

2. **Filtering Parameters**
   - Date range filtering
   - Source filtering
   - Entity type filtering

3. **Comparison Mode**
   - Compare stats between date ranges
   - Growth metrics
   - Trend analysis

4. **WebSocket Updates**
   - Real-time stats updates
   - Push notifications on changes

5. **Export Formats**
   - CSV export
   - JSON download
   - PDF reports

## API Design Decisions

### Why Unified Endpoint?

**Problem**: Frontend makes 6-7 separate API calls to load dashboard
- High latency from request waterfall
- Complex error handling (which failed?)
- Cache management spread across multiple calls
- Difficult to ensure consistency

**Solution**: Single endpoint with intelligent caching
- 1 request instead of 6-7 (85% reduction)
- Single error handler with partial failure support
- Unified cache with consistent TTL
- Atomic snapshot of system state

### Why In-Memory Cache?

**Decision**: Simple in-memory cache vs Redis/database
- **Performance**: Microsecond lookup (vs millisecond for Redis)
- **Complexity**: Zero dependencies, no external services
- **Ephemeral Data**: Stats change infrequently (60s TTL sufficient)
- **Scalability**: Single server deployment (not distributed)

**Trade-off**: Cache lost on restart (acceptable for stats)

### Why Graceful Degradation?

**Decision**: Return partial data vs fail entire request
- **UX**: Show available data immediately
- **Reliability**: One broken data source doesn't break entire UI
- **Debugging**: Error array shows exactly what failed
- **Progressive Enhancement**: Frontend can decide how to handle missing data

## Monitoring

### Health Checks

Check endpoint health:

```bash
# Should return 200 with data
curl -f http://localhost:8000/api/v2/stats

# Check status field
curl http://localhost:8000/api/v2/stats | jq '.status'
```

### Key Metrics to Monitor

1. **Response Time**
   - Target: < 50ms (cached), < 500ms (fresh)
   - Alert if > 1000ms

2. **Cache Hit Rate**
   - Target: > 80% during normal operation
   - Alert if < 50%

3. **Partial Failures**
   - Monitor `status: "partial"` responses
   - Alert if > 10% of requests

4. **Error Rate**
   - Target: < 1% `status: "error"`
   - Alert if > 5%

### Logging

Server logs include:

```
INFO: Stats routes registered at /api/v2/stats
ERROR: Error loading entity statistics: [FileNotFoundError]
WARNING: ChromaDB not available for vector store stats
```

## Troubleshooting

### Cache Not Working

**Symptom**: All requests show `cache: { hit: false }`

**Cause**: Server restarted, cache cleared, or TTL expired

**Solution**: Cache rebuilds automatically on next request

### Partial Failures

**Symptom**: `status: "partial"`, some sections are `null`

**Cause**: Data file missing or ChromaDB not initialized

**Solution**: Check `errors` array for specific failures:
```json
{
  "errors": [
    {
      "source": "vector_store",
      "message": "Vector store not available"
    }
  ]
}
```

### Slow Response Times

**Symptom**: Fresh data requests > 1000ms

**Cause**: Large data files, slow disk I/O, or external dependencies

**Solutions**:
1. Check disk performance
2. Verify data file sizes aren't excessive
3. Optimize data file structure
4. Increase cache TTL

### Complete Failure

**Symptom**: HTTP 500 or `status: "error"`

**Cause**: All data sources unavailable

**Solution**:
1. Check server logs for specific errors
2. Verify data files exist in `data/metadata/`
3. Check file permissions
4. Restart server if data corruption

## Support

### Documentation
- API Reference: This document
- Code: `server/routes/stats.py`
- Tests: `test_unified_stats.py`

### Getting Help

1. Check server logs: `logs/server.log`
2. Run test suite: `python3 test_unified_stats.py`
3. Test individual data sources (existing endpoints)
4. Check file permissions in `data/` directory

## Changelog

### Version 1.0.0 (2025-11-20)
- Initial release
- Unified statistics endpoint
- 60-second in-memory caching
- Graceful degradation
- Section filtering
- Cache management endpoint
- Comprehensive test suite
