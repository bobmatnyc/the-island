# 🌐 Ngrok Tunnel - Active

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- ✅ Backend is NOT exposed to internet
- ✅ Frontend is publicly accessible
- ✅ API calls happen over localhost
- **Total Documents**: 38,482 documents indexed
- **Document Types**:

---

**Date**: 2025-11-22 22:22
**Status**: ✅ Running

---

## Quick Access

**Public URL**: https://the-island.ngrok.app

---

## Architecture

```
Internet Users
      ↓
https://the-island.ngrok.app (Ngrok Tunnel)
      ↓
http://localhost:5173 (Frontend - Vite Dev Server)
      ↓
http://localhost:8081 (Backend - FastAPI, LOCAL ONLY)
```

**Security**:
- ✅ Backend is NOT exposed to internet
- ✅ Frontend is publicly accessible
- ✅ API calls happen over localhost

---

## Services Status

| Service | Port | Status | Access |
|---------|------|--------|--------|
| Frontend (Vite) | 5173 | ✅ Running | http://localhost:5173 |
| Backend (FastAPI) | 8081 | ✅ Running | http://localhost:8081 (local only) |
| Ngrok Tunnel | - | ✅ Active | https://the-island.ngrok.app |
| Ngrok Dashboard | 4040 | ✅ Active | http://localhost:4040 |

---

## Document Viewer Status

### Documents Available ✅
- **Total Documents**: 38,482 documents indexed
- **Document Types**:
  - PDFs: 38,177
  - Emails: 305

### Document Sources
- House Oversight Nov 2025: 37,469 files
- Court filings (Giuffre/Maxwell): 358 files
- FBI Vault documents: 21 files
- 404Media articles: 319 files
- Emails: 305 files
- Other sources: ~115 files

### API Endpoints ✅
- **Documents List**: `GET /api/documents`
- **Document View**: `GET /api/documents/{doc_id}/view`
- **Authentication**: Basic auth (demo:demo)

### Testing Document Viewer
```bash
# List documents
curl -u demo:demo "http://localhost:8081/api/documents?limit=5"

# Get specific document
curl -u demo:demo "http://localhost:8081/api/documents/0ef53e7de52ac7ae2a4357f7faa60a3f38227d7b9e1e5ec70bba8fdef3dcc017"
```

---

## Biography System Status

### Entity Biographies ✅
- **Total Biographies**: 98 entities (Tier 1-4)
- **With Flight Log Sources**: 91 entities (93%)
- **Total Flight Appearances**: 2,909 documented

### Document Linking ✅
All biographies now include `document_sources` field linking to:
- Flight log entries (dates, routes, passenger names)
- Black book references (when available)

### Sample Biography with Sources
```json
{
  "larry_summers": {
    "display_name": "Larry Summers",
    "biography": "Larry Summers, born Lawrence Henry Summers...",
    "document_sources": {
      "flight_logs": {
        "count": 4,
        "entries": [
          {"date": "9/19/1998", "from": "Unknown", "to": "Unknown"},
          {"date": "4/15/2004", "from": "Unknown", "to": "Unknown"}
        ]
      }
    }
  }
}
```

---

## Management Commands

### Check Status
```bash
# Check all services
ps aux | grep -E "(ngrok|vite|python.*app)" | grep -v grep

# Test public URL
curl -I https://the-island.ngrok.app

# Test backend (local only)
curl http://localhost:8081/api/v2/stats
```

### View Logs
```bash
# Ngrok logs
tail -f /tmp/ngrok_frontend_new.log

# Frontend logs
tail -f /tmp/frontend_dev.log

# Backend logs
tail -f /tmp/backend_restart_sources.log

# Ngrok web dashboard
open http://localhost:4040
```

### Stop Services
```bash
# Stop ngrok
pkill -f ngrok

# Stop frontend
pkill -f vite

# Stop backend
lsof -ti:8081 | xargs kill -9

# Stop all
pkill -f ngrok && pkill -f vite && lsof -ti:8081 | xargs kill -9
```

### Restart Services
```bash
# 1. Start backend
python3 server/app.py 8081 > /tmp/backend.log 2>&1 &

# 2. Start frontend
cd frontend && npm run dev > /tmp/frontend.log 2>&1 &

# 3. Start ngrok (wait for frontend to be ready)
sleep 5
ngrok http --domain="the-island.ngrok.app" 5173 > /tmp/ngrok_frontend_new.log 2>&1 &
```

---

## Testing URLs

