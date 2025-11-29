# Timeline Mentions Visualization Feature

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- **X-axis**: Time (months/years) from oldest to newest (1995-2024)
- **Y-axis**: Total number of mentions
- **Visualization Type**: Stacked area chart with smooth curves
- **Color Coding**:
- 🔵 Blue: Documents (court filings, depositions)

---

## Overview

The Timeline Mentions visualization provides a comprehensive view of entity mentions over time across all data sources in the Epstein archive. This feature enables users to analyze mention patterns, identify trends, and understand the temporal distribution of references to specific entities.

## Features

### 1. Stacked Area Chart Visualization
- **X-axis**: Time (months/years) from oldest to newest (1995-2024)
- **Y-axis**: Total number of mentions
- **Visualization Type**: Stacked area chart with smooth curves
- **Color Coding**:
  - 🔵 Blue: Documents (court filings, depositions)
  - 🔴 Red: Flight logs (passenger lists)
  - 🟢 Green: News articles (media coverage)

### 2. Interactive Filtering
- **Entity Filter**: Dropdown to filter mentions by specific entity
  - Pre-populated with top 50 entities by mention count
  - Supports searching through entity names
- **Date Range Filter**:
  - Start date filter (YYYY-MM)
  - End date filter (YYYY-MM)
- **Apply/Clear Buttons**: Apply filters or reset to view all data

### 3. Summary Statistics
- **Total Mentions**: Aggregate count across all sources
- **Time Range**: Number of months in the dataset
- **Peak Month**: Month with highest mention count
- **Data Sources**: Active data source indicators

### 4. Data Export
- **CSV Export**: Download timeline data as CSV
- **JSON Export**: Download complete data structure
- **Filename**: Includes current date for version tracking

### 5. Interactive Tooltips
- Hover over chart to see detailed breakdown
- Shows exact counts per data source
- Displays formatted month/year
- Total mentions for that month

## Implementation

### Backend API Endpoint

**Endpoint**: `/api/v2/analytics/timeline-mentions`

**Query Parameters**:
- `entity_id` (optional): Filter by specific entity name (e.g., "Jeffrey Epstein")
- `start_date` (optional): Start date filter (YYYY-MM-DD)
- `end_date` (optional): End date filter (YYYY-MM-DD)

**Response Format**:
```json
{
  "timeline": [
    {
      "month": "2019-01",
      "documents": 150,
      "flights": 20,
      "news": 5,
      "total": 175
    }
  ],
  "entity": "Jeffrey Epstein",
  "date_range": {
    "start": "1995-11",
    "end": "2024-11"
  },
  "total_mentions": 1155,
  "data_sources": {
    "documents": true,
    "flights": true,
    "news": true
  }
}
```

### Frontend Component

**Location**: `/frontend/src/components/visualizations/TimelineMentions.tsx`

**Key Technologies**:
- React with TypeScript
- Recharts for visualization
- ShadCN UI components for interface
- Responsive design for all screen sizes

**Integration**: Added to Analytics page (`/frontend/src/pages/Analytics.tsx`)

## Data Sources

### 1. Flight Logs
- **Source**: `data/md/entities/flight_logs_by_flight.json`
- **Date Format**: MM/DD/YYYY
- **Aggregation**: One mention per flight per passenger
- **Coverage**: 1995-2005

### 2. News Articles
- **Source**: `data/metadata/news_articles_index.json`
- **Date Format**: YYYY-MM-DD
- **Aggregation**: Counts actual entity mentions in articles
- **Coverage**: 2019-2024

### 3. Court Documents
- **Source**: `data/metadata/all_documents_index.json`
- **Date Format**: Variable (from metadata)
- **Aggregation**: Entity mentions in documents
- **Coverage**: Limited date metadata availability

## Usage Examples

### Example 1: View All Mentions
Navigate to Analytics page → Timeline Mentions section shows all entity mentions from 1995-2024.

### Example 2: Filter by Entity
1. Select "Jeffrey Epstein" from entity dropdown
2. Click "Apply"
3. View timeline showing only Jeffrey Epstein mentions (1,155 total)

