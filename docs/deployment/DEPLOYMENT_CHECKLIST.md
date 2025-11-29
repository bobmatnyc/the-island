# Deployment Checklist

**Quick Summary**: **Epstein Document Archive** - Comprehensive pre-deployment and deployment verification checklist. .

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- [Quick Checklist](#quick-checklist)
- [Pre-Deployment Verification](#pre-deployment-verification)
- [Service Startup](#service-startup)
- [Health Check Verification](#health-check-verification)
- [Functional Testing](#functional-testing)

---

**Epstein Document Archive** - Comprehensive pre-deployment and deployment verification checklist.

Use this checklist to ensure your deployment is production-ready and all systems are functioning correctly.

---

## Table of Contents

- [Quick Checklist](#quick-checklist)
- [Pre-Deployment Verification](#pre-deployment-verification)
- [Service Startup](#service-startup)
- [Health Check Verification](#health-check-verification)
- [Functional Testing](#functional-testing)
- [Performance Validation](#performance-validation)
- [Security Verification](#security-verification)
- [Post-Deployment Validation](#post-deployment-validation)
- [Common Failure Modes](#common-failure-modes)
- [Rollback Procedure](#rollback-procedure)

---

## Quick Checklist

**Use this for rapid verification before starting development:**

```bash
# ✅ 1. Prerequisites
[ ] Virtual environment exists (.venv/)
[ ] Backend dependencies installed (pip list)
[ ] Frontend dependencies installed (node_modules/)

# ✅ 2. Start Services
[ ] Backend starts without errors
[ ] Frontend starts without errors
[ ] No port conflicts

# ✅ 3. Basic Health
[ ] Backend health endpoint responds
[ ] Frontend loads in browser
[ ] API requests work

# ✅ 4. Quick Test
[ ] Can view entities page
[ ] Can view flights page
[ ] Search functionality works

# All checks passed? Ready to develop! 🎉
```

**Commands**:
```bash
./scripts/dev-start.sh       # Start everything
./scripts/dev-status.sh      # Verify status
curl http://localhost:8081/health  # Health check
```

---

## Pre-Deployment Verification

### Environment Setup

#### Virtual Environment

```bash
# Check virtual environment exists
[ ] ls -la .venv/bin/activate
[ ] source .venv/bin/activate
[ ] which python3  # Should point to .venv/bin/python3
```

**Command**:
```bash
if [ -f .venv/bin/activate ]; then
    echo "✅ Virtual environment exists"
else
    echo "❌ Virtual environment missing - run: python3 -m venv .venv"
fi
```

---

#### Python Dependencies

```bash
[ ] pip list | grep fastapi
[ ] pip list | grep uvicorn
[ ] pip list | grep pydantic
[ ] pip list | grep numpy
[ ] pip list | grep requests
```

**Command**:
```bash
source .venv/bin/activate
pip list | grep -E 'fastapi|uvicorn|pydantic' && echo "✅ Key dependencies installed" || echo "❌ Missing dependencies - run: pip install -r requirements.txt"
```

---

#### Node.js Dependencies

```bash
[ ] ls -la frontend/node_modules/
[ ] ls frontend/node_modules/react
[ ] ls frontend/node_modules/vite
```

**Command**:
```bash
if [ -d frontend/node_modules ]; then
    echo "✅ Frontend dependencies installed"
else
    echo "❌ Frontend dependencies missing - run: cd frontend && npm install"
fi
```

---

#### Data Files

```bash
[ ] ls -la data/
[ ] ls data/entities/ENTITIES_INDEX.json
[ ] ls data/metadata/entity_network.json
[ ] ls data/metadata/entity_statistics.json
```

**Command**:
```bash
if [ -f data/entities/ENTITIES_INDEX.json ]; then
    echo "✅ Data files present"
else
    echo "⚠️  Data files missing - may need initialization"
fi
```

---

### Port Availability

```bash
# Check ports are free before starting
[ ] lsof -i :8081  # Backend port (should be empty)
[ ] lsof -i :5173  # Frontend port (should be empty)
[ ] lsof -i :4040  # Ngrok dashboard (if using ngrok)
```

**Command**:
```bash
# Quick port check
for port in 8081 5173; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port in use"
    else
        echo "✅ Port $port available"
    fi
done
```

---

### Configuration Files

```bash
# Backend configuration
[ ] ls server/app.py
[ ] grep "port.*8081" server/app.py

# Frontend configuration
[ ] ls frontend/.env.example
[ ] ls frontend/vite.config.ts
```

**Command**:
```bash
if [ -f server/app.py ] && [ -f frontend/vite.config.ts ]; then
    echo "✅ Configuration files present"
else
    echo "❌ Missing configuration files"
fi
```

---

## Service Startup

### Step 1: Start Backend

```bash
[ ] Run: ./scripts/dev-backend.sh start
[ ] Wait for "Backend is healthy!" message
[ ] Verify process running: lsof -i :8081
[ ] Check logs: tail -20 logs/backend.log
```

**Expected Output**:
```
🔵 [Backend] Starting backend server...
🔵 [Backend] Backend starting (PID: 12345)...
✅ [Backend] Backend process running (PID: 12345)
🔵 [Backend] Running health check...
✅ [Backend] Backend is healthy!
✅ [Backend] Response: {"status":"ok",...}
```

**Failure Indicators**:
- ❌ "Port 8081 is already in use"
- ❌ "Backend failed to start"
- ❌ "Health check failed"

---

### Step 2: Start Frontend

```bash
[ ] Run: ./scripts/dev-frontend.sh start
[ ] Wait for "Frontend started" message
[ ] Verify process running: lsof -i :5173
[ ] Check logs: tail -20 logs/frontend.log
```

**Expected Output**:
```
Frontend started on PID 12346
URL: http://localhost:5173
Logs: logs/frontend.log
```

**Failure Indicators**:
- ❌ "Port 5173 is already in use"
- ❌ "npm not found"
- ❌ "Module not found" errors in logs

---

### Step 3: Optional - Start Ngrok

```bash
[ ] Run: ./scripts/ngrok_persistent.sh start
[ ] Wait for tunnel to establish
[ ] Verify tunnel: curl -s http://localhost:4040/api/tunnels
[ ] Check public URL: curl https://the-island.ngrok.app/health
```

**Expected Output**:
```
✅ Ngrok tunnel established
Public URL: https://the-island.ngrok.app
Dashboard: http://localhost:4040
```

---

## Health Check Verification

### Backend Health Checks

#### Basic Health Endpoint

```bash
[ ] curl http://localhost:8081/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "timestamp": "2025-11-21T10:00:00.000000",
  "service": "epstein-archive-api",
  "version": "1.0.0"
}
```

**Checklist**:
- [ ] Status is "ok"
- [ ] Timestamp is recent
- [ ] Service name correct
- [ ] HTTP 200 status code

---

#### API Stats Endpoint

```bash
[ ] curl http://localhost:8081/api/stats
```

**Expected Response**:
```json
{
  "entities": 1637,
  "documents": 38482,
  "flights": 1167,
  "relationships": 5423
}
```

**Checklist**:
- [ ] Returns valid JSON
- [ ] Entity count > 0
- [ ] Document count > 0
- [ ] Flight count > 0
- [ ] HTTP 200 status code

---

#### API Documentation

```bash
[ ] curl -I http://localhost:8081/docs
[ ] Open http://localhost:8081/docs in browser
```

**Checklist**:
- [ ] Returns HTTP 200
- [ ] Swagger UI loads
- [ ] All endpoints visible
- [ ] Can test endpoints

---

### Frontend Health Checks

#### Frontend Loads

```bash
[ ] curl -I http://localhost:5173
[ ] Open http://localhost:5173 in browser
```

**Checklist**:
- [ ] Returns HTTP 200
- [ ] Page loads without errors
- [ ] No console errors (check DevTools)
- [ ] React app renders

---

#### API Connection

```bash
# Open browser DevTools → Network tab
[ ] Navigate to http://localhost:5173
[ ] Check Network tab for API requests
[ ] Verify requests go to correct backend URL
```

**Checklist**:
- [ ] Requests to http://localhost:8081/api/* (or ngrok URL)
- [ ] Requests return 200 status
- [ ] No CORS errors in console
- [ ] Data loads correctly

---

## Functional Testing

### Core Functionality Tests

#### 1. Home Page

```bash
# Visit http://localhost:5173
[ ] Homepage loads
[ ] Statistics displayed (entities, documents, flights)
[ ] No errors in console
[ ] Navigation menu works
```

---

#### 2. Entities Page

```bash
# Visit http://localhost:5173/entities
[ ] Entity list loads
[ ] At least 10 entities visible
[ ] Search box functional
[ ] Can filter entities
[ ] Entity cards clickable
```

**Test Command**:
```bash
curl http://localhost:8081/api/entities?limit=5
# Should return array of entities
```

---

#### 3. Entity Detail Page

```bash
# Click on any entity
[ ] Entity detail page loads
[ ] Biography displayed
[ ] Connections shown
[ ] Related documents listed
[ ] Flight history visible
[ ] Back button works
```

---

#### 4. Flights Page

```bash
# Visit http://localhost:5173/flights
[ ] Flight list loads
[ ] Flight map renders
[ ] Can interact with map
[ ] Flight details expandable
[ ] Date filters work
```

**Test Command**:
```bash
curl http://localhost:8081/api/flights?limit=5
# Should return array of flights
```

---

#### 5. Documents Page

```bash
# Visit http://localhost:5173/documents
[ ] Document list loads
[ ] Can view document categories
[ ] Document viewer works
[ ] Search/filter functional
[ ] Pagination works
```

---

#### 6. Search Functionality

```bash
# Use search box in header
[ ] Search box visible
[ ] Can type search query
[ ] Search results appear
[ ] Results are relevant
[ ] Can click results to navigate
```

**Test Command**:
```bash
curl -X POST http://localhost:8081/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Clinton", "limit": 5}'
# Should return search results
```

---

#### 7. Timeline/Activity

```bash
# Visit http://localhost:5173/activity or /timeline
[ ] Timeline loads
[ ] Events displayed chronologically
[ ] Can scroll through timeline
[ ] Event details expandable
[ ] Date navigation works
```

---

#### 8. Network Graph

```bash
# Visit http://localhost:5173/network
[ ] Network visualization loads
[ ] Nodes and edges visible
[ ] Can zoom/pan
[ ] Can click nodes
[ ] Legend displayed
```

---

## Performance Validation

### Response Time Checks

```bash
# Backend response times
[ ] /health endpoint < 100ms
[ ] /api/stats endpoint < 500ms
[ ] /api/entities endpoint < 1000ms
[ ] /api/search endpoint < 2000ms
```

**Test Commands**:
```bash
# Use curl with timing
time curl -s http://localhost:8081/health > /dev/null
time curl -s http://localhost:8081/api/stats > /dev/null
time curl -s http://localhost:8081/api/entities?limit=100 > /dev/null
```

---

### Frontend Performance

```bash
# Browser DevTools → Performance tab
[ ] Initial page load < 3 seconds
[ ] Time to Interactive < 5 seconds
[ ] No layout shifts (CLS < 0.1)
[ ] Smooth scrolling (60fps)
```

---

### Memory Usage

```bash
# Check backend memory
[ ] Backend process < 500MB RAM
[ ] No memory leaks over time

# Check frontend memory
[ ] Browser tab < 300MB RAM
[ ] No memory leaks over time
```

**Commands**:
```bash
# Backend memory check
ps aux | grep "python.*app.py" | awk '{print $6/1024 " MB"}'

# Monitor over time
watch -n 5 'ps aux | grep "python.*app.py" | awk "{print \$6/1024 \" MB\"}"'
```

---

## Security Verification

### Backend Security

```bash
[ ] CORS configured appropriately
[ ] No sensitive data in logs
[ ] Error messages don't leak info
[ ] API rate limiting considered (if needed)
```

**Check CORS**:
```bash
grep -A 5 "CORSMiddleware" server/app.py
# Should show appropriate origins
```

---

### Frontend Security

```bash
[ ] No API keys in frontend code
[ ] .env file not committed to git
[ ] HTTPS used for production (ngrok)
[ ] No console.log with sensitive data
```

**Check .gitignore**:
```bash
grep ".env" .gitignore
# Should include .env files
```

---

### Network Security

```bash
[ ] Ngrok URL not shared publicly (if sensitive)
[ ] Backend not exposed unnecessarily
[ ] Firewall rules appropriate
```

---

## Post-Deployment Validation

### Monitoring Setup

```bash
[ ] Logs accessible: ./scripts/dev-logs.sh
[ ] Can monitor real-time: tail -f logs/backend.log
[ ] Error alerts configured (if production)
[ ] Health check monitoring (if production)
```

---

### Backup Verification

```bash
[ ] Data directory backed up
[ ] Configuration backed up
[ ] Can restore from backup
```

---

### Documentation Updated

```bash
[ ] README.md reflects current state
[ ] Deployment docs updated
[ ] Known issues documented
[ ] Team notified of deployment
```

---

## Common Failure Modes

### Issue 1: Port Already in Use

**Symptoms**:
- "Address already in use" error
- "Port 8081 is already in use"

**Resolution**:
```bash
# 1. Find process using port
lsof -i :8081

# 2. Kill process
lsof -ti :8081 | xargs kill

# 3. Or use stop script
./scripts/dev-stop.sh

# 4. Retry startup
./scripts/dev-start.sh
```

**Prevention**:
- Always use `./scripts/dev-stop.sh` before restarting
- Check status before starting: `./scripts/dev-status.sh`

---

### Issue 2: Backend Health Check Fails

**Symptoms**:
- Backend starts but health check times out
- "Backend health check failed after 10 attempts"

**Resolution**:
```bash
# 1. Check if backend is actually running
lsof -i :8081

# 2. Check backend logs for errors
tail -50 logs/backend.log

# 3. Test health endpoint manually
curl -v http://localhost:8081/health

# 4. Check for Python errors
python3 server/app.py 8081  # Run in foreground to see errors
```

**Common Causes**:
- Missing dependencies
- Data file corruption
- Python version incompatibility
- Configuration errors

---

### Issue 3: Frontend Can't Connect to Backend

**Symptoms**:
- Frontend loads but shows no data
- CORS errors in console
- "Network Error" messages

**Resolution**:
```bash
# 1. Verify backend is running
curl http://localhost:8081/health

# 2. Check frontend .env configuration
cat frontend/.env
# Should have correct VITE_API_BASE_URL

# 3. Verify CORS settings
grep -A 5 "CORSMiddleware" server/app.py

# 4. Restart frontend (if .env changed)
./scripts/dev-frontend.sh restart
```

---

### Issue 4: Changes Not Appearing

**Symptoms**:
- Code changes don't show in browser
- Old version still running

**Resolution**:
```bash
# Backend changes:
./scripts/dev-backend.sh restart

# Frontend changes:
./scripts/dev-frontend.sh restart

# Or hard refresh browser:
# Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)

# Clear all and restart:
./scripts/dev-stop.sh
./scripts/dev-start.sh
```

---

### Issue 5: Ngrok Tunnel Fails

**Symptoms**:
- "ERR_NGROK_3200" error
- Tunnel not accessible

**Resolution**:
```bash
# 1. Check ngrok status
curl -s http://localhost:4040/api/tunnels | python3 -m json.tool

# 2. Restart ngrok
pkill -f ngrok
./scripts/ngrok_persistent.sh start

# 3. Verify backend is running
curl http://localhost:8081/health

# 4. Test tunnel
curl https://the-island.ngrok.app/health
```

---

## Rollback Procedure

### Emergency Rollback Steps

If deployment fails and you need to rollback:

```bash
# 1. Stop all services
./scripts/dev-stop.sh

# 2. Restore from backup (if applicable)
cp -r backup/data/ data/

# 3. Checkout previous version (if using git)
git log --oneline -10  # Find previous working commit
git checkout <commit-hash>

# 4. Reinstall dependencies (if changed)
source .venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 5. Restart services
./scripts/dev-start.sh

# 6. Verify rollback successful
./scripts/dev-status.sh
```

---

## Deployment Sign-Off

### Final Verification

```bash
# All checks must pass before considering deployment complete

✅ Core Services:
[ ] Backend healthy
[ ] Frontend responding
[ ] Logs accessible

✅ Functionality:
[ ] All pages load
[ ] Search works
[ ] Data displays correctly

✅ Performance:
[ ] Response times acceptable
[ ] No memory leaks
[ ] Smooth user experience

✅ Security:
[ ] CORS configured
[ ] No sensitive data exposed
[ ] .env files protected

✅ Monitoring:
[ ] Logs being written
[ ] Can monitor status
[ ] Alert system configured (if production)

✅ Documentation:
[ ] Deployment documented
[ ] Team notified
[ ] Known issues logged
```

**Deployment Status**: [ ] APPROVED  [ ] REJECTED

**Signed Off By**: ___________________

**Date**: ___________________

---

## Related Documentation

- **[DEPLOYMENT.md](../DEPLOYMENT.md)** - Complete deployment guide
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture diagrams
- **[PORT_CONFIGURATION.md](./PORT_CONFIGURATION.md)** - Port configuration details
- **[SCRIPT_MIGRATION.md](./SCRIPT_MIGRATION.md)** - Legacy script migration

---

**Last Updated**: 2025-11-21
**Maintained By**: Development Team
**Questions?** See [DEPLOYMENT.md](../DEPLOYMENT.md) for comprehensive deployment guide.
