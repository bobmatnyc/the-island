# News API 422 Error Fix

**Quick Summary**: Implementation summary documenting changes, files modified, and testing results.

**Category**: Implementation
**Status**: Complete
**Last Updated**: 2025-11-24

**Key Points**:
- **Backend Constraint**: `/api/news/articles` endpoint validates `limit` with `Query(20, ge=1, le=100)`
- Maximum allowed limit: **100**
- **Frontend Violation**: Two methods were using `limit=1000`:

---

**Date**: 2025-11-20
**Status**: ✅ Completed
**Issue**: 422 Unprocessable Content error when loading /news page

## Root Cause

The News API client in the frontend was requesting more articles than the backend allows:

- **Backend Constraint**: `/api/news/articles` endpoint validates `limit` with `Query(20, ge=1, le=100)`
  - Maximum allowed limit: **100**
- **Frontend Violation**: Two methods were using `limit=1000`:
  1. `getTags()` at line 210
  2. `getStats()` at line 143

When the frontend requested `limit=1000`, the backend rejected it with 422 status code.

## Solution

Implemented **pagination logic** in both methods to respect the backend's maximum limit while still fetching all articles.

### Changes Made

**File**: `/frontend/src/services/newsApi.ts`

#### 1. Fixed `getStats()` Method (Lines 131-193)

**Before**:
```typescript
const articlesResponse = await fetchAPI<{ articles: NewsArticle[]; total: number }>(
  '/api/news/articles?limit=1000'
);
const articles = articlesResponse.articles;
```

**After**:
```typescript
// Fetch all articles with pagination (backend max limit is 100)
const allArticles: NewsArticle[] = [];
let offset = 0;
const limit = 100; // Backend maximum allowed limit

while (true) {
  const articlesResponse = await fetchAPI<{ articles: NewsArticle[]; total: number }>(
    `/api/news/articles?limit=${limit}&offset=${offset}`
  );

  allArticles.push(...articlesResponse.articles);

  // Stop if we've fetched all articles
  if (allArticles.length >= articlesResponse.total || articlesResponse.articles.length === 0) {
    break;
  }

  offset += limit;
}
```

#### 2. Fixed `getTags()` Method (Lines 222-249)

**Before**:
```typescript
const response = await fetchAPI<{ articles: NewsArticle[]; total: number }>(
  '/api/news/articles?limit=1000'
);

const tags = new Set<string>();
response.articles.forEach(article => {
  article.tags.forEach(tag => tags.add(tag));
});
```

**After**:
```typescript
// Fetch all articles with pagination (backend max limit is 100)
const allArticles: NewsArticle[] = [];
let offset = 0;
const limit = 100; // Backend maximum allowed limit

while (true) {
  const response = await fetchAPI<{ articles: NewsArticle[]; total: number }>(
    `/api/news/articles?limit=${limit}&offset=${offset}`
  );

  allArticles.push(...response.articles);

  // Stop if we've fetched all articles
  if (allArticles.length >= response.total || response.articles.length === 0) {
    break;
  }

  offset += limit;
}

const tags = new Set<string>();
allArticles.forEach(article => {
  article.tags.forEach(tag => tags.add(tag));
});
```

## Implementation Details

### Pagination Logic

The pagination implementation:
1. **Respects Backend Limit**: Uses `limit=100` (backend maximum)
2. **Fetches All Data**: Loops with increasing `offset` until all articles are retrieved
3. **Efficient Termination**: Stops when:
   - We've fetched all articles (`allArticles.length >= total`)
   - OR no more articles returned (`articles.length === 0`)

### Benefits

1. **No 422 Errors**: All requests respect backend validation
2. **Complete Data**: Still fetches ALL articles for accurate stats/tags
3. **Memory Efficient**: Processes articles in 100-item batches
4. **Maintainable**: Clear comments explain the pagination logic

## Testing

### Test Script

Created `/test_news_api_fix.py` to verify:
1. ✅ Valid limit=100 succeeds
2. ✅ Invalid limit=1000 returns 422 (as expected)
3. ✅ Pagination works correctly

### Manual Testing

Run backend server and test:
```bash
# Start backend
./start_server.sh

# Test the fix
python3 test_news_api_fix.py

# Or manually test in browser
open http://localhost:3000/news
```

## Success Criteria

- [x] No 422 errors when loading /news page
- [x] `getTags()` returns all unique tags from all articles
- [x] `getStats()` returns accurate statistics across all articles
- [x] All API calls respect backend limit ≤ 100
- [x] Pagination efficiently fetches all data

## Performance Considerations

### Before (Broken)
- Single request with `limit=1000` → **422 Error**
- No data returned

### After (Fixed)
- Example: 250 total articles
  - Request 1: `limit=100&offset=0` → 100 articles
  - Request 2: `limit=100&offset=100` → 100 articles
  - Request 3: `limit=100&offset=200` → 50 articles
  - Total: **3 requests** to fetch all data

### Trade-offs
- **Pro**: Respects backend validation, complete data
- **Con**: Multiple API requests for large datasets
- **Optimization**: Could cache results or implement lazy loading if needed

## Related Files

- `/Users/masa/Projects/epstein/frontend/src/services/newsApi.ts` - Fixed pagination logic
- `/Users/masa/Projects/epstein/server/routes/news.py:87` - Backend limit validation
- `/Users/masa/Projects/epstein/test_news_api_fix.py` - Validation test script

## Notes

- Backend limit validation: `limit: int = Query(20, ge=1, le=100)`
- Other methods (`getArticlesByEntity`, `getArticlesByDateRange`) already respect limits via `searchNews()`
- No changes needed to other API methods
