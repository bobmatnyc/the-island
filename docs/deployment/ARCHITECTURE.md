# System Architecture

**Quick Summary**: **Epstein Document Archive** - Development and deployment architecture overview. .

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- [System Overview](#system-overview)
- [Port Architecture](#port-architecture)
- [Service Dependencies](#service-dependencies)
- [Data Flow](#data-flow)
- [Ngrok Tunnel Architecture](#ngrok-tunnel-architecture)

---

**Epstein Document Archive** - Development and deployment architecture overview.

This document provides visual representations of the system architecture, data flow, port configuration, and service dependencies.

---

## Table of Contents

- [System Overview](#system-overview)
- [Port Architecture](#port-architecture)
- [Service Dependencies](#service-dependencies)
- [Data Flow](#data-flow)
- [Ngrok Tunnel Architecture](#ngrok-tunnel-architecture)
- [Development Environment](#development-environment)
- [Production Architecture](#production-architecture)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EPSTEIN DOCUMENT ARCHIVE                        │
│                                                                     │
│  ┌──────────────────┐         ┌──────────────────┐                │
│  │                  │         │                  │                │
│  │    Frontend      │────────▶│     Backend      │                │
│  │   (React+Vite)   │  HTTP   │   (FastAPI)      │                │
│  │   Port: 5173     │         │   Port: 8081     │                │
│  │                  │         │                  │                │
│  └──────────────────┘         └──────────────────┘                │
│           │                            │                           │
│           │                            │                           │
│           ▼                            ▼                           │
│  ┌──────────────────┐         ┌──────────────────┐                │
│  │   Browser UI     │         │   Data Storage   │                │
│  │  (localhost:5173)│         │  - JSON Files    │                │
│  └──────────────────┘         │  - Embeddings    │                │
│                                │  - Metadata      │                │
│                                └──────────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Port Architecture

### Local Development Setup

```
┌────────────────────────────────────────────────────────────────┐
│                        LOCAL MACHINE                           │
│                                                                │
│  User's Browser                                                │
│       │                                                        │
│       │                                                        │
│       ▼                                                        │
│  ┌─────────────────────────────────────┐                      │
│  │   Frontend Dev Server               │                      │
│  │   http://localhost:5173             │                      │
│  │   - Vite HMR enabled                │                      │
│  │   - Hot module reloading            │                      │
│  │   - Source maps                     │                      │
│  └─────────────────────────────────────┘                      │
│       │                                                        │
│       │ API Requests                                           │
│       │ (VITE_API_BASE_URL)                                   │
│       ▼                                                        │
│  ┌─────────────────────────────────────┐                      │
│  │   Backend API Server                │                      │
│  │   http://localhost:8081             │                      │
│  │   - FastAPI + Uvicorn               │                      │
│  │   - Auto-reload enabled             │                      │
│  │   - CORS: allow all origins         │                      │
│  └─────────────────────────────────────┘                      │
│       │                                                        │
│       │ File I/O                                               │
│       ▼                                                        │
│  ┌─────────────────────────────────────┐                      │
│  │   Data Directory                    │                      │
│  │   /data/                            │                      │
│  │   - entities/                       │                      │
│  │   - documents/                      │                      │
│  │   - metadata/                       │                      │
│  └─────────────────────────────────────┘                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘

Port Assignments:
  Frontend:  5173  (Vite default)
  Backend:   8081  (Project standard)
```

---

### Ngrok Tunnel Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         REMOTE USER                                  │
│                                                                      │
│  ┌────────────────────────────────────┐                             │
│  │   Browser (any device)             │                             │
│  │   Mobile, Tablet, Desktop          │                             │
│  └────────────────────────────────────┘                             │
│               │                                                      │
│               │ HTTPS                                                │
│               ▼                                                      │
└───────────────┼──────────────────────────────────────────────────────┘
                │
                │ Internet
                │
┌───────────────▼──────────────────────────────────────────────────────┐
│                         NGROK CLOUD                                  │
│                                                                      │
│  ┌────────────────────────────────────┐                             │
│  │   Ngrok Edge Network               │                             │
│  │   https://the-island.ngrok.app     │                             │
│  │   - SSL Termination                │                             │
│  │   - DDoS Protection                │                             │
│  │   - Load Balancing                 │                             │
│  └────────────────────────────────────┘                             │
│               │                                                      │
│               │ Secure Tunnel                                        │
│               ▼                                                      │
└───────────────┼──────────────────────────────────────────────────────┘
                │
                │ Encrypted Connection
                │
┌───────────────▼──────────────────────────────────────────────────────┐
│                         LOCAL MACHINE                                │
│                                                                      │
│  ┌────────────────────────────────────┐                             │
│  │   Ngrok Client                     │                             │
│  │   localhost:4040 (dashboard)       │                             │
│  └────────────────────────────────────┘                             │
│               │                                                      │
│               │ Forward to backend                                   │
│               ▼                                                      │
│  ┌────────────────────────────────────┐                             │
│  │   Backend API                      │                             │
│  │   localhost:8081                   │                             │
│  └────────────────────────────────────┘                             │
│               │                                                      │
│  ┌────────────────────────────────────┐                             │
│  │   Frontend Dev Server              │                             │
│  │   localhost:5173                   │                             │
│  │   (configured to use ngrok URL)    │                             │
│  └────────────────────────────────────┘                             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

Data Flow:
  1. Remote user visits https://the-island.ngrok.app
  2. Ngrok cloud routes to local ngrok client
  3. Ngrok client forwards to localhost:8081
  4. Backend API responds
  5. Response travels back through tunnel
```

---

## Service Dependencies

### Startup Order

```
┌─────────────────────────────────────────────────────────────────┐
│                     STARTUP SEQUENCE                            │
└─────────────────────────────────────────────────────────────────┘

Step 1: Prerequisites
┌────────────────────────────────────┐
│  Python Virtual Environment        │
│  - .venv/ directory                │
│  - pip dependencies installed      │
│  - FastAPI, Uvicorn, etc.          │
└────────────────────────────────────┘
         │
         ▼
Step 2: Backend
┌────────────────────────────────────┐
│  Backend API Server (Port 8081)    │
│  - Load configuration              │
│  - Initialize data structures      │
│  - Start Uvicorn server            │
│  - Health check endpoint active    │
└────────────────────────────────────┘
         │
         ▼
Step 3: Frontend
┌────────────────────────────────────┐
│  Frontend Dev Server (Port 5173)   │
│  - Load .env configuration         │
│  - Initialize Vite                 │
│  - Compile React components        │
│  - Start dev server                │
└────────────────────────────────────┘
         │
         ▼
Step 4: Ngrok (Optional)
┌────────────────────────────────────┐
│  Ngrok Tunnel                      │
│  - Establish tunnel to 8081        │
│  - Generate public URL             │
│  - Update frontend .env            │
│  - Restart frontend (reload .env)  │
└────────────────────────────────────┘
```

### Dependency Graph

```
┌──────────────────────────────────────────────────────────────┐
│                    DEPENDENCY GRAPH                          │
└──────────────────────────────────────────────────────────────┘

Python Virtual Environment (.venv)
    │
    ├─▶ Backend API
    │       │
    │       ├─▶ Data Files (data/)
    │       │       ├─▶ entities/
    │       │       ├─▶ documents/
    │       │       └─▶ metadata/
    │       │
    │       └─▶ Health Endpoint (/health)
    │
    └─▶ [Optional] Ngrok Client
            │
            └─▶ Ngrok Tunnel
                    │
                    └─▶ Public URL

Node.js & NPM (frontend)
    │
    └─▶ Frontend Dev Server
            │
            ├─▶ Environment Config (.env)
            │       └─▶ VITE_API_BASE_URL
            │
            └─▶ Backend API (via HTTP)
```

---

## Data Flow

### Request/Response Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW DIAGRAM                           │
└────────────────────────────────────────────────────────────────────┘

User Action (Browser)
    │
    │ 1. User clicks "View Entities"
    ▼
┌─────────────────────────┐
│  Frontend (React)       │
│  - EntityList component │
│  - useEffect hook       │
└─────────────────────────┘
    │
    │ 2. HTTP GET /api/entities
    ▼
┌─────────────────────────┐
│  Backend (FastAPI)      │
│  - Route handler        │
│  - Validation           │
└─────────────────────────┘
    │
    │ 3. Read from disk
    ▼
┌─────────────────────────┐
│  Data Storage           │
│  - data/entities/       │
│  - JSON files           │
└─────────────────────────┘
    │
    │ 4. Return data
    ▼
┌─────────────────────────┐
│  Backend Response       │
│  - JSON payload         │
│  - Status: 200          │
└─────────────────────────┘
    │
    │ 5. Parse & render
    ▼
┌─────────────────────────┐
│  Frontend Display       │
│  - Entity cards         │
│  - Interactive UI       │
└─────────────────────────┘
    │
    │ 6. Rendered page
    ▼
User sees results
```

### API Communication Flow

```
Frontend                 Backend                  Data
  │                         │                       │
  │ GET /api/entities       │                       │
  ├────────────────────────▶│                       │
  │                         │ Read entities.json    │
  │                         ├──────────────────────▶│
  │                         │ Return JSON data      │
  │                         │◀──────────────────────┤
  │ Response: entity[]      │                       │
  │◀────────────────────────┤                       │
  │                         │                       │
  │ GET /api/flights        │                       │
  ├────────────────────────▶│                       │
  │                         │ Read flights.json     │
  │                         ├──────────────────────▶│
  │                         │ Return JSON data      │
  │                         │◀──────────────────────┤
  │ Response: flight[]      │                       │
  │◀────────────────────────┤                       │
  │                         │                       │
  │ POST /api/search        │                       │
  ├────────────────────────▶│                       │
  │                         │ Query embeddings      │
  │                         ├──────────────────────▶│
  │                         │ Return results        │
  │                         │◀──────────────────────┤
  │ Response: results[]     │                       │
  │◀────────────────────────┤                       │
```

---

## Development Environment

### Full Development Stack

```
┌────────────────────────────────────────────────────────────────┐
│                  DEVELOPMENT ENVIRONMENT                       │
└────────────────────────────────────────────────────────────────┘

Developer's Machine
    │
    ├─▶ Terminal 1: Backend
    │   └─▶ ./scripts/dev-backend.sh start
    │       ├─▶ Activate .venv
    │       ├─▶ Start uvicorn on port 8081
    │       ├─▶ Enable auto-reload
    │       └─▶ Tail logs/backend.log
    │
    ├─▶ Terminal 2: Frontend
    │   └─▶ ./scripts/dev-frontend.sh start
    │       ├─▶ Start Vite on port 5173
    │       ├─▶ Enable HMR
    │       └─▶ Tail logs/frontend.log
    │
    ├─▶ Terminal 3: Monitoring
    │   └─▶ ./scripts/dev-status.sh
    │       ├─▶ Check backend health
    │       ├─▶ Check frontend status
    │       └─▶ Display service info
    │
    └─▶ Browser
        ├─▶ http://localhost:5173 (Frontend)
        ├─▶ http://localhost:8081/docs (API Docs)
        └─▶ DevTools for debugging
```

### Development Workflow

```
┌────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT WORKFLOW                        │
└────────────────────────────────────────────────────────────────┘

1. Start Environment
   ./scripts/dev-start.sh
        │
        ├─▶ Backend starts on 8081
        ├─▶ Frontend starts on 5173
        └─▶ Health checks pass

2. Make Code Changes
   Edit files in:
        │
        ├─▶ server/ (Backend)
        │   └─▶ Auto-reload triggered
        │
        └─▶ frontend/src/ (Frontend)
            └─▶ HMR updates browser

3. Test Changes
   Browser automatically updates
        │
        ├─▶ View in UI
        ├─▶ Check console
        └─▶ Test functionality

4. Check Status
   ./scripts/dev-status.sh
        │
        └─▶ Verify services healthy

5. Stop Environment
   ./scripts/dev-stop.sh
        │
        ├─▶ Graceful backend shutdown
        └─▶ Stop frontend server
```

---

## Production Architecture

### Production Deployment (Future)

```
┌────────────────────────────────────────────────────────────────┐
│                   PRODUCTION ARCHITECTURE                      │
└────────────────────────────────────────────────────────────────┘

Internet
    │
    │ HTTPS
    ▼
┌─────────────────────────┐
│  Load Balancer          │
│  - SSL Termination      │
│  - Health Checks        │
└─────────────────────────┘
    │
    ├──────────────┬──────────────┐
    │              │              │
    ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Backend │  │ Backend │  │ Backend │
│  Node 1 │  │  Node 2 │  │  Node 3 │
│ Port:80 │  │ Port:80 │  │ Port:80 │
└─────────┘  └─────────┘  └─────────┘
    │              │              │
    └──────────────┴──────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  Shared Storage     │
         │  - Documents        │
         │  - Metadata         │
         │  - Embeddings       │
         └─────────────────────┘

Frontend:
  - Built static files served by backend
  - Or separate CDN/static hosting
```

---

## Network Ports Summary

### Port Allocation Table

| Service | Port | Protocol | Purpose | Access |
|---------|------|----------|---------|--------|
| **Frontend Dev** | 5173 | HTTP | Vite development server | Local only |
| **Backend API** | 8081 | HTTP | FastAPI server | Local or via ngrok |
| **Ngrok Dashboard** | 4040 | HTTP | Ngrok web interface | Local only |
| **Frontend Preview** | 4173 | HTTP | Production build preview | Local only |

### Port Conflict Resolution

```
Port Conflict Detected
    │
    ▼
Check what's using port
    │ lsof -i :8081
    │
    ▼
┌─────────────────────────┐
│ Is it our service?      │
└─────────────────────────┘
    │              │
    Yes            No
    │              │
    ▼              ▼
Stop it        Kill process
properly       (manual)
    │              │
    └──────┬───────┘
           │
           ▼
    Start service
    on clean port
```

---

## Environment Variables Flow

### Configuration Hierarchy

```
┌────────────────────────────────────────────────────────────────┐
│              ENVIRONMENT VARIABLE FLOW                         │
└────────────────────────────────────────────────────────────────┘

Frontend Configuration:
    .env.example (template)
        │
        ▼
    .env (active config)
        │
        ├─▶ VITE_API_BASE_URL
        │       │
        │       ├─▶ http://localhost:8081 (local)
        │       └─▶ https://the-island.ngrok.app (remote)
        │
        ▼
    src/lib/api.ts
        │
        └─▶ import.meta.env.VITE_API_BASE_URL

Backend Configuration:
    Environment variables
        │
        ├─▶ PORT (default: 8081)
        ├─▶ HOST (default: 0.0.0.0)
        ├─▶ LOG_LEVEL (default: INFO)
        └─▶ CORS_ORIGINS (default: *)
        │
        ▼
    server/app.py
        │
        └─▶ Application startup
```

---

## Process Management

### Service Lifecycle

```
┌────────────────────────────────────────────────────────────────┐
│                     SERVICE LIFECYCLE                          │
└────────────────────────────────────────────────────────────────┘

START
    │
    ▼
┌──────────────────────┐
│ Prerequisites Check  │
│ - Virtual env exists │
│ - Dependencies OK    │
│ - Ports available    │
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│ Start Process        │
│ - Run in background  │
│ - Save PID           │
│ - Redirect logs      │
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│ Health Check         │
│ - Wait for ready     │
│ - Verify endpoint    │
│ - Confirm working    │
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│ RUNNING              │
│ - Process active     │
│ - Handling requests  │
│ - Writing logs       │
└──────────────────────┘
    │
    ▼
STOP (Ctrl+C or stop script)
    │
    ▼
┌──────────────────────┐
│ Graceful Shutdown    │
│ - SIGTERM sent       │
│ - Wait 5 seconds     │
│ - SIGKILL if needed  │
└──────────────────────┘
    │
    ▼
┌──────────────────────┐
│ Cleanup              │
│ - Remove PID file    │
│ - Close log handles  │
│ - Free ports         │
└──────────────────────┘
    │
    ▼
STOPPED
```

---

## Logging Architecture

### Log Flow

```
Application Logs
    │
    ├─▶ Backend (Python/FastAPI)
    │   │
    │   ├─▶ stdout/stderr
    │   │       │
    │   │       └─▶ logs/backend.log
    │   │
    │   └─▶ uvicorn access logs
    │           │
    │           └─▶ logs/backend.log
    │
    └─▶ Frontend (Vite/React)
        │
        ├─▶ stdout/stderr
        │       │
        │       └─▶ logs/frontend.log
        │
        └─▶ Browser console
                │
                └─▶ (not captured)

Log Access:
    ./scripts/dev-logs.sh
        │
        ├─▶ tail -f logs/backend.log
        └─▶ tail -f logs/frontend.log
```

---

## Summary

### Key Architecture Principles

1. **Separation of Concerns**
   - Frontend: UI/UX (React + Vite)
   - Backend: API/Logic (FastAPI)
   - Data: File-based storage

2. **Standard Ports**
   - Frontend: 5173 (Vite default)
   - Backend: 8081 (project standard)

3. **Flexible Access**
   - Local: Direct port access
   - Remote: Ngrok tunnel

4. **Reliable Management**
   - Health checks
   - PID tracking
   - Graceful shutdown

5. **Clear Data Flow**
   - HTTP API communication
   - JSON data exchange
   - File-based persistence

---

## Related Documentation

- **[DEPLOYMENT.md](../DEPLOYMENT.md)** - Complete deployment guide
- **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** - Pre-deployment verification
- **[PORT_CONFIGURATION.md](./PORT_CONFIGURATION.md)** - Detailed port management
- **[SCRIPT_MIGRATION.md](./SCRIPT_MIGRATION.md)** - Legacy script migration

---

**Last Updated**: 2025-11-21
**Maintained By**: Development Team
