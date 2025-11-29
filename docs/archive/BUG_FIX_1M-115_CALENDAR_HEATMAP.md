# Bug Fix: 1M-115 - Calendar Heatmap Sparse Data

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- LZU, MCN, MDW, MIV, MRY, MTN, OAK, OEO, OFF, OQU
- OSU, PBF, PVD, RIC, RSW, SAF, SAN, SBA, SJC
- TED, TGB, TIX, TVC, VNC
- **Before**: 922 flights visible (79% of 1,167 total)
- **After**: 1,082 flights visible (93% of 1,167 total)

---

## Root Cause Analysis

The Calendar Heatmap on `/activity` was showing sparse data due to **two separate issues**:

### Issue 1: Missing Airport Location Data (FIXED) ✅
**Impact**: 160 flights (14% of total) were excluded from visualization
**Cause**: 24 airport codes were missing from `flight_locations.json` database
**Fix**: Added missing airport coordinates for all 24 codes

**Missing Airport Codes**:
- LZU, MCN, MDW, MIV, MRY, MTN, OAK, OEO, OFF, OQU
- OSU, PBF, PVD, RIC, RSW, SAF, SAN, SBA, SJC
- TED, TGB, TIX, TVC, VNC

**Results**:
- **Before**: 922 flights visible (79% of 1,167 total)
- **After**: 1,082 flights visible (93% of 1,167 total)
- **Improvement**: +160 flights (+17% more data)

### Issue 2: Limited to Flight Data Only (DESIGN ISSUE)
**Observation**: The Activity page is titled "Flight Activity Calendar" and only shows flight data
**User Expectation**: The Linear ticket suggests expectation of "activity/event density across calendar dates"
**Available Data Sources**:
1. **Flights**: 1,082 flights (1995-2019)
2. **Documents**: ~947 court documents (various dates)
3. **News Articles**: 1,074 news articles (1990s-2025)
4. **Timeline Events**: 98 major biographical/case events (1953-2025)

**Recommendation**: Consider enhancing Activity page to show unified activity from all sources

## Changes Made

### 1. Fixed Missing Airport Data
**File**: `data/metadata/flight_locations.json`
**Change**: Added 24 missing airport codes with geocoordinates

```json
{
  "airports": {
    // ... existing 86 airports
    // Added 24 new airports:
    "MDW": {"name": "Chicago Midway International", "city": "Chicago, IL", "lat": 41.7868, "lon": -87.7522},
    "OAK": {"name": "Oakland International", "city": "Oakland, CA", "lat": 37.7213, "lon": -122.2208},
    "PVD": {"name": "Rhode Island T.F. Green International", "city": "Providence/Warwick, RI", "lat": 41.7240, "lon": -71.4281},
    "RIC": {"name": "Richmond International", "city": "Richmond, VA", "lat": 37.5052, "lon": -77.3197},
    "SAN": {"name": "San Diego International", "city": "San Diego, CA", "lat": 32.7338, "lon": -117.1933},
    // ... 19 more airports
  }
}
```

**Impact**:
- `/api/flights/all` now returns 1,082 flights (was 922)
- Calendar heatmap shows 17% more flight activity
- All valid flight routes now have geocoded locations

### 2. Data Quality Improvements

**Remaining Excluded Flights**:
- 85 flights with "UNKNOWN" routes (7.3% of total)
- These flights have incomplete route information in the source data
- Cannot be mapped without origin/destination airport codes

**Verification**:
```bash
# Test API endpoint
curl http://localhost:8081/api/flights/all | jq '{total_flights, unique_routes}'

# Result:
# {
#   "total_flights": 1082,
#   "unique_routes": 254
# }
```

## Testing

### Before Fix
1. Navigate to http://localhost:5173/activity
2. Select year 2002 (peak flight activity)
3. **Observed**: Sparse calendar with only 922 total flights
4. **Missing**: 160 flights not displayed due to missing airports

### After Fix
1. Navigate to http://localhost:5173/activity
2. Select year 2002
3. **Expected**: Denser calendar showing 1,082 flights
4. **Improvement**: +17% more data points visible

### Verification Commands
```bash
# Count valid flights after fix
python3 << 'EOF'
import json
with open('data/md/entities/flight_logs_by_flight.json') as f:
    flights = json.load(f)['flights']
with open('data/metadata/flight_locations.json') as f:
    airports = json.load(f)['airports']

valid = sum(1 for f in flights
           if '-' in f.get('route', '')
           and f['route'] != 'UNKNOWN'
           and all(code in airports for code in f['route'].split('-')))
print(f"Valid flights: {valid}/{len(flights)}")
EOF
# Output: Valid flights: 1082/1167
```

## Future Enhancements (Optional)

### Enhancement 1: Unified Activity Heatmap
**Current State**: Activity page only shows flight data
**Proposal**: Show combined activity from all data sources

**Implementation Approach**:
1. Create new API endpoint `/api/v2/analytics/activity-calendar`
2. Aggregate events by date from:
   - Flights (1,082 items)
   - Documents (947 items with dates)
   - News Articles (1,074 items)
   - Timeline Events (98 items)
3. Update CalendarHeatmap to consume unified data
4. Add color coding by event type

**Benefits**:
- Much denser calendar visualization (3,000+ events vs. 1,082)
- Better historical coverage (1953-2025 vs. 1995-2019)
- More comprehensive activity overview

**API Exists**: `/api/v2/analytics/timeline-mentions` already provides this aggregation

### Enhancement 2: Event Type Filtering
Add toggles to show/hide different event types:
- ☑️ Flights (1,082)
- ☑️ Documents (947)
- ☑️ News (1,074)
- ☑️ Timeline Events (98)

## Files Modified

1. ✅ `data/metadata/flight_locations.json` - Added 24 missing airports
2. 📝 `frontend/src/components/visualizations/CalendarHeatmap.tsx` - No changes needed (automatically picks up new data)
3. 📝 `frontend/src/pages/Activity.tsx` - No changes needed

## Performance Impact

- **API Response**: No change (same endpoint, more complete data)
- **Frontend Rendering**: +17% more DOM elements (minor, within normal range)
- **Memory Usage**: Negligible increase
- **User Experience**: Improved data density and completeness

## Success Metrics

✅ **Fixed**: Missing airport locations (24 codes added)
✅ **Improved**: Flight data coverage from 79% to 93%
✅ **Enhanced**: +160 flights now visible in heatmap
⏳ **Optional**: Consider unified activity heatmap for even better UX

## Deployment Notes

1. Restart backend server to reload updated `flight_locations.json`
2. Hard refresh frontend to clear any cached data
3. Test calendar shows denser data across multiple years

## Related Files

- `data/metadata/flight_locations.json` - Airport database (110 airports)
- `data/md/entities/flight_logs_by_flight.json` - Flight records (1,167 total)
- `server/routes/flights.py` - API endpoint `/api/flights/all`
- `frontend/src/pages/Activity.tsx` - Calendar page component
- `frontend/src/components/visualizations/CalendarHeatmap.tsx` - Heatmap component
