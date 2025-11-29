# Epstein Archive Document Explorer - Web Interface

**Quick Summary**: - **Interactive Network Graph** - D3. js force-directed graph showing entity relationships.

**Category**: Developer
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Interactive Network Graph** - D3.js force-directed graph showing entity relationships
- **Entity Search** - Search and filter 1,700+ entities
- **Entity Details** - Comprehensive profiles with connections and document mentions
- **Timeline Visualization** - Interactive timeline with month/year slider
- **Flight Logs** - Searchable flight records with passenger filtering

---

## Features

- **Interactive Network Graph** - D3.js force-directed graph showing entity relationships
- **Entity Search** - Search and filter 1,700+ entities
- **Entity Details** - Comprehensive profiles with connections and document mentions
- **Timeline Visualization** - Interactive timeline with month/year slider
- **Flight Logs** - Searchable flight records with passenger filtering
- **Statistics Dashboard** - Overview of archive contents
- **Document Search** - Full-text search across document archive
- **Real-time Updates** - Live data from FastAPI backend

## Quick Start

1. Start the API server:
```bash
source .venv/bin/activate
python server/app.py
# Backend runs on http://localhost:8000
```

2. Start the React frontend (in new terminal):
```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173
```

3. Open browser:
```bash
open http://localhost:5173
```

## Technologies

### Frontend (Port 5173)
- **React 18** - Component framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI component library
- **React Router v6** - Client-side routing
- **Recharts** - Charts and data visualization
- **D3.js** - Network graph visualization

### Backend (Port 8000)
- **FastAPI** - Python API framework
- **Uvicorn** - ASGI server

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
