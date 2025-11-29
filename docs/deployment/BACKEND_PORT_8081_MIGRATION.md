# Backend Migration to Port 8081

**Quick Summary**: Successfully migrated the backend server from port 8000 to port 8081 and reconfigured the ngrok tunnel to match. .

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Port 8000**: Freed (old backend process already terminated)
- **Port 8081**:
- Stopped Docker container `espocrm-phpmyadmin` that was occupying the port
- Killed old Python backend process (PID 18895)
- Port now exclusively used by the new backend server

---

**Date**: 2025-11-20
**Status**: COMPLETED

## Overview

Successfully migrated the backend server from port 8000 to port 8081 and reconfigured the ngrok tunnel to match.

## Changes Made

### 1. Port Conflicts Resolved

- **Port 8000**: Freed (old backend process already terminated)
- **Port 8081**:
  - Stopped Docker container `espocrm-phpmyadmin` that was occupying the port
  - Killed old Python backend process (PID 18895)
  - Port now exclusively used by the new backend server

### 2. Backend Server Configuration

**Script**: `/Users/masa/Projects/epstein/scripts/dev-backend.sh`
- Already configured for port 8081 (BACKEND_PORT=8081)
- Backend started using: `python3 server/app.py 8081`
- Health check passed successfully

**Process Information**:
- PID: 33994
- Port: 8081
- Log file: `/Users/masa/Projects/epstein/logs/backend.log`

### 3. ngrok Tunnel Configuration

**Script**: `/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh`

**Update Made**:
```bash
# Changed from:
nohup ngrok http --url="$NGROK_URL" "$LOCAL_PORT" > /dev/null 2>&1 &

# To:
nohup ngrok http --domain="$NGROK_URL" "$LOCAL_PORT" > /dev/null 2>&1 &
```

**Configuration**:
- Domain: `the-island.ngrok.app`
- Local Port: 8081
- Public URL: `https://the-island.ngrok.app`
- Tunnel PID: 35157
- Monitor PIDs: 36115, 35060

## Verification Results

### Local Endpoints (Port 8081)

✅ **Health Check**:
```bash
curl http://localhost:8081/health
```
Response:
```json
{
  "status": "ok",
  "timestamp": "2025-11-20T19:31:27.507784",
  "service": "epstein-archive-api",
  "version": "1.0.0"
}
```

✅ **V2 Entity Endpoint**:
```bash
curl http://localhost:8081/api/v2/entities/jeffrey_epstein
```
- Entity ID: `jeffrey_epstein`
- Flight count: 1018
- Status: SUCCESS

✅ **V1 Entity Endpoint**:
```bash
curl http://localhost:8081/api/entities/jeffrey_epstein
```
- Entity ID: `jeffrey_epstein`
- Flight count: 1018
- Status: SUCCESS

### Public Endpoints (ngrok)

✅ **Health Check**:
```bash
curl https://the-island.ngrok.app/health
```
Response:
```json
{
  "status": "ok",
  "timestamp": "2025-11-20T19:31:30.076541",
  "service": "epstein-archive-api",
  "version": "1.0.0"
}
```

✅ **V2 Entity Endpoint**:
```bash
curl https://the-island.ngrok.app/api/v2/entities/jeffrey_epstein
```
- Entity ID: `jeffrey_epstein`
- Flight count: 1018
- Status: SUCCESS

✅ **V1 Entity Endpoint**:
```bash
curl https://the-island.ngrok.app/api/entities/jeffrey_epstein
```
- Entity ID: `jeffrey_epstein`
- Flight count: 1018
- Status: SUCCESS

## Service Status

### Backend Server
- **Status**: Running
- **PID**: 33994
- **Port**: 8081
- **Command**: `python3 server/app.py 8081`
- **Logs**: `tail -f logs/backend.log`

### ngrok Tunnel
- **Status**: UP
- **PID**: 35157
- **Public URL**: https://the-island.ngrok.app
- **Local Port**: http://localhost:8081
- **Connections**: 3
- **HTTP Requests**: 3

