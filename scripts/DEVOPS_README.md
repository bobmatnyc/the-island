# Development & Deployment Scripts

Comprehensive script collection for managing the Epstein Archive development environment, deployment, and monitoring.

## 📋 Quick Start

### Starting Development Environment

```bash
# Start both backend and frontend
./scripts/dev-start.sh

# Start only backend (FastAPI on port 8000)
./scripts/dev-start.sh --backend-only

# Start only frontend (Vite on port 5173)
./scripts/dev-start.sh --frontend-only

# Check status before starting
./scripts/dev-start.sh --status

# Restart both servers
./scripts/dev-start.sh --restart
```

### Stopping Development Environment

```bash
# Stop all servers
./scripts/dev-stop.sh

# Stop only backend
./scripts/dev-stop.sh --backend

# Stop only frontend
./scripts/dev-stop.sh --frontend

# Force kill if graceful shutdown fails
./scripts/dev-stop.sh --force
```

### Checking Status

```bash
# Full status report
./scripts/dev-status.sh

# Compact output
./scripts/dev-status.sh --compact

# JSON output (for scripting)
./scripts/dev-status.sh --json
```

### Viewing Logs

```bash
# Follow both server logs
./scripts/dev-logs.sh

# Follow only backend logs
./scripts/dev-logs.sh --backend-only

# Follow only frontend logs
./scripts/dev-logs.sh --frontend-only

# Show last 50 lines
./scripts/dev-logs.sh --last 50

# Show only errors
./scripts/dev-logs.sh --errors-only

# Filter by keyword
./scripts/dev-logs.sh --grep "authentication"
```

## 🏥 Health Checks

### Quick Health Check

```bash
# Quick check (< 2 seconds)
./scripts/health-check.sh

# Verbose output
./scripts/health-check.sh --verbose

# Custom timeout
./scripts/health-check.sh --timeout 5
```

**Exit Codes:**
- `0` - All services healthy
- `1` - Critical services down
- `2` - Non-critical issues

**Use Cases:**
- Monitoring systems (Nagios, Datadog)
- CI/CD pipelines
- Pre-deployment verification
- Health check endpoints

## 🚀 Deployment

### Deploy to Environments

```bash
# Deploy to staging
./scripts/deploy.sh --env staging

# Deploy to production (requires confirmation)
./scripts/deploy.sh --env production

# Dry run (test without deploying)
./scripts/deploy.sh --dry-run

# Skip tests (not recommended)
./scripts/deploy.sh --skip-tests
```

### Rollback

```bash
# Rollback to previous version
./scripts/deploy.sh --rollback
```

**Deployment Process:**
1. ✅ Stop development servers
2. ✅ Run Python tests (pytest)
3. ✅ Run frontend tests
4. ✅ Build frontend for production
5. ✅ Run API smoke tests
6. ✅ Backup current deployment
7. ✅ Create deployment package
8. ✅ Deploy to environment
9. ✅ Verify deployment
10. ✅ Rollback on failure (optional)

**Deployment Artifacts:**
- `deploy/epstein-archive-{env}-{timestamp}.tar.gz` - Deployment package
- `backups/backup-{timestamp}-frontend/` - Frontend backup
- `backups/backup-{timestamp}-backend/` - Backend backup

## 📊 Status & Monitoring

### Process Information

The scripts track processes using PID files:

**PID Files:**
- `.dev-pids` - JSON file with both backend and frontend PIDs
- `.backend.pid` - Backend process ID
- `.frontend.pid` - Frontend process ID

**PID File Format (.dev-pids):**
```json
{
  "backend": {
    "pid": 12345,
    "port": 8000,
    "started_at": "2025-11-20T11:30:00",
    "log_file": "logs/backend.log"
  },
  "frontend": {
    "pid": 12346,
    "port": 5173,
    "started_at": "2025-11-20T11:30:00",
    "log_file": "logs/frontend.log"
  }
}
```

### Log Files

All logs are stored in `logs/` directory:

- `logs/backend.log` - FastAPI/uvicorn logs
- `logs/frontend.log` - Vite dev server logs

**Log Rotation:**
Logs are appended (not rotated). For production, configure logrotate or similar.

## 🔧 Environment Variables

