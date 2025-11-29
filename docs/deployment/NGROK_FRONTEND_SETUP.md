# Frontend Ngrok Configuration Guide

**Quick Summary**: **Ngrok URL**: https://the-island. ngrok.

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Overview
- Configuration Files
- 1. Environment Variable (`.env`)
- 2. API Client Configuration
- 3. Backend CORS

---

**Status**: ✅ **CONFIGURED**
**Date**: 2025-11-20
**Ngrok URL**: https://the-island.ngrok.app
**Backend Port**: 8081

---

## Overview

The frontend is configured to connect to the backend via ngrok tunnel, enabling remote access and testing. The configuration uses environment variables for easy switching between local and remote backends.

## Configuration Files

### 1. Environment Variable (`.env`)
```bash
# Location: /Users/masa/Projects/epstein/frontend/.env
VITE_API_BASE_URL=https://the-island.ngrok.app
```

**To switch to local development**:
```bash
# Edit .env and change to:
VITE_API_BASE_URL=http://localhost:8081

# Then restart Vite dev server:
# Press Ctrl+C in terminal running npm
# Run: npm run dev
```

### 2. API Client Configuration
```typescript
// Location: /Users/masa/Projects/epstein/frontend/src/lib/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';
```

This automatically uses the environment variable if set, otherwise defaults to localhost.

### 3. Backend CORS
```python
# Location: /Users/masa/Projects/epstein/server/app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Allows all origins including ngrok
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Quick Start

### Start Ngrok Tunnel
```bash
# Manual start
ngrok http --url=the-island.ngrok.app 8081

# Or use persistent script
/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh start
```

### Start Frontend Dev Server
```bash
cd /Users/masa/Projects/epstein/frontend
npm run dev
```

**Important**: Restart Vite dev server after changing `.env` file to load new values.

### Verify Configuration
```bash
cd /Users/masa/Projects/epstein/frontend
./test-ngrok-config.sh
```

---

## Testing the Connection

### 1. Backend Health Check
```bash
# Test ngrok tunnel
curl https://the-island.ngrok.app/health

# Expected response:
# {"status":"ok","timestamp":"...","service":"epstein-archive-api","version":"1.0.0"}
```

### 2. Backend Stats Check
```bash
curl https://the-island.ngrok.app/api/stats

# Should return JSON with entities, documents, flights, etc.
```

### 3. Frontend Browser Test
1. Open http://localhost:5173
2. Open DevTools (F12) → Network tab
3. Navigate to any page (Entities, Flights, etc.)
4. Verify API requests show:
   - Request URL: `https://the-island.ngrok.app/api/...`
   - Status: `200 OK`
   - Response: Valid JSON data

### 4. Common API Endpoints to Test
```bash
# Entities
curl https://the-island.ngrok.app/api/entities?limit=5

# Flights
curl https://the-island.ngrok.app/api/flights

# Timeline
curl https://the-island.ngrok.app/api/timeline

# Network
curl https://the-island.ngrok.app/api/network
```

---

## Troubleshooting

### Issue: Frontend shows "Cannot connect to backend"

**Solution 1**: Verify ngrok tunnel is running
```bash
curl https://the-island.ngrok.app/health

# If offline (ERR_NGROK_3200), start ngrok:
ngrok http --url=the-island.ngrok.app 8081
```

**Solution 2**: Check .env file
```bash
cat /Users/masa/Projects/epstein/frontend/.env

# Should show:
# VITE_API_BASE_URL=https://the-island.ngrok.app
```

**Solution 3**: Restart Vite dev server
```bash
# In terminal running Vite:
# Press Ctrl+C
# Then: npm run dev
```

### Issue: CORS errors in browser console

**Check**: Backend CORS configuration
```bash
grep -A 5 "CORSMiddleware" /Users/masa/Projects/epstein/server/app.py

# Should show allow_origins=["*"]
```

