# Network Graph Testing Guide

## Quick Start

### 1. Start the Application
```bash
# Terminal 1 - Backend (if not running)
cd /Users/masa/Projects/epstein
python server/app.py

# Terminal 2 - Frontend
cd /Users/masa/Projects/epstein/frontend
npm run dev
```

### 2. Access the Network Page
```
http://localhost:5173/network
```

## Visual Test Checklist

### Initial Load ✅
- [ ] Page loads within 3 seconds
- [ ] Graph displays with 275+ nodes
- [ ] Nodes are positioned in a force-directed layout
- [ ] Color legend visible in top-left
- [ ] Filter panel visible on left
- [ ] Statistics panel visible on right
- [ ] Control buttons visible in top-right of graph

### Graph Interaction ✅

#### Zoom Controls
1. Click **Zoom In** button (+ icon)
   - ✅ Graph should zoom in smoothly
   - ✅ Node labels become more visible

2. Click **Zoom Out** button (- icon)
   - ✅ Graph should zoom out smoothly
   - ✅ More nodes become visible

3. Click **Reset View** button (maximize icon)
   - ✅ Graph fits all visible nodes in viewport
   - ✅ Zoom level resets to optimal

4. Use **mouse wheel** to zoom
   - ✅ Scroll up to zoom in
   - ✅ Scroll down to zoom out

#### Pan Controls
1. Click and drag on empty space
   - ✅ Graph pans in drag direction
   - ✅ Smooth animation

2. Click and drag a node
   - ✅ Node moves to new position
   - ✅ Other nodes adjust via force simulation
   - ✅ Connected edges follow the node

#### Physics Controls
1. Click **Pause** button
   - ✅ Animation stops
   - ✅ Icon changes to Play
   - ✅ Nodes stay in current positions

2. Click **Play** button (after pausing)
   - ✅ Animation resumes
   - ✅ Icon changes to Pause
   - ✅ Force simulation continues

### Node Selection ✅

1. Click any node
   - ✅ Node and connections highlighted
   - ✅ Other nodes fade to 30% opacity
   - ✅ Graph auto-zooms to selected node
   - ✅ Details panel opens on right
   - ✅ Animated particles appear on edges

2. Details Panel Content
   - ✅ Shows entity name
   - ✅ Close button (X) visible
   - ✅ Badges for Black Book/Billionaire (if applicable)
   - ✅ Connection count displayed
   - ✅ Flight count displayed
   - ✅ Categories shown as chips
   - ✅ Direct connections list visible

3. Click another node from connections list
   - ✅ New node selected
   - ✅ Details panel updates
   - ✅ Graph re-centers on new node
   - ✅ Previous selection cleared

4. Click background to deselect
   - ✅ Selection cleared
   - ✅ All nodes return to normal opacity
   - ✅ Details panel closes (statistics panel returns)

### Hover Interactions ✅

1. Hover over a node (without clicking)
   - ✅ Tooltip appears at bottom center
   - ✅ Shows entity name
   - ✅ Shows connection and flight counts
   - ✅ Tooltip follows cursor smoothly

2. Move mouse away
   - ✅ Tooltip disappears

### Filter Testing ✅

#### Search Filter
1. Type "Clinton" in search box
   - ✅ Graph updates to show only matching entities
   - ✅ Edge count updates (only edges between visible nodes)
   - ✅ Statistics update to reflect filtered data
   - ✅ If match found, graph centers on first match

2. Clear search
   - ✅ All nodes reappear
   - ✅ Statistics return to full dataset

#### Category Filter
1. Check one category (e.g., "politician")
   - ✅ Graph shows only entities in that category
   - ✅ Node count updates
   - ✅ Edge count updates

2. Check multiple categories
   - ✅ Graph shows union of selected categories
   - ✅ Counts update correctly

3. Uncheck all categories
   - ✅ All nodes reappear

#### Special Filters
1. Check "In Black Book"
   - ✅ Only Black Book entities visible
   - ✅ All visible nodes are red
   - ✅ Count updates

2. Check "Billionaire"
   - ✅ Only billionaires visible
   - ✅ Count updates

3. Check both filters
   - ✅ Only entities that are BOTH billionaires AND in black book
   - ✅ Intersection logic works

#### Range Filters
1. Drag "Min Connections" slider to 10
   - ✅ Label updates to show "Min Connections: 10"
   - ✅ Only highly connected nodes visible
   - ✅ Graph updates in real-time

2. Drag "Min Flights" slider to 5
   - ✅ Label updates
   - ✅ Only frequent flyers visible
   - ✅ Graph updates smoothly

#### Reset Filters
1. Apply multiple filters
2. Click "Reset Filters" button
   - ✅ All filters cleared
   - ✅ Search box empty
   - ✅ Checkboxes unchecked
   - ✅ Sliders at 0
   - ✅ Full graph restored

### Statistics Panel ✅

1. View default statistics (no node selected)
   - ✅ Shows current node count
   - ✅ Shows current edge count
   - ✅ Shows network density %
   - ✅ Shows clustering coefficient %
   - ✅ Top 10 most connected nodes listed

2. Click a node from top 10 list
   - ✅ Node gets selected
   - ✅ Graph centers on node
   - ✅ Details panel replaces statistics

3. Close details panel (X button)
   - ✅ Statistics panel returns

### Color Legend ✅

