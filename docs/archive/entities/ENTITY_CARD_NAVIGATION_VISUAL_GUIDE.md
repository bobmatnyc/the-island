# Entity Card Navigation - Visual Testing Guide

## What Changed: Before vs. After

### BEFORE (Old Popup System)
```
Entity Card:
┌─────────────────────────────────┐
│ Jeffrey Epstein                 │
│ ───────────────────────────────│
│ Bio text here...                │
│                                 │
│ [View Flights]                  │  ← Opens popup modal
│ [View Documents]                │  ← Opens popup modal
│ [View Network]                  │  ← Opens popup modal
└─────────────────────────────────┘
```

### AFTER (New Direct Navigation)
```
Entity Card:
┌─────────────────────────────────┐
│ Jeffrey Epstein                 │
│ ───────────────────────────────│
│ Bio text here...                │
│                                 │
│ [✈️ Flights     42]             │  ← Direct navigation
│ [📄 Docs       156]             │  ← Direct navigation
│ [🔗 Network     8]              │  ← Direct navigation
│ [📅 Timeline   12]              │  ← NEW! Direct navigation
└─────────────────────────────────┘
```

## Visual Appearance

### Active Button (Enabled)
```
┌──────────────────────┐
│ ✈️ Flights      42   │  ← Blue background (#3b82f6)
└──────────────────────┘  ← White text, count badge visible
   ↑ Hover: Lifts up with shadow
```

### Disabled Button (0 Count)
```
┌──────────────────────┐
│ ✈️ Flights       0   │  ← Gray background (--border-color)
└──────────────────────┘  ← Dimmed (40% opacity), no hover effect
   ↑ Not clickable
```

### Button Components
```
┌────────────────────────────┐
│ [Icon] Label     [Badge]  │
│   ↑       ↑          ↑     │
│ Lucide  Text    Count     │
└────────────────────────────┘
```

## User Interaction Flow

### 1. Click "Flights" Button
```
Step 1: User clicks button
   │
   ├─→ Modal closes immediately
   │
   ├─→ Page switches to "Flights" tab
   │       (Tab becomes active)
   │
   ├─→ Filter applies automatically
   │       (Shows only flights with this entity)
   │
   ├─→ URL updates
   │       http://localhost:8000/#flights?entity=Epstein,%20Jeffrey
   │
   └─→ Toast appears
           "Showing flights for Epstein, Jeffrey"
```

### 2. Share Deep Link
```
User copies URL:
   http://localhost:8000/#documents?entity=Trump,%20Donald

Other user opens link:
   │
   ├─→ Page loads normally
   │
   ├─→ handleHashNavigation() detects hash
   │
   ├─→ Switches to "Documents" tab
   │
   ├─→ Applies filter for "Trump, Donald"
   │
   └─→ Shows only relevant documents
```

## Button Behavior Matrix

| Button    | Entity Has Data | State    | Click Result                          |
|-----------|----------------|----------|---------------------------------------|
| Flights   | Yes (42)       | Enabled  | → Flights tab, filter applied         |
| Flights   | No (0)         | Disabled | No action                             |
| Docs      | Yes (156)      | Enabled  | → Documents tab, filter applied       |
| Docs      | No (0)         | Disabled | No action                             |
| Network   | Any count      | Enabled  | → Network tab, entity highlighted     |
| Timeline  | Yes (12)       | Enabled  | → Timeline tab, filter applied        |
| Timeline  | No (0)         | Disabled | No action                             |

## CSS Styling Details

