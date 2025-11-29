# Port Configuration

**Quick Summary**: This document defines the standard port configuration for the Epstein Document Archive project. .

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Framework**: Vite (React)
- **Config File**: `/frontend/vite.config.ts`
- **Default Port**: 5173 (Vite default)
- **Process**: Node.js running Vite dev server
- **Framework**: FastAPI

---

**Last Updated**: 2025-11-20

This document defines the standard port configuration for the Epstein Document Archive project.

---

## Standard Ports

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **Frontend (Vite)** | 5173 | http://localhost:5173 | React development server |
| **Backend (FastAPI)** | 8081 | http://localhost:8081 | Python API server |

---

## Frontend (Port 5173)

### Configuration
- **Framework**: Vite (React)
- **Config File**: `/frontend/vite.config.ts`
- **Default Port**: 5173 (Vite default)
- **Process**: Node.js running Vite dev server

### Starting Frontend
```bash
cd frontend
npm run dev
# Server starts on http://localhost:5173
```

### Verification
```bash
# Check if port is in use
lsof -i :5173

# Test if server is responding
curl -I http://localhost:5173
```

---

## Backend (Port 8081)

### Configuration
- **Framework**: FastAPI
- **Main File**: `/server/app.py`
- **Default Port**: 8000 (can be overridden)
- **Standard Port**: 8081 (project convention)
- **Process**: Python uvicorn server

### Starting Backend
```bash
# Method 1: Explicit port specification
python server/app.py 8081

# Method 2: Use default (port 8000)
python server/app.py
```

### Verification
```bash
# Check if port is in use
lsof -i :8081

# Test if server is responding
curl -I http://localhost:8081
```

---

## External Access (ngrok)

### Frontend Domain
- **ngrok Domain**: the-island.ngrok.app
- **Links to**: http://localhost:5173
- **Configuration**: Link ngrok domain to frontend port

### Setup ngrok
```bash
# Start ngrok tunnel to frontend
ngrok http --domain=the-island.ngrok.app 5173
```

---

## Port Conflicts

### Frontend Port Conflicts
If port 5173 is occupied:
```bash
# Kill process on port 5173
lsof -ti :5173 | xargs kill

# Or let Vite choose next available port
# Vite will auto-increment (5174, 5175, etc.)
```

### Backend Port Conflicts
If port 8081 is occupied:
```bash
# Kill process on port 8081
lsof -ti :8081 | xargs kill

# Or use a different port
python server/app.py 8082
```

---

## Process Management

### Current Running Processes
As of 2025-11-20:

**Frontend**:
- Process ID: 29502
- Command: `node /Users/masa/Projects/epstein/frontend/node_modules/.bin/vite`
- Port: 5173

**Backend**:
- Multiple instances may be running on ports 8000 and 8081
- Use `lsof -i :8081` to check current status

### Stopping All Dev Servers
```bash
# Stop all frontend servers
lsof -ti :5173 :5174 :5175 :5176 :5177 :5178 | xargs kill

# Stop backend servers
lsof -ti :8000 :8081 | xargs kill
```

---

## Best Practices

1. **Always use port 5173 for frontend** - This is the standard Vite port
2. **Always use port 8081 for backend** - This is the project convention
3. **Kill duplicate servers** - Avoid running multiple instances
4. **Verify ports before starting** - Check if ports are already in use
5. **Document changes** - Update this file if ports change

---

## Troubleshooting

### Multiple Frontend Servers Running
If multiple Vite servers are running on different ports:
```bash
# Find all Vite processes
ps aux | grep "vite" | grep -v grep

# Kill all except port 5173
lsof -ti :5174 :5175 :5176 :5177 :5178 | xargs kill
```

### Backend Not Responding
```bash
# Check if backend is running
lsof -i :8081

# Check backend logs
tail -f logs/server.log

# Restart backend
python server/app.py 8081
```

### CORS Issues
Ensure frontend is configured to point to correct backend port:
- Frontend expects backend at `http://localhost:8081`
- Check API client configuration in frontend code

---

## Configuration Files

### Frontend (Vite)
File: `/frontend/vite.config.ts`
```typescript
export default defineConfig({
  plugins: [react()],
  // Port is not specified, defaults to 5173
  // To override: server: { port: 5173 }
})
```

### Backend (FastAPI)
File: `/server/app.py`
```python
# Port is configurable via command line
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
```

---

**Maintained by**: Development Team
**Questions**: Refer to [Developer Documentation](docs/developer/README.md)
