# Deployment Guide

**Quick Summary**: **Epstein Document Archive** - Comprehensive deployment and development environment guide. .

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- [30-Second Startup](#30-second-startup)
- [Development Environments](#development-environments)
- [Port Configuration](#port-configuration)
- [Service Management](#service-management)
- [Environment Options](#environment-options)

---

**Epstein Document Archive** - Comprehensive deployment and development environment guide.

> **Quick Start**: Ready to go? Jump to [30-Second Startup](#30-second-startup)

---

## Table of Contents

- [30-Second Startup](#30-second-startup)
- [Development Environments](#development-environments)
- [Port Configuration](#port-configuration)
- [Service Management](#service-management)
- [Environment Options](#environment-options)
- [Troubleshooting](#troubleshooting)
- [Deep Dive Documentation](#deep-dive-documentation)
- [Migration from Legacy Scripts](#migration-from-legacy-scripts)

---

## 30-Second Startup

### Prerequisites Check
```bash
# Ensure you have virtual environment and dependencies installed
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Start Everything
```bash
# Option 1: Start both backend and frontend (recommended)
./scripts/dev-start.sh

# Option 2: Start services separately
./scripts/dev-backend.sh start    # Backend on port 8081
./scripts/dev-frontend.sh start   # Frontend on port 5173
```

### Verify Everything Works
```bash
# Check service status
./scripts/dev-status.sh

# Backend health check
curl http://localhost:8081/health

# Frontend accessible at
open http://localhost:5173
```

**That's it!** 🎉 Your development environment is running.

---

## Development Environments

Choose the environment that matches your workflow:

### 1. Local Development (Default)

**Best for**: Day-to-day development, testing, debugging

```bash
# Start both services
./scripts/dev-start.sh

# Or start individually
./scripts/dev-backend.sh start
./scripts/dev-frontend.sh start
```

**Access**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8081
- API Docs: http://localhost:8081/docs

**Features**:
- Hot module reloading (frontend)
- Auto-reload on code changes (backend)
- Local file watching
- Full debug capabilities

---

### 2. Ngrok Tunnel (Remote Access)

**Best for**: Sharing work, remote testing, mobile device testing, external API webhooks

```bash
# 1. Start backend
./scripts/dev-backend.sh start

# 2. Start ngrok tunnel
./scripts/ngrok_persistent.sh start

# 3. Configure frontend for ngrok
echo "VITE_API_BASE_URL=https://the-island.ngrok.app" > frontend/.env

# 4. Start frontend (restart if already running)
./scripts/dev-frontend.sh restart
```

**Access**:
- Public URL: https://the-island.ngrok.app
- Ngrok Dashboard: http://localhost:4040
- Frontend: http://localhost:5173 (configured to use ngrok backend)

**Features**:
- Public HTTPS access
- Share work with team/clients
- Test on mobile devices
- Webhook testing

**📖 See**: [NGROK_CONFIGURATION_SUMMARY.md](./deployment/NGROK_CONFIGURATION_SUMMARY.md) for complete setup

---

### 3. Production-Like Local

**Best for**: Pre-deployment testing, performance testing

```bash
# Start backend without auto-reload
source .venv/bin/activate
python server/app.py 8081 > logs/backend.log 2>&1 &

# Build frontend for production
cd frontend
npm run build
npm run preview  # Serves production build
```

**Access**:
- Frontend (production build): http://localhost:4173
- Backend: http://localhost:8081

---

## Port Configuration

### Standard Ports

| Service | Port | URL | Notes |
|---------|------|-----|-------|
| **Frontend (Vite)** | 5173 | http://localhost:5173 | Default Vite dev port |
| **Backend (FastAPI)** | 8081 | http://localhost:8081 | Project standard |
| **Ngrok Dashboard** | 4040 | http://localhost:4040 | When ngrok is running |
| **Frontend Preview** | 4173 | http://localhost:4173 | Production build preview |

### Why Port 8081?

The project uses **port 8081** (not FastAPI's default 8000) for the backend to:
- Avoid conflicts with other common services
- Maintain consistency across team environments
- Support side-by-side testing with other projects

### Port Conflict Resolution

If you see "port already in use" errors:

```bash
# Check what's using the port
lsof -i :8081  # For backend
lsof -i :5173  # For frontend

# Kill the process
lsof -ti :8081 | xargs kill
lsof -ti :5173 | xargs kill

# Or use the stop script
./scripts/dev-stop.sh
```

**📖 See**: [PORT_CONFIGURATION.md](./deployment/PORT_CONFIGURATION.md) for detailed port management

---

## Service Management

### Quick Commands Reference

```bash
# ──────────────────────────────────────────────────────────
# START SERVICES
# ──────────────────────────────────────────────────────────
./scripts/dev-start.sh              # Start both services
./scripts/dev-start.sh --backend-only    # Backend only
./scripts/dev-start.sh --frontend-only   # Frontend only

./scripts/dev-backend.sh start      # Backend with health check
./scripts/dev-frontend.sh start     # Frontend with process management

# ──────────────────────────────────────────────────────────
# STOP SERVICES
# ──────────────────────────────────────────────────────────
./scripts/dev-stop.sh               # Stop both services
./scripts/dev-backend.sh stop       # Stop backend only
./scripts/dev-frontend.sh stop      # Stop frontend only

# ──────────────────────────────────────────────────────────
# RESTART SERVICES
# ──────────────────────────────────────────────────────────
./scripts/dev-start.sh --restart    # Restart both
./scripts/dev-backend.sh restart    # Restart backend
./scripts/dev-frontend.sh restart   # Restart frontend

# ──────────────────────────────────────────────────────────
# CHECK STATUS
# ──────────────────────────────────────────────────────────
./scripts/dev-status.sh             # Status of both services
./scripts/dev-backend.sh status     # Backend status + health check
./scripts/dev-frontend.sh status    # Frontend status

# ──────────────────────────────────────────────────────────
# VIEW LOGS
# ──────────────────────────────────────────────────────────
./scripts/dev-logs.sh               # Tail both logs
./scripts/dev-backend.sh logs       # Backend logs only
./scripts/dev-frontend.sh logs      # Frontend logs only

tail -f logs/backend.log            # Manual log tailing
tail -f logs/frontend.log
```

### Script Features

All new dev scripts (`/scripts/dev-*.sh`) include:

✅ **Process Detection** - Detect running instances before starting
✅ **Port Conflict Handling** - Automatic detection and resolution prompts
✅ **Health Checks** - Verify services are responding correctly
✅ **PID Tracking** - Reliable process management
✅ **Graceful Shutdown** - Clean termination of processes
✅ **Colored Output** - Clear status messages with colors
✅ **Error Handling** - Detailed error messages and recovery suggestions

---

## Environment Options

### Local Development (Default)

**Configuration**: No setup needed

```bash
# Frontend .env (or leave empty for defaults)
VITE_API_BASE_URL=http://localhost:8081
```

**When to Use**:
- Normal development work
- Testing features locally
- Debugging issues
- Fast iteration cycles

---

### Remote Backend (Ngrok)

**Configuration**:

```bash
# frontend/.env
VITE_API_BASE_URL=https://the-island.ngrok.app
```

**Important**: After changing `.env`, you **MUST** restart the frontend:
```bash
./scripts/dev-frontend.sh restart
```

**When to Use**:
- Sharing work with remote team members
- Testing on mobile devices
- External API integrations (webhooks)
- Demo to stakeholders

**Switching Back to Local**:
```bash
# Edit frontend/.env
VITE_API_BASE_URL=http://localhost:8081

# Restart frontend
./scripts/dev-frontend.sh restart
```

---

### Production Environment Variables

For production deployments, configure additional environment variables:

```bash
# Backend environment (.env in project root)
DATABASE_PATH=/path/to/production/data
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
API_PORT=8081

# Frontend environment (frontend/.env.production)
VITE_API_BASE_URL=https://api.yourdomain.com
```

---

## Troubleshooting

### Problem: Services Won't Start

**Symptoms**: Error messages when running start scripts

**Solutions**:

```bash
# 1. Check for port conflicts
lsof -i :8081  # Backend
lsof -i :5173  # Frontend

# 2. Kill conflicting processes
./scripts/dev-stop.sh

# 3. Verify virtual environment
ls -la .venv/bin/activate
source .venv/bin/activate
pip list | grep fastapi  # Should show FastAPI

# 4. Verify frontend dependencies
ls -la frontend/node_modules
cd frontend && npm install
```

---

### Problem: Backend Starts but Not Responding

**Symptoms**: Backend process running but health check fails

**Solutions**:

```bash
# 1. Check backend logs
./scripts/dev-backend.sh logs

# 2. Look for errors in logs
tail -50 logs/backend.log | grep -i error

# 3. Verify port binding
lsof -i :8081

# 4. Test health endpoint manually
curl -v http://localhost:8081/health
curl -v http://localhost:8081/api/stats

# 5. Check virtual environment activation
which python3  # Should point to .venv
```

**Common Causes**:
- Missing dependencies (run `pip install -r requirements.txt`)
- Database connection issues (check `data/` directory permissions)
- Port already in use by different service
- Python version incompatibility (requires Python 3.9+)

---

### Problem: Frontend Shows CORS Errors

**Symptoms**: Console errors like "Access to fetch blocked by CORS policy"

**Solutions**:

```bash
# 1. Verify backend CORS configuration
grep -A 5 "CORSMiddleware" server/app.py

# Should see:
# allow_origins=["*"]  # or specific origins

# 2. Check frontend API configuration
cat frontend/.env
# Should point to correct backend URL

# 3. Verify backend is accessible
curl http://localhost:8081/health

# 4. Restart both services
./scripts/dev-stop.sh
./scripts/dev-start.sh
```

---

### Problem: Ngrok Tunnel Not Working

**Symptoms**: "ERR_NGROK_3200" or tunnel offline

**Solutions**:

```bash
# 1. Check ngrok status
curl -s http://localhost:4040/api/tunnels | python3 -m json.tool

# 2. Restart ngrok tunnel
pkill -f ngrok
./scripts/ngrok_persistent.sh start

# 3. Verify backend is running
curl http://localhost:8081/health

# 4. Test tunnel connectivity
curl https://the-island.ngrok.app/health
```

**Common Causes**:
- Ngrok not authenticated (run `ngrok authtoken YOUR_TOKEN`)
- Backend not running on port 8081
- Ngrok tunnel configuration pointing to wrong port
- Network connectivity issues

---

### Problem: Changes Not Appearing

**Symptoms**: Code changes don't show up in browser

**Solutions**:

```bash
# Backend changes not showing:
# 1. Verify auto-reload is enabled (check logs)
./scripts/dev-backend.sh logs | grep -i reload

# 2. Restart backend if needed
./scripts/dev-backend.sh restart

# Frontend changes not showing:
# 1. Check Vite is running
./scripts/dev-frontend.sh status

# 2. Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)

# 3. Check for build errors
./scripts/dev-frontend.sh logs

# 4. Restart frontend
./scripts/dev-frontend.sh restart
```

---

### Problem: Environment Variables Not Loading

**Symptoms**: Frontend still using old API URL after changing `.env`

**Solution**:

```bash
# Vite only loads .env files at startup
# YOU MUST RESTART for changes to take effect

./scripts/dev-frontend.sh restart

# Verify environment variables are loaded
# (Check Network tab in browser DevTools)
```

---

### Getting More Help

If you're still stuck after trying these solutions:

1. **Check Logs**:
   ```bash
   ./scripts/dev-logs.sh  # Live tail both logs
   ```

2. **Run Status Checks**:
   ```bash
   ./scripts/dev-status.sh  # Comprehensive status report
   ```

3. **Review Documentation**:
   - [Architecture Diagrams](./deployment/ARCHITECTURE.md)
   - [Deployment Checklist](./deployment/DEPLOYMENT_CHECKLIST.md)
   - [Port Configuration](./deployment/PORT_CONFIGURATION.md)

4. **Check Project Issues**: Review existing issues in the repository

---

## Deep Dive Documentation

For detailed information on specific topics:

### Deployment & Configuration
- **[ARCHITECTURE.md](./deployment/ARCHITECTURE.md)** - System architecture diagrams and data flow
- **[DEPLOYMENT_CHECKLIST.md](./deployment/DEPLOYMENT_CHECKLIST.md)** - Pre-deployment verification checklist
- **[PORT_CONFIGURATION.md](./deployment/PORT_CONFIGURATION.md)** - Detailed port configuration and management
- **[SCRIPT_MIGRATION.md](./deployment/SCRIPT_MIGRATION.md)** - Migrating from legacy scripts

### Ngrok & Remote Access
- **[NGROK_CONFIGURATION_SUMMARY.md](./deployment/NGROK_CONFIGURATION_SUMMARY.md)** - Complete ngrok setup
- **[NGROK_FRONTEND_SETUP.md](./deployment/NGROK_FRONTEND_SETUP.md)** - Frontend configuration for ngrok
- **[NGROK_ACCESS.md](./deployment/NGROK_ACCESS.md)** - Ngrok access guide

### Security & Best Practices
- **[SECURITY.md](./deployment/SECURITY.md)** - Security considerations and best practices
- **[ACCESS_INFO.md](./deployment/ACCESS_INFO.md)** - Server access information

---

## Migration from Legacy Scripts

**⚠️ Deprecated Scripts** (in project root):
- `start_all.sh` - Use `./scripts/dev-start.sh` instead
- `start_server.sh` - Use `./scripts/dev-backend.sh start` instead
- `start_ngrok.sh` - Use `./scripts/ngrok_persistent.sh start` instead

**Why migrate?**
- Better error handling and recovery
- Health checks and status monitoring
- Consistent interface across all commands
- PID tracking for reliable process management
- Colored output for better readability

**📖 See**: [SCRIPT_MIGRATION.md](./deployment/SCRIPT_MIGRATION.md) for complete migration guide

---

## Deployment Checklist

Before deploying or sharing your environment:

### Pre-Deployment Verification

```bash
# ✅ 1. Check service status
./scripts/dev-status.sh

# ✅ 2. Run health checks
curl http://localhost:8081/health
curl http://localhost:8081/api/stats

# ✅ 3. Verify frontend builds
cd frontend && npm run build

# ✅ 4. Check for errors in logs
tail -100 logs/backend.log | grep -i error
tail -100 logs/frontend.log | grep -i error

# ✅ 5. Test key functionality
# - Load main pages
# - Test search
# - Verify data loads correctly
```

**📖 See**: [DEPLOYMENT_CHECKLIST.md](./deployment/DEPLOYMENT_CHECKLIST.md) for complete checklist

---

## Quick Reference Card

### Most Common Commands

```bash
# Start development environment
./scripts/dev-start.sh

# Check if everything is running
./scripts/dev-status.sh

# View real-time logs
./scripts/dev-logs.sh

# Stop everything
./scripts/dev-stop.sh

# Restart after code changes
./scripts/dev-start.sh --restart
```

### Port Reference

| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend | 8081 | http://localhost:8081 |
| Ngrok (public) | - | https://the-island.ngrok.app |
| Ngrok Dashboard | 4040 | http://localhost:4040 |

### Health Check URLs

```bash
# Backend health
curl http://localhost:8081/health

# Backend stats
curl http://localhost:8081/api/stats

# API documentation
open http://localhost:8081/docs
```

---

## Related Documentation

- **[CLAUDE.md](../CLAUDE.md)** - Main project entry point for AI assistants
- **[README.md](../README.md)** - Project overview and introduction
- **[docs/deployment/](./deployment/)** - Detailed deployment documentation
- **[docs/developer/](./developer/)** - Development guides and standards

---

**Last Updated**: 2025-11-21
**Maintained By**: Development Team
**Questions?** See [Troubleshooting](#troubleshooting) or check the [Deployment Documentation](./deployment/) directory.
