# Calendar Heatmap - Quick Start Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Total Flights**: How many flights occurred that year
- **Active Days**: Number of days with at least one flight
- **Most Active Day**: Day with highest flight count
- **Busiest Month**: Month with most total flights
- **Gray**: No flights that day

---

## Access the Visualization

**URL**: http://localhost:5178/activity

**Navigation**: Click "Activity" in the top navigation bar

## 5-Minute Quick Start

### 1. View Current Year Activity
1. Open http://localhost:5178/activity
2. Default view shows the most recent year with data
3. Hover over colored cells to see flight details

### 2. Switch Years
1. Click the year dropdown (top right)
2. Select any year from 1995 to 2025
3. Heatmap updates immediately

### 3. Filter by Passenger
1. Type a name in the filter box (e.g., "Epstein", "Maxwell", "Clinton")
2. Heatmap updates in real-time
3. Shows only flights with that passenger
4. Click "Clear filter" to reset

### 4. Read Statistics
- **Total Flights**: How many flights occurred that year
- **Active Days**: Number of days with at least one flight
- **Most Active Day**: Day with highest flight count
- **Busiest Month**: Month with most total flights

## Common Use Cases

### Find Someone's Travel Pattern
```
1. Type their name in filter: "Donald Trump"
2. Select year: "2000"
3. Observe colored cells = days they flew
```

### Identify Busy Periods
```
1. Look for darkest blue cells (11+ flights)
2. Check stats panel for "Most Active Day"
3. Hover cells to see passenger lists
```

### Compare Years
```
1. Select year 1995 → note "Total Flights"
2. Select year 2005 → compare total
3. Repeat for pattern analysis
```

### Track Regular Routes
```
1. Filter by frequent flyer (e.g., "Epstein")
2. Look for weekly patterns (same day each week)
3. Hover cells to confirm routes (e.g., "PBI-TEB")
```

## Color Guide (Quick Reference)

- **Gray**: No flights that day
- **Light Blue**: 1-2 flights (minimal activity)
- **Medium Blue**: 3-5 flights (moderate activity)
- **Dark Blue**: 6-10 flights (high activity)
- **Darkest Blue**: 11+ flights (very high activity)

## Tooltip Information

Hover over any cell to see:
- ✈️ **Date**: Full formatted date
- 📊 **Flight Count**: Number of flights that day
- 👥 **Passenger Count**: Unique passengers
- 🗺️ **Routes**: Up to 3 routes (with "more" if applicable)
- 🧑 **Passengers**: Up to 5 names (with "more" if applicable)

## Tips & Tricks

### 💡 Pro Tip #1: Find Cluster Events
Look for consecutive dark blue cells - indicates major event or trip

### 💡 Pro Tip #2: Weekly Commute Detection
Same day each week with flights = regular commute pattern

### 💡 Pro Tip #3: Cross-Reference with Timeline
Use year selector to match timeline events with flight activity

### 💡 Pro Tip #4: Passenger Co-Occurrence
Filter by one person, then check tooltip passenger lists to find companions

### 💡 Pro Tip #5: Seasonal Analysis
Compare same month across different years to spot patterns

## Keyboard Shortcuts

- **Tab**: Navigate between year selector and filter
- **Arrow Keys**: Navigate dropdown options (when open)
- **Enter**: Select dropdown option
- **Escape**: Close dropdown

## Mobile Usage

On mobile devices:
- Swipe left/right to scroll the heatmap
- Tap cells for tooltips (instead of hover)
- Use pinch-to-zoom if needed
- Year selector and filter stack vertically

## Performance Notes

- Year switching is instant (<50ms)
- Filter applies in real-time (<30ms)
- Smooth scrolling on large displays
- Optimized for 1,167 flights across 31 years

## Data Coverage

- **Start Date**: 1995
- **End Date**: 2025 (present)
- **Total Flights**: 1,167
- **Unique Routes**: Multiple international routes
- **Passengers**: Hundreds of named individuals

## Troubleshooting

### Heatmap Not Showing
**Solution**: Refresh page, ensure API is running on port 8081

### Filter Not Working
**Solution**: Clear filter and try again, check spelling

### Year Selector Empty
**Solution**: Ensure backend API is responding (check Network tab)

### Tooltip Not Appearing
**Solution**: Ensure JavaScript is enabled, try different browser

## Integration with Other Pages

This visualization complements:

- **Flights Page**: See detailed flight logs
- **Timeline Page**: Correlate dates with events
- **Network Page**: Understand passenger relationships
- **Entities Page**: Research individual passengers

## Example Queries

### 1. "When did Bill Clinton fly the most?"
```
Filter: "Clinton"
Action: Switch through years, check stats panel
Result: See year + month with most Clinton flights
```

### 2. "What was the busiest day ever?"
```
Action: Switch through each year (1995-2025)
Compare: "Most Active Day" in stats panel
Result: Find highest single-day flight count
```

### 3. "Did flight activity decrease over time?"
```
Action: Start at 1995, note "Total Flights"
Progress: Click through years sequentially
Observe: Trend up or down in total flights
```

### 4. "Who flew with Ghislaine Maxwell in 2002?"
```
Year: 2002
Filter: "Maxwell"
Action: Hover cells, read passenger lists
Result: Co-travelers list
```

## Advanced Patterns

### Pattern 1: Commute Detection
Regular flights on same day of week (e.g., every Monday)

### Pattern 2: Vacation Periods
Long gaps of gray cells = extended stays

### Pattern 3: Event Clustering
Multiple consecutive dark days = major trip or event

### Pattern 4: Route Switching
Different route patterns in different years

### Pattern 5: Co-Travel Analysis
Same passengers appearing together repeatedly

## Screenshot Locations

After using the visualization, check:
- Statistics panel for overall metrics
- Darkest cells for high-activity days
- Tooltips for detailed flight information
- Legend for color scale reference

## Next Steps

After exploring the calendar heatmap:

1. **Flights Page**: See full flight logs with filters
2. **Network Page**: Visualize passenger connections
3. **Timeline Page**: See chronological event sequence
4. **Entities Page**: Research individual profiles

---

**Ready to Explore?** → http://localhost:5178/activity

**Questions?** Check the full implementation guide: `CALENDAR_HEATMAP_IMPLEMENTATION.md`

**Visual Guide**: See `CALENDAR_HEATMAP_VISUAL_GUIDE.md` for detailed screenshots
