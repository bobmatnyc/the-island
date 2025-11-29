# Network Graph - Visual Guide

## 🖼️ Layout Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                      │
│ ┌─────────────────────────────────────┐  ┌──────────┐  ┌──────────┐       │
│ │ Network Graph                       │  │ Filter   │  │ Stats    │       │
│ │ Explore 275 entities & 1,584 edges  │  │ Toggle   │  │ Toggle   │       │
│ └─────────────────────────────────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌────────────────────────────────────┐  ┌────────────┐ │
│  │              │  │                                    │  │            │ │
│  │   FILTERS    │  │         GRAPH CANVAS               │  │  DETAILS/  │ │
│  │   SIDEBAR    │  │                                    │  │   STATS    │ │
│  │              │  │                                    │  │  SIDEBAR   │ │
│  │              │  │                                    │  │            │ │
│  │  Search      │  │    ┌──────────┐  Graph Controls   │  │            │ │
│  │  [_______]   │  │    │ Legend   │  ┌──┐┌──┐┌──┐┌──┐│  │            │ │
│  │              │  │    │ 🔴 Black │  │+ ││- ││□ ││⏸││  │            │ │
│  │  Categories  │  │    │ 🟠 Bil.  │  └──┘└──┘└──┘└──┘│  │            │ │
│  │  ☑ Politician│  │    │ 🔵 10+   │                   │  │            │ │
│  │  ☐ Business  │  │    │ 🟣 Pol.  │                   │  │            │ │
│  │  ☐ Celebrity │  │    └──────────┘                   │  │            │ │
│  │              │  │                                    │  │            │ │
│  │  Special     │  │         ●     ●──●                │  │            │ │
│  │  ☐ Black Bk  │  │      ●     ●        ●            │  │            │ │
│  │  ☐ Billion.  │  │        ●  ●  ●    ●              │  │            │ │
│  │              │  │     ●           ●     ●           │  │            │ │
│  │  Range       │  │   ●    ●   ●     ●               │  │            │ │
│  │  Min Conn: 0 │  │      ●  ●    ●  ●    ●           │  │            │ │
│  │  ├────○─────┤│  │    ●      ●        ●   ●         │  │            │ │
│  │              │  │  ●    ●      ●   ●               │  │            │ │
│  │  Min Flts: 0 │  │        ●  ●    ●     ●           │  │            │ │
│  │  ├────○─────┤│  │    ●         ●   ●  ●            │  │            │ │
│  │              │  │                                    │  │            │ │
│  │  [Reset All] │  │                                    │  │            │ │
│  │              │  │   [Node hover tooltip]             │  │            │ │
│  │              │  │                                    │  │            │ │
│  └──────────────┘  └────────────────────────────────────┘  └────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🎨 Component Breakdown

### 1. Header Section
```
┌─────────────────────────────────────────────────────────────┐
│ Network Graph                                    [F] [S]    │
│ Explore 275 entities and 1,584 connections                  │
└─────────────────────────────────────────────────────────────┘

Legend:
[F] = Filter Toggle    [S] = Statistics Toggle
```

### 2. Left Sidebar - Filters Panel (320px)
```
┌──────────────────────┐
│  🔍 Filters         │
├──────────────────────┤
│                      │
│  Search              │
│  🔍 [Find entity...] │
│                      │
│  Categories          │
│  ☑ politician        │
│  ☐ business          │
│  ☐ celebrity         │
│  ☐ academic          │
│  ☐ government        │
│  ⋮ (scrollable)      │
│                      │
│  Special Filters     │
│  ☐ In Black Book     │
│  ☐ Billionaire       │
│                      │
│  Min Connections: 5  │
│  ├─────○──────────┤  │
│  0              50   │
│                      │
│  Min Flights: 0      │
│  ├○────────────────┤ │
│  0              50   │
│                      │
│  [Reset Filters]     │
│                      │
└──────────────────────┘
```

