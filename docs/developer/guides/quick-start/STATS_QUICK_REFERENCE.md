# Unified Stats API - Quick Reference

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Endpoint
- Common Usage
- Get all stats (cached)
- Get fresh data
- Get specific sections

---

## Endpoint

```
GET /api/v2/stats
```

## Common Usage

### Get all stats (cached)
```bash
curl http://localhost:8000/api/v2/stats
```

### Get fresh data
```bash
curl http://localhost:8000/api/v2/stats?use_cache=false
```

### Get specific sections
```bash
curl http://localhost:8000/api/v2/stats?sections=documents,entities,flights
```

### Clear cache
```bash
curl -X POST http://localhost:8000/api/v2/stats/cache/clear
```

## Response Structure

```typescript
{
  status: "success" | "partial" | "error",
  timestamp: string,  // ISO 8601 UTC
  data: {
    documents?: {
      total: number,
      court_documents: number,
      sources: number
    },
    timeline?: {
      total_events: number,
      date_range: { earliest: string, latest: string }
    },
    entities?: {
      total: number,
      with_biographies: number,
      types: { person: number, organization: number }
    },
    flights?: {
      total: number,
      date_range: { earliest: string, latest: string },
      unique_passengers: number
    },
    news?: {
      total_articles: number,
      sources: number,
      date_range: { earliest: string, latest: string }
    },
    network?: {
      nodes: number,
      edges: number,
      avg_degree: number
    },
    vector_store?: {
      total_documents: number,
      court_documents: number,
      news_articles: number,
      collection: string
    }
  },
  cache: {
    hit: boolean,
    ttl: number  // seconds
  },
  errors?: Array<{
    source: string,
    message: string
  }>
}
```

## React Hook

```typescript
import { useQuery } from '@tanstack/react-query';

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const res = await fetch('/api/v2/stats');
      if (!res.ok) throw new Error('Failed to fetch stats');
      return res.json();
    },
    staleTime: 60 * 1000  // 1 minute
  });
}
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Cached | < 50ms |
| Fresh | < 500ms |
| Cache Hit Rate | > 80% |

## Testing

```bash
# Run full test suite
python3 test_unified_stats.py

# Quick check
curl http://localhost:8000/api/v2/stats | jq '.status'
```

## Files

- **Endpoint**: `server/routes/stats.py`
- **Tests**: `test_unified_stats.py`
- **Docs**: `UNIFIED_STATS_API.md`

## Migration

### Old (multiple requests)
```typescript
const docs = await fetch('/api/stats');
const entities = await fetch('/api/entities');
const flights = await fetch('/api/flights/all');
```

### New (single request)
```typescript
const { data } = await fetch('/api/v2/stats').then(r => r.json());
const { documents, entities, flights } = data;
```

## Common Issues

### Partial Failures
Check `errors` array:
```bash
curl http://localhost:8000/api/v2/stats | jq '.errors'
```

### Cache Not Working
Clear and retry:
```bash
curl -X POST http://localhost:8000/api/v2/stats/cache/clear
curl http://localhost:8000/api/v2/stats
```

### Slow Responses
Force cache:
```bash
curl http://localhost:8000/api/v2/stats?use_cache=true
```
