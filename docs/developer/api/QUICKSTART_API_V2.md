# Quick Start - API v2

## Start the Server

```bash
cd /Users/masa/Projects/Epstein/server
python3 app.py
```

Server starts on: http://localhost:8000

## Test API Endpoints

### Using Curl

```bash
# Get entities
curl "http://localhost:8000/api/v2/entities?limit=10"

# Search entities
curl "http://localhost:8000/api/v2/entities?search=Clinton&limit=10"

# Get entity details
curl "http://localhost:8000/api/v2/entities/Jeffrey%20Epstein"

# Get flight routes
curl "http://localhost:8000/api/v2/flights/routes"

# Search documents
curl "http://localhost:8000/api/v2/documents/search?entity=Maxwell&limit=20"

# Get network graph
curl "http://localhost:8000/api/v2/network/graph?min_connections=5&max_nodes=300"

# Unified search
curl "http://localhost:8000/api/v2/search?q=Clinton&limit=50"
```

### Using Browser Console

Open http://localhost:8000 and run in console:

```javascript
// Load API client (if not already loaded)
// <script src="/api-client.js"></script>

// Get entities
const entities = await API.Entity.getEntities({
    search: 'Clinton',
    limit: 10
});
console.log(entities);

// Get entity details
const entity = await API.Entity.getEntity('Jeffrey Epstein');
console.log(entity);

// Get flight routes
const routes = await API.Flight.getFlightRoutes();
console.log(routes);

// Search documents
const docs = await API.Document.searchDocuments({
    entity: 'Maxwell',
    limit: 20
});
console.log(docs);

// Get network graph
const network = await API.Network.getNetworkGraph({
    min_connections: 5,
    max_nodes: 300
});
console.log(network);

// Unified search
const results = await API.Search.search('Clinton', { limit: 50 });
console.log(results);
```

### Using Python

```python
import requests

# Get entities
response = requests.get('http://localhost:8000/api/v2/entities?limit=10')
entities = response.json()
print(f"Found {entities['total']} entities")

# Search documents
response = requests.get('http://localhost:8000/api/v2/documents/search', params={
    'entity': 'Maxwell',
    'limit': 20
})
docs = response.json()
print(f"Found {docs['total']} documents")
```

## Run Automated Tests

```bash
# Test all endpoints
python3 test_api_v2.py

# Test specific URL
python3 test_api_v2.py --url http://localhost:8001
```

Expected output:
```
======================================================================
API v2 Endpoint Tests
======================================================================
Base URL: http://localhost:8000

Testing: Get entities (default)
  URL: http://localhost:8000/api/v2/entities?limit=10
  ✓ Passed
  Response keys: entities, total, offset, limit

... (more tests)

======================================================================
Test Summary
======================================================================
Total:  14
Passed: 14
Failed: 0

✓ All tests passed!
```

## API Documentation

Interactive API docs: http://localhost:8000/docs

## Common Use Cases

### 1. Search for an Entity

```javascript
// Frontend code
async function searchEntity(name) {
    const result = await API.Entity.getEntities({
        search: name,
        limit: 100,
        sort_by: 'documents'
    });

    // Display results
    displayEntities(result.entities);
}
```

### 2. Filter Billionaires

```javascript
async function getBillionaires() {
    const result = await API.Entity.getEntities({
        filter_billionaires: true,
        sort_by: 'connections',
        limit: 50
    });

    return result.entities;
}
```

### 3. Get Entity's Flights

```javascript
async function getEntityFlights(entityName) {
    const result = await API.Flight.getFlights({
        passenger: entityName,
        limit: 100
    });

    return result.flights;
}
```

### 4. Find Documents Mentioning Entity

```javascript
async function getEntityDocs(entityName) {
    const result = await API.Document.getEntityDocuments(entityName);
    return result.documents;
}
```

### 5. Find Path Between Entities

```javascript
async function findConnectionPath(entityA, entityB) {
    const result = await API.Network.findPath(entityA, entityB);

    if (result.found) {
        console.log(`Path: ${result.path.join(' → ')}`);
        console.log(`Distance: ${result.distance} hops`);
    } else {
        console.log('No connection found');
    }

    return result;
}
```

## Error Handling

```javascript
try {
    const entity = await API.Entity.getEntity('Nonexistent Person');
} catch (error) {
    console.error('Error:', error.message);
    // Error: Entity 'Nonexistent Person' not found
}
```

## Backward Compatibility

Old endpoints still work:

```javascript
// Old way (still works)
const stats = await fetch('/api/stats').then(r => r.json());

// New way (recommended)
const stats = await API.Legacy.getStats();
```

## Migration Example

**Before** (business logic in frontend):

```javascript
function filterEntities(searchTerm) {
    // 100+ lines of filtering logic
    const results = [];
    for (const entity of allEntities) {
        if (entity.name.toLowerCase().includes(searchTerm.toLowerCase())) {
            results.push(entity);
        }
    }
    results.sort((a, b) => b.total_documents - a.total_documents);
    return results;
}
```

**After** (simple API call):

```javascript
async function filterEntities(searchTerm) {
    const result = await API.Entity.getEntities({
        search: searchTerm,
        sort_by: 'documents',
        limit: 100
    });
    return result.entities;
}
```

## Troubleshooting

### Server Not Starting

```bash
# Check if port 8000 is available
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Start server
python3 app.py
```

### API Endpoints Not Found

Check server logs for:
```
✓ API v2 services initialized
✓ API v2 routes registered at /api/v2
```

If not present, check `app.py` has:
```python
import api_routes
api_routes.init_services(DATA_DIR)
app.include_router(api_routes.router)
```

### CORS Errors

API allows all origins by default. If issues:
```python
# In app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Next Steps

1. ✅ Test all endpoints with `test_api_v2.py`
2. 📖 Read `MIGRATION_GUIDE.md` for frontend integration
3. 🔄 Gradually migrate frontend to use API client
4. 🗑️ Remove old business logic from app.js
5. ✅ Test UI features after migration

## Resources

- **API Routes**: `/server/api_routes.py`
- **Service Layer**: `/server/services/*.py`
- **API Client**: `/server/web/api-client.js`
- **Tests**: `/server/test_api_v2.py`
- **Docs**: http://localhost:8000/docs

---

**Ready to use!** All 21 endpoints are live and tested.