### 3. Center - Graph Canvas (Flex 1)
```
┌──────────────────────────────────────────────────────────┐
│ ┌──────────┐                         ┌──┐               │
│ │ Legend   │                         │+ │ Zoom In       │
│ │ 🔴 Black │                         ├──┤               │
│ │ 🟠 Bil.  │                         │- │ Zoom Out      │
│ │ 🔵 10+   │                         ├──┤               │
│ │ 🟣 Pol.  │                         │□ │ Reset View    │
│ └──────────┘                         ├──┤               │
│                                      │⏸│ Pause Physics │
│                                      └──┘               │
│                                                          │
│           ●────●     ●──●──●                             │
│        ●     ●   ●         ●                             │
│     ●    ●           ●                                   │
│        ●   ●──●   ●     ●                                │
│    ●  ●        ●     ●   ●──●                            │
│  ●       ●──●     ●         ●                            │
│      ●          ●   ●   ●                                │
│        ●──●  ●    ●   ●                                  │
│    ●         ●  ●                                        │
│         ●  ●      ●                                      │
│                                                          │
│              [Hover tooltip: Bill Clinton]               │
│              12 connections • 26 flights                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4. Right Sidebar - Details/Stats Panel (320px)

#### When NO node selected (Statistics):
```
┌──────────────────────┐
│  📊 Statistics      │
├──────────────────────┤
│                      │
│  Nodes:      275     │
│  Edges:    1,584     │
│  Density:   4.21%    │
│  Clustering: 12.35%  │
│                      │
│  Most Connected      │
│  ────────────────    │
│  #1 Bill Clinton 45  │
│  #2 Ghislaine M. 42  │
│  #3 Prince Andrew 38 │
│  #4 Donald Trump 35  │
│  #5 Alan Dershow.31  │
│  #6 Les Wexner   28  │
│  #7 Jean-Luc B.  26  │
│  #8 Victoria's S.24  │
│  #9 Naomi Campb. 22  │
│  #10 Kevin Space 21  │
│                      │
└──────────────────────┘
```

#### When node SELECTED (Details):
```
┌──────────────────────┐
│  Bill Clinton    [X]│
├──────────────────────┤
│                      │
│  🔴 Black Book       │
│                      │
│  Connections:   45   │
│  Flights:       26   │
│                      │
│  Categories          │
│  ┌────────────────┐  │
│  │ politician     │  │
│  │ government     │  │
│  └────────────────┘  │
│                      │
│  Direct Connections  │
│  (45)                │
│  ────────────────    │
│  Ghislaine M.    12  │
│  Prince Andrew    8  │
│  Alan Dershowitz  7  │
│  Naomi Campbell   6  │
│  Kevin Spacey     5  │
│  Chris Tucker     4  │
│  ⋮ (scrollable)      │
│                      │
└──────────────────────┘
```

## 🎭 Node States

### Default Node
```
  ●  Small gray circle
     Label hidden (unless zoomed)
```

### Hovered Node
```
  ●  Same size, same color
     Tooltip appears below graph:
     ┌─────────────────────┐
     │ Bill Clinton        │
     │ 45 conn • 26 flights│
     └─────────────────────┘
```

### Selected Node
```
  ⬤  Enlarged, bright color
     Label always visible
     Connected nodes highlighted

  ⬤────⬤────⬤  (thick edges with particles)
     ╲    ╱
       ⬤

  Other nodes fade to 30% opacity
```

### Node Color Examples
```
🔴 ●  Red    = In Black Book (Ghislaine Maxwell)
🟠 ●  Orange = Billionaire (Bill Gates, Trump)
🔵 ●  Blue   = 10+ flights (Chris Tucker)
🟣 ●  Purple = Politician (Bill Clinton)
⚫ ●  Gray   = Default (most entities)
```

## 🔗 Edge Visualization

### Default Edge
```
●────●  Thin gray line (weight 1)
●══════●  Thick gray line (weight 20+)
```

### Highlighted Edge
```
●═>═>═●  Thick with animated particles
        (shows strength of connection)
```

### Edge Thickness Scale
```
Weight  1-5:   ●──●
Weight  6-10:  ●───●
Weight  11-20: ●════●
Weight  20+:   ●═════●
```

## 🎯 Interaction Flow

### Click Node Flow
```
1. User clicks node
   ↓
2. Graph zooms to node (4x)
   ↓
3. Node + connections highlighted
   ↓
4. Other nodes fade (30% opacity)
   ↓
5. Details panel opens (right)
   ↓
6. Edge particles animate
```

### Filter Flow
```
1. User changes filter
   ↓
2. filterGraphData() executes (<50ms)
   ↓
3. Visible nodes recalculated
   ↓
4. Edges filtered (only between visible nodes)
   ↓
5. Graph re-renders smoothly
   ↓
6. Statistics update
```

### Search Flow
```
1. User types "Clinton"
   ↓
2. Graph filters to matches
   ↓
3. First match found
   ↓
4. Auto-click that node
   ↓
5. Graph centers on match
   ↓
