# Entity Type Filter - Manual Testing Guide

## Prerequisites
- Server running on http://localhost:8000
- Browser open with developer console

## Test Steps

### Test 1: Verify API v2 Returns Entity Types
Open browser console and run:
```javascript
fetch('http://localhost:8000/api/v2/entities?limit=5', {
    credentials: 'include'
}).then(r => r.json()).then(data => {
    console.log('First 5 entities:');
    data.entities.forEach(e => {
        console.log(`  ${e.name}: type=${e.entity_type}`);
    });
});
```

**Expected**: Each entity should have `entity_type` field (person/business/location/organization)

### Test 2: Test Type Filter - Business
1. Navigate to http://localhost:8000
2. Click on "Entities" tab
3. In the filter dropdown, select "Business" from "By Type" section
4. **Expected**: Only business entities shown (companies, trusts, corporations)
5. Check console for: `console.log('Filtered entities:', filtered.length)`

### Test 3: Test Type Filter - Person
1. Select "Person" from type filter
2. **Expected**: ~1600+ person entities shown
3. Verify count in UI updates

### Test 4: Test Type Filter - Location
1. Select "Location" from type filter
2. **Expected**: ~3 location entities shown (estates, islands, airports)

### Test 5: Combined Filter Test
1. Select "Person" from type filter
2. Type "Maxwell" in search box
3. **Expected**: Only persons with "Maxwell" in name shown
4. Count should be small (< 10)

### Test 6: Verify Filter Reset
1. Select "All Entities" from filter dropdown
2. Clear search box
3. **Expected**: All ~1700 entities shown

## Debugging

If filters don't work:

### Check 1: API Endpoint
Open console and check network tab:
- Look for request to `/api/v2/entities` (NOT `/api/entities`)
- Response should include `entity_type` field

### Check 2: Entity Data Structure
In console, run:
```javascript
console.log('Sample entity:', allEntitiesData[0]);
```
**Expected**: Should include `entity_type` field

### Check 3: Filter Function
In console, run:
```javascript
// Get filter value
const filterVal = document.getElementById('entity-filter').value;
console.log('Current filter:', filterVal);

// Manually test filter
const testEntity = allEntitiesData[0];
console.log('Test entity type:', testEntity.entity_type);
```

## Success Criteria

✅ All entity type filters work (Person/Business/Location/Organization)
✅ Combined search + type filter works
✅ Entity count updates correctly
✅ API v2 endpoint is being used
✅ No console errors
✅ Entities display with correct entity_type

## Common Issues

### Issue: No entities shown after filter
**Cause**: Filter value doesn't match any entities
**Fix**: Select "All Entities" to reset

### Issue: Console error "entity_type is undefined"
**Cause**: API v1 being used instead of v2
**Fix**: Check app.js line 2238 uses `/v2/entities`

### Issue: Wrong entities shown for type
**Cause**: Keyword detection giving false positives
**Expected**: Small number of false positives is acceptable
**Example**: "Driver, Minnie" might show as location (contains "drive")

## Performance Check

Entity filtering should be instant (<100ms):
```javascript
console.time('filter');
filterEntities('test');
console.timeEnd('filter');
```

**Expected**: < 100ms for 1700 entities

---

**Quick Test Command** (paste in console):
```javascript
// Quick test all filters
['type:person', 'type:business', 'type:location', 'type:organization'].forEach(filterVal => {
    document.getElementById('entity-filter').value = filterVal;
    filterEntities('');
    const count = document.querySelectorAll('.entity-card').length;
    console.log(`${filterVal}: ${count} entities`);
});
// Reset
document.getElementById('entity-filter').value = 'all';
filterEntities('');
```

**Expected Output**:
```
type:person: ~1600 entities
type:business: ~14 entities
type:location: ~3 entities
type:organization: ~0-5 entities
```