All scripts support environment variable configuration:

```bash
# Backend port (default: 8000)
export BACKEND_PORT=8000

# Frontend port (default: 5173)
export FRONTEND_PORT=5173

# Log level (default: INFO)
export LOG_LEVEL=DEBUG

# Deployment target
export DEPLOY_TARGET=staging

# Backup count (default: 3)
export BACKUP_COUNT=5
```

## 🎨 Color Codes & Symbols

All scripts use consistent color coding:

- 🔵 **Blue (INFO)**: Informational messages
- ✅ **Green (SUCCESS)**: Success messages
- ⚠️  **Yellow (WARNING)**: Warning messages
- ❌ **Red (ERROR)**: Error messages

## 🧪 Testing Integration

### Running Tests Before Deployment

```bash
# Full test suite
./scripts/deploy.sh --env local

# Skip tests (not recommended)
./scripts/deploy.sh --env local --skip-tests
```

**Test Suite:**
1. Python tests (pytest)
2. Frontend tests (npm test with CI=true)
3. API smoke tests:
   - `/api/rag/stats` endpoint
   - `/api/news/stats` endpoint
   - Database connections
   - Vector store accessibility

## 📦 Prerequisites

### System Requirements

```bash
# Required commands
- bash (POSIX-compatible shell)
- curl (HTTP client)
- lsof (list open files)
- ps (process status)
- python3 (Python interpreter)
- npm (Node.js package manager)
- tar (archive utility)

# Check if installed
command -v bash curl lsof ps python3 npm tar
```

### Project Setup

```bash
# 1. Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Install frontend dependencies
cd frontend
npm install

# 3. Create logs directory
mkdir -p logs

# 4. Make scripts executable
chmod +x scripts/*.sh
```

## 🔒 Port Management

### Default Ports

- **Backend**: 8000 (FastAPI/uvicorn)
- **Frontend**: 5173 (Vite dev server)

### Port Conflict Resolution

If ports are in use, `dev-start.sh` will:
1. Detect the conflict
2. Identify the process using the port
3. Offer to kill the existing process
4. Wait for confirmation (y/n)

**Manual Port Management:**

```bash
# Check what's using a port
lsof -i :8000

# Kill process on port
kill $(lsof -t -i :8000)

# Use custom ports
BACKEND_PORT=9000 FRONTEND_PORT=6173 ./scripts/dev-start.sh
```

## 🛠️ Troubleshooting

### Common Issues

#### Ports Already in Use

```bash
# Find and kill processes
./scripts/dev-stop.sh --force

# Or manually
lsof -ti :8000 | xargs kill -9
lsof -ti :5173 | xargs kill -9
```

#### Virtual Environment Not Found

```bash
# Create virtual environment
python3 -m venv .venv

# Activate and install dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

#### Frontend Dependencies Missing

```bash
# Install dependencies
cd frontend
npm install
```

#### Process Dies During Startup

```bash
# Check logs
tail -f logs/backend.log
tail -f logs/frontend.log

# Or use log viewer
./scripts/dev-logs.sh --errors-only
```

#### Health Check Fails

```bash
# Detailed health check
./scripts/health-check.sh --verbose

