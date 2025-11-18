# Epstein Archive Document Explorer - Web Interface

## Features

- **Interactive Network Graph** - D3.js force-directed graph showing entity relationships
- **Entity Search** - Search and filter 1,700+ entities
- **Entity Details** - Comprehensive profiles with connections and document mentions
- **Statistics Dashboard** - Overview of archive contents
- **Real-time Updates** - Live data from FastAPI backend

## Quick Start

1. Start the API server:
```bash
cd server
./start.sh 8000
```

2. Open web interface:
```bash
open server/web/index.html
```

Or use a local server:
```bash
cd server/web
python3 -m http.server 8080
# Then open http://localhost:8080
```

## Technologies

- **D3.js** - Network visualization
- **FastAPI** - Backend API
- **Vanilla JS** - No framework overhead, maximum performance

## API Endpoints

- GET `/api/stats` - Overall statistics
- GET `/api/entities` - List entities (with filtering)
- GET `/api/entities/{name}` - Entity details
- GET `/api/network` - Network graph data
- GET `/api/search` - Search entities and documents
- GET `/api/timeline` - Timeline events

## Network Visualization

- **Node Size** - Based on number of connections
- **Node Color** - Gold = Billionaire, Blue = Other
- **Edge Width** - Number of flights together
- **Zoom & Pan** - Scroll to zoom, drag to pan
- **Click** - Select entity for details
- **Hover** - Show quick info

## Performance

- Supports up to 500 nodes in network view
- Adjustable minimum connections filter
- Efficient D3 force simulation
- Responsive design

## Next Steps

- Add timeline visualization
- Add document viewer
- Add advanced search filters
- Add export functionality