### Local Testing
- Home: http://localhost:5173
- Entities: http://localhost:5173/entities
- Biographies: http://localhost:5173/entities?bio=true
- Documents: http://localhost:5173/documents
- Timeline: http://localhost:5173/timeline
- Network: http://localhost:5173/network

### Public Testing
- Home: https://the-island.ngrok.app
- Entities: https://the-island.ngrok.app/entities
- Biographies: https://the-island.ngrok.app/entities?bio=true
- Documents: https://the-island.ngrok.app/documents
- Timeline: https://the-island.ngrok.app/timeline
- Network: https://the-island.ngrok.app/network

---

## Features Available

✅ 98 entity biographies (Tier 1-4)
✅ 91 biographies with flight log sources
✅ 2,909 flight appearances documented
✅ 38,482 documents indexed
✅ PDF document viewer (inline viewing)
✅ Timeline visualization
✅ Network graph
✅ Advanced search

---

## Ngrok Domain Configuration

**Reserved Domain**: `the-island.ngrok.app`

This is a permanent ngrok domain configured for this project. It won't change between restarts.

To use a different domain, modify the ngrok command:
```bash
ngrok http --domain="your-domain.ngrok.app" 5173
```

---

## Environment Configuration

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8081
```

**CRITICAL**: The frontend MUST use `localhost:8081` for API calls because:
- Backend is ONLY accessible on localhost (not exposed via ngrok)
- When users access site via ngrok, their browser downloads the React app
- The React app then runs IN THE USER'S BROWSER
- Browser makes API calls to `localhost:8081` which connects to YOUR local backend
- This only works when user's browser is on the same machine as the backend

**This setup is for LOCAL TESTING ONLY** - won't work for external users!

For external users to access the full app, you would need:
1. Expose backend on ngrok too (separate tunnel on port 8081), OR
2. Deploy backend to a public server, OR
3. Use a reverse proxy setup

### Vite Config
`allowedHosts: ['the-island.ngrok.app', 'localhost']`

This allows Vite to accept connections from the ngrok domain.

---

## Troubleshooting

### "ERR_NGROK_3200 - Endpoint is offline"
This means ngrok tunnel is down. To fix:
```bash
# 1. Stop all ngrok processes
pkill -9 -f ngrok

# 2. If there's a launchd service, unload it
launchctl unload ~/Library/LaunchAgents/com.epstein.ngrok.plist

# 3. Wait a moment
sleep 2

# 4. Start fresh tunnel
ngrok http --domain="the-island.ngrok.app" 5173 > /tmp/ngrok_frontend_new.log 2>&1 &

# 5. Verify (should return HTTP/2 200)
curl -I https://the-island.ngrok.app
```

### Frontend not loading
```bash
# Check if frontend is running
curl http://localhost:5173

# Check frontend logs
tail -f /tmp/frontend_dev.log

# Restart frontend
pkill -f vite
cd frontend && npm run dev > /tmp/frontend.log 2>&1 &
```

### Backend errors
```bash
# Check if backend is running
curl http://localhost:8081

# Check backend logs
tail -f /tmp/backend_restart_sources.log

# Restart backend
lsof -ti:8081 | xargs kill -9
python3 server/app.py 8081 > /tmp/backend.log 2>&1 &
```

### Documents not loading
```bash
# Check documents API
curl -u demo:demo "http://localhost:8081/api/documents?limit=3"

# Should return JSON with 38,482 total documents
# If it returns {"total": 0}, check backend logs
```

### "Connection refused" errors
This usually means the backend isn't running. Check:
```bash
# Is backend running?
lsof -ti:8081

# Start if not running
python3 server/app.py 8081 > /tmp/backend.log 2>&1 &
```

---

## Session Summary (2025-11-22)

### What Was Done
1. ✅ Stopped launchd ngrok service that was conflicting
2. ✅ Killed all ngrok processes cleanly
3. ✅ Started fresh ngrok tunnel pointing to frontend (port 5173)
4. ✅ Verified public accessibility (HTTP/2 200)
5. ✅ Confirmed backend is running and accessible locally
6. ✅ Verified document viewer functionality (38,482 documents available)
7. ✅ Confirmed biography system with document sources (91 entities linked)

### Current State
- All services running correctly
- Public URL active and accessible: https://the-island.ngrok.app
- Frontend → Backend communication working
- Security model correct (backend not exposed)
- Document viewer functional with 38k+ documents
- Biography system enhanced with verifiable sources

---

**Last Updated**: 2025-11-22 22:22
**Public URL**: https://the-island.ngrok.app
**Status**: ✅ Active and verified
**Ngrok PID**: 50011
