# API-First Architecture Migration Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Before**: Business logic in frontend JavaScript (app.js)
- **After**: Business logic in backend services, frontend makes API calls
- **`services/entity_service.py`** - Entity filtering, type detection, stats
- **`services/flight_service.py`** - Flight filtering, route grouping, stats
- **`services/document_service.py`** - Document search, classification

---

## Overview

We've refactored the Epstein Archive to **API-first architecture**:

- **Before**: Business logic in frontend JavaScript (app.js)
- **After**: Business logic in backend services, frontend makes API calls

## Benefits

1. **Cleaner Separation**: UI code is simpler, backend is testable
2. **API Reusability**: Can build mobile app, CLI, other clients
3. **Better Caching**: Backend can cache processed data
4. **Easier Testing**: API endpoints can be unit tested
5. **Performance**: Heavy processing happens server-side
6. **Future-Proof**: Easy to add database layer later

## Architecture

```
┌─────────────────┐
│   Frontend      │ ← Only: Rendering, user interaction, API calls
│   (HTML/JS)     │
└────────┬────────┘
         │ HTTP Requests (JSON)
         ↓
┌─────────────────┐
│   FastAPI       │ ← All business logic, data processing
│   Backend       │
│   /api/v2/*     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Services      │ ← entity_service, flight_service, etc.
│   (Business     │
│    Logic)       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Data Layer    │ ← JSON files, future database
│   (Files/DB)    │
└─────────────────┘
```

## Service Layer

All business logic moved to services:

- **`services/entity_service.py`** - Entity filtering, type detection, stats
- **`services/flight_service.py`** - Flight filtering, route grouping, stats
- **`services/document_service.py`** - Document search, classification
- **`services/network_service.py`** - Graph filtering, path finding, stats

## API Endpoints (v2)

### Entities

```
GET /api/v2/entities?search=Clinton&sort_by=documents&limit=100
GET /api/v2/entities/{entity_name}
GET /api/v2/entities/{entity_name}/connections?max_hops=2
GET /api/v2/entities/stats/summary
```

### Flights

```
GET /api/v2/flights?passenger=Maxwell&limit=100
GET /api/v2/flights/routes
GET /api/v2/flights/passenger/{passenger_name}
GET /api/v2/flights/stats
```

### Documents

```
GET /api/v2/documents/search?q=email&entity=Clinton&limit=20
GET /api/v2/documents/{doc_id}
GET /api/v2/documents/entity/{entity_name}
GET /api/v2/documents/stats
```

### Network

```
GET /api/v2/network/graph?min_connections=5&max_nodes=300
GET /api/v2/network/path?entity_a=Epstein&entity_b=Clinton
GET /api/v2/network/subgraph/{entity_name}?max_hops=2
GET /api/v2/network/stats
```

### Unified Search

```
GET /api/v2/search?q=Clinton&type=entities&limit=50
```

## Frontend API Client

Include the new API client:

```html
<script src="/api-client.js"></script>
```

Then use the API:

```javascript
// Old way (business logic in frontend) ❌
function filterEntities(query) {
    let filtered = allEntities.filter(e => {
        // 100+ lines of filtering logic
        // Type detection
        // Tag matching
        // Source checking
        // etc.
    });
    return filtered;
}

// New way (API call only) ✅
async function filterEntities(query) {
    const result = await API.Entity.getEntities({
        search: query.search,
        entity_type: query.type,
        tag: query.tag,
        source: query.source,
        sort_by: 'documents',
        limit: 100
    });

    return result.entities;
}
```

## Migration Examples

### Example 1: Entity Search

**Before** (app.js):

```javascript
// Complex filtering logic in frontend
function searchEntities(searchTerm) {
    const results = [];

    for (const [name, entity] of Object.entries(entityStats)) {
        // Type detection
        const entityType = detectEntityType(name);
        if (entityType !== filters.type) continue;

        // Text search
        if (!name.toLowerCase().includes(searchTerm.toLowerCase())) continue;

        // Billionaire filter
        if (filters.billionaires && !entity.is_billionaire) continue;

        // Connection filter
        if (filters.connected && entity.connection_count === 0) continue;

        results.push(entity);
    }

    // Sort
    results.sort((a, b) => b.total_documents - a.total_documents);

    return results;
}
```

**After** (using API):

```javascript
// Simple API call
async function searchEntities(searchTerm) {
    const result = await API.Entity.getEntities({
        search: searchTerm,
        entity_type: filters.type,
        filter_billionaires: filters.billionaires,
        filter_connected: filters.connected,
        sort_by: 'documents',
        limit: 100
    });

    return result.entities;
}
```

### Example 2: Network Graph

**Before**:

