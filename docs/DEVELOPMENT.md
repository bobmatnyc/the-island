# Development Guide

**Quick Summary**: This guide covers local development server management for the Epstein project. .

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **PID Tracking**: Prevents multiple instances from running
- **Automatic Cleanup**: Kills orphaned processes before starting
- **Status Checking**: Verify if the server is running before starting
- **Log Management**: All output redirected to `logs/frontend.log`
- Local: http://localhost:5173

---

This guide covers local development server management for the Epstein project.

## Development Servers

### Frontend (Vite + React)

The frontend runs on port 5173 and is managed by a dedicated script that prevents duplicate instances.

#### Commands

```bash
# Start the frontend server
./scripts/dev-frontend.sh start

# Stop the frontend server
./scripts/dev-frontend.sh stop

# Restart the frontend server
./scripts/dev-frontend.sh restart

# Check if frontend is running
./scripts/dev-frontend.sh status

# View frontend logs (live tail)
./scripts/dev-frontend.sh logs
```

#### Features

- **PID Tracking**: Prevents multiple instances from running
- **Automatic Cleanup**: Kills orphaned processes before starting
- **Status Checking**: Verify if the server is running before starting
- **Log Management**: All output redirected to `logs/frontend.log`

#### URLs

- Local: http://localhost:5173
- Network: Available on your local network (check logs for specific URLs)

### Backend (FastAPI + Python)

The backend runs on port 8081 and is managed by PM2 for process management.

#### Commands

```bash
# Start the backend server
./scripts/dev-backend.sh start

# Stop the backend server
./scripts/dev-backend.sh stop

# Restart the backend server
./scripts/dev-backend.sh restart

# Check backend status
./scripts/dev-backend.sh status

# View backend logs
./scripts/dev-backend.sh logs
```

#### Features

- **PM2 Management**: Professional process management
- **Virtual Environment Validation**: Ensures dependencies are installed
- **Port Conflict Detection**: Checks for port availability before starting
- **Health Checks**: Verifies server is responding after startup

#### URLs

- API: http://localhost:8081
- API Docs: http://localhost:8081/docs
- Health Check: http://localhost:8081/health

## Quick Start

Start both servers for full development:

```bash
# Start backend
./scripts/dev-backend.sh start

# Start frontend
./scripts/dev-frontend.sh start

# Check both are running
./scripts/dev-backend.sh status
./scripts/dev-frontend.sh status
```

## Troubleshooting

### Port Conflicts

If you see `EADDRINUSE` errors:

```bash
# Check what's using the port
lsof -ti:5173  # Frontend
lsof -ti:8081  # Backend

# Stop the servers properly
./scripts/dev-frontend.sh stop
./scripts/dev-backend.sh stop
```

### Multiple Frontend Instances

The frontend script prevents this automatically. If you encounter duplicates:

```bash
# Kill all vite processes
pkill -9 -f "vite"

# Start fresh
./scripts/dev-frontend.sh start
```

### Server Not Starting

1. Check logs:
   ```bash
   ./scripts/dev-frontend.sh logs
   ./scripts/dev-backend.sh logs
   ```

2. Verify dependencies:
   ```bash
   # Frontend
   cd frontend && npm install

   # Backend
   cd server && pip install -r requirements.txt
   ```

3. Clean restart:
   ```bash
   ./scripts/dev-frontend.sh stop
   ./scripts/dev-backend.sh stop
   sleep 2
   ./scripts/dev-backend.sh start
   ./scripts/dev-frontend.sh start
   ```

## Log Files

All logs are stored in the `logs/` directory:

- `logs/frontend.log` - Frontend server output
- Backend logs accessible via PM2: `pm2 logs epstein-backend`

## Best Practices

1. **Always use the management scripts** instead of manual `npm run dev` or `python server/app.py`
2. **Check status before starting** to avoid duplicate processes
3. **Stop servers when done** to free up system resources
4. **Check logs** when debugging issues

## Development Workflow

1. Start backend first (API dependency)
2. Start frontend second
3. Access frontend at http://localhost:5173
4. Backend API at http://localhost:8081
5. Stop both when done developing

## Process Management Details

### Frontend (dev-frontend.sh)

- Uses PID file: `.frontend-dev.pid`
- Logs to: `logs/frontend.log`
- Port: 5173
- Process name pattern: `vite.*frontend`

### Backend (dev-backend.sh)

- Uses PM2 for management
- PM2 app name: `epstein-backend`
- Port: 8081
- Health check endpoint: `/health`

## Emergency Cleanup

If everything is stuck:

```bash
# Nuclear option - kill everything
pkill -9 -f "vite"
pm2 delete epstein-backend
rm -f .frontend-dev.pid

# Start fresh
./scripts/dev-backend.sh start
./scripts/dev-frontend.sh start
```
