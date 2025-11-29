# Script Migration Guide

**Quick Summary**: **Migrating from Legacy Root Scripts to Modern Dev Scripts**...

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- [Overview](#overview)
- [Why Migrate?](#why-migrate)
- [Legacy vs Modern Scripts](#legacy-vs-modern-scripts)
- [Migration Examples](#migration-examples)
- [Breaking Changes](#breaking-changes)

---

**Migrating from Legacy Root Scripts to Modern Dev Scripts**

This guide explains the transition from legacy startup scripts in the project root to the new, improved dev management scripts in `/scripts/`.

---

## Table of Contents

- [Overview](#overview)
- [Why Migrate?](#why-migrate)
- [Legacy vs Modern Scripts](#legacy-vs-modern-scripts)
- [Migration Examples](#migration-examples)
- [Breaking Changes](#breaking-changes)
- [Backward Compatibility](#backward-compatibility)
- [Deprecation Timeline](#deprecation-timeline)

---

## Overview

### Legacy Scripts (Deprecated)

Located in project root:
- `start_all.sh` - Start backend + ngrok
- `start_server.sh` - Start backend only
- `start_ngrok.sh` - Start ngrok tunnel

**Status**: ⚠️ **DEPRECATED** - Will be removed in future release

### Modern Scripts (Current)

Located in `/scripts/`:
- `dev-start.sh` - Complete environment management
- `dev-backend.sh` - Backend service management
- `dev-frontend.sh` - Frontend service management
- `dev-stop.sh` - Stop all services
- `dev-status.sh` - Check service status
- `dev-logs.sh` - View logs
- `ngrok_persistent.sh` - Ngrok tunnel management

**Status**: ✅ **ACTIVE** - Recommended for all use cases

---

## Why Migrate?

### Problems with Legacy Scripts

❌ **No error handling** - Silent failures, difficult to debug
❌ **No health checks** - Don't verify services actually started
❌ **No process tracking** - Can't reliably stop services
❌ **No status reporting** - Hard to tell what's running
❌ **Port conflicts unhandled** - Fail when ports are in use
❌ **No log management** - Output goes to stdout only
❌ **Limited functionality** - Start only, no stop/restart/status
❌ **Inconsistent interface** - Different patterns across scripts

### Benefits of Modern Scripts

✅ **Robust error handling** - Clear error messages with recovery steps
✅ **Built-in health checks** - Verify services respond correctly
✅ **PID tracking** - Reliable process management
✅ **Comprehensive status** - See exactly what's running
✅ **Port conflict detection** - Prompt to kill conflicting processes
✅ **Centralized logging** - All logs in `logs/` directory
✅ **Full lifecycle management** - Start, stop, restart, status, logs
✅ **Consistent interface** - Same commands across all scripts
✅ **Colored output** - Easy to read status messages
✅ **Virtual environment validation** - Verify dependencies installed

---

## Legacy vs Modern Scripts

### Comparison Table

| Operation | Legacy Command | Modern Command | Improvements |
|-----------|---------------|----------------|--------------|
| Start backend | `./start_server.sh 8081` | `./scripts/dev-backend.sh start` | Health checks, PID tracking, error handling |
| Start ngrok | `./start_ngrok.sh` | `./scripts/ngrok_persistent.sh start` | Better tunnel management, status checks |
| Start both | `./start_all.sh` | `./scripts/dev-start.sh` | Includes frontend, better orchestration |
| Stop services | `lsof -ti:8081 \| xargs kill` | `./scripts/dev-stop.sh` | Graceful shutdown, cleanup |
| Check status | `lsof -i :8081` | `./scripts/dev-status.sh` | Full status report, health checks |
| View logs | `tail -f /tmp/epstein_*.log` | `./scripts/dev-logs.sh` | Centralized, organized logs |

---

## Migration Examples

### Example 1: Start Backend Server

**Before (Legacy)**:
```bash
./start_server.sh 8081
```

**After (Modern)**:
```bash
./scripts/dev-backend.sh start
```

**What Changed**:
- Port 8081 is now the default (no need to specify)
- Automatic health check after startup
- Process PID tracked for reliable management
- Logs written to `logs/backend.log`
- Virtual environment validation
- Port conflict detection

---

### Example 2: Start Backend + Ngrok

**Before (Legacy)**:
```bash
./start_all.sh
```

**After (Modern)**:
```bash
# Start backend
./scripts/dev-backend.sh start

# Start ngrok
./scripts/ngrok_persistent.sh start
```

**What Changed**:
- Split into separate commands for better control
- Can start services independently
- Better error handling for each service
- Health checks for both services
- Easy to restart individual services

**Pro Tip**: For full development environment including frontend:
```bash
./scripts/dev-start.sh
```

---

### Example 3: Start Ngrok Tunnel

**Before (Legacy)**:
```bash
./start_ngrok.sh
```

**After (Modern)**:
```bash
./scripts/ngrok_persistent.sh start
```

**What Changed**:
- Better tunnel status verification
- Automatic reconnection on failure
- Cleaner log output
- Easier to stop/restart

---

### Example 4: Check What's Running

**Before (Legacy)**:
```bash
# Manual checks required
lsof -i :8081  # Backend
lsof -i :5173  # Frontend
curl http://localhost:8081/health  # Health check
```

**After (Modern)**:
```bash
./scripts/dev-status.sh
```

**Output Example**:
```
🔵 Checking development environment status...

Backend Service:
  ✅ Running on port 8081 (PID: 12345)
  ✅ Health check: PASS
  📊 Stats: 1,637 entities, 38,482 documents

Frontend Service:
  ✅ Running on port 5173 (PID: 12346)
  ✅ Responding to requests

Logs:
  Backend:  logs/backend.log
  Frontend: logs/frontend.log
```

---

### Example 5: Stop Services

**Before (Legacy)**:
```bash
# Manual process killing
lsof -ti :8081 | xargs kill    # Backend
pkill -f 'ngrok start'         # Ngrok
# No way to stop frontend (wasn't managed)
```

**After (Modern)**:
```bash
# Stop all services
./scripts/dev-stop.sh

# Or stop individually
./scripts/dev-backend.sh stop
./scripts/dev-frontend.sh stop
pkill -f ngrok  # Or use ngrok_persistent.sh stop if available
```

**What Changed**:
- Graceful shutdown (SIGTERM before SIGKILL)
- Cleanup of PID files
- Verification that services stopped
- Single command to stop everything

---

### Example 6: View Logs

**Before (Legacy)**:
```bash
# Scattered log locations
tail -f /tmp/epstein_8081_venv.log  # Backend (if saved)
tail -f /tmp/ngrok_the-island.log   # Ngrok
# Frontend logs: nowhere (stdout only)
```

**After (Modern)**:
```bash
# Centralized log management
./scripts/dev-logs.sh           # Both services
./scripts/dev-backend.sh logs   # Backend only
./scripts/dev-frontend.sh logs  # Frontend only

# Or manual access
tail -f logs/backend.log
tail -f logs/frontend.log
```

**What Changed**:
- All logs in one location (`logs/` directory)
- Persistent logs (not just stdout)
- Easy access via management scripts
- Log rotation ready (can be added)

---

## Breaking Changes

### Port Changes

**Legacy Default**: Backend on port 8081 (if specified), Ngrok auto-detected
**Modern Default**: Backend on port 8081 (hardcoded as standard)

**Impact**: None - port 8081 is standard in both

---

### Log Locations

**Legacy Locations**:
- Backend: `/tmp/epstein_${PORT}_venv.log`
- Ngrok: `/tmp/ngrok_the-island.log`
- Frontend: stdout only (not saved)

**Modern Locations**:
- Backend: `logs/backend.log`
- Frontend: `logs/frontend.log`
- All services: Centralized in `logs/` directory

**Migration**: Update any scripts/tools that reference old log paths

---

### PID Files

**Legacy**: No PID tracking (manual process management)

**Modern**: PID files created:
- `.backend.pid` - Backend process ID
- `.frontend.pid` - Frontend process ID
- `.dev-pids` - JSON file with all service metadata

**Migration**: No action needed - new feature only

---

### Command Arguments

**Legacy**: Port as positional argument
```bash
./start_server.sh 8081  # Port specified
```

**Modern**: Port is hardcoded default, use flags for options
```bash
./scripts/dev-backend.sh start  # Port 8081 default
./scripts/dev-start.sh --backend-only  # Flags for options
```

**Migration**: Remove port arguments, use default 8081

---

## Backward Compatibility

### Legacy Scripts Still Work

The legacy scripts in the project root are **deprecated but not removed** to maintain backward compatibility.

**Current Status**:
- ✅ `start_server.sh` - Still works, logs to `/tmp/`
- ✅ `start_ngrok.sh` - Still works, logs to `/tmp/`
- ✅ `start_all.sh` - Still works, calls legacy scripts

**Recommendation**: Update to modern scripts as soon as possible

---

### Gradual Migration Strategy

You can migrate gradually:

1. **Phase 1**: Learn modern commands (run side-by-side)
   ```bash
   # Start with legacy
   ./start_server.sh 8081

   # Try modern commands for status/logs
   ./scripts/dev-status.sh
   ./scripts/dev-logs.sh
   ```

2. **Phase 2**: Use modern scripts for new workflows
   ```bash
   # New terminal sessions use modern scripts
   ./scripts/dev-backend.sh start
   ```

3. **Phase 3**: Fully switch to modern scripts
   ```bash
   # Stop using legacy scripts entirely
   ./scripts/dev-start.sh
   ```

---

## Deprecation Timeline

### Current Status (v1.0)

**Legacy Scripts**: ⚠️ **DEPRECATED** but functional
**Modern Scripts**: ✅ **RECOMMENDED** for all use cases

---

### Future Releases

#### v2.0 (Planned)

- Legacy scripts moved to `/scripts/deprecated/`
- Warning messages when using legacy scripts
- Documentation updated to remove legacy references

#### v3.0 (Future)

- Legacy scripts removed entirely
- Only modern scripts supported
- Breaking change noted in release notes

---

## Migration Checklist

Use this checklist to ensure complete migration:

### Scripts Migration

- [ ] Replace `start_server.sh` with `scripts/dev-backend.sh`
- [ ] Replace `start_ngrok.sh` with `scripts/ngrok_persistent.sh`
- [ ] Replace `start_all.sh` with `scripts/dev-start.sh`
- [ ] Add frontend management with `scripts/dev-frontend.sh`
- [ ] Use `scripts/dev-stop.sh` for cleanup
- [ ] Use `scripts/dev-status.sh` for monitoring

### Documentation Updates

- [ ] Update personal notes/documentation
- [ ] Update team runbooks
- [ ] Update deployment guides
- [ ] Update CI/CD scripts (if any)

### Tooling Updates

- [ ] Update IDE run configurations
- [ ] Update shell aliases
- [ ] Update automation scripts
- [ ] Update monitoring scripts

### Testing

- [ ] Verify backend starts correctly
- [ ] Verify frontend starts correctly
- [ ] Verify health checks pass
- [ ] Verify logs are accessible
- [ ] Verify stop/restart works
- [ ] Verify status reporting accurate

---

## Quick Reference

### Command Mapping

| Task | Legacy | Modern |
|------|--------|--------|
| Start backend | `./start_server.sh 8081` | `./scripts/dev-backend.sh start` |
| Start ngrok | `./start_ngrok.sh` | `./scripts/ngrok_persistent.sh start` |
| Start all | `./start_all.sh` | `./scripts/dev-start.sh` |
| Stop backend | `lsof -ti:8081 \| xargs kill` | `./scripts/dev-backend.sh stop` |
| Stop all | Manual kills | `./scripts/dev-stop.sh` |
| Check status | `lsof -i :8081` | `./scripts/dev-status.sh` |
| View logs | `tail -f /tmp/epstein_*.log` | `./scripts/dev-logs.sh` |

---

## Getting Help

### Issues with Migration?

1. **Check Status**: `./scripts/dev-status.sh`
2. **Check Logs**: `./scripts/dev-logs.sh`
3. **Review Main Guide**: [DEPLOYMENT.md](../DEPLOYMENT.md)
4. **Troubleshooting**: See [DEPLOYMENT.md#troubleshooting](../DEPLOYMENT.md#troubleshooting)

### Report Issues

If you encounter problems with the new scripts:
1. Check logs for error messages
2. Verify prerequisites (venv, dependencies)
3. Review this migration guide
4. Create an issue with details

---

## Summary

### Key Takeaways

1. **Modern scripts are better** - More reliable, better error handling
2. **Legacy scripts deprecated** - Will be removed in future release
3. **Migration is easy** - Simple command substitutions
4. **No breaking changes** - Port configuration remains the same
5. **Better developer experience** - Status checks, health monitoring, log management

### Next Steps

1. ✅ Read [DEPLOYMENT.md](../DEPLOYMENT.md) for complete guide
2. ✅ Try modern scripts in your workflow
3. ✅ Update personal documentation/aliases
4. ✅ Inform team members about changes
5. ✅ Report any issues or feedback

---

**Last Updated**: 2025-11-21
**Maintained By**: Development Team
**Questions?** See [DEPLOYMENT.md](../DEPLOYMENT.md) for comprehensive deployment guide.