### Issue: API requests still going to localhost

**Solution**: Clear browser cache and hard reload
```bash
# In browser: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

### Issue: Mixed content warnings (HTTP/HTTPS)

**Cause**: Ngrok provides HTTPS, but frontend might be requesting HTTP
**Solution**: Ensure .env has `https://` not `http://`

---

## Environment Management

### Development (Local Backend)
```bash
# .env
VITE_API_BASE_URL=http://localhost:8081
```

### Testing (Ngrok Tunnel)
```bash
# .env
VITE_API_BASE_URL=https://the-island.ngrok.app
```

### Production (Deploy)
```bash
# .env
VITE_API_BASE_URL=https://your-production-domain.com
```

---

## Ngrok Tunnel Management

### Start Tunnel
```bash
ngrok http --url=the-island.ngrok.app 8081
```

### Check Tunnel Status
```bash
# Check ngrok web interface
open http://localhost:4040

# Or check process
ps aux | grep "ngrok.*the-island"
```

### Stop Tunnel
```bash
pkill -f "ngrok.*the-island"
```

### Monitor Tunnel
```bash
# View ngrok dashboard
open http://localhost:4040

# View logs
tail -f /tmp/ngrok_the_island.log
```

---

## Security Notes

### ⚠️ Important
1. **Credentials**: The `.env` file is gitignored to prevent exposing configuration
2. **HTTPS**: Ngrok provides HTTPS automatically (SSL certificates managed by ngrok)
3. **Access Control**: The ngrok URL is public but requires backend authentication if configured
4. **Rate Limits**: Free ngrok accounts have connection limits

### Best Practices
- ✅ Use environment variables (not hardcoded URLs)
- ✅ Keep `.env` in `.gitignore`
- ✅ Provide `.env.example` template for other developers
- ✅ Document all environment variables
- ✅ Use HTTPS in production

---

## Files Modified

| File | Purpose | Status |
|------|---------|--------|
| `frontend/.env` | Environment variables (ngrok URL) | ✅ Created |
| `frontend/.env.example` | Template for configuration | ✅ Created |
| `frontend/src/lib/api.ts` | API client configuration | ✅ Updated |
| `frontend/.gitignore` | Protect .env from git | ✅ Updated |
| `frontend/test-ngrok-config.sh` | Verification script | ✅ Created |
| `server/app.py` | CORS configuration | ✅ Verified |

---

## Verification Checklist

- [x] Ngrok tunnel running on https://the-island.ngrok.app
- [x] Backend responding to /health endpoint
- [x] Backend responding to /api/stats endpoint
- [x] `.env` file created with VITE_API_BASE_URL
- [x] `api.ts` updated to use environment variable
- [x] CORS configured to allow ngrok origin
- [x] `.env` added to `.gitignore`
- [x] `.env.example` created for documentation
- [ ] Vite dev server restarted (MANUAL STEP REQUIRED)
- [ ] Browser test: API calls go to ngrok URL (MANUAL VERIFICATION)

---

## Next Steps

### Manual Actions Required:

1. **Restart Vite Dev Server**:
   ```bash
   # In terminal running Vite:
   # Press Ctrl+C
   # Then: npm run dev
   ```

2. **Test in Browser**:
   - Open http://localhost:5173
   - Open DevTools → Network tab
   - Navigate to Entities, Flights, or Timeline
   - Verify requests show `https://the-island.ngrok.app/api/...`

3. **Verify All Pages Work**:
   - [x] Home page
   - [ ] Entities list
   - [ ] Entity detail pages
   - [ ] Flights page
   - [ ] Timeline page
   - [ ] Network graph
   - [ ] Search functionality
   - [ ] Documents page

---

## Support

**Script**: `/Users/masa/Projects/epstein/frontend/test-ngrok-config.sh`
**Documentation**: This file
**Ngrok Dashboard**: http://localhost:4040

For issues, run the test script and check the output.
