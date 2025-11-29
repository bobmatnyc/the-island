# Entity ID API Reference

**Quick Summary**: Quick reference for the new entity ID system. .

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- `jeffrey_epstein`
- `ghislaine_maxwell`
- `bill_clinton`
- `donald_trump`
- ID lookup: O(1)

---

Quick reference for the new entity ID system.

---

## Entity ID Format

**Format:** `snake_case` slug
**Pattern:** `^[a-z0-9_]+$`
**Examples:**
- `jeffrey_epstein`
- `ghislaine_maxwell`
- `bill_clinton`
- `donald_trump`

---

## API Endpoints

### v2 Endpoints (Recommended)

#### Get Entity by ID
```
GET /api/v2/entities/{entity_id}
```

**Example:**
```bash
curl http://localhost:8000/api/v2/entities/jeffrey_epstein
```

**Response:**
```json
{
  "id": "jeffrey_epstein",
  "name": "Epstein, Jeffrey",
  "name_variations": ["Epstein, Jeffrey", "Jeffrey Epstein"],
  "flight_count": 1018,
  "connection_count": 191,
  ...
}
```

**Performance:** O(1) - Fastest method

---

### v1 Endpoints (Backward Compatible)

#### Get Entity by Name or ID
```
GET /api/entities/{name_or_id}
```

**Example (by ID):**
```bash
curl http://localhost:8000/api/entities/jeffrey_epstein
```

**Example (by name):**
```bash
curl http://localhost:8000/api/entities/Epstein,%20Jeffrey
```

**Response:** Same as v2, plus deprecation header
```
X-API-Deprecation: Use /api/v2/entities/{entity_id} for better performance
```

**Performance:**
- ID lookup: O(1)
- Name lookup: O(1) via mapping

---

### Utility Endpoints

#### Resolve Name to ID
```
GET /api/entities/resolve/{name}
```

**Example:**
```bash
curl http://localhost:8000/api/entities/resolve/Epstein,%20Jeffrey
```

**Response:**
```json
{
  "name": "Epstein, Jeffrey",
  "entity_id": "jeffrey_epstein",
  "canonical_name": "Epstein, Jeffrey"
}
```

**Use case:** Convert user-entered names to entity IDs

---

#### Batch Resolve Names
```
POST /api/entities/batch/resolve
```

**Request:**
```json
{
  "names": [
    "Epstein, Jeffrey",
    "Maxwell, Ghislaine",
    "Clinton, Bill"
  ]
}
```

**Response:**
```json
{
  "results": {
    "Epstein, Jeffrey": "jeffrey_epstein",
    "Maxwell, Ghislaine": "ghislaine_maxwell"
  },
  "not_found": ["Clinton, Bill"],
  "total_requested": 3,
  "resolved": 2,
  "failed": 1
}
```

**Use case:** Bulk resolution of names (e.g., importing data)

---

## Frontend Migration Guide

### Step 1: Update Entity Routes

**Before (name-based):**
```typescript
// Route: /entities/:name
const name = route.params.name;
fetch(`/api/entities/${name}`);
```

**After (ID-based):**
```typescript
// Route: /entities/:entityId
const entityId = route.params.entityId;
fetch(`/api/v2/entities/${entityId}`);
```

---

### Step 2: Handle User Searches

**Search + Resolve Pattern:**
```typescript
async function searchEntity(searchName: string) {
  // Step 1: Resolve name to ID
  const resolveResponse = await fetch(
    `/api/entities/resolve/${encodeURIComponent(searchName)}`
  );

  if (!resolveResponse.ok) {
    throw new Error(`Entity not found: ${searchName}`);
  }

  const { entity_id } = await resolveResponse.json();

  // Step 2: Navigate using ID
  router.push(`/entities/${entity_id}`);
}
```

---

### Step 3: Update Links

**Before:**
```jsx
<a href={`/entities/${entity.name}`}>
  {entity.name}
</a>
```

