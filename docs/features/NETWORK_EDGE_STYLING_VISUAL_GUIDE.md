# Network Edge Styling - Visual Guide

## Visual Layout Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Network Graph Viewport                       │
│                                                                   │
│   ○────────●═══════●                                             │
│    \      /     thin│  ∙ Nodes: Variable size based on         │
│     \    / medium   │    connection count                       │
│      \  /           │  ∙ Edges: Thickness varies (1.5px-8px)   │
│   ●━━━○             │  ∙ Colors: Blue (default flight)         │
│       ║ very bold   │            Purple (business)              │
│       ║             │            Red (family)                   │
│   ●━━━●             │            Gold (legal)                   │
│     bold            │            Green (employment)             │
│                                                                  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ Legend (Bottom Left Corner)                         │        │
│  │                                                      │        │
│  │  Connection Strength:                               │        │
│  │  ━━━━━━ Very Bold (21+)                             │        │
│  │  ━━━━━ Bold (11-20)                                 │        │
│  │  ━━━━ Medium (6-10)                                 │        │
│  │  ━━━ Light (3-5)                                    │        │
│  │  ━━ Thin (1-2)                                      │        │
│  │                                                      │        │
│  │  Relationship Types: (Click to filter)              │        │
│  │  ━━━━ Flew Together                  [Blue]         │        │
│  │  ━━━━ Business Partner              [Purple]        │        │
│  │  ━━━━ Family Member                 [Red]           │        │
│  │  ━━━━ Legal/Attorney                [Gold]          │        │
│  │  ━━━━ Employment                    [Green]         │        │
│  │                                                      │        │
│  │  Click colors to filter connections                 │        │
│  └─────────────────────────────────────────────────────┘        │
└───────────────────────────────────────────────────────────────────┘
```

## Edge Hover Tooltip

```
┌────────────────────────────────────┐
│  5 connections (Light)             │  ← Count + Tier
│                                    │
│  ━━━ Business Partner              │  ← Type with color
│                                    │
│  Between:                          │
│  John Doe ↔ Jane Smith            │  ← Entities
│                                    │
│  Source: Flight Logs, Documents    │  ← Context
│                                    │
│  Click for details                 │  ← Action hint
└────────────────────────────────────┘
```

## Connection Details Panel (Right Side)

```
┌──────────────────────────────────────┐
│  Connection Details              × │  ← Header
│  John Doe ↔ Jane Smith              │
├──────────────────────────────────────┤
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Business Partnership          │ │  ← Type badge (colored)
│  └────────────────────────────────┘ │
│                                      │
│          5                           │  ← Large count
│    Total connections                │
│                                      │
│  Data Sources                        │
│  ┌────────────────────────────────┐ │
│  │ Flight Logs                    │ │
│  │ Appeared together on flights   │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │ Documents                      │ │
│  │ Co-mentioned in analysis       │ │
│  └────────────────────────────────┘ │
│                                      │
│  Note: Co-occurrences represent...  │
│                                      │
│  [View John Doe] [View Jane Smith]  │  ← Actions
│                                      │
└──────────────────────────────────────┘
```

## Edge Thickness Examples (Actual Pixel Widths)

```
Thin (1-2 connections):
────────────────────────────────  1.5px stroke

Light (3-5 connections):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  3px stroke

Medium (6-10 connections):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  5px stroke

Bold (11-20 connections):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  6.5px stroke

Very Bold (21+ connections):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  8px stroke
```

## Color Coding Examples

### Flight Connection (Blue #0969da)
```
John Doe ━━━━━━━━ Jane Smith
         (Blue, 3px - 5 flights)
```

### Business Relationship (Purple #8250df)
```
Company A ━━━━━━━━ Company B
          (Purple, 6.5px - 15 partnerships)
```

### Family Relationship (Red #cf222e)
```
Parent ━━━━━━━━ Child
       (Red, 1.5px - 1 relationship)
```

### Legal Connection (Gold #bf8700)
```
Client ━━━━━━━━ Attorney
       (Gold, 5px - 8 cases)
```

### Employment Relationship (Green #1a7f37)
```
Employee ━━━━━━━━ Employer
         (Green, 3px - 4 positions)
```

## Interactive States

### Default State
- All edges visible at 60% opacity
- Colors match relationship type
- Thickness matches connection count
- Legend shows all options

### Hover State
- Hovered edge: 100% opacity
- Hovered edge: 30% thicker
- Tooltip appears near cursor
- 200ms smooth transition

### Filtered State (After Clicking Legend Color)
```
Example: Clicked "Business Partner" (Purple)

┌─────────────────────────────────────┐
│                                     │
│  ○      ●                           │  ← Only purple edges visible
│   \    /                            │  ← Other edges 10% opacity/hidden
│    ○━━━●  (Purple business edge)    │
│                                     │
│  Legend:                            │
│  ━━━━ Flew Together        [Faded] │  ← Inactive (30% opacity)
│  ━━━━ Business Partner  [Bright]   │  ← Active (100% opacity)
│  ━━━━ Family Member        [Faded] │
│  ━━━━ Legal/Attorney       [Faded] │
│  ━━━━ Employment          [Faded]  │
└─────────────────────────────────────┘
```

### Click Same Color Again
- Filter clears
- All edges return to 60% opacity
- All legend items return to 80% opacity
- Smooth 300ms transition back

## Legend Interaction Flow

```
User Action:                    Result:
───────────────────────────────────────────────────────────
Click Blue (Flew Together)  →   Only blue edges shown
                                Blue legend item highlighted
                                Other items faded (30% opacity)

