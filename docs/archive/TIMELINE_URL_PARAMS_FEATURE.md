# Timeline URL Parameter Feature

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- `?news=true` - Forces news coverage ON
- `?showNews=true` - Alternative parameter (same effect)
- Fetches articles for the timeline date range
- Groups articles by date
- Updates the UI with article counts

---

## Overview

The Timeline page now supports URL parameters to control news coverage display, providing a robust workaround for persistent cache/state issues and enabling direct links to timeline with news enabled.

## Feature Implementation

### URL Parameters Supported

- `?news=true` - Forces news coverage ON
- `?showNews=true` - Alternative parameter (same effect)

### Examples

```
# Enable news coverage via URL
http://localhost:5173/timeline?news=true

# Alternative parameter name
http://localhost:5173/timeline?showNews=true

# Default behavior (no parameter)
http://localhost:5173/timeline
# News coverage is OFF by default
```

## Implementation Details

### 1. URL Parameter Detection

**File**: `frontend/src/pages/Timeline.tsx`

```typescript
import { useSearchParams } from 'react-router-dom';

const [searchParams] = useSearchParams();
const forceShowNews = searchParams.get('news') === 'true' ||
                      searchParams.get('showNews') === 'true';
```

### 2. State Override

The URL parameter overrides the default checkbox state:

```typescript
const [showNews, setShowNews] = useState(forceShowNews);

useEffect(() => {
  if (forceShowNews && !showNews) {
    setShowNews(true);
  }
}, [forceShowNews]);
```

### 3. News Loading

When `showNews` is true, the `useTimelineNews` hook automatically:
- Fetches articles for the timeline date range
- Groups articles by date
- Updates the UI with article counts

## User Experience

### With URL Parameter

1. User navigates to `/timeline?news=true`
2. News coverage checkbox is **automatically checked**
3. News articles load immediately
4. Badge shows article count (e.g., "213 articles")
5. Timeline events display news article badges

### Without URL Parameter

1. User navigates to `/timeline`
2. News coverage checkbox is **OFF** by default
3. User can manually toggle news coverage ON
4. Standard behavior applies

## Debugging

### Console Logs

The implementation includes comprehensive logging:

```javascript
// URL parameter detection
[Timeline URL Params] {
  newsParam: "true",
  showNewsParam: null,
  forceShowNews: true,
  timestamp: "2025-01-22T..."
}

// State override
[Timeline] URL param forcing news coverage ON {
  forceShowNews: true,
  currentShowNews: false,
  timestamp: "2025-01-22T..."
}

// News fetch process
[useTimelineNews] Effect triggered {
  enabled: true,
  dateRange: { start: "1990-01-01", end: "2020-12-31" },
  ...
}

[useTimelineNews] Fetch complete {
  articleCount: 213,
  sampleArticles: [...],
  ...
}

// Filter state
[Timeline Filter Debug] {
  showNews: true,
  totalArticles: 213,
  articlesCount: 45,
  ...
}
```

### Verification Steps

1. **Open browser to**: `http://localhost:5173/timeline?news=true`
2. **Open Developer Console** (F12)
3. **Check console logs**:
   - `[Timeline URL Params]` shows `forceShowNews=true`
   - `[useTimelineNews] Fetch complete` shows article count
   - `[Timeline Filter Debug]` shows `totalArticles > 0`
4. **Verify UI**:
   - News coverage toggle is ON
   - Badge shows article count (not "0 articles")
   - Timeline events show news badges

## Testing

### Manual Testing

Run the test script:

```bash
./test-timeline-url-params.sh
```

### Test Cases

| Test Case | URL | Expected Behavior |
|-----------|-----|-------------------|
| Force news ON | `/timeline?news=true` | News coverage enabled, articles loaded |
| Alternative param | `/timeline?showNews=true` | News coverage enabled, articles loaded |
| Default behavior | `/timeline` | News coverage OFF by default |
| Invalid param | `/timeline?news=false` | News coverage OFF (only "true" triggers) |

## Technical Benefits

### 1. Cache/State Workaround

URL parameters bypass React state/cache issues by providing external control over component behavior.

### 2. Shareable Links

Users can share direct links to timeline with news enabled:

```
Share: http://localhost:5173/timeline?news=true
```

### 3. Bookmarkable State

Users can bookmark timeline with news coverage for quick access.

### 4. Deterministic Behavior

URL parameters provide predictable, testable behavior independent of browser state.

## Architecture

### Data Flow

```
URL Parameter (?news=true)
  ↓
useSearchParams hook
  ↓
forceShowNews = true
  ↓
useState(forceShowNews) → showNews = true
  ↓
useTimelineNews(dateRange, showNews=true)
  ↓
Fetch articles from API
  ↓
Group by date
  ↓
Update UI with article counts
```

### Component Interaction

```
Timeline.tsx
  ├─ useSearchParams() → URL params
  ├─ useState(showNews) → State management
  ├─ useTimelineNews() → News fetching
  └─ Render news badges & articles
```

## Troubleshooting

### Issue: News coverage not showing

**Check:**
1. URL parameter is exactly `?news=true` (case-sensitive)
2. Frontend is running on correct port
3. Backend API is accessible
4. Console shows `forceShowNews=true`

**Solution:**
```bash
# Verify URL
curl http://localhost:5173/timeline?news=true

# Check backend
curl http://localhost:8081/api/v2/news/search?limit=1
```

### Issue: "0 articles" displayed

**Check:**
1. Console logs show article count > 0
2. `useTimelineNews` fetch completed successfully
3. `articlesByDate` object has entries
4. Date range is valid

**Solution:**
```javascript
// Check console for:
[useTimelineNews] Fetch complete {
  articleCount: 213  // Should be > 0
}
```

### Issue: URL parameter ignored

**Check:**
1. React Router is configured correctly
2. `useSearchParams` is imported from `react-router-dom`
3. Browser supports URL parameters

**Solution:**
Verify import:
```typescript
import { useSearchParams } from 'react-router-dom';
```

## Future Enhancements

### Additional Parameters

Could support additional URL parameters:

```
?news=true&source=timeline  # Show only timeline events with news
?news=true&category=case    # Show only case-related events with news
?news=true&search=Maxwell   # Search + news coverage
```

### Implementation:

```typescript
const sourceParam = searchParams.get('source') as SourceFilter;
const categoryParam = searchParams.get('category') as CategoryFilter;
const searchParam = searchParams.get('search');

useEffect(() => {
  if (sourceParam) setSourceFilter(sourceParam);
  if (categoryParam) setSelectedCategory(categoryParam);
  if (searchParam) setSearchQuery(searchParam);
}, [searchParams]);
```

## Summary

**Problem**: User seeing "0 articles" despite all fixes
**Solution**: URL parameter control bypasses state/cache issues
**Implementation**: `?news=true` parameter forces news coverage ON
**Benefit**: Reliable, shareable, bookmarkable timeline with news

**Key Files Modified**:
- `frontend/src/pages/Timeline.tsx` - URL parameter detection and state override
- `frontend/src/hooks/useTimelineNews.ts` - Enhanced logging

**Testing**:
```bash
# Open browser to:
http://localhost:5173/timeline?news=true

# Expected: News coverage ON, articles loaded, badge shows count
```

---

**Status**: ✅ Implemented and ready for testing
**Date**: 2025-01-22
**Priority**: HIGH - Resolves persistent "0 articles" issue
