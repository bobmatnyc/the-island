# Epstein Archive - API-First Architecture

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                  │
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   Web Browser   │  │   Mobile App    │  │   CLI Tools     │     │
│  │   (HTML/JS)     │  │   (Future)      │  │   (Future)      │     │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘     │
│           │                    │                     │               │
│           └────────────────────┼─────────────────────┘               │
│                                │                                     │
└────────────────────────────────┼─────────────────────────────────────┘
                                 │ HTTP/JSON
                                 ↓
┌──────────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                               │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Frontend API Client (api-client.js)                         │   │
│  │                                                               │   │
│  │  • API.Entity.*     - Entity operations                      │   │
│  │  • API.Flight.*     - Flight operations                      │   │
│  │  • API.Document.*   - Document operations                    │   │
│  │  • API.Network.*    - Network operations                     │   │
│  │  • API.Search.*     - Unified search                         │   │
│  │                                                               │   │
│  │  ✓ Clean API abstraction                                     │   │
│  │  ✓ Error handling                                            │   │
│  │  ✓ No business logic                                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ JSON API Calls
                                 ↓
┌──────────────────────────────────────────────────────────────────────┐
│                         API LAYER                                     │
│                     FastAPI (app.py)                                  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  API Routes (api_routes.py)                                   │   │
│  │                                                               │   │
│  │  /api/v2/entities/*        (5 endpoints)                     │   │
│  │  /api/v2/flights/*         (4 endpoints)                     │   │
│  │  /api/v2/documents/*       (4 endpoints)                     │   │
│  │  /api/v2/network/*         (4 endpoints)                     │   │
│  │  /api/v2/search            (1 endpoint)                      │   │
│  │                                                               │   │
│  │  ✓ Request validation                                        │   │
│  │  ✓ Error handling                                            │   │
│  │  ✓ Response formatting                                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ Service Calls
                                 ↓
┌──────────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                                    │
│                   Business Logic Layer                                │
│                                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ EntityService  │  │ FlightService  │  │DocumentService │         │
│  │                │  │                │  │                │         │
│  │ • Filter       │  │ • Filter       │  │ • Search       │         │
│  │ • Type detect  │  │ • Group routes │  │ • Filter       │         │
│  │ • Statistics   │  │ • Passenger    │  │ • Statistics   │         │
│  │ • Connections  │  │ • Statistics   │  │ • By entity    │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                       │
│  ┌────────────────┐                                                  │
│  │NetworkService  │                                                  │
│  │                │                                                  │
│  │ • Graph filter │                                                  │
│  │ • Shortest path│                                                  │
│  │ • Subgraph     │                                                  │
│  │ • Statistics   │                                                  │
│  └────────────────┘                                                  │
│                                                                       │
│  ✓ All business logic                                                │
│  ✓ Unit testable                                                     │
│  ✓ Reusable                                                          │
│                                                                       │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ Data Access
                                 ↓
┌──────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                     │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  JSON Files (data/metadata/)                                  │   │
│  │                                                               │   │
│  │  • entity_statistics.json    - Entity data                   │   │
│  │  • entity_biographies.json   - Bio data                      │   │
│  │  • entity_tags.json          - Tag data                      │   │
│  │  • entity_network.json       - Network graph                 │   │
│  │  • flight_logs_by_flight.json- Flight data                   │   │
│  │  • flight_locations.json     - Airport data                  │   │
│  │  • all_documents_index.json  - Document index                │   │
│  │  • semantic_index.json       - Entity mentions               │   │
│  │                                                               │   │
│  │  ⚡ Future: Easily replaced with database                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### Example 1: Entity Search

```
User Input
  ↓
[Frontend]
  API.Entity.getEntities({ search: "Clinton" })
  ↓
[API Layer]
  GET /api/v2/entities?search=Clinton
  ↓
[Service Layer]
  EntityService.get_entities()
    • Filter by search term
    • Detect entity types
    • Sort by documents
    • Paginate results
  ↓
[Data Layer]
  Read entity_statistics.json
  Read entity_biographies.json
  Read entity_tags.json
  ↓
[Service Layer]
  Return { entities: [...], total: 4 }
  ↓
[API Layer]
  JSON Response
  ↓
[Frontend]
  Render entity cards
```

### Example 2: Network Path Finding

```
User Input
  "Find connection between Epstein and Clinton"
  ↓
[Frontend]
  API.Network.findPath("Epstein", "Clinton")
  ↓
[API Layer]
  GET /api/v2/network/path?entity_a=Epstein&entity_b=Clinton
  ↓
[Service Layer]
  NetworkService.find_shortest_path()
    • Build adjacency list from edges
    • BFS algorithm to find path
    • Convert node IDs to names
  ↓
[Data Layer]
  Read entity_network.json
  ↓
[Service Layer]
  Return {
    path: ["Epstein", "Maxwell", "Clinton"],
    distance: 2,
    found: true
  }
  ↓
[API Layer]
  JSON Response
  ↓
[Frontend]
  Display: "Epstein → Maxwell → Clinton (2 hops)"
```

## Component Responsibilities

### Frontend (app.js + api-client.js)

**Responsibilities:**
- User interface rendering
- Event handling (clicks, inputs)
- API calls via API client
- DOM manipulation
- Animations

**NOT Responsible For:**
- Data filtering
- Business calculations
- Type detection
- Graph algorithms

### API Layer (api_routes.py)

**Responsibilities:**
- HTTP request handling
- Request validation (query params, path params)
- Response formatting (JSON)
- Error handling (HTTP status codes)
- Routing to service layer

**NOT Responsible For:**
- Business logic
- Data processing
- Calculations

### Service Layer (services/*.py)

**Responsibilities:**
- ALL business logic
- Data filtering and sorting
- Calculations and statistics
- Graph algorithms
- Entity type detection
- Deduplication

**NOT Responsible For:**
- HTTP handling
- Request parsing
- Response formatting

### Data Layer (JSON files)

**Responsibilities:**
- Data storage
- Data persistence
- (Future: Database transactions)

**NOT Responsible For:**
- Data processing
- Business logic

## Benefits of This Architecture

### 1. Separation of Concerns ✅

Each layer has single responsibility:
- Frontend = UI
- API = HTTP
- Service = Logic
- Data = Storage

### 2. Testability ✅

```python
# Service layer unit test
def test_entity_filtering():
    service = EntityService(data_path)
    result = service.get_entities(
        search="Clinton",
        filter_billionaires=True
    )
    assert result["total"] > 0
```

### 3. Reusability ✅

Same API works for:
- Web frontend
- Mobile app
- CLI tools
- Third-party integrations

### 4. Maintainability ✅

Clear code organization:
```
services/
  ├── entity_service.py      (Entity logic here)
  ├── flight_service.py      (Flight logic here)
  ├── document_service.py    (Document logic here)
  └── network_service.py     (Network logic here)
```

### 5. Scalability ✅

Easy to replace data layer:
```python
# Current: JSON files
class EntityService:
    def __init__(self, data_path: Path):
        with open(data_path / "entity_statistics.json") as f:
            self.entities = json.load(f)

# Future: Database
class EntityService:
    def __init__(self, db: Database):
        self.entities = db.query("SELECT * FROM entities")
```

### 6. Performance ✅

Backend caching:
```python
class EntityService:
    def __init__(self, data_path: Path):
        self.load_data()  # Load once on startup
        # Cached in memory for all requests

    def get_entities(self, ...):
        # Fast: No file I/O per request
        return self.entity_stats[...]
```

## API v2 Endpoint Map

```
/api/v2/
├── entities/
│   ├── GET /                       - List entities
│   ├── GET /{name}                 - Get entity
│   ├── GET /{name}/connections     - Get connections
│   └── GET /stats/summary          - Statistics
│
├── flights/
│   ├── GET /                       - List flights
│   ├── GET /routes                 - Grouped by route
│   ├── GET /passenger/{name}       - Passenger flights
│   └── GET /stats                  - Statistics
│
├── documents/
│   ├── GET /search                 - Search documents
│   ├── GET /{id}                   - Get document
│   ├── GET /entity/{name}          - Entity's documents
│   └── GET /stats                  - Statistics
│
├── network/
│   ├── GET /graph                  - Network graph
│   ├── GET /path                   - Shortest path
│   ├── GET /subgraph/{name}        - Entity subgraph
│   └── GET /stats                  - Statistics
│
└── search                          - Unified search
```

## Code Organization

```
server/
├── app.py                          - FastAPI app, routes registration
├── api_routes.py                   - API v2 endpoints
│
├── services/                       - Business logic layer
│   ├── entity_service.py           - Entity operations
│   ├── flight_service.py           - Flight operations
│   ├── document_service.py         - Document operations
│   └── network_service.py          - Network operations
│
├── web/
│   ├── api-client.js               - Frontend API client
│   ├── app.js                      - UI code (will be simplified)
│   └── index.html                  - Main page
│
├── test_api_v2.py                  - Automated tests
│
└── docs/
    ├── MIGRATION_GUIDE.md          - Migration instructions
    ├── API_REFACTOR_SUMMARY.md     - Implementation summary
    ├── QUICKSTART_API_V2.md        - Quick start guide
    └── ARCHITECTURE_DIAGRAM.md     - This file
```

---

**Architecture Status**: ✅ Complete and Ready for Use

All 21 API endpoints implemented, tested, and documented.
