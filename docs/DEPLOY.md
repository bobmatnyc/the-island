# Deployment Guide - Ngrok Configuration

**Quick Summary**: Critical deployment information for the Epstein Archive ngrok tunnel configuration.

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-28

**Key Points**:
- [Critical Port Configuration](#critical-port-configuration)
- [Why the-island.ngrok.app Breaks](#why-the-islandngrokapps-breaks)
- [Quick Fix Guide](#quick-fix-guide)
- [Port Change Procedure](#port-change-procedure)
- [Deployment Verification](#deployment-verification)

---

## Overview

This document provides critical deployment information for the Epstein Archive application, with particular focus on the **ngrok tunnel configuration** and **port management**.

> **⚠️ CRITICAL**: The ngrok URL `https://the-island.ngrok.app` is **port-specific**. If you change ports, the tunnel will break and must be reconfigured.

---

## Table of Contents

- [Critical Port Configuration](#critical-port-configuration)
- [Why the-island.ngrok.app Breaks](#why-the-islandngrokapps-breaks)
- [Quick Fix Guide](#quick-fix-guide)
- [Port Change Procedure](#port-change-procedure)
- [Current Configuration](#current-configuration)
- [Deployment Verification](#deployment-verification)
- [Troubleshooting](#troubleshooting)
- [Related Documentation](#related-documentation)

---

## Critical Port Configuration

### ⚠️ Port-Dependent Ngrok Tunnel

The Epstein Archive uses a **persistent ngrok domain** (`the-island.ngrok.app`) which is hardcoded to forward to a **specific local port**.

**Current Configuration**:
- **Ngrok Domain**: `the-island.ngrok.app`
- **Backend Port**: `8081`
- **Frontend Port**: `5173`
- **Ngrok Dashboard**: `4040`

**What This Means**:
- The ngrok tunnel is configured in `scripts/ngrok_persistent.sh` to forward `the-island.ngrok.app` → `localhost:8081`
- If you change the backend port from `8081` to something else, the ngrok tunnel will **still forward to port 8081**
- This creates a mismatch: ngrok sends traffic to the old port, but your backend is listening on a new port
- **Result**: `https://the-island.ngrok.app` stops working

---

## Why the-island.ngrok.app Breaks

### The Problem

When you change the backend port (for example, from `8081` to `8000`):

1. **You update** `ecosystem.config.js` to use the new port
2. **You restart** the backend on the new port
3. **Ngrok still forwards** to the old port (`8081`)
4. **Traffic is lost** because nothing is listening on `8081` anymore

### Port Configuration Files

The backend port is configured in **multiple locations** that must stay synchronized:

| File | Configuration | Purpose |
|------|---------------|---------|
| `ecosystem.config.js` | `--port 8081` | Backend startup port |
| `scripts/ngrok_persistent.sh` | `LOCAL_PORT="8081"` | Ngrok tunnel target |
| `frontend/vite.config.ts` | `target: 'http://localhost:8081'` | Frontend proxy |
| `frontend/.env` | `VITE_API_BASE_URL=https://the-island.ngrok.app` | Frontend API URL |

### What Breaks

When ports get out of sync:

```bash
# Backend starts on new port
Backend: Listening on port 8000 ✅

# Ngrok still forwards to old port
Ngrok: the-island.ngrok.app → localhost:8081 ❌

# Result
curl https://the-island.ngrok.app/health
# Error: Connection refused (nothing listening on 8081)
```

---

## Quick Fix Guide

### If the-island.ngrok.app Stops Working

**Symptoms**:
- `curl https://the-island.ngrok.app/health` fails
- Frontend shows "Cannot connect to backend"
- Browser console shows network errors

**Quick Diagnosis**:

```bash
# 1. Check what port backend is actually running on
lsof -i -P | grep python | grep LISTEN
# Look for: python3 ... (LISTEN) on port XXXX

# 2. Check what port ngrok is forwarding to
grep LOCAL_PORT /Users/masa/Projects/epstein/scripts/ngrok_persistent.sh
# Should show: LOCAL_PORT="8081"

# 3. If they don't match, you need to fix the mismatch
```

**Quick Fix**:

```bash
# Option A: Change backend to match ngrok (RECOMMENDED)
# Edit ecosystem.config.js line 6
# Change: --port XXXX
# To:     --port 8081

# Restart backend
pm2 restart epstein-backend

# Option B: Change ngrok to match backend (if you must change port)
# Follow "Port Change Procedure" below
```

---

## Port Change Procedure

### If You Must Change the Backend Port

Follow these steps **in order** to change the backend port without breaking the deployment:

#### Step 1: Identify Current Port

```bash
# Check current configuration
grep -n "port.*8081" ecosystem.config.js
grep -n "LOCAL_PORT" scripts/ngrok_persistent.sh
grep -n "localhost:8081" frontend/vite.config.ts
```

#### Step 2: Stop All Services

```bash
# Stop PM2 services
pm2 stop all

# Stop ngrok tunnel
./scripts/ngrok_persistent.sh stop

# Stop frontend (if running separately)
./scripts/dev-frontend.sh stop
```

#### Step 3: Update All Configuration Files

**Update Backend Port** (`ecosystem.config.js`):
```javascript
// Line 6 - Update port argument
args: '-m uvicorn server.app:app --host 0.0.0.0 --port XXXX --reload',
```

**Update Ngrok Target** (`scripts/ngrok_persistent.sh`):
```bash
# Line 6 - Update LOCAL_PORT
LOCAL_PORT="XXXX"  # Use same port as backend
```

**Update Frontend Proxy** (`frontend/vite.config.ts`):
```typescript
// Line 20 - Update proxy target
proxy: {
  '/api': {
    target: 'http://localhost:XXXX',  // Use same port as backend
    changeOrigin: true,
    secure: false
  }
}
```

#### Step 4: Verify Configuration Consistency

```bash
# All these should show the SAME port number
grep "port" ecosystem.config.js | grep -o '[0-9]\{4,\}'
grep "LOCAL_PORT" scripts/ngrok_persistent.sh | grep -o '[0-9]\{4,\}'
grep "localhost:" frontend/vite.config.ts | grep -o '[0-9]\{4,\}'
```

#### Step 5: Restart Services in Order

```bash
# 1. Start backend on new port
pm2 start epstein-backend

# 2. Verify backend is running
curl http://localhost:XXXX/health

# 3. Start ngrok tunnel (now pointing to correct port)
./scripts/ngrok_persistent.sh start

# 4. Verify ngrok tunnel
curl https://the-island.ngrok.app/health

# 5. Restart frontend (to pick up vite.config.ts changes)
./scripts/dev-frontend.sh restart
```

#### Step 6: Test Complete Flow

```bash
# Test local backend
curl http://localhost:XXXX/health

# Test ngrok tunnel
curl https://the-island.ngrok.app/health

# Test frontend (open in browser)
open http://localhost:5173

# Check browser DevTools → Network tab
# Verify API calls go to: https://the-island.ngrok.app/api/*
```

---

## Current Configuration

### Port Assignments

| Service | Port | URL | Configuration File |
|---------|------|-----|-------------------|
| **Backend (FastAPI)** | 8081 | http://localhost:8081 | `ecosystem.config.js` line 6 |
| **Frontend (Vite)** | 5173 | http://localhost:5173 | `frontend/vite.config.ts` line 14 |
| **Ngrok Tunnel** | → 8081 | https://the-island.ngrok.app | `scripts/ngrok_persistent.sh` line 6 |
| **Ngrok Dashboard** | 4040 | http://localhost:4040 | Default ngrok config |

### Configuration File Locations

```bash
# Backend port configuration
/Users/masa/Projects/epstein/ecosystem.config.js
# Line 6: args: '-m uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload'

# Ngrok tunnel configuration
/Users/masa/Projects/epstein/scripts/ngrok_persistent.sh
# Line 5: NGROK_URL="the-island.ngrok.app"
# Line 6: LOCAL_PORT="8081"

# Frontend proxy configuration
/Users/masa/Projects/epstein/frontend/vite.config.ts
# Line 14: port: 5173
# Line 20: target: 'http://localhost:8081'

# Frontend API URL (for remote access)
/Users/masa/Projects/epstein/frontend/.env
# VITE_API_BASE_URL=https://the-island.ngrok.app
```

---

## Deployment Verification

### Pre-Deployment Checklist

Before deploying or sharing the ngrok URL:

```bash
# ✅ 1. Verify port consistency
grep -n "8081" ecosystem.config.js scripts/ngrok_persistent.sh frontend/vite.config.ts

# ✅ 2. Check backend is running on correct port
lsof -i :8081 | grep LISTEN

# ✅ 3. Test local backend
curl http://localhost:8081/health

# ✅ 4. Verify ngrok tunnel is running
./scripts/ngrok_persistent.sh status

# ✅ 5. Test ngrok tunnel
curl https://the-island.ngrok.app/health

# ✅ 6. Check frontend configuration
cat frontend/.env | grep VITE_API_BASE_URL

# ✅ 7. Test complete flow in browser
open http://localhost:5173
# Open DevTools → Network tab
# Verify API calls use: https://the-island.ngrok.app
```

### Expected Results

**Backend Health Check**:
```bash
curl http://localhost:8081/health
# Expected:
# {"status":"ok","timestamp":"2025-11-28T...","service":"epstein-archive-api","version":"1.0.0"}
```

**Ngrok Tunnel Health Check**:
```bash
curl https://the-island.ngrok.app/health
# Expected: Same response as above
```

**Ngrok Status**:
```bash
./scripts/ngrok_persistent.sh status
# Expected:
# Tunnel Status: UP
# Public URL: https://the-island.ngrok.app
# Local Port: localhost:8081
# PID: XXXXX
```

---

## Troubleshooting

### Problem: Ngrok tunnel won't start

**Symptoms**:
- `./scripts/ngrok_persistent.sh start` fails
- "Tunnel failed to start" error

**Solutions**:

```bash
# 1. Check if ngrok is installed
which ngrok
# If not installed: brew install ngrok

# 2. Check if ngrok is authenticated
ngrok config check
# If not: ngrok config add-authtoken YOUR_TOKEN

# 3. Check if port 4040 is available
lsof -i :4040
# If in use, kill the process

# 4. Check if backend is running
curl http://localhost:8081/health
# If not running, start backend first

# 5. Try manual start to see error messages
ngrok http --domain=the-island.ngrok.app 8081
```

---

### Problem: Ngrok tunnel works but returns 502 Bad Gateway

**Symptoms**:
- `curl https://the-island.ngrok.app/health` returns 502
- Ngrok dashboard shows tunnel is UP

**Diagnosis**:
```bash
# Check if backend is actually running on port 8081
lsof -i :8081 | grep LISTEN

# If nothing, backend is not running or on wrong port
```

**Solutions**:

```bash
# Check what port backend is using
lsof -i -P | grep python | grep LISTEN

# If backend is on different port, update ngrok:
# Edit scripts/ngrok_persistent.sh line 6
# Set LOCAL_PORT to match backend port

# Restart ngrok
./scripts/ngrok_persistent.sh restart
```

---

### Problem: Frontend shows "Cannot connect to backend"

**Symptoms**:
- Frontend loads but no data appears
- Console shows network errors
- API calls timing out

**Diagnosis**:

```bash
# 1. Check frontend .env configuration
cat frontend/.env

# 2. Test backend directly
curl https://the-island.ngrok.app/health

# 3. Check browser DevTools → Network tab
# Look at Request URL for API calls
```

**Solutions**:

```bash
# If .env is wrong or missing:
echo "VITE_API_BASE_URL=https://the-island.ngrok.app" > frontend/.env

# Restart frontend to load new .env
./scripts/dev-frontend.sh restart

# If ngrok tunnel is down:
./scripts/ngrok_persistent.sh start

# If backend is down:
pm2 start epstein-backend
```

---

### Problem: Port conflicts when starting services

**Symptoms**:
- "Address already in use" error
- "Port 8081 is already in use"

**Solutions**:

```bash
# Find what's using the port
lsof -i :8081

# Kill the process
lsof -ti :8081 | xargs kill

# Or kill by process type
pkill -f "uvicorn.*8081"

# Then restart services
pm2 restart epstein-backend
```

---

### Problem: Changes to ecosystem.config.js not taking effect

**Symptoms**:
- Updated port in config but backend still uses old port
- PM2 shows old configuration

**Solution**:

```bash
# PM2 caches the config, you must reload it
pm2 delete epstein-backend
pm2 start ecosystem.config.js

# Or full PM2 restart
pm2 kill
pm2 start ecosystem.config.js
```

---

## Related Documentation

### Deployment Documentation
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Complete deployment guide with all environments
- **[deployment/DEPLOYMENT_CHECKLIST.md](./deployment/DEPLOYMENT_CHECKLIST.md)** - Pre-deployment verification checklist
- **[deployment/PORT_CONFIGURATION.md](./deployment/PORT_CONFIGURATION.md)** - Detailed port configuration and management

### Ngrok Documentation
- **[deployment/NGROK_CONFIGURATION_SUMMARY.md](./deployment/NGROK_CONFIGURATION_SUMMARY.md)** - Complete ngrok setup and configuration
- **[deployment/NGROK_FRONTEND_SETUP.md](./deployment/NGROK_FRONTEND_SETUP.md)** - Frontend configuration for ngrok
- **[deployment/NGROK_ACCESS.md](./deployment/NGROK_ACCESS.md)** - Ngrok access guide

### Development Scripts
- **[deployment/SCRIPT_MIGRATION.md](./deployment/SCRIPT_MIGRATION.md)** - Migration from legacy scripts
- **`scripts/ngrok_persistent.sh`** - Ngrok tunnel management script
- **`scripts/dev-start.sh`** - Start development environment
- **`ecosystem.config.js`** - PM2 process configuration

---

## Quick Reference

### Common Commands

```bash
# Check port configuration
grep "8081" ecosystem.config.js scripts/ngrok_persistent.sh frontend/vite.config.ts

# Verify services are running on correct ports
lsof -i :8081  # Backend
lsof -i :5173  # Frontend
lsof -i :4040  # Ngrok dashboard

# Test endpoints
curl http://localhost:8081/health           # Local backend
curl https://the-island.ngrok.app/health    # Ngrok tunnel
open http://localhost:5173                  # Frontend

# Manage services
pm2 restart epstein-backend                 # Restart backend
./scripts/ngrok_persistent.sh restart       # Restart tunnel
./scripts/dev-frontend.sh restart           # Restart frontend

# Check status
pm2 status                                  # Backend status
./scripts/ngrok_persistent.sh status        # Tunnel status
./scripts/dev-status.sh                     # All services
```

### Emergency Port Mismatch Fix

```bash
# If you suspect port mismatch, run this diagnostic:
echo "=== Backend Port Check ==="
grep "port" ecosystem.config.js | grep -o '[0-9]\{4,\}'
lsof -i -P | grep python | grep LISTEN | awk '{print $9}'

echo "=== Ngrok Port Check ==="
grep "LOCAL_PORT" scripts/ngrok_persistent.sh | grep -o '[0-9]\{4,\}'
curl -s http://localhost:4040/api/tunnels | grep -o 'localhost:[0-9]\{4,\}'

echo "=== Frontend Proxy Check ==="
grep "localhost:" frontend/vite.config.ts | grep -o '[0-9]\{4,\}'

# All should show: 8081
```

---

## Key Takeaways

1. **⚠️ Port Changes Break Ngrok**: The `the-island.ngrok.app` domain is hardcoded to forward to a specific port
2. **📝 Update Multiple Files**: When changing ports, update `ecosystem.config.js`, `ngrok_persistent.sh`, AND `vite.config.ts`
3. **🔄 Restart Required**: After port changes, restart backend, ngrok, AND frontend
4. **✅ Verify Consistency**: Always verify all services are using the same port
5. **🔍 Test Complete Flow**: Test local backend → ngrok tunnel → frontend

---

**Last Updated**: 2025-11-28
**Maintained By**: Development Team
**Questions?** See [Troubleshooting](#troubleshooting) or [Related Documentation](#related-documentation)
