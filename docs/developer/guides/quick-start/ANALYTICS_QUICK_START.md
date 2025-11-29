# Analytics Dashboard - Quick Start Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- People vs Organizations breakdown
- Court Documents vs News Articles
- Nodes, Edges, Average Connections
- Data completeness visualization
- ✈️ Flight Logs

---

## 🚀 Access the Dashboard

### Method 1: Navigation Menu
1. Open the application in your browser
2. Click **"Visualizations"** in the top navigation bar
3. Select **"Analytics Dashboard"** from the dropdown

### Method 2: Direct URL
Navigate directly to: **`http://localhost:3000/analytics`**

---

## 📊 What You'll See

### 8 Key Metric Cards

1. **Total Entities** - All people and organizations tracked
2. **Flight Logs** - Total flights with passenger count
3. **Documents** - Court documents and sources
4. **Network Size** - Graph nodes and connections
5. **Timeline Events** - Documented historical events
6. **News Coverage** - Articles and publications
7. **Vector Store** - Embedded documents for search
8. **Average Connections** - Network connectivity metric

### 4 Interactive Visualizations

1. **Entity Type Distribution** (Pie Chart)
   - People vs Organizations breakdown

2. **Document Type Distribution** (Pie Chart)
   - Court Documents vs News Articles

3. **Network Graph Metrics** (Bar Chart)
   - Nodes, Edges, Average Connections

4. **Entity Biography Coverage** (Pie Chart)
   - Data completeness visualization

### Data Coverage Timeline

Shows date ranges for:
- ✈️ Flight Logs
- 📅 Timeline Events
- 🌐 News Articles

---

## 💾 Export Your Data

### Export as CSV (Spreadsheet)

1. Click **"Export CSV"** button (top-right)
2. File downloads automatically as: `epstein-analytics-YYYY-MM-DD.csv`
3. Open in Excel, Google Sheets, or any spreadsheet application

**CSV Contents:**
```
Metric,Category,Value
Total Documents,Documents,5678
Total Entities,Entities,2345
...
```

### Export as JSON (Data File)

1. Click **"Export JSON"** button (top-right)
2. File downloads as: `epstein-analytics-YYYY-MM-DD.json`
3. Use for data analysis, backups, or API testing

**JSON Contents:**
- Complete unified stats response
- Preserves all data structure
- Machine-readable format

---

## 🔄 Refresh Data

Click the **"Refresh Data"** button at the bottom of the page to:
- Bypass cache (60-second TTL)
- Fetch latest statistics
- Update all visualizations instantly

---

## 📱 Mobile & Tablet Support

The dashboard is fully responsive:

- **Desktop (≥1024px)**: 4 cards per row, 2 charts per row
- **Tablet (768-1023px)**: 2 cards per row, 1 chart per row
- **Mobile (<768px)**: 1 card per row, stacked layout

---

## 🎨 Understanding the Charts

### Pie Charts
- **Hover** over any segment to see exact numbers
- **Percentage** automatically calculated
- **Color Legend** explains each segment

### Bar Charts
- **Horizontal bars** show comparative metrics
- **Axis labels** indicate scale
- **Tooltips** display exact values

---

## ⚠️ Status Indicators

### Success (Green)
All data sources loaded successfully

### Partial (Yellow/Orange)
Some data sources unavailable, but displaying available metrics

### Error (Red)
Failed to load data - check backend connection

---

## 🔧 Troubleshooting

### "Failed to load analytics data"
**Solution:** Ensure backend server is running on port 8000
```bash
# Check if server is running
curl http://localhost:8000/api/v2/stats

# Start server if needed
python server/app.py
```

### Charts not displaying
**Solution:**
1. Check browser console for errors
2. Ensure JavaScript is enabled
3. Try refreshing the page

### Export buttons not working
**Solution:**
1. Check browser download settings
2. Ensure pop-ups are not blocked
3. Try a different browser

---

## 📖 Key Features Summary

✅ **Comprehensive Metrics** - 8 key statistics cards
✅ **Visual Analytics** - 4 interactive chart types
✅ **Data Export** - CSV and JSON formats
✅ **Date Ranges** - Coverage timeline display
✅ **Responsive Design** - Works on all devices
✅ **Loading States** - Smooth skeleton loaders
✅ **Error Handling** - Graceful degradation
✅ **Refresh Control** - Manual data updates

---

## 🎯 Common Use Cases

### 1. Overview Report
**Goal:** Get a complete snapshot of archive data

**Steps:**
1. Navigate to Analytics Dashboard
2. Review all 8 metric cards
3. Click "Export JSON" to save complete report
4. Share with stakeholders

### 2. Data Quality Assessment
**Goal:** Check biography coverage and completeness

**Steps:**
1. Look at "Entity Biography Coverage" pie chart
2. Note percentage of entities with biographies
3. Export CSV for detailed analysis
4. Identify gaps in data

### 3. Network Analysis
**Goal:** Understand connection density

**Steps:**
1. Check "Network Size" metric card
2. Review "Network Graph Metrics" bar chart
3. Note average connections per entity
4. Compare with target metrics

### 4. Timeline Research
**Goal:** Identify date coverage gaps

**Steps:**
1. Scroll to "Data Coverage Timeline" section
2. Review date ranges for each source
3. Identify periods with missing data
4. Plan data collection priorities

### 5. Progress Tracking
**Goal:** Monitor archive growth over time

**Steps:**
1. Export JSON on Day 1
2. Return weekly/monthly
3. Click "Refresh Data"
4. Export JSON again
5. Compare metrics to track growth

---

## 🔗 Related Pages

- **Network Graph** - Interactive visualization of entity connections
- **Adjacency Matrix** - Entity relationship matrix view
- **Calendar Heatmap** - Flight activity over time
- **Home Dashboard** - Project overview and recent updates

---

## 💡 Pro Tips

1. **Regular Exports**: Schedule weekly CSV exports to track trends
2. **Browser Bookmarks**: Bookmark `/analytics` for quick access
3. **Multiple Tabs**: Open different visualizations side-by-side
4. **Screenshot Sharing**: Use browser screenshot tools to share charts
5. **JSON Analysis**: Import JSON exports into Python/R for deeper analysis

---

## 📞 Support

### Need Help?
- Check the full implementation guide: `ANALYTICS_DASHBOARD_IMPLEMENTATION.md`
- Review visual guide: `ANALYTICS_VISUAL_GUIDE.md`
- Inspect browser console for error messages

### Found a Bug?
- Note the error message
- Check backend logs: `server/logs/`
- Review API response: `http://localhost:8000/api/v2/stats`

---

## 🎓 Advanced Usage

### API Integration
Fetch stats programmatically:
```bash
curl http://localhost:8000/api/v2/stats
```

### Custom Sections
Request specific data sections:
```bash
curl 'http://localhost:8000/api/v2/stats?sections=entities,flights,news'
```

### Cache Control
Bypass cache for fresh data:
```bash
curl 'http://localhost:8000/api/v2/stats?use_cache=false'
```

---

**Quick Start Version:** 1.0
**Last Updated:** November 20, 2025
**Estimated Reading Time:** 5 minutes
**Difficulty Level:** Beginner-Friendly

---

## ✨ Getting Started Checklist

- [ ] Access dashboard via menu or URL
- [ ] Review all 8 metric cards
- [ ] Explore each visualization
- [ ] Try hovering over charts
- [ ] Export data as CSV
- [ ] Export data as JSON
- [ ] Click "Refresh Data" button
- [ ] Test on mobile device
- [ ] Bookmark the page
- [ ] Share with team members

---

**Ready to explore your data? Navigate to `/analytics` now!** 🚀
