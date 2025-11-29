# PM2 Setup and Management Guide

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- **epstein-backend**: Python FastAPI server on port 8081
- **epstein-frontend**: Vite development server on port 5173
- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8081
- **API Documentation**: http://localhost:8081/docs

---

## Overview
Both the backend and frontend are now managed by PM2 for automatic restarts and persistent operation.

## Current Configuration

### Services Running
- **epstein-backend**: Python FastAPI server on port 8081
- **epstein-frontend**: Vite development server on port 5173

### Configuration File
Location: `/Users/masa/Projects/epstein/ecosystem.config.js`

## Access URLs
- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8081
- **API Documentation**: http://localhost:8081/docs

## Environment Configuration

### Local Development (Current Setup)
The frontend is configured to use localhost backend:
```
VITE_API_BASE_URL=http://localhost:8081
```

### Production with ngrok
To switch to ngrok tunnel, edit `/Users/masa/Projects/epstein/frontend/.env`:
```
VITE_API_BASE_URL=https://the-island.ngrok.app
```
Then restart: `pm2 restart epstein-frontend`

## Common PM2 Commands

### View Status
```bash
pm2 list                    # List all processes
pm2 status                  # Same as list
pm2 monit                   # Live monitoring dashboard
```

### Logs
```bash
pm2 logs                    # View logs from all services
pm2 logs epstein-backend    # Backend logs only
pm2 logs epstein-frontend   # Frontend logs only
pm2 logs --lines 50         # Show last 50 lines
pm2 flush                   # Clear all logs
```

### Restart Services
```bash
pm2 restart epstein-backend     # Restart backend only
pm2 restart epstein-frontend    # Restart frontend only
pm2 restart all                 # Restart everything
```

### Stop Services
```bash
pm2 stop epstein-backend    # Stop backend
pm2 stop epstein-frontend   # Stop frontend
pm2 stop all               # Stop everything
```

### Start Services
```bash
pm2 start epstein-backend   # Start backend
pm2 start epstein-frontend  # Start frontend
pm2 start all              # Start everything
```

### Delete from PM2
```bash
pm2 delete epstein-backend    # Remove from PM2
pm2 delete epstein-frontend
pm2 delete all
```

### Reload Configuration
```bash
pm2 reload ecosystem.config.js   # Reload from config file
```

## Troubleshooting

### Backend Offline Message
If you see "Backend server is offline" in the frontend:

1. **Check PM2 status**:
   ```bash
   pm2 list
   ```

2. **Check backend logs**:
   ```bash
   pm2 logs epstein-backend --lines 50
   ```

3. **Test backend directly**:
   ```bash
   curl http://localhost:8081/api/timeline
   ```

4. **Restart services**:
   ```bash
   pm2 restart all
   ```

### Port Already in Use
If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -ti:8081  # Backend port
lsof -ti:5173  # Frontend port

# Kill processes if needed
lsof -ti:8081 | xargs kill -9
pm2 restart all
```

### After Code Changes

**Backend changes**: The backend has `--reload` enabled, so it auto-restarts on Python file changes.

**Frontend changes**: Vite hot-reload should work automatically. If not:
```bash
pm2 restart epstein-frontend
```

**Environment variable changes**: Always restart after .env changes:
```bash
pm2 restart epstein-frontend
```

## Auto-start on System Boot

PM2 configuration is saved. To enable auto-start on macOS boot:

```bash
pm2 startup
# Then copy and run the command it provides
pm2 save
```

## Benefits of PM2

1. **Auto-restart**: Crashes are automatically recovered
2. **Persistent**: Services survive terminal closures
3. **Log Management**: Centralized logging
4. **Process Monitoring**: CPU and memory tracking
5. **Zero-downtime Restarts**: Graceful reloads
6. **Cluster Mode**: Can run multiple instances (not configured)

## Manual Startup (Without PM2)

If you need to run without PM2:

**Backend**:
```bash
cd /Users/masa/Projects/epstein
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload
```

**Frontend**:
```bash
cd /Users/masa/Projects/epstein/frontend
npm run dev
```

## Previous Issues Resolved

### Issue: Frequent Backend Downtime
**Cause**: Server was manually started and would stop when terminal closed or on file changes.

**Solution**: PM2 now manages the process with auto-restart and persistence.

### Issue: ngrok Configuration Conflict
**Cause**: Frontend was configured to use `https://the-island.ngrok.app` which wasn't accessible locally.

**Solution**: Changed `.env` to use `http://localhost:8081` for local development.

## Next Steps

For production deployment, consider:
1. Set up ngrok tunnel for external access
2. Configure PM2 auto-start on system boot
3. Set up proper logging rotation
4. Configure monitoring alerts