### ngrok Monitor
- **Status**: Running
- **PIDs**: 36115, 35060
- **Monitor Script**: `/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh monitor`
- **Health Check Interval**: 300 seconds (5 minutes)
- **Auto-restart**: Enabled

## Management Commands

### Backend Server
```bash
# Start
bash scripts/dev-backend.sh start

# Stop
bash scripts/dev-backend.sh stop

# Restart
bash scripts/dev-backend.sh restart

# Status
bash scripts/dev-backend.sh status

# View logs
bash scripts/dev-backend.sh logs
```

### ngrok Tunnel
```bash
# Start
bash /Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh start

# Stop
bash /Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh stop

# Restart
bash /Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh restart

# Status
bash /Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh status

# Start monitor (auto-restart on failure)
bash /Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh monitor
```

## Configuration Files Updated

1. **`/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh`**
   - Fixed ngrok flag from `--url` to `--domain`
   - Already configured for port 8081

2. **`/Users/masa/Projects/epstein/scripts/dev-backend.sh`**
   - No changes needed (already configured for port 8081)

## Frontend API Configuration Status

### ✅ Correctly Configured (Port 8081)
- `/frontend/src/lib/api.ts` - Main API library (default: http://localhost:8081)
- `/frontend/src/components/visualizations/CalendarHeatmap.tsx`
- `/frontend/src/pages/Matrix.tsx`
- `/frontend/src/pages/Activity.tsx`

### ⚠️ Needs Update (Still Using Port 8000)
The following files have hardcoded references to port 8000 and should be updated:

1. `/frontend/src/components/documents/DocumentViewer.tsx`
   - Line: `const downloadUrl = 'http://localhost:8000/api/documents/${document.id}/download'`

2. `/frontend/src/lib/schemas.example.ts`
   - Example code (non-critical)

3. `/frontend/src/pages/Analytics.tsx`
   - Line: `const response = await fetch('http://localhost:8000/api/v2/stats')`

4. `/frontend/src/pages/Documents.tsx`
   - Line: `const downloadUrl = 'http://localhost:8000/api/documents/${doc.id}/download'`

5. `/frontend/src/pages/AdvancedSearch.tsx`
   - Line: `const API_BASE_URL = 'http://localhost:8000'`

6. `/frontend/src/services/newsApi.ts`
   - Line: `const API_BASE_URL = 'http://localhost:8000'`

**Recommendation**: Update all hardcoded URLs to use the `API_BASE_URL` from `/frontend/src/lib/api.ts` or update to port 8081.

## Notes

### Docker Container Conflict
The Docker container `espocrm-phpmyadmin` was using port 8081. This container has been stopped:
```bash
docker stop espocrm-phpmyadmin
```

If you need to restart the phpMyAdmin container, you'll need to either:
1. Use a different port for phpMyAdmin
2. Stop the Epstein backend before starting phpMyAdmin

### ngrok Monitor
The persistent monitor ensures the tunnel stays up by:
- Checking tunnel health every 5 minutes
- Auto-restarting on failure
- Logging events to `/tmp/ngrok_persistent.log`

## Success Criteria

All success criteria met:

- ✅ Backend running on port 8081
- ✅ Backend loads migrated entity data successfully
- ✅ ngrok tunnel accessible on port 8081
- ✅ Health check passes (local and public)
- ✅ Entity ID endpoints responding correctly (local and public)
- ✅ Persistent monitoring enabled

## Quick Reference

**Backend URL (Local)**: http://localhost:8081
**Backend URL (Public)**: https://the-island.ngrok.app
**API Docs**: http://localhost:8081/docs
**ngrok Dashboard**: http://localhost:4040

**Key Files**:
- Backend: `/Users/masa/Projects/epstein/server/app.py`
- Backend Script: `/Users/masa/Projects/epstein/scripts/dev-backend.sh`
- ngrok Script: `/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh`
- Backend Logs: `/Users/masa/Projects/epstein/logs/backend.log`
- ngrok Logs: `/tmp/ngrok_persistent.log`
