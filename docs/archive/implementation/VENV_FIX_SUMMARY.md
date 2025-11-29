# Epstein Archive Server - Virtual Environment Fix

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- ❌ RAG routes failing to load
- ❌ Error: "ChromaDB dependencies may not be installed"
- ❌ Missing packages: ChromaDB, SentenceTransformers
- ❌ Server running with system Python instead of venv Python
- Kills existing processes on the port

---

## Problem Summary

The Epstein Archive server was experiencing failures with RAG (Retrieval-Augmented Generation) routes because it was running with system Python instead of the virtual environment Python, causing ChromaDB and other dependencies to be unavailable.

### Symptoms
- ❌ RAG routes failing to load
- ❌ Error: "ChromaDB dependencies may not be installed"
- ❌ Missing packages: ChromaDB, SentenceTransformers
- ❌ Server running with system Python instead of venv Python

## Root Cause

The server startup process was using system Python (`python3`) instead of the venv Python located at `/Users/masa/Projects/epstein/.venv/bin/python3`. This meant the server couldn't access the packages installed in the virtual environment.

## Solution Implemented

### 1. Missing Dependencies Installed

The venv was missing some server-specific dependencies that were defined in `/Users/masa/Projects/epstein/server/requirements.txt`:

```bash
pip install sse-starlette==1.8.2 aiofiles==23.2.1 watchdog==3.0.0
```

### 2. Server Restarted with Venv Python

Changed server startup from:
```bash
# WRONG - Uses system Python
python3 /Users/masa/Projects/epstein/server/app.py
```

To:
```bash
# CORRECT - Uses venv Python
/Users/masa/Projects/epstein/.venv/bin/python3 /Users/masa/Projects/epstein/server/app.py 8081
```

### 3. Startup Scripts Created

Created three convenience scripts for easy startup:

#### `start_server.sh` - Server Only
```bash
./start_server.sh [port]
```
- Kills existing processes on the port
- Starts server with venv Python
- Verifies server is responding
- Checks RAG system status
- Displays server info and logs location

#### `start_ngrok.sh` - Ngrok Tunnel Only
```bash
./start_ngrok.sh
```
- Kills existing ngrok processes
- Starts ngrok tunnel for "the-island"
- Verifies tunnel is active
- Displays tunnel URL and status

#### `start_all.sh` - Complete Startup
```bash
./start_all.sh [port]
```
- Runs both server and ngrok startup
- Comprehensive status output
- Error handling for each component

## Verification Results

All systems verified and operational:

### ✅ Server Status
- Running on port 8081
- Using venv Python with all dependencies
- Responding with HTTP 200 OK

### ✅ RAG System Status
- RAG routes successfully registered
- ChromaDB loaded without warnings
- 33,329 documents indexed
- Search endpoint functional (<20ms response time)

### ✅ Ngrok Tunnel Status
- Tunnel active at https://the-island.ngrok.app/
- Publicly accessible
- Web UI available at http://localhost:4040

### ✅ Network Graph Status
- 284 nodes
- 1,624 edges
- Network data accessible

## Usage

### Starting the Server

**Recommended - Start Everything:**
```bash
cd /Users/masa/Projects/epstein
./start_all.sh
```

**Server Only:**
```bash
./start_server.sh 8081
```

**Ngrok Only:**
```bash
./start_ngrok.sh
```

### Monitoring

**View Server Logs:**
```bash
tail -f /tmp/epstein_8081_venv.log
```

**View Ngrok Logs:**
```bash
tail -f /tmp/ngrok_the-island.log
```

**Ngrok Web Interface:**
```bash
open http://localhost:4040
```

### Stopping Services

**Stop Server:**
```bash
lsof -ti:8081 | xargs kill
```

**Stop Ngrok:**
```bash
pkill -f "ngrok start"
```

## Testing RAG Endpoints

### Search Documents
```bash
curl -s "http://localhost:8081/api/rag/search?query=epstein&limit=5" | python3 -m json.tool
```

### Get Stats
```bash
curl -s "http://localhost:8081/api/rag/stats" | python3 -m json.tool
```

### Search by Entity
```bash
curl -s "http://localhost:8081/api/rag/entity/Jeffrey%20Epstein" | python3 -m json.tool
```

## Technical Details

### Virtual Environment
- Location: `/Users/masa/Projects/epstein/.venv/`
- Python: Python 3.13
- Key packages:
  - ChromaDB 0.4.22
  - SentenceTransformers
  - FastAPI 0.104.1
  - sse-starlette 1.8.2

### Server Configuration
- Port: 8081
- Framework: FastAPI with Uvicorn
- Log file: `/tmp/epstein_8081_venv.log`
- Working directory: `/Users/masa/Projects/epstein/server`

### Ngrok Configuration
- Tunnel name: the-island
- Domain: the-island.ngrok.app
- Protocol: HTTP
- Local port: 8081
- Config file: `/Users/masa/Library/Application Support/ngrok/ngrok.yml`

## Requirements Files

The project has two requirements files that must both be installed:

1. **Root requirements.txt** - Core dependencies
   ```bash
   .venv/bin/pip install -r requirements.txt
   ```

2. **Server requirements.txt** - Server-specific dependencies
   ```bash
   .venv/bin/pip install -r server/requirements.txt
   ```

Note: The server/requirements.txt contains invalid packages (`secrets-management`, `python-cors`) that should be removed or corrected.

## Troubleshooting

### Server Won't Start
1. Check if port 8081 is already in use:
   ```bash
   lsof -i:8081
   ```
2. Kill existing processes:
   ```bash
   lsof -ti:8081 | xargs kill -9
   ```
3. Check server logs:
   ```bash
   tail -50 /tmp/epstein_8081_venv.log
   ```

### RAG Routes Not Loading
1. Verify ChromaDB is installed:
   ```bash
   .venv/bin/pip list | grep chroma
   ```
2. Check for errors in server logs:
   ```bash
   grep -i "error\|chroma\|rag" /tmp/epstein_8081_venv.log
   ```

### Ngrok Not Starting
1. Verify ngrok config:
   ```bash
   ngrok config check
   ```
2. Check ngrok logs:
   ```bash
   tail -50 /tmp/ngrok_the-island.log
   ```

## Future Improvements

1. **Fix server/requirements.txt**: Remove invalid packages (`secrets-management`, `python-cors`)
2. **Consolidate requirements**: Merge server/requirements.txt into main requirements.txt
3. **Add systemd/launchd service**: Auto-start server on boot
4. **Health check endpoint**: Add `/api/rag/health` endpoint
5. **Environment validation**: Script to verify all dependencies are installed

## Related Files

- `/Users/masa/Projects/epstein/start_server.sh` - Server startup script
- `/Users/masa/Projects/epstein/start_ngrok.sh` - Ngrok startup script
- `/Users/masa/Projects/epstein/start_all.sh` - Complete startup script
- `/Users/masa/Projects/epstein/server/app.py` - Main server application
- `/Users/masa/Projects/epstein/server/routes/rag.py` - RAG endpoints

---

**Status**: ✅ All systems operational as of 2025-11-18

**Deployment**: Production-ready