1. Verify color legend accuracy
   - ✅ Red nodes = In Black Book
   - ✅ Orange nodes = Billionaires
   - ✅ Blue nodes = 10+ flights
   - ✅ Purple nodes = Politicians
   - ✅ Gray nodes = Default

2. Find examples of each color
   - Search "Trump" → Should be orange (billionaire)
   - Search "Clinton" → Should be purple (politician)
   - Filter by "In Black Book" → All red nodes

### UI Panel Toggles ✅

1. Click Filter toggle button (top-right)
   - ✅ Filter panel hides
   - ✅ Graph expands to fill space
   - ✅ Button stays active

2. Click Filter toggle again
   - ✅ Filter panel reappears
   - ✅ Graph resizes smoothly

3. Click Statistics toggle button
   - ✅ Statistics/details panel hides
   - ✅ Graph expands
   - ✅ Works same as filter toggle

4. Hide both panels
   - ✅ Graph uses full width
   - ✅ Maximum visualization space

## Performance Tests

### Load Performance
1. Open browser DevTools → Performance tab
2. Reload page and record
3. Check metrics:
   - ✅ First render: < 1 second
   - ✅ Full load: < 3 seconds
   - ✅ No frame drops during simulation

### Filter Performance
1. Open DevTools → Performance
2. Type in search box while recording
3. Check metrics:
   - ✅ Filter updates: < 100ms
   - ✅ Maintains 60fps
   - ✅ No blocking operations

### Zoom Performance
1. Record while zooming in/out rapidly
2. Check metrics:
   - ✅ Maintains 60fps
   - ✅ Smooth animations
   - ✅ No lag or stuttering

### Memory Usage
1. Open DevTools → Memory tab
2. Take heap snapshot
3. Check memory:
   - ✅ Initial heap: ~100-200MB
   - ✅ After interactions: < 300MB
   - ✅ No significant leaks after 5 minutes

## Edge Cases

### Empty Results
1. Search for "NONEXISTENTNAME123"
   - ✅ Graph shows no nodes
   - ✅ No errors in console
   - ✅ Statistics show 0 nodes, 0 edges
   - ✅ Clear message or empty state

### Single Node
1. Use very restrictive filters to get 1 node
   - ✅ Single node displays centered
   - ✅ No edges shown
   - ✅ Statistics accurate
   - ✅ No crashes

### Maximum Filters
1. Apply ALL category filters
   - ✅ Shows union of all categories
   - ✅ Equivalent to showing all nodes

### Rapid Interactions
1. Click nodes rapidly (10+ clicks/second)
   - ✅ No crashes
   - ✅ Details panel updates correctly
   - ✅ No visual glitches

2. Type and delete search rapidly
   - ✅ Graph updates smoothly
   - ✅ No race conditions
   - ✅ Final state correct

## Browser Compatibility

Test in multiple browsers:

### Chrome (Primary)
- ✅ All features work
- ✅ Best performance
- ✅ No visual issues

### Firefox
- ✅ All features work
- ✅ Slightly lower FPS acceptable
- ✅ Same visual appearance

### Safari
- ✅ All features work
- ✅ May have different physics behavior
- ✅ Color rendering consistent

## Mobile Testing (Future)

Current implementation NOT optimized for mobile:
- ⚠️ Three-column layout may not fit
- ⚠️ Touch gestures need implementation
- ⚠️ Performance may be slower

## Error Testing

### API Errors
1. Stop backend server
2. Reload page
   - ✅ Shows error message
   - ✅ Offers "Retry" button
   - ✅ No console errors

3. Click "Retry"
   - ✅ Attempts to reload
   - ✅ Shows loading state

4. Restart backend
5. Click "Retry"
   - ✅ Loads successfully

### Network Timeout
1. Throttle network in DevTools
2. Reload page
   - ✅ Loading state shows
   - ✅ Eventually loads or shows error
   - ✅ No infinite loading

## Console Errors Check

Throughout ALL tests:
- ✅ No errors in browser console
- ✅ No warnings about performance
- ✅ No React warnings
- ✅ API calls return successfully (200 OK)

## Accessibility Tests

### Keyboard Navigation
1. Tab through controls
   - ✅ Focus visible on buttons
   - ✅ Can activate with Enter/Space
   - ⚠️ Graph interaction keyboard-only limited

### Screen Reader
1. Test with VoiceOver/NVDA
   - ✅ Buttons have labels
   - ✅ Panels have headings
   - ⚠️ Graph nodes not fully accessible (visual component)

### Color Contrast
1. Check all text
   - ✅ Labels readable
   - ✅ Sufficient contrast ratios
   - ✅ Works in both light/dark mode (if applicable)

## Success Criteria Summary

All checkboxes (✅) must be verified:
- [ ] Graph loads and renders correctly
- [ ] All controls functional
- [ ] Filters work in real-time
- [ ] Statistics accurate
- [ ] No performance issues
- [ ] No console errors
- [ ] Cross-browser compatible
- [ ] Accessible UI controls

## Known Issues

Document any issues found during testing:

1. **Issue**: [Description]
   - **Severity**: High/Medium/Low
   - **Workaround**: [If any]
   - **Fix**: [Planned or completed]

## Testing Sign-Off

- **Tester**: _____________
- **Date**: _____________
- **Browser**: _____________
- **OS**: _____________
- **Result**: PASS / FAIL
- **Notes**: _____________
