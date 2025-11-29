# 🐛 Advanced Search Bug Fix Guide

**Quick Summary**: Implementation summary documenting changes, files modified, and testing results.

**Category**: Implementation
**Status**: Complete
**Last Updated**: 2025-11-24

**Key Points**:
- Function name collision
- Missing `await` keywords
- Coroutine errors throughout

---

**Priority:** 🚨 **CRITICAL - BLOCKING ALL SEARCH FUNCTIONALITY**
**Estimated Fix Time:** 30 minutes
**File:** `server/routes/search.py`

---

## Problem Summary

Search API returns 500 errors due to async/await bugs:
- Function name collision
- Missing `await` keywords
- Coroutine errors throughout

---

## Quick Fix Steps

### Step 1: Rename Helper Function (Line 85)

**Location:** `server/routes/search.py:85-101`

**BEFORE:**
```python
def get_search_analytics():
    """Get or initialize search analytics (lazy loading)."""
    global _search_analytics

    if _search_analytics is None:
        if SEARCH_ANALYTICS_PATH.exists():
            with open(SEARCH_ANALYTICS_PATH, 'r') as f:
                _search_analytics = json.load(f)
        else:
            _search_analytics = {
                "total_searches": 0,
                "popular_queries": {},
                "recent_searches": [],
                "last_updated": datetime.utcnow().isoformat()
            }

    return _search_analytics
```

**AFTER:**
```python
def load_search_analytics():  # ← RENAME THIS
    """Get or initialize search analytics (lazy loading)."""
    global _search_analytics

    if _search_analytics is None:
        if SEARCH_ANALYTICS_PATH.exists():
            with open(SEARCH_ANALYTICS_PATH, 'r') as f:
                _search_analytics = json.load(f)
        else:
            _search_analytics = {
                "total_searches": 0,
                "popular_queries": {},
                "recent_searches": [],
                "last_updated": datetime.utcnow().isoformat()
            }

    return _search_analytics
```

---

### Step 2: Fix Line 638 (Analytics Endpoint)

**Location:** `server/routes/search.py:638`

**BEFORE:**
```python
@router.get("/analytics")
async def get_search_analytics():
    """Get search analytics data."""
    try:
        analytics = get_search_analytics()  # ❌ Wrong - calls itself
        # ...
```

**AFTER:**
```python
@router.get("/analytics")
async def get_search_analytics():
    """Get search analytics data."""
    try:
        analytics = load_search_analytics()  # ✅ Call renamed helper
        # ...
```

---

### Step 3: Fix Line 676 (Clear History Endpoint)

**Location:** `server/routes/search.py:676`

**BEFORE:**
```python
@router.delete("/analytics/history")
async def clear_search_history():
    """Clear search history and analytics."""
    try:
        global _search_analytics

        analytics = get_search_analytics()  # ❌ Missing await
        analytics["recent_searches"] = []
        # ...
```

**AFTER:**
```python
@router.delete("/analytics/history")
async def clear_search_history():
    """Clear search history and analytics."""
    try:
        global _search_analytics

        analytics = load_search_analytics()  # ✅ Call helper
        analytics["recent_searches"] = []
        # ...
```

---

### Step 4: Fix Line 281 (Unified Search)

**Location:** `server/routes/search.py:281`

**BEFORE:**
```python
@router.get("/unified", response_model=UnifiedSearchResponse)
async def unified_search(...):
    try:
        # Track search analytics
        analytics = get_search_analytics()  # ❌ Missing await
        analytics["total_searches"] += 1
        # ...
```

**AFTER:**
```python
@router.get("/unified", response_model=UnifiedSearchResponse)
async def unified_search(...):
    try:
        # Track search analytics
        analytics = load_search_analytics()  # ✅ Call helper
        analytics["total_searches"] += 1
        # ...
```

---

### Step 5: Fix Line 601 (Suggestions Endpoint)

**Location:** `server/routes/search.py:601`

**BEFORE:**
```python
@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_search_suggestions(...):
    try:
        # ...

        # Get popular queries
        analytics = get_search_analytics()  # ❌ Missing await
        popular = analytics.get("popular_queries", {})
        # ...
```

