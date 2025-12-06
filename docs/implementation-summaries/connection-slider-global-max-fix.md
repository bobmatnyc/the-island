# Connection Slider Global Max Fix

**Date**: 2025-12-06
**Issue**: Connection slider max value was recalculated from current page data, causing jumping behavior when navigating pages
**File Modified**: `frontend/src/pages/Entities.tsx`

## Problem Description

The connection slider on the Entities page had poor UX when decreasing the minimum connection threshold because the slider's max value was dynamically recalculated from the **current page's entities** rather than the **global maximum**.

**Symptoms**:
- Page 1: slider max = 1,431
- Page 2: slider max = 777
- Page 3: slider max = 272
- Moving slider down was difficult as scale kept changing between pages

## Solution Implemented

### Changes Made

#### 1. Added Global Max State (Line 42)
```typescript
const [globalMaxConnections, setGlobalMaxConnections] = useState(100);
```

#### 2. Fetch Global Max on Mount (Lines 70-93)
```typescript
// Fetch global max connection count once on mount
useEffect(() => {
  const fetchGlobalMax = async () => {
    try {
      // Fetch all entities to find true maximum
      const response = await api.getEntities({ limit: 2000 });

      // Find the maximum connection_count across ALL entities
      const max = Math.max(
        ...response.entities.map(e => e.connection_count || 0),
        100 // Fallback minimum
      );

      setGlobalMaxConnections(max);
      console.log(`Global max connections: ${max}`);
    } catch (error) {
      console.error('Failed to fetch global max connections:', error);
      // Fallback to a reasonable default
      setGlobalMaxConnections(1500);
    }
  };

  fetchGlobalMax();
}, []); // Empty dependency array = run once on mount
```

#### 3. Removed Dynamic Max Calculation (Previously Lines 128-129)
```typescript
// REMOVED these lines:
// const maxConns = Math.max(...filteredEntities.map(e => e.connection_count || 0), 100);
// setMaxConnections(maxConns);
```

#### 4. Updated Slider to Use Global Max (Line 356)
```typescript
// OLD: max={maxConnections}
// NEW: max={globalMaxConnections}
<input
  type="range"
  min="0"
  max={globalMaxConnections}  // ✅ Now uses constant global max
  value={filters.minConnections}
  onChange={(e) => updateFilter('minConnections', Number(e.target.value))}
  className="flex-1 h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
/>
```

#### 5. Updated Max Display Label (Line 362)
```typescript
// OLD: {maxConnections}
// NEW: {globalMaxConnections}
<span className="text-xs text-muted-foreground">{globalMaxConnections}</span>
```

#### 6. Added Info Tooltip (Lines 340-345)
```typescript
<span
  className="text-muted-foreground cursor-help"
  title="Connections represent co-appearances in flight logs. Not all entities appear in the flight network."
>
  ℹ️
</span>
```

## Code Impact

### Lines Changed
- **Added**: ~24 lines (new useEffect hook + tooltip)
- **Removed**: ~2 lines (dynamic max calculation)
- **Modified**: ~3 lines (slider attributes + label)
- **Net Impact**: +19 lines

### State Management
- **Kept**: `maxConnections` state (backward compatibility, currently unused)
- **Added**: `globalMaxConnections` state (new constant slider max)
- **Removed**: Dynamic recalculation of max on every filter change

### Performance Impact
- **Initial Load**: One additional API call to fetch global max (2000 entities)
- **Subsequent Operations**: No additional overhead (uses cached value)
- **Benefit**: Eliminates repeated max calculations on every page change

## Expected Behavior After Fix

### ✅ Slider Stability
- Slider max label shows constant value across all pages
- No jumping when navigating between pages
- Smooth bidirectional movement (up and down)

### ✅ Global Max Value
- Console logs: `Global max connections: {value}` on mount
- Value should be ~1,431 (highest connection count in dataset)
- Slider max label displays global max consistently

### ✅ Filtering Correctness
- minConnections=0: Shows all entities (including zero connections)
- minConnections=100: Shows only entities with 100+ connections
- Pagination works correctly with connection filter

### ✅ Performance
- Single fetch on mount (one-time cost)
- No repeated max calculations on filter changes
- No noticeable performance degradation

## Testing Checklist

### Manual Testing Required
- [ ] Navigate to Entities page → check console for global max log
- [ ] Navigate between pages → verify slider max stays constant
- [ ] Move slider left (decrease) → confirm smooth movement
- [ ] Move slider right (increase) → confirm smooth movement
- [ ] Apply other filters → verify slider max unchanged
- [ ] Hover info icon → verify tooltip appears
- [ ] Set minConnections=100 → verify filtering works
- [ ] Set minConnections=0 → verify all entities shown

### Browser Console Verification
```javascript
// Expected console output on page load:
Global max connections: 1431
```

## Rollback Plan

If issues arise, revert the following changes in `frontend/src/pages/Entities.tsx`:

1. Remove `globalMaxConnections` state (line 42)
2. Remove global max fetch useEffect (lines 70-93)
3. Restore dynamic max calculation:
   ```typescript
   const maxConns = Math.max(...filteredEntities.map(e => e.connection_count || 0), 100);
   setMaxConnections(maxConns);
   ```
4. Change slider: `max={maxConnections}` instead of `max={globalMaxConnections}`
5. Change label: `{maxConnections}` instead of `{globalMaxConnections}`
6. Remove info tooltip (lines 340-345)

## Future Enhancements

### Backend Optimization (Optional)
Consider adding a backend endpoint to fetch just the max value:
```python
@app.get("/api/entities/max-connections")
async def get_max_connections() -> dict:
    """Return the maximum connection count across all entities."""
    max_conn = db.query(func.max(Entity.connection_count)).scalar()
    return {"max_connections": max_conn or 0}
```

This would reduce the initial API call from fetching 2000 entities to a single aggregate query.

### State Management Cleanup
The `maxConnections` state variable is currently kept for backward compatibility but is no longer used. Future refactoring could remove it entirely if no other components depend on it.

## Related Issues

- **Root Cause**: Dynamic slider max recalculated per page
- **Impact**: Poor UX when decreasing connection threshold
- **Resolution**: Global static max fetched once on mount

## Lessons Learned

1. **Slider controls should have stable ranges**: Changing slider max dynamically creates confusing UX
2. **Global aggregates belong at mount time**: Don't recalculate global stats on every filter change
3. **Tooltips improve UX**: Info icons help explain domain concepts to users
4. **Console logs for debugging**: Helpful to log global max for verification

---

**Status**: ✅ Implemented
**Verified**: Pending manual testing
**Deployed**: Pending