6. Details panel shows info
```

## 📐 Responsive Breakpoints

### Desktop (1024px+) - CURRENT
```
┌────────┬──────────────────┬────────┐
│ Filters│      Graph       │ Details│
│  320px │    Flex 1        │  320px │
└────────┴──────────────────┴────────┘
```

### Tablet (768px - 1024px) - FUTURE
```
┌──────────────────────────────────┐
│            Graph                  │
│                                   │
├───────────────┬───────────────────┤
│   Filters     │    Details        │
└───────────────┴───────────────────┘
```

### Mobile (<768px) - FUTURE
```
┌──────────────┐
│    Graph     │
│              │
├──────────────┤
│   Drawer     │
│  (Filters)   │
└──────────────┘
```

## 🎨 Color Palette

### Node Colors
```css
Black Book:    #ef4444  /* Red 500 */
Billionaire:   #f59e0b  /* Amber 500 */
Frequent (10+): #3b82f6  /* Blue 500 */
Politician:    #8b5cf6  /* Violet 500 */
Default:       #6b7280  /* Gray 500 */
Faded:         rgba(200,200,200,0.3)
```

### Edge Colors
```css
Default:       rgba(100,100,100,0.4)
Highlighted:   rgba(100,100,100,0.4)
Faded:         rgba(200,200,200,0.1)
```

### Background
```css
Canvas:        #ffffff  /* White */
Panels:        #ffffff  /* White */
Legend:        rgba(255,255,255,0.9) /* Semi-transparent */
```

## 🖱️ Cursor States

```
Default area:     cursor: default
Node hover:       cursor: pointer
Node dragging:    cursor: move
Background pan:   cursor: grab
Panning:          cursor: grabbing
Button hover:     cursor: pointer
Link hover:       cursor: default
```

## 📱 Touch Gestures (Future)

```
Pinch:       Zoom in/out
Drag:        Pan graph
Tap:         Select node
Double tap:  Reset view
Long press:  Show context menu
```

## 🎬 Animation Timing

```
Zoom transition:    300ms ease
Node selection:     1000ms ease (zoom + pan)
Filter update:      Instant (React render)
Physics:            Continuous (60fps)
Particle flow:      2 particles/link
Panel toggle:       200ms ease
Tooltip appear:     100ms fade
```

## 📊 Information Density

### Overview (Zoomed Out)
```
● ● ● ● ● ●
 ● ● ● ● ●
● ● ● ● ● ●
 ● ● ● ● ●

- No labels visible
- Shape/pattern visible
- Color coding clear
- Clusters identifiable
```

### Detail (Zoomed In)
```
    Bill Clinton
         ●
        ╱│╲
       ╱ │ ╲
      ╱  │  ╲
     ●   ●   ●
 Ghis  Prince Alan

- Labels visible
- Edge weights clear
- Individual connections
- Names readable
```

## 🎪 Special States

### Loading
```
┌──────────────────┐
│                  │
│       ⏳         │
│  Loading graph   │
│                  │
└──────────────────┘
```

### Error
```
┌──────────────────┐
│       ⚠️         │
│  Failed to load  │
│  [Retry Button]  │
└──────────────────┘
```

### Empty (No Results)
```
┌──────────────────┐
│       🔍         │
│  No nodes found  │
│  Try different   │
│    filters       │
└──────────────────┘
```

### Physics Paused
```
Graph frozen in current state
⏸ button shows ▶ Play icon
Tooltip: "Resume Physics"
```

## 🎯 Visual Hierarchy

```
1. HEADER (largest text)
   Network Graph

2. PANEL TITLES (medium text)
   Filters | Statistics

3. LABELS (small text)
   Search, Categories, Min Connections

4. VALUES (small text, bold)
   275 nodes, 45 connections

5. NODE LABELS (variable)
   Scales with zoom level

6. TOOLTIPS (small text)
   Overlay on graph
```

## 🎨 Accessibility Notes

### Color Blind Friendly
- Red/Orange distinction clear
- Legend provides text labels
- Size also indicates importance
- Shape coding possible future enhancement

### Screen Reader
- Buttons have aria-labels
- Panels have headings
- Statistics read as data
- Graph canvas is visual-only (limitation)

### Keyboard (Future)
- Tab through controls ✅
- Arrow keys to pan ⚠️
- Enter to select ⚠️
- Escape to deselect ⚠️

---

**Visual Design Status**: ✅ Complete and Polished
**Last Updated**: November 19, 2025
