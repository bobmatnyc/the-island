# Timeline Navigation Visual Guide

## Button Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLIGHT TIMELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Sep 2002 • 156 routes, 423 flights                          │
│                                                                 │
│   ═══════════════════════════════════════════════════════      │
│   Jan'98        Jan'00        Jan'02        Sep'02 ●           │
│                                                                 │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│   │← Previous│  │📅 Latest │  │  Next →  │                   │
│   └──────────┘  └──────────┘  └──────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Button States

### State 1: At Last Month (Sep 2002) - Default

```
Month: Sep 2002 • 156 routes, 423 flights

Slider Position: ═══════════════════════════●  (far right)

Buttons:
┌──────────┐  ┌──────────┐  ┌──────────┐
│← Previous│  │📅 Latest │  │  Next →  │  ← Disabled (greyed)
│ ENABLED  │  │ ENABLED  │  │ DISABLED │
│opacity:1 │  │opacity:1 │  │opacity:0.5│
└──────────┘  └──────────┘  └──────────┘
   ↑                            ↑
   Can click               Cannot click
   Pointer cursor          Not-allowed cursor
```

**Why**: At the last month (Sep 2002), can't go forward anymore.

---

### State 2: At First Month (Jan 1998)

```
Month: Jan 1998 • 34 routes, 87 flights

Slider Position: ●═══════════════════════════  (far left)

Buttons:
┌──────────┐  ┌──────────┐  ┌──────────┐
│← Previous│  │📅 Latest │  │  Next →  │
│ DISABLED │  │ ENABLED  │  │ ENABLED  │  ← Can click
│opacity:0.5│  │opacity:1 │  │opacity:1 │
└──────────┘  └──────────┘  └──────────┘
   ↑                            ↑
Cannot click                 Can click
Not-allowed cursor          Pointer cursor
```

**Why**: At the first month (Jan 1998), can't go backward anymore.

---

### State 3: At Middle Month (e.g., Jan 2000)

```
Month: Jan 2000 • 89 routes, 234 flights

Slider Position: ════════●══════════════════  (middle)

Buttons:
┌──────────┐  ┌──────────┐  ┌──────────┐
│← Previous│  │📅 Latest │  │  Next →  │
│ ENABLED  │  │ ENABLED  │  │ ENABLED  │
│opacity:1 │  │opacity:1 │  │opacity:1 │
└──────────┘  └──────────┘  └──────────┘
   ↑              ↑              ↑
All buttons clickable and fully visible
```

**Why**: In the middle of the timeline, all navigation is available.

---

## User Interactions

### Clicking Previous (Enabled)

```
BEFORE:                         AFTER:
Sep 2002                        Aug 2002
══════════════════════●   →     ═════════════════════●

Click [← Previous]

Result:
✓ Slider moves left one step
✓ Month changes to Aug 2002
✓ Flight count updates
✓ Map shows Aug 2002 flights
✓ Next button becomes enabled
✓ Console: [Timeline Nav] Moving to index 47 (Aug 2002)
```

---

### Clicking Next (Enabled)

```
BEFORE:                         AFTER:
Jan 1998                        Feb 1998
●══════════════════════   →     ══●═════════════════════

Click [Next →]

Result:
✓ Slider moves right one step
✓ Month changes to Feb 1998
✓ Flight count updates
✓ Map shows Feb 1998 flights
✓ Previous button becomes enabled
✓ Console: [Timeline Nav] Moving to index 1 (Feb 1998)
```

---

### Clicking Latest (From Middle Month)

```
BEFORE:                         AFTER:
Jan 2000                        Sep 2002
════════●═══════════     →      ══════════════════════●

Click [📅 Latest]

Result:
✓ Slider jumps to far right
✓ Month changes to Sep 2002
✓ Flight count updates
✓ Map shows Sep 2002 flights
✓ Next button becomes disabled
✓ Previous button becomes enabled
✓ Toast: "Jumped to Sep 2002" (green)
✓ Console: [Timeline Nav] Jumping to latest month (index 48: Sep 2002)
```

---

### Clicking Disabled Button

```
At Sep 2002 (last month):
══════════════════════●

Click [Next →] (disabled)

Visual:
- Cursor changes to "not-allowed" (🚫)
- Button opacity is 0.5 (greyed out)
- Button has disabled attribute

Result:
✓ No slider movement
✓ No map update
✓ Toast: "Already at last month" (blue info)
✓ Console: [Timeline Nav] Already at last month
```

