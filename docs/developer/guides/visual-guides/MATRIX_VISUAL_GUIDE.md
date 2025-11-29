# Adjacency Matrix Visual Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Quick Start
- Visual Layout
- Reading the Matrix
- Cell Interpretation

---

## Quick Start

**Access**: http://localhost:5179/matrix

**What You'll See**: A square heatmap grid showing which entities appear together most frequently.

## Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Entity Adjacency Matrix                    [Sort] [N] [Min]│
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Column Headers (Rotated -45°)                              │
│     ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙                                         │
│     E M S E A C N L                                          │
│     p a a l i n d a                                          │
│     s x r d t d i r                                          │
│     Row  w a r r a r                                          │
│  ┌─ e h o c y                                                │
│  │  l . h v                                                  │
│  │  l   K M L N                                              │
│  │    G e i o M                                              │
│  │      l t p o                                              │
│  │      l r e r                                              │
│  ▼      e o z r                                              │
│ Epstein      ⬜102 26  8  5  12  4                           │
│ Maxwell     102 ⬜ 18  3  15  8  6                           │
│ Sarah K      26 18 ⬜  5   9  7  11                          │
│ El Dorfman    8  3  5 ⬜   2  4   5                          │
│ ...                                                          │
│                                                              │
│  Legend: ⬜ = 0   🟦 = 1-5   🟦 = 6-20   🟦 = 21-50   🟦 = 51+│
└─────────────────────────────────────────────────────────────┘
│  Statistics                                                  │
│  275 Total | 30 Displayed | 1,584 Connections | 5.8 Avg     │
│  Strongest: Epstein ↔ Maxwell (102 connections)            │
└─────────────────────────────────────────────────────────────┘
```

## Reading the Matrix

### Cell Interpretation

**Position**: Row × Column intersection
```
            Column: Maxwell
            ↓
Row: Epstein → [102]  ← Connection strength
```

**Meaning**: Jeffrey Epstein and Ghislaine Maxwell appear together in 102 flights or documents.

### Color Coding

**Visual Examples** (using emoji approximation):
```
⬜ White/Gray    = No connections (0)
🟦 Light Blue   = Weak connection (1-5)
🟦 Medium Blue  = Moderate connection (6-20)
🟦 Dark Blue    = Strong connection (21-50)
🟦 Navy Blue    = Very strong connection (51+)
```

**Real Example**:
```
                Epstein  Maxwell  Clinton  Trump
Epstein           ⬜       🟦       🟦      🟦
Maxwell           🟦       ⬜       🟦      🟦
Clinton           🟦       🟦       ⬜      🟦
Trump             🟦       🟦       🟦      ⬜
```

## Interactive Features

### 1. Hover Tooltips

**Action**: Move mouse over any colored cell

**Display**:
```
┌──────────────────────────────┐
│ Jeffrey Epstein ↔            │
│ Ghislaine Maxwell            │
│                              │
│ 102 connections              │
└──────────────────────────────┘
```

### 2. Filter Controls

**Top-Right Controls**:
```
[Sort By ▼]  [Show Top N]  [Min. Connections]  [Color Scheme ▼]
Most Conn.      30             0                   Blue
```

**Sort By Options**:
- **Most Connected**: Highest connection count first (default)
- **Alphabetical**: A-Z by name

**Show Top N**:
- Range: 10 to 100 entities
- Default: 30 entities
- Lower = faster rendering, focus on core network

**Min. Connections**:
- Range: 0 to 50
- Default: 0 (show all)
- Higher = filter out peripheral entities

**Color Scheme**:
- Blue (default) - Professional
- Red - Alternative
- Green - Alternative

### 3. Statistics Panel

**Bottom Section**:
```
┌─────────────────────────────────────────────────┐
│ Matrix Statistics                               │
├────────────┬────────────┬────────────┬──────────┤
│ 275        │ 30         │ 1,584      │ 5.8      │
│ Total      │ Displayed  │ Total      │ Avg.     │
│ Entities   │            │ Connections│ Connections
└────────────┴────────────┴────────────┴──────────┘
│                                                  │
│ Strongest Connection                             │
│ Jeffrey Epstein ↔ Ghislaine Maxwell             │
│ 102 shared connections                           │
└──────────────────────────────────────────────────┘
```

## Analysis Patterns

### Pattern 1: Finding Key Players

**Goal**: Identify most connected entities

**Steps**:
1. Ensure **Sort By** = "Most Connected"
2. Look at **top-left corner** of matrix
3. Darker colors = more important

**Visual**:
```
First row/column = Jeffrey Epstein (262 connections)
Second row/column = Ghislaine Maxwell (188 connections)
Third row/column = Sarah Kellen (135 connections)
```

### Pattern 2: Discovering Clusters

**Goal**: Find groups that interact frequently

**Steps**:
1. Set **Show Top N** = 20 (smaller matrix)
2. Look for **dark blue squares** in clusters
3. Cluster = group with many dark cells

**Visual Example**:
```
          A  B  C  D  E  F
    A     ⬜ 🟦 🟦 ⬜ ⬜ ⬜
    B     🟦 ⬜ 🟦 ⬜ ⬜ ⬜  ← A-B-C cluster
    C     🟦 🟦 ⬜ ⬜ ⬜ ⬜
    D     ⬜ ⬜ ⬜ ⬜ 🟦 🟦
    E     ⬜ ⬜ ⬜ 🟦 ⬜ 🟦  ← D-E-F cluster
    F     ⬜ ⬜ ⬜ 🟦 🟦 ⬜
