# Authentication System Changes

**Date**: 2025-11-17
**Status**: ✅ Implemented - Ready for Testing

## Problem Fixed

**Before**: Users experienced double authentication:
1. HTTP Basic Auth popup (browser) on root route `/`
2. THEN redirect to login page with form-based authentication
3. Session token stored in sessionStorage (vulnerable to XSS)

**After**: Single, seamless authentication:
1. Visit `/` → redirect to login page (no popup)
2. Login once with form → HTTP-only cookie set
3. Automatic session persistence (no JavaScript access)

---

## Changes Made

### 1. Backend Changes (`app.py`)

#### Root Route - No More HTTP Basic Auth
```python
@app.get("/")
async def root(request: Request):
    """Redirect to main app if logged in, otherwise redirect to login"""
    session_token = request.cookies.get("session_token")

    if session_token and session_token in session_tokens:
        session = session_tokens[session_token]
        if datetime.now() <= session["expires"]:
            return RedirectResponse(url="/static/index.html")

    return RedirectResponse(url="/static/login.html")
```

**Change**: No `Depends(authenticate)` - public route

---

#### Login Endpoint - HTTP-Only Cookies
```python
@app.post("/login")
async def login(login_data: LoginRequest, request: Request, response: Response):
    # ... credential validation ...

    # Set HTTP-only cookie
    max_age_seconds = 2592000 if login_data.remember else 86400  # 30 days or 1 day
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,  # Prevent XSS attacks
        secure=False,   # Set to True in production with HTTPS
        samesite='lax', # CSRF protection
        max_age=max_age_seconds
    )
```

**Changes**:
- Added `response: Response` parameter
- Set HTTP-only cookie (JavaScript cannot access)
- `secure=False` for HTTP development (change to `True` in production)
- `samesite='lax'` for CSRF protection

---

#### Session Verification - Cookie-Based
```python
@app.get("/api/verify-session")
async def verify_session(request: Request):
    """Verify session token from cookie is valid"""
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="No session cookie found")

    if session_token not in session_tokens:
        raise HTTPException(status_code=401, detail="Invalid session token")

    session = session_tokens[session_token]
    if datetime.now() > session["expires"]:
        del session_tokens[session_token]
        raise HTTPException(status_code=401, detail="Session expired")

    return {"username": session["username"], "valid": True}
```

**Changes**:
- No longer accepts `Authorization: Bearer` header
- Reads session from cookie instead
- Automatically cleans up expired sessions

---

#### Logout Endpoint - Clear Cookie
```python
@app.post("/api/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session cookie"""
    session_token = request.cookies.get("session_token")

    if session_token and session_token in session_tokens:
        del session_tokens[session_token]

    response.delete_cookie(key="session_token")
    return {"success": True, "message": "Logged out successfully"}
```

**New endpoint** for proper logout

---

#### Flexible Authentication - Cookie or HTTP Basic Auth
```python
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Depends(security)
) -> str:
    """Accept either session cookie OR HTTP Basic Auth"""

    # Try session cookie first (for web app users)
    session_token = request.cookies.get("session_token")

    if session_token and session_token in session_tokens:
        session = session_tokens[session_token]
        if datetime.now() <= session["expires"]:
            return session["username"]
        else:
            del session_tokens[session_token]

    # Fall back to HTTP Basic Auth (for API clients)
    if credentials:
        return authenticate(credentials)

    raise HTTPException(
        status_code=401,
        detail="Not authenticated. Please log in via /static/login.html or use HTTP Basic Auth.",
        headers={"WWW-Authenticate": "Basic"}
    )
```

**Changes**:
- Renamed from `flexible_auth` to `get_current_user`
- Checks cookies FIRST, then falls back to HTTP Basic Auth
- Allows both web users (cookies) and API clients (Basic Auth)

---

#### API Routes - Use get_current_user
```python
# All API routes changed from:
@app.get("/api/stats")
async def get_stats(username: str = Depends(authenticate)):

# To:
@app.get("/api/stats")
async def get_stats(username: str = Depends(get_current_user)):
```

**Change**: All `Depends(authenticate)` → `Depends(get_current_user)`

---

### 2. Frontend Changes

#### Login Page (`login.html`)

**Before**:
```javascript
const response = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, remember })
});

if (response.ok) {
    const data = await response.json();
    if (rememberMe) {
        localStorage.setItem('sessionToken', data.token);
    } else {
        sessionStorage.setItem('sessionToken', data.token);
    }
    window.location.href = '/static/index.html';
}
```

**After**:
```javascript
const response = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Important: include cookies
    body: JSON.stringify({ username, password, remember })
});

if (response.ok) {
    // Cookie is set automatically by server
    // No need to store token in localStorage/sessionStorage
    window.location.href = '/static/index.html';
}
```

**Changes**:
- Added `credentials: 'include'`
- Removed localStorage/sessionStorage token storage
- Cookie is set automatically by server

---

#### Main App (`app.js`)