---

## CSS Styling

### Enabled Button
```css
.timeline-nav-btn:enabled {
    opacity: 1;
    cursor: pointer;
    /* User can click */
}
```

**Visual**: Full color, normal cursor (pointer/hand)

---

### Disabled Button
```css
.timeline-nav-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    /* User cannot click */
}
```

**Visual**: Greyed out (50% opacity), blocked cursor (🚫)

---

## Toast Notifications

### Success Toast (Green)
```
┌────────────────────────────┐
│ ✓ Jumped to Sep 2002       │  ← Green background
└────────────────────────────┘
```
**When**: Clicked Latest and jumped to new month

---

### Info Toast (Blue)
```
┌────────────────────────────┐
│ ℹ Already at first month   │  ← Blue background
└────────────────────────────┘
```
**When**: Clicked Previous at Jan 1998, or Next at Sep 2002

---

### Error Toast (Red)
```
┌────────────────────────────┐
│ ✗ Timeline not ready       │  ← Red background
└────────────────────────────┘
```
**When**: Clicked button before timeline initialized (rare)

---

## Console Output Examples

### Normal Navigation
```
[Timeline Nav] Previous button clicked
[Timeline Nav] Current index: 48
[Timeline Nav] Moving to index 47 (Aug 2002)
```

### Boundary Condition
```
[Timeline Nav] Next button clicked
[Timeline Nav] Current index: 48, Max: 48
[Timeline Nav] Already at last month
```

### Latest Jump
```
[Timeline Nav] Latest button clicked
[Timeline Nav] Jumping to latest month (index 48: Sep 2002)
```

### Error Condition
```
[Timeline Nav] Previous button clicked
Timeline not initialized
```

---

## Animation Flow

### Previous/Next Click Animation

```
1. User clicks button
   ↓
2. Console log appears
   ↓
3. Slider handle moves smoothly (CSS transition)
   ↓
4. Month label updates
   ↓
5. Flight count updates
   ↓
6. Map routes fade out
   ↓
7. New routes fade in
   ↓
8. Button states update
   ↓
9. Complete (total ~300-500ms)
```

### Latest Button Animation

```
1. User clicks Latest
   ↓
2. Console log appears
   ↓
3. Slider jumps to end (no smooth transition for big jumps)
   ↓
4. Month label updates
   ↓
5. Flight count updates
   ↓
6. Map routes clear
   ↓
7. New routes appear
   ↓
8. Toast notification appears
   ↓
9. Button states update
   ↓
10. Complete (~500-700ms)
```

---

## Responsive Behavior

### Desktop (>768px)
```
┌──────────┐  ┌──────────┐  ┌──────────┐
│← Previous│  │📅 Latest │  │  Next →  │
└──────────┘  └──────────┘  └──────────┘
     Horizontal layout, centered
```

### Mobile (<768px)
```
May stack vertically or stay horizontal with smaller buttons
```

---

## Accessibility

### Keyboard Navigation
- **Tab**: Navigate to Previous → Latest → Next
- **Enter/Space**: Activate focused button
- **Arrow Keys**: Move slider directly (native noUiSlider behavior)

### Screen Reader Announcements
- Button titles: "Previous Month", "Jump to Latest", "Next Month"
- Disabled state announced: "Previous Month, button, dimmed"
- Toast messages read aloud when appearing

### Focus Indicators
```
┌──────────┐
│← Previous│  ← Blue outline when focused
└──────────┘
```

---

## Edge Cases

### Timeline Not Initialized
```
Buttons: All appear normal (no visual change)
Click: Toast "Timeline not ready"
Console: Error message
```

### No Flight Data
```
Timeline: Not shown at all
Buttons: Not rendered
```

### Single Month Data
```
Timeline: Slider shows single point
Previous: Disabled
Next: Disabled
Latest: Enabled but does nothing
```

---

## Color Scheme

### Enabled State
- **Background**: Primary button color (likely blue/purple)
- **Text**: White
- **Opacity**: 1.0
- **Cursor**: pointer

### Disabled State
- **Background**: Same as enabled (but with opacity)
- **Text**: Same as enabled (but dimmed by opacity)
- **Opacity**: 0.5
- **Cursor**: not-allowed

### Hover State (Enabled Only)
- **Background**: Slightly darker shade
- **Opacity**: 1.0
- **Transition**: Smooth color change

---

**Cache Version**: `app.js?v=20251118_timeline_nav_fix`
**Last Updated**: 2025-11-18
