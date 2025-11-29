# DevOps Scripts Quick Reference

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- 🚀 Common Commands
- Start/Stop Development
- Quick Status Check
- Deployment
- 🎯 Use Cases

---

**One-page cheat sheet for Epstein Archive development operations**

## 🚀 Common Commands

### Start/Stop Development

```bash
./scripts/dev-start.sh              # Start both servers
./scripts/dev-stop.sh               # Stop both servers
./scripts/dev-status.sh             # Check status
./scripts/dev-logs.sh               # View logs
```

### Quick Status Check

```bash
./scripts/health-check.sh           # < 2 second health check
./scripts/dev-status.sh --compact   # Quick status summary
```

### Deployment

```bash
./scripts/deploy.sh --dry-run       # Test deployment
./scripts/deploy.sh --env staging   # Deploy to staging
./scripts/deploy.sh --rollback      # Rollback to previous
```

## 🎯 Use Cases

### "Just start the servers"
```bash
./scripts/dev-start.sh
# Visit: http://localhost:5173 (frontend)
# API: http://localhost:8000/api/rag/stats
```

### "Debug why something broke"
```bash
./scripts/dev-status.sh              # Check what's running
./scripts/dev-logs.sh --errors-only  # Show errors only
./scripts/health-check.sh --verbose  # Detailed health check
```

### "Clean restart everything"
```bash
./scripts/dev-stop.sh --force
./scripts/dev-start.sh --restart
```

### "Monitor in real-time"
```bash
./scripts/dev-logs.sh                # Follow both logs
./scripts/dev-logs.sh --backend-only # Only backend
./scripts/dev-logs.sh --frontend-only # Only frontend
```

### "Deploy to production"
```bash
# 1. Test locally
./scripts/deploy.sh --dry-run

# 2. Deploy to staging
./scripts/deploy.sh --env staging
./scripts/health-check.sh --verbose

# 3. Deploy to production (requires confirmation)
./scripts/deploy.sh --env production
```

## 🔧 Troubleshooting

### Port already in use
```bash
./scripts/dev-stop.sh --force
# or manually: lsof -ti :8000 | xargs kill -9
```

### Frontend won't start
```bash
cd frontend && npm install
./scripts/dev-start.sh --frontend-only
```

### Backend crashes on startup
```bash
source .venv/bin/activate
pip install -r requirements.txt
./scripts/dev-logs.sh --backend-only --errors-only
```

### "Where are my logs?"
```bash
ls -lh logs/
tail -f logs/backend.log
tail -f logs/frontend.log
```

## 📊 Script Options Summary

### dev-start.sh
- `--backend-only` - Only start backend
- `--frontend-only` - Only start frontend
- `--status` - Check status without starting
- `--restart` - Restart servers

### dev-stop.sh
- `--backend` - Stop only backend
- `--frontend` - Stop only frontend
- `--force` - Force kill processes

### dev-status.sh
- `--compact` - Brief output
- `--json` - JSON output (for scripts)

### dev-logs.sh
- `--backend-only` - Backend logs only
- `--frontend-only` - Frontend logs only
- `--last 50` - Last 50 lines
- `--errors-only` - Only errors/warnings
- `--grep "keyword"` - Filter by keyword

### health-check.sh
- `--verbose` - Show details
- `--timeout 5` - Custom timeout

### deploy.sh
- `--env {local|staging|production}` - Target environment
- `--dry-run` - Test without deploying
- `--rollback` - Rollback to previous
- `--skip-tests` - Skip tests (not recommended)

## 🌐 Default Ports

| Service | Port | URL |
|---------|------|-----|
| Backend | 8000 | http://localhost:8000 |
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8000 | http://localhost:8000/api/rag/stats |

## 📂 Important Files

| File | Purpose |
|------|---------|
| `.dev-pids` | Process IDs (JSON) |
| `.backend.pid` | Backend process ID |
| `.frontend.pid` | Frontend process ID |
| `logs/backend.log` | Backend logs |
| `logs/frontend.log` | Frontend logs |
| `deploy/*.tar.gz` | Deployment packages |
| `backups/backup-*` | Deployment backups |

## 🔴 Exit Codes

| Code | Meaning | Scripts |
|------|---------|---------|
| 0 | Success/Healthy | All |
| 1 | Critical failure | dev-status.sh, health-check.sh |
| 2 | Non-critical warning | health-check.sh |

## 🎨 Color Codes

- 🔵 **BLUE** - Info
- ✅ **GREEN** - Success
- ⚠️  **YELLOW** - Warning
- ❌ **RED** - Error

## ⚡ Environment Variables

```bash
export BACKEND_PORT=8000        # Backend port
export FRONTEND_PORT=5173       # Frontend port
export LOG_LEVEL=DEBUG          # Log verbosity
export DEPLOY_TARGET=staging    # Deployment target
export BACKUP_COUNT=5           # Number of backups
```

## 📚 Documentation

- **Full DevOps Guide**: `scripts/DEVOPS_README.md`
- **Data Scripts**: `scripts/README.md`
- **Project Docs**: `docs/README.md`
- **API Docs**: http://localhost:8000/docs (when running)

## 💡 Pro Tips

1. **Always check status first**: `./scripts/dev-status.sh --compact`
2. **Use --dry-run before deploying**: Test without risk
3. **Monitor logs during development**: `./scripts/dev-logs.sh`
4. **Health check before committing**: `./scripts/health-check.sh`
5. **Backup automatically happens**: During deployment
6. **Graceful shutdown with Ctrl+C**: In dev-start.sh

## 🆘 Emergency Commands

```bash
# Kill everything
./scripts/dev-stop.sh --force
pkill -f uvicorn
pkill -f vite

# Clean restart
rm -f .*.pid .dev-pids
./scripts/dev-start.sh

# Fresh install
source .venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install

# Check what's running
ps aux | grep -E "(uvicorn|vite)"
lsof -i :8000
lsof -i :5173
```

---

**Last Updated:** 2025-11-20
**For full documentation**: `scripts/DEVOPS_README.md`
