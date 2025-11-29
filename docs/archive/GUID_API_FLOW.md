# GUID-Based Entity API Flow

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- System Architecture
- Request Flow
- Pattern 1: GUID Only

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Server Startup                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Load entity_statistics.json (1,637 entities)               │
│     ↓                                                           │
│  2. Build name_to_id mapping (backward compatibility)          │
│     ↓                                                           │
│  3. Build guid_to_id mapping (v3 API)     ← NEW!               │
│                                                                 │
│     guid_to_id = {                                              │
│       "8889edfa-d770-54e4-8192-dc900cdd2257": "abby",          │
│       "8e0f7e1f-3a6a-5e26-a922-0ceb12cb346a": "abby_king",     │
│       ...                                                       │
│     }                                                           │
│                                                                 │
│  ✓ 1,637 GUIDs indexed (100% coverage)                         │
│  ✓ O(1) lookup performance                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow

### Pattern 1: GUID Only

```
┌────────────────────────────────────────────────────────────────┐
│ Request: GET /api/v3/entities/{guid}                           │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ Example: GET /api/v3/entities/8889edfa-d770-54e4-8192-...     │
└────────────────────────────────────────────────────────────────┘
                            ↓
             ┌──────────────────────────┐
             │  1. Validate UUID format │
             │     UUID(guid, version=4)│
             └──────────────────────────┘
                            ↓
             ┌──────────────────────────┐
             │  2. Lookup entity_id     │
             │     guid_to_id[guid]     │
             │     → "abby"              │
             └──────────────────────────┘
                            ↓
             ┌──────────────────────────┐
             │  3. Retrieve entity data │
             │     entity_stats["abby"] │
             └──────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ Response: 200 OK                                               │
│ {                                                              │
│   "id": "abby",                                                │
│   "name": "Abby",                                              │
│   "guid": "8889edfa-d770-54e4-8192-dc900cdd2257",            │
│   "total_documents": 0,                                        │
│   ...                                                          │
│ }                                                              │
└────────────────────────────────────────────────────────────────┘
```

### Pattern 2: GUID + SEO Name

```
┌────────────────────────────────────────────────────────────────┐
│ Request: GET /api/v3/entities/{guid}/{name}                    │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ Example: GET /api/v3/entities/8889edfa-d770-54e4.../abby      │
└────────────────────────────────────────────────────────────────┘
                            ↓
             ┌──────────────────────────┐
             │  1. Validate UUID format │
             │     UUID(guid, version=4)│
             └──────────────────────────┘
                            ↓
             ┌──────────────────────────┐
             │  2. Lookup entity_id     │
             │     (name param ignored) │
             │     guid_to_id[guid]     │
             │     → "abby"              │
             └──────────────────────────┘
                            ↓
             ┌──────────────────────────┐
             │  3. Retrieve entity data │
             │     entity_stats["abby"] │
             └──────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ Response: 200 OK (same as Pattern 1)                           │
│ {                                                              │
│   "id": "abby",                                                │
│   "name": "Abby",                                              │
│   "guid": "8889edfa-d770-54e4-8192-dc900cdd2257",            │
│   ...                                                          │
│ }                                                              │
└────────────────────────────────────────────────────────────────┘

Note: SEO name "abby" is purely for URL readability
      It is NOT used in entity lookup (only GUID matters)
```

## Error Handling

### Case 1: Invalid GUID Format

```
Request: GET /api/v3/entities/invalid-guid

             ┌──────────────────────────┐
             │  UUID validation fails   │
             │  ValueError raised       │
             └──────────────────────────┘
                            ↓
Response: 400 Bad Request
{
  "detail": "Invalid GUID format: 'invalid-guid'.
             Expected UUID4 format..."
}
```

### Case 2: GUID Not Found

```
Request: GET /api/v3/entities/00000000-0000-4000-8000-000000000000

             ┌──────────────────────────┐
             │  guid_to_id[guid] = None │
             └──────────────────────────┘
                            ↓
Response: 404 Not Found
{
  "detail": "Entity not found for GUID: '00000000...'.
             GUID may not exist or entity may have been removed."
}
```

### Case 3: Data Inconsistency (Defensive)

```
Request: GET /api/v3/entities/{valid_guid}

             ┌──────────────────────────┐
             │  guid_to_id[guid] = "id" │
             │  BUT entity_stats["id"]  │
             │  returns None/missing    │
             └──────────────────────────┘
                            ↓
Response: 500 Internal Server Error
{
  "detail": "Internal error: Entity data inconsistency detected."
}

Log: ERROR: GUID mapping out of sync: GUID '{guid}' maps to ID '{id}'
                                       but entity not found
```

## Performance Characteristics

| Operation | Complexity | Time (1,637 entities) |
|-----------|------------|----------------------|
| Startup: Build guid_to_id | O(n) | <10ms |
| Request: UUID validation | O(1) | ~1-5µs |
| Request: GUID lookup | O(1) | ~0.1-1µs |
| Request: Entity retrieval | O(1) | ~0.1-1µs |
| **Total per request** | **O(1)** | **~10µs overhead** |

