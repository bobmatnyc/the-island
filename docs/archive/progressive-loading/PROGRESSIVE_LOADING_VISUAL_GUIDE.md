# Progressive Network Loading - Visual Guide

## UI Component Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Network Controls Panel (Top-Right)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Search Nodes]                                             │
│  ┌─────────────────────────────────┐                        │
│  │ Search entities...              │                        │
│  └─────────────────────────────────┘                        │
│                                                             │
│  Filters:                                                   │
│  ☐ Billionaires only                                        │
│  ☐ High connections (>10)                                   │
│  ☐ Medium (5-10)                                            │
│  ☐ Low connections (<5)                                     │
│                                                             │
│  Showing: 387 of 387 nodes                                  │
│                                                             │
│  ───────────────────────────────────────────────────────── │
│                                                             │
│  ★ Connection Loading ★                    [NEW FEATURE]   │
│                                                             │
│  Showing 300 of 1,584 connections                           │
│         ─────         ─────                                 │
│         │300│   of   │1584│                                 │
│         ─────         ─────                                 │
│         (blue)      (gray)                                  │
│                                                             │
│  ├────●────────────────────────────────────────┤            │
│  100         500         1000        1584                   │
│            (slider thumb)                                   │
│                                                             │
│  ┌───────────────────────────────────────┐                  │
│  │      Load More (+100)                 │  [Blue/Active]  │
│  └───────────────────────────────────────┘                  │
│                                                             │
│  ┌───────────────────────────────────────┐                  │
│  │        Show All                       │  [Amber/Warn]   │
│  └───────────────────────────────────────┘                  │
│                                                             │
│  ┌───────────────────────────────────────┐                  │
│  │     Reset to Default                  │  [Gray]         │
│  └───────────────────────────────────────┘                  │
│                                                             │
│  ───────────────────────────────────────────────────────── │
│                                                             │
│  Link Distance: 50                                          │
│  ├────●────────────────────────────────────┤                │
│                                                             │
│  Charge Strength: -300                                      │
│  ├────●────────────────────────────────────┤                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Connection Count Display
```
┌─────────────────────────────────────────┐
│ Showing 300 of 1,584 connections        │
│         ─────                           │
│         │300│  ← Current (blue, bold)   │
│         ─────                           │
│           of                            │
│         ─────                           │
│        │1584│  ← Total (gray)           │
│         ─────                           │
└─────────────────────────────────────────┘
```

**States**:
- Default: 300 of 1,584
- After Load More: 400 of 1,584 (then 500, 600, etc.)
- Maximum: 1,584 of 1,584

### 2. Range Slider
```
Min                                    Max
100                                   1584
├────●────────────────────────────────┤
     │
     └─ Thumb (16px blue circle)
        - Drag to adjust
        - Step size: 100
        - Hover: Scale to 1.1x
```

**Interaction**:
- **Drag**: Move thumb to set connection count
- **Click Track**: Jump to clicked position
- **Arrow Keys**: Adjust when focused
- **Debounce**: Updates network after 200ms

### 3. Load More Button
```
┌───────────────────────────────────────┐
│      Load More (+100)                 │  ← Active State
└───────────────────────────────────────┘
     │
     └─ Background: Accent Blue (#58a6ff)
        Text: White
        Hover: Darker blue + lift effect

┌───────────────────────────────────────┐
│        All Loaded                     │  ← Disabled State
└───────────────────────────────────────┘
     │
     └─ Background: Gray (50% opacity)
        Text: Gray
        Cursor: not-allowed
```

**Behavior**:
- Click: Add 100 connections to current count
- Disabled when: count >= 1,584
- Text changes: "Load More (+100)" → "All Loaded"

### 4. Show All Button
```
┌───────────────────────────────────────┐
│        Show All                       │  ← Warning Style
└───────────────────────────────────────┘
     │
     └─ Border: Amber (#bf8700)
        Text: Amber
        Hover: Amber background + white text
        Tooltip: "May impact performance"

Clicking triggers:
┌─────────────────────────────────────────┐
│  Warning: Loading all 1,584 connections │
│  may impact performance.                │
│                                         │
│  Continue?                              │
│                                         │
│  [ Cancel ]  [ OK ]                     │
└─────────────────────────────────────────┘
```

### 5. Reset Button
```
┌───────────────────────────────────────┐
│     Reset to Default                  │  ← Active State
└───────────────────────────────────────┘
     │
     └─ Background: Tertiary gray
        Text: Primary text color
        Hover: Blue background + white text

┌───────────────────────────────────────┐
│     Reset to Default                  │  ← Disabled State
└───────────────────────────────────────┘
     │
     └─ Already at 300 connections
        Opacity: 50%
        Cursor: not-allowed
```

### 6. Loading Indicator
```
Hidden by default:
(invisible)

Active during updates:
┌─────────────────────────────────────┐
│     Updating network...             │
└─────────────────────────────────────┘
     │
     └─ Font: 10px italic
        Color: Secondary text
        Display: 500ms
        Fade in/out: smooth
```

## State Transitions

### State 1: Initial Load (Default)
```
Count: 300 of 1,584
Slider: Position at 300
Buttons:
  - Load More: ENABLED
  - Show All: ENABLED
  - Reset: DISABLED (already at default)
```

### State 2: After Load More (e.g., 500)
```
Count: 500 of 1,584
Slider: Position at 500
Buttons:
  - Load More: ENABLED
  - Show All: ENABLED
  - Reset: ENABLED
```