Hover Purple (while filtered)  → Purple legend brightens temporarily
                                 No filter change yet

Click Blue again             →   Filter clears
                                 All edges visible
                                 All legend items 80% opacity

Click Red (Family)           →   Only red edges shown
                                 Red legend item highlighted
                                 Previously blue filter removed
```

## Tooltip Content Breakdown

```
┌─────────────────────────────────────────┐
│ 15 connections (Bold)                   │  ← Dynamic based on weight
│   ↑          ↑                           │
│   |          └─ Tier label (auto)       │
│   └─ Actual count from edge data        │
│                                         │
│ ■■■ Business Partner                    │  ← Color bar matches edge
│  ↑   ↑                                   │
│  |   └─ Relationship label               │
│  └─ Color indicator (12px × 3px)        │
│                                         │
│ Between:                                │
│ John Doe ↔ Jane Smith                   │  ← Entity names formatted
│  ↑       ↑                               │
│  |       └─ Bidirectional arrow         │
│  └─ Source entity                       │
│                                         │
│ Source: Flight Logs, Documents          │  ← Context list
│  ↑                                       │
│  └─ Comma-separated contexts            │
│                                         │
│ Click for details                       │  ← Action hint (italic)
└─────────────────────────────────────────┘
```

## Performance Characteristics

### Rendering Performance
- **Initial Load**: ~500ms for 1,624 edges
- **Hover Response**: <16ms (60 FPS)
- **Filter Toggle**: 300ms smooth transition
- **Zoom/Pan**: No lag (GPU accelerated)
- **Tooltip Display**: <100ms

### Memory Usage
- **SVG Elements**: ~1,624 line elements
- **Event Listeners**: ~3,248 (hover + click per edge)
- **Legend Elements**: ~20 elements (static)
- **Total DOM Nodes**: ~1,700 nodes
- **Memory Footprint**: ~8MB for graph data

### Interaction Performance
- **Edge Hover**: O(1) - direct DOM element
- **Filter Apply**: O(n) - iterates all edges once
- **Tooltip Update**: O(1) - single element update
- **Legend Click**: O(n) - updates all edge opacities

## Responsive Behavior

### Zoom In (Scale > 1)
- Edge thickness remains constant (SVG stroke-width)
- Labels scale with zoom
- Tooltip stays near cursor (absolute positioning)
- Legend stays in corner (fixed position)

### Zoom Out (Scale < 1)
- Thinner edges become harder to see (consider threshold)
- Labels may overlap (D3.js handles collision)
- Tooltip unchanged (always readable)
- Legend unchanged (always visible)

### Pan (Translate)
- All edges move together (SVG group transform)
- Legend stays in viewport corner
- Tooltip follows cursor (not graph)
- Selection state maintained

## Accessibility Considerations

### Color Blindness
- ✅ Thickness provides alternative visual encoding
- ✅ Tooltip text provides non-visual information
- ⚠️ Purple/Blue may be hard to distinguish (deuteranopia)
- ⚠️ Red/Green may be hard to distinguish (protanopia)

### Screen Readers
- ⚠️ SVG edges not accessible without ARIA labels
- ⚠️ Tooltip content readable but not announced
- ⚠️ Legend interactions not keyboard accessible

### Keyboard Navigation
- ❌ Legend not keyboard accessible (mouse-only)
- ❌ Edges not keyboard navigable
- ❌ Tooltip not keyboard triggerable

## Future Accessibility Enhancements
1. Add ARIA labels to edges
2. Make legend keyboard navigable
3. Add focus states for keyboard users
4. Consider colorblind-safe palette option
5. Add text labels option for screen readers

## Testing Scenarios

### Scenario 1: Verify Thickness Tiers
1. Find edge with 1-2 connections → Check 1.5px stroke
2. Find edge with 3-5 connections → Check 3px stroke
3. Find edge with 21+ connections → Check 8px stroke

### Scenario 2: Verify Color Coding
1. Check flight edges are blue (#0969da)
2. Check business edges are purple (#8250df)
3. Check family edges are red (#cf222e)

### Scenario 3: Verify Hover Behavior
1. Hover edge → Tooltip appears
2. Check tooltip shows correct count
3. Check tooltip shows correct relationship type
4. Check edge highlights (opacity + thickness increase)
5. Move mouse away → Tooltip disappears, edge resets

### Scenario 4: Verify Legend Filtering
1. Click blue legend item → Only blue edges visible
2. Verify legend item highlights
3. Click blue again → All edges return
4. Click purple → Different edges visible
5. Verify smooth transitions

### Scenario 5: Verify Details Panel
1. Click edge → Panel opens on right
2. Verify relationship badge shows correct type/color
3. Verify connection count matches
4. Verify data sources listed
5. Close panel → Returns to default state

### Scenario 6: Performance Test
1. Load graph with 1,624 edges
2. Zoom in/out rapidly → Should be smooth
3. Pan across graph → No lag
4. Hover multiple edges quickly → Responsive
5. Toggle filters rapidly → Smooth transitions