```javascript
// Build network graph in frontend
function buildNetworkGraph(minConnections) {
    const nodes = networkData.nodes.filter(n => {
        // Generic entity filtering
        if (isGenericEntity(n.name)) return false;

        // Connection filtering
        if (n.connection_count < minConnections) return false;

        return true;
    });

    // Deduplication logic (100+ lines)
    const deduplicated = deduplicateNodes(nodes);

    // Edge filtering
    const edges = filterEdges(deduplicated);

    return { nodes: deduplicated, edges };
}
```

**After**:

```javascript
// Simple API call
async function buildNetworkGraph(minConnections) {
    const result = await API.Network.getNetworkGraph({
        min_connections: minConnections,
        max_nodes: 500,
        deduplicate: true
    });

    return result; // { nodes, edges, metadata }
}
```

### Example 3: Flight Search

**Before**:

```javascript
// Filter flights in frontend
function filterFlights(passengerName, dateRange) {
    const flights = allFlights.filter(f => {
        // Passenger matching
        const hasPassenger = f.passengers.some(p =>
            p.toLowerCase().includes(passengerName.toLowerCase())
        );
        if (!hasPassenger) return false;

        // Date parsing and filtering
        const flightDate = parseDate(f.date);
        if (dateRange.start && flightDate < parseDate(dateRange.start)) return false;
        if (dateRange.end && flightDate > parseDate(dateRange.end)) return false;

        return true;
    });

    // Sort by date
    flights.sort((a, b) => parseDate(a.date) - parseDate(b.date));

    return flights;
}
```

**After**:

```javascript
// Simple API call
async function filterFlights(passengerName, dateRange) {
    const result = await API.Flight.getFlights({
        passenger: passengerName,
        start_date: dateRange.start,
        end_date: dateRange.end,
        limit: 100
    });

    return result.flights;
}
```

## Backward Compatibility

Old API endpoints (`/api/*`) still work:

```javascript
// Legacy endpoints still available
const stats = await LegacyAPI.getStats();
const bios = await LegacyAPI.getEntityBiographies();
const tags = await LegacyAPI.getEntityTags();
const network = await LegacyAPI.getNetwork({ max_nodes: 500 });
```

## Testing

### Test API Endpoints

```bash
# Test entity search
curl "http://localhost:8000/api/v2/entities?search=Clinton&limit=10"

# Test flight routes
curl "http://localhost:8000/api/v2/flights/routes"

# Test document search
curl "http://localhost:8000/api/v2/documents/search?entity=Maxwell&limit=20"

# Test network graph
curl "http://localhost:8000/api/v2/network/graph?min_connections=5&max_nodes=300"

# Test unified search
curl "http://localhost:8000/api/v2/search?q=Clinton&limit=50"
```

### Test Frontend Integration

```javascript
// Open browser console on http://localhost:8000

// Test entity API
const entities = await API.Entity.getEntities({ search: 'Clinton', limit: 10 });
console.log(entities);

// Test flight API
const routes = await API.Flight.getFlightRoutes();
console.log(routes);

// Test document API
const docs = await API.Document.searchDocuments({ entity: 'Maxwell', limit: 20 });
console.log(docs);

// Test network API
const network = await API.Network.getNetworkGraph({ min_connections: 5 });
console.log(network);

// Test unified search
const results = await API.Search.search('Clinton', { limit: 50 });
console.log(results);
```

## Refactoring Checklist

For each feature in app.js:

- [ ] Identify business logic function (filtering, sorting, calculations)
- [ ] Find corresponding API endpoint in `/api/v2/*`
- [ ] Replace logic with API call using `API.Entity.*`, `API.Flight.*`, etc.
- [ ] Remove old business logic code
- [ ] Test with API client in browser console
- [ ] Verify UI still works correctly

## Code Reduction

Expected reduction in frontend code:

- **Before**: ~3,800 lines in app.js (business logic + UI)
- **After**: ~1,500 lines in app.js (UI only)
- **Reduction**: ~60% fewer lines, cleaner code

All business logic moved to testable backend services.

## Next Steps

1. **Test all endpoints**: Use curl or browser console
2. **Gradual migration**: Update one feature at a time
3. **Remove old code**: Delete unused business logic functions
4. **Add tests**: Write unit tests for backend services
5. **Monitor performance**: Check API response times

## Support

- API documentation: http://localhost:8000/docs
- Service layer code: `/server/services/`
- API routes: `/server/api_routes.py`
- Frontend client: `/server/web/api-client.js`

---

**Success Criteria**:
- All data processing in backend services ✅
- Frontend makes API calls for all operations ✅
- No business logic in app.js (only rendering) 🔄
- All endpoints return JSON with error handling ✅
- Frontend is <50% of original size 🔄