```

### Pattern 3: Filtering Noise

**Goal**: Focus on core network members only

**Steps**:
1. Set **Min. Connections** = 10
2. Set **Show Top N** = 30
3. Matrix now shows only well-connected entities

**Before**:
```
275 entities displayed (including many with 1-2 connections)
```

**After**:
```
45 entities displayed (only those with 10+ connections)
```

### Pattern 4: Comparing Relationships

**Goal**: See who connects to both Entity A and Entity B

**Steps**:
1. Find Entity A's row (horizontal)
2. Find Entity B's column (vertical)
3. Where they intersect = their direct connection
4. Scan A's row and B's column for mutual connections

**Visual**:
```
          E  M  S  K  L
    E     ⬜ 🟦 🟦 ⬜ 🟦  ← Epstein's connections
    M     🟦 ⬜ 🟦 ⬜ 🟦  ← Maxwell's connections
              ↑
           Both connect to Sarah (S) and Lopez (L)
```

## Common Use Cases

### Use Case 1: Investigating an Entity

**Scenario**: User wants to know who Jeffrey Epstein associated with most

**Steps**:
1. Navigate to Matrix page
2. Sort by "Most Connected" (Epstein will be first row)
3. Scan first row for darkest cells
4. Hover over dark cells to see connection counts

**Result**: See Ghislaine Maxwell (102), Sarah Kellen (26), etc.

### Use Case 2: Finding All Connections Above Threshold

**Scenario**: Show only relationships with 20+ shared flights

**Steps**:
1. Look at color legend (20+ = dark blue or navy)
2. Visually scan for dark blue cells
3. Hover to confirm exact count
4. Note entity pairs with 20+ connections

**Alternative**:
- Future enhancement: Add "Min. Connection Strength" filter for cells

### Use Case 3: Comparing Two Entities

**Scenario**: Do Entity A and Entity B share connections?

**Steps**:
1. Find Entity A's row (horizontal)
2. Find Entity B's row (horizontal)
3. Look for columns where both have dark cells
4. Those are shared connections

**Visual**:
```
          X  Y  Z
    A     🟦 🟦 ⬜  ← A connects to X, Y
    B     🟦 ⬜ 🟦  ← B connects to X, Z
          ↑
       Both connect to X (shared connection)
```

## Tips & Tricks

### Tip 1: Performance Optimization

**Problem**: Large matrix (100×100) is slow to render

**Solution**:
- Reduce **Show Top N** to 30-50
- Increase **Min. Connections** to filter entities
- Use **Most Connected** sort to see important entities first

### Tip 2: Finding Specific Entities

**Current Method** (manual):
- Sort alphabetically
- Scroll to find entity name

**Future Enhancement**: Search box to filter by name

### Tip 3: Color Scheme Selection

**Blue** (default):
- Professional appearance
- High contrast
- Recommended for most users

**Red**:
- Alternative if you prefer warm colors
- May indicate "warning" associations

**Green**:
- Good for accessibility (color blind friendly)
- Neutral associations

### Tip 4: Understanding Symmetry

**Key Insight**: Matrix is symmetric

```
If Cell[A][B] = 10, then Cell[B][A] = 10
```

**Why**: Connection from A to B = connection from B to A
(they appeared together in same flights/documents)

**Visual Confirmation**: Diagonal line of symmetry

```
    A  B  C