### Normal State
- Background: `var(--accent-blue)` (#3b82f6)
- Text: White
- Badge: White with 25% opacity background
- Font: 13px, weight 600
- Padding: 10px 16px
- Border radius: 6px

### Hover State (Enabled Only)
- Background: `var(--accent-blue-hover)` (darker blue)
- Transform: `translateY(-1px)` (lifts up 1px)
- Shadow: `0 4px 12px rgba(0, 0, 0, 0.2)`
- Cursor: Pointer

### Disabled State
- Background: `var(--border-color)` (gray)
- Opacity: 0.4
- Cursor: Not-allowed
- No hover effects
- Badge: Black with 10% opacity background

### Badge Styling
- Min width: 20px
- Height: 20px
- Padding: 0 6px
- Border radius: 10px (pill shape)
- Font: 11px, weight 700
- Center aligned (flex)

## Testing Scenarios

### Scenario 1: Entity with All Data
**Entity**: Jeffrey Epstein
**Expected Counts**:
- Flights: > 0 (enabled)
- Docs: > 0 (enabled)
- Network: > 0 (enabled)
- Timeline: > 0 (enabled)

**Test**:
1. Open entity card
2. All 4 buttons should be blue
3. All badges show non-zero counts
4. Hover over each → lift animation
5. Click each → navigates correctly

### Scenario 2: Entity with Partial Data
**Entity**: Someone with only documents
**Expected Counts**:
- Flights: 0 (disabled)
- Docs: > 0 (enabled)
- Network: 0 or > 0
- Timeline: 0 (disabled)

**Test**:
1. Open entity card
2. Disabled buttons are gray and dim
3. Enabled buttons are blue
4. Click disabled → no action
5. Click enabled → navigates correctly

### Scenario 3: Deep Link Navigation
**URL**: `#flights?entity=Epstein,%20Jeffrey`

**Test**:
1. Open URL in new tab
2. Page loads
3. Automatically switches to Flights tab
4. Filter shows "Epstein, Jeffrey"
5. Only relevant flights displayed
6. URL hash remains in address bar

### Scenario 4: Network Button (Always Enabled)
**Note**: Network button is always enabled (even with 0 connections)

**Test**:
1. Find entity with 0 connections
2. Network button should still be blue
3. Badge shows "0"
4. Click → navigates to Network tab
5. Shows entity node in isolation

## Browser Console Verification

Open DevTools Console (F12) and check:

### ✅ Good Indicators:
```
Filtering flights by entity: Epstein, Jeffrey
Switching to tab: flights
Applied filters to flights
URL hash updated: #flights?entity=Epstein%2C%20Jeffrey
```

### ❌ Bad Indicators (Should Not Appear):
```
Uncaught TypeError: ...
ReferenceError: filterTimelineByEntity is not defined
Cannot read property 'value' of null
```

## Visual Regression Checklist

Compare before/after screenshots:

- [ ] Button layout: 4 buttons in a row (wraps on mobile)
- [ ] Button icons: Plane, File, Share, Calendar
- [ ] Button labels: "Flights", "Docs", "Network", "Timeline"
- [ ] Badge position: Right side of each button
- [ ] Badge color: White/transparent on enabled, gray on disabled
- [ ] Spacing: 8px gap between buttons
- [ ] Min width: 140px per button
- [ ] Hover effect: Buttons lift on hover (enabled only)
- [ ] Disabled styling: Opacity 40%, gray background

## Mobile Responsiveness

On screens < 600px:

```
Desktop (Wide):
[Flights 42] [Docs 156] [Network 8] [Timeline 12]

Mobile (Narrow):
[Flights 42] [Docs 156]
[Network 8]  [Timeline 12]
```

Buttons wrap to 2 columns on narrow screens due to `flex-wrap: wrap`.

## Accessibility Testing

### Keyboard Navigation:
1. Tab to entity card
2. Tab through buttons
3. Space/Enter activates button
4. Disabled buttons skip in tab order (native browser behavior)

### Screen Reader:
- Button text announces: "Flights, 42"
- Disabled state announces: "Flights, 0, dimmed button"
- Icon is decorative (aria-hidden by Lucide)

## Performance Expectations

### Tab Switching:
- **Target**: < 100ms to switch tab
- **Actual**: ~50ms (setTimeout delay)

### Filter Application:
- **Target**: < 500ms to apply filter
- **Actual**: Varies by dataset size

### URL Hash Update:
- **Target**: Instant (< 10ms)
- **Actual**: Synchronous operation

## Common Issues and Solutions

### Issue: Buttons Don't Show Counts
**Symptom**: All badges show "0"
**Cause**: Entity data not loaded before modal opens
**Solution**: Ensure `loadEntitiesList()` completes before opening cards

### Issue: Deep Links Don't Work
**Symptom**: Page loads but doesn't navigate to tab
**Cause**: `handleHashNavigation()` not called
**Solution**: Verify DOMContentLoaded listener is active

### Issue: Timeline Button Always Disabled
**Symptom**: Timeline badge always shows "0"
**Cause**: `timelineData` not defined when modal opens
**Solution**: Load timeline data on page init

### Issue: Icons Don't Render
**Symptom**: Boxes instead of icons
**Cause**: Lucide icons not initialized after modal insert
**Solution**: `lucide.createIcons()` called at line 366

## Success Metrics

After implementation, you should see:

✅ **No popups** - All navigation is direct
✅ **4 buttons** - Including new Timeline button
✅ **Accurate counts** - Badges match actual data
✅ **Working deep links** - URLs are shareable
✅ **Smooth navigation** - No lag or jank
✅ **Clear disabled state** - Gray and dim when 0 count
✅ **Toast feedback** - Confirmation message appears
✅ **No console errors** - Clean JavaScript execution

## Final Visual Reference

```
┌─────────────────────────────────────────────────────┐
│                  Jeffrey Epstein                     │
│  [Government] [Finance] [Intelligence]              │
│  Bio: American financier and convicted sex...       │
│  ─────────────────────────────────────────────────  │
│  Connections: 127  Documents: 1,256  Flights: 587  │
│  ─────────────────────────────────────────────────  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐│
│  │✈️ Flights │ │📄 Docs   │ │🔗 Network│ │📅Timeline││
│  │    587   │ │  1,256   │ │   127    │ │    42   ││
│  └──────────┘ └──────────┘ └──────────┘ └─────────┘│
└─────────────────────────────────────────────────────┘
     ↑ Blue       ↑ Blue      ↑ Blue       ↑ Blue
   (Enabled)   (Enabled)   (Enabled)    (Enabled)
```

vs. entity with limited data:

```
┌─────────────────────────────────────────────────────┐
│                    John Smith                        │
│  [Unknown]                                           │
│  Bio: No biographical information available.        │
│  ─────────────────────────────────────────────────  │
│  Connections: 0    Documents: 12    Flights: 0     │
│  ─────────────────────────────────────────────────  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐│
│  │✈️ Flights │ │📄 Docs   │ │🔗 Network│ │📅Timeline││
│  │     0    │ │    12    │ │    0     │ │    0    ││
│  └──────────┘ └──────────┘ └──────────┘ └─────────┘│
└─────────────────────────────────────────────────────┘
     ↑ Gray       ↑ Blue       ↑ Blue       ↑ Gray
  (Disabled)  (Enabled)    (Enabled)    (Disabled)
```