**AFTER:**
```python
@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_search_suggestions(...):
    try:
        # ...

        # Get popular queries
        analytics = load_search_analytics()  # ✅ Call helper
        popular = analytics.get("popular_queries", {})
        # ...
```

---

## Complete Patch

If you want to apply all fixes at once, here's the complete patch:

```bash
# Create backup
cp server/routes/search.py server/routes/search.py.backup

# Apply fixes (manual edits required)
# Edit server/routes/search.py and make these 5 changes:

# 1. Line 85: Rename function
#    def get_search_analytics() → def load_search_analytics()

# 2. Line 281: Change call
#    analytics = get_search_analytics() → analytics = load_search_analytics()

# 3. Line 601: Change call
#    analytics = get_search_analytics() → analytics = load_search_analytics()

# 4. Line 638: Change call (inside async endpoint)
#    analytics = get_search_analytics() → analytics = load_search_analytics()

# 5. Line 676: Change call
#    analytics = get_search_analytics() → analytics = load_search_analytics()
```

---

## Testing After Fix

### Test 1: Simple Search
```bash
curl "http://localhost:8000/api/search/unified?query=Epstein&limit=5"

# Expected: JSON with search results
# Should NOT see: 'coroutine' object error
```

### Test 2: Suggestions
```bash
curl "http://localhost:8000/api/search/suggestions?query=Eps&limit=5"

# Expected: JSON array of suggestions
# Should NOT see: 'coroutine' object has no attribute 'get'
```

### Test 3: Analytics
```bash
curl "http://localhost:8000/api/search/analytics"

# Expected: JSON with total_searches, top_queries, recent_searches
# Should NOT see: 'coroutine' object has no attribute 'get'
```

### Test 4: Run Full Test Suite
```bash
cd /Users/masa/Projects/epstein
python3 test_advanced_search.py

# Expected: All 10 performance tests pass
# Expected: P50 latency < 300ms
# Expected: P95 latency < 500ms
```

---

## Verification Checklist

After making fixes, verify:

- [ ] No coroutine errors in any endpoint
- [ ] `/api/search/unified` returns results
- [ ] `/api/search/suggestions` returns suggestions
- [ ] `/api/search/analytics` returns statistics
- [ ] Search history saves correctly
- [ ] All 10 test queries complete successfully
- [ ] Performance meets goals (P50 < 300ms)
- [ ] No errors in server logs

---

## Root Cause Analysis

### Why This Happened

Python's async/await requires strict discipline:

```python
# Async function definition
async def my_function():
    return {"key": "value"}

# WRONG ❌
result = my_function()  # Returns <coroutine object>
result.get("key")       # ERROR: 'coroutine' has no attribute 'get'

# CORRECT ✅
result = await my_function()  # Returns {"key": "value"}
result.get("key")             # Works: "value"
```

In this case:
1. Helper function `get_search_analytics()` was regular (non-async)
2. API endpoint reused same name as `async def get_search_analytics()`
3. Python picked the async version when called
4. Code didn't await → got coroutine instead of dict
5. Tried to use dict methods → crash

### Prevention

1. **Use distinct names** for sync helpers vs async endpoints
2. **Always await async calls** in async functions
3. **Use type hints** to catch these at dev time:
   ```python
   async def get_data() -> dict:  # Type hint helps catch errors
       return {}
   ```
4. **Add tests** for async functions
5. **Use linters** like `mypy` or `pylance`

---

## Files for Reference

- **QA Report:** `QA_REPORT_ADVANCED_SEARCH.md`
- **Visual Summary:** `QA_SEARCH_VISUAL_SUMMARY.md`
- **Test Script:** `test_advanced_search.py`
- **Bug Fix Guide:** `SEARCH_BUG_FIX_GUIDE.md` (this file)

---

## After Fix: Next Steps

1. ✅ Apply all 5 fixes
2. ✅ Restart server
3. ✅ Test all 3 endpoints manually
4. ✅ Run full test suite
5. ✅ Verify performance metrics
6. ✅ Notify QA for re-certification
7. ✅ Update any related documentation

---

## Questions?

**QA Contact:** Web QA Agent
**Report Date:** 2025-11-20
**Priority:** 🚨 CRITICAL

**Need help?** Reference the full QA report in `QA_REPORT_ADVANCED_SEARCH.md`