A   ⬜ 5  10
B   5  ⬜ 3   ← Mirror symmetry across diagonal
C   10 3  ⬜
```

## Troubleshooting

### Issue 1: Matrix Not Loading

**Symptom**: White page or "Loading..." indefinitely

**Causes & Solutions**:
1. Backend API not running
   ```bash
   # Check if API is running
   curl http://localhost:8081/api/network
   # If fails, start backend server
   ```

2. Network error
   ```
   Check browser console (F12) for errors
   ```

3. Data parsing error
   ```
   Verify API returns valid JSON
   ```

### Issue 2: Colors Not Showing

**Symptom**: All cells are white/gray

**Causes**:
1. No edges in data (all connection weights = 0)
2. JavaScript error preventing color calculation

**Solution**:
```bash
# Verify edges exist in API
curl http://localhost:8081/api/network | grep -o '"edges":\[.*\]' | head -c 100
```

### Issue 3: Slow Performance

**Symptom**: Page lag when hovering or scrolling

**Causes**:
- Too many entities displayed (e.g., 100×100 = 10,000 cells)

**Solutions**:
1. Reduce **Show Top N** to 30
2. Increase **Min. Connections** to 10+
3. Use smaller monitor/browser window (fewer cells rendered)

### Issue 4: Labels Unreadable

**Symptom**: Entity names cut off or overlapping

**Current Behavior**:
- Column headers rotated -45° to save space
- Row labels truncated with ellipsis (...)

**Solution**:
- Hover to see full name in tooltip
- Future enhancement: Adjustable label font size

## Keyboard Shortcuts

**Current**: None implemented

**Future Enhancements**:
- Arrow keys: Navigate cells
- `/`: Focus search box (when implemented)
- `+/-`: Zoom in/out
- `Esc`: Clear selection/highlight

## Accessibility Notes

**Current Implementation**:
- Tooltips on hover (mouse-based)
- Color-coded with legend

**Accessibility Improvements Needed**:
- [ ] Keyboard navigation
- [ ] Screen reader descriptions
- [ ] ARIA labels for matrix cells
- [ ] High contrast mode
- [ ] Alternative to color-only encoding (patterns/textures)

## Data Source Details

**API Endpoint**: `http://localhost:8081/api/network`

**Response Structure**:
```json
{
  "nodes": [
    {
      "id": "Jeffrey Epstein",
      "name": "Jeffrey Epstein",
      "connection_count": 262,
      ...
    }
  ],
  "edges": [
    {
      "source": "Jeffrey Epstein",
      "target": "Maxwell, Ghislaine",
      "weight": 102
    }
  ]
}
```

**Current Data**:
- 275 entities (nodes)
- 1,584 connections (edges)
- Max connection weight: 478 (highest shared flights/interactions)

## Related Pages

- **Network Graph** (`/network`): Force-directed graph of same data
- **Entities** (`/entities`): List view with connection counts
- **Flights** (`/flights`): Flight log data source
- **Timeline** (`/timeline`): Chronological view of events

## Support & Feedback

**For Issues**:
1. Check browser console (F12) for errors
2. Verify backend API is running
3. Try reducing **Show Top N** to 20

**Feature Requests**:
- Search/filter by entity name
- Export to CSV
- Click to highlight row/column
- Cluster detection visualization

---

**Quick Reference Card**:
```
┌──────────────────────────────────────────┐
│ ADJACENCY MATRIX QUICK REFERENCE         │
├──────────────────────────────────────────┤
│ URL: http://localhost:5179/matrix        │
│                                          │
│ COLORS:                                  │
│  ⬜ White = No connection                │
│  🟦 Light = 1-5 connections              │
│  🟦 Medium = 6-20 connections            │
│  🟦 Dark = 21-50 connections             │
│  🟦 Navy = 51+ connections               │
│                                          │
│ CONTROLS:                                │
│  Sort: Most Connected / Alphabetical     │
│  Top N: 10-100 entities (default: 30)    │
│  Min Connections: Filter threshold       │
│  Color: Blue / Red / Green               │
│                                          │
│ TIPS:                                    │
│  • Hover cell for details                │
│  • Smaller N = faster render             │
│  • Top-left = most connected             │
│  • Dark clusters = groups                │
└──────────────────────────────────────────┘
```