**Before**:
```javascript
function checkAuthentication() {
    const sessionToken = localStorage.getItem('sessionToken') ||
                        sessionStorage.getItem('sessionToken');

    if (!sessionToken) {
        window.location.href = '/static/login.html';
        return false;
    }

    fetch('/api/verify-session', {
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    }).then(response => {
        if (!response.ok) {
            localStorage.removeItem('sessionToken');
            sessionStorage.removeItem('sessionToken');
            window.location.href = '/static/login.html';
        }
    });
}

// Override fetch to add Authorization header
window.fetch = function(url, options = {}) {
    const sessionToken = localStorage.getItem('sessionToken') ||
                        sessionStorage.getItem('sessionToken');

    if (sessionToken && url.startsWith('/api')) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${sessionToken}`;
    }

    return originalFetch(url, options);
};
```

**After**:
```javascript
function checkAuthentication() {
    fetch('/api/verify-session', {
        credentials: 'include' // Include cookies
    }).then(response => {
        if (!response.ok) {
            window.location.href = '/static/login.html';
        }
    });
}

// Override fetch to always include credentials
window.fetch = function(url, options = {}) {
    if (!options.credentials) {
        options.credentials = 'include';
    }

    return originalFetch(url, options);
};
```

**Changes**:
- No sessionToken lookup
- Added `credentials: 'include'` to all requests
- Removed localStorage/sessionStorage cleanup

---

#### Logout Function

**Before**:
```javascript
function logout() {
    localStorage.removeItem('sessionToken');
    sessionStorage.removeItem('sessionToken');
    window.location.href = '/static/login.html';
}
```

**After**:
```javascript
async function logout() {
    try {
        await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    window.location.href = '/static/login.html';
}
```

**Changes**:
- Calls server `/api/logout` endpoint to clear cookie
- No localStorage/sessionStorage cleanup needed

---

#### Other Files Updated

**`hot-reload.js`**:
- Removed sessionToken checks
- EventSource automatically sends cookies for same-origin
- Updated polling to use `credentials: 'include'`

**`audit.html`**:
- Removed sessionToken authentication check
- Added cookie-based verification
- Updated apiCall helper to use `credentials: 'include'`

---

## Security Improvements

### Before (sessionStorage)
❌ **Vulnerable to XSS**: JavaScript can access sessionStorage
❌ **Not persistent**: Lost on browser close (unless localStorage)
❌ **Manual token management**: Frontend must send token with every request
❌ **No automatic expiration**: Token cleanup is manual

### After (HTTP-only cookies)
✅ **XSS Protection**: JavaScript cannot access HTTP-only cookies
✅ **Automatic persistence**: Cookie max-age handles expiration
✅ **Automatic transmission**: Browser sends cookie automatically
✅ **Server-side expiration**: Sessions auto-cleaned on server
✅ **CSRF Protection**: `samesite='lax'` prevents cross-site attacks

---

## Testing Checklist

### Login Flow
- [ ] Visit `http://localhost:8000/` → redirects to `/static/login.html`
- [ ] **NO HTTP Basic Auth popup appears**
- [ ] Enter credentials → redirects to `/static/index.html`
- [ ] Cookie `session_token` is set (check DevTools → Application → Cookies)
- [ ] Cookie has `HttpOnly` flag (JavaScript cannot access)

### Session Persistence
- [ ] Refresh page → still logged in (no redirect to login)
- [ ] Close tab, reopen → still logged in if "Remember me" checked
- [ ] Close tab, reopen → logged out if "Remember me" NOT checked

### API Access
- [ ] All API calls work without manual Authorization headers
- [ ] Network tab shows cookies sent with requests
- [ ] Web users don't see HTTP Basic Auth popups

### HTTP Basic Auth Fallback
- [ ] API clients can still use HTTP Basic Auth
```bash
curl -u username:password http://localhost:8000/api/stats
```

### Logout
- [ ] Click logout → redirects to login page
- [ ] Cookie `session_token` is deleted
- [ ] Visiting `/` redirects to login (not main app)

### Security
- [ ] Cookie has `HttpOnly` flag in browser DevTools
- [ ] JavaScript `document.cookie` does NOT show session_token
- [ ] `samesite='lax'` attribute is set

---

## Production Deployment

### Required Changes for HTTPS

In `app.py`, change:
```python
response.set_cookie(
    key="session_token",
    value=token,
    httponly=True,
    secure=True,   # ← Change to True for HTTPS
    samesite='lax',
    max_age=max_age_seconds
)
```

**Important**: `secure=True` requires HTTPS. Don't enable in development without HTTPS.

---

## Rollback Plan

If issues arise, revert these files:
1. `server/app.py` (authentication functions)
2. `server/web/login.html` (login form)
3. `server/web/app.js` (checkAuthentication, logout)
4. `server/web/hot-reload.js` (SSE connection)
5. `server/web/audit.html` (authentication check)

Git revert:
```bash
git revert <commit-hash>
```

---

## Benefits Summary

1. **No Double Authentication**: Users log in once via form
2. **Better Security**: HTTP-only cookies prevent XSS attacks
3. **Seamless UX**: No browser popup, automatic session handling
4. **Flexible API Access**: Web users (cookies) + API clients (Basic Auth)
5. **Proper Session Management**: Server-side expiration, automatic cleanup

---

## Questions?

- **Q**: Why not use both cookies AND localStorage?
  - **A**: HTTP-only cookies are more secure. localStorage is vulnerable to XSS.

- **Q**: Can API clients still use the API?
  - **A**: Yes! HTTP Basic Auth still works for curl/Postman/scripts.

- **Q**: What about CSRF attacks?
  - **A**: `samesite='lax'` prevents cross-site requests from sending cookies.

- **Q**: How do I enable HTTPS cookies?
  - **A**: Set `secure=True` in production with HTTPS.