### Example 3: Date Range Analysis
1. Set start date: 2019-01
2. Set end date: 2024-12
3. Click "Apply"
4. Analyze recent news coverage patterns (67 mentions)

### Example 4: Export Data
1. Configure desired filters
2. Click "CSV" or "JSON" button
3. Download file with name: `timeline-mentions-YYYY-MM-DD.csv`

## Performance Characteristics

- **Response Time**: < 1 second for full dataset
- **Data Processing**: O(n) where n = total data items
- **Caching**: Not implemented (lightweight aggregation)
- **Scalability**: Handles current dataset efficiently

## API Testing

Run the test script:
```bash
./test-timeline-mentions.sh
```

**Test Results** (2025-11-21):
- ✅ All mentions: 1,237 total across 144 months (1995-2024)
- ✅ Jeffrey Epstein filter: 1,155 mentions across 138 months
- ✅ Ghislaine Maxwell filter: 47 mentions across 13 months
- ✅ Date range filter (2019-2024): 67 mentions across 25 months

## Visual Design

### Chart Features
- Smooth curved areas (monotone interpolation)
- Gradient fills for visual appeal
- Grid lines for easy value reading
- Responsive legend
- Interactive tooltips with detailed breakdowns

### Color Accessibility
- High contrast color scheme
- Distinct colors for colorblind users
- Clear legend with text labels
- Visual indicators beyond just color

### Responsive Design
- Mobile: Single column layout
- Tablet: Optimized grid layout
- Desktop: Full width chart with side-by-side filters

## Future Enhancements

### Potential Improvements
1. **Zoom and Pan**: Enable interactive chart navigation
2. **Annotation Layer**: Mark significant events on timeline
3. **Comparative View**: Compare multiple entities side-by-side
4. **Trend Analysis**: Show moving averages or trend lines
5. **Document Links**: Click through to source documents
6. **Advanced Filters**: Filter by mention type, source credibility
7. **Time Granularity**: Switch between daily/weekly/monthly/yearly views
8. **Export to PNG**: Visual chart export in addition to data

## Files Modified/Created

### Backend
- ✅ `/server/routes/stats.py` - Added timeline mentions endpoint

### Frontend
- ✅ `/frontend/src/components/visualizations/TimelineMentions.tsx` - Main component
- ✅ `/frontend/src/pages/Analytics.tsx` - Integration

### Testing
- ✅ `/test-timeline-mentions.sh` - API test suite

### Documentation
- ✅ `/TIMELINE_MENTIONS_FEATURE.md` - This file

## Success Criteria

All requirements met:
- ✅ Timeline displays mentions from oldest to newest (1995 → 2024)
- ✅ X-axis shows months/years clearly
- ✅ Y-axis shows mention counts
- ✅ Color bands distinguish mention types (blue/red/green)
- ✅ Entity filter works to show specific entity timeline
- ✅ Date range filters function correctly
- ✅ Responsive and performs well with full dataset
- ✅ Tooltips show detailed breakdown on hover
- ✅ Integrates seamlessly with Analytics page
- ✅ Data export functionality (CSV/JSON)
- ✅ Summary statistics display

## Developer Notes

### Entity Matching Logic
The entity filter uses case-insensitive partial matching:
- Matches if `entity_id` appears in stored entity name
- Matches if stored entity name appears in `entity_id`
- Works with both full names ("Jeffrey Epstein") and partial matches

### Date Parsing
Handles multiple date formats:
- MM/DD/YYYY (flight logs)
- YYYY-MM-DD (news articles)
- Various ISO formats (documents)
- Normalizes all to YYYY-MM for aggregation

### Error Handling
- Graceful degradation if data sources unavailable
- Continues processing other sources if one fails
- Displays helpful error messages to users
- Logs errors to server console for debugging

## Maintenance

### Regular Updates
- Entity list refreshes on component mount
- Data fetches fresh from API on filter changes
- No client-side caching (server-side could be added)

### Monitoring
- Check API response times in production
- Monitor for errors in data parsing
- Track user interactions with filters

---

**Status**: ✅ Complete and Production Ready
**Version**: 1.0
**Last Updated**: 2025-11-21
**Author**: Claude (React Engineer)
