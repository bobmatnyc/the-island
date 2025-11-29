# Biography Filter API Documentation

**Quick Summary**: The `/api/v2/entities` endpoint now supports server-side filtering for biography status, ensuring reliable filtering of entities with biography data. .

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **`has_biography`** (boolean, optional, default: `false`)
- When `true`: Returns only entities with biography data
- When `false`: Returns all entities (default behavior)
- `server/api_routes.py`: Added `has_biography` query parameter
- `server/services/entity_service.py`: Implemented biography filtering logic

---

## Overview
The `/api/v2/entities` endpoint now supports server-side filtering for biography status, ensuring reliable filtering of entities with biography data.

## Implementation Details

### API Endpoint
```
GET /api/v2/entities?has_biography=true
```

### New Parameter
- **`has_biography`** (boolean, optional, default: `false`)
  - When `true`: Returns only entities with biography data
  - When `false`: Returns all entities (default behavior)

### Backend Implementation
**Files Modified:**
- `server/api_routes.py`: Added `has_biography` query parameter
- `server/services/entity_service.py`: Implemented biography filtering logic

**Filter Logic:**
```python
# Biography filter in EntityService.get_entities()
if has_biography:
    entities_list = [
        e
        for e in entities_list
        if e.get("id", "") in self.entity_bios or e.get("name", "") in self.entity_bios
    ]
```

The filter checks both entity ID and name for backward compatibility during the ID migration.

## Usage Examples

### Basic Biography Filter
```bash
# Get entities with biographies
curl "http://localhost:8081/api/v2/entities?has_biography=true&limit=10"
```

**Response:**
```json
{
  "entities": [
    {
      "id": "alan_dershowitz",
      "name": "Alan Dershowitz",
      "bio": {
        "summary": "...",
        "key_facts": [...],
        "sources": [...]
      },
      ...
    }
  ],
  "total": 59,
  "offset": 0,
  "limit": 10
}
```

### Combined with Search
```bash
# Find entities with biography matching search term
curl "http://localhost:8081/api/v2/entities?has_biography=true&search=jeffrey"
```

### Combined with Other Filters
```bash
# Biography + billionaire filter
curl "http://localhost:8081/api/v2/entities?has_biography=true&filter_billionaires=true"

# Biography + entity type
curl "http://localhost:8081/api/v2/entities?has_biography=true&entity_type=person"

# Biography + tag filter
curl "http://localhost:8081/api/v2/entities?has_biography=true&tag=politician"
```

## Test Results

### Statistics (as of implementation)
- **Total entities**: 1,634
- **Entities with biography**: 59
- **Filter accuracy**: 100% (all returned entities have bio data)

### Test Coverage
✅ Basic filter (`has_biography=true`)
✅ No filter (default behavior)
✅ Combined with search filter
✅ Combined with other filters
✅ Pagination support
✅ Total count reflects filtered results

### Example Test
```python
import requests

# Test biography filter
response = requests.get(
    "http://localhost:8081/api/v2/entities",
    params={"has_biography": "true", "limit": 100}
)
data = response.json()

print(f"Total with biography: {data['total']}")
print(f"Entities returned: {len(data['entities'])}")

# Verify all have bio
all_have_bio = all(e.get('bio') for e in data['entities'])
print(f"All have bio: {all_have_bio}")  # Should be True
```

## Frontend Integration

### TypeScript Example
```typescript
// Update API client
interface GetEntitiesParams {
  search?: string;
  entity_type?: string;
  tag?: string;
  source?: string;
  filter_billionaires?: boolean;
  filter_connected?: boolean;
  has_biography?: boolean;  // NEW
  sort_by?: 'documents' | 'connections' | 'name';
  limit?: number;
  offset?: number;
}

// Usage
const entitiesWithBio = await api.getEntities({
  has_biography: true,
  limit: 100
});
```

### React Component Example
```tsx
const EntitiesPage = () => {
  const [showOnlyBiography, setShowOnlyBiography] = useState(false);

  const { data } = useQuery({
    queryKey: ['entities', { has_biography: showOnlyBiography }],
    queryFn: () => api.getEntities({ has_biography: showOnlyBiography })
  });

  return (
    <div>
      <Checkbox
        checked={showOnlyBiography}
        onCheckedChange={setShowOnlyBiography}
      >
        Show only entities with biography
      </Checkbox>

      <EntityGrid entities={data?.entities} />
    </div>
  );
};
```

## Benefits Over Client-Side Filtering

### Reliability
- ✅ Server has direct access to `entity_bios` dictionary
- ✅ No race conditions or stale data
- ✅ Consistent filtering logic across all clients

### Performance
- ✅ Reduced network payload (only relevant entities sent)
- ✅ Correct pagination (total count reflects filtered results)
- ✅ No client-side filtering overhead

### Maintainability
- ✅ Single source of truth for filter logic
- ✅ Easier to debug and test
- ✅ API documentation auto-generated (OpenAPI)

## Migration from Client-Side Filter

### Before (Client-Side)
```typescript
// ❌ Unreliable - depends on bio data being loaded
const filteredEntities = entities.filter(e => e.bio);
```

### After (Server-Side)
```typescript
// ✅ Reliable - server guarantees bio data exists
const { entities } = await api.getEntities({ has_biography: true });
```

## OpenAPI Documentation
The parameter is automatically documented in the OpenAPI schema at:
```
http://localhost:8081/openapi.json
```

**Parameter Schema:**
```json
{
  "name": "has_biography",
  "in": "query",
  "required": false,
  "schema": {
    "type": "boolean",
    "default": false,
    "description": "Only entities with biography"
  }
}
```

## Future Enhancements

### Potential Improvements
1. **Biography Completeness Score**: Filter by biography quality/completeness
2. **Biography Field Filters**: Filter by specific bio fields (e.g., `has_sources=true`)
3. **Biography Freshness**: Filter by when biography was last updated
4. **Cached Counts**: Cache biography count for faster query planning

### Related Endpoints
- `GET /api/v2/entities/{entity_id}`: Get single entity with bio
- `GET /api/v2/entities/{entity_name}/connections`: Entity network
- `GET /api/v2/entities/stats/summary`: Entity statistics

## Troubleshooting

### No Results When Filtering
**Problem**: `has_biography=true` returns 0 results

**Possible Causes:**
1. Biography data not loaded (check `entity_biographies.json` exists)
2. Entity IDs not matching (check ID migration status)
3. Service not initialized (check server logs)

**Debug:**
```bash
# Check biography count
curl "http://localhost:8081/api/v2/entities?limit=1000" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); \
  print(f\"With bio: {sum(1 for e in d['entities'] if e.get('bio'))}\")"
```

### Incorrect Total Count
**Problem**: Total count doesn't match filtered results

**Solution**: Ensure filter is applied before counting:
```python
# ✅ Correct order
entities_list = apply_all_filters(entities_list)
total = len(entities_list)  # Count after filtering
entities_page = entities_list[offset:offset+limit]
```

## Related Documentation
- [Entity ID Migration](ENTITY_ID_MIGRATION_COMPLETE.md)
- [Entity Biography System](ENTITY_BIOGRAPHY_ENHANCEMENT_SYSTEM.md)
- [API Reference](ENTITY_ID_API_REFERENCE.md)