### State 3: Maximum Loaded (1,584)
```
Count: 1,584 of 1,584
Slider: Position at 1,584
Buttons:
  - Load More: DISABLED (text: "All Loaded")
  - Show All: DISABLED
  - Reset: ENABLED
```

### State 4: Custom Slider Position (e.g., 750)
```
Count: 750 of 1,584
Slider: Position at 750
Buttons:
  - Load More: ENABLED
  - Show All: ENABLED
  - Reset: ENABLED
```

## Visual Effects

### Edge Transitions
```
Adding edges (fade in):
  Opacity: 0 → 0.6
  Duration: 300ms
  Easing: ease-in-out

Removing edges (fade out):
  Opacity: 0.6 → 0
  Duration: 300ms
  Then: remove from DOM
```

### Button Hover Effects
```
Default → Hover:
  Background: tertiary → accent-blue
  Color: primary → white
  Transform: translateY(0) → translateY(-1px)
  Duration: 200ms

Hover → Active (click):
  Transform: translateY(-1px) → translateY(0)
  Duration: 100ms
```

### Slider Thumb Animations
```
Default → Hover:
  Background: accent-blue → accent-blue-hover
  Transform: scale(1) → scale(1.1)
  Duration: 200ms

While dragging:
  Cursor: grabbing
  Transform: scale(1.1) maintained
```

## Color Scheme (Dark Theme)

```
Primary Background:   #0d1117 (very dark gray)
Secondary Background: #161b22 (dark gray)
Tertiary Background:  #1c2128 (medium dark gray)
Border Color:         #30363d (light gray)
Text Primary:         #c9d1d9 (light gray)
Text Secondary:       #8b949e (medium gray)
Accent Blue:          #58a6ff (bright blue)
Accent Blue Hover:    #1f6feb (darker blue)
Warning Amber:        #bf8700 (gold/amber)
```

## Spacing & Sizing

```
Control Panel:
  Width: ~280px
  Padding: 16px
  Gap between elements: 12px

Connection Loading Section:
  Margin top: 8px
  Internal spacing: 8px between elements

Slider:
  Height: 6px (track)
  Thumb: 16px × 16px
  Margin: 8px 0

Buttons:
  Height: ~36px (with padding)
  Padding: 8px 12px
  Font size: 11px
  Gap between buttons: 6px
```

## Responsive Behavior

### Desktop (> 1024px)
```
Full panel visible
All controls on single column
Comfortable spacing
```

### Tablet (768px - 1024px)
```
Panel slightly narrower
Controls remain vertical
Touch-friendly button sizes
```

### Mobile (< 768px)
```
Panel may overlay network
Larger touch targets
Buttons full width
Slider easier to grab
```

## Accessibility Features

### Keyboard Navigation
```
Tab order:
1. Slider
2. Load More button
3. Show All button
4. Reset button

Keyboard shortcuts:
- Slider: ←/→ arrows to adjust
- Buttons: Enter or Space to activate
- Tab: Move to next control
- Shift+Tab: Move to previous
```

### Screen Reader Announcements
```
Slider:
"Number of connections to display, 300 of 1584, slider"

On change:
"Showing 400 of 1584 connections"

Load More button:
"Load More, add 100 connections, button"

When disabled:
"All Loaded, button, disabled"

Show All button:
"Show all connections, may impact performance, button"

Reset button:
"Reset to default 300 connections, button"
```

### Focus Indicators
```
Focused element:
  Outline: 2px solid accent-blue
  Offset: 2px
  Border radius: matches element
  Visible: always (not removed)
```

## Performance Indicators

### Loading States
```
Idle (not updating):
  Loading indicator: hidden
  Buttons: normal cursor
  Network: interactive

Updating (after slider/button):
  Loading indicator: visible "Updating network..."
  Duration: ~200-500ms
  Buttons: remain clickable
  Network: continues rendering

Completed:
  Loading indicator: fade out
  Buttons: updated states
  Network: stabilized
```

### Visual Feedback Timing
```
Slider drag → Count display: 0ms (immediate)
Slider release → Network update: 200ms (debounced)
Network update → Edges appear: 300ms (transition)
Update complete → Loading hide: 500ms total
```

## Error States

### Network Load Failure
```
If window.networkEdges undefined:
  Controls: grayed out
  Message: "Network data not available"
  Console: warning logged
```

### Invalid State
```
If slider goes out of bounds:
  Automatically clamped to 100-1584
  No error shown to user
  Continues functioning
```

## User Flow Diagram

```
                    ┌─────────────┐
                    │ Page Loads  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Network    │
                    │  Renders    │
                    │  300 edges  │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
         ┌────▼────┐              ┌─────▼─────┐
         │  Slider │              │  Buttons  │
         │   Drag  │              │   Click   │
         └────┬────┘              └─────┬─────┘
              │                         │
              └────────────┬────────────┘
                           │
                    ┌──────▼──────┐
                    │  Update     │
                    │  Edges      │
                    │  (200ms)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  D3 Re-     │
                    │  renders    │
                    │  (300ms)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Simulation  │
                    │ Stabilizes  │
                    └─────────────┘
```

---

**Visual Guide Version**: 1.0.0
**Last Updated**: November 17, 2025
**Purpose**: Quick visual reference for progressive loading UI