## API Versions Comparison

```
┌──────────────────────────────────────────────────────────────────┐
│                      Entity Lookup Methods                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  v1: /api/entities/{name_or_id}                                 │
│      ├─ Try ID lookup (O(1))                                    │
│      ├─ Fallback: Name disambiguation (O(n))                    │
│      └─ Use case: Legacy backward compatibility                 │
│                                                                  │
│  v2: /api/v2/entities/{entity_id}                               │
│      ├─ Direct ID lookup (O(1))                                 │
│      └─ Use case: Internal API, known entity IDs                │
│                                                                  │
│  v3: /api/v3/entities/{guid}/{name?}     ← NEW!                 │
│      ├─ GUID lookup via guid_to_id (O(1))                       │
│      ├─ Optional SEO name (ignored in lookup)                   │
│      └─ Use case: Public URLs, shareable links, SEO            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Real-World Examples

### Example 1: Direct GUID Access

```bash
# Curl command
curl "https://epstein.archive/api/v3/entities/8889edfa-d770-54e4-8192-dc900cdd2257"

# JavaScript fetch
const guid = "8889edfa-d770-54e4-8192-dc900cdd2257";
const response = await fetch(`/api/v3/entities/${guid}`);
const entity = await response.json();
```

### Example 2: SEO-Friendly URL

```bash
# Curl command
curl "https://epstein.archive/api/v3/entities/8889edfa-d770-54e4-8192-dc900cdd2257/abby"

# JavaScript fetch with slug generation
const guid = entity.guid;
const slug = entity.name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
const url = `/api/v3/entities/${guid}/${slug}`;
const response = await fetch(url);
```

### Example 3: React Component

```tsx
// EntityLink.tsx
interface EntityLinkProps {
  entity: {
    guid: string;
    name: string;
  };
}

function EntityLink({ entity }: EntityLinkProps) {
  const slug = entity.name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

  const url = `/entities/${entity.guid}/${slug}`;

  return (
    <a href={url} className="entity-link">
      {entity.name}
    </a>
  );
}

// Generated URL: /entities/8889edfa-d770-54e4-8192-dc900cdd2257/abby
// Backend ignores "abby" and only uses GUID for lookup
```

## Security Considerations

### GUID Enumeration

**Risk**: Attackers could enumerate GUIDs to discover entities
**Mitigation**:
- UUID4 provides 2^122 possible values (~5.3 × 10^36)
- Brute force enumeration is computationally infeasible
- Authentication required for all endpoints (username: str = Depends(get_current_user))

### GUID Validation

**Risk**: Invalid GUIDs could cause errors or security issues
**Mitigation**:
- UUID validation before lookup (UUID(guid, version=4))
- Rejects non-UUID strings early in request pipeline
- Prevents injection attacks via GUID parameter

### Name Parameter Injection

**Risk**: Malicious content in name parameter
**Mitigation**:
- Name parameter is ignored in lookup logic
- FastAPI path parameter validation
- No SQL/code execution risk (name not used in queries)

## Migration Path

### Phase 1: Deployment (Current)
- ✅ Deploy v3 endpoint
- ✅ Test GUID lookups
- ✅ Verify error handling

### Phase 2: Frontend Integration
- [ ] Update entity link generation to use GUIDs
- [ ] Implement URL slug helper function
- [ ] Add canonical URL meta tags

### Phase 3: URL Migration
- [ ] Add 301 redirects from v1/v2 URLs to v3
- [ ] Update sitemap.xml with GUID URLs
- [ ] Update Open Graph tags for social sharing

### Phase 4: Monitoring
- [ ] Track v3 endpoint usage
- [ ] Monitor error rates (400/404/500)
- [ ] Performance benchmarks in production

## Monitoring & Observability

### Key Metrics

```python
# Add to app.py for monitoring
@app.middleware("http")
async def track_guid_lookups(request: Request, call_next):
    if request.url.path.startswith("/api/v3/entities/"):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Log metrics
        logger.info(
            f"v3_entity_lookup status={response.status_code} "
            f"duration={duration*1000:.2f}ms"
        )
        return response
    return await call_next(request)
```

### Health Checks

```python
@app.get("/api/v3/health")
async def v3_health():
    """V3 API health check"""
    return {
        "status": "healthy",
        "guid_mapping_size": len(guid_to_id),
        "entity_count": len(entity_stats),
        "coverage": f"{len(guid_to_id) / len(entity_stats) * 100:.1f}%"
    }
```

## Conclusion

The GUID-based v3 endpoint provides:
- ✅ **Stable URLs**: GUIDs never change
- ✅ **SEO-Friendly**: Human-readable names in URLs
- ✅ **Fast**: O(1) lookup performance
- ✅ **Secure**: UUID validation + authentication
- ✅ **Flexible**: Name parameter allows URL customization

**Ready for production deployment!**