**After:**
```jsx
<a href={`/entities/${entity.id}`}>
  {entity.name}
</a>
```

---

### Step 4: Network Graph

**Nodes already use entity IDs:**
```typescript
// Node object
{
  id: "jeffrey_epstein",
  name: "Epstein, Jeffrey",
  connection_count: 191
}

// Edge object
{
  source: "jeffrey_epstein",
  target: "ghislaine_maxwell",
  weight: 18
}
```

**When clicking a node:**
```typescript
function onNodeClick(node) {
  // Use node.id directly (already an entity ID)
  router.push(`/entities/${node.id}`);
}
```

---

## Common Patterns

### Pattern 1: Direct ID Lookup
```typescript
// Fastest method - use when you already have the ID
const entity = await fetch(`/api/v2/entities/${entityId}`)
  .then(r => r.json());
```

### Pattern 2: Name Resolution + Fetch
```typescript
// Use when user provides a name
const { entity_id } = await fetch(`/api/entities/resolve/${name}`)
  .then(r => r.json());

const entity = await fetch(`/api/v2/entities/${entity_id}`)
  .then(r => r.json());
```

### Pattern 3: Batch Operations
```typescript
// Use for bulk operations (e.g., importing, processing lists)
const names = ['Epstein, Jeffrey', 'Maxwell, Ghislaine'];
const { results } = await fetch('/api/entities/batch/resolve', {
  method: 'POST',
  body: JSON.stringify({ names })
}).then(r => r.json());

// results = { "Epstein, Jeffrey": "jeffrey_epstein", ... }
const entityIds = Object.values(results);
```

---

## Error Handling

### 404 Not Found (v2)
```json
{
  "detail": "Entity not found: 'unknown_entity'. Use /api/entities/resolve to find entity ID from name."
}
```

**Action:** Use name resolution or check entity ID spelling

---

### 404 Not Found (resolve)
```json
{
  "detail": "Could not resolve name: 'Unknown Person'. Try canonical name or check spelling."
}
```

**Action:** Try different name variation or use entity search

---

## Performance Comparison

| Method | Performance | Use Case |
|--------|-------------|----------|
| `/api/v2/entities/{id}` | O(1) - 17-20x faster | Direct entity access |
| `/api/entities/{id}` | O(1) | Backward compatibility |
| `/api/entities/{name}` | O(1) via mapping | Legacy name lookups |
| `/api/entities/resolve/{name}` | O(1) mapping | Name-to-ID conversion |
| `/api/entities/batch/resolve` | O(n) where n = names | Bulk resolution |

---

## Migration Checklist

### Frontend Components to Update

- [ ] Entity detail pages (use ID in URL)
- [ ] Entity search (resolve name → ID)
- [ ] Entity links (use `entity.id` not `entity.name`)
- [ ] Network graph (already uses IDs, just verify)
- [ ] Timeline events (update entity references)
- [ ] Flight logs (update passenger links)

### Testing

- [ ] Test entity detail page with ID
- [ ] Test entity search with names
- [ ] Test direct navigation to entity by ID
- [ ] Test entity links in network graph
- [ ] Test entity references in documents
- [ ] Test 404 handling for non-existent IDs

---

## Examples for Common Entities

| Entity Name | Entity ID |
|-------------|-----------|
| Epstein, Jeffrey | `jeffrey_epstein` |
| Maxwell, Ghislaine | `ghislaine_maxwell` |
| Clinton, William | `william_clinton` |
| Trump, Donald | `donald_trump` |
| Prince Andrew | `prince_andrew` |

**Note:** Use the resolve endpoint to find IDs for other entities.

---

## Need Help?

**Check entity ID:**
```bash
curl http://localhost:8000/api/entities/resolve/YOUR_NAME_HERE
```

**List all entities:**
```bash
curl http://localhost:8000/api/entities?limit=100
```

**View API docs:**
```
http://localhost:8000/docs
```

---

**Last Updated:** 2025-11-20
**Version:** 2.0 (Entity ID System)