# Check individual services
curl http://localhost:8000/api/rag/stats
curl http://localhost:5173
```

## 📖 Script Reference

### dev-start.sh

**Purpose:** Start development environment with health monitoring

**Features:**
- ✅ Port conflict detection and resolution
- ✅ Health checks after startup
- ✅ Process monitoring (auto-restart on crash)
- ✅ Graceful shutdown (Ctrl+C)
- ✅ PID tracking
- ✅ Log aggregation

**Options:**
- `--backend-only` - Start only backend
- `--frontend-only` - Start only frontend
- `--status` - Check status without starting
- `--restart` - Restart both servers

### dev-stop.sh

**Purpose:** Gracefully stop development servers

**Features:**
- ✅ Graceful shutdown (SIGTERM)
- ✅ Force kill option (SIGKILL)
- ✅ Port verification
- ✅ PID cleanup

**Options:**
- `--backend` - Stop only backend
- `--frontend` - Stop only frontend
- `--force` - Force kill if graceful fails

### dev-status.sh

**Purpose:** Comprehensive status monitoring

**Features:**
- ✅ Process status (running/stopped)
- ✅ Port availability checks
- ✅ Health checks (HTTP endpoints)
- ✅ Memory usage
- ✅ Uptime tracking
- ✅ Recent logs preview

**Options:**
- `--compact` - Compact output
- `--json` - JSON output for scripting

**Exit Codes:**
- `0` - All services healthy
- `1` - One or more services have issues

### dev-logs.sh

**Purpose:** View and filter server logs

**Features:**
- ✅ Color-coded by service
- ✅ Follow mode (like `tail -f`)
- ✅ Error filtering
- ✅ Keyword search
- ✅ Timestamped output

**Options:**
- `--backend-only` - Only backend logs
- `--frontend-only` - Only frontend logs
- `--last N` - Last N lines from each
- `--errors-only` - Only error messages
- `--grep "keyword"` - Filter by keyword
- `--no-follow` - Don't follow (show and exit)

### health-check.sh

**Purpose:** Fast health check for monitoring systems

**Features:**
- ✅ Completes in < 2 seconds
- ✅ Checks critical endpoints
- ✅ Proper exit codes
- ✅ Monitoring system compatible

**Options:**
- `--verbose` - Show details
- `--timeout N` - Custom timeout (seconds)

**Exit Codes:**
- `0` - All services healthy
- `1` - Critical services down
- `2` - Non-critical issues

### deploy.sh

**Purpose:** Production deployment with testing and rollback

**Features:**
- ✅ Full test suite integration
- ✅ Frontend production build
- ✅ Deployment packaging
- ✅ Backup before deployment
- ✅ Verification after deployment
- ✅ Automatic rollback on failure
- ✅ Multiple environment support

**Options:**
- `--env {staging|production}` - Target environment
- `--dry-run` - Test without deploying
- `--rollback` - Rollback to previous version
- `--skip-tests` - Skip test suite (not recommended)

**Environments:**
- `local` - Deploy locally (default)
- `staging` - Deploy to staging server
- `production` - Deploy to production (requires confirmation)

## 🔐 Security Notes

### Production Deployment

- **Never skip tests** in production deployments
- **Always run dry-run** first
- **Verify backups** before deployment
- **Monitor logs** during deployment
- **Have rollback plan** ready

### Environment Variables

- **Don't commit** `.env.local` files
- **Use secrets management** for production
- **Rotate API keys** regularly
- **Audit access logs** periodically

## 📝 Best Practices

### Development Workflow

1. Start development servers: `./scripts/dev-start.sh`
2. Monitor status: `./scripts/dev-status.sh`
3. View logs: `./scripts/dev-logs.sh`
4. Make changes (auto-reload enabled)
5. Stop servers: `./scripts/dev-stop.sh`

### Deployment Workflow

1. Run tests: `./scripts/deploy.sh --dry-run`
2. Deploy to staging: `./scripts/deploy.sh --env staging`
3. Verify staging: `./scripts/health-check.sh --verbose`
4. Deploy to production: `./scripts/deploy.sh --env production`
5. Monitor production: `./scripts/dev-logs.sh`

### Monitoring Workflow

1. Quick health check: `./scripts/health-check.sh`
2. Detailed status: `./scripts/dev-status.sh`
3. View logs: `./scripts/dev-logs.sh --errors-only`
4. Debug issues: `./scripts/dev-logs.sh --grep "error"`

## 🤝 Contributing

When adding new scripts:

1. Follow existing naming conventions
2. Add comprehensive help text (header comments)
3. Use consistent color codes and symbols
4. Add error handling for all edge cases
5. Support environment variables
6. Document in this README
7. Make executable: `chmod +x scripts/your-script.sh`

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vite Documentation](https://vitejs.dev/)
- [Bash Scripting Guide](https://www.gnu.org/software/bash/manual/)
- [POSIX Shell Standards](https://pubs.opengroup.org/onlinepubs/9699919799/)

## 📞 Support

For issues or questions:

1. Check logs: `./scripts/dev-logs.sh --errors-only`
2. Verify status: `./scripts/dev-status.sh --verbose`
3. Review troubleshooting section above
4. Check project documentation in `/docs`

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0
**Maintainer:** Epstein Archive Development Team
